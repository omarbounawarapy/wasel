# Self-hosted LLM (vLLM on a GPU host)

The LLM layer speaks the OpenAI-compatible chat-completions protocol (`app/llm/groq_backend.py`), so a single environment variable moves it from Groq's hosted API to a model you serve yourself. The request shape is unchanged. You get no provider rate limits or daily cap, evaluation runs without pacing, and a fallback when the hosted provider is throttled. `scripts/vllm_serve.sh` (`make llm-serve`, `make llm-check`) sets up the GPU host and verifies the client side. No application code changes beyond `GROQ_BASE_URL` in `.env`.

## Prerequisites

- A GPU host you can reach over the network:
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

On the **GPU host** (clone the repository, or copy `scripts/vllm_serve.sh`):

```bash
make llm-serve                                   # MODEL=openai/gpt-oss-20b by default
```

It installs vLLM (docker if present, otherwise a virtualenv), starts the server on `:8001` behind an API token (generated and shown once if `GROQ_API_KEY` is not set), waits for the weights to load, and prints the `.env` lines to use on the client. The first boot downloads weights: allow 15–25 minutes for 20b and 30–40 minutes for 120b. Re-running is safe; it exits 0 if the model is already being served.

On the **client**:

```bash
make llm-check                                   # /v1/models, one JSON completion, round-trip time
.venv/bin/python -m eval.run --live              # unpaced live evaluation; add --sample 279 for the full set
```

If the GPU host has no reachable public address, tunnel it: run `cloudflared tunnel --url http://localhost:8001` on the host and put the printed URL in `GROQ_BASE_URL`.

## Switching providers at runtime

The chain reads its environment at request time, so switching only needs the API restarted so that `.env` is re-read. Set `GROQ_BASE_URL`, `GROQ_API_KEY` and `EXTRACT_MODEL` and restart; the next message is extracted by the self-hosted model. Empty the values to return to Groq.

## Serving a fine-tuned adapter

Extra server flags pass through `VLLM_ARGS`, so serving a LoRA adapter needs no script change:

```bash
VLLM_ARGS="--enable-lora --lora-modules extract-v1=$PWD/models/extract_lora_v1" make llm-serve
# client .env: EXTRACT_MODEL=extract-v1   (the name given in --lora-modules)
```

After swapping the model, re-record the offline extraction cache with `LIVE=1 make warm` against the new server.

## Operating notes

- `make llm-check` must pass before you rely on the endpoint. Also run `make eval` (offline, unchanged by the switch) and one `eval.run --live` so the model's behaviour is known.
- The Groq-only `reasoning_format` field is dropped automatically for self-hosted endpoints; `reasoning_effort=low` is kept. `tests/unit/test_groq_backend_routing.py` pins which fields each path sends.
- On hosts with a CUDA 12.x driver older than 12.8, pin `VLLM_IMAGE=vllm/vllm-openai:v0.10.1`; the `latest` image ships torch for CUDA 13 and fails with "NVIDIA driver too old". v0.10.1 serves gpt-oss MXFP4 on Ampere through the Triton backend, which is slower than the optimized kernels.
- gpt-oss keeps a hidden reasoning channel: a very small `max_completion_tokens` can be consumed entirely by reasoning and return `content: null`. The check uses 512 tokens; the extraction prompts budget enough.
- Values in `.env` that contain spaces must be quoted (`VLLM_ARGS="--gpu-memory-utilization 0.92 …"`); the loader only rewrites variable names.
- Do not run an evaluation while other SSH-multiplexed commands (port-forward, exec, copy) use the same connection to the host: the added latency can push calls past the step deadline, and cases then fall through to the rules extractor and misrepresent the model.
- Never expose the endpoint without its `--api-key` token. Anyone with the URL and token can use your GPU.
- Cloud GPU instances bill while they exist. `bash scripts/vllm_serve.sh stop` stops the server, but stop or delete the instance itself with your provider as well; some providers do not support "stop" and need a delete.

## Measured behaviour

A live run of the golden sets against gpt-oss-20b on a 48 GB card completed in about 6.5 minutes (104 extraction and 114 judge requests, no cache hits). On the 40-case extraction sample it scored `is_order` 0.875, address exact-match 0.650, address within one level 0.775 and flag F1 0.833, against 0.961 / 0.907 / 0.971 / 0.964 for the recorded gpt-oss-120b outputs the offline suite replays. The misses on `is_order` were cases where the LLM step failed inside the step deadline and the chain fell through to the rules extractor, not wrong model answers; address quality is the real gap of the smaller model. Treat gpt-oss-120b as the reference model for extraction, and the 20b as a throttling fallback. The record of that run is [`reports/eval_live.json`](../reports/eval_live.json); regenerate it with `eval.run --live` against any serving endpoint.
