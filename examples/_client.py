"""Shared helpers for the examples: one httpx client with a visitor id (required for writes in public mode)."""
from __future__ import annotations

import os
import sys
import time
import uuid

import httpx

BASE = os.environ.get("API_BASE_URL", "http://localhost:8000").rstrip("/")


def client() -> httpx.Client:
    c = httpx.Client(base_url=f"{BASE}/api", headers={"X-Visitor-Id": str(uuid.uuid4())}, timeout=30)
    try:
        h = c.get("/health").json()
    except httpx.HTTPError:
        sys.exit(f"No API at {BASE}. Start it with `make run` (or `make up`) first.")
    print(f"API {BASE} · mode={h['mode']} · extractor={h['llm']['primary']}\n")
    return c


def wait_for_version(c: httpx.Client, order_id: str, version: int, timeout_s: float = 30) -> dict:
    """Poll the order until assessment `version` exists and the worker is idle (debounce + scoring)."""
    end = time.monotonic() + timeout_s
    while time.monotonic() < end:
        d = c.get(f"/orders/{order_id}").json()
        s = d["order"]["score"]
        if s and s["version"] >= version and d["order"]["rescore_state"] == "idle":
            return d
        time.sleep(1)
    sys.exit(f"order {order_id} did not reach v{version} within {timeout_s:.0f} s")


def show(d: dict) -> None:
    o, s = d["order"], d["order"]["score"]
    print(f"  {o['order_ref']}  v{s['version']}  {s['tier'].upper()} {s['final_score']}  action={s['action']}"
          f"  status={o['status']}  path={s['path']}")
    print(f"  reason: {s['reason_short']}")
