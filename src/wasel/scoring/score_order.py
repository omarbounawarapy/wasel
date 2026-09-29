"""score_order(): the whole DB-free scoring core.

window -> input_hash -> cache -> meter + LLM chain -> rules extractor
-> repair -> evidence -> tone gate -> cross-field -> pin -> resolve_flags -> features -> XGBoost
pred_contribs -> reply adjustments -> tier/action/confidence -> reasons.
Never raises for provider problems (ends in path='rules'). Raises only on programmer error.
"""
from __future__ import annotations

import functools
from dataclasses import dataclass

from wasel.contracts import (
    Adjustment,
    AssessmentRecord,
    CachedExtraction,
    CacheEntry,
    CoreEvent,
    EvidenceSpan,
    ExtractionCache,
    ExtractionRecord,
    Factor,
    FlagView,
    OrderPatch,
    ScoreInput,
    ScoreResult,
    UsageMeter,
)
from wasel.extraction.cross_field import Processed, postprocess
from wasel.extraction.repair import OrderExtraction, parse_extraction
from wasel.extraction.rules_extractor import rules_extract
from wasel.extraction.window import Window, build_window
from wasel.llm import trace
from wasel.llm.prompts import PROMPT_VERSION, extraction_task
from wasel.ml.features import FEATURES, ZONE_DEC, build_features, score_prior, zone_from_text
from wasel.outbound.templates import choose_template
from wasel.scoring.catalog import match_product
from wasel.scoring.config import ScoringConfig, default_config
from wasel.scoring.model import load_model
from wasel.scoring.reason import build_diff, build_reason, driver_label, points

FLAG_LABELS = {"availability_uncertain": "May not be home", "vague_location": "Vague location",
               "price_hesitation": "Price hesitation", "third_party_recipient": "Someone else receives",
               "prior_refusal_mention": "Mentions a past refusal",
               "pressure_or_inconsistency": "Pressure or inconsistency"}


@dataclass
class _Extracted:
    ext: OrderExtraction
    path: str
    provider: str
    model: str
    path_origin: str
    cache_hit: bool
    attempts: list
    usage: list
    raw: str | None
    error: str | None
    latency_ms: int | None
    tokens_in: int | None
    tokens_out: int | None
    cap: str | None
    warnings: list[str]


def _from_cache(c: CachedExtraction) -> OrderExtraction:
    d = dict(c.extraction)
    d["red_flags"] = [{"evidence": f["evidence"], "code": f["code"]} for f in d["red_flags"]]
    return OrderExtraction.model_validate(d)


def _extract(inp: ScoreInput, w: Window, input_hash: str, *, cache, llm, meter, config: ScoringConfig) -> _Extracted:
    if cache is not None and (hit := cache.get(input_hash)) is not None:
        return _Extracted(_from_cache(hit), "cascade_cache", hit.provider, hit.model, hit.origin_path, True,
                          [], [], None, None, 0, 0, 0, None, [])
    res = None
    if llm is not None and not w.is_empty:
        res = llm.extract(extraction_task(), w.render(), parse=parse_extraction, meter=meter,
                          sandbox_id=inp.sandbox_id, now=inp.now)
        if res.parsed is not None:
            ext, warns = res.parsed
            m = res.meta
            return _Extracted(ext, res.path, res.provider, res.model, res.path, False, res.attempts, res.usage,
                              res.raw, "; ".join(res.errors) or None, m.latency_ms if m else None,
                              m.tokens_in if m else None, m.tokens_out if m else None, None,
                              [f"warn:{x}" for x in warns])
    ext = rules_extract(w, banks=config.banks, catalog=config.catalog, zones=config.zones,
                        lexicons=config["lexicons"])
    return _Extracted(ext, "rules", "rules", "rules_v1", "rules", False,
                      res.attempts if res else [], res.usage if res else [], None,
                      ("; ".join(res.errors) if res and res.errors else None), None, None, None,
                      res.cap if res else None, [])


def _tier(final: float, t: dict) -> str:
    return "low" if final < t["low_max"] else "medium" if final < t["medium_max"] else "high"


def _action(tier: str, price: float, confirmation: str, path: str, cfg: dict) -> str:
    if confirmation == "declined":
        return "cancelled"
    if path == "rules":
        return "review"
    if tier == "low":
        return "ship"
    if tier == "high" and price >= cfg["actions"]["prepay_min_tnd"]:
        return "prepay"
    return "confirm"


def _adjust(model_score: float, confirmation: str, trigger: str, cfg: dict) -> tuple[int, list[Adjustment]]:
    ra = cfg["reply_adjustments"]
    lo, hi = cfg["final_score"]["clip"]
    adjs: list[Adjustment] = []
    x = model_score
    if confirmation == "confirmed":
        m = ra["confirmed"]["multiply"]
        adjs.append(Adjustment("confirmed", f"Customer confirmed ×{m:g} (starting assumption)", f"x{m:g}",
                               x, x * m))
        x *= m
    elif confirmation in ("declined", "reschedule", "ambiguous"):
        label = {"declined": "Customer declined: order cancelled",
                 "reschedule": "Customer asked to reschedule (score unchanged)",
                 "ambiguous": "Unclear reply (score unchanged, needs review)"}[confirmation]
        adjs.append(Adjustment(confirmation, label, "none", x, x))
    if trigger == "no_reply_timeout":
        a = ra["no_reply_timeout"]["add"]
        adjs.append(Adjustment("no_reply_timeout", f"No reply before the timeout +{a:g} (starting assumption)",
                               f"+{a:g}", x, min(hi, x + a)))
        x += a
    return int(round(min(hi, max(lo, x)))), adjs


def _confidence(*, path: str, path_origin: str, proc: Processed | None, product_matched: bool,
                imputed: list[str], final: int, cap: str | None, cfg: dict) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if path == "rules":
        reasons.append("rules_path")
    elif not (path == "llm" or (path == "cascade_cache" and path_origin == "llm")):
        reasons.append("not_primary_model")
    if cap:
        reasons.append("llm_cap_reached")
    if proc is not None:
        if proc.clarity == "unclear":
            reasons.append("clarity_unclear")
        if proc.dropped_flags > cfg["confidence"]["max_dropped_flags"]:
            reasons.append("dropped_flags")
        if proc.injection_suspected:
            reasons.append("injection_suspected")          
    if not product_matched:
        reasons.append("product_not_in_catalog")
    if [i for i in imputed if i != "price_tnd"]:
        reasons.append("imputed_inputs")                    
    margin = cfg["confidence"]["boundary_margin"]
    if min(abs(final - cfg["tiers"]["low_max"]), abs(final - cfg["tiers"]["medium_max"])) < margin:
        reasons.append("near_tier_boundary")
    return ("low" if reasons else "high"), reasons


def _record_spans(proc: Processed) -> list[EvidenceSpan]:
    return [EvidenceSpan(s.message_id, s.start, s.end, s.kind, s.code, s.quote)
            for s in proc.spans if s.kind in ("red_flag", "address")]


def score_order(inp: ScoreInput, *, cache: ExtractionCache | None, llm, meter: UsageMeter | None,
                config: ScoringConfig | None = None) -> ScoreResult:
    config = config or default_config()
    cfg = config.raw
    trace.bind(order_id=inp.order_id, sandbox_id=inp.sandbox_id, trigger=inp.trigger)
    win = cfg.get("window", {})
    w = build_window(inp, win.get("max_messages", 12), win.get("max_chars", 2000))
    events: list[CoreEvent] = []

    # ---- no_reply_timeout: never calls the LLM; reuses the prior extraction, +15, path cascade_cache
    if inp.trigger == "no_reply_timeout" and inp.prior is not None:
        return _no_reply(inp, config)

    input_hash = w.cache_key(PROMPT_VERSION)
    x = _extract(inp, w, input_hash, cache=cache, llm=llm, meter=meter, config=config)
    if x.cache_hit:
        events.append(CoreEvent("cache.hit", "info", {"input_hash": input_hash[:12], "origin": x.path_origin}))
    if x.path not in ("llm", "cascade_cache") and x.attempts:
        events.append(CoreEvent("llm.fallback", "warning",
                                {"path": x.path, "attempts": [a.__dict__ for a in x.attempts]}))
    if x.cap:
        events.append(CoreEvent("llm.cap_reached", "warning", {"decision": x.cap}))

    prior_conf = inp.prior.confirmation if inp.prior else "none"
    proc = postprocess(x.ext, w, prior_confirmation=prior_conf,
                       injection_lexicon=cfg["lexicons"].get("injection", {}))
    valid = x.path != "rules"
    if proc.dropped_flags or proc.dropped_quotes:
        events.append(CoreEvent("evidence.dropped", "warning",
                                {"flags": proc.dropped_flags, "quotes": proc.dropped_quotes}))
    if proc.resolved_flags:
        events.append(CoreEvent("flags.resolved", "success", {"codes": proc.resolved_flags}))
    if proc.injection_suspected:
        events.append(CoreEvent("injection.suspected", "warning", {}))

    record = ExtractionRecord(
        input_message_ids=w.message_ids, input_hash=input_hash, provider=x.provider, model=x.model,
        prompt_version=PROMPT_VERSION, cache_hit=x.cache_hit, attempts=x.attempts, output_json=x.raw,
        validated=proc.validated(), spans=_record_spans(proc), valid=valid, dropped_flags=proc.dropped_flags,
        dropped_quotes=proc.dropped_quotes, injection_suspected=proc.injection_suspected,
        error="; ".join(filter(None, [x.error, *x.warnings])) or None, latency_ms=x.latency_ms,
        tokens_in=x.tokens_in, tokens_out=x.tokens_out)
    cache_put = None
    if x.path == "llm" and not x.cache_hit:            # fallbacks are never cached
        cache_put = CacheEntry(input_hash, PROMPT_VERSION, x.provider, x.model, "llm", proc.cache_extraction())

    if not proc.is_order:
        events.append(CoreEvent("extraction.not_order", "info", {}))
        return ScoreResult(False, record, cache_put, None, None, None, x.usage, events, False)

    # ---- resolve product, price, zone (structured > catalog/gazetteer > default)
    st, cat = inp.structured, config.catalog
    prod, _ = match_product(st.product_name or proc.product_quote, cat, cfg["catalog_match"]["min_score"])
    qty = st.quantity or proc.quantity
    qlo, qhi = cfg["catalog_match"]["quantity_clamp"]
    q_for_price = min(qhi, max(qlo, qty or 1))
    price = st.price_tnd if st.price_tnd is not None else (prod["price_tnd"] * q_for_price if prod else None)
    customer_texts = [m.text_orig for m in w.messages if m.role == "customer" and m.text_orig]
    if st.zone:
        zone, zone_src = st.zone, "csv"
    elif hit := zone_from_text([qq for qq, _ in proc.address_quotes], config.zones):
        zone, zone_src = hit
    elif hit := zone_from_text(customer_texts, config.zones):
        zone, zone_src = hit
    else:
        zone, zone_src = None, "default"
    feats, imputed = build_features(
        address_level=proc.address_level, flag_count=len(proc.flags), tone=proc.tone, price_tnd=price,
        zone=zone, refusals=inp.customer.refusals_total, completed=inp.customer.completed_orders)
    zone_name = ZONE_DEC[int(feats["zone_encoded"])]

    # ---- model
    lm = load_model(str(config.root / cfg["model"]["file"]))
    if lm is not None:
        out = lm.predict(feats)
        model_score, p0 = out.model_score, out.p0
        pts = points(out.phi, out.p, out.p0, cfg["reasons"]["linearise_if_abs_sum_phi_below"])
        classifier_version = lm.classifier_version
    else:                                                # model unavailable: the documented prior
        model_score, p0, pts, classifier_version = round(score_prior(feats), 1), 0.3, {}, "prior_v1"

    final, adjustments = _adjust(model_score, proc.confirmation, inp.trigger, cfg)
    tier = _tier(final, cfg["tiers"])
    action = _action(tier, feats["price_tnd"], proc.confirmation, x.path, cfg)
    confidence, conf_reasons = _confidence(path=x.path, path_origin=x.path_origin, proc=proc,
                                           product_matched=prod is not None, imputed=imputed, final=final,
                                           cap=x.cap, cfg=cfg)
    first_flag = proc.flags[0].quote if proc.flags else None
    ctx = {"address_quote": proc.address_quotes[0][0] if proc.address_quotes else None,
           "n_flags": len(proc.flags), "flag_evidence": first_flag, "tone_evidence": proc.tone_evidence,
           "price_tnd": feats["price_tnd"], "zone": zone_name,
           "completed": inp.customer.completed_orders, "refusals": inp.customer.refusals_total}
    if pts:
        reason, reason_short = build_reason(tier=tier, final=final, p0=p0, pts=pts, ctx=ctx,
                                            adjustments=adjustments, cfg=cfg["reasons"])
    else:
        reason = reason_short = f"{tier.upper()} {final} (model unavailable: documented prior)"
    reason_diff = None
    if inp.prior is not None:
        reason_diff = build_diff(v_prev=inp.prior.version, final_prev=inp.prior.final_score,
                                 v=inp.prior.version + 1, final=final, pts_prev=inp.prior.points, pts=pts,
                                 feats_prev=inp.prior.features, feats=feats, ctx=ctx,
                                 prev_codes=list(inp.prior.flag_codes), codes=proc.flag_codes,
                                 resolved=proc.resolved_flags, adjustments=adjustments, cfg=cfg["reasons"])
    top = sorted(pts.items(), key=lambda kv: -abs(kv[1]))[:3]
    top_factors = [Factor(k, driver_label(k, v, ctx), feats[k], round(v, 1)) for k, v in top]
    context = {
        "has_geo_pin": w.has_geo_pin, "product_id": prod["product_id"] if prod else None,
        "product_category": prod["category"] if prod else None, "quantity": qty,
        "customer_completed_orders": inp.customer.completed_orders,
        "customer_refusal_count": inp.customer.refusals_total, "zone_source": zone_src, "imputed": imputed,
        "resolved_flags": proc.resolved_flags, "tone_reset": proc.tone_reset,
        "address_level_raw": proc.address_level_raw, "address_level_final": proc.address_level,
        "clarity": proc.clarity, "language": proc.language, "tone": proc.tone, "path_origin": x.path_origin,
    }
    assessment_path = x.path
    assessment = AssessmentRecord(
        path=assessment_path, is_order_change=proc.is_order_change, has_unsupported_media=w.has_unsupported_media,
        features={k: feats[k] for k in FEATURES}, context=context, model_score=model_score,
        confirmation=proc.confirmation, adjustments=adjustments, resolved_flags=proc.resolved_flags,
        flags=[FlagView(f.code, f.quote, f.message_id) for f in proc.flags], final_score=final, tier=tier,
        action=action, confidence=confidence, confidence_reasons=conf_reasons, reason=reason,
        reason_short=reason_short, reason_diff=reason_diff, top_factors=top_factors,
        classifier_version=classifier_version, config_hash=config.short_hash, prompt_version=PROMPT_VERSION,
        injection_suspected=proc.injection_suspected, points={k: round(v, 3) for k, v in pts.items()})
    patch = OrderPatch(
        product_id=prod["product_id"] if prod else None,
        product_name=prod["name"] if prod else st.product_name, price_tnd=price, quantity=qty,
        zone=zone, zone_source="gazetteer" if zone_src == "keyword" else zone_src,   # DDL has no 'keyword'
        address_text=" · ".join(qq for qq, _ in proc.address_quotes) or None, language=proc.language)
    return ScoreResult(True, record, cache_put, assessment, patch,
                       choose_template(tier, action, proc.address_level), x.usage, events,
                       proc.injection_suspected)


def _no_reply(inp: ScoreInput, config: ScoringConfig) -> ScoreResult:
    """trigger='no_reply_timeout': prior extraction reused, +15, path cascade_cache, extraction=None."""
    cfg, pr = config.raw, inp.prior
    final, adjustments = _adjust(pr.model_score, "none", "no_reply_timeout", cfg)
    tier = _tier(final, cfg["tiers"])
    price = float(pr.features.get("price_tnd", 69))
    action = _action(tier, price, "none", "cascade_cache", cfg)
    reason = f"{tier.upper()} {final} · no reply before the timeout +15 (cold-start rule)"
    lm = load_model(str(config.root / cfg["model"]["file"]))
    assessment = AssessmentRecord(
        path="cascade_cache", is_order_change=False, has_unsupported_media=False, features=dict(pr.features),
        context={"reused_extraction_id": pr.extraction_id}, model_score=pr.model_score, confirmation="none",
        adjustments=adjustments, resolved_flags=[], flags=[], final_score=final, tier=tier, action=action,
        confidence="low", confidence_reasons=["no_reply_timeout"], reason=reason, reason_short=reason[:90],
        reason_diff=f"v{pr.version} {pr.final_score} → v{pr.version + 1} {final} · no reply +15",
        top_factors=[], classifier_version=lm.classifier_version if lm else "prior_v1",
        config_hash=config.short_hash, prompt_version=PROMPT_VERSION, points=dict(pr.points))
    return ScoreResult(True, None, None, assessment, None,
                       choose_template(tier, action, "street_and_landmark"), [], [])


def make_scorer(*, cache: ExtractionCache | None, llm, meter: UsageMeter | None,
                config: ScoringConfig | None = None):
    return functools.partial(score_order, cache=cache, llm=llm, meter=meter, config=config)

