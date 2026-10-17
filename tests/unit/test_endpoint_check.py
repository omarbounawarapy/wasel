"""scripts/ops/endpoint_check.py: one endpoint, the real extraction request, no backup steps."""
import sys
from pathlib import Path

import pytest

from wasel.llm.base import CallMeta, SchemaRejected
from wasel.llm.routes import ADAPTERS

ROOT = Path(__file__).resolve().parents[2]
ANSWER = (ROOT / "tests" / "fixtures" / "hero" / "v1.json").read_text(encoding="utf-8")
NAMES = ("AMD_TOKENFACTORY_API_KEY", "AMD_TOKENFACTORY_BASE_URL", "AMD_TOKENFACTORY_MODEL", "GROQ_API_KEY",
         "GROQ_BASE_URL", "SELF_HOSTED_API_KEY", "GEMINI_API_KEY")


@pytest.fixture
def check(monkeypatch):
    for k in NAMES:
        monkeypatch.delenv(k, raising=False)
    sys.path.insert(0, str(ROOT / "scripts" / "ops"))
    try:
        import endpoint_check
        yield endpoint_check
    finally:
        sys.path.remove(str(ROOT / "scripts" / "ops"))


def _token_factory(monkeypatch, answer):
    monkeypatch.setenv("AMD_TOKENFACTORY_API_KEY", "tf-key")
    monkeypatch.setenv("AMD_TOKENFACTORY_BASE_URL", "https://tokenfactory.test/v1")
    monkeypatch.setenv("AMD_TOKENFACTORY_MODEL", "amd/some-model")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")       # a backup that the check must not use

    class Backend:
        def complete_json(self, task, model, user, timeout_s):
            return answer(model)
    monkeypatch.setitem(ADAPTERS, "openai-compatible", lambda ep, cfg: Backend())


def test_an_inactive_endpoint_names_its_missing_variables(check, capsys):
    assert check.main(["amd-tokenfactory"]) == 2
    assert "AMD_TOKENFACTORY_MODEL" in capsys.readouterr().err


def test_answers_on_path_llm_pass(check, monkeypatch, capsys):
    _token_factory(monkeypatch, lambda m: (ANSWER, CallMeta(provider="groq", model=m, latency_ms=1)))
    assert check.main(["amd-tokenfactory", "--cases", "2"]) == 0
    out = capsys.readouterr().out
    assert "amd-tokenfactory:amd/some-model" in out and "2/2 cases answered" in out


def test_a_rejected_request_fails_and_shows_the_provider_error(check, monkeypatch, capsys):
    def reject(m):
        raise SchemaRejected('{"error":"response_format not supported"}')
    _token_factory(monkeypatch, reject)
    assert check.main(["amd-tokenfactory", "--cases", "1"]) == 1
    out = capsys.readouterr().out
    assert "path=rules" in out and "response_format not supported" in out
