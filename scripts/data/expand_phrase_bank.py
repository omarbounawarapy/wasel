"""Draft paraphrase expansions for data/phrase_banks.yaml via a hosted LLM.

Never edits the authored bank: writes data/phrase_banks_candidates.yaml containing only the
requested cells, with drafted lines placed in eval_only (review-facing pool) AFTER they
survive the generator's own lints (ml.generate.lint_banks). Native-speaker review is still
required before any line moves into the authored bank — this tool only drafts.

Run against a self-hosted endpoint (make llm-serve) to stay quota-free:

    GROQ_BASE_URL=http://<ip>:8001/v1 GROQ_API_KEY=... python scripts/data/expand_phrase_bank.py \
        [--cells time,flags.price_hesitation] [--langs arabizi,fr] [--k 3] [--out PATH]

Requires GROQ_BASE_URL + GROQ_API_KEY (the vLLM token) and EXTRACT_MODEL (default
openai/gpt-oss-20b) — same .env keys as make llm-check.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path

import httpx
import yaml

from wasel.ml.generate import LANGS, _cells, lint_banks, load_inputs  # noqa: E402
from wasel.ml.textnorm import normalize  # noqa: E402
from wasel.paths import ROOT

BANNED = ("risk", "refus", "fake", "arnaque", "مرفوض")
SYSTEM = (
    "You extend a Tunisian cash-on-delivery phrase bank. Customers write informal Darija "
    "(Latin 'arabizi' with digits like 3/7/9, or Arabic script) or French. Given a cell's "
    "existing lines, draft new lines with the SAME meaning, register and length, varying "
    "wording only. Rules: keep every {slot} placeholder exactly; no terminal periods on "
    "French lines; never use these words or derivatives: " + ", ".join(BANNED) + ". "
    "Reply with JSON only: {\"paraphrases\": [\"...\"]}"
)


def cell_iter(banks: dict, want_cells: set[str], want_langs: set[str]):
    for label, lang, cell in _cells(banks):
        if lang not in LANGS or (want_cells and label not in want_cells) or (want_langs and lang not in want_langs):
            continue
        yield label, lang, cell


def ask(base: str, token: str, model: str, user: str, timeout_s: float = 90.0) -> list[str]:
    r = httpx.post(f"{base.rstrip('/')}/chat/completions",
                   headers={"Authorization": f"Bearer {token}"},
                   json={"model": model, "temperature": 0.8, "max_tokens": 400,
                         "messages": [{"role": "system", "content": SYSTEM},
                                      {"role": "user", "content": user}]},
                   timeout=timeout_s)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):                                   # strip a code fence if any
        content = content.split("```")[1].removeprefix("json").strip()
    return [p.strip() for p in json.loads(content)["paraphrases"] if p.strip()]


def draft_cell(banks: dict, zones: dict, prompt_text: str, label: str, lang: str, cell: dict,
               k: int, base: str, token: str, model: str) -> tuple[dict, list[str], int]:
    """Returns (candidate cell, kept drafts, dropped count). Offending drafts are dropped."""
    existing = cell["train"] + cell["eval_only"]
    user = (f"Cell: {label} ({lang}). Existing lines:\n"
            + "\n".join(f"- {p}" for p in existing)
            + f"\n\nDraft {k} new lines.")
    drafted = ask(base, token, model, user)
    kept: list[str] = []
    seen = {normalize(x) for x in existing}
    for phrase in drafted:
        if normalize(phrase) in seen:                       # lint3 only catches cross-label dups
            continue
        seen.add(normalize(phrase))
        trial_cell = copy.deepcopy(cell)
        trial_cell["eval_only"] = cell["eval_only"] + kept + [phrase]
        if lint_banks(_with_cell(banks, label, lang, trial_cell), zones, prompt_text):
            continue                                    # lint failure -> drop this draft
        kept.append(phrase)
    cand = copy.deepcopy(cell)
    cand["eval_only"] = cand["eval_only"] + kept
    return cand, kept, len(drafted) - len(kept)


def _with_cell(banks: dict, label: str, lang: str, cell: dict) -> dict:
    """The full banks dict with exactly one (label, lang) cell replaced — for scoped linting."""
    scoped = copy.deepcopy(banks)
    group, _, leaf = label.partition(".")
    if leaf:
        scoped[group][leaf][lang] = cell
    else:
        scoped[group][lang] = cell
    return scoped


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cells", default="", help="comma-separated cell labels (default: all)")
    ap.add_argument("--langs", default="", help="comma-separated languages (default: all)")
    ap.add_argument("--k", type=int, default=3, help="drafts per cell per language")
    ap.add_argument("--out", default=str(ROOT / "data" / "phrase_banks_candidates.yaml"))
    a = ap.parse_args(argv)

    base, token = os.environ.get("GROQ_BASE_URL"), os.environ.get("GROQ_API_KEY")
    model = os.environ.get("EXTRACT_MODEL", "openai/gpt-oss-20b")
    if not (base and token):
        print("GROQ_BASE_URL / GROQ_API_KEY missing (.env) — nothing to draft against", file=sys.stderr)
        return 1

    banks, _catalog, zones = load_inputs()
    prompt_text = " ".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "config" / "prompts").glob("*")))
    want_cells = {c.strip() for c in a.cells.split(",") if c.strip()}
    want_langs = {x.strip() for x in a.langs.split(",") if x.strip()}

    out: dict = {"_draft": True, "_note": "LLM-drafted paraphrases (scripts/data/expand_phrase_bank.py); "
                                           "PENDING native review — never merge unreviewed."}
    total = 0
    for label, lang, cell in cell_iter(banks, want_cells, want_langs):
        cand, kept, dropped = draft_cell(banks, zones, prompt_text, label, lang, cell, a.k, base, token, model)
        out.setdefault(label, {})[lang] = cand
        total += len(kept)
        print(f"{label}.{lang}: +{len(kept)} drafted" + (f" (dropped {dropped} by lint)" if dropped else ""))

    Path(a.out).write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"wrote {total} drafts -> {a.out} (native review required before merging)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
