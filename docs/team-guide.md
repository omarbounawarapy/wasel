# Team guide: where to work and how

For Z-Team. Use it to find which files a change touches, who owns them, and how to get the change onto `main`. For how the code runs, see [architecture.md](architecture.md). Live status and open points are in [`STATUS.md`](../STATUS.md).

- [1. Who owns what](#1-who-owns-what)
- [2. "I want to change…" → go here](#2-i-want-to-change--go-here)
- [3. How lanes meet: the contracts](#3-how-lanes-meet-the-contracts)
- [4. From branch to `main`](#4-from-branch-to-main)
- [5. Which tests cover what](#5-which-tests-cover-what)
- [6. Day-one setup](#6-day-one-setup)

## 1. Who owns what

Folder = owner. Only the owning lane edits its folders; everyone else asks. Omar merges to `main`. Source: [01 §1](council-spec/01-architecture-contracts.md#1-repository-tree-and-ownership).

```mermaid
flowchart LR
    subgraph FEDI["🗣️ Fedi · story, language, scope"]
        direction TB
        F1["data/phrase_banks.yaml<br/>data/zones.yaml additions"]
        F2["data/templates/outbound.yaml<br/>wording · event_text copy"]
        F3["README prose · pitch<br/>video · FEDI.md"]
    end

    subgraph MONT["🖥️ Montassar · frontend + infra + CI"]
        direction TB
        M1["dashboard/<br/>Streamlit UI"]
        M2["Makefile · Dockerfile<br/>.github/workflows/ci.yml"]
        M3["app/settings.py · app/mode.py<br/>.env.example"]
        M4["hosting · mode switches<br/>smoke · mocks/"]
    end

    subgraph JESSER["⚙️ Jesser · backend + WhatsApp"]
        direction TB
        J1["app/db/<br/>schema · repo · seed · purge"]
        J2["app/api/<br/>routes · models = API contract"]
        J3["app/ingress/<br/>store_inbound · WhatsApp"]
        J4["app/worker.py · app/state.py<br/>app/main.py · clock · ids"]
        J5["requirements*.txt"]
    end

    subgraph OMAR["🧠 Omar · AI/ML core · merges"]
        direction TB
        O1["app/llm/<br/>provider chain"]
        O2["app/extraction/<br/>window · repair · evidence<br/>injection · rules extractor"]
        O3["app/scoring/<br/>score_order · model · reasons"]
        O4["app/outbound/<br/>templates · prefilter · route"]
        O5["ml/ · models/ · reports/"]
        O6["prompts/ · schemas/<br/>scoring.yaml<br/>app/contracts.py"]
    end

    classDef omar fill:#dbeafe,stroke:#1d4ed8,color:#0f172a
    classDef jesser fill:#dcfce7,stroke:#15803d,color:#0f172a
    classDef mont fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef fedi fill:#fce7f3,stroke:#be185d,color:#0f172a
    class O1,O2,O3,O4,O5,O6 omar
    class J1,J2,J3,J4,J5 jesser
    class M1,M2,M3,M4 mont
    class F1,F2,F3 fedi
```

The lanes hand work to each other only through the contracts in [§3](#3-how-lanes-meet-the-contracts): Fedi → Omar (phrases, eval windows), Omar → Jesser (`score_order()`, `make_draft()`), Jesser → Montassar (the `/api` JSON and mocks).

## 2. "I want to change…" → go here

```mermaid
flowchart LR
    Q{"What are you changing?"}

    Q --> A["A score, tier cut-off,<br/>weight or reason text"]
    Q --> B["What the LLM extracts<br/>or how it is prompted"]
    Q --> C["An endpoint, a field in<br/>the JSON, or a status"]
    Q --> D["How WhatsApp messages<br/>come in or go out"]
    Q --> E["A screen, a button<br/>or UI copy"]
    Q --> F["Deploy, env vars,<br/>CI or make targets"]
    Q --> G["Darija / Arabizi / French<br/>phrases or message wording"]

    A --> A1["scoring.yaml first<br/>then app/scoring/<br/>test: tests/unit/test_scoring.py<br/>+ golden hero · Omar"]
    B --> B1["prompts/ + schemas/<br/>app/extraction/ · app/llm/<br/>bump PROMPT_VERSION<br/>test: tests/unit/test_extraction.py · Omar"]
    C --> C1["app/api/models.py (contract)<br/>app/api/routes.py · app/state.py<br/>re-run make mocks<br/>test: tests/integration/test_backend.py · Jesser"]
    D --> D1["app/ingress/ · routes_webhook.py<br/>test: tests/integration/test_whatsapp.py<br/>fixtures: tests/fixtures/whatsapp/ · Jesser"]
    E --> E1["dashboard/app.py<br/>dashboard/api_client.py<br/>test: tests/e2e/test_dashboard.py · Montassar"]
    F --> F1["Makefile · Dockerfile<br/>.github/workflows/ci.yml<br/>app/settings.py · .env.example · Montassar"]
    G --> G1["data/phrase_banks.yaml<br/>data/templates/outbound.yaml<br/>then make generate + make train<br/>Fedi → Omar"]

    classDef omar fill:#dbeafe,stroke:#1d4ed8,color:#0f172a
    classDef jesser fill:#dcfce7,stroke:#15803d,color:#0f172a
    classDef mont fill:#fef3c7,stroke:#b45309,color:#0f172a
    classDef fedi fill:#fce7f3,stroke:#be185d,color:#0f172a
    class A1,B1 omar
    class C1,D1 jesser
    class E1,F1 mont
    class G1 fedi
```

Colours match the lanes above: blue Omar, green Jesser, amber Montassar, pink Fedi.

Before you touch a **contract file**, tell the lane that consumes it (see §3).

## 3. How lanes meet: the contracts

Each lane codes against a typed boundary, not against another lane's internals. Stubs and mocks let everyone work before the neighbour is finished.

```mermaid
flowchart LR
    subgraph ML["Omar"]
        SO["score_order(ScoreInput) → ScoreResult<br/>make_draft(DraftRequest) → DraftRecord"]
    end
    subgraph BE["Jesser"]
        WK["worker.py calls the Scorer / Drafter<br/>(stub: app/scoring/stub.py)"]
        AM["app/api/models.py<br/>Pydantic = the JSON contract"]
    end
    subgraph FE["Montassar"]
        UI["dashboard/api_client.py<br/>(works against mocks/*.json)"]
    end

    CT[["app/contracts.py<br/>Scorer, Drafter, LLMClient,<br/>ExtractionCache, UsageMeter, Clock"]]

    SO -. implements .-> CT
    WK -. depends on .-> CT
    WK --> AM
    AM -- "make mocks → mocks/*.json" --> UI
```

| Contract file | Owner | Consumer to warn |
|---|---|---|
| `app/contracts.py` | Omar (Jesser reviews) | Jesser |
| `scoring.yaml` | Omar | everyone (the golden test will move) |
| `app/api/models.py`, `mocks/*.json`, `app/db/schema.sql` | Jesser | Montassar |
| `Makefile`, `ci.yml`, `tests/conftest.py` | Montassar | everyone |
| `requirements*.txt` | Jesser | everyone |

## 4. From branch to `main`

```mermaid
flowchart TD
    A["git switch -c &lt;name&gt;/&lt;task&gt;<br/>e.g. jesser/sandbox-visibility"] --> B["code + its tests<br/>(missing test = visible skip with reason)"]
    B --> C{"touches a<br/>contract file?"}
    C -- yes --> C1["message the consuming lane"] --> D
    C -- no --> D["git rebase main"]
    D --> E["make check<br/>hygiene + ruff + offline tests, no keys"]
    E -- red --> B
    E -- green --> F["open a PR<br/>(template asks lane, tests, contracts)"]
    F --> G["CI: same make check<br/>+ image boots in public mode"]
    G -- red --> B
    G -- green --> H["Omar merges"]
    H --> I["on main: make check && make seed && make smoke"]
    I -- red --> STOP["stop the line:<br/>the last merge's author fixes main<br/>before anyone else merges"]
```

Prompt edits have one more rule: bump `PROMPT_VERSION` and rebuild the extraction cache (`make warm`), because the prompt is locked by sha256 in the tests.

## 5. Which tests cover what

`make check` runs all of this offline in under a couple of minutes. Nothing in CI needs an API key; tests marked `live` run only with `RUN_LIVE=1`.

```mermaid
flowchart LR
    U["tests/unit/<br/>extraction · scoring · ml"] --> PURE["pure functions,<br/>no DB, no HTTP"]
    I["tests/integration/<br/>backend · whatsapp"] --> APPDB["the app in-process<br/>+ SQLite + worker"]
    E["tests/e2e/<br/>hero · injection · dashboard"] --> FULL["full flows, incl. the<br/>Streamlit UI against the API"]
    G["tests/golden/hero.json"] --> HERO["HIGH 87 → LOW 16<br/>must not drift silently"]
    FX["tests/fixtures/<br/>hero/, whatsapp/"] -.-> I
    FX -.-> E
```

Run one area while you work: `.venv/bin/pytest tests/unit/test_scoring.py -q`. Run `make check` before you push.

## 6. Day-one setup

```bash
git clone https://github.com/omarbounawarapy/hackathon && cd hackathon
make setup          # .venv with pinned deps
make check          # must be green before you change anything
make up             # API :8000 + dashboard :8501, seeded
.venv/bin/python examples/02_customer_reply_rescore.py    # see the core loop from the API
```

Keys are optional. Copy `.env.example` to `.env` and set `GROQ_API_KEY` for live extraction; `.env` is gitignored and `make hygiene` fails if a key-shaped string gets committed.
