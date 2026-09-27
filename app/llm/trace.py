"""LLM observability: one trace record per LLM request (every role goes through ChainClient.extract, the one LLM
entry point). Records carry ids, versions, models, outcomes, latency, tokens, cache hits and a sha256 of the
input: never the customer's text or phone number. Rewrite/judge outputs (shop text, no customer data) are kept
so the failure analyzer and the monitor can read verdicts.

Sinks: an in-process ring buffer (always; /api/traces reads it) + a JSONL file when TRACE_FILE is set.
"""
from __future__ import annotations

import contextvars
import json
import os
import threading
import uuid
from collections import deque
from datetime import UTC, datetime
from pathlib import Path

TRACE_CTX: contextvars.ContextVar[dict | None] = contextvars.ContextVar("trace_ctx", default=None)
_lock = threading.Lock()
_ring: deque[dict] = deque(maxlen=5000)


def bind(**kw) -> contextvars.Token:
    """Attach order_id / sandbox_id / step to every trace emitted in this context."""
    return TRACE_CTX.set({**(TRACE_CTX.get() or {}), **kw})


def new_id() -> str:
    return uuid.uuid4().hex[:16]


def emit(rec: dict) -> None:
    rec = {"ts": datetime.now(UTC).isoformat(timespec="milliseconds"), **(TRACE_CTX.get() or {}), **rec}
    with _lock:
        _ring.append(rec)
        path = os.environ.get("TRACE_FILE")
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def recent(limit: int = 200, role: str | None = None, order_id: str | None = None) -> list[dict]:
    with _lock:
        rows = list(_ring)
    rows = [r for r in rows if (role is None or r.get("role") == role)
            and (order_id is None or r.get("order_id") == order_id)]
    return rows[-limit:][::-1]


def summary() -> dict:
    """Aggregates for /api/monitor: per role counts, cache hit rate, error rate, p50/p95 latency, tokens."""
    with _lock:
        rows = list(_ring)
    out: dict[str, dict] = {}
    for r in rows:
        s = out.setdefault(r.get("role", "?"), {"requests": 0, "cache_hits": 0, "failed": 0, "capped": 0,
                                                "tokens_in": 0, "tokens_out": 0, "latencies": []})
        s["requests"] += 1
        s["cache_hits"] += int(bool(r.get("cache_hit")))
        s["failed"] += int(r.get("outcome") not in ("ok", "cache_hit"))
        s["capped"] += int(r.get("outcome") in ("cap", "input_too_large"))
        s["tokens_in"] += r.get("tokens_in") or 0
        s["tokens_out"] += r.get("tokens_out") or 0
        if r.get("latency_ms") is not None and not r.get("cache_hit"):
            s["latencies"].append(r["latency_ms"])
    for s in out.values():
        lat = sorted(s.pop("latencies"))
        s["p50_ms"] = lat[len(lat) // 2] if lat else None
        s["p95_ms"] = lat[min(len(lat) - 1, int(len(lat) * 0.95))] if lat else None
    return out


def clear() -> None:
    with _lock:
        _ring.clear()
