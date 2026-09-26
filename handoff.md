> **Superseded 26 Sept. Historical only.** Do not use this file for numbers, scope or screens. Canonical: `docs/council-spec/`, then `PRD.md`, `SYSTEM_DESIGN.md`, `execution_plan.md`.

# COD Risk Scoring — Hackathon Handoff

Tunisian e-commerce cash-on-delivery orders get refused 40-60% of the time (no-show, address issues, change of mind). Each refusal costs the seller a wasted driver trip. This tool scores incoming orders for refusal risk and recommends an action, so sellers stop paying for doomed deliveries.

## Product shape

**Form factor: web app, not native mobile.**
- The buyer (seller / delivery aggregator ops team) already works from a dashboard, not a phone. Web app *is* the correct form factor for this persona, not a compromise.
- Ship it as a **PWA** (manifest + icon, "Add to Home Screen") — ~30 min of extra config buys the "looks like an app" moment for judges without the native build/signing overhead a hackathon can't afford.
- Keep push notifications out of the pitch — web push is unreliable (esp. iOS Safari). Fake the "seller gets alerted" beat with an in-app toast instead.

**Trade-off, noted but accepted:** if the hackathon track explicitly scores a "mobile app" category, a browser-based product reads as less polished to judges who don't dig into the tech. Worth checking the rubric. Also gives up native offline mode and reliable push — irrelevant to this demo, but would matter for a real driver-facing field app later.

## Screens (MVP)

1. **Risk Queue** — orders sorted by risk (color-coded badge), recommended action per row, a top-line ROI banner ("X TND saved this week"). This is the money screen for the demo.
2. **Order Detail** — original address/note text with LLM-flagged phrases highlighted inline, feature weight breakdown, plain-English reason string, action buttons (Confirm via SMS / Require prepayment / Ship normally), and the drafted customer message (see below).
3. **Ingest** — CSV upload or paste-one-order box; a (mocked) "connect your store" button for WooCommerce/Shopify to signal productization.
4. **Impact Dashboard** — refusal rate before/after, estimated cost saved. Closes the ROI loop for judges.

## Pipeline

1. **LLM feature extraction** — reads messy Arabic/French address + note text, outputs structured flags: address specificity, red-flag phrases, tone.
2. **Classifier** (XGBoost/LightGBM) — combines flags + order data (price, product, zone, customer history) into a risk score + tier (Low/Med/High).
3. **Rule layer** — maps tier + order value to a recommended action. Simple rules on top of the score, not another model.
4. **Explanation string** — plain-English reason, e.g. "vague address + high value + far zone = high risk."

## Extension: LLM drafts the customer-facing message too

Same extraction call can also emit a drafted outbound message tailored to the triggering flag (vague address → ask for a landmark; high value/far zone → confirmation or prepayment nudge; hesitant tone → reassurance + reschedule offer). Match the customer's own dialect/register — a formal reply to a dialect note reads as a bot and undermines trust.

- Gate drafting/sending by risk tier (Med/High only) — don't spam low-risk customers.
- For the hackathon: show the draft with Edit/Send buttons rather than auto-sending. Stronger for the demo and for the responsible-AI judging criterion — proves the system isn't a black box.

## Extension: autonomous send with LLM-as-judge

Longer-term shape (good pitch angle, not just a hackathon shortcut — human review doesn't scale past a demo): generator drafts the message, a judge LLM gates it before send.

**Judge should check:**
- Grounding — draft only references facts in the order data/flags, no invented discounts/promises.
- Tone/language match to the customer's own register.
- No overreach — doesn't request payment info or commit the seller to anything the rule layer didn't authorize.
- Actionability — clear yes/no ask.

**On reject:** never fail open. Regenerate once with the rejection reason fed back in, or fall back to a safe static template. Log every judge decision (approved/rejected + reason) and surface it as a small "judge activity" feed in the demo — cheap to build, and it's the artifact that proves the safety story is real, not a slide.

**Production caveat (out of scope for the hackathon, worth having an answer ready for):** full autonomy on real customers is the first objection sellers will raise. A sampling audit (human spot-checks ~5% of auto-sent messages) or a volume cap that lifts as trust builds is the realistic pilot answer.

## MVP scope decisions

**Build:** CSV/paste ingest, LLM extraction, classifier + risk tier, rule-based recommended action, explanation string, risk queue + detail UI, one aggregate ROI stat.

**Skip for the hackathon:** auth/multi-tenant, real store integrations, model retraining UI, native mobile.

## Open questions / next steps

- Confirm whether the hackathon rubric names "mobile app" as a scored category — decides how much PWA polish is worth investing in.
- Decide message channel for the demo: WhatsApp-style chat bubble mock is the cheapest visually-convincing option vs. real SMS/WhatsApp API integration.
- Still to draft: role split (data / LLM / classifier / UI) and the synthetic dataset schema (~200-500 rows).
