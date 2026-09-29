# `config/scoring.yaml`

The tunable numbers and lexicons of scoring, drafting and the rules extractor, in one file. It is read once when the app starts (`scoring/config.py: load_config`), so a change needs a restart. Together with `data/zones.yaml` and `data/catalog.yaml` it is hashed into the `config_hash` stored with every assessment and shown by `/api/health`, which lets you tell which configuration produced a score.

Every numeric value in the file is a cold-start assumption, labelled as such in its comments, not something measured from real orders. [Scoring](../subsystems/scoring.md) explains how the values are used; this page lists what each one controls and what depends on it.

On load, the sections `tiers`, `confidence`, `actions`, `reply_adjustments`, `lexicons`, `prefilter` and `roi` must exist, and `tiers.low_max` must be below `tiers.medium_max`, otherwise start-up fails with a `ValueError`. Other sections that the code indexes directly (`model`, `final_score`, `catalog_match`, `reasons`, `timeouts`, `auto_send`) fail with a `KeyError` at first use if removed. `window` and `outbound` are optional and fall back to built-in defaults.

Every key in the file is read by code. Keys that once existed without an effect were removed.

## `model`

| Key | Effect |
|---|---|
| `file` | Path, relative to the repository root, of the XGBoost booster (`models/risk_xgb_v1.json`). Read by the scorer, `/api/health` and the trainer, which writes it. Pointing it at another file changes the `classifier_version` of every new assessment. |

## `tiers`, `actions`, `confidence`

```yaml
tiers:      { low_max: 35, medium_max: 65 }
confidence: { boundary_margin: 10, max_dropped_flags: 1 }
actions:    { prepay_min_tnd: 250 }
```

| Key | Effect | Notes |
|---|---|---|
| `tiers.low_max` | Scores below this are `low` (action `ship`) | Fixed cut-offs, not percentiles. Also used by `make train` for the tier-ordering gate and the impact simulation. |
| `tiers.medium_max` | Scores below this and at or above `low_max` are `medium`; the rest `high` | Must exceed `low_max`. |
| `confidence.boundary_margin` | A final score within this many points of either cut-off makes the assessment `low` confidence (`near_tier_boundary`) | Larger values send more borderline orders to a person and stop them auto-sending. |
| `confidence.max_dropped_flags` | More dropped (unverified) flags than this makes confidence low | |
| `actions.prepay_min_tnd` | A `high` tier order priced at or above this gets action `prepay`; below it, `confirm` | Also drives the `T_PREPAY` template and the impact simulation. |

Changing tiers or actions changes decisions for new scorings only; stored assessments keep their values. Retraining is not needed. Rerun `make eval` and `make test`: the hero test pins tier and action for the sample order.

## `reply_adjustments` and `final_score`

```yaml
reply_adjustments:
  confirmed:        { multiply: 0.6 }
  no_reply_timeout: { add: 15, route: needs_review }
final_score:      { clip: [0, 100], round: 0 }
```

`confirmed.multiply` scales the model score when the customer confirms. `no_reply_timeout.add` is added when a timeout rescore fires. `final_score.clip` bounds the result. The order of application and the effect on reasons are in [scoring](../subsystems/scoring.md#reply-adjustments-and-the-final-score). The timeout always sends the order to `needs_review` (rule 5 in `state.py`) and the score is always rounded to an integer. The reason text quotes the configured values.

## `auto_send` and `outbound`

```yaml
auto_send: { max_tnd: 150, max_auto_messages_per_order: 2, gate: classifier }
outbound:
  static_insert_when_tier_at_least: medium
  judge: { classifier_block_at: 0.5, classifier_hold_at: 0.1, max_attempts: 2 }
```

| Key | Effect |
|---|---|
| `auto_send.gate` | `classifier`: the guard classifier's `send` decision alone clears a rewrite for automatic sending. `judge`: the LLM judge must also approve. Missing defaults to `judge`. |
| `auto_send.max_tnd` | Orders priced above this are never auto-sent |
| `auto_send.max_auto_messages_per_order` | Loop guard: at most this many automatic messages per order (the database allows 0 to 2) |
| `outbound.judge.classifier_block_at` | Classifier `p_unsafe` at or above this blocks a rewrite |
| `outbound.judge.classifier_hold_at` | At or above this (and below block) the draft goes to a person; below it the classifier clears it. Lower values hold more drafts. The comment in the file records the measured trade-off; `calibrate()` in `guard_clf.py` recomputes it, and a test pins the shipped value to the calibrated suggestion. |
| `outbound.judge.max_attempts` | Number of rewrite attempts before falling back to the static template |

Automatic sending also needs `WA_AUTO_SEND=true`, `DRAFT_LLM=true` and a non-public mode ([outbound](../subsystems/outbound.md#routing)). Tightening the thresholds is always safe; loosening them should come with a `make eval` run and a look at `calibrate()`.

## `catalog_match`, `reasons`, `window`

| Key | Effect |
|---|---|
| `catalog_match.min_score` | Minimum RapidFuzz score (0 to 100) for a product to match the catalog. Lower values match more product names, and more wrong ones. Unmatched products give `confidence=low`. |
| `catalog_match.quantity_clamp` | Quantity range used when multiplying a catalog price (`[1, 5]`) |
| `reasons.max_drivers` | Most drivers named in a reason for medium and high tiers |
| `reasons.min_pts` | A driver must move the score by at least this many points to be named |
| `reasons.always_show_zone_if_abs_pts_at_least` | The zone is always named when it moves the score this much |
| `reasons.diff_min_delta_pts` | Smallest per-feature change listed in a reason diff |
| `reasons.linearise_if_abs_sum_phi_below` | Switch to a linear points approximation when contributions nearly cancel |
| `window.max_messages`, `window.max_chars` | Extraction window caps (12 messages, 2,000 characters). Changing them alters what long conversations render, so the cache keys of conversations over a cap change and their cached extractions stop matching. Optional. |

## `timeouts`

```yaml
timeouts: { debounce_s: { demo: 4, prod: 15 }, no_reply_s: { demo: 60, prod: 21600 } }
```

`demo` applies when `DEMO_MODE=true` (the default), `prod` otherwise. `debounce_s` is how long after the last message the worker waits before scoring. `no_reply_s` is how long an order may sit in `awaiting_reply` before a timeout rescore adds points and sends it to review; it does not apply in public mode. Values are read at start.

## `lexicons`

| Key | Used by | Effect |
|---|---|---|
| `ack` | rules extractor | Words that, at the start of a customer line after the seller line, read as `confirmed` |
| `decline` | rules extractor | Words that read as `declined` |
| `order_intent` | rules extractor | Darija commitment verbs that make a message an order even without a product name |
| `injection.normalized` | injection detector, draft prefilter | Regexes run on the normalized text with format characters removed |
| `injection.defused` | injection detector, draft prefilter | Regexes run on the sanitized model view |

`injection` is the **only** injection lexicon. A pattern that is too broad flags legitimate orders (they go to review); a gap lets an injection through unflagged. Test additions against `tests/unit/test_extraction.py` (`test_injection_lexicon_hits` and `..._false_positives`) and the injection golden sets, then run `make eval`. The regexes are case-insensitive Python patterns.

## `prefilter`

| Key | Effect |
|---|---|
| `payment`, `discount`, `promise` | Terms that fail a draft if present in it but not in its template. Matched as whole tokens on normalized text. |
| `allowlist` | Phrases removed before matching (`code postal`, which would otherwise look like a payment term) |
| `max_chars` | Longest allowed draft (400) |

Adding a term only ever makes the check stricter. Adding an allowlist entry weakens it; do so only for a phrase that appears in an approved template.

## `roi`

Assumptions for the simulated impact shown in the UI (`c_fail_tnd`, `prevent_rate` per action, `prepay_conversion_loss`, `gross_margin`, `msg_cost_tnd`, `sensitivity_confirm`). Only `make train` reads them, when it writes `data/reports/impact.json`. Runtime behaviour does not depend on them. The impact endpoint shows `simulated: true` and lists these as its assumptions.

## What a change requires

| You change | Restart the app | Re-run `make eval` | Regenerate or retrain | Also update |
|---|---|---|---|---|
| tiers, actions, confidence, auto-send, timeouts, reasons | yes | yes | no | `tests/golden/hero.json` if the sample order moves (via `make train`, or edit deliberately) |
| `reply_adjustments`, `final_score` | yes | yes | no | hero golden; the fixed reason wording |
| `catalog_match`, `window` | yes | yes | no | extraction cache (`make warm`) if a sample conversation would render differently |
| `lexicons.ack/decline/order_intent` | yes | yes | no | |
| `lexicons.injection`, `prefilter` | yes | yes | no | |
| `outbound.judge` thresholds | yes | yes | no | `calibrate()` output |
| `model.file` | yes | yes | you need a trained file at that path | |
| `roi` | no runtime effect | no | `make train` to refresh `impact.json` | |
