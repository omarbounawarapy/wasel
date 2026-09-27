"""Hidden-failure analyzer: sessions -> detectors -> (optional LLM review of the ambiguous ones) -> ranked issues.

  python -m failures.run                     synthetic labeled set (data/agent_sessions.jsonl) + scoring
  python -m failures.run --source db         this app's own orders (var/app.db), same detectors
  python -m failures.run --llm               also ask the LLM to adjudicate needs-review findings

Writes reports/failures.json (synthetic) or reports/failures_db.json: ranked issues with grouped sessions and
evidence, per-type precision/recall against the labels, runtime and cost.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from failures import dataset
from failures.detect import REPORT_AT, SEVERITY, Finding, detect
from failures.rank import group
from failures.semantics import LLMSemantics, RuleSemantics

ROOT = Path(__file__).resolve().parents[1]
LIMITS = [
    "Detectors are rules tuned on the shapes in this dataset (tool names, FR/Arabizi phrasing). New tools or "
    "languages need new patterns; the LLM review only sees findings the rules already raised (no recall gain).",
    "Synthetic sessions are cleaner than real traffic; the scores below are an upper bound for real logs.",
    "Ambiguous cases (reminders after silence, hedged wording) are surfaced as needs-review, not counted as failures.",
    "On this app's data, 'tool calls' are the pipeline steps (extraction, scoring, drafting, judge, send) rebuilt "
    "from the database, not a live agent trace.",
]


def score(sessions: list[dict], findings: list[Finding]) -> dict:
    """Session-level precision/recall per type, counting only findings at >= REPORT_AT confidence."""
    got: dict[str, set] = {t: set() for t in SEVERITY}
    for f in findings:
        if f.confidence >= REPORT_AT:
            got[f.type].add(f.session_id)
    per, tp_all, fp_all, fn_all = {}, 0, 0, 0
    for t in SEVERITY:
        want = {s["session_id"] for s in sessions if t in s["label"]["failures"]}
        tp, fp, fn = len(got[t] & want), len(got[t] - want), len(want - got[t])
        tp_all, fp_all, fn_all = tp_all + tp, fp_all + fp, fn_all + fn
        per[t] = {"support": len(want), "tp": tp, "fp": fp, "fn": fn,
                  "precision": round(tp / (tp + fp), 3) if tp + fp else None,
                  "recall": round(tp / (tp + fn), 3) if tp + fn else None,
                  "false_positive_sessions": sorted(got[t] - want)[:5], "missed_sessions": sorted(want - got[t])[:5]}
    flagged = {f.session_id for f in findings if f.confidence >= REPORT_AT}
    clean = [s for s in sessions if s["label"]["kind"] in ("success", "recovery")]
    return {"per_type": per,
            "micro_precision": round(tp_all / (tp_all + fp_all), 3) if tp_all + fp_all else None,
            "micro_recall": round(tp_all / (tp_all + fn_all), 3) if tp_all + fn_all else None,
            "clean_sessions_flagged": sum(1 for s in clean if s["session_id"] in flagged),
            "clean_sessions": len(clean),
            "recoveries_flagged": sorted(s["session_id"] for s in clean
                                         if s["label"]["kind"] == "recovery" and s["session_id"] in flagged),
            "ambiguous_to_review": sum(1 for s in sessions if s["label"]["kind"] == "ambiguous"
                                       and any(f.session_id == s["session_id"] and f.confidence < REPORT_AT
                                               for f in findings))}


def analyze(sessions: list[dict], *, llm=None) -> dict:
    t0 = time.perf_counter()
    sem = RuleSemantics()
    if llm is not None:
        sem = LLMSemantics(llm, sessions)
    t_label = time.perf_counter() - t0
    findings = [f for s in sessions for f in detect(s, sem)]
    t_rules = time.perf_counter() - t0 - t_label
    review = {"semantics": sem.name, **(sem.stats if llm is not None else {})}
    issues = group(findings, len(sessions))
    runtime = time.perf_counter() - t0
    return {"n_sessions": len(sessions), "n_events": sum(len(s["events"]) for s in sessions),
            "findings": len(findings), "by_status": dict(Counter(f.status for f in findings)),
            "issues": issues, "semantics": review,
            "runtime": {"labeling_s": round(t_label, 3), "rules_s": round(t_rules, 3), "total_s": round(runtime, 3),
                        "ms_per_session": round(1000 * runtime / max(1, len(sessions)), 2)},
            "cost": {"llm_calls": review.get("calls", 0),
                     "llm_tokens": review.get("tokens_in", 0) + review.get("tokens_out", 0),
                     "note": "rules only: 0 LLM calls, CPU only" if llm is None else
                     "one call per 25 unique message texts; cached by text"},
            "limitations": LIMITS, "_findings": findings}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["synthetic", "holdout", "db"], default="synthetic")
    ap.add_argument("--db", default=str(ROOT / "var" / "app.db"))
    ap.add_argument("--llm", action="store_true", help="LLM language layer (needs GROQ_API_KEY)")
    a = ap.parse_args(argv)
    if a.source in ("synthetic", "holdout"):
        sessions = dataset.load(dataset.OUT if a.source == "synthetic" else dataset.OUT_HOLDOUT)
    else:
        from app.db.conn import connect
        from failures.adapter import sessions_from_db
        sessions = sessions_from_db(connect(a.db))
    llm = None
    if a.llm:
        from app.llm.client import build_client
        llm = build_client("live")
        if not llm.steps:
            print("failures --llm: no provider configured (GROQ_API_KEY)", file=sys.stderr)
            return 2
    rep = analyze(sessions, llm=llm)
    findings = rep.pop("_findings")
    if a.source != "db":
        rep["accuracy"] = score(sessions, findings)
    out = ROOT / "reports" / (f"failures_{a.source}" + ("_llm" if a.llm else "") + ".json")
    doc = {"source": a.source, "semantics_mode": "llm" if a.llm else "rules", **rep}
    out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{rep['n_sessions']} sessions, {rep['findings']} findings {rep['by_status']}, "
          f"{len(rep['issues'])} issues, {rep['runtime']['total_s']} s")
    for i in rep["issues"][:10]:
        print(f"  #{i['rank']} [{i['status']}] {i['type']} x{i['n_sessions']} conf {i['confidence']} "
              f"prio {i['priority']}: {i['signature']} {i['details'] or ''}")
    if "accuracy" in rep:
        acc = rep["accuracy"]
        print(f"precision {acc['micro_precision']} recall {acc['micro_recall']} · clean flagged "
              f"{acc['clean_sessions_flagged']}/{acc['clean_sessions']} · ambiguous to review "
              f"{acc['ambiguous_to_review']}")
        for t, m in acc["per_type"].items():
            print(f"    {t:28s} P {m['precision']} R {m['recall']} (n={m['support']}) fp {m['false_positive_sessions']}"
                  f" miss {m['missed_sessions']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
