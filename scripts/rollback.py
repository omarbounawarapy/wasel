"""One-step rollback of an LLM role: `python -m scripts.rollback judge judge-v1` rewrites that role's `active`
line in config/llm.yaml (nothing else). Commit + deploy as usual; `make eval` gates the result."""
from __future__ import annotations

import re
import sys

import yaml

from app.llm.prompts import REGISTRY


def rollback(role: str, version: str) -> str:
    text = REGISTRY.read_text(encoding="utf-8")
    reg = yaml.safe_load(text)
    if role not in reg["roles"] or version not in reg["roles"][role]["versions"]:
        raise SystemExit(f"unknown role/version {role}/{version}")
    block = re.search(rf"^  {role}:\n(    .*\n)+", text, re.M)
    new_block = re.sub(r"^    active: \S+", f"    active: {version}", block.group(0), count=1, flags=re.M)
    REGISTRY.write_text(text.replace(block.group(0), new_block), encoding="utf-8")
    return f"{role}: {reg['roles'][role]['active']} -> {version}"


if __name__ == "__main__":
    print(rollback(*sys.argv[1:3]))
