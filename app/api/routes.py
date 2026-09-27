"""/api routes (01 §4.1). DEVIATION: one module instead of routes_{orders,conversations,drafts,events,health,
admin}.py; split by owner when promoted. The WhatsApp webhook (S-1) lives in routes_webhook.py."""
from __future__ import annotations

import hmac
import json

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse

from app.api import commands
from app.api import models as M
from app.api import projections as P
from app.api.errors import ApiError
from app.mode import require_visitor, visitor_id

router = APIRouter(prefix="/api")


def _s(request: Request):
    return request.app.state.core


def _nocache(model) -> JSONResponse:
    return JSONResponse(model.model_dump(mode="json"), headers={"Cache-Control": "no-store"})


@router.get("/health")
def health(request: Request):
    st = _s(request)
    return _nocache(st.health(st.conn()))


@router.get("/orders")
def list_orders(request: Request, tier: str | None = None, status: str | None = None,
                include_collecting: bool = False, limit: int = 100, vid: str | None = Depends(visitor_id)):
    st = _s(request)
    return _nocache(P.list_orders(st.conn(), st.settings, vid, tier=tier, status=status,
                                  include_collecting=include_collecting, limit=min(limit, 500)))


@router.get("/orders/{order_id}")
def get_order(order_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    st = _s(request)
    o = commands.visible_order(st.conn(), order_id, st.settings, vid)
    return _nocache(P.order_detail(st.conn(), st.settings, o))


@router.post("/orders/ingest", status_code=202)
def ingest(body: M.PasteIngest | M.CsvIngest, request: Request, vid: str | None = Depends(visitor_id)):
    st = _s(request)
    vid = require_visitor(request, vid)
    conn, now = st.conn(), st.clock.now()
    if isinstance(body, M.PasteIngest):
        created = [commands.ingest_paste(conn, st.ids, now, st.settings, st.config.raw, vid, text=body.text,
                                         customer_name=body.customer_name,
                                         structured=body.structured.model_dump() if body.structured else None)]
        rejected = []
    else:
        created, rejected = commands.ingest_csv(conn, st.ids, now, st.settings, st.config.raw, vid, body.csv_text)
    eta = st.config.raw["timeouts"]["debounce_s"]["demo" if st.settings.demo_mode else "prod"] + 1
    return M.IngestResponse(created=created, rejected=rejected, rescore_eta_s=eta)


@router.post("/orders/{order_id}/try", status_code=201)
def try_order(order_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    st = _s(request)
    if vid is None:
        raise ApiError(400, "VISITOR_ID_REQUIRED", "X-Visitor-Id (uuid v4) is required",
                       {"X-Visitor-Id": ["missing or malformed"]})
    conn = st.conn()
    r = commands.try_order(conn, st.ids, st.clock.now(), st.settings, order_id, vid)
    st.drain(conn)                                     # scored immediately: no debounce, cache hit
    return M.TryResponse(**r)


@router.post("/conversations/{conversation_id}/simulate-reply", status_code=202)
def simulate_reply(conversation_id: str, body: M.SimulateText | M.SimulateLocation, request: Request,
                   vid: str | None = Depends(visitor_id)):
    st = _s(request)
    vid = require_visitor(request, vid)
    kw = {"text": body.text} if isinstance(body, M.SimulateText) else {"lat": body.lat, "lng": body.lng}
    return M.SimulateReplyResponse(**commands.simulate_reply(st.conn(), st.ids, st.clock.now(), st.settings,
                                                             st.config.raw, vid, conversation_id, **kw))


@router.post("/orders/{order_id}/rescore", status_code=202)
def rescore(order_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    st = _s(request)
    vid = require_visitor(request, vid)
    return M.RescoreResponse(**commands.rescore(st.conn(), st.clock.now(), st.settings, vid, order_id))


@router.post("/orders/{order_id}/actions")
def action(order_id: str, body: M.SellerActionRequest, request: Request, vid: str | None = Depends(visitor_id)):
    st = _s(request)
    vid = require_visitor(request, vid)
    conn = st.conn()
    commands.apply_action(conn, st.ids, st.clock.now(), st.settings, vid, order_id, body.action, st.drafter)
    from app.db import repo
    return P.order_summary(conn, st.settings, repo.get_order(conn, order_id))


@router.post("/drafts/{draft_id}/send")
def send_draft(draft_id: str, request: Request, vid: str | None = Depends(visitor_id)):
    st = _s(request)
    vid = require_visitor(request, vid)
    return M.SendDraftResponse(**commands.send_draft(st.conn(), st.ids, st.clock.now(), st.settings, vid, draft_id,
                                                         st.sender))


@router.get("/events")
def events(request: Request, after: int = 0, order_id: str | None = None, limit: int = 50,
           vid: str | None = Depends(visitor_id)):
    st = _s(request)
    return _nocache(P.list_events(st.conn(), st.settings, vid, after=after, order_id=order_id, limit=min(limit, 200)))


@router.get("/metrics/impact")
def impact(request: Request):
    st = _s(request)
    p = st.config.root / "reports" / "impact.json"
    d = json.loads(p.read_text()) if p.exists() else {}
    return _nocache(M.ImpactResponse(simulated=True, dataset=d.get("dataset", "none"), n_orders=d.get("n_orders", 0),
                                     baseline_refusal_rate=d.get("baseline_refusal_rate", 0.0),
                                     projected_refusal_rate=d.get("projected_refusal_rate", 0.0),
                                     trips_avoided=d.get("trips_avoided", 0.0), tnd_saved=d.get("tnd_saved", 0.0),
                                     assumptions=d.get("assumptions", [])))


admin = APIRouter(prefix="/api/admin")


@admin.post("/reset")
def reset(request: Request, x_admin_token: str | None = Header(default=None)):
    st = _s(request)
    if not x_admin_token or not hmac.compare_digest(x_admin_token, st.settings.admin_token):
        raise ApiError(401, "UNAUTHORIZED", "admin token required")
    purged, reseeded = st.reset()
    return M.ResetResponse(reseeded_orders=reseeded, purged_rows=purged)

