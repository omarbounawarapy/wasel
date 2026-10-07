# Testing

The test suite is offline, keyless and deterministic. It runs the real code (SQLite, FastAPI, XGBoost, the guard classifier, the Streamlit app) and replaces only what would need a network or a wall clock. The current tree passes with one expected failure (the xfail below); `make test` prints the current counts and duration.

## Running

```bash
make test                                    # the full suite under the offline environment
make check                                   # hygiene + lint + suite + evaluation gate (CI)
make test PYTEST_ARGS="-k monitor"           # a focused run through make
.venv/bin/python -m pytest tests/unit/test_scoring.py -k tier_boundaries   # or call pytest directly
.venv/bin/python -m pytest tests/integration/test_whatsapp.py -x
```

Calling `pytest` directly works without any environment variables because `tests/conftest.py` disables reading `.env` (`Settings.model_config["env_file"] = None`) and every test builds its own `Settings`. `make test` additionally sets `TEST_ENV` (`APP_MODE=dev LLM_MODE=fail_all WORKER_ENABLED=false DEMO_MODE=true GEMINI_ENABLED=false` and empty keys) so that anything reading the process environment behaves the same on every machine and in CI.

Configuration lives in `pyproject.toml`: `testpaths = ["tests"]`, options `-q -ra --strict-markers --durations=5`, and one marker, `live` ("needs real API keys; never in CI"). The suite is discovered by pytest's defaults (`tests/**/test_*.py`). The `live` marker is registered and deselected by `make test`, but no test carries it yet, and `RUN_LIVE` is not read anywhere; live behaviour is measured by `make eval-live`, not by pytest.

The slowest tests are the dashboard renders (a few seconds each) and the guard-classifier calibration test, which is why the whole run takes minutes.

## Layout

| Directory | Tests | What it covers |
|---|---|---|
| `tests/unit/` | scoring, extraction, ML, outbound judge, failure analyzer, Groq routing | Pure functions and small components with injected fakes. No app, no database. |
| `tests/integration/` | backend, WhatsApp, monitor | The real FastAPI app with a temporary SQLite file, a frozen clock and sequential ids, driven through `TestClient`. |
| `tests/e2e/` | hero scenario, injection regression, dashboard | End-to-end behaviours: the frozen sample scenario through `score_order`, injected text through the whole pipeline, and the Streamlit dashboard driven by Streamlit's `AppTest` against a real in-process backend. |
| `tests/fixtures/` | `whatsapp/`, `api/`, `hero/`, `cases/` | Meta-shaped webhook payloads, frozen API responses, the frozen extractions for the sample scenario, and the hand-written prefilter drafts. |
| `tests/golden/hero.json` | | The pinned scores and reasons of the sample scenario. |

## Harness and fixtures

- **`tests/conftest.py`**: a session-scoped scoring `config`; a `FrozenClock` at 2026-09-27 10:00 UTC; helpers `make_input`, `customer_msg` and `seller_msg` that build a `ScoreInput`; a `replay_dir` fixture that writes recorded-response envelopes into a temporary directory; a `CountingMeter` that stands in for the usage meter; and an autouse guard that makes any network connection to a non-loopback address raise `RuntimeError("network call ... use ReplayBackend")`.
- **`tests/integration/conftest.py`**: `make_client(tmp_path, mode, llm_mode="fail_all", **settings)` builds the app with a temporary database, `worker_enabled=False`, the failing LLM chain and sequential ids. The `dev` and `public` fixtures use it. `settle(core, clock)` advances the clock five seconds and drains the worker, replacing the one-second loop deterministically.
- **`tests/e2e/conftest.py`**: puts `dashboard/` on `sys.path` so the tests import `api_client` the same way `streamlit run` does. The dashboard tests route the dashboard's HTTP calls into the in-process backend and advance time and drain the worker before every request.
- **WhatsApp tests** sign payloads with a fake secret and use fake phone numbers `21600000001` to `...009` only. Sending is tested against an `httpx.MockTransport` that plays Meta.

### What is mocked and what is real

| Real | Replaced |
|---|---|
| SQLite (a temporary file), the schema, repository and transactions | The clock (`FrozenClock`) and id generation (`SeqIds`) |
| FastAPI routing, middleware, validation and error envelopes | LLM providers: `LLM_MODE=fail_all` makes every step fail so new text takes the rules path, and sample orders are served from the committed extraction cache; scoring unit tests use `ReplayBackend` fixtures or scripted fake backends |
| The worker step (`drain`), state machine, scoring, extraction, verification | WhatsApp: payloads are fixtures and sending goes through a mock transport |
| The XGBoost model file, the guard classifier (trained in the test process), the rules extractor | The network: blocked outright by the autouse guard |
| The Streamlit app (`AppTest`) | |

Because the LLM chain fails everywhere by default, any test that accidentally needs a provider shows up as a `path='rules'` result instead of hanging or spending tokens. A missing recorded fixture in `replay` mode raises `FixtureMissing` on purpose.

## Kinds of tests and what they protect

| Kind | Examples | Protects against |
|---|---|---|
| **Correctness** | `test_scoring.py` (tiers, actions, confidence, adjustments, chain behaviour on each error class), `test_extraction.py` (repair, evidence, tone gate, confirmation, exact guard, injection lexicon, PII masking), `test_outbound_judge.py`, `test_backend.py` (order boundaries, seller actions, sandbox isolation, purge, CSV limits), `test_whatsapp.py` (signature, dedupe, ordering, fail-closed mounting, retries, 24 h window) | logic errors in a component |
| **Contract** | the extraction schema equals its Pydantic mirror; responses validate against `api/models.py`; no response model exposes `phone_e164` or `raw_payload`; committed frozen API responses validate; a stub scorer satisfies the `contracts.py` signature; feature order and constraints match between code, dataset and model card; the model file's hash equals the card's; the layering test forbids the core importing infrastructure | silent drift between pieces that must agree |
| **Golden and regression** | `test_hero.py` and `test_whatsapp.py::test_hero_loop_webhook_parity` compare against `tests/golden/hero.json`; `test_injection.py` checks that an order with an injected instruction is flagged, never scores lower than its clean twin, has low confidence and ignores an injected confirmation; the committed dataset, failure sessions and monitor reference must equal what their generators produce | unintended change of scoring, reasons or generated data |
| **Evaluation** | `make eval`, `tests/unit/test_outbound_judge.py` (classifier holdout recall, calibration and the pinned hold line) | quality regressions measured on labelled sets; see [evaluation](../evaluation.md). `make eval` is not pytest but is part of `make check`. |
| **Smoke** | `make smoke`; the CI `serve` job (builds the web UI, starts `make serve` with no configuration, checks `/api/health` reports safe public defaults, `/dashboard/` serves the UI, then runs the smoke test); the dashboard test that renders every page | a broken deployment path or boot |
| **Safety properties** | the webhook is not mounted in public mode or with short secrets; public mode never builds a sender or auto-sends; the verify token is redacted in access logs; the sender phone number never leaves the database or reaches a log; prefilter blocks each unsafe class | regressions in the protections described in [SECURITY.md](../../SECURITY.md) |

### The sample scenario

The hero test replays a fixed three-message conversation and a customer reply through the real `score_order`, with the model outputs frozen in `tests/fixtures/hero/` and served through the extraction-cache seam. It pins features, model score, final score, tier, action, confidence, reason and reason diff (87 HIGH to 16 LOW). Three robustness tests (`test_r1_...`, `test_r3_...`, `test_r4_...`) pin behaviour: no confirmation gives LOW from the model alone, tone without evidence stays HIGH, a street and landmark address is at least MEDIUM. The stale and clean second-turn variants must give identical results.

## The expected failure

`tests/unit/test_ml.py::test_fairness_invariant` is `xfail(strict=True)`. It asserts that a rural order with an exact address, no flags, a neutral tone, a new customer and any catalog price up to 450 TND is `low` tier. The committed model gives 36.3 for the 450 TND product, so it fails as expected. Because it is strict, the moment the model starts to pass it the suite fails until the marker is removed. Its reason string says what to do: change the data or the catalog, or accept the trade-off in the card; never tune the model to pass. `test_fairness_prior_value` documents the prior's value (29.0) for the same input.

## Generated outputs

- Tests write only to temporary directories. They must not modify tracked files.
- A few tests compare committed generated files to their generators (`test_committed_datasets_match_the_generator`, `test_reference_is_committed_and_matches_the_builder`, the model card and metrics checks). When you change a generator input, regenerate and commit the outputs in the same change or these fail.
- `make eval` rewrites `data/reports/eval.json`, and `make mocks` rewrites `tests/fixtures/api/*.json`, which are outside pytest.

## Writing tests

1. Put the test where the component lives: `unit` if it needs no app, `integration` if it needs the database or HTTP, `e2e` for a full flow or a UI.
2. Prefer the existing harness: `make_input` for scoring, `make_client` and `settle` for the API, `replay_dir` for provider responses. Give scripted fake backends the `complete_json(task, model, user, timeout_s)` method (see `tests/unit/test_outbound_judge.py::Scripted`).
3. Never call a real provider. To simulate provider behaviour, use `FailingBackend("429" | "timeout" | "5xx" | ...)`, a `ReplayBackend` over a `replay_dir`, or a fake.
4. Assert on behaviour and on stored rows, not only on status codes. For a bug fix, add a test that fails without it.
5. Use `pytest.skip(reason=...)` rather than omitting a test you cannot write yet.
6. Use fake data only: phone numbers `21600000001` to `...009`, synthetic names. `make hygiene` enforces the phone allowlist for `tests/fixtures` and `data`.
