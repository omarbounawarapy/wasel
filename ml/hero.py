"""The hero scenario as ScoreInputs, shared by ml/train.py (writes tests/golden/hero.json) and
the E1 golden test. The frozen extractions are served through the extraction cache, so no LLM runs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.contracts import (
    CachedExtraction,
    CustomerHistory,
    PriorAssessment,
    ScoreInput,
    ScoreResult,
    StructuredFields,
    WindowMessage,
)
from app.extraction.window import build_window
from app.llm.prompts import PROMPT_VERSION
from app.outbound.templates import render_template

ROOT = Path(__file__).resolve().parents[1]
HERO_DIR = ROOT / "tests" / "fixtures" / "hero"
T0 = datetime(2026, 9, 27, 10, 0, 0, tzinfo=UTC)


def _load(name: str) -> dict:
    return json.loads((HERO_DIR / f"{name}.json").read_text(encoding="utf-8"))


def hero_messages(upto: int, templates: dict) -> list[WindowMessage]:
    script = _load("script")
    out = []
    for m in script["messages"]:
        if m["idx"] > upto:
            break
        ts = T0 + timedelta(seconds=10 * m["idx"])
        if m["role"] == "seller":
            canon = render_template(templates, m["template_id"], "arabizi",
                                    {"first_name": script["customer"]["display_name"],
                                     "product": "casque bluetooth"})
            out.append(WindowMessage(f"msg_{m['idx']}", "outbound", "ai", "simulated", "text", canon, canon,
                                     m["template_id"], None, False, ts, True))
        else:
            out.append(WindowMessage(f"msg_{m['idx']}", "inbound", "customer", "paste", "text", m["text"], None,
                                     None, None, False, ts, True))
    return out


def hero_input(version: str, templates: dict, prior: PriorAssessment | None = None) -> ScoreInput:
    upto = 2 if version == "v1" else 4
    script = _load("script")
    return ScoreInput(
        order_id="ord_hero", sandbox_id=None, channel="simulated",
        trigger="initial" if version == "v1" else "customer_reply",
        messages=hero_messages(upto, templates), structured=StructuredFields(),
        customer=CustomerHistory(script["customer"]["completed_orders"], script["customer"]["refusals_total"]),
        prior=prior, now=T0 + timedelta(seconds=60 if version == "v1" else 120))


@dataclass
class DictCache:
    entries: dict

    def get(self, input_hash: str) -> CachedExtraction | None:
        return self.entries.get(input_hash)


def cache_for(version: str, inp: ScoreInput) -> DictCache:
    """A cache holding the frozen fixture for exactly this window (origin 'llm')."""
    key = build_window(inp).cache_key(PROMPT_VERSION)
    return DictCache({key: CachedExtraction(key, "groq", "openai/gpt-oss-120b", "llm", _load(version))})


def prior_from(result: ScoreResult, version: int = 1) -> PriorAssessment:
    a = result.assessment
    return PriorAssessment(version=version, created_at=T0, extraction_id="ext_v1",
                           extraction=result.extraction.validated if result.extraction else None,
                           flag_codes=[f.code for f in a.flags], features=a.features, model_score=a.model_score,
                           final_score=a.final_score, tier=a.tier, path=a.path, reason=a.reason,
                           points=a.points, confirmation=a.confirmation)
