# Gate checklists, by person

> Built from [07 §2–3](07-scope-schedule-delivery.md) (hour blocks and gates), [05 §7](05-testing-ci.md) (definition of done), [06 §1.4](06-frontend-ux.md) (frontend gates), [04 §3](04-security-public-mode.md) (runbook and audit), with the [Conductor rulings](README.md#6-conductor-rulings) applied where those files disagree. If this file and a spec file disagree, the spec file wins. Fix this file.

**How to use it:** each person ticks their own section. At every gate, the owner reads their boxes out in the sync. A gate passes only when **every** box for that gate is ticked across all four people. If a box can't be ticked, apply the "If it fails" line right away, not later.

## Open decisions (settle at G0 09:15)

The spec gives two answers for each of these. Omar picks one at G0 and edits this file.

| # | Topic | Answer A | Answer B |
|---|---|---|---|
| O1 | When the repo goes public | Sat 22:00–22:30 after secret scan #1 (07 M-18, G7; Montassar's block) | Sun ~16:47 after secret scan #2 (04 §3.1, §6.3) |
| O2 | Eval report file name | `reports/g1_extract_v1.json` + `reports/g3_injection.json` (07 §3) | `reports/eval_extraction.json` (05, 08 AC-03.4) |
| O3 | Who opens which link in the 16:50 audit | Jesser: video + slides · Montassar: URL + repo · form preview per `FEDI.md` §4.8 | settled in `FEDI.md` §4.8 |
| O4 | Omar's G1 checks | due at G1 12:00 (07 §3) | run in Omar's 12:15–13:00 block (07 §2) |

---

## Gate index

| Gate | Time (Tunis) | Passes when | Omar | Jesser | Montassar |
|---|---|---|---|---|---|
| FE0 | Sat 09:00 | Frontend stack chosen | | | ● |
| G0 | Sat 09:15 | All four free to 22:00; stack chosen; Darija reader known | ● | ● | ● |
| G-seams | Sat 10:30 | Seams + harness on `main`; `make check` green on 4 laptops | ● | ● | ● |
| G1 | Sat 12:00 | Keys, host hello-world, Meta token, team confirmation | ● | | ● |
| G2 | Sat 12:00 | `ScoreResult` + mocks frozen and C3-valid | ● | ● | |
| FE1 | Sat 13:00 | Queue renders from mocks locally | | | ● |
| T0 | Sat 14:00 | Seams + CI badge + U1 U16 U23 C2 green | ● | ● | ● |
| G3 | Sat 14:00 | Content received from `FEDI.md`: banks (F2), ≥ 12 of 24 windows (F3), templates (F4) | ● | | |
| G4 | Sat 16:00 | Frontend's 5 checks pass on the hosted URL | | | ● |
| Flip → event | Sat 16:15 | Container in `event` for phone tests (R5) | | ● | |
| G3b | Sat 16:30 | `extract-v1` frozen, prefix ≤ 2.8K tokens | ● | | |
| G5 | Sat 17:30 | Real phone message → hosted webhook → order row; flip back to `public` | | ● | ● |
| G6 | Sat 18:00 | Hero loop green on the hosted URL | ● | ● | ● |
| Eval | Sat 19:00 | G1 + G3 reports committed | ● | | |
| Smoke | Sat 20:00 | M3 smoke on hosted URL; public-mode P1–P6 merged | ● | ● | ● |
| G-Gem | Sat 20:00 | Gemini Stage A green | ● | | |
| G7 | Sat 22:00 | 16 ★ tests green; public build; safety take captured | ● | ● | ● |
| Flip → event | Sun 08:00 | `event` mode live (only if G5 passed) | | | ● |
| D1 | Sun 09:00 | Morning checks green | ● | ● | ● |
| D2 | Sun 11:30 | Hero loop over the venue network | ● | ● | ● |
| D3 | Sun 12:30 | Gemini Stage A (only if it slipped) | ● | | |
| D4 | Sun 13:00 | Rewrite + judge on or off | ● | | ● |
| Briefing | Sun 13:45 | Every submission field re-checked | ● | ● | ● |
| D5 | Sun 15:30 | Feature freeze | ● | ● | ● |
| D6 | Sun 16:40 | Final cut exported | ● | ● | ● |
| Flip → public | Sun 16:45 | Public mode, WA secrets gone, tag `submission-v1` | ● | | ● |
| Audit | Sun 16:50 | Incognito audit passes | | ● | ● |
| D7 | Sun 17:10 | Form submitted | ● | | |

---

## Omar (lead, AI/ML, merges)

### Saturday

**G0 · 09:15**
- [ ] All four present and free until 22:00. Anyone with < 9 h → apply the cut order (07 §1) now
- [ ] V7: who reads Darija natively (eval windows, S-5 second labeler; `FEDI.md` F3) is confirmed
- [ ] Open decisions O1–O4 settled and written into this file
- [ ] Doc cleanup (07 §8) started, 30-min time-box (R13)

**G-seams · 10:30**
- [ ] `app/contracts.py` (`Window`, `OrderCtx`, `ScoreResult`) merged
- [ ] `Clock`, `LLMClient` + `ReplayClient` / `FailingClient`, stub `score_order` merged (with Jesser, Montassar)
- [ ] `make check` green on all 4 laptops
- If it fails: you freeze the seams on your own at 10:45

**G1 · 12:00** (see O4)
- [ ] V1: Final Team Confirmation sent (check it wasn't already done)
- [ ] V3: `GET /models` answers on all 5 Groq orgs; `gpt-oss-120b` / `20b` / qwen active on the demo org
- [ ] V3: two parallel calls on the demo org → buckets are per model or per org (recorded)
- [ ] V4: Gemini `models.list` shows a free Flash-class model; JSON-mode parameter names checked in the installed `google-genai`
- If buckets are per org: chain = 120b → Gemini → rules (20b removed)
- If the Gemini key fails: build Stage A against a hand-made fixture, retry the key at D1, README states the status

**G2 · 12:00**
- [ ] `ScoreResult` fields frozen with Jesser; `mocks/orders.json` + `mocks/order_detail.json` validate against the Pydantic models (C3)
- If it fails: you freeze them; after that, changes are additive only and a rename needs Montassar's OK

**T0 · 14:00**
- [ ] U1 ★ and U16 ★ green on CI (U23 with the eval data from `FEDI.md` F3)
- [ ] M-5a: 12-field schema, Pydantic repair, `NUM` helper, cross-field rules + U3 merged
- [ ] M-5b: defuse, `normalize_with_map`, spans → segments, evidence check, tone gate + U5 U7 merged
- [ ] M-7: Groq chain, extraction cache, daily cap + U14 merged
- [ ] M-6: D2/D3 prompt loaded, compact few-shots, `usage.prompt_tokens` measured

**G3b · 16:30**
- [ ] M-9 generator on the phrase banks (`FEDI.md` F2): 10,000 rows, `eval_only` tagging, no-LLM import test (ML10)
- [ ] Prompt iterated only on 5 windows **outside** G1
- [ ] `extract-v1` frozen; prefix ≤ 2.8K tokens, measured
- [ ] V9: tokens per call noted → caps re-derived (R6: public 80 calls/day, 120K tokens/model/day)
- If it fails: freeze whatever exists at 17:00. Any later change = `extract-v2` + a full G1 rerun

**G6 · 18:00**
- [ ] M-10: XGBoost (6 monotone features), `scoring.yaml`, reasons, `resolve_flags`, `choose_template`, prefilter, `impact.json`
- [ ] E1 green: v1 model 75–92, HIGH, |final − 65| ≥ 10; v2 final ≤ 25, LOW; clean and stale v2 give identical features
- [ ] `tests/golden/hero.json` written; `HERO_V1` / `HERO_V2` pinned; U17 green
- [ ] Real `score_order` wired into Jesser's worker on the hosted build
- [ ] With no Groq key, the rules path still scores
- If it fails: Gemini Stage A and the G2 synthetic eval move to Sunday; all hands on the hero. Still red at 20:00 → the safety take shows the true tier with an honest caption; tune `scoring.yaml` (not the model) in Sunday Sprint 1

**Eval · 19:00**
- [ ] U28 and U30 green before the run
- [ ] G1 run: eval mode, one model, no fallback / cache / cascade → report committed (O2)
- [ ] G3 injection run (8 variants, or 4 if G3 slipped) → report committed
- [ ] `make record` (L5) after G3b → `data/llm_replay/` refreshed
- [ ] G2 synthetic eval started unattended on Jesser's dev org
- If it fails: commit by 20:30 with the N that exists

**Smoke · 20:00**
- [ ] Your part of public mode merged: LLM caps inside `LLMClient` (per-visitor + global → `path=rules` + banner, never a 429)

**G-Gem · 20:00** (R2)
- [ ] `GeminiBackend` in JSON mode, through repair → Pydantic `extra="forbid"` → evidence check
- [ ] U14 Gemini branch, C1 `fallback_provider`, E3 `fail_groq` green
- [ ] Recorded fixture `fixtures/llm/gemini/extract_hero_v1.json` parses through `OrderExtraction`
- [ ] `/api/health?deep=1` shows `gemini: ok`
- If it fails: your first Sunday task (11:45), hard stop D3 12:30

**21:00 (only if G6 and G-Gem are green)**
- [ ] S-11a text baseline: `python -m ml.text_clf train` + `eval`, ML14 green, baseline row in the eval table (03 §14)
- [ ] Then S-7 qwen bake-off, only if S-11a is done

**G7 · 22:00**
- [ ] Your ★ tests green on CI: U1 U3 U5 U7 U14 U16 U17 C1 E1 E4
- [ ] U24 U28 U29 U30 J14 U12 merged with their code
- [ ] Model + card committed; eval reports committed; `data/llm_replay/` recorded after G3b
- [ ] Gemini either merged with its tests or still on its branch (never half-merged)
- [ ] Secret + phone scan #1 (04 §6.2) prints nothing
- [ ] Backend watched during the safety take
- If anything is red: it's Sunday work, and only if it's a Must

### Sunday

**D1 · 08:30–09:00**
- [ ] `GET /models` on the Groq demo org; Gemini `models.list`
- [ ] `/api/health?deep=1`: one fixture per provider
- [ ] Warm-up call
- If it fails: switch that item to its fallback (rules / Gemini off) and flag it for the captions (`FEDI.md` F14)

**D2 · 11:30**
- [ ] E1 green on `main`; provider chain healthy
- If it fails: no new work until it's green

**D3 · 12:30** (only if Gemini slipped)
- [ ] Gemini Stage A green (11:45–12:30)
- If it fails: ship code + fixture tests, `GEMINI_ENABLED=false` in the hosted build, README line with the reason; S-3 stays cut

**D4 · 13:00**
- [ ] S-3 rewrite + judge behind `DRAFT_LLM`: verdicts on 12 drafts, fails closed, J16 green
- If it fails: `DRAFT_LLM=off`, static draft shown, no judge claim anywhere

**13:45 briefing**
- [ ] Every checklist field (`FEDI.md` §5.3) re-checked against what the organisers say

**D5 · 15:30**
- [ ] S-6 cascade (14:00–14:30, hard stop); S-4 Gemini Stage B (14:30–15:00); S-11b only if S-6 finished early
- [ ] README eval + test numbers filled only from `reports/` (15:00–15:30)
- [ ] ≥ 34 tests green on CI; E3 R1 R2 green; tag `v-freeze` (CI green on it)
- After 15:30: only bug fixes with a reproducing test

**D6 · 16:40**
- [ ] 15:45 warm-up call on a non-hero text
- [ ] Backend watched during capture; takes reviewed against 04 §6.4 before upload

**Flip → public · 16:45**
- [ ] Secret scan #2 (04 §6.2) prints nothing
- [ ] Tag `submission-v1` only after Montassar's public `make smoke` is green and CI is green
- [ ] Repo visibility per O1

**D7 · 17:10**
- [ ] Screenshot of the submission receipt kept

---

## Jesser (backend, messaging)

### Saturday

**G0 · 09:15**
- [ ] Present and free until 22:00

**G-seams · 10:30**
- [ ] `Clock`, sync `process_due(now)`, `make check` target, repo skeleton merged (with Omar)

**G1 · 12:00**
- [ ] System User token received from Montassar (handover by 11:30)
- If Meta is blocked: WhatsApp is dropped now; your 16:15–17:30 block goes to M-2 and tests

**G2 · 12:00**
- [ ] `schema.sql` with `sandbox_id`, `template_id`, `canonical_text`, `provider`, `path='fallback_provider'`; repos
- [ ] C2 green (stub result inserts; `version` 1 → 2)
- [ ] `api/models.py` + mocks validate (C3); additive fields `seed_key`, `llm.visitor_cap`, `injection_suspected` confirmed (R8)

**T0 · 14:00**
- [ ] C2 ★ green on CI
- [ ] Endpoints: ingest (paste/CSV), list, detail with `segments`, health, `simulate-reply`, rescore, draft send
- [ ] V8: package names and pins resolved (`python-ulid`, `google-genai`); `requirements.txt` `==`-pinned

**Flip → event · 16:15** (R5)
- [ ] Worker + debounce + versioned assessments + `rescore_state` + static template insert; J10 J11 green
- [ ] M-1: seed on boot (12 orders + hero), `POST /api/admin/reset`, J12 green
- [ ] Hosted container flipped to `APP_MODE=event` for the S-1 phone tests

**G5 · 17:30**
- [ ] Webhook: GET verify, POST HMAC signature, dedupe, statuses ignored, maps to ingest, fails closed on an empty secret (W1–W6)
- [ ] A real phone message reaches the **hosted** webhook with a valid signature and an order row appears
- [ ] Flipped back to `public` at 17:30, **pass or fail**, WA secrets deleted from the host (R5)
- If WhatsApp was dropped at G1: do the flip pair once at 17:30 (10 min) to prove restart + reseed
- If G5 fails: WhatsApp becomes a roadmap line; the G5 decision is written down

**G6 · 18:00**
- [ ] Hero integration with Omar on the hosted URL: paste → v1 HIGH → `T_ADDRESS` insert → simulate-reply → v2 LOW with reason diff

**Smoke · 20:00**
- [ ] M-2: visibility helper, seed loader with `sandbox_id`, 409 `SEEDED_READONLY`, per-visitor + global caps, 5 sandbox P0 tests
- [ ] C3 re-run with Montassar against the frozen mocks
- If sandbox isolation isn't working by G7: shared DB + reseed every 30 min + admin reset, and the decision is written down

**G7 · 22:00**
- [ ] C2 C3 J10 J11 J12 green on CI
- [ ] J15 J19 C4 P2 P3 P4 P7 merged with their code (or the shared-DB fallback is recorded)
- [ ] `make seed` and `make demo-reset` work; `.env.example` complete
- [ ] WhatsApp: J1–J3 + `reports/whatsapp_e2e.md` 5/5, **or** the G5 roadmap decision recorded (20:30–21:00)
- [ ] Played "customer" for the safety take

### Sunday

**D1 · 08:30–09:00** (only if G5 passed)
- [ ] Meta callback re-verified; token valid; one phone message → hosted webhook → order row
- If not fixed by 09:00: `WEBHOOK_ENABLED=false`, paste + simulate-reply path, caption per 04 §1 row 11

**D2 · 11:30**
- [ ] Paste → v1 works on the hosted URL over the venue network

**D4 · 13:00**
- [ ] S-2 outbound send (only if G5) 11:45–12:15
- [ ] S-10 tests: U4 U8 U12 U13 + sandbox P0

**13:45 briefing**
- [ ] Attended; nothing in your lane contradicts the field list

**D5 · 15:30**
- [ ] Fallback drill with Montassar (Groq key removed → Gemini → rules; all keys removed → rules) → `reports/fallback_drill.json`
- [ ] S-10: lead the push to ≥ 34 tests on CI

**D6 · 16:40**
- [ ] 15:45 `POST /api/admin/reset`; extraction cache cleared or script text varied, so the badges read `LLM · gpt-oss-120b`
- [ ] Phone on Do Not Disturb; played "customer" in the takes

**Audit · 16:50** (O3)
- [ ] Opened your assigned links in incognito on phone data; each one plays or loads

---

## Montassar (frontend, infra, CI)

### Saturday

**FE0 · 09:00**
- [ ] Stack decided and recorded: Vite + React + TS (default), Next static export only if clearly faster
- If you're not going with React: Streamlit from the first frontend block

**G0 · 09:15**
- [ ] Present and free until 22:30

**G-seams · 10:30**
- [ ] `conftest.py`, `Makefile`, `hygiene.sh`, `ci.yml`, `constraints.txt` on `main`

**G1 · 12:00**
- [ ] Host picked; Dockerfile; hello-world (static page + `/api/health`) live: `mode=public`, `wa_token_present=false`
- [ ] CI yaml + badge
- [ ] Meta: dev app, WhatsApp product, test number, 2 phones registered, System User token handed to Jesser by 11:30
- If the host fails: second candidate by 13:00; nothing by 14:00 → laptop tunnel on event day + S-9 snapshot on a static host as the judges' link

**FE1 · 13:00** (early exit)
- [ ] With `VITE_DATA_SOURCE=mock`, `npm run dev` shows the queue from `mocks/orders.json` with tier badges; clicking a row sets `?order=`
- If it fails: Streamlit from 14:15

**T0 · 14:00**
- [ ] `conftest` harness (clock, db, client, `wa_post`); CI green, badge in the README
- [ ] V5: host always-on vs sleep, cold start, restart on env change, disk persistence, `PORT` injection, auto-deploy pinning (recorded)

**G4 · 16:00** (R3; show Omar in ≤ 5 min)
- [ ] 1. Queue: every mock row renders with tier badge, `▼69` on #2613, `Scoring…` on #2614, action pill, `reason_short`, status, chips; summary strip correct
- [ ] 2. Detail: #2613 in the right pane, refresh keeps `?order=`, timeline v2 above v1 with the ×0.6 line and "Resolved: …"
- [ ] 3. RTL: #2604 Arabic bubble on the customer side and right-aligned; mixed bubble resolves RTL; Arabizi stays LTR
- [ ] 4. Highlights cover exactly the quoted words; `react/no-danger` lint and grep clean
- [ ] 5. Read-only seeded order shows only **Try this order**; `npm run build` → `web/dist` served by FastAPI **on the hosted URL**
- If it fails: Streamlit from 16:00, one framework, never both; draft panel → Sunday; safety take slips to 21:30–22:30

**G5 · 17:30**
- [ ] Support Jesser on the hosted webhook if needed (Meta console)

**G6 · 18:00**
- [ ] Live API, 3 s polling, `rescore_state` ghost card, paste dialog, simulate-reply, timeline + reason diff, path chip, on the hosted URL

**Smoke · 20:00**
- [ ] M-13: draft panel + Send ("sent (simulated)" in public mode); ROI banner labeled "simulated"
- [ ] M-2: `APP_MODE` settings, `X-Visitor-Id` middleware + header, **Try this order**, 2 h purge
- [ ] M1 health test green; M3 `smoke.sh` passes on the hosted URL

**G7 · 22:00**
- [ ] M-18: `.gitignore` block applied; secret grep (`gsk_`, `AIza`, `EAA`) clean
- [ ] Safety take captured against the hosted public build (21:00–22:00)
- [ ] P1 and P5 merged; `image` job green; M4 web job green
- [ ] `main` deployed in `public`, no WA secrets on the host; `make smoke URL=<hosted>` public-green
- [ ] Incognito check #1: 04 §3.3 items 1–6 pass
- [ ] Repo visibility per O1 (22:00–22:30 if answer A)

### Sunday

**Flip → event · 08:00** (only if G5 passed)
- [ ] `APP_MODE=event`, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `GROQ_API_KEY=KEY_EVENT`, `LIVE_LLM_DAILY_CAP=300` → restart
- [ ] `/api/health` shows `mode=event`, `wa_send=true`, `webhook=enabled`; `make smoke` event-green

**D1 · 08:30–09:00**
- [ ] Hosted URL loads on venue Wi-Fi **and** on phone data
- [ ] Admin reset done

**D2 · 11:30**
- [ ] Queue + detail work on the hosted URL over the venue network

**D4 · 13:00**
- [ ] S-8 activity feed; judge badge (if S-3); path chip polish

**13:45 briefing**
- [ ] Attended; hosted URL and repo fields confirmed

**D5 · 15:30**
- [ ] Fallback drill in the UI with Jesser
- [ ] S-9 snapshot mode (ships only if the bundle is also on a second static host, R7); hero-path polish only

**D6 · 16:40**
- [ ] 15:50–16:15: two takes captured against the hosted instance

**Flip → public · 16:45**
- [ ] `APP_MODE=public`, `GROQ_API_KEY=KEY_PUBLIC`, `LIVE_LLM_DAILY_CAP=80`; `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` **deleted** → restart (reseed wipes real rows)
- [ ] Meta webhook unsubscribed / callback removed
- [ ] Host pinned to `submission-v1` or auto-deploy off
- [ ] `make smoke URL=<hosted>` public-green → tell Omar to tag
- [ ] 16:48 snapshot capture (only if S-9 shipped)

**Audit · 16:50** (read 04 §3.3 aloud; ticking per `FEDI.md` §4.8)
- [ ] 1. `/api/health`: `mode=public`, `wa_send=false`, `webhook=disabled`, `wa_token_present=false`, `real_rows=0`
- [ ] 2. `POST /webhook/whatsapp` → 404
- [ ] 3. Only sample orders; no teammate names, phone numbers or `+216`
- [ ] 4. Try this order → HIGH with highlights → scripted reply → LOW with reason diff
- [ ] 5. A mutation on a sample order → toast, not a crash
- [ ] 6. A new pasted order scores (live, or rules with the banner)
- [ ] 7. Repo opens in incognito; no `.db`, `.env` or `.claude`
- [ ] 8. Video opens and plays

**During judging (daily)**
- [ ] Open the URL, run **Try this order**, health green

---

## Fedi

Fedi's tasks and checks are in [`FEDI.md`](../../FEDI.md), not in these gates. Where a gate above needs one of his deliverables, it names the `FEDI.md` item (F1–F16) as an input.
