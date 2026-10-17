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
| No `GROQ_API_KEY`, or `LIVE_LLM_DAILY_CAP=0` | "Scoring with rules" | Recorded extractions for the sample orders, rules for new text |
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

The image starts uvicorn with `--proxy-headers --forwarded-allow-ips '*'`, so the `X-Forwarded-Proto` from Render sets the scheme of redirects. Per-address limits read `CF-Connecting-IP` (`CLIENT_IP_HEADER` in `render.yaml`), not the socket address. Cloudflare's edge sets that header and refuses a request that brings its own (error 1000). Checked on the live service on 2026-10-14: after 29 writes from one address the next ones got `429`, also with a fresh visitor id. If the header were missing, no per-address limit would apply.

`deploy/render/Dockerfile.dockerignore` is a Dockerfile-specific ignore file. If Render's builder does not honour it, the build fails on missing files or is slow; there is no root `.dockerignore`.

## Website checks

What the site does for visitors, search engines and scanners, and how each is checked. `make check` does not need a browser; the rows marked CI run in `.github/workflows/ci.yml` or `links.yml`.

### Public origin, indexing and share cards

- `NEXT_PUBLIC_SITE_URL` is the public origin (`https://wasel.runs-on.dev`). It is baked in at build time into canonical URLs, the Open Graph card and the sitemap. A production `npm run build` **fails** when it is unset. `make web` defaults it to `http://localhost:8000`; `deploy/render/Dockerfile` defaults it to the demo host and `render.yaml` sets it.
- **The demo is not indexed.** It shows synthetic data under the product name, so `robots.txt` says `Disallow: /` and every page has `noindex`. To allow indexing, set `NEXT_PUBLIC_INDEXABLE=1` at build time: `robots.txt` then allows the pages and links `/sitemap.xml`. The sitemap file is always generated and lists the real routes only (not `/dashboard/order`).
- Every page has its own title (`Page · Wasel`), a description of at most 160 characters and a canonical URL, all from one table in `web/lib/site.ts`. `npm run check:pages` (CI) fails if a page of the export has only the root title, a missing or long description, or a missing canonical.
- Share card: `web/public/og-image.png` (1200 x 630, from `docs/assets/social-preview.png`), with Open Graph and Twitter `summary_large_image` tags. The same card is used on every route; the product page carries `SoftwareApplication` JSON-LD, added to `dist/index.html` by `web/scripts/inject-jsonld.mjs` after the build (React would escape a JSON script, and `dangerouslySetInnerHTML` is banned by `make hygiene`).
- There is one host in this repository. The Cloudflare worker mentioned in the earlier issue is not part of it (`deploy/cloudflare` holds only local tooling), so no hreflang and no second set of headers exist.

### Security headers

`SECURITY_HEADERS` in `src/wasel/main.py` is sent on every response: CSP, `X-Content-Type-Options`, `Referrer-Policy: no-referrer`, `Permissions-Policy` (camera, microphone, geolocation, payment, usb and sensors off), `Cross-Origin-Opener-Policy: same-origin` and `Cross-Origin-Resource-Policy: same-origin`. `Strict-Transport-Security: max-age=31536000` is added only when the request arrived over https (behind Render's proxy through `X-Forwarded-Proto`), without `includeSubDomains` or `preload`. A test pins the set (`test_security_headers_are_complete_and_hsts_is_https_only`). **Scanner grade: not yet recorded.** After the next deploy run securityheaders.com or Mozilla Observatory against `https://wasel.runs-on.dev` and write the grade here.

### Contact, privacy, cookies, analytics

- Contact is `contact@wasel.runs-on.dev`, in the footer of every page, the 404, the privacy page, `SECURITY.md`, the README and `/.well-known/security.txt` (Expires 2027-09-30; renew it before then).
- `/privacy/` states what is stored and for how long, from `SANDBOX_TTL_S` (2 h) and the `RETENTION_*` settings. Keep it in step with those values.
- **No cookie banner, decided.** On a clean profile the demo sets no cookie. Local storage holds `cod_visitor_id` (the sandbox scope), `wasel_lang` (language) and `wasel_guide_*` (closed how-to strips), all strictly necessary or a user preference. Event and dev modes with `API_TOKEN` set one HttpOnly session cookie; those modes are not the public demo.
- **No analytics, decided.** No visit counting or tracking script is loaded, so there is nothing to consent to and the CSP stays `connect-src 'self'`. If counting is added later, use a cookieless tool, allow its origin in the CSP, say so on the privacy page and revisit the banner decision.

### Load budget

Lighthouse CI (`web/lighthouserc.json`, the `lighthouse` job) builds the export and runs Lighthouse's mobile profile three times on `/`, `/dashboard/` and `/dashboard/order/`. It fails on a performance score under 0.7, accessibility under 0.95, best-practices under 0.9, simulated LCP over 4 s or a page over 600 kB. These are the shell pages without an API, so the numbers are a floor for regressions, not what a visitor with data sees.

Baseline on 14 Oct 2026 (median of 3, simulated slow 4G, 4x CPU slowdown, local machine):

| Page | Performance | LCP (simulated) | Transfer |
| --- | --- | --- | --- |
| `/` | 0.97 | 2.5 s | 268 kB |
| `/dashboard/` | 0.74 | 3.4 s | 292 kB |
| `/dashboard/order/` | 0.82 | 3.6 s | 338 kB |

Before this pass the same pages transferred 424 to 495 kB: the logo was a 105 kB PNG (now 7 kB) and the unused monospace font (58 kB) was loaded on every page. Measured directly in Chrome with the same network and CPU throttling (not Lighthouse's simulation), the landing page's largest paint is at 1.8 s and the dashboard shell's at 0.6 s. The 2 s goal holds in that measurement and not in Lighthouse's simulated one; the CI budget follows the simulated number so a regression is visible. **Render cold start: not measured.** The keep-alive workflow pings every 10 minutes, so the service never slept while this was written; Render's documentation says about a minute.

### Offline and install

The app is installable (`display: standalone`) with a service worker (`web/public/sw.js`) that caches only the app shell and static build files and serves `/offline.html` when a page request fails offline. It never stores or answers `/api` requests, because they carry customer text. Remove `sw.js`, `offline.html` and `components/ServiceWorker.tsx` and `display` from the manifest to drop install.

### Uptime alert and waking state

- In the app, `HealthBar` shows "Wasel is starting up" when the first `/api/health` answer takes longer than 3 s, and "Can't reach the Wasel server" when it fails. While the free instance sleeps the browser gets Render's own page instead (the app shell is served by the same process), which Wasel cannot change.
- **External uptime monitor: not set up, needs an account.** To get an alert, create a free monitor (UptimeRobot, Better Stack or similar) with an HTTPS check on `https://wasel.runs-on.dev/api/health` every 5 minutes, keyword `"status":"ok"`, and an email alert to the owner. A pinging monitor also keeps the instance awake. The `keep-alive` workflow pings the same URL; a failing run emails the person who last edited it.

### Accessibility and keyboard

`npm run a11y` (`make a11y`; runs in CI after the smoke test) loads every route in light and dark, at 390 and 1440 px, injects axe-core with the WCAG 2.2 AA rules, and checks that the first Tab stop is the skip link and that it focuses the main region. It reported no violations on 14 Oct 2026 after the dark tokens were corrected. Reduced motion is honoured (`prefers-reduced-motion` stops animation and transitions). The dark theme follows the system setting. Interface text is available in English, French and Arabic for the navigation, landing, 404 and waking messages; the pages' own content is English.
