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

The image starts uvicorn with `--proxy-headers --forwarded-allow-ips '*'`, so the `X-Forwarded-Proto` from Render sets the scheme of redirects. Per-address limits read `CF-Connecting-IP` (`CLIENT_IP_HEADER` in `render.yaml`), not the socket address.

`deploy/render/Dockerfile.dockerignore` is a Dockerfile-specific ignore file. If Render's builder does not honour it, the build fails on missing files or is slow; there is no root `.dockerignore`.
