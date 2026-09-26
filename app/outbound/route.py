"""Draft routing (SD §8.4, 02 §8.2 rules 3/5/6/7). auto_send needs judge approval + confidence high +
price <= auto_send.max_tnd + the loop guard + the 24 h window. A static template is never judged, so it
routes to needs_review (a human clicks Send). A static template failing the prefilter -> blocked."""
from __future__ import annotations

from datetime import datetime, timedelta


def route_draft(*, source: str, prefilter_passed: bool, judge_approved: bool | None, confidence: str,
                price_tnd: float | None, auto_messages_sent: int, last_inbound_at: datetime | None,
                now: datetime, cfg: dict) -> str:
    if not prefilter_passed:
        return "blocked"
    if source == "static_template" or not judge_approved:
        return "needs_review"
    if confidence != "high" or price_tnd is None or price_tnd > cfg["auto_send"]["max_tnd"]:
        return "needs_review"
    if auto_messages_sent >= cfg["auto_send"]["max_auto_messages_per_order"]:
        return "needs_review"
    if last_inbound_at is not None and now - last_inbound_at > timedelta(hours=24):
        return "needs_review"
    return "auto_send"
