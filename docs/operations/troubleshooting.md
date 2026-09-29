# Troubleshooting

Symptoms, likely causes and concrete diagnostics, organised by where you notice the problem. Commands assume the repository root and a local database at `var/app.db`; for a deployed host, run them there. If the `sqlite3` command line tool is not installed, use `python -c "import sqlite3; ..."` with the same SQL.

First look, for any problem:

```bash
curl -s localhost:8000/api/health | python3 -m json.tool     # mode, wa_send, webhook, llm chain and budget, worker heartbeat
curl -s 'localhost:8000/api/events?limit=30'                  # recent events: errors, fallbacks, rejected webhooks
```

## Start-up

| Symptom | Cause and diagnostic |
|---|---|
| The API exits at start with `PromptVersionMismatch: config/prompts/... changed without a version bump` | A locked prompt file no longer matches `config/prompts/VERSIONS`. Either you edited a prompt in place (create a new version instead, [procedure](../configuration/llm-registry.md#procedures)) or a Windows checkout converted line endings to CRLF (`git config core.autocrlf false`, re-checkout; `.gitattributes` forces LF). List what the code sees: `python -c "from wasel.llm.prompts import check_versions; print(check_versions())"`. |
| `PromptVersionMismatch: ... is not a listed version` or `is not locked as ...` | `config/llm.yaml` names a version that is missing from its `versions:` block, or a file under it is not listed in `VERSIONS` under that same version. |
| Start-up validation error from pydantic (`Input should be ...`) | An invalid value in `.env` or the environment for a typed setting such as `SEED_ON_BOOT`, `LLM_MODE` or a boolean. The message names the field. Values are listed in [environment](../configuration/environment.md). |
| `ModuleNotFoundError: No module named 'wasel'` | The package is not installed in the interpreter you are using. Run `make setup` (it installs the package editable) and use the same `.venv`, or `PY=...`. |
| `make up` prints `API at ... did not answer /api/health within 180 s` | The API process died or hangs. Run `make run` in the foreground to see the traceback. |
| `Address already in use` | Another process holds 8000 or 8501. Use `make up API_PORT=8001 UI_PORT=8502`, or find the process (`ss -ltnp \| grep 8000`). |
| Warning `unknown APP_MODE 'x' -> public` | A typo in `APP_MODE`. Only `dev`, `event` and `public` are valid. |
| Scores say `(model unavailable: documented prior)` and `classifier_version` is `prior_v1` | `models/risk_xgb_v1.json` (the `model.file` in `scoring.yaml`) is missing. Restore it from git or run `make train`. |

## Data disappears or looks wrong

| Symptom | Cause and diagnostic |
|---|---|
| Orders and edits vanish after a restart | Public mode (`APP_MODE` unset or `public`) sets `SEED_ON_BOOT` to `always`, which deletes and rebuilds the database. `make up` also defaults to `always`. Use `APP_MODE=dev`/`event` with `make run` or `make serve` and leave `SEED_ON_BOOT` unset (`if_empty`). |
| `make failures` fails with `no such table: orders` | `var/app.db` does not exist or is empty. Run `make seed` (or start the app once) first. |
| A sample order scores differently from the README | Its extraction was not found in the cache (a changed message, template text, window rule or prompt version), so it fell to the rules extractor. Look for `path=rules` on the assessment and run `make warm`. `test_seed_all_cache_hits_under_fail_all` guards this. |
| `database is locked` | Something else holds a write transaction for more than the 5 s busy timeout: a second API instance on the same file, or an open `sqlite3` shell. Keep one API process per database and close other writers. |

## Scoring and extraction

| Symptom | Cause and diagnostic |
|---|---|
| New orders show `path=rules`, action `review`, status `needs_review` | No model answered. Check, in order: `llm.chain_extract` in `/api/health` (empty means no provider is configured: `GROQ_API_KEY` was found neither in the process environment nor in `.env` in the working directory; start from the repository root); `llm.llm_mode` (must be `live`); `llm.cap_reached`; and the provider outcomes: `sqlite3 var/app.db "select role,provider,model,outcome,count(*) from llm_usage group by 1,2,3,4"`. Repeated `rate_limited` or `down` points at the provider; `schema_rejected` with a Gemini model at a schema style mismatch (`config/probe.json`); `timeout` at the 6/5/8 s step timeouts or the 20 s deadline. |
| `/api/health` says `degraded` | The worker has not ticked for 10 s (`worker.last_tick_at`; the loop crashed or `WORKER_ENABLED=false`), or an assessment in the last five minutes used a fallback path (`llm.fallback_reason` says which). With no LLM configured this is normal after any new order. |
| Order stays `debouncing` or never scores | The worker is not running (`WORKER_ENABLED=false`, or a crashed tick: look for `worker tick failed` in the log) or the debounce is long (15 s when `DEMO_MODE=false`). `sqlite3 var/app.db "select order_no,status,rescore_state,pending_rescore_at,pending_trigger from orders order by updated_at desc limit 5"`. A `manual` rescore (`POST /api/orders/{id}/rescore`) is due immediately. |
| Order is in `needs_review` and you do not know why | Read the assessment's `confidence_reasons` and the order's events. Causes: rules path, injection suspected, customer changed the order, ambiguous reply, unsupported media (audio, image, sticker), no-reply timeout, a scoring exception (`error` event with `where: rescore`), or the seller-approved order's tier rose. [Rules table](../architecture/order-pipeline.md#automatic-transitions). |
| Order is missing from the queue | Orders in `collecting` with no rescore pending are hidden. Use `GET /api/orders?include_collecting=true`. A conversation with only unsupported media never becomes an order. In public mode you only see samples and your own sandbox (your `X-Visitor-Id`). |
| Order flagged `injection_suspected` but the text looks fine | A pattern in `lexicons.injection` matched. It only flags for review; it never changes the score. To find the pattern, run `wasel.extraction.injection.injection_hit_text` on the text with the patterns from `scoring.yaml`. Legitimate phrases like "je confirme" must not match; add a case to `test_injection_lexicon_false_positives` when you fix one. |
| Quotes are missing from the highlighted text | The evidence check drops any quote that is not verbatim in a customer message. `evidence.dropped` events and `dropped_quotes` on the extraction run count them. A high rate on a live model means the prompt or model is paraphrasing ([monitoring](../subsystems/monitoring.md)). |
| `confidence` is low on obviously good orders | See `confidence_reasons`: a product not in the catalog, an imputed zone, an unclear message, or a score within 10 points of a tier boundary all count. |

## Drafts and sending

| Symptom | Cause and diagnostic |
|---|---|
| Send returns `delivery: recorded_only` and nothing reaches the customer | Real sends need a WhatsApp conversation, a non-public mode, `WA_SEND_ENABLED=true`, `WA_TOKEN` and `WA_PHONE_NUMBER_ID`. Otherwise the draft is recorded as sent by design. `/api/health` shows `wa_send`. |
| `409 OUTSIDE_24H_WINDOW` | The customer's last message is over 24 hours old; WhatsApp allows free-form text only inside that window. Template messages are not implemented. |
| `409 NO_RECIPIENT` | The customer has no phone number (paste and sample customers have none). |
| `409 DRAFT_BLOCKED` | The deterministic prefilter failed. Read `prefilter.failures` on the draft. A failing static template is a configuration error and produces an `error` event. |
| `409 ALREADY_SENT` | The draft was already sent; each order has at most one unsent draft. |
| `502 WHATSAPP_SEND_FAILED` | Meta refused the message. The reason (for example `http_400:131047`) is in the response and in the `draft.send_failed` event; the number after the colon is Meta's Graph error code. |
| `DRAFT_LLM=true` but drafts are still static templates | The rewrite call failed or the chain is empty (`draft.rewrite_unavailable` event), the prefilter or classifier rejected it (`draft.rejected`), or the judge rejected it twice (`draft.fallback_static`). `chain_judge` in `/api/health` is empty when no provider is configured. |
| Automatic sending never happens | It needs all of: `WA_AUTO_SEND=true`, a non-public mode, an `auto_send` route, which needs `DRAFT_LLM=true`, a classifier decision of `send`, `confidence=high`, a known price at most 150 TND, fewer than 2 automatic messages for the order, and the customer's last message under 24 hours old. Static templates never auto-send. Sample and sandbox orders are excluded. |

## WhatsApp webhook

| Symptom | Cause and diagnostic |
|---|---|
| `POST /webhook/whatsapp` returns 404 or 405 | The webhook is not mounted. `/api/health` must show `webhook: enabled`. It requires a non-public `APP_MODE`, `WEBHOOK_ENABLED=true`, `WA_APP_SECRET` of at least 16 characters and `WA_VERIFY_TOKEN` of at least 24. A short secret silently leaves it unmounted. |
| Meta's verification fails (`403`) | The verify token in the Meta console differs from `WA_VERIFY_TOKEN`, or `hub.mode` is not `subscribe`. The log says `webhook verify refused`. |
| Deliveries return `401` | Wrong `WA_APP_SECRET` (it must be the Meta **app** secret) or a proxy modified the body. A `webhook.rejected` event records `missing`, `malformed` or `mismatch`. |
| Deliveries return 200 but nothing appears | `WA_PHONE_NUMBER_ID` is empty or not the number id in the payload; the log warns `change(s) for another phone_number_id ignored`. Also check `webhook.process_error` events and that the message is not a duplicate. |
| Messages arrive but only as needs-review | Media messages are stored as unsupported and always need review. |
| `make wa-up` says `webhook not mounted` | The API is not running with the webhook enabled. It also needs `META_APP_ID`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` and `WA_PHONE_NUMBER_ID` in `.env`; it fails with the name of any missing one. |

## Public mode and the API

| Symptom | Cause |
|---|---|
| `400 VISITOR_ID_REQUIRED` | Send `X-Visitor-Id` with a UUID v4 on mutations, or use `dev` mode. |
| `409 SEEDED_READ_ONLY` | Sample orders are read-only in public mode; call `POST /api/orders/{id}/try`. |
| `404` on an order you created | A different `X-Visitor-Id` (the dashboard makes a new one per session), or it was purged after the 2 hour TTL. |
| `429 SANDBOX_LIMIT`, `DEMO_BUSY`, `REPLY_LIMIT` | 15 orders per visitor, 500 sandbox orders overall, 5 simulated replies per conversation. Limits are `SANDBOX_MAX_ORDERS`, `SANDBOX_GLOBAL_MAX`, `REPLY_LIMIT`. |
| `413` on a small request | Body over 64 KB, paste over 2,000 characters, reply over 600, CSV over 10 rows in public mode. |
| `/docs` is 404 | Public mode disables it. `/openapi.json` is available. |
| CORS errors from `npm run dev` | The API must run with `APP_MODE=dev`; `FRONTEND_ORIGIN` must equal the dev server's origin. |

## Interfaces

| Symptom | Cause |
|---|---|
| `/` returns 404 or the UI is stale | `web/dist` is missing or built before the last pull: `make web`. |
| Dashboard shows "can't reach the backend" | `API_BASE_URL` does not point at a running API (`make ui` defaults to `http://localhost:8000`). |
| The web UI in the browser shows nothing but the API works | Open the browser console; a `NEXT_PUBLIC_API_URL` baked into the build pointing at the wrong host is the usual cause. Rebuild with it unset. |
| Traces or LLM call log are empty after a restart | The trace buffer is in memory only; set `TRACE_FILE` to persist. |
| The monitor shows alerts on a new install | Alerts need at least 20 samples; with no LLM, `fallback_rate` and `invalid_extraction_rate` are high by design. |

## Development, tests and CI

| Symptom | Cause and diagnostic |
|---|---|
| `make check` fails at `hygiene` | The message names the rule: a tracked `.env`, database or `web/dist`; a key-shaped string; a phone number outside `21600000001` to `...009` in `tests/fixtures` or `data`; `datetime.now()` outside `clock.py`; an LLM SDK import; `dangerouslySetInnerHTML`. |
| `make check` fails at `eval` with `EVAL GATE FAILED` | A metric is under its floor in `config/eval.yaml`. [Reading a failure](../evaluation.md#reading-a-failure). |
| `git status` shows `data/reports/eval.json` modified after `make check` | `runtime_s` changed. Restore it (`git checkout -- data/reports/eval.json`) unless metrics changed too. |
| A test fails with `network call to ... in an offline test` | The test (or code it exercises) tried to reach a non-loopback address. Use `ReplayBackend`, `FailingBackend` or an `httpx.MockTransport`. |
| `FixtureMissing: no fixture for key ...` | An offline `replay` client has no recording for that exact rendered window. Add an envelope for it under the replay directory (`LLM_REPLAY_DIR`); tests use the `replay_dir` helper in `tests/conftest.py`. |
| `ValueError: LLM_MODE=replay needs recorded fixtures` | `LLM_REPLAY_DIR` (default `data/llm_replay`) has no `*.json` files. |
| `test_hero...` fails after a code or config change | The sample scenario's numbers moved. Decide whether the new values are correct; if so re-pin with `make train` (which rewrites `tests/golden/hero.json` and other artifacts). Otherwise fix the change. |
| `test_model_artifact_matches_card` fails after upgrading XGBoost | The card records the library's minor version. Retrain (`make train`) and commit the new artifacts. |
| `test_reference_is_committed_and_matches_the_builder` fails | The golden set or extraction rules changed the drift baseline: `python -m wasel.monitor --build-reference`. |
| `test_fairness_invariant` reports `XPASS(strict)` | The model now passes the fairness check; remove the `xfail` marker and update the notes in [machine learning](../machine-learning.md#known-limitations). |
| `make eval-live` says `no provider configured` | No provider key was found in the environment or in `.env` in the working directory (see [environment](../configuration/environment.md#how-values-are-loaded)). |
| Live evaluation shows many `none` paths or low `is_order_acc` | Calls fell out of the step deadline or were rate limited and the chain returned rules or nothing. Use `--pace 2`, or a self-hosted endpoint, and read `paths` and `llm_usage` in the report. |
| `make llm-check` fails | `GROQ_BASE_URL` or `GROQ_API_KEY` empty in `.env`; the model name in `/v1/models` differs from `MODEL`; the server has not finished loading; or (gpt-oss) too few completion tokens for the reasoning channel. |
