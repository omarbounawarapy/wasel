"""Per-client-address limits for the public demo, in memory.

Every other public-mode limit is keyed on `X-Visitor-Id`, which the client chooses, so a fresh id resets it. These
count per address instead: writes in a window, sandbox orders created, and which visitor ids came from the same
address (so the LLM budget of an address is shared by all of its ids). The state is lost on a restart, which only
resets the counters.
"""
from __future__ import annotations

import ipaddress
from collections import defaultdict, deque

MAX_ADDRESSES = 20_000              # a flood of distinct addresses cannot grow memory without bound


def client_address(peer: str | None, headers, header_name: str) -> str | None:
    """The address to rate-limit, or None when it cannot be told.

    `header_name` is a header that a trusted proxy overwrites on every request (CF-Connecting-IP on Cloudflare and
    on Render); with none configured the socket peer is used. A loopback or private peer means a proxy sits in
    front and the real address is unknown, so there is nothing to limit by.
    """
    candidate = (headers.get(header_name) or "").strip() if header_name else ""
    for value in (candidate, "" if header_name else (peer or "")):
        try:
            ip = ipaddress.ip_address(value)
        except ValueError:
            continue
        if ip.is_loopback or ip.is_private or ip.is_unspecified:
            if value == candidate:
                continue
            return None
        if ip.version == 6:                         # one subscriber holds a whole /64: count the prefix
            return str(ipaddress.ip_network(f"{ip}/64", strict=False))
        return str(ip)
    return None


class AddressLimiter:
    """Sliding-window counters per client address."""

    def __init__(self):
        self._writes: dict[str, deque[float]] = defaultdict(deque)
        self._orders: dict[str, deque[float]] = defaultdict(deque)
        self._visitors: dict[str, dict[str, float]] = defaultdict(dict)
        self._address_of: dict[str, str] = {}

    @staticmethod
    def _trim(q: deque[float], now: float, window: float) -> None:
        while q and q[0] <= now - window:
            q.popleft()

    def _bound(self, table: dict) -> None:
        if len(table) > MAX_ADDRESSES:
            for k in list(table)[: len(table) // 2]:
                table.pop(k, None)

    def hit_write(self, addr: str, now: float, limit: int, window_s: float) -> float | None:
        """Count one write. Returns None if allowed, else the seconds until the oldest counted write expires."""
        q = self._writes[addr]
        self._trim(q, now, window_s)
        if len(q) >= limit:
            return max(1.0, q[0] + window_s - now)
        q.append(now)
        self._bound(self._writes)
        return None

    def orders_wait(self, addr: str, now: float, limit: int, window_s: float, adding: int = 1) -> float | None:
        """None if `adding` more sandbox orders fit in the budget, else the seconds until room appears."""
        q = self._orders[addr]
        self._trim(q, now, window_s)
        if len(q) + adding > limit:
            return max(1.0, q[0] + window_s - now) if q else window_s
        return None

    def add_orders(self, addr: str, now: float, n: int) -> None:
        self._orders[addr].extend([now] * n)
        self._bound(self._orders)

    def note_visitor(self, addr: str, vid: str, now: float) -> None:
        self._visitors[addr][vid] = now
        self._address_of[vid] = addr
        self._bound(self._visitors)
        if len(self._address_of) > MAX_ADDRESSES * 4:
            self._address_of.clear()
            self._visitors.clear()

    def siblings(self, vid: str) -> list[str]:
        """Every visitor id seen from the same address as `vid` (including `vid`)."""
        addr = self._address_of.get(vid)
        return list(self._visitors.get(addr, {vid: 0})) if addr else [vid]
