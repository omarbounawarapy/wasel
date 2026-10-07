"""Shared fixtures. Offline, keyless, deterministic: every test runs with no network."""
from __future__ import annotations

import json
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wasel.clock import FrozenClock
from wasel.contracts import CustomerHistory, ScoreInput, StructuredFields, WindowMessage
from wasel.scoring.config import load_config
from wasel.settings import Settings

# Tests never read a developer's .env (auto-send, webhook, DRAFT_LLM, keys...): only the process env, which
# `make test` sets, and each test's explicit Settings(...). Same results on every laptop as in CI (no .env).
Settings.model_config["env_file"] = None

T0 = datetime(2026, 9, 27, 10, 0, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _no_network(monkeypatch, request):
    if request.node.get_closest_marker("live"):
        return
    real = socket.socket.connect

    def guard(self, addr, *a, **k):
        if isinstance(addr, str) or addr[0] in ("127.0.0.1", "::1", "localhost"):
            return real(self, addr, *a, **k)
        raise RuntimeError(f"network call to {addr} in an offline test: use ReplayBackend")
    monkeypatch.setattr(socket.socket, "connect", guard)


@pytest.fixture(scope="session")
def config():
    return load_config()


@pytest.fixture
def clock():
    return FrozenClock(T0)


def customer_msg(i: int, text: str, kind: str = "text") -> WindowMessage:
    return WindowMessage(f"m{i}", "inbound", "customer", "paste", kind, text if kind == "text" else None, None,
                         None, None, kind == "location", T0.replace(second=i))


def seller_msg(i: int, canonical: str, template_id: str = "T_CONFIRM") -> WindowMessage:
    return WindowMessage(f"m{i}", "outbound", "ai", "dashboard", "text", canonical, canonical, template_id, None,
                         False, T0.replace(second=i))


def make_input(texts, *, seller_at: int | None = None, seller_text: str = "Vous confirmez, oui ou non ?",
               template_id: str = "T_CONFIRM", completed: int = 0, refusals: int = 0,
               structured: StructuredFields | None = None, trigger: str = "initial", prior=None,
               sandbox_id: str | None = None) -> ScoreInput:
    msgs, i = [], 0
    for j, t in enumerate(texts):
        if seller_at is not None and j == seller_at:
            msgs.append(seller_msg(i, seller_text, template_id))
            i += 1
        msgs.append(customer_msg(i, t) if t != "<pin>" else customer_msg(i, "", "location"))
        i += 1
    return ScoreInput("ord_test", sandbox_id, "paste", trigger, msgs, structured or StructuredFields(),
                      CustomerHistory(completed, refusals), prior, T0)


def envelope(render: str, extraction: dict | str, *, source: str = "hand_crafted", provider: str = "groq",
             model: str = "openai/gpt-oss-120b", status: int = 200) -> dict:
    from wasel.llm.client import replay_key
    content = extraction if isinstance(extraction, str) else json.dumps(extraction, ensure_ascii=False)
    return {"meta": {"source": source, "provider": provider, "model": model, "prompt_version": "extract-v1",
                     "recorded_at": "2026-09-26"},
            "key": replay_key(render), "window": render, "status": status, "headers": {},
            "response": {"choices": [{"finish_reason": "stop", "message": {"content": content}}],
                         "usage": {"prompt_tokens": 2800, "completion_tokens": 120}}}


@pytest.fixture
def replay_dir(tmp_path):
    d = tmp_path / "replay"
    d.mkdir()

    def add(name: str, render: str, extraction, **kw) -> Path:
        p = d / f"{name}.json"
        p.write_text(json.dumps(envelope(render, extraction, **kw), ensure_ascii=False), encoding="utf-8")
        return p
    add.dir = d
    return add


class CountingMeter:
    def __init__(self, cap: int | None = None):
        self.cap, self.calls = cap, 0

    def allow(self, role, sandbox_id, now):
        if self.cap is not None and self.calls >= self.cap:
            return "global_cap"
        self.calls += 1
        return "ok"


@pytest.fixture
def meter():
    return CountingMeter()
