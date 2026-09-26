# Frontend + UX: stack, screens, states, copy, mocks

> Council final spec — Advocate lens (Round 3). Source of truth for its area. Where this file conflicts with a **Conductor ruling** in [README.md](README.md#conductor-rulings), the ruling wins. Unverified external facts are marked [VERIFY].


## 1. Stack, gate, Streamlit fallback

### 1.1 Decision
**Vite + React + TypeScript single-page app** in `web/`, built to `web/dist`. FastAPI mounts it last: `app.mount("/", StaticFiles(directory="web/dist", html=True))`. The API lives under `/api/*`, and `/webhook/whatsapp` only in event/dev mode, as mounted by `app/mode.py`.
- **Dev:** the `vite` dev server with `server.proxy: {"/api": "http://localhost:8000"}`. No CORS.
- **Next.js is allowed** only on the conditions below; the choice is made at 09:00 and never revisited.
  - `output: "export"`, built to `web/dist`;
  - one page with `?order=`;
  - no dynamic routes and no API routes;
  - every component is a client component.
- **`.gitignore`:** Skeptic N-1 applies. Add the `!web/src/lib/` re-include before the first frontend commit, and CI builds `web/` from a clean checkout.

### 1.2 Wiring
```
web/
  index.html               <html lang="en" dir="ltr">
  vite.config.ts           outDir "dist"; dev proxy /api; server.fs.allow: [".."] (reads ../mocks in dev)
  src/api/types.ts         Architect R3 §4.2 verbatim + §2.0 additions (C3 compares it to the Pydantic JSON Schema)
  src/api/datasource.ts    "live" | "mock" | "snapshot"; picks by VITE_DATA_SOURCE, then ?source=; the only module that fetches
  src/api/mock.ts          dynamic-imports ../../mocks/*.json (separate chunk, loaded only in mock mode); applies ?mock= patches (§6.5)
  src/api/usePoll.ts       fetch + AbortController + keep-last-good + failure count + pause while document.hidden
  src/api/visitor.ts       localStorage["cod_visitor_id"] (Skeptic's key), crypto.randomUUID(); try/catch → per-tab id in memory
  src/copy/en.ts           every UI string by key (§5); server-built strings (reasons, labels, event titles) are not duplicated
  src/components/…         §2.12
  public/snapshot/         Sunday Should; capture only in public mode (script refuses otherwise, Skeptic N-7)
mocks/                     repo root; Jesser commits §6 as the hand-written mocks; C3 validates them at G2 12:00
```
- **Lint and CI:**
  - ESLint `react/no-danger: error` (Architect);
  - CI `! grep -rn "dangerouslySetInnerHTML\|innerHTML" web/src`;
  - `npm ci && npm run build` from a clean checkout.

### 1.3 Libraries (keep it small)
- **Core:** React, ReactDOM, TypeScript, Vite, ESLint with `eslint-plugin-react`.
- **Styling:** plain CSS with custom properties, or Tailwind if Montassar is fluent in it. No component kit.
- **Polling and routing:** a hand-written `usePoll` (~40 lines). No router library: selection lives in `URLSearchParams` plus `history.replaceState`.
- **Fonts:** `system-ui, "Segoe UI", "Noto Sans Arabic", "Geeza Pro", Tahoma, sans-serif`. No web-font download at the venue [VERIFY that Arabic glyphs render on the recording machine].

### 1.4 Gates (Sat 26 Sept, Tunis)

| Gate | Time | Pass | Fail → |
|---|---|---|---|
| **FE0** | 09:00 kickoff | Montassar confirms he's going with React and picks Vite (default) or a Next static export | Streamlit from the first frontend block (zero cost) |
| **FE1** (early exit) | 13:00 (end of the 11:30–13:00 block) | With `VITE_DATA_SOURCE=mock`, `npm run dev` shows the queue from `mocks/orders.json` with tier badges, and clicking a row sets `?order=` | Streamlit from 14:15 |
| **G4** | **16:00** | **All five checks below pass and are shown to Omar in ≤ 5 min** | **Streamlit from 16:00.** After 16:00 there is no framework change in either direction |

**G4 checks (each binary):**
1. **Queue.** Every row from `orders.json` renders with:
   - a tier badge showing text, number and shape;
   - `▼69` on #2613 and `Scoring…` on #2614;
   - an action pill, the `reason_short` line, a status label, and `Sample`/`Yours` chips.

   The summary strip reads `1 needs review · 3 waiting for customer · 3 ready to ship`. Order is #2614 first, then by score. #2603 (Delivered) sits in a collapsed "Closed (1)".
2. **Detail.** Clicking #2613 shows `order_detail.json` in the right pane, and a browser refresh keeps `?order=`. The timeline shows v2 above v1, with:
   - `▼69`;
   - `Model 24 → Rule: customer confirmed ×0.6 (starting assumption) → 14`;
   - "Resolved: Vague location · May not be home · Price hesitation".

   The customer reply carries `Simulated`, and the outbound bubble carries "Sent (simulated)".
3. **RTL.** Clicking #2604 loads `order_detail_ar.json`.
   - The Arabic-script bubble sits on the customer side (left), with its text right-aligned inside the bubble.
   - The mixed bubble `نخدم في الصباح، livraison après 17h svp 🙏` resolves RTL.
   - The Arabizi bubbles in #2613 stay LTR.
   - `سارة م.` doesn't reorder the `#2604` next to it.
   - In the reason line, the parentheses stay around the isolated Arabic quotes and "149 TND" stays at the end.
4. **Highlights.** In #2604 both `risk` marks cover exactly `قدام الصيدلية` and `كلمني كي توصل`. The `address` underline covers exactly `حي النصر`. `react/no-danger` lint and the grep are clean.
5. **Read-only and served build.** #2604 shows **Try this order** as the only filled button, with no seller actions and no Demo tools. `npm run build` produces `web/dist`, and FastAPI (`StaticFiles`, stub `/api/health`) serves it with checks 1–4 still passing in mock mode.
   - Run this on the **hosted URL** if the 14:00 hello-world container is live (Strategist's condition).
   - If the host is down, run it on local uvicorn. A host problem is Montassar's infra issue, not a reason to switch frameworks, because Streamlit would need the same host plus a second deployable.

**Soft checks (not gating; due at G6 18:00):** the live source against Jesser's API, 3 s polling that picks up a changed score, and the hosted URL in public mode.

### 1.5 Streamlit fallback (only if FE0, FE1 or G4 fails)

**Deployment**
- **A second deployable** calls the hosted API over `API_BASE_URL` [VERIFY host: Streamlit Community Cloud, or a second service on the same host]. The API contract doesn't change. This is the only configuration with two deployables. The council accepts it because it's the fallback.
- **Visitor id:** `st.session_state.setdefault("visitor_id", str(uuid4()))`, sent as `X-Visitor-Id` on every `requests` call. It resets on a browser refresh. The public banner then adds "Your copies last for this browser session."

**Page**
- **Layout:** `st.columns([2, 3])`. The queue is one `st.button` per row, and the selection lives in `st.query_params["order"]` [VERIFY the API in the pinned version].
- **Polling:** `@st.fragment(run_every=3)` around the queue and the detail [VERIFY Streamlit ≥ 1.37; pin it]. Paste, Try and simulate each sit in an `st.form`, so reruns don't wipe the input.
- **Highlights** are the only HTML we build:
  ```python
  def render_segments(segs):
      return "".join(
          f'<mark class="hl-{s["kind"]}" title="{html.escape(s["label"] or "")}">{html.escape(s["text"])}</mark>'
          if s["kind"] else html.escape(s["text"]) for s in segs)
  st.markdown(f'<p dir="auto" class="bubble">{render_segments(segs)}</p>', unsafe_allow_html=True)
  ```
  FSI and PDI pass through `html.escape` unchanged. Every string that reaches `unsafe_allow_html` goes through `html.escape`: names, reasons, drafts, all of it.

**Scope**
- **Kept:**
  - tier text, number and shape characters;
  - public banner, mode chip, Sample/Yours, Try this order;
  - `Simulated` and "Sent (simulated)";
  - budget and fallback banners, path chips;
  - the timeline, using `st.container(border=True)` [VERIFY param];
  - the ROI line and the footer.
- **Moved to Sunday (Strategist):** the draft panel. The reply loop still works because simulate-reply auto-records the draft (Architect §5.3).
- **Cut:** the row flash, keyboard arrow navigation, and the Activity feed.

**Budget [estimate]:** 4.25 h, which fits 16:00–20:30.

| Work | Time |
|---|---|
| Queue + detail | 1.75 h |
| Segments + RTL | 0.5 h |
| Paste / Try / simulate forms | 1 h |
| Banners + labels | 0.5 h |
| Deploy | 0.5 h |

### 1.6 Build order, mapped to Strategist's Round 3 blocks for Montassar

| Block (Sat) | Frontend work | Notes |
|---|---|---|
| 11:30–13:00 | scaffold, `datasource.ts` (mock), `usePoll`, `visitor.ts`, master–detail layout, QueueRow, TierBadge, DeltaArrow, summary strip | **FE1 13:00** |
| 14:15–16:00 | Transcript + Bubble + Segments (RTL), detail pane: header + ScoreBlock + PrimaryActions (capabilities), WhyPanel, ScoreTimeline (static), read-only state with Try button (inert on mock), build served by FastAPI | **G4 16:00** |
| 16:00–18:00 | live source + `X-Visitor-Id`; 3 s / 1 s polling; `rescore_state` ghost card; Paste dialog; Demo box (simulate + scripted chip + auto-record note); timeline + reason diff + path chip; Try this order live | **G6 18:00** |
| 18:20–19:05 | DraftPanel + Send; ROI line (`/api/metrics/impact`) | |
| 19:05–19:35 | (server side, Montassar) `APP_MODE`, visitor middleware, purge | |
| 20:30–21:00 | **public-mode chrome:** public banner with Try CTA, mode chip, Sample/Yours chips, budget/per-visitor/fallback banners, "Sent (simulated)" labels, 404-expired state, footer | must land before the safety take and the 22:00 public flip |
| Sun 11:45–13:00 | Activity feed (EventView `level`/`title`), judge rows (if S-3), `drafting` state, row flash | Should |
| Sun 14:00–15:30 | snapshot capture + mirror (public mode only), FLIP move | Should |

**Cut order if behind:**
1. FLIP
2. Activity feed
3. Row flash
4. The timeline visual. Keep the ScoreBlock, the delta and the latest `reason_diff` line.
5. Highlighting (fall back to raw text)

**Never cut:**
- the public banner, mode chip and Try this order;
- the read-only handling;
- `Simulated` and "Sent (simulated)";
- the budget and fallback banners, and path chips;
- the "Simulated" ROI line and the synthetic footer;
- the one-page master–detail layout.

---

## 2. Screen spec: the master–detail page

### 2.0 API: Architect Round 3 §4.2 verbatim, plus three additive fields
Every binding below uses Architect's Round 3 type names: `OrderListResponse`, `OrderSummary`, `ScoreBadge`, `OrderDetailResponse`, `Segment`, `MessageView`, `AssessmentView`, `DraftView`, `JudgeView`, `Capabilities`, `HealthResponse`, `TryResponse`, `SimulateReplyResponse`, `SendDraftResponse`, `EventView`, `ImpactResponse`, `ErrorCode`. I need three more fields. All three are additive, and the UI degrades gracefully without them.

| # | Where | Field | Why | Without it |
|---|---|---|---|---|
| B1 | `OrderSummary` | `seed_key: string \| null` (from `conversations.seed_key`; copies keep their sample's key) | the banner's **Try the main sample** targets `seed_key == "hero"`; "Your copy of sample #2601" pairs a copy with its sample | CTA targets the seeded row with the highest `final_score`; the "copy of" line is hidden |
| B2 | `HealthResponse.llm` | `visitor_cap: {reached: boolean, until: string \| null}`, computed for the request's `X-Visitor-Id` (null-safe in event mode) | Skeptic's per-visitor banner says "until {time}" | no per-visitor banner; the version's path chip still explains `llm_cap_reached` |
| B3 | `AssessmentView` | `injection_suspected: boolean` (already on `ScoreResult` and `risk_assessments`) | Skeptic's injection chip | the chip is never shown; status still goes to `needs_review` |

**Fields in Architect Round 3 that the UI depends on** (renaming any of these breaks the UI):
- `OrderSummary.read_only` and `OrderDetailResponse.capabilities`: the whole read-only and Try UX.
- `MessageView.origin`: the `Simulated` chip, and "Sent (simulated)" via `dashboard` or `simulated` outbound.
- `DraftView.delivery`: `recorded_only`.
- `SimulateReplyResponse.recorded_draft_id`: the auto-record announcement.
- `HealthResponse.mode`, `.wa_send`, `.webhook` and `.llm.cap_reached`, `.fallback_active`, `.fallback_reason`.
- `AssessmentView.resolved_flags` and `.extraction.cache_hit`.

**Error codes the UI handles:** Architect Round 3 §4.3 in full. Skeptic's Round 3 codes (`REPLY_LIMIT`, `DEMO_BUSY`, `VISITOR_ID_REQUIRED`) are not in Architect's table. The UI still gives them copy (§5.4), and any unknown code falls back to `error.INTERNAL` plus the server `message`. The conductor reconciles (§7).

### 2.1 Data flow
- **Polling cadence:**

  | Request | Cadence |
  |---|---|
  | `GET /api/orders?include_collecting=true` | every **3 s** |
  | `GET /api/orders/{id}` (selected order) | every **3 s**; every **1 s** while `order.rescore_state != "idle"`, for at most 60 s |
  | `GET /api/health` | every **10 s** |
  | `GET /api/metrics/impact` | once per load |
  | `GET /api/events?after=` | every 3 s (Sunday) |

  All polling pauses while `document.hidden` and fires once on return.
- **Every `/api` request** sends `X-Visitor-Id`. Public mutations without the header get a 422, so the header is not optional.
- **Mutations** (Try, Send, actions, paste, simulate) refetch the list and the detail immediately. There are no optimistic score changes.
- **Times:**
  - absolute times use `Intl.DateTimeFormat("en-GB", {timeZone: "Africa/Tunis", hour: "2-digit", minute: "2-digit"})`;
  - relative times ("6 min") are computed from the list's `server_time` plus the elapsed time since that fetch, so client clock skew doesn't matter and the mocks are deterministic.
- **Keep last good data.** A failed poll never blanks the screen. After 2 consecutive failures the "Connection lost" bar appears (§2.4).

### 2.2 Layout regions
Target: a 1920×1080 recording at 125 % zoom, about 1536 CSS px [VERIFY on the recording machine]. It must also work at 1280.
```
┌ Header ─────────────────────────────────────────────────────────────────────────────────────────┐
│ {Product}   ● Live   [Public demo]                                            [Paste order]      │
├ Public banner (public mode, always on) ── text ─────────────────────── [Try the main sample] ───┤
├ Status banners (0–2, §2.4) ─────────────────────────────────────────────────────────────────────┤
├ Queue ≈ 36 % ─────────────────────┬ Detail ≈ 64 % ──────────────────────────────────────────────┤
│ ROI line (Simulated) ▸ Assumptions│ A  Order header · ScoreBlock · primary action   (sticky)    │
│ Summary strip                     │ B  Why this score                                           │
│ QueueRow × n                      │ C  Score history (timeline)                                 │
│ ▸ Closed (n)                      │ D  Conversation                                             │
│                                   │ E  Message to customer (drafts)                             │
│                                   │ F  DEMO · Simulate a customer reply                         │
├───────────────────────────────────┴─────────────────────────────────────────────────────────────┤
│ Footer: All orders and customers in this demo are synthetic test data. · build a1b2c3d · config 3f9a1c2e │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```
- **≥ 1440 px, Sunday:** the Activity feed is a third column (≈ 22 %).
- **1024–1439 px:** Activity opens as a drawer from a header toggle.
- **< 1024 px:** single column. The detail pushes over the queue with a "← Queue" button. It isn't a demo target; it just mustn't break.
- **Detail pane:** scrolls on its own. Region A is sticky, so the primary action stays visible while the seller reads the conversation.

### 2.3 Header and banners

| Element | Bound to | Rule / copy key |
|---|---|---|
| Product name | static | `app.name` (Fedi, G1 12:00) |
| Live dot | poll state | `header.live` (green) · `header.reconnecting` (amber, after 2 failures) · `header.snapshot` (grey) |
| Mode chip | `health.mode` | `header.mode.public` / `.event` / `.dev`; tooltip `header.mode.tooltip.*` |
| WhatsApp chip | `health.webhook`, `health.whatsapp.last_webhook_at` | only when `webhook == "enabled"`: `header.whatsapp.last` / `.none` |
| Paste order | opens §4.1 | `header.paste`; disabled in snapshot with `common.offline_tooltip` |
| Public banner | `health.mode == "public"` (or `list.mode`) | `banner.public` + button `banner.public.cta` (Try on `seed_key == "hero"`, B1). Neutral info colour, `role="region" aria-label="About this demo"`. **Not dismissible.** The CTA is filled only while no order is selected; after that it becomes an outline button, so the detail's primary action is the page's single filled button. |

### 2.4 Status banner stack (below the public banner)
At most two bars show at once, in this priority order. A higher-priority bar takes the slot.

| # | Bar | Condition | Copy key | Colour / role | Rules |
|---|---|---|---|---|---|
| 1 | **Snapshot** | source is snapshot | `banner.snapshot` | grey, `role="status"` | replaces every other bar |
| 2 | **Connection lost** | ≥ 2 consecutive poll failures | `banner.connection` | amber | data is kept |
| 3 | **Budget** | `health.llm.cap_reached` | `banner.cap.global` | amber, `role="status"` | not dismissible |
| 3 | **Budget** | else `health.llm.visitor_cap.reached` (B2) | `banner.cap.visitor` | amber, `role="status"` | not dismissible |
| 4 | **Fallback** | `health.llm.fallback_active` and no budget bar | `banner.fallback`; `{path}` = `enum.path[health.llm.last_path]` | amber | not dismissible; 10 s grace before hiding, so one flap doesn't flicker |

### 2.5 Queue

**ROI line** (top of the queue, one line), bound to `ImpactResponse`:
- **Visible text:** `roi.line`, e.g. "Simulated on 2,000 synthetic orders: refusal rate 31 % → 22 %, 190 trips and 12,480 TND avoided."
- **Disclosure:** `roi.assumptions` opens `assumptions[]` and `dataset` in a popover.
- **Error:** hidden. No number appears without "Simulated".

**Summary strip:** `queue.summary`, from `counts.needs_review`, `counts.awaiting_reply` and `counts.ready_to_ship`. The mocks give "1 needs review · 3 waiting for customer · 3 ready to ship".

**QueueRow:** one full-width `<button>` per row, inside `<ul role="list" aria-label={queue.aria}>`.
```
[● HIGH 83]        Amira B. · #2601 · [Sample]                               28 min
[Confirm with customer]  Vague address (9rib el jemaa) · rural zone · 220 TND · may not be home
[Waiting for customer]  [Message ready]
```

| Element | Field | Rule |
|---|---|---|
| TierBadge | `score.tier`, `score.final_score` | `HIGH 83` / `MED 52` / `LOW 14`, plus a shape (● high, ◆ med, ▲ low), plus colour. `aria-label` = `row.tier.aria`. When `score == null`: grey `row.scoring` |
| DeltaArrow | `score.delta` | `▼69` green (risk down), `▲15` red (risk up). Hidden when null or 0. `aria-label` = `row.delta.*.aria` |
| Name | `customer.display_name` | inside `<bdi>`, ellipsis at 22 chars, full name in `title`. null → `row.unnamed` |
| Ref | `order_ref` | e.g. `#2601` |
| Owner chip | `is_seeded`, `read_only`, list `mode` | public: `row.sample` (lock icon) when `is_seeded`, else `row.yours`. event/dev: channel chip (`enum.channel.*`) |
| Updated | `updated_at` | relative (`common.rel.*`); `title` = absolute time in Tunis |
| Action pill | `score.action` | `enum.action.*` |
| Reason | `score.reason_short` | one line, text node (isolates already inside), CSS ellipsis as a guard |
| Status | `status` | `enum.status.*` |
| Flags | `score.confidence == "low"`, `score.path`, `has_pending_draft`, `rescore_state != "idle"` | `row.low_conf`; `row.rules` when `path == "rules"`; `row.draft_ready`; `row.rescoring` (pulsing dot, static under reduced motion) |

**Sort and grouping** (client-side):
1. `collecting` rows with `rescore_state != "idle"` come first and show `Scoring…`. `collecting` rows that are idle are hidden unless selected (e.g. a lone "salam").
2. Non-terminal rows by `score.final_score` descending, then `updated_at` descending.
3. `delivered`, `refused` and `cancelled` go into a collapsed `queue.group.closed`. `shipped` stays in step 2.

Rows are keyed by `order_id`, so focus survives re-sorts. When `score.version` or `status` changes, the row flashes for 1.5 s; under reduced motion it gets a static 2 px outline instead. FLIP movement is Sunday work.

### 2.6 Detail pane

**A. Order header, ScoreBlock and primary action** (sticky)
- **Left side:**
  - `customer.display_name` in `<bdi>`, `customer.phone_masked` (hidden when null), `order_ref`.
  - Chips:
    - `detail.sample_chip` when `capabilities.read_only`;
    - `detail.copy_of` when `!is_seeded && seed_key`, with the sample's ref taken from the list row that shares the `seed_key`;
    - the injection chip `chip.injection` when the current assessment has `injection_suspected` (B3).
  - `product_name × quantity`, the price (`common.tnd`), and the zone (`enum.zone.*`). Append `detail.zone_default` when `zone_source == "default"`.
  - A status pill.
  - A history line from `customer.completed_orders` / `refusals_total`: `detail.history.new` when both are 0, else `detail.history.some`.
- **Right side (ScoreBlock):** a large TierBadge, the DeltaArrow, and the action label (`enum.action.*`) underneath.
- **Primary action row:** see §2.7.

**B. Why this score**
- `assessments.at(-1).reason`, full, as a text node.
- Confidence chip: `why.conf.high`, or `why.conf.low`. The low chip lists each `confidence_reasons` entry (`enum.conf_reason.*`) in a tooltip, and also as sr-only text.
- Path chip. When `extraction?.cache_hit` it reads `enum.path.cached`; otherwise it is `enum.path[path]`. The tooltip shows `extraction.provider:model`.
- `why.factors`: `top_factors[0..2]`, each as `label` plus signed points (`+15`, `−9`).

**C. Score history** (the hero component). Cards run newest first, reversing `assessments`.
```
v2 · Customer replied · 10:06                                   LOW 14  ▼69
   Model 24 → Rule: customer confirmed ×0.6 (starting assumption) → 14
   Address now exact · customer confirmed ×0.6 · resolved: vague address, …        ← reason_diff
   Resolved: Vague location · May not be home · Price hesitation                   ← resolved_flags → enum.flag.*
   [Recorded AI result · no new AI call]                                            ← path chip
v1 · First score · 10:02                                        HIGH 83
   Vague address (9rib el jemaa) · rural delivery zone · 220 TND order · …          ← reason
   Flagged: Vague location “9rib el jemaa” · Price hesitation “ghali chwaya” · …    ← flags[] (quotes in <bdi dir="auto">)
   [Recorded AI result · no new AI call]
```
- **Header line:** `timeline.card.header`, built from `version`, `trigger` (`enum.trigger.*`) and `created_at`.
- **Arithmetic line:** shown only when `adjustments` is non-empty. It is `timeline.model` (rounded `model_score`), then `timeline.rule` for each adjustment (`label`, with `effect` shown as `×0.6` or `+15`), then `→ {final_score}`.
- **Body:** `reason_diff` when present, otherwise `reason`.
- **Pending ghost card:** shown on top whenever `order.rescore_state != "idle"`. Its text is `timeline.pending.debouncing`, `.scoring` or `.drafting`, and it sits in its own `aria-live="polite"` region. The new card flashes for 1.5 s when it arrives.
- **Cut fallback:** ScoreBlock plus delta plus the latest `reason_diff` line.

**D. Conversation**
- **Bubble order:** by `provider_ts`.
- **Bubble position** follows `author`, never language. Customer bubbles sit on the inline-start (left); seller and ai bubbles sit on the inline-end (right).
- **Bubble text:** `<p dir="auto" class="bubble-text">`, with `text-align: start`. Customer bubbles that have `segments` go through `<Segments>`. Everything else renders `text` as plain text (§3).
- **Meta line:** the time (HH:mm, Tunis), then:
  - **Author line (outbound):** `convo.meta.template` when the draft with `sent_message_id == message_id` has `source == "static_template"`, `convo.meta.ai` when it has `llm_rewrite`, otherwise `convo.meta.seller`.
  - **Delivery line:** `origin == "dashboard"` or outbound `simulated` → `chip.sent_simulated`. `origin == "whatsapp"` → `enum.delivery[delivery_status]`.
- **Chips:**
  - `origin == "simulated"` → **`convo.simulated`**: an amber outline chip on both inbound and auto-recorded outbound bubbles, always visible, never cut;
  - `origin == "paste"` → `convo.pasted`;
  - `kind == "audio"` without a transcript → `convo.voice`;
  - `location` → `convo.location`;
  - `image` or `unsupported` → `convo.unsupported`.
- **Auto-scroll** to the newest bubble only when the user was already at the bottom.

**E. Message to customer (drafts)**

The current draft is the newest `DraftView` with `route != "blocked"`. Older sent drafts collapse under `draft.earlier`. Blocked drafts collapse under `draft.blocked_group`, each with its failure.
```
Message to customer · Arabizi · Standard message
┌──────────────────────────────────────────────────────────────┐
│ Aslema! El casque bluetooth b 220 DT. …        (dir="auto")  │
└──────────────────────────────────────────────────────────────┘
Safety checks: ✓ Rule checks passed                  ← + judge rows only when judge is a verdict
Standard message · no AI-written text                ← route line
Demo: sending records it in the conversation. The public demo never sends WhatsApp messages.
                                                  [ Send message ]   ← filled when it is the primary (§2.7)
```
- **Safety rows:**
  - `prefilter.passed` → `draft.check.prefilter`; otherwise one `draft.check.prefilter_fail` per failure.
  - When `judge` is a verdict (Sunday, S-3), add these rows, each ✓/✗:

    | Row | Passes when |
    |---|---|
    | `draft.check.grounded` | `grounded && unsupported_claims.length == 0` |
    | `draft.check.language` | `language_ok` |
    | `draft.check.tone` | `tone_ok` |
    | `draft.check.overreach` | `overreach == "none"` |
    | `draft.check.one_question` | `question_count == "one"` |

  - `judge.unavailable` → `draft.check.judge_unavailable`.
- **Route line:**
  - `source == "static_template"` → `draft.route.static`;
  - `auto_send` → `draft.route.auto`;
  - `needs_review` → `draft.route.review`, where `{check}` is the first failing row;
  - `blocked` → `draft.route.blocked`.
- **Help line:** `action.send.help.public` when `health.wa_send == false`, else `action.send.help.event`.
- **After sending:** the panel collapses to `action.send.done` plus "Sent (simulated)" when `delivery == "recorded_only"`.
- **Read-only:** the text is visible, and the Send button is replaced by `draft.readonly`.
- **No draft:** hidden when the tier is low. While `rescore_state == "drafting"`, show a skeleton with `draft.drafting`.

**F. DEMO · Simulate a customer reply:** see §4.2. Shown only when `capabilities.can_simulate_reply` is true and the source is not snapshot.

### 2.7 Primary action map (exactly one filled button)
The UI renders only actions in `capabilities.actions`, plus Send when `capabilities.can_send_drafts` and Try when `capabilities.can_try`. First match wins.

| Condition | Filled primary | Secondary (outline/ghost) |
|---|---|---|
| snapshot source | none | none (all disabled, `common.offline_tooltip`) |
| `capabilities.read_only` | **`action.try`** (when `can_try`) | none; `detail.readonly.note` sits under it |
| `status == "collecting"` | none; `row.scoring` while `rescore_state != "idle"`, else `detail.not_order` | `action.cancel` |
| `awaiting_reply` with an unsent, non-blocked draft | **`action.send`**, rendered in E; A shows the text link "Send message ↓", which scrolls to it | `action.approve`, `action.cancel` |
| `awaiting_reply` with the draft already sent | none; `detail.waiting` | `action.approve`, `action.cancel` |
| `needs_review` | **`action.approve`** | `action.request_confirmation`, `action.cancel` |
| `ready_to_ship` | **`action.ship`** | `action.cancel` |
| `shipped` | **`action.mark_delivered`** | `action.mark_refused` (confirm popover) |
| terminal | none; status only | none |

**Button behaviour:**
- **Lifecycle:** default → loading (label `…loading`, disabled, spinner) → success (refetch) → error (inline text under the button, button re-enabled).
- **409 responses:**
  - `INVALID_TRANSITION` → `error.INVALID_TRANSITION`, then refetch.
  - `SEEDED_READ_ONLY` → `toast.seeded_read_only` with a Try button.
- **Destructive actions** (cancel, mark refused) confirm in a popover (`action.*.confirm`), never a modal.

### 2.8 Activity feed (Sunday Should)
- **Item:** `EventView.title` and `detail` as text, with an icon from `level` and a link from `order_ref`.
- **Click:** selects `order_id`.
- **Limits:** at most 50 items in the DOM.
- **Empty state:** `activity.empty`.
- **Unread count:** shown on the drawer toggle.

### 2.9 State catalogue (every state the UI must render)

| State | Trigger (data) | Where | Treatment | Copy keys |
|---|---|---|---|---|
| **First load** | no data yet | queue, detail | 5 skeleton rows; detail skeleton (static under reduced motion) | none |
| **First load failed** | 3 failed `/api/orders` attempts (1 s, 2 s, 4 s) | page | centred message, Retry, plus "Open recorded snapshot" if the mirror exists | `banner.first_load_error.*` |
| **Empty queue** | no visible rows | queue | text + Paste button | `queue.empty.*` |
| **No selection** | no `?order=` | detail | centred hint; in public mode the banner CTA is filled | `detail.empty.*` |
| **Poll error ×1** | one failure | none | silent, data kept | none |
| **Connection lost** | ≥ 2 consecutive failures | status bar | amber, data kept, auto-retry | `banner.connection` |
| **Selected order gone** | detail 404 (purged copy, reseed, another visitor's id) | detail | message + two buttons | `detail.not_found`, `.try`, `.back` |
| **Detail error** | detail 5xx / network | detail | last data kept, inline amber line | `detail.error` |
| **Scoring (new order)** | `collecting`, `rescore_state != "idle"`, `score == null` | row, A, C | grey `Scoring…` badge; ghost card | `row.scoring`, `timeline.pending.*` |
| **Rescoring** | `rescore_state` `debouncing` / `scoring` / `drafting` | row chip, ghost card, 1 s detail poll | pulsing dot; ghost card text per state; polite live region | `row.rescoring`, `timeline.pending.*` |
| **Score changed** | `score.version` increased | row, C, live region | 1.5 s flash; new-card highlight; announcement for the selected order only | `sr.score_changed` |
| **Fallback active** | `health.llm.fallback_active` | status bar | amber, not dismissible, 10 s grace | `banner.fallback` |
| **Degraded path on a version** | `path` is `fallback_model`, `fallback_provider` or `rules` | timeline chip, Why chip, row flags | chip text + reason (`llm_cap_reached`, `rules_path`, `not_primary_model`) | `enum.path.*`, `enum.conf_reason.*` |
| **LLM budget reached** | `health.llm.cap_reached` or `visitor_cap.reached` | status bar, paste dialog, reply box | amber banner; inline notes; scripted chip stays enabled | `banner.cap.*`, `paste.cap_note`, `demo.cap_note` |
| **Snapshot / unreachable** | `?source=snapshot`, or first load failed and the snapshot was opened | page | grey banner; Try, Send, Paste, Reply and actions disabled with a tooltip | `banner.snapshot`, `common.offline_tooltip` |
| **Read-only sample** | `capabilities.read_only` | A, E, F | Sample chip + note; single filled **Try this order**; Send replaced by a note; F hidden | `detail.sample_chip`, `detail.readonly.note`, `action.try`, `draft.readonly` |
| **Try in progress / done / error** | `POST /api/orders/{id}/try` | A, banner CTA | loading → select the new `order_id` → announce. `429 SANDBOX_LIMIT` / `409 NOT_SEEDED` / other → inline | `action.try.loading`, `try.done.sr`, `try.error.*` |
| **Your copy** | `!is_seeded && seed_key` | row chip, A | `Yours` chip; "Your copy of sample #2601" | `row.yours`, `detail.copy_of` |
| **Simulated message** | `message.origin == "simulated"` | bubble | amber outline chip, always visible | `convo.simulated` |
| **Sent (simulated)** | outbound `origin` `dashboard`/`simulated`, or `DraftView.delivery == "recorded_only"` | bubble meta, E | neutral text, no ticks | `chip.sent_simulated` |
| **Auto-recorded draft** | `SimulateReplyResponse.recorded_draft_id != null` | live region, F note beforehand | announcement; the bubble gets `Simulated` + "Sent (simulated)" | `demo.autorecord_note`, `demo.autorecord.sr` |
| **Injection suspected** | `assessment.injection_suspected` (B3) | A chip, Why | amber chip | `chip.injection` |
| **Waiting for reply** | `awaiting_reply` + draft sent | A | no filled button; waiting line | `detail.waiting` |
| **Not an order** | `collecting` + `idle` + selected | A, B | explanatory line, no timeline | `detail.not_order` |
| **Send error** | 409 / 502 from send | E | inline red text, button re-enabled | `draft.error.*` |
| **Seeded mutation refused** | 409 `SEEDED_READ_ONLY` | toast | Skeptic's text + Try button, then refetch | `toast.seeded_read_only` |
| **ROI unavailable** | `/api/metrics/impact` fails | queue top | line hidden | none |

### 2.10 Accessibility and motion (Round 1 Appendix A, still correct, updated)

**Roles**
- Rows are `<button>`s inside `<ul role="list" aria-label="Orders by risk">`.
- The detail is a `<section aria-labelledby>`.
- The public banner is `role="region"`, and status bars are `role="status"`.
- The paste dialog is a `<dialog>` with a focus trap. `Esc` closes it and focus returns to the opener.

**Keyboard**
- Tab order: header → banners → queue → detail.
- In the queue, ↑/↓ move between rows and Enter or Space selects.
- Marks are focusable (`tabIndex=0`) and show their label on focus.

**Focus and live regions**
- Polling never moves focus. The selected row keeps focus across re-sorts.
- There is one polite live region. It announces only:
  - changes to the selected order's score or status;
  - Try, Paste, Send and Reply results;
  - the auto-record notice.
- Nothing is announced on routine polls.

**Visual**
- Tier is never colour-only: text, number and shape. The delta is an arrow, a number and an `aria-label`.
- Contrast: text ≥ 4.5:1; focus rings and boundaries ≥ 3:1 [VERIFY with a checker once the palette is set]. Highlighted text stays near-black.
- Targets are ≥ 44×44 px: buttons, rows, actionable chips.

**Motion**

| Transition | Duration |
|---|---|
| hover / focus | 120 ms |
| chip swap | 200 ms |
| flash | 1.5 s |
| FLIP (Sunday) | 300 ms |

Under `prefers-reduced-motion` everything is instant, and the flash becomes a static 2 px outline.

**Content limits**

| Content | Limit | Overflow |
|---|---|---|
| name | 22 chars in the row, 40 in the detail | ellipsis + `title` |
| `reason_short` | 90 chars (server) | CSS ellipsis as a guard |
| chips | ≤ 28 chars EN (+30 % FR) | wrap in the detail, never in the row |
| paste text | 2,000 chars | counter amber at 1,900 |
| reply text | 1,000 chars (Architect §4) | counter amber at 900 |
| price | `220 TND`; decimals only when non-integer | none |
| times | HH:mm Tunis; relative in the queue | none |

### 2.11 Component API (for Montassar)
```
App                  owns: datasource, visitorId, selection (?order=)
Header               props: health: HealthResponse|null; pollState: "live"|"reconnecting"|"snapshot"; onPaste()
PublicBanner         props: visible: boolean; heroOrderId: string|null; ctaPrimary: boolean; onTry(orderId)
StatusBanners        props: health; pollFailures: number; snapshotMeta: {captured_at: string}|null
RoiLine              props: impact: ImpactResponse|null
Queue                props: list: OrderListResponse; selectedId; onSelect(id)
QueueRow             props: order: OrderSummary; selected; changed; mode: AppMode
TierBadge            props: tier: Tier|null; score: number|null; size: "sm"|"lg"
DeltaArrow           props: delta: number|null
OrderDetail          props: detail: OrderDetailResponse|null; health; samples: OrderSummary[]; handlers
PrimaryActions       props: order; capabilities: Capabilities; currentDraft: DraftView|null; snapshot: boolean
WhyPanel             props: assessment: AssessmentView
ScoreTimeline        props: assessments: AssessmentView[]; rescoreState: RescoreState
Transcript / Bubble  props: messages: MessageView[]; drafts: DraftView[]  (drafts → author line)
Segments             props: segments: Segment[]           (the only highlight code in the app)
DraftPanel           props: drafts: DraftView[]; canSend: boolean; waSend: boolean; onSend(id) → Promise<SendDraftResponse>
SimulateReply        props: conversationId; scriptedReplies: string[]; hasUnsentDraft: boolean; capNote: boolean;
                            onSubmit(text) → Promise<SimulateReplyResponse>
PasteOrderDialog     props: open; mode: AppMode; capNote: boolean; onSubmit(IngestRequest) → Promise<IngestResponse>; onClose()
ActivityFeed (Sun)   props: events: EventView[]; onSelectOrder(id)
usePoll<T>(path, {intervalMs, fastWhile?: (t: T) => boolean, fastMs?: number, enabled}) → {data, error, failures, lastOkAt}
```

---

## 3. Evidence rendering from server `segments`, and RTL/bidi rules

### 3.1 Server side (Omar and Jesser; algorithm in Architect Round 3)
- **Built per message on the original text**, using the `normalize_with_map` index map. Spans are stored per run as `spans_json` `[{message_id, start, end, kind, code, quote}]`, and the projection splits them into `Segment[]`.
- **Invariant (tested):** `segments.map(s => s.text).join("") === text`.
- **Only surviving evidence from the current assessment is highlighted:**
  - flags that remain **after** `resolve_flags()` → `kind: "risk"`, with `codes` = the union of flag codes covering the segment;
  - verified `address_quotes` → `kind: "address"`.

  A flag removed by `resolve_flags` produces no span. That's why the three amber marks on hero message 1 disappear at v2, while the v1 timeline card still lists them from `assessments[0].flags`. In the §6 mock, message 1 is therefore a single plain segment.
- **Priority:** `risk` over `address`. Overlaps split naturally.
- **Scope:** only `author == "customer"` messages carry `segments`. Outbound messages have `segments: null`, so the AI never gets to flag its own words, and the UI shows it.
- **Labels:** `label` is server-built English from one file (Fedi reviews it). React and Streamlit show it verbatim.
- **Quote isolation:** every customer quote inside `reason`, `reason_short`, `reason_diff`, `EventView.title`/`detail` and flag labels is wrapped as U+2068 FSI + quote + U+2069 PDI. In JSON these appear as `⁨…⁩`. They're plain characters, not markup.

### 3.2 Client side (React)
```tsx
export function Segments({ segments }: { segments: Segment[] }) {
  return <>{segments.map((s, i) => s.kind
    ? <mark key={i} className={`hl hl-${s.kind}`} tabIndex={0} data-label={s.label ?? ""}>
        {s.text}<span className="sr-only"> ({s.label})</span>
      </mark>
    : <Fragment key={i}>{s.text}</Fragment>)}</>;
}
// Bubble: <p dir="auto" className="bubble-text">{m.segments ? <Segments segments={m.segments}/> : m.text}</p>
```
- **Text nodes only.** React escapes them, so `<script>` in customer text renders as text. The browser does no offset maths, which means code-point versus UTF-16 differences and emoji can't shift anything.
- **Label on hover and focus:** `mark:hover::after, mark:focus-visible::after { content: attr(data-label) }`. `title` is not used, because it doesn't show on keyboard focus.

| kind | Style | Meaning to the seller |
|---|---|---|
| `risk` | amber background, plus a 2 px dotted bottom border | this raised the risk |
| `address` | 2 px solid green underline, no fill | address detail found (good) |

Text stays near-black in both styles. **No `unicode-bidi` or `direction` on `mark`**, so the paragraph's `dir="auto"` resolution stays intact across segments.

### 3.3 RTL/bidi rules (all in one place)
1. **The page is `<html lang="en" dir="ltr">`, and the UI chrome is LTR English.** There is no Arabic chrome in this build, because it would need a mirrored layout.
2. **`dir="auto"` goes on every element holding customer- or draft-authored text:** bubbles, the draft box, timeline flag quotes, the reply textarea, the paste textarea, and `last_message_preview` if it's shown. Direction comes from the **first strong character**:

   | Text | Direction |
   |---|---|
   | `السلام عليكم…` | RTL |
   | `نخدم في الصباح، livraison après 17h svp 🙏` | RTL paragraph with an embedded LTR run |
   | `salam, nheb…` (Arabizi) | LTR |
   | `Svp après 17h, خاطر…` | LTR |

   All of these are correct. **Never split a message by script, and never force a direction.**
3. **`text-align: start` on bubble paragraphs**, so Arabic right-aligns *inside* its bubble. Bubble *position* comes only from `author`, via flex `justify-content`, never from `dir`.
4. **Names and bare quotes inside chrome** go in `<bdi>`. That covers the row and detail name, `flags[].quote` in the timeline (`<bdi dir="auto">`), and `order_ref` next to a name. Without it, "سارة م. · #2604" would reorder the ref and the separator.
5. **Server sentences** (`reason`, `reason_short`, `reason_diff`, event titles, labels) arrive with their isolates already in place. Render them as plain text inside LTR elements, and **never put `dir="auto"` on them**: a reason that starts with an Arabic quote would flip the whole English sentence.
6. **Numbers and currency** next to Arabic always come from chrome (`149 TND` in its own span). The client never concatenates them into customer text.
7. **Placeholders** in `dir="auto"` textareas stay in English. Alignment flips as soon as the user types Arabic.
8. **Bubbles use `line-height: 1.6` for every script** (Arabic diacritics need it), with the Arabic fallback fonts from §1.3 [VERIFY on the recording machine].
9. **Streamlit follows the same rules:** `<p dir="auto">` with escaped segments (§1.5), and `<bdi>` around names inside any HTML string.
10. **Tests:**
    - Server: Craftsman's segment tests (tatweel and harakat, an emoji before a quote, overlapping spans, a quote that appears twice, `<script>`, the join invariant).
    - Client: the lint, the grep, and G4 check 3 as the manual RTL check on the mocks.

---

## 4. Paste-order, Try-this-order and simulate-reply UI

### 4.1 Paste order dialog
Opened from `header.paste` or the empty queue, as a modal `<dialog>` 560 px wide.

| Field | Control | Binding | Validation |
|---|---|---|---|
| Customer name | text input, `dir="auto"`, max 40. **Hidden in public mode**, because visitor rows are pseudonymised (Architect mode matrix) | `customer_name` | none |
| Customer message | textarea, 6 rows, `dir="auto"`, required | `text` | 1–2,000 chars; counter `paste.counter` turns amber at ≥ 1,900 |
| Order details (optional), **P3, collapsed** | Product (text), Price TND (number ≥ 0), Zone (Urban / Suburban / Rural / Not sure) | `structured.product_name`, `.price_tnd`, `.zone` (omitted for "Not sure") | numeric price |

- **Notes above the buttons:**
  - public mode → `paste.privacy.public`;
  - a cap is reached → `paste.cap_note`. Submit stays enabled, and the order gets a rules-only score.
- **Buttons:** **`paste.submit`** (filled, the dialog's only primary) and `paste.cancel` (ghost). Enter adds a newline; Ctrl/Cmd+Enter submits.
- **Flow:** `POST /api/orders/ingest {kind: "paste", text, customer_name?, structured?}` → `202 IngestResponse`.
  1. Close the dialog.
  2. Select `created[0].order_id`.
  3. Announce `paste.sr.done`, using `created[0].order_ref`.
  4. The row appears at the top as `Scoring…`, and the detail shows the pasted bubble plus the ghost card (`debouncing`, then `scoring`).
  5. The detail polls every 1 s.
- **Errors:** the dialog stays open and keeps the text.

  | Response | Copy |
  |---|---|
  | 422 | field message (`error.VALIDATION_ERROR`) |
  | 413 | `paste.error.too_long` |
  | 429 `SANDBOX_LIMIT` | `try.error.limit` |
  | network / 5xx | `paste.error` |

- CSV upload stays API-only in this build.

### 4.2 Simulate a customer reply (Demo tools, region F)
Shown when `capabilities.can_simulate_reply` is true and the source isn't snapshot. That excludes read-only samples and terminal orders.
```
┌ ─ DEMO ─ Simulate a customer reply ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  Your reply goes through the same pipeline as a WhatsApp message and is marked
  Simulated in the conversation.
  Scripted reply · instant:  [ ey behi. Douar Ouled Ali, triq el jemaa, dar 14 … ]   ← one chip per scripted_replies[]
  (i) The message above hasn't been sent. Your simulated reply records it as sent    ← only when an unsent draft exists
      first, so the reply answers it.
  ┌ textarea dir="auto", 3 rows, placeholder "Type what the customer would reply…" ┐
  └────────────────────────────────────────────────────────────────────────────────┘
  (note line: demo.cap_note | demo.error)                    {n} / 1,000
                                                     [ Send simulated reply ]   ← outline, neutral, never filled
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```
- **Placement:** below the conversation, so the whole transcript separates it from Send. Dashed border, grey `DEMO` tag, no brand colour.
- **Scripted chip:** clicking it **fills** the textarea rather than sending, so the viewer sees the text first. The chip shows at most 60 characters, with the full text in `title`. It is the zero-LLM path (Skeptic N-3), so it stays enabled under every cap.
- **Button states:**

  | Condition | Button | Note |
  |---|---|---|
  | textarea empty | disabled | `demo.empty` via `aria-describedby` |
  | an unsent draft exists (`has_pending_draft`) | enabled | `demo.autorecord_note` (info) |
  | budget reached | enabled | `demo.cap_note` |
  | over 1,000 chars | disabled | counter turns red |
  | submitting | "Sending…", textarea read-only | none |

- **Flow:** `POST /api/conversations/{conversation_id}/simulate-reply {kind: "text", text}` → `202 SimulateReplyResponse`.
  1. Clear the textarea and announce `demo.done.sr`.
  2. If `recorded_draft_id`, also announce `demo.autorecord.sr`.
  3. Poll every 1 s.
  4. The next poll shows the new bubble with the **`Simulated`** chip, plus the auto-recorded outbound bubble if there was one.
  5. The ghost card moves from `debouncing` to `scoring`. The new version card appears and flashes, and the ScoreBlock and queue row update.
  6. If the response `order_id` is not the selected order (the previous order was terminal), select it and announce `demo.new_order`.
- **Errors:** `demo.error`, with the text kept.

  | Response | Copy |
  |---|---|
  | 409 `SEEDED_READ_ONLY` | `toast.seeded_read_only` |
  | 413 | `demo.error.too_long` |
  | `REPLY_LIMIT` (if Skeptic's limit ships) | `demo.error.reply_limit` |

- **Location-pin reply** (`{kind: "location"}`) is P3.

### 4.3 Try this order
- **Where it appears:** the detail's primary button on a read-only sample (`capabilities.can_try`), and the public banner CTA, which targets the `seed_key == "hero"` sample (B1).
- **Flow:** `POST /api/orders/{order_id}/try` → `201 TryResponse`.
  1. The button shows `action.try.loading`.
  2. Select `TryResponse.order_id` and announce `try.done.sr`.
  3. Poll every 1 s.
  4. The copy appears with `Yours` and `Scoring…`, then v1 arrives. There's no debounce, and the result comes from the cache.
- **Errors:** `429 SANDBOX_LIMIT` → `try.error.limit`; `409 NOT_SEEDED` → `try.error.not_seeded`; anything else → `try.error`.
- **The judge's public hero journey (about 60 s):**
  1. **Try the main sample**.
  2. v1 HIGH 83, with three amber phrases in the Arabizi message.
  3. Optionally **Send message**, which shows as "Sent (simulated)".
  4. Scripted reply chip → **Send simulated reply**.
  5. "Rescoring…" for about 5 s [estimate: 4 s demo debounce + cache hit].
  6. v2 LOW 14 ▼69: the amber marks disappear, the new address is underlined green, the timeline shows `Rule: customer confirmed ×0.6 (starting assumption)` and "Resolved: …", and the row flashes.
- **Video end card:** Strategist's end card must use these exact button names: **"Try this order → Send simulated reply"**. Fedi edits the caption to match.

---

## 5. Copy table (English source; notes for Fedi's FR/AR pass)

**Rules for Fedi:**
- **Language:** UI chrome ships in **English**. Switch to French only if the video narration is French, and decide that **by Sat 18:00**, because the safety take is recorded at 21:00 [VERIFY with Fedi].
- **No Arabic chrome.** It would need a mirrored layout. The AR notes below cover two things only: video captions and glosses, and checking that each English label matches what the flagged Darija phrase actually says.
- **Wording:**
  - buttons use verbs;
  - no "AI-powered" or "smart";
  - anything simulated says "simulated", "synthetic", "sample" or "recorded";
  - ×0.6 and +15 are always called a "starting assumption";
  - no refusal-rate figure appears unless it is sourced.
- **Fixed strings:**
  - Rows marked **(Skeptic, exact)** are safety copy from Skeptic Round 3 §2.7. Change them only with Skeptic's OK.
  - Rows marked **(server)** live in the server's text file, not in `web/src/copy/en.ts`.
- **Mechanics:** leave `{…}` placeholders untranslated. Budget +30 % width for French.

### 5.1 Chrome, header, banners

| Key | EN | Fedi note (FR / AR) |
|---|---|---|
| `app.name` | {Product name} | Fedi picks it by G1 12:00 |
| `header.live` | Live | FR "En direct" |
| `header.reconnecting` | Reconnecting… | FR "Reconnexion…" |
| `header.snapshot` | Snapshot | FR "Instantané" |
| `header.mode.public` | Public demo | FR "Démo publique" |
| `header.mode.event` | Live pilot · a person approves every send | FR "Pilote en direct · chaque envoi est validé par une personne" |
| `header.mode.dev` | Dev | none |
| `header.mode.tooltip.public` | Synthetic sample data. This demo never sends WhatsApp messages. | none |
| `header.mode.tooltip.event` | Judge-gated auto-send is built; in this pilot a person clicks Send. | "judge" only if S-3 ships; otherwise "Auto-send is off; a person clicks Send." |
| `header.whatsapp.last` | WhatsApp · last message {time} | none |
| `header.whatsapp.none` | WhatsApp · no messages yet | none |
| `header.paste` | Paste order | FR "Coller une commande" |
| `header.activity` | Activity | Sunday |
| `banner.public` | Public demo. Sample orders are synthetic and read-only — use **Try this order** to get your own copy. What you add is visible only in this browser and deleted after 2 hours. This demo never sends WhatsApp messages. | **(Skeptic, exact)**; "2 hours" must match `SANDBOX_TTL_S` |
| `banner.public.cta` | Try the main sample | FR "Essayer l'exemple principal" |
| `banner.cap.global` | Today's live-AI budget for this public demo is used up. New text is scored by the rules-only fallback (marked **rules**). Sample orders still show real AI output recorded on {date}. The budget resets at 01:00 Tunis time. | **(Skeptic, exact)**; `{date}` = the `seed_version` capture date [Jesser to expose it, or drop "on {date}"] |
| `banner.cap.visitor` | You've used this browser's live-AI allowance (6 per 10 minutes, 20 per day). New text uses the rules-only fallback until {time}. | **(Skeptic, exact)**; numbers = `VISITOR_LLM_CAP_*`; `{time}` = `visitor_cap.until` (B2) |
| `banner.fallback` | The main AI model is unavailable right now. Scores are coming from {path}; each score shows which path produced it. | **(Skeptic, exact)**; `{path}` = `enum.path.*` label |
| `banner.connection` | Connection lost. Showing data from {time}. Retrying… | none |
| `banner.snapshot` | Offline snapshot: the live backend is unreachable, so this page shows outputs recorded from the real system on {date}. Nothing on this page is live. | **(Skeptic, exact)** |
| `banner.first_load_error.title` | Couldn't reach the demo server. | none |
| `banner.first_load_error.body` | It may be starting up. Retrying in {s} s. | [VERIFY host cold-start behaviour] |
| `banner.first_load_error.retry` | Retry now | none |
| `banner.first_load_error.snapshot` | Open recorded snapshot | only if the mirror ships |
| `toast.seeded_read_only` | Sample orders are read-only so every visitor starts from the same point. **Try this order** to work on your own copy. | **(Skeptic, exact)** |
| `roi.line` | Simulated on {n} synthetic orders: refusal rate {before} → {after}, {trips} trips and {tnd} TND avoided. | the word "Simulated" is never cut; no number without it |
| `roi.assumptions` | Assumptions | none |
| `footer.synthetic` | All orders and customers in this demo are synthetic test data. | never cut |
| `footer.build` | Build {git_sha} · config {config_hash} | none |
| `common.offline_tooltip` | Live server offline | none |
| `common.tnd` | {amount} TND | FR/local usage often says "DT"; pick one and use it in the slides too |
| `common.rel.now` / `.min` / `.h` / `.d` | just now / {n} min / {n} h / {n} d | none |

### 5.2 Queue and rows

| Key | EN | Fedi note |
|---|---|---|
| `queue.aria` | Orders by risk | screen reader only |
| `queue.summary` | {review} need review · {waiting} waiting for customer · {ready} ready to ship | singular: "1 needs review" |
| `queue.group.closed` | Closed ({n}) | FR "Clôturées ({n})" |
| `queue.empty.title` | No orders yet. | none |
| `queue.empty.body.event` | Orders appear here when a customer messages the WhatsApp number, or you can paste one. | none |
| `queue.empty.body.public` | Paste a customer message to score it. | none |
| `queue.empty.cta` | Paste order | same as `header.paste` |
| `row.sample` | Sample | FR "Exemple" |
| `row.yours` | Yours | FR "À vous" |
| `row.scoring` | Scoring… | FR "Évaluation…" |
| `row.rescoring` | Rescoring… | FR "Réévaluation…" |
| `row.low_conf` | Low confidence | FR "Confiance faible" |
| `row.rules` | Rules only | same as `enum.path.rules` |
| `row.draft_ready` | Message ready | FR "Message prêt" |
| `row.unnamed` | Unnamed customer | FR "Client sans nom" |
| `row.tier.aria` | {tier} risk, score {score} | e.g. "High risk, score 83" |
| `row.delta.down.aria` / `.up.aria` | risk down {n} / risk up {n} | none |

### 5.3 Detail, actions, Why, timeline

| Key | EN | Fedi note |
|---|---|---|
| `detail.empty.title` | Select an order | none |
| `detail.empty.body` | Pick an order on the left to see why it was scored and what to do next. | none |
| `detail.not_found` | This order isn't available any more. Your copies are deleted after 2 hours. | none |
| `detail.not_found.try` | Try the sample again | only when `seed_key` is known |
| `detail.not_found.back` | Back to the queue | none |
| `detail.error` | Couldn't refresh this order. Showing the last version. Retrying… | none |
| `detail.sample_chip` | Sample · read-only | none |
| `detail.copy_of` | Your copy of sample {ref} | none |
| `detail.readonly.note` | This sample is shared by every visitor, so it's read-only. Make your own copy to send the message and simulate the customer's reply. | none |
| `detail.history.new` | New customer | FR "Nouveau client" |
| `detail.history.some` | {n} past orders · {r} refused at door | none |
| `detail.zone_default` | (not found in the address; default used) | appended to the zone |
| `detail.not_order` | Not an order yet: no product or address found in the messages so far. | none |
| `detail.waiting` | Waiting for the customer's reply · sent {time} | none |
| `chip.injection` | Possible instruction text in the message — check before acting. | **(Skeptic, exact)** |
| `chip.sent_simulated` | Sent (simulated) — the public demo never sends WhatsApp messages. | **(Skeptic, exact)**; short form "Sent (simulated)" in bubble meta, full text in `title` |
| `action.try` | Try this order | FR "Essayer cette commande"; must match the video end card |
| `action.try.loading` | Making your copy… | none |
| `try.done.sr` | Your copy {ref} is ready. | screen reader |
| `try.error.limit` | You already have 15 copies. Copies are deleted after 2 hours. | "15" = `SANDBOX_MAX_ORDERS` |
| `try.error.not_seeded` | This order can't be copied. | none |
| `try.error` | Couldn't make a copy: {message}. | none |
| `action.send` | Send message | FR "Envoyer le message" |
| `action.send.loading` | Sending… | none |
| `action.send.done` | Sent {time} | none |
| `action.send.help.public` | Demo: sending records it in the conversation. The public demo never sends WhatsApp messages. | never cut |
| `action.send.help.event` | Sends on WhatsApp to {phone_masked}. | none |
| `action.approve` | Approve for shipping | FR "Valider l'expédition" |
| `action.request_confirmation` | Ask the customer to confirm | none |
| `action.ship` | Mark shipped | FR "Marquer expédiée" |
| `action.mark_delivered` | Mark delivered | FR "Marquer livrée" |
| `action.mark_refused` | Refused at door | FR "Refusée à la livraison" |
| `action.cancel` | Cancel order | FR "Annuler la commande" |
| `action.cancel.confirm` | Cancel this order? The customer won't be messaged. · [Cancel order] [Keep order] | none |
| `action.mark_refused.confirm` | Mark as refused at the door? This counts in the customer's history. · [Mark refused] [Keep] | fairness-sensitive; keep it neutral |
| `why.title` | Why this score | none |
| `why.conf.high` | High confidence | none |
| `why.conf.low` | Low confidence · check before acting | none |
| `why.factors` | Biggest factors | none |
| `timeline.title` | Score history | none |
| `timeline.card.header` | v{n} · {trigger} · {time} | none |
| `timeline.model` | Model {model_score} | integer |
| `timeline.rule` | Rule: {label} {effect} (starting assumption) | "starting assumption" is mandatory (SD §4 cold-start priors) |
| `timeline.flags` | Flagged: {items} | label + quote in `<bdi>` |
| `timeline.resolved` | Resolved: {labels} | none |
| `timeline.pending.debouncing` | New message · rescoring in a few seconds… | none |
| `timeline.pending.scoring` | Reading the messages and scoring… | none |
| `timeline.pending.drafting` | Drafting the message to the customer… | none |
| `sr.score_changed` | Order {ref}: {tier} {score}, risk {direction} {n}. | screen reader |

### 5.4 Conversation, drafts, demo tools, paste, activity, errors

| Key | EN | Fedi note |
|---|---|---|
| `convo.title` | Conversation | none |
| `convo.empty` | No messages yet. | none |
| `convo.simulated` | Simulated | never cut; FR "Simulé" |
| `convo.pasted` | Pasted | none |
| `convo.voice` | Voice note · not transcribed | none |
| `convo.location` | Location pin | none |
| `convo.unsupported` | Unsupported: {kind} | none |
| `convo.meta.seller` | Sent by you | none |
| `convo.meta.template` | Standard message | FR "Message standard" |
| `convo.meta.ai` | AI-written, safety-checked | Sunday only |
| `draft.title` | Message to customer | none |
| `draft.sub` | {language} · {source} | none |
| `draft.checks` | Safety checks | none |
| `draft.check.prefilter` | Rule checks passed | none |
| `draft.check.prefilter_fail` | Rule check failed: {failure} | `{failure}` **(server)** |
| `draft.check.grounded` | Uses only order facts | Sunday |
| `draft.check.language` | Same language as the customer | Sunday |
| `draft.check.tone` | Tone matches the customer | Sunday |
| `draft.check.overreach` | No promises or discounts | Sunday |
| `draft.check.one_question` | One clear question | Sunday |
| `draft.check.judge_unavailable` | Safety judge unavailable — review before sending | Sunday; fail-closed |
| `draft.route.static` | Standard message · no AI-written text | Saturday default |
| `draft.route.auto` | Judge approved · eligible for auto-send (in this demo a person sends) | Sunday |
| `draft.route.review` | Needs your review: {check} | none |
| `draft.route.blocked` | Blocked by safety checks: {reason} | none |
| `draft.earlier` | Earlier messages ({n}) | none |
| `draft.blocked_group` | Blocked drafts ({n}) | none |
| `draft.drafting` | Drafting the message… | none |
| `draft.readonly` | Make your own copy to send this message. | none |
| `draft.error` | Not sent: {reason}. The message is kept. | none |
| `draft.error.ALREADY_SENT` | Already sent. | none |
| `draft.error.DRAFT_BLOCKED` | This draft failed the safety checks and can't be sent. | none |
| `draft.error.WINDOW_CLOSED` | Not sent: more than 24 h since the customer's last message. Review needed. | none |
| `draft.error.LOOP_GUARD` | Not sent: the automatic message limit for this order is reached. | none |
| `draft.error.WHATSAPP_SEND_FAILED` | WhatsApp didn't accept the message. Nothing was sent. Try again. | none |
| `draft.retry` | Try again | none |
| `demo.tag` | DEMO | none |
| `demo.title` | Simulate a customer reply | matches the video end card |
| `demo.body` | Your reply goes through the same pipeline as a WhatsApp message and is marked Simulated in the conversation. | none |
| `demo.scripted` | Scripted reply · instant | none |
| `demo.placeholder` | Type what the customer would reply… | none |
| `demo.submit` | Send simulated reply | FR "Envoyer la réponse simulée" |
| `demo.submit.loading` | Sending… | none |
| `demo.empty` | Type a reply first. | none |
| `demo.autorecord_note` | The message above hasn't been sent. Your simulated reply records it as sent first, so the reply answers it. | none |
| `demo.autorecord.sr` | The message was recorded as sent (simulated) before your reply. | screen reader |
| `demo.cap_note` | Live-AI budget used: a typed reply is scored by rules only. The scripted reply still uses recorded AI output. | none |
| `demo.done.sr` | Simulated reply added. Rescoring. | screen reader |
| `demo.new_order` | Your reply opened a new order {ref}. | none |
| `demo.error` | Couldn't add the reply: {message}. Your text is kept. | none |
| `demo.error.too_long` | Replies are limited to 1,000 characters. | none |
| `demo.error.reply_limit` | This conversation has reached the demo's reply limit. Try another sample. | only if Skeptic's `REPLY_LIMIT` ships |
| `paste.title` | Paste an order | none |
| `paste.name` | Customer name (optional) | event/dev mode only |
| `paste.message` | Customer message | none |
| `paste.placeholder` | Paste the customer's message exactly as they wrote it: Darija, Arabizi or French. | AR note: the placeholder contains no example phrase, so no few-shot or eval text leaks into the UI |
| `paste.counter` | {n} / 2,000 | none |
| `paste.details` | Order details (optional) | P3 |
| `paste.product` / `.price` / `.zone` | Product / Price (TND) / Delivery zone | none |
| `enum.zone.urban` / `.suburban` / `.rural` / `.unknown` | Urban / Suburban / Rural / Not sure | FR "Urbaine / Périurbaine / Rurale / Je ne sais pas" |
| `paste.privacy.public` | Visible only in this browser and deleted after 2 hours. Don't paste real customer data. | never cut in public mode |
| `paste.cap_note` | Live-AI budget used: this order will be scored by rules only (Low confidence). | none |
| `paste.submit` | Add order | FR "Ajouter la commande" |
| `paste.submit.loading` | Adding… | none |
| `paste.cancel` | Cancel | none |
| `paste.error` | Couldn't add the order: {message}. Your text is still here. | none |
| `paste.error.too_long` | Messages are limited to 2,000 characters. | none |
| `paste.sr.done` | Order {ref} added. Scoring. | screen reader |
| `activity.empty` | Nothing yet. Every message, score change and safety decision shows up here. | Sunday |
| `error.SEEDED_READ_ONLY` | → `toast.seeded_read_only` | none |
| `error.INVALID_TRANSITION` | That action isn't possible any more: the order changed. The page is up to date now. | none |
| `error.VALIDATION_ERROR` | {field}: {message} | none |
| `error.PAYLOAD_TOO_LARGE` | That's too long for this demo. | none |
| `error.SANDBOX_LIMIT` | → `try.error.limit` | none |
| `error.DEMO_BUSY` | The demo is busy right now. Try again in a few minutes. | only if Skeptic's global sandbox cap ships |
| `error.INTERNAL` | Something went wrong on the server. Try again. | also used for unknown codes, followed by the server `message` |
| `error.network` | No connection to the server. Try again. | none |

### 5.5 Enum labels (client-side map, `enum.*`)

| Key | EN | Fedi note |
|---|---|---|
| `enum.tier.high` / `.medium` / `.low` | HIGH / MED / LOW | FR ÉLEVÉ / MOYEN / FAIBLE |
| `enum.action.confirm` | Confirm with customer | FR "Confirmer avec le client" |
| `enum.action.ship` | Ship | FR "Expédier" |
| `enum.action.prepay` | Ask for prepayment | never "require"; fairness (SD §12) |
| `enum.action.review` | Needs your review | none |
| `enum.action.cancelled` | Cancelled | none |
| `enum.status.collecting` | Collecting details | none |
| `enum.status.awaiting_reply` | Waiting for customer | none |
| `enum.status.needs_review` | Needs review | none |
| `enum.status.ready_to_ship` | Ready to ship | none |
| `enum.status.shipped` / `.delivered` / `.refused` / `.cancelled` | Shipped / Delivered / Refused at door / Cancelled | none |
| `enum.trigger.initial` / `.customer_reply` / `.no_reply_timeout` / `.manual` | First score / Customer replied / No reply in time / Manual rescore | none |
| `enum.path.llm` | AI extraction | none |
| `enum.path.fallback_model` | Backup AI model | none |
| `enum.path.fallback_provider` | Backup AI provider | tooltip names the provider (Gemini) only if it's actually live |
| `enum.path.cascade_ack` | No AI needed · short reply | the cost-control story; keep "No AI needed" |
| `enum.path.cascade_cache` / `enum.path.cached` | Recorded AI result · no new AI call | also used when `extraction.cache_hit`, and for Skeptic's `path='cached'` if it ships |
| `enum.path.rules` | Rules only | + `· live-AI budget used` (`llm_cap_reached`) or `· AI unavailable` (`rules_path`) |
| `enum.conf_reason.near_tier_boundary` | Close to a tier boundary | none |
| `enum.conf_reason.not_primary_model` | Backup AI used | none |
| `enum.conf_reason.product_not_in_catalog` | Product not in catalog | none |
| `enum.conf_reason.dropped_flags` | Some AI quotes failed verification | none |
| `enum.conf_reason.clarity_unclear` | Message is unclear | none |
| `enum.conf_reason.rules_path` | AI unavailable, rules only | none |
| `enum.conf_reason.llm_cap_reached` | Live-AI budget used | none |
| `enum.channel.whatsapp` / `.paste` / `.csv` / `.simulated` | WhatsApp / Pasted / CSV / Sample data | none |
| `enum.delivery.queued` / `.sent` / `.delivered` / `.read` / `.failed` | Sending / Sent / Delivered / Read / Not delivered | WhatsApp origin only |
| `enum.language.arabizi` / `.darija_arabic_script` / `.ar` / `.fr` / `.mixed` | Arabizi / Darija (Arabic script) / Arabic / French / Mixed | none |
| `enum.source.static_template` / `.llm_rewrite` | Standard message / AI rewrite of the standard message | none |
| `enum.flag.vague_location` | Vague location | AR: covers "9rib el jemaa", "قدام الصيدلية", "كلمني كي توصل"; must equal the server label |
| `enum.flag.availability_uncertain` | May not be home | AR: matches "mouch dima fi dar" |
| `enum.flag.price_hesitation` | Price hesitation | AR: matches "ghali chwaya", "غالية شوية" |
| `enum.flag.third_party_recipient` | Someone else receives | none |
| `enum.flag.prior_refusal_mention` | Mentions a past refusal | none |
| `enum.flag.pressure_or_inconsistency` | Pressure or inconsistency | none |

**(server) labels for Fedi to review:** `Segment.label` ("Vague location", "Address detail", …), `flags[].label`, `adjustments[].label` ("customer confirmed", "customer declined", "customer rescheduled", "unclear reply", "no reply in time"), `top_factors[].label`, `reason*`, `EventView.title/detail`, and `fallback_reason`. The client-side `enum.flag.*` labels must equal the server's flag labels. Fedi reviews both lists together.

---

## 6. Frozen mocks the frontend builds against

**Status and ownership.** These are the frozen working contract from Sat 09:00, and Montassar builds against them from the first frontend block.
- **Commit and validation:** Jesser commits them as `mocks/*.json`, and they must pass C3 (`tests/contract/test_mocks_match_models.py`) at G2 12:00. **If C3 fails, fix the mock or the model at 12:00, not the UI.**
- **Change rules:** after 12:00, changes are additive only. A rename needs Montassar's OK.
- **Replacement:** at G6 (18:00), `scripts/dump_mocks.py` regenerates the files from the seeded DB.

**Shape and scenario.** The shapes are Architect Round 3 §4.2 plus B1 (`seed_key`), B2 (`llm.visitor_cap`) and B3 (`injection_suspected`). The scenario is **public mode**, seen by one visitor who:
- ran the hero loop on their copy (#2613), clicked Send, then sent the scripted reply;
- then pasted an order (#2614, `debouncing`).

**Placeholders.** Replace these numbers with the `tests/golden/hero.json` values once `train.py` writes them:
- the hero numbers are the council's hand-computed values (v1 model 82.5 → 83; v2 model 23.9 ×0.6 → 14);
- the ROI numbers in `roi.line` are illustrative only (there is no impact mock).

Two text placeholders for Fedi:
- the template texts, which his `data/templates/*.yaml` replaces;
- the tone phrase `manich mt2akda`, which he picks.

The hero messages follow Alchemist §B.10 plus the Round 2 `price_hesitation` phrase. No text equals FS7/FS8 or an eval phrase.

**How the files were checked:**
- generated by a script with Crockford-alphabet ULIDs;
- `segments.map(s => s.text).join("") === text` checked for every customer message;
- `reason_short` ≤ 90 characters;
- `last_message_preview` ≤ 80 characters;
- `json.loads` run on every file;
- FSI/PDI written as `⁨`/`⁩` escapes, so they're visible in review.

**Mock DataSource routing:**

| Request | Returns |
|---|---|
| `GET /api/orders` | `orders.json` |
| `GET /api/orders/{#2613 id}` | `order_detail.json` |
| `GET /api/orders/{#2604 id}` | `order_detail_ar.json` |
| `GET /api/orders/{any other id}` | **404**, which exercises the "order gone" state |
| `GET /api/health` | `health.json` |
| `GET /api/metrics/impact` | 404 (the ROI line stays hidden) |
| POSTs | resolve after 600 ms with a canned success; Try returns the #2613 id |

### 6.1 `mocks/orders.json`
```json
{
  "orders": [
    {
      "order_id": "01K6BQGBAHZWZRV6XFY1TD2RM5",
      "order_ref": "#2601",
      "conversation_id": "01K6BQGJZQFT6PDDRA4Y3E3NZ3",
      "customer": {
        "customer_id": "01K6BQ3W97ZV27FVPRYW0S7JR0",
        "display_name": "Amira B.",
        "phone_masked": "+216 •• ••• 456"
      },
      "channel": "simulated",
      "status": "awaiting_reply",
      "rescore_state": "idle",
      "product_name": "Casque Bluetooth",
      "price_tnd": 220.0,
      "score": {
        "version": 1,
        "final_score": 83,
        "tier": "high",
        "action": "confirm",
        "confidence": "high",
        "path": "llm",
        "delta": null,
        "reason_short": "Vague address (\u20689rib el jemaa\u2069) · rural zone · 220 TND · may not be home"
      },
      "has_pending_draft": true,
      "is_seeded": true,
      "read_only": true,
      "last_message_preview": "salam, nheb el casque bluetooth. Douar Ouled Ali, 9rib el jemaa. ama ghali chway",
      "updated_at": "2026-09-29T08:40:09Z",
      "seed_key": "hero"
    },
    {
      "order_id": "01K6BQXJCEM7Z6N47TXXCA84E0",
      "order_ref": "#2606",
      "conversation_id": "01K6BQ8EH9CN564G946BBDK3N4",
      "customer": {
        "customer_id": "01K6BQA61BE2J173MJRR9YQTSH",
        "display_name": "Karim S.",
        "phone_masked": "+216 •• ••• 731"
      },
      "channel": "simulated",
      "status": "awaiting_reply",
      "rescore_state": "idle",
      "product_name": "Aspirateur sans fil",
      "price_tnd": 349.0,
      "score": {
        "version": 1,
        "final_score": 71,
        "tier": "high",
        "action": "prepay",
        "confidence": "high",
        "path": "llm",
        "delta": null,
        "reason_short": "Mentions a past refusal (\u2068l marra li fetet ma 5dhitech\u2069) · 349 TND"
      },
      "has_pending_draft": true,
      "is_seeded": true,
      "read_only": true,
      "last_message_preview": "slm nheb l aspirateur, l marra li fetet ma 5dhitech el colis ama taw sure",
      "updated_at": "2026-09-29T08:40:15Z",
      "seed_key": "prepay_refusal"
    },
    {
      "order_id": "01K6BQSRFS30WGF8B7ZB4PN0WH",
      "order_ref": "#2605",
      "conversation_id": "01K6BQ4WDWFKFWFF8EXA87VFVA",
      "customer": {
        "customer_id": "01K6BQQZ9001K4AZRCJCKKG7SM",
        "display_name": "Hela T.",
        "phone_masked": "+216 •• ••• 902"
      },
      "channel": "simulated",
      "status": "needs_review",
      "rescore_state": "idle",
      "product_name": "Sac en cuir",
      "price_tnd": 89.0,
      "score": {
        "version": 1,
        "final_score": 58,
        "tier": "medium",
        "action": "review",
        "confidence": "low",
        "path": "rules",
        "delta": null,
        "reason_short": "Rules only · address has no street · 89 TND"
      },
      "has_pending_draft": false,
      "is_seeded": true,
      "read_only": true,
      "last_message_preview": "Bonjour je veux le sac marron, livraison à Sidi Bouzid centre",
      "updated_at": "2026-09-29T08:40:18Z",
      "seed_key": "rules_fallback"
    },
    {
      "order_id": "01K6BQ8KZNRN4ZPQYKZCEFEP6K",
      "order_ref": "#2604",
      "conversation_id": "01K6BQJASZHTG1B7X23WFG679F",
      "customer": {
        "customer_id": "01K6BQKVGH2B3X75FN971E1GZN",
        "display_name": "سارة م.",
        "phone_masked": "+216 •• ••• 218"
      },
      "channel": "simulated",
      "status": "awaiting_reply",
      "rescore_state": "idle",
      "product_name": "Montre connectée noire",
      "price_tnd": 149.0,
      "score": {
        "version": 1,
        "final_score": 52,
        "tier": "medium",
        "action": "confirm",
        "confidence": "high",
        "path": "llm",
        "delta": null,
        "reason_short": "Landmark-only address (\u2068قدام الصيدلية\u2069) · call on arrival · 149 TND"
      },
      "has_pending_draft": true,
      "is_seeded": true,
      "read_only": true,
      "last_message_preview": "نخدم في الصباح، livraison après 17h svp 🙏",
      "updated_at": "2026-09-29T08:40:12Z",
      "seed_key": "ar_landmark"
    },
    {
      "order_id": "01K6BQE7V07HEGWEZ9FAY5PZ0N",
      "order_ref": "#2603",
      "conversation_id": "01K6BQ0FRDQG3AQ8DK5E746D8M",
      "customer": {
        "customer_id": "01K6BQ0BEJKZA876SMX0E5NQ89",
        "display_name": "Mohamed A.",
        "phone_masked": "+216 •• ••• 250"
      },
      "channel": "simulated",
      "status": "delivered",
      "rescore_state": "idle",
      "product_name": "Tapis de bain",
      "price_tnd": 45.0,
      "score": {
        "version": 1,
        "final_score": 18,
        "tier": "low",
        "action": "ship",
        "confidence": "high",
        "path": "llm",
        "delta": null,
        "reason_short": "Exact address · returning customer · 45 TND"
      },
      "has_pending_draft": false,
      "is_seeded": true,
      "read_only": true,
      "last_message_preview": "3aslema, nheb tapis el azra9, nahj Tahar Haddad 7, Nabeul",
      "updated_at": "2026-09-29T08:40:03Z",
      "seed_key": "delivered_example"
    },
    {
      "order_id": "01K6BQYHJC44GNGQSBFFZ45VT3",
      "order_ref": "#2613",
      "conversation_id": "01K6BQWP0YG8NE96SK25AX9G3B",
      "customer": {
        "customer_id": "01K6BQ0W9PT4KWXP0QAGBYP3FA",
        "display_name": "Customer #2613",
        "phone_masked": null
      },
      "channel": "simulated",
      "status": "ready_to_ship",
      "rescore_state": "idle",
      "product_name": "Casque Bluetooth",
      "price_tnd": 220.0,
      "score": {
        "version": 2,
        "final_score": 14,
        "tier": "low",
        "action": "ship",
        "confidence": "high",
        "path": "cascade_cache",
        "delta": -69,
        "reason_short": "Exact address · customer confirmed · rural zone · 220 TND"
      },
      "has_pending_draft": false,
      "is_seeded": false,
      "read_only": false,
      "last_message_preview": "ey behi. Douar Ouled Ali, triq el jemaa, dar 14 el bab lazra9 9odem el pharmacie",
      "updated_at": "2026-09-29T09:06:31Z",
      "seed_key": "hero"
    },
    {
      "order_id": "01K6BQDXX6ARFX02AYSS1029VD",
      "order_ref": "#2608",
      "conversation_id": "01K6BQMEEDAB6E42NY7YXJF992",
      "customer": {
        "customer_id": "01K6BQTTVDFD8ZE4QDKV4DY5RV",
        "display_name": "Youssef K.",
        "phone_masked": "+216 •• ••• 377"
      },
      "channel": "simulated",
      "status": "ready_to_ship",
      "rescore_state": "idle",
      "product_name": "Montre connectée noire",
      "price_tnd": 149.0,
      "score": {
        "version": 2,
        "final_score": 11,
        "tier": "low",
        "action": "ship",
        "confidence": "high",
        "path": "cascade_ack",
        "delta": -27,
        "reason_short": "Customer confirmed (short reply) · exact address · 149 TND"
      },
      "has_pending_draft": false,
      "is_seeded": true,
      "read_only": true,
      "last_message_preview": "ok",
      "updated_at": "2026-09-29T08:40:21Z",
      "seed_key": "cascade_ack"
    },
    {
      "order_id": "01K6BQM7ZVARCDFMGFPZA3PBNT",
      "order_ref": "#2602",
      "conversation_id": "01K6BQ7W39WKJTT05JP7E3Q8J0",
      "customer": {
        "customer_id": "01K6BQXYY42AT8XD4E221EVFG0",
        "display_name": "Ines M.",
        "phone_masked": "+216 •• ••• 614"
      },
      "channel": "simulated",
      "status": "ready_to_ship",
      "rescore_state": "idle",
      "product_name": "Crème hydratante",
      "price_tnd": 35.0,
      "score": {
        "version": 1,
        "final_score": 9,
        "tier": "low",
        "action": "ship",
        "confidence": "high",
        "path": "llm",
        "delta": null,
        "reason_short": "Exact address (\u206812 rue Ali Belhouane, imm. Salwa\u2069) · 35 TND"
      },
      "has_pending_draft": false,
      "is_seeded": true,
      "read_only": true,
      "last_message_preview": "Bonjour, je commande la crème hydratante. 12 rue Ali Belhouane, imm. Salwa, 2e é",
      "updated_at": "2026-09-29T08:40:06Z",
      "seed_key": "fr_exact"
    },
    {
      "order_id": "01K6BQVAR3ET2HC88ZC0ZWZC5R",
      "order_ref": "#2614",
      "conversation_id": "01K6BQADYHFKXT3ZRWD6KH9377",
      "customer": {
        "customer_id": "01K6BQQXTYSET9K4XGVZ22Z0Z5",
        "display_name": "Customer #2614",
        "phone_masked": null
      },
      "channel": "paste",
      "status": "collecting",
      "rescore_state": "debouncing",
      "product_name": null,
      "price_tnd": null,
      "score": null,
      "has_pending_draft": false,
      "is_seeded": false,
      "read_only": false,
      "last_message_preview": "nheb zouz kwayes, cité ennour ba3d el marché",
      "updated_at": "2026-09-29T09:08:02Z",
      "seed_key": null
    }
  ],
  "counts": {
    "low": 4,
    "medium": 2,
    "high": 2,
    "needs_review": 1,
    "awaiting_reply": 3,
    "ready_to_ship": 3
  },
  "server_time": "2026-09-29T09:08:05Z",
  "mode": "public"
}
```

### 6.2 `mocks/order_detail.json` (the visitor's copy of the hero, after the reply loop)
```json
{
  "order": {
    "order_id": "01K6BQYHJC44GNGQSBFFZ45VT3",
    "order_ref": "#2613",
    "conversation_id": "01K6BQWP0YG8NE96SK25AX9G3B",
    "customer": {
      "customer_id": "01K6BQ0W9PT4KWXP0QAGBYP3FA",
      "display_name": "Customer #2613",
      "phone_masked": null
    },
    "channel": "simulated",
    "status": "ready_to_ship",
    "rescore_state": "idle",
    "product_name": "Casque Bluetooth",
    "price_tnd": 220.0,
    "score": {
      "version": 2,
      "final_score": 14,
      "tier": "low",
      "action": "ship",
      "confidence": "high",
      "path": "cascade_cache",
      "delta": -69,
      "reason_short": "Exact address · customer confirmed · rural zone · 220 TND"
    },
    "has_pending_draft": false,
    "is_seeded": false,
    "read_only": false,
    "last_message_preview": "ey behi. Douar Ouled Ali, triq el jemaa, dar 14 el bab lazra9 9odem el pharmacie",
    "updated_at": "2026-09-29T09:06:31Z",
    "seed_key": "hero",
    "quantity": 1,
    "zone": "rural",
    "zone_source": "gazetteer",
    "address_text": "Douar Ouled Ali, triq el jemaa, dar 14 el bab lazra9 9odem el pharmacie",
    "product_id": "P12",
    "language": "arabizi",
    "auto_messages_sent": 0,
    "awaiting_reply_since": "2026-09-29T09:05:40Z",
    "seller_approved_at": null,
    "opened_at": "2026-09-29T09:02:03Z"
  },
  "customer": {
    "customer_id": "01K6BQ0W9PT4KWXP0QAGBYP3FA",
    "display_name": "Customer #2613",
    "phone_masked": null,
    "completed_orders": 0,
    "refusals_total": 0
  },
  "conversation": {
    "conversation_id": "01K6BQWP0YG8NE96SK25AX9G3B",
    "channel": "simulated",
    "messages": [
      {
        "message_id": "01K6BQDZ5NN3SN7KG5KXXJ71JD",
        "direction": "inbound",
        "author": "customer",
        "origin": "seed",
        "kind": "text",
        "provider_ts": "2026-09-29T09:02:03Z",
        "text": "salam, nheb el casque bluetooth. Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya w mouch dima fi dar, manich mt2akda",
        "segments": [
          {
            "text": "salam, nheb el casque bluetooth. Douar Ouled Ali, 9rib el jemaa. ama ghali chwaya w mouch dima fi dar, manich mt2akda",
            "kind": null,
            "codes": [],
            "label": null
          }
        ],
        "transcript": null,
        "location": null,
        "reply_to": null,
        "template_id": null,
        "delivery_status": null
      },
      {
        "message_id": "01K6BQY703QCJ62VTX0BP0CERC",
        "direction": "outbound",
        "author": "ai",
        "origin": "dashboard",
        "kind": "text",
        "provider_ts": "2026-09-29T09:05:40Z",
        "text": "Aslema! El casque bluetooth b 220 DT. Bech nwasslouhoulek, ab3athli esm el nahj w noumrou el dar, w 2akedli el commande (ey / le).",
        "segments": null,
        "transcript": null,
        "location": null,
        "reply_to": null,
        "template_id": "T_ADDRESS",
        "delivery_status": null
      },
      {
        "message_id": "01K6BQNR4P2B45JE8XY6EQH1ZA",
        "direction": "inbound",
        "author": "customer",
        "origin": "simulated",
        "kind": "text",
        "provider_ts": "2026-09-29T09:06:25Z",
        "text": "ey behi. Douar Ouled Ali, triq el jemaa, dar 14 el bab lazra9 9odem el pharmacie. ghodwa ba3d 17h nkoun fi dar",
        "segments": [
          {
            "text": "ey behi. ",
            "kind": null,
            "codes": [],
            "label": null
          },
          {
            "text": "Douar Ouled Ali, triq el jemaa, dar 14 el bab lazra9 9odem el pharmacie",
            "kind": "address",
            "codes": [],
            "label": "Address detail"
          },
          {
            "text": ". ghodwa ba3d 17h nkoun fi dar",
            "kind": null,
            "codes": [],
            "label": null
          }
        ],
        "transcript": null,
        "location": null,
        "reply_to": null,
        "template_id": null,
        "delivery_status": null
      }
    ]
  },
  "assessments": [
    {
      "assessment_id": "01K6BQKXDVKD9N3E7Y5FVMK286",
      "version": 1,
      "trigger": "initial",
      "created_at": "2026-09-29T09:02:04Z",
      "path": "cascade_cache",
      "model_score": 82.5,
      "final_score": 83,
      "delta": null,
      "tier": "high",
      "action": "confirm",
      "confidence": "high",
      "confidence_reasons": [],
      "confirmation": "none",
      "reason": "Vague address (\u20689rib el jemaa\u2069) · rural delivery zone · 220 TND order · may not be home (\u2068mouch dima fi dar\u2069) · price hesitation (\u2068ghali chwaya\u2069)",
      "reason_diff": null,
      "adjustments": [],
      "resolved_flags": [],
      "flags": [
        {
          "code": "vague_location",
          "label": "Vague location",
          "quote": "9rib el jemaa",
          "message_id": "01K6BQDZ5NN3SN7KG5KXXJ71JD"
        },
        {
          "code": "price_hesitation",
          "label": "Price hesitation",
          "quote": "ghali chwaya",
          "message_id": "01K6BQDZ5NN3SN7KG5KXXJ71JD"
        },
        {
          "code": "availability_uncertain",
          "label": "May not be home",
          "quote": "mouch dima fi dar",
          "message_id": "01K6BQDZ5NN3SN7KG5KXXJ71JD"
        }
      ],
      "top_factors": [
        {
          "feature": "zone_encoded",
          "label": "Rural delivery zone",
          "value": 2,
          "contribution": 15.0
        },
        {
          "feature": "address_specificity",
          "label": "Vague address (landmark only)",
          "value": 0.5,
          "contribution": 12.0
        },
        {
          "feature": "price_tnd",
          "label": "Order value 220 TND",
          "value": 220,
          "contribution": 11.0
        }
      ],
      "extraction": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "cache_hit": true,
        "valid": true,
        "dropped_flags": 0,
        "latency_ms": null
      },
      "config_hash": "3f9a1c2e",
      "classifier_version": "classifier_v1",
      "prompt_version": "extract-v1",
      "injection_suspected": false
    },
    {
      "assessment_id": "01K6BQS5QDA1BW3W3EHC6WQNDS",
      "version": 2,
      "trigger": "customer_reply",
      "created_at": "2026-09-29T09:06:31Z",
      "path": "cascade_cache",
      "model_score": 23.9,
      "final_score": 14,
      "delta": -69,
      "tier": "low",
      "action": "ship",
      "confidence": "high",
      "confidence_reasons": [],
      "confirmation": "confirmed",
      "reason": "Exact address (\u2068dar 14 el bab lazra9 9odem el pharmacie\u2069) · customer confirmed · rural delivery zone · 220 TND order",
      "reason_diff": "Address now exact · customer confirmed ×0.6 · resolved: vague address, may not be home, price hesitation",
      "adjustments": [
        {
          "rule": "confirmed",
          "label": "customer confirmed",
          "effect": "x0.6",
          "before": 24,
          "after": 14
        }
      ],
      "resolved_flags": [
        "vague_location",
        "availability_uncertain",
        "price_hesitation"
      ],
      "flags": [],
      "top_factors": [
        {
          "feature": "zone_encoded",
          "label": "Rural delivery zone",
          "value": 2,
          "contribution": 15.0
        },
        {
          "feature": "price_tnd",
          "label": "Order value 220 TND",
          "value": 220,
          "contribution": 11.0
        },
        {
          "feature": "address_specificity",
          "label": "Exact address",
          "value": 1.0,
          "contribution": -9.0
        }
      ],
      "extraction": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "cache_hit": true,
        "valid": true,
        "dropped_flags": 0,
        "latency_ms": null
      },
      "config_hash": "3f9a1c2e",
      "classifier_version": "classifier_v1",
      "prompt_version": "extract-v1",
      "injection_suspected": false
    }
  ],
  "drafts": [
    {
      "draft_id": "01K6BQCA0PFCMRYN4F4383Z5W6",
      "assessment_version": 1,
      "template_id": "T_ADDRESS",
      "language": "arabizi",
      "text": "Aslema! El casque bluetooth b 220 DT. Bech nwasslouhoulek, ab3athli esm el nahj w noumrou el dar, w 2akedli el commande (ey / le).",
      "canonical_text": "Aslema! El casque bluetooth b 220 DT. Bech nwasslouhoulek, ab3athli esm el nahj w noumrou el dar, w 2akedli el commande (ey / le).",
      "source": "static_template",
      "route": "needs_review",
      "prefilter": {
        "passed": true,
        "failures": []
      },
      "judge": null,
      "sent_message_id": "01K6BQY703QCJ62VTX0BP0CERC",
      "sent_at": "2026-09-29T09:05:40Z",
      "delivery": "recorded_only",
      "created_at": "2026-09-29T09:02:04Z"
    }
  ],
  "capabilities": {
    "read_only": false,
    "can_try": false,
    "can_simulate_reply": true,
    "can_rescore": true,
    "can_send_drafts": true,
    "actions": [
      "ship",
      "cancel"
    ]
  },
  "scripted_replies": [
    "ey behi. Douar Ouled Ali, triq el jemaa, dar 14 el bab lazra9 9odem el pharmacie. ghodwa ba3d 17h nkoun fi dar"
  ]
}
```

### 6.3 `mocks/order_detail_ar.json` (seeded Arabic-script sample, read-only; G4 checks 3–5)
```json
{
  "order": {
    "order_id": "01K6BQ8KZNRN4ZPQYKZCEFEP6K",
    "order_ref": "#2604",
    "conversation_id": "01K6BQJASZHTG1B7X23WFG679F",
    "customer": {
      "customer_id": "01K6BQKVGH2B3X75FN971E1GZN",
      "display_name": "سارة م.",
      "phone_masked": "+216 •• ••• 218"
    },
    "channel": "simulated",
    "status": "awaiting_reply",
    "rescore_state": "idle",
    "product_name": "Montre connectée noire",
    "price_tnd": 149.0,
    "score": {
      "version": 1,
      "final_score": 52,
      "tier": "medium",
      "action": "confirm",
      "confidence": "high",
      "path": "llm",
      "delta": null,
      "reason_short": "Landmark-only address (\u2068قدام الصيدلية\u2069) · call on arrival · 149 TND"
    },
    "has_pending_draft": true,
    "is_seeded": true,
    "read_only": true,
    "last_message_preview": "نخدم في الصباح، livraison après 17h svp 🙏",
    "updated_at": "2026-09-29T08:40:12Z",
    "seed_key": "ar_landmark",
    "quantity": 1,
    "zone": "urban",
    "zone_source": "gazetteer",
    "address_text": "حي النصر · قدام الصيدلية",
    "product_id": "P10",
    "language": "darija_arabic_script",
    "auto_messages_sent": 0,
    "awaiting_reply_since": null,
    "seller_approved_at": null,
    "opened_at": "2026-09-29T08:40:02Z"
  },
  "customer": {
    "customer_id": "01K6BQKVGH2B3X75FN971E1GZN",
    "display_name": "سارة م.",
    "phone_masked": "+216 •• ••• 218",
    "completed_orders": 2,
    "refusals_total": 0
  },
  "conversation": {
    "conversation_id": "01K6BQJASZHTG1B7X23WFG679F",
    "channel": "simulated",
    "messages": [
      {
        "message_id": "01K6BQ0V51QJ67B9B1JZ2Q7Z9N",
        "direction": "inbound",
        "author": "customer",
        "origin": "seed",
        "kind": "text",
        "provider_ts": "2026-09-29T08:40:02Z",
        "text": "السلام عليكم، نحب نطلب الساعة الذكية السوداء. العنوان حي النصر قدام الصيدلية، كلمني كي توصل",
        "segments": [
          {
            "text": "السلام عليكم، نحب نطلب الساعة الذكية السوداء. العنوان ",
            "kind": null,
            "codes": [],
            "label": null
          },
          {
            "text": "حي النصر",
            "kind": "address",
            "codes": [],
            "label": "Address detail"
          },
          {
            "text": " ",
            "kind": null,
            "codes": [],
            "label": null
          },
          {
            "text": "قدام الصيدلية",
            "kind": "risk",
            "codes": [
              "vague_location"
            ],
            "label": "Vague location"
          },
          {
            "text": "، ",
            "kind": null,
            "codes": [],
            "label": null
          },
          {
            "text": "كلمني كي توصل",
            "kind": "risk",
            "codes": [
              "vague_location"
            ],
            "label": "Vague location"
          }
        ],
        "transcript": null,
        "location": null,
        "reply_to": null,
        "template_id": null,
        "delivery_status": null
      },
      {
        "message_id": "01K6BQXNHCNGCTX84VVSRNVVA4",
        "direction": "inbound",
        "author": "customer",
        "origin": "seed",
        "kind": "text",
        "provider_ts": "2026-09-29T08:40:05Z",
        "text": "نخدم في الصباح، livraison après 17h svp 🙏",
        "segments": [
          {
            "text": "نخدم في الصباح، livraison après 17h svp 🙏",
            "kind": null,
            "codes": [],
            "label": null
          }
        ],
        "transcript": null,
        "location": null,
        "reply_to": null,
        "template_id": null,
        "delivery_status": null
      }
    ]
  },
  "assessments": [
    {
      "assessment_id": "01K6BQ78VC9JZRNBHN564ZAT10",
      "version": 1,
      "trigger": "initial",
      "created_at": "2026-09-29T08:40:12Z",
      "path": "llm",
      "model_score": 51.6,
      "final_score": 52,
      "delta": null,
      "tier": "medium",
      "action": "confirm",
      "confidence": "high",
      "confidence_reasons": [],
      "confirmation": "none",
      "reason": "Landmark-only address (\u2068قدام الصيدلية\u2069) · asks to be called on arrival (\u2068كلمني كي توصل\u2069) · urban zone · 149 TND order",
      "reason_diff": null,
      "adjustments": [],
      "resolved_flags": [],
      "flags": [
        {
          "code": "vague_location",
          "label": "Vague location",
          "quote": "قدام الصيدلية",
          "message_id": "01K6BQ0V51QJ67B9B1JZ2Q7Z9N"
        },
        {
          "code": "vague_location",
          "label": "Vague location",
          "quote": "كلمني كي توصل",
          "message_id": "01K6BQ0V51QJ67B9B1JZ2Q7Z9N"
        }
      ],
      "top_factors": [
        {
          "feature": "address_specificity",
          "label": "Vague address (landmark only)",
          "value": 0.5,
          "contribution": 12.0
        },
        {
          "feature": "red_flag_count",
          "label": "2 risk phrases",
          "value": 2,
          "contribution": 6.0
        },
        {
          "feature": "zone_encoded",
          "label": "Urban delivery zone",
          "value": 0,
          "contribution": -4.0
        }
      ],
      "extraction": {
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "cache_hit": false,
        "valid": true,
        "dropped_flags": 0,
        "latency_ms": 2140
      },
      "config_hash": "3f9a1c2e",
      "classifier_version": "classifier_v1",
      "prompt_version": "extract-v1",
      "injection_suspected": false
    }
  ],
  "drafts": [
    {
      "draft_id": "01K6BQ0BGZ1KY7ZTSRMMF0G0W1",
      "assessment_version": 1,
      "template_id": "T_ADDRESS",
      "language": "darija_arabic_script",
      "text": "عسلامة! الساعة الذكية السوداء بـ 149 دينار. باش توصلك، ابعثلنا اسم النهج ونومرو الدار، وأكدلنا الطلبية (إيه / لا).",
      "canonical_text": "عسلامة! الساعة الذكية السوداء بـ 149 دينار. باش توصلك، ابعثلنا اسم النهج ونومرو الدار، وأكدلنا الطلبية (إيه / لا).",
      "source": "static_template",
      "route": "needs_review",
      "prefilter": {
        "passed": true,
        "failures": []
      },
      "judge": null,
      "sent_message_id": null,
      "sent_at": null,
      "delivery": null,
      "created_at": "2026-09-29T08:40:12Z"
    }
  ],
  "capabilities": {
    "read_only": true,
    "can_try": true,
    "can_simulate_reply": false,
    "can_rescore": false,
    "can_send_drafts": false,
    "actions": []
  },
  "scripted_replies": [
    "إيه، نهج الحرية عدد 12، الطابق الثاني. بعد الخمسة نكون في الدار"
  ]
}
```

### 6.4 `mocks/health.json` (public mode, normal)
```json
{
  "status": "ok",
  "mode": "public",
  "wa_send": false,
  "webhook": "disabled",
  "db": true,
  "demo_mode": true,
  "build": {
    "git_sha": "a1b2c3d",
    "started_at": "2026-09-29T08:39:40Z"
  },
  "config": {
    "config_hash": "3f9a1c2e",
    "prompt_version": "extract-v1",
    "classifier_version": "classifier_v1",
    "seed_version": 1
  },
  "llm": {
    "llm_mode": "live",
    "chain_extract": [
      "groq:openai/gpt-oss-120b",
      "groq:openai/gpt-oss-20b",
      "gemini:TBD"
    ],
    "chain_judge": [],
    "primary": "groq:openai/gpt-oss-120b",
    "fallback_active": false,
    "fallback_reason": null,
    "last_path": "llm",
    "last_call_at": "2026-09-29T09:07:58Z",
    "remaining_tokens": null,
    "live_calls_today": 42,
    "live_call_cap": 300,
    "cap_reached": false,
    "visitor_cap": {
      "reached": false,
      "until": null
    }
  },
  "whatsapp": {
    "last_webhook_at": null
  },
  "worker": {
    "last_tick_at": "2026-09-29T09:08:05Z",
    "pending": 1,
    "last_purge_at": "2026-09-29T09:00:00Z"
  }
}
```

### 6.5 Mock state switches (`?mock=<state>`, applied in `web/src/api/mock.ts`; dev and G4 only)

| `?mock=` | Patch |
|---|---|
| `empty` | `orders: []`, all counts 0 |
| `error` | every GET rejects, which drives connection-lost and then first-load-failed |
| `cap` | `health.llm.cap_reached = true` |
| `visitor_cap` | `health.llm.visitor_cap = {reached: true, until: "2026-09-29T09:18:00Z"}` |
| `fallback` | `health.llm.fallback_active = true`, `fallback_reason = "primary model rate-limited"`, `last_path = "fallback_model"` |
| `rescoring` | #2613: `rescore_state = "scoring"` in both the list and the detail |
| `event` | `mode = "event"`, `wa_send = true`, `webhook = "enabled"`, `whatsapp.last_webhook_at` set, `llm.visitor_cap = null`; every row gets `read_only = false`; #2604 `capabilities` = `{read_only: false, can_try: false, can_simulate_reply: true, can_rescore: true, can_send_drafts: true, actions: ["approve", "cancel"]}` |
| `snapshot` | source = snapshot: banner shown, actions disabled |
| `unsent` | #2613 detail: the draft gets `sent_message_id/sent_at/delivery = null`; messages 2 and 3 are removed; `assessments` = v1 only; `status = "awaiting_reply"`, `has_pending_draft = true`; `capabilities.actions = ["approve", "cancel"]`. This exercises Send and `demo.autorecord_note`. |
| `injection` | #2613 v2: `injection_suspected = true`, `confidence = "low"` |

---

## 7. Unresolved items (handed on)

1. **Gate time and the 15:30 rehearsal flip.** I pick G4 at 16:00 (Strategist Round 3) and ask that **Jesser** runs Architect's 15:30 rehearsal flip. Strategist and Architect confirm one schedule at the 09:00 kickoff.
2. **B1–B3 additive fields:** Jesser accepts or trims them at G2 12:00. All three degrade gracefully (§2.0).
3. **Try endpoint and error codes differ between Architect and Skeptic Round 3:**

   | Topic | Architect | Skeptic |
   |---|---|---|
   | Try endpoint | `POST /api/orders/{id}/try`, `cascade_cache` | `POST /api/sandbox/try`, `path='cached'` |
   | Error codes | 422 `VALIDATION_ERROR` | `VISITOR_ID_REQUIRED` 400, plus `REPLY_LIMIT` and `DEMO_BUSY` |

   The UI follows Architect and tolerates Skeptic's variants: a `cached` label, and copy for all three codes. The conductor picks one set.
4. **The budget banner's "{date}"** needs the seed capture date. Jesser adds it to `health.config`, or the phrase is dropped.
5. **UI language:** EN or FR. Fedi decides by Sat 18:00.
6. **Hero numbers:** placeholders until `tests/golden/hero.json` exists (G6).
7. **[VERIFY] list:**
   - host cold start, and whether the host shows its own loading page;
   - Streamlit ≥ 1.37 `st.fragment(run_every)`, `st.query_params` and `st.container(border=)`, only if the fallback triggers;
   - Arabic fonts and viewport width on the recording machine;
   - palette contrast;
   - the Gemini model id (the mock uses `gemini:TBD`).
