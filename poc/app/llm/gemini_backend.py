"""Gemini extraction fallback, Stage A (M-8): Gemini's OpenAI-compat endpoint through the same backend,
repair, Pydantic and evidence gate as Groq (02 §6). Disabled unless GEMINI_API_KEY and GEMINI_MODEL
are set. [VERIFY] base URL, free-tier model id, schema style (probe), data-use terms."""
from __future__ import annotations

import json
from functools import partial
from pathlib import Path

import httpx

from app.llm.groq_backend import OpenAICompatBackend
from app.llm.schema_gemini import to_gemini_compat_schema

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_PROBE = {"schema_style": {"nullable": "type_array", "strip_additional": False, "property_ordering": False},
                 "max_tokens_param": "max_completion_tokens", "seed_ok": False, "extra": {}}


def load_probe(path: str | Path | None) -> dict:
    if path and Path(path).exists():
        return {**DEFAULT_PROBE, **json.loads(Path(path).read_text())}
    return DEFAULT_PROBE


def gemini_backend(api_key: str, model: str, probe: dict | None = None,
                   base_url: str = GEMINI_BASE_URL, transport: httpx.BaseTransport | None = None
                   ) -> OpenAICompatBackend:
    probe = probe or DEFAULT_PROBE
    return OpenAICompatBackend(
        "gemini", base_url, api_key,
        schema_adapter=partial(to_gemini_compat_schema, **probe["schema_style"]),
        extra={model: probe.get("extra", {})}, max_tokens_param=probe["max_tokens_param"],
        send_seed=probe["seed_ok"], transport=transport)
