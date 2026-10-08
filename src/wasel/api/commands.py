"""Mutations behind the /api routes, callable without HTTP (routes stay thin; tests and scripts reuse these).
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta

from wasel.api.errors import ApiError, invalid_transition, not_found, seeded_read_only
from wasel.clock import parse_utc, utc_iso
from wasel.contracts import Drafter
from wasel.db import repo
from wasel.db.conn import tx
from wasel.db.seed import fixture_for, seed_conversation
from wasel.ids import IdGen
from wasel.ingress.ingest import store_inbound
from wasel.settings import Settings
from wasel.state import ACTIONS, TERMINAL, allowed_actions


# ---------------------------------------------------------------- visibility
def visible_order(conn, order_id: str, settings: Settings, vid: str | None):
    """Return the order row, or raise 404 if it doesn't exist or (public mode) belongs to another visitor."""
    o = repo.get_order(conn, order_id)
    if o is None:
        raise not_found()
    if settings.is_public and o["sandbox_id"] is not None and o["sandbox_id"] != vid:
        raise not_found()                                 # another visitor's row: existence not revealed
    return o


def writable_order(conn, order_id: str, settings: Settings, vid: str | None):
    """visible_order plus a write check: raises 409 SEEDED_READ_ONLY for seeded orders in public mode."""
    o = visible_order(conn, order_id, settings, vid)
    if settings.is_public and o["sandbox_id"] is None:
        raise seeded_read_only()
    return o


def _sandbox_limits(conn, settings: Settings, vid: str | None) -> None:
    """Public mode only: refuse (429) when this visitor already has `sandbox_max_orders` orders (SANDBOX_LIMIT) or the
    demo holds `sandbox_global_max` sandbox orders in total (DEMO_BUSY).
    """
    if not settings.is_public:
        return
    mine = conn.execute("SELECT COUNT(*) FROM orders WHERE sandbox_id=?", (vid,)).fetchone()[0]
    if mine >= settings.sandbox_max_orders:
        raise ApiError(429, "SANDBOX_LIMIT", f"this browser already has {mine} demo orders")
    total = conn.execute("SELECT COUNT(*) FROM orders WHERE sandbox_id IS NOT NULL").fetchone()[0]
    if total >= settings.sandbox_global_max:
        raise ApiError(429, "DEMO_BUSY", "Demo busy, try again in a minute or open a sample order")


def _debounce(settings: Settings, cfg: dict) -> float:
    return cfg["timeouts"]["debounce_s"]["demo" if settings.demo_mode else "prod"]


# ---------------------------------------------------------------- ingest
def ingest_paste(conn, ids: IdGen, now: datetime, settings: Settings, cfg: dict, vid: str | None, *, text: str,
                 customer_name: str | None = None, structured: dict | None = None) -> dict:
    """Create a customer, conversation and order from one pasted message and arm a debounced rescore.
    Returns the created ids.

    Raises ApiError 422/413 when `text` is empty or over 2000 characters, and 429 when a public-mode sandbox limit
    is hit.
    In public mode the order belongs to visitor `vid` and `customer_name` is ignored. Runs in one transaction.
    """
    if not 1 <= len(text) <= 2000:
        raise ApiError(413 if len(text) > 2000 else 422, "PAYLOAD_TOO_LARGE" if len(text) > 2000 else "VALIDATION_ERROR",
                       "paste text must be 1..2000 characters")
    _sandbox_limits(conn, settings, vid)
    with tx(conn):
        return _insert_paste(conn, ids, now, settings, cfg, vid, text, customer_name, structured)


def _insert_paste(conn, ids: IdGen, now: datetime, settings: Settings, cfg: dict, vid: str | None, text: str,
                  customer_name: str | None, structured: dict | None, external_ref: str | None = None) -> dict:
    """The rows of one pasted order. The caller holds the transaction."""
    sid = vid if settings.is_public else None
    cid = repo.get_or_create_customer(conn, ids, now, sandbox_id=sid, external_ref=external_ref,
                                      display_name=None if settings.is_public else customer_name)
    conv = repo.create_conversation(conn, ids, now, customer_id=cid, sandbox_id=sid, channel="paste")
    st = store_inbound(conn, ids, now, conversation_id=conv, origin="paste", text=text,
                       debounce_s=_debounce(settings, cfg), structured={k: v for k, v in (structured or {}).items()
                                                                       if v is not None})
    o = repo.get_order(conn, st.order_id)
    return {"order_id": st.order_id, "order_ref": f"#{o['order_no']}", "conversation_id": conv,
            "message_id": st.message_id}


CSV_HEADER = ["customer_id", "customer_name", "product", "price_tnd", "zone", "address", "note"]


def ingest_csv(conn, ids: IdGen, now: datetime, settings: Settings, cfg: dict, vid: str | None, csv_text: str) -> tuple:
    """Ingest up to 10 (public) or 200 rows as pasted orders. Returns (created, rejected).

    Each row's text is address + note. Rows with no text, an unknown zone, a price that is not a number between 0
    and 1,000,000 or a name over the length limit are rejected with a 1-based row number and the rest go on; a
    larger file raises 413. A file with no `address` or `note` column, no data rows or unreadable CSV raises 422. The
    `customer_id` column is stored as the customer's external reference, so rows with the same id share one customer
    and its history (per visitor in public mode). All accepted rows are inserted in one transaction, so an
    error part-way leaves no rows behind.
    """
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        rows_ = list(reader)
    except csv.Error as e:
        raise ApiError(422, "VALIDATION_ERROR", f"unreadable CSV: {e}") from None
    if not {"address", "note"} & set(reader.fieldnames or []):
        raise ApiError(422, "VALIDATION_ERROR", "the header needs an address or a note column: " + ",".join(CSV_HEADER))
    if not rows_:
        raise ApiError(422, "VALIDATION_ERROR", "the CSV has a header but no rows")
    limit = 10 if settings.is_public else 200
    if len(rows_) > limit:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", f"CSV has {len(rows_)} rows; the limit is {limit}")
    accepted, rejected = [], []
    for i, r in enumerate(rows_, start=1):
        text = " ".join(x for x in ((r.get("address") or "").strip(), (r.get("note") or "").strip()) if x)
        zone = (r.get("zone") or "").strip().lower() or None
        name = (r.get("customer_name") or "").strip() or None
        product = (r.get("product") or "").strip() or None
        price, why = None, None
        if not text:
            why = "address and note are both empty"
        elif zone and zone not in ("urban", "suburban", "rural"):
            why = f"unknown zone {zone!r}"
        elif name and len(name) > 40 or product and len(product) > 80:
            why = "customer_name is over 40 characters or product over 80"
        else:
            try:
                price = float(r["price_tnd"]) if (r.get("price_tnd") or "").strip() else None
                if price is not None and not 0 <= price <= 1_000_000:       # also rejects nan and inf
                    raise ValueError
            except ValueError:
                why = "price_tnd is not a number between 0 and 1000000"
        if why is None:
            try:
                for cell in (text, name, product):
                    (cell or "").encode("utf-8")
            except UnicodeEncodeError:
                why = "contains a character that is not valid text"
        if why:
            rejected.append({"row": i, "reason": why})
        else:
            ext = (r.get("customer_id") or "").strip()[:60] or None
            accepted.append((text[:2000], name, {"product_name": product, "price_tnd": price, "zone": zone}, ext))
    created = []
    with tx(conn):
        for text, name, structured, ext in accepted:
            _sandbox_limits(conn, settings, vid)
            created.append(_insert_paste(conn, ids, now, settings, cfg, vid, text, name, structured, ext))
    return created, rejected


# ---------------------------------------------------------------- try this order (zero LLM calls)
def try_order(conn, ids: IdGen, now: datetime, settings: Settings, order_id: str, vid: str) -> dict:
    """Copy a seeded sample order into the visitor's sandbox, without an LLM call. Returns the new order's ids.

    Raises 409 NOT_SEEDED if the order has no seed fixture. The copy is not scored here; the caller drains the worker.
    """
    o = visible_order(conn, order_id, settings, vid)
    conv = repo.row(conn, "SELECT seed_key FROM conversations WHERE conversation_id=?", o["conversation_id"])
    fx = fixture_for(conv["seed_key"]) if conv["seed_key"] else None
    if fx is None:
        raise ApiError(409, "NOT_SEEDED", "only sample orders can be tried")
    _sandbox_limits(conn, settings, vid)
    new_oid = seed_conversation(conn, ids, now, fx, vid)
    n = repo.get_order(conn, new_oid)
    return {"order_id": new_oid, "order_ref": f"#{n['order_no']}", "conversation_id": n["conversation_id"]}


# ---------------------------------------------------------------- simulate a customer reply
def simulate_reply(conn, ids: IdGen, now: datetime, settings: Settings, cfg: dict, vid: str | None,
                   conversation_id: str, *, text: str | None = None, lat: float | None = None,
                   lng: float | None = None) -> dict:
    """Add a simulated customer reply (text or location pin) to a conversation and arm a rescore.

    If the order has an unsent draft it is first recorded as sent, since the reply implies it went out. Raises 404 for
    unknown or foreign conversations, 409 on seeded ones (public), 413 above 600 characters, 429 past `reply_limit` in
    public mode. Returns the message id and when the rescore is due.
    """
    conv = repo.row(conn, "SELECT * FROM conversations WHERE conversation_id=?", conversation_id)
    if conv is None or (settings.is_public and conv["sandbox_id"] not in (None, vid)):
        raise not_found("conversation")
    if settings.is_public and conv["sandbox_id"] is None:
        raise seeded_read_only()
    if text is not None and len(text) > 600:
        raise ApiError(413, "PAYLOAD_TOO_LARGE", "a simulated reply is at most 600 characters")
    if settings.is_public:
        n = conn.execute("SELECT COUNT(*) FROM messages WHERE conversation_id=? AND origin='simulated' AND"
                         " direction='inbound'", (conversation_id,)).fetchone()[0]
        if n >= settings.reply_limit:
            raise ApiError(429, "REPLY_LIMIT", f"{settings.reply_limit} simulated replies per conversation")
    recorded = None
    with tx(conn):
        order = repo.open_order(conn, conversation_id)
        if order is not None and (d := repo.unsent_draft(conn, order["order_id"])) is not None:
            repo.mark_draft_sent(conn, ids, now, d, origin="simulated", delivery="recorded_only", decided_by="human")
            repo.add_event(conn, now, "draft.recorded_for_simulation", "info", order_id=order["order_id"],
                           sandbox_id=conv["sandbox_id"], entity_id=d["draft_id"])
            recorded = d["draft_id"]
        kind = "location" if text is None else "text"
        st = store_inbound(conn, ids, now, conversation_id=conversation_id, origin="simulated", text=text,
                           kind=kind, lat=lat, lng=lng, provider_ts=now + timedelta(microseconds=1),
                           debounce_s=_debounce(settings, cfg))     # +1 µs: sorts after the recorded draft
    o = repo.get_order(conn, st.order_id)
    return {"message_id": st.message_id, "order_id": st.order_id, "rescore_at": o["pending_rescore_at"],
            "recorded_draft_id": recorded}


# ---------------------------------------------------------------- rescore / actions / send
def rescore(conn, now: datetime, settings: Settings, vid: str | None, order_id: str) -> dict:
    """Schedule an immediate manual rescore (state 'debouncing', due now); the worker does the scoring.

    Raises 409 INVALID_TRANSITION for orders in a terminal status.
    """
    o = writable_order(conn, order_id, settings, vid)
    if o["status"] in TERMINAL:
        raise invalid_transition(allowed_actions(o["status"]))
    with tx(conn):
        repo.arm_rescore(conn, order_id, "manual", now, now, keep_trigger=False)
    return {"order_id": order_id, "rescore_state": "debouncing", "rescore_at": utc_iso(now)}


def apply_action(conn, ids: IdGen, now: datetime, settings: Settings, vid: str | None, order_id: str, action: str,
                 drafter: Drafter) -> None:
    """Apply a seller action: move the order to the action's target status and log an order.<action> event.

    Raises 409 if the action is unknown or not allowed from the current status. 'approve' stamps seller_approved_at,
    'mark_delivered'/'mark_refused' update the customer's history counters, and 'request_confirmation' creates a draft.
    One transaction.
    """
    o = writable_order(conn, order_id, settings, vid)
    if action not in ACTIONS or o["status"] not in ACTIONS[action][0]:
        raise invalid_transition(allowed_actions(o["status"]))
    to = ACTIONS[action][1]
    with tx(conn):
        conn.execute("UPDATE orders SET status=?, updated_at=? WHERE order_id=?", (to, utc_iso(now), order_id))
        if to in TERMINAL:                              # a rescore armed before the action must not outlive it
            conn.execute("UPDATE orders SET pending_rescore_at=NULL, pending_trigger=NULL, rescore_state='idle'"
                         " WHERE order_id=?", (order_id,))
        if action == "approve":
            conn.execute("UPDATE orders SET seller_approved_at=? WHERE order_id=?", (utc_iso(now), order_id))
        elif action in ("mark_delivered", "mark_refused"):
            conn.execute("UPDATE customers SET completed_orders = completed_orders + 1,"
                         " refusals_total = refusals_total + ? WHERE customer_id=?",
                         (int(action == "mark_refused"), o["customer_id"]))
        elif action == "request_confirmation":
            from wasel.worker import create_draft
            create_draft(conn, ids, now, order_id, drafter, None)
        repo.add_event(conn, now, f"order.{action}", "info", order_id=order_id, sandbox_id=o["sandbox_id"])


WA_WINDOW = timedelta(hours=24)


def send_draft(conn, ids: IdGen, now: datetime, settings: Settings, vid: str | None, draft_id: str,
               sender=None, *, decided_by: str = "human") -> dict:
    """Send a draft: record it as an outbound message, or send it through WhatsApp when that is effective.

    Real sends happen only for WhatsApp conversations when sending is effective and `sender` is given, and only within the
    customer's 24 h window. Otherwise the draft is recorded as sent ('recorded_only') without leaving the system.
    `decided_by='system'` is only accepted for auto_send drafts. Raises 404/409 (already sent, blocked, needs review,
    outside the 24 h window, no recipient) and 502 if WhatsApp refuses; the failure is logged as an event.
    """
    d = repo.row(conn, "SELECT * FROM outbound_drafts WHERE draft_id=?", draft_id)
    if d is None:
        raise not_found("draft")
    o = writable_order(conn, d["order_id"], settings, vid)
    if d["sent_message_id"]:
        raise ApiError(409, "ALREADY_SENT", "this draft was already sent")
    if d["route"] == "blocked":
        raise ApiError(409, "DRAFT_BLOCKED", "this draft failed the prefilter")
    if decided_by == "system" and d["route"] != "auto_send":
        raise ApiError(409, "NEEDS_REVIEW", "only an auto_send draft goes out without a human click")
    conv = repo.row(conn, "SELECT * FROM conversations WHERE conversation_id=?", o["conversation_id"])
    delivery, origin, wamid = "recorded_only", "dashboard", None
    if conv["channel"] == "whatsapp" and settings.wa_send_effective and sender is not None:
        # free-form text is only allowed inside the 24 h customer-service window
        last_in = conv["last_inbound_at"]
        if not last_in or now - parse_utc(last_in) > WA_WINDOW:
            raise ApiError(409, "OUTSIDE_24H_WINDOW", "the customer's last message is older than 24 h")
        cust = repo.row(conn, "SELECT phone_e164 FROM customers WHERE customer_id=?", o["customer_id"])
        if not cust or not cust["phone_e164"]:
            raise ApiError(409, "NO_RECIPIENT", "this customer has no WhatsApp number")
        from wasel.outbound.whatsapp_send import SendFailed
        try:
            wamid = sender.send_text(cust["phone_e164"], d["rendered_text"])
        except SendFailed as e:
            with tx(conn):
                repo.add_event(conn, now, "draft.send_failed", "error", order_id=o["order_id"],
                               sandbox_id=o["sandbox_id"], entity_id=draft_id, payload={"reason": e.reason})
            raise ApiError(502, "WHATSAPP_SEND_FAILED", f"WhatsApp refused the message ({e.reason})") from e
        delivery, origin = "whatsapp_sent", "whatsapp"
    with tx(conn):
        mid = repo.mark_draft_sent(conn, ids, now, d, origin=origin, delivery=delivery, decided_by=decided_by,
                                   channel_message_id=wamid)
        repo.add_event(conn, now, "draft.sent", "success", order_id=o["order_id"], sandbox_id=o["sandbox_id"],
                       entity_id=draft_id, payload={"delivery": delivery, "decided_by": decided_by,
                                                    "source": d["source"]})
    return {"draft_id": draft_id, "sent_message_id": mid, "sent_at": utc_iso(now), "delivery": delivery}


def auto_send_due(conn, ids: IdGen, now: datetime, settings: Settings, sender) -> list[str]:
    """Send every unsent auto_send draft (WA_AUTO_SEND, never in public mode). route=auto_send already means
    the auto_send gate passed (route.py): the classifier cleared the draft, confidence high, price under the
    cap, loop guard and 24 h window. Real WhatsApp conversations go out through the Cloud API; any other
    channel records the send as simulated, so the threshold loop is visible in the demo. Failures stay
    unsent and visible for a human."""
    if not settings.wa_auto_send or settings.is_public:
        return []
    sent = []
    for d in conn.execute("SELECT d.draft_id FROM outbound_drafts d JOIN orders o ON o.order_id=d.order_id"
                          " WHERE d.sent_message_id IS NULL AND d.route='auto_send'"
                          " AND o.sandbox_id IS NULL").fetchall():
        try:
            send_draft(conn, ids, now, settings, None, d["draft_id"], sender, decided_by="system")
            sent.append(d["draft_id"])
        except ApiError:
            continue
    return sent
