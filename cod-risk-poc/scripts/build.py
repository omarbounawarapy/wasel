"""Extract flags for every seed order, train the classifier, score everything, write seed.db + model files.

    python scripts/build.py            # offline: heuristic extractor, no API key, ~5 s
    python scripts/build.py --llm      # LLM extractor (needs LLM_PROVIDER + key); sleeps to respect --rpm

Run it once in the background, never in front of the camera. The app copies seed.db -> app.db on start,
so the seeded queue renders with zero LLM calls even after the free-tier quota is gone.
"""
import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline import config, db, explain, features, model, rules  # noqa: E402
from pipeline.extract import extract  # noqa: E402
from pipeline.llm import get_client  # noqa: E402
from pipeline.schemas import Score  # noqa: E402

SEED_DB = config.ROOT / "seed.db"


def auc(y: np.ndarray, p: np.ndarray) -> float:
    """Mann-Whitney AUC; no sklearn dependency."""
    order = np.argsort(p)
    ranks = np.empty(len(p))
    ranks[order] = np.arange(1, len(p) + 1)
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def stratified_split(y: np.ndarray, frac: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    holdout = np.zeros(len(y), dtype=bool)
    for cls in (0, 1):
        idx = np.flatnonzero(y == cls)
        holdout[rng.choice(idx, size=round(len(idx) * frac), replace=False)] = True
    return holdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--llm", action="store_true", help="use the configured LLM for extraction")
    ap.add_argument("--rpm", type=int, default=25, help="max LLM requests per minute (free-tier cap)")
    a = ap.parse_args()

    client = get_client() if a.llm else None
    if a.llm and client is None:
        sys.exit("--llm needs LLM_PROVIDER=gemini|groq and GEMINI_API_KEY / GROQ_API_KEY")

    orders = pd.read_csv(config.DATA_CSV, keep_default_na=False).to_dict("records")
    tmp = SEED_DB.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    conn = db.connect(tmp)

    extractions, failed = [], 0
    for i, o in enumerate(orders):
        ext = extract(o["address_text"], o["note_text"], client, conn)
        extractions.append(ext)
        failed += ext.failed
        if client is not None and not ext.cache_hit:
            time.sleep(60 / a.rpm)
            print(f"\r{i + 1}/{len(orders)} extracted ({failed} failed)", end="", flush=True)
    print(f"extraction: {len(orders)} orders, source={extractions[0].source}, failed={failed}")

    feats = [features.to_features(o, e.flags) for o, e in zip(orders, extractions)]
    X = np.array([[f[k] for k in features.FEATURES] for f in feats], dtype=float)
    y = np.array([int(o["refused"]) for o in orders])
    holdout = stratified_split(y, 0.2, seed=7)

    import xgboost as xgb
    # 5-fold CV AUC on all rows: a less split-dependent number than the single 60-row holdout.
    rng, cv = np.random.default_rng(0), []
    for fold in np.array_split(rng.permutation(len(y)), 5):
        tr = np.setdiff1d(np.arange(len(y)), fold)
        b = model.train(X[tr], y[tr])
        cv.append(auc(y[fold], b.predict(xgb.DMatrix(X[fold], feature_names=features.FEATURES))))

    booster = model.train(X[~holdout], y[~holdout])
    p_hold = booster.predict(xgb.DMatrix(X[holdout], feature_names=features.FEATURES))
    thresholds = model.tier_thresholds(p_hold)
    tiers_hold = np.array([model.tier_for(p, thresholds) for p in p_hold])
    per_tier = {t: {"n": int((tiers_hold == t).sum()),
                    "refusal_rate": float(y[holdout][tiers_hold == t].mean()) if (tiers_hold == t).any() else None}
                for t in ("Low", "Med", "High")}

    version = f"xgb-{dt.datetime.now(dt.timezone.utc):%Y%m%d%H%M}-{extractions[0].source}"
    meta = {
        "model_version": version, "thresholds": thresholds, "features": features.FEATURES,
        "extraction_source": extractions[0].source, "n_train": int((~holdout).sum()),
        "n_holdout": int(holdout.sum()), "holdout_auc": auc(y[holdout], p_hold),
        "cv5_auc_mean": float(np.mean(cv)), "cv5_auc_std": float(np.std(cv)),
        "holdout_per_tier": per_tier, "base_refusal_rate": float(y.mean()),
        "holdout_order_ids": [o["order_id"] for o, h in zip(orders, holdout) if h],
        "note": "Synthetic data. Metrics show the pipeline recovers the generator's relationships, "
                "not predictive power on real orders.",
    }
    model.save(booster, meta)
    model.load.cache_clear()

    with db.tx(conn):
        for o, e, f in zip(orders, extractions, feats):
            p, contribs = model.predict(f, booster)
            tier = model.tier_for(p, thresholds)
            s = Score(score=p, tier=tier, contribs=contribs, action=rules.action_for(tier, float(o["value_tnd"])),
                      explanation=explain.explanation(tier, contribs, f))
            db.upsert_order(conn, o, refused=o["refused"])
            db.save_extraction(conn, o["order_id"], e)
            db.save_score(conn, o["order_id"], version, s)
    conn.close()
    tmp.replace(SEED_DB)

    print(json.dumps({k: meta[k] for k in ("model_version", "n_train", "n_holdout", "holdout_auc", "cv5_auc_mean", "cv5_auc_std",
                                           "holdout_per_tier", "base_refusal_rate")}, indent=2))


if __name__ == "__main__":
    main()
