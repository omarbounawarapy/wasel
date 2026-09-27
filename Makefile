# Makefile (05 §5): every command a teammate or CI needs. `make help` lists them.
SHELL         := /bin/bash
.SHELLFLAGS   := -eu -o pipefail -c
.DEFAULT_GOAL := help

PY          ?= python3
PYTEST      := $(PY) -m pytest
RUFF        := $(PY) -m ruff
URL         ?= http://localhost:8000
API_PORT    ?= 8000
UI_PORT     ?= 8501
DB          ?= var/app.db
PYTEST_ARGS ?=
export PYTHONPATH := .

# Offline, keyless, deterministic: the ONLY environment tests run under (CI runs this too).
TEST_ENV := APP_MODE=dev LLM_MODE=fail_all WORKER_ENABLED=false DEMO_MODE=true GEMINI_ENABLED=false \
            GROQ_API_KEY= GEMINI_API_KEY= WA_TOKEN= WA_APP_SECRET= WA_VERIFY_TOKEN= WA_SEND_ENABLED=false

up: ## backend :8000 + dashboard :8501 together, seeded (APP_MODE=dev unless set; reads .env). Ctrl-C stops both
	@set -a; [ -f .env ] && . ./.env; set +a; \
	APP_MODE=$${APP_MODE:-dev} SEED_ON_BOOT=$${SEED_ON_BOOT:-always} \
	  $(PY) -m uvicorn app.main:create_app --factory --port $(API_PORT) & api=$$!; \
	trap 'kill $$api 2>/dev/null; wait $$api 2>/dev/null || true' EXIT; trap 'exit 0' INT TERM; \
	$(PY) scripts/wait_health.py http://localhost:$(API_PORT) || exit 1; \
	echo "API        http://localhost:$(API_PORT)   (docs: /docs)"; \
	echo "Dashboard  http://localhost:$(UI_PORT)"; \
	API_BASE_URL=http://localhost:$(API_PORT) $(PY) -m streamlit run dashboard/app.py --server.port $(UI_PORT)

ui: ## dashboard only on :8501 (06 §1.5), against API_BASE_URL (default :8000)
	API_BASE_URL=$${API_BASE_URL:-$(URL)} $(PY) -m streamlit run dashboard/app.py --server.port $(UI_PORT)

.PHONY: help setup run up ui test lint fmt hygiene check seed demo generate train warm eval eval-live golden failures failures-llm sessions drill smoke mocks docker clean

help: ## list targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-10s %s\n",$$1,$$2}'

setup: ## pinned deps
	$(PY) -m pip install -q -r requirements.txt -r requirements-dev.txt

run: ## API on :8000 (APP_MODE=dev unless set; live LLM only if GROQ_API_KEY is set)
	APP_MODE=$${APP_MODE:-dev} $(PY) -m uvicorn app.main:create_app --factory --reload --port 8000

demo: ## the full app offline, no keys: public mode, seeded, rules path for new text
	APP_MODE=public SEED_ON_BOOT=always $(PY) -m uvicorn app.main:create_app --factory --port 8000

test: ## full offline suite, no keys, no network
	$(TEST_ENV) $(PYTEST) -m "not live" $(PYTEST_ARGS)

lint: ## ruff
	$(RUFF) check .

fmt: ## autofix
	$(RUFF) check --fix .

hygiene: ## no tracked secrets/DBs, fixture phones allowlisted, one clock, one LLM entry point
	bash scripts/hygiene.sh

eval: ## offline golden sets (455 cases, no keys) gated on eval/thresholds.yaml -> reports/eval.json
	$(TEST_ENV) $(PY) -m eval.run

eval-live: ## same golden sets through the live LLM extractor + judge (needs GROQ_API_KEY) -> reports/eval_live.json
	$(PY) -m eval.run --live

golden: ## rebuild eval/golden/*.jsonl from committed synthetic sources (deterministic, 0 LLM calls)
	$(PY) -m eval.build_golden

sessions: ## rebuild data/agent_sessions{,_holdout}.jsonl: labeled synthetic agent runs (deterministic)
	$(PY) -m failures.dataset

failures: ## hidden-failure analyzer, rules only, on the train + holdout sets and this app's DB -> reports/failures_*.json
	$(PY) -m failures.run && $(PY) -m failures.run --source holdout && $(PY) -m failures.run --source db --db $(DB)

failures-llm: ## same with the LLM language layer (needs GROQ_API_KEY) -> reports/failures_*_llm.json
	$(PY) -m failures.run --llm && $(PY) -m failures.run --source holdout --llm

check: hygiene lint test eval ## THE pre-merge gate. CI runs exactly this.
	@echo "check: green, ok to merge"

generate: ## 10,000 synthetic rows, seeded, zero LLM calls (lints 1-8)
	$(PY) -m ml.generate --seed 20260927 --n 10000

train: ## monotone XGBoost -> models/ + reports/ + tests/golden/hero.json (gates enforced)
	$(PY) -m ml.train

warm: ## rebuild data/seed/extraction_cache.jsonl (hand mode; LIVE=1 records with the dev key)
	$(PY) -m scripts.warm_cache $${LIVE:+--live}

seed: ## fresh $(DB): schema + catalog + demo_seed + committed cache (0 tokens)
	mkdir -p var && APP_MODE=dev SEED_ON_BOOT=always DB_PATH=$(DB) WORKER_ENABLED=false \
	  $(PY) -c "from app.main import create_app; from fastapi.testclient import TestClient; TestClient(create_app()).__enter__()"

drill: ## fallback drill, no keys
	$(TEST_ENV) $(PYTEST) tests/integration/test_backend.py -k fallback_drill -q

smoke: ## deployed/local URL: health+mode, try hero, reply, 409 (no key)
	$(PY) -m scripts.smoke $(URL)

mocks: ## dump mocks/*.json from a seeded in-process app (C3 contract for the frontend)
	$(PY) -m scripts.dump_mocks

docker: ## build the image exactly as the host will
	docker build -t cod-risk:local .

clean: ## remove caches and local DBs
	rm -rf .pytest_cache .ruff_cache htmlcov var/*.db var/*.db-wal var/*.db-shm
