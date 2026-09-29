"""This app's own orders as analyzer sessions: the WhatsApp/paste conversation is the dialogue, and each pipeline step
is a tool call rebuilt from the database, in time order:

  extract_order    extraction_runs   ok = valid; a failed LLM extraction followed by the rules path is a retry
  confirm_order    risk_assessments  only when the customer's confirmation was read as 'confirmed'
  score_order      risk_assessments  tier, action, confirmation
  update_order     risk_assessments  the address level the extraction found (what the order would ship with)
  draft_message    outbound_drafts   route, source, judge verdict
  send_message     outbound_drafts   delivery (whatsapp_sent / recorded_only)
  <event type>     events            level 'error' -> a failed step

Final status = the order's status. No phone numbers or names leave this module: the session carries ids only.
"""
from __future__ import annotations

import json
import sqlite3

from wasel.clock import parse_utc

STATUS = {"ready_to_ship": "ready", "shipped": "shipped", "delivered": "shipped", "awaiting_reply": "awaiting_reply",
          "needs_review": "needs_review", "collecting": "collecting", "refused": "refused", "cancelled": "cancelled"}


def _j(s, default):
    try:
        return json.loads(s) if s else default
    except ValueError:
        return default


def session_for(conn: sqlite3.Connection, o: sqlite3.Row) -> dict:
    """Rebuild one order as an analyzer session from the database. Read-only.

    `o` is an orders row joined with `channel` (as sessions_from_db selects it). Messages become agent/user turns and
    each pipeline step (extraction, scoring, address update, confirmation, drafting, sending, error events) becomes a
    tool_call and tool_result pair. Events are ordered by time and `t` is seconds since the first one. The session has
    no `label`, so it can't be scored for accuracy.
    """
    items: list[tuple[str, int, dict]] = []                 # (ts, tiebreak, event)
    for m in conn.execute("SELECT m.* FROM messages m JOIN order_messages om ON om.message_id = m.message_id "
                          "WHERE om.order_id = ? UNION SELECT m.* FROM messages m WHERE m.conversation_id = ? "
                          "AND m.direction = 'outbound' AND m.received_at >= ?",
                          (o["order_id"], o["conversation_id"], o["opened_at"])):
        text = m["text"] or m["transcript"] or m["canonical_text"] or ""
        if m["kind"] == "location":
            text = text or f"[location {m['location_lat']:.3f},{m['location_lng']:.3f}]"
        who = "user" if m["direction"] == "inbound" else "agent"
        items.append((m["received_at"], 0, {"type": who, "text": text, "message_id": m["message_id"],
                                            "template_id": m["template_id"]}))
    for e in conn.execute("SELECT * FROM extraction_runs WHERE order_id = ? ORDER BY created_at", (o["order_id"],)):
        v = _j(e["validated_json"], {})
        res = {"provider": e["provider"], "model": e["model"], "address_level": v.get("address_level"),
               "flags": [f.get("code") for f in v.get("red_flags", [])], "dropped_quotes": e["dropped_quotes"],
               "injection_suspected": bool(e["injection_suspected"])}
        if e["error"]:
            res["error"] = e["error"]
        items.append((e["created_at"], 1, {"type": "tool_call", "tool": "extract_order",
                                           "args": {"messages": len(_j(e["input_message_ids"], []))}}))
        items.append((e["created_at"], 2, {"type": "tool_result", "tool": "extract_order", "ok": bool(e["valid"]),
                                           "result": res}))
        if not e["valid"]:                                  # the pipeline falls back to the rules extractor
            items.append((e["created_at"], 3, {"type": "tool_call", "tool": "extract_order",
                                               "args": {"messages": len(_j(e["input_message_ids"], [])),
                                                        "provider": "rules"}}))
            items.append((e["created_at"], 4, {"type": "tool_result", "tool": "extract_order", "ok": True,
                                               "result": {"provider": "rules"}}))
    for a in conn.execute("SELECT a.*, e.validated_json FROM risk_assessments a LEFT JOIN extraction_runs e "
                          "ON e.extraction_id = a.extraction_id WHERE a.order_id = ? ORDER BY a.version",
                          (o["order_id"],)):
        ts = a["created_at"]
        items.append((ts, 5, {"type": "tool_call", "tool": "score_order", "args": {"trigger": a["trigger"]}}))
        items.append((ts, 6, {"type": "tool_result", "tool": "score_order", "ok": True,
                              "result": {"version": a["version"], "tier": a["tier"], "score": a["final_score"],
                                         "action": a["action"], "confirmation": a["confirmation"],
                                         "path": a["path"]}}))
        lvl = _j(a["validated_json"], {}).get("address_level")
        if lvl:
            items.append((ts, 7, {"type": "tool_call", "tool": "update_order",
                                  "args": {"order_id": o["order_id"], "address_level": lvl}}))
            items.append((ts, 8, {"type": "tool_result", "tool": "update_order", "ok": True,
                                  "result": {"updated": True}}))
        if a["confirmation"] == "confirmed":
            items.append((ts, 9, {"type": "tool_call", "tool": "confirm_order", "args": {"order_id": o["order_id"]}}))
            items.append((ts, 10, {"type": "tool_result", "tool": "confirm_order", "ok": True,
                                   "result": {"status": "confirmed"}}))
    for d in conn.execute("SELECT * FROM outbound_drafts WHERE order_id = ? ORDER BY created_at", (o["order_id"],)):
        j = _j(d["judge_json"], None)
        res = {"template_id": d["template_id"], "route": d["route"], "source": d["source"]}
        if j:
            res["judge"] = {k: j.get(k) for k in ("decided_by", "approved", "grounded", "overreach", "unavailable")}
        items.append((d["created_at"], 11, {"type": "tool_call", "tool": "draft_message",
                                            "args": {"template_id": d["template_id"]}}))
        items.append((d["created_at"], 12, {"type": "tool_result", "tool": "draft_message",
                                            "ok": d["route"] != "blocked", "result": res}))
        if d["sent_at"]:
            items.append((d["sent_at"], -2, {"type": "tool_call", "tool": "send_message",
                                             "args": {"template_id": d["template_id"]}}))
            items.append((d["sent_at"], -1, {"type": "tool_result", "tool": "send_message", "ok": True,
                                             "result": {"delivery": d["delivery"]}}))
    for e in conn.execute("SELECT * FROM events WHERE order_id = ? AND level = 'error' ORDER BY seq",
                          (o["order_id"],)):
        items.append((e["ts"], 13, {"type": "tool_result", "tool": e["type"], "ok": False,
                                    "result": {"error": next(iter(_j(e["payload"], {}) or {"error": 1}))}}))
    items.sort(key=lambda x: (x[0], x[1]))
    events = []
    t0 = None
    for ts, _, e in items:
        t = parse_utc(ts)
        t0 = t0 or t
        events.append({**e, "i": len(events), "t": int((t - t0).total_seconds())})
    return {"session_id": f"order-{o['order_no']}", "source": "app", "order_id": o["order_id"],
            "context": {"order_id": o["order_id"], "channel": o["channel"]},
            "events": events, "final": {"status_claimed": STATUS.get(o["status"], o["status"])}}


def sessions_from_db(conn: sqlite3.Connection, sandbox_id: str | None = None, limit: int = 500) -> list[dict]:
    """Seeded/event orders by default (sandbox_id NULL); a visitor's own sandbox when given."""
    q = ("SELECT o.*, c.channel FROM orders o JOIN conversations c ON c.conversation_id = o.conversation_id "
         "WHERE o.sandbox_id IS ? ORDER BY o.opened_at DESC LIMIT ?")
    return [session_for(conn, o) for o in conn.execute(q, (sandbox_id, limit))]
