# Deploying on Cloudflare

Wasel can run on Cloudflare as **one Worker in front of one Container**, with an **R2 bucket** that keeps the database across container restarts. The self-hosted path (`make serve` plus a Cloudflare Tunnel, see [deployment.md](deployment.md)) is unchanged; pick one per environment.

This guide separates what was **verified** on a development machine from what needs your Cloudflare account. Section 9 lists both.

## 1. Architecture

```
 browser ───HTTPS──▶  Worker  wasel-<env>                       (deploy/cloudflare/worker/src/index.ts)
 Meta webhook ─────▶   │
                       ├─ /api/*  /webhook/*  /docs  /openapi.json ─▶ Container "primary"  (FastAPI, port 8000)
                       │                                               │  worker loop, scorer, SQLite in /data/app.db
                       │                                               ├─ HTTPS ─▶ Groq / Gemini / graph.facebook.com
                       │                                               └─ http://state.wasel.internal/snapshot
                       │                                                      │ (intercepted by the Worker, never leaves Cloudflare)
                       │                                                      ▼
                       │                                                  R2 bucket  wasel-state-<env>
                       │                                                  wasel.sqlite, wasel.sqlite.prev
                       └─ everything else ─▶ static assets  (web/dist, the Next.js export, served at the edge)
 Cron (production) ──▶ Worker.scheduled ──▶ keeps the container awake outside public mode
```

| Piece | Why it exists |
|---|---|
| **Worker** | Serves the static UI from the edge (no container wake-up for page loads), routes API and webhook traffic to the container, rejects bodies over 1 MiB before they reach it, and hands the container its environment. |
| **Container** (`deploy/cloudflare/container/Dockerfile`) | The backend needs Linux, xgboost and numpy, one SQLite file and a 1-second in-process worker loop. That does not fit Python Workers (Pyodide) and cannot be split across isolates. Exactly one instance (`max_instances: 1`), addressed by a fixed name. |
| **R2 bucket** | A container's disk is wiped whenever it sleeps. `wasel.db.snapshot` restores the SQLite file from R2 at boot, saves it back at most every `SNAPSHOT_INTERVAL_S` (60 s) when it changed, and once more on shutdown (SIGTERM, up to 15 min of grace). The Worker keeps one previous generation (`wasel.sqlite.prev`). The container reaches R2 through a Worker outbound handler, so it holds no Cloudflare credential. |
| **Cron** (production only) | Outside `public` mode, no-reply timeouts must fire while nobody is browsing, so the cron pings the container every 5 minutes. In `public` mode it does nothing and the container sleeps after `CONTAINER_SLEEP_AFTER` (15 m). |

Not used, on purpose: **D1** (the repository layer is synchronous `sqlite3` with `BEGIN IMMEDIATE` and compare-and-swap claims; D1 has no interactive transactions, so using it would be a rewrite), **KV**, **Queues** (the worker loop already runs inside the container), **vinext** (the web UI is a client-only static export with no server features).

### What lives where

| Component | Classification | On Cloudflare |
|---|---|---|
| FastAPI app, worker loop, scorer, XGBoost | Container required | Container |
| SQLite database | Mutable state | Container disk + R2 snapshot |
| `config/`, `models/`, runtime `data/` files | Immutable deployment assets | Baked into the image |
| Extraction cache, usage counters, events | Persistent state (tables in the same SQLite file) | Snapshotted with it |
| LLM trace ring buffer (`/api/traces`) | Process-local, lost on restart (`TRACE_FILE` is not set) | Container memory |
| Next.js UI (`web/`) | Frontend-only, static export | Worker static assets |
| Streamlit dashboard (`dashboard/`) | Needs a conventional Python server; a second UI over the same API | **Not deployed.** Run it locally with `make ui API_BASE_URL=https://<your worker URL>`. |
| Training, generation, evaluation (`wasel.ml`, `wasel.evaluation`, `data/synth_v1.csv`, `data/eval/`, pandas) | Development / training | **Not in the image** (`.dockerignore`, `deploy/cloudflare/container/requirements.txt`) |
| `make serve`, `make tunnel`, `deploy/wasel.service` | Self-hosted | Unchanged, not used on Cloudflare |

### Mode and durability

`SEED_ON_BOOT` decides whether the database is durable. Snapshots are disabled (with a log warning) when it resolves to `always`, because the database is rebuilt at every boot. The shipped environments use `if_empty`, so visitor sandboxes and (in `event` mode) real conversations survive restarts. After deploying a changed demo seed, reseed once with `POST /api/admin/reset` (needs `ADMIN_TOKEN`).

Data-loss window: writes made after the last snapshot are lost if the container dies without a graceful stop (up to `SNAPSHOT_INTERVAL_S`). If a restore fails (R2 unreachable, corrupt or foreign file) the container **refuses to start** and the Worker answers 503/500, rather than booting empty and overwriting the last good snapshot. If saves keep failing, `/api/health` reports `status: "degraded"`.

## 2. Files

| Path | Purpose |
|---|---|
| `deploy/cloudflare/wrangler.jsonc` | Worker, assets, container, Durable Object, R2 binding, cron. Top level = local dev; `env.preview`, `env.production` |
| `deploy/cloudflare/worker/src/index.ts`, `snapshot.ts` | Router, `Container` subclass, R2 snapshot endpoint |
| `deploy/cloudflare/container/Dockerfile`, `requirements.txt` | Backend image (linux/amd64, Python 3.11, non-root, no pandas, `xgboost-cpu`) |
| `deploy/cloudflare/container-env.json` | The only variables and secrets handed to the container |
| `deploy/cloudflare/.dev.vars.example` | Local secrets template |
| `web/public/_headers` | Security headers for edge-served assets (mirrors `SECURITY_HEADERS` in `src/wasel/main.py`) |
| `.dockerignore` | Build context allow-list |
| `scripts/ops/cf_check.py`, `cf_local_smoke.py` | Offline checks and the local image smoke test |

Wrangler does not inherit `vars`, `assets`, `containers`, `durable_objects`, `exports` or `r2_buckets` into named environments, so each environment repeats them; `make cf-check` fails if one drifts or is missing.

## 3. Prerequisites

- A Cloudflare account on the **Workers Paid** plan (Containers are not on the Free plan).
- Node 22 and Docker running locally (`docker info`); `wrangler deploy` builds the image on your machine.
- `make setup` and `make cf-install`.
- `npx wrangler login` (from `deploy/cloudflare`), or `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in the shell for CI.

## 4. Values you substitute

| Where | What | Default in the repo |
|---|---|---|
| `wrangler.jsonc` `name` per environment | Worker names | `wasel-dev`, `wasel-preview`, `wasel-production` |
| `wrangler.jsonc` `r2_buckets[].bucket_name` | Bucket per environment | `wasel-state-dev`, `-preview`, `-production` |
| `wrangler.jsonc` `vars` | Non-secret settings (table in section 6) | Safe: `public` mode, sending and webhook off |
| Custom domain | Add to the environment: `"routes": [{ "pattern": "wasel.yourdomain.com", "custom_domain": true }]` | None: deployed on `*.workers.dev` |
| `NEXT_PUBLIC_SITE_URL` at web build | Public origin for absolute metadata URLs | `http://localhost:5173` |
| Secrets | `wrangler secret put` (section 6) | None |

No account IDs, database IDs or hostnames are committed.

## 5. Local testing (no Cloudflare account)

```bash
make cf-install
make cf-check        # config consistency, Worker typecheck and unit tests. No Docker, no account
make cf-smoke        # builds the image, runs it (docker or podman), then:
                     #   boots keyless as uid 10001, passes scripts/ops/smoke.py,
                     #   keeps its orders across a wiped container disk (file:// snapshot store),
                     #   refuses to boot on a corrupt snapshot and leaves that file untouched
make cf-dry-run ENV=preview   # wrangler validates the config and builds the image; uploads nothing
```

`make cf-dev` runs `wrangler dev` (Worker, static assets, container and a local R2 simulation) on <http://localhost:8787>. Copy `deploy/cloudflare/.dev.vars.example` to `.dev.vars` first if you want keys; with none, extraction falls back to rules and nothing is sent to WhatsApp. It needs a working Docker; the R2 snapshot path is only exercised there (section 9).

Everything on `make test`, `make check`, `make serve`, `make ui` and the other targets is unchanged.

## 6. Environment and secrets

Secrets are **names only** here; set them per environment with `npx wrangler secret put <NAME> --env <preview|production>` (run in `deploy/cloudflare`). Never put them in `wrangler.jsonc`; `make cf-check` and `make hygiene` fail if a secret name or key-shaped value appears in `vars`.

| Variable | Sensitive | Local (`make serve`, `.env`) | Cloudflare | Default |
|---|---|---|---|---|
| `GROQ_API_KEY` | secret | `.env` | `wrangler secret put` | none: rules path |
| `GEMINI_API_KEY` | secret | `.env` | `wrangler secret put` | none |
| `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` | secret | `.env` | `wrangler secret put` (`event` mode only) | none |
| `ADMIN_TOKEN` (≥ 24 chars) | secret | `.env` | `wrangler secret put` | none: `/api/admin` not mounted |
| `APP_MODE`, `SEED_ON_BOOT`, `DEMO_MODE`, `WORKER_ENABLED` | no | `.env` | `vars` | `public`, `if_empty` (see above), `true`, `true` |
| `LLM_MODE`, `DRAFT_LLM`, `EXTRACT_MODEL`, `FALLBACK_MODEL`, `GROQ_BASE_URL`, `GROQ_FALLBACK_ENABLED`, `GEMINI_ENABLED`, `GEMINI_MODEL`, `LLM_DEADLINE_S`, `PROMPT_VERSION` | no | `.env` | `vars` (add to the environment's `vars` to override) | see [environment.md](../configuration/environment.md) |
| `LIVE_LLM_DAILY_CAP`, `VISITOR_LLM_CAP_10MIN`, `VISITOR_LLM_CAP_DAY`, `SANDBOX_TTL_S`, `SANDBOX_MAX_ORDERS`, `PURGE_INTERVAL_S` | no | `.env` | `vars` | mode defaults |
| `WA_SEND_ENABLED`, `WA_AUTO_SEND`, `WEBHOOK_ENABLED`, `WA_PHONE_NUMBER_ID`, `WA_API_VERSION` | no | `.env` | `vars` | off |
| `SNAPSHOT_URL`, `SNAPSHOT_INTERVAL_S` | no | unset (off) | `vars`: `http://state.wasel.internal/snapshot`, `60` | off |
| `GIT_SHA` | no | `.env` | set by `make cf-deploy` (`--var GIT_SHA:<sha>`) | `dev` |
| `CONTAINER_SLEEP_AFTER` | no | n/a | `vars`, read by the Worker | `15m` |
| `DB_PATH` | no | `.env` | fixed to `/data/app.db` in the image | `var/app.db` |
| `HOST`, `PORT`, `CLOUDFLARE_TUNNEL_TOKEN`, `META_APP_ID`, `FRONTEND_ORIGIN`, `TRACE_FILE`, `LLM_REPLAY_DIR`, `SCORING_CONFIG` | mixed | `.env` | **not passed** (self-hosting / development only; same-origin means no CORS) | |
| `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_API_URL` | no | build time | build time; leave `NEXT_PUBLIC_API_URL` unset: the UI calls its own origin | |

Configuration loading: on Cloudflare there is no `.env` file. The Worker builds the container's environment from `container-env.json`, and the app reads the process environment (the `.env` fallback in `wasel.envutil` simply finds no file). Locally, `make serve` sources `.env`, and the LLM layer reads `.env` itself, so both see the same values.

The frontend receives no secrets: only `NEXT_PUBLIC_*` values are compiled in, and provider keys exist only inside the container. Only the webhook (`/webhook/whatsapp`, signature-checked and mounted only in `event` mode with its secrets) and the `/api` routes are reachable from the internet; the R2 snapshot endpoint exists only on the internal host `state.wasel.internal`, which the Worker answers for the container.

## 7. Deploy (you run these; nothing here was run against a real account)

Run from the repository root unless noted.

```bash
# once per environment: the bucket (names must match wrangler.jsonc)
cd deploy/cloudflare
npx wrangler r2 bucket create wasel-state-preview
npx wrangler r2 bucket create wasel-state-production

# secrets (prompted; repeat per name you use, per environment)
npx wrangler secret put GROQ_API_KEY --env preview
npx wrangler secret put ADMIN_TOKEN  --env preview
cd ../..
```

`wrangler secret put` targets an existing Worker. For a first deploy of an environment, run the `make cf-deploy` line below first (it starts without keys, in safe rules mode), then set the secrets and deploy once more.

```bash
make cf-check
make cf-deploy ENV=preview        # builds web/dist, builds and pushes the image, uploads the Worker and assets
make smoke URL=https://wasel-preview.<your-subdomain>.workers.dev
make cf-deploy ENV=production
make smoke URL=https://<your production URL>
```

The first request after a deploy or an idle period waits for the container to start (tens of seconds while it pulls, restores the snapshot and warms up); the Worker returns 503 `BACKEND_UNAVAILABLE` if it cannot. Container rollouts are gradual by default (`rollout_step_percentage` 10 % then 100 %).

**WhatsApp (`event` mode):** set `APP_MODE` to `event`, `WEBHOOK_ENABLED` and `WA_SEND_ENABLED` as you need in that environment's `vars`, set the four `WA_*` secrets and `ADMIN_TOKEN`, and register `https://<your host>/webhook/whatsapp` with Meta using the same verify token. See [whatsapp.md](../subsystems/whatsapp.md). Keep the cron; without it the container sleeps and no-reply timeouts do not fire.

### Rollback

- **Code and config:** check out the previous commit and `make cf-deploy ENV=…` again. (`npx wrangler rollback` exists for Worker versions; it has not been exercised against a container rollout here.)
- **LLM prompt/model versions:** `scripts/ops/rollback.py`, then deploy, as before.
- **Data:** public mode on Cloudflare persists the database across restarts (R2 snapshot, `SEED_ON_BOOT=if_empty`), so visitor data lives until the sandbox purge deletes it, and a purge that has not run yet is restored with the snapshot. R2 holds `wasel.sqlite` and the generation before it, `wasel.sqlite.prev`. To recover, copy the wanted object over `wasel.sqlite` (`wrangler r2 object get` / `put`; see `wrangler r2 object --help`), then restart the container by redeploying.

### Monitoring

`npx wrangler tail --env production` streams Worker and container logs (observability is enabled in `wrangler.jsonc`). `/api/health` shows mode, worker tick, LLM path, and `degraded` when snapshots keep failing; `/api/monitor` and `/api/traces` are kept per process, so they are empty after every restart or sleep. `npx wrangler containers list` shows the application and its instances.

## 8. Known limits

- One container instance, one process: no horizontal scaling. `standard-1` or larger is a one-line change to `instance_type` if `basic` (1 GiB) is not enough; the app used about 125 MB resident in the local smoke run.
- The container disk is ephemeral; durability is snapshot-based (RPO up to `SNAPSHOT_INTERVAL_S` on a hard stop).
- Cold start: seconds to tens of seconds; use the cron in non-public modes and a longer `CONTAINER_SLEEP_AFTER` if that matters.
- The Streamlit dashboard is not deployed; the LLM trace ring buffer resets with the container.
- The Worker limits requests to 1 MiB (the container itself enforces 64 KB, 1 MiB for the webhook).
- The container needs outbound internet (`enableInternet`) for Groq, Gemini and WhatsApp.

## 9. Validation status

| Area | Verified on a dev machine | Cloudflare tooling | Not verifiable without an account |
|---|---|---|---|
| Backend image | Builds; boots keyless and non-root; `smoke.py` passes; ~125 MB RSS (`make cf-smoke`) | `wrangler deploy --dry-run` builds it | Running on Cloudflare's runtime, instance sizing |
| Database / snapshots | Restore, periodic and shutdown save, fresh-disk recovery, corrupt/unreachable store refuses boot, save-failure reporting (`tests/integration/test_snapshot.py`, `make cf-smoke`) | | Real R2 latency; the Worker → R2 handler end to end |
| Worker code | Typecheck, snapshot handler unit tests (`npm test`) | `wrangler deploy --dry-run` validates the config for preview | Routing to a live container, `ContainerProxy` interception |
| Frontend | `next build` static export; `_headers` copied to `dist` | Assets binding validated by dry run | Edge caching behaviour |
| Secrets | `cf_check.py` and hygiene block secrets in `vars` | | Uploading them |
| Scheduled jobs | Handler compiled and typechecked | Cron accepted by the config | The trigger firing |
| Dashboard | Unchanged, local only | | Intentionally not deployed |
| `wrangler dev` end to end | Reached "Ready", served static assets, started the container image | | The R2 interception sidecar did not start under rootless podman on the development machine (`Could not bind egress listener`); test `make cf-dev` with Docker |
