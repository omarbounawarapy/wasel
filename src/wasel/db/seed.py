"""Seeding: catalog mirror, the committed extraction cache, and demo conversations. Seeding runs
store_inbound() (origin 'seed') and then the worker, so seeded orders get real assessments through the
cache, with zero LLM calls."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from wasel.clock import utc_iso
from wasel.db import repo
from wasel.db.conn import tx
from wasel.ids import IdGen
from wasel.ingress.ingest import store_inbound
from wasel.paths import ROOT

SEED_FILE = ROOT / "data" / "seed" / "demo_seed.json"
CACHE_FILE = ROOT / "data" / "seed" / "extraction_cache.jsonl"


def load_seed(path: Path = SEED_FILE) -> dict:
    """Parse the demo seed file (demo conversation fixtures and a version number)."""
    return json.loads(path.read_text(encoding="utf-8"))


def seed_catalog(conn, catalog: dict) -> None:
    """Write the product catalog to the database in one transaction."""
    with tx(conn):
        repo.upsert_catalog(conn, catalog)


def sync_catalog(conn, catalog: dict) -> tuple[list[str], list[str]]:
    """Write the product catalog and return the ids of products added and changed since the last call."""
    old = {r["product_id"]: (r["name"], r["price_tnd"], r["category"]) for r in
           conn.execute("SELECT product_id, name, price_tnd, category FROM catalog")}
    seed_catalog(conn, catalog)
    added = [p["product_id"] for p in catalog["products"] if p["product_id"] not in old]
    changed = [p["product_id"] for p in catalog["products"]
               if p["product_id"] in old and old[p["product_id"]] != (p["name"], p["price_tnd"], p["category"])]
    return added, changed


def seed_cache(conn, now: datetime, path: Path = CACHE_FILE) -> int:
    """Load the committed extraction cache (JSONL) into the database. Returns the number of entries loaded, 0 if the file
    is missing.

    Entries replace existing rows with the same input hash. Only 'llm' entries are stored as primary.
    """
    if not path.exists():
        return 0
    n = 0
    with tx(conn):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            conn.execute("INSERT OR REPLACE INTO extraction_cache (input_hash, prompt_version, provider, model, origin_path,"
                         " is_primary, extraction_json, created_at) VALUES (?,?,?,?,?,?,?,?)",
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
    """Load catalog, cache and every demo conversation as seeded (non-sandbox) orders, then score them.

    Scoring uses the given scorer; with the committed cache that needs no LLM call. Returns the number of orders scored.
    """
    from wasel.worker import drain
    seed_catalog(conn, catalog)
    seed_cache(conn, now)
    data = load_seed()
    for fx in data["conversations"]:
        seed_conversation(conn, ids, now, fx, None)
    scored = drain(conn, now, scorer, drafter, ids=ids)
    # a fixture with an "answer" already has the customer's reply: score the order before it, then after it, so the
    # sample order carries two versions (the reason diff shows in its score history)
    for fx in data["conversations"]:
        if fx.get("answer"):
            answer_seeded_conversation(conn, ids, now, fx)
    drain(conn, now, scorer, drafter, ids=ids)           # the second pass re-scores the answered orders only
    return scored


def answer_seeded_conversation(conn, ids: IdGen, now: datetime, fx: dict) -> None:
    """Store the customer's reply from a seed fixture's `answer` on its (seeded, non-sandbox) conversation, after the
    draft the first score made. The caller scores afterwards, so the order gets a second assessment."""
    cid = conn.execute("SELECT conversation_id FROM conversations WHERE seed_key=? AND sandbox_id IS NULL",
                       (fx["key"],)).fetchone()[0]
    with tx(conn):
        order = repo.open_order(conn, cid)
        if order is not None and (d := repo.unsent_draft(conn, order["order_id"])) is not None:
            # as in commands.simulate_reply: the reply implies the draft went out, so the reply reads as an answer to it
            repo.mark_draft_sent(conn, ids, now, d, origin="simulated", delivery="recorded_only", decided_by="human")
        store_inbound(conn, ids, now, conversation_id=cid, origin="seed", text=fx["answer"]["text"],
                      provider_ts=now + timedelta(microseconds=1),     # after the draft recorded above, as simulate_reply
                      no_debounce=True)


def fixture_for(seed_key: str) -> dict | None:
    """The demo conversation fixture with this `seed_key`, or None. Re-reads the seed file on each call."""
    return next((c for c in load_seed()["conversations"] if c["key"] == seed_key), None)
