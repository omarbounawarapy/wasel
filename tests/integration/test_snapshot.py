"""The SQLite snapshot boundary used on Cloudflare Containers: restore at boot, save while running and at shutdown,
and no silent fallback to an empty database when the store is unhealthy."""
from __future__ import annotations

import httpx
import pytest

from tests.conftest import T0
from tests.integration.conftest import make_client
from wasel.clock import FrozenClock
from wasel.db import snapshot as S
from wasel.db.conn import connect, create_schema


def _url(tmp_path):
    return (tmp_path / "store" / "wasel.sqlite").resolve().as_uri()


def _orders(core):
    return core.conn().execute("SELECT COUNT(*) FROM orders").fetchone()[0]


def test_store_from_url_schemes(tmp_path):
    assert S.store_from_url("") is None
    assert isinstance(S.store_from_url(_url(tmp_path)), S.FileSnapshotStore)
    assert isinstance(S.store_from_url("http://state.wasel.internal/snapshot"), S.HttpSnapshotStore)
    with pytest.raises(ValueError, match="SNAPSHOT_URL"):
        S.store_from_url("ftp://x/y")


def test_state_survives_a_disk_wipe(tmp_path):
    over = dict(snapshot_url=_url(tmp_path), seed_on_boot="if_empty")
    first = tmp_path / "a"
    first.mkdir()
    c, core, clock = make_client(first, "dev", **over)
    with c:
        seeded = _orders(core)
        assert seeded > 0
        core.conn().execute("UPDATE orders SET product_name='SURVIVED' WHERE order_id=(SELECT order_id FROM orders LIMIT 1)")
    # leaving the context ran the shutdown snapshot; a brand-new disk must come back with the same state
    second = tmp_path / "b"
    second.mkdir()
    c2, core2, _ = make_client(second, "dev", **over)
    with c2:
        assert _orders(core2) == seeded
        assert core2.conn().execute("SELECT COUNT(*) FROM orders WHERE product_name='SURVIVED'").fetchone()[0] == 1
        assert c2.get("/api/health").json()["status"] in ("ok", "degraded")


def test_first_boot_without_snapshot_seeds_and_saves(tmp_path):
    c, core, clock = make_client(tmp_path, "dev", snapshot_url=_url(tmp_path), seed_on_boot="if_empty")
    with c:
        assert _orders(core) > 0
    assert S.FileSnapshotStore(tmp_path / "store" / "wasel.sqlite").load() is not None


def test_always_seed_mode_ignores_the_store(tmp_path):
    c, core, _ = make_client(tmp_path, "public", snapshot_url=_url(tmp_path))     # public -> seed 'always'
    with c:
        assert core.snapshotter is None
    assert not (tmp_path / "store").exists()


def test_corrupt_snapshot_stops_boot_and_is_not_overwritten(tmp_path):
    store = tmp_path / "store" / "wasel.sqlite"
    store.parent.mkdir()
    store.write_bytes(b"not a database")
    c, _, _ = make_client(tmp_path, "dev", snapshot_url=_url(tmp_path), seed_on_boot="if_empty")
    with pytest.raises(S.SnapshotError), c:
        pass
    assert store.read_bytes() == b"not a database"


def test_foreign_sqlite_snapshot_is_rejected(tmp_path):
    import sqlite3
    m = sqlite3.connect(":memory:")
    m.execute("CREATE TABLE other(x)")
    with pytest.raises(S.SnapshotError, match="not a Wasel database"):
        S.check_image(m.serialize())


def test_unreachable_store_is_an_error_not_an_empty_db():
    def boom(request):
        raise httpx.ConnectError("down")
    store = S.HttpSnapshotStore("http://state.wasel.internal/snapshot",
                                client=httpx.Client(transport=httpx.MockTransport(boom)))
    with pytest.raises(S.SnapshotError, match="ConnectError"):
        store.load()


def test_http_store_roundtrip_and_status_handling():
    blobs = {}

    def handler(request):
        if request.method == "PUT":
            blobs["b"] = request.content
            return httpx.Response(204)
        return httpx.Response(200, content=blobs["b"]) if "b" in blobs else httpx.Response(404)
    store = S.HttpSnapshotStore("http://x/s", client=httpx.Client(transport=httpx.MockTransport(handler)))
    assert store.load() is None
    store.save(b"abc")
    assert store.load() == b"abc"
    bad = S.HttpSnapshotStore("http://x/s", client=httpx.Client(
        transport=httpx.MockTransport(lambda r: httpx.Response(500))))
    with pytest.raises(S.SnapshotError, match="500"):
        bad.load()
    with pytest.raises(S.SnapshotError, match="500"):
        bad.save(b"x")


def test_snapshotter_interval_change_detection_and_failure_reporting(tmp_path):
    conn = connect(tmp_path / "s.db")
    create_schema(conn)

    class Flaky:
        def __init__(self):
            self.saved, self.fail = [], False

        def save(self, data):
            if self.fail:
                raise S.SnapshotError("down")
            self.saved.append(data)

    store, clock = Flaky(), FrozenClock(T0)
    sn = S.Snapshotter(store, 60)
    assert sn.tick(conn, clock.now()) is True and len(store.saved) == 1
    clock.advance(61)
    assert sn.tick(conn, clock.now()) is False                    # unchanged -> no upload
    conn.execute("PRAGMA user_version=7")
    clock.advance(1)
    assert sn.tick(conn, clock.now()) is False                    # not due yet
    store.fail = True
    for _ in range(3):
        clock.advance(61)
        assert sn.tick(conn, clock.now()) is False
    assert sn.failing
    store.fail = False
    clock.advance(61)
    assert sn.tick(conn, clock.now()) is True and not sn.failing
