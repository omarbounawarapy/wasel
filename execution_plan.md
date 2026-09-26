# Execution Plan — COD Risk Scoring, 27 Sept 2026

> **Council update (Sat 26 Sept 2026):** [`docs/council-spec/`](docs/council-spec/README.md) is now the build spec. Where this file conflicts with it, the council spec wins. The line-by-line edits that align this file are listed in [`docs/council-spec/07-scope-schedule-delivery.md` §8](docs/council-spec/07-scope-schedule-delivery.md) (Omar, Sat 09:15).

Companion to `PRD.md` (what/why) and `SYSTEM_DESIGN.md` (how). This is who does what, when. Team: **Omar (Lead)**, **Jesser**, **Montassar**, **Fedi**.

Total live coding time on event day: **~4h15**, across four fixed blocks. Everything else is pre-event prep or fixed program (opening, workshop, lunch).

---

## Roles (vertical split, no overlap)

| Person | Lane | Owns |
|---|---|---|
| **Omar (Lead)** | AI/ML core | Groq extraction (strict schemas, prompt, validation, cascade, bake-off — `SYSTEM_DESIGN.md` §6), synthetic generator with ground-truth features + seeded `catalog` (§7.1), XGBoost classifier, scoring rules + `scoring.yaml` (§7.4), reason strings, extraction eval, the cached `demo_orders.json`, all merges to `main`, firefighting |
| **Jesser** | Backend + messaging I/O | DB schema + repositories (§2.3), API endpoints (§10), rescore worker + debounce (§3.3), order state machine (§5), **WhatsApp webhook in/out** (§9: signature, dedupe, statuses, send), outbound drafts pipeline + templates + no-reply timer (§8), `requirements.txt` + `.env` |
| **Montassar** | Frontend + infra | Dashboard (§11): queue, conversation transcript, score timeline, drafts panel, activity feed; public HTTPS URL (tunnel or deploy) for the webhook; `/health` check; fallback drill; final submission-link audit |
| **Fedi** | Story, scope, language | Pitch script, video, submission form, scope gate, UI copy pass, outbound template copy (§8.1), **Darija/Arabizi/French phrase banks** for the generator, **hand-labels the 20 bake-off windows** against the rubric |

Interfaces between lanes, so nobody blocks on anyone:
- **Omar → Jesser:** a pure function `score_order(window, order_ctx) -> Assessment`. Jesser's worker calls it. Until Omar's is ready, Jesser uses a stub that returns a fixed assessment.
- **Jesser → Montassar:** the JSON shapes of `GET /orders` and `GET /orders/{id}` (§10), frozen by 26 Sept 18:00. Montassar builds against a mock of exactly those shapes until the real API is up.
- **Fedi → Omar:** phrase banks and labeled bake-off windows by 26 Sept 14:00.

### Frontend decision (made once, at 26 Sept 22:00)

- **Next.js** if Montassar's skeleton — queue page + detail page rendering the mock JSON — is working by 26 Sept 22:00.
- **Otherwise Streamlit**, with Montassar building it.
- **Never both.** Jesser enables CORS for the frontend origin either way.

---

## Feature contract (locked — Omar defines and trains against it; Jesser's API returns it; Montassar's UI shows it)

| Feature | Type | Source |
|---|---|---|
| `address_specificity` | float in {0, .25, .5, .75, 1} | code-mapped from the LLM's `address_level` enum (`SYSTEM_DESIGN.md` §6.3) |
| `red_flag_count` | int | LLM extraction, after the evidence check drops unverifiable flags |
| `tone_score` | int, encoded (neutral=0, uncertain=1, negative=2, positive=-1) | LLM extraction |
| `has_geo_pin` | bool | deterministic (WhatsApp location message) |
| `price_tnd` | float | **catalog lookup**, never the LLM |
| `zone_encoded` | categorical/int (urban=0, suburban=1, rural=2, or similar) | order data |
| `product_category_encoded` | categorical/int | catalog |
| `customer_refusal_count` | int | customer order history |
| `customer_order_age_days` | int | customer order history |

If behind schedule: cut to the first 4 (address_specificity, red_flag_count, tone_score, price_tnd).

---

## Pre-event (25–26 Sept — commit to `main` by 26 Sept 22:00)

| Person | Task | Est. time |
|---|---|---|
| Omar | Strict JSON schemas + Pydantic mirrors (§6.3), extraction prompt + few-shot, validation (§6.4), cascade (§6.8), the four key checks (§16), bake-off on Fedi's 20 labeled windows (§6.6) | ~4h |
| Omar | Generator: pick ground-truth `address_level`/flags/tone first, then render matching text from Fedi's phrase banks, and **save the ground truth alongside the text**. Seeded `catalog` (~15 products). Weak labels. XGBoost on the ground-truth features. `scoring.yaml`. `demo_orders.json` (10 pre-computed: 3 High / 4 Med / 3 Low) | ~3h |
| Jesser | SQLite schema + repositories; endpoints (§10) with the stub scorer; rescore worker + debounce; `simulate-reply`; WhatsApp webhook: Meta dev app + WhatsApp product, register the "customer" test numbers, long-lived System User token, `GET` verify + `POST` with signature check + dedupe; 5+ phone → order-row tests. **WhatsApp not working by 26 Sept 22:00 → drop it**; pitch it as roadmap and demo on paste | ~5h |
| Montassar | Next.js skeleton: queue + detail rendering the frozen mock JSON (the 22:00 decision above). Public HTTPS URL for Jesser's webhook (tunnel or deploy), kept stable across restarts if possible. `/health` page | ~4h |
| Fedi | Phrase banks: for each `address_level`, each flag code, and each tone, 5–8 real-sounding phrasings in Arabizi, Arabic-script Darija and French (**by 14:00**). Hand-label the 20 bake-off windows using the §6.3 rubric (**by 14:00**). Outbound templates ×3 languages (§8.1). Pitch script, scope gate, submission form ~80% | ~5h |

**Sample synthetic rows (generator output — ground truth saved alongside):**

| order_id | price_tnd | zone | customer text | gt `address_level` | gt flags | weak_label_score |
|---|---|---|---|---|---|---|
| ORD-2601 | 450 | Sfax-Rural | "Douar Ben Amir, route principale km 8.5 ba3d el jemaa. mouch dima fi dar" | `area_or_landmark` | vague_location, availability_uncertain | 78 |
| ORD-2602 | 89 | Tunis-Urban | "Apt 4, Rue Bourguiba, Medina 1008. Nkoun lahne samedi ba3d 16h" | `exact` | — | 22 |
| ORD-2604 | 45 | Ben Arous-Urban | "شقة 7، شارع المنستير، حي الخضراء. livraison rapide svp" | `exact` | — | 18 |

Weak-labeling formula: `score = address_vagueness*0.25 + price_percentile*0.20 + zone_risk*0.25 + customer_refusal_rate*0.20 + red_flag_density*0.10`, then `± random(-10,+10)` noise so it isn't trivially learnable.

---

## Event day — unified timeline

| Time | Program | Omar | Jesser | Montassar | Fedi |
|---|---|---|---|---|---|
| 08:30-09:00 | Check-in | `GET /models` on the demo key; one warm-up extraction | Re-verify the webhook in the Meta console; WhatsApp token still valid; one test message from a registered phone | Restart tunnel/deploy; `/health` all green | Confirm roster; attend |
| 09:00-11:15 | Opening, history session, NVIDIA workshop | Attend | Attend | Attend | Attend |
| **11:15-11:30** (15m) | Sprint 1 | `score_order` end-to-end on 3 fixtures | API boots; one WhatsApp message → order row | Frontend boots against the **real** API; queue lists orders | Sync with all three builders |
| 11:30-11:45 | Mentor checkpoint | — | — | — | — |
| **11:45-13:00** (75m) | Sprint 2 (hero loop) | Swap the stub for real `score_order` in Jesser's worker; cascade on; reason strings; **first merge** | Ingest + webhook → messages/orders → debounced rescore → versioned assessments persisted; `simulate-reply` works | Queue live: tier badges, ▲/▼ deltas, 3s refresh; detail shows the chat transcript (RTL-aware) | Reason-string wording pass; lock the demo test messages |
| 13:00-13:45 | Lunch | — | — | — | — |
| 13:45-14:00 | Submission briefing | Attend | Attend | Attend | Attend + pre-fill remaining form fields |
| **14:00-15:30** (90m) | Sprint 3 | Reply adjustments via `scoring.yaml`; extraction-eval number for the submission; **second merge** | Should-have: outbound drafts (template → rewrite → prefilter → judge via Omar's client → human-click send), delivery statuses, no-reply timer | Detail: evidence highlighting, score timeline with reason diff, drafts panel + send button, simulate-reply box; **fallback drill** (webhook down → paste; Groq down → cached) | Full UI copy pass; form to 95%; rehearse the script twice |
| 15:30-15:45 | Checkpoint | **Feature freeze — no new code after this point** | | | |
| **15:45-17:00** (75m) | Final sprint | Bug fixes; warm-up extraction right before recording (primes Groq's prompt cache) | Bug fixes; reset the demo DB to a clean seeded state before recording | Final audit: `/health`, every submission link opened in incognito | Dry run (15m) → record 2 takes (30m) → fix or accept fallback (15m) → final form fill (15m) |
| 17:00-17:30 | Submission workshop | Submit early | | | Submit; handle any last Q&A |

---

## Checkpoints (hard stop-and-fix rules)

- **End of Sprint 1 (11:30):** each lane runs on its own against the real neighbor, not a stub, with no crashes. If not: fix before Sprint 2, add no scope.
- **End of Sprint 2 (13:00):** a pasted order shows up in the queue, scored, tiered, with a reason; `simulate-reply` produces version 2 with a changed score. **If behind:** cut the cascade and reason diffs; ship score + tier + reason only.
- **End of Sprint 3 (15:30):** the full hero loop works in one live run — order in (WhatsApp or paste) → HIGH with highlighted evidence → confirmation → reply → LOW with reason diff. **Feature freeze is absolute from here.** If behind, cut in this order: outbound drafts, then highlighting (show raw text), then the timeline visual (keep the delta number).
- **17:00:** video recorded (live input, or disclosed fallback), submission form complete, all links verified in an incognito window.

**If Groq fails during the demo:** switch to the cached `demo_orders.json` and say so on stage — "using cached predictions for reliability." A disclosed fallback reads as engineering judgment; a hidden one reads as dishonest.

**If the WhatsApp webhook or tunnel fails:** switch to paste ingest + `simulate-reply` — same pipeline downstream — and say so on stage. WhatsApp is never the only way orders get into the demo.

---

## Scope-gate checklist (Fedi enforces on every "can we also add X?")

Ask in order, stop at the first NO:
1. **Is it must-have** per `PRD.md`'s scope list? → No: defer, stop.
2. **Does it unblock the hero loop** (order → HIGH + evidence → reply → LOW + reason diff)? → No: defer, stop.
3. **Under 15 minutes per builder, with buffer left in the block?** → No: too risky, stop.

All three yes → greenlight. Any no → "not in scope, nail the hero first."

---

## Pitch script (90 seconds, locked by Fedi pre-event)

- **0:00-0:10** — "We predict which cash-on-delivery orders will get refused, so Tunisian sellers stop paying for wasted delivery trips."
- **0:10-0:20** — "In Tunisia, 20-40% of COD orders get refused — customer not home, address unclear, or they changed their mind. Every refusal costs fuel, time, packaging." *(20-40%, not 40-60% — confirm with one real source before using on stage.)*
- **0:20-1:20** — the hero loop, live: a customer orders on WhatsApp in Darija with a landmark-only address → the queue shows **HIGH**, with the vague phrase highlighted as evidence → a confirmation goes out in the customer's own register (judge-approved, human click) → the customer replies with street + building + time → **the same order drops to LOW live**, with the reason diff on screen.
- **1:20-1:30** — the simulated ROI stat, labeled as simulated, plus the next step: real delivered/refused outcomes retrain the model.

If asked about limitations in Q&A: synthetic training data, WhatsApp sandbox not production, dialect extraction measured on 20 labeled samples — state plainly, don't oversell.
