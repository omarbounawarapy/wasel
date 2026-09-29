"""The provider chain and its test doubles.

ChainClient.extract() walks this chain:
  1 Groq gpt-oss-120b            -> path 'llm'
  2 Groq gpt-oss-20b             -> 'fallback_model'    (only after 429/400/404/truncated/parse error)
  3 Gemini (if configured)       -> 'fallback_provider' (after any failure, or when step 2 was skipped)
  4 nothing left                 -> the caller runs the rules extractor, path 'rules'
No retries, no sleeps. ProviderDown opens a 60 s breaker for that provider. A step whose timeout doesn't
fit in the remaining deadline is skipped. Each attempted call first asks the UsageMeter; a cap stops the
chain (path 'rules', `cap` set) and never becomes an HTTP error.

ReplayClient / FailingClient are the same ChainClient over ReplayBackend / FailingBackend, selected by
LLM_MODE = live | replay | fail_primary | fail_groq | fail_all (build_client).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

from app.contracts import Attempt, CapDecision, UsageMeter, UsageRecord
from app.llm import trace
from app.llm.base import (
    CallMeta,
    FixtureMissing,
    LLMError,
    ModelGone,
    ParseError,
    ProviderDown,
    RateLimited,
    SchemaRejected,
    TaskSpec,
    Timeout,
    Truncated,
)

StepKind = Literal["primary", "fallback_model", "fallback_provider"]
_PATH = {"primary": "llm", "fallback_model": "fallback_model", "fallback_provider": "fallback_provider"}
_NEXT_MODEL_ERRORS = (RateLimited, SchemaRejected, ModelGone, Truncated, ParseError)


def replay_key(user: str) -> str:
    """ReplayClient key: sha256 of the rendered window, not normalized, no version."""
    return hashlib.sha256(user.encode("utf-8")).hexdigest()


@dataclass
class ChainStep:
    kind: StepKind
    provider: Literal["groq", "gemini"]
    model: str
    backend: object                   # .complete_json(task, model, user, timeout_s) -> (str, CallMeta)
    timeout_s: float


@dataclass
class ChainResult:
    parsed: object | None             # whatever `parse` returned for the winning step, None -> rules
    raw: str | None
    path: str                         # llm | fallback_model | fallback_provider | rules
    provider: str | None
    model: str | None
    attempts: list[Attempt] = field(default_factory=list)
    usage: list[UsageRecord] = field(default_factory=list)
    meta: CallMeta | None = None
    cap: CapDecision | None = None    # set when a cap stopped the chain
    errors: list[str] = field(default_factory=list)


class ChainClient:
    def __init__(self, steps: list[ChainStep], *, deadline_s: float = 20.0, breaker_s: float = 60.0,
                 monotonic: Callable[[], float] = time.monotonic, cache_size: int = 512):
        self.steps = steps
        self._cache: OrderedDict[str, ChainResult] = OrderedDict()
        self.cache_size = cache_size
        self.deadline_s, self.breaker_s = deadline_s, breaker_s
        self._mono = monotonic
        self._breaker_until: dict[str, float] = {}

    @property
    def primary(self) -> str:
        return f"{self.steps[0].provider}:{self.steps[0].model}" if self.steps else "rules"

    @property
    def chain_names(self) -> list[str]:
        return [f"{s.provider}:{s.model}" for s in self.steps]

    def extract(self, task: TaskSpec, user: str, *, parse: Callable[[str], object],
                meter: UsageMeter | None, sandbox_id: str | None, now: datetime,
                role: Literal["extract", "rewrite", "judge"] = "extract") -> ChainResult:
        """The one LLM entry point: per-request input cap, response cache, then the chain; one trace per call."""
        key = hashlib.sha256(f"{task.name}\0{task.prompt_version}\0{user}".encode()).hexdigest()
        base = {"trace_id": trace.new_id(), "role": role, "prompt_version": task.prompt_version,
                "schema": task.schema_name, "input_sha": key[:16], "input_chars": len(user),
                "max_output_tokens": task.max_output_tokens}
        if task.max_input_chars and len(user) > task.max_input_chars:
            trace.emit({**base, "outcome": "input_too_large", "path": "rules", "attempts": []})
            return ChainResult(None, None, "rules", None, None, errors=["input_too_large"])
        if task.cache and key in self._cache:
            self._cache.move_to_end(key)
            hit = self._cache[key]
            trace.emit({**base, "outcome": "cache_hit", "cache_hit": True, "path": hit.path,
                        "provider": hit.provider, "model": hit.model, "latency_ms": 0, "attempts": [],
                        "output": hit.raw if role != "extract" else None})
            return ChainResult(hit.parsed, hit.raw, hit.path, hit.provider, hit.model, meta=hit.meta)
        res = self._run(task, user, parse=parse, meter=meter, sandbox_id=sandbox_id, now=now, role=role)
        ok = res.parsed is not None
        trace.emit({**base, "outcome": "ok" if ok else ("cap" if res.cap else "failed"), "cache_hit": False,
                    "path": res.path, "provider": res.provider, "model": res.model,
                    "attempts": [f"{a.provider}:{a.model}:{a.outcome}" for a in res.attempts],
                    "latency_ms": sum(u.latency_ms or 0 for u in res.usage),
                    "tokens_in": sum(u.tokens_in or 0 for u in res.usage),
                    "tokens_out": sum(u.tokens_out or 0 for u in res.usage),
                    "errors": res.errors[:3], "output": res.raw if ok and role != "extract" else None})
        if ok and task.cache:
            self._cache[key] = res
            if len(self._cache) > self.cache_size:
                self._cache.popitem(last=False)
        return res

    def _run(self, task: TaskSpec, user: str, *, parse, meter, sandbox_id, now, role) -> ChainResult:
        t0 = self._mono()
        res = ChainResult(None, None, "rules", None, None)
        skip_same_provider_fallback = False
        for step in self.steps:
            if step.kind == "fallback_model" and skip_same_provider_fallback:
                continue
            if self._breaker_until.get(step.provider, 0) > self._mono():
                res.errors.append(f"{step.provider}:breaker_open")
                continue
            if step.timeout_s > self.deadline_s - (self._mono() - t0):
                res.errors.append(f"{step.model}:skipped_deadline")
                continue
            if meter is not None:
                decision = meter.allow(role, sandbox_id, now)
                if decision != "ok":
                    res.cap = decision
                    return res
            t_call = self._mono()
            try:
                raw, meta = step.backend.complete_json(task, step.model, user, step.timeout_s)
                parsed = parse(raw)
            except LLMError as e:
                latency = int((self._mono() - t_call) * 1000)
                res.attempts.append(Attempt(step.provider, step.model, e.outcome, latency))
                res.usage.append(UsageRecord(now, role, step.provider, step.model, e.outcome, None, None, latency))
                res.errors.append(f"{step.model}:{type(e).__name__}:{str(e)[:120]}")
                if isinstance(e, ProviderDown):
                    self._breaker_until[step.provider] = self._mono() + self.breaker_s
                if step.kind == "primary" and not isinstance(e, _NEXT_MODEL_ERRORS):
                    skip_same_provider_fallback = True        # Timeout / ProviderDown skip the sibling
                continue
            latency = meta.latency_ms or int((self._mono() - t_call) * 1000)
            res.attempts.append(Attempt(step.provider, step.model, "ok", latency))
            res.usage.append(UsageRecord(now, role, step.provider, step.model, "ok",
                                         meta.tokens_in, meta.tokens_out, latency))
            res.parsed, res.raw, res.meta = parsed, raw, meta
            res.path, res.provider, res.model = _PATH[step.kind], step.provider, step.model
            return res
        return res


# ---------------------------------------------------------------- test doubles
class ReplayBackend:
    """Serves recorded fixtures keyed by replay_key(user). Envelope:
    {"meta":{"source","provider","model","prompt_version","recorded_at"},"key","window","status",
     "headers","response":{"choices":[{"finish_reason","message":{"content"}}],"usage":{...}}}"""

    def __init__(self, dirs: list[Path], *, allow_hand_crafted: bool = False, as_provider: str | None = None):
        self.provider = as_provider or "replay"
        self.fixtures: dict[str, dict] = {}
        for d in dirs:
            for p in sorted(Path(d).rglob("*.json")):
                fx = json.loads(p.read_text(encoding="utf-8"))
                if "key" not in fx or "response" not in fx:
                    continue
                if fx["meta"].get("source") == "hand_crafted" and not allow_hand_crafted:
                    continue
                self.fixtures[fx["key"]] = fx

    def complete_json(self, task: TaskSpec, model: str, user: str, timeout_s: float) -> tuple[str, CallMeta]:
        fx = self.fixtures.get(replay_key(user))
        if fx is None:
            preview = user.split("\n")[1][:60] if "\n" in user else user[:60]
            raise FixtureMissing(f"no fixture for key {replay_key(user)[:12]}…: {preview!r}: run `make record`")
        status = fx.get("status", 200)
        if status == 429:
            raise RateLimited(None)
        if status >= 500:
            raise ProviderDown(f"http {status}")
        if status >= 400:
            raise SchemaRejected(f"http {status}")
        ch = fx["response"]["choices"][0]
        if ch.get("finish_reason", "stop") != "stop":
            raise Truncated(ch.get("finish_reason"))
        usage = fx["response"].get("usage") or {}
        return ch["message"]["content"], CallMeta(
            provider=fx["meta"].get("provider", self.provider), model=fx["meta"].get("model", model),
            latency_ms=0, tokens_in=usage.get("prompt_tokens"), tokens_out=usage.get("completion_tokens"),
            source=fx["meta"].get("source", "recorded"))


class FailingBackend:
    ERRORS = {"429": lambda: RateLimited(None), "timeout": lambda: Timeout("timeout"),
              "400": lambda: SchemaRejected("400"), "malformed": lambda: ParseError("malformed"),
              "5xx": lambda: ProviderDown("5xx"), "404": lambda: ModelGone("404"),
              "truncated": lambda: Truncated("length")}

    def __init__(self, kind: str):
        self.kind = kind
        self.calls = 0

    def complete_json(self, task, model, user, timeout_s):
        self.calls += 1
        raise self.ERRORS[self.kind]()


# ---------------------------------------------------------------- selection by LLM_MODE
EXTRACT_MODEL = "openai/gpt-oss-120b"            # defaults; config/llm.yaml routing and env override
FALLBACK_MODEL = "openai/gpt-oss-20b"


def build_client(mode: str | None = None, *, replay_dirs: list[Path] | None = None,
                 allow_hand_crafted: bool = False, deadline_s: float = 20.0) -> ChainClient:
    mode = mode or os.environ.get("LLM_MODE", "live")
    replay_dirs = replay_dirs or []
    from app.llm.prompts import registry
    routing = registry().get("routing", {})
    primary, fallback = routing.get("primary", EXTRACT_MODEL), routing.get("fallback_model", FALLBACK_MODEL)
    gem_model = os.environ.get("GEMINI_MODEL", "gemini")

    def replay(provider="groq"):
        return ReplayBackend(replay_dirs, allow_hand_crafted=allow_hand_crafted, as_provider=provider)

    if mode == "replay":
        return ChainClient([ChainStep("primary", "groq", EXTRACT_MODEL, replay(), 6)], deadline_s=deadline_s)
    if mode == "fail_primary":
        return ChainClient([ChainStep("primary", "groq", EXTRACT_MODEL, FailingBackend("429"), 6),
                            ChainStep("fallback_model", "groq", FALLBACK_MODEL, replay(), 5)],
                           deadline_s=deadline_s)
    if mode == "fail_groq":
        return ChainClient([ChainStep("primary", "groq", EXTRACT_MODEL, FailingBackend("5xx"), 6),
                            ChainStep("fallback_model", "groq", FALLBACK_MODEL, FailingBackend("5xx"), 5),
                            ChainStep("fallback_provider", "gemini", gem_model, replay("gemini"), 8)],
                           deadline_s=deadline_s)
    if mode == "fail_all":
        return ChainClient([ChainStep("primary", "groq", EXTRACT_MODEL, FailingBackend("5xx"), 6),
                            ChainStep("fallback_model", "groq", FALLBACK_MODEL, FailingBackend("429"), 5),
                            ChainStep("fallback_provider", "gemini", gem_model, FailingBackend("5xx"), 8)],
                           deadline_s=deadline_s)
    if mode != "live":
        raise ValueError(f"unknown LLM_MODE {mode!r}")
    from app.llm.gemini_backend import gemini_backend, load_probe
    from app.llm.groq_backend import groq_backend
    steps: list[ChainStep] = []
    if os.environ.get("GROQ_API_KEY"):
        g = groq_backend(os.environ["GROQ_API_KEY"])
        steps.append(ChainStep("primary", "groq", os.environ.get("EXTRACT_MODEL", primary), g, 6))
        if os.environ.get("GROQ_FALLBACK_ENABLED", "true").lower() == "true":   # false if buckets are per org
            steps.append(ChainStep("fallback_model", "groq",
                                   os.environ.get("FALLBACK_MODEL", fallback), g, 5))
    if os.environ.get("GEMINI_API_KEY") and os.environ.get("GEMINI_MODEL") and \
            os.environ.get("GEMINI_ENABLED", "false").lower() == "true":
        gb = gemini_backend(os.environ["GEMINI_API_KEY"], os.environ["GEMINI_MODEL"],
                            load_probe(os.environ.get("PROBE_FILE", "config/probe.json")))
        steps.append(ChainStep("fallback_provider", "gemini", os.environ["GEMINI_MODEL"], gb, 8))
    return ChainClient(steps, deadline_s=float(os.environ.get("LLM_DEADLINE_S", routing.get("deadline_s", deadline_s))),
                       cache_size=int(routing.get("cache_size", 512)))
