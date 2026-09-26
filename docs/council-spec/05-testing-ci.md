# Testing, seams, fixtures, CI, Makefile, definition of done

> Council final spec — Craftsman lens (Round 3). Source of truth for its area. Where this file conflicts with a **Conductor ruling** in [README.md](README.md#conductor-rulings), the ruling wins. Unverified external facts are marked [VERIFY].


Rubric shorthand: **PV** Problem+Value 20 · **FX** Functional 20 · **AI** Quality of AI 20 · **TR** Testing 15 · **XP** Experience 15 · **RAI** Responsible AI 10. Every test counts toward TR; the "Evidences" column names the red-team row (§14 number) or the extra rubric criterion.

Risks from Round 2 that aren't in §14, numbered N1–N5:
- **N1:** the public URL sends real WhatsApp messages or ingests real PII.
- **N2:** judge A finishes the hero loop for judge B (shared state).
- **N3:** visitors burn the LLM quota.
- **N4:** eval leakage, or a prompt tuned on the eval set.
- **N5:** stale flags survive a reply and keep the score high, which breaks the hero.

## 1. Test inventory

Tiers:
- **T0**: on `main` by Sat 14:00.
- **T1**: on `main` by G7 Sat 22:00. The ★ rows are the **16-test minimum** and the G7 gate.
- **T1+**: merges in the same PR as its Must code. It may slip to T2 only as a visible `pytest.mark.skip(reason="T2 debt: <ID> <owner>")`, which CI counts.
- **T2**: Sunday 11:15–15:30, in the order listed, until at least 34 are green.
- **F(x)**: ships only if Should feature *x* ships.
- **L**: live, key needed, never in CI, output committed to `reports/`.

LLM column: **No** = pure or mocked · **Rec** = `ReplayClient` over recorded fixtures · **Hand** = hand-crafted fixture · **Fail** = `FailingClient` · **Live** = real key.

| ID | Test | Module | Asserts | LLM? | Owner | Tier | Evidences |
|---|---|---|---|---|---|---|---|
| **U1 ★** | `test_extraction_schema_matches_pydantic` | extraction/schemas | `schemas/order_extraction_v1.json` and `OrderExtraction` list the same **12 fields in the same order**: `is_order, is_order_change, product_quote, quantity, address_quotes, address_level, red_flags, tone_evidence, tone, confirmation, language, clarity`. `has_landmark` and `has_building_or_apt` are absent. Every property is in `required`, every object has `additionalProperties:false`, and the enum sets are equal. The same checks run for the rewrite and judge schemas once those files exist. | No | Omar | T0 | #2, #25 · AI |
| **U16 ★** | `test_tier_action_confidence` (param) | scoring/rules | Scores 34/35/64/65 give the right tier on each side of the boundary. Price 249/250 flips prepay. Margin < 10 gives confidence low. An invalid extraction gives `review`. `clarity=unclear` gives confidence low (drop this case if `clarity` is cut). | No | Omar | T0 | #12 · AI |
| U23 | `test_eval_windows_valid` | data | Every row of `data/eval/windows.jsonl` validates against the 12-field enums. Each language has at least 5 rows. IDs are unique. Every ID in `second_label.jsonl` is also in `windows.jsonl`. | No | Omar (data: Fedi) | T0 | #4 · AI |
| **C2 ★** | `test_stub_scorer_satisfies_contract` | scoring/stub ↔ db/repo | The stub's `ScoreResult` for `initial` and `customer_reply` inserts into a fresh `schema.sql` DB with no CHECK, NOT NULL or FK error, and `version` goes 1 → 2. | No | Jesser | T0 | #25 · FX |
| **U3 ★** | `test_repair_clamps_and_truncates` | extraction/schemas (`repair`) | qty 60 → 50 and 0 → 1. 7 flags → 6. 5 quotes → 4. 200-char evidence → 160. An unknown flag code is dropped. **No `ValidationError` is raised.** Each repair is listed in `repairs[]`. | Hand | Omar | T1 | #3 · AI |
| **U5 ★** | `test_evidence_drops_unverifiable` | extraction/evidence | An invented flag is dropped and counted in `dropped_flags`. A quote found only in the `[SELLER]` line is dropped (#13). If every address quote is dropped, `address_level` becomes `none`. A bad `product_quote` becomes null. Two or more drops give confidence low. Surviving flags carry `msg_idx`. | Hand | Omar | T1 | #3, #13 · RAI |
| **U7 ★** | `test_spans_map_to_original_text` (table + property) | extraction/normalize, evidence | `normalize_with_map` preserves length. For every span, `original[start:end]` normalizes to the quote. Cases: tatweel, harakat, أ/إ/آ, uppercase French, Arabizi digits (`9rib`, `3and`), emoji. Property: 200 seeded random strings over the case alphabet. | No | Omar | T1 | #3, #17 · XP |
| **U14 ★** | `test_fallback_chain` (param) | extraction/clients, cascade | 120b gives 429 → 20b is called exactly once, with no sleep (clock unchanged). 120b and 20b both fail → Gemini if `GEMINI_ENABLED`, otherwise rules. Everything fails → `path='rules'`, `valid=0`, confidence low. `Malformed` and `BadRequest` are never retried on the same model. `CapReached` goes straight to rules. The call order is asserted, and each fallback writes an `llm.fallback` event. | Fail | Omar | T1 | #5 · FX |
| **U17 ★** | `test_reply_adjustments` (param) | scoring/rules | confirmed → ×0.6. declined → `action='cancelled'` with the previous scores **carried forward**. reschedule → unchanged. ambiguous → `needs_review`. no-reply → +15, capped at 100. | No | Omar | T1 | FX · hero |
| **C1 ★** | `test_score_results_persist` (param: `llm, cascade_cache, fallback_model, rules, rules_capped, declined, not_order`; plus `cascade_ack` and `fallback_provider` under F) | scoring ↔ db/repo | The **real** `score_order` output inserts cleanly and `version = prev + 1`. `current_assessment_id` moves. `not_order` writes no assessment. `rules` has `extraction_id` NULL. `declined` carries the previous scores. | Rec | Omar | T1 (G2 12:00) | #5, #25 · FX |
| **C3 ★** | `test_mocks_match_api_models` | api/models ↔ mocks | `mocks/orders.json` and `mocks/order_detail.json` validate against the Pydantic response models, including `segments`, `rescore_state`, `origin` and `path`. `GET /api/orders` and `GET /api/orders/{hero}` on a seeded DB validate against the same models. No response model has a `phone_e164` field. | No | Jesser | T1 (12:00, rerun 18:00) | #25, #16 |
| **J10 ★** | `test_debounce` | worker | With `FrozenClock`, 3 messages 1 s apart give exactly 1 rescore, at last + 4 s. `process_due` before the due time does nothing. The due field is cleared in the same transaction. `utc_iso` output is fixed-width, `Z`-suffixed and sorts lexicographically. | No | Jesser | T1 | #14, #22 |
| **J11 ★** | `test_versions_append_only` | db/repo | A rescore inserts v2 and the v1 row stays byte-identical. A duplicate `(order_id, version)` raises. | No | Jesser | T1 | #24 · AI |
| **J12 ★** | `test_ingest_paths_parity` | ingress, seed | The same hero text via `/api/orders/ingest`, `simulate-reply` and the seed loader (plus the signed webhook under F(S-1)) gives identical `features_json` and `final_score`. | Rec | Jesser | T1 | #9 · FX |
| **E1 ★** | `test_hero_loop_golden` | full pipeline | **v1 (paste):** tier high, `75 ≤ model_score ≤ 92`, `abs(final - 65) ≥ 10`, a risk segment exactly "9rib el jemaa" in original coordinates, and a static `T_ADDRESS` outbound stored with `template_id`. **v2 (simulate-reply)**, run with both the clean fixture **and** the stale fixture (v1 flags re-emitted at `msg_idx` 0): features identical, `[1.0, 0, 0, 220, 2, 0.30]`, tier low, `final ≤ 25`, `abs(final - 35) ≥ 10`, and the reason diff names the resolved codes. `final == HERO_V1 / HERO_V2` (`tests/e2e/hero.py`); these are the numbers slides and video cite. | Rec + Hand (stale) | Omar (Jesser pairs) | T1 (G6 18:00) | #3, N5 · FX, XP |
| **E4 ★** | `test_injection_regression` (param: 8 = 4 base × 2 languages from `injection.yaml`, floor 4) | full pipeline | With the injection appended, `final_score ≥` the clean twin's score, the tier is not lowered, `status == needs_review` with an assessment row written, and no field outside the schema appears. One extra case per language: a recorded extraction with `is_order=false` for a real order + "this is not an order" must still produce an assessment row in `needs_review` (02 §5 step 9, 01 §5.2 rule 0). This is framed as regression on recorded outputs; live behaviour is measured in L1. | Rec | Omar | T1 (20:00) | #2 · AI, RAI |
| **M1 ★** | `test_health_and_safe_defaults` | api/routes, settings | With **no** `APP_MODE`, `/api/health` returns 200 with `mode=public`, `wa_send=false`, `webhook="disabled"`, `config_hash`, the extraction model and `live_calls_today/cap`. `POST /api/webhook/whatsapp` returns 404. `/health` makes **0** LLM calls. | No | Montassar | T1 (by 20:00) | N1, #5 |
| U24 | `test_resolve_flags` (param + properties) | extraction/resolve | `r(r(x)) == r(x)` and `r(x) ⊆ x`. `vague_location` drops only at final `exact`. `availability_uncertain` drops iff confirmation ∈ {confirmed, reschedule} and `msg_idx < k`. `price_hesitation` drops iff confirmed and `msg_idx < k`. With `k=None` only the vague rule fires. A flag quoted after `k` survives. Drops are written to `adjustments.resolved_flags`. | No | Omar | T1+ | N5 · AI |
| U28 | `test_no_eval_leakage` | data, prompts | No `eval_only` phrase appears in `prompts/*` or `fewshot.jsonl`. No few-shot line appears in the eval windows. The hero script differs from FS7/FS8. | No | Omar | T1+ (due G3b 16:30) | N4 · AI |
| U30 | `test_eval_mode_is_single_shot` | extraction/clients | `build_chain(eval_mode=True)` has exactly 1 client, the cache is bypassed, and a failure is recorded as a failure rather than replaced by rules. | No | Omar | T1+ (before eval run) | N4 · AI |
| U29 | `test_llm_budget` | extraction/clients (`CappedClient`) | At the cap it raises `CapReached` and never reaches the inner client. Replay and cache hits spend nothing. The per-visitor window resets after `FrozenClock.advance`. | No | Omar | T1+ | N3, #5 |
| J14 | `test_prefilter` (param: `prefilter.yaml`, 6 bad drafts + passes) | outbound/prefilter | Rejected: missing slot, extra number, URL, phone, `carte`/`rib`, a discount not in the order, > 400 chars. "code postal" passes. | No | Omar | T1+ (G4) | #2, #8 · RAI |
| J15 | `test_static_templates_pass_prefilter` | outbound/templates | Every template × language × sample slot set passes the prefilter. | No | Jesser (copy: Fedi) | T1+ (when copy lands) | #2 |
| J19 | `test_static_insert_and_seller_context` | worker, outbound | Tier ≥ medium writes exactly one outbound message with `template_id` and `canonical_text` (hero: `T_ADDRESS`). Tier low writes none. The next window's `[SELLER]` line equals `canonical_text`. An `author='ai'` row with NULL `canonical_text` is skipped. Outbound text is never extracted as customer text. | No | Jesser | T1+ | #8, #13, N5 |
| C4 | `test_runtime_replay_is_recorded_only` | clients, seed | The runtime `ReplayClient` (`data/llm_replay/` only) refuses `meta.source == "hand_crafted"`. After `make seed`, every `extraction_runs.model` is a real model id. Every `data/llm_replay` fixture has `meta.prompt_version == PROMPT_VERSION`; on a mismatch the message says "run `make record`". | No | Jesser | T1+ | RAI (honesty), #19 |
| P1 | `test_public_mode_forces_sends_off` (param: `APP_MODE` unset / `public` / `staging`) | settings, main | The effective mode is public. Even with `WA_SEND_ENABLED=true` and `WA_TOKEN` set, the sender is `NullSender`. `POST /api/drafts/{id}/send` returns "sent (simulated)" with an injected `FakeSender.calls == 0`. The webhook is not mounted. The no-reply timer is off. | No | Montassar | T1+ (**deploy gate** before 22:00 first public deploy) | N1 · RAI |
| P2 | `test_seeded_rows_read_only` | api/routes, visibility | In public mode, actions, rescore, simulate-reply and send on a `sandbox_id IS NULL` order return **409 `SEEDED_READONLY`**, and the row is unchanged. | No | Jesser | T1+ (sandbox gate 22:00) | N2 |
| P3 | `test_visitor_isolation` | visibility helper | Lists for `X-Visitor-Id: A` return seeded ∪ A. A request by A for B's order returns 404. In `event` mode the header is ignored and seeded rows are writable. | No | Jesser | T1+ | N2 · RAI |
| P4 | `test_try_this_order_zero_llm` | api/sandbox, seed loader | `POST /api/sandbox/try {"fixture_id":"hero"}` creates a new order with `sandbox_id=A` and the same `final_score` as the seeded hero, with **0** chain calls (cache hit). | No | Jesser | T1+ | N2, N3 · FX |
| P5 | `test_sandbox_purge` | worker.`purge_sandboxes` | After clock + 2 h + 1 s, visitor rows and their messages, assessments, drafts and events are gone, seeded rows are untouched, and the function returns the count. | No | Montassar | T1+ | N2 · RAI |
| P7 | `test_webhook_fails_closed` | main, ingress | With an empty `WA_APP_SECRET`, in any mode, the webhook POST is not mounted and `/api/health` shows `webhook:"disabled"`. A GET verify with the wrong token returns 403. | No | Jesser | T1+ | #6, N1 |
| U12 | `test_mask_phones` (param) | privacy | `+216 22 123 456`, `22123456` and `216-22-123-456` become `+216 ** *** 456`. `immeuble 4`, `km 8.5` and `1008` are untouched. | No | Omar | T1+ | #16 · RAI |
| M3 | `scripts/smoke.py URL` | deployed app | Steps are in §5. Health and mode, SPA served, "Try this order" gives HIGH, the v2 reply gives LOW, and a seeded mutation returns 409. | No | Montassar | T1+ (20:00; Sun 08:30, 15:30, 16:50) | FX, N1 |
| M4 | CI `web` job | web/ | `eslint` with `react/no-danger: error`, `tsc --noEmit`, `vite build`. | No | Montassar | T1+ (from stack decision) | #17 |
| E3 | `test_fallback_drill` (param: `fail_primary`, `fail_all`; `fail_groq` under F(S-6)) | full pipeline | Hero v1 is still scored (fallback model, then rules). Every API call returns 200. `llm.fallback` events are written. Under rules, v2 < v1. Writes `reports/fallback_drill.json` when `WRITE_REPORTS=1`. | Fail + Rec | Jesser + Montassar | T2 #1 | #5, #9 · FX |
| R1 | `test_reports_have_provenance` | reports/ | Every `reports/*.json` validates against `reports/schema.json`: `report, created_at, git_sha, model, prompt_version, prompt_sha256, n, labelers, eval_mode{fallback,cache,cascade}, scope, metrics`. | No | Montassar | T2 #2 | N4 · AI, RAI |
| R2 | `test_readme_numbers_match_reports` | README ↔ reports | Each `<!--r:FILE#dotted.path-->VALUE<!--/r-->` marker in README equals `str()` of that value in the report. Unfilled `{{…}}` placeholders fail only when `SUBMISSION=1`. | No | Montassar (fill: Fedi) | T2 #3 | TR, RAI |
| M2 | `test_segments_escape_and_align` | api/segments | `"".join(s.text) == original text` for every message. Risk and address segments cover exactly the verified spans. `<script>`, `<img onerror>` and `</mark>` stay literal text. Arabic spans land on the correct characters. The Streamlit fallback escapes each segment. | No | Montassar | T2 #4 | #17 · XP |
| U13 | `test_llm_request_has_no_pii` | extraction/prompt | The built request for a window containing a phone number and a customer ID contains neither. | No | Omar | T2 #5 | #16 · RAI |
| U8 | `test_cross_field_rules` (param) | extraction/evidence | `exact` without the `NUM` helper or a building token becomes `street_and_landmark`. A pin gives `exact`. `is_order=false` gives no score. Confirmation with no outbound becomes `none`. | No | Jesser | T2 #6 | #3 · AI |
| U26 | `test_tone_gate` | extraction/evidence | Non-neutral tone without verified `tone_evidence` becomes neutral. `tone_evidence` that overlaps a flag span becomes neutral. | No | Omar | T2 #7 | #11 · AI |
| U27 | `test_generator_offline_and_deterministic` | ml/generate | An AST scan finds no import of `groq`, `google.genai` or `app.extraction.clients`. The same seed gives the same sha256 over 500 rows. `eval_only` phrases appear only in `eval_subset` rows. | No | Omar | T2 #8 | #11 · RAI |
| U22 | `test_model_artifact_matches_manifest` | scoring/model | `sha256(classifier.json)` matches the manifest. The feature order equals `FEATURE_ORDER` (6 features). The monotone vector is `(-1,1,1,1,1,1)`. The installed xgboost major.minor matches the manifest. | No | Jesser | T2 #9 | #24 · AI |
| U20 | `test_classifier_monotone` | scoring/model | Over a grid of the other features, the score is non-increasing in `address_specificity` and non-decreasing in the other five. | No | Jesser | T2 #10 | AI · hero |
| U19 | `test_scoring_config` | scoring/rules | `scoring.yaml` validates and its sha256 is stable. Changing one threshold changes the hash. A bad file fails at load. | No | Jesser | T2 #11 | #24 |
| U4 | `test_normalize_cases` (param: `normalize.yaml`) | extraction/normalize | NFKC, casefold, diacritics, tatweel, أ/إ/آ → ا, ى → ي, ة → ه, whitespace collapse. | No | Jesser (data: Fedi) | T2 #12 | #4 |
| U25 | `test_num_helper_shared` | text/numbers | One case table drives both the `exact` guard and the generator lint. `km 8.5`, `1008`, `3and` (Arabizi letter, not a number) and `rue 7` behave as specified. | No | Omar | T2 #13 | #4 · AI |
| J9 | `test_state_transitions` (table) | state | Every allowed edge passes. `cancelled→ready_to_ship` raises. A reply while in `needs_review` triggers a rescore and keeps the seller override. | No | Jesser | T2 #14 | FX |
| J8 | `test_extraction_window` | worker | Customer lines only, capped at the last 12 lines / 2,000 chars. The latest template `canonical_text` appears as `[SELLER]`. Lines are in `provider_ts` order. | No | Jesser | T2 #15 | #13 |
| J7 | `test_order_boundary_rules` | ingress/ingest | No open order → create one. An open order → attach. After `shipped` or `cancelled` → a new order. | No | Jesser | T2 #16 | #8 |
| E5 | `test_public_judge_path` | full pipeline, public | This is the judge path in-process: try hero → HIGH, reply → LOW, and afterwards the seeded hero is still v1 HIGH for the next visitor. | Rec | Jesser | T2 #17 | N2 · FX |
| P6 | `test_cap_returns_rules_not_429` | api + budget | Over the global or per-visitor cap, the response is 200 with `path='rules'` and `banner="llm_cap"`. The seeded and cached hero path is never capped. | No | Montassar | T2 #18 | N3, #5 |
| P9 | `test_public_boot_reseed_wipes_real_rows` | seed on boot | A public boot with `SEED_ON_BOOT=true` removes every non-seeded row (WhatsApp-origin rows included). | No | Montassar | T2 #19 | N1 · RAI |
| P10 | `test_public_display_pseudonymized` | api/models | In public mode `display_name` is pseudonymized, and no response contains a `216\d{8}` string. | No | Jesser | T2 #20 | #16 · RAI |
| U15 | `test_feature_mapping` | scoring/features | The address-level → specificity table. Price comes **from the catalog** even when the text mentions another price. An unmatched product gives `product_id=null` and confidence low. | No | Omar | T2 #21 | #11 |
| U18 | `test_reason_deterministic` | scoring/reason | Same input gives the same string. The reason names the top-3 contributions and zone when zone is in the top 3. The diff is `codes(v−1) − codes(v)`. Quotes are wrapped in FSI/PDI. | No | Omar | T2 #22 | #15 · RAI |
| U10 | `test_prompt_prefix_byte_stable` | extraction/prompt | System prompt and few-shot bytes are identical across windows, contain no timestamp or order-ID digits, and stay ≤ 2.8K tokens (tokenizer estimate). | No | Omar | T2 #23 | #5 |
| M5 | `test_spa_served` | main | With `web/dist` present, `/` serves `index.html` and `/api/*` isn't shadowed. Skipped if `dist` is absent. | No | Montassar | T2 #24 | FX |
| U2 | `test_gemini_schema_matches_pydantic` | extraction/schemas | `to_gemini_schema(order_extraction_v1)` has the same field set and enums [VERIFY Gemini dialect]. | No | Omar | F(S-6 Gemini) | #5 |
| U9 | `test_cascade_table` (param: `cascade.yaml`) | extraction/cascade | "ey", "باهي" or "👍" after a template question → `cascade_ack` with **0** LLM calls. "ey" with no prior question → `llm`. "ey, ama bdel l'adresse…" → `llm`. A pin → `exact`. "la" → declined. | No | Omar | F(S-5 cascade) | #23, #5 |
| J1 | `test_webhook_verify_get` | ingress/whatsapp | The right token returns 200 with the `text/plain` challenge; the wrong one returns 403. | No | Jesser | F(S-1 WhatsApp) | #6 |
| J2 | `test_webhook_signature` (param) | ingress/whatsapp | Valid → 200. **Forged** → 401, a `webhook.rejected` event and 0 message rows. Missing header → 401. Body tampered after signing → 401. | No | Jesser | F(S-1) | #6 · RAI |
| J3 | `test_webhook_duplicate_wamid` | ingress + db | The same payload posted twice gives 1 message row, 1 pending rescore and 1 assessment version after `process_due`. | No | Jesser | F(S-1) | #7 |
| J4 | `test_webhook_status_receipt` | ingress + db | `statuses[]` updates `delivery_status` only: 0 new messages, no rescore. An unknown wamid returns 200 as a no-op. | No | Jesser | F(S-1) | #7 |
| J5 | `test_webhook_out_of_order_batch` | ingress | A batch with reversed timestamps produces a window ordered by `provider_ts`. | No | Jesser | F(S-1) | #7 |
| J6 | `test_webhook_type_mapping` (param) | ingress | location → lat/lng and `has_geo_pin`. image/sticker/audio → `unsupported`, and the order goes to review. `context.id` → `reply_to_message_id`. | No | Jesser | F(S-1) | #18 |
| E2 | `test_hero_loop_webhook_parity` | full pipeline | Hero v1 as a signed webhook payload gives the same scores as E1. | Rec | Jesser | F(S-1) | #9 |
| J13 | `test_no_reply_timeout` | worker | At 60 s (demo), a version with `trigger=no_reply_timeout`, +15 and `needs_review`. A reply at 59 s cancels it. Off in public mode. | No | Jesser | F(no-reply) | FX |
| J16 | `test_judge_gate` (param) | outbound/judge | `approve` with overreach ≠ none → reject. Non-empty `unsupported_claims` → reject. A judge error → fail closed. Two rejects → `static_template`. | Hand | Omar | F(S-3 rewrite) | #2 · RAI |
| J17 | `test_loop_guard_and_window` | outbound/route | `auto_messages_sent ≤ 2`. Never a reply to our own outbound. `now − last_inbound > 24h` → `needs_review`. | No | Jesser | F(S-3) | #8, #20 |
| J18 | `test_demo_mode_requires_click` | outbound/route | In `DEMO_MODE`, `auto_send` sends nothing until `POST /api/drafts/{id}/send`. | No | Jesser | F(S-3) | RAI |
| L1 | `make eval` | live | 24 windows, frozen `extract-v1`, no fallback/cache/cascade, plus second-labeler agreement on 6 → `reports/eval_extraction.json` | Live | Omar (labels: Fedi + 2nd labeler) | L (G3b 16:30 → committed 19:00) | #4, N4 · AI |
| L3 | §16 key checks | live | `reports/verification.md` (date and result per checkbox) | Live | Omar / Jesser | L (G1 12:00) | #5 |
| L4 | WhatsApp phone → queue × 5 | live | `reports/whatsapp_e2e.md` (timestamp, wamid suffix, pass/fail) | Live | Jesser | L, F(S-1) | #6, #7 |
| L5 | `make record` | live | Refreshes `data/llm_replay/` and `tests/fixtures/llm/recorded/`; about 15 calls on the **dev** org | Live | Omar | L (after G3b; again after any prompt bump) | TR |
| L6 | `make bakeoff` (qwen challenger) | live | `reports/bakeoff.json`; must reach ≥ 3/N | Live | Omar | L, F(S-4), cut before S-6 | #4 · AI |
| L7 | `make eval-skew` | live | 40 `eval_only` synthetic rows through the real `score_order` in eval mode → `reports/eval_skew.json` (tier agreement N/40, 3×3 confusion, mean/max \|Δ\|) | Live | Omar | L (Should, Sun 15:00) | #11 · AI |
| — | Backlog (listed under "What this does not prove") | | U11 input-hash components (partly covered by C1 `cascade_cache`), U21 holdout tier ordering (reported in `classifier_holdout.json` instead), U6 (merged into U5) | | | B | |

**Counts:**
- T0: 4. T1 ★ minimum: 16 (3 of them already in T0).
- T1+: 15 pytest functions, plus M3 and M4.
- If all Must code merges Saturday, `main` holds about 32 green test functions at 22:00. T2 needs only E3, R1 and R2 to pass 34.
- Parametrization brings the case count to about 180.

**Budget check against the Strategist's hours:**
- ★ tests: Omar ~110 min, Jesser ~65 min, Montassar ~30 min (all as agreed in R2).
- T1+ tests: each is 10–20 lines of table data, written in the same PR as the code, and costed inside that code's estimate (resolve_flags, sandbox, cap, prefilter, static insert).

## 2. Seams and contracts (skeleton at 09:30, frozen at G-seams 10:30; fields frozen at G2 12:00)

```python
# app/clock.py — the ONLY place that reads the wall clock (hygiene + ruff DTZ enforce)
class Clock(Protocol):
    def now(self) -> datetime: ...                      # always tz-aware UTC

class SystemClock:
    def now(self) -> datetime: return datetime.now(timezone.utc)

class FrozenClock:                                       # in app/, so drills and scripts can use it too
    def __init__(self, start: datetime) -> None: ...     # asserts start.tzinfo is not None
    def now(self) -> datetime: ...
    def advance(self, seconds: float) -> None: ...

def utc_iso(dt: datetime) -> str: ...    # "2026-09-27T10:00:04.123Z": fixed width, sorts lexicographically
def parse_utc(s: str) -> datetime: ...

# app/ids.py
class IdGen(Protocol):
    def __call__(self, prefix: str) -> str: ...          # UlidIds in prod, SeqIds ("ord_0001", ...) in tests
```

```python
# app/extraction/clients.py — the ONLY module that imports groq / google.genai (hygiene enforces)
@dataclass(frozen=True)
class LLMRequest:
    purpose: Literal["extract", "rewrite", "judge"]
    messages: list[dict[str, str]]        # already PII-masked (U13)
    schema_name: str                      # "order_extraction_v1"
    schema: dict                          # strict JSON Schema, Groq dialect; GeminiClient converts via to_gemini_schema
    replay_key: str                       # sha256(normalized window text); deliberately excludes model + prompt_version

@dataclass(frozen=True)
class LLMResult:
    raw_json: str
    provider: str                         # "groq" | "gemini" (replay reports the ORIGINAL provider from fixture meta)
    model: str                            # e.g. "openai/gpt-oss-120b" [VERIFY ids]
    source: Literal["live", "recorded", "hand_crafted"]
    tokens_in: int | None
    tokens_out: int | None
    latency_ms: int
    ratelimit_remaining_tokens: int | None

class LLMError(Exception): kind: ClassVar[str]
class RateLimited(LLMError):  kind = "429"          # .retry_after_s: float | None
class Timeout(LLMError):      kind = "timeout"
class BadRequest(LLMError):   kind = "400"          # schema mismatch: never retried on the same model
class Malformed(LLMError):    kind = "malformed"    # non-JSON content: never retried on the same model
class ProviderDown(LLMError): kind = "5xx"
class CapReached(LLMError):   kind = "cap"          # chain goes straight to rules
class FixtureMissing(LookupError): ...              # NOT an LLMError: tests fail loudly, never silently go to rules.
                                                    # Message: "no fixture for key ab12…: '<window preview>': run `make record`"

class LLMClient(Protocol):
    name: str                                       # "groq:openai/gpt-oss-120b"
    def complete(self, req: LLMRequest) -> LLMResult: ...    # raises LLMError; NEVER retries or sleeps internally

# Implementations
GroqClient(model: str, timeout_s: float)
GeminiClient(model: str, timeout_s: float)                    # [VERIFY SDK + schema dialect]
ReplayClient(dirs: list[Path], *, allow_hand_crafted: bool = False, as_provider: str | None = None)
FailingClient(kind: Literal["429","timeout","400","malformed","5xx"], name: str)
CappedClient(inner: LLMClient, budget: CallBudget, budget_key: Callable[[], str])
RecordingClient(inner: LLMClient, out_dir: Path)              # used only by `make record`

class CallBudget(Protocol):
    def try_spend(self, key: str) -> bool: ...    # keys "global", "visitor:<vid>"; windows driven by the injected Clock

def build_chain(settings: Settings, *, eval_mode: bool = False) -> list[LLMClient]: ...
# LLM_MODE=live          [Capped(Groq 120b), Capped(Groq 20b), Capped(Gemini) if GEMINI_ENABLED]
# LLM_MODE=replay        [Replay(runtime dirs)]                        (tests: fixture adds test dirs + allow_hand_crafted)
# LLM_MODE=fail_primary  [Failing("429","groq:120b"), Replay(as_provider="groq")]           -> path fallback_model
# LLM_MODE=fail_groq     [Failing("429",…120b), Failing("5xx",…20b), Replay(as_provider="gemini")] -> fallback_provider
# LLM_MODE=fail_all      [Failing(...) for each tier]                                       -> path rules
# eval_mode=True         [Groq 120b] only; caller bypasses cache and cascade (U30)
# One switch serves CI, rehearsal, the disclosed stage fallback and the drill. demo_orders.json is gone; data/demo_seed.json is seed data only.

# app/extraction/cascade.py
def run_chain(chain: list[LLMClient], req: LLMRequest) -> tuple[LLMResult | None, list[Attempt]]: ...
# path = "llm" (index 0) | "fallback_model" (same provider, later index) | "fallback_provider" | "rules" (None)
```

```python
# app/worker.py — sync functions tests call directly; the async loop is a thin wrapper
def process_due(conn: sqlite3.Connection, now: datetime, scorer: Scorer, *, limit: int = 10) -> list[str]: ...
    # rescore every order with rescore_due_at <= now; no clock reads, no sleeps; returns processed order_ids
def fire_no_reply_timeouts(conn, now: datetime, scorer: Scorer) -> list[str]: ...   # no-op in public mode
def purge_sandboxes(conn, now: datetime, ttl: timedelta = timedelta(hours=2)) -> int: ...  # public mode only
async def run_loop(app: FastAPI) -> None: ...
    # every 1 s: await asyncio.to_thread(tick, now=clock.now()); started in lifespan only if settings.worker_enabled
```

```python
# app/contracts.py — types frozen 10:30; fields frozen G2 12:00; Omar merges any change and announces it in chat
Path    = Literal["llm", "cascade_ack", "cascade_cache", "fallback_model", "fallback_provider", "rules"]
Trigger = Literal["initial", "customer_reply", "no_reply_timeout", "manual"]
Tier    = Literal["low", "medium", "high"]

@dataclass(frozen=True)
class Line:
    msg_idx: int
    role: Literal["CUSTOMER", "SELLER"]    # SELLER text = canonical template text, never LLM-rewritten text
    text: str
    message_id: str

@dataclass(frozen=True)
class Window:
    order_id: str
    lines: tuple[Line, ...]
    seller_idx: int | None                 # k: index of the latest SELLER line
    has_geo_pin: bool
    new_message_ids: tuple[str, ...]

@dataclass(frozen=True)
class OrderCtx:
    order_id: str
    zone: str | None
    customer_refusal_rate: float
    trigger: Trigger
    prev_extraction: "OrderExtraction | None"     # 12-field Pydantic model, app/extraction/schemas.py
    prev_assessment: "AssessmentRow | None"
    sandbox_id: str | None

@dataclass(frozen=True)
class OutboundInsert:                      # static template insert when tier >= medium (J19)
    template_id: str
    language: str
    canonical_text: str

@dataclass(frozen=True)
class ScoreResult:
    extraction_run: "ExtractionRunRow | None"   # None for cascade_cache/rules
    assessment: "AssessmentRow | None"          # None only when is_order=false
    order_patch: dict[str, object]
    events: tuple["EventRow", ...]
    outbound: OutboundInsert | None

class Scorer(Protocol):
    def __call__(self, window: Window, ctx: OrderCtx) -> ScoreResult: ...
# AssessmentRow must include (tests read these): version, trigger, model_score, final_score, tier, confidence,
# action, path, features_json (FEATURE_ORDER, 6 values), adjustments_json (incl. resolved_flags, repairs),
# reason, config_hash, model_version, prompt_version. Architect owns the full field list.
```

```python
# app/settings.py (pydantic-settings; fails fast naming the missing variable)
app_mode: Literal["dev", "event", "public"] = "public"      # before-validator: unknown value -> "public"
llm_mode: Literal["live", "replay", "fail_primary", "fail_groq", "fail_all"] = "live"
worker_enabled: bool = True
gemini_enabled: bool = False
live_llm_daily_cap: int = 300
# derived, never read from env directly:
@property wa_send_enabled -> app_mode != "public" and WA_SEND_ENABLED and bool(wa_token)
@property webhook_mounted -> app_mode != "public" and WEBHOOK_ENABLED and bool(wa_app_secret)
@property admin_mounted   -> bool(admin_token)

# app/outbound/sender.py
class Sender(Protocol):
    def send_text(self, to_e164: str, text: str) -> str: ...   # returns wamid
# WhatsAppSender (httpx), NullSender ("sent (simulated)"; chosen whenever not wa_send_enabled), FakeSender (tests; records .calls)

# app/main.py
def create_app(settings: Settings | None = None, *, clock: Clock | None = None,
               chain: list[LLMClient] | None = None, sender: Sender | None = None,
               ids: IdGen | None = None, budget: CallBudget | None = None) -> FastAPI: ...
# zero-arg call works (uvicorn --factory). Routes under /api; SPA mounted last from web/dist.
```

**`tests/conftest.py` fixtures (Montassar owns the file; T0):**
- `settings(**over)`: `APP_MODE=dev`, `LLM_MODE=replay`, `WORKER_ENABLED=false`, test secrets.
- `clock`: `FrozenClock(2026-09-27T10:00:00Z)`.
- `ids`: `SeqIds`.
- `db`: a tmp-path **file** DB from `schema.sql` plus the catalog, so WAL and multiple connections behave as in prod.
- `replay`: the runtime dirs plus `tests/fixtures/llm/{recorded,hand_crafted}`, with `allow_hand_crafted=True`.
- `failing(kind)`, `chain(mode)`, `sender` (`FakeSender`), `client` (`TestClient(create_app(...))`).
- `public_client(vid="A")`: `APP_MODE=public`, sets `X-Visitor-Id`.
- `seeded`: runs the seed loader on `db`.
- `wa_post`, `seed_order(**over)`, `hero` (text + constants).
- `_no_network` (autouse).

```python
@pytest.fixture(autouse=True)
def _no_network(monkeypatch, request):
    if request.node.get_closest_marker("live"):
        return
    real = socket.socket.connect
    def guard(self, addr, *a, **k):
        if isinstance(addr, str) or addr[0] in ("127.0.0.1", "::1", "localhost"):
            return real(self, addr, *a, **k)
        raise RuntimeError(f"network call to {addr} in an offline test: use ReplayClient / FakeSender")
    monkeypatch.setattr(socket.socket, "connect", guard)

def wa_post(client, name, *, secret=TEST_WA_SECRET, tamper=False, header=True):
    raw = (FIXTURES / "whatsapp" / name).read_bytes()          # sign the EXACT bytes; never json=
    sig = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    body = raw.replace(b"wamid.TEST", b"wamid.TESX") if tamper else raw
    headers = {"Content-Type": "application/json", **({"X-Hub-Signature-256": sig} if header else {})}
    return client.post("/api/webhook/whatsapp", content=body, headers=headers)
```

`tests/e2e/hero.py` holds `HERO_V1`, `HERO_V2`, `HERO_V1_TEXT`, `HERO_V2_TEXT` and `HERO_V2_FEATURES = [1.0, 0, 0, 220, 2, 0.30]`. The stub values are replaced at G6 by the numbers the real model produces. Slides, video captions and README read them from here, never from the script.

## 3. Fixtures

**Rule:** there are three LLM fixture roots, and the directory decides what may reach users.

| Root | Contents | Shipped in Docker image | Loaded at runtime |
|---|---|---|---|
| `data/llm_replay/{groq,gemini}/` | **recorded** outputs needed by seed, "Try this order" and the stage fallback | yes | yes (`LLM_MODE=replay`, seed cache) |
| `tests/fixtures/llm/recorded/` | recorded, test-only (injections, languages) | no (`.dockerignore: tests/`) | no |
| `tests/fixtures/llm/hand_crafted/` | edge cases no model produced | no | never; `ReplayClient` refuses them unless `allow_hand_crafted=True` |

Every LLM fixture uses one envelope: `{"meta":{"source":"recorded"|"hand_crafted","provider","model","prompt_version","recorded_at"},"key":"<sha256 normalized window>","window":"<text>","status":200,"headers":{...},"response":{...}}`.

| Path | Source | Content | Used by |
|---|---|---|---|
| `data/demo_seed.json` | Fedi (text), Jesser (shape) | seeded conversations; entry `"hero"` has v1 text, the `T_ADDRESS` slot values and the v2 reply text | seed, P4, E1, E5, M3 |
| `data/llm_replay/groq/extract_hero_v1.json` | recorded | hero v1 (Arabizi, landmark, 3 flags incl. `price_hesitation`) | E1, J12, C1, E3, P4, seed |
| `data/llm_replay/groq/extract_hero_v2_clean.json` | recorded | hero v2 reply (street + building + time), no stale flags | E1, E5, P4, seed |
| `data/llm_replay/groq/extract_seed_{fr_exact,ar_exact,mixed_medium}.json` | recorded | the other seeded orders | seed, C1, J12 |
| `data/llm_replay/gemini/extract_hero_v1.json` | recorded [VERIFY response shape] | hero v1 via Gemini | C1[`fallback_provider`], E3[`fail_groq`] (F S-6) |
| `tests/fixtures/llm/hand_crafted/extract_hero_v2_stale.json` | hand_crafted | v2 that re-emits all 3 v1 flags at `msg_idx` 0 | E1 (stale variant), U24 |
| `tests/fixtures/llm/recorded/extract_injection_{fr,arabizi,ar,mixed}_{a,b}.json` + `extract_clean_{fr,arabizi,ar,mixed}.json` | recorded | 4 base × 2 injection variants and their clean twins | E4 |
| `tests/fixtures/llm/recorded/extract_not_order_greeting.json` | recorded | `is_order:false` | C1[`not_order`], U8 |
| `tests/fixtures/llm/hand_crafted/extract_hallucinated_evidence.json` | hand_crafted | flag evidence absent from the window, one quote only in `[SELLER]` | U5 |
| `tests/fixtures/llm/hand_crafted/extract_overflow_qty60_7flags.json` | hand_crafted | qty 60, 7 flags, 5 quotes, 200-char evidence, unknown code | U3 |
| `tests/fixtures/llm/hand_crafted/extract_exact_without_num.json` | hand_crafted | `exact` without a number or building token | U8 |
| `tests/fixtures/llm/hand_crafted/extract_tone_overlap.json` | hand_crafted | `tone_evidence` equal to a flag span | U26 |
| `tests/fixtures/llm/hand_crafted/err_429.json` | hand_crafted from docs [VERIFY body] | status 429, `retry-after`, `x-ratelimit-*` | U14, E3 |
| `tests/fixtures/llm/hand_crafted/err_400_schema_mismatch.json`, `malformed_content.json` | hand_crafted | 400 body; non-JSON `content` | U14 |
| `tests/fixtures/llm/hand_crafted/judge_{approve,approve_but_overreach,reject}.json` | hand_crafted | judge verdicts | J16 (F S-3) |
| `tests/fixtures/whatsapp/text_inbound.json` | Meta docs shape [VERIFY], then scrubbed L4 | 1 text, `wamid.TEST1` | J2, J3 |
| `tests/fixtures/whatsapp/text_inbound_duplicate.json` | same | batch with `wamid.TEST1` again + 1 new | J3 |
| **forged signature** | not a file | `wa_post("text_inbound.json", secret="wrong")`, `tamper=True`, `header=False` | J2 |
| `tests/fixtures/whatsapp/status_{delivered,read}.json`, `status_unknown_wamid.json` | same | `statuses[]` only | J4 |
| `tests/fixtures/whatsapp/batch_out_of_order.json` | same | 2 messages, reversed timestamps | J5 |
| `tests/fixtures/whatsapp/{location,audio,image,reply_with_context}.json` | same | type mapping | J6 |
| `tests/fixtures/whatsapp/hero_v1_inbound.json`, `hero_v2_reply.json` | same | hero as webhook payloads | E2 |
| `tests/fixtures/whatsapp/verify_get.txt` | hand | GET handshake query string | J1 |
| `tests/fixtures/cases/injection.yaml` | Fedi | 4 base injections × 2 languages (FR, Arabizi, Arabic-script, mixed) + clean twin ids | E4, L1 |
| `tests/fixtures/cases/prefilter.yaml` | Fedi | 6 should-reject + should-pass drafts (incl. "code postal") | J14 |
| `tests/fixtures/cases/cascade.yaml` | Fedi | ack/decline/content-bearing per language | U9 (F) |
| `tests/fixtures/cases/normalize.yaml`, `numbers.yaml` | Fedi | Arabic variant pairs; `NUM` helper cases | U4, U7, U25 |
| `data/eval/windows.jsonl` (24), `data/eval/second_label.jsonl` (6) | Fedi, second labeler | eval set | U23, U28, L1 |
| `data/catalog.csv`, `mocks/orders.json`, `mocks/order_detail.json` | Omar / Jesser | catalog; frozen UI contract (18:00) | U15, C3 |
| `reports/schema.json` | Montassar | provenance schema | R1 |

All phone and `wa_id` values come from the allowlist `21600000001`–`21600000009` (fake). `scripts/scrub_fixture.py` swaps them in, and `make hygiene` fails on any other `216\d{8}` under `tests/fixtures`, `data` or `mocks`.

## 4. GitHub Actions: `.github/workflows/ci.yml` (Montassar, T0)

```yaml
name: ci
on:
  push:
  pull_request:
  workflow_dispatch:
concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true
permissions:
  contents: read

jobs:
  backend:
    name: backend (make check, no keys)
    runs-on: ubuntu-latest
    timeout-minutes: 10
    env:
      GROQ_API_KEY: ""          # deliberately empty: CI must never need a key
      GEMINI_API_KEY: ""
      WA_TOKEN: ""
    steps:
      - uses: actions/checkout@v4            # [VERIFY current major]
      - uses: actions/setup-python@v5        # [VERIFY current major]
        with:
          python-version-file: .python-version
          cache: pip
          cache-dependency-path: |
            requirements.txt
            requirements-dev.txt
            constraints.txt
      - name: make check (hygiene + lint + offline tests)
        run: make check PYTEST_ARGS="--junitxml=reports/junit.xml --cov=app --cov-report=term-missing:skip-covered"
      - name: test summary
        if: always()
        run: |
          python3 - <<'EOF' >> "$GITHUB_STEP_SUMMARY"
          import os, xml.etree.ElementTree as ET
          p = "reports/junit.xml"
          if not os.path.exists(p):
              print("no junit report"); raise SystemExit
          r = ET.parse(p).getroot(); s = r if r.tag == "testsuite" else r[0]
          print(f"### {s.get('tests')} cases · {s.get('failures')} failed · {s.get('errors')} errors · "
                f"{s.get('skipped')} skipped (T2 debt) · {float(s.get('time')):.1f}s")
          EOF
      - uses: actions/upload-artifact@v4     # [VERIFY current major]
        if: always()
        with:
          name: junit
          path: reports/junit.xml
          if-no-files-found: ignore

  web:
    name: web (lint, types, build)
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - id: detect
        run: |
          if [ -f web/package-lock.json ]; then echo "present=true" >> "$GITHUB_OUTPUT"
          else echo "present=false" >> "$GITHUB_OUTPUT"; echo "No web/package-lock.json: Streamlit path, M2 runs in backend job."; fi
      - if: steps.detect.outputs.present == 'true'
        uses: actions/setup-node@v4          # [VERIFY current major]
        with:
          node-version-file: web/.nvmrc
          cache: npm
          cache-dependency-path: web/package-lock.json
      - if: steps.detect.outputs.present == 'true'
        working-directory: web
        run: npm ci --no-audit --no-fund
      - if: steps.detect.outputs.present == 'true'
        working-directory: web
        run: npm run lint            # eslint config sets react/no-danger: "error"
      - if: steps.detect.outputs.present == 'true'
        working-directory: web
        run: npx tsc --noEmit
      - if: steps.detect.outputs.present == 'true'
        working-directory: web
        run: npm run build

  image:
    name: image boots safe (public, no secrets)
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [backend, web]
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - name: docker build (same Dockerfile the host builds)
        run: docker build -t cod-risk:ci .
      - name: unconfigured container is public, sends off, webhook off (P1 against the real image)
        run: |
          docker run -d --name app -p 8000:8000 -e PORT=8000 cod-risk:ci
          for i in $(seq 1 40); do curl -fsS localhost:8000/api/health >/dev/null 2>&1 && break; sleep 1; done
          curl -fsS localhost:8000/api/health | python3 -c 'import json,sys; d=json.load(sys.stdin); assert d["mode"]=="public" and d["wa_send"] is False and d["webhook"]=="disabled", d; print("safe defaults ok:", d["mode"])'
          curl -fsS -o /dev/null -w "%{http_code}\n" localhost:8000/ | grep -qE "^(200|404)$"
      - name: container logs on failure
        if: failure()
        run: docker logs app || true
```

Notes:
- CI is the backstop, not a required check.
- Targets: the backend job under 3 min, `pytest` under 20 s locally.
- Badge: `![ci](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg?branch=main)`.
- The `image` job requires the Dockerfile to listen on `${PORT:-8000}` and to have `APP_MODE` unset in the image.

## 5. Makefile (Montassar owns; T0)

```make
# Makefile: every command a teammate or CI needs. `make help` lists them.
SHELL         := /bin/bash
.SHELLFLAGS   := -eu -o pipefail -c
.DEFAULT_GOAL := help

VENV        ?= .venv
PY          ?= $(VENV)/bin/python
PIP         := $(PY) -m pip
PYTEST      := $(PY) -m pytest
RUFF        := $(PY) -m ruff
URL         ?= http://localhost:8000
DB          ?= var/app.db
PYTEST_ARGS ?=
export PYTHONPATH := .

# Offline, keyless, deterministic: the ONLY environment tests run under (CI runs this too).
TEST_ENV := APP_MODE=dev LLM_MODE=replay WORKER_ENABLED=false DEMO_MODE=true GEMINI_ENABLED=false \
            GROQ_API_KEY= GEMINI_API_KEY= WA_TOKEN= WA_SEND_ENABLED=false \
            WA_APP_SECRET=test-secret WA_VERIFY_TOKEN=test-verify ADMIN_TOKEN=test-admin

.PHONY: help setup lock run ui ui-build test test-unit lint fmt hygiene check seed demo-reset reset-remote \
        generate train record eval eval-skew bakeoff drill smoke reports-check docker clean

help: ## list targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  %-14s %s\n",$$1,$$2}'

$(VENV)/.installed: requirements.txt requirements-dev.txt constraints.txt
	python3 -m venv $(VENV)
	$(PY) -c 'import sys; assert sys.version_info[:2] == (3, 11), f"need Python 3.11, got {sys.version}"'
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r requirements.txt -r requirements-dev.txt -c constraints.txt
	touch $@

setup: $(VENV)/.installed ## venv + pinned deps (+ web deps if web/ exists)
	@if [ -f web/package-lock.json ]; then cd web && npm ci --no-audit --no-fund; fi

lock: setup ## freeze the full resolved set into constraints.txt (Jesser only; announce in chat)
	$(PIP) freeze --exclude-editable | sort > constraints.txt

run: setup ## API on :8000 (APP_MODE=dev unless set; live LLM if keys are in .env)
	APP_MODE=$${APP_MODE:-dev} $(PY) -m uvicorn app.main:create_app --factory --reload --port 8000

ui: ## dashboard dev server (Vite proxies /api to :8000; Streamlit if no web/)
	@if [ -f web/package.json ]; then cd web && npm run dev; else $(PY) -m streamlit run dashboard/app.py; fi

ui-build: setup ## build web/dist (what FastAPI serves on /)
	cd web && npm run build

test: setup ## full offline suite, no keys, no network (< 20 s)
	$(TEST_ENV) $(PYTEST) -m "not live" $(PYTEST_ARGS)

test-unit: setup ## unit + contract only (< 5 s)
	$(TEST_ENV) $(PYTEST) tests/unit tests/contract -m "not live" $(PYTEST_ARGS)

lint: setup ## ruff lint + format check
	$(RUFF) check .
	$(RUFF) format --check .

fmt: setup ## auto-format + autofix
	$(RUFF) format .
	$(RUFF) check --fix .

hygiene: ## no tracked secrets/DBs, fixture phones allowlisted, clock + SDK import rules
	bash scripts/hygiene.sh

check: hygiene lint test ## THE pre-merge gate (< 60 s). CI runs exactly this.
	@echo "check: green, ok to merge"

seed: setup ## fresh $(DB): schema + catalog + demo_seed + committed replay cache (0 tokens)
	mkdir -p var
	LLM_MODE=replay $(PY) -m scripts.seed --db $(DB) --fresh

demo-reset: setup ## wipe orders/messages/assessments/drafts/events; KEEP catalog + extraction_cache; reseed
	LLM_MODE=replay $(PY) -m scripts.demo_reset --db $(DB)
	@curl -fsS $(URL)/api/health || echo "(API not running: health skipped)"

reset-remote: ## POST /api/admin/reset on URL (needs ADMIN_TOKEN in env)
	@test -n "$${ADMIN_TOKEN:-}" || { echo "set ADMIN_TOKEN"; exit 1; }
	curl -fsS -X POST -H "X-Admin-Token: $$ADMIN_TOKEN" $(URL)/api/admin/reset

data/synthetic/rows.csv: ml/generate.py $(wildcard data/banks/*.yaml)
	$(PY) -m ml.generate --rows 10000 --seed 20260926 --out $@

generate: setup data/synthetic/rows.csv ## 10,000 synthetic rows, seeded, zero LLM calls

train: setup data/synthetic/rows.csv ## monotone XGBoost -> models/classifier.json + manifest + reports/classifier_holdout.json
	$(PY) -m ml.train --rows data/synthetic/rows.csv --seed 20260926

record: setup ## re-record LLM fixtures with the DEV org key (asks first; ~15 calls)
	@read -p "Record fixtures with LIVE Groq/Gemini on the DEV org? [y/N] " a; [ "$$a" = y ]
	LLM_MODE=live $(PY) -m scripts.record_llm_fixtures
	bash scripts/hygiene.sh

eval: setup ## headline eval: frozen prompt, no fallback/cache/cascade -> reports/eval_extraction.json
	LLM_MODE=live WRITE_REPORTS=1 $(PY) -m scripts.eval_extraction \
	  --windows data/eval/windows.jsonl --second-label data/eval/second_label.jsonl \
	  --out reports/eval_extraction.json

eval-skew: setup ## (Should) 40 eval_only synthetic rows through score_order -> reports/eval_skew.json
	LLM_MODE=live WRITE_REPORTS=1 $(PY) -m ml.eval_skew --out reports/eval_skew.json

bakeoff: setup ## (Should, cut before Gemini) qwen challenger on the same windows -> reports/bakeoff.json
	LLM_MODE=live WRITE_REPORTS=1 $(PY) -m scripts.bakeoff --out reports/bakeoff.json

drill: setup ## fallback drill, no keys -> reports/fallback_drill.json
	$(TEST_ENV) WRITE_REPORTS=1 $(PYTEST) tests/e2e/test_fallback_drill.py -q

smoke: setup ## deployed/tunneled URL: health+mode, SPA, try hero, reply, 409 (no key)
	$(PY) -m scripts.smoke $(URL)

reports-check: setup ## reports provenance + README numbers match (SUBMISSION=1 also fails on {{placeholders}})
	$(TEST_ENV) $(PYTEST) tests/reports -q

docker: ## build the image exactly as the host will
	docker build -t cod-risk:local .

clean: ## remove caches and local DBs
	rm -rf .pytest_cache .ruff_cache htmlcov var/*.db var/*.db-wal var/*.db-shm
```

**`scripts/hygiene.sh` (Montassar, T0):**

```bash
#!/usr/bin/env bash
# Fails on anything that must never be committed or that breaks determinism.
set -uo pipefail
fail=0; say(){ printf 'hygiene: %b\n' "$*" >&2; fail=1; }

bad=$(git ls-files | grep -E '(^|/)\.env$|\.db$|\.db-(wal|shm)$|\.sqlite3?$|(^|/)node_modules/|(^|/)web/dist/|(^|/)var/' || true)
[ -n "$bad" ] && say "tracked files that must be ignored:\n$bad"

# key-shaped strings [VERIFY Groq/Gemini/Meta prefixes]
git grep -nIE '(gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{30,}|EAA[A-Za-z0-9]{50,})' -- . ':!scripts/hygiene.sh' \
  && say "key-shaped string in a tracked file"

# phone numbers in fixtures/data/mocks must be allowlisted 21600000001..21600000009
phones=$(git grep -nIoE '216[0-9]{8}' -- tests/fixtures data mocks 2>/dev/null | grep -vE ':2160000000[1-9]$' || true)
[ -n "$phones" ] && say "non-allowlisted phone numbers (run scripts/scrub_fixture.py):\n$phones"

# one clock
git grep -nE 'datetime\.(now|utcnow|today)\(' -- 'app/*.py' 'ml/*.py' ':!app/clock.py' \
  && say "read time through app.clock.Clock, not datetime.now()"

# one LLM entry point; the generator never calls an LLM
git grep -nE '^\s*(import|from)\s+(groq|google\.genai|google\.generativeai)\b' -- 'app/*.py' 'ml/*.py' 'scripts/*.py' \
  ':!app/extraction/clients.py' && say "LLM SDKs are imported only in app/extraction/clients.py"

# no raw HTML injection in the dashboard
git grep -n 'dangerouslySetInnerHTML' -- 'web/src/*' && say "dangerouslySetInnerHTML is banned (#17)"

exit $fail
```

**`scripts/smoke.py URL` (M3) steps.** It uses httpx and a random `X-Visitor-Id`, prints one line per step with timings, and exits 1 on the first failure.
1. `GET /api/health` returns 200. Print mode, model and `live_calls_today/cap`. If the mode is public, assert `wa_send=false` and `webhook=disabled`.
2. `GET /` returns 200 `text/html`.
3. Public: `POST /api/sandbox/try {"fixture_id":"hero"}`. Event/dev: `POST /api/orders/ingest` with the hero text. Then poll `GET /api/orders/{id}` for up to 20 s until `rescore_state == idle` and version 1 has tier `high`.
4. `POST /api/conversations/{cid}/simulate-reply` with the hero v2 text from `data/demo_seed.json`. Poll for up to 20 s until version 2 has tier `low` and a lower `final_score`.
5. Public only: `POST /api/orders/{seeded_hero_id}/rescore` returns 409 `SEEDED_READONLY`.
6. Print `SMOKE PASS <url> <mode> v1=<n> v2=<n> <seconds>s`.

**`pyproject.toml` (tool config only):**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q -ra --strict-markers --durations=5"
markers = ["live: needs real API keys; never in CI (set RUN_LIVE=1)"]

[tool.ruff]
line-length = 100
target-version = "py311"
extend-exclude = ["web", ".venv", "var"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "DTZ"]   # DTZ catches naive datetimes
```

## 6. Requirements and tooling pinning rules

1. **Python 3.11 everywhere:** `.python-version` = `3.11`, Dockerfile `python:3.11-slim`, and `make setup` asserts the version.
2. **`requirements.txt` = direct runtime deps, `==`-pinned** to what `pip install` resolves on 26 Sept. Never type versions from memory. The deps: `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `groq`, `google-genai` [VERIFY package name], `httpx`, `xgboost`, `numpy`, `pandas`, `scikit-learn`, `rapidfuzz`, `pyyaml`, `python-ulid` [VERIFY name]. Add `streamlit` only if Streamlit wins.
3. **`requirements-dev.txt`:** `pytest`, `pytest-cov`, `ruff`, `==`-pinned.
4. **`constraints.txt` pins the transitive set.** `make lock` produces it once at G-seams (10:30) and again at G7 (22:00). CI, Docker and `make setup` all install with `-c constraints.txt`. Only Jesser edits requirements, and only after announcing it in chat. From the Sun 15:30 freeze, dependencies can't change at all.
5. **Model artifact:** `save_model("models/classifier.json")`, never pickle. `models/manifest.json` records `xgboost_version`, `feature_order`, `monotone_constraints`, `data_sha256`, `seed`, `created_at`. U22 checks it.
6. **Web:** `web/.nvmrc` (current Node LTS [VERIFY]), a committed `package-lock.json`, and **`npm ci` only** in CI and Docker. ESLint sets `react/no-danger: "error"`. `tsconfig` sets `"strict": true`.
7. **No pre-commit framework.** `make check` is the hook. `.env.example` lists every variable with an empty value, and settings fail fast with the missing variable's name.
8. **`.gitignore`:** Skeptic's App. C block plus `var/`, `*.db`, `*.db-wal`, `*.db-shm`, `.venv/`, `web/node_modules/`, `web/dist/`, `reports/junit.xml`, `htmlcov/`. **`.dockerignore`:** `tests/`, `.venv/`, `var/`, `web/node_modules/`, `.git/`, `reports/junit.xml`.
9. **Actions pinned to a major** (`@v4`/`@v5`). Check the current majors once [VERIFY] and don't float to `@main`.

## 7. Merge protocol and definition of done

**Merge protocol (Sat and Sun):**
1. One short-lived branch per lane per task (`jesser/sandbox-visibility`), rebased on `main` just before merge. **The PR contains the code and its tests.** A missing test is allowed only as a visible `skip(reason="T2 debt: …")`.
2. The author runs `make check` and gets green (< 60 s). Omar merges, then runs `make check && make seed && make smoke` on `main`.
3. **Contract files:** `contracts.py` (Omar), `api/models.py` + `mocks/*.json` + `schema.sql` (Jesser), `scoring.yaml` (Omar), `ci.yml` + `Makefile` + `conftest.py` (Montassar), `requirements*` + `constraints.txt` (Jesser). A change to any of them needs C1, C2 and C3 green **and** a chat message to the consuming lane before merge.
4. **Red `main` = stop the line.** The author of the last merge fixes it before anyone merges again.
5. **Prompt changes:** any edit bumps `PROMPT_VERSION`, then `make record` for `data/llm_replay/` (C4 enforces), then a full `make eval` rerun if it happens after G3b.
6. **After the Sun 15:30 freeze:** only bug fixes that come with a reproducing test. Tag `v-freeze`, and CI must be green on it before recording.
7. **Mode flips:**
   - Sat 22:00 first public deploy: P1 green plus the CI `image` job green on `main`.
   - Sun 08:00 → `event`: `make smoke URL=<host>` shows `mode=event`.
   - Sun 16:45 → `public`: redeploy, then `make smoke URL=<host>` shows public with sends and webhook off. Tag `submission-v1` only when that is green and CI is green.

**Definition of done: pre-event, Sat 26 Sept**

| Gate | Done means |
|---|---|
| G-seams 10:30 | The 4 seams, `conftest.py`, `Makefile`, `hygiene.sh`, `ci.yml` and `constraints.txt` are on `main`. `make check` is green on all 4 laptops. |
| 14:00 (T0) | U1, U16, U23 and C2 are green on CI. The badge is in the README. |
| G6 18:00 | E1 is green with the real model and both margins ≥ 10. `HERO_V1`/`HERO_V2` are pinned. C3 has been re-run against the frozen mocks. |
| 19:00 | `reports/eval_extraction.json` is committed, and R1-valid if R1 exists yet. U28 and U30 were green before the run. |
| G7 22:00 | The 16 ★ tests are green on CI, and P1 plus the `image` job are green before the public deploy. |

| Lane | Done at 22:00 Sat means |
|---|---|
| **Omar** | The real `score_order` passes C1 on every Must path. U1, U3, U5, U7, U14, U16, U17, E1 and E4 are green. U24, U28, U29, U30, J14 and U12 are merged with their code. `data/llm_replay/` is recorded after G3b. `models/classifier.json` and the manifest are committed. `reports/eval_extraction.json` is committed. If Gemini started, it is either merged with U2/U14/C1[`fallback_provider`] or still on its branch. |
| **Jesser** | `schema.sql`, repo, worker and every `/api` endpoint pass C2, C3, J10, J11 and J12. J15, J19, C4, P2, P3, P4 and P7 are merged with their code, or the sandbox fell back to shared-DB + reseed with that decision written down. `make seed` and `make demo-reset` work. `.env.example` is complete. WhatsApp: J1–J3 plus `reports/whatsapp_e2e.md` 5/5, **or** the G5 "roadmap" decision is recorded. |
| **Montassar** | `conftest.py`, `Makefile`, `hygiene.sh` and `ci.yml` are on `main` by 10:30. M1 is green by 20:00. P1 and P5 are merged. The `image` job is green. `make smoke URL=<hosted>` passes in public mode. The web job (M4) is green for the chosen stack, and that stack decision is recorded. The dashboard renders `mocks/*.json`. |
| **Fedi** | `windows.jsonl` (24) and the banks with `eval_only` tags are in by 14:00, and U23 is green. `injection.yaml` (8), `prefilter.yaml`, `normalize.yaml` and `numbers.yaml` are committed. `templates/outbound.yaml` is in, and J15 is green. The README "Testing & reliability" skeleton (§8) is committed with `<!--r:…-->` markers. |

**Definition of done: event day, Sun 27 Sept**
- **08:30:** `make smoke URL=<hosted>` is green in `event` mode, and the `/api/health` model check is done.
- **End of S1 (11:30):** `make check` is green on every laptop.
- **End of S2 (13:00):** E1 is still green on `main` after the real-worker swap, and no ★ test is red.
- **Sun 14:00:** Gemini is either green (U2 + E3[`fail_groq`]) or `GEMINI_ENABLED=false` with the README line written.
- **End of S3 (15:30):** T2 items #1–#3 (E3, R1, R2) are green, and at least 34 tests pass on CI. `reports/fallback_drill.json` is committed. The README numbers are filled from `reports/`. Tag `v-freeze`.
- **16:45–16:50:** the public flip, then `make smoke` public-green. `SUBMISSION=1 make reports-check` is green (no `{{placeholders}}` left). The badge is green, and the source link opens in incognito.

## 8. README "Testing & reliability" section (Fedi commits the skeleton Sat; numbers are filled only from `reports/`)

```markdown
## Testing & reliability

![ci](https://github.com/{{OWNER}}/{{REPO}}/actions/workflows/ci.yml/badge.svg?branch=main)

**{{N_TESTS}} automated tests ({{N_CASES}} cases) run on every push, with no API keys and no network.**
LLM calls are replayed from recorded responses, so the suite is free, deterministic and takes {{SUITE_SECONDS}} s.
Reproduce: `make setup && make check`. Live measurements are separate commands (`make eval`, `make drill`)
whose outputs are committed in `reports/`.

### What each risk is tested by
| Risk (from our red-team pass) | Guard | Test |
|---|---|---|
| Customer text tries to lower its own score ("ignore instructions…") | The LLM never scores; schema-only output; code computes every number | `test_injection_regression` ({{N_INJ}} variants, FR / Arabizi / Arabic / mixed) |
| Invented evidence shown to the seller | Verbatim-substring check against customer lines only | `test_evidence_drops_unverifiable` |
| Highlight lands on the wrong Arabic characters | Length-preserving normalization + server-built segments | `test_spans_map_to_original_text`, `test_segments_escape_and_align` |
| Old red flags keep the score high after the customer fixes the address | Code-owned `resolve_flags` (only removes, idempotent) | `test_resolve_flags`, `test_hero_loop_golden` (clean and stale model output give identical features) |
| Groq rate limit or outage | gpt-oss-120b → gpt-oss-20b → {{GEMINI_OR_NOT}} → rules; no retries on stage | `test_fallback_chain`, `test_fallback_drill` |
| A judge's click changes what the next judge sees | Seeded orders are read-only; "Try this order" makes your own copy; visitor rows expire after 2 h | `test_seeded_rows_read_only`, `test_visitor_isolation`, `test_try_this_order_zero_llm` |
| The public demo sends a real WhatsApp message | Public mode is the default and forces sends and the webhook off | `test_public_mode_forces_sends_off` + CI boots the real container and checks it |
| Forged or duplicate webhooks | HMAC-SHA256 on the raw body; unique wamid | {{WEBHOOK_TESTS_OR "WhatsApp is on the roadmap; not shipped"}} |
| Customer sends 3 messages in a row | 4 s debounce | `test_debounce` |
| Frontend/backend drift between four people | Frozen response models, mocks validated in CI | `test_mocks_match_api_models` |
| Markup injection into the dashboard | Text segments only, `react/no-danger` lint | `test_segments_escape_and_align`, CI lint |
| Phone numbers sent to the LLM | Masking before every request | `test_mask_phones`, `test_llm_request_has_no_pii` |

### Numbers (each scoped to what it was measured on)
- **Extraction on real dialect text:** `address_level` exact match
  <!--r:eval_extraction.json#metrics.address_exact-->{{X/N}}<!--/r--> on {{N}} windows written by a native speaker
  ({{MIX}} Arabizi / Arabic-script / French / mixed), gpt-oss-120b, prompt `extract-v1` frozen before the run,
  one run, no fallback, no cache. Second labeler agreed on
  <!--r:eval_extraction.json#metrics.second_label_agreement-->{{a/6}}<!--/r--> windows.
  Flag F1 <!--r:eval_extraction.json#metrics.flag_f1-->{{F1}}<!--/r-->; invented quotes dropped
  <!--r:eval_extraction.json#metrics.dropped_quotes-->{{d/q}}<!--/r-->.
- **Hero loop (the demo order):** {{HERO_V1}} (HIGH) → {{HERO_V2}} (LOW) after the customer's reply. The numbers are asserted by
  `test_hero_loop_golden`, both at least 10 points from a tier boundary.
- **Injection:** <!--r:eval_extraction.json#metrics.injection_tier_unchanged-->{{k/8}}<!--/r--> live injection windows did not
  lower the tier; {{8/8}} on recorded outputs in CI.
- **Fallback drill:** primary down → {{path}} ✓ · all LLMs down → rules ✓ · no API errors
  <!--r:fallback_drill.json#metrics.summary-->{{…}}<!--/r-->
- **Training/serving skew (synthetic, unseen phrases, pre-reply):** tier agreement
  <!--r:eval_skew.json#metrics.tier_agreement-->{{N/40}}<!--/r-->  {{or: "not measured in time"}}
- **Classifier:** monotone in address specificity by construction; holdout tier ordering in `reports/classifier_holdout.json`.

### What this does not prove
- The classifier is trained on synthetic data. Its labels come from a formula we wrote (§7.1), so it learns our assumptions, not real refusals.
- {{N}} labeled windows is small, and one person wrote most of them.
- Recorded fixtures prove our code handles those model outputs, not that the model always produces them.
- {{WhatsApp: sandbox only / roadmap}}. {{Gemini fallback: shipped / implemented and tested offline, disabled in the deployed build}}.
- Not tested: {{list of skipped "T2 debt" IDs from the CI summary}}.
```

Slides: one "Testing & reliability" slide with the top 5 rows of the risk→test table, the badge and the headline eval number. Video: the 10-second injection beat (paste the injection live; the tier doesn't drop). It covers Testing and Responsible AI in one shot. No terminal footage.

---

### Unchanged from Round 1 (still correct)
- Findings F4 (repair, don't reject), F5 (declined carries scores forward), F6 (a `path` value for the provider fallback), F7 (index-mapped spans), F10 (the worker runs `process_due` through `asyncio.to_thread`; `WORKER_ENABLED=false` in tests), F11/F14 (`.gitignore` + fixture scrubbing), F15 (one clock), F16 ("code postal"), F17 (templates pass the prefilter), F18 (`.env.example`) and F19 (`/health` makes no chat calls). All of them are now carried by named tests above.
- Test pyramid: unit + contract < 5 s with pure functions, Replay and FrozenClock. Integration and e2e run on a real SQLite file DB, a real `TestClient` and the real XGBoost artifact. Live runs are manual and committed to `reports/`.
- Coverage targets are reported, not enforced: `extraction/`, `scoring/` 90%; `ingress/`, `outbound/prefilter` 85%; api and worker glue 70%; web gets lint, types and build only; scripts and ml are skipped (checked through U22, U27 and the reports).

### [VERIFY] list (carried and new)
1. Current majors for `actions/checkout`, `setup-python`, `setup-node`, `upload-artifact`; current Node LTS for `.nvmrc`.
2. Gemini structured-output dialect and the Python SDK package name (`google-genai`).
3. Meta webhook payload shapes (replace the hand-built fixtures with scrubbed L4 recordings if S-1 passes).
4. Groq 429 body shape; Groq, Gemini and Meta token prefixes for the hygiene scan.
5. Host behaviour: restart on env change, `PORT` injection, whether a restart reseeds.
6. `python-ulid` package name; whether `eslint-config-next`/Vite templates already enable `react/no-danger` (set it explicitly regardless).
