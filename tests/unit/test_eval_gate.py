"""The evaluation gate fails closed: a missing metric, a shrunken set and a partial run cannot pass."""
from __future__ import annotations

import yaml

from wasel.evaluation import run as R

TH = {"a": {"min_cases": 10, "acc": 0.9, "rate": 1.0}, "b": {"min_cases": 2, "acc": 0.5}}
OK = {"results": {"a": {"n": 10, "acc": 0.95, "rate": 1.0}, "b": {"n": 2, "acc": 0.5}}}


def test_a_complete_report_above_its_floors_passes():
    assert R.gate(OK, TH) == []


def test_empty_results_fail_every_gated_metric_and_set_size():
    fails = R.gate({"results": {}}, TH)
    assert "a.acc missing from report" in fails and "a.rate missing from report" in fails
    assert "b.acc missing from report" in fails
    assert any(f.startswith("a.n = 0 < 10") for f in fails) and any(f.startswith("b.n = 0 < 2") for f in fails)
    assert len(fails) == 5


def test_a_renamed_metric_fails():
    res = {"a": {"n": 10, "accuracy": 0.95, "rate": 1.0}, "b": OK["results"]["b"]}
    assert R.gate({"results": res}, TH) == ["a.acc missing from report"]


def test_a_set_with_fewer_cases_than_min_cases_fails():
    res = {"a": {"n": 9, "acc": 0.95, "rate": 1.0}, "b": OK["results"]["b"]}
    assert R.gate({"results": res}, TH) == ["a.n = 9 < 10 cases (min_cases)"]


def test_a_metric_under_its_floor_still_fails():
    res = {"a": {"n": 10, "acc": 0.89, "rate": 1.0}, "b": OK["results"]["b"]}
    assert R.gate({"results": res}, TH) == ["a.acc = 0.890 < 0.9"]


def test_every_committed_gate_entry_has_a_min_cases():
    cfg = yaml.safe_load((R.ROOT / "config" / "eval.yaml").read_text())
    for mode in ("offline", "live"):
        assert all("min_cases" in t for t in cfg[mode].values()), mode


def test_a_partial_run_neither_passes_nor_rewrites_the_committed_report(tmp_path):
    report = R.ROOT / "data" / "reports" / "eval.json"
    before = report.read_bytes()
    assert R.main(["--limit", "5"]) == 3
    assert report.read_bytes() == before
