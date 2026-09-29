# WhatsApp integration and local testing

The WhatsApp path is complete end to end: a signed Cloud API webhook, deduplication, debounce, LLM extraction and scoring, and sending through the Cloud API. Running locally, the only missing piece is a public URL Meta can deliver to. `scripts/wa_webhook_up.sh` (`make wa-up`) provides one for as long as it runs: a cloudflared quick tunnel plus Graph API registration of the callback URL and the `messages` field. It needs no deployment and no Cloudflare account, and it is idempotent on re-run. For a permanent deployment see [deployment.md](deployment.md).

## Prerequisites

- `cloudflared` (a single static binary; quick tunnels need no account):
  ```bash
  mkdir -p ~/.local/bin && curl -sL -o ~/.local/bin/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    && chmod +x ~/.local/bin/cloudflared
  ```
  On macOS use `brew install cloudflared`, or point `CLOUDFLARED=…` at any binary.
- A Meta app with the WhatsApp product, a business phone number and a system-user token. Put the values in `.env` at the repository root and never commit them:
  ```
  APP_MODE=dev              # public mode never mounts the webhook
  WEBHOOK_ENABLED=true
  META_APP_ID=<your Meta app id>
  WA_TOKEN=<system-user token>
  WA_APP_SECRET=<app secret, at least 16 characters>
  WA_VERIFY_TOKEN=<at least 24 characters>
  WA_PHONE_NUMBER_ID=<id of the business phone number>
  WA_SEND_ENABLED=true      # only if draft sends should actually be delivered; otherwise they are recorded only
  ```
  Without `WA_PHONE_NUMBER_ID` every inbound payload is dropped as foreign: the webhook answers 200 and ingests nothing.

## Run

```bash
make up          # API :8000 + dashboard :8501, seeded
make wa-up       # tunnel + Meta callback registration; Ctrl-C tears the tunnel down
```

Send a WhatsApp message to the business number. If Meta prompts for a join code the first time, follow its instructions for the test number. The message appears in the **WhatsApp inbox** within a couple of seconds and runs the full pipeline (extract, score, draft). Sending a draft delivers only if `WA_SEND_ENABLED=true`, and Meta's 24-hour customer-service window applies.

## What registration does

The script obtains an app access token (`META_APP_ID` and `WA_APP_SECRET`, never printed) and calls `POST /{app}/subscriptions` with `object=whatsapp_business_account`, `callback_url=<tunnel>/webhook/whatsapp`, the verify token from `.env` and `fields=messages`. Meta verifies the callback with a `hub.challenge` GET, which `app/api/routes_webhook.py` echoes only for the matching token (403 otherwise). Each run replaces the previous callback, so a new tunnel URL after a restart only needs the script re-run.

## Checks and caveats

- `GET /api/health` must show `"webhook":"enabled"` and a `wa_send` value that matches what you chose.
- Handshake check: the correct verify token echoes the challenge (200); a wrong token returns 403.
- The quick-tunnel URL is ephemeral and dies with the script or the machine. A hosted deployment registers its own permanent URL once.
- While the tunnel is down Meta retries delivery for a while; there is nothing to clean up.
- To test the webhook without any keys or network: `pytest tests/integration/test_whatsapp.py`.
