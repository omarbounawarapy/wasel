# Contributing

The code is not open source (see [LICENSE](LICENSE)). Issues from anyone are welcome; code changes are accepted from maintainers and invited contributors.

## Development setup

You need Python 3.11, `make`, and Node 22 if you work on the web UI.

```bash
python3.11 -m venv .venv
make setup        # pinned Python dependencies + the wasel package (editable install)
make check        # hygiene + ruff + offline tests + offline eval gate; needs no API keys
make up           # API on :8000 + Streamlit dashboard on :8501, seeded
make web          # build the Next.js UI into web/dist (served by the API at /)
make web-dev      # Next.js dev server on :5173 against the API on :8000
```

`make help` lists every target. The [architecture document](docs/architecture.md) explains how the pieces fit, and each folder's role is listed in the [README](README.md#project-layout).

## Workflow

1. Get `make check` green before you change anything.
2. Work on a branch per change, named `<area>/<change>`, e.g. `worker/no-rearm-after-error`.
3. Include tests with the change. A missing test is allowed only as a visible `pytest.skip(reason=...)`.
4. Rebase on `main` and run `make check` again. CI runs the same target, and on `main` it also builds the web UI and boots the server in public mode.
5. Open a pull request and fill in the template.

When changing a shared interface (`src/wasel/contracts.py`, `src/wasel/api/models.py`, `src/wasel/db/schema.sql`, `config/scoring.yaml`, `Makefile`, `requirements*.txt`), update its consumers in the same pull request.

## House rules the checks enforce

- Read time through `src/wasel/clock.py`, never `datetime.now()`.
- No LLM SDKs: providers are called with `httpx` from `src/wasel/llm/` only.
- No secrets, `.env` or `*.db` files in git.
- Editing a prompt means bumping its version in `config/llm.yaml` and `config/prompts/VERSIONS` (prompt files are sha-locked).
- Every number the UI shows comes from code or `data/reports/*.json`, never from the LLM.
- Public mode must never send WhatsApp messages or bypass the visitor sandbox.

## Style

`make fmt` fixes what ruff can. Line length is 125. Match the surrounding code: short docstrings, no comments that restate the code.

## Commit messages

Imperative and specific, optionally prefixed with the area: `worker: never re-arm a rescore after an exception`.
