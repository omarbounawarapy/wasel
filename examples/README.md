# Examples

Small Python scripts that drive the running API over HTTP, the same way the web UI does. Each prints what it does, needs no API key, and depends only on `httpx` (installed by `make setup`). They show the API contract in [docs/api.md](../docs/api.md) in action.

```bash
make run                                                  # API on :8000 in dev mode (or make up for API + dashboard)
.venv/bin/python examples/01_score_a_pasted_order.py
.venv/bin/python examples/02_customer_reply_rescore.py
.venv/bin/python examples/03_seller_workflow.py
API_BASE_URL=https://your-host .venv/bin/python examples/02_customer_reply_rescore.py   # any deployment
```

| Script | Shows | Endpoints |
|---|---|---|
| `01_score_a_pasted_order.py` | Paste raw Arabizi text, wait out the debounce, read the tier, action and reason | `POST /api/orders/ingest`, `GET /api/orders/{id}` |
| `02_customer_reply_rescore.py` | The sample order #2601 goes from HIGH 87 to LOW 16 after the customer replies with a full address, with the reason diff. In public mode it works on your own copy made with `try`. | `GET /api/orders`, `POST /api/orders/{id}/try` (public mode), `POST /api/conversations/{id}/simulate-reply` |
| `03_seller_workflow.py` | The queue, a person sending the drafted question, shipping a low-risk order, and the `409 INVALID_TRANSITION` for an action the state machine forbids | `GET /api/orders`, `POST /api/drafts/{id}/send`, `POST /api/orders/{id}/actions` |

Shared helpers are in `_client.py`: one `httpx` client with a fresh `X-Visitor-Id`, a health check that prints the API's mode and extractor, and a polling helper that waits for the worker to produce a given assessment version.

## What to expect

Example 02, on a fresh API:

```
before the reply:
  #2601  v1  HIGH 87  action=confirm  status=awaiting_reply  path=cascade_cache
customer replies: 'ey behi. Douar Ouled Ali, triq el jemaa, dar 14, el bab lazra9 9odem el pharmacie. ...'
after the reply:
  #2601  v2  LOW 16  action=ship  status=ready_to_ship  path=cascade_cache
  diff:   v1 87 → v2 16 · full address given ("Douar Ouled Ali, triq el jemaa, dar 14") −32 · ...
```

`path=cascade_cache` means the extraction came from the committed cache of recorded sample extractions, not from a live model call.

Example 01 scores new text, so its result depends on the extraction path. With no provider configured (the default) the text goes through the rules extractor and looks like this:

```
ingested #2610 (ord_...), scoring in ~5 s
  #2610  v1  MEDIUM 64  action=review  status=needs_review  path=rules
```

The rules path always ends in `needs_review` with `confidence=low`. With a live provider (`GROQ_API_KEY` exported in the shell that starts the API, or use `make up`/`make serve` with a `.env`) the same text goes to the model and the result carries `path=llm`.

Example 03 prints the queue, sends the first drafted question it finds (`delivery: recorded_only` unless WhatsApp sending is enabled), and ships a low-risk order.

## Modes

The examples work against the default development API. Public mode adds two constraints:

- Writes need an `X-Visitor-Id` header. The helper sends a new random UUID on every run, so each run has its own private sandbox.
- Sample orders are read-only. Example 02 detects this and makes a copy with `try`. Example 03 only acts on writable orders, and because each run is a new visitor it finds none in public mode, so run it against a `dev` API.

Set `API_BASE_URL` to point any of them at another host (default `http://localhost:8000`).
