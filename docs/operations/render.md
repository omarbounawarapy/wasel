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

## Local check of the image

```bash
docker build -f deploy/render/Dockerfile -t wasel-render .
docker run --rm -p 10000:10000 -e PORT=10000 wasel-render
make smoke URL=http://localhost:10000
```

`deploy/render/Dockerfile.dockerignore` is a Dockerfile-specific ignore file. If Render's builder does not honour it, the build fails on missing files or is slow; the root `.dockerignore` (which belongs to the Cloudflare image) must not be edited for this.
