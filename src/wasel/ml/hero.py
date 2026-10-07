"""The hero scenario as ScoreInputs, shared by src/wasel/ml/train.py (writes tests/golden/hero.json) and
the hero golden test (tests/e2e/test_hero.py). The frozen extractions are served through the extraction cache,
so no LLM runs."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from wasel.contracts import (
    CachedExtraction,
    CustomerHistory,
    PriorAssessment,
    ScoreInput,
    ScoreResult,
    StructuredFields,
    WindowMessage,
)
from wasel.extraction.window import build_window
from wasel.llm.prompts import PROMPT_VERSION
from wasel.outbound.templates import render_template
from wasel.paths import ROOT

HERO_DIR = ROOT / "tests" / "fixtures" / "hero"
T0 = datetime(2026, 9, 27, 10, 0, 0, tzinfo=UTC)


def _load(name: str) -> dict:
    return json.loads((HERO_DIR / f"{name}.json").read_text(encoding="utf-8"))


def hero_messages(upto: int, templates: dict) -> list[WindowMessage]:
    """The hero conversation as scorer messages, up to and including script message `upto`.

    Seller lines become outbound 'ai' messages with the canonical template rendered in Arabizi; customer lines become
    inbound pasted text. Timestamps are T0 plus 10 s per message index.
    """
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
                                     m["template_id"], None, False, ts))
        else:
            out.append(WindowMessage(f"msg_{m['idx']}", "inbound", "customer", "paste", "text", m["text"], None,
                                     None, None, False, ts))
    return out


def hero_input(version: str, templates: dict, prior: PriorAssessment | None = None) -> ScoreInput:
    """ScoreInput for the hero scenario: 'v1' is the first score (messages up to 2, trigger initial); any other value
    is the rescore after the customer's reply (messages up to 4, trigger customer_reply). Pass the v1 result as
    `prior` for the rescore.
    """
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
    """Dict-backed ExtractionCache for tests, keyed by input hash."""
    entries: dict

    def get(self, input_hash: str) -> CachedExtraction | None:
        """The entry for `input_hash`, or None."""
        return self.entries.get(input_hash)


def cache_for(version: str, inp: ScoreInput) -> DictCache:
    """A cache holding the frozen fixture for exactly this window (origin 'llm')."""
    key = build_window(inp).cache_key(PROMPT_VERSION)
    return DictCache({key: CachedExtraction(key, "groq", "openai/gpt-oss-120b", "llm", _load(version))})


def prior_from(result: ScoreResult, version: int = 1) -> PriorAssessment:
    """PriorAssessment built from a score result, as the worker would store and reload it.

    `created_at` is T0 and the extraction id is a fixed placeholder. `version` is the version number to claim.
    """
    a = result.assessment
    return PriorAssessment(version=version, created_at=T0, extraction_id="ext_v1",
                           extraction=result.extraction.validated if result.extraction else None,
                           flag_codes=[f.code for f in a.flags], features=a.features, model_score=a.model_score,
                           final_score=a.final_score, tier=a.tier, path=a.path, reason=a.reason,
                           points=a.points, confirmation=a.confirmation)
