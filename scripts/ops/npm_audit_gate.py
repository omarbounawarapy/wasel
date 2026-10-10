"""python scripts/ops/npm_audit_gate.py DIR [--allow GHSA-ID ...]

Runs `npm audit --package-lock-only` on the whole tree (dev dependencies included) and exits 1 when a high or critical
advisory is not on the allowlist. Every allowed advisory needs a reason here: an exception is a decision, not a default.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# advisory -> why it is accepted. Keep this list short; remove an entry as soon as upstream ships a fix.
ALLOWED = {
    "GHSA-vfj7-8cjw-p6xm": "braces <=3.0.3 (stack exhaustion). Reached only through eslint-config-next -> "
                           "@next/eslint-plugin-next -> fast-glob -> micromatch. No braces release is fixed, and the "
                           "linter does not ship in the images.",
}
GHSA = re.compile(r"GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}")


def high_advisories(report: dict) -> set[str]:
    found = set()
    for vuln in report.get("vulnerabilities", {}).values():
        if vuln.get("severity") not in ("high", "critical"):
            continue
        for via in vuln.get("via", []):
            if isinstance(via, dict):
                found.update(GHSA.findall(via.get("url", "")))
    return found


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    directory = Path(argv[0])
    run = subprocess.run(["npm", "audit", "--package-lock-only", "--json"], cwd=directory, capture_output=True, text=True)
    report = json.loads(run.stdout or "{}")
    if "error" in report:
        print(f"{directory}: npm audit failed: {report['error'].get('summary', report['error'])}")
        return 1
    found = high_advisories(report)
    blocked = sorted(found - set(ALLOWED))
    for advisory in sorted(found & set(ALLOWED)):
        print(f"{directory}: accepted {advisory}: {ALLOWED[advisory]}")
    if blocked:
        print(f"{directory}: high or critical advisories not accepted: {', '.join(blocked)}")
        return 1
    print(f"{directory}: no unaccepted high or critical advisories")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
