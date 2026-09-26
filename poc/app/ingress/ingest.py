"""store_inbound(): the ONE path for whatsapp / csv / paste / simulate / seed (01 §5.1)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.db import repo
from app.ids import IdGen

TRIGGER_FOR = {"collecting": "initial", "awaiting_reply": "customer_reply", "needs_review": "customer_reply",
               "ready_to_ship": "customer_reply"}


@dataclass(frozen=True)
class Stored:
    order_id: str
    message_id: str | None
    conversation_id: str
    created_order: bool


def store_inbound(conn, ids: IdGen, now: datetime, *, conversation_id: str, origin: str, text: str | None,
                  kind: str = "text", lat: float | None = None, lng: float | None = None,
                  transcript: str | None = None, provider_ts: datetime | None = None,
                  channel_message_id: str | None = None, reply_to_message_id: str | None = None,
                  debounce_s: float = 4, no_debounce: bool = False, structured: dict | None = None) -> Stored:
    """Caller holds the transaction. Links the message to the conversation's open order (or opens one) and arms a
    debounced rescore. Duplicate wamids and outbound messages never arm a rescore."""
    conv = repo.row(conn, "SELECT * FROM conversations WHERE conversation_id=?", conversation_id)
    mid = repo.insert_message(conn, ids, now, conversation_id=conversation_id, direction="inbound", author="customer",
                              origin=origin, kind=kind, text=text, transcript=transcript, lat=lat, lng=lng,
                              provider_ts=provider_ts, channel_message_id=channel_message_id,
                              reply_to_message_id=reply_to_message_id)
    order = repo.open_order(conn, conversation_id)
    if mid is None:                                                    # duplicate (W-6)
        return Stored(order["order_id"] if order else "", None, conversation_id, False)
    created = order is None
    if created:
        oid = repo.create_order(conn, ids, now, conversation_id=conversation_id, customer_id=conv["customer_id"],
                                sandbox_id=conv["sandbox_id"], structured=structured)
        status = "collecting"
    else:
        oid, status = order["order_id"], order["status"]
    repo.link(conn, oid, mid)
    conn.execute("UPDATE conversations SET last_inbound_at=? WHERE conversation_id=?",
                 (repo.utc_iso(now), conversation_id))
    due = now if no_debounce else now + timedelta(seconds=debounce_s)
    repo.arm_rescore(conn, oid, TRIGGER_FOR[status], due, now)
    repo.add_event(conn, now, "message.received", "info", order_id=oid, sandbox_id=conv["sandbox_id"],
                   entity_id=mid, payload={"origin": origin, "kind": kind})
    return Stored(oid, mid, conversation_id, created)
