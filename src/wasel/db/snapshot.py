"""Durable copy of the SQLite database for hosts whose disk is ephemeral (for example Render).

The app keeps using one local SQLite file. When SNAPSHOT_URL is set, the file is restored from a snapshot store at boot
and copied back to it while the app runs and once more on shutdown. Without SNAPSHOT_URL nothing here runs, so `make
serve`, `make run` and the tests behave exactly as before.

Stores: `file:///abs/dir/wasel.sqlite` (local emulation and tests) and `http(s)://host/path` (GET returns the bytes or
404 when no snapshot exists yet; PUT stores them).

Failure rules: a missing snapshot is a first boot; any other restore error, or a snapshot that is not a healthy Wasel
database, stops startup. Booting empty and then snapshotting would overwrite the last good copy. A failed save is
logged, retried on the next interval and reported through /api/health as "degraded" once it has been failing for
three intervals.
"""
from __future__ import annotations

import hashlib
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlparse

import httpx

from wasel.db.conn import schema_problem

log = logging.getLogger("cod.snapshot")


class SnapshotError(RuntimeError):
    """A snapshot could not be read, written or trusted."""


class SnapshotStore(Protocol):
    """Where snapshots live."""

    def load(self) -> bytes | None:
        """The latest snapshot, or None if none was ever saved. Raises SnapshotError on any other failure."""
        ...

    def save(self, data: bytes) -> None:
        """Replace the latest snapshot. Raises SnapshotError on failure."""
        ...


class FileSnapshotStore:
    """A snapshot in one local file, replaced atomically."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> bytes | None:
        """The file's bytes, or None if it does not exist."""
        try:
            return self.path.read_bytes()
        except FileNotFoundError:
            return None
        except OSError as e:
            raise SnapshotError(f"cannot read {self.path}: {e}") from e

    def save(self, data: bytes) -> None:
        """Write `data` next to the target and rename it into place."""
        tmp = self.path.with_name(self.path.name + ".tmp")
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_bytes(data)
            os.replace(tmp, self.path)
        except OSError as e:
            raise SnapshotError(f"cannot write {self.path}: {e}") from e


class HttpSnapshotStore:
    """GET/PUT of the snapshot bytes on one URL."""

    def __init__(self, url: str, *, client: httpx.Client | None = None, timeout: float = 30.0):
        self.url, self.client = url, client or httpx.Client(timeout=timeout, trust_env=False)

    def load(self) -> bytes | None:
        """The snapshot bytes; None on 404. Any other status or a network error is a SnapshotError."""
        try:
            r = self.client.get(self.url)
        except httpx.HTTPError as e:
            raise SnapshotError(f"GET {self.url} failed: {type(e).__name__}: {e}") from e
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            raise SnapshotError(f"GET {self.url} returned {r.status_code}")
        return r.content

    def save(self, data: bytes) -> None:
        """PUT the bytes; any status other than 200/201/204 is a SnapshotError."""
        try:
            r = self.client.put(self.url, content=data, headers={"Content-Type": "application/vnd.sqlite3"})
        except httpx.HTTPError as e:
            raise SnapshotError(f"PUT {self.url} failed: {type(e).__name__}: {e}") from e
        if r.status_code not in (200, 201, 204):
            raise SnapshotError(f"PUT {self.url} returned {r.status_code}")


def store_from_url(url: str) -> SnapshotStore | None:
    """The store for a SNAPSHOT_URL value: None for empty, a ValueError for anything but file:// or http(s)://."""
    url = url.strip()
    if not url:
        return None
    u = urlparse(url)
    if u.scheme == "file":
        return FileSnapshotStore(unquote(u.path))
    if u.scheme in ("http", "https") and u.netloc:
        return HttpSnapshotStore(url)
    raise ValueError(f"SNAPSHOT_URL must be file:///path or http(s)://host/path, got {url!r}")


def serialize_db(conn: sqlite3.Connection) -> bytes:
    """A consistent image of the database behind `conn` (WAL contents included), taken with SQLite's online backup."""
    mem = sqlite3.connect(":memory:")
    try:
        conn.backup(mem)
        img = bytearray(mem.serialize())
        img[18] = img[19] = 1       # the image is complete on its own: mark it rollback-journal (connect() re-enables WAL)
        return bytes(img)
    finally:
        mem.close()


def check_image(data: bytes) -> None:
    """Raise SnapshotError unless `data` is an intact SQLite image that has Wasel's orders table."""
    mem = sqlite3.connect(":memory:")
    try:
        mem.deserialize(data)
        if mem.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise SnapshotError("snapshot failed PRAGMA integrity_check")
        if not mem.execute("SELECT 1 FROM sqlite_master WHERE name='orders'").fetchone():
            raise SnapshotError("snapshot has no orders table: not a Wasel database")
        problem = schema_problem(mem.execute("PRAGMA user_version").fetchone()[0])
        if problem:
            raise SnapshotError(f"snapshot refused: {problem}")
    except sqlite3.DatabaseError as e:
        raise SnapshotError(f"snapshot is not a readable SQLite database: {e}") from e
    finally:
        mem.close()


def restore(store: SnapshotStore, db_path: str | Path) -> bool:
    """Replace the local database file with the latest snapshot. False if there is none yet (first boot).

    The image is verified before anything on disk changes; stale -wal/-shm files are removed.
    """
    data = store.load()
    if data is None:
        return False
    check_image(data)
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    for suffix in ("-wal", "-shm"):
        Path(str(p) + suffix).unlink(missing_ok=True)
    tmp = p.with_name(p.name + ".restore")
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)        # customer data: owner only
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, p)
    log.info("restored %s from snapshot (%d bytes)", p, len(data))
    return True


class Snapshotter:
    """Saves the database to a store at most every `interval_s`, and only when its content changed."""

    def __init__(self, store: SnapshotStore, interval_s: float):
        self.store, self.interval_s = store, interval_s
        self._digest: str | None = None
        self._last_attempt: datetime | None = None
        self.last_saved_at: datetime | None = None
        self.failures = 0
        self.last_error: str | None = None              # exception type of the last failed save, no message
        self.size_bytes: int | None = None              # size of the last saved image

    def seed_digest(self, conn: sqlite3.Connection) -> None:
        """Remember the current content as already stored (call right after a restore)."""
        self._digest = hashlib.sha256(serialize_db(conn)).hexdigest()

    def tick(self, conn: sqlite3.Connection, now: datetime, *, force: bool = False) -> bool:
        """Save if due (or `force`) and changed. True if a save happened. Never raises: failures are counted."""
        if not force and self._last_attempt and (now - self._last_attempt).total_seconds() < self.interval_s:
            return False
        self._last_attempt = now
        try:
            data = serialize_db(conn)
            digest = hashlib.sha256(data).hexdigest()
            if digest == self._digest:
                return False
            self.store.save(data)
        except (SnapshotError, sqlite3.Error) as e:
            self.failures += 1
            self.last_error = type(e).__name__
            log.exception("snapshot save failed (%d in a row)", self.failures)
            return False
        self._digest, self.last_saved_at, self.failures, self.last_error = digest, now, 0, None
        self.size_bytes = len(data)
        log.info("snapshot saved (%d bytes)", len(data))
        return True

    @property
    def failing(self) -> bool:
        """True after three saves in a row failed."""
        return self.failures >= 3
