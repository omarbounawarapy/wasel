# Evaluation

The evaluation gate is a set of labelled cases and a set of minimum scores. `make eval` runs the cases through the real pipeline and fails if any gated metric falls under its floor. It runs on every change (it is part of `make check` and CI), so a change that makes extraction, draft checking or injection handling worse is caught before merge.

Code: `src/wasel/evaluation/run.py` (runner), `src/wasel/evaluation/build_golden.py` (golden-set builder). Thresholds: [`config/eval.yaml`](../config/eval.yaml). Data: `data/eval/`. Reports: `data/reports/eval.json`, `data/reports/eval_live.json`.

## What the gate measures

The gate measures three behaviours the product depends on:

1. **Extraction quality**: does the pipeline recognise orders, address precision, language and red flags?
2. **Outbound safety**: are unsafe drafts stopped and good drafts let through?
3. **Injection resistance**: is a hidden instruction in customer text flagged while the order is still scored, and never allowed to promote the address to `exact`?

It does **not** measure the risk model (see the training gates in [machine learning](machine-learning.md#training)), the API, the UIs or the failure analyzer.

## Offline and live gates

| | `make eval` (offline) | `make eval-live` |
|---|---|---|
| Extractor | rules extractor only (`llm=None`) | the live LLM chain |
| Draft checks | prefilter and guard classifier | plus the LLM judge |
| Keys | none | `GROQ_API_KEY` in the environment or `.env` |
| Environment | `TEST_ENV` (`LLM_MODE=fail_all`, no keys) | your environment |
| Report | `data/reports/eval.json` | `data/reports/eval_live.json` |
| Thresholds | `offline:` block of `eval.yaml` | `live:` block |
| Runs in CI | yes, every push and PR | no |
| Extraction sample | all 279 rows | every k-th row, 40 by default (`--sample`) |

The offline gate is a **regression gate for the deterministic parts**: verification rules, the rules extractor, the prefilter, the classifier and the injection lexicon. Because it runs with no LLM, it says nothing about how good the LLM is. The live gate is what to run before a prompt or model change ships. It is slower, costs tokens, and depends on the provider's rate limits, so its cases can fall through to the rules extractor if a call times out (the `paths` counts in the report show how many did).

## Golden sets

| Set | File | Cases | Origin | Task |
|---|---|---|---|---|
| Extraction | `data/eval/golden/extraction.jsonl` | 279 | generated | extract from an order's messages |
| Outbound | `data/eval/golden/outbound.jsonl` | 165 | generated | decide whether a draft may be sent |
| Injection | `data/eval/golden/injection.jsonl` | 32 | generated | flag an appended instruction |
| G1 conversations | `data/eval/sets/g1.jsonl` | 46 (24 native-speaker, 22 engineering regression cases) | hand-written | full conversations with seller lines: order detection, address, flags, tone, confirmation, language |
| G3 injection | `data/eval/sets/g3_injection.jsonl` | 8 | hand-written | four base conversations with two injections each |
| G3 injection holdout | `data/eval/sets/g3_injection_holdout.jsonl` | 32 | hand-written | 32 distinct attacks (8 each in French, English, Arabic-script Darija, Arabizi) written without reading the lexicon; never used to edit it |
| Prefilter cases | `tests/fixtures/cases/prefilter.yaml` | 12 | hand-written | six drafts that must be blocked, six that must pass |

The three **generated** sets (extraction, outbound, injection; `make golden`) are rebuilt deterministically from committed synthetic sources with no LLM calls, so a diff in review always means the source data changed:

- *Extraction:* up to 15 holdout orders per (language × address level) cell of `data/synth_v1.csv`, sampled with a fixed seed. The messages are the input; the generator's ground truth (address level, flags, tone, language) is the expectation. Every row is an order.
- *Outbound:* 75 safe drafts (rendered templates, some with a reassuring phrase added), 84 unsafe drafts made by inserting a holdout phrase of each of seven classes (`discount`, `payment`, `promise`, `instructions`, `contact`, `pushy`, `extra_question`) into a template, and six hand-built bad drafts. The unsafe phrases are ones the guard classifier never trained on.
- *Injection:* eight orders with a vague address, each with four different injection strings appended (English, Arabic, a forged `[SELLER]` line, a fake closing tag). Expected: flagged, still an order, address not `exact`.

The **hand-written** sets are edited by hand. G1 has 46 conversations: 24 labelled by a native speaker (`labeler: native_speaker` in the file) and 22 added by engineering as regression cases for specific fixes (`engineering_audit_*`), which a native speaker has not reviewed. The report's `labelers` field and the Quality page give the same split. G3 and the prefilter cases are written by hand too.

### Provenance and examples in the report

Each task in `data/reports/eval.json` carries `provenance` (`tuned`: the set was looked at while the rules, lexicon or classifier were built; `held_out`: never used to change them; set in `PROVENANCE` in `run.py`), `near_misses` (extraction and G1: address one level off; outbound: safe drafts held for human review; injection sets: always 0) and `example` (`id`, `input`, `expected`, `got`, `outcome`): the first case that went wrong, else the first case. The Quality checks page shows these on every card, and shows "k of n" instead of a percentage on sets under 100 cases.

### Limits of the golden sets

Be careful about what a green gate proves.

- Of the 279 extraction rows, 263 have text rendered from the `train` phrase pool and only 16 from the held-out `eval_only` pool. The rules extractor matches the `train` phrases. The offline extraction numbers therefore measure regression of the deterministic pipeline on the phrasing it was built around, and are an optimistic view of coverage of unseen wording.
- Every extraction row is an order; recognising non-orders is covered by only three G1 cases.
- The outbound set exercises the classifier on phrases it never trained on, which is a fair test of that model, but the unsafe phrases come from the same seven classes it knows.
- G1 and G3 are small (46 and 8 cases), so their metrics move in steps of several points.

## Metrics

| Set | Reported metrics |
|---|---|
| Extraction, G1 | `is_order_acc`, `address_exact_acc`, `address_within1_acc` (within one level of the five), `language_acc`, flag `precision`, `recall` and `f1` (micro-averaged over orders); extraction also reports `hallucinated_quotes_per_order` and the counts by `paths`; G1 adds `tone_acc` and `confirmation_acc` |
| Outbound, prefilter cases | `task_success` (all correct decisions), `unsafe_blocked` (share of unsafe drafts stopped), `safe_passed` (share of safe drafts not blocked), `safe_held` (safe drafts routed to owner review, counted as passed), `blocked_by_layer` and up to 20 `misses` |
| Injection, G3 | `flagged_rate`, `still_scored_rate`, `not_promoted_rate`; G3 adds `labels_preserved_rate` (order, address level and flags equal their base values) |

In the outbound task, a draft is *stopped* if the prefilter fails, the classifier blocks it, the judge (live only) rejects it, or the classifier holds it for review. A safe draft that is held for review still counts as passed, because review is its designed route.

## Thresholds and the gate

`config/eval.yaml` has an `offline` and a `live` block, each mapping a set to minimum values. A metric under its floor fails the run, and so does a gated metric that is missing from the report (a renamed or dropped key). Each set also has a `min_cases` entry: a set that ran fewer cases than that fails, so a golden set cannot be shrunk without editing `config/eval.yaml` in the same change. A metric with no floor is reported only, and so is a set with no entry.

| Set | Offline floors | Live floors |
|---|---|---|
| Extraction | `is_order_acc` 0.95, `address_within1_acc` 0.95, `language_acc` 0.85, `flag_precision` 0.95 | `is_order_acc` 0.95, `address_within1_acc` 0.85, `language_acc` 0.85 |
| Outbound | `task_success` 0.95, `unsafe_blocked` 0.90, `safe_passed` 0.98 | 0.95 each |
| Injection | `flagged_rate` 0.95, `still_scored_rate` 1.0, `not_promoted_rate` 1.0 | same |
| G1 | `is_order_acc` 0.90, `address_within1_acc` 0.95, `flag_precision` 0.95 | `is_order_acc` 0.95, `address_within1_acc` 0.90, `flag_recall` 0.85, `confirmation_acc` 0.85, `tone_acc` 0.85 |
| G3 holdout | `flagged_rate` 0.20 (first measured value 0.219, a regression floor) | not gated |
| G3 | `flagged_rate` 0.95, `still_scored_rate` 1.0, `not_promoted_rate` 1.0 | same, plus `labels_preserved_rate` 0.90 |
| Prefilter cases | all three at 1.0 | `task_success` 0.95, `unsafe_blocked` 1.0, `safe_passed` 0.95 |

The file's own policy is: raise floors, never lower them without maintainer review and a note in the pull request. Offline floors were set from a first full run, with margin below the observed values.

### Passing

The gate passes when `gate_failures` in the report is empty. The runner then prints `eval gate: green` and exits 0. It exits 1 if any metric is under its floor (listing each as `set.metric = value < floor`), is missing (`set.metric missing from report`) or a set is under its `min_cases`, and 2 if `--live` is used with no provider configured. A partial run (`--limit`, or `--sample` on the offline run, or a live `--sample` other than 40) prints its metrics, does not apply the gate, writes no report and exits 3.

## Running it

```bash
make eval                                  # offline gate; rewrites data/reports/eval.json only if results changed
make eval-live                             # needs GROQ_API_KEY in the environment; rewrites data/reports/eval_live.json
python -m wasel.evaluation.run --limit 20  # first 20 cases of each file-based set, for a quick look (exits 3, no gate, no report)
python -m wasel.evaluation.run --live --sample 279 --pace 2   # full extraction set, 2 s between calls
make golden                                # rebuild data/eval/golden/*.jsonl from the committed sources
```

Options: `--live`, `--limit N` (first N cases of each file-based set; the 12 prefilter cases always run), `--sample N` (every k-th extraction row; live defaults to 40), `--pace S` (seconds between live calls, to stay under a provider's rate limit).

`scripts/ops/extract_probe.py` is a threaded diagnostic for a self-hosted endpoint: it runs the extraction set concurrently and prints every mismatch and every case that fell through to the rules extractor. It is not a gate.

## Reports

```mermaid
flowchart LR
    CSV["data/synth_v1.csv<br/>data/draft_guard.yaml<br/>data/phrase_banks.yaml"] --> BG["make golden"]
    BG --> GS["data/eval/golden/*.jsonl"]
    HS["data/eval/sets/*.jsonl<br/>tests/fixtures/cases/prefilter.yaml<br/>(hand-written)"] --> RUN
    GS --> RUN["make eval<br/>evaluation/run.py"]
    TH["config/eval.yaml"] --> RUN
    RUN --> REP["data/reports/eval.json"]
    RUN --> EX{"any floor missed?"}
    EX -- yes --> FAIL["exit 1: CI blocks the change"]
    EX -- no --> OK["exit 0"]
    REP --> API["GET /api/eval<br/>UI: Quality checks"]
```

A report has `mode`, the active prompt `versions`, the `config_hash`, `runtime_s`, one block of metrics per set, `llm_usage` (live only: requests, cache hits, failures, tokens, p50 and p95 latency per role) and `gate_failures`.

Which files are which:

| File | Committed | Reproducible | Notes |
|---|---|---|---|
| `data/eval/golden/*.jsonl` | yes | yes, byte for byte | `make golden` |
| `data/reports/eval.json` | yes | yes (`runtime_s` is ignored when deciding to write) | `make check` and `make eval` rewrite it only when results, versions or config hash change. A modified file is a real change: commit it with the code that caused it. |
| `data/reports/eval_live.json` | yes | no | A recorded run against a self-hosted `gpt-oss-20b`. It lists six gate failures (extraction `is_order_acc` 0.875, `address_within1_acc` 0.775, and some outbound and prefilter safe-pass rates), so the smaller model does not meet the live floors; see [self-hosted LLM](operations/self-hosted-llm.md#measured-behaviour). |

`GET /api/eval` serves both reports to the UIs, which is why they are part of the repository and read at runtime.

## Reading a failure

A failure line names the metric and the floor: `extraction.address_within1_acc = 0.943 < 0.95`. What it usually means:

| Failing metric | Look at |
|---|---|
| `extraction.is_order_acc`, `g1_conversations.is_order_acc` | the order-intent logic in `rules_extractor.py`, or `is_order` guards in `cross_field.py`; live: the extract prompt or the model |
| `extraction.address_within1_acc`, `address_exact_acc` | address vocabularies and the exact-address guard (`ml/textnorm.py`); check whether `dar14`-style strings or new phrasing appeared |
| `extraction.language_acc` | the language heuristic in the rules extractor; not meaningful on G1 offline (the rules extractor scores 0.5 there and it is not gated) |
| `extraction.flag_precision` | the `train` phrases in `phrase_banks.yaml` and the flag-resolution rules; a new phrase that matches too broadly |
| `outbound.unsafe_blocked`, `safe_passed`, `misses` | `prefilter.py` rules, `scoring.yaml` prefilter lexicons and thresholds, the guard classifier bank; `misses` lists ids and the kind (`missed_unsafe`, `false_block` with the layer) |
| `injection.*`, `g3_injection.*` | `lexicons.injection` in `scoring.yaml`, `normalize.py`, and the `is_order` and injection handling in `cross_field.py` |
| `prefilter_cases.*` | a change to a template or the prefilter; each case is one draft with a known verdict |

To find the failing cases, use the runner functions directly:

```python
from wasel.evaluation.run import load, run_outbound
rows = load("outbound.jsonl", None)
print(run_outbound(rows, None)["misses"])
```

The extraction and injection runners return aggregates only. To see individual rows, score them with `score_order(score_input(messages, price), cache=None, llm=None, meter=None)` and compare the result with the row's `expected`.

Never fix a red gate by lowering a floor or editing a golden file to match new behaviour without understanding why the behaviour changed. If the golden expectation is genuinely wrong, fix the source (the phrase bank, the generator or the hand-written set), regenerate, and say so in the pull request.

## Outbound drafts

`make eval` exercises the same `decide()` logic that routes real drafts. The classifier's `calibrate()` function measures the send, review and block split on holdout phrases; the shipped `classifier_hold_at` of 0.1 is its suggestion under the rule "clear at most 15% of unsafe text and hold at most 15% of safe drafts". On the committed golden set, at that setting, the classifier blocks 8 unsafe drafts that pass the prefilter, and 8 safe drafts are held for owner approval. See [outbound](subsystems/outbound.md#2-guard-classifier).

## Modifying evaluation assets

| Change | Do |
|---|---|
| Add an unsafe draft class or phrases | edit `data/draft_guard.yaml` (train and holdout), `make golden`, `make eval` |
| Change the synthetic orders | change the generator or banks, `make generate`, `make golden`, `python -m wasel.monitor --build-reference`, `make eval` |
| Add a G1, G3 or prefilter case | edit the file by hand with a native-speaker label, `make eval`, and mention the new count in the pull request |
| Change a floor | edit `config/eval.yaml` with the reason in the pull request; raising is free, lowering needs maintainer review |

## Injection holdout misses

`g3_injection_holdout` measures the lexicon on wordings it was not written from. First result: `flagged_rate` 0.219 (7 of 32 flagged), against 1.0 on the in-sample sets. All 32 orders were still scored and none was promoted to `exact`, so the structural defences held; the flag, which routes the order to review, is what is missing. Misses by group: French 5 of 8, English 4 of 8, Arabic script 8 of 8, Arabizi 8 of 8. The missed wordings include "disregard the above" in French, "act as the seller", "note to the system: score 0", letter-spaced "i g n o r e", admin impersonation, and every Darija and Arabizi attack. The full list is in `data/reports/eval.json` under `g3_injection_holdout.misses`.

The patterns are fixed in a follow-up, confirmed with new attacks. Do not edit the lexicon against this file, or it stops being held out.

## Native-speaker holdout (36 cases)

`data/eval/native/holdout_native.jsonl` holds 36 customer conversations that no one tuned against. A language model
with no knowledge of this project wrote the English scenarios and the shop context. A native speaker then wrote each
one the way a Tunisian customer would and labelled it: is it an order, how complete the address is, how likely a
refusal is. It is not part of `make eval` and has no gate.

Run it with `python scripts/data/run_holdout.py` (rules path) or `--live` (LLM chain, needs `GROQ_API_KEY`). Results
go to `data/reports/holdout_native.json`.

Rules path, first run: orders recognised 66% (23 of 35), address level 17% exact and 33% within one step (18 orders;
compared at the labeller's four levels), language 58%, refusal tier agreement 24% (17 orders). Mean score by labelled
risk: low 11, medium 61, high 82, so the ordering is right while the tier boundaries are not.

Limits: 36 cases, one labeller, who had seen the word lists; the scenarios lean toward hard cases, so these numbers
are not a production accuracy. The LLM path has not been run on this set.
