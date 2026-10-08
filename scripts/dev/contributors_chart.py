"""Write docs/assets/contributors.svg: a pie chart of the commits per contributor on the current branch.

usage: python scripts/dev/contributors_chart.py [--out PATH] [--rev REV]

The same person often commits under several names and emails, so identities are merged by GitHub handle (see
ALIASES; a `<id>+<handle>@users.noreply.github.com` address maps to its handle on its own). Bot accounts and the
commits that regenerate this chart are not counted. The .github/workflows/contributors.yml workflow runs this on
every push to main and commits the result, which is what keeps the README chart current.
"""
from __future__ import annotations

import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "assets" / "contributors.svg"
CHART_COMMIT = "Update the contributors chart"
# email or commit name (lower case) -> GitHub handle, for people who commit with an address that carries no handle
ALIASES = {
    "omar.bounawara.py@gmail.com": "omarbounawarapy",
    "riahiaziz199@gmail.com": "azaizoz",
    "jesser.chebbi16@gmail.com": "j6r-t",
}
COLORS = ["#2563eb", "#16a34a", "#d97706", "#9333ea", "#dc2626", "#0891b2", "#64748b", "#db2777"]
NOREPLY = re.compile(r"^(?:\d+\+)?([A-Za-z0-9-]+)@users\.noreply\.github\.com$")


def handle(name: str, email: str) -> str | None:
    """The GitHub handle behind a commit identity, its name when unknown, or None for a bot."""
    email = email.strip().lower()
    if name.endswith("[bot]") or email.endswith("[bot]@users.noreply.github.com"):
        return None
    if email in ALIASES:
        return ALIASES[email]
    m = NOREPLY.match(email)
    return m.group(1).lower() if m else name.strip()


def count_commits(rev: str = "HEAD") -> Counter:
    out = subprocess.run(["git", "log", rev, "--format=%an%x1f%ae%x1f%s"], cwd=ROOT, capture_output=True, text=True,
                         check=True).stdout
    counts: Counter = Counter()
    for line in out.splitlines():
        name, email, subject = line.split("\x1f", 2)
        who = handle(name, email)
        if who and subject != CHART_COMMIT:
            counts[who] += 1
    return counts


def _slice(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    x0, y0 = cx + r * math.sin(a0), cy - r * math.cos(a0)
    x1, y1 = cx + r * math.sin(a1), cy - r * math.cos(a1)
    return f"M{cx:.1f},{cy:.1f} L{x0:.2f},{y0:.2f} A{r},{r} 0 {int(a1 - a0 > math.pi)} 1 {x1:.2f},{y1:.2f} Z"


def render(counts: Counter) -> str:
    total = sum(counts.values()) or 1
    people = counts.most_common()
    cx, cy, r = 130, 130, 110
    height = max(260, 70 + 30 * len(people))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="{height}" viewBox="0 0 640 {height}" '
             'role="img" aria-labelledby="t"><title id="t">Commits per contributor</title>',
             f'<rect width="640" height="{height}" rx="12" fill="#ffffff" stroke="#d0d7de"/>']
    angle = 0.0
    for i, (who, n) in enumerate(people):
        color = COLORS[i % len(COLORS)]
        sweep = 2 * math.pi * n / total
        if len(people) == 1:
            parts.append(f'<circle cx="{cx}" cy="{cy + 10}" r="{r}" fill="{color}"/>')
        else:
            parts.append(f'<path d="{_slice(cx, cy + 10, r, angle, angle + sweep)}" fill="{color}" stroke="#ffffff" '
                         'stroke-width="2"/>')
        angle += sweep
        y = 62 + 30 * i
        unit = "commit" if n == 1 else "commits"
        parts.append(f'<rect x="270" y="{y - 12}" width="14" height="14" rx="3" fill="{color}"/>')
        parts.append(f'<text x="294" y="{y}" font-family="Arial,Helvetica,sans-serif" font-size="15" fill="#1f2328">'
                     f'{who} <tspan fill="#59636e">{100 * n / total:.1f}% · {n} {unit}</tspan></text>')
    parts.append('<text x="270" y="32" font-family="Arial,Helvetica,sans-serif" font-size="16" font-weight="700" '
                 f'fill="#1f2328">Commits per contributor ({total})</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    out, rev = OUT, "HEAD"
    args = iter(argv)
    for a in args:
        if a == "--out":
            out = Path(next(args))
        elif a == "--rev":
            rev = next(args)
        else:
            print(f"unknown argument {a}", file=sys.stderr)
            return 2
    counts = count_commits(rev)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(counts), encoding="utf-8")
    print(", ".join(f"{k} {v}" for k, v in counts.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
