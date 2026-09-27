## What and why

<!-- One or two sentences. Link the issue or spec item (e.g. M-7, S-1, 01 §5.2). -->

## Lane

- [ ] Omar: AI/ML (`app/llm`, `app/extraction`, `app/scoring`, `app/outbound`, `ml/`, `prompts/`, `schemas/`)
- [ ] Jesser: backend (`app/db`, `app/api`, `app/ingress`, `worker.py`, `state.py`)
- [ ] Montassar: frontend + infra (`dashboard/`, `Makefile`, `Dockerfile`, CI, `settings.py`, `mode.py`)
- [ ] Fedi: content (`data/phrase_banks.yaml`, templates wording, README prose)

## Checklist

- [ ] `make check` is green locally (no API keys)
- [ ] Tests are in this PR, or there is a visible `skip(reason=...)`
- [ ] Contract file touched? (`contracts.py`, `api/models.py`, `mocks/`, `schema.sql`, `scoring.yaml`, `Makefile`, `ci.yml`, `requirements*`) If yes, the consuming lane has been told: <!-- who -->
- [ ] Prompt changed? `PROMPT_VERSION` bumped and `make warm` re-run
- [ ] Nothing in public mode can now send WhatsApp messages or bypass the visitor sandbox

## How to see it

<!-- e.g. `make up`, open order #2601, click Simulate reply. Screenshot if the UI changed. -->
