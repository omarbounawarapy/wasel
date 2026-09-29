"""process_due(): the sync worker step tests call directly. run_loop() wraps it in
asyncio.to_thread every second. No clock reads and no sleeps in process_due."""
from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta

from wasel.clock import parse_utc, utc_iso
from wasel.contracts import Drafter, DraftRequest, ScoreInput, Scorer
from wasel.db import repo
from wasel.db.conn import tx
from wasel.extraction.normalize import mask_phones
from wasel.ids import IdGen
from wasel.outbound.templates import format_price, sanitize_first_name
from wasel.state import next_status

log = logging.getLogger("cod.worker")


def fire_no_reply_timeouts(conn, now: datetime, no_reply_s: float) -> list[str]:
    """Not called in public mode. awaiting_reply for longer than no_reply_s -> pending no_reply_timeout."""
    cutoff = utc_iso(now - timedelta(seconds=no_reply_s))
    due = repo.rows(conn, "SELECT o.order_id FROM orders o WHERE o.status='awaiting_reply' AND o.awaiting_reply_since"
                          " <= ? AND o.pending_rescore_at IS NULL AND NOT EXISTS (SELECT 1 FROM risk_assessments a"
                          " WHERE a.order_id=o.order_id AND a.trigger='no_reply_timeout' AND a.created_at >="
                          " o.awaiting_reply_since)", cutoff)
    for r in due:
        conn.execute("UPDATE orders SET pending_trigger='no_reply_timeout', pending_rescore_at=?,"
                     " rescore_state='debouncing' WHERE order_id=?", (utc_iso(now), r["order_id"]))
    return [r["order_id"] for r in due]


def build_score_input(conn, order: sqlite3.Row, trigger: str, now: datetime) -> ScoreInput:
    prior = repo.prior_assessment(conn, order["order_id"])
    conv = repo.row(conn, "SELECT channel FROM conversations WHERE conversation_id=?", order["conversation_id"])
    return ScoreInput(order_id=order["order_id"], sandbox_id=order["sandbox_id"], channel=conv["channel"],
                      trigger=trigger, messages=repo.window_messages(conn, order["order_id"],
                                                                     prior.created_at if prior else None),
                      structured=repo.structured(order), customer=repo.customer_history(conn, order["customer_id"]),
                      prior=prior, now=now)


def draft_request(conn, order_id: str, now: datetime, template_id: str) -> DraftRequest:
    o = repo.get_order(conn, order_id)
    cust = repo.row(conn, "SELECT display_name FROM customers WHERE customer_id=?", o["customer_id"])
    a = repo.current_assessment(conn, order_id)
    recent = [mask_phones(m["text"]) for m in repo.order_messages(conn, order_id)
              if m["direction"] == "inbound" and m["text"]][-3:]
    conv = repo.row(conn, "SELECT last_inbound_at FROM conversations WHERE conversation_id=?", o["conversation_id"])
    return DraftRequest(
        order_id=order_id, sandbox_id=o["sandbox_id"], template_id=template_id, language=o["language"] or "mixed",
        slots={k: v for k, v in {"first_name": sanitize_first_name(cust["display_name"]),
                                 "product": o["product_name"], "price_tnd": format_price(o["price_tnd"])}.items()},
        customer_recent=recent, confidence=a["confidence"] if a else "low", price_tnd=o["price_tnd"],
        auto_messages_sent=o["auto_messages_sent"],
        last_inbound_at=parse_utc(conv["last_inbound_at"]) if conv["last_inbound_at"] else None, now=now)


def create_draft(conn, ids: IdGen, now: datetime, order_id: str, drafter: Drafter, template_id: str | None) -> str | None:
    if repo.unsent_draft(conn, order_id):
        return None
    a = repo.current_assessment(conn, order_id)
    if a is None:
        return None
    tid = template_id or a["template_id"] or "T_CONFIRM"
    rec = drafter(draft_request(conn, order_id, now, tid))
    did = repo.insert_draft(conn, ids, now, order_id, a["assessment_id"], rec)
    o = repo.get_order(conn, order_id)
    for u in rec.usage:                                 # rewrite/judge calls count against the caps
        repo.insert_usage(conn, u, sandbox_id=o["sandbox_id"], order_id=order_id)
    for e in rec.events:
        repo.add_event(conn, now, e.type, e.level, order_id=order_id, sandbox_id=o["sandbox_id"], entity_id=did,
                       payload=e.payload)
    return did


def process_due(conn, now: datetime, scorer: Scorer, drafter: Drafter, *, ids: IdGen, limit: int = 10,
                no_reply_s: float | None = None, meter=None) -> list[str]:
    if no_reply_s is not None:
        with tx(conn):
            fire_no_reply_timeouts(conn, now, no_reply_s)
    done: list[str] = []
    for _ in range(limit):
        cand = repo.row(conn, "SELECT order_id, pending_rescore_at, pending_trigger FROM orders WHERE pending_rescore_at"
                              " IS NOT NULL AND pending_rescore_at <= ? ORDER BY pending_rescore_at LIMIT 1", utc_iso(now))
        if cand is None:
            break
        with tx(conn):                                      # claim (CAS)
            cur = conn.execute("UPDATE orders SET pending_rescore_at=NULL, pending_trigger=NULL, rescore_state='scoring'"
                               " WHERE order_id=? AND pending_rescore_at=?",
                               (cand["order_id"], cand["pending_rescore_at"]))
        if cur.rowcount == 0:
            continue
        oid, trigger = cand["order_id"], cand["pending_trigger"] or "manual"
        try:
            order = repo.get_order(conn, oid)
            inp = build_score_input(conn, order, trigger, now)
            result = scorer(inp)
            with tx(conn):
                order = repo.get_order(conn, oid)
                nxt = next_status(order["status"], result, trigger, inp.prior.tier if inp.prior else None,
                                  order["seller_approved_at"])
                drafting = nxt == "awaiting_reply" and repo.unsent_draft(conn, oid) is None
                repo.persist_result(conn, ids, now, order, trigger, result, inp.prior, nxt,
                                    "drafting" if drafting else "idle")
            if meter is not None:
                meter.settle()
            if drafting:
                with tx(conn):
                    create_draft(conn, ids, now, oid, drafter, result.template_id)
                    conn.execute("UPDATE orders SET rescore_state='idle' WHERE order_id=?", (oid,))
            done.append(oid)
        except Exception as e:                              # step 7: never re-armed automatically
            log.exception("rescore failed for %s", oid)
            with tx(conn):
                conn.execute("UPDATE orders SET status=CASE WHEN status IN ('shipped','delivered','refused','cancelled')"
                             " THEN status ELSE 'needs_review' END, rescore_state='idle' WHERE order_id=?", (oid,))
                repo.add_event(conn, now, "error", "error", order_id=oid,
                               payload={"where": "rescore", "error": f"{type(e).__name__}: {str(e)[:200]}"})
    return done


def drain(conn, now: datetime, scorer: Scorer, drafter: Drafter, *, ids: IdGen, max_rounds: int = 200) -> int:
    """Run process_due until nothing is due (seeding, tests)."""
    n = 0
    for _ in range(max_rounds):
        got = process_due(conn, now, scorer, drafter, ids=ids)
        if not got:
            break
        n += len(got)
    return n


async def run_loop(state) -> None:
    """state: app.main.AppState. Every 1 s: asyncio.to_thread(state.tick); purge in public mode."""
    last_purge = None
    while True:
        now = state.clock.now()
        try:
            await asyncio.to_thread(state.tick, now)
            state.last_tick_at = now
            if state.settings.is_public and (last_purge is None or
                                             (now - last_purge).total_seconds() >= state.settings.purge_interval_s):
                await asyncio.to_thread(state.purge, now)
                state.last_purge_at = last_purge = now
        except Exception:
            log.exception("worker tick failed")
        await asyncio.sleep(1)
