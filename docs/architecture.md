# Architecture

How the code is laid out and how an order moves through it. The diagrams follow the code on `main`. Where they simplify, the spec section that holds the full detail is linked. For who works where, see the [team guide](team-guide.md).

- [1. The system on one page](#1-the-system-on-one-page)
- [2. One message, end to end](#2-one-message-end-to-end)
- [3. Inside `score_order`](#3-inside-score_order)
- [4. The LLM chain](#4-the-llm-chain)
- [5. Order lifecycle](#5-order-lifecycle)
- [6. Drafting the customer message](#6-drafting-the-customer-message)
- [7. Modes](#7-modes)
- [8. Offline ML pipeline](#8-offline-ml-pipeline)

## 1. The system on one page

A single FastAPI process owns the SQLite database. Every way an order can arrive goes through the same `store_inbound()`, and the background worker does all the scoring. The dashboard only talks HTTP.

```mermaid
flowchart LR
    subgraph in["Ways in"]
        WA["WhatsApp<br/>(Meta webhook)"]
        PASTE["Paste / CSV"]
        SIM["Simulated reply<br/>and 'Try this order'"]
    end

    subgraph api["FastAPI · app/ (one process)"]
        direction TB
        ROUTES["/api/* routes<br/>app/api/"]
        HOOK["/webhook/whatsapp<br/>app/api/routes_webhook.py"]
        INGEST["store_inbound()<br/>app/ingress/ingest.py"]
        WORKER["worker, 1 s tick<br/>app/worker.py"]
        SCORE["score_order()<br/>app/scoring/"]
        DRAFT["make_draft()<br/>app/outbound/"]
    end

    DB[("SQLite WAL<br/>var/app.db")]
    LLM["Groq → Gemini<br/>app/llm/"]
    UI["Streamlit dashboard<br/>dashboard/"]
    SELLER(("Seller"))

    WA --> HOOK --> INGEST
    PASTE --> ROUTES
    SIM --> ROUTES
    ROUTES --> INGEST
    INGEST -- "message stored,<br/>rescore armed" --> DB
    WORKER -- "picks due orders" --> DB
    WORKER --> SCORE
    SCORE <--> LLM
    WORKER --> DRAFT
    WORKER -- "new assessment version,<br/>status, draft" --> DB
    ROUTES -- reads --> DB
    SELLER --> UI -- "HTTP only" --> ROUTES

    classDef store fill:#eef,stroke:#557;
    class DB store;
```

Three rules hold everywhere:

- **FastAPI is the only writer.** The dashboard never touches the database.
- **One ingestion path.** WhatsApp, paste, CSV, simulated replies and seeding all call `store_inbound()`, so each fallback runs the real pipeline.
- **The LLM extracts, code decides.** The LLM fills a strict 12-field schema and quotes the customer. The XGBoost model and the rules in `scoring.yaml` produce every number.

## 2. One message, end to end

A new message arms a debounced rescore (a newer message pushes it back). The worker claims the order, scores it, saves a new assessment version, moves the order through the state machine and, when a question is needed, drafts one. A person sends it.

```mermaid
sequenceDiagram
    autonumber
    participant C as Customer
    participant I as Ingress<br/>(webhook / paste / simulate)
    participant DB as SQLite
    participant W as Worker (1 s)
    participant S as score_order()
    participant L as LLM chain
    participant D as make_draft()
    participant U as Seller (dashboard)

    C->>I: message
    I->>DB: store message, link to open order,<br/>pending_rescore_at = now + debounce
    Note over DB: status unchanged,<br/>rescore_state = debouncing
    W->>DB: claim due order (compare-and-set)
    W->>S: ScoreInput (window, order, customer, prior assessment)
    S->>DB: extraction cache lookup
    alt cache miss
        S->>L: extract (strict JSON schema)
        L-->>S: 12 fields + quotes
    end
    S-->>W: ScoreResult (score, tier, action, reasons)
    W->>DB: assessment vN+1, next_status(), events
    opt medium / high and no unsent draft
        W->>D: DraftRequest
        D-->>W: template + prefilter + route
        W->>DB: outbound_drafts row
    end
    U->>DB: GET /api/orders (poll)
    U->>DB: POST /api/drafts/{id}/send (a human clicks)
    Note over C,U: the customer's reply starts the loop again → v2 with a reason diff
```

Spec: [01 §5.1–5.3](council-spec/01-architecture-contracts.md#5-order-state-machine).

## 3. Inside `score_order`

`app/scoring/score_order.py` is a pure function of its input plus injected seams (cache, LLM client, usage meter, config). That is what lets the tests run it without a network.

```mermaid
flowchart TD
    A["ScoreInput"] --> B["build window<br/>12 msgs / 2,000 chars, [CUSTOMER]/[SELLER] lines<br/>extraction/window.py"]
    B --> C{"no_reply_timeout?"}
    C -- yes --> C1["reuse prior extraction, +15"] --> H
    C -- no --> D{"cache hit?<br/>db/cache.py"}
    D -- yes --> E
    D -- no --> D1["LLM chain → rules fallback<br/>llm/client.py"] --> E
    E["repair: clamp and truncate, never reject<br/>extraction/repair.py"] --> F["evidence: every quote must exist in the<br/>original text, else dropped<br/>extraction/evidence.py"]
    F --> G["injection guard + cross-field checks<br/>extraction/injection.py · cross_field.py"]
    G --> G1{"is_order?"}
    G1 -- no --> X["no assessment<br/>(event extraction.not_order)"]
    G1 -- yes --> H["resolve product, price, zone<br/>structured > catalog / gazetteer > default<br/>scoring/catalog.py"]
    H --> I["6 features → monotone XGBoost<br/>ml/features.py · scoring/model.py"]
    I --> J["reply adjustments, tier, action, confidence<br/>scoring.yaml"]
    J --> K["reason, reason_short, reason_diff<br/>scoring/reason.py"]
    K --> R["ScoreResult"]
```

Tiers are fixed cut-offs from `scoring.yaml`: **low < 35 ≤ medium < 65 ≤ high**. Spec: [02 LLM layer](council-spec/02-llm-layer.md), [03 Data + ML](council-spec/03-data-ml.md).

## 4. The LLM chain

`ChainClient` in `app/llm/client.py` tries each step once (no retries) and records every attempt. A daily cap or a failure never becomes an HTTP error; the order drops to the rules path and goes to review.

```mermaid
flowchart LR
    S(["extract()"]) --> G1["Groq<br/>EXTRACT_MODEL<br/>gpt-oss-120b"]
    G1 -- ok --> OK(["path = llm<br/>(cached)"])
    G1 -- "error / timeout" --> G2["Groq<br/>FALLBACK_MODEL<br/>gpt-oss-20b"]
    G2 -- ok --> FB(["path = fallback_model"])
    G2 -- "error" --> GM["Gemini<br/>if GEMINI_ENABLED"]
    GM -- ok --> FP(["path = fallback_provider"])
    GM -- "error / off" --> R["rules extractor<br/>extraction/rules_extractor.py"]
    CAP{{"daily / visitor<br/>cap reached"}} -.-> R
    R --> RV(["path = rules<br/>→ needs_review"])
```

`LLM_MODE` swaps the chain for tests and drills: `live`, `replay`, `fail_primary`, `fail_groq`, `fail_all`. Only `path = llm` results are cached; fallbacks never are.

## 5. Order lifecycle

Statuses come from `next_status()` (automatic, after each scoring) and `ACTIONS` (seller clicks), both in `app/state.py`. An action that is not allowed from the current status returns `409 INVALID_TRANSITION` with the allowed list.

```mermaid
stateDiagram-v2
    [*] --> collecting: first message
    collecting --> ready_to_ship: scored LOW
    collecting --> awaiting_reply: scored MEDIUM / HIGH<br/>(draft created)
    collecting --> needs_review: rules path, injection,<br/>order change, ambiguous

    awaiting_reply --> ready_to_ship: reply rescored LOW
    awaiting_reply --> needs_review: no reply in time,<br/>ambiguous, rules path
    awaiting_reply --> cancelled: customer declines

    needs_review --> ready_to_ship: rescored LOW
    needs_review --> awaiting_reply: seller · request_confirmation

    awaiting_reply --> ready_to_ship: seller · approve
    needs_review --> ready_to_ship: seller · approve

    ready_to_ship --> needs_review: risk rose after approval
    ready_to_ship --> shipped: seller · ship
    shipped --> delivered: seller · mark_delivered
    shipped --> refused: seller · mark_refused

    delivered --> [*]
    refused --> [*]
    cancelled --> [*]
    note right of cancelled
        seller · cancel works from
        any non-terminal status
    end note
```

A message on a terminal order opens a new order. The full first-match-wins table is in [01 §5.2](council-spec/01-architecture-contracts.md#5-order-state-machine).

## 6. Drafting the customer message

Today the draft is a static template (`data/templates/outbound.yaml`) in the customer's language, checked by a prefilter and routed. The LLM rewrite and judge (spec item S-3, `DRAFT_LLM`) are **not built**: the prompts and schemas exist, the code path raises if enabled.

```mermaid
flowchart LR
    T["template_id from tier / flags<br/>(e.g. T_ADDRESS)"] --> L["language from the<br/>customer's last message"]
    L --> R["render slots<br/>outbound/templates.py"]
    R --> P["prefilter<br/>outbound/prefilter.py"]
    P --> RT{"route<br/>outbound/route.py"}
    RT --> A["auto_send<br/>(small order, caps)"]
    RT --> N["needs_review"]
    RT --> B["blocked"]
    N --> H(["seller clicks Send"])
    A --> H2(["sent only if wa_send is on"])
```

## 7. Modes

`APP_MODE` decides what is safe to expose. Missing or unknown means `public`.

| | `dev` | `event` | `public` (default) |
|---|---|---|---|
| WhatsApp send | `WA_SEND_ENABLED` | `WA_SEND_ENABLED` | forced off |
| Webhook mounted | if enabled and secrets set | same | never |
| Who sees what | everything | everything | seeded rows + your own sandbox (`X-Visitor-Id`) |
| Seeded rows writable | yes | yes | no (409, use "Try this order") |
| No-reply timeout | on | on | off |
| Sandbox purge | off | off | every 10 min, 2 h TTL |
| `SEED_ON_BOOT=auto` | if empty | if empty | always (fresh DB) |

`GET /api/health` always reports `mode`, `wa_send` and `webhook`, and CI checks that the Docker image boots as public with both off. Spec: [01 §6](council-spec/01-architecture-contracts.md#6-deploy-topology-modes-and-the-switch-runbook), [04 Security](council-spec/04-security-public-mode.md).

## 8. Offline ML pipeline

Nothing here runs at request time. The app only loads `models/` and reads `reports/impact.json`.

```mermaid
flowchart LR
    PB["data/phrase_banks.yaml<br/>catalog.yaml · zones.yaml"] --> GEN["make generate<br/>ml/generate.py<br/>(no LLM calls)"]
    GEN --> CSV["data/synth_v1.csv<br/>10,000 synthetic rows"]
    CSV --> TR["make train<br/>ml/train.py"]
    TR --> M["models/<br/>XGBoost + card"]
    TR --> REP["reports/train_metrics.json<br/>reports/impact.json"]
    TR --> GOLD["tests/golden/hero.json"]
    M --> APP(["app/scoring/model.py"])
    REP --> APP2(["GET /api/metrics/impact"])
```

All data is synthetic. Holdout AUC is 0.784 (`reports/train_metrics.json`), and the impact figures are simulated from the same holdout.
