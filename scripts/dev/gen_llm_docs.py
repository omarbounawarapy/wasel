"""Rewrite the generated endpoint and route tables in docs/subsystems/llm.md from config/llm.yaml.

Run `python scripts/dev/gen_llm_docs.py` after editing endpoints or routes. tests/unit/test_llm_docs.py fails when
the page and the config disagree.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from wasel.llm.prompts import registry
from wasel.llm.routes import ROLE_ROUTES, docs_tables, parse_endpoints, parse_route

PAGE = Path(__file__).resolve().parents[2] / "docs" / "subsystems" / "llm.md"
BEGIN, END = "<!-- BEGIN GENERATED: llm-endpoints -->", "<!-- END GENERATED: llm-endpoints -->"


def generated(reg: dict | None = None) -> str:
    reg = reg or registry()
    eps = parse_endpoints(reg.get("endpoints"))
    routes = {role: parse_route(role, reg["routes"][role], eps) for role in ROLE_ROUTES
              if role in (reg.get("routes") or {})}
    return docs_tables(eps, routes)


def current(text: str) -> str | None:
    m = re.search(re.escape(BEGIN) + r"\n(.*?)\n" + re.escape(END), text, re.S)
    return m.group(1) if m else None


def main() -> int:
    text = PAGE.read_text(encoding="utf-8")
    if current(text) is None:
        print(f"{PAGE}: markers not found", file=sys.stderr)
        return 1
    new = re.sub(re.escape(BEGIN) + r"\n.*?\n" + re.escape(END), lambda _: f"{BEGIN}\n{generated()}\n{END}", text,
                 flags=re.S)
    PAGE.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
