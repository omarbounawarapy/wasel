# Deployment and operations

Wasel runs as one Python process (`make serve`) on an always-on machine. A Cloudflare Tunnel can publish it on a stable HTTPS address without opening any port. This page covers the **self-hosted** target: a checkout on a host, started by `make serve` (directly or under systemd). For a free public demo see [Deploying on Render](render.md). To run on Cloudflare's own platform (Worker, Container and R2, no host to maintain, paid plan) see [Deploying on Cloudflare](cloudflare.md). The targets are independent and share no infrastructure.

```
 browser ─────HTTPS──▶ Cloudflare (your hostname, TLS)
 Meta webhook ─HTTPS──▶      │  Cloudflare Tunnel (outbound-only connection)
                             ▼
        always-on host:  cloudflared ──▶ make serve = one Uvicorn process on 127.0.0.1:8000
                                          /api/*, /webhook/whatsapp (when enabled), web UI at /,
                                          worker loop, SQLite in var/app.db
        optional:        GPU host running vLLM ◀── HTTPS ── the LLM layer (GROQ_BASE_URL)
```

What `make serve` does: it loads `.env` (parsed, never run as shell code), prints `Wasel on http://HOST:PORT mode=<mode>`, and runs `uvicorn wasel.main:create_app --factory --host $HOST --port $PORT --workers 1`. The worker count must stay at one: the process owns the SQLite file and runs the in-process worker loop, so a second worker would duplicate the loop and the sandbox purge. `make tunnel` runs `cloudflared tunnel run` with the token from `.env`. `make deploy` updates the checkout. `deploy/wasel.service` is a systemd unit for Linux. The Streamlit dashboard (`make up`, `make ui`) is not part of this setup: it has no login and listens on `127.0.0.1` (`UI_HOST`), so publish it only behind an access-controlled tunnel or reverse proxy. Nothing else is provisioned.

## Requirements

| Item | Notes |
|---|---|
| A host | Linux VPS or PC that stays on, at least 1 GB RAM, Python 3.11, Node 22, git, make. `cloudflared` if you use the tunnel. |
| Repository checkout | Wasel resolves `config/`, `data/`, `models/` and `web/dist` relative to the checkout. It cannot run from an installed package alone. |
| Committed artifacts | `models/risk_xgb_v1.json` (without it scoring drops to the documented prior and says so in every reason), `data/seed/extraction_cache.jsonl`, `data/reports/impact.json` and `eval.json`. All are in the repository. |
| Built web UI | `web/dist`, from `make web`. Without it `/` returns 404 and only `/api` is available. |
| Cloudflare account and a domain on Cloudflare | Only if you publish through a tunnel. The free plan is enough. |
| Secrets | A Groq API key (with a spending cap), an `ADMIN_TOKEN` of at least 24 random characters if you want the reset endpoint, the tunnel token, and WhatsApp secrets only in `event` mode. |
| Outbound network | HTTPS to `api.groq.com` (and Gemini or your vLLM host if used), `graph.facebook.com` for WhatsApp, and to Cloudflare for the tunnel. |

## 1. Cloudflare (once)

The console layout changes; the intent of each step is what matters.

1. Add your domain to Cloudflare (free plan) and change the registrar's nameservers until the domain is Active.
2. Create a **named tunnel** of type Cloudflared, for example `wasel`. The page shows an install command containing a long token that starts with `eyJhIjoi`. Copy only the token. It is a secret and belongs only in the host's `.env` (`CLOUDFLARE_TUNNEL_TOKEN`).
3. Add a public hostname route: subdomain `wasel`, your domain, service `http://localhost:8000`.
4. Set SSL/TLS encryption to Full and turn on Always Use HTTPS.
5. Do not put Cloudflare Access in front of the hostname if visitors should reach it without an account.

The public URL shows Cloudflare error 1033 until the tunnel connects.

## 2. Prepare the host (once)

```bash
git clone <repository-url> wasel && cd wasel
python3.11 -m venv .venv
make setup            # Python dependencies and the package
make web              # builds web/dist, which make serve serves at /
cp .env.example .env  # then edit it
chmod 600 .env        # it will hold WA_TOKEN, WA_APP_SECRET and the provider keys
install -d -m 700 var # the SQLite file and its -wal/-shm files live here
```

Install `cloudflared` from Cloudflare's downloads (on Windows, save the executable as `~/.local/bin/cloudflared.exe`, where `make tunnel` looks for it).

Host `.env` for **public mode**, the default and the safe choice for anonymous visitors:

| Key | Value |
|---|---|
| `APP_MODE` | empty (means public) |
| `GROQ_API_KEY` | a capped key. Optional: without it the app runs on recorded extractions and rules. |
| `LIVE_LLM_DAILY_CAP` | optional; public mode defaults to 80 provider calls per day |
| `ADMIN_TOKEN` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CLOUDFLARE_TUNNEL_TOKEN` | the token from step 1.2 |
| `HOST`, `PORT` | `127.0.0.1`, `8000`: only the tunnel on this machine reaches the app. `0.0.0.0` exposes the port to the network. |
| `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` | empty: a public host must not hold WhatsApp secrets |
| `WA_AUTO_SEND`, `DRAFT_LLM` | `false` |

**Public mode deletes the database on every start** (`SEED_ON_BOOT=auto` resolves to `always`): the schema is rebuilt and the nine sample orders are reseeded. That is intended for a stateless demo. A deployment that must keep data needs `APP_MODE=event` (or `dev`) with the default `SEED_ON_BOOT`, which keeps existing rows.

The full variable reference is [configuration/environment.md](../configuration/environment.md).

## 3. Run

Quickly, in two terminals:

```bash
make serve     # the app on 127.0.0.1:8000, mode from .env
make tunnel    # connects the tunnel; the public URL starts answering
```

Always on, on Linux:

1. Copy `deploy/wasel.service` to `/etc/systemd/system/wasel.service` and edit `User` (default `wasel`) and `WorkingDirectory` (default `/opt/wasel`). The unit runs `ExecStart=/usr/bin/make serve` with `Restart=always` and `RestartSec=3`, after `network-online.target`. Adjust the path if `make` is elsewhere (`command -v make`). The Makefile finds `.venv` under the working directory, so the virtual environment and `.env` must be there and readable by that user (keep `.env` at mode 600 and `var/` at 700). The unit sandboxes the process: `NoNewPrivileges`, `ProtectSystem=strict` with only `/opt/wasel/var` writable, `ProtectHome`, `PrivateTmp`, no capabilities, no raw sockets, `UMask=0077`, `MemoryMax=1G`, `TasksMax=256`. Keep the checkout under `/opt/wasel` (a path under `/home` is hidden by `ProtectHome`) and check the result with `systemd-analyze security wasel`. The app creates the database with mode 600 whatever the umask.
2. `sudo systemctl daemon-reload && sudo systemctl enable --now wasel`.
3. Install the tunnel as its own service: `sudo cloudflared service install <CLOUDFLARE_TUNNEL_TOKEN>`.

On Windows, run `cloudflared service install <token>` in an admin terminal and start `make serve` at logon with Task Scheduler.

## 4. Verify (after every deploy and every mode change)

```bash
make smoke URL=https://wasel.<your-domain>
```

`SMOKE PASS ... public v1=87 v2=16` means health, the UI, the score-and-reply loop and the read-only samples all work. Then check by hand:

1. `/api/health` shows `mode=public`, `wa_send=false`, `webhook=disabled`, `wa_auto_send=false`.
2. `POST /webhook/whatsapp` returns 404 or 405.
3. The queue shows only sample orders.
4. "Try this order" on a sample runs the full loop.
5. A second private browser window does not see the first window's copy.
6. `/api/metrics/impact` shows `simulated: true`.

CI performs the equivalent checks on every push: it builds the web UI, starts `make serve` with no `.env`, asserts safe public defaults, confirms the UI is served and runs the smoke test.

## Operating

### Health and monitoring

`GET /api/health` is the liveness and safety check (there is no separate readiness endpoint). Alert on `worker.last_tick_at` older than about 10 seconds (the endpoint itself reports `degraded` then), on `mode`, `wa_send`, `webhook` or `wa_auto_send` differing from what you deployed, and on `llm.cap_reached`. `status: degraded` also appears for five minutes after any fallback extraction path was used, which includes the rules path when no LLM is configured, so a keyless host will show `degraded` while orders are being scored. `GET /api/monitor` reports drift and safety rates ([monitoring](../subsystems/monitoring.md)). `llm.live_calls_today` against `live_call_cap` shows the budget.

### Logs

The application configures no logging of its own. Uvicorn writes its access log and start-up lines to standard error, and Python's default handler prints warnings and errors from the application's loggers (`cod.settings`, `cod.main`, `cod.worker`, `cod.webhook`, `cod.wa_send`). Informational application messages are not emitted by default. Under systemd everything goes to the journal:

```bash
journalctl -u wasel -f
```

What to look for: `unknown APP_MODE ... -> public` (a typo in the mode), `webhook rejected: <reason>` (bad signature), `webhook verify refused`, `webhook process_error: <ExceptionType>`, `rescore failed for <order>` with a traceback (an order was moved to `needs_review`), `worker tick failed`, and `whatsapp send ... failed`. An `error` event holds only the exception type; the message and traceback are in the log, never in the feed. The activity feed and `GET /api/events` carry the same events as `events` rows (`error`, `webhook.rejected`, `llm.fallback`, `llm.cap_reached`, `draft.send_failed`). Logs never contain message bodies, sender numbers or secrets, and the webhook's verify token is redacted from the access log. Set `TRACE_FILE` to keep every LLM trace record (no customer text) in a JSONL file.

### Restart

```bash
sudo systemctl restart wasel     # or Ctrl-C and re-run make serve
```

Settings, prompts, `config/*.yaml` and the model file are read at start, so a restart is how any of them take effect. In public mode a restart also resets the database. Rescores that were pending in the database are resumed on the next start.

### Update

```bash
make deploy                      # git pull --ff-only, then make setup web
sudo systemctl restart wasel
make smoke URL=https://wasel.<your-domain>
```

`make deploy` does not restart anything. If the pull changed `db/schema.sql`, an existing database (in `event` or `dev` mode) is **not** migrated: the schema is only created when the file is missing. Check the change log and the diff first, and plan a rebuild or a manual migration for a database you want to keep.

### Roll back

```bash
git checkout <tag-or-sha> && make setup web
sudo systemctl restart wasel
make smoke URL=https://wasel.<your-domain>
```

To roll back only an LLM prompt, use `python scripts/ops/rollback.py <role> <version>`, commit, and restart ([registry](../configuration/llm-registry.md#procedures)). Rolling code back does not roll back a database schema; see the note above.

### Data and backups

The only state is `var/app.db` (and its `-wal` and `-shm` files). In public mode it holds nothing worth keeping and is rebuilt on start. In `event` mode it holds real conversations, phone numbers and decisions: stop the process or use SQLite's online backup (`sqlite3 var/app.db ".backup 'backup.db'"`) rather than copying the file while it is being written. `make clean` and any start in public mode delete it. `POST /api/admin/reset` empties the order tables and reseeds, keeping the catalog, extraction cache and LLM usage.

### Cache warming

`make warm` is a development step, not an operational one. It rebuilds `data/seed/extraction_cache.jsonl`, the recorded extractions that make the nine sample orders score identically with no LLM call. You need it after changing a sample conversation, a template's canonical text, the window rules or the extract prompt version. In production the persistent cache also fills by itself: every successful primary-model extraction is stored in the `extraction_cache` table, and an identical conversation window later costs no call.

### Cost and rate controls

A capped API key at the provider is the outermost limit. Inside the app, `LIVE_LLM_DAILY_CAP` bounds provider calls per UTC day (attempts, including fallbacks and failures, all count), and in public mode the per-visitor caps apply. Reaching a cap degrades to the rules path, never to an error. `GET /api/health` reports the counts.

## Connecting WhatsApp (`event` mode)

`APP_MODE=event` allows the webhook and real sends. Use it only with a phone number registered in your Meta app, and never on a host that serves anonymous visitors.

1. In `.env` set `APP_MODE=event`, `DEMO_MODE=false` (real timings: 15 s debounce, 6 h no-reply timeout), `WA_TOKEN`, `WA_APP_SECRET` (at least 16 characters), `WA_VERIFY_TOKEN` (at least 24), `WA_PHONE_NUMBER_ID`, `WEBHOOK_ENABLED=true`, `WA_SEND_ENABLED=true`, a `GROQ_API_KEY`, and a `LIVE_LLM_DAILY_CAP` that fits your budget (the event default is 300). Add `DRAFT_LLM=true` and `WA_AUTO_SEND=true` only if cleared replies should go out without a click.
2. Restart. `/api/health` must show `mode=event` and `webhook=enabled`.
3. In the Meta console (your app, WhatsApp, Configuration) set the callback URL to `https://wasel.<your-domain>/webhook/whatsapp`, the verify token to `WA_VERIFY_TOKEN`, and subscribe to the `messages` field.
4. Send a message from a registered phone and check that it appears under WhatsApp messages.

To return to public mode: empty `APP_MODE`, remove the WhatsApp secrets, set `WEBHOOK_ENABLED=false` and `WA_AUTO_SEND=false`, restart (public mode reseeds, which removes the real rows), remove the callback in the Meta console, then run the verification in section 4. For testing without a permanent host, see [WhatsApp](../subsystems/whatsapp.md#testing-locally).

## Secrets

- `.env` stays on the host and is git-ignored. `make hygiene` (part of `make check` and CI) fails on key-shaped strings, including tunnel tokens.
- The secrets are the tunnel token, API keys, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` and `ADMIN_TOKEN`. The hostname is not secret.
- When retiring a deployment, delete the tunnel or rotate its token, revoke `WA_TOKEN` and the API keys, and rotate `ADMIN_TOKEN`.

## Trying it without a domain

`cloudflared tunnel --url http://localhost:8000` prints a random `https://....trycloudflare.com` address. It needs no account but changes on every restart, so it is not suitable for a link you share or for a permanent Meta callback.

## Common operational failures

| Symptom | Cause |
|---|---|
| Cloudflare error 1033 | The tunnel is not connected: `make tunnel` or the cloudflared service is not running |
| 502 Bad Gateway | The tunnel is up but `make serve` is not running, or the route's service URL is not `http://localhost:8000` |
| Health shows the wrong `mode` | `APP_MODE` in the host `.env`; empty means public |
| `/` answers 404 or shows a blank page | `web/dist` is missing or stale: run `make web` after every pull |
| The service restarts in a loop | `journalctl -u wasel`: a `PromptVersionMismatch`, an invalid `.env` value, or a missing `.venv` for `User` |
| Data vanished after a restart | Public mode reseeds on start; see section 2 |
| Every new order is `needs_review` with `path=rules` | No provider is configured or reachable. Check `llm.chain_extract` in `/api/health`, that `GROQ_API_KEY` is in the process environment or in the `.env` next to the working directory, and `llm.cap_reached` |

More symptoms and how to diagnose them: [troubleshooting](troubleshooting.md).
