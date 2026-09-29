# Web UI

The seller-facing interface of Wasel: a Next.js 16 app (App Router, React 19, Tailwind 4, Radix primitives, Sonner toasts, Geist fonts) that is built to static files and served by the FastAPI backend at `/`. It has no server of its own and no data of its own; every screen reads `/api` and every button calls it. The overview of both front ends is in [docs/interfaces.md](../docs/interfaces.md).

## Screens

`/` redirects to `/dashboard`. Routes (all under `app/dashboard/`):

| Route | Screen | Endpoints |
|---|---|---|
| `/dashboard` | Orders to check: queue with tier filters and counts, refreshed every 3 s | `GET /api/orders` |
| `/dashboard/order?id=<order_id>` | One order: highlighted messages, score and reason, history with diffs, draft with its checks, actions, simulated reply | `GET /api/orders/{id}`, `POST .../actions`, `POST /api/drafts/{id}/send`, `POST .../simulate-reply`, `POST .../rescore`, `POST .../try` |
| `/dashboard/inbox` | WhatsApp messages: orders that arrived through the webhook | `GET /api/orders` |
| `/dashboard/paste` | Add an order: paste text and follow it until it is scored | `POST /api/orders/ingest`, `GET /api/orders/{id}` |
| `/dashboard/impact` | Money saved (simulated) | `GET /api/metrics/impact` |
| `/dashboard/activity` | Activity log | `GET /api/events` |
| `/dashboard/quality` | Quality checks: evaluation reports | `GET /api/eval` |
| `/dashboard/failures` | Silent failures | `GET /api/failures`, `GET /api/failures/sessions/{id}` |
| `/dashboard/monitor` | Live monitor | `GET /api/monitor` |
| `/dashboard/traces` | AI call log | `GET /api/traces` |

The order page takes its id from the query string, not from a path segment, because a static export cannot pre-render unknown ids. A header bar on every page shows the backend's mode, LLM path, WhatsApp state and worker health (`GET /api/health`, every 10 s).

## Structure

```
app/               routes, layouts, global CSS; app/dashboard/* are the screens
components/        dashboard/ (Sidebar, HealthBar, MobileFootbar), ui/ (Radix-based primitives), wasel/kit.tsx (shared building blocks), ErrorBoundary
lib/api.ts         the single HTTP client (axios): base URL logic, visitor id header, error normalisation
lib/api/orders.ts  one function per endpoint the UI uses
lib/api/visitor.ts the visitor id (uuid v4 in localStorage["cod_visitor_id"], with an in-memory fallback)
hooks/             toast hook
public/            logo, icons, manifest
next.config.mjs    output: 'export', distDir: 'dist', trailingSlash: true, unoptimized images
```

Every request carries `X-Visitor-Id`, which scopes the sandbox in public mode (see the [API](../docs/api.md#identity-and-access)). Server text is rendered as React text; the messages arrive pre-split into highlight `segments` and the UI does no offset arithmetic. `make hygiene` fails on `dangerouslySetInnerHTML`.

## Backend integration

`lib/api.ts` decides where the API is:

| Situation | API origin |
|---|---|
| Built app served by the backend | its own origin, `/api` |
| `npm run dev` (port 5173) | `http://localhost:8000` |
| `NEXT_PUBLIC_API_URL` set at build time | that origin, plus `/api` (give the host without the `/api` suffix) |

## Development

```bash
make run          # terminal 1: API on :8000, APP_MODE=dev (this is what enables CORS for :5173)
make web-dev      # terminal 2: cd web && npm run dev, hot reload on :5173
```

`FRONTEND_ORIGIN` (default `http://localhost:5173`) is the origin the API allows in `dev` mode. `npm ci` must have run once (`make web` does it) so `node_modules` exists. `npm run lint` runs ESLint with `.eslintrc.js`; it is not part of `make check`. There are no front-end unit tests; the UI is exercised by the CI `serve` job (build, serve, check `/dashboard/`, smoke test) and, indirectly, by the dashboard tests that cover the same API calls.

## Build and serve

```bash
make web          # cd web && npm ci --no-audit --no-fund && npm run build  ->  web/dist
make demo         # or make serve: FastAPI serves web/dist at /
```

`next build` runs the TypeScript check (`ignoreBuildErrors: false`), so a type error fails the build. The static export goes to `web/dist` (ignored by git). `trailingSlash: true` makes every route a directory with an `index.html`, which is what FastAPI's `StaticFiles(html=True)` serves. `create_app` mounts `web/dist` last, at `/`, after the API routes, only if the directory exists. Without a build, `/` returns 404 and only `/api` works. After every `git pull` on a host, run `make web` again (`make deploy` does).

The backend's `Content-Security-Policy` allows inline scripts (`script-src 'self' 'unsafe-inline'`) because the static export boots from inline `<script>` tags. Cross-site scripting protection therefore rests on React's escaping and on the ban on raw HTML injection.

`npm run start` (`next start`) is not used: the app is a static export and is served by the API.
