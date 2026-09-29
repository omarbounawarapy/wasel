"""Outbound rewrite + judge. Three layers decide whether a draft may go out, cheapest first:

  1. prefilter      deterministic rules (numbers, URLs, phones, payment/discount/promise terms, question count)
  2. guard_clf      char n-gram TF-IDF + logistic regression, local, no LLM; a veto that can't be prompt-injected
  3. LLM judge      judge-v1 prompt, strict outbound_judge_v1 schema; approval is recomputed in code

Every layer can only take approval away. The judge never raises: any provider error, parse error, cap or
missing fixture is `unavailable` -> needs_review, never auto_send. The judge never sees customer text.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime

from wasel.contracts import UsageMeter, UsageRecord
from wasel.extraction.normalize import DEFUSE
from wasel.llm.base import ParseError
from wasel.llm.prompts import judge_task, rewrite_task
from wasel.outbound.guard_clf import decide

JUDGE_KEYS = {"unsupported_claims", "grounded", "language_ok", "tone_ok", "overreach", "question_count", "verdict"}
OVERREACH = {"none", "discount_or_price_change", "payment_request", "delivery_commitment", "instructions_in_draft",
             "other"}


@dataclass
class Verdict:
    approved: bool                   # all available layers approve
    hold: bool                       # approved but not trusted enough for auto_send (classifier in the grey zone)
    unavailable: bool                # the LLM judge could not answer
    judge_json: dict                 # stored in outbound_drafts.judge_json
    feedback: dict                   # fed to the one regeneration
    usage: list[UsageRecord] = field(default_factory=list)


def parse_judge(raw: str) -> dict:
    try:
        j = json.loads(raw)
    except ValueError as e:
        raise ParseError(str(e)[:120]) from e
    if not isinstance(j, dict) or set(j) != JUDGE_KEYS or j["overreach"] not in OVERREACH \
            or j["question_count"] not in ("none", "one", "several") or j["verdict"] not in ("approve", "reject") \
            or not isinstance(j["unsupported_claims"], list) \
            or not all(isinstance(j[k], bool) for k in ("grounded", "language_ok", "tone_ok")):
        raise ParseError("judge json shape")
    return j


def parse_rewrite(raw: str) -> str:
    try:
        j = json.loads(raw)
    except ValueError as e:
        raise ParseError(str(e)[:120]) from e
    if not isinstance(j, dict) or not isinstance(j.get("text"), str) or not j["text"].strip():
        raise ParseError("rewrite json shape")
    return j["text"].strip()


def approved_in_code(j: dict, expected_questions: str) -> bool:
    """The model's verdict alone is never enough."""
    return (j["verdict"] == "approve" and j["grounded"] and not j["unsupported_claims"] and j["language_ok"]
            and j["tone_ok"] and j["overreach"] == "none" and j["question_count"] == expected_questions)


def _call(llm, task, user: str, parse, *, role: str, meter: UsageMeter | None, sandbox_id: str | None,
          now: datetime):
    """(parsed or None, usage, why). Never raises: FixtureMissing (replay) and anything else -> None."""
    try:
        res = llm.extract(task, user, parse=parse, meter=meter, sandbox_id=sandbox_id, now=now, role=role)
    except Exception as e:                                # noqa: BLE001 - fail closed, never break drafting
        return None, [], type(e).__name__
    if res.parsed is None:
        return None, res.usage, (f"cap:{res.cap}" if res.cap else ";".join(res.errors)[:200] or "no_provider")
    return res.parsed, res.usage, f"{res.provider}:{res.model}"


def rewrite(llm, *, template_text: str, slots: dict, language: str, formality: str, tone_hint: str,
            expects_question: bool, feedback: dict | None, meter, sandbox_id, now):
    payload = {"template_text": template_text, "slots": slots, "language": language, "formality": formality,
               "tone_hint": tone_hint, "expects_question": expects_question}
    if feedback:
        payload["previous_attempt_problems"] = feedback
    return _call(llm, rewrite_task(), json.dumps(payload, ensure_ascii=False), parse_rewrite, role="rewrite",
                 meter=meter, sandbox_id=sandbox_id, now=now)


def judge(draft: str, facts: dict, *, llm, meter: UsageMeter | None, sandbox_id: str | None, now: datetime,
          block_at: float | None = None, hold_at: float | None = None,
          final_text: str | None = None) -> Verdict:
    """`draft` is what the LLM judge sees (the customer's name as a {first_name} placeholder); `final_text` is the
    text that would be sent, which the local classifier scores and turns into the send/review/block decision.
    block_at/hold_at default to config/scoring.yaml; pass 1.01/1.01 to measure the judge layer alone."""
    d = decide(final_text or draft, block_at=block_at, hold_at=hold_at)
    clf = {"p_unsafe": d.p_unsafe, "label": d.label, "top": d.top, "decision": d.decision}
    if d.decision == "block":                             # the veto: don't spend a judge call on it
        return Verdict(False, False, False, {"decided_by": "classifier", "classifier": clf},
                       {"overreach": d.label, "unsupported_claims": []})
    user = (f"<order_facts>{json.dumps(facts, ensure_ascii=False)}</order_facts>\n"
            f"<draft>{draft.translate(DEFUSE)}</draft>")
    j, usage, who = (None, [], "no_llm") if llm is None else \
        _call(llm, judge_task(), user, parse_judge, role="judge", meter=meter, sandbox_id=sandbox_id, now=now)
    if j is None:
        return Verdict(False, d.decision != "send", True,
                       {"unavailable": True, "reason": who, "decided_by": "classifier", "classifier": clf},
                       {}, usage)
    ok = approved_in_code(j, facts["expected_questions"])
    return Verdict(ok, ok and d.decision != "send", False,
                   {**j, "approved": ok, "decided_by": "llm", "judge_model": who, "classifier": clf},
                   {"overreach": j["overreach"], "unsupported_claims": [c[:80] for c in j["unsupported_claims"][:3]]},
                   usage)
