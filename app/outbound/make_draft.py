"""make_draft(): static template + prefilter + human click (02 §8.1), and with an LLM client (DRAFT_LLM=true)
the S-3 rewrite + judge flow of 02 §8.2:

  rewrite -> prefilter -> guard classifier -> LLM judge      (at most `max_attempts` rewrites, with feedback)
  any rewrite that doesn't pass every layer -> the static template, which a human sends
  judge unavailable -> the rewrite goes to needs_review (never auto_send), unless the classifier holds it
"""
from __future__ import annotations

import re

from app.contracts import CoreEvent, DraftRecord, DraftRequest, PrefilterResult, UsageMeter
from app.llm import trace
from app.outbound import judge as J
from app.outbound.prefilter import prefilter
from app.outbound.route import route_draft
from app.outbound.templates import expected_questions, render_template, template_language, template_slots
from app.scoring.config import ScoringConfig, default_config

NAME = "{first_name}"             # personal data never reaches an LLM: the name is a placeholder, filled in by code
AUTHORIZED = {"T_CONFIRM": "ask_confirmation", "T_ADDRESS": "ask_exact_address_and_confirmation",
              "T_PREPAY": "ask_payment_before_delivery", "T_ACK": "acknowledge_confirmation"}
_VOUS = re.compile(r"\bvous\b", re.I)


def formality(lang: str, customer_recent: list[str]) -> str:
    """02 §8.2: French with "vous" in any customer line -> formal; Darija/Arabizi -> informal."""
    if lang != "fr":
        return "informal"
    return "formal" if any(_VOUS.search(t or "") for t in customer_recent) or not customer_recent else "informal"


def make_draft(req: DraftRequest, *, llm=None, meter: UsageMeter | None = None,
               config: ScoringConfig | None = None) -> DraftRecord:
    config = config or default_config()
    lang = template_language(req.language, req.customer_recent[-1] if req.customer_recent else None)
    canonical = render_template(config.templates, req.template_id, lang, req.slots)
    used = template_slots(config.templates, req.template_id, lang, req.slots)
    expected = expected_questions(config.templates, req.template_id)

    def check(text: str) -> list[str]:
        return prefilter(text, canonical, used, expected, config["prefilter"], config["lexicons"].get("injection"))

    def route(source: str, passed: bool, approved: bool | None) -> str:
        return route_draft(source=source, prefilter_passed=passed, judge_approved=approved,
                           confidence=req.confidence, price_tnd=req.price_tnd,
                           auto_messages_sent=req.auto_messages_sent, last_inbound_at=req.last_inbound_at,
                           now=req.now, cfg=config.raw)

    events: list[CoreEvent] = []
    usage: list = []
    trace.bind(order_id=req.order_id, sandbox_id=req.sandbox_id, template_id=req.template_id)
    if llm is not None:
        rec = _rewrite_and_judge(req, llm, meter, config, lang, canonical, used, expected, check, route,
                                 events, usage)
        if rec is not None:
            return rec

    fails = check(canonical)
    r = route("static_template", not fails, None)
    events.insert(0, CoreEvent("draft.created", "info", {"template_id": req.template_id, "language": lang,
                                                         "route": r, "source": "static_template"}))
    if fails:
        events.append(CoreEvent("error", "error", {"static_template_failed_prefilter": fails}))
    return DraftRecord(req.template_id, lang, canonical, canonical, "static_template",
                       PrefilterResult(not fails, fails), None, r, usage, events)


def _rewrite_and_judge(req, llm, meter, config, lang, canonical, used, expected, check, route, events, usage):
    jc = config.raw.get("outbound", {}).get("judge", {})
    form = formality(lang, req.customer_recent)
    name = used.get("first_name")
    llm_slots = {**used, "first_name": NAME} if name else dict(used)
    llm_template = render_template(config.templates, req.template_id, lang, {**req.slots, "first_name": NAME}) \
        if name else canonical
    facts = {"product": req.slots.get("product"), "price_tnd": req.slots.get("price_tnd"), "quantity": 1,
             "authorized_action": AUTHORIZED[req.template_id], "template_id": req.template_id,
             "approved_template": llm_template, "language": lang, "formality": form, "expected_questions": expected}
    feedback = None
    for attempt in range(1, int(jc.get("max_attempts", 2)) + 1):
        raw, u, who = J.rewrite(llm, template_text=llm_template, slots=llm_slots, language=lang, formality=form,
                                 tone_hint="neutral", expects_question=expected != "none", feedback=feedback,
                                 meter=meter, sandbox_id=req.sandbox_id, now=req.now)
        usage += u
        if raw is None:
            events.append(CoreEvent("draft.rewrite_unavailable", "warning", {"reason": who}))
            return None
        text = raw.replace(NAME, name) if name else raw
        fails = check(text) + (["name_placeholder_missing"] if name and raw.count(NAME) != 1 else [])
        if fails:
            events.append(CoreEvent("draft.rejected", "warning", {"attempt": attempt, "layer": "prefilter",
                                                                  "failures": fails}))
            feedback = {"prefilter_fails": fails}
            continue
        v = J.judge(raw, facts, llm=llm, meter=meter, sandbox_id=req.sandbox_id, now=req.now, final_text=text)
        usage += v.usage
        summary = {"attempt": attempt, "decided_by": v.judge_json.get("decided_by"), "approved": v.approved,
                   "hold": v.hold, "unavailable": v.unavailable,
                   "p_unsafe": v.judge_json["classifier"]["p_unsafe"],
                   "decision": v.judge_json["classifier"].get("decision"),
                   "overreach": v.judge_json.get("overreach", v.feedback.get("overreach"))}
        events.append(CoreEvent("draft.judged", "success" if v.approved else "warning", summary))
        if v.unavailable and v.hold:
            return None                                   # no judge and a doubtful classifier: send the template
        if v.approved or v.unavailable:
            r = route("llm_rewrite", True, v.approved and not v.hold)
            events.insert(0, CoreEvent("draft.created", "info", {"template_id": req.template_id, "language": lang,
                                                                 "route": r, "source": "llm_rewrite"}))
            return DraftRecord(req.template_id, lang, canonical, text, "llm_rewrite", PrefilterResult(True, []),
                               v.judge_json, r, usage, events)
        feedback = v.feedback
    events.append(CoreEvent("draft.fallback_static", "warning", {"attempts": attempt}))
    return None
