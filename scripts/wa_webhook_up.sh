#!/usr/bin/env bash
# wa_webhook_up.sh: put the localhost webhook on the internet for Meta in one command — a
# cloudflared quick tunnel + Graph API registration of the callback URL and the `messages`
# field. What remains afterwards is to send a WhatsApp message to the business number.
# See docs/whatsapp.md. Needs META_APP_ID, WA_APP_SECRET, WA_VERIFY_TOKEN and
# WA_PHONE_NUMBER_ID in .env plus WEBHOOK_ENABLED=true; the quick-tunnel URL is ephemeral, so
# re-run after every restart (registration is idempotent — it replaces the previous callback).
# Ctrl-C tears the tunnel down.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PORT="${PORT:-8000}"
GRAPH="${META_GRAPH_VERSION:-v21.0}"
CLOUDFLARED="${CLOUDFLARED:-$(command -v cloudflared || true)}"
[ -n "$CLOUDFLARED" ] || CLOUDFLARED="$HOME/.local/bin/cloudflared"
[ -x "$CLOUDFLARED" ] || [ ! -x "$CLOUDFLARED.exe" ] || CLOUDFLARED="$CLOUDFLARED.exe"      # Windows (Git Bash)
# the project venv's python if present; on Windows `python3` is only the Microsoft Store stub
PYTHON="${PYTHON:-$(for p in .venv/bin/python .venv/Scripts/python.exe; do [ -x "$p" ] && echo "$p" && break; done)}"
PYTHON="${PYTHON:-python3}"
[ -x "$CLOUDFLARED" ] || { echo "cloudflared not found (set CLOUDFLARED=… or install it)" >&2; exit 1; }

[ -f .env ] && { set -a; . ./.env; set +a; }
: "${META_APP_ID:?META_APP_ID missing (.env): the id of your Meta app}"
APP_ID="$META_APP_ID"
: "${WA_APP_SECRET:?WA_APP_SECRET missing (.env)}"
: "${WA_VERIFY_TOKEN:?WA_VERIFY_TOKEN missing (.env)}"
: "${WA_PHONE_NUMBER_ID:?WA_PHONE_NUMBER_ID missing — without it every inbound payload is dropped as foreign}"

HEALTH=$(curl -sf -m 5 "http://localhost:$PORT/api/health") || { echo "API not up on :$PORT (make up first)" >&2; exit 1; }
grep -q '"webhook":"enabled"' <<<"$HEALTH" || { echo "webhook not mounted: set APP_MODE=dev|event and WEBHOOK_ENABLED=true" >&2; exit 1; }

LOG=$(mktemp)
TUNNEL_PID=""
cleanup() { [ -n "$TUNNEL_PID" ] && kill "$TUNNEL_PID" 2>/dev/null || true; rm -f "$LOG"; }
trap cleanup EXIT
trap 'exit 0' INT TERM

"$CLOUDFLARED" tunnel --url "http://localhost:$PORT" --no-autoupdate >"$LOG" 2>&1 &
TUNNEL_PID=$!

echo "waiting for the tunnel…"
URL=""
for _ in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1 || true)   # no match yet: keep waiting (set -e)
  [ -n "$URL" ] && break
  sleep 2
done
[ -n "$URL" ] || { echo "tunnel did not come up:" >&2; tail -5 "$LOG" >&2; exit 1; }

for _ in $(seq 1 15); do
  curl -sf -m 10 "$URL/api/health" >/dev/null && break
  sleep 2
done
echo "tunnel up: $URL"

TOKEN=$(curl -sf -m 15 "https://graph.facebook.com/oauth/access_token?client_id=$APP_ID&client_secret=$WA_APP_SECRET&grant_type=client_credentials" \
        | "$PYTHON" -c "import json,sys; print(json.load(sys.stdin).get('access_token',''))")
[ -n "$TOKEN" ] || { echo "could not get an app access token — check META_APP_ID / WA_APP_SECRET" >&2; exit 1; }

RESULT=$(curl -sf -m 15 -X POST "https://graph.facebook.com/$GRAPH/$APP_ID/subscriptions" \
  -H "Authorization: Bearer $TOKEN" \
  -d "object=whatsapp_business_account" \
  -d "callback_url=$URL/webhook/whatsapp" \
  -d "verify_token=$WA_VERIFY_TOKEN" \
  -d "fields=messages") || RESULT='{"error":"registration failed (network or permissions)"}'
grep -q '"success":true' <<<"$RESULT" || { echo "callback registration failed: $RESULT" >&2; exit 1; }
echo "Meta callback registered: $URL/webhook/whatsapp (fields=messages, active)"

echo "ready — send a WhatsApp message to the business number; it lands in the dashboard's WhatsApp inbox."
wait "$TUNNEL_PID"
