"""process_due(): the sync worker step tests call directly. run_loop() wraps it in
asyncio.to_thread every second. No clock reads and no sleeps in process_due."""
from __future__ import annotations

import asyncio
import logging
import sqlite3
import threading
import time
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


class OrderTimeout(Exception):
    """Scoring one order ran past its hard time limit."""


def score_with_deadline(scorer: Scorer, inp: ScoreInput, timeout_s: float | None):
    """Run scorer(inp) on a daemon thread and wait at most `timeout_s`; raise OrderTimeout if it is still running.

    Python cannot kill a thread, so a timed-out scorer is abandoned: its result is discarded and it ends when it ends.
    It only works on `inp` (a value) and never on the worker's transaction; the worker writes the result itself, so
    the abandoned thread cannot change order state. Its only possible database use is one autocommit statement
    (extraction cache or usage meter), which is harmless. With no timeout the scorer runs inline.
    """
    if timeout_s is None:
        return scorer(inp)
    box: dict = {}

    def run() -> None:
        try:
            box["result"] = scorer(inp)
        except BaseException as e:                          # handed back to the caller's thread
            box["error"] = e

    t = threading.Thread(target=run, name="score-order", daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        raise OrderTimeout(f"scoring did not finish within {timeout_s:g} s")
    if "error" in box:
        raise box["error"]
    return box["result"]


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
    """Assemble the scorer's input for an order from the database. Read-only."""
    prior = repo.prior_assessment(conn, order["order_id"])
    conv = repo.row(conn, "SELECT channel FROM conversations WHERE conversation_id=?", order["conversation_id"])
    return ScoreInput(order_id=order["order_id"], sandbox_id=order["sandbox_id"], channel=conv["channel"],
                      trigger=trigger, messages=repo.window_messages(conn, order["order_id"]),
                      structured=repo.structured(order), customer=repo.customer_history(conn, order["customer_id"]),
                      prior=prior, now=now)


def draft_request(conn, order_id: str, now: datetime, template_id: str) -> DraftRequest:
    """Build the DraftRequest for an order's current assessment. Read-only.

    Slots come from the order and customer records; `customer_recent` is the last 3 inbound texts with phone numbers
    masked. Language defaults to 'mixed' when the order has none.
    """
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
    """Draft a message for the order and store it. Returns the draft id, or None if there is nothing to do.

    None means an unsent draft already exists or the order was never assessed. The template is `template_id`, else the
    one recorded on the current assessment, else T_CONFIRM. Also records the drafter's LLM usage and events. The caller
    holds the transaction.
    """
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
                no_reply_s: float | None = None, meter=None, only_order_id: str | None = None,
                budget_s: float | None = None, order_timeout_s: float | None = None) -> list[str]:
    """Score every order whose rescore is due at `now`, up to `limit`, and return the ids that were scored.

    With `only_order_id` only that order is considered. With `budget_s` no further order is taken once that many
    seconds have passed since the call started, so a queue of slow orders is spread over several ticks.
    With `order_timeout_s` one order's scoring is abandoned after that many seconds (see score_with_deadline); the
    order goes to 'needs_review' with an error event whose reason is 'order_timeout', and is not re-armed.

    Each order is claimed atomically, scored outside a transaction, then its result, next status and events are written
    in one transaction; a draft is created afterwards if the order is now awaiting a reply. With `no_reply_s`, orders
    that have waited that long for a reply are first queued for a no-reply rescore. A failure in one order puts it in
    'needs_review' (unless already terminal), logs an error event and does not re-arm it; other orders continue.
    """
    if no_reply_s is not None:
        with tx(conn):
            fire_no_reply_timeouts(conn, now, no_reply_s)
    done: list[str] = []
    started = time.monotonic()
    only_sql, only_args = (" AND order_id=?", (only_order_id,)) if only_order_id else ("", ())
    for _ in range(limit):
        if budget_s is not None and time.monotonic() - started >= budget_s:
            break
        cand = repo.row(conn, "SELECT order_id, pending_rescore_at, pending_trigger FROM orders WHERE pending_rescore_at"
                              " IS NOT NULL AND pending_rescore_at <= ?" + only_sql + " ORDER BY pending_rescore_at"
                              " LIMIT 1", utc_iso(now), *only_args)
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
            result = score_with_deadline(scorer, inp, order_timeout_s)
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
        except OrderTimeout as e:
            log.error("rescore timed out for %s: %s", oid, e)
            with tx(conn):
                conn.execute("UPDATE orders SET status=CASE WHEN status IN ('shipped','delivered','refused','cancelled')"
                             " THEN status ELSE 'needs_review' END, rescore_state='idle' WHERE order_id=?", (oid,))
                repo.add_event(conn, now, "error", "error", order_id=oid,
                               payload={"where": "rescore", "reason": "order_timeout",
                                        "error": f"Needs review: scoring took longer than {order_timeout_s:g} s"})
        except Exception as e:                              # a failed rescore is never re-armed automatically
            log.exception("rescore failed for %s", oid)
            with tx(conn):
                conn.execute("UPDATE orders SET status=CASE WHEN status IN ('shipped','delivered','refused','cancelled')"
                             " THEN status ELSE 'needs_review' END, rescore_state='idle' WHERE order_id=?", (oid,))
                repo.add_event(conn, now, "error", "error", order_id=oid,
                               payload={"where": "rescore", "error": type(e).__name__})   # the text stays in the log
    return done


def drain(conn, now: datetime, scorer: Scorer, drafter: Drafter, *, ids: IdGen, max_rounds: int = 200,
          only_order_id: str | None = None, order_timeout_s: float | None = None) -> int:
    """Run process_due until nothing is due (seeding, tests); with `only_order_id`, for that order alone."""
    n = 0
    for _ in range(max_rounds):
        got = process_due(conn, now, scorer, drafter, ids=ids, only_order_id=only_order_id,
                          order_timeout_s=order_timeout_s)
        if not got:
            break
        n += len(got)
    return n


async def run_loop(state, interval_s: float = 1.0) -> None:
    """state: app.main.AppState. Two tasks: the tick (budgeted) and housekeeping (snapshot, purge in public mode).

    They run apart so a slow model in a tick cannot delay the snapshot or the purge.
    """
    async def ticks() -> None:
        while True:
            now = state.clock.now()
            try:
                await asyncio.to_thread(state.tick, now)
                state.last_tick_at = now
            except Exception:
                log.exception("worker tick failed")
            await asyncio.sleep(interval_s)

    async def housekeeping() -> None:
        last_purge = None
        while True:
            now = state.clock.now()
            try:
                await asyncio.to_thread(state.snapshot, now)
                if state.settings.is_public and (last_purge is None or
                                                 (now - last_purge).total_seconds() >= state.settings.purge_interval_s):
                    await asyncio.to_thread(state.purge, now)
                    state.last_purge_at = last_purge = now
            except Exception:
                log.exception("worker housekeeping failed")
            await asyncio.sleep(interval_s)

    await asyncio.gather(ticks(), housekeeping())
