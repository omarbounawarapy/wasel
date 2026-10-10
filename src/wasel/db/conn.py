"""SQLite connections and transactions. connect() applies the PRAGMAs that schema.sql lists in its header.
The DB is rebuilt from schema.sql (no migrations)."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")
# Bump this with every change to schema.sql. It is stored in the file header (PRAGMA user_version). A database with
# another non-zero version is refused at boot and in snapshot restore; version 0 is an unversioned database made before
# this check existed, accepted once and stamped (see main.AppState.boot).
SCHEMA_VERSION = 1


def connect(path: str | Path) -> sqlite3.Connection:
    """Open the SQLite file with autocommit, WAL, foreign keys on, a 5 s busy timeout and synchronous=NORMAL.

    The connection may be used from any thread, but callers keep one per thread (see AppState.conn). Transactions are
    explicit, via `tx`.

    A new database file is created with mode 0600 (SQLite gives the -wal and -shm files the same mode), and an
    existing one that other users can read is tightened to 0600: it holds customer messages and phone numbers.
    """
    if str(path) != ":memory:":
        try:
            os.close(os.open(path, os.O_CREAT | os.O_RDWR, 0o600))
            if os.stat(path).st_mode & 0o077:
                os.chmod(path, 0o600)
        except OSError:
            pass                                        # a read-only or special path: let sqlite3 report it
    conn = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Run schema.sql on the connection and stamp SCHEMA_VERSION. The schema has no migrations."""
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    stamp_schema(conn)


def stamp_schema(conn: sqlite3.Connection) -> None:
    """Write SCHEMA_VERSION into the database header."""
    conn.execute(f"PRAGMA user_version = {int(SCHEMA_VERSION)}")


def schema_problem(version: int) -> str | None:
    """None if a database with this user_version can be used by this build; otherwise the reason it cannot."""
    if version in (0, SCHEMA_VERSION):
        return None
    return (f"database schema version {version}, this build expects {SCHEMA_VERSION}. Either delete the database file "
            f"(its data is lost) or restore a snapshot made by a compatible build")


def fresh_db(path: str | Path) -> sqlite3.Connection:
    """Delete the DB file (+ WAL/SHM) and rebuild it from schema.sql."""
    p = Path(path)
    for suffix in ("", "-wal", "-shm"):
        Path(str(p) + suffix).unlink(missing_ok=True)
    p.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    conn = connect(p)
    create_schema(conn)
    return conn


class tx:
    """BEGIN IMMEDIATE … COMMIT/ROLLBACK. The deferred FK lets an order point at a new assessment
    inside the same transaction."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def __enter__(self):
        self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        self.conn.execute("ROLLBACK" if exc_type else "COMMIT")
        return False
