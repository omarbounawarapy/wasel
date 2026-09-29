"""Draft routing. auto_send needs the auto_send gate (config/scoring.yaml) +
confidence high + price <= auto_send.max_tnd + the loop guard + the 24 h window. Two gates:
"classifier" — the guard classifier's decision alone: "send" auto-sends, "review" is the owner-approval
queue; the judge's rejection still kills the rewrite in make_draft, it is just not required to send.
"judge" — the LLM judge must approve AND the classifier must clear the draft.
A static template is never auto-sent in either gate (a human clicks Send)."""
from __future__ import annotations

from datetime import datetime, timedelta


def route_draft(*, source: str, prefilter_passed: bool, judge_approved: bool | None, confidence: str,
                price_tnd: float | None, auto_messages_sent: int, last_inbound_at: datetime | None,
                now: datetime, cfg: dict, clf_decision: str | None = None) -> str:
    """Decide what happens to a draft: 'blocked', 'needs_review' or 'auto_send'.

    A failed prefilter blocks it and a static template always needs a person. An LLM rewrite auto-sends only when the
    configured gate clears it (the classifier alone, or the judge plus the classifier), confidence is high, the price
    is known and at or under the auto-send limit, the per-order auto-message limit is not reached, and the last
    customer message is within 24 hours.
    """
    if not prefilter_passed:
        return "blocked"
    if source == "static_template":
        return "needs_review"
    if cfg["auto_send"].get("gate", "judge") == "classifier":
        cleared = clf_decision == "send"
    else:
        cleared = bool(judge_approved) and clf_decision == "send"
    if not cleared:
        return "needs_review"
    if confidence != "high" or price_tnd is None or price_tnd > cfg["auto_send"]["max_tnd"]:
        return "needs_review"
    if auto_messages_sent >= cfg["auto_send"]["max_auto_messages_per_order"]:
        return "needs_review"
    if last_inbound_at is not None and now - last_inbound_at > timedelta(hours=24):
        return "needs_review"
    return "auto_send"
