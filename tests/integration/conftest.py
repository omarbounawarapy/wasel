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


# ---------------------------------------------------------------- contract: every status seen is declared
def _template_regex(path: str):
    import re
    return re.compile("^" + re.sub(r"\{[^}/]+\}", "[^/]+", path) + "$")


@pytest.fixture(autouse=True)
def _every_status_is_declared(monkeypatch):
    """Fail the test that sees a status under /api that the OpenAPI document does not declare for that operation."""
    original = TestClient.request

    def checked(self, method, url, *a, **kw):
        resp = original(self, method, url, *a, **kw)
        path = str(resp.request.url.path)
        if path.startswith("/api/") and not getattr(self.app, "_contract_skip", False):
            doc = self.app.openapi()
            for template, ops in doc["paths"].items():
                if _template_regex(template).match(path) and method.lower() in ops:
                    declared = ops[method.lower()]["responses"]
                    ok = str(resp.status_code) in declared or str(resp.status_code)[0] == "2" and "default" in declared
                    assert ok, f"{method.upper()} {template} answered {resp.status_code}, declared {sorted(declared)}"
                    break
        return resp
    monkeypatch.setattr(TestClient, "request", checked)
    yield
