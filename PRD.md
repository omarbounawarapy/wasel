# PRD — COD Risk Scoring for Tunisian E-commerce
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
7. One aggregate ROI stat for the demo close

**Should-have (only after must-haves work end-to-end):**
8. Tiered-autonomy customer messaging — see §10 below for the settled design
9. Impact dashboard (before/after refusal rate, estimated TND saved)
10. WhatsApp chat-export ingestion as an alternate input path (see §11) — same pipeline, different parser

**Nice-to-have (cut without guilt if behind schedule):**
11. Filter/search in the queue

**Explicitly out of scope — do not build:**
- Auth/multi-tenant accounts, real store integrations (WooCommerce/Shopify — mock the button only), model retraining UI, native mobile, Docker/deployment infra beyond `requirements.txt` + a run command.

**Hard rule from failure-pattern research:** pick ONE hero feature (the risk queue + explanation) and make it bulletproof. A second half-built feature scores worse than a first fully-working one.

---

## 3. Tech stack (locked — do not revisit on build day)

| Layer | Choice | Why |
|---|---|---|
| LLM extraction | Claude Haiku + Pydantic schema, with defaults for missing/invalid fields | Fast, cheap, handles Arabic/French mixed text; schema + defaults contain hallucination risk |
| Classifier | XGBoost on extracted features + order metadata | Default hyperparameters are fine — do not tune |
| Backend | FastAPI | Minimal boilerplate |
| Frontend | Streamlit | Fastest path to a working queue/detail UI; do not over-engineer |
| Data | CSV / SQLite | No Postgres, no migrations |
| Language | Python 3.11+ | Team-wide familiarity assumed |

**Time-sinks to actively avoid (research-confirmed):** prompt tuning beyond 30 min, hyperparameter search beyond 20 min, any data pipeline beyond flat CSV, UI polish beyond ~30 min for the base Streamlit layout, any deployment/Docker work before submission is safe.

---

## 4. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| LLM hallucinates extracted fields | High | Pydantic schema with `Optional` fields + safe defaults; validate before feeding classifier |
| Cold-start: no real labeled data | High | ~500 synthetic, weak-labeled rows is enough for a PoC — **disclose this openly** in the submission's AI/tool section rather than implying real data |
| Latency during live demo | Medium | Pre-compute a few demo predictions as fallback; use Haiku not a larger model; target <3s end-to-end |
| Multilingual (Arabic/French) extraction quality | Medium | Lean on Claude's native bilingual handling; hand-pick test cases you've verified work; have a structured-fields-only fallback if free text confuses the model |
| Live API fails during judging | High | Have a cached/mocked response path ready so the demo continues even if the API times out — **and say so on stage** if you fall back to it. Hiding a mock reads as dishonest; disclosing it reads as engineering judgment |
| Git conflicts under deadline pressure | Medium | Merge to `main` every 30-60 minutes, one person owns `main`, test immediately after every merge |

---

## 5. Timeline — mapped to the ACTUAL event schedule, not a generic hackathon clock

Real coding time inside the official program is only about **4-4.5 hours**, split across three sprint blocks with mandatory workshops and checkpoints in between. This is far less than a typical "24-hour hackathon" — plan accordingly and **front-load as much as possible before 27 September**.

### Before event day (today 25 Sept / tomorrow 26 Sept) — do this now, not on the day
- [ ] Lock the problem statement, demo scenario, and this tech stack (done — this PRD)
- [ ] Generate the synthetic dataset (~200-500 rows) — this needs zero live coordination and can be done solo tonight
- [ ] Draft and test the LLM extraction prompt against 10-15 sample orders
- [ ] Scaffold the repo: FastAPI skeleton, Streamlit skeleton, requirements.txt, folder structure
- [ ] Get API keys working end-to-end (one successful call, checked in, not committed as a secret)
- [ ] Assign roles (below) so there's zero ambiguity at 08:30 on the 27th
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

## 6. Team roles (3-5 people)

Mixed skills beat matched skills — one strong builder plus one strong communicator outperforms four coders with no one owning the story.

| Role | Owns | Notes |
|---|---|---|
| **Builder** | LLM extraction pipeline + FastAPI backend + classifier | Owns `main` branch merges |
| **Interface** | Streamlit UI, synthetic dataset prep, wiring demo flow | Also owns test-case curation (which sample orders get shown live) |
| **Storyteller / Integrator** | Repo setup pre-event, pitch narrative, 90-second video, rehearsal schedule, submission form | If team is 3, this person also handles repo/deploy plumbing |
| *(4th, if available)* | Prompt engineering + edge-case testing | Dedicated owner for the hallucination/multilingual risks above |
| *(5th, if available)* | Floating — mentor liaison, backup API/fallback engineering, timekeeper | Enforces the 15:30 feature freeze |

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

## 11. Ingestion — WhatsApp chat-export as an alternate path

Shopify/WooCommerce-store integration was considered and dropped as the primary ingestion story: a meaningful share of actual Tunisian sellers take orders directly over WhatsApp/Instagram DMs rather than running a formal storefront, so a Shopify-first pitch targets a more sophisticated seller than the one this product is actually for. It's also a weaker differentiator — Shopify's app ecosystem likely already has fraud/risk-scoring apps, inviting the "isn't this solved already?" reaction from a judge.

**What's actually buildable in the time available:** not a live WhatsApp Business API/webhook integration — that needs Meta business verification and days of review, not hours. Instead: parse a **WhatsApp chat export** (the `.txt` file exportable from any thread today) as an alternate input alongside CSV/paste. Same extraction pipeline, same classifier, only the parser changes (chat lines → order rows instead of CSV cells) — low cost to add once CSV ingest works, since nothing downstream changes.

**State this precisely in the pitch:** "today — upload your WhatsApp export; next — live webhook integration." Do not imply a live API connection exists if it doesn't; that's the kind of overclaim that a direct question from a judge exposes immediately.

---

## 12. Open items still needing a human before the pitch is final

- [ ] Verify the refusal-rate and COD-penetration numbers against one real source
- [ ] Verify or drop the eGrow/SoukFlow competitor mentions
- [ ] Decide final team roster and confirm via the Final Team Confirmation form (due 26 Sept)
- [ ] Decide who owns the "feature freeze" enforcement at 15:30 on event day
- [ ] Set the actual order-value threshold for auto-send vs fallback-to-review (§10)
- [ ] Decide whether WhatsApp-export parsing (§11) is worth building given the ~4h15 time budget, or stays a pitch-only roadmap item
