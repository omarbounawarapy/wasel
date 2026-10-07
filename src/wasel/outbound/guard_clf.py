"""Draft guard classifier: a cheap, local, no-LLM second opinion on an outgoing draft (the text-baseline idea applied
to outbound). Char n-gram TF-IDF (2-5, char_wb: catches Arabizi spelling variants) + one multinomial
binary LogisticRegression (ok vs unsafe) for p_unsafe, plus a multinomial one naming the likely class
{discount, payment, promise, instructions, contact, pushy, extra_question} for the activity feed.

Trained at `make train` time (wasel/ml/train_guard.py, scikit-learn, deterministic) from data/draft_guard.yaml + the
static templates. The vocabulary, IDF and coefficients are committed in models/draft_guard_v1.json with a card
(bank sha256, versions, holdout numbers, thresholds); this module scores with numpy only and refuses to load if the
bank no longer matches the artifact, so any change in decisions shows up as an artifact diff. decide()
turns p_unsafe into the three-way send / review / block call: >= block_at blocks the draft, >= hold_at
routes it to the owner's approval queue, below hold_at it is cleared to send. "send" is this classifier's recommendation.
Whether it is enough to auto-send is set by auto_send.gate in
config/scoring.yaml (see outbound/route.py). With gate "classifier" (the current setting) a "send"
decision alone clears the draft: the LLM judge still runs when available and its rejection still kills a
rewrite, but its approval is not required. With gate "judge" the LLM judge must approve as well. Either
way the route guards apply (prefilter pass, high confidence, price cap, loop guard, 24 h window; a static
template is never auto-sent). The classifier can't be prompt-injected because it never sees the customer text.
calibrate() measures the decision on bank phrases the classifier never trained on.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import yaml

from wasel.ml.textnorm import normalize
from wasel.outbound.templates import TEMPLATE_LANGS
from wasel.paths import ROOT

BANK = ROOT / "data" / "draft_guard.yaml"
ARTIFACT = ROOT / "models" / "draft_guard_v1.json"
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


class _Model:
    """Numpy TF-IDF (char_wb 2-5, sublinear tf, smooth idf, l2) + two logistic heads, loaded from the artifact."""

    def __init__(self, d: dict):
        self.index = {g: i for i, g in enumerate(d["vocab"])}
        self.idf = np.asarray(d["idf"], dtype=np.float64)
        self.w = np.asarray(d["binary"]["coef"], dtype=np.float64)
        self.b = float(d["binary"]["intercept"])
        self.classes = list(d["kind"]["classes"])
        self.kw = np.asarray(d["kind"]["coef"], dtype=np.float64)
        self.kb = np.asarray(d["kind"]["intercept"], dtype=np.float64)

    def vector(self, text: str) -> np.ndarray:
        """L2-normalised TF-IDF row; same n-grams as scikit-learn's char_wb analyzer."""
        counts: dict[int, int] = {}
        for word in normalize(text).split():
            w = f" {word} "
            n_w = len(w)
            for n in range(2, 6):
                for off in range(max(n_w - n + 1, 1)):
                    i = self.index.get(w[off:off + n])
                    if i is not None:
                        counts[i] = counts.get(i, 0) + 1
                if n_w <= n:                      # a word this short is counted once, not again at larger n
                    break
        x = np.zeros(len(self.idf))
        for i, c in counts.items():
            x[i] = (1.0 + math.log(c)) * self.idf[i]
        norm = float(np.linalg.norm(x))
        return x / norm if norm else x

    def p_unsafe(self, x: np.ndarray) -> float:
        return float(1.0 / (1.0 + math.exp(-(float(x @ self.w) + self.b))))

    def kinds(self, x: np.ndarray) -> np.ndarray:
        z = self.kw @ x + self.kb
        e = np.exp(z - z.max())
        return e / e.sum()


def _bank_sha(path: Path = BANK) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _model(artifact: str = str(ARTIFACT)) -> _Model:
    d = json.loads(Path(artifact).read_text(encoding="utf-8"))
    if d["bank_sha256"] != _bank_sha():
        raise RuntimeError("data/draft_guard.yaml changed since models/draft_guard_v1.json was trained; "
                           "run `make train` and commit the artifact")
    return _Model(d)


def classify(draft: str) -> GuardResult:
    """Score one draft with the local classifier (artifact loaded once per process, numpy only)."""
    m = _model()
    x = m.vector(draft)
    p = round(m.p_unsafe(x), 3)
    top = sorted(((c, round(float(q), 3)) for c, q in zip(m.classes, m.kinds(x), strict=True)),
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
