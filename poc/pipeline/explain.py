"""Deterministic explanation string built from the top feature contributions (no LLM)."""
import math

from .features import CATEGORIES, CHANNELS


def describe(name: str, f: dict[str, float], raising: bool) -> str:
    v = f.get(name, math.nan)
    if isinstance(v, float) and math.isnan(v):
        return "text not analyzed"
    match name:
        case "value_tnd":
            return f"order value {v:.0f} TND"
        case "item_count":
            return f"{int(v)} item{'s' if v != 1 else ''}"
        case "product_category":
            return f"product category: {CATEGORIES[int(v)]}"
        case "zone_tier":
            return ["urban zone", "peri-urban zone", "remote zone"][int(v)]
        case "is_first_order":
            return "first order from this customer" if v else "returning customer"
        case "prior_orders":
            return f"{int(v)} previous order{'s' if v != 1 else ''}"
        case "prior_refusals":
            return f"{int(v)} previous refusal{'s' if v != 1 else ''}" if v else "no previous refusals"
        case "hour_of_day":
            return f"ordered at {int(v):02d}:00"
        case "channel":
            return f"ordered via {CHANNELS[int(v)]}"
        case "address_specificity":
            return ["no usable address", "city-only address", "neighborhood-level address",
                    "precise address (street or landmark)"][int(v)]
        case "has_landmark":
            return "landmark given" if v else "no landmark"
        case "n_vague_location":
            return "vague location phrase" if v else "no vague location phrase"
        case "n_reschedule":
            return "asks to reschedule" if v else "no reschedule request"
        case "n_hesitation":
            return "hesitant wording in the note" if v else "no hesitation in the note"
        case "n_third_party":
            return "someone else will receive the parcel" if v else "customer receives in person"
        case "tone_hesitant":
            return "hesitant tone" if v else "no hesitant tone"
        case "tone_confident":
            return "confident tone" if v else "no confident signal in the note"
    return name


def explanation(tier: str, contribs: dict[str, float], features: dict[str, float], k: int = 3) -> str:
    raising = tier != "Low"
    ranked = sorted(contribs.items(), key=lambda kv: kv[1], reverse=raising)
    parts = [describe(n, features, raising) for n, c in ranked if (c > 0) == raising and abs(c) > 0.02][:k]
    if not parts:
        return f"{tier} risk: no single factor stands out."
    return f"{tier} risk: " + " + ".join(parts) + "."
