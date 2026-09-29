# API

Wasel's HTTP API is the only interface to the system. The web UI, the Streamlit dashboard, the smoke test and the example scripts are all clients of it. This page explains the contract: how to start it, who may call what, the shape of the data, and how errors and modes behave. For every request and response field, use the generated OpenAPI documentation, which is always current:

- `GET /docs` (Swagger UI) in `dev` and `event` mode. It is disabled in `public` mode.
- `GET /openapi.json` in every mode, including `public`.

Handlers are in `src/wasel/api/routes.py` (mutations in `commands.py`, read models in `projections.py`, response models in `models.py`) and `routes_webhook.py`. Route docstrings appear as the endpoint descriptions.

## Starting the server

```bash
make run                                       # development: reload, APP_MODE=dev
make serve                                     # host run, settings from .env
uvicorn wasel.main:create_app --factory --port 8000    # what those run
```

The app factory needs no arguments. Boot prepares the database (creating or rebuilding it and seeding, see the [data model](architecture/data-model.md#persistence-lifecycle)), then starts the worker loop. Every response carries `Content-Security-Policy`, `X-Content-Type-Options: nosniff` and `Referrer-Policy: no-referrer` headers, and API data responses carry `Cache-Control: no-store`. Request bodies declaring more than 64 KB are refused with `413` (1 MiB for the webhook). If `web/dist` exists it is served at `/`, mounted after the API routes.

## Identity and access

| Interface | Protection |
|---|---|
| `/api/*` (except admin) | **No authentication.** In `public` mode, mutations require an `X-Visitor-Id` header holding a UUID v4 (`400 VISITOR_ID_REQUIRED` otherwise), and reads are scoped by it. The header is a scoping token, not an identity: anyone can invent one, and anyone who knows a visitor's id can see that visitor's sandbox. In `dev` and `event` mode the header is not required. |
| `POST /api/admin/reset` | Mounted only when `ADMIN_TOKEN` is at least 24 characters. Requires the `X-Admin-Token` header (constant-time comparison); `401 UNAUTHORIZED` otherwise. |
| `/webhook/whatsapp` | Mounted only when the mode is not public, `WEBHOOK_ENABLED` is on and both secrets are long enough. `GET` verifies with the verify token; `POST` requires a valid `X-Hub-Signature-256` HMAC. |
| CORS | Only in `dev` mode, for `FRONTEND_ORIGIN`. |

Do not put an instance with real data behind the default `/api` without a network-level control such as an access-restricted tunnel. The observability endpoints (`/api/monitor`, `/api/traces`, `/api/eval`, `/api/failures`) and the impact endpoint are readable by anyone who can reach the server in every mode. They return rates, codes and identifiers, not customer text or phone numbers. See [SECURITY.md](../SECURITY.md).

## Endpoints

### Health

| Method and path | Description |
|---|---|
| `GET /api/health` | Mode, safety flags and state. There is no separate readiness endpoint; use this one. |

Fields: `status` (`ok` or `degraded`), `mode`, `wa_send`, `webhook` (`enabled` or `disabled`), `wa_auto_send`, `demo_mode`, `db`, `build` (`git_sha`, `started_at`), `config` (`config_hash`, `prompt_version`, `classifier_version`, `seed_version`), `llm` (mode, `chain_extract`, `chain_judge`, `primary`, `fallback_active`, `last_path`, `live_calls_today`, `live_call_cap`, `cap_reached`, `visitor_cap`), `whatsapp.last_webhook_at`, `worker` (`last_tick_at`, `pending`, `last_purge_at`), `wa_token_present`, `real_rows`, `sandbox_orders`.

`status` is `degraded` when the worker is enabled and has not ticked in 10 seconds, or when any assessment in the last five minutes used a fallback path (`fallback_model`, `fallback_provider`, `rules`). Orders scored on the rules path because no LLM is configured therefore make a keyless instance report `degraded` while it is being used. Monitors should read `mode`, `wa_send`, `webhook` and `wa_auto_send` for safety and `worker.last_tick_at` for liveness.

### Orders

| Method and path | Status | Description |
|---|---|---|
| `GET /api/orders` | 200 | The queue, riskiest first, unscored last. Query: `tier`, `status`, `include_collecting` (default false), `limit` (default 100, at most 500). Returns `orders`, `counts` by tier and by `needs_review`, `awaiting_reply`, `ready_to_ship`, `server_time`, `mode`. |
| `GET /api/orders/{order_id}` | 200 | One order in full: `order`, `customer` (phone masked), `conversation` (messages with highlight `segments`), `assessments` (every version), `drafts`, `capabilities` (`read_only`, `can_try`, `can_simulate_reply`, `can_rescore`, `can_send_drafts`, `actions`), `scripted_replies` (for samples). |
| `POST /api/orders/ingest` | 202 | Queue a pasted message (`{"kind": "paste", "text", "customer_name?", "structured?"}`) or a CSV (`{"kind": "csv", "csv_text"}`). Returns `created`, `rejected` rows with reasons, and `rescore_eta_s`. Scoring happens later. |
| `POST /api/orders/{order_id}/try` | 201 | Copy a sample order into the caller's sandbox and score it immediately (no LLM call). Needs a visitor id. |
| `POST /api/orders/{order_id}/rescore` | 202 | Schedule an immediate manual rescore. `409 INVALID_TRANSITION` for terminal orders. |
| `POST /api/orders/{order_id}/actions` | 200 | `{"action": "approve" \| "request_confirmation" \| "cancel" \| "ship" \| "mark_delivered" \| "mark_refused"}`. Returns the updated order summary. See the [state table](architecture/order-pipeline.md#seller-actions). |
| `POST /api/conversations/{conversation_id}/simulate-reply` | 202 | `{"kind": "text", "text"}` (up to 600 characters) or `{"kind": "location", "lat", "lng"}`. Adds a simulated customer message and arms a rescore. |
| `POST /api/drafts/{draft_id}/send` | 200 | Send a draft (or record it as sent, depending on mode and channel; see [outbound](subsystems/outbound.md#sending)). Returns `sent_message_id`, `sent_at`, `delivery`. |

Structured fields on ingest: `product_name`, `price_tnd` (at least 0), `zone` (`urban`, `suburban`, `rural`), `quantity` (1 to 50). CSV columns: `customer_id, customer_name, product, price_tnd, zone, address, note`; the `customer_id` column is currently ignored.

### Activity and analysis

| Method and path | Description |
|---|---|
| `GET /api/events` | The activity log after a cursor: `after` (event `seq`), `order_id`, `limit` (default 50, at most 200). Returns `events` and `last_seq`; poll with the last seq. In public mode only global events and the caller's own. |
| `GET /api/metrics/impact` | The simulated impact from `data/reports/impact.json`. Always `simulated: true`. |
| `GET /api/monitor` | Drift, faithfulness, safety and provider health ([monitoring](subsystems/monitoring.md)) |
| `GET /api/traces` | Recent LLM trace records: `role`, `order_id`, `limit` (at most 500) |
| `GET /api/eval` | The committed offline and live evaluation reports (`null` if absent) |
| `GET /api/failures` | The failure analysis: `source=synthetic\|holdout\|app` (`400 BAD_SOURCE` otherwise) |
| `GET /api/failures/sessions/{session_id}` | One session with its findings; same `source` parameter |

### Admin and webhook

| Method and path | Description |
|---|---|
| `POST /api/admin/reset` | Delete every order and reseed the samples. Returns `reseeded_orders` and `purged_rows` (the number of orders removed). Keeps the catalog, extraction cache and LLM usage. |
| `GET /webhook/whatsapp` | Meta's verification handshake ([WhatsApp](subsystems/whatsapp.md#verification-handshake)) |
| `POST /webhook/whatsapp` | Meta's message and status delivery: `401` for a bad signature, `413` over 1 MiB, otherwise `200 {}` and processing in the background |

## Data concepts

- **Order summary** (queue rows): `order_ref` (`#2601`), `status`, `rescore_state` (`idle`, `debouncing`, `scoring`, `drafting`), `score` (a badge: `version`, `final_score`, `tier`, `action`, `confidence`, `path`, `delta` from the previous version, `reason_short`), `has_pending_draft`, `is_seeded`, `read_only`, `injection_suspected`, `seed_key`. Customer phone numbers are masked (`+216 •• ••• 001`), and in public mode sandbox customers are shown as `Customer #<n>`.
- **Assessment**: one stored scoring result with its reason, reason diff, top factors, adjustments, flags, confidence reasons, extraction provenance and the versions that produced it. The full list per order is in `assessments`, oldest first.
- **Segments**: each customer message is returned with `segments` computed on the server: consecutive pieces with a `kind` (`risk`, `address` or none), flag `codes` and a `label`. Concatenating the segment texts gives the message text with bidirectional control characters removed. Clients should render segments and never compute offsets.
- **Reasons** contain Unicode isolate characters (U+2068 and U+2069) around each quoted phrase; render them as text.
- **Capabilities** tell a client what it may show as enabled, so UIs do not re-derive mode rules.

## Validation and errors

Errors use one envelope:

```json
{"error": {"code": "INVALID_TRANSITION", "message": "not allowed from the current status", "details": {"allowed": ["approve", "cancel"]}}}
```

Request validation failures are `422 VALIDATION_ERROR` with `details` keyed by field. Unknown routes return FastAPI's default `{"detail": "Not Found"}`, not this envelope.

| Status | Codes |
|---|---|
| 400 | `VISITOR_ID_REQUIRED`, `BAD_SOURCE` |
| 401 | `UNAUTHORIZED` (admin token or webhook signature) |
| 404 | `NOT_FOUND`. Also returned for another visitor's rows in public mode, so their existence is not revealed. |
| 409 | `SEEDED_READ_ONLY` (mutating a sample in public mode), `NOT_SEEDED` (`try` on a non-sample), `INVALID_TRANSITION`, `ALREADY_SENT`, `DRAFT_BLOCKED`, `NEEDS_REVIEW` (system send of a non-`auto_send` draft), `OUTSIDE_24H_WINDOW`, `NO_RECIPIENT` |
| 413 | `PAYLOAD_TOO_LARGE`: body over 64 KB, paste over 2,000 characters, reply over 600, CSV over 10 rows (public) or 200 |
| 422 | `VALIDATION_ERROR` |
| 429 | `SANDBOX_LIMIT` (per-visitor order cap), `DEMO_BUSY` (global sandbox cap), `REPLY_LIMIT` (simulated replies per conversation) |
| 502 | `WHATSAPP_SEND_FAILED` |

An exhausted LLM budget is never an error: the order is scored on the rules path.

## Behaviour to design clients around

- **Scoring is asynchronous.** `ingest`, `simulate-reply` and `rescore` return `202` immediately; the result appears after the debounce (`rescore_eta_s`, 5 seconds in the default demo timing). Poll `GET /api/orders/{id}` until `order.rescore_state` is `idle` and the assessment count has grown, as `scripts/ops/smoke.py` and the examples do. `try` and seller actions are synchronous.
- **Rows are append-only.** A rescore adds an assessment version; it never edits the previous one. An order's history is the list.
- **One open order per conversation.** A message on a conversation with a terminal order opens a new order.
- **Public mode is deliberately awkward for scripts.** It needs the visitor header, forbids writing samples (use `try`), caps orders, replies and LLM calls, and purges sandbox data after two hours.
- **The activity feed is a cursor**, not a page: keep the `last_seq` you received and pass it as `after`.

## Examples

```bash
H='X-Visitor-Id: 3f2b8c1e-4a5d-4e6f-9a7b-1c2d3e4f5a6b'   # any UUID v4; required for writes in public mode

curl -s -X POST localhost:8000/api/orders/ingest -H "$H" -H 'Content-Type: application/json' \
  -d '{"kind":"paste","text":"n7eb el casque, livraison l douar ouled ali 9rib el jemaa","customer_name":"Sami"}'
# {"created":[{"order_id":"ord_...","order_ref":"#2610",...}],"rejected":[],"rescore_eta_s":5.0}

curl -s localhost:8000/api/orders -H "$H"                                   # the queue

curl -s -X POST localhost:8000/api/conversations/<conversation_id>/simulate-reply -H "$H" \
  -H 'Content-Type: application/json' -d '{"kind":"text","text":"Douar Ouled Ali, triq el jemaa, dar 14"}'
```

Python versions of the main flows, including polling, are in [`examples/`](../examples/README.md). The examples send an `X-Visitor-Id` automatically.
