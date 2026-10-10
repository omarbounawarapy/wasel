# Makefile: every command a developer or CI needs. `make help` lists them.
SHELL         := /bin/bash
.SHELLFLAGS   := -eu -o pipefail -c
.DEFAULT_GOAL := help

# the project venv if there is one (.venv/bin on Linux/macOS, .venv/Scripts on Windows, where
# `python3` is only the Microsoft Store stub), else python3 on PATH
PY          ?= $(firstword $(abspath $(wildcard .venv/bin/python .venv/Scripts/python.exe)) python3)
PYTEST      := $(PY) -m pytest
RUFF        := $(PY) -m ruff
URL         ?= http://localhost:8000
API_PORT    ?= 8000
UI_PORT     ?= 8501
UI_HOST     ?= 127.0.0.1
DB          ?= var/app.db
PYTEST_ARGS ?=

# Offline, keyless, deterministic: the ONLY environment tests run under (CI runs this too).
TEST_ENV := APP_MODE=dev LLM_MODE=fail_all WORKER_ENABLED=false DEMO_MODE=true GEMINI_ENABLED=false \
            GROQ_API_KEY= GEMINI_API_KEY= WA_TOKEN= WA_APP_SECRET= WA_VERIFY_TOKEN= WA_SEND_ENABLED=false

up: ## the seller UI and API on :8000, seeded (APP_MODE=dev unless set; reads .env). Builds web/ if missing. Ctrl-C stops it
	@test -f web/dist/index.html || $(MAKE) web
	@eval "$$($(PY) scripts/dev/loadenv.py)"; \
	echo "Wasel on http://localhost:$(API_PORT)   (seller UI; API reference at /docs; analyst view: make ui)"; \
	APP_MODE=$${APP_MODE:-dev} SEED_ON_BOOT=$${SEED_ON_BOOT:-always} \
	  $(PY) -m uvicorn wasel.main:create_app --factory --port $(API_PORT)

ui: ## analyst view (Streamlit operator tools) on :8501, against API_BASE_URL (default :8000); needs the API running
	cd dashboard && API_BASE_URL=$${API_BASE_URL:-$(URL)} $(PY) -m streamlit run app.py --server.address $(UI_HOST) --server.port $(UI_PORT)

web: ## build the web/ UI (Next.js static export -> web/dist); `make up` / `make demo` then serve it at :8000/
	cd web && npm ci --no-audit --no-fund && npm run build

web-dev: ## web/ UI with hot reload on :5173 against the API on :8000 (run `make run` or `make up` first)
	cd web && npm run dev

# ---- self-hosting with make (docs/operations/deployment.md)
serve: ## host run: API + web UI, no reload, settings from .env (unset APP_MODE = public), on HOST:PORT (127.0.0.1:8000)
	@eval "$$($(PY) scripts/dev/loadenv.py)"; 	echo "Wasel on http://$${HOST:-127.0.0.1}:$${PORT:-$(API_PORT)}  mode=$${APP_MODE:-public}"; 	$(PY) -m uvicorn wasel.main:create_app --factory --host $${HOST:-127.0.0.1} --port $${PORT:-$(API_PORT)} --workers 1

deploy: ## on the host: pull main, install deps, rebuild the UI; then restart `make serve` and run `make smoke URL=<public url>`
	git pull --ff-only
	$(MAKE) setup web
	@echo "updated to $$(git rev-parse --short HEAD). Restart the server (systemctl restart wasel, or Ctrl-C + make serve),"
	@echo "then check it from outside: make smoke URL=<your public URL>"

lock: ## regenerate the hashed locks: requirements.lock (dev + dashboard, any OS) and the Render image's (linux/amd64); needs uv
	uv pip compile requirements.txt requirements-dev.txt dashboard/requirements.txt --universal --generate-hashes --python-version 3.11 --no-strip-extras -o requirements.lock
	uv pip compile deploy/render/requirements.txt --generate-hashes --python-version 3.11 --python-platform x86_64-manylinux_2_28 --no-strip-extras -o deploy/render/requirements.lock

render-smoke: ## build the Render image, run it on :10000 and smoke-test it (docker/podman; CI runs this)
	docker build -f deploy/render/Dockerfile -t wasel-render .
	-docker rm -f wasel-render-smoke >/dev/null 2>&1
	docker run -d --name wasel-render-smoke -p 10000:10000 -e PORT=10000 wasel-render >/dev/null
	trap 'docker rm -f wasel-render-smoke >/dev/null 2>&1' EXIT; \
	$(PY) scripts/dev/wait_health.py http://127.0.0.1:10000 && $(PY) scripts/ops/smoke.py http://127.0.0.1:10000

wa-up: ## live WhatsApp test: ephemeral public URL for the webhook + Meta callback registration (docs/subsystems/whatsapp.md)
	bash scripts/ops/wa_webhook_up.sh

llm-serve: ## run ON a GPU host: install + serve vLLM (MODEL, VLLM_PORT, VLLM_ARGS; docs/operations/self-hosted-llm.md)
	bash scripts/ops/vllm_serve.sh serve

llm-check: ## verify the self-hosted LLM endpoint from the client (GROQ_BASE_URL + GROQ_API_KEY in .env)
	bash scripts/ops/vllm_serve.sh check

.PHONY: help setup lock run up ui web web-dev serve deploy render-smoke wa-up llm-serve llm-check test lint fmt hygiene check seed demo generate train warm eval eval-live golden failures failures-llm sessions drill smoke mocks clean

help: ## list targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-10s %s\n",$$1,$$2}'

setup: ## pinned deps + the wasel package (editable, src/ layout)
	$(PY) -m pip install -q --require-hashes -r requirements.lock
	$(PY) -m pip install -q --no-deps -e .

run: ## API on :8000 (APP_MODE=dev unless set; live LLM only if GROQ_API_KEY is set)
	APP_MODE=$${APP_MODE:-dev} $(PY) -m uvicorn wasel.main:create_app --factory --reload --port 8000

demo: ## the full app offline, no keys: public mode, seeded, rules path for new text
	APP_MODE=public SEED_ON_BOOT=always $(PY) -m uvicorn wasel.main:create_app --factory --port 8000

test: ## full offline suite, no keys, no network
	$(TEST_ENV) $(PYTEST) -m "not live" $(PYTEST_ARGS)

lint: ## ruff
	$(RUFF) check .

fmt: ## autofix
	$(RUFF) check --fix .

hygiene: ## no tracked secrets/DBs, fixture phones allowlisted, one clock, one LLM entry point
	bash scripts/dev/hygiene.sh

eval: ## offline golden sets (no keys) gated on config/eval.yaml -> data/reports/eval.json
	$(TEST_ENV) $(PY) -m wasel.evaluation.run

eval-live: ## same golden sets through the live LLM extractor + judge (needs GROQ_API_KEY) -> data/reports/eval_live.json
	$(PY) -m wasel.evaluation.run --live

golden: ## rebuild data/eval/golden/*.jsonl from committed synthetic sources (deterministic, 0 LLM calls)
	$(PY) -m wasel.evaluation.build_golden

sessions: ## rebuild data/agent_sessions{,_holdout}.jsonl: labeled synthetic agent runs (deterministic)
	$(PY) -m wasel.failures.dataset

failures: ## hidden-failure analyzer, rules only, on the train + holdout sets and this app's DB -> data/reports/failures_*.json
	$(PY) -m wasel.failures.run && $(PY) -m wasel.failures.run --source holdout && if [ -f $(DB) ]; then $(PY) -m wasel.failures.run --source db --db $(DB); else echo "skipped: no $(DB) yet (start the app once, then re-run)"; fi

failures-llm: ## same with the LLM language layer (needs GROQ_API_KEY) -> data/reports/failures_*_llm.json
	$(PY) -m wasel.failures.run --llm && $(PY) -m wasel.failures.run --source holdout --llm

check: hygiene lint test eval ## THE pre-merge gate. CI runs exactly this.
	@echo "check: green, ok to merge"

generate: ## 10,000 synthetic rows, seeded, zero LLM calls (lints 1-8)
	$(PY) -m wasel.ml.generate --seed 20260927 --n 10000

train: ## monotone XGBoost -> models/ + data/reports/ + tests/golden/hero.json (gates enforced)
	$(PY) -m wasel.ml.train

warm: ## rebuild data/seed/extraction_cache.jsonl (hand mode; LIVE=1 records with the dev key)
	$(PY) scripts/data/warm_cache.py $${LIVE:+--live}

seed: ## fresh $(DB): schema + catalog + demo_seed + committed cache (0 tokens)
	mkdir -p var && APP_MODE=dev SEED_ON_BOOT=always DB_PATH=$(DB) WORKER_ENABLED=false \
	  $(PY) -c "from wasel.main import create_app; from fastapi.testclient import TestClient; TestClient(create_app()).__enter__()"

drill: ## fallback drill, no keys
	$(TEST_ENV) $(PYTEST) tests/integration/test_backend.py -k fallback_drill -q

smoke: ## deployed/local URL: health+mode, try hero, reply, 409 (no key)
	$(PY) scripts/ops/smoke.py $(URL)

mocks: ## rewrite tests/fixtures/api/*.json (frozen API responses checked by the API contract test) from a seeded in-process app
	$(PY) scripts/data/dump_mocks.py

clean: ## remove caches and local DBs
	rm -rf .pytest_cache .ruff_cache htmlcov var/*.db var/*.db-wal var/*.db-shm
