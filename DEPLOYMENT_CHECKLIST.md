# Cloudflare Deployment Checklist

**Status:** ✅ Production-Ready as of commit f68c208

## Pre-Deployment (One Time)

- [ ] Cloudflare account created (free plan OK)
- [ ] Domain added to Cloudflare (nameservers pointed)
- [ ] Always-on host prepared (Linux VPS or PC, Python 3.11, Node 22, git, make, cloudflared)
- [ ] Cloudflare tunnel created in dashboard, token extracted to `.env` as `CLOUDFLARE_TUNNEL_TOKEN`

## Host Setup

```bash
git clone https://github.com/omarbounawarapy/hackathon wasel
cd wasel
make setup
make web
cp .env.example .env
# Edit .env:
#   APP_MODE= (empty for public mode)
#   GROQ_API_KEY=<capped public key>
#   ADMIN_TOKEN=<32 random chars>
#   CLOUDFLARE_TUNNEL_TOKEN=<token from dashboard>
#   HOST=127.0.0.1
#   PORT=8000
```

## Run

```bash
# Terminal 1: FastAPI app
make serve

# Terminal 2: Tunnel (when stable, use systemd service)
make tunnel
```

## Verify

```bash
make smoke URL=https://wasel.<your-domain>
# Expected: PASS + "public v1=87 v2=16"

# Incognito audit (judge safeguards):
# 1. /api/health → mode=public, wa_send=false, webhook=disabled
# 2. POST /webhook/whatsapp → 404/405 (not mounted)
# 3. Queue shows only samples (no PII)
# 4. "Try this order" works (hero v1 → v2)
# 5. Second incognito window isolated from first
# 6. /api/metrics/impact → simulated: true
```

## Test Results

- ✅ 347 tests pass, 1 xfailed (expected ML fairness trade-off)
- ✅ Hero loop: v1 HIGH 87 → v2 LOW 16
- ✅ Live LLM verified Sat 05:00: Groq 120b + Gemini fallback work
- ✅ Injection guard holds on all test cases
- ✅ Evidence check removes hallucinated quotes

## What's Running

- **Backend:** FastAPI on 127.0.0.1:8000 (only tunnel reaches it)
  - Extraction: 12-field LLM schema + validation + evidence check
  - Scoring: XGBoost monotone classifier (AUC 0.784) + deterministic rules
  - Storage: SQLite with WAL (var/app.db, seeded on boot in public mode)
  - Worker: 1-second tick loop, debounce, state machine
  
- **Frontend:** Streamlit dashboard at `/`, React SPA at `/dashboard`
  - Queue (sorted by risk)
  - Order detail (messages, timeline, actions)
  - Paste/CSV ingest
  - Simulate reply
  - Activity feed
  - Impact dashboard
  
- **Safety by Default (Public Mode)**
  - Webhook unmounted
  - WhatsApp sends forced off
  - Each visitor isolated (`X-Visitor-Id` sandbox)
  - Seeded orders read-only
  - LLM caps (80/day) → rules fallback
  - Public mode reseeds on boot (wipes real data)

## Updates

When a new version is ready on `main`:

```bash
make deploy
# Then restart:
sudo systemctl restart wasel  # or Ctrl-C + make serve
make smoke URL=https://wasel.<your-domain>
```

## WhatsApp Event Window (Optional)

Only during the competition:

1. `.env`: `APP_MODE=event`, add `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `WA_PHONE_NUMBER_ID`
2. `make serve` → restart
3. Meta dashboard: set callback to `https://wasel.<your-domain>/webhook/whatsapp`
4. Verify messages arrive in queue
5. After event: flip back to public mode, restart, run `make smoke`

## Support

- **Troubleshooting:** See `docs/deploy-cloudflare.md` §8
- **Rollback:** `git checkout <sha> && make setup web && make serve`
- **After judging:** Delete tunnel, revoke keys, rotate ADMIN_TOKEN

---

**Commit:** f68c208  
**Date:** 2026-09-27  
**Tests:** 347 passed, 1 xfailed  
**Status:** ✅ Ready to Deploy
