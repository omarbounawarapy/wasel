"""event type -> (title, detail) for the activity feed. Jesser's code, copy per FEDI.md F13 (01 §1). English source."""
from __future__ import annotations

import json

TITLES = {
    "message.received": "Customer message received",
    "order.rescored": "Order rescored",
    "draft.created": "Confirmation drafted",
    "draft.sent": "Message sent (simulated in this demo)",
    "draft.recorded_for_simulation": "Draft recorded as sent for the simulated reply",
    "llm.fallback": "Primary model unavailable: fallback used",
    "llm.cap_reached": "Live-AI budget reached: scored with rules",
    "cache.hit": "Handled from the extraction cache (no LLM call)",
    "cascade.hit": "Handled without an LLM call",
    "evidence.dropped": "Unverifiable evidence dropped",
    "flags.resolved": "Warning signs resolved by the reply",
    "extraction.not_order": "Message is not an order",
    "injection.suspected": "Possible instruction text in the message — check before acting",
    "webhook.rejected": "Webhook rejected (bad signature)",
    "sandbox.created": "Your copy of a sample order was created",
    "draft.judged": "LLM rewrite checked by the judge",
    "draft.rejected": "LLM rewrite rejected by the checks",
    "draft.fallback_static": "Rewrites rejected: standard template used",
    "draft.rewrite_unavailable": "LLM rewrite unavailable: standard template used",
    "error": "Error",
}


def event_text(type_: str, payload_json: str) -> tuple[str, str | None]:
    p = json.loads(payload_json or "{}")
    title = TITLES.get(type_, type_.replace(".", " ").capitalize())
    detail = None
    if type_ == "draft.sent":            # who sent it and where: a real WhatsApp send is not the demo record
        auto = p.get("decided_by") == "system"
        if p.get("delivery") == "whatsapp_sent":
            title = "Message sent automatically on WhatsApp" if auto else "Message sent on WhatsApp"
        elif auto:
            title = "Message sent automatically (simulated in this demo)"
    if type_ == "order.rescored" and p.get("tier"):
        detail = f"{p['tier'].upper()} {p.get('final_score')} · path {p.get('path')} · trigger {p.get('trigger')}"
    elif type_ == "llm.fallback":
        detail = f"path {p.get('path')}"
    elif type_ == "flags.resolved":
        detail = ", ".join(p.get("codes", []))
    elif type_ == "evidence.dropped":
        detail = f"{p.get('flags', 0)} flag(s), {p.get('quotes', 0)} quote(s)"
    elif type_ == "draft.created":
        detail = f"{p.get('template_id')} · {p.get('language')} · {p.get('route')}"
    elif type_ == "draft.judged":
        verdict = "approved" if p.get("approved") else "unavailable" if p.get("unavailable") else "rejected"
        by = {"llm": "LLM judge", "classifier": "guard classifier"}.get(p.get("decided_by"), p.get("decided_by"))
        decision = {"send": "classifier: clear to send", "review": "classifier: owner approval",
                    "block": "classifier: blocked"}.get(p.get("decision"))
        detail = (f"attempt {p.get('attempt')} · {verdict} by {by} · classifier risk {p.get('p_unsafe', 0):.0%}"
                  + (f" · {p['overreach']}" if p.get("overreach") not in (None, "none", "ok") else "")
                  + (f" · {decision}" if decision else (" · held for review" if p.get("hold") else "")))
    elif type_ == "draft.rejected":
        detail = f"attempt {p.get('attempt')} · {p.get('layer')}: {', '.join(p.get('failures', []))}"
    elif type_ == "draft.fallback_static":
        detail = f"after {p.get('attempts')} attempt(s)"
    elif type_ == "draft.rewrite_unavailable":
        detail = p.get("reason")
    elif type_ == "error":
        detail = p.get("error")
    return title, detail
