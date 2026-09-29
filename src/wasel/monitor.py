"""Drift, faithfulness and safety monitor (GET /api/monitor). Reads only what the app already stores: assessments,
extraction runs, drafts (judge_json), llm_usage and the in-process trace buffer. Returns rates and codes, never
customer text. Thresholds: config/monitor.yaml. Reference mix for drift: data/monitor_reference.json, built from
the golden extraction set scored offline (`python -m wasel.monitor --build-reference`, deterministic).
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import Counter
from pathlib import Path

import yaml

from wasel.llm import trace
from wasel.paths import ROOT

CONFIG = ROOT / "config" / "monitor.yaml"
REFERENCE = ROOT / "data" / "monitor_reference.json"
EPS = 1e-4


def load_config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def psi(ref: dict[str, float], cur: dict[str, float]) -> float:
    """Population stability index over the union of categories (smoothed so an empty bin isn't infinite)."""
    keys = set(ref) | set(cur)
    total = 0.0
    for k in keys:
        p, q = max(ref.get(k, 0.0), EPS), max(cur.get(k, 0.0), EPS)
        total += (q - p) * math.log(q / p)
    return round(total, 4)


def dist(values: list) -> dict[str, float]:
    c = Counter(v if v is not None else "none" for v in values)
    n = sum(c.values())
    return {k: round(v / n, 4) for k, v in sorted(c.items())} if n else {}


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 4) if den else None


def _j(s: str | None, default):
    try:
        return json.loads(s) if s else default
    except ValueError:
        return default


def current_mix(conn: sqlite3.Connection, window: int) -> tuple[dict[str, list], list[sqlite3.Row]]:
    rows = conn.execute(
        "SELECT a.tier, a.path, a.context_json, e.validated_json, e.valid, e.dropped_quotes, e.dropped_flags, "
        "e.injection_suspected, e.provider FROM risk_assessments a "
        "LEFT JOIN extraction_runs e ON e.extraction_id = a.extraction_id "
        "ORDER BY a.created_at DESC LIMIT ?", (window,)).fetchall()
    mix: dict[str, list] = {"language": [], "address_level": [], "tier": [], "path": []}
    for r in rows:
        v = _j(r["validated_json"], {})
        ctx = _j(r["context_json"], {})
        mix["language"].append(v.get("language") or ctx.get("language"))
        mix["address_level"].append(v.get("address_level"))
        mix["tier"].append(r["tier"])
        mix["path"].append(r["path"])
    return mix, rows


def drift(mix: dict[str, list], reference: dict, features: list[str], threshold: float, min_n: int) -> list[dict]:
    out = []
    for f in features:
        cur, ref = dist(mix.get(f, [])), reference.get(f, {})
        n = len(mix.get(f, []))
        score = psi(ref, cur) if cur and ref else None
        out.append({"feature": f, "psi": score, "n": n, "reference": ref, "current": cur,
                    "drifted": bool(score is not None and n >= min_n and score >= threshold)})
    return out


def faithfulness(rows: list[sqlite3.Row]) -> dict:
    ext = [r for r in rows if r["validated_json"] is not None or r["valid"] is not None]
    n = len(ext)
    return {"n": n,
            "hallucinated_quotes_per_extraction": _rate(sum(r["dropped_quotes"] or 0 for r in ext), n),
            "dropped_flags_per_extraction": _rate(sum(r["dropped_flags"] or 0 for r in ext), n),
            "invalid_extraction_rate": _rate(sum(1 for r in ext if r["valid"] == 0), n),
            "injection_rate": _rate(sum(1 for r in ext if r["injection_suspected"]), n),
            "fallback_rate": _rate(sum(1 for r in rows if r["path"] not in ("llm", "cascade_ack", "cascade_cache")),
                                   len(rows))}


def judge_safety(conn: sqlite3.Connection, window: int) -> dict:
    drafts = conn.execute("SELECT source, route, judge_json FROM outbound_drafts ORDER BY created_at DESC LIMIT ?",
                          (window,)).fetchall()
    judged = [_j(d["judge_json"], {}) for d in drafts if d["judge_json"]]
    by_llm = [j for j in judged if j.get("decided_by") == "llm"]
    overreach = Counter(j.get("overreach") for j in by_llm if j.get("overreach") not in (None, "none"))
    return {"drafts": len(drafts), "judged": len(judged),
            "routes": dict(Counter(d["route"] for d in drafts)),
            "sources": dict(Counter(d["source"] for d in drafts)),
            "judge_reject_rate": _rate(sum(1 for j in by_llm if not j.get("approved")), len(by_llm)),
            "judge_ungrounded_rate": _rate(sum(1 for j in by_llm if not j.get("grounded", True)
                                               or j.get("unsupported_claims")), len(by_llm)),
            "judge_tone_fail_rate": _rate(sum(1 for j in by_llm if j.get("tone_ok") is False), len(by_llm)),
            "judge_unavailable_rate": _rate(sum(1 for j in judged if j.get("unavailable")), len(judged)),
            "classifier_veto_rate": _rate(sum(1 for j in judged if j.get("decided_by") == "classifier"
                                              and not j.get("unavailable")), len(judged)),
            "overreach": dict(overreach)}


def llm_ops(conn: sqlite3.Connection, window: int) -> dict:
    rows = conn.execute("SELECT role, provider, model, outcome, latency_ms, tokens_in, tokens_out FROM llm_usage "
                        "ORDER BY usage_id DESC LIMIT ?", (window,)).fetchall()
    roles: dict[str, dict] = {}
    for r in rows:
        s = roles.setdefault(r["role"], {"attempts": 0, "errors": 0, "refusals": 0, "tokens_in": 0,
                                         "tokens_out": 0, "lat": [], "models": Counter()})
        s["attempts"] += 1
        s["errors"] += int(r["outcome"] != "ok")
        s["refusals"] += int(r["outcome"] in ("schema_rejected", "parse_error", "truncated"))
        s["tokens_in"] += r["tokens_in"] or 0
        s["tokens_out"] += r["tokens_out"] or 0
        s["lat"].append(r["latency_ms"])
        s["models"][f"{r['provider']}:{r['model']}"] += 1
    for s in roles.values():
        lat = sorted(s.pop("lat"))
        s["p50_ms"], s["p95_ms"] = lat[len(lat) // 2], lat[min(len(lat) - 1, int(len(lat) * 0.95))]
        s["models"] = dict(s["models"])
    n = len(rows)
    return {"attempts": n, "llm_error_rate": _rate(sum(1 for r in rows if r["outcome"] != "ok"), n),
            "refusal_rate": _rate(sum(1 for r in rows if r["outcome"] in ("schema_rejected", "parse_error",
                                                                           "truncated")), n),
            "by_role": roles, "traces": trace.summary()}


def report(conn: sqlite3.Connection, cfg: dict | None = None, reference: dict | None = None) -> dict:
    cfg = cfg or load_config()
    if reference is None:
        reference = json.loads(REFERENCE.read_text(encoding="utf-8")) if REFERENCE.exists() else {}
    w, min_n = cfg["window"], cfg["min_samples"]
    mix, rows = current_mix(conn, w)
    d = drift(mix, reference.get("distributions", {}), cfg["drift_features"], cfg["drift_psi"], min_n)
    faith, safety, ops = faithfulness(rows), judge_safety(conn, w), llm_ops(conn, w)
    sizes = {"faithfulness": faith["n"], "safety": safety["judged"], "ops": ops["attempts"]}
    alerts = [{"kind": "drift", "metric": x["feature"], "value": x["psi"], "limit": cfg["drift_psi"]}
              for x in d if x["drifted"]]
    for group, vals in (("faithfulness", faith), ("safety", safety), ("ops", ops)):
        for metric, limit in cfg["ceilings"].items():
            v = vals.get(metric)
            if v is not None and sizes[group] >= min_n and v > limit:
                alerts.append({"kind": group, "metric": metric, "value": v, "limit": limit})
    return {"window": w, "min_samples": min_n, "reference": reference.get("source"), "drift": d,
            "faithfulness": faith, "safety": safety, "ops": ops, "alerts": alerts}


def build_reference() -> dict:
    """Mix of the golden extraction set as the offline pipeline scores it: the population the floors were set on."""
    from wasel.evaluation.run import load, score_input
    from wasel.scoring.score_order import score_order
    mix: dict[str, list] = {"language": [], "address_level": [], "tier": []}
    rows = load("extraction.jsonl", None)
    for r in rows:
        res = score_order(score_input(r["input"]["messages"], r["input"]["price_tnd"]), cache=None, llm=None,
                          meter=None)
        v = (res.extraction.validated if res.extraction else {}) or {}
        mix["language"].append(v.get("language"))
        mix["address_level"].append(v.get("address_level"))
        mix["tier"].append(res.assessment.tier if res.assessment else None)
    return {"source": f"data/eval/golden/extraction.jsonl ({len(rows)} rows, offline pipeline)",
            "distributions": {k: dist(v) for k, v in mix.items()}}


if __name__ == "__main__":
    if "--build-reference" in sys.argv:
        REFERENCE.write_text(json.dumps(build_reference(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {REFERENCE.relative_to(ROOT)}")
