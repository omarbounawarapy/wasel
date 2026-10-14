"""Score the native-speaker holdout (data/eval/native/holdout_native.jsonl) with the rules extractor, or with the
configured LLM chain (--live), and write the metrics next to the other reports.

The set is separate from the development sets and from `make eval`: nothing here is gated or tuned against. Labels
are the translator's own: is it an order, how complete the address is, how likely a refusal is.

    python scripts/data/run_holdout.py            # rules path, no network
    python scripts/data/run_holdout.py --live     # LLM chain (needs GROQ_API_KEY); --pace seconds between cases
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from wasel.evaluation.run import T0  # noqa: E402
from wasel.contracts import CustomerHistory, ScoreInput, StructuredFields, WindowMessage  # noqa: E402
from wasel.scoring.score_order import score_order  # noqa: E402

SET = ROOT / "data" / "eval" / "native" / "holdout_native.jsonl"
# The labeler used four address words; the system uses five levels. Compare at the labeler's granularity.
BUCKET = {"none": "none", "city_only": "vague", "area_or_landmark": "partial",
          "street_and_landmark": "complete", "exact": "complete"}


def build_input(r: dict) -> ScoreInput:
    msgs = [WindowMessage(f"m{i}", "inbound", "customer", "paste", "text", t, None, None, None, False,
                          T0.replace(second=i)) for i, t in enumerate(r["messages"])]
    return ScoreInput("holdout", None, "paste", "initial", msgs,
                      StructuredFields(price_tnd=r["price_tnd"], zone=None),
                      CustomerHistory(r["completed_orders"], r["refusals_total"]), None, T0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--pace", type=float, default=0.0)
    a = ap.parse_args(argv)
    llm = None
    if a.live:
        from wasel.llm.client import build_client
        llm = build_client("live")
        if not llm.steps:
            print("--live needs GROQ_API_KEY", file=sys.stderr)
            return 2
    rows = [json.loads(x) for x in SET.read_text(encoding="utf-8").splitlines() if x.strip()]
    n = ord_n = ord_ok = addr_n = addr_ok = addr_near = lang_n = lang_ok = risk_n = risk_ok = 0
    paths: dict[str, int] = {}
    by_risk: dict[str, list[int]] = {}
    misses = []
    order_levels = ["none", "vague", "partial", "complete"]
    t0 = time.monotonic()
    for r in rows:
        if a.pace:
            time.sleep(a.pace)
        res = score_order(build_input(r), cache=None, llm=llm, meter=None)
        v = (res.extraction.validated if res.extraction else {}) or {}
        lab = r["labels"]
        n += 1
        p = res.extraction.model if res.extraction else "?"
        paths[p] = paths.get(p, 0) + 1
        if lab["is_order"] is not None:
            ord_n += 1
            ok = bool(res.is_order) == lab["is_order"]
            ord_ok += ok
            if not ok:
                misses.append({"id": r["id"], "kind": "is_order", "expected": lab["is_order"], "got": bool(res.is_order)})
        if lab["is_order"] and lab["address"] in order_levels:
            got = BUCKET[v.get("address_level", "none")]
            addr_n += 1
            addr_ok += got == lab["address"]
            addr_near += abs(order_levels.index(got) - order_levels.index(lab["address"])) <= 1
        if lab["language"]:
            lang_n += 1
            lang_ok += v.get("language") == lab["language"]
        if lab["is_order"] and lab["refusal_risk"] in ("low", "medium", "high"):
            risk_n += 1
            if res.assessment is not None:       # a labelled order that the system did not treat as one counts as wrong
                risk_ok += res.assessment.tier == lab["refusal_risk"]
                by_risk.setdefault(lab["refusal_risk"], []).append(res.assessment.final_score)
    report = {
        "mode": "live" if a.live else "rules",
        "set": "data/eval/native/holdout_native.jsonl",
        "provenance": "native_speaker_holdout: scenarios by a context-free model, translated and labelled by a native "
                      "speaker who had seen the word lists; never used to tune the system",
        "n": n, "paths": paths,
        "is_order_acc": ord_ok / ord_n if ord_n else None, "is_order_n": ord_n,
        "address_exact_acc": addr_ok / addr_n if addr_n else None,
        "address_within1_acc": addr_near / addr_n if addr_n else None, "address_n": addr_n,
        "language_acc": lang_ok / lang_n if lang_n else None, "language_n": lang_n,
        "refusal_tier_agreement": risk_ok / risk_n if risk_n else None, "refusal_n": risk_n,
        "mean_score_by_labelled_risk": {k: round(sum(v) / len(v), 1) for k, v in sorted(by_risk.items())},
        "misses": misses, "runtime_s": round(time.monotonic() - t0, 1),
    }
    out = ROOT / "data" / "reports" / ("holdout_native_live.json" if a.live else "holdout_native.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
