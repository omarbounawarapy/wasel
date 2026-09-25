# Execution Plan — COD Risk Scoring, 27 Sept 2026

Companion to `PRD.md` and `hackathon_playbook.md`. This is the minute-level plan, merged from four workstream drafts, with overlaps reconciled. Team: **Omar (Lead)**, **Jesser**, **Montassar**, **Fedi**.

Total live coding time on event day: **~4h15**, across four fixed blocks. Everything else is pre-event prep or fixed program (opening, workshop, lunch).

---

## Roles (reconciled, no overlap)

| Person | Owns |
|---|---|
| **Omar (Lead)** | LLM extraction schema + prompt, feature contract (the exact fields the classifier expects), all merges to `main`, firefighting/edge cases during sprints |
| **Jesser** | FastAPI backend (4 endpoints), Streamlit frontend (Ingest/Queue/Detail pages), `requirements.txt` + `.env` setup, stretch: tiered-autonomy messaging (PRD §10) |
| **Montassar** | Synthetic dataset generator, weak-labeling heuristic, XGBoost training script, fallback/cache mechanism, WhatsApp Cloud API sandbox + webhook (PRD §11), final submission-link audit |
| **Fedi** | Pitch script, video, submission form, scope-gate checklist, UI copy pass |

**Note:** dataset generation and classifier training are Montassar's alone — an earlier draft of Jesser's plan also listed these; that's removed here to avoid duplicate work.

---

## Feature contract (locked — Omar defines, Montassar trains against it, Jesser's API returns it)

| Feature | Type | Source |
|---|---|---|
| `address_specificity` | float 0-1 | LLM extraction |
| `red_flag_count` | int | LLM extraction (`len(red_flags)`) |
| `tone_score` | int, encoded (neutral=0, uncertain=1, negative=2, positive=-1) | LLM extraction |
| `extraction_confidence` | float 0-1 | LLM extraction |
| `price_tnd` | float | order data |
| `zone_encoded` | categorical/int (urban=0, suburban=1, rural=2, or similar) | order data |
| `product_category_encoded` | categorical/int | order data |
| `customer_refusal_count` | int | customer order history |
| `customer_order_age_days` | int | customer order history |

If behind schedule: cut to the first 4 (address_specificity, red_flag_count, tone_score, price_tnd) — Montassar's plan explicitly allows shipping with 4 features instead of 8-9.

---

## Pre-event (tonight 25 Sept / tomorrow 26 Sept — commit to `main` by 26 Sept 22:00)

| Person | Task | Est. time |
|---|---|---|
| Omar | Draft Pydantic schema (fields above) + extraction prompt; test on 10-15 diverse sample orders (Arabic, French, vague, tone variants); write feature-contract doc | ~3.5h |
| Jesser | FastAPI skeleton: `POST /orders/ingest`, `GET /orders`, `GET /orders/{id}`, `POST /orders/{id}/action`; Streamlit multi-page skeleton (Ingest/Queue/Detail); `requirements.txt` + `.env` setup (moved from Montassar to make room for the WhatsApp work) | ~2h |
| Montassar | Synthetic dataset (300-500 rows, mixed Arabic/French addresses+notes); weak-labeling heuristic; XGBoost training script; fallback cache of ~10 pre-computed predictions (3 High/4 Med/3 Low) | ~3h |
| Montassar | WhatsApp sandbox: Meta dev app + WhatsApp product, register "customer" test numbers, long-lived System User token, `POST /webhook/whatsapp` + `GET` verification in FastAPI (coordinate with Jesser — same app), public HTTPS URL (tunnel or deploy), 5+ end-to-end phone → queue tests. **If not working by 26 Sept 22:00, drop it** — pitch it as roadmap, demo on CSV/paste | ~2-3h |
| Fedi | Fact-check and lock the pitch script (below); build the scope-gate checklist; pre-fill submission form (everything except video link, ~80%) | ~1.5-2h |

**Sample synthetic rows (Montassar's format):**

| order_id | price_tnd | zone | address_text | note_text | weak_label_score |
|---|---|---|---|---|---|
| ORD-2601 | 450 | Sfax-Rural | Douar Ben Amir, Route Principale, km 8.5 (après mosquée) | Client pas souvent à la maison | 78 |
| ORD-2602 | 89 | Tunis-Urban | Apt 4, Rue Bourguiba, Medina - 1008 | Client sera là samedi après 16h | 22 |
| ORD-2604 | 45 | Ben Arous-Urban | شقة 7، شارع المنستير، حي الخضراء | Livraison rapide SVP | 18 |

Weak-labeling formula: `score = address_vagueness*0.25 + price_percentile*0.20 + zone_risk*0.25 + customer_refusal_rate*0.20 + red_flag_density*0.10`, then `± random(-10,+10)` noise so it isn't trivially learnable.

---

## Event day — unified timeline

| Time | Program | Omar | Jesser | Montassar | Fedi |
|---|---|---|---|---|---|
| 08:30-09:00 | Check-in | Attend | Attend | Attend + restart tunnel, re-verify webhook URL in Meta console, confirm token still valid, send one test message from a registered phone | Attend |
| 09:00-11:15 | Opening, history session, NVIDIA workshop | Attend | Attend | Attend | Attend |
| **11:15-11:30** (15m) | Sprint 1 | Verify extraction+classifier run end-to-end | Verify FastAPI+Streamlit boot with no errors | Smoke test: data gen + model train + one prediction; one WhatsApp message → queue row | Confirm repo runs, sync with all three builders |
| 11:30-11:45 | Mentor checkpoint | — | — | — | — |
| **11:45-13:00** (75m) | Sprint 2 (hero feature) | Extract+validate 50 rows; first `main` merge; confirm feature contract with Montassar | Wire ingest → queue page; table sorted by risk, color badges (red/yellow/green) | Wire LLM extraction → feature frame → XGBoost; merge to `main` | Draft plain-English reason string wording; first UI copy pass; lock test-order set |
| 13:00-13:45 | Lunch | — | — | — | — |
| 13:45-14:00 | Submission briefing | Attend | Attend | Attend | Attend + pre-fill remaining form fields |
| **14:00-15:30** (90m) | Sprint 3 | Integration + explanation layer; full rehearsal <3s; second merge | Detail page: highlighted flagged text, reason, action buttons | Fallback engineering; rehearse demo under simulated API failure *and* simulated webhook/tunnel failure (switch to CSV/paste); verify submission links open | Full UI copy pass; submission form to 95%; rehearse script twice |
| 15:30-15:45 | Checkpoint | **Feature freeze — no new code after this point** | | | |
| **15:45-17:00** (75m) | Final sprint | Bug fixes only | Bug fixes only; help record if needed | Final audit: fallback tested, links verified | Dry run (15m) → record 2 takes (30m) → fix or accept fallback (15m) → final form fill (15m) |
| 17:00-17:30 | Submission workshop | Submit early | | | Submit; handle any last Q&A |

---

## Checkpoints (hard stop-and-fix rules)

- **End of Sprint 1 (11:30):** pipeline pieces run locally/independently, no crashes. If not: fix before Sprint 2, do not add scope.
- **End of Sprint 2 (13:00):** queue table visible, sorted, color-coded, clickable; 50 rows extracted and validated; first merge done. **If behind:** cut reason-string generation and action logic, ship scores+tiers only.
- **End of Sprint 3 (15:30):** full flow works — ingest → queue → detail with highlighted text + reason + action buttons — in one live run, <3s. **Feature freeze is absolute from here.** If behind: cut the highlighting (show raw text) before cutting the buttons.
- **17:00:** video recorded (live typed input, or disclosed fallback), submission form complete, all links verified to open in an incognito window.

**If the live API fails at any point during the demo:** switch to Montassar's cached `demo_orders.json` and say so on stage — "using cached predictions for reliability." Disclosed fallback reads as engineering judgment; a hidden one reads as dishonest.

**If the WhatsApp webhook or tunnel fails during the demo:** switch to CSV/paste ingest — same pipeline downstream, so nothing else changes — and say so on stage. Never let the WhatsApp path be the only way orders get into the demo.

---

## Scope-gate checklist (Fedi enforces on every "can we also add X?")

Ask in order, stop at the first NO:
1. **Is it must-have** per `PRD.md`'s scope list? → No: defer, stop.
2. **Does it unblock the hero feature** (queue + reason + action, visible in the demo's 0:20-1:20 window)? → No: defer, stop.
3. **Under 15 minutes per builder, with buffer left in the block?** → No: too risky, stop.

All three yes → greenlight. Any no → "not in scope, nail the hero first."

---

## Pitch script (90 seconds, locked by Fedi pre-event)

- **0:00-0:10** — "We predict which cash-on-delivery orders will get refused, so Tunisian sellers stop paying for wasted delivery trips."
- **0:10-0:20** — "In Tunisia, 20-40% of COD orders get refused — customer not home, address unclear, or they changed their mind. Every refusal costs fuel, time, packaging." *(20-40%, not 40-60% — see PRD's numbers-to-verify section; confirm with one real source before using on stage.)*
- **0:20-1:20** — live demo: paste orders → risk queue sorts by risk → click a high-risk order → show flagged phrases + plain-English reason → recommended action.
- **1:20-1:30** — the ROI stat on the synthetic set + next step (connect to a real store feed).

If asked about limitations in Q&A: synthetic data, not yet connected to a real store, multilingual extraction tested on curated cases — state plainly, don't oversell.
