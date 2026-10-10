# Extending Wasel

Recipes for common changes, with the files each one touches. Most changes are small if you know where the seams are: the scoring core exchanges only the dataclasses in `src/wasel/contracts.py`, everything stored goes through `src/wasel/db/repo.py`, and everything users see goes through `src/wasel/api/`. Read the [architecture overview](../architecture/overview.md) first if you have not.

## Where to change what

| I want to change | Look at |
|---|---|
| What the LLM is asked to extract | `config/prompts/extract_v*.txt`, `config/schemas/order_extraction_v1.json`, `extraction/repair.py` |
| How a model answer is verified | `extraction/cross_field.py`, `extraction/evidence.py`, `ml/features.py` (`resolve_flags`, `tone_gate`) |
| The rules extractor | `extraction/rules_extractor.py`, `data/phrase_banks.yaml`, `config/scoring.yaml` lexicons |
| The score, tiers, actions, confidence | `scoring/score_order.py`, `config/scoring.yaml`, the model |
| Reason wording | `scoring/reason.py` |
| Order statuses and seller actions | `state.py`, `api/commands.py`, `db/schema.sql` |
| When and how a message is drafted | `outbound/templates.py`, `outbound/make_draft.py`, `data/templates/outbound.yaml` |
| What may be sent automatically | `outbound/route.py`, `config/scoring.yaml` (`auto_send`, `outbound`) |
| A new HTTP endpoint | `api/routes.py`, `api/commands.py` or `api/projections.py`, `api/models.py` |
| A new channel | `ingress/`, `db/schema.sql`, `contracts.py` |
| Background behaviour | `worker.py`, `main.py` (`AppState.tick`) |
| Provider calls | `llm/client.py`, `llm/groq_backend.py`, `config/llm.yaml` |

## Change a prompt

Prompts are locked by hash, versioned, and tied to cached extractions, so a change is a small procedure:

1. Copy the prompt file to a new name with the next version (`extract_v2.system.txt`) and edit the copy. For `extract`, copy the few-shot file too (`extract_v2.fewshot.jsonl`): every file of a version must be locked under that version.
2. In `config/llm.yaml`, add the version under the role's `versions:` and set `active`.
3. Append the new files to `config/prompts/VERSIONS`: `<version> <sha256> <file>`, hash from `sha256sum`.
4. `make warm` to re-record the sample extractions (the cache keys contain the version), then `make test` and `make eval`.
5. With a key, run `make eval-live` and compare with `data/reports/eval_live.json`.
6. Keep the previous version listed so `scripts/ops/rollback.py` still works.

If the output shape changes, change the JSON schema and its Pydantic mirror in the same commit; a unit test compares them.

## Add a red-flag code

A code is part of the schema, the model input and the UI:

1. `config/schemas/order_extraction_v1.json` (enum) and `FlagCode` in `extraction/repair.py`, `contracts.py` and `api/models.py`.
2. `FLAG_ORDER` in `ml/features.py`, the `FLAG_LABELS` dictionary in `scoring/score_order.py` (the label the API returns) and the code-to-label map in `web/app/dashboard/order/page.tsx`.
3. The extract prompt and few-shot examples (a new prompt version), and a definition in the phrase banks with `train` and `eval_only` phrases.
4. Decide how it should affect the score. The model sees only the *count* of flags, so a new code changes what `red_flag_count` means: the generator (`sample_latents`) needs to plant it and the model needs retraining ([retraining](../machine-learning.md#retraining)).
5. Update `resolve_flags` if the code can be resolved by a later message.
6. Tests: extraction, the schema-parity test, and a golden case. Run `make eval`.

## Change or add a model feature

The feature list is a contract shared by `ml/features.py`, the generator, the trainer, the model card and the scorer. Adding a feature means changing `FEATURES`, `MONOTONE`, `build_features`, the prior `S()` if the generator should depend on it, the generator's columns, the training gates, and then regenerating, retraining and re-pinning the hero golden. Old assessments keep their stored `features_json`. The `context_json` of new assessments can carry the extra provenance. See [machine learning](../machine-learning.md).

## Add a template or a language

Templates live in `data/templates/outbound.yaml`.

- **New wording or a new template id:** add the text (with a `no_name` variant) for `fr`, `arabizi` and `darija_arabic_script`, add the id to `expected_questions`, and extend `TemplateId` in `contracts.py`, `api/models.py` and the check constraints in `schema.sql`. Give `choose_template` a rule and `make_draft.AUTHORIZED` an entry. Every template must pass the prefilter (a unit test renders each one) and the guard classifier trains on them, so add matching safe phrases to `data/draft_guard.yaml` if the vocabulary is new.
- **New language:** it must be added to `Language` in the extraction contracts, the phrase banks (authored and reviewed by a native speaker), the templates, the classifier bank, the rules extractor's vocabularies and the language routing in `outbound/templates.py`, then the generator, golden sets and monitor reference.

## Add an API endpoint

1. A response model in `api/models.py`. Never include `phone_e164` or `raw_payload`; a test enforces it.
2. The logic: a mutation goes in `api/commands.py` (take the connection, ids, `now`, settings and visitor id; raise `ApiError` with a code; use `tx(conn)`); a read goes in `api/projections.py`. Keep the route in `api/routes.py` thin, with a docstring (it becomes the OpenAPI description).
3. Respect the modes: in public mode, use `visible_order` or `writable_order` for anything tied to an order, and `require_visitor` for mutations, so isolation and the read-only samples hold.
4. Tests in `tests/integration/test_backend.py` for both `dev` and `public` behaviour.
5. If the UIs need it, add it to `web/lib/api/orders.ts` and `dashboard/api_client.py`.
6. `make mocks` if the change alters an existing response (the frozen responses in `tests/fixtures/api/` are checked against the models).

## Add a channel

Every channel must end in `store_inbound()`. Add the channel name to `Channel` and `Origin` in `contracts.py` and `api/models.py`, to the check constraints on `conversations.channel` and `messages.origin` in `schema.sql`, create or find the customer and conversation in the new entry code, and call `store_inbound(...)` inside one transaction. Do not score in the request path: the debounce and the worker handle that. For anything internet-facing, follow the webhook's pattern: size cap first, authenticity check on the raw bytes, store the message before answering 200 (answer 503 if it could not be stored, so the sender retries), log counts and reasons only.

## Add an order status or seller action

Statuses and actions are defined in `state.py` (`ACTIONS`, `next_status`), constrained in `schema.sql` (`orders.status`), typed in `api/models.py`, labelled in both UIs and covered by `test_next_status_table` and `test_actions_table_shape` in `tests/integration/test_backend.py`. Add the transition rule in the right position (first match wins), the action's side effects in `commands.apply_action`, and the rows to the table tests.

## Change the schema

`schema.sql` is the schema and there are no migrations. Edit it, update `repo.py` and `contracts.py`, and expect that any existing database must be rebuilt (`make seed`, or start with `SEED_ON_BOOT=always`). Deployments that keep real rows (`event` mode) need a manual migration; write one before changing a table that holds them.

## Add a monitor metric

Compute it in `monitor.py` inside the appropriate group (`faithfulness`, `safety` or `ops`), add a ceiling to `config/monitor.yaml` (alerts match by metric name), and add a case to `tests/integration/test_monitor.py`.

## Modify configuration safely

1. Read the section in [configuration](../configuration/README.md) first, including any note that a key is unused.
2. Change one thing at a time. Rerun `make eval` and `make test`.
3. For safety-relevant values (`auto_send`, `outbound.judge`, prefilter and injection lexicons, eval floors, caps), explain the reason in the pull request. Tightening is easy to justify; loosening needs measurements.
4. If a change alters the sample order's numbers, decide deliberately whether the new values are correct, then update `tests/golden/hero.json` through `make train` (or edit it with a reason).

## Update the sample data

`data/seed/demo_seed.json` defines the eleven sample conversations and scripted replies. A conversation can carry an `answer` (the customer's reply, stored after the first score so the order gets a second one). A new or edited conversation needs entries in `data/seed/hand_extractions.json` (one extraction per turn), a `make warm` run so the extraction cache has a matching entry for each rendered window, a check that `test_seed_all_cache_hits_under_fail_all` passes, and `make mocks` if the frozen API responses should reflect it.

## Conventions

- Time only through `wasel.clock` and ids through `wasel.ids`. `make hygiene` enforces the clock rule. Prefer a function in `db/repo.py` over new inline SQL; some SQL also lives in the worker, the commands, the projections, the monitor and the failure adapter.
- No LLM SDKs: use `httpx` and `ChainClient`. Every model call goes through `ChainClient.extract`.
- No secrets, `.env` files or databases in git.
- Docstrings state behaviour, inputs, outputs and failure modes, not history. Match the surrounding code's density of comments.
- Ruff is the linter and formatter of record (`make lint`, `make fmt`, line length 125).
- Keep the scoring core free of `sqlite3`, `fastapi` and the persistence, API and worker modules; a test enforces it.
