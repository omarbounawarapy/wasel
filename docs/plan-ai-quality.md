# Plan: AI quality phase (27 Sept)

Finishes the "refine every LLM interaction" phase. Four pieces, built in this order, each committed and pushed
on its own with `make check` green. Everything offline-testable; live runs are extra evidence, never a CI need.

## 1. Live eval (`make eval-live`)
- Run the 455 golden cases through the live Groq extractor + LLM judge → `reports/eval_live.json`.
- Set the `live:` floors in `eval/thresholds.yaml` from what the live run actually scores (raise, never
  invent). Record cost (tokens, calls) and runtime in the report.
- Findings that fail a floor go to STATUS as open points, not tuned away.

## 2. Monitor: drift + safety (`app/monitor.py`, `GET /api/monitor`, `GET /api/traces`)
Reads only what is already stored: trace ring buffer (+ `TRACE_FILE`), `risk_assessments`, `extraction_runs`,
`outbound_drafts.judge_json`. No customer text in the output.
- **Drift:** PSI of the recent window vs a committed reference (`data/monitor_reference.json`, built from the
  synthetic holdout by `make monitor-ref`) on language, address level, tier, extraction path. PSI ≥ 0.2 → alert.
- **Faithfulness:** dropped evidence quotes and dropped flags per extraction (the model quoted text that isn't in
  the chat = hallucination), judge `grounded=false` / `unsupported_claims` rate.
- **Safety:** judge reject rate by overreach class, classifier veto rate, `tone_ok=false` (toxicity proxy),
  injection-suspected rate, refusals (LLM answered but not in schema / non-order), fallback + cap rates.
- **Ops:** per role requests, cache hit rate, p50/p95 latency, tokens, prompt versions in use.
- Thresholds in `config/monitor.yaml`; `alerts[]` in the response.

## 3. Hidden-failure analyzer (SupplyzPro challenge) — `failures/`
A standalone tool over agent sessions (conversation turns + tool calls), with an adapter for our own app.
- **Session format** (`failures/schema.py`): session_id, turns (role, text, ts), tool calls (name, args,
  result, ok), final status the agent claimed.
- **Dataset** (`failures/dataset.py` → `data/agent_sessions.jsonl`): ~120 synthetic sessions of a COD order
  confirmation agent, deterministic, labeled: clean successes, legitimate retries/recoveries, ambiguous cases
  and planted failures (unsupported success claims, repeated questions, searches with no progress, wrong customer
  record, incomplete request marked finished, tool error swallowed).
- **Detectors** (deterministic first, cheap, explainable): each returns findings with evidence pointers
  (turn / tool call index + quoted text) and a confidence. Retries that end in success are recognised as
  recoveries, not failures.
- **Grouping + ranking:** group by (detector, normalized signature), then TF-IDF + agglomerative clustering of
  evidence text inside a detector; rank by severity × sessions affected × confidence.
- **Optional LLM pass** (`--llm`): only for ambiguous findings, the LLM adjudicates with the evidence; cost
  tracked. Deterministic result stands without it.
- **Scoring against labels:** precision/recall per failure type, runtime, cost → `reports/failures.json`.
- **Adapter:** turns our DB (messages, drafts, events, assessments) into sessions, so the same analyzer runs on
  the live app: `GET /api/failures`.
- CLI: `python -m failures.run [--source synthetic|db] [--llm]`, `make failures`.

## 4. Dashboard (`dashboard/`)
- **Order detail:** full draft decision panel: rewrite vs template, each layer (prefilter fails, classifier
  risk + label, judge verdict, grounded, unsupported claims, overreach, question count, model), attempts with
  feedback, route, send status (WhatsApp / recorded, delivery ticks).
- **New page "AI quality":** eval report (offline + live, gate status), monitor (drift PSI table, safety and
  faithfulness rates, alerts), per-role ops table, recent traces, active prompt versions + rollback command.
- **New page "Hidden failures":** ranked issue list → grouped sessions → evidence messages/tool results,
  uncertainty and limitations, runtime and cost; source switch synthetic / this app.
- API client + dashboard tests for the new pages.

## Cross-cutting
- Tests for each piece (unit + API + dashboard render), hygiene/lint clean, CI green after every push.
- Docs: README section, CHANGELOG, STATUS, `docs/failures.md` (method, limits, cost) for the award submission.
- Commits under Omar Bounawara, no AI attribution.
