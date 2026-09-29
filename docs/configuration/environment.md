# Environment variables

Every environment variable that Wasel, its scripts and its front ends read. [`.env.example`](../../.env.example) is the annotated template for the ones a deployment normally sets; this page also lists the ones it omits.

## How values are loaded

Values are read in two ways, and both see `.env`:

| Reader | Sources | Variables |
|---|---|---|
| `wasel.settings.Settings` (pydantic-settings) | process environment, then the `.env` file in the current working directory | mode, safety, WhatsApp, caps, sandbox, runtime |
| `wasel.envutil.env()`, used by the LLM layer, prompt registry, tracing and scoring config | process environment, then the same `.env` file | `GROQ_API_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_ENABLED`, `EXTRACT_MODEL`, `FALLBACK_MODEL`, `GROQ_BASE_URL`, `GROQ_FALLBACK_ENABLED`, `LLM_DEADLINE_S`, `LLM_MODE` (when called without a mode), `LLM_REPLAY_DIR`, `PROBE_FILE`, `PROMPT_VERSION`, `LLM_REGISTRY`, `TRACE_FILE`, `SCORING_CONFIG` |

In both, a real environment variable wins over the file, and an empty value counts as unset. So `make run`, `make demo`, a bare `uvicorn wasel.main:create_app --factory`, `make eval-live`, `make warm LIVE=1` and `make failures-llm` all see the provider keys in `.env`, run from the repository root. `make up` and `make serve` additionally source the file into the shell (`set -a; . ./.env; set +a`), which makes every variable, including ones the app never reads, visible to child processes. `make llm-check` and `scripts/ops/vllm_serve.sh` read `.env` themselves (names rewritten, values untouched); `scripts/ops/wa_webhook_up.sh` sources it. The test suite disables the file (`Settings.model_config["env_file"] = None`), which also disables the fallback in `env()`.

Because `make` sources `.env` as shell code, a value containing spaces must be quoted (`VLLM_ARGS="--gpu-memory-utilization 0.92 --max-model-len 16384"`).

Relative paths behave differently by setting:

| Setting | Resolved against |
|---|---|
| `DB_PATH`, `SCORING_CONFIG`, the model file in `scoring.yaml` | the repository root |
| `LLM_REGISTRY` | used as given (absolute, or relative to the working directory); default is `config/llm.yaml` under the root |
| `PROBE_FILE`, `TRACE_FILE`, `LLM_REPLAY_DIR` (when relative), the `.env` file | the current working directory (`LLM_REPLAY_DIR` defaults to `data/llm_replay` under the repository root) |

Run the API from the repository root and these all coincide. Invalid values (a bad enum, a non-numeric number) stop the app at start with a validation error rather than being ignored.

## Mode and safety

| Variable | Default | Values | Effect |
|---|---|---|---|
| `APP_MODE` | unset = `public` | `dev`, `event`, `public` | The master switch. Unknown or empty resolves to `public` with a logged warning. See [modes](../architecture/overview.md#modes). |
| `WA_SEND_ENABLED` | `false` | bool | Allows real WhatsApp sends. Effective only outside `public` mode and with `WA_TOKEN` (and `WA_PHONE_NUMBER_ID` for the sender). |
| `WA_AUTO_SEND` | `false` | bool | Lets the worker send `auto_send` drafts without a click. Never in `public` mode. |
| `WEBHOOK_ENABLED` | `false` | bool | Mounts `/webhook/whatsapp` if the mode allows and both secrets are long enough. |
| `SEED_ON_BOOT` | `auto` | `auto`, `always`, `if_empty`, `never` | `auto` resolves to `always` in `public` mode, else `if_empty`. `always` deletes the database file and rebuilds it. |
| `DB_PATH` | `var/app.db` | path | The SQLite file. Its parent directory is created if needed. |
| `DEMO_MODE` | `true` | bool | Selects the short timings: debounce 4 s and no-reply timeout 60 s instead of 15 s and 6 h. Set `false` for a real deployment. |
| `WORKER_ENABLED` | `true` | bool | `false` starts no worker loop. Tests and `make seed` use this. |
| `ADMIN_TOKEN` | empty | at least 24 characters | Mounts `POST /api/admin/reset`, checked in the `X-Admin-Token` header. Empty or short: the admin router does not exist. |

## Secrets

Never commit these. `.env` is git-ignored and `make hygiene` fails on key-shaped strings.

| Variable | Used for |
|---|---|
| `GROQ_API_KEY` | Groq API, or the token of a self-hosted server when `GROQ_BASE_URL` is set |
| `GEMINI_API_KEY` | Gemini fallback |
| `WA_TOKEN` | WhatsApp Cloud API bearer token (sending) |
| `WA_APP_SECRET` | Meta app secret: webhook signature check. At least 16 characters to mount the webhook. |
| `WA_VERIFY_TOKEN` | Webhook verification handshake. At least 24 characters to mount the webhook. |
| `ADMIN_TOKEN` | Admin reset endpoint |
| `CLOUDFLARE_TUNNEL_TOKEN` | `make tunnel` |

## LLM

| Variable | Default | Effect |
|---|---|---|
| `LLM_MODE` | `live` | `live`, `replay`, `fail_primary`, `fail_groq`, `fail_all`. See [LLM layer](../subsystems/llm.md#test-and-drill-modes). |
| `EXTRACT_MODEL` | `routing.primary` in `llm.yaml` (`openai/gpt-oss-120b`) | Model of the primary step |
| `FALLBACK_MODEL` | `routing.fallback_model` (`openai/gpt-oss-20b`) | Model of the second Groq step |
| `GROQ_BASE_URL` | empty (= Groq) | Point the Groq steps at any OpenAI-compatible server. `GROQ_API_KEY` must still be set. |
| `GROQ_FALLBACK_ENABLED` | `true` | `false` removes the second Groq step |
| `GEMINI_ENABLED` | `false` | Gemini needs this set to `true` **and** `GEMINI_API_KEY` **and** `GEMINI_MODEL` |
| `GEMINI_MODEL` | empty | A Flash-class model id from your Gemini account |
| `PROBE_FILE` | `config/probe.json` | Optional JSON describing how your Gemini account wants the schema written. The file is absent from the repository; built-in defaults apply. |
| `LLM_DEADLINE_S` | `20` (or `routing.deadline_s`) | Total time budget of one chain run |
| `PROMPT_VERSION` | unset | Overrides the active extract prompt version from `llm.yaml`. Both the cache key and the cache lookup use the resulting version, so the cache stays consistent. Leave unset normally. |
| `DRAFT_LLM` | `false` | Enables the LLM rewrite and judge for outbound drafts |
| `LLM_REGISTRY` | `config/llm.yaml` | Alternative registry file |
| `TRACE_FILE` | unset | Append every LLM trace record to this JSONL file |
| `LLM_REPLAY_DIR` | `data/llm_replay` | Directory of recorded provider responses used by `LLM_MODE=replay`. Startup fails with a clear error if it has no `*.json` fixtures. |

## Caps and sandbox

| Variable | Default | Effect |
|---|---|---|
| `LIVE_LLM_DAILY_CAP` | empty = mode default (public 80, event 300, dev none) | Provider calls per UTC day, counting fallback hops and failed attempts. `0` disables live calls. |
| `VISITOR_LLM_CAP_10MIN` | `6` | Provider calls per visitor in 10 minutes (public mode) |
| `VISITOR_LLM_CAP_DAY` | `20` | Provider calls per visitor per UTC day (public mode) |
| `SANDBOX_TTL_S` | `7200` | Age after which a visitor's conversations are purged |
| `SANDBOX_MAX_ORDERS` | `15` | Orders per visitor (429 `SANDBOX_LIMIT`) |
| `SANDBOX_GLOBAL_MAX` | `500` | Sandbox orders in total (429 `DEMO_BUSY`) |
| `PURGE_INTERVAL_S` | `600` | How often the purge runs |
| `REPLY_LIMIT` | `5` | Simulated replies per conversation in public mode |

`SANDBOX_GLOBAL_MAX` and `REPLY_LIMIT` are read by `Settings` but are not listed in `.env.example`.

## WhatsApp (non-secret)

| Variable | Default | Effect |
|---|---|---|
| `WA_PHONE_NUMBER_ID` | empty | Id of the business phone number. Without it inbound payloads are dropped as foreign and no sender is built. |
| `WA_API_VERSION` | empty (= `v21.0`) | Graph API version for sending |
| `META_APP_ID` | empty | Only `scripts/ops/wa_webhook_up.sh` (`make wa-up`) |
| `META_GRAPH_VERSION` | `v21.0` | Only that script |

## Hosting and runtime

| Variable | Default | Effect |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address for `make serve`. `0.0.0.0` exposes the port on the network. |
| `PORT` | `8000` | Port for `make serve` |
| `GIT_SHA` | `dev` | Shown in `/api/health` `build.git_sha` |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin allowed in `dev` mode |
| `SCORING_CONFIG` | `config/scoring.yaml` | Alternative scoring file |
| `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` | set to `1` at import if unset | Keeps NumPy and XGBoost single-threaded; an explicit value wins |

## Front ends and scripts

| Variable | Read by | Effect |
|---|---|---|
| `API_BASE_URL` | `dashboard/api_client.py`, `examples/_client.py`, `make ui` | Backend URL (default `http://localhost:8000`) |
| `API_TIMEOUT_S` | `dashboard/api_client.py` | Per-request timeout of the dashboard's HTTP client (default `30`) |
| `NEXT_PUBLIC_API_URL` | `web/lib/api.ts` (build time) | Backend origin for the web UI, without `/api`. Unset: the built app calls its own origin; `npm run dev` calls `http://localhost:8000`. |
| `CLOUDFLARED` | `wa_webhook_up.sh` | Path to the `cloudflared` binary |
| `PYTHON` | `wa_webhook_up.sh` | Python interpreter for its JSON parsing |
| `MODEL` | `vllm_serve.sh` | Model to serve (default `openai/gpt-oss-20b`) |
| `VLLM_PORT` | `vllm_serve.sh` | Port on the GPU host (default `8001`; kept separate from `PORT`) |
| `VLLM_IMAGE`, `VLLM_ARGS`, `CONTAINER`, `WAIT_MINS`, `CHECK_TIMEOUT_S` | `vllm_serve.sh` | Docker image, extra server flags, container name, boot wait (25 min), check timeout (60 s) |

## Makefile variables

Set them on the command line, for example `make up API_PORT=8001`.

| Variable | Default | Used by |
|---|---|---|
| `PY` | `.venv/bin/python` (or `.venv/Scripts/python.exe`) if present, else `python3` | every Python command |
| `URL` | `http://localhost:8000` | `make smoke`, `make ui` |
| `API_PORT`, `UI_PORT` | `8000`, `8501` | `make up`, `make ui` |
| `DB` | `var/app.db` | `make seed`, `make failures` |
| `PYTEST_ARGS` | empty | appended to `make test` |
| `LIVE` | unset | `make warm LIVE=1` records with the live chain |

## Recommended combinations

| Goal | Settings |
|---|---|
| Local development | `APP_MODE=dev` (default of `make run` and `make up`) |
| Safe public demo | nothing set (public), `GROQ_API_KEY` optional and capped, `ADMIN_TOKEN` if you want the reset endpoint |
| Live WhatsApp | `APP_MODE=event`, `DEMO_MODE=false`, `WEBHOOK_ENABLED=true`, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `WA_PHONE_NUMBER_ID`, `WA_SEND_ENABLED=true`, a `GROQ_API_KEY`, and a `LIVE_LLM_DAILY_CAP` that fits your budget. Add `DRAFT_LLM=true` and `WA_AUTO_SEND=true` only if cleared drafts should go out without a click. See [deployment](../operations/deployment.md#connecting-whatsapp-event-mode). |
| Offline test run | what `make test` sets: `APP_MODE=dev LLM_MODE=fail_all WORKER_ENABLED=false DEMO_MODE=true GEMINI_ENABLED=false` and empty keys |
