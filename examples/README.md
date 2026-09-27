# Examples

Small scripts against the running API. Each one prints what it does; none needs an API key.

```bash
make run                                          # API on :8000 (or make up for API + dashboard)
.venv/bin/python examples/01_score_a_pasted_order.py
.venv/bin/python examples/02_customer_reply_rescore.py
.venv/bin/python examples/03_seller_workflow.py
API_BASE_URL=https://your-host .venv/bin/python examples/02_customer_reply_rescore.py   # any deployment
```

| Script | Shows | Endpoints |
|---|---|---|
| `01_score_a_pasted_order.py` | paste raw Arabizi text → the worker scores it after the debounce → tier, action, reason | `POST /api/orders/ingest`, `GET /api/orders/{id}` |
| `02_customer_reply_rescore.py` | the hero order goes HIGH 87 → LOW 16 after the customer replies with a full address, with the reason diff | `POST …/try` (public mode), `POST /api/conversations/{id}/simulate-reply` |
| `03_seller_workflow.py` | the queue, a human sending the drafted question, ship, and the 409 for an action the state machine forbids | `GET /api/orders`, `POST /api/drafts/{id}/send`, `POST …/actions` |

Without `GROQ_API_KEY`, seeded orders use recorded LLM results (`path=cascade_cache`) and new text goes to the rules extractor (`path=rules`, which always sends the order to review). With a key, `01` uses the live LLM chain.

Every write sends an `X-Visitor-Id` header (`_client.py`). Public mode requires it and gives each visitor a private sandbox, so in public mode `03` only sees writable orders created by the same visitor.
