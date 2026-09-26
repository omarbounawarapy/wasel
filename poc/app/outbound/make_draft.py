"""make_draft(): the Saturday Must is static template + prefilter + human click (02 §8.1).
The LLM rewrite + judge (S-3, DRAFT_LLM) is not built: llm must be None."""
from __future__ import annotations

from app.contracts import CoreEvent, DraftRecord, DraftRequest, PrefilterResult, UsageMeter
from app.outbound.prefilter import prefilter
from app.outbound.route import route_draft
from app.outbound.templates import expected_questions, render_template, template_language
from app.scoring.config import ScoringConfig, default_config


def make_draft(req: DraftRequest, *, llm=None, meter: UsageMeter | None = None,
               config: ScoringConfig | None = None) -> DraftRecord:
    if llm is not None:
        raise NotImplementedError("S-3 rewrite + judge is not built; run with DRAFT_LLM=false (llm=None)")
    config = config or default_config()
    lang = template_language(req.language, req.customer_recent[-1] if req.customer_recent else None)
    canonical = render_template(config.templates, req.template_id, lang, req.slots)
    fails = prefilter(canonical, canonical, req.slots, expected_questions(config.templates, req.template_id),
                      config["prefilter"], config["lexicons"].get("injection"))
    route = route_draft(source="static_template", prefilter_passed=not fails, judge_approved=None,
                        confidence=req.confidence, price_tnd=req.price_tnd,
                        auto_messages_sent=req.auto_messages_sent, last_inbound_at=req.last_inbound_at,
                        now=req.now, cfg=config.raw)
    events = [CoreEvent("draft.created", "info", {"template_id": req.template_id, "language": lang,
                                                  "route": route})]
    if fails:
        events.append(CoreEvent("error", "error", {"static_template_failed_prefilter": fails}))
    return DraftRecord(req.template_id, lang, canonical, canonical, "static_template",
                       PrefilterResult(not fails, fails), None, route, [], events)
