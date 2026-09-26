"""ID generation (05 §2): ULIDs in prod, sequential ids in tests."""
from __future__ import annotations

from typing import Protocol

from ulid import ULID


class IdGen(Protocol):
    def __call__(self, prefix: str) -> str: ...


class UlidIds:
    def __call__(self, prefix: str) -> str:
        return f"{prefix}_{ULID()}"


class SeqIds:
    def __init__(self) -> None:
        self._n: dict[str, int] = {}

    def __call__(self, prefix: str) -> str:
        self._n[prefix] = self._n.get(prefix, 0) + 1
        return f"{prefix}_{self._n[prefix]:04d}"


def new_id(prefix: str = "id") -> str:
    return UlidIds()(prefix)
