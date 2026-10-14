# Deploying on Render (free)

One free Render web service runs the API and the built web UI from a single image (`deploy/render/Dockerfile`), on one origin. It suits a **public demo**: no card, no domain, a stable `https://<name>.onrender.com` address.

## Limits of the free plan

- The service sleeps after about 15 minutes without traffic; the first request afterwards waits about a minute.
- The disk is ephemeral and the worker loop stops while asleep. Public mode rebuilds the database on every start anyway, so nothing is lost that matters. Do not use this for real WhatsApp conversations (`event` mode); test WhatsApp locally with `make wa-up` ([whatsapp.md](../subsystems/whatsapp.md#testing-locally)).
- 512 MB RAM; the app used about 125 MB in the local smoke run.

## Steps

1. Sign in at render.com with GitHub (no card).
2. New, then Blueprint, select this repository. Render reads `render.yaml`.
3. Optional secrets in the service's Environment tab: `GROQ_API_KEY` (capped key), `ADMIN_TOKEN` (24+ characters). Without a key the app scores with recorded extractions and rules.
4. Verify: `make smoke URL=https://<name>.onrender.com`, expect `SMOKE PASS ... public v1=87 v2=16`.
5. Deploys follow `render.yaml`'s `autoDeployTrigger: checksPass`: a commit goes live only after its CI checks pass. `/api/health` shows `build.git_sha`, the commit the service runs (`RENDER_GIT_COMMIT`, unless `GIT_SHA` is set).

## Before the demo

Do this 15 minutes before judges arrive. Replace `$URL` with `https://<name>.onrender.com` (or `https://wasel.runs-on.dev`).

1. **Wake the service.** `curl -s $URL/api/health` and wait. The first request after a sleep takes about a minute.
2. **Smoke test.** `make smoke URL=$URL`. Expect `SMOKE PASS ... public v1=87 v2=16`. A failure here means the deploy is not healthy; look at the Render logs before anything else.
3. **Check the AI.** In `/api/health` (or the bar at the top of the dashboard) read `llm`:
   - `chain_extract` is not empty and `primary` is not `rules`. If it is `rules`, `GROQ_API_KEY` is missing or invalid.
   - `cap_reached` is `false`. `live_calls_today` against `live_call_cap` shows what is left; the counter is per UTC day and resets at 00:00 UTC.
4. **Start from a clean queue.** Visitors' orders stay until the next restart. To clear them without restarting:

   ```bash
   curl -s -X POST $URL/api/admin/reset -H "X-Admin-Token: $ADMIN_TOKEN"
   ```

   The endpoint exists only when `ADMIN_TOKEN` is set on Render to at least 24 characters. It deletes every order, reseeds the samples and keeps the catalog, the extraction cache and the AI usage count (so a reset does not refill the daily cap).
5. **Adjust the AI budget if needed.** In Render, Environment, change `LIVE_LLM_DAILY_CAP` (provider calls per UTC day; `render.yaml` sets 500), then save; Render restarts the service. `ADDR_LLM_SHARE` and `VISITOR_LLM_CAP_DAY` bound what one address and one visitor may use of it. All three are described in [environment.md](../configuration/environment.md).
6. **Keep it awake** for the judging window: see the next section, or point an external HTTP monitor at `/api/health` every 10 minutes (no GitHub Actions minutes used).

### What a visitor sees when the AI is not available

| State | Health bar | Scoring |
| --- | --- | --- |
| No `GROQ_API_KEY`, or `LIVE_LLM_DAILY_CAP=0` | "AI offline: scoring with rules only" | Recorded extractions for the sample orders, rules for new text |
| Daily cap reached | "AI budget used up: new messages are scored by rules only" | Rules only; the sample orders still use their recorded extractions |
| Backup model answering | "AI running on its backup model" | Normal |

The product keeps working in all three; only the quality on unusual new text drops.

## Keep the demo awake (submission day)

`.github/workflows/keep-alive.yml` pings `/api/health` every 10 minutes so the service never sleeps. It ships **disabled**: only the manual trigger is on. To use it:

1. Uncomment the `schedule:` block in the workflow and push to `main` (or run it once by hand from the Actions tab to test).
2. Optional: set the repository variable `DEMO_URL` if the demo is not at `https://wasel.runs-on.dev`.
3. After judging, comment the block out again so the free-plan hours are not spent for nothing.

## Custom domain (runs-on.dev)

The demo is also served at `https://wasel.runs-on.dev`, a free subdomain from [runs-on.dev](https://runs-on.dev). No code or `render.yaml` change is involved; the app has no hard-coded host.

1. Claim the name at runs-on.dev (GitHub sign-in; one name per account).
2. In runs-on.dev's manage page, add a `CNAME` record pointing to the service's `onrender.com` hostname (hostname only, no `https://`). In the registry this is `"records": { "CNAME": "<name>.onrender.com" }`.
3. In Render, service Settings, Custom Domains, add `wasel.runs-on.dev`, then Verify. Render issues the certificate itself.
4. Check: `make smoke URL=https://wasel.runs-on.dev`.

If verification fails right after adding the record, retry in a few minutes; DNS propagation is the usual cause.

## Local check of the image

```bash
make render-smoke   # build, run on :10000 and smoke-test in one step (CI runs it too)
docker build -f deploy/render/Dockerfile -t wasel-render .
docker run --rm -p 10000:10000 -e PORT=10000 wasel-render
make smoke URL=http://127.0.0.1:10000
```

The image starts uvicorn with `--proxy-headers --forwarded-allow-ips '*'`, so the `X-Forwarded-Proto` from Render sets the scheme of redirects. Per-address limits read `CF-Connecting-IP` (`CLIENT_IP_HEADER` in `render.yaml`), not the socket address. Render's edge is expected to set that header; this has not been confirmed on the live service, and if it is missing no per-address limit applies.

`deploy/render/Dockerfile.dockerignore` is a Dockerfile-specific ignore file. If Render's builder does not honour it, the build fails on missing files or is slow; there is no root `.dockerignore`.
