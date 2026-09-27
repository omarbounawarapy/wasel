"""Run the golden sets and gate on eval/thresholds.yaml. `make eval` (offline, no keys: rules extractor + prefilter
+ guard classifier, runs in CI on every PR) or `make eval-live` (LLM extraction + LLM judge, with GROQ_API_KEY).
Writes reports/eval[_live].json. Exit code 1 if any gated metric is under its threshold -> the PR is blocked.

  python -m eval.run [--live] [--limit N]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

from app.contracts import CustomerHistory, ScoreInput, StructuredFields, WindowMessage
from app.llm import trace
from app.llm.prompts import active_versions
from app.outbound import judge as J
from app.outbound.guard_clf import classify
from app.outbound.prefilter import prefilter
from app.scoring.config import default_config
from app.scoring.score_order import score_order

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "eval" / "golden"
LEVELS = ["none", "city_only", "area_or_landmark", "street_and_landmark", "exact"]
T0 = datetime(2026, 9, 27, 10, 0, tzinfo=UTC)


def load(name: str, limit: int | None, sample: int | None = None) -> list[dict]:
    """`sample`: every k-th row. The files are sorted by stratum (language x address level), so this keeps the mix."""
    rows = [json.loads(line) for line in (GOLD / name).read_text(encoding="utf-8").splitlines() if line.strip()]
    if sample and sample < len(rows):
        rows = rows[::-(-len(rows) // sample)]
    return rows[:limit] if limit else rows


def paced(rows, pace_s: float):
    """Live runs: space the calls so the primary model's tokens-per-minute limit isn't what gets measured."""
    for i, r in enumerate(rows):
        if i and pace_s:
            time.sleep(pace_s)
        yield r


def score_input(texts: list[str], price: float) -> ScoreInput:
    msgs = [WindowMessage(f"m{i}", "inbound", "customer", "paste", "text", t, None, None, None, False,
                          T0.replace(second=i), True) for i, t in enumerate(texts)]
    return ScoreInput("eval", None, "paste", "initial", msgs, StructuredFields(price_tnd=price),
                      CustomerHistory(0, 0), None, T0)


def run_extraction(rows, llm) -> dict:
    n = exact = near = lang_ok = flag_tp = flag_fp = flag_fn = order_ok = hallucinated = 0
    paths: dict[str, int] = {}
    for r in rows:
        res = score_order(score_input(r["input"]["messages"], r["input"]["price_tnd"]), cache=None, llm=llm,
                          meter=None)
        e, v = r["expected"], (res.extraction.validated if res.extraction else {}) or {}
        n += 1
        order_ok += int(res.is_order == e["is_order"])
        paths[res.assessment.path if res.assessment else "none"] = paths.get(
            res.assessment.path if res.assessment else "none", 0) + 1
        hallucinated += (res.extraction.dropped_quotes or 0) if res.extraction else 0
        got = v.get("address_level", "none")
        exact += int(got == e["address_level"])
        near += int(abs(LEVELS.index(got) - LEVELS.index(e["address_level"])) <= 1)
        lang_ok += int(v.get("language") == e["language"])
        codes = {f["code"] for f in v.get("red_flags", [])}
        want = set(e["flags"])
        flag_tp += len(codes & want)
        flag_fp += len(codes - want)
        flag_fn += len(want - codes)
    p = flag_tp / (flag_tp + flag_fp) if flag_tp + flag_fp else 1.0
    rc = flag_tp / (flag_tp + flag_fn) if flag_tp + flag_fn else 1.0
    return {"n": n, "is_order_acc": order_ok / n, "address_exact_acc": exact / n, "address_within1_acc": near / n,
            "language_acc": lang_ok / n, "flag_precision": p, "flag_recall": rc,
            "flag_f1": 2 * p * rc / (p + rc) if p + rc else 0.0,
            "hallucinated_quotes_per_order": hallucinated / n, "paths": paths}


def run_outbound(rows, llm) -> dict:
    """Task: decide send / don't send. Success = unsafe drafts stopped AND safe drafts let through."""
    cfg = default_config()
    tp = tn = fp = fn = 0
    misses, by_layer = [], {"prefilter": 0, "classifier": 0, "llm_judge": 0}
    for r in rows:
        d, tmpl = r["input"]["draft"], r["input"]["template"]
        q = "one" if ("?" in tmpl or "؟" in tmpl) else "none"
        fails = prefilter(d, tmpl, {}, q, cfg["prefilter"], cfg["lexicons"].get("injection"))
        blocked, layer = bool(fails), "prefilter"
        if not blocked:
            blocked, layer = classify(d).p_unsafe >= 0.2, "classifier"
        if not blocked and llm is not None:
            facts = {"product": None, "price_tnd": None, "quantity": 1, "authorized_action": "as_in_template",
                     "template_id": "T_CONFIRM", "approved_template": tmpl, "language": "any",
                     "formality": "formal", "expected_questions": q}
            v = J.judge(d, facts, llm=llm, meter=None, sandbox_id=None, now=T0, block_at=1.01, hold_at=1.01)
            blocked, layer = (not v.approved and not v.unavailable), "llm_judge"
        if not r["expected"]["safe"]:
            tp, fn = tp + blocked, fn + (not blocked)
            if blocked:
                by_layer[layer] += 1
            else:
                misses.append({"id": r["id"], "kind": "missed_unsafe", "category": r["expected"]["category"]})
        else:
            tn, fp = tn + (not blocked), fp + blocked
            if blocked:
                misses.append({"id": r["id"], "kind": "false_block", "layer": layer})
    n = tp + tn + fp + fn
    return {"n": n, "task_success": (tp + tn) / n, "unsafe_blocked": tp / (tp + fn) if tp + fn else 1.0,
            "safe_passed": tn / (tn + fp) if tn + fp else 1.0, "blocked_by_layer": by_layer, "misses": misses[:20]}


def run_injection(rows, llm) -> dict:
    flagged = scored = not_exact = n = 0
    for r in rows:
        n += 1
        res = score_order(score_input(r["input"]["messages"], r["input"]["price_tnd"]), cache=None, llm=llm,
                          meter=None)
        flagged += int(res.injection_suspected)
        scored += int(res.is_order and res.assessment is not None)
        lvl = (res.extraction.validated or {}).get("address_level") if res.extraction else None
        not_exact += int(lvl != "exact")
    return {"n": n, "flagged_rate": flagged / n, "still_scored_rate": scored / n, "not_promoted_rate": not_exact / n}


def _usage_delta(before: dict, after: dict) -> dict:
    keys = ("requests", "cache_hits", "failed", "tokens_in", "tokens_out")
    return {role: {**{k: s[k] - before.get(role, {}).get(k, 0) for k in keys},
                   "p50_ms": s["p50_ms"], "p95_ms": s["p95_ms"]} for role, s in after.items()}


def gate(report: dict, thresholds: dict) -> list[str]:
    fails = []
    for task, metrics in thresholds.items():
        for metric, floor in metrics.items():
            got = report["results"].get(task, {}).get(metric)
            if got is not None and got < floor:
                fails.append(f"{task}.{metric} = {got:.3f} < {floor}")
    return fails


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sample", type=int, help="extraction rows, stratified (live default 40: token budget)")
    ap.add_argument("--pace", type=float, default=0.0, help="seconds between LLM cases (live)")
    a = ap.parse_args(argv)
    llm = None
    if a.live:
        from app.llm.client import build_client
        llm = build_client("live")
        if not llm.steps:
            print("eval --live: no provider configured (GROQ_API_KEY)", file=sys.stderr)
            return 2
    t0 = time.monotonic()
    sample = a.sample if a.sample is not None else (40 if a.live else None)
    usage0 = trace.summary()
    results = {"extraction": run_extraction(paced(load("extraction.jsonl", a.limit, sample), a.pace), llm),
               "outbound": run_outbound(paced(load("outbound.jsonl", a.limit), a.pace / 4), llm),
               "injection": run_injection(paced(load("injection.jsonl", a.limit), a.pace), llm)}
    th = yaml.safe_load((ROOT / "eval" / "thresholds.yaml").read_text())["live" if a.live else "offline"]
    report = {"mode": "live" if a.live else "offline", "versions": active_versions(),
              "config_hash": default_config().short_hash, "runtime_s": round(time.monotonic() - t0, 1),
              "results": results, "llm_usage": _usage_delta(usage0, trace.summary()) if a.live else {}}
    report["gate_failures"] = gate(report, th)
    out = ROOT / "reports" / ("eval_live.json" if a.live else "eval.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for task, m in results.items():
        print(task, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in m.items() if k != "misses"})
    if report["gate_failures"]:
        print("EVAL GATE FAILED:\n  " + "\n  ".join(report["gate_failures"]))
        return 1
    print(f"eval gate: green ({report['runtime_s']} s) -> {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
