"""One connection per thread, with the PRAGMAs from 01 §3. The DB is rebuilt from schema.sql (no migrations)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = Path(__file__).with_name("schema.sql")


def connect(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))


def fresh_db(path: str | Path) -> sqlite3.Connection:
    """Delete the DB file (+ WAL/SHM) and rebuild it from schema.sql."""
    p = Path(path)
    for suffix in ("", "-wal", "-shm"):
        Path(str(p) + suffix).unlink(missing_ok=True)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = connect(p)
    create_schema(conn)
    return conn


class tx:
    """BEGIN IMMEDIATE … COMMIT/ROLLBACK. The deferred FK lets an order point at a new assessment
    inside the same transaction (01 §3.1)."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def __enter__(self):
        self.conn.execute("BEGIN IMMEDIATE")
        return self.conn

    def __exit__(self, exc_type, exc, tb):
        self.conn.execute("ROLLBACK" if exc_type else "COMMIT")
        return False
