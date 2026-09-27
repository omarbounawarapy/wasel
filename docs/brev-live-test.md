# Live self-hosted LLM: the brain on a Brev GPU, from a laptop

Brev plan P0/P1 (`docs/brev_gpu_plan.md`). The LLM layer here is already OpenAI-compatible
(`app/llm/groq_backend.py`), so one env var moves it from Groq's free tier (1,000 req/day,
8K tok/min, ~1 h per paced eval) to a GPU you rent by the hour: same request shape, no rate
limits, unpaced evals in minutes, and demo-day insurance when Groq caps out mid-pitch.
`scripts/brev_llm_up.sh` (`make brev-serve` / `make brev-check`) sets the instance side up
and verifies the laptop side. No app code changes beyond `GROQ_BASE_URL` in `.env`.

## Prerequisites

- A Brev account with credit (brev.nvidia.com) and an instance:
  - **gpt-oss-20b** (default): any 24 GB card — L4, A10G, RTX 4090 class. ~$0.4–1/hr.
  - **gpt-oss-120b**: an 80 GB card — A100/H100. ~$1.5–3.5/hr; launch it with
    `MODEL=openai/gpt-oss-120b VLLM_ARGS="--gpu-memory-utilization 0.95 --max-model-len 16384"`.
- SSH access to the instance (Brev gives you the command in the console) and either `docker`
  or `python3` on it. On Blackwell GPUs use the docker path — the official `vllm/vllm-openai`
  image ships the right kernels.
- On the laptop: `.env` keys (the instance's public IP goes in `GROQ_BASE_URL`):
  ```
  GROQ_BASE_URL=http://<instance-ip>:8001/v1   # empty = Groq (the default chain)
  GROQ_API_KEY=<the vLLM --api-key token>       # still required when self-hosted
  EXTRACT_MODEL=openai/gpt-oss-20b
  FALLBACK_MODEL=openai/gpt-oss-20b             # or GROQ_FALLBACK_ENABLED=false: single-model backend
  ```

## Run

On the **instance** (clone the repo, or at least `scripts/` + a `.env` if you prefer):

```bash
make brev-serve                                  # MODEL=openai/gpt-oss-20b by default
```

Installs vLLM (docker if present, else a venv), starts the server on :8001 keyed by a token
(generated and shown once if `GROQ_API_KEY` isn't set), waits for the weights to load, then
prints the exact `.env` lines to paste on the laptop.

On the **laptop**:

```bash
make brev-check                                  # /v1/models + one JSON completion + round-trip ms
GROQ_BASE_URL=… GROQ_API_KEY=… EXTRACT_MODEL=… \
  .venv/bin/python -m eval.run --live            # unpaced; add --sample 279 for the full set
```

If the instance has no reachable public IP, tunnel it: `cloudflared tunnel --url
http://localhost:8001` on the instance, and put the trycloudflare URL in `GROQ_BASE_URL`.

## Demo-day flip (Groq dies mid-pitch)

The chain reads env at request time — no restart of code needed beyond restarting the API so
`.env` is re-read: set `GROQ_BASE_URL` + `GROQ_API_KEY` + `EXTRACT_MODEL` in `.env`, `make up`,
and the next message extracts from the GPU. Flip the keys back to empty to return to Groq.

## Serving the fine-tuned artifact (LoRA)

Fine-tune happens once on Brev (brev plan P2a); hosts only ever serve the result. The run kit
passes extra server flags through `VLLM_ARGS`, so no script change is needed:

```bash
VLLM_ARGS="--enable-lora --lora-modules extract-v1=$PWD/models/extract_lora_v1" make brev-serve
# laptop .env: EXTRACT_MODEL=extract-v1   (the name given in --lora-modules)
```

A 20b base + adapter still fits a 24 GB L4. The adapter is versioned and committed with a
model card + sha256 (`models/extract_lora_v1/`, same discipline as `models/risk_xgb_v1.json`);
after swapping it, re-record the offline cache: `scripts/warm_cache.py` with `LIVE=1` against
the fine-tuned server.

## Checks and caveats

- `make brev-check` must pass before trusting the flip; check both `make eval` (offline,
  unchanged) and one `eval.run --live` before demo day so the model's behavior is known.
- The Groq-only `reasoning_format` field is dropped automatically for self-hosted endpoints;
  `reasoning_effort=low` is kept (vLLM honors it for gpt-oss). If the server 400s anyway,
  `tests/unit/test_groq_backend_routing.py` pins which kwargs each path sends.
- On hosts with a CUDA 12.x driver (< 12.8), pin `VLLM_IMAGE=vllm/vllm-openai:v0.10.1` —
  the `latest` image ships torch/cu13 and dies with "NVIDIA driver too old". v0.10.1
  serves gpt-oss MXFP4 on Ampere (Triton backend, slower than optimized kernels).
- Verify the box's real disk before choosing it for 120b (`df -h`, not `brev search`):
  a denvr A100 advertising 2 TB had a 92 GB root volume — 63 GB weights + image do not fit.
- After any `brev create`, run `brev ls` and delete phantoms: a create can report
  "0/1 instances" while still provisioning (and billing) one.
- Shadeform-backed instances cannot be stopped — `brev delete` is the only way to stop
  the meter once you're done.
- gpt-oss on vLLM keeps the harmony analysis channel: a tiny `max_completion_tokens` can be
  consumed entirely by reasoning and return `content: null` (the check uses 512 and falls
  back to `reasoning_content` for display). Extraction prompts budget enough tokens — this
  only bites quick manual probes.
- `.env` values containing spaces must be **quoted** (`VLLM_ARGS="--gpu-memory-utilization
  0.92 …"`) — the loader rewrites names only, and an unquoted `0.92` gets executed as a
  command (`set -u` kills the script).
- Don't run the eval while other `brev exec/copy` commands are in flight against the same
  instance: they share one multiplexed SSH connection with the port-forward, and the added
  latency can push LLM calls past the 6 s step deadline (cases then fall through to the
  rules extractor and the run mis-measures the model).
- The endpoint must never be exposed without its `--api-key` token; anyone with the URL and
  token can burn your GPU credit.
- **Credit burns while the instance runs, not while it's stopped**: `make brev-serve`'s
  `stop` subcommand (or `bash scripts/brev_llm_up.sh stop`) tears the server down, then stop
  the instance in the Brev console. This is the whole budget discipline.
- The script re-runs cleanly (`serve` exits 0 if the model is already being served); the
  first boot downloads weights, so give 20b ~15–25 min and 120b ~30–40 min the first time.
- Measured 2026-09-27 (A6000 48 GB, gpt-oss-20b): `eval.run --live` unpaced in 6.5 min —
  40-case extraction sample is_order 0.875 vs 0.961 on the offline 279-case cache (Groq
  120b outputs); every LLM-answered case was right on is_order and the gate misses were
  chain fall-throughs. 120b on an A100 80 GB is the production-parity shape.
