"""Hero golden and robustness. Runs the real score_order through the live
chain code with a ReplayBackend over the frozen fixtures (hand_crafted fixtures), and asserts both the documented ranges and equality with tests/golden/hero.json."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.extraction.window import build_window
from app.llm.client import ChainClient, ChainStep, ReplayBackend
from app.scoring.score_order import score_order
from ml.features import FEATURES
from ml.hero import HERO_DIR, hero_input, prior_from

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = json.loads((ROOT / "tests/golden/hero.json").read_text(encoding="utf-8"))


def fx(name):
    return json.loads((HERO_DIR / f"{name}.json").read_text(encoding="utf-8"))


def run(replay_dir, version, extraction, prior=None, config=None):
    inp = hero_input("v1" if version == "v1" else "v2", config.templates, prior)
    replay_dir(version, build_window(inp).render(), extraction)
    chain = ChainClient([ChainStep("primary", "groq", "openai/gpt-oss-120b",
                                   ReplayBackend([replay_dir.dir], allow_hand_crafted=True), 6)])
    return score_order(inp, cache=None, llm=chain, meter=None, config=config)


@pytest.fixture
def v1(replay_dir, config):
    return run(replay_dir, "v1", fx("v1"), config=config)


def test_hero_v1(v1):
    a = v1.assessment
    assert [a.features[k] for k in FEATURES] == [0.5, 3, 1, 220.0, 2, 0.30]
    assert a.context["zone_source"] == "keyword" and a.context["imputed"] == []
    assert 75 <= a.model_score <= 92 and a.final_score == round(a.model_score)
    assert a.tier == "high" and abs(a.final_score - 65) >= 10 and a.confidence == "high"
    assert a.action == "confirm" and v1.template_id == "T_ADDRESS" and a.path == "llm"
    assert "9rib el jemaa" in a.reason
    risk = [s for s in v1.extraction.spans if s.kind == "red_flag" and s.code == "vague_location"]
    assert risk and risk[0].quote == "9rib el jemaa"


@pytest.mark.parametrize("variant,resolved", [
    ("v2a", []), ("v2b", ["vague_location", "availability_uncertain", "price_hesitation"])])
def test_hero_v2_clean_and_stale_are_identical(replay_dir, config, v1, variant, resolved):
    r = run(replay_dir, "v2", fx(variant), prior_from(v1), config)
    a = r.assessment
    assert [a.features[k] for k in FEATURES] == [1.0, 0, 0, 220.0, 2, 0.30]
    assert a.context["address_level_final"] == "exact" and a.resolved_flags == resolved
    assert 15 <= a.model_score <= 32 and a.final_score == round(0.6 * a.model_score) and a.final_score <= 25
    assert a.tier == "low" and a.confidence == "high" and a.action == "ship"
    assert v1.assessment.model_score - a.model_score >= 40
    assert "dar 14" in a.reason_diff and "×0.6" in a.reason_diff


def test_hero_matches_pinned_golden(replay_dir, config, v1):
    g = GOLDEN
    assert v1.assessment.model_score == g["v1"]["model_score"] and v1.assessment.final_score == g["v1"]["final"]
    assert v1.assessment.reason == g["v1"]["reason"]
    r = run(replay_dir, "v2", fx("v2a"), prior_from(v1), config)
    assert r.assessment.final_score == g["v2a"]["final"] and r.assessment.reason_diff == g["diff_reason"]
    assert g["classifier_version"] == v1.assessment.classifier_version, "re-run `python -m ml.train` to re-pin"


# ---------------------------------------------------------------- ML13 robustness (tier only)
def test_r1_no_confirmation_is_low_from_model_alone(replay_dir, config, v1):
    r = run(replay_dir, "v2", {**fx("v2a"), "confirmation": "none"}, prior_from(v1), config)
    assert r.assessment.tier == "low"


def test_r3_tone_without_evidence_stays_high(replay_dir, config):
    r = run(replay_dir, "v1", {**fx("v1"), "tone_evidence": None}, config=config)
    assert r.assessment.tier == "high" and r.assessment.context["tone"] == "neutral"


def test_r4_street_and_landmark_is_medium_or_high(replay_dir, config):
    r = run(replay_dir, "v1", {**fx("v1"), "address_level": "street_and_landmark"}, config=config)
    assert r.assessment.tier in ("medium", "high")
