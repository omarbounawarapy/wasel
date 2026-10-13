#!/usr/bin/env bash
# vllm_serve.sh: run the LLM layer on a self-hosted GPU instead of Groq — the same
# OpenAI-compatible request shape, no provider rate limits or daily cap.
#   preflight  run ON the GPU host: GPU, VRAM, disk, docker, port, token. Changes nothing.
#   serve      run ON the GPU host: start MODEL on :VLLM_PORT (docker, or a venv for NVIDIA)
#   check      run LOCALLY: verify GROQ_BASE_URL lists the model in /v1/models and answers one JSON call
#   stop       run ON the GPU host: tear the server down
# Accelerator: ACCEL=auto (default) picks rocm when /dev/kfd or rocm-smi is present, else cuda. Set ACCEL explicitly
# to override. DRY_RUN=1 prints the docker command that `serve` would run and starts nothing.
# See docs/operations/self-hosted-llm.md and docs/operations/amd-instance.md. Secrets come from the environment / .env
# and are never printed — except a token generated fresh by `serve`, which is shown once so it can be stored.
# Idempotent: `serve` against an already-running server exits 0.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# .env provides defaults, but the caller's environment always wins (so
# `MODEL=openai/gpt-oss-120b bash scripts/ops/vllm_serve.sh serve` works even with a stale .env).
# Values are loaded under a DOTENV_ prefix by scripts/dev/loadenv.py, which parses .env like the app and quotes
# every value, so a `$` or `$(...)` in a value is data and nothing in .env is executed.
if [ -f .env ]; then
  eval "$(python3 scripts/dev/loadenv.py --prefix DOTENV_)"
fi
cfg() { # cfg VAR [default] — caller env > .env > default; echoes the resolved value
  local v="$1" n="DOTENV_$1"
  echo "${!v:-${!n:-${2:-}}}"
}
MODEL="$(cfg MODEL openai/gpt-oss-20b)"  # 120b needs an 80GB card: MODEL=openai/gpt-oss-120b
VLLM_PORT="$(cfg VLLM_PORT 8001)"        # own name on purpose: PORT=8000 in .env is uvicorn's
WAIT_MINS="$(cfg WAIT_MINS 25)"          # first boot pulls weights (~13GB for 20b)
BASE="$(cfg GROQ_BASE_URL)"              # check: e.g. http://<instance-ip>:8001/v1
# The vLLM --api-key value. SELF_HOSTED_API_KEY wins; GROQ_API_KEY is the fallback for older setups, where it is the token.
TOKEN="$(cfg SELF_HOSTED_API_KEY "$(cfg GROQ_API_KEY)")"
CONTAINER="$(cfg CONTAINER vllm)"
ACCEL="$(cfg ACCEL auto)"                # auto | rocm | cuda
VLLM_ARGS="$(cfg VLLM_ARGS)"             # only from caller env or .env; unquoted on purpose
DRY_RUN="${DRY_RUN:-0}"

die() { echo "vllm_serve: $*" >&2; exit 1; }
warn() { echo "vllm_serve: warning: $*" >&2; }

if [ "$ACCEL" = auto ]; then
  if [ -e /dev/kfd ] || command -v rocm-smi >/dev/null 2>&1; then ACCEL=rocm
  else ACCEL=cuda; fi
fi
case "$ACCEL" in
  rocm) DEFAULT_IMAGE=vllm/vllm-openai-rocm:latest ;;
  cuda) DEFAULT_IMAGE=vllm/vllm-openai:latest ;;   # pin older (cu12) on 12.4 drivers: vllm/vllm-openai:v0.10.1
  *) die "ACCEL must be auto, rocm or cuda (got '$ACCEL')" ;;
esac
VLLM_IMAGE="$(cfg VLLM_IMAGE "$DEFAULT_IMAGE")"

models_ok() { curl -sf -m 5 -H "Authorization: Bearer $TOKEN" "$1/models" | grep -q "$MODEL"; }

# GPU access flags for `docker run`. ROCm passes the kernel driver devices through; NVIDIA uses the container toolkit.
gpu_flags() {
  if [ "$ACCEL" = rocm ]; then
    echo "--device=/dev/kfd --device=/dev/dri --group-add video --group-add render --ipc=host --cap-add=SYS_PTRACE --security-opt seccomp=unconfined"
  else
    echo "--gpus all"
  fi
}

# Refuse to start on a host that cannot hold the model: 20b needs 24 GB of VRAM, 120b 80 GB; disk for weights + image.
min_vram_gb() { case "$MODEL" in *120b*) echo 80 ;; *) echo 24 ;; esac; }
min_disk_gb() { case "$MODEL" in *120b*) echo 120 ;; *) echo 40 ;; esac; }

gpu_vram_gb() { # largest single GPU, GB (0 when unknown)
  if [ "$ACCEL" = rocm ] && command -v rocm-smi >/dev/null 2>&1; then
    rocm-smi --showmeminfo vram --csv 2>/dev/null | awk -F, '/^card/ && $2+0>m {m=$2+0} END {printf "%d", m/1073741824}'
  elif command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | sort -n | tail -1 | awk '{printf "%d", $1/1024}'
  else
    echo 0
  fi
}

case "${1:-check}" in
  preflight)
    fail=0
    echo "accelerator: $ACCEL   image: $VLLM_IMAGE   model: $MODEL"
    if [ "$ACCEL" = rocm ]; then
      rocm-smi --showproductname 2>/dev/null | grep -E "Card series|Card model" | head -2 || true
    else
      nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -2 || true
    fi
    VRAM=$(gpu_vram_gb)
    if [ "$VRAM" -ge "$(min_vram_gb)" ]; then echo "  OK: $VRAM GB VRAM (need $(min_vram_gb))"
    else echo "  FAIL: VRAM ${VRAM} GB, need $(min_vram_gb) GB for $MODEL"; fail=1; fi
    FREE=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc 0-9)
    if [ "$FREE" -ge "$(min_disk_gb)" ]; then echo "  OK: ${FREE} GB free in \$HOME (need $(min_disk_gb))"
    else echo "  FAIL: ${FREE} GB free in \$HOME, need $(min_disk_gb)"; fail=1; fi
    if command -v docker >/dev/null && docker info >/dev/null 2>&1; then echo "  OK: docker reachable"
    elif command -v docker >/dev/null; then echo "  FAIL: docker installed but this user cannot use it (docker group?)"; fail=1
    else echo "  FAIL: docker not installed (the ROCm path needs it)"; fail=1; fi
    if [ "$ACCEL" = rocm ] && docker info >/dev/null 2>&1; then
      docker image inspect "$VLLM_IMAGE" >/dev/null 2>&1 && echo "  OK: image already pulled" || echo "  note: image not pulled yet (serve pulls it, several GB)"
    fi
    if ss -ltn 2>/dev/null | grep -q ":$VLLM_PORT "; then echo "  FAIL: port $VLLM_PORT already in use"; fail=1
    else echo "  OK: port $VLLM_PORT free"; fi
    if [ -n "$TOKEN" ]; then echo "  OK: vLLM token set (SELF_HOSTED_API_KEY, or GROQ_API_KEY on older setups)"
    else echo "  note: no GROQ_API_KEY; serve will generate one and print it once"; fi
    [ "$fail" = 0 ] && echo "preflight passed" || { echo "preflight FAILED"; exit 1; }
    ;;

  serve)
    command -v curl >/dev/null || die "curl is required on the GPU host"
    if [ -z "$TOKEN" ] && [ "$DRY_RUN" = 1 ]; then TOKEN="<token>"; fi
    if [ -z "$TOKEN" ]; then
      TOKEN="$(openssl rand -hex 24 2>/dev/null || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
      echo "generated a fresh API token — store it in the laptop .env now, it is shown only here:"
      echo "  $TOKEN"
      echo
    fi
    if models_ok "http://localhost:$VLLM_PORT/v1"; then echo "already serving $MODEL on :$VLLM_PORT"; exit 0; fi

    # VLLM_ARGS is intentionally unquoted (multiple flags), e.g. for 120b on 80GB:
    #   VLLM_ARGS="--gpu-memory-utilization 0.95 --max-model-len 16384"
    if command -v docker >/dev/null; then
      # shellcheck disable=SC2046  # gpu_flags is a word list on purpose
      RUN=(docker run -d --name "$CONTAINER" --restart unless-stopped $(gpu_flags)
           -p "$VLLM_PORT:8000" -v "$HOME/.cache/huggingface:/root/.cache/huggingface"
           "$VLLM_IMAGE" --model "$MODEL" --api-key "$TOKEN" ${VLLM_ARGS:-})
      if [ "$DRY_RUN" = 1 ]; then
        printf '%q ' "${RUN[@]}"; echo
        exit 0
      fi
      docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
      docker pull "$VLLM_IMAGE" >/dev/null || warn "docker pull failed; starting with a local copy if there is one"
      "${RUN[@]}" >/dev/null
      echo "docker container '$CONTAINER' up ($VLLM_IMAGE, $ACCEL)"
    else
      [ "$ACCEL" = cuda ] || die "ACCEL=rocm needs docker (the ROCm vLLM build ships as a container); install docker first"
      command -v python3 >/dev/null || die "need docker or python3 on the GPU host"
      VENV="$HOME/vllm-venv"
      [ -x "$VENV/bin/vllm" ] || {
        echo "installing vLLM into $VENV (a few minutes)…"
        python3 -m venv "$VENV"
        "$VENV/bin/pip" install -q -U vllm
      }
      nohup "$VENV/bin/vllm" serve "$MODEL" --port "$VLLM_PORT" --api-key "$TOKEN" ${VLLM_ARGS:-} \
        >"$HOME/vllm.log" 2>&1 &
      echo $! >"$HOME/vllm.pid"
      echo "vLLM starting in the background (pid $(cat "$HOME/vllm.pid"), log ~/vllm.log)"
    fi

    echo "waiting for $MODEL (first boot downloads weights)…"
    for _ in $(seq 1 $((WAIT_MINS * 6))); do
      models_ok "http://localhost:$VLLM_PORT/v1" && break
      sleep 10
    done
    if ! models_ok "http://localhost:$VLLM_PORT/v1"; then
      echo "not serving after ${WAIT_MINS}min — last log lines:" >&2
      docker logs --tail 20 "$CONTAINER" 2>/dev/null || tail -20 "$HOME/vllm.log" >&2 || true
      exit 1
    fi
    echo "serving $MODEL on :$VLLM_PORT"
    echo
    echo "paste into the client .env:"
    echo "  GROQ_BASE_URL=http://<gpu-host-address>:$VLLM_PORT/v1"
    echo "  SELF_HOSTED_API_KEY=<the token you set>   # keep GROQ_API_KEY as your hosted Groq key"
    echo "  EXTRACT_MODEL=$MODEL"
    echo "  FALLBACK_MODEL=$MODEL   # or GROQ_FALLBACK_ENABLED=false: single-model backend"
    echo "  GROQ_FALLBACK_ENABLED=false   # one model is served here; the hosted backup uses GROQ_API_KEY"
    ;;

  check)
    [ -n "$BASE" ] || die "GROQ_BASE_URL is empty (.env) — nothing to check"
    [ -n "$TOKEN" ] || die "GROQ_API_KEY is empty (.env) — the vLLM --api-key value"
    models_ok "$BASE" || die "$BASE/models did not list $MODEL (server up? token right?)"
    echo "  OK: $MODEL listed in $BASE/models"
    BODY=$(printf '{"model":"%s","messages":[{"role":"user","content":"Return only JSON: {\\"ok\\": true}"}],"temperature":0,"max_completion_tokens":512}' "$MODEL")
    T0=$(date +%s%3N)
    RESP=$(curl -sf -m "${CHECK_TIMEOUT_S:-60}" -H "Authorization: Bearer $TOKEN" \
                 -H "Content-Type: application/json" -d "$BODY" "$BASE/chat/completions") \
      || die "chat/completions failed"
    T1=$(date +%s%3N)
    # gpt-oss reasoning models may return the answer in content after an analysis
    # channel (reasoning_content); 512 tokens leaves room for both.
    echo "$RESP" | python3 -c 'import json,sys; m=json.load(sys.stdin)["choices"][0]["message"]; c=m.get("content") or m.get("reasoning_content") or ""; print("  OK: completion:", (c[:80].replace("\n", " ")) or "(empty)")'
    echo "  round-trip $((T1 - T0)) ms"
    echo "self-hosted endpoint check passed"
    ;;

  stop)
    if docker rm -f "$CONTAINER" >/dev/null 2>&1; then
      echo "docker container '$CONTAINER' removed"
    elif [ -f "$HOME/vllm.pid" ]; then
      kill "$(cat "$HOME/vllm.pid")" 2>/dev/null || true
      rm -f "$HOME/vllm.pid"
      echo "vLLM process stopped"
    else
      echo "nothing to stop (no container, no pidfile)"
    fi
    echo "remember to stop or delete the GPU instance itself if it is billed by the hour"
    ;;

  *)
    die "usage: vllm_serve.sh preflight|serve|check|stop"
    ;;
esac
