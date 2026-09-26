"""The ONLY place that reads the wall clock (05 §2; hygiene greps for datetime.now elsewhere)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...                      # always tz-aware UTC


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """For tests, drills and scripts."""

    def __init__(self, start: datetime) -> None:
        assert start.tzinfo is not None, "FrozenClock needs a tz-aware start"
        self._now = start.astimezone(UTC)

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


def utc_iso(dt: datetime) -> str:
    """'2026-09-27T10:00:04.123456Z': fixed width, sorts lexicographically (01 §3)."""
    assert dt.tzinfo is not None, "utc_iso needs a tz-aware datetime"
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_utc(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
