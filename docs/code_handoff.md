# Handoff: `poc/` aligned to the council spec

> **Update, Sun 27 Sept 00:50:** `poc/` was promoted to the repo root (01 §1 tree). Every `poc/<path>` below is now `<path>` at the root, CI runs from the root `.github/`, and the Streamlit UI is `dashboard/app.py` (the `cod-risk-poc` screens on `/api`). `make up` runs the API and the dashboard together. Current state: [`STATUS.md`](../STATUS.md).

Written Sat 26 Sept 2026 (early morning, before the 09:00 kickoff). Canonical spec: `docs/council-spec/`. This
file records what `poc/` now implements, line by line against the spec, where it deviates and why, what is still
open, and what I need from you (keys, Meta values, hosting) before the next phases.

**Bottom line:** the DB-free scoring core, the SQLite backend + worker + `/api`, and a Streamlit fallback UI are
built and match the spec's contracts. 232 offline tests pass, plus 1 strict `xfail`: the ML8 fairness finding in §5.
The whole hero loop runs with zero config and zero LLM calls: *Try this order* → HIGH 87 → simulated reply → LOW 16,
with the reason diff. Nothing has run against a real Groq/Gemini/Meta key yet. That is Phase 5 and needs §7.

---

## 1. How to run

```bash
pip install -r requirements.txt -r requirements-dev.txt    # from the repo root
make check                       # hygiene + ruff + offline tests (no keys, no network)
make up                          # API :8000 + dashboard :8501 together
make demo                        # API only on :8000, public mode, seeded, no keys needed
python -m scripts.smoke http://localhost:8000                        # M3 smoke: health, try, reply, 409
```

Regenerate the ML artifacts (deterministic, byte-identical on rerun):
`python -m ml.generate && python -m ml.train && python -m scripts.warm_cache && make mocks`.

**Promotion to the repo root:** done on 27 Sept (see the note at the top). Still open: reflow code to ruff
line-length 100 (it's 125 here).

---

## 2. Phases

| Phase | Scope | Status | Commit |
|---|---|---|---|
| 0 | Read the full spec (01–09 + SD §3–§8) and audit the old POC | done | — |
| 1 | DB-free core: contracts, ml/, extraction, LLM chain, scoring, outbound (static), train + hero golden | **done** | `9d45c4a` |
| 2 | Persistence, worker, state machine, `/api`, public-mode sandbox, seed + cache | **done** | `89ab4c6` |
| 4 | Tooling: Makefile, hygiene, CI (inactive under poc/), `.env.example`, Dockerfile, smoke, mocks | **done** (Docker unverified: no daemon here) | `66b22be` |
| 3 | UI: Streamlit fallback (06 §1.5) over the API | **done** (React SPA not built; FE0 is Montassar's call) | this commit |
| 5 | Live-key work: probe, prompt iteration, `make record` / `warm_cache --live`, G1/G3 eval, Gemini Stage A | **blocked on §7** | — |
| 6a | **S-1 WhatsApp webhook** (verify, HMAC, dedupe, statuses, type mapping, fail closed) + J1–J6, P7, E2 | **done** offline (J1–J6, P7, E2 green). Live Meta test **not run yet**: the cloud sandbox can't open a tunnel (cloudflared needs TCP/QUIC 7844; localtunnel needs plain HTTP). Run it from a laptop or the host (§3.2) | `af2a7c6`, `f295d11` |
| 6 | Other Should items: S-2 send, S-3 rewrite + judge, S-6 cascade, S-8 feed UI, S-11 text baseline | not started | — |
| 7 | Hosting (Cloudflare, see §8), public flip, video/slides/README numbers, submission | not started | — |

Recommended order from here: **5 → 7 (host the API early) → 6 (S-1 first, since the Meta app exists) → React (if FE0 says so)**.

---

## 3. Line-by-line alignment

Legend: ✅ built and tested · 🟡 built with a stated deviation · ⏳ not built yet (phase) · 🔑 needs a key or human input.

### 3.1 Must items (07 §1)

| # | Spec item | Where in `poc/` | Status |
|---|---|---|---|
| M-1 | Single container: FastAPI serves `/api` + static bundle, SQLite seeded on boot, `/api/health`, admin reset | `app/main.py`, `Dockerfile`, `app/db/seed.py`, `app/api/routes.py` | 🟡 9 seed orders + hero, not 12. Static mount waits for `web/dist`. Docker build not run (no daemon) |
| M-2 | Public mode: `APP_MODE` default public, `X-Visitor-Id`, `sandbox_id`, seeded read-only 409, *Try this order* (0 LLM), 2 h purge, caps → rules | `app/settings.py`, `app/mode.py`, `app/api/commands.py`, `app/db/purge.py`, `app/db/usage.py` | ✅ P1–P5 tests. Visitor cap counts provider calls, not "LLM actions" (stricter) |
| M-3 | Contracts + seams: `contracts.py`, `Clock`, `LLMClient` + Replay/Failing, sync `process_due`, stub scorer, mocks | `app/contracts.py`, `app/clock.py`, `app/llm/client.py`, `app/worker.py`, `app/scoring/stub.py`, `mocks/` | ✅ C2, C3. Additive contract fields are marked `ADDITIVE` |
| M-4 | Paste/CSV ingest → same pipeline | `app/api/commands.py` (`ingest_paste`, `ingest_csv`) → `app/ingress/ingest.py` | ✅ |
| M-5 | Extraction core: 12-field schema, repair, NUM helper, cross-field, defuse, `normalize_with_map`, spans → segments, evidence, tone gate, injection lexicon | `schemas/`, `app/extraction/*`, `ml/textnorm.py`, `app/api/projections.py` | ✅ U1 U3 U5 U5b U7 U8 U12 U13 U26, I-1 I-3 I-4 (+10 false-positive cases) |
| M-6 | Prompt `extract-v1`, few-shots, prefix ≤ 2.8K measured, frozen with sha | `prompts/` (verbatim from 02 §2–3), `prompts/VERSIONS`, `app/llm/prompts.py` refuses mismatched sha | 🔑 Prefix not measured and prompt not iterated: needs a key (Phase 5). FS1–FS8 pass the self-consistency test |
| M-7 | Groq chain 120b → 20b → Gemini → rules, routed by error class, no retries, breaker, deadline, cap in the client | `app/llm/client.py`, `app/llm/groq_backend.py` | 🟡 U14-style tests pass on fakes. The backend is httpx, not the `openai`/`groq` SDK. 🔑 Never called live |
| M-8 | Gemini Stage A (compat endpoint, same gate) | `app/llm/gemini_backend.py`, `app/llm/schema_gemini.py` | 🔑 Code only. Probe and recorded fixture need a key. `GEMINI_ENABLED=false` by default |
| M-9 | Generator: 10k rows, 8k/2k, Bernoulli labels, ≥30% `eval_only`, 40-row eval subset, no LLM imports | `ml/generate.py`, `data/phrase_banks.yaml`, `data/synth_v1.csv` | ✅ lints 1–8, ML1 ML2 ML10. Base rate 0.299. Banks are a **starter draft**: Fedi replaces them |
| M-10 | Monotone XGBoost (6 features), `scoring.yaml`, reasons (FSI/PDI), `resolve_flags`, `choose_template`, `impact.json` | `ml/features.py`, `ml/train.py`, `scoring.yaml`, `app/scoring/*`, `app/outbound/templates.py`, `reports/` | ✅ Gates pass: AUC 0.784 (oracle 0.783), calib MAE 2.4. ❗ ML8 fails, see §5.1 |
| M-11 | Hero golden E1: v1 75–92 HIGH, v2 ≤ 25 LOW, clean = stale features, `tests/golden/hero.json` | `ml/hero.py`, `tests/e2e/test_hero.py`, `tests/golden/hero.json` | ✅ v1 **87.1 → 87 HIGH**, v2 **26.8 → 16 LOW**, Δmodel 60.3, both ≥ 10 from a boundary. ML13 R1/R3/R4 pass |
| M-12 | Versioned rescore loop: schema, repos, endpoints, worker + debounce, simulate-reply, `origin`, `rescore_state`, reason diff, static template | `app/db/schema.sql` (verbatim 01 §3), `app/db/repo.py`, `app/worker.py`, `app/state.py`, `app/api/*` | 🟡 J10 J11 J12-lite, J7, J9 (all 11 rows of §5.2). The template becomes a **draft** that simulate-reply auto-records (01 §5.3), not an immediate outbound insert (J19 wording). See §4 |
| M-13 | Static template + prefilter + human-click Send ("sent (simulated)") | `data/templates/outbound.yaml`, `app/outbound/*`, `send_draft` | ✅ J15 (24 variants incl. no-name), J14 (8 bad drafts, "code postal" passes). Template copy is a **draft** for Fedi |
| M-14 | Frontend: Vite + React + TS master–detail | — | ⏳ Not built. Streamlit fallback built instead (06 §1.5), see Phase 3 |
| M-15 | Eval: G1 24 native windows, G3 8 injection, headline address-level X/N | — | 🔑 Needs Fedi's windows + a key. Offline E4 (8 variants + 4 "not an order" cases) passes on hand-crafted outputs |
| M-16 | Tests: 16-set, keyless CI, badge, README risk table | `tests/` (232), `Makefile`, `poc/.github/workflows/ci.yml` | 🟡 All 16 ★ IDs are covered (§3.3). CI is inactive until promoted. No badge yet |
| M-17 | Submission pack (video, slides, README) | — | ⏳ Phase 7 (Fedi) |
| M-18 | Repo hygiene: gitignore, secret grep, tag | `scripts/hygiene.sh`, `.gitignore` | ✅ hygiene green. Root `.gitignore` already ignores `*.db`, `.claude/` |

### 3.2 Should items

| # | Item | Status |
|---|---|---|
| S-1 | WhatsApp webhook (verify, HMAC, dedupe, statuses, fail closed) | ✅ `app/ingress/whatsapp.py` (pure: signature, verify, payload walk) + `app/api/routes_webhook.py` (GET verify, POST: raw body ≤ 1 MiB → HMAC → 200 `{}` → background task). Mounted only when `settings.webhook_mounted` (04 W-1). Messages go through the one `store_inbound`; wamid dedupe; batch sorted by provider timestamp; `statuses[]` only move `delivery_status` forward on our outbound rows; text → body, location → pin, everything else → `unsupported`; `context.id` → `reply_to`. Sender number only in `customers.phone_e164`. Tests: `tests/integration/test_whatsapp.py` (J1–J6, P7, E2 + W-3/W-5), fixtures `tests/fixtures/whatsapp/`. **Live test:** `APP_MODE=event WEBHOOK_ENABLED=true` + `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `WA_PHONE_NUMBER_ID` → `uvicorn app.main:create_app --factory --port 8000` → `cloudflared tunnel --url http://localhost:8000` → `POST /{app_id}/subscriptions` (app token, `object=whatsapp_business_account`, `fields=messages`, callback `<tunnel>/webhook/whatsapp`) + `POST /{waba_id}/subscribed_apps` → send a message to the test number. Afterwards `DELETE /{app_id}/subscriptions?object=whatsapp_business_account`. Open: an image/audio **alone** (no text yet) leaves the order in `collecting` (01 §5.2 rule 1 `not_order` fires before rule 4) |
| S-2 | WhatsApp send | ⏳ `send_draft` returns 502 for the WhatsApp channel by design until built. S-1's status handler already updates `delivery_status` for outbound rows that carry a wamid |
| S-3 | Rewrite + judge | ⏳ `make_draft` raises if an LLM is passed. Prompts and schemas are committed |
| S-4 | Gemini Stage B | ⏳ |
| S-5 | Second labeler | 🔑 human |
| S-6 | Cascade (ack/pin/decline without LLM) | ⏳ `CASCADE_ENABLED` exists, logic not built |
| S-7 | qwen bake-off | ⏳ 🔑 |
| S-8 | Activity feed | 🟡 `/api/events` + `event_text.py` built. No feed UI |
| S-9 | Snapshot mode | ⏳ |
| S-10 | Tests to 34 | ✅ well past 34 test functions |
| S-11 | Text baseline classifier | ⏳ `scoring.yaml: text_clf` stanza present, `ml/text_clf.py` not built |

### 3.3 Test IDs (05 §1) → where

| ID | File / test | | ID | File / test |
|---|---|---|---|---|
| U1 ★ | `unit/test_extraction.py::test_extraction_schema_matches_pydantic` | | J10 ★ | `integration/test_backend.py::test_debounce_and_append_only_versions` |
| U3 ★ | `unit/test_extraction.py::test_repair_*` | | J11 ★ | same test (v1 row byte-identical; duplicate version raises) |
| U5 ★ | `unit/test_extraction.py::test_evidence_drops_unverifiable` (+ seller-only quote) | | J12 ★ | `test_hero_loop_in_dev` / seed vs try vs paste share one `store_inbound` (full parity test ⏳) |
| U7 ★ | `unit/test_extraction.py::test_spans_map_to_original_text_property` | | E1 ★ | `e2e/test_hero.py` (ranges + pinned golden) |
| U14 ★ | `unit/test_scoring.py::test_primary_*`, `test_provider_down_*`, `test_everything_down_*`, breaker, deadline, cap | | E4 ★ | `e2e/test_injection.py` (4 bases × 2 variants + not-an-order + injected confirmation) |
| U16 ★ | `unit/test_scoring.py::test_tier_boundaries`, `test_action`, `test_confidence_rules` | | M1 ★ | `integration/test_backend.py::test_health_and_safe_defaults` |
| U17 ★ | `unit/test_scoring.py::test_reply_adjustments` | | C1 ★ | covered across paths (llm, fallback_model, fallback_provider, rules, cache, not_order) in `test_scoring.py` + persistence in integration tests |
| C2 ★ | `integration/test_backend.py::test_stub_scorer_satisfies_contract` | | C3 ★ | `test_responses_validate_against_models`, `test_committed_mocks_match_api_models`, no `phone_e164` |
| U24/ML6, ML5/U25, ML7/U26, ML1–3, ML9–11, ML13, U15, U20, U22, U21 | `unit/test_ml.py`, `e2e/test_hero.py` | | P1–P5, P7-lite, E3, E5, J7, J9, M2-lite | `integration/test_backend.py` |
| **ML8** | `unit/test_ml.py::test_fairness_invariant`: **strict xfail**, §5.1 | | L1 L3–L7 | 🔑 live, Phase 5 |

---

## 4. Spec conflicts I found, and what `poc/` does

The spec files disagree in a few places. The README rulings decide where they cover a conflict. Where they don't,
I picked one side and tagged the code. Omar should confirm or flip each at G0.

| # | Conflict | Picked | Why |
|---|---|---|---|
| 1 | Out-of-range quantity: 05 U3 "60 → 50" vs 02 §1b / 08 AC-03.2 "→ null" | null | 08 says U3 was updated per 02 |
| 2 | Cache key: 01 "normalized window" vs 02 §7 "sanitized render, not normalized (F14)" | 02 | LLM-layer area; a cache hit's quotes must be substrings of the current window |
| 3 | Template rule: 03 §7 / SD §8.1 (flag `vague_location` → T_ADDRESS) vs 02 §8.1 `choose_template` (prepay first, then imprecise address) | 02 | Later finding (F17), named in M-10. Same result on the hero |
| 4 | Declined: 01 §2 "scored normally, never None" vs 05 U17 "previous scores carried forward" | 01 | Contract + DDL CHECK |
| 5 | `zone_source`: 03 E1 expects `keyword`, 01 DDL allows only `csv\|gazetteer\|default` | `keyword` in `context_json`, mapped to `gazetteer` in `orders.zone_source` | Satisfies both |
| 6 | Tier-≥-medium template: J19 "writes an outbound message" vs 01 §5.3 "draft; simulate-reply auto-records it" | 01 §5.3 | Canonical architecture; the `[SELLER]` line is still the canonical text |
| 7 | Visitor id missing: 01 "422 VALIDATION_ERROR" vs 04/R4 "400 VISITOR_ID_REQUIRED" | 400 (R4) | README rulings win |
| 8 | Error code spelling `SEEDED_READONLY` (04, R4) vs `SEEDED_READ_ONLY` (01 TS types) | `SEEDED_READ_ONLY` | The TS contract is what the frontend compiles against |
| 9 | Two NUM regexes (03 §5: 1–3 digits, Latin-adjacency; 02 §5: any length) | 03 for the exact guard, 02-style for the prefilter | 03's case table (`Bardo 2000`) |
| 10 | **Bug in 02 §8.1's prefilter regex**: `(?<![^\W\d_])` backtracks into `89DT` → `8`, `10h30` → `0`, `1` | fixed: boundary on any word char | would have rejected valid drafts |
| 11 | 05 Makefile paths (`data/synthetic/rows.csv`, `models/classifier.json`, seed 20260926) vs 01/03 (`data/synth_v1.csv`, `models/risk_xgb_v1.json`, seed 20260927) | 01/03 | ML area + canonical tree |
| 12 | 01 `LLMClient` protocol vs 05 `LLMClient.complete(req)` vs 02 `Backend.complete_json` | 02's Backend + a `ChainClient` exposing 01's `primary` | R10: 01 tree canonical; 02 owns the chain table |
| 13 | Public display name: 01 "Customer #2614" vs 04 "Client #<last 3 of ULID>" | 01 | contract owner |

## 5. Findings and open decisions

1. **ML8 fairness invariant fails for P15 (tablette, 450 TND).** A rural order with an exact address, 0 flags, neutral tone and a new customer scores **36.3** (medium). The spec sim says ≤ 30.8, and the prior gives 29.0. The other 14 products pass (a 349 TND product scores 30.6). The model is not tuned to hide it: the MAE gate passes, and 03 forbids a calibration layer unless that gate fails. **Your call:** (a) accept and move ML8 into the model card as a stated limit (03's cut order allows this), (b) drop P15's price or weight in the catalog, or (c) add more rural/exact/high-price mass to the generator. Leaning toward (a).
2. **Seed cache and hero fixtures are hand-written, not recorded.** `data/seed/extraction_cache.jsonl` carries `model = "hand-crafted (not an LLM output …)"`, and the UI shows that string next to the path chip. Replace it with `python -m scripts.warm_cache --live` on the **dev** key after the prompt freeze (G3b), then `make mocks`.
3. **Darija/Arabizi content is a draft by a non-native writer:** phrase banks, catalog aliases, outbound templates and the 9 seed conversations. Fedi must check or replace all of it. A bank edit changes only text columns (ML1), so the model and hero numbers don't move.
4. **The T_ADDRESS hero template now asks exactly one question.** 03 §10's placeholder had two `?` and would fail the prefilter's `question_count`.
5. **Bug found and fixed in Phase 3:** the worker passed every slot to the prefilter, so T_ADDRESS drafts were blocked (`slot_missing:price_tnd`). Now only the slots the chosen template uses are checked, and a test asserts static drafts are never blocked. The Streamlit v2 view after the reply wasn't re-screenshotted after the fix; the API tests and smoke cover the loop.
6. `E3 fail_primary` ends in `needs_review` + an `error` event, not `fallback_model`: no recorded 20b fixture exists for a new window. It completes once Phase 5 records fixtures.
7. The 01 §1 `.gitignore` asks to ignore `web/public/snapshot/*.json`, `var/`, etc. The root `.gitignore` covers `*.db` and `.claude/`; `poc/.gitignore` covers `var/` and caches.

## 6. Deviations (intentional, tagged in code)

- LLM backends use **httpx**, not the `openai` (02) or `groq` (05) SDK. They speak the same HTTP API with one less dependency. Hygiene now bans all provider SDK imports.
- `app/extraction/injection.py`, `app/api/commands.py` and `app/api/errors.py` are additive modules. `app/api/routes.py` is one file instead of six `routes_*.py`: split it by owner on promotion.
- `ScoringConfig` also loads `data/phrase_banks.yaml` (for `rules_v1`). It's not in `config_hash`, per 01 §2.
- Contract additions: `PriorAssessment.points/confirmation`, `AssessmentRecord.injection_suspected/points`, `ScoreResult.injection_suspected`, confidence codes `injection_suspected`, `imputed_inputs`. Per-feature points are stored in `context_json.points` so the next version can build `reason_diff`.
- Seed: 9 conversations (hero + 8), not 12 + hero.

---

## 7. What I need from you

**Never paste a key, token or secret into this chat.** Add each one in this cloud environment's settings instead:
title bar → cloud environment menu → **Edit** → API credentials / environment variables. A new session picks them up.
I'll read the variable names below.

### 7.1 LLM keys (Phase 5)

| Variable | What | Used for |
|---|---|---|
| `GROQ_API_KEY` | Groq key on your **dev** org | probe (V3), prompt iteration, `warm_cache --live`, G1/G3 eval, `record` |
| `GEMINI_API_KEY` + `GEMINI_MODEL` | Google AI Studio key + a free Flash-class model id | M-8 probe + one recorded fixture |
| `KEY_PUBLIC`, `KEY_EVENT` | two more Groq keys on teammates' orgs (04 §2.1) | set only on the **host**, not here |
| `ADMIN_TOKEN` | any random string ≥ 24 chars | `/api/admin/reset` (host only) |

Also needed from people: Fedi's G1 windows (24), phrase banks, templates, hero wording and product name. For S-5 (second labeler), confirm who reads Darija natively.

### 7.2 Meta app (you created it): setup steps for S-1/S-2

All of this is **[VERIFY]** against the current Meta console. The webhook code (S-1) is not built yet (Phase 6), so
these values are needed only when that phase starts. Until then, keep `APP_MODE=public`, which never mounts the
webhook.

1. **Add the WhatsApp product** to the app (developers.facebook.com → your app → Add product → WhatsApp → Set up). Meta gives you a **test phone number**, its **Phone number ID** and a **WhatsApp Business Account ID**.
2. **Register recipient phones:** WhatsApp → API Setup → "To" → add each teammate's number and confirm the code. The test number can only message pre-registered numbers.
3. **Permanent token:** Business Settings → Users → **System users** → add an admin system user → assign the app and the WhatsApp account with full control → **Generate token** with `whatsapp_business_messaging` and `whatsapp_business_management`. The 24 h token on the API Setup page expires, so don't use it.
4. **App secret:** App settings → Basic → **App secret** (≥ 16 chars; used for the `X-Hub-Signature-256` HMAC).
5. **Verify token:** make up a random string ≥ 24 chars. You'll paste it into the Meta webhook form later.
6. **Webhook (only once the host URL and S-1 exist):** WhatsApp → Configuration → Callback URL `https://<host>/webhook/whatsapp`, Verify token = step 5, then subscribe to the **`messages`** field.

Env variable names for those values (host secrets, and here for dev testing): `WA_TOKEN` (step 3),
`WA_APP_SECRET` (4), `WA_VERIFY_TOKEN` (5), `WA_PHONE_NUMBER_ID` (1), `WA_API_VERSION` (the Graph version shown in
the console, e.g. `v2x.0` [VERIFY]). Then set `WEBHOOK_ENABLED=true`, `WA_SEND_ENABLED=true` and `APP_MODE=event`
only for the event window (04 §3.1 runbook).

---

## 8. Hosting on Cloudflare: what fits and what doesn't

The spec's topology (01 §6) is **one long-running container**: FastAPI + a 1 s worker loop + a SQLite file rebuilt on
boot + XGBoost (native code). That shapes the Cloudflare options:

| Cloudflare product | Fits? | Notes |
|---|---|---|
| **Pages** | only the static UI | Good for the React `web/dist` bundle (or the S-9 snapshot mirror). It can't run the API |
| **Workers (incl. Python Workers)** | ✗ for the API | No long-running loop, no local SQLite file, no native XGBoost wheels [VERIFY] |
| **Containers** (runs our Docker image) | ✓ likely | Closest match to M-1. **[VERIFY]:** plan/pricing (appears to need Workers Paid), idle sleep and cold start, ephemeral disk (fine: we reseed on boot), how env secrets and restart-on-env-change work (the mode-flip runbook depends on it), one instance only (`--workers 1`, SQLite) |
| **Tunnel** | fallback | Exposes a laptop or another host behind a Cloudflare hostname. The spec's event-day fallback (01 §6.1) |

**Proposal:** run the API container on Cloudflare Containers if the plan allows. Otherwise run it on another container host from 01 §6.1 (Render / HF Spaces / Fly / Railway / Koyeb) with Cloudflare DNS in front. Serve the React bundle from the same container, per the spec, or from Pages if the frontend ships separately. The Streamlit fallback is a second deployable (06 §1.5) and can't run on Pages.
Before deploying: the Dockerfile needs its Node build stage once `web/` exists, and it must pass the CI `image` job (boots public, sends off, webhook off). Run `python -m scripts.smoke https://<host>` after every deploy and mode flip.

---

## 9. Next session checklist

1. Settle §5.1 (ML8) and the §4 conflicts at G0, then edit this file.
2. Add `GROQ_API_KEY` (dev org) to the environment (§7.1). Then run the probe, measure the prompt prefix, iterate on 5 dev windows, freeze `extract-v1` (update `prompts/VERSIONS`), `warm_cache --live`, `make mocks`, then re-run `ml.train` to re-pin `hero.json` if anything moved.
3. Pick the host (§8), deploy public mode, run `make smoke URL=…`.
4. Build S-1 against the Meta values (§7.2), tests J1–J6, then the rehearsal flip.
5. Promote lanes from `poc/` to the root as owners take them over.
