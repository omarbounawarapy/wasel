"""All SQL except purge/seed. Timestamps are written only through wasel.clock.utc_iso."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime

from wasel.clock import parse_utc, utc_iso
from wasel.contracts import CustomerHistory, DraftRecord, PriorAssessment, ScoreResult, StructuredFields, WindowMessage
from wasel.ids import IdGen

OPEN = ("collecting", "awaiting_reply", "needs_review", "ready_to_ship")
TERMINAL = ("shipped", "delivered", "refused", "cancelled")


def _j(x) -> str:
    return json.dumps(x, ensure_ascii=False, default=lambda o: asdict(o) if hasattr(o, "__dataclass_fields__") else str(o))


def row(conn, sql, *args) -> sqlite3.Row | None:
    """First row of the query, or None. `args` are the positional SQL parameters."""
    return conn.execute(sql, args).fetchone()


def rows(conn, sql, *args) -> list[sqlite3.Row]:
    """All rows of the query, as a list. `args` are the positional SQL parameters."""
    return conn.execute(sql, args).fetchall()


# ---------------------------------------------------------------- catalog
def upsert_catalog(conn, catalog: dict) -> None:
    """Insert or update the product catalog from the parsed catalog config, keyed by product_id.

    `aliases_json` holds the aliases of every language merged into one sorted, de-duplicated list. Does not open a
    transaction.
    """
    for p in catalog["products"]:
        aliases = sorted({a for v in p["aliases"].values() for a in v})
        conn.execute("INSERT INTO catalog VALUES (?,?,?,?,?) ON CONFLICT(product_id) DO UPDATE SET name=excluded.name,"
                     " aliases_json=excluded.aliases_json, price_tnd=excluded.price_tnd, category=excluded.category",
                     (p["product_id"], p["name"], _j(aliases), p["price_tnd"], p["category"]))


# ---------------------------------------------------------------- customers / conversations / messages
def get_or_create_customer(conn, ids: IdGen, now: datetime, *, sandbox_id, display_name=None, external_ref=None,
                           phone_e164=None, completed_orders=0, refusals_total=0) -> str:
    """Return the customer id, creating the customer if there is no match.

    Lookup is by `phone_e164` when given (global, across sandboxes), otherwise by `external_ref` within `sandbox_id`;
    with neither, a new customer is always created. A match only has `last_seen_at` refreshed: the other arguments
    (name, counters) are ignored. `sandbox_id` None means seeded/event data rather than a visitor's sandbox.
    """
    r = None
    if phone_e164:
        r = row(conn, "SELECT customer_id FROM customers WHERE phone_e164=?", phone_e164)
    elif external_ref:
        r = row(conn, "SELECT customer_id FROM customers WHERE external_ref=? AND COALESCE(sandbox_id,'')=?",
                external_ref, sandbox_id or "")
    if r:
        conn.execute("UPDATE customers SET last_seen_at=? WHERE customer_id=?", (utc_iso(now), r[0]))
        return r[0]
    cid = ids("cus")
    conn.execute("INSERT INTO customers (customer_id, sandbox_id, phone_e164, external_ref, display_name,"
                 " completed_orders, refusals_total, first_seen_at, last_seen_at) VALUES (?,?,?,?,?,?,?,?,?)",
                 (cid, sandbox_id, phone_e164, external_ref, display_name, completed_orders, refusals_total,
                  utc_iso(now), utc_iso(now)))
    return cid


def create_conversation(conn, ids: IdGen, now: datetime, *, customer_id, sandbox_id, channel, seed_key=None) -> str:
    """Insert a conversation for a customer and return its id. `seed_key` links it to a demo fixture, if any."""
    cid = ids("cnv")
    conn.execute("INSERT INTO conversations (conversation_id, customer_id, sandbox_id, channel, seed_key, opened_at)"
                 " VALUES (?,?,?,?,?,?)", (cid, customer_id, sandbox_id, channel, seed_key, utc_iso(now)))
    return cid


def insert_message(conn, ids: IdGen, now: datetime, *, conversation_id, direction, author, origin, kind="text",
                   text=None, canonical_text=None, template_id=None, transcript=None, lat=None, lng=None,
                   provider_ts: datetime | None = None, channel_message_id=None, delivery_status=None,
                   reply_to_message_id=None) -> str | None:
    """Insert a message and return its id, or None if it duplicates an existing `channel_message_id` (the row is skipped).

    Does not link the message to an order. `provider_ts` is the time the provider stamped the message and defaults to
    `now`; `received_at` is always `now`.
    """
    mid = ids("msg")
    cur = conn.execute(
        "INSERT OR IGNORE INTO messages (message_id, conversation_id, channel_message_id, direction, author, origin,"
        " kind, text, canonical_text, template_id, transcript, location_lat, location_lng, reply_to_message_id,"
        " provider_ts, received_at, delivery_status) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (mid, conversation_id, channel_message_id, direction, author, origin, kind, text, canonical_text, template_id,
         transcript, lat, lng, reply_to_message_id, utc_iso(provider_ts or now), utc_iso(now), delivery_status))
    return mid if cur.rowcount else None          # None = duplicate wamid


# ---------------------------------------------------------------- orders
def open_order(conn, conversation_id) -> sqlite3.Row | None:
    """The conversation's order that is not in a terminal status, or None.

    Ingestion only opens a new order when there is none.
    """
    return row(conn, f"SELECT * FROM orders WHERE conversation_id=? AND status IN {OPEN}", conversation_id)


def create_order(conn, ids: IdGen, now: datetime, *, conversation_id, customer_id, sandbox_id,
                 structured: dict | None = None, order_no: int | None = None) -> str:
    """Insert an order for a conversation and return its id. `structured` holds the seller-entered fields.

    Without `order_no`, numbering continues from the highest existing number (the first order is #2601).
    """
    oid = ids("ord")
    if order_no is None:
        order_no = (row(conn, "SELECT COALESCE(MAX(order_no), 2600) FROM orders")[0]) + 1
    conn.execute("INSERT INTO orders (order_id, order_no, conversation_id, customer_id, sandbox_id, structured_json,"
                 " opened_at, updated_at) VALUES (?,?,?,?,?,?,?,?)",
                 (oid, order_no, conversation_id, customer_id, sandbox_id, _j(structured or {}), utc_iso(now),
                  utc_iso(now)))
    return oid


def link(conn, order_id, message_id) -> None:
    """Attach a message to an order's thread. Idempotent."""
    conn.execute("INSERT OR IGNORE INTO order_messages VALUES (?,?)", (order_id, message_id))


def arm_rescore(conn, order_id, trigger: str, due: datetime, now: datetime, *, keep_trigger: bool = True) -> None:
    """pending_trigger = COALESCE(pending_trigger, trigger); a newer message pushes the due time back."""
    conn.execute("UPDATE orders SET pending_trigger = CASE WHEN ? THEN COALESCE(pending_trigger, ?) ELSE ? END,"
                 " pending_rescore_at=?, rescore_state='debouncing', updated_at=? WHERE order_id=?",
                 (int(keep_trigger), trigger, trigger, utc_iso(due), utc_iso(now), order_id))


def get_order(conn, order_id) -> sqlite3.Row | None:
    """The order row, or None."""
    return row(conn, "SELECT * FROM orders WHERE order_id=?", order_id)


def order_messages(conn, order_id) -> list[sqlite3.Row]:
    """Messages linked to the order, oldest first by provider timestamp, then by arrival."""
    return rows(conn, "SELECT m.* FROM messages m JOIN order_messages om ON om.message_id=m.message_id"
                      " WHERE om.order_id=? ORDER BY m.provider_ts, m.received_at", order_id)


def window_messages(conn, order_id) -> list[WindowMessage]:
    """The order's messages as scorer input, oldest first."""
    out = []
    for m in order_messages(conn, order_id):
        ts = parse_utc(m["provider_ts"])
        out.append(WindowMessage(
            message_id=m["message_id"], direction=m["direction"], author=m["author"], origin=m["origin"],
            kind=m["kind"], text=m["text"], canonical_text=m["canonical_text"], template_id=m["template_id"],
            transcript=m["transcript"], has_location=m["kind"] == "location", provider_ts=ts))
    return out


def customer_history(conn, customer_id) -> CustomerHistory:
    """The customer's delivered-plus-refused count and refusal count. Assumes the customer exists."""
    c = row(conn, "SELECT completed_orders, refusals_total FROM customers WHERE customer_id=?", customer_id)
    return CustomerHistory(c["completed_orders"], c["refusals_total"])


def structured(order: sqlite3.Row) -> StructuredFields:
    """The seller-entered fields stored on the order. Fields that were not given come back as None."""
    d = json.loads(order["structured_json"] or "{}")
    return StructuredFields(**{k: d.get(k) for k in ("product_name", "price_tnd", "zone", "quantity")})


def assessments(conn, order_id) -> list[sqlite3.Row]:
    """All assessment rows of the order, ascending by version."""
    return rows(conn, "SELECT * FROM risk_assessments WHERE order_id=? ORDER BY version", order_id)


def current_assessment(conn, order_id) -> sqlite3.Row | None:
    """The order's latest assessment row (highest version), or None if it was never scored."""
    return row(conn, "SELECT * FROM risk_assessments WHERE order_id=? ORDER BY version DESC LIMIT 1", order_id)


def prior_assessment(conn, order_id) -> PriorAssessment | None:
    """The latest assessment converted to the scorer's PriorAssessment, or None if the order was never scored.

    `extraction` is the validated extraction of that version, or None when it has none stored.
    """
    a = current_assessment(conn, order_id)
    if a is None:
        return None
    ext = row(conn, "SELECT validated_json FROM extraction_runs WHERE extraction_id=?", a["extraction_id"]) \
        if a["extraction_id"] else None
    ctx = json.loads(a["context_json"])
    return PriorAssessment(
        version=a["version"], created_at=parse_utc(a["created_at"]), extraction_id=a["extraction_id"],
        extraction=json.loads(ext["validated_json"]) if ext and ext["validated_json"] else None,
        flag_codes=[f["code"] for f in json.loads(a["flags_json"])], features=json.loads(a["features_json"]),
        model_score=a["model_score"], final_score=a["final_score"], tier=a["tier"], path=a["path"],
        reason=a["reason"], points=ctx.get("points", {}), confirmation=a["confirmation"])


# ---------------------------------------------------------------- persist one rescore (one transaction)
MAX_STORED_OUTPUT = 16 * 1024


def _cap_text(s: str | None, limit: int = MAX_STORED_OUTPUT) -> str | None:
    """`s` cut to `limit` characters with a visible marker, so one provider answer cannot bloat the database."""
    if s is None or len(s) <= limit:
        return s
    return s[:limit] + f"…[truncated, {len(s)} characters in all]"


def persist_result(conn, ids: IdGen, now: datetime, order: sqlite3.Row, trigger: str, result: ScoreResult,
                   prior: PriorAssessment | None, next_status: str | None, rescore_state: str) -> str | None:
    """Write one rescore's ScoreResult and update the order. The caller wraps it in a transaction.

    Writes the extraction run and cache entry (a cache row is only replaced by an entry that is at least as primary),
    the next assessment version (prior.version + 1, or 1), the order columns (`rescore_state`, current assessment, the
    resolved order patch, and `status` when `next_status` is given), usage rows, the result's events, and an
    'order.rescored' event. A result without an extraction (no-reply timeout) reuses the prior extraction id.
    Returns the new assessment id, or None when the result has no assessment (not an order).
    """
    oid, sid = order["order_id"], order["sandbox_id"]
    ext_id = None
    if result.extraction is not None:
        x = result.extraction
        ext_id = ids("ext")
        conn.execute(
            "INSERT INTO extraction_runs (extraction_id, order_id, input_message_ids, input_hash, provider, model,"
            " prompt_version, cache_hit, attempts_json, output_json, validated_json, spans_json, valid, dropped_flags,"
            " dropped_quotes, injection_suspected, error, latency_ms, tokens_in, tokens_out, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (ext_id, oid, _j(x.input_message_ids), x.input_hash, x.provider, x.model, x.prompt_version,
             int(x.cache_hit), _j(x.attempts), _cap_text(x.output_json),
             _j(x.validated) if x.validated is not None else None,
             _j(x.spans), int(x.valid), x.dropped_flags, x.dropped_quotes, int(x.injection_suspected), x.error,
             x.latency_ms, x.tokens_in, x.tokens_out, utc_iso(now)))
    elif prior is not None:
        ext_id = prior.extraction_id                      # no_reply_timeout reuses the prior extraction
    if result.cache_put is not None:
        c = result.cache_put
        conn.execute(
            "INSERT INTO extraction_cache VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(input_hash) DO UPDATE SET"
            " prompt_version=excluded.prompt_version, provider=excluded.provider, model=excluded.model,"
            " origin_path=excluded.origin_path, is_primary=excluded.is_primary, extraction_json=excluded.extraction_json,"
            " created_at=excluded.created_at WHERE excluded.is_primary >= extraction_cache.is_primary",
            (c.input_hash, c.prompt_version, c.provider, c.model, c.origin_path, int(c.origin_path == "llm"),
             _j(c.extraction), utc_iso(now)))
    aid = None
    if result.assessment is not None:
        a = result.assessment
        aid = ids("asm")
        version = (prior.version + 1) if prior else 1
        ctx = {**a.context, "points": a.points, "injection_suspected": a.injection_suspected}
        conn.execute(
            "INSERT INTO risk_assessments (assessment_id, order_id, version, trigger, extraction_id, path, features_json,"
            " context_json, model_score, confirmation, adjustments_json, resolved_flags_json, flags_json, final_score,"
            " tier, action, confidence, confidence_reasons_json, reason, reason_short, reason_diff, top_factors_json,"
            " template_id, is_order_change, classifier_version, config_hash, prompt_version, created_at)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (aid, oid, version, trigger, ext_id, a.path, _j(a.features), _j(ctx), a.model_score, a.confirmation,
             _j(a.adjustments), _j(a.resolved_flags), _j(a.flags), a.final_score, a.tier, a.action, a.confidence,
             _j(a.confidence_reasons), a.reason, a.reason_short, a.reason_diff, _j(a.top_factors),
             result.template_id, int(a.is_order_change), a.classifier_version, a.config_hash, a.prompt_version,
             utc_iso(now)))
    sets, vals = ["rescore_state=?", "updated_at=?"], [rescore_state, utc_iso(now)]
    if aid:
        sets.append("current_assessment_id=?")
        vals.append(aid)
    if next_status:
        sets.append("status=?")
        vals.append(next_status)
    if result.order_patch is not None:
        p = result.order_patch
        for col in ("product_id", "product_name", "price_tnd", "quantity", "zone", "zone_source", "address_text",
                    "language"):
            sets.append(f"{col}=?")
            vals.append(getattr(p, col))
    conn.execute(f"UPDATE orders SET {', '.join(sets)} WHERE order_id=?", (*vals, oid))
    for u in result.usage:
        insert_usage(conn, u, sandbox_id=sid, order_id=oid)
    for e in result.events:
        add_event(conn, now, e.type, e.level, order_id=oid, sandbox_id=sid, payload=e.payload)
    add_event(conn, now, "order.rescored", "info", order_id=oid, sandbox_id=sid, entity_id=aid,
              payload={"trigger": trigger, "tier": result.assessment.tier if result.assessment else None,
                       "final_score": result.assessment.final_score if result.assessment else None,
                       "path": result.assessment.path if result.assessment else None})
    return aid


def insert_usage(conn, u, *, sandbox_id, order_id) -> None:
    """Record one LLM provider attempt in llm_usage. `day` is the UTC date of `u.ts`."""
    conn.execute("INSERT INTO llm_usage (ts, day, sandbox_id, order_id, role, provider, model, outcome, tokens_in,"
                 " tokens_out, latency_ms) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                 (utc_iso(u.ts), u.ts.strftime("%Y-%m-%d"), sandbox_id, order_id, u.role, u.provider, u.model,
                  u.outcome, u.tokens_in, u.tokens_out, u.latency_ms))


# ---------------------------------------------------------------- drafts
def unsent_draft(conn, order_id) -> sqlite3.Row | None:
    """An unsent draft of the order, or None. Orders are expected to hold at most one."""
    return row(conn, "SELECT * FROM outbound_drafts WHERE order_id=? AND sent_message_id IS NULL", order_id)


def insert_draft(conn, ids: IdGen, now: datetime, order_id, assessment_id, d: DraftRecord) -> str:
    """Store a drafted message for the order, tied to the assessment it was made from. Returns the draft id."""
    did = ids("drf")
    conn.execute(
        "INSERT INTO outbound_drafts (draft_id, order_id, assessment_id, template_id, language, canonical_text,"
        " rendered_text, source, prefilter_json, judge_json, route, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (did, order_id, assessment_id, d.template_id, d.language, d.canonical_text, d.rendered_text, d.source,
         _j(d.prefilter), _j(d.judge) if d.judge is not None else None, d.route, utc_iso(now)))
    return did


def mark_draft_sent(conn, ids: IdGen, now: datetime, draft: sqlite3.Row, *, origin: str, delivery: str,
                    decided_by: str, channel_message_id: str | None = None) -> str:
    """Record a draft as sent and return the new outbound message id.

    Adds the message (author 'ai', text as sent, canonical text kept) to the order's thread, stamps the draft, sets
    `last_outbound_at` on the conversation and `awaiting_reply_since` on the order, and counts it in
    `auto_messages_sent` only when `decided_by` is 'system'. `delivery_status` starts as 'sent' only for
    'whatsapp_sent'. This does not send anything: the caller has already sent (or decided not to send) the message.
    """
    order = get_order(conn, draft["order_id"])
    mid = insert_message(conn, ids, now, conversation_id=order["conversation_id"], direction="outbound", author="ai",
                         origin=origin, text=draft["rendered_text"], canonical_text=draft["canonical_text"],
                         template_id=draft["template_id"], delivery_status="sent" if delivery == "whatsapp_sent" else None,
                         channel_message_id=channel_message_id)
    link(conn, order["order_id"], mid)
    conn.execute("UPDATE outbound_drafts SET sent_message_id=?, sent_at=?, delivery=?, decided_by=? WHERE draft_id=?",
                 (mid, utc_iso(now), delivery, decided_by, draft["draft_id"]))
    conn.execute("UPDATE conversations SET last_outbound_at=? WHERE conversation_id=?",
                 (utc_iso(now), order["conversation_id"]))
    conn.execute("UPDATE orders SET awaiting_reply_since=?, updated_at=?,"
                 " auto_messages_sent = auto_messages_sent + ? WHERE order_id=?",
                 (utc_iso(now), utc_iso(now), int(decided_by == "system"), order["order_id"]))
    return mid


# ---------------------------------------------------------------- events
def add_event(conn, now: datetime, type_: str, level: str = "info", *, order_id=None, sandbox_id=None, entity_id=None,
              payload: dict | None = None) -> None:
    """Append a row to the activity log. `entity_id` is the id of the related row (message, draft, assessment)."""
    conn.execute("INSERT INTO events (ts, type, level, order_id, sandbox_id, entity_id, payload) VALUES (?,?,?,?,?,?,?)",
                 (utc_iso(now), type_, level, order_id, sandbox_id, entity_id, _j(payload or {})))
