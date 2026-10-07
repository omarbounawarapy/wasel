"""XGBoost load + pred_contribs. One predict call gives the score and the 6 per-feature
contributions (+ bias) in log-odds; points are derived in reason.py."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import xgboost as xgb

from wasel.ml.features import FEATURES


@dataclass(frozen=True)
class ModelOutput:
    """Model prediction for one order. `p` is the refusal probability, `model_score` is 100 x p rounded to one decimal,
    and `phi` are per-feature contributions in log-odds (with `bias` the base term) that reason.points turns into
    score points.
    """
    model_score: float                 # round(100·p, 1)
    p: float
    p0: float                          # sigmoid(bias): the base rate the points are measured from
    phi: dict[str, float]              # log-odds contribution per feature
    bias: float


@dataclass(frozen=True)
class LoadedModel:
    """The XGBoost booster with its version string. Obtained from load_model."""
    booster: xgb.Booster
    classifier_version: str
    path: Path

    def predict(self, features: dict) -> ModelOutput:
        """Score one feature dict (all FEATURES keys, no NaN) and return its ModelOutput.

        A single booster call gives both the probability and the per-feature contributions.
        """
        x = np.array([[float(features[k]) for k in FEATURES]], dtype=float)
        assert not np.isnan(x).any(), "NaN must never reach the booster (ML9)"
        c = self.booster.predict(xgb.DMatrix(x, feature_names=list(FEATURES)), pred_contribs=True)[0]
        margin = float(c.sum())
        p = 1.0 / (1.0 + math.exp(-margin))
        bias = float(c[-1])
        return ModelOutput(round(100.0 * p, 1), p, 1.0 / (1.0 + math.exp(-bias)),
                           {k: float(v) for k, v in zip(FEATURES, c[:-1], strict=True)}, bias)


def classifier_version_of(path: Path) -> str:
    """Version string for a model file: 'xgb_v1-' plus the first 8 hex characters of its SHA-256."""
    return "xgb_v1-" + hashlib.sha256(path.read_bytes()).hexdigest()[:8]


@lru_cache(maxsize=4)
def load_model(path: str) -> LoadedModel | None:
    """Load the booster at `path`, or None if the file doesn't exist. Results are cached per path."""
    p = Path(path)
    if not p.exists():
        return None
    b = xgb.Booster()
    b.load_model(str(p))
    return LoadedModel(b, classifier_version_of(p), p)


def model_problem(path: str) -> tuple[str, str] | None:
    """Check the model file against its card (`<model>.card.json`), the FEATURES list and the booster's feature names.

    Returns None when all agree, else (code, reason) with code 'model_missing' or 'model_mismatch'.
    """
    p = Path(path)
    if not p.exists():
        return "model_missing", f"model file not found: {p.name}"
    card_path = p.with_suffix(".card.json")
    try:
        card = json.loads(card_path.read_text())
    except (OSError, ValueError) as e:
        return "model_mismatch", f"model card unreadable: {card_path.name} ({type(e).__name__})"
    if hashlib.sha256(p.read_bytes()).hexdigest() != card.get("model_sha256"):
        return "model_mismatch", f"{p.name} does not match model_sha256 in {card_path.name}"
    if card.get("FEATURES") != list(FEATURES):
        return "model_mismatch", f"FEATURES in {card_path.name} differ from the code"
    lm = load_model(str(p))
    if lm is None or list(lm.booster.feature_names or []) != list(FEATURES):
        return "model_mismatch", f"feature names in {p.name} differ from FEATURES"
    return None
