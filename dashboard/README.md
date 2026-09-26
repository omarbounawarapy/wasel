# Dashboard: COD Risk Queue on the API

The Streamlit UI from the standalone `cod-risk-poc` prototype (same six screens and look), rewired so that every read and every button goes through the FastAPI backend in `app/`. It is the spec's Streamlit dashboard (06 §1.5). The UI has no database, model or LLM of its own.

```
browser ──► dashboard/app.py ──HTTP──► app/ FastAPI  /api/*  ──► SQLite, worker, LLM chain, classifier, rules
            (api_client.py)            ▲
                                       └── /webhook/whatsapp ◄── Meta (customer messages)
```

## Run

```bash
make up        # from the repo root: API :8000 + dashboard :8501, Ctrl-C stops both

# or separately
make run       # API on :8000
make ui        # dashboard on :8501, against API_BASE_URL (default http://localhost:8000)
```

To deploy the dashboard on its own (a second service next to the API), install `dashboard/requirements.txt` and run `streamlit run dashboard/app.py` with `API_BASE_URL` set to the API's URL.

For live LLM scoring and WhatsApp, configure the **backend** (`APP_MODE=event`, `LLM_MODE=live`, `GROQ_API_KEY`, `WEBHOOK_ENABLED=true`, `WA_*`). The dashboard only needs `API_BASE_URL`.

## Screens → backend calls

| Screen | What it shows | Backend |
|---|---|---|
| Risk Queue | Tier counts, simulated savings banner, orders sorted by risk with the one-line reason | `GET /api/orders`, `GET /api/metrics/impact` |
| Order Detail | Conversation with flagged phrases highlighted, top factors chart, rules applied, pipeline trace, seller actions, the drafted message and Send, simulated customer reply (text or pin), score history with the reason diff | `GET /api/orders/{id}`, `POST …/actions`, `POST /api/drafts/{id}/send`, `POST /api/conversations/{id}/simulate-reply`, `POST …/rescore`, `POST …/try` (public mode) |
| Paste an order | Scores a pasted message live; for a message with an instruction aimed at the AI, scores a clean twin and compares | `POST /api/orders/ingest`, then polls `GET /api/orders/{id}` |
| WhatsApp inbox | Orders that came in through the webhook, with their threads | `GET /api/orders` (channel `whatsapp`), `GET /api/health` |
| Activity | The backend's event feed: messages, rescores, drafts, fallbacks, cache hits, injection flags, rejected webhooks | `GET /api/events` |
| Impact (simulated) | Refusal rate before/after, TND avoided, assumptions | `GET /api/metrics/impact` |

The sidebar shows the backend's health (mode, LLM chain and budget, WhatsApp send and webhook state) and polls `/api/events` every 5 s: a new customer message or rescore shows a toast and refreshes the page.

## What changed from the `cod-risk-poc` prototype

- Scores are the backend's 0–100 `final_score` and tiers `high / medium / low` (shown as High / Med / Low), not the old 0–1 probability.
- An order is a conversation, not an address + note pair: the detail page shows the thread with the backend's highlight segments.
- "Judge activity" became **Activity** (the backend's event feed). The backend has no LLM judge yet (S-3); drafts are static templates with rule checks.
- The seller's free-text reply box became **Simulate the customer's reply**: the backend has no free-text outbound send yet (S-2).
- The ROI sliders are gone: the savings figures come from the backend's `reports/impact.json`.

## Tests

```bash
make check                                  # includes these tests
python -m pytest tests/e2e/test_dashboard.py -q
```

The tests boot the real backend in-process (tmp database, frozen clock, LLM chain failing everywhere so new text takes the rules path) and drive the UI with Streamlit's `AppTest`. They cover every screen, the hero loop (reply → rescore → v2 lower than v1), send, seller actions, paste with the injection check, the "not an order" case, public-mode read-only samples and **Try this order**, a signed WhatsApp webhook message reaching the inbox, and the backend being down.
