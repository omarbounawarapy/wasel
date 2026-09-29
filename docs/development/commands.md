# Commands and scripts

The Makefile is the operational interface of the repository. `make help` lists targets with a one-line description; this page says what each one really does, what it needs, and whether it changes files you might commit.

Conventions used below:

- **Mutates** names committed or persistent files a target rewrites. If `git status` shows them changed after a run, decide whether the change is intended before committing.
- **Long-running** targets keep a process in the foreground until Ctrl-C.
- The Makefile uses `.venv/bin/python` (or `.venv/Scripts/python.exe`) when it exists, otherwise `python3`. Override with `PY=...`.
- `.env` is read from the working directory by the application and by the LLM layer, whichever command starts them; `up` and `serve` also source it into the shell. See [environment](../configuration/environment.md#how-values-are-loaded).

## Setup and quality

| Target | What it does | Needs | Mutates |
|---|---|---|---|
| `setup` | `pip install -r requirements.txt -r requirements-dev.txt`, then `pip install --no-deps -e .` | network, a Python 3.11 environment | the virtual environment |
| `lint` | `ruff check .` (rules E, F, I, B, UP, DTZ; line length 125; `web/`, `.venv/`, `var/` excluded) | | nothing |
| `fmt` | `ruff check --fix .` | | source files (autofixes) |
| `hygiene` | `scripts/dev/hygiene.sh`: fails on tracked `.env`, database, `node_modules`, `web/dist` or `var/` files; key-shaped strings (Groq, Gemini, Meta, tunnel prefixes); phone numbers in `tests/fixtures` or `data` outside the allowlist `21600000001` to `...009`; `datetime.now()` outside `clock.py`; LLM SDK imports; `dangerouslySetInnerHTML` in the web UI | git | nothing |
| `test` | The offline test suite with `TEST_ENV` (`APP_MODE=dev LLM_MODE=fail_all WORKER_ENABLED=false DEMO_MODE=true`, all keys and WhatsApp secrets empty) and `-m "not live"`. Extra pytest arguments: `PYTEST_ARGS="-k monitor"`. About 4 minutes. | nothing external | pytest caches only |
| `eval` | The offline evaluation gate: `python -m wasel.evaluation.run` under `TEST_ENV`. About 6 seconds. | | **`data/reports/eval.json`** |
| `check` | `hygiene`, `lint`, `test`, `eval` in that order, ending with `check: green, ok to merge`. This is what CI runs. | | **`data/reports/eval.json`** |
| `drill` | Runs `tests/integration/test_backend.py -k fallback_drill`: with every LLM path failing, ingestion still scores on the rules path and never errors | | nothing |
| `smoke` | `scripts/ops/smoke.py $(URL)`: health, `GET /`, the sample order through `try` (or paste), a scripted reply, the read-only check in public mode | a running API; no key | creates orders in the target's sandbox |
| `clean` | Removes `.pytest_cache`, `.ruff_cache`, `htmlcov` and `var/*.db` with their WAL and SHM files | | **deletes the local database** |

`make check` rewrites `data/reports/eval.json`. When only its `runtime_s` changed, restore it (`git checkout -- data/reports/eval.json`) before committing. When metrics changed, that is a real change; see [evaluation](../evaluation.md#reports).

## Running the application

| Target | What it does | Mode and database | Long-running |
|---|---|---|---|
| `up` | Starts the API on `API_PORT` (8000), waits up to 180 s for `/api/health`, then starts the Streamlit dashboard on `UI_PORT` (8501) against it. Reads `.env`. Ctrl-C stops both. | `APP_MODE` default `dev`; `SEED_ON_BOOT` default **`always`**: the database is deleted and reseeded on every start | yes |
| `run` | `uvicorn wasel.main:create_app --factory --reload --port 8000`. Reads `.env` from the working directory like every start command, without sourcing it into the shell. Reloads on code changes. | `APP_MODE` default `dev`; database kept, seeded when empty | yes |
| `ui` | The dashboard on `UI_PORT` against `API_BASE_URL` (default `$(URL)`) | any | yes |
| `demo` | The API in `public` mode with `SEED_ON_BOOT=always`, no reload. Serves `web/dist` at `/` if built. | public, reseeded | yes |
| `serve` | Reads `.env`, then `uvicorn ... --host $HOST --port $PORT --workers 1`, no reload. Prints the mode. Unset `APP_MODE` means public. | from `.env`; public reseeds every start | yes |
| `web` | `cd web && npm ci && npm run build`: Next.js static export into `web/dist` | Node 22, network | replaces `web/node_modules` and `web/dist` (both ignored by git) |
| `web-dev` | `cd web && npm run dev`: Next.js dev server on :5173 with hot reload against the API on :8000 (needs `node_modules` and an API in `dev` mode) | | yes |
| `seed` | Rebuilds the database from scratch (`SEED_ON_BOOT=always`, worker disabled) at `DB` (default `var/app.db`): schema, catalog, committed extraction cache, nine sample orders, all scored with no LLM call | | **deletes and recreates the database** |

## Hosting and integrations

| Target | What it does | Needs |
|---|---|---|
| `tunnel` | Runs `cloudflared tunnel run` with `CLOUDFLARE_TUNNEL_TOKEN` from `.env`; publishes `make serve` on your Cloudflare hostname | `cloudflared`, the token |
| `deploy` | On the host: `git pull --ff-only`, then `make setup web`, and prints the restart and smoke-test commands. It does not restart anything. | git remote, network |
| `wa-up` | `scripts/ops/wa_webhook_up.sh`: a quick tunnel and Meta callback registration for local WhatsApp testing ([WhatsApp](../subsystems/whatsapp.md#testing-locally)) | a running API with the webhook enabled, `cloudflared`, Meta credentials |
| `llm-serve` | On a GPU host: installs and starts vLLM, waits for the model ([self-hosted LLM](../operations/self-hosted-llm.md)) | GPU host, docker or python |
| `llm-check` | From the client: lists the model at `GROQ_BASE_URL` and makes one completion | `GROQ_BASE_URL`, `GROQ_API_KEY` in `.env` |

## Data, model and evaluation assets

These targets regenerate committed files. Use them deliberately and commit the results together with the change that required them.

| Target | What it does | Mutates (committed) | External |
|---|---|---|---|
| `generate` | `python -m wasel.ml.generate --seed 20260927 --n 10000`: 10,000 synthetic orders; runs the phrase-bank and row lints first and writes nothing if one fails | `data/synth_v1.csv`, `data/synth_v1.meta.json` | none |
| `train` | `python -m wasel.ml.train`: trains the monotone XGBoost, enforces the gates, writes the model, card, metrics, impact and hero golden | `models/risk_xgb_v1.json`, `models/risk_xgb_v1.card.json`, `data/reports/train_metrics.json`, `data/reports/impact.json`, `tests/golden/hero.json` | none |
| `golden` | `python -m wasel.evaluation.build_golden`: the three golden sets from the CSV, the classifier bank and the templates | `data/eval/golden/*.jsonl` | none |
| `sessions` | `python -m wasel.failures.dataset`: the labelled agent sessions | `data/agent_sessions.jsonl`, `data/agent_sessions_holdout.jsonl` | none |
| `failures` | The failure analyzer, rules only, on both synthetic files and on the database at `DB` | `data/reports/failures_synthetic.json`, `failures_holdout.json`, and a new untracked `failures_db.json` | needs `var/app.db` to exist |
| `failures-llm` | The same with the LLM language layer | `data/reports/failures_synthetic_llm.json`, `failures_holdout_llm.json` (new files) | `GROQ_API_KEY` in the environment or `.env`; LLM calls |
| `eval-live` | The golden sets through the live extractor and judge (`python -m wasel.evaluation.run --live`) | `data/reports/eval_live.json` | `GROQ_API_KEY` in the environment or `.env`; LLM calls |
| `warm` | `scripts/data/warm_cache.py`: runs every sample conversation and scripted reply through the real worker in a scratch database and writes the extraction cache. Default mode uses `data/seed/hand_extractions.json` and labels the entries as hand-crafted, not model output. `LIVE=1 make warm` records real outputs from the live chain. | `data/seed/extraction_cache.jsonl` | live mode: `GROQ_API_KEY`, LLM calls |
| `mocks` | `scripts/data/dump_mocks.py`: rewrites the frozen API responses from a seeded in-process app | `tests/fixtures/api/*.json` | none |

`generate`, `golden`, `sessions` and `train` are deterministic apart from timestamps that `train` writes (see [machine learning](../machine-learning.md#reproducibility)); running them on an unchanged tree should leave `git diff` empty except for those fields. `make mocks` currently produces a diff against the committed files, because the committed frozen responses predate the current health payload and configuration hash; the contract test only requires that they validate against the API models.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/dev/hygiene.sh` | The repository checks listed under `hygiene` |
| `scripts/dev/wait_health.py [URL]` | Polls `/api/health` for up to 180 s; exit 1 on timeout. Used by `make up` and CI. |
| `scripts/ops/smoke.py [URL]` | The smoke test |
| `scripts/ops/rollback.py <role> <version>` | Switch an LLM role's `active` prompt version in `config/llm.yaml` ([registry](../configuration/llm-registry.md#procedures)) |
| `scripts/ops/extract_probe.py [--threads N] [--sample N] [--set FILE]` | Runs the golden extraction set concurrently through the live chain and prints every mismatch and every case that fell through to rules. A diagnostic for self-hosted endpoints, not a gate. |
| `scripts/ops/vllm_serve.sh serve\|check\|stop` | Serve, verify or stop a self-hosted vLLM (`llm-serve` and `llm-check` call the first two; there is no make target for `stop`) |
| `scripts/ops/wa_webhook_up.sh` | Quick tunnel and Meta callback registration |
| `scripts/data/warm_cache.py [--live] [--out FILE]` | Behind `make warm` |
| `scripts/data/dump_mocks.py` | Behind `make mocks` |
| `scripts/data/expand_phrase_bank.py [--cells ...] [--langs ...] [--k N] [--out FILE]` | Drafts paraphrases for phrase-bank cells with an OpenAI-compatible endpoint (`GROQ_BASE_URL`, `GROQ_API_KEY`, `EXTRACT_MODEL`). Candidates that pass the generator lints are written to `data/phrase_banks_candidates.yaml` under `eval_only`. It never edits the authored bank, and every line needs native-speaker review before use. |

## Python entry points

| Command | What |
|---|---|
| `uvicorn wasel.main:create_app --factory` | The application |
| `python -m wasel.ml.generate`, `python -m wasel.ml.train` | Dataset and model |
| `python -m wasel.evaluation.run [--live] [--limit N] [--sample N] [--pace S]`, `python -m wasel.evaluation.build_golden` | Evaluation |
| `python -m wasel.failures.run --source synthetic\|holdout\|db [--llm] [--db PATH]`, `python -m wasel.failures.dataset` | Failure analysis |
| `python -m wasel.monitor --build-reference` | Rebuild `data/monitor_reference.json` |
| `python -m pytest tests/unit/test_scoring.py -k tier` | Focused tests ([testing](testing.md)) |

## Which command, when

| Situation | Run |
|---|---|
| Before opening a pull request | `make check` |
| Trying the app | `make up` |
| Working on the API | `make run` |
| Working on the web UI | `make run` and `make web-dev` |
| Hosting | `make serve`, `make tunnel`, then `make smoke URL=...` |
| After changing extraction or drafting logic | `make eval`, then `make eval-live` if you have a key |
| After changing a prompt | [change a prompt](extending.md#change-a-prompt) |
| After changing features or generator | [retraining](../machine-learning.md#retraining) |
