"""scripts/dev/hygiene.sh fails on the secret shapes this project handles."""
import subprocess

import pytest

from wasel.paths import ROOT

SCRIPT = ROOT / "scripts" / "dev" / "hygiene.sh"

# built at run time so this file never contains a secret-shaped literal itself
SECRETS = {
    "github token": "TOKEN_FILE = 'g" + "hp_" + "a1" * 20 + "'",
    "private key": "-----" + "BEGIN PRIVATE" + " KEY-----",
    "aws key id": "id = AK" + "IA" + "ABCDEFGHIJKLMNOP",
    "whatsapp secret": "WA_APP_SECRET = '" + "0123456789abcdef" * 2 + "'",
    "admin token": "ADMIN_TOKEN=" + "Zx9" * 12,
    "slack token": "x = xox" + "b-1234567890-abcdef",
}


def _repo(tmp_path, text):
    run = lambda *a: subprocess.run(a, cwd=tmp_path, check=True, capture_output=True)  # noqa: E731
    run("git", "init", "-q")
    (tmp_path / "config.txt").write_text(text + "\n", encoding="utf-8")
    run("git", "add", "config.txt")
    return subprocess.run(["bash", str(SCRIPT)], cwd=tmp_path, capture_output=True, text=True)


@pytest.mark.parametrize("kind", SECRETS)
def test_secret_shapes_fail(tmp_path, kind):
    r = _repo(tmp_path, SECRETS[kind])
    assert r.returncode == 1 and "hygiene:" in r.stderr, r.stderr


def test_a_clean_file_passes(tmp_path):
    assert _repo(tmp_path, "ADMIN_TOKEN=\nWA_TOKEN=changeme\nnote = 'a token is needed here'").returncode == 0


def test_the_real_tree_passes():
    r = subprocess.run(["bash", str(SCRIPT)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
