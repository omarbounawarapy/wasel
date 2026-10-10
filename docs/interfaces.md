# Web UI and analyst view (Streamlit)

Wasel has one seller product and one operator view. Both are separate programs that talk to the same HTTP [API](api.md) and hold no data or logic of their own: every order, score, draft and event comes from `/api`, and every button is a backend command. Neither is part of the Python backend process.

| | Web UI (`web/`): the seller product | Analyst view (`dashboard/`, Streamlit) |
|---|---|---|
| Technology | Next.js 16, React 19, Tailwind 4, Radix, static export | Streamlit 1.64, Altair, `httpx` |
| Audience | Sellers | Operators and analysts: evaluation, failures, monitoring, demos driven from Python |
| Runs as | static files served by the API at `/` | its own process (`make ui`) |
| Start | `make up` (builds on first run), or `make demo` / `make serve` | `make ui`, with the API already running |
| URL | http://localhost:8000/ (redirects to `/dashboard`) | http://localhost:8501 |
| Visitor id (public mode) | a UUID in the browser's `localStorage` (`cod_visitor_id`), so it survives reloads | a new UUID per Streamlit session, so a browser reload starts a fresh sandbox |
| Network | served by the API (`HOST`, default `127.0.0.1`) | `127.0.0.1` only (`UI_HOST`); it has no login |
| Backend address | its own origin (`/api`), or `NEXT_PUBLIC_API_URL` | `API_BASE_URL` |
| Detailed guide | [`web/README.md`](../web/README.md) | [`dashboard/README.md`](../dashboard/README.md) |
| Tested by | the CI `serve` job (built and served) | `tests/e2e/test_dashboard.py` in `make check` |

The web UI is the product. The analyst view is not for sellers: it shows the evaluation, failure and monitoring screens in more depth, and it runs without a build step.

## Screens

Both use the same names for the same functions:

| Function | Web UI and analyst view | API used |
|---|---|---|
| Orders to check, sorted by score | Orders to check | `GET /api/orders` |
| One order: messages with highlights, reason, factors, history, draft, actions, simulated reply | Order | `GET /api/orders/{id}`, `POST .../actions`, `POST /api/drafts/{id}/send`, `POST .../simulate-reply`, `POST .../rescore`, `POST .../try` |
| Add an order (paste) | Add an order | `POST /api/orders/ingest` |
| Orders that came through WhatsApp | WhatsApp messages | `GET /api/orders` (channel `whatsapp`) |
| Activity feed | Activity log | `GET /api/events` |
| Simulated impact | Money saved | `GET /api/metrics/impact` |
| Evaluation and drift | Quality checks, Live monitor, AI call log | `GET /api/eval`, `/api/monitor`, `/api/traces` |
| Silent failures | Silent failures | `GET /api/failures` |

Both draw evidence the same way: the server returns messages already split into `segments`, and the UIs render them with highlights. Customer text is never inserted as HTML (the web UI relies on React text nodes, and `make hygiene` bans `dangerouslySetInnerHTML`; the analyst view escapes it with `html.escape`).

## Live updates

Neither uses websockets. Both poll. The web UI reloads the queue and WhatsApp messages every 3 seconds, the activity page every 5 seconds and the health bar every 10 seconds, and the paste page polls the new order until it is scored. The analyst view polls `/api/events` every 5 seconds (a new event shows a toast and refreshes the page) and, on the order page, shows a banner and polls every 2 seconds while a rescore is pending.

## Choosing one

- Use the **web UI** for everything a seller does, for anything shared with other people, and for the hosted deployment. It must be built (`make web`, or `make up` on first run) and rebuilt after a pull.
- Use the **analyst view** for evaluation, failure analysis and monitoring in depth, for demos without Node, and for the end-to-end tests.
- The two are independent: you can run the dashboard against a deployed API (`API_BASE_URL=https://host make ui`), or point a development build of the web UI at another API with `NEXT_PUBLIC_API_URL`.
