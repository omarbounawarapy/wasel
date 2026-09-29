"""Synthetic order generator.

    python -m wasel.ml.generate --seed 20260927 --n 10000

One row = one synthetic order at first scoring (v1, pre-reply, no [SELLER] line). All distributions
are synthetic assumptions, not market facts. The renderer never sees S, p_true or refused:
the label never touches text, and text never touches the label.

A rerun with the same seed and banks is byte-identical. A bank edit changes only the text columns
(text, messages_json, gt_evidence_json). This module imports no LLM SDK (ML10).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import yaml

from wasel.ml.features import FEATURES, FLAG_ORDER, LEVEL_TO_SPEC, LEVELS, TONE_ENC, ZONE_ENC, S, p_true, smoothed_rate
from wasel.ml.textnorm import find_span, normalize, passes_exact_guard
from wasel.paths import ROOT

DEFAULT_SEED = 20260927
LANGS = ("arabizi", "darija_arabic_script", "fr")          # authored languages
ROW_LANGS = ("arabizi", "darija_arabic_script", "fr", "mixed")

ZONE_P = {"urban": .55, "suburban": .30, "rural": .15}
LEVEL_P = {"urban": [.02, .05, .18, .35, .40], "suburban": [.03, .08, .27, .32, .30],
           "rural": [.05, .12, .40, .28, .15]}
QTY_P = {1: .85, 2: .12, 3: .03}
HIST_P = {0: .45, 1: .15, 2: .12, 3: .07, 4: .06, 5: .05, 6: .04, 8: .03, 10: .03}
TONE_P = {"positive": .25, "neutral": .50, "uncertain": .18, "negative": .07}
LANG_P = {"arabizi": .35, "darija_arabic_script": .25, "fr": .20, "mixed": .20}
VAGUE_P = {"none": .5, "city_only": .6, "area_or_landmark": .7, "street_and_landmark": .1, "exact": 0.0}
TONE_FLAG_P = {  # (availability_uncertain, price_hesitation, pressure_or_inconsistency)
    "positive": (.03, .04, .02), "neutral": (.08, .06, .03),
    "uncertain": (.45, .25, .08), "negative": (.25, .35, .25)}
LABEL_WORDS = ("risk", "refus", "fake", "arnaque", "مرفوض")
SLOT_RE = re.compile(r"\{(\w+)\}")

COLUMNS = ["row_id", "zone", "zone_encoded", "governorate", "place_name", "address_level",
           "address_specificity", "has_geo_pin", "product_id", "product_category", "quantity",
           "price_tnd", "customer_completed_orders", "customer_refusal_count", "customer_refusal_rate",
           "tone", "tone_score", "flags_gt", "red_flag_count", "language", "S", "p_true", "refused",
           "split", "eval_subset", "text_pool", "messages_json", "text", "gt_evidence_json"]
TEXT_COLUMNS = ("messages_json", "text", "gt_evidence_json")


def load_inputs(root: Path = ROOT) -> tuple[dict, dict, dict]:
    def y(p):
        return yaml.safe_load((root / p).read_text(encoding="utf-8"))
    return y("data/phrase_banks.yaml"), y("data/catalog.yaml"), y("data/zones.yaml")


def _choice(rng, options: dict):
    keys = list(options)
    return keys[int(rng.choice(len(keys), p=np.array(list(options.values())) / sum(options.values())))]


# ---------------------------------------------------------------- latents + label (stream "rows")
def sample_latents(rng, catalog: dict, zones: dict, n: int) -> list[dict]:
    products = catalog["products"]
    prod_p = {p["product_id"]: p["weight"] for p in products}
    by_id = {p["product_id"]: p for p in products}
    places = {z: [e for e in zones["entries"] if e["zone"] == z] for z in ZONE_P}
    rows = []
    for i in range(n):
        zone = _choice(rng, ZONE_P)
        entry = places[zone][int(rng.integers(len(places[zone])))]
        level = LEVELS[int(rng.choice(5, p=LEVEL_P[zone]))]
        has_pin = bool(level == "exact" and rng.random() < .15)
        pid = _choice(rng, prod_p)
        qty = _choice(rng, QTY_P)
        n_hist = _choice(rng, HIST_P)
        q = rng.beta(2, 6)
        r = int(rng.binomial(n_hist, q)) if n_hist > 0 else 0
        tone = _choice(rng, TONE_P)
        flags = []
        if rng.random() < VAGUE_P[level]:
            flags.append("vague_location")
        pa, pp, pc = TONE_FLAG_P[tone]
        if rng.random() < pa:
            flags.append("availability_uncertain")
        if rng.random() < pp:
            flags.append("price_hesitation")
        if rng.random() < .06:
            flags.append("third_party_recipient")
        if rng.random() < (.17 if r > 0 else .02):
            flags.append("prior_refusal_mention")
        if rng.random() < pc:
            flags.append("pressure_or_inconsistency")
        flags = [c for c in FLAG_ORDER if c in flags]
        lang = _choice(rng, LANG_P)
        price = float(by_id[pid]["price_tnd"] * qty)
        feats = {"address_specificity": LEVEL_TO_SPEC[level], "red_flag_count": len(flags),
                 "tone_score": TONE_ENC[tone], "price_tnd": price, "zone_encoded": ZONE_ENC[zone],
                 "customer_refusal_rate": smoothed_rate(r, n_hist)}
        s = S(feats)
        pt = p_true(s)
        refused = int(rng.random() < pt)                  # the Bernoulli draw IS the noise; no ±10
        rows.append({
            "row_id": i, "zone": zone, "zone_encoded": ZONE_ENC[zone], "governorate": entry["governorate"],
            "place_name": entry["name"], "_place_ar": entry.get("name_ar", entry["name"]),
            "address_level": level, "address_specificity": LEVEL_TO_SPEC[level], "has_geo_pin": has_pin,
            "product_id": pid, "product_category": by_id[pid]["category"], "quantity": qty, "price_tnd": price,
            "customer_completed_orders": n_hist, "customer_refusal_count": r,
            "customer_refusal_rate": feats["customer_refusal_rate"], "tone": tone, "tone_score": TONE_ENC[tone],
            "flags_gt": flags, "red_flag_count": len(flags), "language": lang, "S": s, "p_true": pt,
            "refused": refused, "_aliases": by_id[pid]["aliases"],
        })
    return rows


def assign_split(rng, rows: list[dict], holdout_frac: float = 0.2) -> None:
    """One stratified permutation on (refused × zone)."""
    strata: dict[tuple, list[int]] = {}
    for r in rows:
        strata.setdefault((r["refused"], r["zone"]), []).append(r["row_id"])
    holdout = set()
    for key in sorted(strata):
        ids = strata[key]
        perm = rng.permutation(len(ids))
        k = round(len(ids) * holdout_frac)
        holdout.update(ids[j] for j in perm[:k])
    for r in rows:
        r["split"] = "holdout" if r["row_id"] in holdout else "train"


def assign_eval_subset(rng, rows: list[dict], per_cell: int = 2) -> None:
    """40 holdout rows: 2 per (address_level × language) cell."""
    for r in rows:
        r["eval_subset"] = False
    for level in LEVELS:
        for lang in ROW_LANGS:
            cell = [r["row_id"] for r in rows
                    if r["split"] == "holdout" and r["address_level"] == level and r["language"] == lang]
            for j in rng.permutation(len(cell))[:per_cell]:
                rows[cell[j]]["eval_subset"] = True
    for r in rows:
        r["text_pool"] = "eval_only" if r["eval_subset"] else "train"


# ---------------------------------------------------------------- text (stream "text", per row)
def _fill(rng, phrase: str, lang: str, row: dict, banks: dict) -> str:
    def repl(m):
        slot = m.group(1)
        if slot == "place":
            return row["_place_ar"] if lang == "darija_arabic_script" else row["place_name"]
        if slot == "number":
            return str(int(rng.integers(1, 121)))
        if slot == "product":
            aliases = row["_aliases"][lang]
            return aliases[int(rng.integers(len(aliases)))]
        vals = banks["slots"][slot][lang]
        return vals[int(rng.integers(len(vals)))]
    return SLOT_RE.sub(repl, phrase)


def _pick(rng, cell: dict, pool: str) -> str:
    opts = cell[pool]
    return opts[int(rng.integers(len(opts)))]


def render_text(row: dict, banks: dict, text_seed: int) -> dict:
    rng = np.random.default_rng([text_seed, row["row_id"]])
    pool = row["text_pool"]

    def seg_lang():
        return LANGS[int(rng.integers(3))] if row["language"] == "mixed" else row["language"]

    segments: list[tuple[str, str]] = []           # (kind, text)
    gt = {"address": None, "flags": {}, "tone": None}
    lang = seg_lang()
    segments.append(("product", _fill(rng, _pick(rng, banks["order_intro"][lang], pool), lang, row, banks)))
    lang = seg_lang()
    if row["address_level"] != "none" or rng.random() < .5:
        addr = _fill(rng, _pick(rng, banks["address"][row["address_level"]][lang], pool), lang, row, banks)
        segments.append(("address", addr))
        gt["address"] = addr
    for code in row["flags_gt"]:
        lang = seg_lang()
        ph = _fill(rng, _pick(rng, banks["flags"][code][lang], pool), lang, row, banks)
        segments.append(("flag", ph))
        gt["flags"][code] = ph
    if row["tone"] != "neutral":
        lang = seg_lang()
        ph = _fill(rng, _pick(rng, banks["tone"][row["tone"]][lang], pool), lang, row, banks)
        segments.append(("tone", ph))
        gt["tone"] = ph
    if rng.random() < .4:
        lang = seg_lang()
        segments.append(("time", _fill(rng, _pick(rng, banks["time"][lang], pool), lang, row, banks)))

    # Assembly: address first with p=.70 (after the product intro), otherwise shuffled.
    addr_first = rng.random() < .70
    rest = [s for s in segments if s[0] != "product"]
    if addr_first and any(s[0] == "address" for s in rest):
        a = [s for s in rest if s[0] == "address"]
        others = [s for s in rest if s[0] != "address"]
        order = [others[j] for j in rng.permutation(len(others))]
        ordered = [segments[0], *a, *order]
    else:
        order = [rest[j] for j in rng.permutation(len(rest))]
        ordered = [segments[0], *order]
    u = rng.random()
    n_msgs = 3 if u < .1 else 2 if u < .3 else 1
    n_msgs = min(n_msgs, len(ordered))
    cuts = sorted(rng.choice(np.arange(1, len(ordered)), size=n_msgs - 1, replace=False).tolist()) \
        if n_msgs > 1 else []
    bounds = [0, *cuts, len(ordered)]
    msgs = [{"role": "customer", "kind": "text",
             "text": ". ".join(t for _, t in ordered[bounds[j]:bounds[j + 1]])}
            for j in range(len(bounds) - 1)]
    if row["has_geo_pin"]:
        msgs.append({"role": "customer", "kind": "location", "text": None})
    text = "\n".join(m["text"] for m in msgs if m["text"])
    return {"messages_json": msgs, "text": text, "gt_evidence_json": gt}


# ---------------------------------------------------------------- lints
def _cells(banks: dict):
    """Yield (label, lang, cell) for every authored cell."""
    for lang, cell in banks["order_intro"].items():
        yield ("order_intro", lang, cell)
    for level, by_lang in banks["address"].items():
        for lang, cell in by_lang.items():
            yield (f"address.{level}", lang, cell)
    for code, by_lang in banks["flags"].items():
        for lang, cell in by_lang.items():
            yield (f"flags.{code}", lang, cell)
    for tone, by_lang in banks["tone"].items():
        for lang, cell in by_lang.items():
            yield (f"tone.{tone}", lang, cell)
    for lang, cell in banks["time"].items():
        yield ("time", lang, cell)


def _slot_variants(phrase: str, lang: str, banks: dict, places: list[str]) -> list[str]:
    out = []
    for num in ("1", "57", "120"):
        for lm in banks["slots"]["landmark"][lang]:
            for st in banks["slots"]["street"][lang]:
                for pl in places[:4]:
                    out.append(phrase.replace("{number}", num).replace("{landmark}", lm)
                               .replace("{street}", st).replace("{place}", pl).replace("{product}", "x"))
    return out


def lint_banks(banks: dict, zones: dict, prompt_text: str = "") -> list[str]:
    errors = []
    places = [e["name"] for e in zones["entries"]]
    places_ar = [e.get("name_ar", e["name"]) for e in zones["entries"]]
    seen: dict[str, str] = {}
    for label, lang, cell in _cells(banks):
        tr, ev = cell.get("train", []), cell.get("eval_only", [])
        total = len(tr) + len(ev)
        if len(tr) < 1 or len(ev) < max(1, math.ceil(0.30 * total)):                           # lint 5
            errors.append(f"lint5 split rule: {label}.{lang} has {len(tr)} train / {len(ev)} eval_only")
        for ph in tr + ev:
            for w in LABEL_WORDS:                                                               # lint 4
                if w in normalize(ph):
                    errors.append(f"lint4 label word '{w}' in {label}.{lang}: {ph!r}")
            key = normalize(ph)
            if key in seen and seen[key] != label:                                              # lint 3
                errors.append(f"lint3 phrase under two labels ({seen[key]}, {label}): {ph!r}")
            seen.setdefault(key, label)
            pl = places_ar if lang == "darija_arabic_script" else places
            if label == "address.exact":                                                        # lint 2
                bad = [v for v in _slot_variants(ph, lang, banks, pl) if not passes_exact_guard([v])]
                if bad:
                    errors.append(f"lint2 exact phrase fails the exact guard: {bad[0]!r}")
            if label == "address.street_and_landmark":
                bad = [v for v in _slot_variants(ph, lang, banks, pl) if passes_exact_guard([v])]
                if bad:
                    errors.append(f"lint2 street_and_landmark phrase passes the exact guard: {bad[0]!r}")
            if prompt_text and ph in ev:                                                        # lint 6
                frag = [f for f in (normalize(x) for x in SLOT_RE.sub("\x00", ph).split("\x00")) if len(f) >= 6]
                if any(f in prompt_text for f in frag):
                    errors.append(f"lint6 eval_only phrase leaks into prompts: {ph!r}")
    for lang in LANGS:                                                                          # lint 7
        unc = [normalize(p) for c in ("train", "eval_only") for p in banks["tone"]["uncertain"][lang][c]]
        flg = [normalize(SLOT_RE.sub("", p)) for code in ("availability_uncertain", "price_hesitation")
               for c in ("train", "eval_only") for p in banks["flags"][code][lang][c]]
        for u in unc:
            for f in flg:
                if f and (f in u or u in f):
                    errors.append(f"lint7 tone/flag overlap ({lang}): {u!r} ~ {f!r}")
    return errors


def lint_rows(rows: list[dict]) -> list[str]:
    errors = []
    for r in rows:                                                                              # lint 1
        gt = r["gt_evidence_json"]
        phrases = ([gt["address"]] if gt["address"] else []) + list(gt["flags"].values()) + \
                  ([gt["tone"]] if gt["tone"] else [])
        for ph in phrases:
            if find_span(r["text"], ph) is None:
                errors.append(f"lint1 row {r['row_id']}: {ph!r} not found in its text")
                break
    base = sum(r["refused"] for r in rows) / len(rows)                                          # lint 8
    if not 0.25 <= base <= 0.35:
        errors.append(f"lint8 base rate {base:.3f} outside [0.25, 0.35]")
    return errors


# ---------------------------------------------------------------- driver
def generate(n: int = 10000, seed: int = DEFAULT_SEED, root: Path = ROOT) -> tuple[list[dict], dict]:
    banks, catalog, zones = load_inputs(root)
    ss = np.random.SeedSequence(seed)
    s_rows, s_split, s_eval, s_text = ss.spawn(4)
    rows = sample_latents(np.random.default_rng(s_rows), catalog, zones, n)
    assign_split(np.random.default_rng(s_split), rows)
    assign_eval_subset(np.random.default_rng(s_eval), rows)
    text_seed = int(s_text.generate_state(1)[0])
    for r in rows:
        r.update(render_text(r, banks, text_seed))
    return rows, {"banks": banks, "catalog": catalog, "zones": zones}


def _fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return repr(round(v, 10))
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=False)
    return str(v)


def to_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(COLUMNS)
    for r in rows:
        w.writerow([_fmt(r[c]) for c in COLUMNS])
    return buf.getvalue()


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git_sha(root: Path = ROOT) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    except Exception:
        return "unknown"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED)
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--out", default=str(ROOT / "data" / "synth_v1.csv"))
    a = ap.parse_args(argv)
    rows, inputs = generate(a.n, a.seed)
    prompt_text = " ".join(normalize(p.read_text(encoding="utf-8"))
                           for p in sorted((ROOT / "config" / "prompts").glob("*")) if p.is_file())
    errors = lint_banks(inputs["banks"], inputs["zones"], prompt_text) + lint_rows(rows)
    if errors:
        print("\n".join(errors[:50]), file=sys.stderr)
        print(f"generator lints FAILED ({len(errors)})", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.write_text(to_csv(rows), encoding="utf-8")
    meta = {
        "seed": a.seed, "n": a.n, "features": list(FEATURES),
        "base_rate": sum(r["refused"] for r in rows) / len(rows),
        "split_counts": {s: sum(r["split"] == s for r in rows) for s in ("train", "holdout")},
        "eval_subset": sum(r["eval_subset"] for r in rows),
        "sha256": {p: sha256_file(ROOT / p) for p in ("data/phrase_banks.yaml", "data/catalog.yaml",
                                                      "data/zones.yaml", "src/wasel/ml/features.py")},
        "csv_sha256": sha256_file(out), "git_sha": git_sha(),
    }
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {a.n} rows -> {out} (base rate {meta['base_rate']:.3f}, "
          f"{meta['split_counts']}, eval_subset {meta['eval_subset']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
