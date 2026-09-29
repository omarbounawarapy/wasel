#!/usr/bin/env python3
"""Threaded extraction probe for a self-hosted GPU endpoint.

Runs the golden extraction set against the live LLM chain N-wide (vLLM batches
server-side, so concurrency only changes wall time) and prints per-case rows for
every mismatch and every case that fell through to the rules extractor, plus a
(path, is_order_correct) tally. The official gate stays `make eval-live` — this
is the fast diagnostic, not the record.

  GROQ_BASE_URL=http://localhost:8001/v1 GROQ_API_KEY=... EXTRACT_MODEL=openai/gpt-oss-20b \
      python scripts/ops/extract_probe.py [--threads 8] [--sample 40]
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor

from wasel.evaluation.run import load, score_input
from wasel.llm.client import build_client
from wasel.scoring.score_order import score_order


def probe_row(r: dict, llm) -> dict:
    res = score_order(score_input(r["input"]["messages"], r["input"]["price_tnd"]),
                      cache=None, llm=llm, meter=None)
    v = (res.extraction.validated if res.extraction else {}) or {}
    return {"id": r.get("id"), "messages": r["input"]["messages"],
            "expected": r["expected"], "got": {"is_order": res.is_order, **v},
            "path": res.assessment.path if res.assessment else "none"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--sample", type=int, default=40)
    ap.add_argument("--set", default="extraction.jsonl")
    a = ap.parse_args()

    llm = build_client("live")
    if not llm.steps:
        print("no provider configured (GROQ_API_KEY)", file=sys.stderr)
        return 2
    rows = load(a.set, None, a.sample)
    with ThreadPoolExecutor(max_workers=a.threads) as ex:
        out = list(ex.map(lambda r: probe_row(r, llm), rows))

    tally: dict[tuple, list] = {}
    for p in out:
        ok = p["got"]["is_order"] == p["expected"]["is_order"]
        tally.setdefault((p["path"], ok), []).append(p["id"])
        if not ok or p["path"] == "none":
            e = p["expected"]
            print(f"--- {p['id']} path={p['path']} is_order_ok={ok}")
            print(f"    expected: is_order={e['is_order']} addr={e['address_level']} "
                  f"lang={e['language']} flags={e['flags']}")
            got = p["got"]
            print(f"    got     : is_order={got['is_order']} addr={got.get('address_level')} lang={got.get('language')} "
                  f"flags={[f['code'] for f in got.get('red_flags', [])]} qty={got.get('quantity')}")
            for m in p["messages"]:
                print(f"    msg: {(m.get('text') if isinstance(m, dict) else str(m))[:110]}")
    n = len(out)
    ok_n = sum(len(v) for (path, ok), v in tally.items() if ok)
    print(f"TALLY: is_order {ok_n}/{n} = {ok_n / n:.3f}")
    for k in sorted(tally, key=str):
        print(" ", k, len(tally[k]), tally[k])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
