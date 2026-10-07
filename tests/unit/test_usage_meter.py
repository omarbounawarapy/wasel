"""The real SqliteUsageMeter on an in-memory database: every cap has a failing case."""
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest

from wasel.clock import utc_iso
from wasel.db.conn import create_schema
from wasel.db.usage import SqliteUsageMeter

NOW = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    create_schema(c)
    return c


def add(conn, ts=NOW, sandbox_id=None, model="m1", tokens=0):
    conn.execute("INSERT INTO llm_usage (ts, day, sandbox_id, role, provider, model, outcome, tokens_in,"
                 " tokens_out, latency_ms) VALUES (?,?,?,?,?,?,?,?,?,?)",
                 (utc_iso(ts), ts.strftime("%Y-%m-%d"), sandbox_id, "extract", "groq", model, "ok", tokens, 0, 1))


def meter(conn, **kw):
    kw.setdefault("daily_cap", None)
    kw.setdefault("public", True)
    return SqliteUsageMeter(conn, **kw)


def test_allows_under_cap(conn):
    assert meter(conn, daily_cap=3).allow("extract", "v1", NOW) == "ok"


def test_global_cap_at_daily_cap(conn):
    for _ in range(3):
        add(conn)
    assert meter(conn, daily_cap=3).allow("extract", None, NOW) == "global_cap"
    assert meter(conn, daily_cap=4).allow("extract", None, NOW) == "ok"


def test_zero_cap_disables_calls(conn):
    assert meter(conn, daily_cap=0).allow("extract", None, NOW) == "global_cap"


def test_reservations_count_before_persisting(conn):
    m = meter(conn, daily_cap=3)
    assert [m.allow("extract", None, NOW) for _ in range(4)] == ["ok", "ok", "ok", "global_cap"]


def test_settle_clears_reservations(conn):
    m = meter(conn, daily_cap=2)
    assert m.allow("extract", None, NOW) == m.allow("extract", None, NOW) == "ok"
    assert m.allow("extract", None, NOW) == "global_cap"
    m.settle()
    assert m.allow("extract", None, NOW) == "ok"


def test_visitor_cap_10min(conn):
    for i in range(6):
        add(conn, ts=NOW - timedelta(minutes=i), sandbox_id="v1")
    m = meter(conn)
    assert m.allow("extract", "v1", NOW) == "visitor_cap"
    assert m.allow("extract", "v2", NOW) == "ok"
    assert m.allow("extract", None, NOW) == "ok"


def test_visitor_10min_window_edge(conn):
    for _ in range(5):
        add(conn, sandbox_id="v1")
    add(conn, ts=NOW - timedelta(minutes=10, seconds=1), sandbox_id="v1")
    assert meter(conn).allow("extract", "v1", NOW) == "ok"
    add(conn, ts=NOW - timedelta(minutes=10), sandbox_id="v1")
    assert meter(conn).allow("extract", "v1", NOW) == "visitor_cap"


def test_visitor_cap_day(conn):
    for i in range(20):
        add(conn, ts=NOW.replace(hour=1, minute=i), sandbox_id="v1")
    m = meter(conn)
    assert m.allow("extract", "v1", NOW) == "visitor_cap"
    assert m.allow("extract", "v2", NOW) == "ok"
    assert m.allow("extract", None, NOW) == "ok"


def test_visitor_cap_day_just_under(conn):
    for i in range(19):
        add(conn, ts=NOW.replace(hour=1, minute=i), sandbox_id="v1")
    assert meter(conn).allow("extract", "v1", NOW) == "ok"


def test_visitor_reservations_count(conn):
    m = meter(conn)
    assert [m.allow("extract", "v1", NOW) for _ in range(7)] == ["ok"] * 6 + ["visitor_cap"]
    assert m.allow("extract", "v2", NOW) == "ok"


def test_visitor_caps_off_outside_public(conn):
    for _ in range(30):
        add(conn, sandbox_id="v1")
    assert meter(conn, public=False).allow("extract", "v1", NOW) == "ok"


def test_token_guard_trips_at_limit(conn):
    add(conn, tokens=99)
    assert meter(conn, tokens_per_model_day=100).allow("extract", None, NOW) == "ok"
    add(conn, tokens=1)
    assert meter(conn, tokens_per_model_day=100).allow("extract", None, NOW) == "global_cap"


def test_token_guard_is_per_model_and_counts_both_directions(conn):
    add(conn, model="a", tokens=60)
    add(conn, model="b", tokens=60)
    assert meter(conn, tokens_per_model_day=100).allow("extract", None, NOW) == "ok"
    conn.execute("UPDATE llm_usage SET tokens_out=40 WHERE model='a'")
    assert meter(conn, tokens_per_model_day=100).allow("extract", None, NOW) == "global_cap"


def test_token_guard_default_by_mode(conn):
    assert meter(conn, public=True).tokens_per_model_day == 120_000
    assert meter(conn, public=False).tokens_per_model_day is None
    assert meter(conn, tokens_per_model_day=5).tokens_per_model_day == 5


def test_day_rolls_over_at_utc_midnight(conn):
    late = datetime(2026, 5, 1, 23, 59, tzinfo=UTC)
    for _ in range(2):
        add(conn, ts=late, tokens=200)
    m = meter(conn, daily_cap=2, tokens_per_model_day=100)
    assert m.allow("extract", None, late + timedelta(seconds=30)) == "global_cap"
    assert m.allow("extract", None, late + timedelta(minutes=1)) == "ok"
    assert m.calls_today(late + timedelta(minutes=1)) == 0
