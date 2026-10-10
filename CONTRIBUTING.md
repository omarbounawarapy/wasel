# Contributing

The code is not open source (see [LICENSE](LICENSE)). The repository is private: issues and code changes come from maintainers and invited contributors. Everyone follows the [code of conduct](CODE_OF_CONDUCT.md). Report security problems privately, as described in [SECURITY.md](SECURITY.md).

## Orientation

- [docs/README.md](docs/README.md) is the map of the documentation. Start with [getting started](docs/getting-started.md) and the [architecture overview](docs/architecture/overview.md).
- The repository layout is in the [README](README.md#repository-layout). The seams that matter: the scoring core exchanges only the dataclasses in `src/wasel/contracts.py`; everything stored goes through `src/wasel/db/`; everything users see goes through `src/wasel/api/`.
- [docs/development/extending.md](docs/development/extending.md) has step-by-step recipes for the common changes (a prompt, a red-flag code, a feature, a template, an endpoint, a channel).

## Development setup

You need Python 3.11, `make`, and Node 22 if you work on the web UI.

```bash
python3.11 -m venv .venv
make setup        # pinned Python dependencies + the wasel package (editable install)
make check        # hygiene + ruff + offline tests + evaluation gate; needs no API keys, about a minute
make up           # the seller UI and API on :8000, seeded (make ui for the analyst view on :8501)
make web          # build the Next.js UI into web/dist (served by the API at /)
make run && make web-dev    # API in dev mode + Next.js dev server on :5173
```

`make help` lists every target, and [docs/development/commands.md](docs/development/commands.md) says what each does and which ones overwrite committed files. Live LLM behaviour needs `GROQ_API_KEY` in your environment or in a `.env` at the repository root; nothing in the normal workflow requires a key.

## Workflow

1. Get `make check` green on a clean checkout before you change anything.
2. Work on a branch per change, named `<area>/<change>`, for example `worker/no-rearm-after-error`.
3. Include tests with the change. A missing test is acceptable only as a visible `pytest.skip(reason=...)`. [Testing](docs/development/testing.md) describes the harness and what each kind of test protects.
4. Update the documentation that describes what you changed, in the same pull request (see below).
5. Rebase on `main` and run `make check` again. CI runs the same target on every push and pull request, then builds the web UI, starts `make serve` with no configuration and requires safe public defaults, the UI and a passing smoke test.
6. Open a pull request and fill in the template.

When you change a shared interface (`src/wasel/contracts.py`, `src/wasel/api/models.py`, `src/wasel/db/schema.sql`, `config/scoring.yaml`, the `Makefile`, `requirements*.txt`, `ci.yml`), update its consumers in the same pull request.

## Rules the checks enforce

- Read time through `src/wasel/clock.py`, never `datetime.now()`.
- Call LLM providers only through `src/wasel/llm/` with `httpx`; no provider SDKs.
- No secrets, `.env` files, databases or phone numbers outside the `21600000001` to `21600000009` allowlist in git.
- No `dangerouslySetInnerHTML` in the web UI.
- The scoring core (`llm/`, `extraction/`, `scoring/`, `outbound/`, `ml/`) does not import `sqlite3`, `fastapi`, `wasel.db`, `wasel.api`, `wasel.ingress` or `wasel.worker`.
- A prompt file is never edited in place: add a new version and lock it in `config/prompts/VERSIONS` (see [LLM registry](docs/configuration/llm-registry.md#procedures)).

## Rules reviewers hold you to

- Every number the UI shows comes from code or `data/reports/*.json`, never from an LLM.
- Public mode must never send WhatsApp messages, mount the webhook or bypass the visitor sandbox. A change that touches modes, sending, the webhook, caps or lexicons is a safety change; explain it in the pull request and show `make check` and, where relevant, `make eval`.
- Loosening a safeguard needs measurements. Tightening is easy to justify.
- Do not lower an evaluation floor in `config/eval.yaml` to make a run pass, and do not edit a golden file to match new behaviour without understanding why the behaviour changed. See [evaluation](docs/evaluation.md#reading-a-failure).

## Style

`make fmt` fixes what ruff can fix; `make lint` must pass. Line length is 125. Match the surrounding code: short docstrings that state behaviour, inputs and failure modes, and no comments that restate the code. Python target version is 3.11.

## Tests

Put a test next to the behaviour it protects: `tests/unit/` for pure components, `tests/integration/` for the API and database with the harness in `tests/integration/conftest.py`, `tests/e2e/` for whole flows and the dashboard. Tests are offline and deterministic: never call a real provider or reach the network (a guard fails the test if you do). Use `FrozenClock`, `SeqIds`, `ReplayBackend`/`FailingBackend` and the existing helpers. Use fake data only.

## Data, models and configuration

- **Configuration.** Read the relevant section of [configuration](docs/configuration/README.md) first, change one thing at a time, and re-run `make eval` and `make test`. Several keys in `config/scoring.yaml` are documented as unused; do not tune those.
- **Generated files** (`data/synth_v1.csv`, `data/eval/golden/`, `data/agent_sessions*.jsonl`, `data/reports/`, `models/`, `tests/golden/hero.json`, `data/seed/extraction_cache.jsonl`, `tests/fixtures/api/`) are produced by commands, not edited by hand. If you change their inputs, regenerate and commit the outputs with the change. `make eval` rewrites `data/reports/eval.json` only when the results change (it ignores `runtime_s`), so a clean checkout stays clean; a changed file is a real change to commit with its cause.
- **Hand-maintained data** (phrase banks, templates, catalog, zones, `data/eval/sets/`, seed conversations) needs native-speaker review for new phrasing in Arabizi, Darija or French.
- **The model.** Do not retrain casually: it changes `classifier_version` and can move the pinned sample scores. Follow the [retraining procedure](docs/machine-learning.md#retraining) and commit the model, card, metrics, impact report and hero golden together.
- **Evaluation assets.** How to add or change golden sets, hand-written cases and floors is in [evaluation](docs/evaluation.md#modifying-evaluation-assets).

## Documentation

A change that alters behaviour, a setting, a command, an endpoint or a file's role updates the page that describes it, in the same pull request. Write for a reader who has not seen the code: describe what the system does and how to use it, not how it came to be. Prefer linking to the one authoritative page over repeating it. Verify commands and paths against the Makefile and the tree, and check that relative links resolve.

## Pull requests

Fill in the [template](.github/PULL_REQUEST_TEMPLATE.md): what and why, the checklist, and how to see the change (a command, an order to open, a screenshot for UI changes). Keep pull requests focused; unrelated cleanups belong in their own.

## Commit messages

Imperative and specific, optionally prefixed with the area or a type: `worker: never re-arm a rescore after an exception`, `docs: describe the extraction cache`.
