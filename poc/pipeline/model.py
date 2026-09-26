"""XGBoost classifier: risk score + per-feature contributions from one predict call (pred_contribs)."""
import json
from functools import lru_cache

import numpy as np
import xgboost as xgb

from . import config
from .features import FEATURES

PARAMS = {
    "objective": "binary:logistic", "eval_metric": "auc", "max_depth": 2, "eta": 0.05,
    "subsample": 0.9, "colsample_bytree": 0.9, "min_child_weight": 3, "seed": 7,
}
ROUNDS = 200


def train(X: np.ndarray, y: np.ndarray) -> xgb.Booster:
    return xgb.train(PARAMS, xgb.DMatrix(X, label=y, feature_names=FEATURES), num_boost_round=ROUNDS)


def tier_thresholds(scores: np.ndarray) -> dict:
    """Low 50% / Med 30% / High 20% of the reference score distribution (assumption A5)."""
    return {"med": float(np.percentile(scores, 50)), "high": float(np.percentile(scores, 80))}


def tier_for(score: float, thresholds: dict) -> str:
    if score >= thresholds["high"]:
        return "High"
    if score >= thresholds["med"]:
        return "Med"
    return "Low"


def save(booster: xgb.Booster, meta: dict) -> None:
    booster.save_model(str(config.MODEL_PATH))
    config.MODEL_META_PATH.write_text(json.dumps(meta, indent=2))


@lru_cache(maxsize=1)
def load() -> tuple[xgb.Booster, dict]:
    booster = xgb.Booster()
    booster.load_model(str(config.MODEL_PATH))
    return booster, json.loads(config.MODEL_META_PATH.read_text())


def predict(features: dict[str, float], booster=None) -> tuple[float, dict[str, float]]:
    booster = booster or load()[0]
    dm = xgb.DMatrix(np.array([[features[k] for k in FEATURES]], dtype=float), feature_names=FEATURES)
    score = float(booster.predict(dm)[0])
    contribs = booster.predict(dm, pred_contribs=True)[0]  # last column is the bias term
    return score, {k: float(v) for k, v in zip(FEATURES, contribs[:-1])}
