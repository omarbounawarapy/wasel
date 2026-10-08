"""Order state machine and seller actions."""
from __future__ import annotations

from wasel.contracts import ScoreResult

RANK = {"low": 0, "medium": 1, "high": 2}
TERMINAL = ("shipped", "delivered", "refused", "cancelled")

ACTIONS = {                       # action -> (allowed from, to)
    "approve": (("needs_review", "awaiting_reply"), "ready_to_ship"),
    "request_confirmation": (("needs_review",), "awaiting_reply"),
    "cancel": (("collecting", "awaiting_reply", "needs_review", "ready_to_ship"), "cancelled"),
    "ship": (("ready_to_ship",), "shipped"),
    "mark_delivered": (("shipped",), "delivered"),
    "mark_refused": (("shipped",), "refused"),
}


def allowed_actions(status: str) -> list[str]:
    """Seller actions valid from `status`, in ACTIONS order."""
    return [a for a, (frm, _) in ACTIONS.items() if status in frm]


def next_status(current: str, result: ScoreResult, trigger: str, prior_tier: str | None,
                seller_approved_at: str | None) -> str:
    """First match wins."""
    a = result.assessment
    if current in TERMINAL:                                                 # a closed order stays closed
        return current
    if result.injection_suspected:                                          # 0
        return "needs_review"
    if not result.is_order or a is None:                                    # 1
        return current
    if a.confirmation == "declined":                                        # 2
        return "needs_review" if a.path == "rules" else "cancelled"       # a rules-read decline needs a person
    if a.is_order_change:                                                   # 3
        return "needs_review"
    if (a.path != "rules" and result.extraction is not None and not result.extraction.valid) \
            or a.has_unsupported_media:                                     # 4
        return "needs_review"
    if trigger == "no_reply_timeout":                                       # 5
        return "needs_review"
    if a.confirmation == "ambiguous":                                       # 6
        return "needs_review"
    if current == "ready_to_ship" and seller_approved_at and prior_tier and \
            RANK[a.tier] <= RANK[prior_tier]:                               # 7
        return "ready_to_ship"
    if current == "ready_to_ship" and seller_approved_at:                   # 8
        return "needs_review"
    if a.tier == "low":                                                     # 9
        return "ready_to_ship"
    if current == "needs_review":                                           # 10
        return "needs_review"
    return "awaiting_reply"                                                 # 11
