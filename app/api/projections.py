"""Read-side projections: queue summaries, the detail view and server-built segments.
Segments are built per message on the ORIGINAL text; the client does no offset math."""
from __future__ import annotations

import json
import sqlite3

from app.api import models as M
from app.api.event_text import event_text
from app.db import repo
from app.db.seed import fixture_for
from app.extraction.normalize import mask_phone_for_display
from app.scoring.score_order import FLAG_LABELS
from app.settings import Settings
from app.state import TERMINAL, allowed_actions

# Customer text can't visually reorder the dashboard. Applied to customer text only; server sentences
# (reasons, labels) keep their FSI/PDI isolates.
BIDI_CONTROLS = {chr(c) for c in [*range(0x202A, 0x202F), *range(0x2066, 0x206A)]}


def strip_bidi(s: str | None) -> str | None:
    return None if s is None else "".join(ch for ch in s if ch not in BIDI_CONTROLS)


def build_segments(text: str, spans: list[dict]) -> list[M.Segment]:
    """Invariant (tested): "".join(s.text) == strip_bidi(text). risk wins over address; overlaps split."""
    edges = sorted({0, len(text), *[s["start"] for s in spans], *[s["end"] for s in spans]})
    out: list[M.Segment] = []
    for a, b in zip(edges, edges[1:], strict=False):
        if a >= b:
            continue
        cover = [s for s in spans if s["start"] <= a and b <= s["end"]]
        codes = sorted({s["code"] for s in cover if s["kind"] == "red_flag" and s["code"]})
        kind = "risk" if codes else "address" if any(s["kind"] == "address" for s in cover) else None
        label = " · ".join(FLAG_LABELS[c] for c in codes) if codes else ("Address detail" if kind else None)
        piece = strip_bidi(text[a:b])
        if out and out[-1].kind == kind and out[-1].codes == codes:
            out[-1] = M.Segment(text=out[-1].text + piece, kind=kind, codes=codes, label=label)
        elif piece:
            out.append(M.Segment(text=piece, kind=kind, codes=codes, label=label))
    return out or [M.Segment(text=strip_bidi(text), kind=None, codes=[], label=None)]


def _display_name(settings: Settings, cust: sqlite3.Row, order: sqlite3.Row) -> str | None:
    if settings.is_public and order["sandbox_id"] is not None:
        return f"Customer #{order['order_no']}"
    return cust["display_name"]


def order_summary(conn, settings: Settings, o: sqlite3.Row) -> M.OrderSummary:
    cust = repo.row(conn, "SELECT * FROM customers WHERE customer_id=?", o["customer_id"])
    conv = repo.row(conn, "SELECT channel, seed_key FROM conversations WHERE conversation_id=?", o["conversation_id"])
    asm = repo.assessments(conn, o["order_id"])
    score = None
    inj = False
    if asm:
        cur = asm[-1]
        prev = asm[-2] if len(asm) > 1 else None
        score = M.ScoreBadge(version=cur["version"], final_score=cur["final_score"], tier=cur["tier"],
                             action=cur["action"], confidence=cur["confidence"], path=cur["path"],
                             delta=(cur["final_score"] - prev["final_score"]) if prev else None,
                             reason_short=cur["reason_short"])
        inj = bool(json.loads(cur["context_json"]).get("injection_suspected"))
    last_in = repo.row(conn, "SELECT m.text FROM messages m JOIN order_messages om USING(message_id) WHERE"
                             " om.order_id=? AND m.direction='inbound' AND m.text IS NOT NULL"
                             " ORDER BY m.provider_ts DESC LIMIT 1", o["order_id"])
    seeded = o["sandbox_id"] is None
    return M.OrderSummary(
        order_id=o["order_id"], order_ref=f"#{o['order_no']}", conversation_id=o["conversation_id"],
        customer=M.CustomerRef(customer_id=cust["customer_id"], display_name=_display_name(settings, cust, o),
                               phone_masked=mask_phone_for_display(cust["phone_e164"])),
        channel=conv["channel"], status=o["status"], rescore_state=o["rescore_state"],
        product_name=o["product_name"], price_tnd=o["price_tnd"], score=score,
        has_pending_draft=repo.unsent_draft(conn, o["order_id"]) is not None, is_seeded=seeded,
        read_only=settings.is_public and seeded,
        last_message_preview=strip_bidi(last_in["text"][:80]) if last_in else None, updated_at=o["updated_at"],
        seed_key=conv["seed_key"], injection_suspected=inj)


def list_orders(conn, settings: Settings, vid: str | None, *, tier=None, status=None,
                include_collecting=False, limit=100) -> M.OrderListResponse:
    where, args = [], []
    if settings.is_public:
        where.append("(o.sandbox_id IS NULL OR o.sandbox_id = ?)")
        args.append(vid)
    if not include_collecting:
        where.append("(o.status <> 'collecting' OR o.rescore_state <> 'idle')")
    if status:
        where.append("o.status = ?")
        args.append(status)
    if tier:
        where.append("a.tier = ?")
        args.append(tier)
    sql = ("SELECT o.* FROM orders o LEFT JOIN risk_assessments a ON a.assessment_id = o.current_assessment_id"
           + (" WHERE " + " AND ".join(where) if where else "")
           + " ORDER BY a.final_score IS NULL, a.final_score DESC, o.updated_at DESC LIMIT ?")
    orders = [order_summary(conn, settings, o) for o in conn.execute(sql, (*args, limit)).fetchall()]
    counts = {t: sum(1 for x in orders if x.score and x.score.tier == t) for t in ("low", "medium", "high")}
    counts.update({s: sum(1 for x in orders if x.status == s) for s in ("needs_review", "awaiting_reply",
                                                                          "ready_to_ship")})
    from app.clock import SystemClock, utc_iso
    return M.OrderListResponse(orders=orders, counts=M.Counts(**counts), server_time=utc_iso(SystemClock().now()),
                               mode=settings.app_mode)


def _reply_to(q: sqlite3.Row | None) -> M.ReplyTo | None:
    """The quoted message (WhatsApp context.id), if it belongs to this order's thread."""
    if q is None:
        return None
    return M.ReplyTo(message_id=q["message_id"], preview=strip_bidi(q["text"] or q["canonical_text"] or "")[:80])


def order_detail(conn, settings: Settings, o: sqlite3.Row) -> M.OrderDetailResponse:
    s = order_summary(conn, settings, o)
    cust = repo.row(conn, "SELECT * FROM customers WHERE customer_id=?", o["customer_id"])
    conv = repo.row(conn, "SELECT * FROM conversations WHERE conversation_id=?", o["conversation_id"])
    asm = repo.assessments(conn, o["order_id"])
    cur_spans: dict[str, list[dict]] = {}
    if asm and asm[-1]["extraction_id"]:
        run = repo.row(conn, "SELECT spans_json FROM extraction_runs WHERE extraction_id=?", asm[-1]["extraction_id"])
        for sp in json.loads(run["spans_json"]):
            cur_spans.setdefault(sp["message_id"], []).append(sp)
    msgs = []
    order_msgs = repo.order_messages(conn, o["order_id"])
    by_id = {m["message_id"]: m for m in order_msgs}
    for m in order_msgs:
        segs = build_segments(m["text"], cur_spans.get(m["message_id"], [])) \
            if m["author"] == "customer" and m["text"] else None
        msgs.append(M.MessageView(
            message_id=m["message_id"], direction=m["direction"], author=m["author"], origin=m["origin"],
            kind=m["kind"], provider_ts=m["provider_ts"], text=strip_bidi(m["text"]), segments=segs,
            transcript=m["transcript"],
            location=M.Location(lat=m["location_lat"], lng=m["location_lng"]) if m["kind"] == "location" else None,
            reply_to=_reply_to(by_id.get(m["reply_to_message_id"])), template_id=m["template_id"],
            delivery_status=m["delivery_status"]))
    views, prev = [], None
    for a in asm:
        run = repo.row(conn, "SELECT * FROM extraction_runs WHERE extraction_id=?", a["extraction_id"]) \
            if a["extraction_id"] else None
        views.append(M.AssessmentView(
            assessment_id=a["assessment_id"], version=a["version"], trigger=a["trigger"], created_at=a["created_at"],
            path=a["path"], model_score=a["model_score"], final_score=a["final_score"],
            delta=(a["final_score"] - prev["final_score"]) if prev else None, tier=a["tier"], action=a["action"],
            confidence=a["confidence"], confidence_reasons=json.loads(a["confidence_reasons_json"]),
            confirmation=a["confirmation"], reason=a["reason"], reason_diff=a["reason_diff"],
            adjustments=[M.AdjustmentView(**x) for x in json.loads(a["adjustments_json"])],
            resolved_flags=json.loads(a["resolved_flags_json"]),
            flags=[M.FlagViewModel(code=f["code"], label=FLAG_LABELS[f["code"]], quote=f["quote"],
                                   message_id=f["message_id"]) for f in json.loads(a["flags_json"])],
            top_factors=[M.FactorView(**f) for f in json.loads(a["top_factors_json"])],
            extraction=M.ExtractionView(provider=run["provider"], model=run["model"], cache_hit=bool(run["cache_hit"]),
                                        valid=bool(run["valid"]), dropped_flags=run["dropped_flags"],
                                        latency_ms=run["latency_ms"]) if run else None,
            config_hash=a["config_hash"], classifier_version=a["classifier_version"],
            prompt_version=a["prompt_version"]))
        prev = a
    ver = {a["assessment_id"]: a["version"] for a in asm}
    drafts = [M.DraftView(
        draft_id=d["draft_id"], assessment_version=ver.get(d["assessment_id"], 0), template_id=d["template_id"],
        language=d["language"], text=d["rendered_text"], canonical_text=d["canonical_text"], source=d["source"],
        route=d["route"], prefilter=M.PrefilterView(**json.loads(d["prefilter_json"])),
        judge=json.loads(d["judge_json"]) if d["judge_json"] else None, sent_message_id=d["sent_message_id"],
        sent_at=d["sent_at"], delivery=d["delivery"], created_at=d["created_at"], decided_by=d["decided_by"])
        for d in repo.rows(conn, "SELECT * FROM outbound_drafts WHERE order_id=? ORDER BY created_at DESC",
                           o["order_id"])]
    ro = s.read_only
    terminal = o["status"] in TERMINAL
    fx = fixture_for(conv["seed_key"]) if conv["seed_key"] else None
    return M.OrderDetailResponse(
        order=M.OrderDetailOrder(**s.model_dump(), quantity=o["quantity"], zone=o["zone"], zone_source=o["zone_source"],
                                 address_text=o["address_text"], product_id=o["product_id"], language=o["language"],
                                 auto_messages_sent=o["auto_messages_sent"],
                                 awaiting_reply_since=o["awaiting_reply_since"],
                                 seller_approved_at=o["seller_approved_at"], opened_at=o["opened_at"]),
        customer=M.CustomerDetail(**s.customer.model_dump(), completed_orders=cust["completed_orders"],
                                  refusals_total=cust["refusals_total"]),
        conversation=M.ConversationView(conversation_id=conv["conversation_id"], channel=conv["channel"], messages=msgs),
        assessments=views, drafts=drafts,
        capabilities=M.Capabilities(read_only=ro, can_try=ro and fx is not None,
                                    can_simulate_reply=not ro and not terminal, can_rescore=not ro and not terminal,
                                    can_send_drafts=not ro, actions=[] if ro else allowed_actions(o["status"])),
        scripted_replies=fx.get("scripted_replies", []) if fx else [])


def list_events(conn, settings: Settings, vid: str | None, *, after: int = 0, order_id: str | None = None,
                limit: int = 50) -> M.EventsResponse:
    where, args = ["e.seq > ?"], [after]
    if settings.is_public:
        where.append("(e.sandbox_id IS NULL OR e.sandbox_id = ?)")
        args.append(vid)
    if order_id:
        where.append("e.order_id = ?")
        args.append(order_id)
    rs = conn.execute("SELECT e.*, o.order_no FROM events e LEFT JOIN orders o ON o.order_id = e.order_id WHERE "
                      + " AND ".join(where) + " ORDER BY e.seq LIMIT ?", (*args, limit)).fetchall()
    evs = []
    for r in rs:
        title, detail = event_text(r["type"], r["payload"])
        evs.append(M.EventView(seq=r["seq"], ts=r["ts"], type=r["type"], level=r["level"], order_id=r["order_id"],
                               order_ref=f"#{r['order_no']}" if r["order_no"] else None, title=title, detail=detail))
    return M.EventsResponse(events=evs, last_seq=evs[-1].seq if evs else after)
