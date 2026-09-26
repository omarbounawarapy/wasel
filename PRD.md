# PRD — COD Risk Scoring for Tunisian E-commerce

> **Council update (Sat 26 Sept 2026):** [`docs/council-spec/`](docs/council-spec/README.md) is now the build spec. Where this file conflicts with it, the council spec wins. The line-by-line edits that align this file are listed in [`docs/council-spec/07-scope-schedule-delivery.md` §8](docs/council-spec/07-scope-schedule-delivery.md) (Omar, Sat 09:15).

## GoMyCode "Come Build With AI" · 27 Sept 2026

Built from: `hackathon_playbook.md` (rubric/prize analysis) + 5-agent research pass (failure patterns, architecture, domain/market, roles, judging). Research agents ran on a small model and pulled from open web search — anything below marked **[VERIFY]** must be checked by a human before it appears in the pitch or video. Do not cite an unverified figure or company name in front of judges.

---

## 1. Problem & target user

Cash-on-delivery orders in Tunisian e-commerce get refused at a meaningful rate — customer not home, address too vague, changed their mind. Every refusal costs the seller a wasted driver trip (fuel, packaging, time) for nothing.

**Target user:** e-commerce sellers and delivery/logistics aggregators who already track refusal rate as a cost metric.

**Numbers to use in the pitch — corrected from research:**
- Use **20-40% refusal rate**, not the original 40-60% claim. Research found no strong public source for 40-60%; 20-40% is closer to what's cited. **[VERIFY]** with one real source before the video — even one credible citation beats a round number nobody can back up.
- COD penetration in Tunisia is high (research suggested ~70%, similarly high in Algeria) because of low card penetration and low trust in prepayment. **[VERIFY]** the exact percentage; the underlying "COD dominates here" claim is safe to state without a number if the number can't be confirmed in time.
- Possible existing players in this space: **eGrow** (AI return-prediction, Morocco/Egypt), **SoukFlow** (Tunisia logistics SaaS), Shiprocket (India, different market). **[VERIFY before the pitch mentions any of these]** — a small research model can fabricate plausible-sounding company names, and citing a competitor that doesn't exist is worse than citing none. If verified, frame them as "adjacent, not a direct Tunisia-specific pre-delivery refusal predictor" — that's still the claimed gap, just don't overstate it.

---

## 2. Scope (locked before build day)

**Must-have (the demo depends on these):**
1. CSV/paste ingest of orders (address, note, price, product, zone, customer ID)
2. LLM step: extract address-specificity, red-flag phrases, tone from free text
3. Classifier: risk score (0-100) + tier (Low/Med/High) from signals + order data
4. Rule layer: tier + value → recommended action (ship / confirm / prepay)
5. Plain-English reason string per order
6. Risk queue UI (sorted by risk) + order detail view showing the "why"
7. One aggregate ROI stat for the demo close (labeled as simulated)
8. Customer reply → versioned rescore with a visible reason diff (`SYSTEM_DESIGN.md` §4). This is the ending of the demo story, built on the same pipeline, and it can be driven by `simulate-reply` if WhatsApp is down

**Should-have (only after must-haves work end-to-end):**
9. Tiered-autonomy customer messaging — see §10 below for the settled design
10. Impact dashboard (before/after refusal rate, estimated TND saved)
11. Live WhatsApp ingestion via Meta's Cloud API sandbox/test number (see §11) — set up entirely pre-event; CSV/paste stays as the guaranteed fallback

**Nice-to-have (cut without guilt if behind schedule):**
12. Filter/search in the queue

**Explicitly out of scope — do not build:**
- Auth/multi-tenant accounts, real store integrations (WooCommerce/Shopify — mock the button only), model retraining UI, native mobile, Docker/deployment infra beyond `requirements.txt` + a run command.

**Hard rule from failure-pattern research:** pick ONE hero feature (the risk queue + explanation) and make it bulletproof. A second half-built feature scores worse than a first fully-working one.

---

## 3. Tech stack (locked — do not revisit on build day)

| Layer | Choice | Why |
|---|---|---|
| LLM extraction | Groq free tier: `openai/gpt-oss-120b` or `qwen/qwen3.8-27b` (bake-off decides), strict JSON Schema + Pydantic, verified quotes | Zero cost; strict mode guarantees the shape, code verifies the content — see `SYSTEM_DESIGN.md` §6 |
| Classifier | XGBoost on extracted features + order metadata | Default hyperparameters are fine — do not tune |
| Backend | FastAPI | Minimal boilerplate |
| Frontend | Next.js, **or** Streamlit if the Next.js skeleton isn't rendering the frozen mocks by 26 Sept 22:00 (decided once, never both) | Better chat/RTL rendering and demo polish; Streamlit remains the safe fallback — see `execution_plan.md` |
| Data | CSV / SQLite | No Postgres, no migrations |
| Language | Python 3.11+ | Team-wide familiarity assumed |

**Time-sinks to actively avoid (research-confirmed):** prompt tuning beyond 30 min, hyperparameter search beyond 20 min, any data pipeline beyond flat CSV, UI polish beyond what the hero loop needs, any deployment work beyond the one public URL the WhatsApp webhook requires.

---

## 4. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| LLM hallucinates extracted fields | High | Strict JSON Schema; the model only classifies or quotes; every quote verified as a substring of the customer text; code owns every number — `SYSTEM_DESIGN.md` §6.3-6.4 |
| Cold-start: no real labeled data | High | ~500 synthetic, weak-labeled rows is enough for a PoC — **disclose this openly** in the submission's AI/tool section rather than implying real data |
| Latency / free-tier rate limits (8K TPM) during live demo | High | Extraction cache, cached static prompt prefix + warm-up call, fallback model with its own bucket, rule-based last resort, separate untouched demo key — `SYSTEM_DESIGN.md` §6.7 |
| Multilingual (Darija/Arabizi/French) extraction quality | High | Model bake-off on 20 hand-labeled dialect windows before choosing; low clarity routes to review |
| Live API fails during judging | High | Have a cached/mocked response path ready so the demo continues even if the API times out — **and say so on stage** if you fall back to it. Hiding a mock reads as dishonest; disclosing it reads as engineering judgment |
| Git conflicts under deadline pressure | Medium | Merge to `main` every 30-60 minutes, one person owns `main`, test immediately after every merge |

---

## 5. Timeline — mapped to the ACTUAL event schedule, not a generic hackathon clock

Real coding time inside the official program is only about **4-4.5 hours**, split across three sprint blocks with mandatory workshops and checkpoints in between. This is far less than a typical "24-hour hackathon" — plan accordingly and **front-load as much as possible before 27 September**.

### Before event day (today 25 Sept / tomorrow 26 Sept) — do this now, not on the day
- [ ] Lock the problem statement, demo scenario, and this tech stack (done — this PRD)
- [ ] Generate the synthetic dataset (~200-500 rows) — this needs zero live coordination and can be done solo tonight
- [ ] Draft and test the LLM extraction prompt against 10-15 sample orders
- [ ] Scaffold the repo: FastAPI skeleton, frontend skeleton on frozen mocks, requirements.txt, folder structure
- [ ] Get API keys working end-to-end (one successful call, checked in, not committed as a secret)
- [x] Assign roles — done, see `execution_plan.md`
- [ ] Submit Final Team Confirmation (due 26 Sept)

### Event day, Tunis time
| Time | Program block | What the team does |
|---|---|---|
| 08:30-09:00 | Check-in | Confirm team present, laptops/internet working |
| 09:00-09:45 | Opening + history session | Attend — not skippable, no build time here |
| 09:45-10:00 | Roster check | Confirm attendance form |
| 10:00-11:15 | NVIDIA workshop | Attend (optional Brev part — skip activation unless already decided to use it; judging gives no bonus for it) |
| **11:15-11:30** | Build sprint 1 (15 min) | Confirm pre-built pieces still run; fix any environment drift |
| 11:30-11:45 | Mentor checkpoint | Show current state, ask about anything blocking |
| **11:45-13:00** | Build sprint 2 (75 min) | Wire LLM extraction → classifier → queue UI end-to-end on synthetic data |
| 13:00-13:45 | Lunch | — |
| 13:45-14:00 | Submission briefing | Attend — confirms exact submission requirements |
| **14:00-15:30** | Build sprint 3 (90 min) | Add order-detail view + explanation + recommended action; start should-have features only if must-haves are solid |
| 15:30-15:45 | Checkpoint | Verify every submission link will open; freeze new features now if behind |
| **15:45-17:00** | Final sprint (75 min) | Polish, fix bugs found in rehearsal, record the 90-second video |
| 17:00-17:30 | Submission workshop | Submit early, don't wait for 17:29 |

**Hard rule:** by 15:30, stop adding features entirely. The remaining time is rehearsal, bug fixes on what exists, and the video — not new code.

---

## 6. Team roles

Assigned — see `execution_plan.md`. The split is vertical:
- **Omar:** AI/ML core.
- **Jesser:** backend + messaging I/O.
- **Montassar:** frontend + infra.
- **Fedi:** story, scope gate, language assets.

The interfaces between lanes are frozen before the event, so nobody blocks on anyone.

---

## 7. Demo script (90 seconds, live typed input — not pre-recorded)

Research consistently flagged: judges want to see input typed live, not a canned recording. If any part is mocked (e.g. a cached LLM response for reliability), **say so on stage** — disclosed mocks read as engineering judgment, hidden ones read as dishonesty.

Structure:
- **0:00-0:10** — one sentence: "We predict which cash-on-delivery orders will get refused, so Tunisian sellers stop paying for wasted delivery trips."
- **0:10-0:20** — the cost, in a number the seller already tracks (refusal rate)
- **0:20-1:20** — live demo: paste/select an order → risk queue lights up → click the high-risk one → show the flagged text + plain-English reason → show the recommended action
- **1:20-1:30** — the ROI stat ("X TND saved" on the synthetic set) + one sentence on what's next

If asked in Q&A about limitations: state them plainly (synthetic data, not yet connected to a real store, multilingual extraction tested on curated cases) rather than overselling readiness.

---

## 8. Judging framing (GoMyCode / NVIDIA specifics)

- No public judge names or past GoMyCode winners exist — don't try to tailor to a specific judge, aim for broad mission alignment instead.
- GoMyCode's core mission is African/MENA youth employability and local economic problems — frame the pitch around a concrete regional SME cost problem (which this project already is), not a generic global one.
- **Correction to an earlier research claim:** Brev is confirmed **optional** with **no judging bonus**, per the official participant guide (the primary source of truth). Ignore any research suggesting it's "mandatory" — that appears to be a mix-up with a different event or an unverifiable example.
- Name SupplyzPro, Artefact, and Guepard explicitly in the submission's "evidence of award fit" fields (see `hackathon_playbook.md` for why these fit).

---

## 10. Customer messaging — settled design (tiered autonomy, judge-gated)

Draft-only (human always clicks send) was rejected: it doesn't reduce seller workload enough to be the core value prop, since reviewing every drafted message doesn't scale past a handful of orders a day. Full unconditional autonomous send was also rejected: a probabilistic LLM judge is a risk *reduction*, not a safety guarantee, and shares blind spots with the generator by construction. Settled design:

1. **Deterministic pre-filter** (not an LLM call): reject/flag any draft that mentions a price/discount not present in the order record, requests payment info, or falls outside the approved message templates. Cheap, fast, catches the worst-case failure modes before anything probabilistic is involved.
2. **LLM judge** checks what survives step 1 for: grounding (only references facts in the order data/flags), tone/language match to the customer's register, no overreach, and that the ask is actionable.
3. **Auto-send only when**: judge approves AND classifier confidence is high AND order value is below a threshold. This is where most orders should land — that's what actually delivers "seller works less," since most orders are unambiguous.
4. **Falls back to draft-for-review** (human clicks send) when: judge rejects, OR confidence is low, OR order value is above the threshold. Keeps a human specifically on the cases where being wrong costs the most.
5. **On judge rejection**: regenerate once with the rejection reason fed back in; if it fails again, fall back to a safe static template rather than looping indefinitely.

**For the live demo specifically:** build and show the judge-gating mechanism working, but keep a human click on the actual "send" during the on-stage demo. Say so directly — "judge-gated for autonomous send; keeping a human click during this pilot phase." This is a stronger, more credible answer for judges than either extreme, and removes the worst live-demo failure mode (an autonomous message going out mid-demo if something breaks). This entire feature (steps 1-5, not just drafting) is should-have, not must-have — do not let it eat time from the risk queue + detail view.

## 11. Ingestion — live WhatsApp via Meta Cloud API sandbox

Shopify/WooCommerce-store integration was considered and dropped as the primary ingestion story: a meaningful share of actual Tunisian sellers take orders directly over WhatsApp/Instagram DMs rather than running a formal storefront, so a Shopify-first pitch targets a more sophisticated seller than the one this product is actually for. It's also a weaker differentiator — Shopify's app ecosystem likely already has fraud/risk-scoring apps.

Copy-paste or chat-export ingestion was also rejected as the headline: it doesn't remove any seller work, which undercuts the core value prop. Scraping WhatsApp Web via a browser extension was rejected too (undocumented/obfuscated DOM, separate engineering surface, likely against WhatsApp's terms).

**Settled approach: Meta's WhatsApp Cloud API in test/sandbox mode.** A production, business-verified number isn't obtainable in time, but the developer sandbox is: create a Meta developer app, add the WhatsApp product, and Meta issues a test number immediately — no business verification needed at this tier. It sends and receives real messages via webhook. This is Meta's officially supported dev path, not a workaround.

**Demo flow:** a team member (playing the customer) messages the sandbox number from their phone → Meta POSTs to our webhook → FastAPI parses the message body → same extraction + classifier pipeline → order appears in the risk queue. No copy-paste.

**Setup (pre-event only — Jesser for the Meta app + webhook, Montassar for the public HTTPS URL; must not touch live sprint blocks; webhook spec in `SYSTEM_DESIGN.md` §9):**
1. Meta developer account → create app → add WhatsApp product → note the test number and phone-number ID
2. Register the "customer" phones as test recipients (sandbox limit: 5 numbers)
3. Generate a long-lived token via a System User (the quick-start token expires in 24h — it would die before event day)
4. Add `POST /webhook/whatsapp` (+ the `GET` verification handshake) to FastAPI; map the message payload to the same order shape CSV ingest produces
5. Expose the backend on a public HTTPS URL (tunnel such as ngrok, or a real deployment) and verify the webhook in the Meta console
6. End-to-end test: phone message → queue row, at least 5 times, before 26 Sept 22:00

**Known risks:**
- The public URL/tunnel is a live dependency during judging — if it drops, the webhook path dies. Test on the event venue's network if possible.
- Only pre-registered numbers can message the sandbox; whoever plays "the customer" must be registered beforehand.
- Tokens and tunnel URLs change — re-verify both on the morning of 27 Sept.

**Fallback (non-negotiable):** CSV/paste ingest stays built and tested. If the webhook fails mid-demo, switch to it and say so on stage.

**Pitch wording:** "Orders arrive from WhatsApp automatically — this is running on Meta's WhatsApp Cloud API in sandbox mode; production rollout needs business verification, which is our next step." Accurate, and still the strongest ingestion story available.

---

## 12. Open items still needing a human before the pitch is final

- [ ] Verify the refusal-rate and COD-penetration numbers against one real source
- [ ] Verify or drop the eGrow/SoukFlow competitor mentions
- [ ] Decide final team roster and confirm via the Final Team Confirmation form (due 26 Sept)
- [ ] Decide who owns the "feature freeze" enforcement at 15:30 on event day
- [ ] Set the actual order-value threshold for auto-send vs fallback-to-review (§10)
- [ ] WhatsApp sandbox (§11) working end-to-end by 26 Sept 22:00 — if not, drop it to a pitch-only roadmap line and demo on CSV/paste
