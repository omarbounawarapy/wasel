"""OpenAI-compatible chat-completions backend over httpx, used for Groq and for Gemini's
OpenAI-compat endpoint. max_retries = 0 by construction: this module never retries or sleeps.

Both providers speak the same HTTP API as the `openai` and `groq` SDKs, so this uses plain httpx and
avoids one more pinned dependency.
"""
from __future__ import annotations

import os
import time
from collections.abc import Callable

import httpx

from wasel.llm.base import (
    CallMeta,
    ModelGone,
    ParseError,
    ProviderDown,
    RateLimited,
    SchemaRejected,
    TaskSpec,
    Timeout,
    Truncated,
)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_REASONING_KWARGS = {"reasoning_effort": "low", "reasoning_format": "hidden"}
# Self-hosted OpenAI-compatible servers (vLLM on a GPU host, docs/self-hosted-llm.md) reject the
# Groq-only `reasoning_format` field with a 400; `reasoning_effort` is honored for gpt-oss.
SELFHOST_REASONING_KWARGS = {"reasoning_effort": "low"}


def _int(v) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def build_messages(task: TaskSpec, user: str) -> list[dict]:
    msgs = [{"role": "system", "content": task.system_prompt}]
    for u, a in task.few_shot:
        msgs += [{"role": "user", "content": u}, {"role": "assistant", "content": a}]
    msgs.append({"role": "user", "content": user})
    return msgs


class OpenAICompatBackend:
    def __init__(self, provider: str, base_url: str, api_key: str,
                 schema_adapter: Callable[[dict], dict] = lambda s: s, extra: dict | None = None,
                 max_tokens_param: str = "max_completion_tokens", send_seed: bool = True,
                 transport: httpx.BaseTransport | None = None):
        self.provider = provider
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.schema_adapter, self.extra = schema_adapter, extra or {}
        self.max_tokens_param, self.send_seed = max_tokens_param, send_seed
        self._transport = transport

    def complete_json(self, task: TaskSpec, model: str, user: str, timeout_s: float) -> tuple[str, CallMeta]:
        body = {
            "model": model, "messages": build_messages(task, user), "temperature": task.temperature,
            "response_format": {"type": "json_schema", "json_schema": {
                "name": task.schema_name, "strict": True, "schema": self.schema_adapter(task.schema)}},
            self.max_tokens_param: task.max_output_tokens, **self.extra.get(model, {}),
        }
        if self.send_seed:
            body["seed"] = 7
        t0 = time.monotonic()
        try:
            with httpx.Client(timeout=timeout_s, transport=self._transport) as c:
                r = c.post(f"{self.base_url}/chat/completions", json=body,
                           headers={"Authorization": f"Bearer {self.api_key}"})
        except httpx.TimeoutException as e:
            raise Timeout(str(e)[:200]) from e
        except httpx.HTTPError as e:
            raise ProviderDown(type(e).__name__) from e
        if r.status_code == 429:
            raise RateLimited(float(r.headers["retry-after"]) if r.headers.get("retry-after") else None)
        if r.status_code == 404:
            raise ModelGone(r.text[:200])
        if r.status_code in (401, 403) or r.status_code >= 500:
            raise ProviderDown(f"http {r.status_code}")
        if r.status_code >= 400:
            raise SchemaRejected(r.text[:300])
        try:
            data = r.json()
            ch = data["choices"][0]
        except (ValueError, KeyError, IndexError) as e:
            raise ParseError("bad_envelope") from e
        if ch.get("finish_reason") != "stop":
            raise Truncated(str(ch.get("finish_reason")))
        content = (ch.get("message") or {}).get("content")
        if not content:
            raise ParseError("empty")
        usage = data.get("usage") or {}
        meta = CallMeta(
            provider=self.provider, model=model, latency_ms=int((time.monotonic() - t0) * 1000),
            tokens_in=_int(usage.get("prompt_tokens")),
            tokens_cached=_int((usage.get("prompt_tokens_details") or {}).get("cached_tokens")),
            tokens_out=_int(usage.get("completion_tokens")),
            tokens_reasoning=_int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens")),
            finish_reason=ch.get("finish_reason"),
            ratelimit_remaining_tokens=_int(r.headers.get("x-ratelimit-remaining-tokens")))
        return content, meta


def groq_backend(api_key: str, models: tuple[str, ...] = ("openai/gpt-oss-120b", "openai/gpt-oss-20b"),
                 transport: httpx.BaseTransport | None = None,
                 base_url: str | None = None) -> OpenAICompatBackend:
    """base_url: explicit arg wins, then GROQ_BASE_URL env (self-hosted vLLM), then Groq.

    Env read at call time (not import) so tests and the demo can flip providers in-process.
    """
    url = (base_url or os.environ.get("GROQ_BASE_URL") or GROQ_BASE_URL).rstrip("/")
    kwargs = GROQ_REASONING_KWARGS if url == GROQ_BASE_URL else SELFHOST_REASONING_KWARGS
    return OpenAICompatBackend("groq", url, api_key,
                               extra={m: kwargs for m in models}, transport=transport)
