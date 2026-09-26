# Frontend: COD Risk Queue on the `poc/` backend

The Streamlit UI from `cod-risk-poc/` (same six screens and look), rewired so that every read and every button goes through the `poc/` FastAPI backend. The UI has no database, model or LLM of its own.

```
browser ──► frontend/streamlit_app.py ──HTTP──► poc/ FastAPI  /api/*  ──► SQLite, worker, LLM chain, classifier, rules
                     (api.py)                        ▲
                                                     └── /webhook/whatsapp ◄── Meta (customer messages)
```

## Run

```bash
# 1. backend (see poc/README.md): public demo, no keys
cd poc && make demo                                    # API on :8000

# 2. frontend, in a second terminal
pip install -r frontend/requirements.txt
API_BASE_URL=http://localhost:8000 streamlit run frontend/streamlit_app.py
```

For live LLM scoring and WhatsApp, configure the **backend** (`APP_MODE=event`, `LLM_MODE=live`, `GROQ_API_KEY`, `WEBHOOK_ENABLED=true`, `WA_*`). The frontend only needs `API_BASE_URL`.

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

## What changed from `cod-risk-poc/app.py`

- Scores are the backend's 0–100 `final_score` and tiers `high / medium / low` (shown as High / Med / Low), not the old 0–1 probability.
- An order is a conversation, not an address + note pair: the detail page shows the thread with the backend's highlight segments.
- "Judge activity" became **Activity** (the backend's event feed). The backend has no LLM judge yet (S-3); drafts are static templates with rule checks.
- The seller's free-text reply box became **Simulate the customer's reply**: the backend has no free-text outbound send yet (S-2).
- The ROI sliders are gone: the savings figures come from the backend's `reports/impact.json`.

## Tests

```bash
pip install -r poc/requirements.txt -r frontend/requirements.txt pytest
python -m pytest frontend/tests -q
```

The tests boot the real backend in-process (tmp database, frozen clock, LLM chain failing everywhere so new text takes the rules path) and drive the UI with Streamlit's `AppTest`. They cover every screen, the hero loop (reply → rescore → v2 lower than v1), send, seller actions, paste with the injection check, the "not an order" case, public-mode read-only samples and **Try this order**, a signed WhatsApp webhook message reaching the inbox, and the backend being down.
