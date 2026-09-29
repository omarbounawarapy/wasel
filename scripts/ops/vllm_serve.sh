#!/usr/bin/env bash
# vllm_serve.sh: run the LLM layer on a self-hosted GPU instead of Groq — the same
# OpenAI-compatible request shape, no provider rate limits or daily cap.
#   serve  run ON the GPU host: install vLLM (docker if present, else pip) and serve MODEL on :VLLM_PORT
#   check  run LOCALLY: verify GROQ_BASE_URL lists the model in /v1/models and answers one JSON call
#   stop   run ON the GPU host: tear the server down
# See docs/self-hosted-llm.md. Secrets come from the environment / .env and are never printed —
# except a token generated fresh by `serve`, which is shown once so it can be stored.
# Idempotent: `serve` against an already-running server exits 0.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

# .env provides defaults, but the caller's environment always wins (so
# `MODEL=openai/gpt-oss-120b bash scripts/ops/vllm_serve.sh serve` works even with a stale .env).
# Values are loaded under a DOTENV_ prefix — names rewritten, values untouched, nothing executed.
if [ -f .env ]; then
  set -a
  source /dev/stdin <<EOF2
$(sed -E 's/^([A-Za-z_][A-Za-z0-9_]*)=/DOTENV_\1=/' .env)
EOF2
  set +a
fi
cfg() { # cfg VAR [default] — caller env > .env > default; echoes the resolved value
  local v="$1" n="DOTENV_$1"
  echo "${!v:-${!n:-${2:-}}}"
}
MODEL="$(cfg MODEL openai/gpt-oss-20b)"  # 120b needs an 80GB card: MODEL=openai/gpt-oss-120b
VLLM_PORT="$(cfg VLLM_PORT 8001)"        # own name on purpose: PORT=8000 in .env is uvicorn's
WAIT_MINS="$(cfg WAIT_MINS 25)"          # first boot pulls weights (~13GB for 20b)
BASE="$(cfg GROQ_BASE_URL)"              # check: e.g. http://<instance-ip>:8001/v1
TOKEN="$(cfg GROQ_API_KEY)"              # the vLLM --api-key value (must exist even for vLLM)
CONTAINER="$(cfg CONTAINER vllm)"
VLLM_IMAGE="$(cfg VLLM_IMAGE vllm/vllm-openai:latest)"  # pin older (cu12) on 12.4 drivers: vllm/vllm-openai:v0.10.1
VLLM_ARGS="$(cfg VLLM_ARGS)"            # only from caller env or .env; unquoted on purpose

die() { echo "vllm_serve: $*" >&2; exit 1; }

models_ok() { curl -sf -m 5 -H "Authorization: Bearer $TOKEN" "$1/models" | grep -q "$MODEL"; }

case "${1:-check}" in
  serve)
    command -v curl >/dev/null || die "curl is required on the GPU host"
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
      docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
      docker run -d --name "$CONTAINER" --gpus all --restart unless-stopped \
        -p "$VLLM_PORT:8000" -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
        "$VLLM_IMAGE" --model "$MODEL" --api-key "$TOKEN" ${VLLM_ARGS:-} >/dev/null
      echo "docker container '$CONTAINER' up ($VLLM_IMAGE)"
    else
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
    if [ -n "${GROQ_API_KEY:-}" ]; then echo "  GROQ_API_KEY=<the token you set>"; else echo "  GROQ_API_KEY=$TOKEN"; fi
    echo "  EXTRACT_MODEL=$MODEL"
    echo "  FALLBACK_MODEL=$MODEL   # or GROQ_FALLBACK_ENABLED=false: single-model backend"
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
    die "usage: vllm_serve.sh serve|check|stop"
    ;;
esac
