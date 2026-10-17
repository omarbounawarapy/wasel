# Changelog

Notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). There are no tagged releases yet.

## [Unreleased]

### Changed
- Licence changed to MIT (was a source-available licence), so the repository is open source. The Geist fonts bundled with the pitch deck keep the SIL Open Font License.

### Added
- Render free-plan hosting for the public demo (`render.yaml`, `deploy/render/Dockerfile`, [guide](docs/operations/render.md)), now linked from the README, the docs index and the deployment page, with a "Which target?" note: Render free for a public demo, `make serve` for a host you control, Cloudflare only with a paid plan.
- Evaluation gate: golden cases in three generated sets (extraction, outbound drafts, injection) built deterministically from synthetic data (`make golden`). `make eval` gates them on `config/eval.yaml` and is part of `make check`, so CI blocks a change that drops under a floor. `make eval-live` runs the same sets through the live LLM extractor and judge.
- LLM registry `config/llm.yaml` with one-step rollback (`scripts/ops/rollback.py`), per-request input caps and trace records; a monitor endpoint (`GET /api/monitor`, `GET /api/traces`) reporting drift and safety rates.
- Outbound rewrite and judge (flag `DRAFT_LLM`): the LLM rewrites the template, then a prefilter, a local guard classifier (char n-gram TF-IDF with logistic regression, `data/draft_guard.yaml`) and an LLM judge check it. One retry with feedback, then the static template. If the judge is down the draft goes to a person, unless the `classifier` auto-send gate is configured and the classifier clears it.
- WhatsApp send: drafts go out through the Cloud API from the dashboard, inside the 24 h window only, and the returned message id picks up delivered and read statuses from the webhook. `WA_AUTO_SEND` sends cleared drafts without a click (never in public mode).
- Self-hosted LLM support: `GROQ_BASE_URL` points the chain at any OpenAI-compatible endpoint; `scripts/ops/vllm_serve.sh` (`make llm-serve`, `make llm-check`) serves and verifies a vLLM host.
- Hosting with `make serve` and a Cloudflare Tunnel (`make tunnel`), a systemd unit, and `make smoke` for post-deploy checks.
- Next.js web UI in `web/`, built to a static export and served by the API at `/`.
- Streamlit dashboard in `dashboard/`: risk queue, order detail with highlighted evidence, paste an order, WhatsApp inbox, activity, simulated impact. Every read and action goes through the API.
- WhatsApp Cloud API webhook: verification, HMAC signature check, deduplication, delivery statuses, fails closed; `hub.verify_token` redacted from access logs.
- Backend: SQLite schema and repository, debounced rescore worker, order state machine, versioned append-only assessments, the `/api` endpoints, public-mode visitor sandboxes and purge.
- Scoring core: 12-field extraction schema with repair, evidence checking and highlight spans; Groq → Groq → Gemini → rules provider chain with caps and no retries; monotone XGBoost on six features trained on 10,000 synthetic rows (holdout AUC 0.784); `config/scoring.yaml`; reason strings and reason diffs; hero golden test (HIGH 87 → LOW 16).
- Prompt-injection guardrails: `is_order` guard, one lexicon, Unicode control stripping, size caps.
- Tooling: Makefile, `make check` (hygiene, ruff, offline tests, eval gate), CI, `.env.example`, smoke test.
- Runnable API examples in `examples/`.

### Documentation
- Documentation rebuilt from the implementation: [`docs/`](docs/README.md) now has a getting-started guide, architecture (overview, order pipeline, data model), subsystem references (extraction, scoring, LLM layer, outbound, WhatsApp, monitoring, failure analysis), machine-learning, evaluation, API, data and configuration references, development guides (commands, testing, extending) and operations guides (deployment, self-hosted LLM, troubleshooting). README, SECURITY, CONTRIBUTING, the examples and the dashboard guide were rewritten, and a guide for the web UI was added.

### Changed
- Repository layout: the Python code is now the installable `wasel` package under `src/wasel/` (formerly `app/`, `ml/`, `eval/`, `failures/`; `eval` is `wasel.evaluation`); prompts, schemas and `scoring.yaml` live in `config/`; golden sets in `data/eval/`; committed reports in `data/reports/`; frozen API responses in `tests/fixtures/api/`; scripts are grouped in `scripts/{data,ops,dev}/`; `make setup` installs the package editable. Commands: `python -m wasel.ml.train`, `uvicorn wasel.main:create_app`, `python scripts/ops/smoke.py URL`.
- WhatsApp ingestion uses the Meta Cloud API webhook instead of chat exports.

### Removed
- Contributor material for outside contributors: `CONTRIBUTING.md` (moved to the team workflow page), the contributors charts in the README and their `contributors-chart` workflow and generator script. `CODE_OF_CONDUCT.md` is kept.

### Fixed
- Numeric libraries run single-threaded (`src/wasel/__init__.py`, guard classifier training); the default one-thread-per-core pools used about 7× the CPU for the same result.
- `make up` waits up to 180 s for the API, since a cold start with seeding can take more than 60 s.
- Working tree forced to LF line endings; CRLF checkouts broke the prompt sha lock.
