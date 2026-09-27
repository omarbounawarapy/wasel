"""Draft guard classifier: a cheap, local, no-LLM second opinion on an outgoing draft (the S-11 idea applied
to outbound). Char n-gram TF-IDF (2-5, char_wb: catches Arabizi spelling variants) + one multinomial
binary LogisticRegression (ok vs unsafe) for p_unsafe, plus a multinomial one naming the likely class
{discount, payment, promise, instructions, contact, pushy, extra_question} for the activity feed.

Trained at first use, deterministically, from data/draft_guard.yaml + the static templates (a few thousand
rows, well under a second), so there is no binary artifact to version. It never approves anything on its
own: it can only block (p_unsafe >= block_at) or hold for review. The LLM judge, when available, decides
approval; this stays a veto that can't be prompt-injected.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

from app.outbound.templates import TEMPLATE_LANGS
from ml.textnorm import normalize

ROOT = Path(__file__).resolve().parents[2]
BANK = ROOT / "data" / "draft_guard.yaml"
OK = "ok"


@dataclass(frozen=True)
class GuardResult:
    p_unsafe: float                  # 1 - P(ok)
    label: str                       # argmax class
    top: list[tuple[str, float]]     # 3 most likely unsafe classes, for the activity feed


def _render(templates: dict, tid: str, lang: str, slots: dict[str, str]) -> str:
    t = templates["templates"][tid][lang]
    body = t["text"] if slots.get("first_name") else t["no_name"]
    return body.format(**slots)


def _insert(rng: random.Random, draft: str, phrase: str) -> str:
    where = rng.randrange(3)
    if where == 0:
        return f"{phrase} {draft}"
    if where == 2:
        return f"{draft} {phrase}"
    cut = [i for i, c in enumerate(draft) if c in ".,،"] or [len(draft)]
    i = rng.choice(cut) + 1
    return f"{draft[:i]} {phrase}{draft[i:]}"


def build_corpus(templates: dict, bank: dict, *, split: str = "train", n_base: int = 1100,
                 seed: int = 7, bases: list[str] | None = None) -> tuple[list[str], list[str]]:
    """(texts, labels). split='train' uses the `train` phrases, split='holdout' the `holdout` ones. If `bases` is a
    list, the rendered template each text was built from is appended to it (the golden set needs it)."""
    rng = random.Random(seed if split == "train" else seed + 1)
    s = bank["slots"]
    base: list[tuple[str, str, str]] = []             # (lang, good draft, template it came from)
    for _ in range(n_base):
        tid = rng.choice(list(templates["templates"]))
        lang = rng.choice(TEMPLATE_LANGS)
        slots = {k: rng.choice(v) for k, v in s.items()}
        t = d = _render(templates, tid, lang, slots)
        if rng.random() < 0.4:
            d = f"{d} {rng.choice(bank['safe'][lang])}"
        base.append((lang, d, t))
    X, y = [], []
    if split == "train":
        for _, d, t in base:
            X.append(d)
            y.append(OK)
            if bases is not None:
                bases.append(t)
    for cls, groups in bank["unsafe"].items():
        for lang, phrases in groups[split].items():
            for p in phrases:
                for _ in range(12 if split == "train" else 4):
                    _, d, t = rng.choice([b for b in base if b[0] == lang])
                    X.append(_insert(rng, d, p))
                    y.append(cls)
                    if bases is not None:
                        bases.append(t)
    return X, y


@lru_cache(maxsize=1)
def _model(bank_path: str = str(BANK)) -> tuple[TfidfVectorizer, LogisticRegression, LogisticRegression]:
    from app.scoring.config import default_config
    bank = yaml.safe_load(Path(bank_path).read_text(encoding="utf-8"))
    X, y = build_corpus(default_config().templates, bank)
    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True,
                          preprocessor=normalize)
    M = vec.fit_transform(X)
    bad = [i for i, c in enumerate(y) if c != OK]
    # One BLAS thread: the problem is tiny, and the default pool (one thread per core) burns ~10x the CPU for
    # the same result and pegs every core on a laptop.
    with threadpool_limits(limits=1):
        binary = LogisticRegression(max_iter=3000, C=10.0, class_weight="balanced").fit(M, [int(c != OK) for c in y])
        kind = LogisticRegression(max_iter=3000, C=10.0).fit(M[bad], [y[i] for i in bad])
    return vec, binary, kind


def classify(draft: str) -> GuardResult:
    vec, binary, kind = _model()
    m = vec.transform([draft])
    p = round(float(binary.predict_proba(m)[0][1]), 3)
    top = sorted(((str(c), round(float(q), 3)) for c, q in zip(kind.classes_, kind.predict_proba(m)[0], strict=True)),
                 key=lambda t: -t[1])[:3]
    return GuardResult(p, top[0][0] if p >= 0.5 else OK, top)
