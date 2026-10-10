"""The container lock (deploy/cloudflare/container/requirements.lock, `make lock`) must agree with the pins it is generated
from and must hash every package, so both images install exactly what was reviewed. Offline: no network, no uv."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTAINER = ROOT / "deploy" / "cloudflare" / "container"


def _name(raw: str) -> str:
    return re.sub(r"[-_.]+", "-", raw.split("[")[0]).lower()


def _pins(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name, _, version = line.partition("==")
        out[_name(name)] = version.strip()
    return out


def _locked() -> tuple[dict[str, str], dict[str, bool]]:
    versions, hashed = {}, {}
    current = None
    for line in (CONTAINER / "requirements.lock").read_text().splitlines():
        if not line.startswith((" ", "#")) and "==" in line:
            name, _, rest = line.partition("==")
            current = _name(name)
            versions[current] = rest.split()[0].rstrip("\\").strip()
            hashed[current] = False
        elif current and "--hash=" in line:
            hashed[current] = True
    return versions, hashed


def test_lock_matches_the_source_pins():
    pins = _pins(CONTAINER / "requirements.txt")
    versions, _ = _locked()
    for name, version in pins.items():
        assert versions.get(name) == version, f"{name}: lock has {versions.get(name)}, requirements.txt pins {version}"


def test_every_locked_package_has_a_hash():
    _, hashed = _locked()
    assert hashed, "no packages found in the lock"
    missing = sorted(name for name, ok in hashed.items() if not ok)
    assert missing == [], f"packages without --hash: {missing}"
