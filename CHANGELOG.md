# Changelog

Notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). There are no tagged releases yet; the first will be `submission-v1` (see [07 §8](docs/council-spec/07-scope-schedule-delivery.md)). Entries below were backfilled from the git history.

## [Unreleased]

### Added
- Outbound LLM-as-judge (S-3, flag `DRAFT_LLM`): the LLM rewrites the template, then prefilter → local draft-guard classifier (char n-gram TF-IDF + logistic regression, `data/draft_guard.yaml`) → LLM judge (`judge-v1`, approval re-checked in code). One retry with feedback, then the static template; judge down → needs review, never auto-send. The dashboard shows the verdict and classifier risk. (27 Sept)
- WhatsApp send (S-2): drafts go out through the Cloud API from the dashboard, only inside the 24 h window; the returned wamid picks up delivered/read statuses from the webhook. `WA_AUTO_SEND` sends judge-approved `auto_send` drafts without a click (never in public mode). (27 Sept)
- Repository presentation: README rewrite with screenshots and diagrams, [architecture](docs/architecture.md) and [team guide](docs/team-guide.md) with Mermaid diagrams, runnable [`examples/`](examples/), LICENSE (all rights reserved, Z-Team), CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, issue and PR templates, this changelog.
- Streamlit dashboard in `dashboard/`, ported from the `cod-risk-poc` prototype: risk queue, order detail with highlighted evidence, paste an order, WhatsApp inbox, activity, simulated impact. Every read and action goes through the API. (26 Sept)
- `make up` starts the API (:8000) and the dashboard (:8501) together, seeded. (26 Sept)
- WhatsApp Cloud API webhook: verification, HMAC signature check, dedupe, delivery statuses, fails closed; `hub.verify_token` redacted from access logs. (26 Sept)
- Backend: SQLite schema and repository, debounced rescore worker, order state machine, versioned append-only assessments, the `/api` endpoints, public-mode visitor sandboxes and purge. (26 Sept)
- Scoring core: 12-field extraction schema with repair, evidence checking and highlight spans; Groq → Groq → Gemini → rules provider chain with caps and no retries; monotone XGBoost on 6 features trained on 10,000 synthetic rows (holdout AUC 0.784); `scoring.yaml`; reason strings and reason diffs; hero golden test (HIGH 87 → LOW 16). (26 Sept)
- Prompt-injection guardrails: `is_order` guard, one lexicon, Unicode control stripping, size caps. (26 Sept)
- Text baseline classifier (TF-IDF character n-grams + logistic regression) for comparison. (26 Sept)
- Tooling: Makefile, `make check` (hygiene + ruff + offline tests), CI that also boots the Docker image in public mode, `.env.example`, smoke test, frozen API mocks. (26 Sept)
- Planning and spec: hackathon playbook, PRD, system design, execution plan, the council build spec in `docs/council-spec/`, per-person gate checklists, `STATUS.md`. (25–26 Sept)

### Changed
- Repository aligned with the council tree: backend at the root (was `poc/`), dashboard in `dashboard/`, CI from the root `.github/`. (26 Sept)
- WhatsApp ingestion switched from chat exports to the Meta Cloud API sandbox webhook. (25 Sept)

### Fixed
- `make up` waits up to 180 s for the API, since a cold start with seeding takes more than 60 s. (27 Sept)
- Working tree forced to LF line endings; CRLF checkouts broke the prompt sha lock. (26 Sept)
