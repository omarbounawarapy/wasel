"""llm_usage and extraction_runs record which endpoint answered, an old (version 1)
database is migrated by one ADD COLUMN, and health reports observed calls apart from the configured chain."""
from __future__ import annotations

import sqlite3

from tests.conftest import T0
from tests.integration.conftest import make_client
from wasel.contracts import UsageRecord
from wasel.db import repo
from wasel.db.conn import SCHEMA_VERSION, tx
from wasel.llm.base import CallMeta, ProviderDown, TaskSpec
from wasel.llm.client import ChainClient, ChainStep
from wasel.monitor import llm_ops

TASK = TaskSpec("extract", "s", {}, "sys", (), "v1", 10, 0.0, None, False)


class _Ok:
    def complete_json(self, task, model, user, timeout_s):
        return "{}", CallMeta("groq", model, 5, 1, None, 1)


class _Down:
    def complete_json(self, task, model, user, timeout_s):
        raise ProviderDown("down")


def _run(steps):
    return ChainClient(steps, deadline_s=5.0).extract(TASK, "hi", parse=lambda s: s, meter=None, sandbox_id=None,
                                                      now=T0)


def test_usage_records_carry_the_endpoint_that_was_called():
    res = _run([ChainStep("primary", "groq", "m", _Down(), 1, endpoint="self-hosted"),
                ChainStep("fallback_provider", "groq", "m", _Ok(), 1, endpoint="groq")])
    assert [(u.endpoint, u.outcome) for u in res.usage] == [("self-hosted", "down"), ("groq", "ok")]
    assert res.endpoint == "groq"


def test_insert_usage_stores_endpoint_and_old_rows_read_as_not_recorded(tmp_path):
    c, core, _ = make_client(tmp_path)
    with c:
        conn = core.conn()
        with tx(conn):
            repo.insert_usage(conn, UsageRecord(T0, "extract", "groq", "m", "ok", 1, 1, 9, "amd-host"),
                              sandbox_id=None, order_id=None)
            repo.insert_usage(conn, UsageRecord(T0, "extract", "groq", "m", "ok", 1, 1, 9),
                              sandbox_id=None, order_id=None)
        got = [r["endpoint"] for r in conn.execute("SELECT endpoint FROM llm_usage ORDER BY usage_id DESC LIMIT 2")]
        assert got == [None, "amd-host"]
        by = llm_ops(conn, 100)["by_endpoint"]
        assert by["amd-host"] == 1 and by["not recorded"] >= 1


def test_version_1_database_gets_the_column_and_keeps_its_rows(tmp_path):
    c, core, _ = make_client(tmp_path)
    with c:
        conn = core.conn()
        with tx(conn):
            repo.insert_usage(conn, UsageRecord(T0, "extract", "groq", "m", "ok", 1, 1, 9),
                              sandbox_id=None, order_id=None)
        before = conn.execute("SELECT COUNT(*) FROM llm_usage").fetchone()[0]
        runs = conn.execute("SELECT COUNT(*) FROM extraction_runs").fetchone()[0]
    raw = sqlite3.connect(tmp_path / "app.db")                       # make it look like a version 1 file
    raw.execute("ALTER TABLE llm_usage DROP COLUMN endpoint")
    raw.execute("ALTER TABLE extraction_runs DROP COLUMN endpoint")
    raw.execute("PRAGMA user_version = 1")
    raw.commit()
    raw.close()
    c2, core2, _ = make_client(tmp_path)
    with c2:
        conn = core2.conn()
        for table in ("llm_usage", "extraction_runs"):
            assert any(r["name"] == "endpoint" for r in conn.execute(f"PRAGMA table_info({table})"))
        assert conn.execute("SELECT COUNT(*) FROM llm_usage").fetchone()[0] >= before
        assert conn.execute("SELECT COUNT(*) FROM extraction_runs").fetchone()[0] >= runs
        assert conn.execute("SELECT COUNT(*) FROM llm_usage WHERE endpoint IS NOT NULL").fetchone()[0] == 0
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert c2.get("/api/health").json()["llm"]["observed"] == []     # nothing recorded is not "down"


def test_health_observed_is_separate_from_the_configured_chain(tmp_path):
    c, core, _ = make_client(tmp_path)
    with c:
        core.llm = ChainClient([ChainStep("primary", "groq", "m", _Down(), 1, endpoint="self-hosted")])
        _run_through = core.llm.extract(TASK, "x", parse=lambda s: s, meter=None, sandbox_id=None, now=core.clock.now())
        conn = core.conn()
        with tx(conn):
            for u in _run_through.usage:
                repo.insert_usage(conn, u, sandbox_id=None, order_id=None)
        llm = c.get("/api/health").json()["llm"]
        assert llm["chain_extract"] == ["self-hosted:m"]
        (o,) = llm["observed"]
        assert o["endpoint"] == "self-hosted" and o["last_outcome"] == "down" and o["last_ok_at"] is None
        assert o["breaker_open"] is True and llm["last_call_at"] == o["last_call_at"]
