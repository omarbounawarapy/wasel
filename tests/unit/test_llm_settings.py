"""LLMSettings: same names and meanings as before, clear errors."""
import pytest

from wasel.llm.settings import LLMConfigError, LLMSettings

NAMES = ("GROQ_BASE_URL", "GROQ_API_KEY", "SELF_HOSTED_API_KEY", "EXTRACT_MODEL", "FALLBACK_MODEL",
         "GROQ_FALLBACK_ENABLED", "GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_ENABLED", "LLM_DEADLINE_S",
         "LLM_SERVING_LABEL", "LLM_MODE")


@pytest.fixture
def clean(monkeypatch):
    for k in NAMES:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


def test_defaults_come_from_routing(clean):
    c = LLMSettings.from_env(routing={"primary": "p", "fallback_model": "f", "deadline_s": 7, "cache_size": 9})
    assert (c.mode, c.primary_model, c.fallback_model, c.deadline_s, c.cache_size) == ("live", "p", "f", 7.0, 9)
    assert c.endpoint == "groq" and c.primary_key is None and c.backup_key is None and not c.gemini_active


def test_env_overrides_routing_and_mode_argument_wins(clean):
    clean.setenv("EXTRACT_MODEL", "m1")
    clean.setenv("LLM_MODE", "replay")
    clean.setenv("LLM_DEADLINE_S", "3.5")
    c = LLMSettings.from_env("fail_all", routing={"primary": "p"})
    assert (c.mode, c.primary_model, c.deadline_s) == ("fail_all", "m1", 3.5)


def test_self_hosted_with_its_own_token_makes_groq_key_the_backup(clean):
    clean.setenv("GROQ_BASE_URL", "http://10.0.0.5:8001/v1")
    clean.setenv("GROQ_API_KEY", "hosted")
    clean.setenv("SELF_HOSTED_API_KEY", "own")
    clean.setenv("LLM_SERVING_LABEL", "AMD MI300X")
    c = LLMSettings.from_env()
    assert (c.endpoint, c.primary_key, c.backup_key) == ("self-hosted", "own", "hosted")
    assert (c.serving_host, c.label) == ("10.0.0.5", "AMD MI300X")


def test_self_hosted_without_own_token_keeps_the_old_meaning_of_groq_key(clean):
    clean.setenv("GROQ_BASE_URL", "http://10.0.0.5:8001/v1")
    clean.setenv("GROQ_API_KEY", "token")
    c = LLMSettings.from_env()
    assert (c.primary_key, c.backup_key) == ("token", None)


def test_label_is_never_shown_for_the_hosted_api(clean):
    clean.setenv("LLM_SERVING_LABEL", "AMD")
    assert LLMSettings.from_env().label is None


def test_gemini_needs_key_model_and_the_flag(clean):
    clean.setenv("GEMINI_API_KEY", "k")
    clean.setenv("GEMINI_MODEL", "g")
    assert not LLMSettings.from_env().gemini_active
    clean.setenv("GEMINI_ENABLED", "true")
    assert LLMSettings.from_env().gemini_active


@pytest.mark.parametrize("name, value", [("GROQ_BASE_URL", "not a url"), ("LLM_DEADLINE_S", "soon"),
                                         ("LLM_DEADLINE_S", "0"), ("GROQ_FALLBACK_ENABLED", "maybe")])
def test_bad_values_name_the_setting(clean, name, value):
    clean.setenv(name, value)
    with pytest.raises(LLMConfigError, match=name):
        LLMSettings.from_env()
