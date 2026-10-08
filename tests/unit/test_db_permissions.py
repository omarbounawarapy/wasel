"""The database holds customer messages and phone numbers: only its owner may read it (#40)."""
import os
import stat
import sys

import pytest

from wasel.db.conn import connect, fresh_db, tx

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")


def _mode(p) -> int:
    return stat.S_IMODE(os.stat(p).st_mode)


def test_a_new_database_and_its_wal_files_are_owner_only(tmp_path):
    old = os.umask(0o022)                                   # the permissive default of most hosts
    try:
        conn = fresh_db(tmp_path / "var" / "x.db")
        with tx(conn):
            conn.execute("INSERT INTO catalog VALUES ('P1','n','[]',1,'c')")
        files = [p for p in (tmp_path / "var").iterdir()]
        assert {p.name for p in files} >= {"x.db", "x.db-wal", "x.db-shm"}
        assert {_mode(p) for p in files} == {0o600}
        assert _mode(tmp_path / "var") == 0o700
    finally:
        os.umask(old)


def test_an_existing_world_readable_database_is_tightened(tmp_path):
    p = tmp_path / "old.db"
    connect(p).close()
    os.chmod(p, 0o644)
    connect(p).close()
    assert _mode(p) == 0o600
