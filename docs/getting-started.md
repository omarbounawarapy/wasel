# Getting started

This page takes a fresh clone to a running system, checks it, and shows the first scoring loop. It uses only commands that exist in the [Makefile](../Makefile); [development/commands.md](development/commands.md) explains all of them.

## Prerequisites

| Need | Version | Used for |
|---|---|---|
| Python | 3.11 (`.python-version`; `pyproject.toml` requires `>=3.11`; CI runs 3.11) | backend, tests, dashboard |
| GNU Make | any recent | every command below |
| Node.js | 22 (CI uses 22) | only for the Next.js web UI (`make web`, `make web-dev`) |
| `cloudflared` | current | only for hosting (`make tunnel`, `make wa-up`) |
| A Groq API key | optional | live LLM extraction. Not needed to run, test or evaluate offline |

Linux, macOS and Windows (Git Bash) are handled by the Makefile: it uses `.venv/bin/python` or `.venv/Scripts/python.exe` when a virtual environment exists, otherwise `python3` on the `PATH`.

## Install

```bash
git clone https://github.com/omarbounawarapy/wasel.git && cd wasel
python3.11 -m venv .venv
make setup
```

`make setup` runs `pip install -r requirements.txt -r requirements-dev.txt` and then `pip install --no-deps -e .`. The dependency files pin exact versions. `requirements-dev.txt` also contains Streamlit and Altair, because the dashboard tests run inside `make check`. The editable install makes `import wasel` work from anywhere and lets `uvicorn wasel.main:create_app` find the package.

The checkout must stay where it is. Wasel runs from a repository checkout, not from an installed wheel: `src/wasel/paths.py` resolves `config/`, `data/`, `models/` and `web/dist` relative to the repository root.

## Configure

Nothing is required for a first run. With no environment variables the backend uses the offline path:

- sample orders are scored from the committed extraction cache (`data/seed/extraction_cache.jsonl`), with no LLM call;
- new text is scored by the rules extractor, and those orders are flagged for human review;
- WhatsApp sending and the webhook are off.

To use a live LLM or WhatsApp, copy the template and edit it:

```bash
cp .env.example .env
```

`.env.example` documents every variable it contains. The full reference, including variables that are not in the template, is [configuration/environment.md](configuration/environment.md). Two rules matter on day one:

1. The backend reads `.env` from the working directory for its settings, and the LLM layer reads provider keys from the process environment and then the same `.env`, so a key in `.env` works with every start command run from the repository root.
2. `APP_MODE` decides what is safe to expose. Unset means `public` (the most restrictive mode). `make up` and `make run` default it to `dev`. See [modes](architecture/overview.md#modes).

## Run

| Command | Starts | Mode | Database |
|---|---|---|---|
| `make up` | API on :8000, then the Streamlit dashboard on :8501 | `dev` unless `APP_MODE` is set | **deleted and reseeded on every start** (`SEED_ON_BOOT=always`) |
| `make run` | API on :8000 with auto-reload | `dev` unless set | kept; seeded only if empty |
| `make ui` | dashboard only, against `API_BASE_URL` (default http://localhost:8000) | | |
| `make demo` | API on :8000, serving the built web UI at `/` | `public` | deleted and reseeded on every start |
| `make serve` | API + web UI on `HOST:PORT` (default 127.0.0.1:8000), no reload, settings from `.env` | from `.env`, unset = `public` | per `SEED_ON_BOOT`; `public` reseeds on every start |
| `make web-dev` | Next.js dev server on :5173 with hot reload (start `make run` first) | | |

The database file is `var/app.db` (`DB_PATH`, resolved relative to the repository root). There is no separate initialization step: on startup the app creates the schema from `src/wasel/db/schema.sql` if the file is missing, mirrors `data/catalog.yaml` into the `catalog` table, loads the extraction cache and creates the nine sample orders from `data/seed/demo_seed.json`, scoring them through the worker. `make seed` does the same without starting a server and always rebuilds `var/app.db` from scratch.

Cold start (imports, model load, seeding) can take up to about a minute; `make up` waits up to 180 seconds for `/api/health` before it starts the dashboard.

### Web UI

The Next.js app is built to static files and served by the API at `/`:

```bash
make web        # npm ci && npm run build  ->  web/dist
make demo       # or make serve; open http://localhost:8000/
```

Without `web/dist`, `/` returns a 404 and only `/api` works. For UI development use `make run` in one terminal and `make web-dev` in another; the dev server needs the API in `APP_MODE=dev` for CORS. Details in [interfaces.md](interfaces.md).

## Check that it works

```bash
curl -s localhost:8000/api/health | python3 -m json.tool
```

A healthy fresh start reports `"status": "ok"` and the mode you chose. In `public` mode `wa_send` is `false`, `webhook` is `"disabled"` and `wa_auto_send` is `false`. `status` becomes `"degraded"` when the worker has not ticked for 10 seconds or a fallback extraction path (`fallback_model`, `fallback_provider`, `rules`) was used in the last five minutes. That includes the rules path used for pasted text without an LLM, so a `degraded` status right after pasting an order with no API key is expected.

The end-to-end smoke test drives the real HTTP API and needs no key:

```bash
make smoke                       # against http://localhost:8000
make smoke URL=https://your-host # against any deployment
```

It checks health and `GET /`, scores the sample order #2601 (expects HIGH), replies with the scripted address (expects LOW and a lower score) and, in public mode, that the sample rows are read-only. It ends with `SMOKE PASS ...`. In public mode it copies the sample with `try`, so it works with no key. In `dev` and `event` mode it pastes the sample conversation as new text, which needs a working LLM extractor to reach HIGH.

## First scoring loop

The sample order #2601 is the reference scenario. With the API running:

```bash
.venv/bin/python examples/02_customer_reply_rescore.py
```

```
before the reply:
  #2601  v1  HIGH 87  action=confirm  status=awaiting_reply  path=cascade_cache
customer replies: 'ey behi. Douar Ouled Ali, triq el jemaa, dar 14, el bab lazra9 9odem el pharmacie. ...'
after the reply:
  #2601  v2  LOW 16  action=ship  status=ready_to_ship  path=cascade_cache
  diff:   v1 87 → v2 16 · full address given ("Douar Ouled Ali, triq el jemaa, dar 14") −32 · ...
```

`path=cascade_cache` means the extraction came from the committed cache, not from a fresh LLM call. To score your own text, use `examples/01_score_a_pasted_order.py`, the dashboard's "Paste an order" page, or `POST /api/orders/ingest` (see [api.md](api.md)). The scores you get for new text depend on the extraction path: without a key it is the rules extractor, which always leaves the order in `needs_review`.

## Tests

```bash
make check      # hygiene + ruff + offline test suite + evaluation gate (what CI runs)
make test       # test suite only
make eval       # evaluation gate only
```

`make check` takes about five minutes, most of it the dashboard tests. It needs no keys and no network. It rewrites `data/reports/eval.json` only if results changed; see [testing](development/testing.md) and [evaluation](evaluation.md) before committing after a run.

## Common first-run problems

| Symptom | Cause and fix |
|---|---|
| `make: python3: command not found` or wrong Python | The Makefile uses `.venv` if it exists. Create it with `python3.11 -m venv .venv` before `make setup`. |
| `make up` stops with `API at http://localhost:8000 did not answer /api/health within 180 s` | The API process crashed on start. Run `make run` to see the traceback. A common cause is a prompt file edited without a version bump, which raises `PromptVersionMismatch` at import ([LLM registry](configuration/llm-registry.md)). |
| Port 8000 or 8501 already in use | `make up API_PORT=8001 UI_PORT=8502`. `make ui` needs `API_BASE_URL` to match the API port. |
| `/` returns 404 | `web/dist` does not exist. Run `make web`. |
| `GROQ_API_KEY` is in `.env` but orders still say `path=rules` | The API was not started from the repository root (the `.env` lookup is relative to the working directory), `LLM_MODE` is not `live`, or the provider is failing or capped. `/api/health` shows `llm.chain_extract` (empty means no key was found), `llm.cap_reached` and `llm.fallback_reason`. |
| `POST` calls return `400 VISITOR_ID_REQUIRED` | The API is in `public` mode. Send an `X-Visitor-Id` header containing a UUID v4, or use `APP_MODE=dev`. |
| `409 SEEDED_READ_ONLY` on a sample order | Public mode makes samples read-only. Call `POST /api/orders/{id}/try` to copy one into your sandbox. |
| `/docs` returns 404 | `public` mode disables the Swagger page. `/openapi.json` is still served. |
| Data disappeared after a restart | `SEED_ON_BOOT` resolves to `always` in public mode, and `make up` sets it to `always`. Use `APP_MODE=dev` with `make run` for a persistent database, or set `SEED_ON_BOOT=if_empty`. |

More symptoms and diagnostics are in [operations/troubleshooting.md](operations/troubleshooting.md).

## Next steps

- Understand the system: [architecture overview](architecture/overview.md), then the [order pipeline](architecture/order-pipeline.md).
- Change behaviour: [configuration](configuration/README.md).
- Change code: [development/extending.md](development/extending.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
- Run it for other people: [operations/deployment.md](operations/deployment.md).
