"""`.env` reaches the LLM layer (not only Settings), and LLM_MODE=replay fails clearly without fixtures."""
import pytest

from wasel import envutil
from wasel.llm.client import build_client
from wasel.settings import Settings


@pytest.fixture
def dotenv(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    monkeypatch.setitem(Settings.model_config, "env_file", str(f))
    envutil._dotenv.cache_clear()
    yield f
    envutil._dotenv.cache_clear()


def test_env_falls_back_to_dotenv_but_process_env_wins(dotenv, monkeypatch):
    dotenv.write_text("GROQ_API_KEY=from-file\nEXTRACT_MODEL=file/model\n")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("EXTRACT_MODEL", "env/model")
    assert envutil.env("GROQ_API_KEY") == "from-file"
    assert envutil.env("EXTRACT_MODEL") == "env/model"
    assert envutil.env("NOPE", "d") == "d"


def test_chain_is_built_from_dotenv(dotenv, monkeypatch):
    dotenv.write_text("GROQ_API_KEY=k\nEXTRACT_MODEL=file/model\nGROQ_FALLBACK_ENABLED=false\n")
    for v in ("GROQ_API_KEY", "EXTRACT_MODEL", "GROQ_FALLBACK_ENABLED"):
        monkeypatch.delenv(v, raising=False)
    assert build_client("live").chain_names == ["groq:file/model"]


def test_tests_ignore_dotenv_when_env_file_is_none(monkeypatch):
    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert build_client("live").chain_names == []


def test_replay_without_fixtures_is_a_clear_error(tmp_path):
    with pytest.raises(ValueError, match="LLM_REPLAY_DIR"):
        build_client("replay", replay_dirs=[tmp_path / "missing"])
