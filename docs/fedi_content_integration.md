# Fedi content integration (F1–F8 → generation, training, eval, guard)

All seven FEDI PDFs are parsed and their content is live in the system. `make check` is green
(lint + 333 tests + offline eval gate); the locked hero holds: **v1 87 HIGH → v2 16 LOW** through
regeneration, retraining and golden rebuild. Synthetic data only; no invented metrics.

## What went where

| Fedi artifact | System target | Notes |
|---|---|---|
| F2 phrase bank (14 cells × 3 langs) | `data/phrase_banks.yaml` v2 | verbatim; deviations below |
| F3 eval conversations (24) | `eval/sets/g1.jsonl` | labels = Fedi's, schema per golden rows |
| F4 outbound templates | `data/templates/outbound.yaml` v2 | fr/arabizi verbatim; darija reconstructed from the PDF's RTL de-scramble |
| F5 product aliases + place vocabulary | `data/catalog.yaml` (P12), `data/zones.yaml` | additive keywords; ambiguous aliases rejected |
| F6 locked hero story | `tests/fixtures/hero/script.json` | verified, no changes needed |
| F7 injection tests (4 bases × 2) | `scoring.yaml` lexicons + `eval/sets/g3_injection.jsonl` | 9/9 variants caught deterministically |
| F8 outbound draft tests (6 BLOCK + 6 PASS) | `tests/fixtures/cases/prefilter.yaml` | all 12 behave as labeled (2 PASS drafts correctly hold → human review) |

Pipeline after integration: `make generate` (base rate 0.299) → `make train` (hero preserved) →
`make golden` (476 cases) → `make warm` → `make eval` → gate green.

## Eval results on Fedi's sets (offline, rules path)

- **g1 (F3)**: is_order 1.0, address within1 1.0, flag precision 1.0 / recall 0.875,
  tone 0.833, confirmation 0.958. (language_acc 0.5 is gated live only — the rules language
  detector splits Fedi's verbatim mixed rows differently; the LLM path owns that floor.)
- **g3 (F7)**: flagged 1.0, still scored 1.0, **not promoted to exact 1.0** — the F7 protocol
  invariant holds. labels_preserved is gated live (LLM) only; rules flags don't reproduce
  Fedi's exact flag sets by design.
- **F8**: unsafe_blocked 1.0 (all six: invented discount, payment credentials, delivery promise,
  wrong price, second question, policy override), safe_passed 1.0 with safe_held 2 — P02/P04
  score in the hold band and route to human review, which is the designed path for a PASS draft.

## Decisions and deviations (all documented in the touched file headers)

1. **lint3**: Fedi's `{place}`-bearing phrases moved from §03 street cells to `city_only` (a
   `{place}` phrase cannot also live under city per the full-phrase key rule).
2. **lint4**: Fedi's §10 "refus*" phrases excluded from the bank (banned substring); the darija
   refusal "مرة أخرى رفضت الطلبية" is kept.
3. **lint6**: eval_only fragments colliding with `prompts/` (FS2/FS4/FS8, system.txt) reassigned
   train-side; non-colliding starter phrases cover the eval side.
4. **"البالصة"** in F7-02 kept verbatim — verified against the page image that it is Fedi's own
   spelling, not a pdftotext artifact. Test inputs are quoted as written.
5. **g1 labels**: #24 address = none (Fedi's PENDING resolved); #12 flags = price_hesitation only
   (availability had no text evidence); the three non-orders carry no flag labels; canonical F4
   seller lines (rendered with price 220) sit in conversations 5, 6, 17, 24.
6. **F5 aliases NOT added** despite being plausible: "écouteurs bluetooth", "إيربودز",
   "kit mains libres", "كيت مان ليرب", plain "سماعات" (owned by P11) — Fedi's own caution.
7. **Extractor (rules path) refined to Fedi's semantics**:
   - exact address now requires a **number** plus street/building marker ("dar 57", "Maison
     numéro 12, rue X"); a bare building word ("à la maison") no longer promotes — this is what
     keeps the F7 "not promoted" invariant at 1.0.
   - `is_order`: a flag alone or an availability question is a browse; order evidence is a
     declarative product mention, an address quote, or a darija intent verb (new
     `lexicons.order_intent` in `scoring.yaml`), matching F3's #14/#18/#20 vs #02/#08.
   - Golden extraction is_order 0.961 (floor 0.95): the synth generator labels F2's
     question-form intros ("3andkom {product}?") as orders by template membership; F3 refines
     that a question + commitment is an order, a question alone is not. Documented in
     `eval/thresholds.yaml`.
8. **Guard classifier re-based on the v2 templates**: `data/draft_guard.yaml` slots gained
   "casque bluetooth"/"250" and the fr safe list grew address-ask/paiement-à-la-livraison/
   code-postal sentences mirroring F4 vocabulary (the v2 templates themselves scored 0.25–0.37
   on the old manifold); corpus balance retuned (n_base 1100, train reps 12, holdout reps 4).
9. **Eval routing now mirrors make_draft**: blocked = prefilter fail or classifier ≥ block_at
   (0.5); the hold band (0.2–0.5) is the human-review path — it stops an unsafe draft and passes
   a safe draft to review (tracked as `safe_held`). Previously the eval conflated hold with block.
10. **Monitor reference rebuilt** (`data/monitor_reference.json`) from the new golden mix — the
    distributions moved with the extractor change (e.g. tier.none appears for non-orders).
11. **Judge-flow test fixtures** (`test_outbound_judge.py`) reworded from the v1 template wording
    to v2-consistent rewrites; the lint3 bad-bank mutation now duplicates an existing Fedi phrase.

## PENDING native pass (documented in `phrase_banks.yaml`)

`address.none` and `tone.negative` remain starter stubs — Fedi's F2 does not cover them; they
need a native-speaker pass before they should be trusted for generation.
