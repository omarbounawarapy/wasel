"""event type -> (title, detail) for the activity feed. English source.

No enum or pipeline name reaches the feed: template, language, route, path and trigger values are mapped to plain words.
The path and trigger wording matches dashboard/app.py.
"""
from __future__ import annotations

import json
import re

TITLES = {
    "message.received": "Customer message received",
    "order.rescored": "Order rescored",
    "draft.created": "Confirmation drafted",
    "draft.sent": "Message sent (simulated in this demo)",
    "draft.recorded_for_simulation": "Draft recorded as sent for the simulated reply",
    "llm.fallback": "Primary model unavailable: fallback used",
    "llm.cap_reached": "Live-AI budget reached: scored with rules",
    "cache.hit": "Answered from an earlier result (no AI call)",
    "cascade.hit": "Answered without an AI call",
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


TEMPLATE_WORDS = {"T_CONFIRM": "order confirmation", "T_ADDRESS": "address question", "T_PREPAY": "prepayment question",
                  "T_ACK": "acknowledgement"}
LANGUAGE_WORDS = {"fr": "French", "ar": "Arabic", "darija_arabic_script": "Darija (Arabic script)",
                  "arabizi": "Arabizi (Latin letters)", "mixed": "mixed languages"}
ROUTE_WORDS = {"auto_send": "sent automatically", "needs_review": "waiting for your OK", "blocked": "blocked by the checks"}
PATH_WORDS = {"llm": "AI extraction", "fallback_model": "backup AI model", "fallback_provider": "backup AI provider",
              "cascade_ack": "short reply, no AI call", "cascade_cache": "earlier result, no new AI call",
              "rules": "rules only (no AI)"}
TRIGGER_WORDS = {"initial": "first score", "customer_reply": "customer replied", "no_reply_timeout": "no reply in time",
                 "manual": "manual rescore"}


def _words(*parts) -> str | None:
    """Join the parts that have wording; a value without wording is left out rather than shown raw."""
    shown = [p for p in parts if p]
    return " · ".join(shown) if shown else None


def event_text(type_: str, payload_json: str) -> tuple[str, str | None]:
    """Render an event's (title, detail) for the activity feed.

    `payload_json` is the events.payload column (a JSON object string). Unknown types get a title derived from the type
    name and no detail. draft.sent titles reflect whether it was a real WhatsApp send and whether the system sent it.
    """
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
        detail = _words(f"{p['tier'].upper()} {p.get('final_score')}", PATH_WORDS.get(p.get("path")),
                        TRIGGER_WORDS.get(p.get("trigger")))
    elif type_ == "llm.fallback":
        detail = _words(PATH_WORDS.get(p.get("path")))
    elif type_ == "flags.resolved":
        detail = ", ".join(p.get("codes", []))
    elif type_ == "evidence.dropped":
        detail = f"{p.get('flags', 0)} flag(s), {p.get('quotes', 0)} quote(s)"
    elif type_ == "draft.created":
        detail = _words(TEMPLATE_WORDS.get(p.get("template_id")), LANGUAGE_WORDS.get(p.get("language")),
                        ROUTE_WORDS.get(p.get("route")))
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
    elif type_ == "error":                              # never an exception message: it can carry paths and internals
        err = str(p.get("error") or "")
        detail = err if p.get("reason") == "order_timeout" else (
            f"Scoring failed ({err}); the cause is in the server log" if re.fullmatch(r"\w{1,60}", err)
            else "Something failed; the cause is in the server log")
    return title, detail
