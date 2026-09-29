## What and why

<!-- One or two sentences. Link the issue if there is one. -->

## Checklist

- [ ] `make check` is green locally (no API keys needed)
- [ ] Tests are in this PR, or there is a visible `skip(reason=...)`
- [ ] Touched a shared interface (`app/contracts.py`, `app/api/models.py`, `app/db/schema.sql`, `scoring.yaml`, `Makefile`, `ci.yml`, `requirements*`)? Its consumers are updated in this PR
- [ ] Prompt changed? `prompts/VERSIONS` and `PROMPT_VERSION` bumped and `make warm` re-run
- [ ] Nothing in public mode can now send WhatsApp messages or bypass the visitor sandbox

## How to see it

<!-- e.g. `make up`, open order #2601, click Simulate reply. Screenshot if the UI changed. -->
