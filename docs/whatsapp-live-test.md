# Live WhatsApp test: the webhook on the internet, from a laptop

STATUS O-9 / G5. The WhatsApp path in this app is real end to end — signed Cloud API webhook,
dedupe, debounce, live-LLM extraction and scoring, Cloud API send. The only thing localhost lacks
is a URL Meta can deliver to. `scripts/wa_webhook_up.sh` (or `make wa-up`) puts one up for as
long as the script runs: a cloudflared quick tunnel plus Graph API registration of the callback
and the `messages` field. No deploy, no Cloudflare account, idempotent on re-run.

## Prerequisites

- `cloudflared` (single static binary, no account needed for quick tunnels):
  ```bash
  mkdir -p ~/.local/bin && curl -sL -o ~/.local/bin/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    && chmod +x ~/.local/bin/cloudflared
  ```
  (macOS: `brew install cloudflared`; or point `CLOUDFLARED=…` at any binary.)
- `.env` at the repo root with the WhatsApp keys (values from whoever holds the Meta app —
  never commit them):
  ```
  APP_MODE=dev            # public mode never mounts the webhook (04 W-1)
  WEBHOOK_ENABLED=true
  WA_TOKEN=<system-user token>
  WA_APP_SECRET=<app secret, >=16 chars>
  WA_VERIFY_TOKEN=<>=24 chars>
  WA_PHONE_NUMBER_ID=1420186451169673    # non-secret: the Meta test number's id
  WA_SEND_ENABLED=true    # only if draft sends should actually deliver; otherwise recorded-only
  ```
  Without `WA_PHONE_NUMBER_ID` every inbound payload is dropped as foreign — the webhook answers
  200 and ingests nothing.

## Run

```bash
make up          # API :8000 + dashboard :8501, seeded
make wa-up       # tunnel + Meta callback registration; Ctrl-C tears the tunnel down
```

Then send any WhatsApp message to the business number (**+1 555 175 8185**) — the first time from
a phone that has joined the test-number sandbox if Meta prompts for a join code. The message
lands in the dashboard's **WhatsApp inbox** within a couple of seconds and runs the full
pipeline (extract → score → draft). Sending a draft delivers only if `WA_SEND_ENABLED=true`, and
Meta's 24-hour customer-service window applies.

## What "registered" means

The script takes an app access token (`client_id`/`client_secret`, never printed) and calls
`POST /{app}/subscriptions` with `object=whatsapp_business_account`,
`callback_url=<tunnel>/webhook/whatsapp`, `verify_token` from `.env`, `fields=messages`. Meta
verifies by sending the `hub.challenge` GET, which `app/api/routes_webhook.py` echoes only for
the matching token (403 otherwise). Each run replaces the previous callback, so a fresh tunnel
URL after a restart just needs the script re-run.

## Checks and caveats

- `GET /api/health` must show `"webhook":"enabled"` and `wa_send` matching what you chose.
- Manual handshake check: correct verify token echoes the challenge (200), wrong token → 403.
- The quick-tunnel URL is **ephemeral**: it dies with the script or the machine. That is fine for
  a demo; the hosted deployment (the real scenario) needs no tunnel — it registers its own
  permanent URL once.
- While the tunnel is down Meta retries delivery for a while; nothing to clean up.
- No secrets component: the team-level offline check for the webhook alone is
  `pytest tests/integration/test_whatsapp.py` (no keys, no network).
