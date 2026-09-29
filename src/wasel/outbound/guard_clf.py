"""Draft guard classifier: a cheap, local, no-LLM second opinion on an outgoing draft (the text-baseline idea applied
to outbound). Char n-gram TF-IDF (2-5, char_wb: catches Arabizi spelling variants) + one multinomial
binary LogisticRegression (ok vs unsafe) for p_unsafe, plus a multinomial one naming the likely class
{discount, payment, promise, instructions, contact, pushy, extra_question} for the activity feed.

Trained at first use, deterministically, from data/draft_guard.yaml + the static templates (a few thousand
rows, well under a second), so there is no binary artifact to version. decide() turns p_unsafe into the
three-way send / review / block call: >= block_at blocks the draft, >= hold_at routes it to the owner's
approval queue, below hold_at it is cleared to send. "send" is this classifier's recommendation only: an
auto_send still needs the LLM judge's approval and the route guards; the classifier on its
own can only take approval away, and it can't be prompt-injected because it never sees the customer text.
calibrate() measures the decision on bank phrases the classifier never trained on.
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

from wasel.ml.textnorm import normalize
from wasel.outbound.templates import TEMPLATE_LANGS
from wasel.paths import ROOT

BANK = ROOT / "data" / "draft_guard.yaml"
OK = "ok"
SEND, REVIEW, BLOCK = "send", "review", "block"


@dataclass(frozen=True)
class GuardResult:
    """Classifier output for one draft. `p_unsafe` is the probability that it is unsafe; `label` is 'ok' when that is
    below 0.5, otherwise the most likely unsafe class; `top` holds the three most likely unsafe classes.
    """
    p_unsafe: float                  # 1 - P(ok)
    label: str                       # argmax class
    top: list[tuple[str, float]]     # 3 most likely unsafe classes, for the activity feed


@dataclass(frozen=True)
class GuardDecision:
    """The three-way call on a draft: `decision` is 'send', 'review' or 'block'.

    `reason` is plain English, shown with the draft in the owner-approval queue.
    """
    decision: str                    # send | review | block
    p_unsafe: float
    label: str
    top: list[tuple[str, float]]
    reason: str                      # plain English, shown with the draft in the owner-approval queue


def thresholds(cfg: dict | None = None) -> tuple[float, float]:
    """(block_at, hold_at) from config/scoring.yaml outbound.judge; the same numbers everywhere."""
    from wasel.scoring.config import default_config
    jc = (cfg if cfg is not None else default_config().raw).get("outbound", {}).get("judge", {})
    return float(jc.get("classifier_block_at", 0.5)), float(jc.get("classifier_hold_at", 0.1))


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
    from wasel.scoring.config import default_config
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
    """Score one draft with the local classifier. The first call trains the models (cached for the process)."""
    vec, binary, kind = _model()
    m = vec.transform([draft])
    p = round(float(binary.predict_proba(m)[0][1]), 3)
    top = sorted(((str(c), round(float(q), 3)) for c, q in zip(kind.classes_, kind.predict_proba(m)[0], strict=True)),
                 key=lambda t: -t[1])[:3]
    return GuardResult(p, top[0][0] if p >= 0.5 else OK, top)


def decide(draft: str, *, block_at: float | None = None, hold_at: float | None = None) -> GuardDecision:
    """The send-vs-owner-approval call on a generated draft. block_at/hold_at default to config/scoring.yaml;
    pass explicit values (e.g. 1.01/1.01) to score with the decision layers disabled."""
    g = classify(draft)
    if block_at is None or hold_at is None:
        b, h = thresholds()
        block_at = b if block_at is None else block_at
        hold_at = h if hold_at is None else hold_at
    likely = g.top[0]
    if g.p_unsafe >= block_at:
        d = BLOCK
        reason = f"risk {g.p_unsafe:.0%} >= {block_at:.0%} block line, most likely {likely[0]} ({likely[1]:.0%})"
    elif g.p_unsafe >= hold_at:
        d = REVIEW
        reason = f"risk {g.p_unsafe:.0%} in the {hold_at:.0%}-{block_at:.0%} review band, most likely {likely[0]}"
    else:
        d = SEND
        reason = f"risk {g.p_unsafe:.0%} below the {hold_at:.0%} review line"
    return GuardDecision(d, g.p_unsafe, g.label, g.top, reason)


def calibrate(*, block_at: float | None = None, hold_at: float | None = None, n_base: int = 300,
              seed: int = 99, grid: bool = True) -> dict:
    """Measure the three-way decision on text the classifier never trained on: the bank's `holdout` unsafe
    phrases inserted into rendered templates, against safe drafts built from the static templates + `safe`
    phrases. Reports the counts per decision and the rates that gate the design (how much untrained unsafe
    text is cleared to send; how many safe drafts are held or blocked), plus the smallest hold_at on a 5%
    grid that clears at most 15% of the unsafe holdout while holding at most 15% of safe drafts (auto-send
    has to stay viable) and blocking none, with block_at fixed. Deterministic; no training happens here."""
    import yaml

    from wasel.scoring.config import default_config
    cfg = default_config()
    bank = yaml.safe_load(BANK.read_text(encoding="utf-8"))
    if block_at is None or hold_at is None:
        b, h = thresholds(cfg.raw)
        block_at = b if block_at is None else block_at
        hold_at = h if hold_at is None else hold_at
    X_unsafe, _ = build_corpus(cfg.templates, bank, split="holdout")
    X_all, y_all = build_corpus(cfg.templates, bank, n_base=n_base, seed=seed)
    X_safe = [x for x, y in zip(X_all, y_all, strict=True) if y == OK]

    def counts(texts: list[str], at: tuple[float, float]) -> dict[str, int]:
        out = {SEND: 0, REVIEW: 0, BLOCK: 0}
        for t in texts:
            out[decide(t, block_at=at[0], hold_at=at[1]).decision] += 1
        return out

    def report(at: tuple[float, float]) -> dict:
        u, s = counts(X_unsafe, at), counts(X_safe, at)
        return {"thresholds": {"block_at": at[0], "hold_at": at[1]}, "n": {"unsafe_holdout": len(X_unsafe),
                "safe": len(X_safe)}, "unsafe_decisions": u, "safe_decisions": s,
                "unsafe_sent": u[SEND] / len(X_unsafe), "unsafe_stopped": (u[REVIEW] + u[BLOCK]) / len(X_unsafe),
                "safe_sent": s[SEND] / len(X_safe), "safe_held": s[REVIEW] / len(X_safe),
                "safe_blocked": s[BLOCK] / len(X_safe)}

    rep = report((block_at, hold_at))
    if grid:
        # Smallest hold_at that clears at most 15% of untrained unsafe text while holding at most 15% of
        # safe drafts (auto-send has to stay viable) and blocking none. Both sides matter: 0.05 clears
        # only 4% of unsafe text but holds ~60% of safe rewrites, which kills auto-send in practice.
        # (It only moves the send/review line; block_at stays fixed, so the veto never loosens.)
        candidates = []
        for h in [round(0.05 * i, 2) for i in range(1, int(block_at * 20))]:
            r = report((block_at, h))
            if r["unsafe_sent"] <= 0.15 and r["safe_held"] <= 0.15 and r["safe_blocked"] == 0:
                candidates.append(h)
        rep["suggested_hold_at"] = candidates[0] if candidates else None
        rep["grid"] = [report((block_at, round(0.05 * i, 2))) for i in range(1, int(block_at * 20))]
    return rep
