"""Feature contract, the data-generating prior, and the pure serve-side rules.

The single import for the generator, the trainer and the serve path. Changing a PRIOR constant
means regenerating and retraining; synth_v1.meta.json records this file's sha256.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ml.textnorm import has_phrase, tokens

# ---------------------------------------------------------------- contract (order is load-bearing)
FEATURES = ("address_specificity", "red_flag_count", "tone_score",
            "price_tnd", "zone_encoded", "customer_refusal_rate")
MONOTONE = (-1, 1, 1, 1, 1, 1)
CONTEXT_KEYS = ("has_geo_pin", "product_id", "product_category", "quantity",
                "customer_completed_orders", "customer_refusal_count", "zone_source",
                "imputed", "resolved_flags", "tone_reset", "address_level_raw", "address_level_final",
                "clarity", "language", "tone")

LEVELS = ("none", "city_only", "area_or_landmark", "street_and_landmark", "exact")
LEVEL_TO_SPEC = {"none": 0.0, "city_only": 0.25, "area_or_landmark": 0.5,
                 "street_and_landmark": 0.75, "exact": 1.0}
TONE_ENC = {"positive": -1, "neutral": 0, "uncertain": 1, "negative": 2}
ZONE_ENC = {"urban": 0, "suburban": 1, "rural": 2}
ZONE_DEC = {v: k for k, v in ZONE_ENC.items()}
FLAG_ORDER = ("vague_location", "availability_uncertain", "price_hesitation",
              "third_party_recipient", "prior_refusal_mention", "pressure_or_inconsistency")

# ---------------------------------------------------------------- the prior
PRIOR = {
    "w_vag": 0.35, "w_price": 0.15, "w_zone": 0.10, "w_rate": 0.20, "w_flags": 0.10, "w_tone": 0.10,
    "price_lo": 20.0, "price_hi": 600.0, "flags_cap": 3, "S_mid": 43.0, "S_scale": 12.0,
}
_TONE_C = {-1: 0.0, 0: 0.25, 1: 0.75, 2: 1.0}
SERVE_DEFAULTS = {"address_specificity": 0.0, "red_flag_count": 0, "tone_score": 0,
                  "price_tnd": 69.0, "zone_encoded": 1, "customer_refusal_rate": 0.30}


def smoothed_rate(refusals: int, completed: int) -> float:
    """(r + 0.6) / (n + 2): a new customer gets 0.30."""
    return (refusals + 0.6) / (completed + 2)


def S(f: dict) -> float:
    p = PRIOR
    price = max(float(f["price_tnd"]), 1e-9)
    price_c = min(1.0, max(0.0, (math.log(price) - math.log(p["price_lo"]))
                           / (math.log(p["price_hi"]) - math.log(p["price_lo"]))))
    return 100.0 * (p["w_vag"] * (1.0 - f["address_specificity"])
                    + p["w_price"] * price_c
                    + p["w_zone"] * f["zone_encoded"] / 2.0
                    + p["w_rate"] * f["customer_refusal_rate"]
                    + p["w_flags"] * min(int(f["red_flag_count"]), p["flags_cap"]) / p["flags_cap"]
                    + p["w_tone"] * _TONE_C[int(f["tone_score"])])


def p_true(s: float) -> float:
    return 1.0 / (1.0 + math.exp(-(s - PRIOR["S_mid"]) / PRIOR["S_scale"]))


def score_prior(f: dict) -> float:
    """Model-unavailable fallback: 100 · p_true(S(features))."""
    return 100.0 * p_true(S(f))


# ---------------------------------------------------------------- zone
def _zone_in(text: str, zones: dict) -> tuple[str, str] | None:
    for entry in zones.get("entries", []):
        for alias in [entry["name"], *entry.get("aliases", [])]:
            if has_phrase(text, alias):
                return entry["zone"], "gazetteer"
    toks = set(tokens(text))
    for zone, words in zones.get("keywords", {}).items():
        if any(w in toks or has_phrase(text, w) for w in words):
            return zone, "keyword"
    return None


def zone_from_text(texts: list[str], zones: dict) -> tuple[str, str] | None:
    """Latest text wins; within a text an alias beats a keyword. Returns (zone, source) or None."""
    for t in reversed(texts):
        hit = _zone_in(t, zones)
        if hit:
            return hit
    return None


# ---------------------------------------------------------------- flags and tone
@dataclass(frozen=True)
class VerifiedFlag:
    code: str
    msg_idx: int
    start: int
    end: int
    message_id: str
    quote: str


def dedupe_by_code(flags: list[VerifiedFlag]) -> list[VerifiedFlag]:
    """One flag per code: the one with the largest (msg_idx, start), i.e. the latest evidence."""
    best: dict[str, VerifiedFlag] = {}
    for f in flags:
        cur = best.get(f.code)
        if cur is None or (f.msg_idx, f.start) > (cur.msg_idx, cur.start):
            best[f.code] = f
    return [best[c] for c in FLAG_ORDER if c in best]


def resolve_flags(flags: list[VerifiedFlag], address_level_final: str, confirmation: str,
                  k: int | None) -> tuple[list[VerifiedFlag], list[str]]:
    """Never adds a flag. r(r(x)) == r(x); r(x) ⊆ x. Returns (kept, resolved_codes in FLAG_ORDER)."""
    kept, resolved = [], []
    for f in flags:
        drop = (
            (f.code == "vague_location" and address_level_final == "exact")
            or (f.code == "availability_uncertain" and k is not None
                and confirmation in ("confirmed", "reschedule") and f.msg_idx < k)
            or (f.code == "price_hesitation" and k is not None
                and confirmation == "confirmed" and f.msg_idx < k)
        )
        (resolved if drop else kept).append(f)
    codes = {f.code for f in resolved}
    return kept, [c for c in FLAG_ORDER if c in codes]


def tone_gate(tone: str, tone_span: tuple[int, int, int] | None,
              flag_spans: list[tuple[int, int, int]]) -> str:
    """tone_span / flag_spans are (msg_idx, start, end). Non-neutral tone needs a verified span that
    overlaps no verified flag span (pre-resolve)."""
    if tone == "neutral" or tone_span is None:
        return "neutral"
    ti, ts, te = tone_span
    if any(i == ti and s < te and ts < e for i, s, e in flag_spans):
        return "neutral"
    return tone


# ---------------------------------------------------------------- vector
def build_features(*, address_level: str, flag_count: int, tone: str, price_tnd: float | None,
                   zone: str | None, refusals: int, completed: int) -> tuple[dict, list[str]]:
    """Returns (features in FEATURES order, imputed names). Never returns NaN (ML9)."""
    imputed: list[str] = []
    f = {
        "address_specificity": LEVEL_TO_SPEC[address_level],
        "red_flag_count": int(flag_count),
        "tone_score": TONE_ENC[tone],
        "price_tnd": float(price_tnd) if price_tnd is not None else None,
        "zone_encoded": ZONE_ENC[zone] if zone is not None else None,
        "customer_refusal_rate": smoothed_rate(refusals, completed),
    }
    for k in ("price_tnd", "zone_encoded"):
        if f[k] is None or (isinstance(f[k], float) and math.isnan(f[k])):
            f[k] = SERVE_DEFAULTS[k]
            imputed.append("zone" if k == "zone_encoded" else k)
    return {k: f[k] for k in FEATURES}, imputed
