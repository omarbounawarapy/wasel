# Deploy Wasel on Cloudflare (make, no Docker)

**For:** whoever runs the hosted demo (Montassar owns it; anyone can follow it). **Covers:** spec 01 §6 (topology, mode runbook) and 04 §3 (public/event flips, audit), adapted to the team's decision to run with `make` instead of Docker.

## How it's hosted

```
 judges / seller ──HTTPS──▶ Cloudflare (your hostname, TLS, DDoS)
 Meta webhook ────HTTPS──▶        │  Cloudflare Tunnel (outbound-only connection, no open ports)
                                  ▼
             always-on machine:  cloudflared  ──▶  make serve  = FastAPI on 127.0.0.1:8000
                                                   /api/*, /webhook/whatsapp (event mode), web UI at /,
                                                   worker loop, SQLite in var/app.db
```

One machine runs the app exactly as on a laptop (`make serve`); Cloudflare Tunnel publishes it on a stable HTTPS address. Nothing is containerised.

Why not the other Cloudflare products: **Pages** and **Workers** can't run the long-running Python process, the worker loop and SQLite the spec requires (01 §6.1). **Containers** only run Docker images, and the team doesn't use Docker; their disk is also wiped on every sleep and redeploy.

## What you need

| Item | Notes |
|---|---|
| Cloudflare account | Free plan is enough |
| A domain added to Cloudflare | Required for a stable tunnel address. Add one you own (change its nameservers to Cloudflare's), or buy one in Cloudflare Registrar |
| An always-on machine | Linux VPS or a PC that stays on. ≥ 1 GB RAM, Python 3.11, Node 22, git, make, `cloudflared` |
| Keys for the host | A Groq key for public mode (`KEY_PUBLIC` in the spec, capped), an `ADMIN_TOKEN` (≥ 24 random chars). WhatsApp secrets only for the event window |

## 1. Cloudflare dashboard (manual, once)

1. **Add the domain:** dashboard → **Add a domain** → Free plan → change the nameservers at your registrar to the two Cloudflare shows. Wait until the domain shows **Active**.
2. **Create the tunnel:** **Networking** → **Tunnels** → **Create a tunnel** → type Cloudflared → name it `wasel` → **Create Tunnel**. The page shows an install command containing a long token that starts with `eyJhIjoi`. Copy **only the token**. This is a secret: it goes into the host's `.env` and nowhere else.
3. **Publish the app:** open the tunnel → **Routes** → **Add route** → **Published application**:
   - Subdomain: `wasel` · Domain: your domain
   - Service URL: `http://localhost:8000`
4. **SSL/TLS** (domain settings): encryption mode **Full**, **Always Use HTTPS** on.
5. **Don't** put a Cloudflare Access login in front of this hostname: judges must open it without an account.

Your public URL is now `https://wasel.<your-domain>`. It shows Cloudflare error **1033** until the tunnel connects (step 3 below).

## 2. Prepare the host (once)

```bash
git clone https://github.com/omarbounawarapy/hackathon wasel && cd wasel
make setup            # Python deps (.venv if you create one first: python3.11 -m venv .venv)
make web              # builds the UI into web/dist; `make serve` serves it at /
cp .env.example .env  # then edit it (below)
```

Host `.env` for **public mode** (the judges' default, 04 §2.1):

| Key | Value |
|---|---|
| `APP_MODE` | empty (= public) |
| `GROQ_API_KEY` | the capped public key |
| `ADMIN_TOKEN` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `CLOUDFLARE_TUNNEL_TOKEN` | the token from step 1.2 |
| `HOST` / `PORT` | `127.0.0.1` / `8000` (only the tunnel reaches the app) |
| `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN` | **empty**: public mode must not hold WhatsApp secrets |
| `WA_AUTO_SEND`, `DRAFT_LLM` | `false` (public mode never sends anyway) |

Install `cloudflared`: Linux: the package from Cloudflare's downloads page; Windows: `cloudflared-windows-amd64.exe` saved as `~/.local/bin/cloudflared.exe` (what `make tunnel` looks for).

## 3. Run it

**Quick (two terminals, stops when you close them):**

```bash
make serve     # terminal 1: app on 127.0.0.1:8000, mode from .env
make tunnel    # terminal 2: connects the tunnel; the public URL starts answering
```

**Always on (survives reboots):**

- **Linux:** copy `deploy/wasel.service` to `/etc/systemd/system/`, set `User` and `WorkingDirectory`, then `sudo systemctl enable --now wasel`. For the tunnel: `sudo cloudflared service install <token>`.
- **Windows:** in an admin terminal, `cloudflared service install <token>` (the tunnel becomes a Windows service). Start `make serve` at logon with Task Scheduler, or keep a terminal open.

## 4. Check it (every deploy and every mode flip)

```bash
make smoke URL=https://wasel.<your-domain>
```

`SMOKE PASS … public v1=87 v2=16` means health, the UI, the hero loop and the read-only samples all work. Then the incognito audit (04 §3.3):

1. `/api/health` shows `mode=public`, `wa_send=false`, `webhook=disabled`, `wa_auto_send=false`.
2. `POST /webhook/whatsapp` returns 404/405.
3. The queue shows only sample orders: no teammate names or phone numbers.
4. **Try this order** on the hero runs the full loop.
5. A second incognito window doesn't see the first window's copy.
6. `/api/metrics/impact` shows `simulated: true`.

## 5. Update to a new version

CI must be green on `main` first (it runs the same `make web` + `make serve` + `make smoke` path). Then on the host:

```bash
make deploy                      # git pull + make setup web
sudo systemctl restart wasel     # or Ctrl-C and `make serve` again
make smoke URL=https://wasel.<your-domain>
```

**Rollback:** `git checkout <tag or sha> && make setup web`, restart, smoke. For the submission, pin the host to the tag `submission-v1` (04 §3.1).

## 6. WhatsApp event window (flip to `event`, then back)

Flip **to event** (only with teammates' registered phones):

1. In the host `.env`: `APP_MODE=event`, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `WA_PHONE_NUMBER_ID`, `WEBHOOK_ENABLED=true`, `WA_SEND_ENABLED=true`, `LIVE_LLM_DAILY_CAP=300`. Add `DRAFT_LLM=true` and `WA_AUTO_SEND=true` only if replies should go out without a click.
2. Restart `make serve`. Health must show `mode=event`, `webhook=enabled`.
3. **Meta console** → your app → WhatsApp → **Configuration** → Callback URL `https://wasel.<your-domain>/webhook/whatsapp`, Verify token = `WA_VERIFY_TOKEN`, subscribe the **messages** field. The address is stable, so this is done once (unlike `make wa-up`, whose quick-tunnel URL changes on every run).
4. Send one message from a registered phone and check it lands in **WhatsApp messages**.

Flip **back to public** (before the submission, 04 §3.1 16:45):

1. In `.env`: `APP_MODE=` (empty), delete `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, set `WEBHOOK_ENABLED=false`, `WA_AUTO_SEND=false`.
2. Restart. Public mode reseeds on boot, which wipes the real WhatsApp rows.
3. Meta console: remove the callback (or unsubscribe `messages`).
4. `make smoke` + the audit in §4.

## 7. Secrets and safety

- `.env` stays on the host and is git-ignored. `make hygiene` (part of `make check` and CI) fails on key-shaped strings, including tunnel tokens (`eyJhIjoi…`).
- Only the tunnel token, keys and `ADMIN_TOKEN` are secret. The hostname is public.
- After judging (04 §6.3): delete the tunnel in the dashboard (or rotate its token), revoke `WA_TOKEN`, delete the public Groq key, rotate `ADMIN_TOKEN`.

## No domain yet?

`cloudflared tunnel --url http://localhost:8000` (no account needed) prints a random `https://….trycloudflare.com` address. It works for testing, but the address changes every restart, so it's not suitable for the link you submit or for the Meta callback.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Cloudflare error **1033** | The tunnel isn't connected: `make tunnel` or the cloudflared service isn't running |
| **502 Bad Gateway** | Tunnel is up but `make serve` isn't running, or the route's Service URL isn't `http://localhost:8000` |
| Health shows the wrong `mode` | `.env` on the host: `APP_MODE` empty = public |
| `/` answers but the UI is blank or 404 | `make web` wasn't run after the last pull |
| The app won't start after copying `.env.example` | Update to a version with the `LIVE_LLM_DAILY_CAP=` fix (empty = mode default) |
