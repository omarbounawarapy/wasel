"""SqliteUsageMeter (implements contracts.UsageMeter) over llm_usage. Counters live in SQLite,
so a restart doesn't reset them. Calls allowed inside a scoring run but not yet persisted are held in
`_pending` so a 3-step chain can't overshoot the cap; the worker calls settle() after its transaction.

Caps: global daily provider calls (all providers, fallback hops included); in public mode also per visitor
6 per 10 min and 20 per day, and a per-model token guard. Over a cap -> 'visitor_cap' / 'global_cap', which
the chain turns into path 'rules'. Never an HTTP error.
NOTE: the visitor cap counts provider calls, not "LLM actions"; stricter, simpler."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from wasel.clock import utc_iso


class SqliteUsageMeter:
    """Enforces the LLM call caps from the llm_usage table.

    `daily_cap` is the global daily limit on provider calls (None = unlimited); in public mode the per-visitor limits
    and the per-model daily token guard also apply.
    """

    def __init__(self, conn: sqlite3.Connection, *, daily_cap: int | None, public: bool,
                 visitor_10min: int = 6, visitor_day: int = 20, tokens_per_model_day: int | None = None,
                 siblings=None, address_cap: int | None = None):
        self.conn, self.daily_cap, self.public = conn, daily_cap, public
        self.visitor_10min, self.visitor_day = visitor_10min, visitor_day
        self.tokens_per_model_day = tokens_per_model_day if tokens_per_model_day is not None else \
            (120_000 if public else None)
        self._pending: dict[str | None, int] = {}
        self.siblings, self.address_cap = siblings, address_cap      # visitor ids from one address, and its share

    def _count(self, sql: str, *args) -> int:
        return int(self.conn.execute(sql, args).fetchone()[0] or 0)

    def calls_today(self, now: datetime) -> int:
        """Persisted provider calls on the UTC day of `now`. Calls only reserved by allow() are not counted."""
        return self._count("SELECT COUNT(*) FROM llm_usage WHERE day=?", now.strftime("%Y-%m-%d"))

    def allow(self, role, sandbox_id, now: datetime):
        """Return 'ok', 'global_cap' or 'visitor_cap' for one more provider call.

        On 'ok' the call is reserved, so later checks in the same scoring run count it before it is persisted. `role`
        does
        not affect the decision. `sandbox_id` None (seeded/event traffic) skips the visitor limits.
        """
        day = now.strftime("%Y-%m-%d")
        pending_all = sum(self._pending.values())
        if self.daily_cap is not None and self.calls_today(now) + pending_all >= self.daily_cap:
            return "global_cap"
        if self.tokens_per_model_day is not None and \
                self._count("SELECT COALESCE(MAX(t),0) FROM (SELECT SUM(COALESCE(tokens_in,0)+COALESCE(tokens_out,0)) t"
                            " FROM llm_usage WHERE day=? GROUP BY model)", day) >= self.tokens_per_model_day:
            return "global_cap"
        if self.public and sandbox_id is not None:
            mine = self._pending.get(sandbox_id, 0)
            last10 = self._count("SELECT COUNT(*) FROM llm_usage WHERE sandbox_id=? AND ts>=?", sandbox_id,
                                 utc_iso(now - timedelta(minutes=10)))
            today = self._count("SELECT COUNT(*) FROM llm_usage WHERE sandbox_id=? AND day=?", sandbox_id, day)
            if last10 + mine >= self.visitor_10min or today + mine >= self.visitor_day:
                return "visitor_cap"
            if self.siblings is not None and self.address_cap is not None:       # the address, whatever ids it uses
                ids = self.siblings(sandbox_id)
                marks = ",".join("?" * len(ids))
                used = self._count(f"SELECT COUNT(*) FROM llm_usage WHERE day=? AND sandbox_id IN ({marks})", day, *ids)
                if used + sum(self._pending.get(i, 0) for i in ids) >= self.address_cap:
                    return "visitor_cap"
        self._pending[sandbox_id] = self._pending.get(sandbox_id, 0) + 1
        return "ok"

    def settle(self) -> None:
        """Drop the reservations. Call after the scoring transaction has persisted the usage rows."""
        self._pending.clear()
