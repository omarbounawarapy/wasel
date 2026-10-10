"""The SQLite snapshot boundary used on hosts with an ephemeral disk: restore at boot, save while running and at shutdown,
and no silent fallback to an empty database when the store is unhealthy."""
from __future__ import annotations

import httpx
import pytest

from tests.conftest import T0
from tests.integration.conftest import make_client
from wasel.clock import FrozenClock
from wasel.db import snapshot as S
from wasel.db.conn import SCHEMA_VERSION, connect, create_schema


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


def _set_user_version(path, version):
    import sqlite3
    raw = sqlite3.connect(path, isolation_level=None)
    raw.execute(f"PRAGMA user_version = {int(version)}")
    raw.close()


def _user_version(path):
    import sqlite3
    raw = sqlite3.connect(path)
    try:
        return raw.execute("PRAGMA user_version").fetchone()[0]
    finally:
        raw.close()


def test_fresh_database_is_stamped_with_the_schema_version(tmp_path):
    from wasel.db.conn import SCHEMA_VERSION, fresh_db
    conn = fresh_db(tmp_path / "fresh.db")
    assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION


def test_boot_refuses_a_database_from_another_schema_version(tmp_path):
    c, _, _ = make_client(tmp_path, "dev", seed_on_boot="if_empty")
    with c:
        pass
    _set_user_version(tmp_path / "app.db", 99)
    c2, _, _ = make_client(tmp_path, "dev", seed_on_boot="if_empty")
    with pytest.raises(RuntimeError, match="schema version 99, this build expects 1"), c2:
        pass
    assert _user_version(tmp_path / "app.db") == 99                 # refused, not migrated or stamped


def test_unversioned_database_with_current_tables_is_accepted_and_stamped(tmp_path):
    c, _, _ = make_client(tmp_path, "dev", seed_on_boot="if_empty")
    with c:
        pass
    _set_user_version(tmp_path / "app.db", 0)
    c2, core2, _ = make_client(tmp_path, "dev", seed_on_boot="if_empty")
    with c2:
        assert _orders(core2) > 0
    assert _user_version(tmp_path / "app.db") == SCHEMA_VERSION


def test_snapshot_from_another_schema_version_is_refused_by_restore(tmp_path):
    import sqlite3
    m = sqlite3.connect(":memory:")
    m.execute("CREATE TABLE orders(x)")
    m.execute("PRAGMA user_version = 99")
    with pytest.raises(S.SnapshotError, match="schema version 99"):
        S.check_image(m.serialize())
    store = S.FileSnapshotStore(tmp_path / "store.sqlite")
    store.save(m.serialize())
    with pytest.raises(S.SnapshotError, match="schema version 99"):
        S.restore(store, tmp_path / "restored.db")
    assert not (tmp_path / "restored.db").exists()


def _healthy_image(tmp_path, rows=0):
    import sqlite3
    path = tmp_path / "src.sqlite"
    raw = sqlite3.connect(path, isolation_level=None)
    raw.execute("CREATE TABLE orders(order_id TEXT PRIMARY KEY, note TEXT)")
    raw.execute("BEGIN")
    for i in range(rows):
        raw.execute("INSERT INTO orders VALUES (?, ?)", (f"o{i}", "x" * 200))
    raw.execute("COMMIT")
    raw.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    raw.close()
    return path.read_bytes()


def test_restore_removes_stale_wal_and_shm_files(tmp_path):
    store = S.FileSnapshotStore(tmp_path / "store.sqlite")
    store.save(_healthy_image(tmp_path))
    db = tmp_path / "app.db"
    wal, shm = tmp_path / "app.db-wal", tmp_path / "app.db-shm"
    wal.write_bytes(b"stale journal from the old database")
    shm.write_bytes(b"stale index")
    assert S.restore(store, db) is True
    assert not wal.exists() and not shm.exists()
    assert db.exists()


def test_restore_rejects_an_image_that_fails_the_integrity_check(tmp_path):
    import sqlite3
    data = bytearray(_healthy_image(tmp_path, rows=2000))
    page = 4096
    for n in range(2, len(data) // page):                # damage the content of table pages, keep the header
        data[n * page + 300:n * page + 364] = b"\xff" * 64
    img = bytes(data)
    mem = sqlite3.connect(":memory:")
    mem.deserialize(img)
    assert mem.execute("PRAGMA integrity_check").fetchone()[0] != "ok"      # the damage is real
    store = S.FileSnapshotStore(tmp_path / "store.sqlite")
    store.save(img)
    with pytest.raises(S.SnapshotError, match="integrity_check"):
        S.restore(store, tmp_path / "app.db")
    assert not (tmp_path / "app.db").exists()


# ---------------------------------------------------------------- durability at the boundary operations
def _restored_orders(tmp_path, store_url):
    """What a brand-new disk would hold right now, read from the store (the process is still running)."""
    disk = tmp_path / "fresh-disk"
    disk.mkdir(exist_ok=True)
    db = disk / "restored.db"
    S.restore(S.store_from_url(store_url), db)
    conn = connect(db)
    try:
        return {r["channel_message_id"] for r in conn.execute("SELECT channel_message_id FROM messages")}, \
            {r["draft_id"] for r in conn.execute("SELECT draft_id FROM outbound_drafts WHERE sent_message_id IS NOT NULL")}
    finally:
        conn.close()


def _sub(tmp_path):
    d = tmp_path / "a"
    d.mkdir(exist_ok=True)
    return d


def test_acknowledged_webhook_message_is_in_the_store_before_the_200(tmp_path):
    from tests.integration.test_whatsapp import WA, wa_post
    c, core, _ = make_client(_sub(tmp_path), "dev", snapshot_url=_url(tmp_path), seed_on_boot="if_empty", **WA)
    with c:
        assert wa_post(c, "text_inbound").status_code == 200
        # no shutdown, no interval tick: only what the request itself saved
        wamids, _ = _restored_orders(tmp_path, _url(tmp_path))
        assert "wamid.TEST1" in wamids


def test_failed_save_makes_the_webhook_answer_503_so_meta_retries(tmp_path):
    from tests.integration.test_whatsapp import WA, wa_post
    c, core, _ = make_client(_sub(tmp_path), "dev", snapshot_url=_url(tmp_path), seed_on_boot="if_empty", **WA)
    with c:
        def broken(data):
            raise S.SnapshotError("disk full")
        core.snapshotter.store.save = broken
        r = wa_post(c, "text_inbound")
        assert r.status_code == 503 and r.json()["error"]["code"] == "WEBHOOK_NOT_STORED"
        del core.snapshotter.store.save                      # the store is back: the retry is a duplicate and saves
        assert wa_post(c, "text_inbound").status_code == 200
        assert "wamid.TEST1" in _restored_orders(tmp_path, _url(tmp_path))[0]


def test_recorded_send_is_in_the_store_when_the_request_returns(tmp_path):
    from tests.integration.test_whatsapp import WA, _draft_for, _sender
    c, core, clock = make_client(_sub(tmp_path), "dev", snapshot_url=_url(tmp_path), seed_on_boot="if_empty",
                                 wa_send_enabled=True, wa_token="test-token", **WA)
    with c:
        core.sender = _sender([])
        _, _, d = _draft_for(c, core, clock)
        assert c.post(f"/api/drafts/{d['draft_id']}/send").status_code == 200
        assert d["draft_id"] in _restored_orders(tmp_path, _url(tmp_path))[1]
