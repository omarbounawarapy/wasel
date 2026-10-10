# WhatsApp integration

Wasel talks to WhatsApp through Meta's Cloud API in two directions: an inbound webhook that delivers customer messages and delivery statuses, and an outbound send call for drafted questions. This page describes both, the conditions under which they are active, and how to test them locally. For a permanent deployment see [deployment](../operations/deployment.md).

Code: `src/wasel/api/routes_webhook.py` (routes and processing), `src/wasel/ingress/whatsapp.py` (pure signature and payload logic), `src/wasel/outbound/whatsapp_send.py` (sender), `scripts/ops/wa_webhook_up.sh` (local registration helper).

## When it is active

Everything here is off unless deliberately enabled, and it is off in `public` mode regardless of settings.

| Capability | Requirements |
|---|---|
| Webhook mounted (`/webhook/whatsapp`) | `APP_MODE` is `dev` or `event`, `WEBHOOK_ENABLED=true`, `WA_APP_SECRET` at least 16 characters, `WA_VERIFY_TOKEN` at least 24 characters |
| Inbound payloads accepted | the above plus `WA_PHONE_NUMBER_ID` set; changes addressed to any other phone number id are counted and dropped, so without it the webhook answers 200 and ingests nothing |
| Real sending | `APP_MODE` is not `public`, `WA_SEND_ENABLED=true`, `WA_TOKEN` and `WA_PHONE_NUMBER_ID` set |
| Sending without a click | additionally `WA_AUTO_SEND=true` and an `auto_send` draft ([outbound](outbound.md#routing)) |

`GET /api/health` reports what the running process resolved: `webhook` (`enabled` or `disabled`), `wa_send`, `wa_auto_send`, `wa_token_present` and `whatsapp.last_webhook_at` (the last request with a valid signature).

## Inbound

### Verification handshake

Meta calls `GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...` when a callback is registered. Wasel echoes the challenge as plain text if the mode is `subscribe`, the challenge is at most 128 characters and the token matches `WA_VERIFY_TOKEN` (constant-time comparison); otherwise it returns 403. The uvicorn access log prints the full query string, so a log filter (`RedactVerifyToken`) rewrites verify requests to `?<redacted>`.

### Receiving messages

`POST /webhook/whatsapp` does the following, in order:

1. Refuses bodies over 1 MiB (`413`), checking `Content-Length` first and then the streamed size. The rest of the API allows 64 KB.
2. Verifies `X-Hub-Signature-256` as HMAC-SHA256 of the raw body with `WA_APP_SECRET`. A missing, malformed or mismatching header returns `401` and writes a `webhook.rejected` event with the reason (`missing`, `malformed`, `mismatch`). There is no flag to skip the check.
3. Records `last_webhook_at` and returns `200 {}` immediately.
4. Stores the payload (`process`, in a worker thread) and answers `200` only after the commit. Malformed JSON writes `webhook.malformed` and an unexpected shape writes `webhook.process_error` with the exception type only; both answer `200` because a retry cannot help. A storage error (for example a locked database) writes `webhook.process_error` if it can and answers `503`, so Meta retries; messages already stored are skipped by their `wamid`.

Processing walks `entry[].changes[].value`, drops changes for another `phone_number_id`, and sorts messages and statuses by provider timestamp, so an out-of-order batch is stored in order:

| WhatsApp type | Stored as |
|---|---|
| `text` with a non-blank body | `kind='text'` |
| `location` with valid coordinates | `kind='location'` with latitude and longitude; forces the address level to `exact` |
| anything else (audio, image, sticker, video, document, reaction, interactive, unknown) | `kind='unsupported'`, no text; sends the order to `needs_review` |
| entry missing an id, a valid sender, a timestamp or a type | skipped and counted |

Each message goes through `store_message` and then the ordinary [ingestion path](../architecture/order-pipeline.md#entry-points):

- A `wamid` already stored is a duplicate: nothing is written and no rescore is armed.
- The customer is found or created by phone number (`+` followed by the WhatsApp id, validated as 7 to 15 digits), with the profile name as display name. The conversation is the customer's most recent WhatsApp conversation, created if none exists.
- If the message quotes another (`context.id`) and that message is in the conversation, the link is kept as `reply_to_message_id`.

**Delivery statuses** (`sent`, `delivered`, `read`, `failed`) update `delivery_status` on Wasel's own outbound messages only, and only forward (`sent < delivered < read < failed`). An unknown message id is ignored.

### Privacy in logs and storage

Log lines carry counts and reasons only: never the body, the sender's number or a secret. The phone number is stored in `customers.phone_e164` and nowhere else; every API response masks it, and it is never part of an LLM request. `messages.raw_payload` exists in the schema but the current code does not write it.

## Outbound

`WhatsAppSender.send_text` posts a plain text message to `https://graph.facebook.com/<WA_API_VERSION>/<WA_PHONE_NUMBER_ID>/messages` with the `WA_TOKEN` bearer token and returns the message id (`wamid`). `WA_API_VERSION` defaults to `v21.0` when empty. The request timeout is 10 seconds. Transient failures (network errors, 408, 429, 5xx) are retried twice with exponential backoff; other 4xx responses fail immediately with a reason such as `http_400:131047` (the Graph error code). WhatsApp only allows free-form text within 24 hours of the customer's last message, so Wasel refuses to send outside that window (`409 OUTSIDE_24H_WINDOW`). Template messages are not implemented. See [outbound](outbound.md#sending) for the full send rules.

## Testing locally

`scripts/ops/wa_webhook_up.sh` (`make wa-up`) gives a local API a public URL for as long as it runs. It starts a `cloudflared` quick tunnel, gets an app access token with `META_APP_ID` and `WA_APP_SECRET`, and calls `POST /{app-id}/subscriptions` with `object=whatsapp_business_account`, `callback_url=<tunnel>/webhook/whatsapp`, your verify token and `fields=messages`. Each run replaces the previous callback, so re-run it after a restart (the quick-tunnel address changes every time). Ctrl-C tears the tunnel down.

Prerequisites:

- `cloudflared`. On Linux:
  ```bash
  mkdir -p ~/.local/bin && curl -sL -o ~/.local/bin/cloudflared \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
    && chmod +x ~/.local/bin/cloudflared
  ```
  On macOS use `brew install cloudflared`, or point `CLOUDFLARED=...` at any binary.
- A Meta app with the WhatsApp product, a business phone number and a system-user token, entered in `.env` at the repository root (never committed):
  ```
  APP_MODE=dev
  WEBHOOK_ENABLED=true
  META_APP_ID=<your Meta app id>
  WA_TOKEN=<system-user token>
  WA_APP_SECRET=<app secret, at least 16 characters>
  WA_VERIFY_TOKEN=<at least 24 characters>
  WA_PHONE_NUMBER_ID=<id of the business phone number>
  WA_SEND_ENABLED=true      # only if draft sends should be delivered; otherwise they are only recorded
  ```

Run:

```bash
make up          # the seller UI and API on :8000 (make ui: analyst view on :8501)
make wa-up       # tunnel + callback registration
```

The script checks that `/api/health` reports `"webhook":"enabled"` before it starts. Send a WhatsApp message to the business number; it appears under WhatsApp messages within a couple of seconds and goes through extraction, scoring and drafting.

Checks and caveats:

- The handshake answers 200 with the challenge for the right token and 403 for a wrong one.
- While the tunnel is down Meta retries delivery for a while; there is nothing to clean up.
- To test the webhook with no keys and no network, run `pytest tests/integration/test_whatsapp.py` (fixtures in `tests/fixtures/whatsapp/`, including duplicates, out-of-order batches, statuses and media types).
