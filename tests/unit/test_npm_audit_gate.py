"""The npm audit gate (scripts/ops/npm_audit_gate.py) finds high and critical advisories by GHSA id and nothing else."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("npm_audit_gate", ROOT / "scripts" / "ops" / "npm_audit_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def _vuln(severity, *urls):
    return {"severity": severity, "via": [{"url": u} for u in urls] + ["some-package"]}


def test_only_high_and_critical_advisories_count():
    report = {"vulnerabilities": {
        "a": _vuln("high", "https://github.com/advisories/GHSA-aaaa-bbbb-cccc"),
        "b": _vuln("critical", "https://github.com/advisories/GHSA-dddd-eeee-ffff"),
        "c": _vuln("moderate", "https://github.com/advisories/GHSA-gggg-hhhh-iiii"),
    }}
    assert gate.high_advisories(report) == {"GHSA-aaaa-bbbb-cccc", "GHSA-dddd-eeee-ffff"}


def test_the_accepted_braces_advisory_is_documented():
    assert gate.ALLOWED["GHSA-vfj7-8cjw-p6xm"].startswith("braces")
