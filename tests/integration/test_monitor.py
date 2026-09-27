"""Monitor (app/monitor.py) and the AI-quality read endpoints: /api/monitor, /api/traces, /api/eval."""
from __future__ import annotations

import json
import sqlite3

from app import monitor as mon
from app.llm import trace


def test_psi_zero_for_same_mix_and_large_for_a_shift():
    ref = {"fr": 0.5, "arabizi": 0.5}
    assert mon.psi(ref, ref) == 0.0
    assert mon.psi(ref, {"fr": 0.95, "arabizi": 0.05}) > 0.2
    assert mon.psi(ref, {"fr": 0.5, "arabizi": 0.4, "mixed": 0.1}) > 0      # a new category counts


def test_drift_needs_min_samples_to_alert():
    ref = {"language": {"fr": 1.0}}
    few = mon.drift({"language": ["arabizi"] * 5}, ref, ["language"], 0.2, min_n=20)
    many = mon.drift({"language": ["arabizi"] * 30}, ref, ["language"], 0.2, min_n=20)
    assert few[0]["psi"] > 0.2 and not few[0]["drifted"]
    assert many[0]["drifted"]


def test_monitor_on_seeded_app_has_every_section_and_no_text(dev):
    client, core, _ = dev
    r = client.get("/api/monitor")
    assert r.status_code == 200
    d = r.json()
    assert {"drift", "faithfulness", "safety", "ops", "alerts"} <= set(d)
    assert d["faithfulness"]["n"] > 0 and {x["feature"] for x in d["drift"]} == {"language", "address_level", "tier"}
    body = json.dumps(d)
    for o in client.get("/api/orders").json()["orders"]:          # no customer text leaks into the monitor
        assert not o.get("reason_short") or o["reason_short"] not in body


def test_judge_safety_counts_rejected_ungrounded_and_tone_verdicts():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE outbound_drafts (source TEXT, route TEXT, judge_json TEXT, created_at TEXT)")
    bad = {"decided_by": "llm", "approved": False, "grounded": False, "unsupported_claims": ["free delivery"],
           "tone_ok": False, "overreach": "delivery_commitment"}
    good = {"decided_by": "llm", "approved": True, "grounded": True, "unsupported_claims": [], "tone_ok": True,
            "overreach": "none"}
    rows = [bad] * 3 + [good] + [{"unavailable": True, "decided_by": "classifier"}]
    conn.executemany("INSERT INTO outbound_drafts VALUES (?,?,?,?)",
                     [("llm_rewrite", "needs_review", json.dumps(j), f"t{i}") for i, j in enumerate(rows)])
    s = mon.judge_safety(conn, 200)
    assert s["judge_reject_rate"] == 0.75 and s["judge_ungrounded_rate"] == 0.75 and s["judge_tone_fail_rate"] == 0.75
    assert s["judge_unavailable_rate"] == 0.2 and s["overreach"] == {"delivery_commitment": 3}


def test_traces_endpoint_filters_by_role(dev):
    client, _, _ = dev
    trace.clear()
    trace.emit({"trace_id": "t1", "role": "judge", "outcome": "ok"})
    trace.emit({"trace_id": "t2", "role": "extract", "outcome": "failed"})
    got = client.get("/api/traces", params={"role": "judge"}).json()["traces"]
    assert [t["trace_id"] for t in got] == ["t1"]
    trace.clear()


def test_eval_endpoint_serves_committed_reports(dev):
    client, _, _ = dev
    d = client.get("/api/eval").json()
    assert d["offline"]["mode"] == "offline" and not d["offline"]["gate_failures"]


def test_reference_is_committed_and_matches_the_builder():
    assert json.loads(mon.REFERENCE.read_text()) == mon.build_reference()
