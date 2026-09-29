"""Prompt + schema + limits loading from the LLM registry (config/llm.yaml). The app refuses to start if a
prompt file's sha256 doesn't match config/prompts/VERSIONS, so a prompt can't change silently without a version bump.
Which version each role runs is one line in config/llm.yaml, so a rollback is one edit."""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path

import yaml

from wasel.llm.base import TaskSpec
from wasel.paths import ROOT

REGISTRY = Path(os.environ.get("LLM_REGISTRY", ROOT / "config" / "llm.yaml"))


class PromptVersionMismatch(RuntimeError):
    pass


def check_versions(root: Path = ROOT) -> dict[str, str]:
    """{file: version}; raises if any listed file's sha differs."""
    out = {}
    for line in (root / "config" / "prompts" / "VERSIONS").read_text().splitlines():
        if not line.strip():
            continue
        version, sha, fname = line.split()
        actual = hashlib.sha256((root / "config" / "prompts" / fname).read_bytes()).hexdigest()
        if actual != sha:
            raise PromptVersionMismatch(f"config/prompts/{fname} changed without a version bump "
                                        f"({version}: expected {sha[:12]}, got {actual[:12]})")
        out[fname] = version
    return out


@lru_cache(maxsize=4)
def registry(path: Path = REGISTRY) -> dict:
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    locked = check_versions(ROOT)
    for role, r in reg["roles"].items():
        if r["active"] not in r["versions"]:
            raise PromptVersionMismatch(f"config/llm.yaml: {role}.active={r['active']} is not a listed version")
        for v, spec in r["versions"].items():
            for f in (spec["system"], spec.get("fewshot")):
                if f and locked.get(f) != v:
                    raise PromptVersionMismatch(f"config/prompts/{f} is not locked as {v} in config/prompts/VERSIONS")
    return reg


def active_version(role: str) -> str:
    if role == "extract" and os.environ.get("PROMPT_VERSION"):
        return os.environ["PROMPT_VERSION"]
    return registry()["roles"][role]["active"]


def active_versions() -> dict[str, str]:
    return {role: active_version(role) for role in registry()["roles"]}


@lru_cache(maxsize=8)
def task(role: str, version: str | None = None, root: Path = ROOT) -> TaskSpec:
    r = registry()["roles"][role]
    version = version or active_version(role)
    spec, lim = r["versions"][version], r["limits"]
    prompts_dir, schemas_dir = root / "config" / "prompts", root / "config" / "schemas"
    shots: tuple = ()
    if spec.get("fewshot"):
        shots = tuple((d["user"], d["assistant"]) for d in
                      (json.loads(line) for line in
                       (prompts_dir / spec["fewshot"]).read_text(encoding="utf-8").splitlines() if line.strip()))
    return TaskSpec(name=role, schema_name=spec["schema"], prompt_version=version, few_shot=shots,
                    system_prompt=(prompts_dir / spec["system"]).read_text(encoding="utf-8"),
                    schema=json.loads((schemas_dir / f"{spec['schema']}.json").read_text(encoding="utf-8")),
                    max_output_tokens=lim["max_output_tokens"], temperature=lim["temperature"],
                    max_input_chars=lim.get("max_input_chars"), cache=bool(r.get("cache")))


PROMPT_VERSION = active_version("extract")


def extraction_task(root: Path = ROOT) -> TaskSpec:
    return task("extract", PROMPT_VERSION, root)


def rewrite_task(root: Path = ROOT) -> TaskSpec:
    """No customer text in the user turn."""
    return task("rewrite", root=root)


def judge_task(root: Path = ROOT) -> TaskSpec:
    return task("judge", root=root)
