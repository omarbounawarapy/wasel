"""The GPU-host script's launch command, checked without a GPU: DRY_RUN prints the docker command it would run."""
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "ops" / "vllm_serve.sh"


def run(*args, **env):
    e = {k: v for k, v in os.environ.items() if k not in ("MODEL", "VLLM_ARGS", "ACCEL", "VLLM_IMAGE", "GROQ_API_KEY")}
    e.update(env, DRY_RUN="1")
    return subprocess.run(["bash", str(SCRIPT), *args], capture_output=True, text=True, env=e, cwd=ROOT, timeout=60)


def test_script_is_valid_bash():
    assert subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True).returncode == 0


def test_rocm_launch_passes_the_devices_and_the_rocm_image():
    out = run("serve", ACCEL="rocm", GROQ_API_KEY="tok").stdout
    assert "--device=/dev/kfd" in out and "--device=/dev/dri" in out
    assert "--group-add video" in out and "--ipc=host" in out
    assert "--gpus all" not in out
    assert "vllm/vllm-openai-rocm:latest" in out
    assert "--model openai/gpt-oss-20b" in out and "--api-key tok" in out


def test_cuda_launch_keeps_the_nvidia_flags():
    out = run("serve", ACCEL="cuda", GROQ_API_KEY="tok").stdout
    assert "--gpus all" in out and "vllm/vllm-openai:latest" in out
    assert "/dev/kfd" not in out


def test_120b_model_is_passed_through():
    out = run("serve", ACCEL="rocm", MODEL="openai/gpt-oss-120b", GROQ_API_KEY="tok").stdout
    assert "--model openai/gpt-oss-120b" in out


def test_vllm_args_and_image_override_are_used():
    out = run("serve", ACCEL="rocm", GROQ_API_KEY="tok", VLLM_ARGS="--max-model-len 16384",
              VLLM_IMAGE="example/vllm:test").stdout
    assert "--max-model-len 16384" in out and "example/vllm:test" in out


def test_unknown_accelerator_is_refused():
    r = run("serve", ACCEL="tpu", GROQ_API_KEY="tok")
    assert r.returncode != 0 and "ACCEL must be auto, rocm or cuda" in r.stderr


def test_dry_run_prints_no_generated_token():
    out = run("serve", ACCEL="rocm").stdout
    assert "fresh API token" not in out and "--api-key" in out and "<token" in out


@pytest.mark.parametrize("bad", ["", "wrong"])
def test_check_fails_clearly_without_a_matching_server(bad):
    r = run("check", GROQ_BASE_URL="http://127.0.0.1:9/v1", GROQ_API_KEY=bad or "tok")
    assert r.returncode != 0
