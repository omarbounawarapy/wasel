"""python scripts/ops/cf_check.py: offline consistency checks for the Cloudflare deployment files (no account, no
network, no Docker). Exit 1 and one line per problem. `make cf-check` runs it; tests/unit/test_cloudflare_config.py
runs the same `problems()`.

Checks: wrangler.jsonc environments are complete and isolated, no secret name or key-shaped value in `vars`,
deploy/cloudflare/container-env.json only names variables .env.example documents, the Worker's backend paths match
`assets.run_worker_first`, the container's pinned requirements match /requirements.txt, and web/public/_headers
matches the security headers FastAPI sets.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CF = ROOT / "deploy" / "cloudflare"
WORKER_ONLY_VARS = {"CONTAINER_SLEEP_AFTER"}          # read by the Worker, not passed to the container
KEY_SHAPED = re.compile(r"gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|EAA[A-Za-z0-9]{50,}|eyJhIjoi[A-Za-z0-9+/=_-]{40,}")
SEEN = ("assets", "durable_objects", "exports", "containers", "r2_buckets", "vars")   # not inherited by wrangler envs


def _pins(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        m = re.match(r"^([A-Za-z0-9_.\[\]-]+)==([^\s#]+)", line)
        if m:
            out[m.group(1).lower()] = m.group(2)
    return out


def problems() -> list[str]:
    out: list[str] = []
    cfg = json.loads((CF / "wrangler.jsonc").read_text())
    ce = json.loads((CF / "container-env.json").read_text())
    envs = {"(dev)": cfg, **{f"env.{k}": {**v} for k, v in cfg.get("env", {}).items()}}
    documented = set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", (ROOT / ".env.example").read_text(), re.M))

    for n in ce["vars"] + ce["secrets"]:
        if n not in documented:
            out.append(f"container-env.json: {n} is not documented in .env.example")
    if set(ce["vars"]) & set(ce["secrets"]):
        out.append("container-env.json: a name is both a var and a secret")

    names, buckets = set(), set()
    for label, e in envs.items():
        for k in SEEN:
            if k not in e:
                out.append(f"wrangler.jsonc {label}: missing {k} (wrangler does not inherit it into an environment)")
        names.add(e.get("name"))
        buckets.update(b["bucket_name"] for b in e.get("r2_buckets", []))
        for k, v in e.get("vars", {}).items():
            if k in ce["secrets"] or re.search(r"TOKEN|SECRET|API_KEY|PASSWORD", k):
                out.append(f"wrangler.jsonc {label}: secret-looking name {k} in vars (use `wrangler secret put`)")
            if not isinstance(v, str) or KEY_SHAPED.search(v):
                out.append(f"wrangler.jsonc {label}: vars.{k} must be a plain non-secret string")
            if k not in ce["vars"] and k not in WORKER_ONLY_VARS:
                out.append(f"wrangler.jsonc {label}: vars.{k} is not in container-env.json (container would not see it)")
        if e.get("vars", {}).get("APP_MODE") not in ("dev", "event", "public"):
            out.append(f"wrangler.jsonc {label}: vars.APP_MODE must be dev, event or public")
        if e.get("vars", {}).get("SNAPSHOT_URL", "").split("/")[2:3] != ["state.wasel.internal"]:
            out.append(f"wrangler.jsonc {label}: vars.SNAPSHOT_URL must point at state.wasel.internal (the R2 handler)")
        if [c.get("max_instances") for c in e.get("containers", [])] != [1]:
            out.append(f"wrangler.jsonc {label}: containers[0].max_instances must be 1 (one SQLite file, one worker loop)")
        if "STATE" not in {b["binding"] for b in e.get("r2_buckets", [])}:
            out.append(f"wrangler.jsonc {label}: needs an r2_buckets binding named STATE")
        paths = e.get("assets", {}).get("run_worker_first")
        src = (CF / "worker/src/index.ts").read_text()
        m = re.search(r"BACKEND_PATHS = \[(.*?)\]", src)
        want = sorted(p.strip('"') for p in re.findall(r'"[^"]+"', m.group(1))) if m else []
        got = sorted(p.rstrip("*").rstrip("/") + ("/" if p.endswith("/*") else "") for p in paths or [])
        if want != got:
            out.append(f"wrangler.jsonc {label}: assets.run_worker_first {paths} != BACKEND_PATHS in index.ts")
    if len(names) != len(envs):
        out.append("wrangler.jsonc: environments must have distinct worker names")
    if len(buckets) != len(envs):
        out.append("wrangler.jsonc: environments must not share an R2 bucket")

    base, run = _pins(ROOT / "requirements.txt"), _pins(CF / "container" / "requirements.txt")
    for name, ver in run.items():
        key = "xgboost" if name == "xgboost-cpu" else name
        if base.get(key) != ver:
            out.append(f"container requirements: {name}=={ver} differs from requirements.txt ({base.get(key)})")
    if "pandas" in run:
        out.append("container requirements: pandas is training-only")

    sys.path.insert(0, str(ROOT / "src"))
    from wasel.main import SECURITY_HEADERS
    headers_file = (ROOT / "web/public/_headers").read_text()
    hdr = {k.strip(): v.strip() for k, v in re.findall(r"^\s+([A-Za-z-]+): (.*)$", headers_file, re.M)}
    if hdr != SECURITY_HEADERS:
        out.append("web/public/_headers differs from SECURITY_HEADERS in src/wasel/main.py")
    return out


if __name__ == "__main__":
    bad = problems()
    print("\n".join(bad) if bad else "cf-check: ok")
    sys.exit(1 if bad else 0)
