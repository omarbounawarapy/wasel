# User stories + acceptance contract

> Conductor synthesis. Scope and IDs come from [07 §1](07-scope-schedule-delivery.md) (M-/S- items). Test IDs, assertions and owners come from [05 §1](05-testing-ci.md). Deadlines are the gates in [07 §3](07-scope-schedule-delivery.md). ★ = in the 16-test floor due Sat 22:00 (G7). A story is **done** when every criterion's test is green in `make check` on `main` (or the live report is committed), not when the code merges.

## Quality gates

| Gate | Command | Required | Owner |
|---|---|---|---|
| Lint + format | `make lint` (ruff) | yes, every merge | author |
| Offline tests | `make test` (pytest, no API keys, `LLM_MODE=replay`, FrozenClock) | yes, every merge | author |
| Hygiene | `make hygiene` (secret/key regex, allowlisted phones, one clock, one LLM entry point, no raw-HTML injection) | yes, every merge | Montassar |
| Merge gate | `make check` = lint + test + hygiene, < 60 s | yes | Omar merges only on green |
| Web | CI `web` job: lint (`react/no-danger: error`), `tsc --noEmit`, `vite build` | yes once `web/` exists | Montassar |
| Deploy smoke | `make smoke URL=<hosted>` (M3) | Sat 20:00, Sun 08:30, 15:30, 16:50 | Montassar |

## Stories

### US-01 — Seller sees orders ranked by refusal risk  ·  M-12, M-14  ·  Jesser, Montassar
As a seller's ops person, I want every order in one queue sorted by risk, with a tier, score, change since last version and recommended action, so I spend confirmation effort where refusals are likely.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-01.1 | `GET /api/orders` returns orders sorted by `final_score` desc with `tier`, `final_score`, `delta`, `action`, `reason_short`, `status`, `path` | contract | C3 ★ (mocks ↔ Pydantic models), J12 ★ | G2 12:00 / G6 |
| AC-01.2 | The queue renders from mocks, then from the live API, on the hosted URL | manual-check | G4 checklist (07 §3) → M3 smoke | G4 16:00 / 20:00 |
| AC-01.3 | Seeded orders render with no LLM call (pre-computed assessments + extraction cache) | e2e | E5, P4 | Sun (T2) / G7 |

### US-02 — Seller sees *why*, in the customer's own words  ·  M-5, M-10, M-14  ·  Omar, Montassar
As a seller, I want the risky phrases highlighted inside the customer's message and a plain-language reason, so I trust (or overrule) the score.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-02.1 | Every flag's evidence is a verbatim substring of a `[CUSTOMER]` message; unverifiable flags are dropped and counted | unit | U5 ★ | G7 |
| AC-02.2 | Spans map to the **original** text (Arabic diacritics/tatweel, casefold, emoji) and are returned as server-built `segments` | unit + property | U7 ★ | G7 |
| AC-02.3 | Customer text containing `<script>`, `<img onerror>`, `</mark>` or Markdown renders as text | unit + lint | M2, `react/no-danger` in CI | Sun (T2) / G4 |
| AC-02.4 | Reason string is deterministic from the top feature contributions, with quotes wrapped in FSI/PDI | unit | U18 | Sun (T2) |

### US-03 — Extraction reads Arabizi, Arabic-script Darija and French reliably  ·  M-5, M-6  ·  Omar (Fedi: language)
As the system, I need structured, verifiable signals from messy dialect text, so the classifier gets consistent inputs.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-03.1 | Hand-written `schemas/order_extraction_v1.json` (12 fields, order as specified) and the Pydantic mirror agree on fields and enums | unit | U1 ★ | T0 14:00 |
| AC-03.2 | Out-of-range or overlong outputs are repaired (clamped/truncated/nulled), never rejected | unit | U3 ★ (cases updated per 02 §1b: out-of-range quantity → null, long strings truncated) | G7 |
| AC-03.3 | Cross-field rules: `exact` needs a building/number cue (shared Arabizi-digit helper, so "9rib" is not a number); pin forces `exact`; `confirmation` resets without a seller question | unit | U8, U25 | Sun (T2) |
| AC-03.4 | Headline eval: address-level exact match X/N on native-written windows, one frozen-prompt run, committed with provenance | metric (live) | L1 `make eval` → `reports/eval_extraction.json`; R1 | Eval 19:00 |

### US-04 — The score comes from a monotone model on 6 features  ·  M-9, M-10  ·  Omar
As a judge or seller, I want the risk score to behave sensibly (a better address never raises risk) and to be reproducible.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-04.1 | Generator is offline (imports no LLM SDK) and deterministic for a seed | unit | U27 | Sun (T2), import check in hygiene G7 |
| AC-04.2 | Feature mapping matches the 6-feature contract | unit | U15 | Sun (T2) |
| AC-04.3 | The classifier is monotone in every constrained feature | unit | U20 | Sun (T2) |
| AC-04.4 | Tier, action and confidence follow `scoring.yaml` (35/65 tiers, 10-point boundary margin) | unit (param) | U16 ★, U19 | T0 14:00 |
| AC-04.5 | The model artifact matches its manifest/card | unit | U22 | Sun (T2) |

### US-05 — Confirmation question + reply rescoring: HIGH → LOW  ·  M-11, M-12, M-13  ·  Omar, Jesser (Fedi: copy)
As a seller, I want the system to ask the right question and rescore the same order when the customer answers, so a clarified order ships and a doubtful one gets attention.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-05.1 | **Hero golden**: v1 model 75–92, HIGH, \|final − 65\| ≥ 10; v2 final ≤ 25, LOW; clean and stale v2 windows give identical features; writes `tests/golden/hero.json` | e2e | E1 ★ | **G6 18:00** |
| AC-05.2 | A static template (rule-chosen) is stored as the seller message with `template_id` + `canonical_text` whenever tier ≥ medium; `[SELLER]` context uses canonical text only | integration | J19 | G7 |
| AC-05.3 | Resolved flags are removed (never added), idempotently; `vague_location` drops only at `exact` | unit (param + property) | U24 | G7 |
| AC-05.4 | Reply adjustments (confirmed ×0.6, declined, reschedule, ambiguous) apply as configured | unit (param) | U17 ★ | G7 |
| AC-05.5 | Bursts are debounced into one rescore; assessments are append-only versions | integration | J10 ★, J11 ★ | G7 |
| AC-05.6 | Every static template passes the prefilter; bad drafts are blocked | unit | J15, J14 | G7 |

### US-06 — The demo never hard-fails on the LLM  ·  M-7, M-8  ·  Omar
As the team, we need scoring to continue through rate limits and outages, with the path shown on every score.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-06.1 | Error-class routing: 429 → next Groq model (if per-model buckets) → Gemini → rules; timeout/5xx → Gemini → rules; no retries | unit (param) | U14 ★ (Gemini branch lands with M-8) | G7 / G-Gem 20:00 |
| AC-06.2 | Each path persists with its `path` value (`llm`, `fallback_model`, `fallback_provider`, `rules`, `cascade_cache`, …) | contract (param) | C1 ★ | G2 12:00 → G7 |
| AC-06.3 | Daily LLM cap enforced in the client; at the cap → rules path + banner, never a 429 | unit + api | U29, P6 | G7 / Sun |
| AC-06.4 | Eval mode is single-shot (no fallback, cache or cascade) | unit | U30 | before the 19:00 eval |
| AC-06.5 | Fallback drill (`fail_primary`, `fail_all`, `fail_groq`) produces `reports/fallback_drill.json` | e2e | E3 | Sun (T2 #1) |

### US-07 — Customer text can't steer the score or the outbound message  ·  M-5, M-13, 04 §5  ·  Omar
As a seller, I need prompt injection in customer messages to be harmless.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-07.1 | 8 injection variants (4 base × 2 languages) leave tier unchanged vs. the clean window; delimiter spoofing is defused (length-preserving) | e2e (param) | E4 ★ | G7 (floor 4 variants) |
| AC-07.2 | No phone number, name or customer id reaches an LLM request | unit | U13, U12 | Sun (T2) / G7 |
| AC-07.3 | Eval sets and few-shots share no phrases with training banks | unit | U28 | G3b 16:30 |
| AC-07.4 | An injection can't hide an order: a real order the model marks `is_order=false` (or any lexicon hit) still gets an assessment row in `needs_review` with the injection chip; zero-width/bidi characters can't split a lexicon phrase or reorder the dashboard | unit + e2e | U5b, E4, I-1 property test | G7 |

### US-08 — A judge opens the hosted link days later and can try the whole loop safely  ·  M-1, M-2  ·  Jesser, Montassar
As a judge, I want the prototype to work without the team and without affecting anyone else, and I must not be able to send a real message.

| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-08.1 | `/api/health` reports mode, `wa_send`, webhook, providers, `live_calls_today/cap`, `GIT_SHA`; public mode is the default and forces sends off, webhook unmounted | api (param) | M1 ★, P1 | G7 (P1 before the first public deploy) |
| AC-08.2 | Seeded rows are read-only in public mode (409 `SEEDED_READONLY`); writes without a visitor id → 400 | api | P2 | G7 |
| AC-08.3 | Visitors see seeded ∪ own sandbox only; "Try this order" clones with zero LLM calls; sandboxes purge after 2 h | api | P3, P4, P5 | G7 |
| AC-08.4 | Booting in public reseeds and wipes real rows; public display is pseudonymized | integration | P9, P10 | Sun (T2) |
| AC-08.5 | The SPA is served at `/` from the same origin; hosted smoke passes | e2e / live | M5, M3 | Sun (T2) / Sat 20:00 |

### US-09 — Every ingress path goes through one pipeline  ·  M-4, M-12  ·  Jesser
| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-09.1 | Paste, CSV, seed, simulate-reply (and WhatsApp) produce identical downstream rows | integration | J12 ★ | G7 |
| AC-09.2 | Stub scorer satisfies the contract end-to-end from hour one | contract | C2 ★ | T0 14:00 |
| AC-09.3 | Order boundary rules, extraction window and state transitions match 01 §5 | unit (table) | J7, J8, J9 | Sun (T2) |

### US-10 (Should S-1/S-2) — Orders arrive from WhatsApp  ·  Jesser (Montassar: Meta admin)
| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-10.1 | GET verify handshake; HMAC over the raw body; empty secret → route not mounted | api | J1, J2, P7 | G5 17:30 |
| AC-10.2 | Duplicate wamid ignored; status receipts never create messages; out-of-order batches sorted; types mapped | api (param) | J3, J4, J5, J6 | G5 |
| AC-10.3 | WhatsApp hero matches the paste hero | e2e | E2 | Sun |
| AC-10.4 | Real phone → queue row ×5 | live | L4 | G5 |

### US-11 (Should S-3) — Register-matched rewrite, gated by a judge  ·  Omar
| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-11.1 | Approval only when every judge check passes (not on the verdict alone); fails closed | unit (param) | J16 | D4 Sun 13:00 |
| AC-11.2 | Loop guard (≤ 2 auto messages, never reply to own outbound); demo mode requires a human click | unit | J17, J18 | D4 |

### US-12 — Judges see honest evidence of quality  ·  M-15, M-16, M-17  ·  Omar, Montassar, Fedi
| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-12.1 | Every report carries provenance (prompt version/sha, model, date, N, labelers) | unit | R1 | Sun (T2 #2) |
| AC-12.2 | Numbers in the README match `reports/*.json` | unit | R2 | Sun (T2 #3) |
| AC-12.3 | CI badge green on `main`; README "Testing & reliability" lists risk → test → result and "What this does not prove" | manual-check | 05 §8 template | G7 22:00 |
| AC-12.4 | Video, slides and README show only numbers from `hero.json` / `reports/`; every fallback or simulation is captioned | manual-check | Fedi's checklist (07 §6) | D6 16:40 |

### US-13 — The repo is safe to make public  ·  M-18  ·  Montassar, Omar
| AC | Criterion | Method | Verified by | Due |
|---|---|---|---|---|
| AC-13.1 | No DB, `.env*`, media, build output or `.claude/` tracked (`.gitignore` block applied) | build-output | `git check-ignore` + hygiene | done now; re-check G7 |
| AC-13.2 | Secret + phone scan over full history is clean before the visibility flip | manual-check | 04 §6.2 | G7 22:00, Sun 16:45 |

## Verification summary

| Tier | Due | Tests |
|---|---|---|
| T0 | Sat 14:00 | U1 ★ · U16 ★ · U23 · C2 ★ (+ seams, CI badge) |
| T1 floor (16) | Sat 22:00 | U1 U3 U5 U7 U14 U16 U17 C1 C2 C3 J10 J11 J12 E1 E4 M1 |
| T1+ (lands with its Must code) | Sat 22:00 | U24 U28 U30 U29 J14 J15 J19 C4 P1–P5 P7 U12 M3 M4 |
| T2 | Sun 15:30 (target 34 total) | E3 R1 R2 M2 U13 U8 U26 U27 U22 U20 U19 U4 U25 J9 J8 J7 E5 P6 P9 P10 U15 U18 U10 M5 |
| Gated (with their Should) | per gate | J1–J6 E2 (S-1) · J16–J18 (S-3) · U2 (S-4) · U9 (S-6) · J13 (C-1) |
| Live (reports, not CI) | per gate | L1 eval · L3 key checks · L4 WhatsApp · L5 record · L6 bake-off (S-7) · L7 skew |

Progress: 0 / 13 stories verified (no code yet).
