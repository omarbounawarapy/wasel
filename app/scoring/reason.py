"""SHAP -> points -> reason strings. Deterministic; no LLM writes a reason. Every customer quote
is wrapped in U+2068 FSI … U+2069 PDI so Arabic quotes can't reorder the English sentence."""
from __future__ import annotations

from ml.features import FEATURES, ZONE_DEC

FSI, PDI = "⁨", "⁩"
TIER_WORD = {"low": "LOW", "medium": "MEDIUM", "high": "HIGH"}


def points(phi: dict[str, float], p: float, p0: float, lin_below: float = 0.05) -> dict[str, float]:
    """Exact and additive: the points sum to model_score − 100·p0."""
    s = sum(phi.values())
    if abs(s) >= lin_below:
        return {k: 100.0 * (p - p0) * v / s for k, v in phi.items()}
    return {k: 100.0 * p0 * (1 - p0) * v for k, v in phi.items()}


def q(text: str | None, max_chars: int = 40) -> str:
    if not text:
        return ""
    t = text if len(text) <= max_chars else text[: max_chars - 1] + "…"
    return f"\"{FSI}{t}{PDI}\""


def _pts(x: float) -> str:
    n = round(x)
    return f"+{n}" if n > 0 else f"−{abs(n)}" if n < 0 else "±0"


def driver_label(feature: str, pts: float, ctx: dict) -> str:
    up = pts > 0
    if feature == "address_specificity":
        quote = ctx.get("address_quote")
        if up:
            return f"vague address ({q(quote)})" if quote else "no usable address"
        return f"full address given ({q(quote)})" if quote else "full address given"
    if feature == "red_flag_count":
        n = ctx.get("n_flags", 0)
        if up and n:
            return f"{n} warning sign{'s' if n != 1 else ''}: {q(ctx.get('flag_evidence'))}"
        return "no warning signs"
    if feature == "tone_score":
        return f"hesitant tone ({q(ctx.get('tone_evidence'))})" if up and ctx.get("tone_evidence") \
            else "hesitant tone" if up else "confident tone"
    if feature == "price_tnd":
        return f"{'high' if up else 'low'} order value ({ctx.get('price_tnd'):g} TND)"
    if feature == "zone_encoded":
        return f"{ctx.get('zone', 'unknown')} delivery zone"
    if feature == "customer_refusal_rate":
        n, r = ctx.get("completed", 0), ctx.get("refusals", 0)
        if n == 0:
            return "new customer (no order history)"
        return f"{r} of {n} past orders refused" if up else f"good order history ({n - r} delivered)"
    return feature


def select_drivers(pts: dict[str, float], tier: str, cfg: dict) -> list[str]:
    mn, mx = cfg["min_pts"], cfg["max_drivers"]
    if tier in ("medium", "high"):
        chosen = [k for k, v in sorted(pts.items(), key=lambda kv: -kv[1]) if v >= mn][:mx]
    else:
        chosen = [k for k, v in sorted(pts.items(), key=lambda kv: kv[1]) if v <= -mn][:2]
    if "zone_encoded" not in chosen and abs(pts.get("zone_encoded", 0)) >= cfg["always_show_zone_if_abs_pts_at_least"]:
        chosen.append("zone_encoded")
    return chosen


def adjustment_text(adj) -> str:
    if adj.rule == "confirmed":
        return f"customer confirmed ×0.6 (cold-start rule) {_pts(adj.after - adj.before)}"
    if adj.rule == "no_reply_timeout":
        return f"no reply before the timeout +15 (cold-start rule) {_pts(adj.after - adj.before)}"
    return adj.label


def build_reason(*, tier: str, final: int, p0: float, pts: dict[str, float], ctx: dict,
                 adjustments: list, cfg: dict) -> tuple[str, str]:
    parts = [f"{TIER_WORD[tier]} {final}", f"base {round(100 * p0)}"]
    drivers = [f"{driver_label(k, pts[k], ctx)} {_pts(pts[k])}" for k in select_drivers(pts, tier, cfg)]
    adj = [adjustment_text(a) for a in adjustments if a.after != a.before or a.rule in ("declined",)]
    reason = " · ".join(parts + drivers + adj)
    short = f"{TIER_WORD[tier]} {final}"
    for d in drivers + adj:
        cand = f"{short} · {d}"
        if len(cand) > 90:
            break
        short = cand
    return reason, short[:90]


def build_diff(*, v_prev: int, final_prev: int, v: int, final: int, pts_prev: dict[str, float],
               pts: dict[str, float], feats_prev: dict, feats: dict, ctx: dict, prev_codes: list[str],
               codes: list[str], resolved: list[str], adjustments: list, cfg: dict) -> str:
    items = []
    for k in FEATURES:
        if k not in pts or k not in pts_prev:
            continue
        d = pts[k] - pts_prev[k]
        if abs(d) < cfg["diff_min_delta_pts"]:
            continue
        if k == "address_specificity":
            txt = (f"full address given ({q(ctx.get('address_quote'))})" if d < 0
                   else f"address less precise ({q(ctx.get('address_quote'))})")
        elif k == "red_flag_count":
            gone = [c for c in prev_codes if c not in codes] or resolved
            txt = (f"warning signs resolved ({', '.join(sorted(gone))})" if d < 0
                   else f"new warning sign: {q(ctx.get('flag_evidence'))}")
        elif k == "tone_score":
            inv = {-1: "positive", 0: "neutral", 1: "uncertain", 2: "negative"}
            txt = f"tone {inv[int(feats_prev[k])]} → {inv[int(feats[k])]}"
        elif k == "price_tnd":
            txt = f"order value changed ({feats_prev[k]:g} → {feats[k]:g} TND)"
        elif k == "zone_encoded":
            txt = f"delivery zone changed ({ZONE_DEC[int(feats_prev[k])]} → {ZONE_DEC[int(feats[k])]})"
        else:
            txt = "order history updated"
        items.append((abs(d), f"{txt} {_pts(d)}"))
    items.sort(key=lambda t: -t[0])
    adj = [adjustment_text(a) for a in adjustments if a.after != a.before]
    return " · ".join([f"v{v_prev} {final_prev} → v{v} {final}", *[t for _, t in items], *adj])
