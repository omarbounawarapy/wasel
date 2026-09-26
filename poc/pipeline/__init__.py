"""COD refusal-risk pipeline.

    extract (LLM or heuristic) -> features -> classifier -> rules -> explanation -> draft -> guards -> judge

The LLM never decides the score or the action: it extracts flags and drafts text.
"""
from . import explain, features, model, rules
from .extract import extract
from .schemas import Flags, Score


def score(order: dict, flags: Flags | None, booster=None, meta=None) -> tuple[Score, dict[str, float]]:
    if booster is None or meta is None:
        booster, meta = model.load()
    feats = features.to_features(order, flags)
    p, contribs = model.predict(feats, booster)
    tier = model.tier_for(p, meta["thresholds"])
    s = Score(score=p, tier=tier, contribs=contribs, action=rules.action_for(tier, float(order["value_tnd"])),
              explanation=explain.explanation(tier, contribs, feats))
    return s, feats


__all__ = ["extract", "score"]
