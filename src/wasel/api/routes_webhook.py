"""/webhook/whatsapp. Included by create_app ONLY when
settings.webhook_mounted (never in public mode, never with a short secret or verify token). No skip-signature flag.
Logs carry counts and reasons only: never the body, the sender's number, or a secret."""
from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from wasel.db import repo
from wasel.db.conn import tx
from wasel.ingress import whatsapp as wa
from wasel.ingress.ingest import store_inbound

log = logging.getLogger("cod.webhook")
MAX_WEBHOOK_BODY = 1024 * 1024
webhook = APIRouter()


class RedactVerifyToken(logging.Filter):
    """uvicorn's access log prints the full query string; Meta's verify GET carries hub.verify_token in it."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Replace the query string of a logged verify request with `?<redacted>`. Always keeps the record."""
        args = record.args
        if isinstance(args, tuple) and len(args) >= 3 and isinstance(args[2], str) and "hub." in args[2]:
            record.args = (*args[:2], args[2].split("?", 1)[0] + "?<redacted>", *args[3:])
        return True


def install_log_redaction() -> None:
    """Attach RedactVerifyToken to the uvicorn access logger once (idempotent)."""
    access = logging.getLogger("uvicorn.access")
    if not any(isinstance(f, RedactVerifyToken) for f in access.filters):
        access.addFilter(RedactVerifyToken())


@webhook.get("/webhook/whatsapp")
def verify(request: Request):
    """Meta's webhook verification handshake: echo the challenge, or 403 if the verify token doesn't match."""
    challenge = wa.verify_challenge(request.query_params, request.app.state.core.settings.wa_verify_token)
    if challenge is None:
        log.warning("webhook verify refused")
        return Response(status_code=403)
    log.info("webhook verify ok")
    return PlainTextResponse(challenge, 200)


def _too_large() -> JSONResponse:
    return JSONResponse({"error": {"code": "PAYLOAD_TOO_LARGE", "message": "webhook body over 1 MiB"}},
                        status_code=413)


@webhook.post("/webhook/whatsapp")
async def receive(request: Request):
    """Accept a WhatsApp webhook POST.

    Checks the size cap and the X-Hub-Signature-256 signature on the raw body (401 and a webhook.rejected event on
    failure), then stores the payload and answers 200 only after it is committed and, when a snapshot store is set,
    saved to it. If a message could not be stored or saved (a locked database) the answer is 503, so Meta retries;
    messages already stored are skipped by their wamid.
    """
    core = request.app.state.core
    cl = request.headers.get("content-length")
    if cl and (not cl.isdigit() or int(cl) > MAX_WEBHOOK_BODY):
        return _too_large()
    chunks, size = [], 0
    async for chunk in request.stream():                # raw bytes first, capped, before any hashing or parsing
        size += len(chunk)
        if size > MAX_WEBHOOK_BODY:
            return _too_large()
        chunks.append(chunk)
    raw = b"".join(chunks)
    reason = wa.verify_signature(core.settings.wa_app_secret, raw, request.headers.get("x-hub-signature-256"))
    if reason is not None:
        log.warning("webhook rejected: %s", reason)
        conn = core.conn()
        with tx(conn):
            repo.add_event(conn, core.clock.now(), "webhook.rejected", "warning", payload={"reason": reason})
        return JSONResponse({"error": {"code": "UNAUTHORIZED", "message": "invalid_signature"}}, status_code=401)
    core.last_webhook_at = core.clock.now()
    counts = await asyncio.to_thread(process, core, raw)
    if counts["errors"]:
        return JSONResponse({"error": {"code": "WEBHOOK_NOT_STORED", "message": "try again"}}, status_code=503)
    if counts["new"] or counts["duplicate"] or counts["statuses"]:
        if not await asyncio.to_thread(core.flush):         # Meta's 200 means "kept": not before the store has it
            return JSONResponse({"error": {"code": "WEBHOOK_NOT_STORED", "message": "try again"}}, status_code=503)
    return JSONResponse({})


def process(core, raw: bytes) -> dict:
    """Store the payload: never raises. Returns counts; `errors` > 0 means something was not stored."""
    conn, now = core.conn(), core.clock.now()
    counts = {"new": 0, "duplicate": 0, "statuses": 0, "ignored": 0, "errors": 0}
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        log.warning("webhook malformed JSON (%d bytes)", len(raw))
        try:
            with tx(conn):
                repo.add_event(conn, now, "webhook.malformed", "warning")
        except Exception as e:                           # noqa: BLE001 - the body is unusable either way
            log.error("webhook.malformed event not stored: %s", type(e).__name__)
        return counts
    try:
        batch = wa.parse_payload(payload, core.settings.wa_phone_number_id)
    except Exception as e:                               # noqa: BLE001 - a signed but odd shape: log, never a 5xx
        _process_error(conn, now, e, counts)
        counts["errors"] = 0                             # retrying the same odd body cannot help: answer 200
        return counts
    counts["ignored"] = batch.ignored_foreign + batch.skipped
    if batch.ignored_foreign:
        log.warning("webhook: %d change(s) for another phone_number_id ignored", batch.ignored_foreign)
    debounce = core.config.raw["timeouts"]["debounce_s"]["demo" if core.settings.demo_mode else "prod"]
    for m in batch.messages:
        try:
            with tx(conn):
                counts["new" if store_message(conn, core.ids, now, m, debounce) else "duplicate"] += 1
        except Exception as e:                           # noqa: BLE001
            _process_error(conn, now, e, counts)
    for s in batch.statuses:
        try:
            with tx(conn):
                counts["statuses"] += update_status(conn, s)
        except Exception as e:                           # noqa: BLE001
            _process_error(conn, now, e, counts)
    log.info("webhook processed: %s", counts)
    return counts


def _process_error(conn, now, e: Exception, counts: dict) -> None:
    counts["errors"] += 1
    log.error("webhook process_error: %s", type(e).__name__)          # the type only: no payload, no number
    try:
        with tx(conn):
            repo.add_event(conn, now, "webhook.process_error", "error", payload={"error": type(e).__name__})
    except Exception as e2:                              # noqa: BLE001 - the same lock that failed the first write
        log.error("webhook process_error event not stored: %s (counts %s)", type(e2).__name__, counts)


def store_message(conn, ids, now, m: wa.Inbound, debounce_s: float) -> bool:
    """One inbound message through the ONE ingest path. False = duplicate wamid (no rescore armed)."""
    if repo.row(conn, "SELECT 1 FROM messages WHERE channel_message_id=?", m.wamid):
        return False
    cust = repo.get_or_create_customer(conn, ids, now, sandbox_id=None, phone_e164="+" + m.wa_id,
                                       display_name=m.profile_name)
    conv = repo.row(conn, "SELECT conversation_id FROM conversations WHERE customer_id=? AND channel='whatsapp'"
                          " ORDER BY opened_at DESC LIMIT 1", cust)
    conv_id = conv["conversation_id"] if conv else repo.create_conversation(
        conn, ids, now, customer_id=cust, sandbox_id=None, channel="whatsapp")
    reply_to = repo.row(conn, "SELECT message_id FROM messages WHERE channel_message_id=? AND conversation_id=?",
                        m.context_id, conv_id) if m.context_id else None
    st = store_inbound(conn, ids, now, conversation_id=conv_id, origin="whatsapp", text=m.text, kind=m.kind,
                       lat=m.lat, lng=m.lng, provider_ts=m.ts, channel_message_id=m.wamid,
                       reply_to_message_id=reply_to["message_id"] if reply_to else None, debounce_s=debounce_s)
    return st.message_id is not None


def update_status(conn, s: wa.Status) -> int:
    """statuses[] only move delivery_status forward on OUR outbound rows; unknown wamids are a no-op."""
    r = repo.row(conn, "SELECT message_id, delivery_status FROM messages WHERE channel_message_id=?"
                       " AND direction='outbound'", s.wamid)
    if r is None or wa.STATUS_RANK.get(r["delivery_status"] or "", 0) >= wa.STATUS_RANK[s.status]:
        return 0
    conn.execute("UPDATE messages SET delivery_status=? WHERE message_id=?", (s.status, r["message_id"]))
    return 1
