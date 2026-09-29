"""ID generation: ULIDs in prod, sequential ids in tests."""
from __future__ import annotations

from typing import Protocol

from ulid import ULID


class IdGen(Protocol):
    """Callable that returns a new id string of the form '<prefix>_<suffix>'."""

    def __call__(self, prefix: str) -> str: ...


class UlidIds:
    """Production ids: the prefix plus a ULID, unique and roughly time-sortable."""

    def __call__(self, prefix: str) -> str:
        return f"{prefix}_{ULID()}"


class SeqIds:
    """Test ids: per-prefix counters (`ord_0001`, `ord_0002`, ...), deterministic for a given call order."""

    def __init__(self) -> None:
        self._n: dict[str, int] = {}

    def __call__(self, prefix: str) -> str:
        self._n[prefix] = self._n.get(prefix, 0) + 1
        return f"{prefix}_{self._n[prefix]:04d}"


def new_id(prefix: str = "id") -> str:
    """A one-off ULID-based id with the given prefix."""
    return UlidIds()(prefix)
