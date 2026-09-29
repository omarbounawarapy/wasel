"""GROQ_BASE_URL routing: default -> Groq with the
Groq reasoning kwargs; self-hosted (GROQ_BASE_URL env or explicit base_url) -> URL honored,
Groq-only `reasoning_format` dropped (self-hosted vLLM 400s on unknown fields) while
`reasoning_effort` is kept (vLLM honors it for gpt-oss)."""
from __future__ import annotations

import json

import httpx

from app.llm.base import TaskSpec
from app.llm.groq_backend import groq_backend

TASK = TaskSpec(name="extract", schema_name="extraction", schema={"type": "object"},
                system_prompt="sys", few_shot=(), prompt_version="extract-v1",
                max_output_tokens=64, temperature=0.0)

ENVELOPE = {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1}}


def _capture(seen: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=ENVELOPE)
    return httpx.MockTransport(handler)


def test_default_is_groq_with_groq_reasoning_kwargs(monkeypatch):
    monkeypatch.delenv("GROQ_BASE_URL", raising=False)
    seen: list[httpx.Request] = []
    backend = groq_backend("k", models=("openai/gpt-oss-20b",), transport=_capture(seen))
    content, meta = backend.complete_json(TASK, "openai/gpt-oss-20b", "salam", timeout_s=5)
    assert content == "{}" and meta.provider == "groq"
    assert str(seen[0].url) == "https://api.groq.com/openai/v1/chat/completions"
    body = json.loads(seen[0].content)
    assert body["reasoning_effort"] == "low" and body["reasoning_format"] == "hidden"


def test_env_base_url_routes_selfhosted_and_drops_reasoning_format(monkeypatch):
    monkeypatch.setenv("GROQ_BASE_URL", "http://10.0.0.5:8001/v1/")
    seen: list[httpx.Request] = []
    backend = groq_backend("local-token", models=("openai/gpt-oss-20b",), transport=_capture(seen))
    backend.complete_json(TASK, "openai/gpt-oss-20b", "salam", timeout_s=5)
    assert str(seen[0].url) == "http://10.0.0.5:8001/v1/chat/completions"   # trailing / stripped
    body = json.loads(seen[0].content)
    assert body["reasoning_effort"] == "low" and "reasoning_format" not in body
    assert seen[0].headers["Authorization"] == "Bearer local-token"


def test_explicit_base_url_beats_env(monkeypatch):
    monkeypatch.setenv("GROQ_BASE_URL", "http://env-host:8001/v1")
    seen: list[httpx.Request] = []
    backend = groq_backend("k", models=("m",), transport=_capture(seen),
                           base_url="http://arg-host:8002/v1")
    backend.complete_json(TASK, "m", "salam", timeout_s=5)
    assert str(seen[0].url).startswith("http://arg-host:8002/v1/chat/completions")
