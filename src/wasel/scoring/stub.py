"""Stub scorer with score_order's signature: is_order, path 'llm', tier high, final 78, one
vague_location span on the first customer message (start 0, end min(12, len)), template T_ADDRESS.
The persistence tests insert its result into a fresh DB."""
from __future__ import annotations

from wasel.contracts import (
    AssessmentRecord,
    EvidenceSpan,
    ExtractionRecord,
    FlagView,
    OrderPatch,
    ScoreInput,
    ScoreResult,
)
from wasel.ml.features import FEATURES


def score_order(inp: ScoreInput, *, cache=None, llm=None, meter=None, config=None) -> ScoreResult:
    """Fixed, deterministic result with score_order's signature. Ignores `cache`, `llm`, `meter` and `config`.

    Raises StopIteration if the input has no inbound customer text.
    """
    first = next(m for m in inp.messages if m.direction == "inbound" and m.text)
    end = min(12, len(first.text))
    span = EvidenceSpan(first.message_id, 0, end, "red_flag", "vague_location", first.text[:end])
    feats = dict(zip(FEATURES, [0.5, 1, 0, 220.0, 2, 0.30], strict=True))
    extraction = ExtractionRecord(
        input_message_ids=[m.message_id for m in inp.messages if m.direction == "inbound"], input_hash="stub",
        provider="groq", model="stub", prompt_version="extract-v1", cache_hit=False, attempts=[], output_json=None,
        validated={}, spans=[span], valid=True, dropped_flags=0, dropped_quotes=0, injection_suspected=False,
        error=None, latency_ms=0, tokens_in=0, tokens_out=0)
    version = (inp.prior.version + 1) if inp.prior else 1
    assessment = AssessmentRecord(
        path="llm", is_order_change=False, has_unsupported_media=False, features=feats, context={"stub": True},
        model_score=78.0, confirmation="none", adjustments=[], resolved_flags=[],
        flags=[FlagView("vague_location", span.quote, span.message_id)], final_score=78, tier="high",
        action="confirm", confidence="high", confidence_reasons=[], reason="HIGH 78 · stub",
        reason_short="HIGH 78 · stub", reason_diff=None if version == 1 else "stub diff", top_factors=[],
        classifier_version="stub", config_hash="stub0000", prompt_version="extract-v1")
    patch = OrderPatch("P12", "casque bluetooth", 220.0, 1, "rural", "gazetteer", None, "arabizi")
    return ScoreResult(True, extraction, None, assessment, patch, "T_ADDRESS")
