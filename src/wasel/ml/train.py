"""python -m wasel.ml.train

Trains the monotone XGBoost on the 8,000 train rows and writes:
  models/risk_xgb_v1.json, models/risk_xgb_v1.card.json, data/reports/train_metrics.json,
  data/reports/impact.json, tests/golden/hero.json
Exits non-zero if a gate fails (AUC, calibration MAE, tier refusal-rate ordering). The model is fitted into a temporary
directory and nothing is written under the root unless every gate passes.
S and p_true are never columns of X (the prior must not leak into the model). Imports no LLM SDK.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost as xgb
from sklearn.metrics import brier_score_loss, roc_auc_score
from xgboost import XGBClassifier

from wasel.clock import SystemClock, utc_iso
from wasel.ml.features import FEATURES, MONOTONE
from wasel.paths import ROOT

PARAMS = dict(objective="binary:logistic", n_estimators=400, learning_rate=0.05, max_depth=2,
              min_child_weight=10, subsample=0.8, colsample_bytree=1.0, reg_lambda=1.0,
              tree_method="hist", monotone_constraints="(" + ",".join(map(str, MONOTONE)) + ")",
              random_state=42, n_jobs=1, eval_metric="logloss")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tier_of(score: np.ndarray, low_max: float = 35, medium_max: float = 65) -> np.ndarray:
    """Tier for each score: 'low' below `low_max`, 'medium' below `medium_max`, else 'high'. Vectorised."""
    return np.where(score < low_max, "low", np.where(score < medium_max, "medium", "high"))


def reliability(p_hat: np.ndarray, y: np.ndarray, bins: int = 10) -> list[dict]:
    """Calibration table: per equal-width probability bin, the count, mean predicted probability and observed refusal
    rate. Empty bins are omitted.
    """
    out = []
    edges = np.linspace(0, 1, bins + 1)
    for i in range(bins):
        m = (p_hat >= edges[i]) & (p_hat < edges[i + 1] if i < bins - 1 else p_hat <= 1)
        if m.any():
            out.append({"bin": f"{edges[i]:.1f}-{edges[i + 1]:.1f}", "n": int(m.sum()),
                        "mean_pred": round(float(p_hat[m].mean()), 4), "refusal_rate": round(float(y[m].mean()), 4)})
    return out


def impact(h: pd.DataFrame, p_hat: np.ndarray, cfg: dict) -> dict:
    """Simulated, on the holdout, with the config/scoring.yaml › roi assumptions."""
    roi = cfg["roi"]
    score = np.round(100 * p_hat)
    tier = tier_of(score, cfg["tiers"]["low_max"], cfg["tiers"]["medium_max"])
    price = h["price_tnd"].to_numpy()
    action = np.where(tier == "low", "ship",
                      np.where((tier == "high") & (price >= cfg["actions"]["prepay_min_tnd"]), "prepay", "confirm"))
    refused = h["refused"].to_numpy()

    def saved(confirm_rate):
        pr = {**roi["prevent_rate"], "confirm": confirm_rate}
        avoided = float(sum(r * pr[a] for r, a in zip(refused, action, strict=True)))
        lost = float(sum((1 - r) * (a == "prepay") * roi["prepay_conversion_loss"] * roi["gross_margin"] * p
                         for r, a, p in zip(refused, action, price, strict=True)))
        msg = float(sum(a in ("confirm", "prepay") for a in action)) * roi["msg_cost_tnd"]
        return avoided, avoided * roi["c_fail_tnd"] - lost - msg

    avoided, s = saved(roi["prevent_rate"]["confirm"])
    n = len(h)
    return {
        "report": "impact", "simulated": True, "dataset": "data/synth_v1.csv holdout", "n_orders": n,
        "baseline_refusal_rate": round(float(refused.mean()), 4),
        "projected_refusal_rate": round(float((refused.sum() - avoided) / n), 4),
        "trips_avoided": round(avoided, 1), "tnd_saved": round(s, 1),
        "tnd_saved_per_1000_orders": round(1000 * s / n, 1),
        "recall_of_refusals_flagged": round(float(((tier != "low") & (refused == 1)).sum() / max(1, refused.sum())), 4),
        "share_of_orders_flagged": round(float((tier != "low").mean()), 4),
        "tnd_saved_per_1000_by_confirm_rate": {str(c): round(1000 * saved(c)[1] / n, 1)
                                               for c in roi["sensitivity_confirm"]},
        "assumptions": [f"{k}: {v}" for k, v in roi.items()],
    }


def write_hero_golden(out: Path) -> dict:
    """Runs the frozen hero fixtures through the real score_order offline (cache hits, no LLM)."""
    from wasel.ml.hero import cache_for, hero_input, prior_from
    from wasel.scoring.config import load_config
    from wasel.scoring.model import load_model
    from wasel.scoring.score_order import score_order
    load_model.cache_clear()
    cfg = load_config()
    i1 = hero_input("v1", cfg.templates)
    r1 = score_order(i1, cache=cache_for("v1", i1), llm=None, meter=None, config=cfg)
    prior = prior_from(r1)
    res = {}
    for v in ("v2a", "v2b"):
        iv = hero_input("v2", cfg.templates, prior)
        res[v] = score_order(iv, cache=cache_for(v, iv), llm=None, meter=None, config=cfg)

    def view(r):
        a = r.assessment
        return {"features": [a.features[k] for k in FEATURES], "model_score": a.model_score,
                "final": a.final_score, "tier": a.tier, "action": a.action, "confidence": a.confidence,
                "confidence_reasons": a.confidence_reasons, "template_id": r.template_id,
                "resolved_flags": a.resolved_flags, "zone_source": a.context["zone_source"],
                "imputed": a.context["imputed"], "address_level_final": a.context["address_level_final"],
                "reason": a.reason, "reason_short": a.reason_short}
    golden = {"classifier_version": r1.assessment.classifier_version, "config_hash": r1.assessment.config_hash,
              "v1": view(r1), "v2a": view(res["v2a"]), "v2b": view(res["v2b"]),
              "diff_reason": res["v2a"].assessment.reason_diff}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(golden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return golden


def main(root: Path = ROOT, min_auc: float = 0.70) -> int:
    """Train the classifier on the train split, then write the model, its card, metrics, impact report and the hero
    golden under `root`, but only if every gate passes.

    Returns 1 if a gate (AUC >= `min_auc`, calibration error, tier refusal rates increasing) fails, else 0. On failure
    the metrics are printed and no file under `root` is touched. The hero golden is only written for the real root,
    because it scores through the committed model path.
    """
    import yaml
    cfg = yaml.safe_load((root / "config/scoring.yaml").read_text(encoding="utf-8"))
    csv_path = root / "data" / "synth_v1.csv"
    df = pd.read_csv(csv_path)
    tr, h = df[df.split == "train"], df[df.split == "holdout"]
    X, y = tr.loc[:, list(FEATURES)], tr["refused"]
    assert "S" not in X.columns and "p_true" not in X.columns
    clf = XGBClassifier(**PARAMS)
    clf.fit(X, y)
    booster = clf.get_booster()
    model_path = root / cfg["model"]["file"]
    tmp = tempfile.TemporaryDirectory()
    tmp_model = Path(tmp.name) / model_path.name
    booster.save_model(str(tmp_model))

    p_hat = booster.predict(xgb.DMatrix(h.loc[:, list(FEATURES)], feature_names=list(FEATURES)))
    yh, pt = h["refused"].to_numpy(), h["p_true"].to_numpy()
    tiers = tier_of(np.round(100 * p_hat), cfg["tiers"]["low_max"], cfg["tiers"]["medium_max"])
    rate = {t: (float(yh[tiers == t].mean()) if (tiers == t).any() else None) for t in ("low", "medium", "high")}
    err = np.abs(100 * p_hat - 100 * pt)
    auc, oracle = float(roc_auc_score(yh, p_hat)), float(roc_auc_score(yh, pt))
    gates = {
        "auc": auc >= min_auc and auc >= oracle - 0.03,
        "calibration_mae": float(err.mean()) <= 5.0,
        "tier_refusal_rate_increasing": all(v is not None for v in rate.values())
        and rate["low"] < rate["medium"] < rate["high"],
    }
    version = "xgb_v1-" + _sha(tmp_model)[:8]
    now = utc_iso(SystemClock().now())
    metrics = {
        "report": "train_metrics", "created_at": now, "classifier_version": version,
        "n_train": int(len(tr)), "n_holdout": int(len(h)),
        "base_rate_train": round(float(y.mean()), 4), "base_rate_holdout": round(float(yh.mean()), 4),
        "auc": round(auc, 4), "oracle_auc": round(oracle, 4),
        "brier": round(float(brier_score_loss(yh, p_hat)), 4),
        "oracle_brier": round(float(brier_score_loss(yh, pt)), 4),
        "calib_mae_pts": round(float(err.mean()), 2), "calib_max_pts": round(float(err.max()), 2),
        "tier_share": {t: round(float((tiers == t).mean()), 4) for t in ("low", "medium", "high")},
        "tier_refusal_rate": {t: (round(v, 4) if v is not None else None) for t, v in rate.items()},
        "gates": {k: ("pass" if v else "fail") for k, v in gates.items()},
        "note": "Synthetic data; labels are simulated outcomes drawn from a documented prior.",
    }
    print_summary = {k: metrics[k] for k in ("auc", "oracle_auc", "calib_mae_pts", "tier_share",
                                              "tier_refusal_rate", "gates")}
    print(json.dumps(print_summary, indent=2))
    if not all(gates.values()):
        tmp.cleanup()
        print("TRAIN GATES FAILED, no file was written", file=sys.stderr)
        return 1
    meta = json.loads((root / "data" / "synth_v1.meta.json").read_text())
    card = {
        "classifier_version": version, "params": PARAMS, "FEATURES": list(FEATURES), "monotone": list(MONOTONE),
        "model_sha256": _sha(tmp_model), "data_sha256": _sha(csv_path), "synth_meta": meta,
        "versions": {"xgboost": xgb.__version__, "numpy": np.__version__, "sklearn": sklearn.__version__},
        "git_sha": meta.get("git_sha"), "trained_at": now, "metrics_ref": "data/reports/train_metrics.json",
        "reliability": reliability(p_hat, yh),
        "notes": ["No time split: rows have no temporal order.",
                  "The model class matches the prior (additive in log-odds), so depth 2 and no tuning.",
                  "model_score = 100 · P(refused) on simulated outcomes, not a real-world refusal rate."],
    }
    model_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp_model, model_path)
    tmp.cleanup()
    reports = root / "data" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "train_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    (model_path.with_suffix(".card.json")).write_text(json.dumps(card, indent=2) + "\n")
    (reports / "impact.json").write_text(json.dumps({**impact(h, p_hat, cfg), "created_at": now,
                                                     "classifier_version": version}, indent=2) + "\n")
    if root == ROOT:
        golden = write_hero_golden(root / "tests" / "golden" / "hero.json")
        print("hero:", {v: (golden[v]["model_score"], golden[v]["final"], golden[v]["tier"])
                        for v in ("v1", "v2a", "v2b")})
        from wasel.ml.train_guard import main as train_guard
        return train_guard(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
