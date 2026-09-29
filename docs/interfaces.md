# Web UI and Streamlit dashboard

Wasel has two seller-facing interfaces. They are separate programs that talk to the same HTTP [API](api.md) and hold no data or logic of their own: every order, score, draft and event comes from `/api`, and every button is a backend command. Neither is part of the Python backend process.

| | Web UI (`web/`) | Streamlit dashboard (`dashboard/`) |
|---|---|---|
| Technology | Next.js 16, React 19, Tailwind 4, Radix, static export | Streamlit 1.64, Altair, `httpx` |
| Runs as | static files served by the API at `/` | its own process (`make ui`, or `make up`) |
| Start | `make web`, then `make demo` or `make serve` | `make up`, or `make run` and `make ui` |
| URL | http://localhost:8000/ (redirects to `/dashboard`) | http://localhost:8501 |
| Visitor id (public mode) | a UUID in the browser's `localStorage` (`cod_visitor_id`), so it survives reloads | a new UUID per Streamlit session, so a browser reload starts a fresh sandbox |
| Backend address | its own origin (`/api`), or `NEXT_PUBLIC_API_URL` | `API_BASE_URL` |
| Detailed guide | [`web/README.md`](../web/README.md) | [`dashboard/README.md`](../dashboard/README.md) |
| Tested by | the CI `serve` job (built and served) | `tests/e2e/test_dashboard.py` in `make check` |

The web UI is the intended production interface. The dashboard is a lighter alternative that needs no build step and is convenient for demos and for driving the backend from Python.

## Screens

Both show the same functions under different names:

| Function | Web UI | Dashboard | API used |
|---|---|---|---|
| Risk queue, sorted by score | Orders to check | Risk Queue | `GET /api/orders` |
| One order: messages with highlights, reason, factors, history, draft, actions, simulated reply | Order page | Order Detail | `GET /api/orders/{id}`, `POST .../actions`, `POST /api/drafts/{id}/send`, `POST .../simulate-reply`, `POST .../rescore`, `POST .../try` |
| Paste an order | Add an order | Paste an order | `POST /api/orders/ingest` |
| Orders that came through WhatsApp | WhatsApp messages | WhatsApp inbox | `GET /api/orders` (channel `whatsapp`) |
| Activity feed | Activity log | Activity | `GET /api/events` |
| Simulated impact | Money saved | Impact (simulated) | `GET /api/metrics/impact` |
| Evaluation and drift | Quality checks, Live monitor, AI call log | AI quality | `GET /api/eval`, `/api/monitor`, `/api/traces` |
| Silent failures | Silent failures | Hidden failures | `GET /api/failures` |

Both draw evidence the same way: the server returns messages already split into `segments`, and the UIs render them with highlights. Customer text is never inserted as HTML (the web UI relies on React text nodes, and `make hygiene` bans `dangerouslySetInnerHTML`; the dashboard escapes it with `html.escape`).

## Live updates

Neither uses websockets. Both poll. The web UI reloads the queue and the WhatsApp inbox every 3 seconds, the activity page every 5 seconds and the health bar every 10 seconds, and the paste page polls the new order until it is scored. The dashboard polls `/api/events` every 5 seconds (a new event shows a toast and refreshes the page) and, on the order page, shows a banner and polls every 2 seconds while a rescore is pending.

## Choosing one

- Use the **web UI** for anything shared with other people, and for the hosted deployment. It must be built (`make web`) and rebuilt after a pull.
- Use the **dashboard** for local development of the backend, demos without Node, and the end-to-end tests.
- The two are independent: you can run the dashboard against a deployed API (`API_BASE_URL=https://host make ui`), or point a development build of the web UI at another API with `NEXT_PUBLIC_API_URL`.
