# Self-hosted LLM (vLLM on a GPU host)

The LLM layer speaks the OpenAI-compatible chat-completions protocol (`src/wasel/llm/groq_backend.py`), so one environment variable moves it from Groq's hosted API to a model you serve yourself. The request shape is unchanged, and no application code changes. You avoid the provider's rate limits, evaluation runs need no pacing, and you have a fallback when the hosted provider is throttled. Wasel's own caps (`LIVE_LLM_DAILY_CAP` and the public-mode visitor caps) still apply to calls made by the running app.

`scripts/ops/vllm_serve.sh` (`make llm-serve`, `make llm-check`) sets up the GPU host and verifies the client side.

## Prerequisites

- A GPU host reachable over the network:
  - **gpt-oss-20b** (default): any 24 GB card (L4, A10G, RTX 4090 class).
  - **gpt-oss-120b**: an 80 GB card (A100 or H100), started with `MODEL=openai/gpt-oss-120b VLLM_ARGS="--gpu-memory-utilization 0.95 --max-model-len 16384"`. Check the host's real free disk with `df -h` first: the weights take about 63 GB plus the image.
- SSH access, and either `docker` or `python3` on the host. On Blackwell GPUs use the docker path, because the official `vllm/vllm-openai` image ships the right kernels.
- In the client's `.env`:
  ```
  GROQ_BASE_URL=http://<gpu-host>:8001/v1   # empty = Groq (the default chain)
  GROQ_API_KEY=<the vLLM --api-key token>    # still required when self-hosted
  EXTRACT_MODEL=openai/gpt-oss-20b
  FALLBACK_MODEL=openai/gpt-oss-20b          # or GROQ_FALLBACK_ENABLED=false for a single-model backend
  ```

## Run

On the **GPU host** (clone the repository, or copy `scripts/ops/vllm_serve.sh`):

```bash
make llm-serve                                   # MODEL=openai/gpt-oss-20b by default
```

It installs vLLM (docker if present, otherwise a virtualenv in `~/vllm-venv`), starts the server on `VLLM_PORT` (8001) behind an API token (generated and shown once if `GROQ_API_KEY` is not set), waits for the weights to load, and prints the `.env` lines to use on the client. The first boot downloads weights: allow 15 to 25 minutes for 20b and 30 to 40 for 120b (`WAIT_MINS`, default 25). Re-running is safe; it exits 0 if the model is already being served.

On the **client**:

```bash
make llm-check                                   # /v1/models, one JSON completion, round-trip time
.venv/bin/python -m wasel.evaluation.run --live  # unpaced live evaluation; add --sample 279 for the full extraction set
```

Both read the connection details from `.env`, except that the evaluation command needs them exported in your shell ([why](../configuration/environment.md#how-values-are-loaded)).

If the GPU host has no reachable public address, tunnel it: run `cloudflared tunnel --url http://localhost:8001` on the host and put the printed URL in `GROQ_BASE_URL`.

## Switching providers

The LLM chain is built once, when the API process starts, from the environment at that moment. To switch, set `GROQ_BASE_URL`, `GROQ_API_KEY` and `EXTRACT_MODEL`, then restart the API (with `make serve` or `make up`, which export `.env`). The next message is extracted by the self-hosted model. Empty the values and restart to return to Groq. `GET /api/health` shows the models in `llm.chain_extract`.

When `GROQ_BASE_URL` is set, the Groq-only `reasoning_format` field is dropped from requests automatically, because vLLM rejects unknown fields; `reasoning_effort=low` is kept. `tests/unit/test_groq_backend_routing.py` pins which fields each path sends.

## Serving a fine-tuned adapter

Extra server flags pass through `VLLM_ARGS`, so serving a LoRA adapter needs no script change:

```bash
VLLM_ARGS="--enable-lora --lora-modules extract-v1=$PWD/models/extract_lora_v1" make llm-serve
# client .env: EXTRACT_MODEL=extract-v1   (the name given in --lora-modules)
```

The repository does not contain an adapter. After swapping the model, re-record the sample extractions with `LIVE=1 make warm` against the new server and re-run the live evaluation.

## Operating notes

- `make llm-check` must pass before you rely on the endpoint. Also run `make eval` (unaffected by the switch) and one live evaluation so the model's behaviour is known.
- gpt-oss keeps a hidden reasoning channel: a very small `max_completion_tokens` can be consumed entirely by reasoning and return empty content. The check uses 512 tokens, and the role limits in `config/llm.yaml` budget enough.
- On hosts with a CUDA 12.x driver older than 12.8, pin `VLLM_IMAGE=vllm/vllm-openai:v0.10.1`; the `latest` image ships torch for CUDA 13 and fails with "NVIDIA driver too old". That version serves gpt-oss MXFP4 on Ampere through the Triton backend, which is slower than the optimized kernels.
- Values in `.env` that contain spaces must be quoted (`VLLM_ARGS="--gpu-memory-utilization 0.92 ..."`); the script loads `.env` with variable names rewritten and values untouched.
- Do not run an evaluation while other SSH-multiplexed commands (port-forward, exec, copy) use the same connection to the host: the added latency can push calls past the step deadline, and cases then fall through to the rules extractor and misrepresent the model.
- Never expose the endpoint without its `--api-key` token. Anyone with the URL and token can use your GPU.
- Cloud GPU instances bill while they exist. `bash scripts/ops/vllm_serve.sh stop` removes the container or stops the process (there is no make target for it), but also stop or delete the instance with your provider; some providers do not support "stop" and need a delete.
- `scripts/ops/extract_probe.py` runs the golden extraction set concurrently against the endpoint and prints every mismatch and every case that fell through to rules, which is the fast way to see what a model gets wrong.

## Measured behaviour

The committed [`data/reports/eval_live.json`](../../data/reports/eval_live.json) records one live run through the chain: 386 seconds, 104 extraction and 114 judge requests, no cache hits, 2 failed extraction requests. Per the notes of that run it was made against a self-hosted `gpt-oss-20b` (the report itself does not store the model name). On its 40-case extraction sample:

| Metric | Value | Live floor |
|---|---|---|
| `is_order_acc` | 0.875 | 0.95 |
| `address_exact_acc` | 0.650 | not gated |
| `address_within1_acc` | 0.775 | 0.85 |
| `language_acc` | 0.925 | 0.85 |
| flag F1 | 0.833 | not gated |

Five of the 40 cases ended with no assessment (path `none`), which is what pulled `is_order_acc` down. The report lists six gate failures in all (also outbound `safe_passed` 0.92, prefilter cases and one G3 rate). For context, the offline gate scores the rules extractor, not a model, and gets 0.961, 0.907 and 0.971 on the same three metrics over all 279 rows; the two sets of numbers are different populations and different extractors and should not be compared as a model ranking. The chain's default primary is `gpt-oss-120b` with the 20b as fallback, and the committed record measures only the 20b; no 120b live run is recorded in the repository. Regenerate the record with `eval.run --live` against any serving endpoint.
