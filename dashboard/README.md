# Streamlit dashboard

A Streamlit interface for Wasel in which every read and every button goes through the FastAPI backend in `src/wasel/`. It has no database, model or LLM of its own. The production interface is the Next.js app in [`web/`](../web/README.md), served by the API at `/`; this dashboard is a lighter alternative that needs no build step and runs with `make up`. Both are compared in [docs/interfaces.md](../docs/interfaces.md).

```
browser ──► dashboard/app.py ──HTTP──► FastAPI  /api/*  ──► SQLite, worker, LLM chain, classifier, rules
            (api_client.py)            ▲
                                       └── /webhook/whatsapp ◄── Meta (customer messages)
```

## Run

```bash
make up        # from the repository root: API :8000 + dashboard :8501, Ctrl-C stops both

# or separately
make run       # API on :8000
make ui        # dashboard on :8501, against API_BASE_URL (default http://localhost:8000)
```

`make up` starts the API with `APP_MODE=dev` unless you set another, waits for `/api/health`, then runs `streamlit run app.py` from `dashboard/` with `API_BASE_URL` pointing at it. `make ui` runs only the dashboard, so the API must already be up.

The dashboard has no login. It listens on `127.0.0.1` (`UI_HOST`, `--server.address`); set `UI_HOST=0.0.0.0` only behind an access-controlled tunnel or reverse proxy, because anyone who can reach it can read every order and press Approve, Cancel or Send.

To deploy the dashboard as its own service next to the API, install `dashboard/requirements.txt` (`streamlit`, `altair`, `httpx`, `pandas`, pinned) and run `streamlit run dashboard/app.py --server.address 127.0.0.1 --server.port 8501` with `API_BASE_URL` set to the API's URL. The dashboard does not need the `wasel` package, only network access to the API.

## Configuration

| Setting | Where | Effect |
|---|---|---|
| `API_BASE_URL` | environment | Backend URL, default `http://localhost:8000` |
| `API_TIMEOUT_S` | environment | Per-request timeout, default 30 s |
| `.streamlit/config.toml` | file | Light theme with the Wasel navy primary colour, headless server, usage statistics off |

Everything else, including LLM keys, WhatsApp settings and the mode, is configuration of the **backend**. The dashboard only reads what the backend reports in `/api/health` and shows it in the sidebar: mode, the LLM chain and its daily budget, WhatsApp send and webhook state, automatic sending, and the scoring queue.

Each Streamlit session creates its own visitor id (a UUID v4) and sends it as `X-Visitor-Id`. In public mode this means a browser reload starts a fresh sandbox; the web UI, which keeps its id in `localStorage`, does not.

## Screens and their backend calls

| Screen | What it shows | Backend |
|---|---|---|
| Risk Queue | Tier counts, the simulated-savings banner, and orders sorted by risk with the one-line reason | `GET /api/orders`, `GET /api/metrics/impact` |
| Order Detail | The conversation with flagged phrases highlighted, top-factors chart, rules applied, pipeline trace, seller actions, the drafted message with every check layer and Send, a simulated customer reply (text or map pin), and the score history with reason diffs | `GET /api/orders/{id}`, `POST .../actions`, `POST /api/drafts/{id}/send`, `POST /api/conversations/{id}/simulate-reply`, `POST .../rescore`, `POST .../try` (public mode) |
| Paste an order | Scores pasted text live. For text that looks like an instruction aimed at the AI, it scores a clean twin as well and compares. | `POST /api/orders/ingest`, then polls `GET /api/orders/{id}` |
| WhatsApp inbox | Orders that came in through the webhook, with their threads | `GET /api/orders` (channel `whatsapp`), `GET /api/health` |
| Activity | The backend's event feed | `GET /api/events` |
| Impact (simulated) | Refusal rate before and after, TND avoided, assumptions | `GET /api/metrics/impact` |
| AI quality | The offline and live evaluation reports, the drift and safety monitor, and recent LLM calls | `GET /api/eval`, `/api/monitor`, `/api/traces` |
| Hidden failures | Ranked silent failures with evidence, on the synthetic sets and on this app's orders | `GET /api/failures`, `GET /api/failures/sessions/{id}` |

The sidebar polls `/api/events` every five seconds; a new customer message or rescore shows a toast and refreshes the page. While an order is rescoring, its page shows a banner and refreshes itself until the new version arrives.

## Notes

- Scores are the backend's 0 to 100 `final_score`; tiers are `high`, `medium`, `low`, always shown with a symbol and text as well as colour.
- Customer replies are simulated from the order page ("Simulate the customer's reply"); real replies arrive through the WhatsApp webhook.
- Customer text reaches `unsafe_allow_html` only through `html.escape`.
- Savings figures come from `data/reports/impact.json` and are simulated.
- The code is `app.py` (all screens) and `api_client.py` (the HTTP client with one method per endpoint, and an `OVERRIDE` hook that tests use to route calls into an in-process backend).

## Tests

```bash
make check                                  # includes these tests
python -m pytest tests/e2e/test_dashboard.py -q
```

The tests boot the real backend in-process (temporary database, frozen clock, an LLM chain that fails everywhere so new text takes the rules path) and drive the dashboard with Streamlit's `AppTest`. They cover every screen, the sample scenario (reply, rescore, lower score), sending, seller actions, paste with the injection check, the "not an order" case, public-mode read-only samples and "Try this order", a signed WhatsApp webhook message reaching the inbox, the judge and classifier layers in the draft view, the AI quality and hidden-failure pages, and the backend being down.
