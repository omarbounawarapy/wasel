# Data + ML: generator, label, features, scoring, hero

> Council final spec — Alchemist lens (Round 3). Source of truth for its area. Where this file conflicts with a **Conductor ruling** in [README.md](README.md#conductor-rulings), the ruling wins. Unverified external facts are marked [VERIFY].


### 0. Grain, files, lineage

**One row of `data/synth_v1.csv` = one synthetic order at first scoring (v1, pre-reply, no `[SELLER]` line).**

| File | Committed | Contents |
|---|---|---|
| `ml/features.py` | yes | `FEATURES` tuple; `LEVEL_TO_SPEC`, `TONE_ENC`, `ZONE_ENC`; `PRIOR` constants; `S()`, `p_true()`, `score_prior()`; `smoothed_rate()`; `zone_from_text()`; `resolve_flags()`; `tone_gate()`; `build_features()` (vector, context and imputed list). The single import for the generator, trainer and serve path. |
| `ml/textnorm.py` | yes | `normalize()` (§6.4 rules), `find_span()`, `standalone_numbers()`, `has_building_token()`, `passes_exact_guard()` (§5). Imported by the serve evidence check, the exact guard, the generator lints and the tests. |
| `ml/generate.py` | yes | `python -m ml.generate --seed 20260927 --n 10000`. A rerun gives byte-identical output. It doesn't import `app.llm`, `groq`, `google.genai`, `openai` or `httpx`. |
| `ml/train.py` | yes | `python -m ml.train`. Writes the model, the card, the metrics, the golden hero file and the impact report (§6). |
| `ml/eval_skew.py` | yes | Runs eval rows through the real `score_order` in eval mode: no cascade, no cache, no fallback (§12). |
| `data/phrase_banks.yaml`, `data/catalog.yaml`, `data/zones.yaml` | yes | Fedi's banks, the 15-product catalog and the gazetteer. |
| `data/synth_v1.csv`, `data/synth_v1.meta.json` | yes | About 3–4 MB. The meta file holds the seed, the sha256 of each YAML and of `ml/features.py`, `n`, the base rate, the split counts and the git SHA. |
| `models/risk_xgb_v1.json`, `models/risk_xgb_v1.card.json` | yes | Booster plus card (§6). |
| `reports/train_metrics.json`, `reports/impact.json`, `reports/skew_eval.json`, `reports/extraction_eval.json` | yes | Written by scripts and served or read statically. |
| `tests/golden/hero.json` | yes | Written by `train.py`. Exact v1/v2 scores and reason strings for the copy. |

Lineage: `phrase_banks/catalog/zones.yaml` + seed → `generate.py` → `synth_v1.csv` → `train.py` → `model.json` → `score_order()` at serve time, where the features come from the LLM.

The label never touches text, and text never touches the label.

---

### (1) Generator

#### 1.1 Seeds and streams

`SeedSequence(20260927).spawn(4)` gives 4 streams: `rows`, `split`, `eval_subset`, `text`.

| Stream | What it drives |
|---|---|
| `rows` | Sequential latents and labels, in row order |
| `split` | One stratified permutation |
| `eval_subset` | One stratified draw from the holdout |
| `text` | Per row, `default_rng([text_seed_int, row_id])`. Text rendering for a row depends only on that row and the banks. |

Consequences:
- A phrase-bank edit changes `text`/`messages_json` only. Features, labels, the split, the model and the hero stay identical.
- Test ML1 asserts this: rerun with an edited bank, and every non-text column is byte-equal.

XGBoost itself uses `random_state=42, n_jobs=1`.

#### 1.2 Rows and split

- `n = 10,000`.
- **Split:** 8,000 `train` / 2,000 `holdout`, stratified on (`refused` × `zone`) with the `split` stream. Column `split`.
- **`eval_subset`:** 40 holdout rows, **2 per (`address_level` × `language`) cell** (5 × 4 = 20 cells), drawn with the `eval_subset` stream. Column `eval_subset` (bool).
- These are the only generator rows that ever reach an LLM, through `ml/eval_skew.py`.
- No time split: rows have no temporal order. The card says so.

#### 1.3 Columns

**Latents are sampled per row in this order from the `rows` stream.** All distributions are **synthetic assumptions**, not market facts.

| Column | Type | Distribution / rule |
|---|---|---|
| `row_id` | int | 0…9999 |
| `zone` | enum | urban .55 / suburban .30 / rural .15 **[ASSUMPTION]** |
| `zone_encoded` | int | urban 0 · suburban 1 · rural 2 |
| `governorate`, `place_name` | str | uniform over `zones.yaml` entries with that zone (cosmetic; fills `{place}`) |
| `address_level` | enum | Conditional on zone, over `none, city_only, area_or_landmark, street_and_landmark, exact`. Urban `[.02,.05,.18,.35,.40]`, suburban `[.03,.08,.27,.32,.30]`, rural `[.05,.12,.40,.28,.15]` |
| `address_specificity` | float | `LEVEL_TO_SPEC`: none 0 · city_only .25 · area_or_landmark .5 · street_and_landmark .75 · exact 1.0 |
| `has_geo_pin` | bool | Only if `exact`, p=.15. Renders a `[CUSTOMER:location pin]` line. **Context only, not a model feature.** |
| `product_id` | enum | `catalog.yaml` weights (§1.5) |
| `product_category` | enum | from the catalog |
| `quantity` | int | 1: .85 · 2: .12 · 3: .03 |
| `price_tnd` | float | catalog `unit_price × quantity` |
| `customer_completed_orders` (`n`) | int | {0:.45, 1:.15, 2:.12, 3:.07, 4:.06, 5:.05, 6:.04, 8:.03, 10:.03} |
| `customer_refusal_count` (`r`) | int | `Binomial(n, q)`, with `q ~ Beta(2, 6)` per row; 0 if n=0 |
| `customer_refusal_rate` | float | `(r + 0.6) / (n + 2)`, so a new customer gets 0.30 |
| `tone` | enum | positive .25 / neutral .50 / uncertain .18 / negative .07 |
| `tone_score` | int | positive −1 · neutral 0 · uncertain 1 · negative 2 |
| `flags_gt` | JSON list[str] | Independent Bernoulli per code (§1.4), sorted by the fixed code order in §4.3 |
| `red_flag_count` | int | `len(flags_gt)`, 0–6 |
| `language` | enum | arabizi .35 / darija_arabic_script .25 / fr .20 / mixed .20 **[ASSUMPTION]**. The generator never emits schema value `ar`. |
| `S` | float | §2. **Diagnostics only; `train.py` never reads it.** |
| `p_true` | float | §2. **Diagnostics only (calibration); never a training input.** |
| `refused` | int 0/1 | §2 |
| `split` | enum | train / holdout |
| `eval_subset` | bool | §1.2 |
| `text_pool` | enum | `eval_only` if `eval_subset`, else `train` |
| `messages_json` | JSON list | `[{"role":"customer","kind":"text"|"location","text":...}]`, 1–3 customer messages |
| `text` | str | Customer messages joined with `\n` |
| `gt_evidence_json` | JSON | `{"address": "...", "flags": {"code": "phrase"}, "tone": "phrase"|null}`. Rendered, pre-normalization strings used by the extraction eval. |

#### 1.4 Flag probabilities

| Code | Probability |
|---|---|
| `vague_location` | none .5 · city_only .6 · area_or_landmark .7 · street_and_landmark .1 · exact 0 |
| `availability_uncertain`, `price_hesitation`, `pressure_or_inconsistency` | By tone: positive (.03, .04, .02) · neutral (.08, .06, .03) · uncertain (.45, .25, .08) · negative (.25, .35, .25) |
| `third_party_recipient` | .06 |
| `prior_refusal_mention` | .02, or .17 if `r > 0` |

#### 1.5 Catalog

`catalog.yaml` has 15 rows. Prices are synthetic placeholders, aliases per language are Fedi's, and the P12 name is fixed for the hero.

```
P01 25 cosmetics .10 · P02 35 cosmetics .09 · P03 45 fashion .10 · P04 59 fashion .10 · P05 69 fashion .08
P06 79 home .08 · P07 89 home .07 · P08 99 fashion .07 · P09 129 home .06 · P10 149 electronics .06
P11 179 electronics .05 · P12 220 electronics .05 ("casque bluetooth") · P13 279 electronics .04
P14 349 home .03 · P15 450 electronics .02
```

Catalog median unit price = **69** (P05). That's the serve default for an unmatched product.

#### 1.6 Latent → text rendering (from Fedi's banks; the renderer never sees `S`, `p_true` or `refused`)

**Pool:** rows with `text_pool == eval_only` draw every phrase from the `eval_only` lists, and all other rows from the `train` lists. **Slots and product aliases are not split:**
- slots are proper nouns shared with the gazetteer
- aliases are needed by the serve-side catalog matcher

**Segments, one each:**
1. **Product:** a catalog alias in the row language, inside a `order_intro` phrase (`"nheb {product}"`).
2. **Address:**
   - one phrase from `address.<level>.<lang>` with slots filled
   - `{place}` comes from the row's `place_name`
   - `{landmark}`, `{street}` come from `slots`
   - `{number}` is an integer 1–120 (it must pass `passes_exact_guard`)
   - for `none`, render a no-location phrase with p=.5, else skip the segment
3. **Flags:** one phrase per GT flag from `flags.<code>.<lang>`. **`vague_location` evidence always comes from `flags.vague_location`** (vagueness markers such as `"9rib {landmark}"` or `"ki tousel kalemni"`), never from the address phrase. So the flag is observable in text whenever it's in the ground truth, and absent otherwise.
4. **Tone:** for **positive, uncertain and negative**, always one phrase from `tone.<tone>.<lang>`. Neutral gets no marker.
5. **Time:** a neutral time phrase with p=.4.
6. **Pin:** if `has_geo_pin`, a separate `{"kind":"location"}` message.

**Assembly:**
- `mixed` picks a language per segment (arabizi/fr/darija_arabic_script, uniform).
- The address segment comes first with p=.70; otherwise the order is shuffled.
- 70% of rows are 1 message. The other 30% are split at segment boundaries into 2 (p=.2) or 3 (p=.1) messages.

**`phrase_banks.yaml` format (the Fedi → Omar contract):**

```yaml
version: 1
# Every leaf "cell" is {train: [...], eval_only: [...]}, keyed by language:
# arabizi | darija_arabic_script | fr   (mixed is composed, never authored)
order_intro:
  arabizi: {train: ["nheb {product}", "3andkom {product}?"], eval_only: ["n7eb nechri {product}"]}
  fr: {...}
  darija_arabic_script: {...}
address:
  none:                {arabizi: {train: [...], eval_only: [...]}, fr: ..., darija_arabic_script: ...}
  city_only:           {...}   # "{place}"-level only
  area_or_landmark:    {...}   # e.g. "Douar {place}", "7ay {place}" (no vagueness marker inside)
  street_and_landmark: {...}   # "{street}, {landmark} {place}"
  exact:               {...}   # MUST contain {number} or a building token (lint 2)
flags:
  vague_location:            {arabizi: {train: ["9rib {landmark}", "ki tousel kalemni"], eval_only: [...]}, ...}
  availability_uncertain:    {...}
  price_hesitation:          {...}
  third_party_recipient:     {...}
  prior_refusal_mention:     {...}
  pressure_or_inconsistency: {...}
tone:
  positive:  {...}
  uncertain: {...}   # NEW: hedges about the purchase itself ("mazelt manich met2aked"), no availability/price words
  negative:  {...}
time: {arabizi: {train: [...], eval_only: [...]}, ...}
slots:                              # not split
  landmark: {arabizi: ["el jemaa", "el pharmacie", ...], fr: [...], darija_arabic_script: [...]}
  street:   {...}
```

**Split rule:** for each cell,
- `len(eval_only) ≥ max(1, ceil(0.30 · (len(train) + len(eval_only))))`
- `len(train) ≥ 1`

**Suggested sizes:** 5–8 phrases per cell, so 2–3 are `eval_only`. Fedi's 2.0h budget covers about 20 cells × 3 languages.

**Generator lints (hard asserts; the generator exits non-zero):**
1. **Evidence substring:** every rendered GT phrase (address, each flag, tone) satisfies `find_span(text, phrase) is not None` after `normalize()`.
2. **Exact guard:** every `address.exact` phrase, after slot fill, satisfies `passes_exact_guard([phrase])`. Every `street_and_landmark` phrase does **not**, which also catches a stray digit or building token.
3. **Label uniqueness:** after normalization, no phrase appears under two different labels (address levels, flag codes, tones, time).
4. **No label words** anywhere in the banks: `risk`, `refus`, `fake`, `arnaque`, `مرفوض`.
5. **Split rule** as above, per cell.
6. **Leakage:** no `eval_only` phrase occurs in `prompts/*` or `fewshot.jsonl` (Oracle's lint). No hero-fixture line equals a few-shot line.
7. **Tone bank hygiene:** no `tone.uncertain` phrase contains a `flags.availability_uncertain` or `flags.price_hesitation` phrase as a substring, and vice versa.
8. **Base rate:** mean `refused` ∈ [0.25, 0.35].

---

### (2) `S`, `p_true`, label

These are the `PRIOR` constants in `ml/features.py`. They're not in `scoring.yaml`: they define the data-generating process, and changing them means regenerating and retraining. `synth_v1.meta.json` records their hash through the `features.py` sha256.

Every component is in [0, 1]:

```
vag      = 1 − address_specificity                                   # {1, .75, .5, .25, 0}
price_c  = clip((ln price_tnd − ln 20) / (ln 600 − ln 20), 0, 1)     # fixed log scale; 220 TND → 0.7050
zone_c   = {urban: 0, suburban: 0.5, rural: 1}[zone]
rate_c   = customer_refusal_rate                                     # (r + 0.6) / (n + 2)
flags_c  = min(red_flag_count, 3) / 3
tone_c   = {positive: 0, neutral: 0.25, uncertain: 0.75, negative: 1}[tone]

S        = 100 · (0.35·vag + 0.15·price_c + 0.10·zone_c + 0.20·rate_c + 0.10·flags_c + 0.10·tone_c)
p_true   = 1 / (1 + exp(−(S − 43) / 12))
refused  = 1 if u < p_true else 0,   u ~ Uniform(0,1) from stream "rows"     # this IS the noise; no ±10
```

**Checks:**

| Case | S | 100·p_true |
|---|---|---|
| Hero v1 `[0.5, 3, uncertain, 220, rural, 0.30]` *(hand)* | 61.58 | **82.5** |
| Hero v2 `[1.0, 0, neutral, 220, rural, 0.30]` *(hand)* | 29.08 | **23.9** |
| v2 with tone positive *(hand)* | — | 20.3 |
| v2 with 3 stale flags *(hand)* | — | 41.9 |
| Fairness case, rural + exact + clean + new customer, 450 TND *(hand)* | — | 29.0 |
| Same, 25 TND *(hand)* | — | 12.4 |

*(sim, 4 seeds)*: base rate 0.297–0.302; mean S 30.8–31.0, sd 12.9–13.0.

`score_prior(features) = 100·p_true(S(features))` is the model-unavailable fallback (`path=rules`, `confidence=low`).

On stage, call these "simulated outcomes drawn from a documented prior", not "weak labels".

---

### (3) Feature contract

**Model input: the order is fixed and imported from `ml/features.py`.** Monotone constraints `(-1,1,1,1,1,1)`.

| # | Name | Type | Encoding | Train source | Serve source | Serve default if missing | Monotone |
|---|---|---|---|---|---|---|---|
| 0 | `address_specificity` | float | {0,.25,.5,.75,1} | GT `address_level` | LLM `address_level` after the evidence check, the exact guard (§5) and the pin override | 0.0 (`none`; all quotes dropped) | −1 |
| 1 | `red_flag_count` | int 0–6 | count of distinct codes | `len(flags_gt)` | `len(resolve_flags(dedupe_by_code(evidence_checked(flags))))` (§4) | 0, plus `confidence=low` if extraction failed | +1 |
| 2 | `tone_score` | int | pos −1 · neu 0 · unc 1 · neg 2 | GT `tone` | LLM `tone` after `tone_gate()` (§4.2) | 0 | +1 |
| 3 | `price_tnd` | float | raw TND | catalog unit × qty | catalog match (RapidFuzz ≥ 80) × `clamp(quantity, 1, 5)`, where null → 1. The stored `quantity` keeps up to 50. | 69, `imputed:["price_tnd"]`, `confidence=low` | +1 |
| 4 | `zone_encoded` | int | urban 0 · suburban 1 · rural 2 | GT `zone` | (a) CSV `zone` if present; else (b) `zone_from_text(verified address_quotes)`; else (c) `zone_from_text(all [CUSTOMER] text in the window)` | 1, `imputed:["zone"]`, `confidence=low` | +1 |
| 5 | `customer_refusal_rate` | float | `(r+0.6)/(n+2)` | GT history | `customers.refusals_total` and `customers.completed_orders` (delivered + refused, outcomes known before this order's `opened_at`, open order excluded) | 0.30 | +1 |

**`zone_from_text(text)`:**
- Normalize, then look up `zones.yaml`:
  - entries `{name, aliases[], governorate, zone}`, about 30 of them
  - `keywords: {rural: ["douar", "دوار", "ouled", "أولاد"], ...}`
- Latest message wins.
- An alias match beats a keyword match.
- Returns `(zone, source)`, where `source ∈ {csv, gazetteer, keyword, default}`.

**Context fields:** stored in `features_json` and shown in the UI, **not** model inputs:
- `has_geo_pin`
- `product_id`
- `product_category`
- `quantity`
- `customer_completed_orders`
- `customer_refusal_count`
- `zone_source`
- `imputed: [...]`
- `resolved_flags: [...]`
- `tone_reset: bool`
- `address_level_raw` (the LLM's level before the guard)
- `address_level_final`

**Dropped from the old contract:**
- `customer_order_age_days`: no label term and no column.
- `has_geo_pin` as a feature: it duplicates the pin → `exact` override.
- `product_category_encoded`: no label term.

**Invariants:**
- `features_json` keys = `FEATURES` ∪ the context keys (test ML3).
- **No NaN is ever passed to the booster** (test ML9).

---

### (4) `resolve_flags()`, the tone gate, and the serve pipeline order

#### 4.1 Window indexing

The window is the list of lines `[(role, text), …]` in `provider_ts` order: all `[CUSTOMER]` lines plus the latest `[SELLER]` line.
- `msg_idx` is the position in that list.
- `k` is the index of the `[SELLER]` line, or `None` if the window has none. A pre-reply window has none, and neither do training rows.
- The evidence check returns `(msg_idx, start, end)` for each verified quote: the first match, searched from the latest customer line backwards, over customer lines only.

#### 4.2 Tone gate (code)

```
tone_gate(tone, tone_evidence_span, verified_flag_spans):
  if tone == "neutral": return "neutral"
  if tone_evidence_span is None: return "neutral"            # null or failed the evidence check
  if any(s.msg_idx == t.msg_idx and s.start < t.end and t.start < s.end
         for s in verified_flag_spans):                      # overlap with ANY verified flag (pre-resolve)
      return "neutral"
  return tone
```

A reset sets `tone_reset=true` in the context.

#### 4.3 `resolve_flags()`: the exact rule

```python
FLAG_ORDER = ("vague_location", "availability_uncertain", "price_hesitation",
              "third_party_recipient", "prior_refusal_mention", "pressure_or_inconsistency")

def resolve_flags(flags, address_level_final, confirmation, k):
    """flags: deduped verified flags, each with .code and .msg_idx.
    Returns (kept, resolved_codes). Never adds a flag. r(r(x)) == r(x); r(x) ⊆ x."""
    kept, resolved = [], []
    for f in flags:
        drop = (
            (f.code == "vague_location" and address_level_final == "exact")
            or (f.code == "availability_uncertain" and k is not None
                and confirmation in ("confirmed", "reschedule") and f.msg_idx < k)
            or (f.code == "price_hesitation" and k is not None
                and confirmation == "confirmed" and f.msg_idx < k)
        )
        (resolved if drop else kept).append(f)
    return kept, [f.code for f in resolved]
```

- `dedupe_by_code` keeps one flag per code: the one with the largest `(msg_idx, start)`, i.e. the latest evidence.
- The other 3 codes are never touched.
- The resolved codes go to `adjustments_json.resolved_flags`, and to the context copy for the UI.

#### 4.4 Serve pipeline order (per extraction; `score_order()`)

1. **Extract.** LLM (prompt rule 5 plus few-shot) → cascade → rules. That's Oracle's/Strategist's chain; Gemini is the extraction fallback if S-6 ships.
2. **Parse and repair.** Clamp and truncate; never raise (Craftsman U3).
3. **Evidence check** (`ml/textnorm.normalize` + `find_span`, customer lines only):
   - Drop unverifiable flags and count them in `dropped_flags`.
   - Drop unverifiable address quotes; if all of them are dropped, the level becomes `none`.
   - An unverifiable `product_quote` becomes null.
   - An unverifiable `tone_evidence` span becomes `None`.
4. **Tone gate** (§4.2).
5. **Cross-field rules:**
   - `is_order=false` → stop, **unless** the code-owned guard (02 §5 step 9) forced it to `true`: a verified product/address quote, or an injection hit.
   - `confirmation≠none` with `k is None` → `none`.
   - `exact` without `passes_exact_guard(verified address_quotes)` → `street_and_landmark`.
6. **Overrides:** a location pin forces `exact`.
7. **`dedupe_by_code` → `resolve_flags`.**
8. **`build_features`:** vector, context, imputed.
9. **Model:** `pred_contribs` → `model_score`.
10. **Rules and reasons:** reply adjustments → `final` → tier, action, confidence → reasons (§8).

Steps 3–8 are pure functions in `ml/features.py` / `ml/textnorm.py`. The same functions run in the golden test, the eval runner and the API.

---

### (5) Shared Arabizi-digit helper (`ml/textnorm.py`)

In Arabizi, `2 3 5 6 7 8 9` are letters (ء ع خ ط ح غ ق). A digit run only counts as a number when it isn't glued to a **Latin** letter. A Latin digit next to an Arabic-script letter isn't Arabizi, so that adjacency doesn't disqualify it.

```python
LATIN = r"A-Za-zÀ-ɏ"
DIGITS = r"0-9٠-٩۰-۹"
NUM_RE = re.compile(rf"(?<![{LATIN}{DIGITS}])[{DIGITS}]{{1,3}}(?![{LATIN}{DIGITS}])")
BUILDING_TOKENS = ("imm", "immeuble", "apt", "appartement", "etage", "étage", "bloc",
                   "residence", "résidence", "عمارة", "شقة", "طابق")   # whole-token match after normalize()
DAR_N_RE = re.compile(rf"\b(dar|دار)\s*n?°?\s*[{DIGITS}]{{1,3}}(?![{LATIN}{DIGITS}])")

def standalone_numbers(text) -> list[str]            # NUM_RE.findall(normalize(text))
def has_building_token(text) -> bool                 # token in BUILDING_TOKENS or DAR_N_RE match
def passes_exact_guard(quotes: list[str]) -> bool    # any(standalone_numbers(q) or has_building_token(q) for q in quotes)
```

- Runs are **1–3 digits** so that Tunisian 4-digit postcodes (`"Bardo 2000"`) don't make an address `exact`.
- **Callers:**
  - the serve exact guard (§4.4 step 5)
  - generator lint 2
  - generator `{number}` slot fill (always 1–120)
  - tests ML5/U8

**Case table.** Fedi adds Darija cases; Omar owns the test.

| Input | `standalone_numbers` | `passes_exact_guard` |
|---|---|---|
| `dar 14` | `["14"]` | true |
| `3ayetli 9bal` | `[]` | false |
| `9rib el jemaa` | `[]` | false |
| `ghodwa ba3d 17h` | `[]` (17 glued to `h`) | false |
| `imm 7 étage 2` | `["7","2"]` | true |
| `2eme etage` | `[]` | true (`etage`) |
| `el 7ouma` | `[]` | false |
| `٣٤ شارع الحرية` | `["٣٤"]` | true |
| `عمارة النور` | `[]` | true (`عمارة`) |
| `Bardo 2000` | `[]` (4 digits) | false |
| `dar14` | `[]` | false (known gap: the generator never renders it; serve downgrades to `street_and_landmark`) |
| `22 123 456` (phone) | `["22","123","456"]` | true (known gap: phones are masked before the LLM (U12); not handled further) |

---

### (6) XGBoost config and training outputs

```python
XGBClassifier(objective="binary:logistic", n_estimators=400, learning_rate=0.05, max_depth=2,
              min_child_weight=10, subsample=0.8, colsample_bytree=1.0, reg_lambda=1.0,
              tree_method="hist", monotone_constraints="(-1,1,1,1,1,1)",
              random_state=42, n_jobs=1, eval_metric="logloss")
# pin: xgboost==3.2.0, numpy 2.x, scikit-learn 1.9.x (card records exact versions)
```

- No tuning and no early stopping. Depth 2, because the label is additive in log-odds. Say this openly.
- `X = df.loc[df.split=="train", FEATURES]`, `y = refused`. `S` and `p_true` are **never** columns of `X` (test ML3).

**Serve call:** `c = booster.predict(DMatrix(x, feature_names=list(FEATURES)), pred_contribs=True)[0]` gives 7 values.
- `margin = c.sum()`
- `p = 1/(1+e^−margin)`
- `model_score = round(100·p, 1)`
- `classifier_version = "xgb_v1-" + sha256(model.json)[:8]`

**Outputs of `python -m ml.train`:**

| File | Contents |
|---|---|
| `models/risk_xgb_v1.json` | `booster.save_model` |
| `models/risk_xgb_v1.card.json` | `{classifier_version, params, FEATURES, monotone, data_sha256, synth_meta, xgboost/numpy/sklearn versions, git_sha, trained_at, metrics_ref}`, plus the 10-bin reliability table, plus the "no time split; model class matches the prior" note |
| `reports/train_metrics.json` | `{n_train, n_holdout, base_rate_train, base_rate_holdout, auc, oracle_auc, brier, oracle_brier, calib_mae_pts, calib_max_pts, tier_share{low,medium,high}, tier_refusal_rate{low,medium,high}, gates{name: pass/fail}}` |
| `tests/golden/hero.json` | Runs the frozen hero fixtures (§10) through `score_order` offline. `{v1:{features, model_score, final, tier, confidence, reason}, v2a:{…}, v2b:{…}, diff_reason}` |
| `reports/impact.json` | §9 |

**Gates.** `train.py` exits non-zero on failure:

| Gate | Threshold | *(sim, 4 seeds)* |
|---|---|---|
| AUC | ≥ 0.70 and ≥ `oracle_auc − 0.03` | 0.764–0.774 vs oracle 0.763–0.777 |
| Calibration MAE | `MAE(100·p̂, 100·p_true)` ≤ 5 pts | 2.3–2.8 (max single-row 15.6–24.3) |
| Tier refusal rate | strictly increasing low < medium < high | 0.18 / 0.49–0.50 / 0.67–0.75 |

- Tier shares *(sim)*: 65–69% / 22–26% / 9%.
- No calibration layer unless the MAE gate fails.

---

### (7) `scoring.yaml`, in full

```yaml
version: 1
model:
  file: models/risk_xgb_v1.json
  features: [address_specificity, red_flag_count, tone_score, price_tnd, zone_encoded, customer_refusal_rate]
  # model_score = 100 · P(refused), from simulated outcomes (see card). Not a real-world refusal rate.

tiers:            { low_max: 35, medium_max: 65 }          # low < 35 <= medium < 65 <= high; fixed, not percentiles
confidence:       { boundary_margin: 10, max_dropped_flags: 1 }
actions:          { prepay_min_tnd: 250 }
auto_send:        { max_tnd: 150, max_auto_messages_per_order: 2 }

reply_adjustments:                                           # cold-start priors, not evidence; say so on stage
  confirmed:        { multiply: 0.6 }
  no_reply_timeout: { add: 15, route: needs_review }
final_score:      { clip: [0, 100], round: 0 }               # final = round(clip(model_score*mult + add, 0, 100))

outbound:
  static_insert_when_tier_at_least: medium                   # chosen template's static text is stored as an outbound line (template_id kept)
  template_rule: [ {if_flag: vague_location, template: T_ADDRESS},
                   {if_action: prepay, template: T_PREPAY},
                   {else: T_CONFIRM} ]

serve_defaults:                                              # used only when the source is missing; each adds to imputed[] and sets confidence=low (except refusal rate)
  address_specificity: 0.0
  red_flag_count: 0
  tone_score: 0
  price_tnd: 69
  zone_encoded: 1
  customer_refusal_rate: 0.30

catalog_match:    { min_score: 80, quantity_clamp: [1, 5] }

reasons:
  max_drivers: 3
  min_pts: 3
  always_show_zone_if_abs_pts_at_least: 3
  quote_max_chars: 40
  diff_min_delta_pts: 3
  linearise_if_abs_sum_phi_below: 0.05

timeouts:         { debounce_s: { demo: 4, prod: 15 }, no_reply_s: { demo: 60, prod: 21600 } }

lexicons:
  ack:     [ok, oui, ey, eyh, behi, "d'accord", merci, "ya3tik saha", "نعم", "باهي", "إيه"]
  decline: [non, la, annuler, "ma nhebech", "لا", "ألغي"]

roi:                                                         # every value is an ASSUMPTION; impact is simulated
  c_fail_tnd: 8.0                                            # [VERIFY] courier + return cost of one failed COD trip
  prevent_rate: { ship: 0.0, confirm: 0.30, prepay: 0.60 }   # share of would-be refusals the action avoids
  prepay_conversion_loss: 0.10                               # share of good orders lost when asked to prepay
  gross_margin: 0.25
  msg_cost_tnd: 0.0                                          # [VERIFY] WhatsApp service-window pricing
  sensitivity_confirm: [0.15, 0.30, 0.45]
```

**Confidence** stays as in §7.3. It's `high` only if all of these hold:
- valid extraction from the primary model
- `clarity` is `clear`, or `partial` with nothing else failing
- `dropped_flags ≤ 1`
- the product matched
- `imputed` is empty (except `customer_refusal_rate` for a new customer)
- no Prompt Guard hit
- `|final − nearest boundary| ≥ 10`

`clarity=unclear` means `low`.

Cascade, Gemini-fallback and rules paths always give `low`.

---

### (8) SHAP → reason string

**Points.** Exact and additive; the points sum to `model_score − 100·p0`:

```
φ_i = c[i] (log-odds), b = c[bias];  p0 = σ(b);  p = σ(b + Σφ)
pts_i = 100·(p − p0)·φ_i / Σφ         if |Σφ| ≥ 0.05
pts_i = 100·p0·(1 − p0)·φ_i           otherwise
```

**Selection:**
- medium/high: up to 3 drivers with `pts ≥ 3`, sorted descending
- low: up to 2 with `pts ≤ −3`, sorted ascending
- then zone is appended if `|pts_zone| ≥ 3` and it isn't already listed (§12 transparency)
- then adjustments

**Flag evidence** for the flags template is the evidence of the first kept flag in `FLAG_ORDER`, so the hero quotes `"9rib el jemaa"`.

**Templates** (`reasons.yaml`; quotes come from verified evidence, max 40 characters):

| Feature | pts > 0 | pts < 0 |
|---|---|---|
| `address_specificity` | `vague address ("{address_quote}")` | `full address given ("{address_quote}")` |
| `red_flag_count` | `{n} warning sign(s): "{flag_evidence}"` | `no warning signs` |
| `tone_score` | `hesitant tone ("{tone_evidence}")` | `confident tone` |
| `price_tnd` | `high order value ({price} TND)` | `low order value ({price} TND)` |
| `zone_encoded` | `{zone} delivery zone` | `{zone} delivery zone` |
| `customer_refusal_rate` | `{r} of {n} past orders refused` | `good order history ({n} delivered)` |

**Diff templates** (v_k vs v_{k−1}, features with |Δpts| ≥ 3, sorted by |Δ|, then adjustments):

| Feature | Diff wording |
|---|---|
| address | `full address given ("{quote}")` or `address less precise ("{quote}")` |
| flags | `warning signs resolved ({codes})` when Δ < 0; `new warning sign: "{evidence}"` when Δ > 0 |
| tone | `tone {old} → {new}` |
| price | `order value changed ({old} → {new} TND)` |
| zone | `delivery zone changed` |
| history | `order history updated` |
| adjustments | `customer confirmed ×0.6 (cold-start rule) −{x}` |

**Examples.** These use *(sim, seed 20260927)* points. The committed numbers come from `hero.json`.

- v1 (model 87.9; base 30.0; pts zone +14.5, flags +14.0, address +11.0, price +10.5, tone +6.2, rate +1.6):
  `HIGH 88 · base 30 · rural delivery zone +15 · 3 warning signs: "9rib el jemaa" +14 · vague address ("Douar Ouled Ali") +11`
- v2 (model 26.4; pts address −21.9, flags −4.9, tone −1.6, price +10.1, zone +13.4, rate +1.2; final round(0.6·26.4)=16):
  `LOW 16 · base 30 · full address given ("Douar Ouled Ali, triq el jemaa, dar 14") −22 · no warning signs −5 · rural delivery zone +13 · customer confirmed ×0.6 (cold-start rule) −11`
- Diff:
  `v1 88 → v2 16 · full address given ("…dar 14") −33 · warning signs resolved (availability_uncertain, price_hesitation, vague_location) −19 · tone uncertain → neutral −8 · customer confirmed ×0.6 (cold-start rule) −11`

**What the example shows:**
- The displayed items sum to −71 against an actual −72, because items under 3 pts are omitted. The UI says "items under 3 pts not shown".
- *(sim, 4 seeds)*: the v1 top 3 are always drawn from {address +11–14, flags +13–19, zone +10–15}, with price +5–10.5 just behind. Zone is sometimes the top driver for the rural hero. That's honest. The story is the Δ, and address dominates the Δ. Fedi should know this before writing the script line.

---

### (9) Simulated ROI (`reports/impact.json`; `GET /metrics/impact` returns it with `"simulated": true`)

Inputs are `scoring.yaml › roi`, all assumptions. `H` is the 2,000-row holdout, `action_i` comes from the model tier plus `prepay_min_tnd`, and `refused_i` is the simulated outcome.

```
avoided   = Σ_H refused_i · prevent_rate[action_i]
lost_tnd  = Σ_H (1 − refused_i) · [action_i = prepay] · prepay_conversion_loss · gross_margin · price_i
msg_tnd   = Σ_H [action_i ∈ {confirm, prepay}] · msg_cost_tnd
saved_tnd = avoided · c_fail_tnd − lost_tnd − msg_tnd
report: saved_tnd per 1,000 orders; refusal rate before = Σrefused/|H|, after = (Σrefused − avoided)/|H|;
        recall of refusals flagged (tier ≠ low); share of orders flagged; saved_tnd at each sensitivity_confirm value
```

*(sim, 4 seeds)*:
- 383–473 TND saved per 1,000 orders
- refusal rate 29–32% → 24–25%
- 57–62% of refusals flagged, with 31–35% of orders flagged

Quote only the committed run, always with "simulated, on synthetic orders, with the assumptions shown". Lost conversions and the need for a control group go in Q&A. Per Strategist, the pitch uses no real-world refusal figure unless it's sourced.

---

### (10) Hero scenario: fixtures and golden assertions

**Setup:**
- new customer `Sami`, `completed_orders=0` → rate 0.30
- product P12 `casque bluetooth`, 220 TND
- `DEMO_MODE=true`

**Wording.** Fedi may reword any line if lints 6/7 and the constraints in brackets still hold. The words in bold are load-bearing.

| idx | role | text |
|---|---|---|
| 0 | CUSTOMER | `salam, nheb el casque bluetooth` |
| 1 | CUSTOMER | `**Douar Ouled Ali**, **9rib el jemaa**` [the `douar` keyword → rural; the vagueness marker] |
| 2 | CUSTOMER | `ama **ghali chwaya**. **mouch dima fi dar**, 3ayetli 9bal. **mazelt manich met2aked**` [price_hesitation; availability_uncertain; tone.uncertain evidence, which must not overlap a flag span] |
| 3 | SELLER | Static `T_ADDRESS` (arabizi, Fedi's copy), stored with `template_id=T_ADDRESS`. It must end in a yes/no question. Placeholder: `Aslema Sami, bech nba3thoulek el casque bluetooth. Ta3tina l'adresse bedhabt (triq, noumrou dar)? W tconfirmi el commande, ey walla le?` (no digits, so it passes the prefilter) |
| 4 | CUSTOMER | `**ey** behi. **Douar Ouled Ali, triq el jemaa, dar 14**, el bab lazra9 **9odem el pharmacie**. ghodwa ba3d 17h nkoun fi dar` [`dar 14` passes the exact guard; `17h` doesn't count; zone stays rural] |

**Frozen extraction fixtures** (`tests/fixtures/hero/*.json`, 12 fields):
- **v1** (window 0–2, `k=None`):
  - `is_order` true, `is_order_change` false, `product_quote` "casque bluetooth", `quantity` 1
  - `address_quotes` ["Douar Ouled Ali", "9rib el jemaa"], `address_level` area_or_landmark
  - `red_flags` [vague_location "9rib el jemaa", availability_uncertain "mouch dima fi dar", price_hesitation "ghali chwaya"]
  - `tone_evidence` "mazelt manich met2aked", `tone` uncertain
  - `confirmation` none, `language` arabizi, `clarity` clear
- **v2a**, clean (window 0–4, `k=3`):
  - `address_quotes` ["Douar Ouled Ali, triq el jemaa, dar 14", "9odem el pharmacie"], `address_level` exact
  - `red_flags` []
  - `tone_evidence` null, `tone` neutral
  - `confirmation` confirmed
  - other fields as in v1
- **v2b**, stale: v2a, but `red_flags` re-emits all three v1 flags with their v1 evidence (msg_idx 1, 2, 2).

**Golden assertions** (`tests/test_hero.py` / Craftsman E1; offline; `LLMClient` replay):

| Step | Assertions |
|---|---|
| v1 | `features == [0.5, 3, 1, 220.0, 2, 0.30]`; `zone_source == "keyword"`; `imputed == []`; **`75 ≤ model_score ≤ 92`**; `final == round(model_score)`; tier `high`; **`abs(final − 65) ≥ 10`**; confidence `high`; action `confirm` (220 < 250); template `T_ADDRESS`; route `needs_review` (220 > 150); reason contains `9rib el jemaa`. *(hand truth 82.5; sim model 82.1–88.4)* |
| v2a and v2b | **identical `features == [1.0, 0, 0, 220.0, 2, 0.30]`**; `address_level_final == "exact"`; **`15 ≤ model_score ≤ 32`**; `final == round(0.6·model_score)`; **`final ≤ 25`** (so `abs(final − 35) ≥ 10`); tier `low`; confidence `high`; status `ready_to_ship`; `v1.model_score − v2.model_score ≥ 40`. v2b: `resolved_flags == ["vague_location","availability_uncertain","price_hesitation"]`. v2a: `resolved_flags == []`. The diff reason contains `dar 14` and `×0.6`. *(hand truth 23.9; sim model 19.5–26.4, final 12–16, Δmodel 57.9–66.6)* |
| `resolve_flags` | `r(r(x)) == r(x)`; `r(x) ⊆ x`; with `k=None` only the vague rule fires; a flag quoted at `msg_idx 4 > k` survives. |

**Robustness variants.** Assert tier only; confidence may be low.

| Variant | Tier | *(sim)* |
|---|---|---|
| R1: v2a with `confirmation=none` | `low` from the model alone | 19.5–26.4 |
| R2: v2b with `resolve_flags` bypassed (3 stale flags) | `final` tier `low` | model 40.5–47.7 → ×0.6 = 24.3–28.6 |
| R3: v1 with `tone_evidence` null (the gate resets it to neutral) | `high` | 73.1–84.5 |
| R4: v1 with the LLM saying `street_and_landmark` | `medium` or `high` | 66.2–76.9; too close to 65 to assert `high` |

**Pinning:**
- `train.py` writes `tests/golden/hero.json` with the exact numbers.
- E1 asserts both the ranges above (the spec) and equality with `hero.json` (the pin; re-pinned only by `train.py`).
- Slides, video and UI copy read `hero.json`.

---

### (11) ML test list

All tests are offline, deterministic and keyless. **Owner: Omar** (code owner), unless stated otherwise. IDs extend Craftsman's.

| ID | Test | Asserts | Tier |
|---|---|---|---|
| E1 | `test_hero_loop_golden` | §10 table (Craftsman's E1, with these ranges) | **16-set**, by G6 18:00 |
| U8 | `test_cross_field_rules` | + the exact guard uses `passes_exact_guard` | 34 |
| U15 | `test_feature_mapping` | level→spec, tone encoding, catalog price, qty clamp 1–5, unmatched → 69 + imputed | 34 |
| U18 | `test_reason_deterministic` | same input → same string; drivers/zone/adjustment rules from §8; points sum to `model_score − 100·p0` ±0.5 | 34 |
| U20 | `test_classifier_monotone` (extends Craftsman's) | on a grid, raising `address_specificity` never raises the score; raising any other feature never lowers it | 34 |
| U21 | `test_holdout_tier_refusal_rate` | **replaces** "mean weak label": holdout refusal rate strictly increasing across tiers | 34 |
| U22 | `test_model_artifact_matches_card` | sha256 and `FEATURES` order equal the card | 34 |
| ML1 | `test_generator_deterministic` | same seed → same sha256; a bank edit changes only `text`, `messages_json`, `gt_evidence_json` | 34 (P0) |
| ML2 | `test_generator_lints` | lints 1–8 pass on the committed banks, and each lint fails on a crafted bad bank | 34 (P0) |
| ML3 | `test_feature_contract_parity` | `FEATURES` equal in CSV, trainer `X` (no `S`/`p_true`), card, `features_json`; key set = FEATURES ∪ context | 34 (P0) |
| ML4 | `test_model_gates` | AUC, calibration MAE and tier-rate gates from `train_metrics.json` | 34 |
| ML5 | `test_standalone_numbers` (param.) | the §5 case table (Fedi supplies extra Darija cases) | 34 (P0) |
| ML6 | `test_resolve_flags` (param.) | §4.3 rule table, idempotence, subset, `k=None`, after-`k` survival | 34 (P0) |
| ML7 | `test_tone_gate` | null evidence → neutral; failed evidence → neutral; overlap with a flag span → neutral; clean → kept | 34 |
| ML8 | `test_fairness_invariant` | rural, exact, 0 flags, neutral, new customer, each catalog unit price ≤ 450 → tier `low` *(sim max 27.0–30.8; prior 29.0)* | 34 |
| ML9 | `test_imputation_never_nan` | a missing zone/product/history still scores; `imputed` listed; confidence low; no NaN reaches `DMatrix` | 34 |
| ML10 | `test_generator_no_llm_imports` | an AST scan of `ml/generate.py` and `ml/train.py` finds none of `app.llm`, `groq`, `google.genai`, `openai`, `httpx` | 34 (P0) |
| ML11 | `test_zone_from_text` | alias beats keyword; latest message wins; fallback to the window text; default suburban + imputed | 34 |
| ML12 | `test_demo_orders_fresh` | `demo_orders.json` `classifier_version` and `config_hash` equal the current ones | 34 |
| ML13 | `test_hero_robustness` | R1–R4 | 34 |
| ML14 | `test_text_clf_artifact` | retraining on the same `synth_v1.csv` gives identical holdout predictions; artifact sha256 and class lists equal the card; ML10's no-LLM-import scan also covers `ml/text_clf.py`; `reports/text_clf_eval.json` has holdout and G1 fields with N | F(S-11a) |
| ML15 | `test_text_clf_serving` (param.) | `text_clf.enabled` on vs off: `llm`-path features, `model_score`, tier and action identical; a ≥ 2-level disagreement adds `text_clf_disagrees` and nothing else; rules path: `exact` never without `passes_exact_guard`, tone stays neutral, no address token → rules level kept; hero v1/v2 fixtures predicted at the gold level (else the check ships off, §14) | F(S-11b) |

- Fedi supplies case data for ML5 and ML11 and the hero text.
- Montassar's CI runs everything in `make check`.
- If Omar slips, the cut order is: ML13 R4 → ML8 moves into the card only → ML11 → ML7.

**Never cut:** E1, ML6, ML3, ML10.

---

### (12) Open item resolved: the eval headline

There are two evals with different jobs. Both use the real `score_order` in eval mode, which means the primary model only, with no cascade, cache or fallback.

| | **A. Hand-written windows (headline)** | **B. Synthetic skew (secondary)** |
|---|---|---|
| Rows | Fedi's 24 windows (Strategist's Must), including reply windows; a second labeler on 6 | 40 `eval_subset` rows, text only from `eval_only` phrases |
| Labels | Human, per window: the 12 fields + `product_id` + `zone`; customer = new (0.30) | Generator ground truth |
| Headline number | **Tier agreement N/24** (human-label features vs LLM features, same context, `final` tier incl. ×0.6), plus `address_level` exact match N/24 | Tier agreement N/40 |
| Also reported | Per-field accuracy, flag precision/recall, stale-flag rate on reply windows (M12), inter-labeler agreement on 6 | 3×3 tier confusion; mean, signed-mean and max \|Δ model_score\|; per-feature attribution (swap one feature GT→LLM) |
| Scope wording | "24 hand-written windows, not phrase-bank text" | "synthetic holdout, unseen phrases, pre-reply only" |
| Cost | Fedi +10 min (2 extra label fields); ~24 calls | 0 human time; ~40 calls on the dev key; Omar +10 min (same runner) |
| Output | `reports/extraction_eval.json` | `reports/skew_eval.json` |

**Why A is the headline:** its text isn't generated from the banks the prompt examples came from, and tier is what the seller acts on.

**Rules for both evals:**
- Report whatever number comes out.
- If B's tier agreement is below 30/40, the stretch fix is noisy-channel augmentation: retrain on GT features passed through the measured confusion matrix. Only if there's time; it's a Sunday item.
- If Gemini (S-6) ships, run B once on Gemini as an extra column. Gemini is an extraction fallback, so its outputs always carry `confidence=low` at serve time.

---

### (13) Omar's ML hours (inside Strategist's generator 1.5h + XGBoost/`scoring.yaml`/hero 1.5h)

| Task | Time |
|---|---|
| `ml/textnorm.py` (normalize, spans, NUM helper) + `ml/features.py` (FEATURES, prior, zone, `resolve_flags`, tone gate, `build_features`) | 40 min |
| `generate.py` (streams, render, `eval_only` pools) + lints 1–8 | 50 min |
| `train.py` + card + metrics + gates | 25 min |
| points + reasons + `scoring.yaml` loader glue | 35 min |
| hero fixtures + E1 + ML6 | 30 min |
| **Subtotal** | **3.0h** |
| Deferred to Sunday slots: ROI in `train.py` (15 min), `eval_skew.py` B-run (10 min, runs inside the 19:00 eval block), ML7–ML13 | — |

**Dependencies:**
- **Fedi's banks by 14:00.** The generator can run earlier on a 1-phrase-per-cell stub, since the text doesn't affect the model.
- **Jesser:** `customers.completed_orders`, and the `adjustments_json.resolved_flags` / `features_json` context keys in the frozen `ScoreResult` by 12:00.
- **Oracle's prompt:** rule 5, FS7/FS8 edits with `tone_evidence`, and the 12-field schema frozen at G3b 16:30.
- **Advocate/Montassar:** evidence spans for highlighting come from the step-3 `(msg_idx, start, end)` output, mapped back to the original text (U7). That's the server-provided `segments`.

**Not computed:**
- real LLM tier agreement (A or B)
- the committed-seed exact hero numbers
- real calibration on the committed generator

The first comes from the 19:00 eval. The other two come from `train.py` on the committed seed.

---

### (14) Text baseline classifier: S-11 (added after the council, 26 Sept)

A small classifier that reads the customer's text and returns a label with a probability. It doesn't generate text and it can't quote. It never sets the score. It has two jobs, split into two stages.

**Model.** `ml/text_clf.py`, scikit-learn only (already in `requirements.txt`).
- Input: the customer lines of the window (no `[SELLER]` line), passed through `ml/textnorm.normalize()`.
- `TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)`. Character n-grams catch Arabizi spelling variants (`9rib` / `qrib` / `krib`) that a keyword list misses.
- One `LogisticRegression(max_iter=2000)` per head, default `C`, no tuning:
  - `address_level`: 5 classes (none · city_only · area_or_landmark · street_and_landmark · exact).
  - `tone`: 4 classes (positive · neutral · uncertain · negative). Reported only, never served (see S-11b).
- Trained on the 8,000 train rows of `data/synth_v1.csv` with the generator's ground-truth labels. Zero LLM calls. Trains in seconds on a laptop CPU.
- `python -m ml.text_clf train` → `models/text_clf_v1.joblib` + `models/text_clf_v1.card.json` (sha256, sklearn version, `data_sha256`, class lists, holdout metrics). `python -m ml.text_clf eval` → `reports/text_clf_eval.json`.

**S-11a: baseline number (0.5 h, Sat 21:00 slot, ahead of S-7).** Report on the same sets as the LLM:
- Synthetic holdout (2,000 rows, `eval_only` phrases): `address_level` accuracy, `tone` accuracy, macro F1.
- G1 native windows (Fedi's hand-written set, first-order windows only): `address_level` exact X/N and ±1 level, as a "char n-gram baseline (no LLM)" row in the 02 §9.5 table, next to the LLM.

This answers the obvious judge question: does the LLM beat a cheap classifier on real dialect text? Report whatever comes out. If the baseline matches the LLM on G1, say so. That is a finding, not a failure.

**S-11b: serving (0.5 h, Sunday, only if S-6 finishes early; flag `text_clf.enabled`, default `false`).**
1. **Disagreement check on the LLM path.** When `path` is `llm` or `cascade_cache`, the classifier's top `address_level` has probability ≥ `min_prob`, and it sits ≥ `disagree_levels` levels away from the LLM's post-check level: add `text_clf_disagrees` to `confidence_reasons` (→ `confidence=low`) and emit a `text_clf.disagree` event. It never changes a feature, the score, the tier or the action.
2. **Fallback on the rules path.** In `rules_v1`, `address_level` takes the classifier's level when its probability ≥ `min_prob` **and** the rules extractor found at least one address, landmark or zone token. Otherwise the rules level stands. `exact` still needs `passes_exact_guard` (else `street_and_landmark`). Flags, quotes, confirmation and evidence stay with the rules. **Tone stays neutral**, because the tone gate (§4.2) needs a verified span and the classifier gives none. `path` stays `rules`, confidence stays low, and `extraction_runs` records `extractor = "rules_v1+text_clf_v1"`.

```yaml
# scoring.yaml (addition)
text_clf: { enabled: false, file: models/text_clf_v1.joblib, min_prob: 0.6, disagree_levels: 2 }
```

**Hero guard.** E1 asserts confidence `high` on v1 and v2. ML15 runs the hero fixtures through the classifier. If it disagrees with the gold level on either, the disagreement check ships off (`disagree_levels: 99`) and the README says why.

**Limits (README "What this does not prove").** It learns the generator's templates, like the XGBoost model, so the holdout number is optimistic; only the G1 number counts. It can't quote evidence, so it never feeds the highlights or the reason string.

**Tests:** ML14 (S-11a), ML15 (S-11b), in §11.
