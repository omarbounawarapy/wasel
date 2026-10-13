"""The LLM layer's configuration, read once.

`LLMSettings.from_env()` is the only place that reads the LLM environment names (GROQ_*, SELF_HOSTED_API_KEY,
EXTRACT_MODEL, FALLBACK_MODEL, GEMINI_*, LLM_MODE, LLM_DEADLINE_S, LLM_SERVING_LABEL, LLM_REPLAY_DIR). `build_client`
and the health payload use the object instead of calling `env()` themselves. It changes no behaviour: the names, the
defaults and the meaning of each value are the ones the code had before. Bad values raise `LLMConfigError` at startup with the name of the setting.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from wasel.envutil import env
from wasel.paths import ROOT

DEFAULT_PRIMARY = "openai/gpt-oss-120b"
DEFAULT_FALLBACK = "openai/gpt-oss-20b"
_BOOLS = {"true": True, "1": True, "yes": True, "on": True, "false": False, "0": False, "no": False, "off": False}


class LLMConfigError(ValueError):
    """An LLM setting has a value the layer cannot use."""


def _flag(name: str, default: str) -> bool:
    raw = (env(name, default) or default).strip().lower()
    if raw not in _BOOLS:
        raise LLMConfigError(f"{name}={raw!r}: expected true or false")
    return _BOOLS[raw]


def _seconds(name: str, default: float) -> float:
    raw = env(name)
    if raw is None:
        return float(default)
    try:
        value = float(raw)
    except ValueError:
        raise LLMConfigError(f"{name}={raw!r}: expected a number of seconds") from None
    if value <= 0:
        raise LLMConfigError(f"{name}={raw!r}: must be greater than 0")
    return value


@dataclass(frozen=True)
class LLMSettings:
    """Everything the LLM layer takes from the environment, with the config/llm.yaml routing defaults applied."""
    mode: str
    deadline_s: float
    cache_size: int
    primary_model: str               # EXTRACT_MODEL, else routing.primary
    fallback_model: str              # FALLBACK_MODEL, else routing.fallback_model
    fallback_enabled: bool           # GROQ_FALLBACK_ENABLED; false if the provider's buckets are per org
    groq_key: str | None             # GROQ_API_KEY
    self_hosted_key: str | None      # SELF_HOSTED_API_KEY
    base_url: str | None             # GROQ_BASE_URL: a self-hosted OpenAI-compatible host
    serving_label: str | None        # LLM_SERVING_LABEL, only meaningful with base_url
    gemini_key: str | None
    gemini_model: str | None
    gemini_enabled: bool
    probe_file: str
    replay_dir: Path

    @classmethod
    def from_env(cls, mode: str | None = None, routing: dict | None = None,
                 deadline_s: float = 20.0) -> LLMSettings:
        """Read the environment. `mode` overrides LLM_MODE; `routing` is the `routing:` block of config/llm.yaml."""
        routing = routing or {}
        base_url = env("GROQ_BASE_URL")
        if base_url:
            parsed = urlparse(base_url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise LLMConfigError(f"GROQ_BASE_URL={base_url!r}: expected an http(s) URL with a host")
        try:
            cache_size = int(routing.get("cache_size", 512))
        except (TypeError, ValueError):
            raise LLMConfigError(f"routing.cache_size={routing.get('cache_size')!r}: expected an integer") from None
        return cls(
            mode=mode or env("LLM_MODE", "live"),
            deadline_s=_seconds("LLM_DEADLINE_S", float(routing.get("deadline_s", deadline_s))),
            cache_size=cache_size,
            primary_model=env("EXTRACT_MODEL", routing.get("primary", DEFAULT_PRIMARY)),
            fallback_model=env("FALLBACK_MODEL", routing.get("fallback_model", DEFAULT_FALLBACK)),
            fallback_enabled=_flag("GROQ_FALLBACK_ENABLED", "true"),
            groq_key=env("GROQ_API_KEY"), self_hosted_key=env("SELF_HOSTED_API_KEY"),
            base_url=base_url, serving_label=env("LLM_SERVING_LABEL"),
            gemini_key=env("GEMINI_API_KEY"), gemini_model=env("GEMINI_MODEL"),
            gemini_enabled=_flag("GEMINI_ENABLED", "false"),
            probe_file=env("PROBE_FILE", "config/probe.json"),
            replay_dir=Path(env("LLM_REPLAY_DIR", str(ROOT / "data" / "llm_replay"))),
        )

    @property
    def self_hosted(self) -> bool:
        return bool(self.base_url)

    @property
    def endpoint(self) -> str:
        """Name of the Groq-protocol steps' endpoint: 'self-hosted' when GROQ_BASE_URL is set, else 'groq'."""
        return "self-hosted" if self.self_hosted else "groq"

    @property
    def primary_key(self) -> str | None:
        """Token of the Groq-protocol steps. With a self-hosted host and its own token, GROQ_API_KEY is the backup."""
        if self.self_hosted and self.self_hosted_key:
            return self.self_hosted_key
        return self.groq_key

    @property
    def backup_key(self) -> str | None:
        """The hosted Groq key behind a self-hosted host, or None when GROQ_API_KEY is the host's own token."""
        return self.groq_key if self.self_hosted and self.self_hosted_key else None

    @property
    def serving_host(self) -> str | None:
        return urlparse(self.base_url).hostname if self.base_url else None

    @property
    def label(self) -> str | None:
        """The serving label, only shown for a self-hosted host (never for the hosted Groq API)."""
        return self.serving_label if self.serving_host else None

    @property
    def gemini_active(self) -> bool:
        return bool(self.gemini_key and self.gemini_model and self.gemini_enabled)
