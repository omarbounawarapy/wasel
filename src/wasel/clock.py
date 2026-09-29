"""The ONLY place that reads the wall clock (hygiene greps for datetime.now elsewhere)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    """Source of the current time. Production code reads the time only through this, never from datetime directly."""

    def now(self) -> datetime:
        """The current time as a timezone-aware UTC datetime."""
        ...


class SystemClock:
    """The wall clock."""

    def now(self) -> datetime:
        """The current UTC time."""
        return datetime.now(UTC)


class FrozenClock:
    """For tests, drills and scripts."""

    def __init__(self, start: datetime) -> None:
        assert start.tzinfo is not None, "FrozenClock needs a tz-aware start"
        self._now = start.astimezone(UTC)

    def now(self) -> datetime:
        """The frozen time, unchanged until advance() is called."""
        return self._now

    def advance(self, seconds: float) -> None:
        """Move the frozen time forward by `seconds`."""
        self._now += timedelta(seconds=seconds)


def utc_iso(dt: datetime) -> str:
    """'2026-09-27T10:00:04.123456Z': fixed width, sorts lexicographically."""
    assert dt.tzinfo is not None, "utc_iso needs a tz-aware datetime"
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def parse_utc(s: str) -> datetime:
    """Parse a string produced by utc_iso back into an aware UTC datetime. Raises ValueError for any other format."""
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
