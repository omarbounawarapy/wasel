"""Self-hosted primary (GROQ_BASE_URL, e.g. the AMD host) with the hosted Groq API as backup (SELF_HOSTED_API_KEY holds its token; GROQ_API_KEY is the backup).

The network is replaced: the Groq backend factory returns fakes keyed by the URL they were built for, so each test
decides what the self-hosted host and the hosted API do.
"""
from datetime import UTC, datetime

import pytest

from wasel.llm import client as client_mod
from wasel.llm.base import CallMeta, ProviderDown, TaskSpec, Timeout
from wasel.llm.client import build_client
from wasel.llm.groq_backend import GROQ_BASE_URL as HOSTED_URL

SELF = "http://amd-host.test:8001/v1"
NOW = datetime(2026, 10, 13, tzinfo=UTC)


class _Backend:
    def __init__(self, url, behaviour):
        self.url, self.behaviour, self.calls = url, behaviour, 0

    def complete_json(self, task, model, user, timeout_s):
        self.calls += 1
        if self.behaviour is not None:
            raise self.behaviour
        return '{"ok": true}', CallMeta(provider="groq", model=model, latency_ms=1)


def _task():
    return TaskSpec("extract", "s", {}, "sys", (), "v1", 10, 0.0, None, False)


@pytest.fixture
def backends(monkeypatch, tmp_path):
    """Replace the Groq backend factory; `behave` maps a URL to the error it raises (None = answers)."""
    made = {}
    behave = {}

    def factory(api_key, models=(), transport=None, base_url=None):
        url = (base_url or SELF).rstrip("/")
        b = _Backend(url, behave.get(url))
        made.setdefault(url, []).append(b)
        return b

    monkeypatch.setattr("wasel.llm.groq_backend.groq_backend", factory)
    monkeypatch.setenv("GROQ_BASE_URL", SELF)
    monkeypatch.setenv("SELF_HOSTED_API_KEY", "amd-token")
    monkeypatch.setenv("GROQ_API_KEY", "hosted-key")         # the key Render already has; now the backup
    monkeypatch.setenv("EXTRACT_MODEL", "openai/gpt-oss-20b")
    monkeypatch.setenv("GROQ_FALLBACK_ENABLED", "false")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    return made, behave


def _extract(client):
    return client.extract(_task(), "order text", parse=lambda raw: raw, meter=None, sandbox_id=None, now=NOW)


def test_chain_names_self_hosted_first_then_hosted(backends):
    client = build_client("live", replay_dirs=[])
    assert client.chain_names == ["self-hosted:openai/gpt-oss-20b", "groq:openai/gpt-oss-20b"]
    assert client.steps[1].kind == "fallback_provider" and client.steps[1].provider == "groq"


@pytest.mark.parametrize("error", [ProviderDown("connection refused"), ProviderDown("http 503"),
                                   Timeout("read timed out")], ids=["refused", "5xx", "timeout"])
def test_self_hosted_failure_is_answered_by_the_hosted_backup(backends, error):
    made, behave = backends
    behave[SELF] = error
    res = _extract(build_client("live", replay_dirs=[]))
    assert res.parsed is not None and res.path == "fallback_provider"
    assert res.endpoint == "groq" and res.provider == "groq" and res.model == "openai/gpt-oss-20b"
    assert made[HOSTED_URL][0].calls == 1


def test_dead_self_hosted_host_is_not_retried_while_its_breaker_is_open(backends):
    made, behave = backends
    behave[SELF] = ProviderDown("connection refused")
    client = build_client("live", replay_dirs=[])
    _extract(client)
    res = _extract(client)
    assert res.path == "fallback_provider"
    assert made[SELF][0].calls == 1            # second request skipped the primary, went straight to the backup
    assert any("self-hosted:breaker_open" in e for e in res.errors)


def test_both_down_falls_back_to_rules(backends):
    made, behave = backends
    behave[SELF] = ProviderDown("refused")
    behave[HOSTED_URL] = ProviderDown("http 500")
    res = _extract(build_client("live", replay_dirs=[]))
    assert res.parsed is None and res.path == "rules"


def test_no_self_hosted_token_keeps_the_old_meaning_of_groq_api_key(backends, monkeypatch):
    made, _ = backends
    monkeypatch.delenv("SELF_HOSTED_API_KEY")
    client = build_client("live", replay_dirs=[])
    assert client.chain_names == ["self-hosted:openai/gpt-oss-20b"]     # GROQ_API_KEY is the vLLM token, no backup


def test_without_a_self_hosted_host_the_chain_is_unchanged(backends, monkeypatch):
    monkeypatch.delenv("GROQ_BASE_URL")
    monkeypatch.delenv("SELF_HOSTED_API_KEY")
    client = build_client("live", replay_dirs=[])
    assert client.chain_names == ["groq:openai/gpt-oss-20b"]     # the Render setup: hosted only
    assert client_mod.ChainStep("primary", "groq", "m", None, 1).endpoint == "groq"


def test_render_style_setup_has_no_self_hosted_step(backends, monkeypatch):
    """Render sets GROQ_API_KEY only. Nothing about its chain changes."""
    monkeypatch.delenv("GROQ_BASE_URL")
    monkeypatch.delenv("SELF_HOSTED_API_KEY")
    monkeypatch.setenv("GROQ_API_KEY", "hosted-key")
    monkeypatch.delenv("EXTRACT_MODEL")
    monkeypatch.setenv("GROQ_FALLBACK_ENABLED", "true")
    client = build_client("live", replay_dirs=[])
    assert client.chain_names == ["groq:openai/gpt-oss-120b", "groq:openai/gpt-oss-20b"]
