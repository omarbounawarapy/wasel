"""Write two pie charts for the README: docs/assets/contributors.svg (commits per contributor on the current branch)
and docs/assets/contributors-lines.svg (lines of code added per contributor).

usage: python scripts/dev/contributors_chart.py [--out-dir DIR] [--rev REV]

Lines are the added lines of source files only (see CODE_SUFFIXES and SKIP): lockfiles, generated reports, data, test
fixtures, images and the design exploration pages would otherwise decide the chart. Merge commits add no lines.

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
OUT_DIR = ROOT / "docs" / "assets"
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".css", ".sh", ".sql", ".yml", ".yaml", ".toml", ".md", ".html"}
SKIP = ("docs/design-explorations/", "data/", "tests/fixtures/", "tests/golden/", "docs/assets/", "models/", "web/dist/")
SKIP_NAMES = {"package-lock.json", "eval.json"}
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


def count(rev: str = "HEAD") -> tuple[Counter, Counter]:
    """(commits, lines added) per contributor handle."""
    out = subprocess.run(["git", "log", rev, "--numstat", "--format=@%an%x1f%ae%x1f%s"], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout
    commits: Counter = Counter()
    lines: Counter = Counter()
    who = None
    for line in out.splitlines():
        if line.startswith("@"):
            name, email, subject = line[1:].split("\x1f", 2)
            who = handle(name, email)
            if subject == CHART_COMMIT:
                who = None
            if who:
                commits[who] += 1
        elif who and line.count("\t") == 2:
            added, _, path = line.split("\t")
            if added.isdigit() and counts_as_code(path):
                lines[who] += int(added)
    return commits, +lines


def counts_as_code(path: str) -> bool:
    """Whether the lines of `path` belong in the lines chart."""
    p = Path(path)
    return p.suffix in CODE_SUFFIXES and p.name not in SKIP_NAMES and not path.startswith(SKIP)


def count_commits(rev: str = "HEAD") -> Counter:
    """Commits per contributor handle."""
    return count(rev)[0]


def _slice(cx: float, cy: float, r: float, a0: float, a1: float) -> str:
    x0, y0 = cx + r * math.sin(a0), cy - r * math.cos(a0)
    x1, y1 = cx + r * math.sin(a1), cy - r * math.cos(a1)
    return f"M{cx:.1f},{cy:.1f} L{x0:.2f},{y0:.2f} A{r},{r} 0 {int(a1 - a0 > math.pi)} 1 {x1:.2f},{y1:.2f} Z"


def render(counts: Counter, title: str = "Commits per contributor", unit: str = "commit") -> str:
    """A pie chart with a legend underneath. `unit` is singular; an 's' is added for counts other than 1."""
    total = sum(counts.values()) or 1
    people = counts.most_common()
    cx, cy, r = 210, 135, 90
    height = 250 + 26 * len(people)
    font = 'font-family="Arial,Helvetica,sans-serif"'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" viewBox="0 0 420 {height}" '
             f'role="img" aria-labelledby="t"><title id="t">{title}</title>',
             f'<rect width="420" height="{height}" rx="12" fill="#ffffff" stroke="#d0d7de"/>',
             f'<text x="210" y="30" text-anchor="middle" {font} font-size="16" font-weight="700" fill="#1f2328">'
             f'{title} ({total:,})</text>']
    angle = 0.0
    for i, (who, n) in enumerate(people):
        color = COLORS[i % len(COLORS)]
        sweep = 2 * math.pi * n / total
        if len(people) == 1:
            parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>')
        else:
            parts.append(f'<path d="{_slice(cx, cy, r, angle, angle + sweep)}" fill="{color}" stroke="#ffffff" '
                         'stroke-width="2"/>')
        angle += sweep
        y = 258 + 26 * i
        word = unit if n == 1 else unit + "s"
        parts.append(f'<rect x="40" y="{y - 12}" width="14" height="14" rx="3" fill="{color}"/>')
        parts.append(f'<text x="64" y="{y}" {font} font-size="14" fill="#1f2328">{who} '
                     f'<tspan fill="#59636e">{100 * n / total:.1f}% · {n:,} {word}</tspan></text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main(argv: list[str]) -> int:
    out_dir, rev = OUT_DIR, "HEAD"
    args = iter(argv)
    for a in args:
        if a == "--out-dir":
            out_dir = Path(next(args))
        elif a == "--rev":
            rev = next(args)
        else:
            print(f"unknown argument {a}", file=sys.stderr)
            return 2
    commits, lines = count(rev)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "contributors.svg").write_text(render(commits), encoding="utf-8")
    (out_dir / "contributors-lines.svg").write_text(render(lines, "Lines of code added", "line"), encoding="utf-8")
    for label, c in (("commits", commits), ("lines", lines)):
        print(label + ": " + ", ".join(f"{k} {v}" for k, v in c.most_common()))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
