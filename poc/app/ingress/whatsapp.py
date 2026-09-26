"""WhatsApp Cloud API webhook, pure half (01 §1, 04 §4, SD §9): signature check and payload walk.
No DB, no clock, no logging of payload content. The route (app/api/routes_webhook.py) owns I/O."""
from __future__ import annotations

import hashlib
import hmac
import re
from dataclasses import dataclass
from datetime import UTC, datetime

SIG_RE = re.compile(r"^sha256=[0-9a-f]{64}$")
WA_ID_RE = re.compile(r"^[1-9][0-9]{6,14}$")
MAX_CHALLENGE = 128
STATUS_RANK = {"sent": 1, "delivered": 2, "read": 3, "failed": 4}


def verify_signature(secret: str, raw: bytes, header: str | None) -> str | None:
    """None if the X-Hub-Signature-256 header matches HMAC-SHA256(secret, raw), else the rejection reason."""
    if not header:
        return "missing"
    if not SIG_RE.match(header):
        return "malformed"
    if not secret:                                          # never reached while mounted (W-1); fail closed anyway
        return "no_secret"
    expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return None if hmac.compare_digest(expected, header) else "mismatch"


def verify_challenge(params, verify_token: str) -> str | None:
    """W-2: the challenge to echo, or None (→ 403)."""
    token, challenge = params.get("hub.verify_token") or "", params.get("hub.challenge") or ""
    if (params.get("hub.mode") != "subscribe" or not verify_token or not challenge or len(challenge) > MAX_CHALLENGE
            or not hmac.compare_digest(token.encode(), verify_token.encode())):
        return None
    return challenge


@dataclass(frozen=True)
class Inbound:
    wamid: str
    wa_id: str                       # sender; stored as customers.phone_e164 only, never logged
    profile_name: str | None
    ts: datetime
    kind: str                        # text | location | unsupported
    wa_type: str                     # Meta's type, for the event payload
    text: str | None = None
    lat: float | None = None
    lng: float | None = None
    context_id: str | None = None    # wamid the customer quoted


@dataclass(frozen=True)
class Status:
    wamid: str
    status: str                      # sent | delivered | read | failed
    ts: datetime


@dataclass
class Batch:
    messages: list[Inbound]
    statuses: list[Status]
    ignored_foreign: int = 0         # changes for another phone_number_id (W-5)
    skipped: int = 0                 # entries missing required fields


def _ts(v) -> datetime | None:
    try:
        return datetime.fromtimestamp(int(v), UTC)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _message(m: dict, names: dict[str, str]) -> Inbound | None:
    wamid, wa_id, ts, typ = m.get("id"), str(m.get("from") or ""), _ts(m.get("timestamp")), m.get("type")
    if not (isinstance(wamid, str) and wamid and WA_ID_RE.match(wa_id) and ts and isinstance(typ, str)):
        return None
    ctx = m.get("context") if isinstance(m.get("context"), dict) else {}
    base = dict(wamid=wamid, wa_id=wa_id, profile_name=names.get(wa_id), ts=ts, wa_type=typ,
                context_id=ctx.get("id") if isinstance(ctx.get("id"), str) else None)
    if typ == "text":
        body = (m.get("text") or {}).get("body")
        if isinstance(body, str) and body.strip():
            return Inbound(kind="text", text=body, **base)
    elif typ == "location":
        loc = m.get("location") or {}
        try:
            lat, lng = float(loc["latitude"]), float(loc["longitude"])
        except (KeyError, TypeError, ValueError):
            lat = lng = None
        if lat is not None and -90 <= lat <= 90 and -180 <= lng <= 180:
            return Inbound(kind="location", lat=lat, lng=lng, **base)
    # audio, image, sticker, video, document, reaction, interactive, unknown... → unsupported → needs_review (SD §9)
    return Inbound(kind="unsupported", **base)


def parse_payload(payload, phone_number_id: str) -> Batch:
    """Walk entry[].changes[].value. messages[] → Inbound (sorted by provider timestamp, stable), statuses[] → Status.
    Changes addressed to another phone_number_id are counted and dropped."""
    out = Batch([], [])
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return out
    for entry in payload.get("entry") or []:
        for change in (entry.get("changes") or []) if isinstance(entry, dict) else []:
            value = change.get("value") if isinstance(change, dict) else None
            if not isinstance(value, dict):
                continue
            pnid = str((value.get("metadata") or {}).get("phone_number_id") or "")
            if not phone_number_id or pnid != phone_number_id:
                out.ignored_foreign += 1
                continue
            names = {str(c.get("wa_id")): c["profile"]["name"] for c in value.get("contacts") or []
                     if isinstance(c, dict) and isinstance((c.get("profile") or {}).get("name"), str)}
            for m in value.get("messages") or []:
                msg = _message(m, names) if isinstance(m, dict) else None
                if msg is None:
                    out.skipped += 1
                else:
                    out.messages.append(msg)
            for s in value.get("statuses") or []:
                ts = _ts(s.get("timestamp")) if isinstance(s, dict) else None
                if ts and isinstance(s.get("id"), str) and s.get("status") in STATUS_RANK:
                    out.statuses.append(Status(s["id"], s["status"], ts))
                else:
                    out.skipped += 1
    out.messages.sort(key=lambda m: m.ts)
    out.statuses.sort(key=lambda s: s.ts)
    return out
