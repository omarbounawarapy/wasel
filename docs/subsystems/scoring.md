# Scoring

Scoring turns a verified extraction plus the order record into a number, a tier, a recommended action, a confidence and an explanation. Everything here is deterministic code and configuration. The LLM only supplies the extraction, and the model, the rules and the wording of every reason are computed locally.

Code: `src/wasel/scoring/` (`score_order.py`, `model.py`, `reason.py`, `catalog.py`, `config.py`, `stub.py`) and `src/wasel/ml/features.py`. Tunable values live in [`config/scoring.yaml`](../configuration/scoring.md). How the model was made is in [machine learning](../machine-learning.md); how a rescore fits into the pipeline is in the [order pipeline](../architecture/order-pipeline.md#scoring-one-order).

## Contract

`score_order(inp, *, cache, llm, meter, config) -> ScoreResult` is a pure function. It reads no database and no clock, and makes no network call except through the injected `llm`. The one side effect is binding order metadata to the trace context. Provider problems never raise; they end in the rules path. A programmer error (for example a feature dict with a NaN) does raise, and the worker turns an exception into `needs_review`.

`make_scorer(...)` returns the function with its dependencies bound. `scoring/stub.py` is a fixed-output scorer with the same signature that the persistence tests use.

## Resolving the order record

Before the model runs, three order fields are resolved. Precedence is always: what the seller entered, then reference data, then a default.

| Field | Resolution |
|---|---|
| Product | `match_product` compares the seller-entered name, else the extraction's verified `product_quote`, with every catalog name and alias in every language, after normalization. An exact match scores 100; otherwise RapidFuzz `token_set_ratio`. The best match at or above `catalog_match.min_score` (80) wins. |
| Price (TND) | The seller-entered price if given. Else the matched catalog unit price × quantity, with quantity taken from the seller or the extraction and clamped to 1 to 5 (`catalog_match.quantity_clamp`). Else unknown. The price never comes from the LLM. |
| Zone | The seller-entered zone (`zone_source = csv`). Else the gazetteer applied to the verified address quotes, then to all customer texts, latest text first, an alias match beating a keyword match. Else unknown. The gazetteer is [`data/zones.yaml`](../data.md#top-level-files). |
| Quantity | Seller-entered, else the extraction's `quantity` |

A gazetteer match by keyword (for example "douar") is stored as `zone_source = gazetteer` on the order, although the assessment's `context_json` may still say `keyword`.

## Features

`ml/features.py: build_features` produces the six inputs of the model, in this fixed order. The order is part of the model contract: the trained booster, the model card and `make train` all use it.

| Feature | Values | Source | Direction (monotone constraint) |
|---|---|---|---|
| `address_specificity` | 0, 0.25, 0.5, 0.75, 1.0 for `none`, `city_only`, `area_or_landmark`, `street_and_landmark`, `exact` | final address level after verification | decreasing: a better address never raises the score |
| `red_flag_count` | integer | number of surviving, evidence-checked flags | increasing |
| `tone_score` | -1 positive, 0 neutral, 1 uncertain, 2 negative | tone after the tone gate | increasing |
| `price_tnd` | TND | resolved price | increasing |
| `zone_encoded` | 0 urban, 1 suburban, 2 rural | resolved zone | increasing |
| `customer_refusal_rate` | `(refusals + 0.6) / (completed + 2)` | customer history; a new customer is 0.30 | increasing |

A missing price or zone is imputed with a default (`price_tnd` 69 TND, the catalog median; `zone_encoded` 1) and named in the assessment's `imputed` list. The features are never NaN. The defaults are the `SERVE_DEFAULTS` constant in `ml/features.py`; the `serve_defaults` block in `scoring.yaml` is not read by the code.

## Model

`scoring/model.py` loads the XGBoost booster at `model.file` from `scoring.yaml` (`models/risk_xgb_v1.json`) once per process. One `predict(..., pred_contribs=True)` call returns the probability of refusal and the per-feature contributions in log-odds. `model_score = 100 × p`, rounded to one decimal. The classifier version recorded on every assessment is `xgb_v1-` plus the first eight hex characters of the model file's SHA-256, so any file change is visible.

If the model file does not exist, the scorer falls back to the documented prior, `score_prior` in `ml/features.py`, records classifier version `prior_v1`, and writes `<TIER> <score> (model unavailable: documented prior)` as the reason. That is a degraded mode, not something to ship.

## Reply adjustments and the final score

After the model, `reply_adjustments` in `scoring.yaml` apply, in this order:

| Situation | Adjustment |
|---|---|
| Customer `confirmed` | score × `multiply` (0.6) |
| Customer `declined`, `reschedule` or `ambiguous` | recorded in `adjustments`, score unchanged |
| Trigger `no_reply_timeout` | score + `add` (15), no extraction |

`final_score = round(clip(score, 0, 100))` (`final_score.clip`). These two numbers are cold-start assumptions, labelled as such in the reason text. The wording of the confirmed and timeout reasons is fixed in `reason.py` ("×0.6", "+15"); changing the values in the config changes the score and the adjustment record, but not that sentence.

## Tier, action and template

Tiers are fixed cut-offs, not percentiles: `low` below `tiers.low_max` (35), `medium` below `tiers.medium_max` (65), else `high`. The recommended action follows:

| Condition (checked in this order) | Action |
|---|---|
| Customer declined | `cancelled` |
| Path is `rules` | `review` |
| Tier `low` | `ship` |
| Tier `high` and price ≥ `actions.prepay_min_tnd` (250) | `prepay` |
| Otherwise | `confirm` |

The follow-up template is chosen by `choose_template` and only for medium and high tiers whose action is not `cancelled` or `review`: `T_PREPAY` for a prepay action, else `T_ADDRESS` if the final address level is `none`, `city_only` or `area_or_landmark`, else `T_CONFIRM`. See [outbound](outbound.md).

## Confidence

`confidence` is `high` or `low` and is an operational rule, not a calibrated probability. It is `low` if **any** of these holds, and the reasons are stored in `confidence_reasons`:

| Reason | Condition |
|---|---|
| `rules_path` | the extraction came from the rules extractor |
| `not_primary_model` | it came from the fallback model or provider (a cache hit counts as primary only if the cached entry came from the primary model) |
| `llm_cap_reached` | a usage cap stopped the chain |
| `clarity_unclear` | the extraction's clarity is `unclear` |
| `dropped_flags` | more than `confidence.max_dropped_flags` (1) flags failed verification |
| `injection_suspected` | the injection lexicon matched |
| `product_not_in_catalog` | no catalog match, even if the seller entered a price |
| `imputed_inputs` | an input other than the price was imputed (in practice, the zone) |
| `near_tier_boundary` | the final score is within `confidence.boundary_margin` (10) of 35 or 65 |
| `no_reply_timeout` | the assessment is a timeout rescore |

Low confidence never blocks scoring, but it prevents automatic sending and, on the rules path, sends the order to a person.

## Reasons

Reasons are built by `scoring/reason.py` from the model's per-feature contributions. No model writes them.

1. **Points.** Contributions in log-odds are converted to score points that add up exactly to `model_score − 100 × base`, where base is the model's bias probability. When the contributions nearly cancel (`|Σφ| < reasons.linearise_if_abs_sum_phi_below`, 0.05) a linear approximation is used instead.
2. **Selection.** For medium and high tiers, the largest positive drivers of at least `reasons.min_pts` (3) points, at most `reasons.max_drivers` (3). For low tier, up to two of the most negative. The zone is always added when its magnitude is at least `always_show_zone_if_abs_pts_at_least` (3), so the effect of zone is never hidden.
3. **Wording.** Each driver has a plain-language label with the customer's own words where available: `vague address ("9rib el jemaa") +17`. Quotes are truncated to 40 characters and wrapped in Unicode first-strong and pop isolates (U+2068 and U+2069) so an Arabic quote cannot reorder the surrounding English sentence.
4. **Assembly.** `<TIER> <score> · base <n> · <drivers> · <adjustments>`. `reason_short` keeps as many leading parts as fit in 90 characters.
5. **Diff.** On a rescore, `reason_diff` compares this version's per-feature points with the previous version's and lists changes of at least `reasons.diff_min_delta_pts` (3), largest first, followed by the adjustments: `v1 87 → v2 16 · full address given ("...") −32 · ...`. It uses the stored `points` of the previous assessment, so both versions must have been scored by a model (not the prior).

Every quoted phrase in a reason has already passed the evidence check, because reasons are built only from verified spans.

## Worked example

Sample order #2601: three customer messages ("nheb el casque bluetooth", "Douar Ouled Ali, 9rib el jemaa", "ama ghali chwaya. mouch dima fi dar, 3ayetli 9bal. mazelt manich met2aked").

| | Version 1 | Version 2 (after the customer replies with a full address) |
|---|---|---|
| Features (address, flags, tone, price, zone, refusal rate) | 0.5, 3, 1, 220, 2, 0.30 | 1.0, 0, 0, 220, 2, 0.30 |
| Model score | 87.1 | 26.8 |
| Adjustment | none | confirmed × 0.6 |
| Final score, tier, action | 87, `high`, `confirm` (220 TND is under the 250 prepay threshold) | 16, `low`, `ship` |
| Template | `T_ADDRESS` (address level `area_or_landmark`) | none |

These values are pinned by `tests/golden/hero.json` and `tests/e2e/test_hero.py`, which run the scenario through the real `score_order` with frozen extractions.

## Provenance of a score

Every assessment stores the exact ingredients: `classifier_version`, `config_hash`, `prompt_version`, `path`, features, imputed names and points. `config_hash` is the SHA-256 of `config/scoring.yaml`, `data/zones.yaml` and `data/catalog.yaml` joined by a NUL byte, shown as its first eight characters (`/api/health` reports the same value). It does not cover the phrase banks or the outbound templates. Given an assessment, a maintainer can tell whether a later score differs because of the configuration, the model file or the prompt.
