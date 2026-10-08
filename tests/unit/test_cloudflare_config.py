"""Offline guards for the Cloudflare deployment files (scripts/ops/cf_check.py) and for what the container image
leaves out. No Cloudflare account, Docker or network."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cf_check", ROOT / "scripts" / "ops" / "cf_check.py")
cf_check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf_check)


def test_deployment_files_are_consistent():
    assert cf_check.problems() == []


@pytest.fixture
def tmp_cf(tmp_path, monkeypatch):
    d = tmp_path / "cf"
    shutil.copytree(ROOT / "deploy" / "cloudflare", d, ignore=shutil.ignore_patterns("node_modules", ".wrangler"))
    monkeypatch.setattr(cf_check, "CF", d)
    return d


def _edit(d, fn):
    p = d / "wrangler.jsonc"
    cfg = json.loads(p.read_text())
    fn(cfg)
    p.write_text(json.dumps(cfg))


def test_a_secret_in_vars_is_caught(tmp_cf):
    _edit(tmp_cf, lambda c: c["env"]["production"]["vars"].update(GROQ_API_KEY="x"))
    assert any("secret-looking name GROQ_API_KEY" in p for p in cf_check.problems())


def test_a_key_shaped_value_is_caught(tmp_cf):
    _edit(tmp_cf, lambda c: c["vars"].update(EXTRACT_MODEL="gsk_" + "a" * 30))
    assert any("plain non-secret string" in p for p in cf_check.problems())


def test_var_the_container_would_not_see_is_caught(tmp_cf):
    _edit(tmp_cf, lambda c: c["env"]["preview"]["vars"].update(NEW_THING="1"))
    assert any("NEW_THING is not in container-env.json" in p or "vars.NEW_THING" in p for p in cf_check.problems())


def test_shared_bucket_and_missing_env_keys_are_caught(tmp_cf):
    def f(c):
        c["env"]["preview"]["r2_buckets"][0]["bucket_name"] = c["env"]["production"]["r2_buckets"][0]["bucket_name"]
        del c["env"]["preview"]["containers"]
    _edit(tmp_cf, f)
    got = " | ".join(cf_check.problems())
    assert "must not share an R2 bucket" in got and "preview: missing containers" in got


def test_more_than_one_container_instance_is_caught(tmp_cf):
    _edit(tmp_cf, lambda c: c["containers"][0].update(max_instances=2))
    assert any("max_instances must be 1" in p for p in cf_check.problems())


def test_runtime_modules_never_import_pandas(tmp_path):
    """The container image has no pandas: the API must boot and answer with `import pandas` failing."""
    code = "\n".join([
        "import sys",
        "sys.modules['pandas'] = None      # any import of it now raises ImportError",
        "import wasel.monitor, wasel.outbound.guard_clf, wasel.failures.run, wasel.failures.adapter",
        "from fastapi.testclient import TestClient",
        "from wasel.main import create_app",
        "from wasel.settings import Settings",
        "app = create_app(Settings(app_mode='dev', db_path=sys.argv[1], worker_enabled=False, llm_mode='fail_all', allowed_hosts='testserver'))",
        "with TestClient(app) as c:",
        "    assert c.get('/api/health').json()['status'] in ('ok', 'degraded')",
        "    assert c.get('/api/failures').status_code == 200",
    ])
    r = subprocess.run([sys.executable, "-c", code, str(tmp_path / "a.db")], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
