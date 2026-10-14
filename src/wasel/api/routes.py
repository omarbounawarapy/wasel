"""/api routes (orders, conversations, drafts, events, health, metrics). The WhatsApp webhook lives in
routes_webhook.py."""
from __future__ import annotations

import hmac
import json
import math

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse

from wasel.api import commands
from wasel.api import models as M
from wasel.api import projections as P
from wasel.api.errors import ApiError
from wasel.mode import require_visitor, visitor_id
from wasel.ratelimit import client_address


def _errors(*statuses: int) -> dict[int, dict]:
    """OpenAPI `responses` entries that point at the error envelope."""
    return {s: {"model": M.ErrorEnvelope, "description": _ERROR_TEXT[s]} for s in statuses}


_ERROR_TEXT = {
    400: "BAD_HOST, or VISITOR_ID_REQUIRED in public mode",
    401: "UNAUTHORIZED",
    403: "BAD_ORIGIN, or a mutation refused for this address",
    404: "NOT_FOUND",
    409: "INVALID_TRANSITION, SEEDED_READ_ONLY or another state conflict; `details` may list what is allowed",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR; `details` maps field names to messages",
    429: "RATE_LIMITED",
    502: "WHATSAPP_SEND_FAILED",
}
# what the middleware and guards can answer on any operation
router = APIRouter(prefix="/api", responses=_errors(400, 403, 413, 429))


def _address_guard(request: Request, st, vid: str | None, *, orders: int = 0) -> str | None:
    """Public mode: count this write against its client address, which the visitor id cannot reset.

    Raises 429 RATE_LIMITED (with Retry-After) past `addr_writes_10min` writes, or when `orders` more sandbox orders
    would pass `addr_sandbox_orders`. Returns the address, or None when it is unknown (no trusted header and a
    proxied or local peer), in which case only the per-visitor limits apply.
    """
    s = st.settings
    if not s.is_public:
        return None
    addr = client_address(request.client.host if request.client else None, request.headers, s.client_ip_header)
    if addr is None:
        return None
    now = st.clock.now().timestamp()
    if vid:
        st.limiter.note_visitor(addr, vid, now)
    wait = st.limiter.hit_write(addr, now, s.addr_writes_10min, 600)
    if wait is None and orders:
        wait = st.limiter.orders_wait(addr, now, s.addr_sandbox_orders, s.sandbox_ttl_s, adding=orders)
    if wait is not None:
        raise ApiError(429, "RATE_LIMITED", "Too many requests from this network, try again later",
                       headers={"Retry-After": str(math.ceil(wait))})
    return addr



def _s(request: Request):
    return request.app.state.core


def _nocache(model) -> JSONResponse:
    return JSONResponse(model.model_dump(mode="json"), headers={"Cache-Control": "no-store"})


@router.get("/health")
def health(request: Request):
    """Mode, LLM path, versions and worker state."""
    st = _s(request)
    return _nocache(st.health(st.conn()))


@router.get("/orders")
def list_orders(request: Request, tier: M.Tier | None = None, status: M.OrderStatus | None = None,
                include_collecting: bool = False, limit: int = Query(100, ge=1, le=500),
                vid: str | None = Depends(visitor_id)):
    """The order queue, riskiest first; filter by tier or status. Capped at 500 rows."""
    st = _s(request)
    return _nocache(P.list_orders(st.conn(), st.settings, vid, tier=tier, status=status,
                                  include_collecting=include_collecting, limit=limit))


@router.get("/orders/{order_id}", responses=_errors(404))
def get_order(order_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    """One order in full: messages, assessments, drafts and the actions allowed now."""
    st = _s(request)
    o = commands.visible_order(st.conn(), order_id, st.settings, vid)
    return _nocache(P.order_detail(st.conn(), st.settings, o))


@router.post("/orders/ingest", status_code=202)
def ingest(body: M.PasteIngest | M.CsvIngest, request: Request, vid: str | None = Depends(visitor_id)):
    """Queue a pasted message or a CSV for scoring; the worker scores it after the debounce (`rescore_eta_s`)."""
    st = _s(request)
    vid = require_visitor(request, vid)
    addr = _address_guard(request, st, vid, orders=1)
    conn, now = st.conn(), st.clock.now()
    if isinstance(body, M.PasteIngest):
        created = [commands.ingest_paste(conn, st.ids, now, st.settings, st.config.raw, vid, text=body.text,
                                         customer_name=body.customer_name,
                                         structured=body.structured.model_dump() if body.structured else None)]
        rejected = []
    else:
        created, rejected = commands.ingest_csv(conn, st.ids, now, st.settings, st.config.raw, vid, body.csv_text)
    if addr:
        st.limiter.add_orders(addr, now.timestamp(), len(created))
    eta = st.config.raw["timeouts"]["debounce_s"]["demo" if st.settings.demo_mode else "prod"] + 1
    return M.IngestResponse(created=created, rejected=rejected, rescore_eta_s=eta)


@router.post("/orders/{order_id}/try", status_code=201, responses=_errors(404, 409))
def try_order(order_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    """Copy a seeded sample order into the visitor's sandbox and score it at once."""
    st = _s(request)
    if vid is None:
        raise ApiError(400, "VISITOR_ID_REQUIRED", "X-Visitor-Id (uuid v4) is required",
                       {"X-Visitor-Id": ["missing or malformed"]})
    addr = _address_guard(request, st, vid, orders=1)
    conn = st.conn()
    r = commands.try_order(conn, st.ids, st.clock.now(), st.settings, order_id, vid)
    if addr:
        st.limiter.add_orders(addr, st.clock.now().timestamp(), 1)
    st.drain(conn, r["order_id"])                       # only this order; scored immediately: no debounce, cache hit
    return M.TryResponse(**r)


@router.post("/conversations/{conversation_id}/simulate-reply", status_code=202,
             responses=_errors(404, 409))
def simulate_reply(conversation_id: str, body: M.SimulateText | M.SimulateLocation, request: Request,
                   vid: str | None = Depends(visitor_id)):
    """Add a simulated customer reply (text or location pin); this arms a rescore."""
    st = _s(request)
    vid = require_visitor(request, vid)
    _address_guard(request, st, vid)
    kw = {"text": body.text} if isinstance(body, M.SimulateText) else {"lat": body.lat, "lng": body.lng}
    return M.SimulateReplyResponse(**commands.simulate_reply(st.conn(), st.ids, st.clock.now(), st.settings,
                                                             st.config.raw, vid, conversation_id, **kw))


@router.post("/orders/{order_id}/rescore", status_code=202, responses=_errors(404, 409))
def rescore(order_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    """Force a rescore of the order."""
    st = _s(request)
    vid = require_visitor(request, vid)
    _address_guard(request, st, vid)
    return M.RescoreResponse(**commands.rescore(st.conn(), st.clock.now(), st.settings, vid, order_id))


@router.post("/orders/{order_id}/actions", responses=_errors(404, 409))
def action(order_id: str, body: M.SellerActionRequest, request: Request, vid: str | None = Depends(visitor_id)):
    """Apply a seller action (approve, request_confirmation, cancel, ship, mark_delivered, mark_refused)."""
    st = _s(request)
    vid = require_visitor(request, vid)
    _address_guard(request, st, vid)
    conn = st.conn()
    commands.apply_action(conn, st.ids, st.clock.now(), st.settings, vid, order_id, body.action, st.drafter)
    from wasel.db import repo
    return P.order_summary(conn, st.settings, repo.get_order(conn, order_id))


@router.post("/drafts/{draft_id}/send", responses=_errors(404, 409, 502))
def send_draft(draft_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    """Send a drafted message. A person triggers this; whether it goes out depends on the mode and WhatsApp settings."""
    st = _s(request)
    vid = require_visitor(request, vid)
    _address_guard(request, st, vid)
    out = commands.send_draft(st.conn(), st.ids, st.clock.now(), st.settings, vid, draft_id, st.sender)
    st.flush()                  # the send happened; a failed save shows in /api/health, it cannot undo the send
    return M.SendDraftResponse(**out)


@router.get("/events")
def events(request: Request, after: int = 0, order_id: str | None = None, limit: int = Query(50, ge=1, le=200),
           vid: str | None = Depends(visitor_id)):
    """The activity log, optionally after an event id or for one order. Capped at 200 rows."""
    st = _s(request)
    return _nocache(P.list_events(st.conn(), st.settings, vid, after=after, order_id=order_id, limit=limit))


@router.get("/metrics/impact")
def impact(request: Request, vid: str | None = Depends(visitor_id)):
    """Simulated impact on the synthetic holdout, read from data/reports/impact.json. Not a field result."""
    st = _s(request)
    p = st.config.root / "data" / "reports" / "impact.json"
    d = json.loads(p.read_text()) if p.exists() else {}
    return _nocache(M.ImpactResponse(simulated=True, dataset=d.get("dataset", "none"), n_orders=d.get("n_orders", 0),
                                     baseline_refusal_rate=d.get("baseline_refusal_rate", 0.0),
                                     projected_refusal_rate=d.get("projected_refusal_rate", 0.0),
                                     trips_avoided=d.get("trips_avoided", 0.0), tnd_saved=d.get("tnd_saved", 0.0),
                                     tnd_saved_per_1000_orders=d.get("tnd_saved_per_1000_orders", 0.0),
                                     tnd_saved_per_1000_by_confirm_rate=d.get("tnd_saved_per_1000_by_confirm_rate", {}),
                                     assumptions=d.get("assumptions", []),
                                     this_server=P.server_impact(st.conn(), st.settings, vid,
                                                                 st.config.raw["roi"])))


@router.get("/monitor")
def monitor(request: Request):
    """Drift, faithfulness, safety and LLM ops over the recent window (src/wasel/monitor.py). Rates only, no text."""
    from wasel import monitor as mon
    return _nocache_json(mon.report(_s(request).conn()))


@router.get("/traces")
def traces(request: Request, role: str | None = None, order_id: str | None = None,
           limit: int = Query(100, ge=1, le=500)):
    """Recent LLM trace records (ids, versions, model, outcome, latency, tokens; never the customer's text)."""
    from wasel.llm import trace
    rows = trace.recent(limit, role=role, order_id=order_id)
    rows = [{k: v for k, v in r.items() if k != "sandbox_id"} for r in rows]       # a visitor id is an access key
    return _nocache_json({"traces": rows})


@router.get("/eval")
def eval_reports(request: Request):
    """The last offline (CI gate) and live eval reports, as committed in data/reports/."""
    root = _s(request).config.root / "data" / "reports"
    out = {}
    for mode, name in (("offline", "eval.json"), ("live", "eval_live.json")):
        p = root / name
        try:
            out[mode] = json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        except ValueError:
            out[mode] = None
    return _nocache_json(out)


def _failure_sessions(request: Request, source: str, vid: str | None) -> list[dict]:
    from wasel.failures import dataset
    if source == "app":
        from wasel.failures.adapter import sessions_from_db
        conn = _s(request).conn()
        return sessions_from_db(conn) + (sessions_from_db(conn, vid) if vid else [])
    if source not in ("synthetic", "holdout"):
        raise ApiError(400, "BAD_SOURCE", "source must be synthetic, holdout or app")
    return dataset.load(dataset.OUT if source == "synthetic" else dataset.OUT_HOLDOUT)


@router.get("/failures")
def failures(request: Request, source: str = "synthetic", vid: str | None = Depends(visitor_id)):
    """Hidden-failure analyzer (src/wasel/failures/): ranked issues, grouped sessions, evidence, accuracy on the labeled
    sets, runtime and cost. Rules run live; the LLM-labeled run is read from data/reports/ when it was recorded."""
    from wasel.failures.adapter import redact_message_text
    from wasel.failures.run import analyze, score
    sessions = _failure_sessions(request, source, vid)
    rep = analyze(sessions)
    findings = rep.pop("_findings")
    if source != "app":
        rep["accuracy"] = score(sessions, findings)
    p = _s(request).config.root / "data" / "reports" / f"failures_{source}_llm.json"
    llm = None
    if p.exists():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            llm = {k: d.get(k) for k in ("accuracy", "semantics", "runtime", "cost", "by_status", "issues")}
        except ValueError:
            llm = None
    out = {"source": source, **rep, "llm_run": llm}
    return _nocache_json(redact_message_text(out) if source == "app" else out)


@router.get("/failures/sessions/{session_id}")
def failure_session(session_id: str, request: Request, source: str = "synthetic",
                    vid: str | None = Depends(visitor_id)):
    """One failure-analysis session with its findings."""
    s = next((x for x in _failure_sessions(request, source, vid) if x["session_id"] == session_id), None)
    if s is None:
        raise ApiError(404, "NOT_FOUND", "no such session")
    from wasel.failures.detect import detect
    out = {"session": s, "findings": [f.to_dict() for f in detect(s)]}
    if source == "app":
        from wasel.failures.adapter import redact_message_text
        out = redact_message_text(out)         # detectors ran on the full text; none of it leaves the server
    return _nocache_json(out)


def _nocache_json(d: dict) -> JSONResponse:
    return JSONResponse(d, headers={"Cache-Control": "no-store"})


admin = APIRouter(prefix="/api/admin", responses=_errors(401, 400, 403, 413))


@admin.post("/reset")
def reset(request: Request, x_admin_token: str | None = Header(default=None)):
    """Delete every order and reseed the demo data. Needs the X-Admin-Token header."""
    st = _s(request)
    if not x_admin_token or not hmac.compare_digest(x_admin_token.encode(), st.settings.admin_token.encode()):
        raise ApiError(401, "UNAUTHORIZED", "admin token required")
    purged, reseeded = st.reset()
    return M.ResetResponse(reseeded_orders=reseeded, purged_rows=purged)

