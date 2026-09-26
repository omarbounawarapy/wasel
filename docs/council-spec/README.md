# COD Risk — Council Build Spec

**Status:** build-ready as of Sat 26 Sept 2026, ~03:00 Tunis. **No application code exists yet.** This folder is what the team codes from.
**Where it conflicts** with `PRD.md`, `SYSTEM_DESIGN.md`, `execution_plan.md`, `hackathon_playbook.md` or `handoff.md`, **this folder wins**, and the rulings below win over the individual spec files.

Produced by a 7-member design council (agentic-council plugin, standard mode, run sequentially): Architect, Oracle, Alchemist, Skeptic, Craftsman, Strategist, Advocate. They ran 3 rounds: position → challenge (4 tension pairs) → converge. The raw deliberation is kept outside this repo because it references personal files, and this repo goes public for the submission.

---

## 1. Read this first — by person

| Person | Read in this order | Your first deliverable |
|---|---|---|
| **Omar** (lead, AI/ML, merges) | this README → [02 LLM layer](02-llm-layer.md) → [03 Data + ML](03-data-ml.md) → [01 §2 contracts](01-architecture-contracts.md) → [05 test IDs you own](05-testing-ci.md) | `app/contracts.py` + seams merged by **10:30 (G-seams)**; 09:15 doc cleanup ([07 §8](07-scope-schedule-delivery.md)) |
| **Jesser** (backend + WhatsApp code) | this README → [01 Architecture](01-architecture-contracts.md) (schema, API, state machine, modes) → [04 §2–4 public mode + webhook](04-security-public-mode.md) → [05 tests you own](05-testing-ci.md) | `schema.sql`, `repo.py`, stub scorer + `process_due`, C2 green by **T0 14:00** |
| **Montassar** (frontend + infra + CI) | this README → [06 Frontend](06-frontend-ux.md) → [01 §6 deploy + modes](01-architecture-contracts.md) → [05 §4–5 CI + Makefile](05-testing-ci.md) → [04 §3 runbook](04-security-public-mode.md) | Host picked + hello-world live by **G1 12:00**; queue on mocks on the hosted URL by **G4 16:00** |
| **Fedi** (story, language, delivery, scope gate) | [`FEDI.md`](../../FEDI.md) only: his full plan, start to finish | see `FEDI.md` §0 |

## 2. The spec files

| File | Lens | Holds |
|---|---|---|
| [01-architecture-contracts.md](01-architecture-contracts.md) | Architect | repo tree + owners, `contracts.py`, full SQLite DDL, every API endpoint with TS types and error codes, state machine, deploy topology, `APP_MODE` switches + runbook, config split |
| [02-llm-layer.md](02-llm-layer.md) | Oracle | 12-field `order_extraction_v1` JSON Schema + Pydantic repair, full system prompt, few-shots, window/sanitize/phone masking, evidence index map → spans, `LLMClient` + provider chain + Gemini adapter, cascade + cache key, outbound templates/prefilter/rewrite/judge, eval protocol + README sentence |
| [03-data-ml.md](03-data-ml.md) | Alchemist | generator (10,000 rows, phrase-bank format, `eval_only`), `S`/`p_true`/Bernoulli label, 6-feature contract, `resolve_flags()`, Arabizi-digit helper, XGBoost config, full `scoring.yaml`, reason strings, simulated ROI, hero fixture + golden assertions, ML tests |
| [04-security-public-mode.md](04-security-public-mode.md) | Skeptic | threat/failure table, public-mode rules + caps + banner copy, mode-switch runbook + kill switches, webhook and injection acceptance criteria, `.gitignore` (applied), pre-submission checklist, Responsible-AI statement |
| [05-testing-ci.md](05-testing-ci.md) | Craftsman | test inventory (ID, assertion, owner, tier, risk evidenced), seams, fixtures, CI workflow YAML, Makefile, pinning rules, merge protocol + definition of done, README "Testing & reliability" template |
| [06-frontend-ux.md](06-frontend-ux.md) | Advocate | stack + gate + Streamlit fallback, master–detail screen spec with every state, segments/RTL rendering, paste/try/simulate UI, copy table, frozen mocks in full |
| [07-scope-schedule-delivery.md](07-scope-schedule-delivery.md) | Strategist | MoSCoW (M-1…M-18, S-1…S-10), hour budgets per person Sat + Sun, go/no-go gates, 90-s video shot list, 6-slide outline, submission checklist, award text, line-by-line doc cleanup |
| [08-user-stories-acceptance.md](08-user-stories-acceptance.md) | Conductor | user stories with acceptance criteria, each mapped to its verifying test, owner and deadline (the acceptance contract) |
| [09-gate-checklists.md](09-gate-checklists.md) | Conductor (added after the council) | one tick-box checklist per person per gate, Sat FE0 → Sun D7, with the "if it fails" action, plus four open decisions to settle at G0 |

## 3. Ratings

| Member | Round 1 (design as found) | Round 3 (after council resolutions) | Biggest issue found |
|---|---|---|---|
| Architect | 6 | 8 | Contracts named but never written; prototype dies with the laptop tunnel |
| Oracle | 6.5 | 8 | Highlight offsets computed on normalized text; hero-path bugs (Arabizi digits, stale flags) |
| Alchemist | 5 | 8 | "HIGH 78 → LOW 31" unreachable under the old label formula; 4 of 9 features dead |
| Skeptic | 6 | 8 | Public URL = open write API, budget burn, real WhatsApp sends; second-hop injection via `[SELLER]` |
| Craftsman | 4 | 7.5 | No test plan, no CI, no merge gate for a 15-point criterion |
| Strategist | 6 | 8 | Plan aimed at a live stage that doesn't exist; judges get a dead link |
| Advocate | 5 | 8 | No coordinate system for evidence spans; no "rescoring" state; UI had no layout or states |
| **Average** | **5.5** | **7.9** | |

What keeps it below 9: Saturday has almost no slack for Omar, Jesser and Montassar. Several external facts are still [VERIFY], mainly host restart/sleep behaviour, Gemini's JSON-mode parameters and Groq's per-model vs per-org rate buckets. And real LLM extraction quality stays unknown until the 19:00 eval.

## 4. Design summary

**What we build:** a hosted web app that scores Tunisian cash-on-delivery orders for refusal risk from messy Arabizi / Arabic-script Darija / French chat text. It explains the score with the customer's own words highlighted, sends a rule-chosen confirmation message, and rescores the same order when the customer replies. The demo moment is HIGH → LOW with a reason diff.

**Shape (unchanged from SYSTEM_DESIGN, now specified):**
- One ingestion pipeline (paste, "Try this order", simulate-reply, WhatsApp) → store message → debounced rescore.
- The LLM only classifies or quotes (strict schema); every quote is verified against the original text; code owns every number.
- Monotone XGBoost on 6 features; `scoring.yaml` holds every tunable; assessments are versioned and append-only.

**What the council changed:**
1. **Topology.** One hosted container: FastAPI serves `/api/*` and the static React bundle at `/`, SQLite is seeded on boot. It is the judges' prototype after the event and the WhatsApp webhook target on event day. The laptop tunnel is dev-only.
2. **Public mode is the default** (`APP_MODE=public`): webhook unmounted, sends forced off, WA secrets absent. Each visitor gets a sandbox (`X-Visitor-Id` → `sandbox_id`), seeded rows are read-only, and "Try this order" clones a seeded order with zero LLM calls. Rows purge after 2 h, and LLM caps fall back to the rules path with a banner, never a 429.
3. **Contracts first.** Typed `contracts.py`, Pydantic API models as the single source of the JSON shape, and mocks validated against them (C3). Seams: `Clock`, `LLMClient` with replay/fail modes, sync `process_due(now)`.
4. **Evidence spans.** Normalize per message with an index map back to the original. The server returns ready-split `segments`, so the frontend does no offset math.
5. **Labels.** Simulated binary outcomes `refused ~ Bernoulli(sigmoid((S−43)/12))` on 10,000 template-rendered rows (zero LLM calls), `binary:logistic` XGBoost with monotone constraints. The hero numbers come only from `tests/golden/hero.json`.
6. **Reply loop that actually works.** A static template is inserted as the seller's question whenever tier ≥ medium. Prompt rule 5 is the first pass, then `resolve_flags()` removes flags the reply resolved (it never adds any). `[SELLER]` context is always the canonical template text, never LLM output.
7. **Gemini** (your decision): cross-provider extraction fallback in JSON mode, through the same repair → Pydantic → evidence gate as Groq.
8. **Outbound on Saturday:** static template + deterministic prefilter + human click. LLM rewrite + judge is a Sunday Should behind `DRAFT_LLM`, and fails closed.
9. **Testing is funded:** "done = code + its tests green in `make check`" (< 60 s), keyless CI with a badge, 16 tests minimum by Sat 22:00, target 34 by Sun 15:30. Every README number is traced to `reports/*.json`.
10. **Delivery is a recorded video**, not a stage. There is a safety take Sat night, disclosures go in captions and per-score `path` badges, and all links pass an incognito audit before a 17:10 submission.

## 5. Tension resolutions (Round 2)

| Tension | Agents | Resolution | Reasoning |
|---|---|---|---|
| Visitor isolation on the public URL | Skeptic ↔ Architect | Nullable `sandbox_id` on customers/conversations/orders; unsigned `X-Visitor-Id`; seeded rows read-only (409); "Try this order" = seed-loader replay (cache hit); 2 h purge | A shared DB fails even with honest judges: the first judge to trigger the reply completes the hero for everyone after. A signed-cookie sandbox cost more hours than it bought |
| One container: WhatsApp target and public prototype | Skeptic ↔ Architect | `APP_MODE` defaults to `public` (sends off, webhook unmounted, WA token absent); `event` only Sun 08:00–16:45; flip back reseeds and wipes real rows | Judges must never be able to push a real WhatsApp message to a teammate's phone |
| LLM-layer scope vs hours | Oracle ↔ Strategist | Must: hero fixes, prompts, Groq chain, cache, daily cap, 24-window eval, 8-variant injection suite, Gemini Stage A. Should: cascade, rewrite + judge, Gemini Stage B, qwen bake-off, second labeler | Quality of AI (20) and RAI (10) are earned by correctness and a measured number, not by more model calls |
| Tests vs hours | Craftsman ↔ Strategist | Each author tests their own code; Montassar owns harness + CI; case data comes from `FEDI.md`. 16-set by 22:00, 34 by Sun 15:30 | Testing (15) is judged only via repo, README and video; the 16-set covers every High red-team row |
| Stale flags after a reply | Alchemist ↔ Oracle | Prompt rule 5 first; `resolve_flags()` after the evidence check and exact guard, removal-only and idempotent; `vague_location` drops only at `exact` | Code owns the final flag set; golden test proves clean and stale windows give identical features |
| Schema vs feature contract | Alchemist ↔ Oracle | 12 fields: `+tone_evidence` before `tone`, `−has_landmark`, `−has_building_or_apt`; 6 model features; one shared Arabizi-digit helper | Every extracted field must earn its tokens: a feature, a reason string, confidence, UI or routing |

## 6. Conductor rulings

These settle the few places where the Round 3 files still disagree. **They override the spec files.**

| # | Topic | Ruling | Overrides |
|---|---|---|---|
| R1 | Headline eval number | **Address-level exact match X/N** on the native-written windows (`FEDI.md` F3) (target N = 24, floor 10), `gpt-oss-120b`, prompt `extract-v1` frozen at G3b, one run with no fallback, cache or cascade. Secondary: synthetic tier agreement N/40 (skew check). Second labeler on 6 windows is Should (S-5) | 03 §12 (tier agreement as headline) |
| R2 | Gemini timing | Stage A built **Sat 19:00–20:00** after G6, merged only with its tests (U14 Gemini branch, C1 `fallback_provider`, one recorded fixture, E3 `fail_groq`). Gate **G-Gem Sat 20:00**; if it slips, Omar's first Sunday task, hard stop **D3 Sun 12:30**. Missed → `GEMINI_ENABLED=false` in the hosted build and the README states "implemented and tested offline, disabled in the deployed build" with the reason. Gemini is the judge only if S-3 ships. Stage B (`to_gemini_schema` constrained decoding + U2) = S-4 | 02's Sun 09:30 cutoff; 05's Sun 14:00 hard stop and its "F(S-6 Gemini)" tag |
| R3 | Frontend gate | **G4 Sat 16:00** on the hosted URL (checks in 07 §3 and 06 §1.4), with Advocate's early exits at 09:00 and 13:00. Fail → Streamlit from 16:00, never both | 01 §8 and 05 (15:00) |
| R4 | Try endpoint + error codes | `POST /api/orders/{id}/try` → path label `cascade_cache` (Architect's API is canonical). Error envelope from 01 §4; codes are 01's plus Skeptic's: 400 `VISITOR_ID_REQUIRED`, 409 `SEEDED_READONLY`, 429 `REPLY_LIMIT` (5 simulated replies per conversation), 429 `DEMO_BUSY` (500 global sandbox orders or worker queue > 20). The LLM cap is never a 429 | 04's `POST /api/sandbox/try` + `path='cached'`; 07 §8 SD edit for §10 |
| R5 | Mode-flip rehearsal | Jesser flips the hosted container to `event` at **Sat 16:15** for the S-1 phone tests and back to `public` at **17:30** right after G5, pass or fail. This is the rehearsal that proves restart-on-env-change + reseed. If WhatsApp was dropped at G1, do the same flip pair once at 17:30 (10 min) | 01's 15:30 / 16:45 proposal |
| R6 | LLM caps (public) | 04 §2.5 numbers: 80 live calls/day, 120K tokens/model/day, `0` = no live calls; re-derive from measured tokens-per-call after G3b | Any 150 / 300 figures elsewhere |
| R7 | Snapshot mode (S-9) | Ships only if the static bundle is **also** deployed to a second, static host; otherwise Won't, because a container outage takes the bundle down with it. It stays the G1 host-failure fallback | — |
| R8 | Additive API fields | Accept Advocate's `seed_key`, `llm.visitor_cap`, `injection_suspected`; Jesser confirms at G2 12:00. Budget banner date = `health.config.seed_captured_at` (or drop the phrase) | — |
| R9 | UI language | English chrome by default (the copy table's source language); switch to French only per `FEDI.md` §3.10 (by Sat 18:00). Customer text is always shown as written | — |
| R10 | Module paths | 01 §1 tree is canonical. Oracle's paths map as: `app/llm/schema.py` → `schemas/` + `app/extraction/repair.py`; `app/llm/window.py` → `app/extraction/window.py`; `app/llm/{evidence,postprocess}.py` → `app/extraction/{evidence,cross_field}.py`; `app/llm/backends.py` → `app/llm/{groq_backend,gemini_backend}.py`; `app/llm/rules_extractor.py` → `app/extraction/rules_extractor.py` | 02 file paths |
| R11 | Item numbering | Strategist's IDs (07 §1) are canonical. Craftsman's gated tags map: F(S-1 WhatsApp) = S-1 · F(S-3 rewrite) = S-3 · F(S-5 cascade) = **S-6** · F(S-6 Gemini): Stage A tests = **M-8** (Must), U2 = **S-4** · L6 bake-off F(S-4) = **S-7**. Architect's tree tags `gemini_backend.py` "S-6" → M-8; `cascade.py` "S-5" → S-6 | 05 and 01 tags |
| R12 | Council transcripts | Never committed here: `.claude/` is gitignored (applied). Only this sanitized folder is public | Engine default of committing `.claude/council/` |
| R13 | Doc cleanup | A precedence banner is on every root doc now. Omar applies Strategist's line-by-line table (07 §8) at **Sat 09:15** (30 min time-box). Its line numbers refer to commit `d87901b`; the banner shifts PRD.md down by 3 lines and the other root docs by 2 | — |

## 7. Decision log

| Decision | Options considered | Chosen | Reasoning |
|---|---|---|---|
| Prototype hosting | Laptop tunnel · hosted container · static snapshot only | Hosted single-origin container, seed on boot; tunnel dev-only | Judging runs off submitted materials after the event; a dead link costs most of Functional execution (20) |
| Public-visitor safety | Shared DB + reset · signed-cookie sandbox · unsigned visitor-id sandbox | Unsigned `X-Visitor-Id` sandbox, read-only seeds, caps → rules | Protects the hero and the budget at ~2 h of work |
| Frontend | Next.js SSR · Next static export · Vite React SPA · Streamlit | Vite + React + TS static bundle served by FastAPI; Streamlit only if G4 fails | No SSR needed; one origin, no CORS; Omar can debug React |
| Extraction models | Groq only · Groq + Gemini · bake-off first | Groq `gpt-oss-120b` → `gpt-oss-20b` (only if buckets are per model) → Gemini → rules, routed by error class, no retries | User decision (Groq + Gemini); production model first; cross-provider relief for outages |
| Label | Continuous weak score · thresholded · Bernoulli outcome | Bernoulli on a fully specified `S`; `binary:logistic`, monotone, 6 features | "Probability × 100" must mean a probability; monotone constraints stop a better address from raising risk |
| Training data size | 200–500 · 10,000 | 10,000 template-rendered rows (8k/2k), zero LLM calls | Free to generate; stable holdout metrics |
| Stale flags after reply | Prompt only · code only · both | Both: prompt rule first pass, code `resolve_flags()` has the final say | Deterministic hero; LLM variance can't break the demo |
| Evidence highlighting | Offsets on normalized text · client offsets · server segments | Server-built segments from an index map to the original | Offsets were wrong for Arabic diacritics/tatweel and emoji (UTF-16 vs code points) |
| Saturday outbound | LLM rewrite + judge · static template + prefilter | Static template + prefilter + human click; rewrite + judge Sunday Should | The reply loop needs a question; rewriting adds injection surface for little score |
| `[SELLER]` context | Last outbound text · canonical template text | Canonical template text only | Blocks second-hop injection through the rewrite |
| Headline AI number | Tier agreement (synthetic) · address-level exact match (native windows) | Address-level exact match X/N on 24 native-written windows | Real dialect text is harder to dismiss than synthetic |
| Test floor | 34 by Sat 22:00 · 16 by Sat 22:00, 34 by Sunday | 16-set by 22:00 (covers every High red-team row), 34 target Sun 15:30 | Fits the hour budgets |
| Demo format | Live stage · recorded video | Recorded 90-s video of a real run + Sat safety take | There is no stage; captions and `path` badges carry the disclosures |
| Figures in the pitch | 40–60% · 20–40% · none | No refusal-rate or COD-share figure unless the source is on screen | No verified source; an unbacked number costs credibility |
| Awards | 5 named · 4 named | SupplyzPro, Artefact, Guepard, Real-World AI Impact; not Kredete | Claim only what the build supports |
| Text baseline classifier (added after the council) | none · local TF-IDF char n-grams + logistic regression · hosted or open "typed decision" models | Local TF-IDF + logistic regression as Should S-11 ([03 §14](03-data-ml.md)): a no-LLM baseline row in the eval, then a disagreement check and `address_level` in the rules fallback | Trains in seconds on the synthetic rows with no GPU and no new dependency; it gives the LLM number a baseline. The larger models need a GPU or fine-tuning time the build doesn't have |
| Responsible-AI framing | "business data, not personal data" · accurate personal-data framing | Names, phones and addresses are personal data (not special-category): synthetic only, masking, human send, stated limits | The playbook's framing is wrong and a RAI judge would mark it down |

## 8. Timeline at a glance (Tunis)

**Saturday:** 09:00 kickoff (G0 09:15, doc cleanup 09:15) · **10:30 G-seams** · **12:00 G1 + G2** (keys, host hello-world, Meta, contracts/mocks frozen) · **14:00 T0 + G3** · **16:00 G4** (frontend on hosted URL) · 16:15 event-mode flip for phone tests · **16:30 G3b** (prompt frozen) · **17:30 G5** (WhatsApp) + flip back to public · **18:00 G6** (hero loop green on hosted URL) · 19:00 eval committed · **20:00 G-Gem** · **22:00 G7** (16 tests green, public build, repo public after secret scan, safety take captured) · 23:15 safety take uploaded.

**Sunday:** 08:00 flip to `event` · 08:30–09:00 D1 checks · 11:15–11:30 Sprint 1 → D2 11:30 (hero over venue network) · 11:45–13:00 Sprint 2 → D3 12:30 (Gemini if slipped), D4 13:00 (rewrite + judge on/off) · 14:00–15:30 Sprint 3 → **D5 15:30 freeze** · 15:45–17:00 video + capture → 16:40 export · 16:45 flip to public + tag `submission-v1` · 16:50 incognito audit · **17:10 submit**.

Details, fallbacks and per-person blocks: [07 §2–3](07-scope-schedule-delivery.md).

## 9. Must check with a real call or a human (the [VERIFY] list)

| # | Item | Who | By |
|---|---|---|---|
| V1 | Final Team Confirmation actually sent | Omar | G1 12:00 |
| V2 | Participant guide allows a video recorded before the event (else the safety take is a rehearsal) and the video length limit | `FEDI.md` §3.2 | G1 12:00 |
| V3 | Groq: `gpt-oss-120b` / `20b` / qwen active on the demo org; rate buckets per model or per org (decides whether 20b stays in the chain) | Omar | G1 12:00 |
| V4 | Gemini: free Flash-class model id, JSON-mode parameter names in the installed `google-genai`, schema dialect + key order, data-use terms | Omar | G1 12:00 |
| V5 | Host: always-on vs sleep, cold start, restart on env change, disk persistence, `PORT` injection, auto-deploy pinning | Montassar | Sat 14:00 |
| V6 | Meta: System User token path, test-number limits, webhook payload shapes (replace hand-built fixtures with scrubbed recordings) | Montassar / Jesser | G5 17:30 |
| V7 | Who reads Darija natively (eval windows + S-5 second labeler; `FEDI.md` F3) | Team | G0 09:15 |
| V8 | Package names/pins: `python-ulid`, `google-genai`, current GitHub Actions majors, Node LTS | Jesser / Montassar | T0 14:00 |
| V9 | Tokens-per-call after the prompt freeze → re-derive caps (R6) | Omar | G3b 16:30 |

## 10. Additions after the council

| Date | Item | Where | Changes |
|---|---|---|---|
| Sat 26 Sept | **S-11 text baseline classifier**: TF-IDF char n-grams + logistic regression, trained on the synthetic rows | [03 §14](03-data-ml.md), [07 §1](07-scope-schedule-delivery.md) S-11, tests ML14/ML15 | S-11a takes the Sat 21:00 slot ahead of S-7 (S-7 runs only if S-11a is done). S-11b is second in the Sunday cut order. New `confidence_reasons` value `text_clf_disagrees` (additive). No Must item or gate moves |
| Sat 26 Sept | **Gate checklists** per person | [09](09-gate-checklists.md) | No scope change. Lists four places where the spec gives two answers (repo visibility timing, eval report name, audit link owners, Omar's G1 timing) for Omar to settle at G0 |

## 11. What this spec does not do

- It writes no application code. The first code commit is the 09:30 skeleton ([05 §2](05-testing-ci.md)).
- It does not verify external services; see §9.
- Hero numbers in the mocks (83 → 14) are placeholders until `tests/golden/hero.json` exists (G6).
