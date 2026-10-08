"""App harness: tmp file DB, FrozenClock, sequential ids, worker off, LLM chain failing everywhere, so
any test that silently reaches a provider shows up as path 'rules'."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from tests.conftest import T0
from wasel.clock import FrozenClock
from wasel.ids import SeqIds
from wasel.llm.client import build_client
from wasel.main import create_app
from wasel.settings import Settings

VID_A = str(uuid.UUID(int=0xA, version=4))
VID_B = str(uuid.UUID(int=0xB, version=4))


def make_client(tmp_path, mode="dev", llm_mode="fail_all", **over):
    settings = Settings(app_mode=mode, db_path=str(tmp_path / "app.db"), worker_enabled=False, demo_mode=True,
                        admin_token="x" * 24, llm_mode=llm_mode,
                        **{"allowed_hosts": "testserver", **over})
    clock = FrozenClock(T0)
    app = create_app(settings, clock=clock, llm=build_client(llm_mode), ids=SeqIds(), worker_enabled=False)
    return TestClient(app), app.state.core, clock


@pytest.fixture
def dev(tmp_path):
    c, core, clock = make_client(tmp_path, "dev")
    with c:
        yield c, core, clock


@pytest.fixture
def public(tmp_path):
    c, core, clock = make_client(tmp_path, "public")
    with c:
        yield c, core, clock


def settle(core, clock, seconds=5):
    clock.advance(seconds)
    return core.drain()


def hero_id(client, headers=None):
    orders = client.get("/api/orders", headers=headers or {}).json()["orders"]
    return next(o for o in orders if o["seed_key"] == "hero" and o["is_seeded"])
