# Deployment

Wasel runs as one Python process (`make serve`) on an always-on machine. A Cloudflare Tunnel publishes it on a stable HTTPS address without opening any port. Nothing is containerised.

```
 browser ─────HTTPS──▶ Cloudflare (your hostname, TLS)
 Meta webhook ─HTTPS──▶      │  Cloudflare Tunnel (outbound-only connection)
                             ▼
        always-on machine:  cloudflared ──▶ make serve = FastAPI on 127.0.0.1:8000
                                            /api/*, /webhook/whatsapp (when enabled), web UI at /,
                                            worker loop, SQLite in var/app.db
```

Cloudflare Pages and Workers cannot host the long-running worker loop and the SQLite file this app needs, and Cloudflare Containers only run Docker images, so a small VPS or a PC that stays on is the host.

## Requirements

| Item | Notes |
|---|---|
| Cloudflare account | Free plan is enough |
| A domain added to Cloudflare | Needed for a stable tunnel address |
| An always-on machine | Linux VPS or PC, ≥ 1 GB RAM, Python 3.11, Node 22, git, make, `cloudflared` |
| Secrets | A Groq API key (capped), an `ADMIN_TOKEN` (≥ 24 random characters), the tunnel token. WhatsApp secrets only if you connect WhatsApp |

## 1. Cloudflare (once)

1. **Add the domain:** dashboard → **Add a domain** → Free plan → change the nameservers at your registrar to the two Cloudflare shows. Wait until the domain is **Active**.
2. **Create the tunnel:** **Networking → Tunnels → Create a tunnel** → type Cloudflared → name it `wasel`. The page shows an install command containing a long token starting with `eyJhIjoi`. Copy only the token; it is a secret and belongs in the host's `.env` only.
3. **Publish the app:** open the tunnel → **Routes → Add route → Published application**. Subdomain `wasel`, your domain, service URL `http://localhost:8000`.
4. **SSL/TLS:** encryption mode **Full**, **Always Use HTTPS** on.
5. Do not put Cloudflare Access in front of the hostname if visitors should reach it without an account.

The public URL is now `https://wasel.<your-domain>`. It shows Cloudflare error 1033 until the tunnel connects (step 3 below).

## 2. Prepare the host (once)

```bash
git clone <repository-url> wasel && cd wasel
python3.11 -m venv .venv
make setup            # Python dependencies
make web              # builds the UI into web/dist; make serve serves it at /
cp .env.example .env  # then edit it
```

Host `.env` for **public mode** (the default, safe for anonymous visitors):

| Key | Value |
|---|---|
| `APP_MODE` | empty (= public) |
| `GROQ_API_KEY` | a capped key |
| `ADMIN_TOKEN` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CLOUDFLARE_TUNNEL_TOKEN` | the token from step 1.2 |
| `HOST` / `PORT` | `127.0.0.1` / `8000` (only the tunnel reaches the app) |
| `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` | empty: public mode must not hold WhatsApp secrets |
| `WA_AUTO_SEND`, `DRAFT_LLM` | `false` |

Install `cloudflared` from Cloudflare's downloads page (on Windows, save the executable as `~/.local/bin/cloudflared.exe`, where `make tunnel` looks for it).

## 3. Run

Quick, in two terminals:

```bash
make serve     # app on 127.0.0.1:8000, mode from .env
make tunnel    # connects the tunnel; the public URL starts answering
```

Always on:

- **Linux:** copy `deploy/wasel.service` to `/etc/systemd/system/`, set `User` and `WorkingDirectory`, then `sudo systemctl enable --now wasel`. Install the tunnel as a service with `sudo cloudflared service install <token>`.
- **Windows:** in an admin terminal, `cloudflared service install <token>`; start `make serve` at logon with Task Scheduler.

## 4. Verify (after every deploy and every mode change)

```bash
make smoke URL=https://wasel.<your-domain>
```

`SMOKE PASS … public v1=87 v2=16` means health, the UI, the score-and-reply loop and the read-only samples all work. Then check manually:

1. `/api/health` shows `mode=public`, `wa_send=false`, `webhook=disabled`, `wa_auto_send=false`.
2. `POST /webhook/whatsapp` returns 404 or 405.
3. The queue shows only sample orders.
4. **Try this order** on a sample runs the full loop.
5. A second private window does not see the first window's copy.
6. `/api/metrics/impact` shows `simulated: true`.

## 5. Update

```bash
make deploy                      # git pull --ff-only, then make setup web
sudo systemctl restart wasel     # or stop and re-run make serve
make smoke URL=https://wasel.<your-domain>
```

Roll back with `git checkout <tag or sha> && make setup web`, restart, and smoke test again.

## 6. Connecting WhatsApp (`event` mode)

`APP_MODE=event` mounts the WhatsApp webhook and allows sends. Use it only with a phone number registered in your Meta app, and never on a host that serves anonymous visitors.

1. In `.env` set `APP_MODE=event`, `WA_TOKEN`, `WA_APP_SECRET` (≥ 16 characters), `WA_VERIFY_TOKEN` (≥ 24 characters), `WA_PHONE_NUMBER_ID`, `WEBHOOK_ENABLED=true`, `WA_SEND_ENABLED=true` and, if you want a higher daily LLM budget, `LIVE_LLM_DAILY_CAP`. Add `DRAFT_LLM=true` and `WA_AUTO_SEND=true` only if cleared replies should go out without a click.
2. Restart `make serve`. `/api/health` must show `mode=event`, `webhook=enabled`.
3. In the Meta console (your app → WhatsApp → Configuration) set the callback URL to `https://wasel.<your-domain>/webhook/whatsapp`, the verify token to `WA_VERIFY_TOKEN`, and subscribe to the **messages** field.
4. Send a message from a registered phone and check that it appears in the WhatsApp inbox.

To return to public mode: empty `APP_MODE`, remove the WhatsApp secrets, set `WEBHOOK_ENABLED=false` and `WA_AUTO_SEND=false`, restart (public mode reseeds on boot, which removes real rows), remove the callback in the Meta console, then run the verification in section 4. For local testing without a permanent host, see [whatsapp.md](whatsapp.md).

## 7. Secrets

- `.env` stays on the host and is git-ignored. `make hygiene` (part of `make check` and CI) fails on key-shaped strings, including tunnel tokens.
- Only the tunnel token, API keys and `ADMIN_TOKEN` are secret; the hostname is public.
- When retiring a deployment, delete the tunnel (or rotate its token), revoke `WA_TOKEN` and the API keys, and rotate `ADMIN_TOKEN`.

## Trying it without a domain

`cloudflared tunnel --url http://localhost:8000` prints a random `https://….trycloudflare.com` address. It needs no account but changes on every restart, so it is not suitable for a link you share or for the Meta callback.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Cloudflare error 1033 | The tunnel is not connected: `make tunnel` or the cloudflared service is not running |
| 502 Bad Gateway | The tunnel is up but `make serve` is not running, or the route's service URL is not `http://localhost:8000` |
| Health shows the wrong `mode` | Check `APP_MODE` in the host `.env`; empty means public |
| `/` answers but the UI is blank or 404 | `make web` was not run after the last pull |
