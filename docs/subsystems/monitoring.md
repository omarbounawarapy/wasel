# Monitoring

`GET /api/monitor` reports whether the system is drifting or misbehaving, computed from data the app already stores. It answers "is the input mix changing, is the model inventing evidence, are the safety layers doing their job, are the providers healthy" without exposing customer text. The thresholds are in [`config/monitor.yaml`](../../config/monitor.yaml).

Code: `src/wasel/monitor.py`; trace summary from `src/wasel/llm/trace.py`. Web pages: "Live monitor", "AI call log" and "Quality checks" in the [web UI](../interfaces.md); the analyst view's "Quality checks" page.

## What is measured

The report looks at the most recent `window` (200) assessments, drafts and LLM attempts, whatever their origin. In `public` mode that includes every visitor's rows, so the numbers describe the whole deployment. The endpoint has no authentication and returns rates and codes only.

| Section | Metrics | Source |
|---|---|---|
| `drift` | Population stability index (PSI) of `language`, `address_level` and `tier` against the reference mix | `risk_assessments` joined to `extraction_runs`; `data/monitor_reference.json` |
| `faithfulness` | `hallucinated_quotes_per_extraction` (evidence quotes the model wrote that are not in the chat, dropped by code), `dropped_flags_per_extraction`, `invalid_extraction_rate`, `injection_rate`, `fallback_rate` (share of assessments whose path is not `llm`, `cascade_ack` or `cascade_cache`) | `extraction_runs`, `risk_assessments` |
| `safety` | Draft `routes` and `sources`, `judge_reject_rate`, `judge_ungrounded_rate`, `judge_tone_fail_rate`, `judge_unavailable_rate`, `classifier_veto_rate`, `overreach` breakdown | `outbound_drafts.judge_json` |
| `ops` | `llm_error_rate`, `refusal_rate` (the provider answered but not in schema: `schema_rejected`, `parse_error`, `truncated`), per-role attempts, tokens, p50 and p95 latency and models, plus the in-process trace summary | `llm_usage`, trace ring buffer |
| `alerts` | Drift and ceiling violations | derived |

PSI is `Σ (q − p) · ln(q / p)` over the union of categories with an epsilon floor of 0.0001. A common reading is that below 0.1 the mix is stable and above 0.2 it has moved noticeably; `drift_psi` sets the alert line at 0.2.

## Alerts

An alert is raised when:

- a drift feature has at least `min_samples` values and a PSI of at least `drift_psi`; or
- a metric named in `ceilings` exceeds its ceiling **and** the section it belongs to has at least `min_samples` data points (faithfulness counts extractions, safety counts judged drafts, ops counts attempts).

Below `min_samples` (20) a metric is reported but never alerts, because a rate over a handful of rows is noise. A freshly seeded app therefore shows numbers and no alerts.

| Ceiling | Value | Watches |
|---|---|---|
| `hallucinated_quotes_per_extraction` | 0.10 | the model quoting text that is not in the conversation |
| `dropped_flags_per_extraction` | 0.20 | flags failing evidence verification |
| `invalid_extraction_rate` | 0.05 | extractions that fell to the rules path |
| `refusal_rate` | 0.05 | providers answering outside the schema |
| `fallback_rate` | 0.30 | orders scored by a fallback model, fallback provider or rules |
| `injection_rate` | 0.10 | orders flagged for injection |
| `judge_reject_rate` | 0.40 | LLM judge rejecting rewrites |
| `judge_ungrounded_rate` | 0.10 | drafts with claims the order does not support |
| `judge_tone_fail_rate` | 0.05 | judge finding pressure or rudeness |
| `judge_unavailable_rate` | 0.10 | judge calls that could not answer |
| `classifier_veto_rate` | 0.20 | guard classifier blocking a rewrite |
| `llm_error_rate` | 0.10 | any non-`ok` provider attempt |

With no LLM configured, `fallback_rate` and `invalid_extraction_rate` are high by design, and an alert on them after 20 rules-path orders is expected.

## The reference mix

Drift needs a baseline. `data/monitor_reference.json` holds the distributions of language, address level and tier from scoring the golden extraction set offline (279 rows). It is rebuilt with:

```bash
python -m wasel.monitor --build-reference
```

The command is deterministic and overwrites the file. A test (`test_reference_is_committed_and_matches_the_builder`) fails if the committed file no longer matches what the builder produces, which happens whenever the golden set, the rules extractor or the scoring configuration changes in a way that shifts those distributions. Rebuild it in the same change.

## Related traces

`GET /api/traces?role=&order_id=&limit=` returns recent LLM trace records, newest first (limit capped at 500): ids, versions, models, outcomes, latency and tokens, never customer text. They come from an in-process buffer of 5,000 records that is emptied on restart. Set `TRACE_FILE` to also append every record to a JSONL file. See [LLM layer](llm.md#tracing).

## Changing thresholds

`monitor.yaml` is read on each request. Lowering a ceiling makes alerts easier to trigger; raising one hides problems, so a change should come with a note on why the previous value was wrong. The file is documented in [configuration](../configuration/README.md).
