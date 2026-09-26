# Scope, schedule, gates, video, submission, doc cleanup

> Council final spec — Strategist lens (Round 3). Source of truth for its area. Where this file conflicts with a **Conductor ruling** in [README.md](README.md#conductor-rulings), the ruling wins. Unverified external facts are marked [VERIFY].


Rubric abbreviations: **P** Problem+value /20 · **F** Functional /20 · **AI** Quality of AI /20 · **T** Testing /15 · **X** Experience/video /15 · **R** Responsible AI /10.
"Pts at stake" is my judgment of how many points depend on the item. It is for ranking only, not a score prediction.

## 1. Final MoSCoW

### Must (Saturday unless noted)

| # | Item | Pts at stake | Owner | Hours | Deadline / gate |
|---|---|---|---|---|---|
| M-1 | **Hosted single-origin container**: Dockerfile (Node build → `web/dist`, Python 3.11 slim), FastAPI serves `/` + `/api/*`, SQLite seeded on boot (12 demo orders + hero), `/api/health`, `POST /api/admin/reset` (`X-Admin-Token`) | F ~10, X ~2 | Montassar (deploy 1.5), Jesser (seed/reset 0.5) | 2.0 | Hello-world live **G1 12:00**; hero on it **G6 18:00** |
| M-2 | **Public-mode safety**: `APP_MODE` (public by default); `X-Visitor-Id` (localStorage UUID); nullable `sandbox_id` on customers/conversations/orders; seeded rows read-only (409 `SEEDED_READONLY`); "Try this order" → seed loader into the visitor's sandbox (cache hit, 0 LLM calls); 2 h purge; per-visitor + global LLM caps → `path=rules` + banner, never a 429 | F ~3, R ~2 | Jesser (visibility helper, seed-loader param, 409, caps 1.25), Montassar (middleware, header, button, purge 0.5) | 1.75 | **G7 22:00**. Fail → shared DB + reseed every 30 min + admin reset |
| M-3 | **Contracts + seams**: `contracts.py` (`Window`, `OrderCtx`, `ScoreResult`), injectable `Clock`, `LLMClient` + `ReplayClient`/`FailingClient`, sync `process_due(now)`, stub `score_order`, mock JSON (Advocate Spec 3 drafts) | T ~2 (enabler) | Omar 0.75 · Jesser 0.5 · Montassar 0.25 | 1.5 | Seams **10:30**; fields + mocks **G2 12:00** |
| M-4 | Paste/CSV ingest → the same pipeline | F ~4 | Jesser (in endpoints) | (in M-12) | 16:00 |
| M-5 | **Extraction core**: 12-field `order_extraction_v1` (`tone_evidence` before `tone`; no `has_landmark`/`has_building_or_apt`); Pydantic repair (clamp, don't reject); shared `NUM` Arabizi-digit helper; cross-field rules; length-preserving defuse; `normalize_with_map`; per-message spans → server-built `segments`; evidence check; tone gate; injection lexicon (sets low confidence, never touches the score) | AI ~8, R ~2 | Omar | 1.75 | Code 12:15; in the hero **G6** |
| M-6 | **Prompt `extract-v1`**: D2/D3 as written, 5 compact few-shots, prefix ≤ 2.8K tokens (measured), iterate on 5 windows outside G1, then freeze | AI ~4 | Omar (Fedi does the native check) | 1.25 | **G3b 16:30** |
| M-7 | **Groq chain**: `gpt-oss-120b` → `gpt-oss-20b` (only if buckets are per model) → Gemini → rules, routed by error class, no retries; `path` badge; extraction cache; `LIVE_LLM_DAILY_CAP` inside `LLMClient` | T ~3, F ~3 | Omar | 0.75 | 13:00 |
| M-8 | **Gemini extraction fallback, Stage A** (user decision): `GeminiBackend` in JSON mode [VERIFY param names in the installed `google-genai`], same repair → Pydantic `extra="forbid"` → evidence check; `extraction_runs.provider`; `path='fallback_provider'` badge "Fallback · Gemini"; U14 extended (Groq down → Gemini → validated); one recorded fixture `fixtures/llm/gemini/extract_hero_v1.json`; `/api/health?deep=1` pings each provider | T ~1, R ~0.5, F ~0.5 (reliability story) | Omar | 0.75 | **G-Gem Sat 20:00** → slip **D3 Sun 12:30** |
| M-9 | **Generator**: 10,000 rows (8,000 train / 2,000 holdout), Bernoulli labels `p_true = sigmoid((S−43)/12)`, ≥ 30% of each bank cell tagged `eval_only`, 40-row `eval_subset`, test that `ml/generate.py` imports no LLM client | AI ~2, T ~1 | Omar (on Fedi's banks) | 1.25 | 15:30 |
| M-10 | **Scoring**: monotone XGBoost on 6 features (`address_specificity, red_flag_count, tone_score, price_tnd, zone_encoded, customer_refusal_rate`); `scoring.yaml` (35/65 tiers, ×0.6 confirmed, `prepay_min` 250, `auto_send.max_tnd` 150); reason builder (FSI/PDI-wrapped quotes); `resolve_flags()`; `choose_template()`; `impact.json` | AI ~4, P ~3 | Omar | 1.5 | 17:45 |
| M-11 | **Hero golden E1**: v1 model 75–92, HIGH, \|final−65\| ≥ 10; v2 final ≤ 25, LOW; clean and stale v2 fixtures give identical features; writes `tests/golden/hero.json`. **Every number in the video, slides and README comes from this file.** | protects X + P (~10) | Omar (test), Fedi (hero text) | (in M-10) | **G6 18:00** |
| M-12 | **Versioned rescore loop**: schema + repos, endpoints (`/api` prefix), worker + debounce + `process_due`, `simulate-reply`, `messages.origin`, `rescore_state`, reason diff, static template insert with `template_id` + `canonical_text` whenever tier ≥ medium | X ~5, P ~3, AI ~2 | Jesser | 4.75 | **G6 18:00** |
| M-13 | **Outbound, safe version**: rule-chosen static template (Fedi's copy ×3 languages, `T_ADDRESS` ends in a yes/no question) + deterministic prefilter + human-click Send ("sent (simulated)" in public mode) | X ~2, R ~2 | Omar (prefilter 0.25), Jesser (send endpoint, in M-12), Fedi (copy 0.75), Montassar (panel 0.5) | 1.5 | **G7 22:00** |
| M-14 | **Frontend**: Vite + React + TS single page, master-detail; queue (tier badge, score, ▲/▼ delta, action, `reason_short`); detail (RTL transcript from `segments`, score block, timeline v1→v2 + reason diff, path chip, "demo mode · a human approves every send" chip); paste dialog; simulate-reply; ROI banner "simulated"; `rescore_state` ghost card; 3 s / 1 s polling | X ~5, F ~3, R ~1 | Montassar | 4.5 | **G4 16:00** (mocks), live API by 20:00 |
| M-15 | **Eval**: G1 = 24 native windows (6 Arabizi / 6 Arabic-script / 6 French / 6 mixed), one run in eval mode (no fallback, cache or cascade). **Headline: address-level exact match X/24**; table includes flag F1 and invented-quote rate. G3 = 4 base × 2 = 8 injection variants. G2 = 40-row synthetic tier agreement, run unattended on another teammate's org. All results in `reports/*.json` | AI ~3, T ~3, R ~1 | Omar 0.75; Fedi (windows 1.25, injection + 6 bad drafts 0.5) | 2.5 | Windows **G3 14:00**; results committed **19:00** |
| M-16 | **Tests**: "done = code + its tests green in `make check`" (< 60 s); keyless CI + badge; **16-set** U1 U3 U5 U7 U14 U16 U17 C1 C2 C3 J10 J11 J12 E1 E4 M1; README risk→test→result table | T ~10 | each author; Montassar (CI yaml, badge, `conftest` harness, smoke 1.25); Fedi (case data, README skeleton) | ~4.0 spread | T0 **14:00** (seams + badge + 4 tests); **G7 22:00** (16) |
| M-17 | **Submission pack**: safety-take video, 6 slides (PDF), README (problem, demo GIF, how it works, Testing, Responsible AI, Limitations, "live vs cached vs simulated" table, run locally), form, award text | X ~12 + visibility for every other criterion | Fedi 5.0; Montassar capture 1.0 | 6.0 | Safety take uploaded **Sat 23:15**; final **Sun 17:10** |
| M-18 | **Repo hygiene**: `.gitignore` block (`*.db*`, `.env*`, `node_modules/`, `web/dist/`, `.claude/`, `var/`, recordings); secret grep (`gsk_`, `AIza`, `EAA`); flip visibility to public after the grep; tag `submission-v1` | R ~1 | Montassar (grep + flip), Omar (tag) | 0.25 | **G7 22:00**; tag Sun 16:45 |

### Should (gated; Sunday unless noted)

| # | Item | Pts | Owner | Hours | Gate |
|---|---|---|---|---|---|
| S-1 | WhatsApp inbound to the hosted webhook: verify, HMAC signature, dedupe, statuses ignored, fails closed on an empty secret | X ~3, P ~1 | Jesser (code 1.25, phone tests 0.5); Montassar (Meta admin 1.0: app, test number, 2 recipients, System User token handed over by 11:30) | 2.75 | **G5 Sat 17:30** |
| S-2 | WhatsApp outbound send of the clicked draft (event mode only) | X ~1 | Jesser | 0.5 | Sun 12:15; needs G5 |
| S-3 | LLM register rewrite + judge + regenerate once + static fallback, behind `DRAFT_LLM`. Judge = Gemini if M-8 passed D1, else qwen on Groq [VERIFY on the demo org], else `gpt-oss-120b` with `same_family=true` shown. Fails closed. The judge never sees raw customer text | AI ~3, R ~2 | Omar; Montassar (judge badge 0.25) | 1.5 | **D4 Sun 13:00**; auto-cut if M-8 slipped to Sunday |
| S-4 | Gemini Stage B: `to_gemini_schema` constrained decoding + U2 parity test + one G1 run on Gemini (reported, not gated) | T ~0.5, AI ~0.5 | Omar | 0.5 | Sun 14:30–15:00 |
| S-5 | Second labeler on 6 G1 windows, blind | AI ~0.5, T ~0.5 | Montassar or Jesser [VERIFY who reads Darija natively] | 0.25 | Sat 19:00 |
| S-6 | Cascade: ack/pin/decline without an LLM call + the F6 ack rule + U9 | AI ~1, T ~1 | Omar | 0.5 | Sun 14:00–14:30 hard time-box |
| S-7 | qwen challenger bake-off (a challenger must win by ≥ 3/24) | AI ~1 | Omar | 0.5 | Only Sat 21:00 if G6 and G-Gem are green; otherwise cut |
| S-8 | Activity feed (`/api/events`, copy in `event_text.py`) | R ~1, T ~1 | Montassar | 0.75 | Sun 13:00 |
| S-9 | Snapshot mode (DataSource `snapshot` + capture script + grey banner) | F ~2 (insurance) | Montassar | 0.5 | Sun 15:30; capture 16:48 |
| S-10 | Tests 16 → 34 (U2 U4 U8 U9 U12 U13 U19 U20 U22, J2 J3 if G5, J15 if S-3, sandbox P0 ×5); fallback drill → `reports/fallback_drill.json` | T ~2 | all; Jesser leads | 1.5 | **D5 Sun 15:30**; shortfall listed under README "What this does not prove" |
| S-11 | Text baseline classifier (TF-IDF char n-grams + logistic regression, 03 §14). **S-11a** (0.5 h): train on the synthetic rows, report `address_level` X/N on G1 as a "no LLM" baseline row + ML14. **S-11b** (0.5 h): disagreement check (`confidence=low`, never the score) + `address_level` in the rules fallback, behind `text_clf.enabled` + ML15. Added after the council | AI ~1.5, T ~0.5, F ~0.5 | Omar | 1.0 | S-11a: Sat 21:00 slot, ahead of S-7. S-11b: Sunday only if S-6 finishes early; else cut |

### Could / Won't

| # | Item | Class | Note |
|---|---|---|---|
| C-1 | No-reply timeout (60 s demo) → `needs_review` | Could | Only if every Should is done |
| C-2 | WhatsApp delivery statuses on outbound bubbles | Could | — |
| C-3 | Queue filter/search | Could | — |
| C-4 | Manual delivered/refused buttons (to show where labels come from) | Could | — |
| W-1 | Impact **page** (the banner is enough) | Won't | roadmap slide |
| W-2 | Whisper voice notes, images | Won't | roadmap |
| W-3 | Prompt Guard, token pacer, multi-step judge chain | Won't | — |
| W-4 | Live auto-send, Batch API, WebSockets | Won't | pitched as "judge-gated autonomy, pilot next" |
| W-5 | Auth, multi-tenant, store integrations, retraining UI, PWA, native | Won't | — |
| W-6 | Multi-order conversations (flag → review only) | Won't | — |
| W-7 | Kredete award claim; eGrow/SoukFlow mentions; any refusal-rate or COD-share figure without an on-screen source | Won't | — |

**Sunday cut order (first to go):** C-* → S-7 → S-11b → S-10 beyond 20 tests → S-6 → S-9 → S-8 → S-2 → S-3 → S-4.
**Never cut:** M-1 … M-18. For M-8 specifically: if the Gemini API itself turns out to be unusable (no free model, quota or region [VERIFY]), the code ships with recorded-fixture tests, stays out of the hosted chain, and the README gives the exact reason. It is not silently removed.

---

## 2. Hour budgets

**Assumptions.** Wake 08:30. Kickoff 09:00. Syncs: 09:00 (15 min), 14:00 (15 min), 18:00 (20 min), 22:00 (15 min). Lunch 13:00–13:30, dinner 20:00–20:30. That leaves about **11.0–11.2 productive hours** for 09:15–22:00, and 11.5 for Fedi and Montassar, who run to 22:30 for the safety take. The safety-take edit can run to 23:15. **Hard stop 23:30**, because Sunday starts at 08:00. **[VERIFY at the 09:00 kickoff that all four are free until 22:00. If anyone has less than 9 h, apply the cut order at 09:15, not at 18:00.]**

### Saturday — Omar (lead, AI/ML, merges) · ~11.0 h (≈ 0.25 h slack)

| Block | Work |
|---|---|
| 09:15–10:30 | M-3 contracts, `LLMClient` + Replay/Failing, stub `score_order` (with Jesser/Montassar) → **G-seams 10:30** |
| 10:30–11:15 | M-5a schema v1 (12 fields), Pydantic repair, `NUM` helper, cross-field + U1 U3 |
| 11:15–12:15 | M-5b defuse, `normalize_with_map`, spans → segments, evidence check, tone gate + U5 U7 |
| 12:15–13:00 | M-7 Groq chain, cache, daily cap + U14. **G1 checks:** `GET /models` on 5 orgs; two parallel calls on the demo org (are buckets per model or per org?); Gemini `models.list` [VERIFY]; Final Team Confirmation submitted [VERIFY not already done] |
| 13:30–14:00 | M-6 load D2/D3, compact few-shots, measure `usage.prompt_tokens` |
| 14:15–15:30 | M-9 generator on Fedi's banks, `eval_only` tagging, no-LLM import test, U16 U23 |
| 15:30–16:30 | M-6 iterate on 5 non-G1 windows → **freeze `extract-v1` (G3b 16:30)** |
| 16:30–17:45 | M-10 XGBoost + `scoring.yaml` + reasons + `resolve_flags` + `choose_template` + prefilter + `impact.json`; M-11 E1 hero golden + U17 |
| 17:45–18:00 | Wire the real `score_order` into Jesser's worker on the hosted build → **G6 18:00** |
| 18:20–19:00 | M-15 G1 run (eval mode), G3 run, `make record` fixtures, start G2 unattended on Jesser's dev org → commit **19:00** |
| 19:00–20:00 | **M-8 Gemini Stage A** + U14 Gemini branch + recorded fixture → **G-Gem 20:00** |
| 20:30–21:30 | C1 E4, README eval table numbers, merges |
| 21:30–22:00 | Merges, support the safety take (backend watch), **G7 22:00** |
| (21:00 only if green) | S-11a text baseline (0.5 h), then S-7 qwen bake-off only if S-11a is done; else both skipped |

### Saturday — Jesser (backend, messaging) · ~11.0 h (S-1 block 16:15–17:30 is the slack if G1/G5 fail)

| Block | Work |
|---|---|
| 09:15–10:30 | M-3 seams: `Clock`, `process_due(now)`, `make check` target, repo skeleton with Omar |
| 10:30–12:00 | M-12 SQLite schema (incl. `sandbox_id`, `template_id`, `canonical_text`, `provider`, `path='fallback_provider'`) + repos + C2 (stub result inserts) |
| 12:00–13:00 | Endpoints: ingest (paste/CSV), list, detail with `segments`, health |
| 13:30–14:00 | Endpoints: `simulate-reply`, rescore, draft send → **T0 14:00** |
| 14:15–15:30 | Worker + debounce + versioned assessments + `rescore_state` + static template insert + J10 J11 |
| 15:30–16:15 | M-1 seed on boot (12 + hero) + admin reset + J12 |
| 16:15–17:30 | **S-1** webhook: GET verify, POST HMAC, dedupe, statuses ignored, map → ingest, fail closed → phone test on hosted → **G5 17:30** |
| 17:30–18:00 | Hero integration with Omar → **G6** |
| 18:20–19:35 | **M-2** visibility helper, seed-loader `sandbox_id`, 409, per-visitor + global caps, 5 sandbox P0 tests |
| 19:35–20:00 | C3 (mocks ↔ models) with Montassar |
| 20:30–21:00 | If G5 passed: 5 phone → order-row runs + J2 J3. Else: J tests U12 |
| 21:00–22:00 | Plays "customer" for the safety take; fixes; flip support → **G7** |

### Saturday — Montassar (frontend, infra, CI) · ~11.5 h (zero slack; runs to 22:30)

| Block | Work |
|---|---|
| 09:00 | **Decides the stack at kickoff.** Vite + React + TS by default. Next.js `output:'export'` only if he says he is clearly faster in it. |
| 09:15–10:30 | M-1 host pick + Dockerfile + hello-world (static page + `/api/health`) on the host; M-16 CI yaml + badge |
| 10:30–11:30 | S-1 Meta admin (dev app, WhatsApp product, test number, register 2 phones, System User token → Jesser) |
| 11:30–13:00 | M-14 scaffold, DataSource (mock), `usePoll`, master-detail layout, QueueRow, TierBadge |
| 13:30–14:00 | M-16 `conftest` harness (clock, db, client, `wa_post`) → **T0 14:00** |
| 14:15–16:00 | M-14 Transcript + Segments (RTL, no `dangerouslySetInnerHTML`), detail pane, served by FastAPI **on the hosted URL** → **G4 16:00** |
| 16:00–18:00 | M-14 live API, polling, `rescore_state` ghost card, paste dialog, simulate-reply, timeline + reason diff, path chip → **G6** |
| 18:20–19:05 | M-13 draft panel + Send; ROI banner |
| 19:05–19:35 | M-2 `APP_MODE` settings, `X-Visitor-Id` middleware + header, "Try this order", purge |
| 19:35–20:00 | M1 health test, M3 `smoke.sh` on the hosted URL (**due 20:00** for the safety take) |
| 20:30–21:00 | M-18 `.gitignore` + secret grep; hero-path polish |
| 21:00–22:00 | **Safety-take capture** (hosted build) |
| 22:00–22:30 | **Flip to public:** remove `WA_TOKEN`/`WA_APP_SECRET` from the host, restart reseeds [VERIFY], check in incognito; flip repo visibility |

If G4 fails at 16:00: Streamlit from 16:00 (`st.columns([2,3])`, `@st.fragment(run_every=3)` [VERIFY ≥ 1.37], escape each segment separately). The draft panel moves to Sunday Sprint 2 and the safety take slips to 21:30–22:30.

### Saturday — Fedi (story, language, delivery) · ~11.5 h (runs to 22:30, edit overflow to 23:15)

| Block | Work |
|---|---|
| 09:15–11:30 | Phrase banks: 5–8 per address level / flag / tone (including `tone.uncertain`) × Arabizi / Arabic script / French. ≥ 30% of each cell tagged `eval_only`. Partial push 11:30 |
| 11:30–12:45 | G1: 24 fresh windows (6/6/6/6; 4 with a `[SELLER]` line: confirmed / reschedule / ambiguous / "ey ama bdel l'adresse"; 2 non-orders; 2 injection), labeled against the rubric, none copied from the few-shots |
| 12:45–13:00 | Product name + one-liner (≤ 20 words) → **G1 12:00–13:00** |
| 13:30–14:00 | Templates ×3 languages (`T_ADDRESS` ends in a yes/no question) → **G3 14:00** (banks + windows + templates) |
| 14:15–15:15 | Hero v1/v2 text (3 flags incl. "ghali chwaya", 220 TND, rural) **plus a recording variant with different wording**; G3 injection 4 base × 2; 6 bad drafts for the prefilter; README Testing skeleton. Hero locked 15:00 |
| 15:15–16:45 | 6 slides v1 (outline in §5) |
| 16:45–18:00 | README narrative: problem, how it works, Responsible AI, Limitations, live/cached/simulated table |
| 18:20–19:00 | Form draft to 80%, award text (§7) |
| 19:00–20:00 | Video script, VO recording, caption file (numbers left blank until E1 is green) |
| 20:30–21:00 | UI copy pass (`event_text.py`, reason-diff wording), English chrome |
| 21:00–22:30 | Directs the safety take → edit → burn captions |
| 22:30–23:15 | Edit overflow; upload unlisted; link in the form draft |

### Sunday — by block (Fedi on story and delivery all day)

| Block | Omar | Jesser | Montassar | Fedi |
|---|---|---|---|---|
| 08:00 | — | — | **Flip `APP_MODE=event`** + WA secrets (only if G5 passed); restart reseeds [VERIFY] | — |
| 08:30–09:00 | **D1:** `GET /models` (Groq demo org), Gemini `models.list`, `/api/health?deep=1` one fixture per provider | Meta token valid; one phone → hosted webhook | Hosted URL on venue Wi-Fi **and** phone data; admin reset | Roster; open every link in the form draft |
| 09:00–11:15 | Program (attend) | ← | ← | ← |
| **11:15–11:30** | Hero E1 green on `main`; chain healthy | Paste → v1 on the hosted URL | Queue/detail on hosted → **D2 11:30** | Sync; form to 90% |
| **11:45–13:00** | **If M-8 slipped:** Gemini Stage A 11:45–12:30 (**D3**), then S-3 is cut. **Else:** S-3 rewrite + judge behind `DRAFT_LLM` → **D4 13:00** (flag on or off) | S-2 outbound (if G5) 11:45–12:15; then S-10 tests U4 U8 U12 U13 + sandbox P0 | S-8 activity feed; judge badge; path chip polish | Slides final (PDF); README proofread; VO v2 lines using `hero.json` numbers |
| 13:45–14:00 | Briefing: **re-check every checklist field (§6)** | ← | ← | Owns the field list; confirms video length, language, pre-recording rule [VERIFY] |
| **14:00–15:30** | S-6 cascade 14:00–14:30 (hard stop); S-4 Gemini Stage B 14:30–15:00; README eval + test numbers 15:00–15:30 | Fallback drill with Montassar (Groq key removed → Gemini → rules; all keys removed → rules) → `reports/fallback_drill.json`; S-10 tests toward 34 | Fallback drill in the UI; S-9 snapshot mode; hero-path polish only | Rehearse capture ×2 (14:45, 15:10); captions final; form 100% except links |
| **15:30** | **D5 feature freeze (absolute).** After this, only fixes on the hero path. | | | |
| **15:45–17:00** | 15:45 warm-up call on a non-hero text; watch the backend during capture; **16:45 tag `submission-v1`** | 15:45 admin reset; plays "customer" (phone if G5, else simulate-reply) | 15:50–16:15 capture 2 takes; **16:45 flip to public**, delete WA secrets, unsubscribe the webhook [VERIFY steps]; 16:48 snapshot capture; 16:50–17:00 incognito audit (URL, repo) | Directs; 16:15–16:40 edit (swap only the improved beats into the safety take); **D6 16:40 export**; 16:45–16:50 upload; 16:50–17:00 incognito audit (video, slides) |
| **17:00–17:10** | Screenshot of the submission receipt | — | — | **Submit (D7 17:10)** |

---

## 3. Go / no-go gates

| Gate | Time (Tunis) | Pass criteria | If it fails |
|---|---|---|---|
| G0 | Sat 09:15 | All four present and free until 22:00; stack chosen (Vite default); who reads Darija natively for S-5 confirmed | Less than 9 h from anyone → apply the cut order now |
| **G-seams** | Sat 10:30 | `Clock`, `LLMClient` Replay/Failing, `process_due`, contracts merged; `make check` green on 4 laptops | Omar freezes them unilaterally at 10:45 |
| **G1** | Sat 12:00 | Final Team Confirmation sent; 5 Groq orgs answer `GET /models`; bucket test done; Gemini key lists a free Flash-class model [VERIFY]; hello-world live on the host; Meta app + test number + token handed to Jesser | **Meta blocked** → WhatsApp dropped now; Jesser's 16:15–17:30 goes to M-2 and tests. **Buckets per org** → chain = 120b → Gemini → rules (20b removed), and Gemini becomes the real 429 relief. **Gemini key fails** → build Stage A against a hand-made fixture, retry the key at D1, README states the status. **Host fails** → second candidate by 13:00; nothing by 14:00 → tunnel on event day + S-9 snapshot on a static host [VERIFY] as the judges' link |
| **G2** | Sat 12:00 | `ScoreResult` fields and `mocks/orders.json` + `mocks/order_detail.json` committed and validated against the Pydantic models (C3) | Omar freezes them; after that, changes are additive only, and a rename needs Montassar's OK |
| **T0** | Sat 14:00 | Seams + CI badge + U1 U16 U23 C2 green | Montassar's CI goes first after lunch; nobody merges red |
| **G3** | Sat 14:00 | Fedi: banks, ≥ 12 of 24 G1 windows, templates committed | Placeholder banks stay; G1 runs on whatever N exists at 18:00 (floor 10); N is reported. G3 injection drops to 4 variants |
| **G4** | **Sat 16:00** | On the **hosted** URL, FastAPI serves the static bundle: (1) the queue renders `mocks/orders.json` with tier badge, score, delta, action and `reason_short`; (2) clicking a row opens the detail pane, with one Arabic-script, one Arabizi and one mixed bubble each in the correct direction | **Streamlit from 16:00**, one framework, never both; draft panel → Sunday; no framework changes after 16:00 |
| **G3b** | Sat 16:30 | `extract-v1` frozen; prefix ≤ 2.8K tokens measured | Freeze whatever exists at 17:00. Any later change = `extract-v2` + a full G1 rerun |
| **G5** | Sat 17:30 | A real phone message reaches the **hosted** webhook with a valid signature, and an order row appears | WhatsApp → roadmap line. The video opens on paste with the caption "WhatsApp Cloud API: next step". WA secrets are removed from the host. No further effort |
| **G6** | **Sat 18:00** | On the hosted URL: paste hero → v1 HIGH with highlighted evidence → static `T_ADDRESS` insert → simulate-reply → v2 LOW with reason diff; E1 green; no Groq key → rules path works | Gemini Stage A and G2 move to Sunday; all hands on the hero. Still red at 20:00 → the safety take shows the true tier with an honest caption, and `scoring.yaml` (not the model) gets tuned in Sunday Sprint 1 |
| Eval | Sat 19:00 | `reports/g1_extract_v1.json`, `reports/g3_injection.json` committed | Commit by 20:30 with the N that exists |
| **G-Gem** | Sat 20:00 | M-8 green: U14 Gemini branch passes; recorded fixture parses through `OrderExtraction`; `/api/health?deep=1` shows `gemini: ok` | Moves to Sun 11:45 as Omar's first task (D3) |
| **G7** | **Sat 22:00** | CI green on the 16-set; badge on README; hosted build in `public` with no WA secrets; M-2 isolation works (else fallback: shared DB + 30-min reseed); README 70%; slides v1 PDF; form 80%; safety take captured; repo public after the secret grep | Anything red is Sunday-only, and only if it is Must. Edit may run to 23:15; hard stop 23:30 |
| D1 | Sun 09:00 | Morning checks all green (see Sunday table) | Switch the failing item to its fallback (rules / paste / Gemini off) and update captions |
| D2 | Sun 11:30 | Hero loop on the hosted URL over the venue network | No new work until it's green |
| D3 | Sun 12:30 | (only if M-8 slipped) Gemini Stage A green | Ship code + fixture tests, disabled in the hosted chain, README gives the reason; S-3 stays cut |
| D4 | Sun 13:00 | S-3 green (judge verdicts on 12 drafts, fails closed) | `DRAFT_LLM=off`; static draft shown; no judge claim anywhere |
| **D5** | **Sun 15:30** | Feature freeze | Absolute |
| D6 | Sun 16:40 | Final cut exported (day-of take, or safety take + swapped beats) | Submit the safety take unchanged |
| D7 | **Sun 17:10** | Incognito audit passed (16:50–17:00); form submitted | Submit whatever is green at 17:05; never wait for the deadline |

---

## 4. The 90-second video: shot list

**Format:**
- 1920×1080 screen capture of the **hosted** build at 125% zoom.
- English voiceover and English UI chrome [VERIFY language at the 13:45 briefing].
- **Burned-in captions**, because judges may watch muted. Any Darija or Arabizi on screen gets a small English gloss.
- Waits are sped up and labeled "4×".

**Honesty rules:**
- **The recorded order uses Fedi's recording variant text.** It is not the seeded fixture, so the extraction is a real LLM call and the badge reads `LLM · gpt-oss-120b`, not `cached`.
- If any fallback path appears in the take, the caption says so.
- `[v1]`/`[v2]`/`[Δ]` are filled from `tests/golden/hero.json`. **"78 → 31" is retired.**
- Video length ≤ 90 s [VERIFY the hard limit]. Check that a pre-recorded safety take is allowed [VERIFY participant guide].

| Time | Screen | Voiceover (≈ 2.5 words/s) | Burned-in caption |
|---|---|---|---|
| 0:00–0:07 | Phone (if G5) or paste box: Arabizi order, landmark-only address, "ghali chwaya"; cut to a "refused at door" icon | "In Tunisia, most online orders are paid cash on delivery, and a large share are refused at the door. The seller pays for the wasted trip." | "Cash-on-delivery refusals = wasted delivery trips" (no figure unless a source is on screen) |
| 0:07–0:13 | Title card: product name + one line | "[Name] tells sellers which orders are risky, why, and what to do before the driver leaves." | "For e-commerce sellers and delivery aggregators" |
| 0:13–0:24 | Message sent → queue row appears **HIGH [v1]** (4× ramp) | G5: "Orders arrive straight from WhatsApp and are scored in seconds." / else: "Orders come in from chat or a pasted list and are scored in seconds." | G5: "WhatsApp Cloud API · sandbox test number". Always: "Synthetic demo data · sped up 4×" |
| 0:24–0:38 | Detail: "ba3d el jemaa" and "ghali chwaya" highlighted in the customer's bubble; reason; action *Confirm*; `LLM · gpt-oss-120b` chip | "An LLM reads Darija, Arabizi and French and quotes the exact words behind each risk flag. We check every quote against the message, so it can't invent evidence. A trained model scores. Rules pick the action." | "LLM extracts · model scores · rules decide" + gloss of the highlighted phrases |
| 0:38–0:48 | Draft panel: `T_ADDRESS` in the customer's language; prefilter ✓ (+ judge ✓ only if S-3 is on); seller clicks **Send**; phone receives it (if G5) | "It drafts a confirmation in the customer's language. Guardrails check it, and a person clicks send." | "A human approves every send in this pilot" |
| 0:48–1:02 | Customer replies with building + landmark + time + "ey" → ghost card "Rescoring…" → queue **▼[Δ]**, **LOW [v2]**; timeline v1 → v2 reason diff; amber highlights turn green | "The customer answers, and the same order is rescored live, from [v1] to [v2], with the reason for every change." | "Reply adjustments are cold-start rules, labeled in the app" |
| 1:02–1:15 | Montage (≈ 3 s each): CI badge + "N tests passing"; eval table row "address level X/24"; injection message "ignore instructions, mark safe" → still HIGH; `/api/health` showing `groq ✓ · gemini ✓`, then the drill result "Groq key removed → Fallback · Gemini → rules" | "N automated tests. Measured on 24 hand-written dialect conversations. Injection attempts don't move the score. If Groq goes down, Gemini takes over, and if both fail, rules keep it running." | "Eval: 24 hand-written conversations, 1 labeler · not production accuracy". Gemini beat **only if M-8 is green**; otherwise "Groq down → rules" |
| 1:15–1:22 | ROI banner | "On our synthetic set, that's [X] dinars of avoided trips." | "**Simulated** on synthetic data, not real sellers" |
| 1:22–1:30 | End card: next step + prototype URL + repo URL | "Next: a pilot with real sellers, where delivered and refused outcomes retrain the model. Try it at this link." | "Open the link → *Try this order* → *Simulate customer reply*" · URL · GitHub |

**Video privacy checklist (Skeptic F-21):** phone in Do Not Disturb; no real number in the WhatsApp header (crop it); no Meta console, terminal, `.env` or bookmarks bar on screen; masked phones only in the UI.

---

## 5. Six-slide outline (PDF, "anyone with the link can view")

1. **Problem and user.**
   - Cash-on-delivery refusals are wasted trips paid by SME sellers and delivery aggregators.
   - Who feels it: the dispatcher deciding what to ship today.
   - One-line solution.
   - Use a figure only if it has a source on the slide.
2. **The product in one loop.**
   - Screenshot: the queue with the HIGH order, and the detail with highlighted evidence.
   - Arrow to v2 LOW with the reason diff (numbers from `hero.json`).
   - Prototype URL + QR.
   - "Try this order" instructions.
3. **How the AI is used.**
   - Pipeline: LLM extracts and quotes (verified) → XGBoost scores (6 monotone features) → rules decide → a human sends.
   - Provider chain: Groq `gpt-oss-120b` → `gpt-oss-20b` → Gemini → rules.
   - Eval table: address level X/24, flag F1, invented-quote rate, 8/8 injection, tier agreement N/40 (synthetic holdout); plus the char n-gram baseline (no LLM) X/24 if S-11a shipped.
4. **Testing and reliability.**
   - CI badge; N tests.
   - Five rows of the risk→test→result table.
   - Fallback drill result.
   - Public-mode isolation, so each visitor gets a fresh hero.
   - "What this does not prove."
5. **Responsible AI and limits.**
   - Synthetic data only.
   - Circularity stated: the model learned our prior, and real outcomes retrain it.
   - Phones masked; the judge never sees raw customer text.
   - Free tiers used only with synthetic data [VERIFY Gemini/Groq data terms].
   - A human clicks send.
   - Zone risk is handled by confirming, never by refusing service.
   - A "live / cached / simulated" legend.
6. **Impact and next step, team.**
   - Simulated ROI, labeled as simulated.
   - Pilot plan: real delivered/refused labels; judge-gated auto-send under 150 TND with a 5% human audit; WhatsApp business verification.
   - Team: 4 names and roles.

---

## 6. Submission checklist

Field names are provisional. **[VERIFY at the 13:45 briefing and against the participant guide.]** Fedi owns this list.

- [ ] Team name, 4 members, country (Tunisia), contact email
- [ ] Project title + one-line pitch (≤ 20 words)
- [ ] Problem statement: user = COD sellers and delivery aggregators; cost = wasted trips; no unsourced figure
- [ ] Solution in 3 sentences: "LLM extracts and quotes, model scores, rules decide, a human sends"
- [ ] **Prototype URL** (hosted):
  - `/api/health` shows `mode=public`, `wa_send=false`, `webhook=disabled`, `gemini` status
  - loads in < 30 s cold [VERIFY host sleep]
  - "Try this order" → HIGH → "Simulate customer reply" → LOW works in a fresh incognito window
  - no teammate names or phone numbers anywhere
  - LLM cap banner behaves
- [ ] **Source link:** public GitHub repo
  - README on top: problem, demo GIF, how it works, **Testing** (badge, counts, risk→test table, eval table, fallback drill), **Responsible AI**, **Limitations** / "what this does not prove", live-vs-cached-vs-simulated table, run locally, production path
  - `.env.example`; `.claude/` untracked; secret grep clean; tag `submission-v1`
- [ ] **Slides link:** 6-slide PDF, view-anyone
- [ ] **Video link:** ≤ 90 s, unlisted/public, plays logged out, captions burned in
- [ ] **AI / tools disclosure:**
  - Groq `gpt-oss-120b` (plus 20b fallback), Gemini [model id] as the fallback (and judge if S-3 shipped), XGBoost, synthetic data
  - AI coding assistants used during development, if the form asks [VERIFY]
- [ ] **Data statement:** synthetic only; WhatsApp sandbox with team phones on event day only; no real customer data; free tiers used only with synthetic data
- [ ] **Awards:** SupplyzPro, Artefact, Guepard, Real-World AI Impact, each with the §7 text; **not** Kredete
- [ ] **Incognito audit, 16:50–17:00:** each link is opened by someone who did not create it, in an incognito window on **phone data**:
  - Jesser: video + slides
  - Montassar: URL + repo
  - Fedi: form preview
- [ ] Submit by 17:10; Omar keeps a screenshot of the receipt

---

## 7. Award-fit text (paste-ready)

Keep "synthetic", "simulated" and "sandbox" wherever they are true. Bracketed clauses are kept **only** if their gate passed. Fill X/N from `reports/`.

**SupplyzPro Smart Operations.**
Refused cash-on-delivery orders are wasted delivery trips that SME sellers pay for. [Name] scores every incoming order for refusal risk before dispatch, sorts the ops queue by risk, and recommends one action per order: ship, confirm with the customer, or ask for prepayment. When the customer replies, the order is rescored live, so the dispatcher sees which risky orders became safe to ship. The impact number in the demo is simulated on synthetic data. The pilot plan measures it on real deliveries.

**Artefact Data & AI.**
We turn messy order chats in Darija, Arabizi and French into structured, verified signals: address precision, risk flags with exact quoted evidence, tone and confirmation. A monotone XGBoost model combines them with order data into a 0–100 risk score, with a reason built from per-feature contributions. Every LLM quote is checked against the customer's text, and every decision is versioned with the prompt and config that produced it. On 24 hand-written Tunisian conversations, extraction matched a native speaker's address-precision label in X/24. On 40 synthetic holdout orders, LLM-extracted features gave the same risk tier as ground truth in N/40. These are small curated sets, not production accuracy.

**Guepard AI Automation.**
The workflow runs end to end. An order message arrives [from WhatsApp through Meta's Cloud API sandbox], and it is extracted, scored and routed without a person touching it. A confirmation is drafted in the customer's language [and rewritten into their register, then checked by a second model from a different provider], and deterministic guardrails check every outbound message. The customer's reply automatically triggers a rescore with a visible reason diff. A human clicks send in this pilot. The design allows judge-gated autonomous sending for low-value, high-confidence orders.

**GOMYCODE × NVIDIA Real-World AI Impact.**
A Tunisian operations problem, solved with AI that handles how Tunisian customers actually write: Darija in Arabic script, Arabizi and French, often in the same message. The LLM only extracts and quotes. It never sets the score or sends a message on its own. The system keeps working when a provider fails: Groq falls back to Google Gemini, and if both are unavailable, rules take over. Every result shows which path produced it. Its limits are stated openly: synthetic training data, a sandbox messaging channel, and zone-based risk handled by confirming the order, never by refusing service.

**README eval sentence (paste-ready, fill in):**
"On 24 hand-written Tunisian WhatsApp-style conversations (6 Arabizi, 6 Arabic-script Darija, 6 French, 6 mixed), labeled by one native speaker [second-labeler agreement a/6], `gpt-oss-120b` with prompt `extract-v1` matched the address-precision label in X/24 and reached red-flag F1 of Y. Z% of its quotes did not appear in the message, and the verbatim check dropped every one of them. 8/8 injection variants left the risk tier unchanged. On 40 synthetic holdout orders written with phrases the prompt never saw, LLM-extracted features produced the same risk tier as ground truth in N/40. Small curated sets, not production accuracy."

---

## 8. Doc cleanup

Rules:
- Omar applies these edits in one commit at **09:15 Sat**, message "Align docs with council decisions". Time-box: 30 min, or Fedi takes it if Omar is behind.
- Line numbers refer to the files as of commit `d87901b`.
- Where a whole section is replaced, the replacement is this spec's section, pasted as is.
- The council spec itself goes into this folder (`docs/council-spec/`), sanitized: no personal-file references.

### PRD.md

| Line | Current | Replace with |
|---|---|---|
| 4 (after) | — | Add: "**Council update 26 Sept:** where this file conflicts with `docs/council-spec/`, the council spec wins." |
| 15 | "Use **20-40% refusal rate** … [VERIFY] …" | "Use **no refusal-rate figure** unless a source is shown on screen. Default wording: 'a large share of COD orders are refused at the door.'" |
| 16 | COD penetration "~70%" | "State 'most online orders here are paid cash on delivery' with no percentage unless sourced." |
| 17 | eGrow / SoukFlow / Shiprocket | "No competitor names in any submitted material (not verifiable in time)." |
| 24–31 | Must list (8 items) | Replace with the council MoSCoW Must list M-1…M-18 (§1). Keep #8 wording ("simulate-reply if WhatsApp is down"). |
| 33–36 | Should 9–11 | #9 → "Static template + prefilter + human click = Must; LLM rewrite + judge = Should (Sun, `DRAFT_LLM`)". #10 Impact dashboard → "**Won't** (ROI banner only)". #11 → "Should, gated **G5 Sat 17:30**". |
| 42 | "…Docker/deployment infra beyond `requirements.txt` + a run command." | "…native mobile. **In scope:** one Dockerfile and one hosted container (FastAPI + static frontend + seeded SQLite)." |
| 52 | LLM row: "`openai/gpt-oss-120b` or `qwen/qwen3.8-27b` (bake-off decides)" | "Groq `openai/gpt-oss-120b` (qwen only if it wins by ≥ 3/24) → `gpt-oss-20b` (only if buckets are per model) → **Gemini** [model VERIFY] → rules. Same Pydantic + evidence gate for every provider." |
| 55 | Frontend: "Next.js, **or** Streamlit if … by 26 Sept 22:00" | "Static React bundle (Vite + React + TS; Next.js `output:'export'` only if Montassar is faster), served by FastAPI on one origin. Streamlit only if gate **G4 fails at Sat 16:00**. Never both." |
| 59 | "any deployment work beyond the one public URL the WhatsApp webhook requires" | "any deployment work beyond the one hosted container" |
| 69 | "~500 synthetic, weak-labeled rows" | "10,000 synthetic rows (8,000 train / 2,000 holdout) with simulated Bernoulli outcomes, zero LLM calls; disclose openly" |
| 70 | "bake-off on 20 hand-labeled dialect windows" | "eval on 24 hand-written dialect windows (G1), one frozen-prompt run" |
| 71 | "…**and say so on stage** if you fall back to it…" | "…every assessment shows a `path` badge (LLM / Fallback · Gemini / rules / cached); the video captions any fallback; the README has a 'live vs cached vs simulated' table." |
| 76–106 (§5) | Timeline | Heading note: "**Superseded** by `execution_plan.md` (council version): Saturday = build, Sunday = hardening + Should + video." L82 "~200-500 rows" → "10,000 rows". L87 → "Omar, by Sat 12:00 (G1)". |
| 122–132 (§7) | "Demo script (90 seconds, live typed input — not pre-recorded)" + "say so on stage" + Q&A | Title → "Demo = recorded 90-s video of a real run on the hosted build". Body → the council shot list (§4). Q&A line → "Limitations go in README + slide 5." |
| 141 | Names 3 awards | "Name SupplyzPro, Artefact, Guepard and GOMYCODE × NVIDIA Real-World AI Impact; **not** Kredete. Text in `docs/council-spec/` §7." |
| 155 | "…keep a human click… Say so directly — '…'" | "…keep a human click on every send. Shown by the UI chip 'Demo mode · a human approves every send' and a video caption." |
| 165 | Demo flow (WhatsApp) | Prefix "If G5 passes: …". Add: "Judges always use paste / 'Try this order' + simulate-reply (the sandbox accepts only registered numbers)." |
| 172 | "Expose the backend on a public HTTPS URL (tunnel such as ngrok, or a real deployment)" | "Point the webhook at the **hosted container** URL (tunnel = dev only)" |
| 173 | "…before 26 Sept 22:00" | "…by **Sat 17:30 (G5)**" |
| 176 | "public URL/tunnel is a live dependency during judging" | "The hosted URL is the judges' prototype; in public mode the webhook is unmounted and WA secrets are removed from the host." |
| 180 | "…switch to it and say so on stage." | "…switch to it; the caption and `path` badge disclose it." |
| 188–193 (§12) | Open items | Tick and annotate: refusal number → "no number"; competitors → "dropped"; roster → "Omar, Sat 12:00"; freeze owner → "Fedi (Omar may only cut)"; threshold → "150 TND (assumption, labeled)"; WhatsApp → "G5 Sat 17:30". |

### execution_plan.md

| Line | Current | Replace with |
|---|---|---|
| 5 | "~4h15 … Everything else is pre-event prep…" | Add: "**Saturday is the build day (hero loop green by 18:00). Sunday is hardening, gated Should items and the video.**" |
| 13 | Omar lane | Add "Gemini fallback (Stage A), eval G1/G2/G3, hero golden E1". Replace "`demo_orders.json`" with "seeded assessments + extraction cache". |
| 14 | Jesser lane: "Meta dev app…", "no-timer" etc. | "DB + repos, `/api` endpoints, worker + debounce + `process_due`, seed on boot + reset, **public-mode sandbox visibility + caps**, WhatsApp webhook **code** (Meta admin → Montassar), static template insert + send endpoint. No-reply timer = Could." |
| 15 | Montassar: "public HTTPS URL (tunnel or deploy)… fallback drill" | "Frontend (static React bundle), **hosted container** (Dockerfile, single origin), Meta admin setup, CI + badge + test harness, `APP_MODE` flips (Sat 22:00 → public, Sun 08:00 → event, Sun 16:45 → public), fallback drill, submission-link audit" |
| 16 | Fedi: "hand-labels the 20 bake-off windows" | "writes and labels the **24 G1 windows**, injection and bad-draft case data, templates, **6 slides**, README narrative, video script/VO/edit, submission form, award text" |
| 20 | "frozen by 26 Sept 18:00" | "Council draft mocks adopted now; frozen **Sat 12:00 (G2)**; after that, additive changes only" |
| 23–27 | "Frontend decision (made once, at 26 Sept 22:00)" + "Jesser enables CORS" | "**Frontend gate G4, Sat 16:00, on the hosted URL:** queue renders the mocks + detail pane with RTL bubbles → React stays; else Streamlit from 16:00. Never both. Same origin, so **no CORS**." |
| 31–45 | 9-feature contract + "cut to the first 4" | "**6 features, monotone `(-1,1,1,1,1,1)`:** `address_specificity, red_flag_count, tone_score, price_tnd, zone_encoded, customer_refusal_rate`. `has_geo_pin` is an override, not a feature. `zone` comes from `zone_from_text` over verified quotes." |
| 49–57 | Pre-event table (~4/3/5/4/5 h) | Replace with the council Saturday budgets (§2): Omar ~11.0, Jesser ~11.0, Montassar ~11.5, Fedi ~11.5, with blocks and gates. |
| 59–67 | Sample rows (78/22/18) + weak-label formula | Delete. Replace with: "Labels: `refused ~ Bernoulli(sigmoid((S−43)/12))` (Alchemist spec). Hero numbers come **only** from `tests/golden/hero.json`." |
| 71–85 | Event-day timeline | Replace with the council Sunday table (§2). Key changes: 08:00 event flip, D1 checks incl. Gemini, Sprint 2 = S-3/S-2/S-8 (not integration), 15:45 capture, 16:45 public flip + tag, 16:50 audit, **17:10 submit**. |
| 91–93 | Checkpoints | 11:30 → D2; 13:00 → D4 (`DRAFT_LLM` on/off); 15:30 → freeze + Sunday cut order `C-* → S-7 → S-10>20 → S-6 → S-9 → S-8 → S-2 → S-3 → S-4`. |
| 94 | "video recorded (live input, or disclosed fallback)" | "video exported by 16:40 (day-of take or safety take); incognito audit 16:50; submit by 17:10" |
| 96 | "If Groq fails… switch to the cached `demo_orders.json` and say so on stage…" | "**If Groq fails:** the chain falls to `gpt-oss-20b` → Gemini → rules automatically; the `path` badge shows which, and the video caption states it. Seeded orders carry pre-computed assessments, so the queue never needs an LLM to render." |
| 98 | "…and say so on stage." | "…the caption and badge disclose it. WhatsApp is never the judges' path." |
| 113–120 | Pitch script incl. "20-40%", "judge-approved", Q&A | Replace with the council shot list (§4). Remove "20-40%"; "judge-approved" only if D4 passed; Q&A line → "Limitations: README + slide 5"; "20 labeled samples" → "24 hand-written conversations". |

### SYSTEM_DESIGN.md

| Line | Current | Replace with |
|---|---|---|
| 13–31 (§1 diagram) | Tunnel implied; "Groq API (extraction, judge, optional Whisper)"; "Dashboard (Next.js; Streamlit fallback) ──HTTP──▶" | LLM box: "Groq (gpt-oss-120b → 20b) → Gemini (fallback; judge if S-3) → rules". Dashboard line: "Static React bundle served by FastAPI at `/` (same origin, one hosted container)". Add a note: "`APP_MODE=public` (default): webhook unmounted, sends off, visitor sandbox." |
| 159 | `model_score … -- classifier probability × 100` | "`-- P(refused) × 100 from binary:logistic on simulated Bernoulli labels; shown in UI as 'risk score (0–100)'`". Also add the columns `sandbox_id` (customers/conversations/orders), `messages.template_id`, `messages.canonical_text`, `messages.origin`, `extraction_runs.provider`, and the `path` value `'fallback_provider'`. |
| 198, 251 | "78 → 31", "▼ 47", "→ 78 · … → 31" | "v1 → v2 (numbers from `tests/golden/hero.json`)"; example reason diff without hard numbers. |
| 245 | "must be labeled that way on stage" | "are labeled that way in the UI (reply-adjustment chip), the video caption and the README" |
| 318–319 (§6.2) | Judge = bake-off loser | "Judge = Gemini if the Gemini tier passed D1; else qwen on Groq [VERIFY]; else `gpt-oss-120b` with `same_family=true`. Fails closed. Add row: **Fallback extraction = Gemini** (JSON mode, same repair/Pydantic/evidence gate; Stage B adds `to_gemini_schema`)." |
| 349, 359–360, 407–408 | `has_landmark`, `has_building_or_apt` in schema + Pydantic | Remove both; add `tone_evidence` (string\|null) before `tone`. **12 fields** in Alchemist/Oracle order. |
| 531–542 (§6.6) | "20 hand-labeled windows — 6/5/5/4 … 3 replies … 2 injection"; "full 20 once per model" | "**G1: 24 windows** (6 Arabizi / 6 Arabic-script / 6 French / 6 mixed; 4 replies incl. ack + address change; 2 non-orders; 2 injection). Eval mode (no fallback, cache or cascade); iterate on 5 windows outside G1; freeze; one run. A challenger needs ≥ 3/24. Second labeler on 6 (Should). G2 = 40-row synthetic tier agreement. G3 = 8 injection variants." |
| 556 | "Warm the cache … right before going on stage" | "…right before recording (use a non-hero text; the recording uses the hero variant, so the extraction is live)" |
| 557 | "holdout eval (50 rows)" | "G2 holdout (40 rows) on another teammate's org" |
| 584–590 (§7.1) | Weak label + noise, "holdout" | Add: "10,000 rows; label `refused ~ Bernoulli(sigmoid((S−43)/12))`; ≥ 30% of phrases `eval_only`; zero LLM calls (enforced by a test)." |
| 593–595 (§7.2) | "Same as the execution_plan feature contract, plus `has_geo_pin`" | "6 monotone features (see `execution_plan.md`); `has_geo_pin` = override only." |
| 713 etc. (§10) | Routes without prefix | Prefix all with `/api`; add `POST /api/sandbox/try`, 409 `SEEDED_READONLY`, `rescore_state`, `segments` in the detail response. |
| 722 | "`GET /health` … check before going on stage" | "`GET /api/health` (`mode`, `wa_send`, `webhook`, providers, `live_calls_today/cap`, `GIT_SHA`) — checked Sun 08:30, before recording, and in the 16:50 audit" |
| 726–743 (§11) | "UI (Next.js; Streamlit fallback)", 22:00 decision, CORS, mocks frozen 18:00, `{start,end}` spans, escape-then-mark | Title "UI (static React bundle; Streamlit only if G4 fails Sat 16:00)". Same origin, no CORS. Mocks frozen Sat 12:00. The API returns server-built **`segments`** per message; React renders text nodes; Streamlit escapes each segment separately. Delete the escape-then-mark sentence. |
| 775 (§13) | `FRONTEND_ORIGIN=…` | Delete. Add `APP_MODE`, `GEMINI_API_KEY`, `GEMINI_MODEL` [VERIFY], `JUDGE_PROVIDER`, `LLM_CHAIN_EXTRACT`, `LIVE_LLM_DAILY_CAP`, `ADMIN_TOKEN`, `DRAFT_LLM`, `WEBHOOK_ENABLED`. |
| 797 (§14 #9) | "Tunnel or network drops on stage" | "Host down or asleep during judging → `/api/health` keep-alive ping, snapshot mode (S-9), paste path always available" |
| 798 (§14 #10) | "(judge Q&A)… Say it first" | "Stated first in README + slide 5" |
| 807 (§14 #19) | "labeled in the UI and on stage" | "labeled in the UI, the video caption and the README" |
| 813 (§14 #25) | "frozen by 26 Sept 18:00" | "frozen Sat 12:00 (G2); C3 test checks mocks ↔ models" |
| 819–823 (§15 pre-event) | Lanes due 22:00, Next-vs-Streamlit at 22:00 | Replace with the council Must list and Saturday gates (§1, §3). |
| 834 | "Impact page" (Should) | "Impact page → Won't (ROI banner is Must)" |
| 839–847 (hero demo) | "60 seconds, … HIGH 78 … The judge approves … LOW 31" | "**Recorded 90-s video** (council §4). Numbers from `hero.json`. WhatsApp opening only if G5 passed; judge only if D4 passed; hero at 220 TND, 3 flags, rural; the reply carries building + landmark + time + 'ey'." |
| 851–858 (§16) | Checklist | Add: Groq per-model vs per-org bucket test; Gemini `models.list` + one JSON-mode call; host restart-on-env-change; host sleep/cold start; pre-recorded video allowed; video length limit. Remove the Prompt Guard line (Won't). |

### hackathon_playbook.md

| Line | Current | Replace with |
|---|---|---|
| 34 | "working prototype, source link, presentation, 90-second video" | Append: "The prototype link must work after the event with no laptop running → one hosted container, public mode." |
| 35 | "**Responsible AI (10 pts) favors business data over personal data.** Orders/transactions/logistics data scores cleaner…" | "**Responsible AI (10 pts).** [VERIFY the guide's exact wording.] Our system handles personal data: customer names, phone numbers, addresses and free-text chats. The honest story: synthetic data only in the build; phones masked in the API/UI; the judge never sees raw customer text; free-tier LLMs used only with synthetic data; a human approves every send; zone risk handled by confirming, not refusing service." |
| 43 | "Guepard (the drafted-message/judge-in-the-loop automation)" | "Guepard (the end-to-end order → score → confirm → reply → rescore workflow; the judge is mentioned only if it ships)". Add: "Kredete: **not claimed**." |
| 44 | "**Responsible AI**: business data (addresses/notes/order history), not sensitive personal data — cleaner story here." | "**Responsible AI**: addresses, notes and phone numbers are personal data; see the council RAI list (synthetic-only, masking, human send, stated limits)." |
| 47 | "See `handoff.md` … (web app not mobile, PWA wrapper, … impact screens …)" | "See `PRD.md`, `SYSTEM_DESIGN.md`, `execution_plan.md` and `docs/council-spec/`. `handoff.md` is historical." |

### handoff.md

| Line | Current | Replace with |
|---|---|---|
| 1 (before) | — | Banner: "> **Superseded 26 Sept. Historical only.** Do not use this file for numbers, scope or screens. Canonical: `PRD.md`, `SYSTEM_DESIGN.md`, `execution_plan.md`, `docs/council-spec/`." |
| 3 | "…get refused 40-60% of the time…" | "…get refused at the door often enough that sellers track refusal rate as a cost (no sourced figure)…" |
| 9 | PWA (~30 min) | "PWA: **Won't** for the hackathon." |
| 18 | "(mocked) 'connect your store' button" | Strike: "Won't." |
| 19 | "Impact Dashboard" | "Won't: ROI banner only (labeled simulated)." |
| 30 | "Same extraction call can also emit a drafted outbound message" | "Superseded: outbound = rule-chosen static template + prefilter; the LLM rewrite is a separate Sunday Should item (SD §8)." |
| 58 | "WhatsApp-style chat bubble mock … vs. real … integration" | "Decided: WhatsApp Cloud API sandbox, gated G5; paste/simulate-reply is the judges' path." |

**Also:** `.gitignore`: append Skeptic's App. C block + `.claude/`, `var/`, `web/dist/`, `*.db*`. The council folder is not tracked today (`git ls-files` shows only the 6 files), so keep it that way before the visibility flip.

---

## Unresolved items (need a human or a real call)

1. [VERIFY] Whether the participant guide allows a video recorded before the event (the safety take). If not, it becomes a rehearsal, and the storyboard carries over.
2. [VERIFY] The Gemini free-tier model id, JSON-mode parameter names, and data-use terms. This decides whether M-8 runs live or ships as code plus fixture tests only.
3. [VERIFY] Whether Groq rate buckets are per model or per org. This decides whether `gpt-oss-20b` stays in the chain.
4. [VERIFY] Host free-tier terms: always-on vs. sleep, and whether an env change restarts and reseeds the container.
5. [VERIFY] Who on the team reads Darija natively for S-5, and whether all four are free Saturday 09:00–22:00.
6. [VERIFY] Whether the Final Team Confirmation (due 26 Sept) has already been sent.
