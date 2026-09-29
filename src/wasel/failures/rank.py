"""Group findings into issues and rank them.

Grouping: same failure type + same signature root (the part before " (detail)"), so "confirm_order failed
(timeout)" and "confirm_order failed (out_of_stock)" are one issue with a breakdown of the details.
Ranking: priority = severity x sessions affected x mean confidence. Needs-review issues are listed after every
confirmed failure, whatever their priority.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from wasel.failures.detect import SEVERITY, WHY, Finding


def root(signature: str) -> str:
    return signature.split(" (", 1)[0]


def group(findings: list[Finding], n_sessions: int) -> list[dict]:
    buckets: dict[tuple, list[Finding]] = defaultdict(list)
    for f in findings:
        buckets[(f.status, f.type, root(f.signature))].append(f)
    issues = []
    for (status, ftype, sig), items in buckets.items():
        sessions = sorted({f.session_id for f in items})
        conf = sum(f.confidence for f in items) / len(items)
        details = Counter(f.signature[len(sig):].strip(" ()") for f in items if f.signature != sig)
        issues.append({
            "type": ftype, "status": status, "title": WHY[ftype], "signature": sig, "details": dict(details),
            "sessions": sessions, "n_sessions": len(sessions),
            "share": round(len(sessions) / n_sessions, 3) if n_sessions else 0.0,
            "confidence": round(conf, 2), "severity": SEVERITY[ftype],
            "priority": round(SEVERITY[ftype] * len(sessions) * conf, 2),
            "findings": [f.to_dict() for f in sorted(items, key=lambda f: (-f.confidence, f.session_id))]})
    issues.sort(key=lambda i: (i["status"] != "failure", -i["priority"], i["type"]))
    for rank, i in enumerate(issues, start=1):
        i["rank"] = rank
    return issues
