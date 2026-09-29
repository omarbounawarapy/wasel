"""python scripts/ops/cf_local_smoke.py: run the Cloudflare container image locally (docker or podman, no Cloudflare
account) and check what only the image can show: it boots keyless and non-root, passes the standard smoke test, keeps
its state across a wiped disk through SNAPSHOT_URL, and refuses to start on a corrupt snapshot.

The snapshot store here is a mounted directory (file://); on Cloudflare it is R2 behind the Worker. Set
CONTAINER_BIN=podman to override the engine, PORT to move off 8000. `make cf-smoke` runs this.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
BIN = os.environ.get("CONTAINER_BIN") or shutil.which("docker") or shutil.which("podman") or "docker"
PORT = os.environ.get("PORT", "8000")
IMAGE = "wasel-cf-smoke"
NAME = "wasel-cf-smoke"
URL = f"http://127.0.0.1:{PORT}"


def sh(*args, check=True, **kw):
    return subprocess.run([BIN, *args], check=check, capture_output=True, text=True, **kw)


def in_snap(snap: Path, script: str) -> str:
    """Run a shell snippet as the container's user with the snapshot dir mounted (its files belong to that user)."""
    return sh("run", "--rm", "-v", f"{snap}:/snap:z", "--entrypoint", "sh", IMAGE, "-c", script).stdout


def step(name, ok, detail=""):
    print(f"{'ok ' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        sys.exit(1)


def start(snap: Path, **env):
    sh("rm", "-f", NAME, check=False)
    args = ["run", "-d", "--rm", "--name", NAME, "-p", f"127.0.0.1:{PORT}:8000", "-v", f"{snap}:/snap:z",
            "-e", "APP_MODE=public", "-e", "SEED_ON_BOOT=if_empty", "-e", "SNAPSHOT_URL=file:///snap/wasel.sqlite",
            "-e", "SNAPSHOT_INTERVAL_S=1", "-e", "LLM_MODE=live", "-e", "GROQ_API_KEY="]
    for k, v in env.items():
        args += ["-e", f"{k}={v}"]
    sh(*args, IMAGE)


def wait_health(timeout=60) -> dict | None:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            r = httpx.get(f"{URL}/api/health", timeout=2)
            if r.status_code == 200:
                return r.json()
        except httpx.HTTPError:
            pass
        if sh("ps", "-q", "--filter", f"name={NAME}").stdout.strip() == "":
            return None                                             # the container exited
        time.sleep(0.5)
    return None


def main() -> int:
    snap = Path(tempfile.mkdtemp(prefix="wasel-snap-"))
    snap.chmod(0o777)                                               # the container runs as uid 10001
    try:
        sh("build", "--platform", "linux/amd64", "-t", IMAGE, "-f", "deploy/cloudflare/container/Dockerfile", ".",
           cwd=ROOT)
        step("image builds", True)
        start(snap)
        h = wait_health()
        step("boots keyless", h is not None and h["mode"] == "public" and not h["wa_send"], f"{h and h['status']}")
        step("runs as non-root", sh("exec", NAME, "id", "-u").stdout.strip() == "10001")
        r = subprocess.run([sys.executable, str(ROOT / "scripts/ops/smoke.py"), URL], capture_output=True, text=True)
        step("standard smoke test passes", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr)
        sandboxes = wait_health()["sandbox_orders"]
        step("smoke left sandbox orders", sandboxes > 0, str(sandboxes))
        time.sleep(2)
        sh("stop", "-t", "20", NAME)
        step("snapshot written on shutdown", int(in_snap(snap, "wc -c < /snap/wasel.sqlite")) > 0)
        start(snap)                                                 # a brand-new container disk
        h2 = wait_health()
        step("state survives a fresh disk", h2 is not None and h2["sandbox_orders"] == sandboxes,
             f"{h2 and h2['sandbox_orders']} orders")
        sh("stop", "-t", "20", NAME)
        in_snap(snap, "printf corrupt > /snap/wasel.sqlite")
        start(snap)
        step("corrupt snapshot refuses to boot", wait_health(20) is None)
        step("corrupt snapshot is left untouched", in_snap(snap, "cat /snap/wasel.sqlite") == "corrupt")
        print("CF LOCAL SMOKE PASS")
        return 0
    finally:
        sh("rm", "-f", NAME, check=False)
        sh("run", "--rm", "-v", f"{snap}:/snap:z", "--entrypoint", "sh", IMAGE, "-c", "rm -rf /snap/*", check=False)
        shutil.rmtree(snap, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
