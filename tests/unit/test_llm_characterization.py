"""Characterization of the LLM chain as it is today.

These tests pin the behaviour a refactor must keep: which steps each environment produces, their order, kinds, models,
timeouts and endpoint names, and the path names stored for a result. They change no production code. Keys are dummy
values; the Groq factory is replaced so nothing leaves the process.
"""
import os
from datetime import UTC, datetime

import pytest

from wasel.llm.base import CallMeta, TaskSpec
from wasel.llm.client import ChainClient, ChainStep, FailingBackend, build_client

NOW = datetime(2026, 10, 13, tzinfo=UTC)
ENV_KEYS = ("GROQ_BASE_URL", "GROQ_API_KEY", "SELF_HOSTED_API_KEY", "EXTRACT_MODEL", "FALLBACK_MODEL",
            "GROQ_FALLBACK_ENABLED", "GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_ENABLED", "LLM_DEADLINE_S")


@pytest.fixture
def env(monkeypatch):
    """A clean LLM environment. Tests set only what they need."""
    for k in ENV_KEYS:
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("GROQ_FALLBACK_ENABLED", "true")

    class Env:
        def set(self, **kw):
            for k, v in kw.items():
                monkeypatch.setenv(k, v)
            return self
    return Env()


@pytest.fixture
def groq_factory(monkeypatch):
    """Replace the Groq backend factory. Records the base URL and token each backend was built with."""
    built = []

    class Fake:
        def __init__(self, url, token):
            self.url, self.token = url, token

        def complete_json(self, task, model, user, timeout_s):
            return "{}", CallMeta(provider="groq", model=model, latency_ms=1)

    def factory(api_key, models=(), transport=None, base_url=None, reasoning=None):
        # mirrors groq_backend(): explicit arg, then GROQ_BASE_URL, then the hosted Groq URL
        url = base_url or os.environ.get("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
        f = Fake(url.rstrip("/"), api_key)
        built.append(f)
        return f

    monkeypatch.setattr("wasel.llm.groq_backend.groq_backend", factory)
    return built


def _summary(client):
    return [(s.kind, s.endpoint, s.model, s.timeout_s) for s in client.steps]


# ---- which steps each environment produces

def test_no_keys_means_an_empty_chain_and_rules(env):
    c = build_client("live", replay_dirs=[])
    assert c.steps == [] and c.chain_names == [] and c.primary == "rules"


def test_render_setup_is_hosted_groq_with_the_default_models(env, groq_factory):
    env.set(GROQ_API_KEY="hosted-key")
    c = build_client("live", replay_dirs=[])
    assert c.chain_names == ["groq:openai/gpt-oss-120b", "groq:openai/gpt-oss-20b"]
    assert _summary(c) == [("primary", "groq", "openai/gpt-oss-120b", 6),
                           ("fallback_model", "groq", "openai/gpt-oss-20b", 5)]
    assert c.primary == "groq:openai/gpt-oss-120b"
    assert {b.url for b in groq_factory} == {"https://api.groq.com/openai/v1"}
    assert {b.token for b in groq_factory} == {"hosted-key"}


def test_fallback_disabled_leaves_one_step(env, groq_factory):
    env.set(GROQ_API_KEY="hosted-key", GROQ_FALLBACK_ENABLED="false")
    c = build_client("live", replay_dirs=[])
    assert c.chain_names == ["groq:openai/gpt-oss-120b"]


def test_model_overrides_apply_to_the_matching_steps(env, groq_factory):
    env.set(GROQ_API_KEY="k", EXTRACT_MODEL="openai/gpt-oss-20b", FALLBACK_MODEL="openai/gpt-oss-120b")
    c = build_client("live", replay_dirs=[])
    assert c.chain_names == ["groq:openai/gpt-oss-20b", "groq:openai/gpt-oss-120b"]


def test_deadline_override_is_read(env, groq_factory):
    env.set(GROQ_API_KEY="k", LLM_DEADLINE_S="12.5")
    assert build_client("live", replay_dirs=[]).deadline_s == 12.5


def test_self_hosted_with_only_groq_api_key_uses_it_as_the_token(env, groq_factory):
    """Before SELF_HOSTED_API_KEY existed: GROQ_API_KEY is the vLLM token and there is no backup."""
    env.set(GROQ_BASE_URL="http://amd-host.test:8001/v1", GROQ_API_KEY="vllm-token",
            EXTRACT_MODEL="openai/gpt-oss-20b", GROQ_FALLBACK_ENABLED="false")
    c = build_client("live", replay_dirs=[])
    assert c.chain_names == ["self-hosted:openai/gpt-oss-20b"]
    assert [b.token for b in groq_factory] == ["vllm-token"]


def test_self_hosted_with_its_own_token_adds_the_hosted_backup(env, groq_factory):
    env.set(GROQ_BASE_URL="http://amd-host.test:8001/v1", SELF_HOSTED_API_KEY="vllm-token",
            GROQ_API_KEY="hosted-key", EXTRACT_MODEL="openai/gpt-oss-20b", GROQ_FALLBACK_ENABLED="false")
    c = build_client("live", replay_dirs=[])
    assert _summary(c) == [("primary", "self-hosted", "openai/gpt-oss-20b", 6),
                           ("fallback_provider", "groq", "openai/gpt-oss-20b", 8)]
    tokens = {b.url: b.token for b in groq_factory}
    assert tokens["http://amd-host.test:8001/v1"] == "vllm-token"
    assert tokens["https://api.groq.com/openai/v1"] == "hosted-key"


def test_self_hosted_token_without_a_hosted_key_has_no_backup(env, groq_factory):
    env.set(GROQ_BASE_URL="http://amd-host.test:8001/v1", SELF_HOSTED_API_KEY="vllm-token",
            EXTRACT_MODEL="openai/gpt-oss-20b", GROQ_FALLBACK_ENABLED="false")
    assert build_client("live", replay_dirs=[]).chain_names == ["self-hosted:openai/gpt-oss-20b"]


def test_gemini_is_appended_last_when_enabled(env, groq_factory, monkeypatch):
    env.set(GROQ_API_KEY="k", GEMINI_API_KEY="g", GEMINI_MODEL="gemini-x", GEMINI_ENABLED="true")
    monkeypatch.setattr("wasel.llm.gemini_backend.gemini_backend", lambda *a, **k: FailingBackend("5xx"))
    c = build_client("live", replay_dirs=[])
    assert _summary(c)[-1] == ("fallback_provider", "gemini", "gemini-x", 8)
    assert c.chain_names[-1] == "gemini:gemini-x"


def test_gemini_needs_the_enable_flag(env, groq_factory):
    env.set(GROQ_API_KEY="k", GEMINI_API_KEY="g", GEMINI_MODEL="gemini-x")
    assert all(s.provider != "gemini" for s in build_client("live", replay_dirs=[]).steps)


# ---- fault modes: same chain shape, failing backends

@pytest.mark.parametrize("mode, expected", [
    ("fail_primary", [("primary", "groq", "openai/gpt-oss-120b", 6), ("fallback_model", "groq", "openai/gpt-oss-20b", 5)]),
    ("fail_groq", [("primary", "groq", "openai/gpt-oss-120b", 6), ("fallback_model", "groq", "openai/gpt-oss-20b", 5),
                   ("fallback_provider", "gemini", "gemini", 8)]),
    ("fail_all", [("primary", "groq", "openai/gpt-oss-120b", 6), ("fallback_model", "groq", "openai/gpt-oss-20b", 5),
                  ("fallback_provider", "gemini", "gemini", 8)]),
])
def test_fault_modes_have_fixed_chains(env, mode, expected):
    c = build_client(mode, replay_dirs=[])
    assert _summary(c) == expected


def test_replay_mode_without_fixtures_refuses_to_start(env, tmp_path):
    with pytest.raises(ValueError, match="needs recorded fixtures"):
        build_client("replay", replay_dirs=[tmp_path])


def test_unknown_mode_is_refused(env):
    with pytest.raises(ValueError, match="unknown LLM_MODE"):
        build_client("nonsense", replay_dirs=[])


# ---- what a result records

def _task():
    return TaskSpec("extract", "s", {}, "sys", (), "v1", 10, 0.0, None, False)


class _Ok:
    def complete_json(self, task, model, user, timeout_s):
        return '{"ok": true}', CallMeta(provider="groq", model=model, latency_ms=1)


def test_a_schema_error_on_the_primary_moves_to_the_same_endpoints_next_model():
    """A 400 (SchemaRejected) is a model-level error: the same endpoint's fallback_model step still runs."""
    steps = [ChainStep("primary", "groq", "m1", FailingBackend("400"), 6),
             ChainStep("fallback_model", "groq", "m2", _Ok(), 5)]
    res = ChainClient(steps).extract(_task(), "u", parse=lambda r: r, meter=None, sandbox_id=None, now=NOW)
    assert res.path == "fallback_model" and res.model == "m2" and res.parsed is not None


def test_a_provider_down_on_the_primary_skips_the_same_endpoints_next_model():
    """Current behaviour: ProviderDown opens the endpoint's breaker, so its fallback_model step is skipped."""
    steps = [ChainStep("primary", "groq", "m1", FailingBackend("5xx"), 6),
             ChainStep("fallback_model", "groq", "m2", _Ok(), 5)]
    res = ChainClient(steps).extract(_task(), "u", parse=lambda r: r, meter=None, sandbox_id=None, now=NOW)
    assert res.path == "rules" and res.parsed is None
    assert [a.model for a in res.attempts] == ["m1"]          # m2 was never attempted, and no error is recorded for it


def test_a_provider_down_on_the_primary_reaches_a_different_endpoint():
    steps = [ChainStep("primary", "groq", "m1", FailingBackend("5xx"), 6),
             ChainStep("fallback_provider", "gemini", "g", _Ok(), 8)]
    res = ChainClient(steps).extract(_task(), "u", parse=lambda r: r, meter=None, sandbox_id=None, now=NOW)
    assert res.path == "fallback_provider" and res.provider == "gemini"


def test_the_primary_sets_the_llm_path():
    res = ChainClient([ChainStep("primary", "groq", "m1", _Ok(), 6)]).extract(
        _task(), "u", parse=lambda r: r, meter=None, sandbox_id=None, now=NOW)
    assert res.path == "llm" and res.provider == "groq" and res.endpoint == "groq"


def test_everything_failing_records_rules_and_the_errors():
    client = ChainClient([ChainStep("primary", "groq", "m1", FailingBackend("5xx"), 6)])
    res = client.extract(_task(), "u", parse=lambda r: r, meter=None, sandbox_id=None, now=NOW)
    assert res.path == "rules" and res.parsed is None and res.provider is None
    assert any("ProviderDown" in e for e in res.errors)


def test_the_breaker_is_keyed_by_endpoint_and_is_independent_per_endpoint():
    client = ChainClient([ChainStep("primary", "groq", "m1", FailingBackend("5xx"), 6),
                          ChainStep("fallback_provider", "gemini", "g", FailingBackend("5xx"), 8)])
    client.extract(_task(), "u1", parse=lambda r: r, meter=None, sandbox_id=None, now=NOW)
    assert client._breaker_until.get("groq", 0) > 0
    assert client._breaker_until.get("gemini", 0) > 0
