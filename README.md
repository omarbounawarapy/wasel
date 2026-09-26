# COD Risk

[![ci](https://github.com/omarbounawarapy/hackathon/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/omarbounawarapy/hackathon/actions/workflows/ci.yml)

Scores Tunisian cash-on-delivery orders for refusal risk from the customer's own messages (Darija, Arabizi, Arabic, French), recommends an action, and drafts the confirmation message. A person approves every send. Built for GOMYCODE "Come Build With AI" (27 Sept 2026). **Synthetic data only.**

Current state, gates and open points: [`STATUS.md`](STATUS.md). The build spec: [`docs/council-spec/`](docs/council-spec/README.md).

## Run it

```bash
make setup      # pinned deps (requirements.txt + requirements-dev.txt)
make up         # API on :8000 + dashboard on :8501, seeded, dev mode. Ctrl-C stops both
```

Open http://localhost:8501. With no keys, the samples use recorded LLM results and new text is scored by the rules extractor. For live extraction put `GROQ_API_KEY` (and optionally `GEMINI_API_KEY`, `GEMINI_ENABLED=true`, `GEMINI_MODEL=gemini-3.5-flash-lite`) in `.env` or the environment; `make up` reads `.env`. Every variable is listed in [`.env.example`](.env.example).

| Command | What it does |
|---|---|
| `make up` | API + dashboard together (`APP_MODE=dev` unless set) |
| `make run` / `make ui` | API only / dashboard only (against `API_BASE_URL`) |
| `make demo` | API in public mode, the way the hosted demo runs |
| `make check` | the pre-merge gate: hygiene + lint + offline tests, no keys (CI runs exactly this) |
| `make help` | every target |

## Layout (spec 01 §1)

```
app/          FastAPI backend: api/, db/, ingress/ (WhatsApp webhook), llm/, extraction/, scoring/, outbound/, worker.py
dashboard/    Streamlit dashboard: talks to the API over HTTP only (see dashboard/README.md)
ml/           synthetic data generator and XGBoost training
prompts/ schemas/ scoring.yaml     extraction prompt, JSON schemas, scoring config
data/         catalog, zones, phrase banks, outbound templates, seed conversations, synthetic dataset
models/ reports/                   trained model + card, generated metrics (impact, eval)
mocks/        API responses for frontend work without a backend
scripts/      warm_cache, dump_mocks, smoke, hygiene, wait_health
tests/        unit/ integration/ contract/ e2e/ (incl. the dashboard) golden/ fixtures/
docs/         council spec, code handoff
```

Planning documents stay at the root: `PRD.md`, `SYSTEM_DESIGN.md`, `execution_plan.md`, `hackathon_playbook.md`, `handoff.md`, `FEDI.md`.
