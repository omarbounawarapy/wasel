# Brief and plan: standalone brand and screen book for Wasel

Status: planning. Nothing here is built yet except the saved data, the registry and the earlier exploration rounds. Written 2026-10-07 so work can resume in any session.

## 1. The request, in the owner's words

Expand each of the 16 operations-dashboard directions (round 07) into a **standalone file** that shows every direction as a brand: the different screens, the logos, the colour schemes. Do not reuse fonts, colours or primitives (not even the `High / Medium / Low` risk vocabulary). Show how each would look **on the actual project, not as a concept**: a phone screen, the messages zone, the metrics zone, and so on. Split the work into phases with clear tasks, and save the information needed first.

## 2. Rules every direction must follow

1. **No shared identity.** Each direction has its own font pair (Latin UI + data) and its own Arabic face, its own palette, its own tier vocabulary (names, glyphs, colours), its own status vocabulary, its own logo, its own icon style and its own voice. `registry.json` assigns all of these; `_source/registry_build.py` fails if a font, a non-neutral hex colour or a tier name is repeated. Pure white and pure black are the only shared values.
2. **Real project, not a concept.** Screens use the project's real pages, real copy and real data shapes (section 4 and `_data/`). If the real product has a Messages page, every direction has a Messages page.
3. **Tier is never carried by colour alone.** Each tier has a name, a glyph and a colour (product rule, `PRODUCT.md`).
4. **Bidirectional text.** Customer text appears in Arabic script, Arabizi and French, with `dir="auto"`. Every direction shows at least one Arabic string in its own Arabic face.
5. **Synthetic data, labelled.** All orders are synthetic (as in the repo). A visible "Synthetic data" note sits in the shell.
6. **Accessible.** Text contrast at least 4.5:1 (3:1 for large), 44px touch targets on the phone screens, visible focus. A checker in Phase 4 measures this.
7. **Structure differs.** The home screen layout of each direction is the family's real structure (section 5), not a recoloured shared layout.

## 3. What is saved, and where

All under `docs/design-explorations/` (untracked, nothing committed):

| Path | Content |
|---|---|
| `README.md` | Index of every exploration round (01 to 07) |
| `01` to `07` folders | The earlier rounds as standalone HTML |
| `07-ops-dashboard-families/index.html` | The 16 families with research logic and fit verdicts |
| `registry.json` | The 16 unique brand identities (fonts, palette, tiers, statuses, logo concept, icon style, voice, phone/messages/metrics behaviour) |
| `_data/api_*.json` | Real API responses from the running app (synthetic seed data): health, orders, order detail, events, impact, eval, failures, monitor, traces |
| `_source/` | Generators for every round, including `registry_build.py` |
| `BRIEF-AND-PLAN.md` | This file |
| repo root `PRODUCT.md` | Product truth (users, purpose, positioning, constraints) |
| memory note `design-exploration-wasel` | Owner preferences for future sessions |

## 4. The real project, as the mockups must reproduce it

### Pages (from `web/app/dashboard`) and their real copy

| Page | Route | Title and subtitle | Content zones |
|---|---|---|---|
| Orders to check | `/dashboard` | "Orders to check": "Wasel reads what each customer wrote and scores how likely the order is to be refused at the door. Riskiest orders are at the top." | How-this-page-works strip; three counters (Needs your decision, Waiting for customer, Ready to ship); tier legend; ranked order table (order, customer, risk, next step, status, why) |
| Order detail | `/dashboard/order` | Header with order ref, customer, item, price, zone; verdict card (tier, next step, Review the message, Approve for shipping, Cancel order); order switcher | 1 "What the customer said" (chat transcript with highlighted risky phrases, "How this message was checked"); 2 "Message to the customer" (drafted question, edit, send); "Why this score" (reasons with points, "Full explanation"); "Score history" (v1 to v2 with reason diff); demo "try this order" controls |
| WhatsApp messages | `/dashboard/inbox` | "WhatsApp messages": "Messages your customers send to your WhatsApp business number land here within seconds, already scored." | Counters (Conversations, Needs your decision, Waiting for customer); conversation list with last message preview; empty state "No WhatsApp messages yet" |
| Add an order | `/dashboard/paste` | "Add an order": "Paste a customer's message exactly as they wrote it, in Darija, Arabizi, Arabic or French. Wasel scores it in a few seconds." | Customer message textarea with example chips; optional details (name, product, price, zone); "Score this order" |
| Money saved | `/dashboard/impact` | "Money saved": "How much wasted delivery cost Wasel avoids when you follow its advice. This is a simulation on synthetic orders, not real sales." | Hero estimate (TND saved, trips avoided, "Simulated"); Refused at the door today vs Refused with Wasel; "How this was estimated" assumptions |
| Activity log | `/dashboard/activity` | "Activity log": "Everything Wasel did, newest first: messages received, scores, drafted replies and anything that needed attention." | Counters (Messages received, Orders scored, Replies drafted, Tricks blocked); events list with "only warnings" filter |
| Quality checks | `/dashboard/quality` | "Quality checks": "Before every release, Wasel is tested on hundreds of example conversations. A release only ships when all checks pass." | Release-checks banner; cards per test family (e.g. Reading customer messages 96.1%, Safety of drafted replies 100%) with "All results" |
| Silent failures | `/dashboard/failures` | "Silent failures": "A demonstration of the silent-failure analyzer on synthetic test conversations. It is not a measurement of real Wasel conversations." | Counters (Test conversations checked, Silent failures, Worth a second look); problem groups with cases |
| Live monitor | `/dashboard/monitor` | "Live monitor": "Watches the last messages Wasel scored and warns you if they start to look different from what it was tested on." | "Are customers writing differently?" drift rows; "Is the AI behaving?" safety rates (invented quotes, unreadable answers, trick attempts) |
| AI call log | `/dashboard/traces` | "AI call log": "Every request Wasel made to an AI model: what it was for, which model answered and how long it took. Customer text is never stored here." | Counters (AI calls, Typical answer time, Backup model used); call table with role filter |

Shell: global status bar ("AI scoring live", WhatsApp state, mode); desktop sidebar in three groups (Daily work: Orders to check, WhatsApp messages, Add an order; Results: Money saved, Activity log; AI health: Quality checks, Silent failures, Live monitor, AI call log); **phone**: header with logo, bottom bar with Orders, WhatsApp, Add, Money saved and a "More" sheet listing the rest.

### Real data fields (`_data/`)
Order: `order_id, order_ref, conversation_id, customer, channel, status, rescore_state, product_name, price_tnd, score, has_pending_draft, is_seeded, read_only, last_message_preview, updated_at, injection_suspected`. Order detail adds `conversation` (messages with segments and highlights), `assessments` (versions with reasons and points), `drafts`. Impact: `n_orders, baseline_refusal_rate, projected_refusal_rate, trips_avoided, tnd_saved, assumptions`. Monitor: `drift, faithfulness, safety, ops, alerts`. Eval: per-suite results. Failures: grouped silent failures.

### The nine seeded orders (used in every mockup)
#2609 Mehdi mixeur 129 TND score 89; #2601 Sami casque bluetooth 220 TND 87; #2604 Hedi tablette 450 TND 85; #2605 Nour aspirateur 349 TND 71; #2603 سارة crème visage 35 TND 42; #2608 كريم montre connectée 149 TND 14; #2606 Yassine jean slim 59 TND 9; #2602 Leila montre connectée 149 TND 4; #2607 Rim sac en cuir 99 TND 4. Hero conversation (#2601): "Douar Ouled Ali, 9rib el jemaa" / "ama ghali chwaya" / "mouch dima fi dar". Reasons: three warning signs "9rib el jemaa" +17, rural delivery zone +13, vague address +12. After a full address the score falls to 16 (v1 87 to v2 16, "full address given -32").

## 5. The 16 directions, each with its own identity (from `registry.json`)

| # | Direction | Family | Fit | Fonts (UI + data) | Arabic | Primary on ground | Tier vocabulary | Status vocabulary |
|---|---|---|---|---|---|---|---|---|
| 01 | **Terminal Desk** | Bloomberg Terminal | medium | Archivo Narrow + Red Hat Mono | Readex Pro | #FFB000 on #000000 | ACT / WATCH / CLEAR | NEW, ASKED, WAITING, READY, VOID |
| 02 | **Golden Signals** | Observability (Grafana, Datadog) | high | Rubik + Fira Code | Rubik | #4C8DFF on #0B0C0F | CRITICAL / DEGRADED / HEALTHY | Scored, Asked, Pending reply, Ready, Closed |
| 03 | **Blotter** | Order blotter (trading workstations) | high | Arimo + Cousine | Noto Naskh Arabic | #0A246A on #D4D0C8 | CLASS I / CLASS II / CLASS III | Scored, Question sent, Awaiting reply, Ready, Cancel pending |
| 04 | **Review Desk** | Fraud review queue (Stripe Radar) | high | Figtree + Spectral | Amiri | #0B3D91 on #F6F8FB | Highest / Elevated / Normal | Open, Awaiting customer, Needs decision, Cleared, Closed |
| 05 | **Control Tower** | Logistics control tower (project44, FourKites) | medium | Manrope + Barlow | Almarai | #0F2742 on #EEF1F4 | Breach / At risk / On plan | Planned, In transit, Waiting, Delivered, Refused |
| 06 | **On-Call** | Incident console (PagerDuty) | high | Albert Sans + JetBrains Mono | Cairo | #0B7A4B on #F5F6F8 | SEV 1 / SEV 2 / SEV 3 | Triggered, Acknowledged, Snoozed, Escalated, Resolved |
| 07 | **Dispatch** | Dispatch console (911 CAD) | medium | Chakra Petch + Overpass Mono | Changa | #6FB7FF on #1A1D21 | CODE 3 / CODE 2 / CODE 1 | NEW, ASSIGNED, ON SCENE, HOLD, CLEARED |
| 08 | **Central Station** | Clinical central station (IEC 60601-1-8) | medium | Atkinson Hyperlegible + Atkinson Hyperlegible Mono | Mada | #5BE37A on #000001 | CRISIS / WARNING / ADVISORY | Monitoring, Alarm, Silenced, Stable, Discharged |
| 09 | **Grey Process** | High-performance HMI (ISA-101) | high | Saira Semi Condensed + Saira | Tajawal | #4A5158 on #C9CCD0 | CRITICAL ALARM / MAJOR / MINOR | Normal, Deviating, Abnormal, Out of service, Maintenance |
| 10 | **Scope** | Air-traffic control display | low | B612 + B612 Mono | Reem Kufi | #4BE2A0 on #06100C | ALERT / CAUTION / NOTICE | Tracked, Held, Handoff, Cleared, Lost |
| 11 | **Inbox** | Support inbox with SLAs (Zendesk, Front) | high | Nunito Sans + Literata | Alexandria | #173F35 on #FFFFFF | Breached / Slipping / On track | New, Open, Pending, On hold, Solved |
| 12 | **Back Office** | Merchant admin (Shopify Polaris) | high | Public Sans + Azeret Mono | Vazirmatn | #303030 on #F1F1F1 | Critical tone / Warning tone / Success tone | Unfulfilled, Info requested, On hold, Ready, Archived |
| 13 | **Worklist** | SAP Fiori (worklist and object page) | medium | Source Sans 3 + Source Code Pro | Noto Sans Arabic | #0A6ED1 on #F5F6F7 | Negative / Critical state / Good | To do, In process, Delegated, Completed, Rejected |
| 14 | **Batch Table** | IBM Carbon data table | high | Hanken Grotesk + Martian Mono | Noto Kufi Arabic | #0F62FE on #F4F4F4 | Sev critical / Sev major / Sev minor | Queued, Asked, Waiting, Ready, Cancelled |
| 15 | **Wallboard** | NOC and SOC wall display | low | Big Shoulders Display + Work Sans | Baloo Bhaijaan 2 | #8FB4FF on #050A14 | RED / AMBER / GREEN | Live, Stale, Paused, Test, Offline |
| 16 | **Command Inbox** | Linear | high | Geist + Geist Mono | Zain | #3FB6A8 on #0F1011 | Urgent / Soon / Later | Inbox, Doing, Waiting, Done, Dropped |

Each registry entry also carries the logo concept, icon style, voice, the home-screen structure, and how the phone, messages zone and metrics zone behave in that family.

## 6. Deliverable shape

**One standalone HTML file**, `wasel-brand-book.html`: no network, no external fonts (fonts embedded as base64 woff2), all CSS and SVG inline, opens by double-click. Layout: a direction switcher, then for the selected direction a **brand sheet** and a **screen set**; a compare view shows one screen across several directions. Size budget: 12 MB. If the budget is exceeded, split into one standalone file per direction plus an index file; decide in Phase 0.

Per direction (14 pieces):
- **Brand sheet (1):** logo suite (lockup, mark, one-colour, reversed, favicon, app icon), palette with named tokens and contrast table, type system with a scale, tier and status vocabulary with glyphs, icon set (12 icons), voice and 8 microcopy lines in English and Arabic, shell and button samples.
- **Desktop screens (7):** D1 Home (orders to check, in the family's structure); D2 Order detail with the messages zone; D3 WhatsApp messages; D4 Add an order; D5 Metrics zone (Money saved and Activity log); D6 AI health (Live monitor and Quality checks); D7 System states (empty, loading, error, offline).
- **Phone screens (6):** M1 Orders list; M2 Order detail with the primary action; M3 Messages thread; M4 Add an order; M5 Metrics glance; M6 More sheet and navigation.

16 directions x 14 = 224 pieces. Estimates below use units: S about one working session, M about three, L about eight.

## 7. Phases and tasks

### Phase 0: Foundation (L)
Goal: everything later directions need, so each direction is a pure composition job.
- **T0.1 Data pack (S).** Turn `_data/*.json` into one `dataset.json` of nine orders, conversation, reasons, history, events, metrics, eval, monitor and traces, plus Arabic and French strings. Accept: every screen's content can be read from this file only.
- **T0.2 Content inventory (S).** Freeze section 4 as `content.json`: titles, subtitles, labels, empty states, button texts per page. Accept: each string traces to a file in `web/`.
- **T0.3 Identity lock (S).** Review `registry.json` with the owner, confirm or swap fonts and palettes, confirm each tier vocabulary still means "refusal risk". Accept: checker prints no duplicates.
- **T0.4 Font acquisition (M).** Download every font in the registry (Latin, mono, Arabic) as woff2 subsets (Latin, Latin-ext, Arabic, digits), verify licences and availability, record file sizes. Accept: all 16 sets load offline; size table written. Fallback for any missing font: swap in the registry and rerun the checker.
- **T0.5 Build skeleton (M).** One Python build: reads registry, dataset and content, renders a direction module into HTML, injects fonts and tokens, and assembles the single file. Accept: building a stub direction produces a file that opens offline.
- **T0.6 Component kit (M).** Direction-neutral behaviours only (table sort, tabs, drawers, bidi text, chat transcript, bar and line charts) as unstyled structures that each direction skins with its own tokens, never with shared classes. Accept: no two directions share a CSS class prefix or token name.
- **T0.7 Phone and desktop frames (S).** A phone frame (390x844) and a desktop frame (1280x800) that do not impose styling. Accept: both scale in the compare view.
- **T0.8 QA harness (M).** Scripts for: uniqueness (fonts, hex, tier names, logo outlines), WCAG contrast of every token pair, tap-target size on phone screens, Arabic rendering, offline load, file size, and a Chrome screenshot sweep. Accept: the harness runs on the stub and reports pass or fail per rule.
- **T0.9 Pilot decision (S).** Choose two pilot directions to prove the pipeline. Recommended: 04 Review Desk (closest to the product) and 09 Grey Process (most different), so the pilot covers a light dense UI and a restrained grey one.

### Phase 1: Pilot (L)
- **T1.1** Build all 14 pieces for the two pilot directions end to end.
- **T1.2** Run the harness; fix findings.
- **T1.3** Owner review at the screen level. Output: a short list of rules to change before scaling (spacing, copy length, phone fidelity, level of detail).
Exit criterion: the owner approves the pilot's look and the rules for the rest.

### Phase 2: Brand sheets for the remaining 14 (L)
- **T2.n Brand sheet per direction.** Logo suite as hand-built SVG (lockup, mark, one-colour, reversed, favicon, app icon); palette table with contrast; type specimen in Latin and Arabic; tier and status vocabulary with glyphs; 12 icons; voice samples. Accept: the direction passes the uniqueness check, every logo reads at 16px and in one colour, Arabic specimen renders.

### Phase 3: Desktop screens for the remaining 14 (L, parallelisable per direction)
- **T3.n D1 to D7 per direction**, using only that direction's tokens and structure, the shared dataset and the real copy. Accept: no placeholder content, messages zone and metrics zone present on D2 and D5, states shown on D7.

### Phase 4: Phone screens for the remaining 14 (M, parallelisable)
- **T4.n M1 to M6 per direction**, following the registry's phone behaviour. Accept: 44px targets, bottom navigation matches the real five items plus More (except 15 Wallboard, which gets a TV mode instead), messages thread and metrics glance present.

### Phase 5: Assembly and QA (L)
- **T5.1** Assemble `wasel-brand-book.html`: switcher, per-direction pages, compare view, print stylesheet.
- **T5.2** Embed fonts and verify offline in a browser with the network disabled.
- **T5.3** Run the full harness; fix; record the results in the file's footer.
- **T5.4** Screenshot review pass in Chrome for every direction at desktop and phone width.
- **T5.5** Write a one-page decision summary: the 16 directions with a final fit score per job (daily work, overview, bulk, AI health, phone).

### Phase 6: Decision and handover (S)
- **T6.1** Owner picks one direction or a combination by role.
- **T6.2** Write `DESIGN.md` for the chosen direction(s) and a refactor plan for `web/`. This is the end of this project and the start of implementation, which is separate work.

## 8. Order, dependencies and parallelism
Phase 0 blocks everything. Phase 1 blocks Phases 2 to 4. After Phase 1, Phases 2, 3 and 4 are independent per direction, so they can be done in any order or in parallel (for instance by one delegated worker per direction, if you want that). Phase 5 needs all selected directions finished.

## 9. Recommended scope options
- **A. All 16.** 224 pieces. Most complete, longest.
- **B. The 10 strongest by fit** (02, 03, 04, 06, 09, 11, 12, 13, 14, 16): 140 pieces. Leaves out 01, 05, 07, 08 (medium fits, narrow jobs) and 10, 15 (low fits). Recommended default.
- **C. Pilot only** (Phase 0 and 1): 28 pieces plus the pipeline. Fastest way to see real quality before committing.
Recommendation: C first, then B. Directions 15 Wallboard and 10 Scope can ship as a brand sheet and one screen each, since they are not full products.

## 10. Risks
- **Fonts.** Some registry fonts may be unavailable or lack Arabic or digits; handled in T0.4 by swapping through the registry.
- **File size.** 16 directions with embedded fonts and 224 pieces may exceed 12 MB; the fallback is one file per direction plus an index (T0.5).
- **Logo originality.** Hand-built SVG marks need a similarity check against well-known marks; do it in T0.8 and Phase 2.
- **Arabic and Tunisian text.** Not checked by a native reader; flag in the file and ask the owner or a reader to review.
- **Tier names.** Renaming `High / Medium / Low` must still convey refusal risk; T0.3 checks each vocabulary reads correctly.
- **Honesty.** Mockups are static and untested with sellers; label them so.

## 11. Decisions I need from you
1. Scope: A, B or C (default recommended: C then B).
2. One single file or one file per direction plus an index, if the size budget fails.
3. Whether to delegate Phases 2 to 4 to parallel workers, one per direction (faster; uses more resources and needs your go-ahead).

## 12. Decisions made (2026-10-07)
1. Scope: **all 16 directions** (so the low-fit ones, 10 Scope and 15 Wallboard, get a lighter treatment).
2. Packaging: **one standalone offline file per direction plus an index page** (`book/NN-name.html` and `book/index.html`).
3. Execution: done by one worker in order, no parallel workers.

## 13. Progress log
| Task | State | Notes |
|---|---|---|
| T0.1 Data pack | done | `dataset.json` (real orders, hero conversation, real drafts, reasons, history, activity, impact, quality, monitor) built by `_source/dataset_build.py` |
| T0.2 Content inventory | done | `content.json` (real titles, subtitles, labels, empty states, nav) |
| T0.3 Identity lock | done | `registry.json`; the checker reports no duplicate font, non-neutral hex or tier name. The owner has not yet reviewed individual identities |
| T0.4 Fonts | done | 48 families downloaded as woff2 (latin and arabic subsets) into `_fonts/`, none failed, about 2.5 MB in total |
| T0.5 Build skeleton | done | `_source/book/assemble.py` builds `book/NN-name.html` and `book/index.html`; fonts embedded as base64 |
| T0.6 Kit | done | `_source/book/kit.py` (data accessors, SVG helpers, font embedding, contrast, tint) |
| T0.7 Frames | done | phone 390x844 and desktop 1280x800 frames in `kit.py` |
| T0.8 QA harness | partly | `_source/book/qa.py` (static checks) and `qa_taptargets.js` (browser). Not yet built: similarity check of logos, Arabic rendering check, automated screenshot sweep (`shot.sh` exists and works) |
| T0.9 Pilot choice | done | Pilot A is 04 Review Desk, pilot B is 09 Grey Process |
| T1 Pilot A: 04 Review Desk | built, awaiting owner review | brand sheet, D1 to D7, M1 to M6 all built; static QA passes (16 checks); no phone control under 44px; headless screenshots reviewed |
| T1 Pilot B: 09 Grey Process | not started | owner asked for 01 Terminal Desk next |
| 01 Terminal Desk | built, awaiting owner review | brand sheet, D1 to D7, M1 to M6; static QA passes (16 checks); no phone control under 44px (38 controls); headless screenshots reviewed; fixes made for overlapping logo text, swatch label contrast, grid placement, clipped columns |
| Phases 2 to 6 | not started | |

## 14. How to rebuild and check
From the repo root:
- `python3 docs/design-explorations/_source/registry_build.py` (identity uniqueness)
- `python3 docs/design-explorations/_source/dataset_build.py` (dataset and content)
- `python3 docs/design-explorations/_source/book/assemble.py [direction-id ...]` (build one or all)
- `python3 docs/design-explorations/_source/book/qa.py [direction-id ...]` (static QA)
- `docs/design-explorations/_source/book/shot.sh <id> <only> <out.png> <w> <h>` where `only` is `brand`, `d1`..`d7`, `p1`..`p6` (headless Chrome screenshot of one piece)
- Open `docs/design-explorations/book/index.html` in a browser (everything is offline).

A new direction is one file, `_source/book/directions/dNN.py`, exposing `PREFIX`, `CSS`, `brand()`, `desktop()`, `phone()` and `notes()`; `directions/d04.py` is the reference implementation.
