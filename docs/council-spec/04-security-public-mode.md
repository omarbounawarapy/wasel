# Security, public mode, runbook, repo hygiene, Responsible AI

> Council final spec — Skeptic lens (Round 3). Source of truth for its area. Where this file conflicts with a **Conductor ruling** in [README.md](README.md#conductor-rulings), the ruling wins. Unverified external facts are marked [VERIFY].


Times are Tunis (UTC+1, no DST). "Visitor" = a browser that has an `X-Visitor-Id`. "Seeded" = a row with `sandbox_id IS NULL`.

## 1. Threat / failure table for the agreed topology

Topology: one container on a free host [VERIFY host: sleep, disk, restart-on-env-change, auto-deploy]. FastAPI serves `/api/*`, `/webhook/whatsapp` (mounted only in event mode) and the static React bundle at `/`. SQLite lives at `var/app.db` and is recreated and seeded on boot. The committed seed extraction cache is JSON. LLM chain: Groq `gpt-oss-120b` → `gpt-oss-20b` → [Gemini, only if S-6 passes parity] → rules. `APP_MODE ∈ {public, event, dev}`.

"Caption" is the on-screen video text. "README" is the submission README. Nobody says anything on a stage.

| # | Failure | Detection | Automatic fallback | README / video caption says |
|---|---|---|---|---|
| 1 | Host asleep; the judge's first load is slow | UI shows "Waking up the demo…" when `/api/health` takes > 3s; `uptime_s` small | Seed on boot, so the first render needs no LLM call | README line 1: "Hosted demo: <url>. After idle, the first load can take ~N s [measure Sat 22:00]. Sample orders show recorded AI output; your own text runs live AI within a daily budget." |
| 2 | Host down during judging | Montassar opens the URL at 17:00 and daily at ~10:00 during judging [VERIFY judging window] | None automatic. `make demo` runs locally with no keys (rules path + committed cache). Optional: the static snapshot link (row 16) | "If the hosted link is down: `git clone … && make demo` runs the full UI offline. Live AI needs a free Groq key in `.env`." |
| 3 | A mode flip doesn't take effect (host didn't restart on env change) | 16:50 audit: `/api/health.mode` ≠ `public` | Manual restart or redeploy from the host console. If still wrong at 16:58, submit anyway and fix by 17:30 (the URL doesn't change) | — |
| 4 | Groq 429 / timeout / 5xx | Exception ≤ 8s; circuit breaker opens after 2 consecutive failures | 120b → 20b → [Gemini] → rules. Each hop is logged `llm.fallback`. The rescore has a 12s deadline across all providers | Badge on the score shows the path. README: "Fallback chain; the badge on every score says which path produced it." Caption, if a fallback shows in the video: "Primary model busy; this score came from <path>." |
| 5 | Public daily budget used up | `llm_usage` checked before every call | Skip the LLM; `path='rules'`; budget banner (§2.7). HTTP 200, not 429 | README repeats the banner text. Never silent. |
| 6 | Visitor rotates `X-Visitor-Id` to dodge the per-visitor cap | `llm_usage` global counters | Global cap and token guard (§2.5) bound the total | — (accepted residual) |
| 7 | Judge A's actions change what judge B sees | Test P2/P3 | Seeded rows are read-only (409). A's rows are visible only with A's id and purged after 2h | README: "Sample orders are read-only; 'Try this order' gives you your own copy." |
| 8 | Gemini rejects the schema (dialect mismatch), if S-6 ships | Parity test in CI (replay); `/api/health?deep=1` (admin) preflight at 08:30 | Skip to rules | README lists Gemini only if it passed the parity test. |
| 9 | A sync LLM call blocks the event loop | `/api/health.loop_lag_ms` > 1000 | Design fix: `asyncio.to_thread` / async client and a 12s deadline | — |
| 10 | `WA_APP_SECRET` empty or unset on the host | Startup log; `/api/health.webhook="disabled"` | Route not mounted (404). No skip flag exists | — |
| 11 | WhatsApp token expired or the test recipient deregistered [VERIFY sandbox rules] | Graph 401/190 on send; 08:30 check | Draft marked `send_failed`; order stays `awaiting_reply`; the story continues with `simulate-reply` | README: "WhatsApp runs on Meta's test number, which only pre-registered phones can message, so the hosted demo uses paste and simulated replies through the same pipeline." |
| 12 | Duplicate / out-of-order / status-only webhooks | UNIQUE conflict counter in `/api/health` | Ignored (W-5, W-6) | — |
| 13 | The video shows a cache hit as live | Badge reads `cached` | Clear the cache or vary the scripted text before recording | Caption, if a cached score is shown: "Cached from an identical earlier run of the same model." |
| 14 | Reply arrives after the no-reply timeout moved the order to `needs_review` | Test (R1 F-10) | Transition `needs_review` (cause = `no_reply_timeout`) + customer reply → rescore. Demo timeout 180s; **off** in public mode | — |
| 15 | Real WhatsApp rows survive into public mode | 16:50 audit: no teammate names or numbers; `/api/health.real_rows=0` (count of `channel='whatsapp'`) | 16:45 restart reseeds and wipes them. Fallback: `POST /api/admin/reset` | — |
| 16 | Snapshot page shows stale data as if live | Snapshot banner is always on in snapshot mode | Snapshot captured only in public mode after 16:45 (N-7) | Snapshot banner (§2.7). README: "Offline snapshot: <link>, recorded outputs, clearly marked." |
| 17 | Injected text lowers an order's risk | Lexicon hit → `injection_suspected`; E4 test | `needs_review`, no auto-transition to `ready_to_ship`; confirmation from that message is ignored (§5) | README Testing table row: "8 injection fixtures: tier never lower than the clean twin." |
| 18 | Visitor pastes abusive text | — | Public mode: no live rewrite; static templates only; all text rendered as React text nodes; the text is visible only in that visitor's sandbox | — |
| 19 | Disk or DB growth from visitor inserts | `/api/health.sandbox_orders` | Purge every 10 min (> 2h old). Per-visitor max 15 orders. Global sandbox max 500 → 429 `DEMO_BUSY` | — |
| 20 | Secret found in history at the visibility flip | §6.2 scan | **Rotate first**, then publish a fresh squashed repo if history rewrite isn't possible in time | — |
| 21 | PII or a secret in the video / screenshots | Second-person review (§6.4) | Re-record or crop the segment | — |
| 22 | Frontend `src/lib/` missing on the host build (N-1) | CI clean-checkout build fails | `.gitignore` re-include | — |
| 23 | "Try this order" makes a live call after a prompt bump (N-3) | CI test under `FailingClient` | Copy seeded assessments; `path='cached'` | — |
| 24 | Post-deadline pushes change the judged prototype (N-5) | Host deploy log | Host pinned to `submission-v1` | — |
| 25 | Judge hits the read-only 409 on a seeded order | — | UI turns the 409 into a toast plus a "Try this order" button (§2.7) | — |

**Cascade (Groq down or capped while a judge is on the page):**
```
Groq down / capped
  ├── Extraction → 20b → [Gemini] → rules         badge says which
  ├── Rewrite/judge → static template, no judge   (public mode: always static for visitor orders)
  ├── Seeded queue & detail                        unaffected (no LLM on read)
  ├── "Try this order" + scripted reply            unaffected (zero-LLM by contract, N-3)
  └── simulate-reply with ack/decline/pin          unaffected (cascade §6.8)
```

## 2. Public-mode rules

### 2.1 Mode semantics (settings resolved once at startup; `/api/health` reports the resolved values)

| Setting | `public` (default) | `event` | `dev` |
|---|---|---|---|
| WhatsApp send | **forced off**, env ignored | `WA_SEND_ENABLED` (default true) | env |
| Webhook routes (GET + POST) | **not mounted** | mounted only if `WEBHOOK_ENABLED=true` and `WA_APP_SECRET` and `WA_VERIFY_TOKEN` are non-empty | same rule as event |
| Visitor sandbox filter | on | off | off |
| Seeded rows | read-only (409) | writable | writable |
| `NO_REPLY_TIMEOUT` | off | 180s | env |
| `display_name` | `Client #<last 3 of ULID>` | real (only teammates) | real |
| `raw_payload` stored | never (`DEBUG_RAW=true` is refused at startup with a log line) | only if `DEBUG_RAW=true` | env |
| Live rewrite | off (`PUBLIC_REWRITE_LIVE=false`) | if S-3 shipped | env |
| `LIVE_LLM_DAILY_CAP` default | 80 | 300 | 0 = none unless set |
| Groq key on host | `KEY_PUBLIC` (teammate org A) | `KEY_EVENT` (teammate org B) | personal dev key |

Unknown `APP_MODE` → `public`, plus a startup warning. There is no code path where `public` sends a WhatsApp message: the send client is not constructed in public mode.

### 2.2 Visitor identity

- The frontend creates `crypto.randomUUID()` once, keeps it in `localStorage["cod_visitor_id"]`, and sends it as `X-Visitor-Id` on every `/api/*` request. The read and write are wrapped in try/catch. If storage is blocked, the id lives in memory for that tab only.
- The server accepts only `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`. Anything else counts as no visitor.
- No visitor → reads return seeded rows only. Writes → 400 `VISITOR_ID_REQUIRED`.
- The id is not signed and is not identity. Events log it as `actor=visitor:<first 8 chars>`.

### 2.3 Sandbox semantics

- Schema: `sandbox_id TEXT NULL` on `customers`, `conversations`, `orders`, plus `INDEX orders(sandbox_id)`. Messages, assessments, drafts and events are reached through the order. The customer lookup key includes `sandbox_id`, so a visitor's "refused" never touches a seeded customer's `refusals_total`.
- Reads: `GET /api/orders`, `GET /api/orders/{id}` and `GET /api/events` return `sandbox_id IS NULL OR sandbox_id = :vid`. Global events with no order (`llm.fallback`, `budget.exhausted`) are shown to everyone and carry no message text.
- A mutation on a seeded row (actions, rescore, simulate-reply, draft send) → **409 `SEEDED_READONLY`**.
- A mutation on another visitor's row → **404** (existence isn't revealed).
- `POST /api/sandbox/try {fixture_id}` → 201 `{order_id}`. `fixture_id` must be in the seeded allowlist. The fixture replays through `seed_conversation(fixture, sandbox_id=vid)`. **Zero LLM calls:** on a cache miss it copies the seeded assessment rows with `path='cached'` (N-3).
- The scripted "Customer replies with street + building" button is also a cache hit, badge `cached (real LLM output from <date>)`.
- Drafts show "Sent (simulated)", and `messages.origin='simulated'` shows a chip.

### 2.4 Purge and volume limits

- The worker loop runs a purge every 10 min. It deletes sandbox orders with `created_at < now − 2h`, along with their messages, assessments, drafts, events and extraction runs. It then deletes sandbox conversations and customers that have no orders left.
- Per visitor: 15 sandbox orders max (oldest pruned on insert); `simulate-reply` 5 per conversation (then 429 `REPLY_LIMIT`).
- Global: 500 sandbox orders → `POST ingest` / `try` returns 429 `DEMO_BUSY` ("Demo busy, try again in a minute or open a sample order"). Worker queue > 20 → same 429.
- Input: request body ≤ 64 KB (413); paste ≤ 2,000 chars; simulate-reply ≤ 600 chars (413 with message); CSV ≤ 10 rows in public, 200 in event.

### 2.5 LLM caps (exact; counters in SQLite `llm_usage(day_utc, provider, model, calls, tokens_in, tokens_out)`, so a restart doesn't reset them)

"LLM action" = an `ingest`, `simulate-reply` or `rescore` that is **not** served by `cascade_cache`, `cascade_ack` or a scripted/`try` path.

| Limit | public | event | Over the limit |
|---|---|---|---|
| Per visitor | 6 LLM actions / 10 min; 20 / day | — | `path='rules'` + visitor banner, HTTP 200 |
| Per IP (only if the host's client-IP header is verified [VERIFY]; else not built) | 60 LLM actions / day | — | same |
| `LIVE_LLM_DAILY_CAP` (provider calls, all providers, fallback hops included) | **80** | **300** | `path='rules'` + budget banner, HTTP 200 |
| Token guard per Groq model per UTC day | **120,000** (60% of the 200K TPD in SD §6.1) | **180,000** | next provider → rules |
| Gemini calls per day, only if S-6 shipped | ≤ 60% of the free-tier RPD for the chosen model [VERIFY RPD]; placeholder 100 | same | rules |
| Live rewrite + judge per day | **0** (static templates) | 30 | static template, no judge |
| Manual rescore | never a new LLM call in public (cache/cascade only); min interval 30s | min interval 30s | 429 `TOO_SOON` |
| In-flight per provider | 1 | 1 | queued |

Why 80 and not 300 (changed from my R2 proposal): 120K tokens ÷ ≈2.7K per uncached call ≈ 44 calls per model. Public traffic is sparse, and the prompt cache expires after 2h unused (SD §6.7), so most calls are uncached. Across 120b + 20b that's ≈ 88, so a call cap of 80 is the first limit to trip [estimate; re-measure after the G3b prompt freeze]. Accounting uses the actual `usage` returned by each call. Cached prefix tokens count as reported [VERIFY the field name]. Reasoning tokens count toward usage [VERIFY].

Evaluation order per request (first failing rule wins; nothing is silent): size (413) → visitor id for writes (400) → scripted/`try`/cascade path (always allowed, no budget) → per-visitor → per-IP → global cap / token guard / circuit breaker → queue full (429).

### 2.6 Other public-mode rules

- Security headers on every response: `Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'` [VERIFY the Vite build needs no inline script], `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`.
- No CORS middleware in `public`/`event` (same origin). `dev` allows only `http://localhost:5173`.
- `/api/health` (public) returns `mode`, `wa_send`, `webhook`, `wa_token_present` (bool), `real_rows`, `live_calls_today`, `cap`, `tokens_today{model}`, `fallback_active`, `sandbox_orders`, `loop_lag_ms`, `git_sha`, `uptime_s`. No LLM call, no secrets. `?deep=1` requires `X-Admin-Token` (N-4).
- Admin routes (`/api/admin/reset`, `/api/admin/flags`) are mounted only if `ADMIN_TOKEN` is ≥ 24 chars. Checked with `hmac.compare_digest`. Wrong or missing token → 403.
- Response models: explicit Pydantic schemas. `phone_e164` and `raw_payload` never appear in any response (test P6).

### 2.7 Banner and message copy (exact)

- **Public banner (always on in public mode):** "Public demo. Sample orders are synthetic and read-only — use **Try this order** to get your own copy. What you add is visible only in this browser and deleted after 2 hours. This demo never sends WhatsApp messages."
- **Budget banner:** "Today's live-AI budget for this public demo is used up. New text is scored by the rules-only fallback (marked **rules**). Sample orders still show real AI output recorded on {date}. The budget resets at 01:00 Tunis time."
- **Per-visitor banner:** "You've used this browser's live-AI allowance (6 per 10 minutes, 20 per day). New text uses the rules-only fallback until {time}."
- **Fallback banner** (`fallback_active`): "The main AI model is unavailable right now. Scores are coming from {path}; each score shows which path produced it."
- **409 toast:** "Sample orders are read-only so every visitor starts from the same point. **Try this order** to work on your own copy."
- **Draft chip:** "Sent (simulated) — the public demo never sends WhatsApp messages."
- **Snapshot banner:** "Offline snapshot: the live backend is unreachable, so this page shows outputs recorded from the real system on {date}. Nothing on this page is live."
- **Injection chip:** "Possible instruction text in the message — check before acting."

## 3. Mode-switch runbook and kill switches

### 3.1 Runbook

| When (Tunis) | Action | Check (pass = continue) | Who |
|---|---|---|---|
| Sat by 14:00 | Hello-world container on the host, no `APP_MODE` set, no WA secrets | `/api/health.mode=public`, `wa_token_present=false` | Montassar |
| Sat by 20:00 | Public-mode middleware, sandbox filter, purge and caps merged; tests P1–P6 green | `make check` | Montassar (middleware, purge), Jesser (filter, `try`), Omar (cap) |
| Sat 18:00–18:30 (only if G5 WhatsApp is green) | **Rehearsal flip:** `APP_MODE=event` + WA secrets → Meta callback → hosted `/webhook/whatsapp` → one message from a registered phone → flip back to `public`, delete the WA secrets | Order row appears; W1–W6 green before pointing Meta at the host | Jesser + Montassar |
| Sat 21:00 | Safety take recorded against the **hosted public** URL (Try this order + paste) | Badges visible; captions per §1 | Fedi, Montassar |
| Sat 22:00 | Deploy `main` in public mode; incognito check #1; secret scan #1 (repo still private) | §3.3 audit items 1–6 pass; §6.2 scan prints nothing | Montassar, Omar |
| **Sun 08:00** | Set `APP_MODE=event`, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `GROQ_API_KEY=KEY_EVENT`, `LIVE_LLM_DAILY_CAP=300` → restart (reseeds) [VERIFY restart-on-env-change] | `/api/health.mode=event, wa_send=true, webhook=enabled` | Montassar |
| Sun 08:30 | Meta console: re-verify the callback; token valid; one test message | Order row appears. If not fixed by 09:00: `WEBHOOK_ENABLED=false`, paste + simulate-reply path, caption per §1 row 11 | Jesser; Omar runs `GET /models` + warm-up |
| Sun 09:00–15:30 | Build. Hosted URL stays unlisted (no slides, no shared screens) | — | all |
| 15:30 | Feature freeze; tag `rc` | CI green | Omar |
| 15:45 | `POST /api/admin/reset`; clear the extraction cache or vary the scripted text; phone on DND | Badges read `LLM · gpt-oss-120b` on the live beats | Jesser |
| 16:00–16:30 | Two takes against the hosted instance | §6.4 checklist | Fedi records, Omar reviews |
| **16:45** | Set `APP_MODE=public`, `GROQ_API_KEY=KEY_PUBLIC`, `LIVE_LLM_DAILY_CAP=80`; **delete** `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` from the host → restart (reseed wipes real rows). Meta console: remove the callback / unsubscribe the webhook fields [VERIFY steps]. Pin the host to tag `submission-v1` or turn off auto-deploy (N-5) | `/api/health.mode=public` | Montassar |
| 16:45 (parallel) | Secret scan #2 (§6.2) → fix the playbook wording → flip the repo to public | Scan prints nothing | Omar |
| 16:50 | Incognito audit (§3.3). Then capture the snapshot, if Advocate's snapshot mode shipped (N-7) | All items pass | Montassar + Fedi |
| 17:00 | Submit | Every link opens in incognito | Fedi |
| Daily during judging | Open the URL; run "Try this order" | Health green | Montassar |
| After judging closes [VERIFY date] | Revoke `WA_TOKEN` / remove the test number; delete `KEY_PUBLIC`; rotate `ADMIN_TOKEN`; optional host teardown | — | Montassar, Jesser |

### 3.2 Kill switches

Env changes are durable but restart the container [VERIFY per host], and a restart reseeds. **Never change env during a take.** `POST /api/admin/flags` (Should, Montassar, ~20 min) can only *tighten*: it disables LLM, sends or the webhook instantly, with no restart. It's lost on restart, and the env baseline comes back.

| Switch | Values | Fail-safe default | Effect |
|---|---|---|---|
| `APP_MODE` | public / event / dev | `public` | §2.1 |
| `LLM_LIVE_ENABLED` | true / false | true | false → every score on the rules path + fallback banner |
| `LIVE_LLM_DAILY_CAP` | integer ≥ 0 | mode default (80 / 300) | 0 = no live calls |
| `LLM_TOKENS_PER_MODEL_DAY` | integer | 120000 public / 180000 event | per-model guard |
| `WA_SEND_ENABLED` | true / false | false in public (forced); true in event | false → drafts `send_disabled` |
| `WEBHOOK_ENABLED` | true / false | false | false → webhook routes not mounted |
| `PUBLIC_REWRITE_LIVE` | true / false | false | static templates for visitor orders |
| `SEED_ON_BOOT` | true / false | true | reseed on start |
| `ADMIN_TOKEN` | ≥ 24 chars | empty → admin routes not mounted | — |
| `DEBUG_RAW` | true / false | false; refused in public | — |

Deployment rollback: the host redeploys tag `submission-v1`.

### 3.3 16:50 incognito audit (Montassar reads it out, Fedi ticks)

1. `/api/health` shows `mode=public`, `wa_send=false`, `webhook=disabled`, `wa_token_present=false`, `real_rows=0`.
2. `POST /webhook/whatsapp` → 404.
3. Queue shows only sample orders. No teammate names, phone numbers, or `+216`.
4. "Try this order" on the hero → HIGH with highlights → scripted reply → LOW with reason diff. Badges read `cached (real LLM output from …)`.
5. A mutation on a sample order → toast, not a crash.
6. Paste one new order → it scores (live, or rules with the banner).
7. The repo link opens in incognito. No `.db`, `.env` or `.claude` in the file list.
8. The video link opens and plays.

## 4. Webhook security — acceptance criteria (Jesser; tests W1–W8, only if S-1 passes G5)

- **W-1 Mount rule.** Both webhook routes are registered only when `APP_MODE ∈ {event, dev}`, `WEBHOOK_ENABLED=true`, `len(WA_APP_SECRET) ≥ 16` and `len(WA_VERIFY_TOKEN) ≥ 24`. Otherwise they're not registered (404), and `/api/health.webhook="disabled"`. There is no skip-signature flag in any mode. *Test:* empty secret → 404; public mode with every WA var set → 404.
- **W-2 Verify (GET).** Respond `PlainTextResponse(hub.challenge, 200)` only if `hub.mode == "subscribe"`, `hmac.compare_digest(hub.verify_token, WA_VERIFY_TOKEN)`, and the challenge is ≤ 128 chars. Otherwise 403 with an empty body. *Test:* `content-type` starts with `text/plain`; wrong token → 403.
- **W-3 Size.** Read at most 1 MiB. A larger `Content-Length` or body → 413 before any hashing.
- **W-4 Signature (POST).** `raw = await request.body()` **before** any JSON parsing. Header `X-Hub-Signature-256` must match `^sha256=[0-9a-f]{64}$`. `expected = hmac.new(WA_APP_SECRET.encode(), raw, hashlib.sha256).hexdigest()`, compared with `hmac.compare_digest`. Missing, malformed or mismatched → **401**, body `{"error":"invalid_signature"}`, event `webhook.rejected{reason}` with no body logged. *Tests:* valid → 200 + one message; one flipped byte in the body → 401; re-serialized JSON (same content, different whitespace) → 401; missing header → 401.
- **W-5 Status codes after a valid signature.** Always **200**, returned before processing (background task). That holds for unparseable JSON (`webhook.malformed`), statuses-only payloads, unsupported types, unknown `phone_number_id` and duplicates. Processing errors after the 200 are logged as `webhook.process_error` and never become a 5xx. A payload whose `metadata.phone_number_id ≠ WA_PHONE_NUMBER_ID` is ignored and logged.
- **W-6 Dedupe.** `UNIQUE(channel, channel_message_id)` + `INSERT OR IGNORE`. A duplicate creates no message and doesn't touch `pending_rescore_at`. `statuses[]` only update `delivery_status` of a known outbound wamid; unknown wamids are ignored. Batches are sorted by `timestamp`. *Test:* the same signed payload twice → 1 message, 1 rescore.
- **W-7 Storage.** `raw_payload` is NULL unless `DEBUG_RAW=true` (never in public). `phone_e164` is stored but never returned by any API (P6). The seed exporter refuses rows with `channel='whatsapp'`.
- **W-8 Outbound.** The send client exists only if `WA_SEND_ENABLED` resolves true (never in public). Max 1 send per order per 5 min; loop guard `auto_messages_sent ≤ 2`; 24h window check (SD §8.5). *Test (P4):* public mode + `WA_SEND_ENABLED=true` → a mocked send client is never called.

## 5. Prompt-injection defences end to end — acceptance criteria (Omar unless noted)

- **I-1 `defuse()` is length-preserving and runs on every text that enters any prompt** (customer and seller-typed). It's a 1:1 code-point map applied to the **original** text, so evidence spans still map back through `normalize_with_map`:
  `<`/`＜` → `‹` (U+2039), `>`/`＞` → `›` (U+203A), `[`/`［` → `⟦` (U+27E6), `]`/`］` → `⟧` (U+27E7), `{`/`｛` → `⦃` (U+2983), `}`/`｝` → `⦄` (U+2984), `\r`, `\n`, U+2028, U+2029 → space. (Checked with Python `unicodedata`: all six targets are unchanged by NFKC and are one UTF-16 unit each, so normalization can't undo them and JS offsets don't shift. The fullwidth sources do NFKC-map to ASCII, which is why they're in the map.) **Unicode format characters (category Cf)** → space in the same pass: U+200B–U+200F (zero-width, LRM/RLM), U+202A–U+202E (bidi embeddings/overrides), U+2060–U+2064, U+2066–U+2069 (bidi isolates), U+FEFF. Each is one code point and one UTF-16 unit, so the length is preserved. This is the **only** defuse definition; 02 §4's code mirrors it.
  *Property test:* for random strings (emoji, Arabic, fullwidth brackets, `[SELLER]`, `</customer_messages>`, zero-width and bidi characters), `len(defuse(s)) == len(s)` and no `< > [ ] { }`, fullwidth variant, newline, U+2028/U+2029 or Cf character remains.
- **I-2 Window format.** One line per message: `[CUSTOMER] …`, `[CUSTOMER:voice] …`, `[SELLER] …`, inside `<customer_messages>…</customer_messages>`. After I-1, customer text can't open a new line, close the block, or produce a role tag.
- **I-3 `[SELLER]` = canonical text only.** Outbound rows carry `template_id` and `canonical_text` (the static template rendered with slot values in the extracted language). `author='ai'` → `canonical_text`; if it's NULL the row is skipped. `rendered_text` / rewrite output never enters extraction. `author='seller'` → dashboard-typed text, defused. *Test:* a rewrite containing "IGNORE ALL" never appears in the prompt captured by `ReplayClient`.
- **I-4 Injection lexicon** (deterministic, before the LLM; lives in `scoring.yaml: lexicons.injection`; Fedi supplies the Arabic-script and Arabizi lines). **This is the only lexicon definition; 02 §2 points here.** Scope: every `[CUSTOMER]` and `[CUSTOMER:voice]` line, never `[SELLER]`. Views: the phrase patterns below (override, schema forgery, score directives) match `normalize(text_orig)` with all Cf characters **removed** (so `ig\u200bnore` can't split a word); the role-forgery patterns match the defused `text_llm`. **Phrase-level only** (N-6):
  - instruction override: `ignore (all|the|previous|les|toutes les|tes) (instructions?|consignes|règles|rules)`, `(oublie|forget) (tes|your) (instructions|consignes)`, `تجاهل (التعليمات|الأوامر)`, `you are now`, `tu es maintenant`, `system prompt`;
  - role forgery: `(^|\s)(system|assistant|seller|vendeur|developer)\s*:`, and any `⟦(SELLER|CUSTOMER)` left after defuse;
  - schema forgery: `address_level|confirmation\s*[:=]|injection_suspected|red_flags|risk_score`, `"exact"`, `⦃\s*"`;
  - score directives: `(mark|classe?|set).{0,20}(low risk|faible risque|safe|score\s*0)`.

  A hit sets `injection_suspected=true` (code-owned; OR-ed with the model's own field if the schema has one) → `confidence=low` → `needs_review` plus the injection chip. *False-positive test:* 10 clean fixtures containing "c'est exact", "j'ignore le numéro", "système", "confirmer", "risque" → no hit.
- **I-5 What an injected message can't do.** When `injection_suspected` is true: the `confirmation` from that message is ignored (no ×0.6), there's no transition to `ready_to_ship` without a seller click, there's no auto-send, and **the order can't drop out of scoring**: 02 §5 step 9 forces `is_order=true`, and 01 §5.2 rule 0 always writes an assessment row with `needs_review`, so the chip persists and the order stays in the default queue. *E4 test:* for each of the 8 fixtures, `tier(injected) ≥ tier(clean twin)` and `status == needs_review`.
- **I-6 Evidence and numbers stay code-owned.** Flags need verbatim quotes found in `[CUSTOMER]` text only. `address_level=exact` needs a digit per the shared Arabizi-digit helper. `resolve_flags()` only removes flags. The LLM never outputs the score or the reason. Accepted residual: a customer can lie ("imm 4") about their own order.
- **I-7 Judge input (only if S-3 ships).** The input is exactly `{product, price_tnd, first_name, template_id, canonical_text, draft_text, language, tone}`, with no customer text and no conversation. Code approves only if every boolean check is true. Judge error, timeout or invalid JSON → reject → static template (fail closed). If the judge and rewriter share a model family, the draft card shows `same_family=true`. *Test:* no ≥ 8-char substring of any customer message appears in the captured judge prompt.
- **I-8 Rewrite (only if S-3 ships).** Before the prefilter: Arabic-Indic digits `[٠-٩۰-۹]` → ASCII; strip whitespace between digits; URL regex `\b[\w-]+\.(me|ly|co|com|tn|link|io)\b/?`; forbid `@\w{3,}`; profanity lexicon (ships with S-3). `tone=negative` → no rewrite. Public mode: no live rewrite for visitor orders (§2.5).
- **I-9 Rendering.** Server-built `segments` (Advocate); the server drops bidi controls (U+202A–U+202E, U+2066–U+2069) from segment text, so customer text can't visually reorder the dashboard (ZWJ/ZWNJ are kept for emoji and script shaping). React text nodes only. ESLint `react/no-danger: error`. Quotes inside `reason` wrapped in FSI/PDI. The Streamlit fallback escapes each segment with `html.escape` and never passes customer-derived text to `st.markdown` unescaped. CSP per §2.6.
- **I-10 Fixtures.** `tests/fixtures/injection.yaml` (Fedi) has 8 cases: 4 classes (override, `</customer_messages>` breakout, `[SELLER]` forgery, JSON/schema forgery) × 2 scripts (Latin/Arabizi, Arabic script), run in CI under replay. The live eval runs the 4 base variants once, and the results go to `reports/`.

## 6. Repo hygiene and pre-submission security checklist

### 6.1 `.gitignore` — append below the stock template, before the first code commit (Omar)

Tested in a scratch repo. It commits `app/`, `risk_core/`, `schemas/`, `models/xgb.json`, `scoring.yaml`, `seed/demo_seed.json`, `seed/extraction_cache.json`, `reports/*.json`, `tests/fixtures/`, `web|frontend/src/**` (including `src/lib/`), lockfiles and `.env.example`. It ignores the DB, `.env*`, `node_modules`, build output, media and `.claude/`.

```gitignore
# ===== COD Risk additions — keep below the stock Python template =====
# The stock template ignores EVERY directory named lib/ (and dist/, build/).
# Re-include frontend source dirs (Vite/shadcn put code in src/lib/).
!web/src/lib/
!frontend/src/lib/

# App state and personal data (SQLite lives in var/app.db)
var/
*.db
*.db-journal
*.db-wal
*.db-shm
*.sqlite
*.sqlite3
app.db*
seed/raw/
data/raw/
reports/raw/
exports/

# Media: voice notes, screen recordings, raw screenshots
*.ogg
*.opus
*.m4a
*.mp4
*.mov
*.webm
*.mkv
recordings/
screenshots/raw/

# Env and secrets (.env.example is the only committed env file)
.env
.env.*
!.env.example
*.pem
*.key
secrets/

# Frontend build output and deps
node_modules/
.next/
out/
web/dist/
frontend/out/
.vite/
.vercel/
*.tsbuildinfo

# Local tooling (council transcripts reference personal files)
.claude/
.DS_Store
.idea/
.vscode/
```

Also: commit `.env.example` with names only. No secret in any `VITE_*` / `NEXT_PUBLIC_*` variable; CI fails on `(VITE|NEXT_PUBLIC)_.*(KEY|TOKEN|SECRET)`. The committed extraction cache is JSON (`seed/extraction_cache.json`), never a `.db`, and the exporter refuses `channel='whatsapp'` rows. If the team chooses the "commit the build output on a `deploy` branch" option, that branch uses `git add -f web/dist`, and it never gets merged to `main`.

### 6.2 Secret and PII scan (Omar; Sat 22:00 and Sun 16:45, before the visibility flip)

- [ ] `gitleaks detect --log-opts="--all"` if installed [VERIFY]. Otherwise this must print nothing (tested on the current repo: clean):
  ```
  git log --all -p --no-color | grep -nE 'gsk_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|EAA[A-Za-z0-9]{30,}|sk-[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|-----BEGIN [A-Z ]*PRIVATE KEY|(WA_TOKEN|WA_APP_SECRET|WA_VERIFY_TOKEN|GROQ_API_KEY|GEMINI_API_KEY|KEY_PUBLIC|KEY_EVENT|ADMIN_TOKEN)=[^[:space:]]+'
  ```
- [ ] `git log --all -p --no-color | grep -nE '\+216[ -]?[0-9]|\b216[0-9]{8}\b'` → nothing. Also `git grep -nE '\b[2-9][0-9]{7}\b' -- seed/ tests/`, reviewed by hand (8-digit Tunisian numbers; expect false positives).
- [ ] `git ls-files | grep -E '\.db|\.sqlite|\.env($|\.)|node_modules|\.claude/|\.(ogg|mp4|mov)$' | grep -v '^\.env\.example$'` → nothing.
- [ ] `git ls-files web/src/lib frontend/src/lib` lists the expected files (N-1).
- [ ] GitHub Actions logs contain no printed env (CI is keyless). No issue or PR comment contains a key.

### 6.3 Visibility and rotation

- [ ] Before the flip, fix `hackathon_playbook.md` L35/L44 to "synthetic data only; personal data (name, phone, address) minimized; no special-category data", and add a "superseded by PRD/SYSTEM_DESIGN — do not quote" banner to `handoff.md`.
- [ ] Flip the repo to public at ~16:47 only after §6.2 passes. Keep it private until then. [VERIFY whether the form accepts private + invite; public is still preferred.]
- [ ] Any key that ever appeared in a commit, a chat screenshot, the video or a slide: **revoke and reissue first**, then update the host env. GitHub can keep unreferenced commits reachable by SHA, so history rewrite alone is not enough. If there's no time to rewrite, publish a fresh squashed repo and link that one.
- [ ] `KEY_EVENT`: revoke after 17:00. `KEY_PUBLIC`: keep until judging closes (it's capped), then delete. `WA_TOKEN`: deleted from the host at 16:45; revoke it and remove the test number after judging. `ADMIN_TOKEN`: rotate if it was ever typed on a recorded screen.
- [ ] Keys are shared one-to-one in a direct message and deleted afterwards. Never in a group chat.

### 6.4 Video / slides / README screenshots (Fedi records, Omar reviews before upload)

- [ ] Phone: DND on, notifications hidden, status bar cropped. WhatsApp profile name "Client Test". The header number is cropped or blurred.
- [ ] Nothing on screen from the Meta console, host dashboard, tunnel dashboard, a terminal showing env, or `/api/health?deep=1`.
- [ ] Browser: clean profile (no bookmarks bar, no autofill), hosted URL, not `localhost`.
- [ ] Every fallback shown carries its badge and a caption (§1). The ROI figure shows "simulated". Metrics are scoped ("X/N hand-labeled synthetic windows, one labeler").
- [ ] Screenshots in the README are taken in public mode after 16:45, or from the Saturday public deploy.

### 6.5 Security tests (count toward Testing; owners write their own)

| id | Test | Owner | Due |
|---|---|---|---|
| P1 | Unset or unknown `APP_MODE` → public behaviour | Montassar | Sat 20:00 |
| P2 | Public mutation on a seeded order → 409 | Jesser | Sat 20:00 |
| P3 | Visitor A can't see or mutate B's orders (404) | Jesser | Sat 20:00 |
| P4 | Public + `WA_SEND_ENABLED=true` → send client never called | Montassar | Sat 20:00 |
| P5 | At cap: ingest → 200, `path='rules'`, zero LLM calls (mocked client); `cap=0` → zero calls | Omar | Sat 20:00 |
| P6 | No `phone_e164` / `raw_payload` keys in any response model | Jesser | Sat 20:00 |
| P7 | `try` for every fixture under `FailingClient` succeeds (N-3) | Jesser | Sat 22:00 |
| P8 | Purge deletes a > 2h sandbox order and its children | Montassar | Sun |
| E4 / I-1 / I-3 / I-4 FP | Injection fixtures, defuse property, `[SELLER]` canonical, lexicon false positives | Omar | Sat 22:00 (E4 is in the 16-set) |
| W1–W8 | §4 | Jesser | before Meta points at the host |
| X1 | Markup in customer text / `display_name` renders as text | Montassar | Sun |

## 7. Responsible-AI statement (submission text)

Placeholders in `{}` are filled from `reports/` on Sunday. Drop the bracketed Gemini sentence if S-6 didn't ship, and the judge sentence if S-3 didn't ship.

**Long version (~330 words):**

> **Data.** A COD order holds personal data: the customer's name, phone number and delivery address. We treat it as personal data and handle no special-category data. Everything in our repository and on the public demo is synthetic, generated from templates ({n_rows} rows). The only real messages were test messages that team members sent from their own phones, with their consent, to Meta's WhatsApp test number on event day. Those rows were deleted when the demo was reset at 16:45 and were never committed.
>
> **What the AI sees.** The language model (Groq, `openai/gpt-oss-120b`, falling back to `gpt-oss-20b`[; then Google Gemini]) receives message text only. Phone-number-like strings are masked first. No phone numbers, customer IDs or order history are sent. [VERIFY and cite each provider's data-retention terms.]
>
> **What the AI decides.** The model extracts facts and must quote the customer's own words for each warning sign. Warnings it can't quote are dropped. The risk score comes from a small classifier plus visible rules, not from the language model. Every score shows its reasons, its history, and which path produced it (live model, fallback model, cache, or rules).
>
> **Human control.** No message is sent without a seller's click. [A second model checks every drafted message; if the check fails, a fixed pre-written template is used.] Text that looks like instructions to the AI sends the order to human review. In our {8} test cases it never lowered the risk tier.
>
> **Fairness.** Delivery zone is a risk feature, so rural customers score higher by design. We limit the harm: high risk triggers a confirmation question, not a refusal to serve. Prepayment is suggested only for high-value, high-risk orders. The zone's contribution is shown in every reason so the seller can override it. We have not measured outcomes on real deliveries, so we don't claim the model is fair, only that the zone effect is visible and bounded.
>
> **Limits.** The classifier is trained on synthetic, rule-derived labels, so it reproduces our risk rubric rather than real refusal behaviour. Extraction was measured on {X}/{N} hand-labeled windows by {one} labeler. The reply adjustments are starting assumptions, to be replaced by real delivered/refused outcomes.

**Short version (≤ 600 chars, if the form limits length) [VERIFY field limit]:**

> Orders contain personal data (name, phone, address). Our repo and public demo use synthetic data only; real test messages from team phones were deleted after the event. The LLM gets message text only, with phone numbers masked. It extracts quoted facts; the score comes from a classifier and visible rules. A seller approves every message. Delivery zone raises rural scores, so high risk triggers a confirmation question, never a refusal, and the zone's effect is shown in every reason. Limits: synthetic labels, {X}/{N} hand-labeled eval windows.

---

## Unresolved (for the conductor)

1. **Host choice and its behaviour** (restart on env change, sleep, auto-deploy pinning) are still [VERIFY]. The whole runbook assumes an env change restarts and reseeds. Montassar must confirm by Sat 14:00, or the 08:00 and 16:45 flips need a manual redeploy step.
2. **Caps are estimates** until the G3b prompt freeze gives a measured tokens-per-call. Re-derive 80 / 120K then.
3. **Snapshot mode** (Advocate) only helps if it's hosted somewhere other than the container. Decide whether it ships at all. If it does, N-7 applies.
4. **The headline eval metric** (Oracle vs Strategist) feeds the `{X}/{N}` in §7. That's not mine to settle, but the RAI text must use whichever number ships, with N and the labeler count.
