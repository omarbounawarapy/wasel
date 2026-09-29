"""ML1–ML11, U15, U20, U21, U22, U24, U25: generator, feature contract, model artifact, pure rules."""
from __future__ import annotations

import ast
import copy
import hashlib
import itertools
import json
from pathlib import Path

import pandas as pd
import pytest

from wasel.ml.features import (
    FEATURES,
    LEVEL_TO_SPEC,
    TONE_ENC,
    VerifiedFlag,
    build_features,
    dedupe_by_code,
    resolve_flags,
    score_prior,
    tone_gate,
    zone_from_text,
)
from wasel.ml.generate import COLUMNS, TEXT_COLUMNS, generate, lint_banks, lint_rows, load_inputs, to_csv
from wasel.ml.textnorm import passes_exact_guard, standalone_numbers

ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- the Arabizi-digit helper
@pytest.mark.parametrize("text,nums,guard", [
    ("dar 14", ["14"], True), ("3ayetli 9bal", [], False), ("9rib el jemaa", [], False),
    ("ghodwa ba3d 17h", [], False), ("imm 7 étage 2", ["7", "2"], True), ("2eme etage", [], True),
    ("el 7ouma", [], False), ("٣٤ شارع الحرية", ["٣٤"], True), ("عمارة النور", [], True),
    ("Bardo 2000", [], False), ("dar14", [], False), ("22 123 456", ["22", "123", "456"], True),
    ("km 8.5", ["8", "5"], True), ("rue 7", ["7"], True), ("3and", [], False),
])
def test_standalone_numbers(text, nums, guard):
    assert standalone_numbers(text) == nums
    assert passes_exact_guard([text]) is guard


# ---------------------------------------------------------------- phrase matching
def F(code, i, s=0):
    return VerifiedFlag(code, i, s, s + 3, f"m{i}", "q")


ALL = [F("vague_location", 1), F("availability_uncertain", 2), F("price_hesitation", 2, 5),
       F("third_party_recipient", 2, 9)]


@pytest.mark.parametrize("level,conf,k,expected_resolved", [
    ("exact", "none", None, ["vague_location"]),
    ("area_or_landmark", "confirmed", None, []),                          # k=None: only the vague rule
    ("area_or_landmark", "confirmed", 3, ["availability_uncertain", "price_hesitation"]),
    ("exact", "confirmed", 3, ["vague_location", "availability_uncertain", "price_hesitation"]),
    ("exact", "reschedule", 3, ["vague_location", "availability_uncertain"]),
    ("street_and_landmark", "ambiguous", 3, []),
])
def test_resolve_flags_table(level, conf, k, expected_resolved):
    kept, resolved = resolve_flags(ALL, level, conf, k)
    assert resolved == expected_resolved
    assert set(kept) <= set(ALL)                                          # r(x) ⊆ x
    again, _ = resolve_flags(kept, level, conf, k)
    assert again == kept                                                  # idempotent
    assert "third_party_recipient" in [f.code for f in kept]              # never touched


def test_flag_quoted_after_k_survives():
    kept, _ = resolve_flags([F("availability_uncertain", 4)], "exact", "confirmed", 3)
    assert [f.code for f in kept] == ["availability_uncertain"]


def test_dedupe_keeps_latest_evidence():
    out = dedupe_by_code([F("vague_location", 1, 0), F("vague_location", 3, 2), F("vague_location", 3, 1)])
    assert out == [F("vague_location", 3, 2)]


# ---------------------------------------------------------------- tone gate
def test_tone_gate():
    assert tone_gate("uncertain", None, []) == "neutral"
    assert tone_gate("uncertain", (2, 10, 20), [(2, 0, 9)]) == "uncertain"
    assert tone_gate("uncertain", (2, 10, 20), [(2, 15, 25)]) == "neutral"
    assert tone_gate("negative", (2, 10, 20), [(1, 10, 20)]) == "negative"
    assert tone_gate("neutral", (2, 10, 20), []) == "neutral"


# ---------------------------------------------------------------- zone from text
def test_zone_from_text(config):
    z = config.zones
    assert zone_from_text(["Douar Ouled Ali"], z) == ("rural", "keyword")
    assert zone_from_text(["douar near Sfax"], z) == ("urban", "gazetteer")              # alias beats keyword
    assert zone_from_text(["fi Sfax", "ena fi Thala"], z) == ("rural", "gazetteer")      # latest wins
    assert zone_from_text(["nheb sac"], z) is None


# ---------------------------------------------------------------- features
def test_feature_mapping_and_imputation():
    f, imp = build_features(address_level="street_and_landmark", flag_count=2, tone="negative", price_tnd=None,
                            zone=None, refusals=1, completed=3)
    assert list(f) == list(FEATURES)
    assert f["address_specificity"] == LEVEL_TO_SPEC["street_and_landmark"] == 0.75
    assert f["tone_score"] == TONE_ENC["negative"] == 2
    assert f["price_tnd"] == 69.0 and f["zone_encoded"] == 1 and set(imp) == {"price_tnd", "zone"}
    assert f["customer_refusal_rate"] == pytest.approx((1 + .6) / (3 + 2))
    assert all(v == v for v in f.values())                                   # no NaN


def test_catalog_price_ignores_text_price(config):
    from wasel.scoring.catalog import match_product
    p, _ = match_product("el casque bluetooth", config.catalog)
    assert p["product_id"] == "P12" and p["price_tnd"] == 220
    assert match_product("un truc inconnu", config.catalog)[0] is None


# ---------------------------------------------------------------- generator
def test_generator_deterministic_and_bank_edit_changes_only_text(tmp_path):
    a, _ = generate(400, 20260927)
    b, _ = generate(400, 20260927)
    assert hashlib.sha256(to_csv(a).encode()).hexdigest() == hashlib.sha256(to_csv(b).encode()).hexdigest()
    root = tmp_path / "r"
    for p in ("data", "config/prompts"):
        (root / p).mkdir(parents=True)
    for p in ("data/catalog.yaml", "data/zones.yaml"):
        (root / p).write_text((ROOT / p).read_text(encoding="utf-8"), encoding="utf-8")
    bank = (ROOT / "data/phrase_banks.yaml").read_text(encoding="utf-8").replace('"ghali chwaya"', '"ghalia chwaya"')
    (root / "data/phrase_banks.yaml").write_text(bank, encoding="utf-8")
    c, _ = generate(400, 20260927, root=root)
    for ra, rc in zip(a, c, strict=True):
        for col in COLUMNS:
            if col not in TEXT_COLUMNS:
                assert ra[col] == rc[col], col


def test_eval_only_phrases_appear_only_in_eval_rows():
    rows, inp = generate(2000, 20260927)
    evals = {p for sec in ("flags",) for by in inp["banks"][sec].values() for c in by.values() for p in c["eval_only"]
             if "{" not in p}
    for r in rows:
        if not r["eval_subset"]:
            for p in evals:
                assert p not in r["text"], (r["row_id"], p)


def test_generator_lints_pass_on_committed_banks():
    banks, _, zones = load_inputs()
    assert lint_banks(banks, zones) == []


@pytest.mark.parametrize("mutate,lint", [
    (lambda b: b["address"]["exact"]["fr"].update(train=["{street}, {place}"]), "lint2"),
    (lambda b: b["address"]["street_and_landmark"]["fr"].update(train=["{street} 12, {place}"]), "lint2"),
    (lambda b: b["flags"]["price_hesitation"]["fr"].update(train=["c'est une arnaque"]), "lint4"),
    (lambda b: b["time"]["fr"].update(eval_only=[]), "lint5"),
    (lambda b: b["tone"]["uncertain"]["arabizi"].update(train=["nchouf, ghali chwaya"]), "lint7"),
    (lambda b: b["tone"]["positive"]["fr"].update(train=["Je ne suis pas encore sûr"]), "lint3"),
])
def test_generator_lints_fail_on_bad_banks(mutate, lint):
    banks, _, zones = load_inputs()
    bad = copy.deepcopy(banks)
    mutate(bad)
    assert any(e.startswith(lint) for e in lint_banks(bad, zones))


def test_lint_rows_base_rate():
    rows, _ = generate(3000, 20260927)
    assert lint_rows(rows) == []


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.add(n.module)
    return out


def test_generator_no_llm_imports():
    banned = ("wasel.llm", "groq", "google.genai", "openai", "httpx")
    for f in ("src/wasel/ml/generate.py", "src/wasel/ml/train.py", "src/wasel/ml/features.py", "src/wasel/ml/textnorm.py"):
        mods = _imports(ROOT / f)
        assert not [m for m in mods if any(m == b or m.startswith(b + ".") for b in banned)], f


def test_layering():
    """The core never imports sqlite3, fastapi or the persistence/API/worker modules."""
    banned = ("sqlite3", "fastapi", "wasel.db", "wasel.api", "wasel.ingress", "wasel.worker")
    for d in ("src/wasel/llm", "src/wasel/extraction", "src/wasel/scoring", "src/wasel/outbound", "src/wasel/ml"):
        for f in (ROOT / "src" / "wasel" / d).rglob("*.py"):
            mods = _imports(f)
            assert not [m for m in mods if any(m == b or m.startswith(b + ".") for b in banned)], f


# ---------------------------------------------------------------- model
def _card():
    return json.loads((ROOT / "models/risk_xgb_v1.card.json").read_text())


def test_feature_contract_parity():
    df = pd.read_csv(ROOT / "data/synth_v1.csv", nrows=5)
    assert all(c in df.columns for c in FEATURES)
    assert _card()["FEATURES"] == list(FEATURES)
    meta = json.loads((ROOT / "data/synth_v1.meta.json").read_text())
    assert meta["features"] == list(FEATURES)


def test_model_artifact_matches_card():
    from wasel.scoring.model import classifier_version_of
    card, p = _card(), ROOT / "models/risk_xgb_v1.json"
    assert hashlib.sha256(p.read_bytes()).hexdigest() == card["model_sha256"]
    assert card["monotone"] == [-1, 1, 1, 1, 1, 1]
    assert classifier_version_of(p) == card["classifier_version"]
    import xgboost
    assert xgboost.__version__.split(".")[:2] == card["versions"]["xgboost"].split(".")[:2]


def test_model_gates_and_holdout_tier_ordering():
    m = json.loads((ROOT / "data/reports/train_metrics.json").read_text())
    assert set(m["gates"].values()) == {"pass"}
    r = m["tier_refusal_rate"]
    assert r["low"] < r["medium"] < r["high"]


def test_classifier_monotone(config):
    from wasel.scoring.model import load_model
    lm = load_model(str(ROOT / "models/risk_xgb_v1.json"))
    grid = dict(address_specificity=[0, .25, .5, .75, 1], red_flag_count=[0, 1, 2, 3], tone_score=[-1, 0, 1, 2],
                price_tnd=[25, 69, 149, 220, 450], zone_encoded=[0, 1, 2], customer_refusal_rate=[0.1, .3, .6])
    base = dict(address_specificity=.5, red_flag_count=1, tone_score=0, price_tnd=99.0, zone_encoded=1,
                customer_refusal_rate=.3)
    for feat, vals in grid.items():
        for other in itertools.product([0.25, 1.0], [0, 3]):
            f = dict(base, address_specificity=other[0], red_flag_count=other[1])
            scores = [lm.predict({**f, feat: v}).p for v in vals]
            pairs = list(zip(scores, scores[1:], strict=False))
            if feat == "address_specificity":
                assert all(b <= a + 1e-9 for a, b in pairs), feat
            else:
                assert all(b >= a - 1e-9 for a, b in pairs), feat


@pytest.mark.xfail(strict=True, reason="Known limitation: P15 at 450 TND scores 36.3 on the committed model (simulated "
                   "maximum 30.8, prior 29.0). Resolve by accepting the trade-off and documenting it in the "
                   "card, or by changing the catalog/generator; never tune the model to pass.")
def test_fairness_invariant(config):
    """Rural, exact, 0 flags, neutral, new customer, any catalog price <= 450 -> tier low."""
    from wasel.scoring.model import load_model
    lm = load_model(str(ROOT / "models/risk_xgb_v1.json"))
    for p in config.catalog["products"]:
        f = dict(address_specificity=1.0, red_flag_count=0, tone_score=0, price_tnd=float(p["price_tnd"]),
                 zone_encoded=2, customer_refusal_rate=0.3)
        assert round(lm.predict(f).model_score) < 35, p["product_id"]


def test_fairness_prior_value():
    assert score_prior(dict(address_specificity=1.0, red_flag_count=0, tone_score=0, price_tnd=450.0,
                            zone_encoded=2, customer_refusal_rate=.3)) == pytest.approx(29.0, abs=0.1)
