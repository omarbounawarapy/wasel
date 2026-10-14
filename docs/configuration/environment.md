# Environment variables

Every environment variable that Wasel, its scripts and its front ends read. [`.env.example`](../../.env.example) is the annotated template for the ones a deployment normally sets; this page also lists the ones it omits.

## How values are loaded

Values are read in two ways, and both see `.env`:

| Reader | Sources | Variables |
|---|---|---|
| `wasel.settings.Settings` (pydantic-settings) | process environment, then the `.env` file in the current working directory | mode, safety, WhatsApp, caps, sandbox, runtime |
| `wasel.envutil.env()`, used by the LLM layer, prompt registry, tracing and scoring config | process environment, then the same `.env` file | `GROQ_API_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `GEMINI_ENABLED`, `EXTRACT_MODEL`, `FALLBACK_MODEL`, `GROQ_BASE_URL`, `GROQ_FALLBACK_ENABLED`, `LLM_DEADLINE_S`, `LLM_MODE` (when called without a mode), `LLM_REPLAY_DIR`, `PROBE_FILE`, `PROMPT_VERSION`, `LLM_REGISTRY`, `TRACE_FILE`, `SCORING_CONFIG` |

In both, a real environment variable wins over the file, and an empty value counts as unset. So `make run`, `make demo`, a bare `uvicorn wasel.main:create_app --factory`, `make eval-live`, `make warm LIVE=1` and `make failures-llm` all see the provider keys in `.env`, run from the repository root. `make up`, `make serve` and `scripts/ops/wa_webhook_up.sh` additionally export the file into the shell through `scripts/dev/loadenv.py`, which makes every variable, including ones the app never reads, visible to child processes. The loader parses the file with python-dotenv, as the app does, and quotes every value, so a shell never evaluates it. `make llm-check` and `scripts/ops/vllm_serve.sh` load it the same way, under a `DOTENV_` prefix. The test suite disables the file (`Settings.model_config["env_file"] = None`), which also disables the fallback in `env()`.

Quoting follows python-dotenv: a value with spaces needs quotes (`VLLM_ARGS="--gpu-memory-utilization 0.92 --max-model-len 16384"`), single quotes keep everything literal, and `$`, backticks and `$(...)` are plain characters (a `${NAME}` inside an unquoted or double-quoted value is expanded by python-dotenv, not by a shell). No shell ever runs the file.

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
| `SEED_ON_BOOT` | `auto` | `auto`, `always`, `if_empty`, `never` | `auto` resolves to `always` in `public` mode, else `if_empty`. `always` deletes the database file and rebuilds it. `never` creates the schema and the product catalog but no demo orders. The catalog from `data/catalog.yaml` is written at every boot in every mode, so an edit takes effect after a restart. |
| `DB_PATH` | `var/app.db` | path | The SQLite file. Its parent directory is created if needed. |
| `DEMO_MODE` | `true` | bool | Selects the short timings: debounce 4 s and no-reply timeout 60 s instead of 15 s and 6 h. Set `false` for a real deployment. |
| `WORKER_ENABLED` | `true` | bool | `false` starts no worker loop. Tests and `make seed` use this. |
| `API_TOKEN` | empty | at least 24 characters | Outside public mode, `/api` and `/docs` need it (`Authorization: Bearer`, `X-Api-Token` or the session cookie). Empty or short: no check. `/api/health`, `/api/session` and `/api/admin/*` stay open. |
| `ADMIN_TOKEN` | empty | at least 24 characters | Mounts `POST /api/admin/reset`, checked in the `X-Admin-Token` header. Empty or short: the admin router does not exist. |

## Secrets

Never commit these. `.env` is git-ignored and `make hygiene` fails on key-shaped strings.

| Variable | Used for |
|---|---|
| `GROQ_API_KEY` | Groq API key (the hosted backup when `SELF_HOSTED_API_KEY` is set). Without `SELF_HOSTED_API_KEY`, it is also the token of the server at `GROQ_BASE_URL`, as before. |
| `SELF_HOSTED_API_KEY` | empty | Token of the self-hosted server at `GROQ_BASE_URL` (the AMD host). Read only when `GROQ_BASE_URL` is set. When set, `GROQ_API_KEY` becomes the hosted backup behind it. |
| `GEMINI_API_KEY` | Gemini fallback |
| `WA_TOKEN` | WhatsApp Cloud API bearer token (sending) |
| `WA_APP_SECRET` | Meta app secret: webhook signature check. At least 16 characters to mount the webhook. |
| `WA_VERIFY_TOKEN` | Webhook verification handshake. At least 24 characters to mount the webhook. |
| `ADMIN_TOKEN` | Admin reset endpoint |

## LLM

| Variable | Default | Effect |
|---|---|---|
| `LLM_MODE` | `live` | `live`, `replay`, `fail_primary`, `fail_groq`, `fail_all`. See [LLM layer](../subsystems/llm.md#test-and-drill-modes). |
| `EXTRACT_MODEL` | `routing.primary` in `llm.yaml` (`openai/gpt-oss-120b`) | Model of the primary step |
| `FALLBACK_MODEL` | `routing.fallback_model` (`openai/gpt-oss-20b`) | Model of the second Groq step |
| `GROQ_BASE_URL` | empty (= Groq) | Point the primary Groq step at any OpenAI-compatible server (the AMD host). Needs `SELF_HOSTED_API_KEY`, or `GROQ_API_KEY` as its token. |
| `LLM_SERVING_LABEL` | empty | Hardware and server shown in `/api/health` (`llm.serving_label`) and the header tooltip, for example `AMD Instinct MI300X, ROCm, vLLM`. Only reported when `GROQ_BASE_URL` is set; `llm.serving_host` carries the host name of that URL. Set it to what the endpoint really runs; `make llm-serve` prints a line built from the GPU name the host itself reports. |
| `GROQ_FALLBACK_ENABLED` | `true` | `false` removes the second Groq step |
| `GEMINI_ENABLED` | `false` | Gemini needs this set to `true` **and** `GEMINI_API_KEY` **and** `GEMINI_MODEL` |
| `GEMINI_MODEL` | empty | A Flash-class model id from your Gemini account |
| `PROBE_FILE` | `config/probe.json` | Optional JSON describing how your Gemini account wants the schema written. The file is absent from the repository; built-in defaults apply. |
| `LLM_DEADLINE_S` | `20` (or `routing.deadline_s`) | Total time budget of one chain run |
| `PROMPT_VERSION` | unset | Overrides the active extract prompt version from `llm.yaml`. Both the cache key and the cache lookup use the resulting version, so the cache stays consistent. Must be listed in `llm.yaml`, otherwise startup fails with `PromptVersionMismatch`. A new extract version needs `make warm` before deploy because the seed cache is keyed on the version. Leave unset normally. |
| `DRAFT_LLM` | `false` | Enables the LLM rewrite and judge for outbound drafts |
| `LLM_REGISTRY` | `config/llm.yaml` | Alternative registry file |
| `TRACE_FILE` | unset | Append every LLM trace record to this JSONL file |
| `LLM_REPLAY_DIR` | `data/llm_replay` | Directory of recorded provider responses used by `LLM_MODE=replay`. Startup fails with a clear error if it has no `*.json` fixtures. |

## Caps and sandbox

| Variable | Default | Effect |
|---|---|---|
| `LIVE_LLM_DAILY_CAP` | empty = mode default (public 80, event 300, dev none) | Provider calls per UTC day, counting fallback hops and failed attempts. `0` disables live calls. |
| `LIVE_LLM_TOKENS_PER_MODEL_DAY` | empty = mode default (public 120000, others none) | Input plus output tokens per model per UTC day; at the limit calls fall back to the rules path. |
| `VISITOR_LLM_CAP_10MIN` | `6` | Provider calls per visitor in 10 minutes (public mode) |
| `VISITOR_LLM_CAP_DAY` | `20` | Provider calls per visitor per UTC day (public mode) |
| `SANDBOX_TTL_S` | `7200` | Age after which a visitor's conversations are purged |
| `SANDBOX_MAX_ORDERS` | `15` | Orders per visitor (429 `SANDBOX_LIMIT`) |
| `CLIENT_IP_HEADER` | empty | Public mode: a header your proxy overwrites on every request (for example `CF-Connecting-IP` when Cloudflare is in front). Per-address limits count under it. Empty uses the socket address; a loopback or private peer means an unknown proxy, so only the per-visitor limits apply. Never name a header a client can set freely, such as `X-Forwarded-For` |
| `ADDR_WRITES_10MIN` | `30` | Public mode: write requests per client address per 10 minutes (429 `RATE_LIMITED` with `Retry-After`). A new visitor id does not reset it |
| `ADDR_SANDBOX_ORDERS` | `30` | Public mode: sandbox orders one address may create per `SANDBOX_TTL_S` (429 `RATE_LIMITED`) |
| `ADDR_LLM_SHARE` | `0.25` | Public mode: share of `LIVE_LLM_DAILY_CAP` that all the visitor ids seen from one address may use together; over it, scoring uses the rules path |
| `SANDBOX_GLOBAL_MAX` | `500` | Sandbox orders in total (429 `DEMO_BUSY`) |
| `PURGE_INTERVAL_S` | `600` | How often the purges run |
| `RETENTION_EVENTS_DAYS` | `90` | Any mode: `events` older than this are deleted at each purge. `0` keeps them all |
| `RETENTION_LLM_USAGE_DAYS` | `30` | Any mode: `llm_usage` rows older than this are deleted (the daily cap only needs today). `0` keeps them all |
| `RETENTION_EXTRACTION_RUNS_DAYS` | `30` | Any mode: `extraction_runs` older than this are deleted, except the run behind an order's current score. `0` keeps them all |
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
| `SNAPSHOT_URL` | empty (off) | `file:///abs/path` or `http(s)://…` store the SQLite file is restored from at boot and saved to while running; for hosts with an ephemeral disk. Ignored when `SEED_ON_BOOT` resolves to `always`. A store that errors (other than "no snapshot yet") stops startup |
| `SNAPSHOT_INTERVAL_S` | `60` | Minimum seconds between background snapshot saves (a save happens only if the DB changed, and once at shutdown). Two events do not wait for it: a WhatsApp webhook is answered 200 only after the snapshot holds it (503 if the save fails, so Meta retries), and a send is saved before the request returns. A crash therefore loses at most the changes made by the worker since the last interval (scores, drafts), which are re-armed at the next boot |
| `GIT_SHA` | `dev` | Shown in `/api/health` `build.git_sha` |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS origin allowed in `dev` mode, and the one other origin that may send a state-changing request outside `public` mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]` | `Host` values the API accepts in `dev` and `event` mode (anything else gets `400 BAD_HOST`, which stops DNS rebinding). Add the public hostname when you publish the app through a tunnel. Not applied in `public` mode, where platform hostnames vary. A `POST`, `PUT`, `PATCH` or `DELETE` that carries an `Origin` other than its own host or `FRONTEND_ORIGIN` gets `403 BAD_ORIGIN`; requests without `Origin` (curl, the dashboard, the Meta webhook) are unaffected |
| `SCORING_CONFIG` | `config/scoring.yaml` | Alternative scoring file |
| `LOG_LEVEL` | `INFO` | Root logger level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`). Controls the verbosity of boot messages and worker logs. |
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
