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


def _stub_bin(tmp_path, name, body):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    f = bindir / name
    f.write_text("#!/bin/sh\n" + body + "\n")
    f.chmod(0o755)
    return bindir


def _label(tmp_path, accel, smi, output):
    """The label function alone, sourced with a stub GPU tool first on PATH."""
    bindir = _stub_bin(tmp_path, smi, f"cat <<'EOF'\n{output}\nEOF")
    src = SCRIPT.read_text().split('case "${1:-check}" in', 1)[0]
    r = subprocess.run(["bash", "-c", src + "\nserving_label"], capture_output=True, text=True, timeout=60,
                       env={"PATH": f"{bindir}:/usr/bin:/bin", "ACCEL": accel, "HOME": str(tmp_path)})
    return r.stdout.strip()


def test_serving_label_comes_from_the_rocm_report(tmp_path):
    out = "GPU[0]\t\t: Card Series:\t\tAMD Instinct MI300X OAM\nGPU[0]\t\t: Card Model:\t\t0x74a1"
    # real rocm-smi prints "Card Series:" with the value after the colon
    assert _label(tmp_path, "rocm", "rocm-smi", out) == "AMD Instinct MI300X OAM, ROCm, vLLM"


def test_serving_label_is_empty_when_the_host_reports_no_gpu(tmp_path):
    assert _label(tmp_path, "rocm", "rocm-smi", "no devices") == ""
