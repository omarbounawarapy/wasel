"""The injection holdout must stay held out: distinct attacks, none copied into the lexicon."""
import json

from wasel.paths import ROOT

HOLDOUT = ROOT / "data" / "eval" / "sets" / "g3_injection_holdout.jsonl"


def _attacks() -> list[str]:
    rows = [json.loads(x) for x in HOLDOUT.read_text(encoding="utf-8").splitlines() if x.strip()]
    return [r["input"]["messages"][-1] for r in rows]


def test_at_least_30_distinct_attacks():
    attacks = _attacks()
    assert len(attacks) >= 30
    assert len(set(attacks)) == len(attacks)


def test_no_attack_appears_in_the_lexicon():
    scoring = (ROOT / "config" / "scoring.yaml").read_text(encoding="utf-8").lower()
    assert not [a for a in _attacks() if a.lower() in scoring]
