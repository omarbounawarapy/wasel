"""GROQ_BASE_URL routing: default -> Groq with the
Groq reasoning kwargs; self-hosted (GROQ_BASE_URL env or explicit base_url) -> URL honored,
Groq-only `reasoning_format` dropped (self-hosted vLLM 400s on unknown fields) while
`reasoning_effort` is kept (vLLM honors it for gpt-oss)."""
from __future__ import annotations

import json

import httpx

from wasel.llm.base import TaskSpec
from wasel.llm.groq_backend import groq_backend

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


def test_oversized_provider_answer_is_a_parse_error_not_held_in_memory(monkeypatch):
    import pytest

    from wasel.llm.base import ParseError
    monkeypatch.delenv("GROQ_BASE_URL", raising=False)
    pulled = []

    def chunks():
        for _ in range(20):                                   # 20 x 256 KB = 5 MB on offer
            pulled.append(1)
            yield b" " * 262_144

    backend = groq_backend("k", models=("openai/gpt-oss-20b",), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=chunks())))
    with pytest.raises(ParseError, match="too_large"):
        backend.complete_json(TASK, "openai/gpt-oss-20b", "salam", timeout_s=5)
    assert len(pulled) <= 3                                   # stopped reading shortly after the cap


def test_declared_content_length_over_the_cap_is_refused(monkeypatch):
    import pytest

    from wasel.llm.base import ParseError
    backend = groq_backend("k", models=("openai/gpt-oss-20b",), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"{}", headers={"content-length": "5000000"})))
    with pytest.raises(ParseError, match="too_large"):
        backend.complete_json(TASK, "openai/gpt-oss-20b", "salam", timeout_s=5)


def test_gemini_backend_has_the_same_cap():
    import pytest

    from wasel.llm.base import ParseError
    from wasel.llm.gemini_backend import gemini_backend
    backend = gemini_backend("k", "gemini-x", transport=httpx.MockTransport(
        lambda request: httpx.Response(200, content=b"x" * 600_000)))
    with pytest.raises(ParseError, match="too_large"):
        backend.complete_json(TASK, "gemini-x", "salam", timeout_s=5)


def test_a_large_error_body_is_cut_not_refused():
    import pytest

    from wasel.llm.base import SchemaRejected
    backend = groq_backend("k", models=("openai/gpt-oss-20b",), transport=httpx.MockTransport(
        lambda request: httpx.Response(400, content=b"bad " * 100_000)))
    with pytest.raises(SchemaRejected):
        backend.complete_json(TASK, "openai/gpt-oss-20b", "salam", timeout_s=5)


def test_normal_answer_still_parses():
    backend = groq_backend("k", models=("openai/gpt-oss-20b",), transport=_capture([]))
    assert backend.complete_json(TASK, "openai/gpt-oss-20b", "salam", timeout_s=5)[0] == "{}"
