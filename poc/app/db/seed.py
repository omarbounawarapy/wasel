"""Seeding (01 §3.3): catalog mirror, the committed extraction cache, and demo conversations. Seeding runs
store_inbound() (origin 'seed') and then the worker, so seeded orders get real assessments through the
cache, with zero LLM calls."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from app.clock import utc_iso
from app.db import repo
from app.db.conn import tx
from app.ids import IdGen
from app.ingress.ingest import store_inbound

ROOT = Path(__file__).resolve().parents[2]
SEED_FILE = ROOT / "data" / "seed" / "demo_seed.json"
CACHE_FILE = ROOT / "data" / "seed" / "extraction_cache.jsonl"


def load_seed(path: Path = SEED_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def seed_catalog(conn, catalog: dict) -> None:
    with tx(conn):
        repo.upsert_catalog(conn, catalog)


def seed_cache(conn, now: datetime, path: Path = CACHE_FILE) -> int:
    if not path.exists():
        return 0
    n = 0
    with tx(conn):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            conn.execute("INSERT OR REPLACE INTO extraction_cache VALUES (?,?,?,?,?,?,?,?)",
                         (e["input_hash"], e["prompt_version"], e["provider"], e["model"], e["origin_path"],
                          int(e["origin_path"] == "llm"), json.dumps(e["extraction"], ensure_ascii=False),
                          utc_iso(now)))
            n += 1
    return n


def seed_conversation(conn, ids: IdGen, now: datetime, fx: dict, sandbox_id: str | None) -> str:
    """Creates customer + conversation + messages (no debounce). Returns the order id."""
    c = fx["customer"]
    with tx(conn):
        cid = repo.get_or_create_customer(conn, ids, now, sandbox_id=sandbox_id, display_name=c.get("display_name"),
                                          external_ref=c.get("external_ref") if sandbox_id is None else None,
                                          completed_orders=c.get("completed_orders", 0),
                                          refusals_total=c.get("refusals_total", 0))
        conv = repo.create_conversation(conn, ids, now, customer_id=cid, sandbox_id=sandbox_id,
                                        channel=fx.get("channel", "simulated"), seed_key=fx["key"])
        oid = None
        for m in fx["messages"]:
            st = store_inbound(conn, ids, now, conversation_id=conv, origin="seed", text=m["text"],
                               provider_ts=now - timedelta(seconds=600) + timedelta(seconds=m.get("offset_s", 0)),
                               no_debounce=True, structured=fx.get("structured") or {})
            oid = st.order_id
        if sandbox_id is None and fx.get("order_no"):
            conn.execute("UPDATE orders SET order_no=? WHERE order_id=?", (fx["order_no"], oid))
    return oid


def seed_all(conn, ids: IdGen, now: datetime, scorer, drafter, catalog: dict) -> int:
    from app.worker import drain
    seed_catalog(conn, catalog)
    seed_cache(conn, now)
    data = load_seed()
    for fx in data["conversations"]:
        seed_conversation(conn, ids, now, fx, None)
    return drain(conn, now, scorer, drafter, ids=ids)


def fixture_for(seed_key: str) -> dict | None:
    return next((c for c in load_seed()["conversations"] if c["key"] == seed_key), None)
