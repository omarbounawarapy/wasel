"""Gemini extraction fallback: Gemini's OpenAI-compat endpoint through the same backend,
repair, Pydantic and evidence gate as Groq. Disabled unless GEMINI_API_KEY and GEMINI_MODEL
are set."""
from __future__ import annotations

import json
from functools import partial
from pathlib import Path

import httpx

from wasel.llm.groq_backend import OpenAICompatBackend
from wasel.llm.schema_gemini import to_gemini_compat_schema

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_PROBE = {"schema_style": {"nullable": "type_array", "strip_additional": False, "property_ordering": False},
                 "max_tokens_param": "max_completion_tokens", "seed_ok": False, "extra": {}}


def load_probe(path: str | Path | None) -> dict:
    """Read the provider probe file (config/probe.json by default) over DEFAULT_PROBE; the defaults when the file is
    missing.
    """
    if path and Path(path).exists():
        return {**DEFAULT_PROBE, **json.loads(Path(path).read_text())}
    return DEFAULT_PROBE


def gemini_backend(api_key: str, model: str, probe: dict | None = None,
                   base_url: str = GEMINI_BASE_URL, transport: httpx.BaseTransport | None = None
                   ) -> OpenAICompatBackend:
    """Backend for Gemini's OpenAI-compatible endpoint.

    `probe` (see load_probe) says how this account's model wants the schema written, which token-limit field it takes
    and whether it accepts a seed.
    """
    probe = probe or DEFAULT_PROBE
    return OpenAICompatBackend(
        "gemini", base_url, api_key,
        schema_adapter=partial(to_gemini_compat_schema, **probe["schema_style"]),
        extra={model: probe.get("extra", {})}, max_tokens_param=probe["max_tokens_param"],
        send_seed=probe["seed_ok"], transport=transport)
