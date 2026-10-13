# AMD instance runbook (ROCm + vLLM)

The steps to bring the AMD Developer Cloud GPU online for the extraction model, check it, and point the app at it. Everything below is ready in the repository; the only unknowns are the ones that need the real instance (marked **verify**).

## Status (13 October 2026)

- **No AMD Developer Cloud credits have been received.** The credit request is not confirmed. Until credits arrive, no AMD GPU runs this project.
- The AMD serving path is prepared: the preflight, ROCm launch, client template, health label and the hosted backup below. It has been tested only against a stand-in endpoint, not on AMD hardware.
- The live demo answers from the hosted Groq API (or from rules if no key is set). Do not describe the demo as AMD-served until `/api/health` shows the self-hosted step answering and the committed evaluation report names the AMD model and hardware.
- When credits arrive, the same runbook applies. The chain is AMD first and hosted Groq second, so partial AMD use is measurable from the health payload and the Monitor.

Background: [self-hosted LLM](self-hosted-llm.md) (the general setup) and issue [#191](https://github.com/omarbounawarapy/wasel/issues/191).

## 0. Before you rent

- Credit: the AMD Developer Cloud credit must be active. Credits expire 30 days after activation, and an instance bills while it exists.
- Instance: pick an MI300X (192 GB VRAM). It fits gpt-oss-120b and 20b. A smaller card needs `MODEL` set to 20b and must have at least 24 GB of VRAM.
- Image: a ROCm Ubuntu image with `rocm-smi` and docker. **verify** on the instance; if docker is missing, install it before step 2.
- Network: open TCP 8001 to your laptop's address only. The endpoint is protected by its token, but do not open it to the world.

## 1. Get the code and check the host

```bash
git clone https://github.com/omarbounawarapy/wasel.git wasel && cd wasel
ACCEL=rocm make llm-preflight                    # GPU name, VRAM, disk, docker, port 8001, token
```

Every line must say `OK` before serving. `FAIL` lines say what is missing (VRAM, disk, docker group, port). Preflight changes nothing.

## 2. Serve the model

```bash
export SELF_HOSTED_API_KEY="$(openssl rand -hex 24)"    # the vLLM --api-key; save it in your password manager now
ACCEL=rocm MODEL=openai/gpt-oss-20b make llm-serve
```

It pulls `vllm/vllm-openai-rocm` (several GB), starts the container with the ROCm devices, waits for the weights and prints the `.env` lines. First boot takes 15 to 25 minutes (`WAIT_MINS`). For 120b, use `MODEL=openai/gpt-oss-120b` and allow 30 to 40 minutes.

Preview the exact `docker run` command without starting anything: `DRY_RUN=1 ACCEL=rocm make llm-serve`.

**verify**: `gpt-oss` on the ROCm build of vLLM. If the server starts but the completion is empty or the container exits, read `docker logs vllm` (`docker logs --tail 50 vllm`). If gpt-oss does not run, pick a supported open model, set `MODEL` to it, and record why in [self-hosted-llm.md](self-hosted-llm.md).

## 3. Check from the laptop

Copy `config/amd.env.example` to `.env` and fill the placeholders (`GROQ_BASE_URL`, `SELF_HOSTED_API_KEY`). Your hosted `GROQ_API_KEY` stays as it is. Then:

```bash
make llm-check        # lists the model in /v1/models, runs one JSON completion, prints the round trip
```

If `llm-check` fails, the message names the step: listing (address, port or token) or completion.

## 4. Connect the app

Restart the API so it rebuilds the chain from `.env`, then check:

```bash
curl -s localhost:8000/api/health | python3 -c 'import json,sys; print(json.load(sys.stdin)["llm"])'
```

`chain_extract` must start with `self-hosted:openai/gpt-oss-20b` (the AMD host), followed by `groq:openai/gpt-oss-20b` when the backup is configured. `serving_label` and `serving_host` must be set (they come from `LLM_SERVING_LABEL` and `GROQ_BASE_URL`). Send one message in the seller UI and check that the Monitor shows an AI-scored assessment, not `rules`.

## 5. Evaluate and record

```bash
.venv/bin/python -m wasel.evaluation.run --live        # full extraction set; add --sample 279 for all rows
.venv/bin/python scripts/ops/extract_probe.py           # prints every mismatch and every case that fell to rules
```

Commit the new `data/reports/eval_live.json` only after the report names the model and hardware (issue #193 tracks adding those fields). Do not change the gates to pass.

## 6. Stop billing

```bash
ACCEL=rocm bash scripts/ops/vllm_serve.sh stop
```

Then stop or delete the instance in the AMD console; `stop` only removes the container. Empty `GROQ_BASE_URL` and `SELF_HOSTED_API_KEY` in `.env` and restart the API so requests do not fail while it is off.

## How the fallback works

With `GROQ_BASE_URL` (the AMD host) and `SELF_HOSTED_API_KEY` set, and `GROQ_API_KEY` holding the hosted key, the chain is:

1. `self-hosted:<model>` (primary, 6 s per call)
2. `groq:<model>` (hosted backup, 8 s per call)
3. rules, if both fail

A refused connection, a timeout or a 5xx on the primary moves the request to the backup within the 20 s deadline. After one failure the primary's breaker is open for 60 s, so later requests skip it and go straight to the backup. `/api/health` lists the chain in `llm.chain_extract`. `fallback_active` is true for five minutes after a backup or rules answer, and the header tooltip then says the primary did not answer.

## Known gaps

- The live evaluation numbers in the repository were measured on a self-hosted 20b, not on AMD. Do not quote them as AMD results.
- Per-request provenance is not stored: the database records `provider` (`groq`) and the path, not which endpoint answered. The health payload shows which endpoints are configured and whether a backup was used recently.
- The Monitor page does not show the serving label yet; only the header tooltip does ([#192](https://github.com/omarbounawarapy/wasel/issues/192)).
