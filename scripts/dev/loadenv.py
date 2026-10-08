"""Print the entries of .env as shell `export` lines whose values are quoted, to be used as `eval "$(python loadenv.py)"`.

The app reads .env with python-dotenv; sourcing the file in a shell gave `$name`, backticks and `$(...)` a second
meaning and ran them. This script parses the file the same way the app does (python-dotenv when installed, a
small strict parser otherwise) and quotes every value, so nothing in .env is ever evaluated by a shell.

usage: loadenv.py [--prefix P] [--file PATH]   (P is put in front of every name; default none)
"""
from __future__ import annotations

import re
import shlex
import sys
from pathlib import Path

NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def parse(path: Path) -> dict[str, str]:
    """The NAME=value pairs of `path`; an empty dict when the file does not exist."""
    if not path.is_file():
        return {}
    try:
        from dotenv import dotenv_values
    except ImportError:
        return _fallback(path.read_text(encoding="utf-8"))
    return {k: v for k, v in dotenv_values(path).items() if v is not None}


def _fallback(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_.-]*)\s*=\s*(.*)$", line)
        if not m:
            continue
        v = m.group(2).strip()
        if v[:1] in ("'", '"') and v.count(v[0]) >= 2:
            v = v[1:v.index(v[0], 1)]
        else:
            v = re.split(r"\s+#", v, maxsplit=1)[0].strip()
        out[m.group(1)] = v
    return out


def main(argv: list[str]) -> int:
    prefix, path = "", Path(".env")
    args = iter(argv)
    for a in args:
        if a == "--prefix":
            prefix = next(args, "")
        elif a == "--file":
            path = Path(next(args, ".env"))
        else:
            print(f"loadenv: unknown argument {a}", file=sys.stderr)
            return 2
    for name, value in parse(path).items():
        if NAME.fullmatch(name):                       # a name that is not a shell identifier cannot be exported
            print(f"export {prefix}{name}={shlex.quote(value)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
