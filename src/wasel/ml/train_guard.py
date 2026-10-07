"""Train the draft guard classifier (scikit-learn, dev only) and write models/draft_guard_v1.json + its card.

The runtime (wasel/outbound/guard_clf.py) scores from the JSON with numpy only. Run through `make train`.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import sklearn
import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from wasel.clock import SystemClock, utc_iso
from wasel.ml.textnorm import normalize
from wasel.outbound import guard_clf as G
from wasel.paths import ROOT

ARTIFACT_NAME = "draft_guard_v1"


def fit(bank: dict, templates: dict) -> tuple[TfidfVectorizer, LogisticRegression, LogisticRegression]:
    """The scikit-learn fit the artifact is exported from (also used by the parity test)."""
    X, y = G.build_corpus(templates, bank)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True,
                          preprocessor=normalize)
    M = vec.fit_transform(X)
    bad = [i for i, c in enumerate(y) if c != G.OK]
    with threadpool_limits(limits=1):
        binary = LogisticRegression(max_iter=3000, C=10.0, class_weight="balanced").fit(
            M, [int(c != G.OK) for c in y])
        kind = LogisticRegression(max_iter=3000, C=10.0).fit(M[bad], [y[i] for i in bad])
    return vec, binary, kind


def export(vec: TfidfVectorizer, binary: LogisticRegression, kind: LogisticRegression, bank_sha: str) -> dict:
    """The weights as plain lists, vocabulary in column order."""
    vocab = [g for g, _ in sorted(vec.vocabulary_.items(), key=lambda kv: kv[1])]
    return {
        "bank_sha256": bank_sha, "vocab": vocab, "idf": [float(v) for v in vec.idf_],
        "binary": {"coef": [float(v) for v in binary.coef_[0]], "intercept": float(binary.intercept_[0])},
        "kind": {"classes": [str(c) for c in kind.classes_], "coef": [[float(v) for v in r] for r in kind.coef_],
                 "intercept": [float(v) for v in kind.intercept_]},
    }


def main(root: Path = ROOT) -> int:
    """Fit, write the artifact and card under `root/models`, then measure the holdout decision with the new file."""
    from wasel.scoring.config import default_config
    bank_path = root / "data" / "draft_guard.yaml"
    bank = yaml.safe_load(bank_path.read_text(encoding="utf-8"))
    cfg = default_config()
    sha = G._bank_sha(bank_path)
    art = export(*fit(bank, cfg.templates), sha)
    out = root / "models" / f"{ARTIFACT_NAME}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(art, separators=(",", ":")) + "\n", encoding="utf-8")
    G._model.cache_clear()
    rep = G.calibrate(grid=False)
    block_at, hold_at = G.thresholds(cfg.raw)
    card = {
        "name": ARTIFACT_NAME, "bank_sha256": sha, "artifact_sha256": G.hashlib.sha256(out.read_bytes()).hexdigest(),
        "versions": {"sklearn": sklearn.__version__, "numpy": np.__version__},
        "n_features": len(art["vocab"]), "classes": art["kind"]["classes"],
        "thresholds": {"block_at": block_at, "hold_at": hold_at},
        "holdout": {k: rep[k] for k in ("n", "unsafe_decisions", "safe_decisions", "unsafe_sent", "unsafe_stopped",
                                        "safe_sent", "safe_held", "safe_blocked")},
        "trained_at": utc_iso(SystemClock().now()),
        "notes": ["Holdout = bank phrases never used in training, see guard_clf.calibrate().",
                  "Retrain with `make train`; a changed bank without a new artifact fails at load."],
    }
    (out.with_suffix(".card.json")).write_text(json.dumps(card, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"guard": {k: card[k] for k in ("n_features", "thresholds")}, **{"holdout": card["holdout"]}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
