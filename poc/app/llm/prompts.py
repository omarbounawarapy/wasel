"""Prompt + schema loading. The app refuses to start if a prompt file's sha256 doesn't match
prompts/VERSIONS, so a prompt can't change silently without a version bump (02 §2)."""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

from app.llm.base import TaskSpec

ROOT = Path(__file__).resolve().parents[2]
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "extract-v1")


class PromptVersionMismatch(RuntimeError):
    pass


def check_versions(root: Path = ROOT) -> dict[str, str]:
    """{file: version}; raises if any listed file's sha differs."""
    out = {}
    for line in (root / "prompts" / "VERSIONS").read_text().splitlines():
        if not line.strip():
            continue
        version, sha, fname = line.split()
        actual = hashlib.sha256((root / "prompts" / fname).read_bytes()).hexdigest()
        if actual != sha:
            raise PromptVersionMismatch(f"prompts/{fname} changed without a version bump "
                                        f"({version}: expected {sha[:12]}, got {actual[:12]})")
        out[fname] = version
    return out


@lru_cache(maxsize=2)
def extraction_task(root: Path = ROOT) -> TaskSpec:
    check_versions(root)
    system = (root / "prompts" / "extract_v1.system.txt").read_text(encoding="utf-8")
    shots = tuple((d["user"], d["assistant"]) for d in
                  (json.loads(line) for line in
                   (root / "prompts" / "extract_v1.fewshot.jsonl").read_text(encoding="utf-8").splitlines()
                   if line.strip()))
    schema = json.loads((root / "schemas" / "order_extraction_v1.json").read_text(encoding="utf-8"))
    return TaskSpec(name="extract", schema_name="order_extraction_v1", schema=schema, system_prompt=system,
                    few_shot=shots, prompt_version=PROMPT_VERSION, max_output_tokens=1024, temperature=0.0)
