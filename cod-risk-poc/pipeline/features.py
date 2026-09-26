"""Order + flags -> numeric feature vector. Text features are NaN when extraction failed
(XGBoost routes missing values natively, so the order is still scored on structured data)."""
import datetime as dt
import math

from .schemas import Flags

CATEGORIES = ["fashion", "electronics", "cosmetics", "home", "sports", "kids"]
CHANNELS = ["website", "facebook", "instagram"]
ZONES = {"urban": 0, "peri-urban": 1, "remote": 2}

FEATURES = [
    "value_tnd", "item_count", "product_category", "zone_tier", "is_first_order",
    "prior_orders", "prior_refusals", "hour_of_day", "channel",
    "address_specificity", "has_landmark", "n_vague_location", "n_reschedule",
    "n_hesitation", "n_third_party", "tone_hesitant", "tone_confident",
]
TEXT_FEATURES = FEATURES[9:]


def _hour(created_at: str) -> float:
    try:
        return float(dt.datetime.fromisoformat(str(created_at)).hour)
    except ValueError:
        return math.nan


def to_features(order: dict, flags: Flags | None) -> dict[str, float]:
    cat = str(order["product_category"])
    f = {
        "value_tnd": float(order["value_tnd"]),
        "item_count": float(order["item_count"]),
        "product_category": float(CATEGORIES.index(cat)) if cat in CATEGORIES else math.nan,
        "zone_tier": float(ZONES.get(order["zone_tier"], math.nan)),
        "is_first_order": float(bool(order["is_first_order"])),
        "prior_orders": float(order["prior_orders"]),
        "prior_refusals": float(order["prior_refusals"]),
        "hour_of_day": _hour(order["created_at"]),
        "channel": float(CHANNELS.index(order["channel"])) if order["channel"] in CHANNELS else math.nan,
    }
    if flags is None:
        f.update({k: math.nan for k in TEXT_FEATURES})
        return f
    count = lambda t: float(sum(1 for r in flags.red_flags if r.type == t))  # noqa: E731
    f.update({
        "address_specificity": float(flags.address_specificity),
        "has_landmark": float(flags.has_landmark),
        "n_vague_location": count("vague_location"),
        "n_reschedule": max(count("reschedule"), float(flags.reschedule_requested)),
        "n_hesitation": count("hesitation"),
        "n_third_party": count("third_party_receiver"),
        "tone_hesitant": float(flags.tone in ("hesitant", "hostile")),
        "tone_confident": float(flags.tone == "confident"),
    })
    return f
