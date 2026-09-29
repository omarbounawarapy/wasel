# Failure analysis

The failure analyzer looks for **hidden failures**: conversations that look fine to the system that ran them but are wrong. Nothing raised an exception, a session was closed as done, a status says "confirmed", and yet the customer was told something untrue or asked the same thing twice. Ordinary runtime errors are visible, and this subsystem exists for the ones that are not.

It is an offline analysis tool with its own data, CLI and API endpoints. It does not sit in the order pipeline and never changes an order.

Code: `src/wasel/failures/` (`detect.py`, `semantics.py`, `rank.py`, `run.py`, `dataset.py`, `adapter.py`). Data: `data/agent_sessions.jsonl`, `data/agent_sessions_holdout.jsonl`. Reports: `data/reports/failures_*.json`.

## Model

The unit is a **session**: an ordered list of events from one agent run that confirms a COD order with a customer.

```json
{
  "session_id": "S001",
  "source": "synthetic",
  "context": {"channel_phone": "21600000006", "order_id": "O001"},
  "events": [
    {"i": 0, "t": 28, "type": "tool_call",   "tool": "lookup_customer", "args": {"phone": "..."}},
    {"i": 1, "t": 81, "type": "tool_result", "tool": "lookup_customer", "ok": true, "result": {"...": "..."}},
    {"i": 5, "t": 200, "type": "agent", "text": "..."},
    {"i": 6, "t": 260, "type": "user",  "text": "..."}
  ],
  "final": {"status_claimed": "confirmed"},
  "label": {"kind": "failure", "failures": ["unsupported_success_claim"]}
}
```

`label` exists only on synthetic sessions and is what accuracy is scored against. Sessions built from this app's database have no label.

### What counts as a failure

Six failure types, each with a severity used for ranking:

| Type | Severity | The agent... |
|---|---|---|
| `unsupported_success_claim` | 1.0 | told the customer the order is confirmed with no successful `confirm_order` call before it |
| `wrong_customer_record` | 1.0 | kept using a customer record whose phone number differs from the chat's |
| `incomplete_marked_done` | 0.8 | closed the session as done while the address was imprecise, or the customer's last question was never answered |
| `tool_error_ignored` | 0.7 | carried on after a tool failed, without retrying, escalating or apologising |
| `no_progress_search` | 0.5 | repeated the same search with the same input and no results |
| `repeated_question` | 0.4 | asked again for something the customer had already given |

Just as important is what is **not** a failure. The dataset labels every session with a `kind`:

| Kind | Meaning | Expected result |
|---|---|---|
| `success` | clean run | nothing found |
| `recovery` | a tool error or unclear answer that the agent handled (a retry that worked, a clarifying question) | nothing found |
| `ambiguous` | a judgment call: a reminder after hours of silence, hedged wording after an escalation | may be shown as "needs review", never counted as a failure |
| `failure` | one or more planted failures | found |

## Detectors and confidence

`detect.py` has one function per failure type. Each returns findings that carry evidence pointers (event index and the relevant text or tool result), a confidence and a signature that groups similar findings. A detector combines labels about what a message *says* with the session's structure: order of events, tool results, the final status.

| Confidence | Status | Meaning |
|---|---|---|
| ≥ 0.6 | `failure` | reported and counted |
| 0.35 to 0.6 | `needs_review` | ambiguous; listed after every confirmed failure |
| < 0.35 | dropped | not reported |

Confidence encodes how sure the rule is, for example: a success claim after a failed `confirm_order` scores 0.92, a claim with no call at all 0.85, and a hedged claim 0.45 (0.3 if the agent also escalated). A repeated question after the customer answered it scores 0.88; a reminder after silence 0.65, or 0.4 after more than an hour. A `tool_error_ignored` finding is not raised again for a failed tool result that already backs an unsupported success claim, so one fact produces one finding.

### The language layer

Detectors need to know whether a message is a success claim, is hedged, asks for an address or a confirmation, or answers such a question. That is the language layer (`semantics.py`):

- `RuleSemantics`: regular expressions for French and Arabizi. Free and deterministic. The default and the fallback.
- `LLMSemantics`: labels each unique message text with the `failure_label` LLM role, in batches of 25, through the governed client (`failure-label-v1` prompt, strict schema, caching, traces). Texts the model did not label fall back to the rules. It is used only with `--llm` and it does not use the usage meter, so it is not capped. The model only labels text; it never decides whether something is a failure. The detectors do.

## Grouping and ranking

Findings are grouped into **issues** by status, type and signature root (the signature before a parenthesised detail, so `confirm_order failed (timeout)` and `confirm_order failed (out_of_stock)` are one issue with a breakdown). An issue's priority is `severity × sessions affected × mean confidence`. Confirmed failures come before needs-review issues regardless of priority, and ranks start at 1. Each issue lists its sessions, share of sessions affected and its findings with evidence.

## Datasets

`python -m wasel.failures.dataset` (`make sessions`) writes two files of 130 sessions each from fixed seeds: 36 success, 26 recovery, 12 ambiguous and 56 failure sessions (with 63 planted failures in total across the six types). Rerunning produces byte-identical files, and a test checks the committed files against the generator.

| File | Phrasing | Purpose |
|---|---|---|
| `data/agent_sessions.jsonl` | `train`: the wording the detector patterns were written against | development set |
| `data/agent_sessions_holdout.jsonl` | `holdout`: different wording, addresses and seed, never used to write a rule | honest estimate of generalisation |

Sessions contain business data only. Phone numbers are the allowlisted fakes `21600000001` to `21600000009` (`make hygiene` rejects other numbers in fixtures and data).

## Adapter: this app's own orders

`adapter.py` rebuilds each order as a session so the same detectors can look at real pipeline behaviour. The conversation is the dialogue; each pipeline step becomes a tool call and result, in time order:

| Tool | Built from | `ok` means |
|---|---|---|
| `extract_order` | `extraction_runs` | the extraction was valid; a failed one is followed by a retry on the rules path |
| `score_order` | `risk_assessments` | always true; carries tier, action, confirmation, path |
| `update_order` | the address level of the extraction | always true |
| `confirm_order` | assessments where the customer's confirmation was read as `confirmed` | always true |
| `draft_message`, `send_message` | `outbound_drafts` | the draft was not blocked; sent |
| an event's type | `events` at level `error` | false (a failed step) |

The final status is the order's status. No names or phone numbers enter a session. In this data the "tool calls" are pipeline steps rebuilt from the database, not a live agent trace, so findings on app data are hints to investigate rather than verdicts.

## Running it

| Command | Reads | Writes |
|---|---|---|
| `make failures` | both synthetic files, and `var/app.db` (`DB=`) | `data/reports/failures_synthetic.json`, `failures_holdout.json` and `failures_db.json` |
| `make failures-llm` | both synthetic files, with the LLM language layer (needs `GROQ_API_KEY` exported) | `data/reports/failures_synthetic_llm.json`, `failures_holdout_llm.json` |
| `python -m wasel.failures.run --source synthetic\|holdout\|db [--llm] [--db PATH]` | one source | one report |
| `python -m wasel.failures.dataset` (`make sessions`) | nothing | the two session files |

`make failures` needs the database to exist; run `make seed` or start the app once. `failures_db.json` and the `*_llm.json` reports are not committed by default, so a run leaves untracked files.

Each report contains the ranked issues with grouped sessions and evidence, `by_status` counts, runtime and cost (0 LLM calls for rules), the limitations, and for labeled sources an `accuracy` block: micro precision and recall, per-type precision and recall with false-positive and missed session ids, clean sessions wrongly flagged, and the number of ambiguous sessions surfaced for review.

The API serves the same analysis live: `GET /api/failures?source=synthetic|holdout|app` runs the rules on demand and attaches the recorded LLM run from `data/reports/failures_<source>_llm.json` when that file exists (`llm_run` is null otherwise). `source=app` analyses the seeded and event orders plus the caller's sandbox orders when an `X-Visitor-Id` is sent. `GET /api/failures/sessions/{session_id}` returns one session with its findings. See [API](../api.md).

## Committed results and how to read them

| Source | Sessions | Micro precision | Micro recall |
|---|---|---|---|
| synthetic (train phrasing) | 130 | 1.00 | 1.00 |
| holdout | 130 | 0.84 | 0.65 |

The train result is not evidence of quality: the patterns were written against that data. The holdout figures are the estimate that matters, and they show real gaps. On the holdout wording the rules find none of the 17 unsupported success claims (the phrases were different from any pattern), `tool_error_ignored` has precision 0.43, and `repeated_question` recall is 0.58. The LLM language layer exists to close the wording gap, and a unit test with a scripted labeler shows it recovers claims the rules miss, but no LLM run is committed. Synthetic sessions are also cleaner than real traffic, so these are optimistic.

Known limits (also printed in every report): detectors are rules tuned to this dataset's tool names and phrasing, so new tools or languages need new patterns; the language layer can improve the labels but the structural rules must still match; ambiguous cases are surfaced for review rather than counted.

## Extending

- **New failure type.** Add a detector in `detect.py`, a severity and a `WHY` sentence, include it in `detect()`, plant it in `dataset.py` with train and holdout phrasing, and check the result with `make sessions` and `make failures`. Add a test to `tests/unit/test_failures.py`.
- **New wording.** Extend the patterns in `semantics.py` and confirm on the holdout file, not the train file.
