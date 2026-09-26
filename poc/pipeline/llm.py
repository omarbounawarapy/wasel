"""Minimal JSON-mode LLM client for free-tier Gemini or Groq. No SDKs: one HTTP call each.

`get_client()` returns None when no provider/key is configured; callers then use the offline path.
Tests inject a fake client with the same `complete_json(system, user) -> str` method.
"""
import json
import os
from typing import Protocol

import requests

from . import config


class LLMError(RuntimeError):
    pass


class LLMClient(Protocol):
    model: str

    def complete_json(self, system: str, user: str, temperature: float = 0.0) -> str: ...


class GeminiClient:
    def __init__(self, api_key: str, model: str = config.GEMINI_MODEL):
        self.api_key, self.model = api_key, model

    def complete_json(self, system, user, temperature=0.0):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"},
        }
        try:
            r = requests.post(url, params={"key": self.api_key}, json=body, timeout=config.LLM_TIMEOUT_S)
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except (requests.RequestException, KeyError, IndexError, ValueError) as e:
            raise LLMError(f"gemini: {e}") from e


class GroqClient:
    def __init__(self, api_key: str, model: str = config.GROQ_MODEL):
        self.api_key, self.model = api_key, model

    def complete_json(self, system, user, temperature=0.0):
        body = {
            "model": self.model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        }
        try:
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body, timeout=config.LLM_TIMEOUT_S,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, ValueError) as e:
            raise LLMError(f"groq: {e}") from e


def _secret(name: str) -> str:
    val = os.environ.get(name, "")
    if val:
        return val
    try:  # Streamlit Cloud secrets, when running under Streamlit
        import streamlit as st
        return str(st.secrets.get(name, ""))
    except Exception:
        return ""


def get_client() -> LLMClient | None:
    provider = config.LLM_PROVIDER or _secret("LLM_PROVIDER").lower()
    if provider == "gemini" and _secret("GEMINI_API_KEY"):
        return GeminiClient(_secret("GEMINI_API_KEY"))
    if provider == "groq" and _secret("GROQ_API_KEY"):
        return GroqClient(_secret("GROQ_API_KEY"))
    return None


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw[raw.find("{"):]
    return json.loads(raw)
