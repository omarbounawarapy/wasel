"""Each hashed lock (`make lock`) must agree with the pins it is generated from and must hash every package, so the
dev setup, the audit and the container images install exactly what was reviewed. Offline: no network, no uv."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
IMAGE = ROOT / "deploy" / "render"
# lock file -> the requirement files it was compiled from
LOCKS = {
    ROOT / "requirements.lock": [ROOT / "requirements.txt", ROOT / "requirements-dev.txt", ROOT / "dashboard" / "requirements.txt"],
    IMAGE / "requirements.lock": [IMAGE / "requirements.txt"],
}


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


def _locked(lock: Path) -> tuple[dict[str, str], dict[str, bool]]:
    versions, hashed = {}, {}
    current = None
    for line in lock.read_text().splitlines():
        if not line.startswith((" ", "#")) and "==" in line:
            name, _, rest = line.partition("==")
            current = _name(name)
            versions[current] = rest.split()[0].rstrip("\\").strip()
            hashed[current] = False
        elif current and "--hash=" in line:
            hashed[current] = True
    return versions, hashed


@pytest.mark.parametrize("lock", list(LOCKS), ids=lambda p: str(p.relative_to(ROOT)))
def test_lock_matches_the_source_pins(lock):
    pins = {}
    for source in LOCKS[lock]:
        pins.update(_pins(source))
    versions, _ = _locked(lock)
    for name, version in pins.items():
        assert versions.get(name) == version, f"{name}: lock has {versions.get(name)}, source pins {version}"


@pytest.mark.parametrize("lock", list(LOCKS), ids=lambda p: str(p.relative_to(ROOT)))
def test_every_locked_package_has_a_hash(lock):
    _, hashed = _locked(lock)
    assert hashed, "no packages found in the lock"
    missing = sorted(name for name, ok in hashed.items() if not ok)
    assert missing == [], f"packages without --hash: {missing}"
