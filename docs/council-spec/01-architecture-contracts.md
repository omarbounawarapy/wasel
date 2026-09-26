# Architecture, contracts, schema, API, deploy

> Council final spec — Architect lens (Round 3). Source of truth for its area. Where this file conflicts with a **Conductor ruling** in [README.md](README.md#conductor-rulings), the ruling wins. Unverified external facts are marked [VERIFY].


### 1. Repository tree and ownership

Folder = owner. Anything not listed is edited only by its lane. Omar merges to `main` after `make check`.

```
hackathon/                                    (existing repo; docs stay at root)
├─ README.md                  Fedi (prose) · Omar (numbers, only from reports/*.json) · Montassar (URL, badge)
├─ PRD.md SYSTEM_DESIGN.md execution_plan.md hackathon_playbook.md
├─ handoff.md                 Fedi: add a one-line "Superseded by PRD/SYSTEM_DESIGN/execution_plan" header
├─ Makefile                   Montassar  (setup run test lint hygiene check seed demo-reset train record eval drill smoke capture)
├─ Dockerfile .dockerignore   Montassar
├─ .github/workflows/ci.yml   Montassar  (make check, no API keys)
├─ .gitignore                 Montassar  (+ var/ *.db *.db-wal *.db-shm node_modules/ web/dist/ web/public/snapshot/*.json .env*, !.env.example; Skeptic App. C)
├─ .env.example               Montassar  (every key from §7, secrets empty)
├─ requirements.txt requirements-dev.txt .python-version(3.11)   Jesser (pins with ==, resolved on 26 Sept)
├─ pyproject.toml             Montassar  (pytest markers, ruff config incl. banned-api TID251 for datetime.now/utcnow outside app/clock.py)
├─ scoring.yaml               Omar
│
├─ app/
│  ├─ contracts.py            Omar merges, Jesser reviews. Types FROZEN 10:30, fields FROZEN 12:00 (§2)
│  ├─ clock.py                Jesser    Clock protocol, SystemClock, FrozenClock, utc_iso(), parse_utc()
│  ├─ ids.py                  Jesser    new_id() -> ULID [VERIFY python-ulid package name]
│  ├─ settings.py             Montassar pydantic-settings; fails fast naming the missing var
│  ├─ mode.py                 Montassar APP_MODE resolution, effective flags (§6.2), visitor-id dependency
│  ├─ main.py                 Jesser    create_app(settings, clock, llm, worker_enabled) factory; routers; StaticFiles(web/dist)
│  ├─ db/
│  │  ├─ schema.sql           Jesser    §3, the whole DDL
│  │  ├─ conn.py              Jesser    connect(path) per thread; PRAGMAs
│  │  ├─ repo.py              Jesser    all SQL except purge/seed
│  │  ├─ cache.py             Jesser    SqliteExtractionCache (implements contracts.ExtractionCache)
│  │  ├─ usage.py             Jesser    SqliteUsageMeter (implements contracts.UsageMeter)
│  │  ├─ seed.py              Jesser    seed_catalog(), seed_cache(), seed_conversation(fixture, sandbox_id)
│  │  └─ purge.py             Jesser    purge_sandboxes(now), reset_all()
│  ├─ ingress/
│  │  ├─ ingest.py            Jesser    store_inbound(): the ONE path for whatsapp/csv/paste/simulate/seed
│  │  ├─ whatsapp.py          Jesser    verify_signature(), parse_payload() (pure)
│  │  └─ whatsapp_send.py     Jesser    Graph send; never imported when effective wa_send is false
│  ├─ worker.py               Jesser    process_due(conn, now, scorer, drafter) + run_loop()
│  ├─ state.py                Jesser    next_status(), ACTIONS table (§5)
│  ├─ api/
│  │  ├─ models.py            Jesser    Pydantic request/response = THE API CONTRACT (§4)
│  │  ├─ projections.py       Jesser    detail projection, segments builder (uses extraction.normalize)
│  │  ├─ event_text.py        Jesser code, Fedi copy   event type -> (level, title, detail)
│  │  └─ routes_orders.py routes_conversations.py routes_drafts.py routes_events.py
│  │     routes_health.py routes_admin.py routes_webhook.py              Jesser
│  ├─ llm/                    Omar      (Oracle D6/D8)
│  │  ├─ base.py              TaskSpec, Attempt, LLMError subclasses
│  │  ├─ client.py            ChainClient (live), ReplayClient, FailingClient; selected by LLM_MODE
│  │  ├─ groq_backend.py      max_retries=0, strict json_schema
│  │  ├─ gemini_backend.py    S-6; google-genai [VERIFY package]
│  │  └─ schema_gemini.py     to_gemini_schema()  (ships Saturday with its offline test)
│  ├─ extraction/             Omar
│  │  ├─ window.py            12 msg / 2,000 char cap, [CUSTOMER]/[SELLER] lines, input_hash
│  │  ├─ normalize.py         normalize_with_map(), mask_phones() (length-preserving)
│  │  ├─ repair.py            clamp/truncate, never reject (Craftsman F4)
│  │  ├─ evidence.py          locate() per message, msg_idx, tone gate
│  │  ├─ cross_field.py       exact guard (NUM helper from ml/features.py), pin override
│  │  ├─ cascade.py           S-5 (ack/pin/decline); cache lookup is NOT here (it is Must, in score_order)
│  │  └─ rules_extractor.py   last-resort extractor
│  ├─ scoring/                Omar
│  │  ├─ score_order.py       score_order(), make_scorer()
│  │  ├─ stub.py              same signature, fixed high-tier result with one span
│  │  ├─ model.py             XGBoost load + pred_contribs
│  │  ├─ reason.py            reason, reason_short, reason_diff (FSI/PDI around quotes)
│  │  ├─ catalog.py           fuzzy match (rapidfuzz ≥ 80)
│  │  └─ config.py            ScoringConfig loader + config_hash
│  └─ outbound/               Omar      templates.py prefilter.py route.py make_draft.py (Must, static)
│                                       rewrite.py judge.py (S-3)
├─ ml/                        Omar      (Alchemist B.1)
│  ├─ features.py             FEATURES, NUM helper, zone_from_text, resolve_flags, S(), p_true()
│  ├─ generate.py             python -m ml.generate --seed 20260927 --n 10000 (imports no LLM SDK)
│  ├─ train.py
│  └─ text_clf.py             S-11: TF-IDF char n-grams + logistic regression (03 §14), imports no LLM SDK
├─ prompts/                   Omar (Fedi checks dialect)  extract_v1.system.txt extract_v1.fewshot.jsonl
│                             rewrite_v1.system.txt judge_v1.system.txt
├─ schemas/                   Omar      order_extraction_v1.json (12 fields) outbound_rewrite_v1.json outbound_judge_v1.json
├─ data/
│  ├─ catalog.yaml            Omar      ~15 products: product_id, name, aliases[], price_tnd, category
│  ├─ zones.yaml              Omar (Fedi extends)  urban/suburban/rural keyword lists
│  ├─ phrase_banks.yaml       Fedi      (≥30% of each cell tagged eval_only)
│  ├─ templates/outbound.yaml Fedi      T_CONFIRM/T_ADDRESS/T_PREPAY/T_ACK × fr/darija_arabic_script/arabizi + language fallback map
│  ├─ synth_v1.csv synth_v1.meta.json   Omar (generated, committed)
│  └─ seed/
│     ├─ demo_seed.json       Fedi texts, Jesser shape (§3.3)
│     └─ extraction_cache.jsonl  Omar  (scripts/warm_cache.py, dev key)
├─ eval/sets/                 Fedi      native_windows.jsonl labels.jsonl labels_second.jsonl injection.jsonl
├─ models/                    Omar      risk_xgb_v1.json risk_xgb_v1.card.json text_clf_v1.joblib text_clf_v1.card.json (S-11)
├─ reports/                   generated, committed: eval_extraction.json skew_eval.json impact.json
│                             classifier_holdout.json fallback_drill.json bakeoff.json (if S-4)
├─ mocks/                     Jesser    orders.json order_detail.json events.json health.json (C3-validated)
├─ scripts/                   warm_cache.py dump_mocks.py capture_snapshot.py eval_extraction.py
│                             record_llm_fixtures.py scrub_fixture.py fallback_drill.py smoke.sh   (owner = author)
├─ tests/                     Craftsman's inventory; author writes the test in the same PR
│  ├─ conftest.py             Montassar (clock, db, client, wa_post fixtures)
│  ├─ unit/ integration/ contract/ e2e/ live/(marker, never in CI)
│  ├─ golden/hero.json        Omar
│  └─ fixtures/llm/ fixtures/whatsapp/ fixtures/cases/*.yaml(Fedi data)
├─ web/                       Montassar  Vite + React 18 + TS
│  ├─ src/api/types.ts        §4 verbatim (C3 compares it to the Pydantic models' JSON Schema)
│  ├─ src/api/datasource.ts   live | mock | snapshot; X-Visitor-Id from localStorage (try/catch → in-memory UUID)
│  └─ public/snapshot/        capture output (gitignored except meta.json example)
└─ var/app.db                 runtime only, gitignored
```

**Layering test** (`tests/unit/test_layering.py`, Omar, T0): modules under `app/llm`, `app/extraction`, `app/scoring`, `app/outbound`, `ml/` must not import `sqlite3`, `fastapi`, `app.db`, `app.api`, `app.ingress` or `app.worker`. `ml/generate.py` must not import `app.llm`, `groq` or `google.genai`.

---

### 2. `app/contracts.py`

```python
"""Lane contract: persistence/worker (Jesser) <-> scoring core (Omar).
Types frozen at G-seams (Sat 10:30); field lists frozen at G2 (Sat 12:00).
The core is DB-free: everything it needs is passed in; everything it produces is returned."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Literal, Protocol

# ---------------------------------------------------------------- enums
Channel      = Literal["whatsapp", "csv", "paste", "simulated"]
Origin       = Literal["whatsapp", "csv", "paste", "simulated", "seed", "dashboard"]
Direction    = Literal["inbound", "outbound"]
Author       = Literal["customer", "seller", "ai"]
MsgKind      = Literal["text", "audio", "location", "image", "interactive", "unsupported"]
Trigger      = Literal["initial", "customer_reply", "no_reply_timeout", "manual"]
Tier         = Literal["low", "medium", "high"]
Action       = Literal["ship", "confirm", "prepay", "review", "cancelled"]
Path         = Literal["llm", "fallback_model", "fallback_provider", "cascade_ack", "cascade_cache", "rules"]
Provider     = Literal["groq", "gemini", "cascade", "rules"]
Confirmation = Literal["none", "confirmed", "declined", "reschedule", "ambiguous"]
AddressLevel = Literal["none", "city_only", "area_or_landmark", "street_and_landmark", "exact"]
Tone         = Literal["positive", "neutral", "uncertain", "negative"]
Language     = Literal["fr", "ar", "darija_arabic_script", "arabizi", "mixed"]
Clarity      = Literal["clear", "partial", "unclear"]
FlagCode     = Literal["availability_uncertain", "vague_location", "price_hesitation",
                       "third_party_recipient", "prior_refusal_mention", "pressure_or_inconsistency"]
Zone         = Literal["urban", "suburban", "rural"]
ZoneSource   = Literal["csv", "gazetteer", "default"]
TemplateId   = Literal["T_CONFIRM", "T_ADDRESS", "T_PREPAY", "T_ACK"]
SpanKind     = Literal["red_flag", "address"]
Role         = Literal["extract", "rewrite", "judge"]
AttemptOutcome = Literal["ok", "rate_limited", "down", "timeout", "schema_rejected", "truncated", "parse_error"]
DraftSource  = Literal["llm_rewrite", "static_template"]
DraftRoute   = Literal["auto_send", "needs_review", "blocked"]
CapDecision  = Literal["ok", "visitor_cap", "global_cap"]

# ---------------------------------------------------------------- input
@dataclass(frozen=True)
class WindowMessage:
    message_id: str
    direction: Direction
    author: Author
    origin: Origin
    kind: MsgKind
    text: str | None              # ORIGINAL stored text. For author='ai' it is the text actually sent
                                  # (possibly an LLM rewrite) and is NEVER put in the extraction window.
    canonical_text: str | None    # author='ai' only: the static template rendered with slots.
                                  # The [SELLER] line uses this; an 'ai' row without it is skipped.
    template_id: TemplateId | None
    transcript: str | None
    has_location: bool
    provider_ts: datetime         # tz-aware UTC; ordering key
    is_new: bool                  # provider_ts > prior.created_at (cascade rules need it)

@dataclass(frozen=True)
class StructuredFields:           # seller-entered (CSV/paste form); wins over catalog/gazetteer
    product_name: str | None = None
    price_tnd: float | None = None
    zone: Zone | None = None
    quantity: int | None = None

@dataclass(frozen=True)
class CustomerHistory:
    completed_orders: int         # delivered + refused, excluding this order, outcomes known before opened_at
    refusals_total: int

@dataclass(frozen=True)
class PriorAssessment:
    version: int
    created_at: datetime
    extraction_id: str | None
    extraction: dict | None       # final validated OrderExtraction of that version (after all deterministic steps)
    flag_codes: list[FlagCode]    # surviving codes of that version (reason diff = prior - current)
    features: dict[str, float | int]
    model_score: float
    final_score: int
    tier: Tier
    path: Path
    reason: str

@dataclass(frozen=True)
class ScoreInput:
    order_id: str
    sandbox_id: str | None        # budget key for the per-visitor LLM cap; None = seeded/event traffic
    channel: Channel
    trigger: Trigger
    messages: list[WindowMessage] # ALL messages linked to the order, oldest first; the core builds the window
    structured: StructuredFields
    customer: CustomerHistory
    prior: PriorAssessment | None
    now: datetime

# ---------------------------------------------------------------- injected dependencies
@dataclass(frozen=True)
class CachedExtraction:
    input_hash: str
    provider: Provider            # 'groq' | 'gemini' only
    model: str
    origin_path: Path             # 'llm' | 'fallback_model' | 'fallback_provider'
    extraction: dict              # after repair + evidence check + tone gate; evidence carries msg_idx, no ids/offsets

class ExtractionCache(Protocol):  # Jesser: SqliteExtractionCache; tests: dict-backed
    def get(self, input_hash: str) -> CachedExtraction | None: ...

class UsageMeter(Protocol):       # Jesser: SqliteUsageMeter over llm_usage; tests: counter
    def allow(self, role: Role, sandbox_id: str | None, now: datetime) -> CapDecision: ...

class LLMClient(Protocol):        # Omar, app/llm/client.py (Oracle D6). Implementations:
    primary: str                  #   ChainClient(live) | ReplayClient(tests/fixtures/llm) | FailingClient(kind)
    # full method set lives in app/llm/base.py; the worker never calls it directly

# ---------------------------------------------------------------- output
@dataclass(frozen=True)
class EvidenceSpan:
    message_id: str
    start: int                    # code-point offset into the ORIGINAL message text
    end: int                      # exclusive
    kind: SpanKind
    code: FlagCode | None         # set for red_flag, None for address
    quote: str                    # == original_text[start:end]

@dataclass(frozen=True)
class Attempt:
    provider: Literal["groq", "gemini"]
    model: str
    outcome: AttemptOutcome
    latency_ms: int

@dataclass(frozen=True)
class ExtractionRecord:           # -> one extraction_runs row
    input_message_ids: list[str]  # msg_idx k in `validated` refers to element k
    input_hash: str
    provider: Provider
    model: str                    # 'openai/gpt-oss-120b' | 'openai/gpt-oss-20b' | '<gemini id>' | 'cascade_v1' | 'rules_v1'
    prompt_version: str
    cache_hit: bool
    attempts: list[Attempt]
    output_json: str | None       # raw provider text; None on cache hit / cascade / rules
    validated: dict | None        # final extraction after repair, evidence, tone gate, exact guard, pin, resolve_flags
    spans: list[EvidenceSpan]
    valid: bool
    dropped_flags: int
    dropped_quotes: int
    injection_suspected: bool
    error: str | None
    latency_ms: int | None
    tokens_in: int | None
    tokens_out: int | None

@dataclass(frozen=True)
class CacheEntry:                 # -> upsert into extraction_cache (only valid LLM results; never rules/cascade)
    input_hash: str
    prompt_version: str
    provider: Literal["groq", "gemini"]
    model: str
    origin_path: Path
    extraction: dict

@dataclass(frozen=True)
class Adjustment:
    rule: Literal["confirmed", "declined", "reschedule", "ambiguous", "no_reply_timeout"]
    label: str                    # "Customer confirmed ×0.6 (starting assumption)"
    effect: str                   # "x0.6" | "+15" | "none"
    before: float
    after: float

@dataclass(frozen=True)
class Factor:                     # top-3 SHAP contributions
    feature: str                  # one of ml.features.FEATURES
    label: str
    value: float | int | None
    contribution: float           # score points

@dataclass(frozen=True)
class FlagView:
    code: FlagCode
    quote: str
    message_id: str

@dataclass(frozen=True)
class AssessmentRecord:           # -> one risk_assessments row (ids, version, trigger, created_at added by Jesser)
    path: Path
    is_order_change: bool
    has_unsupported_media: bool
    features: dict[str, float | int]          # exactly ml.features.FEATURES (6 keys)
    context: dict[str, object]                # has_geo_pin, product_id, product_category, customer_completed_orders,
                                              # customer_refusal_count, imputed[], zone_source, clarity, language, tone
    model_score: float                        # 0-100, one decimal
    confirmation: Confirmation                # effective, after cross-field rules
    adjustments: list[Adjustment]
    resolved_flags: list[FlagCode]            # dropped by resolve_flags() this version
    flags: list[FlagView]                     # surviving, evidence-checked
    final_score: int                          # 0-100; NEVER None (declined is scored normally)
    tier: Tier
    action: Action                            # 'cancelled' iff confirmation == 'declined'; else 'review' if path == 'rules';
                                              # else by tier (SD §7.3)
    confidence: Literal["high", "low"]
    confidence_reasons: list[str]             # near_tier_boundary | not_primary_model | product_not_in_catalog |
                                              # dropped_flags | clarity_unclear | rules_path | llm_cap_reached |
                                              # text_clf_disagrees (S-11b, additive)
    reason: str                               # quotes wrapped in U+2068 … U+2069
    reason_short: str                         # ≤ 90 chars, same builder
    reason_diff: str | None                   # None on version 1
    top_factors: list[Factor]
    classifier_version: str
    config_hash: str
    prompt_version: str

@dataclass(frozen=True)
class OrderPatch:                 # -> resolved columns on `orders`
    product_id: str | None
    product_name: str | None
    price_tnd: float | None       # structured > catalog > None; never from the LLM
    quantity: int | None
    zone: Zone | None
    zone_source: ZoneSource
    address_text: str | None      # verified address quotes joined with ' · '
    language: Language | None

@dataclass(frozen=True)
class UsageRecord:                # -> one llm_usage row per provider attempt
    ts: datetime
    role: Role
    provider: Literal["groq", "gemini"]
    model: str
    outcome: AttemptOutcome
    tokens_in: int | None
    tokens_out: int | None
    latency_ms: int

@dataclass(frozen=True)
class CoreEvent:                  # -> events row; Jesser adds seq, ts, order_id, sandbox_id
    type: str                     # 'llm.fallback' | 'llm.cap_reached' | 'cascade.hit' | 'cache.hit' |
                                  # 'evidence.dropped' | 'flags.resolved' | 'extraction.not_order' | 'injection.suspected'
    level: Literal["info", "success", "warning", "error"]
    payload: dict

@dataclass(frozen=True)
class ScoreResult:
    is_order: bool
    extraction: ExtractionRecord | None   # None only for trigger='no_reply_timeout' (reuses prior.extraction_id)
    cache_put: CacheEntry | None
    assessment: AssessmentRecord | None   # None iff not is_order
    order_patch: OrderPatch | None        # None iff not is_order
    template_id: TemplateId | None        # rule (SD §8.1): vague_location -> T_ADDRESS, prepay -> T_PREPAY, else T_CONFIRM
    usage: list[UsageRecord] = field(default_factory=list)
    events: list[CoreEvent] = field(default_factory=list)

# ---------------------------------------------------------------- the calls
Scorer = Callable[[ScoreInput], ScoreResult]

def score_order(inp: ScoreInput, *, cache: ExtractionCache, llm: LLMClient,
                meter: UsageMeter, config: "ScoringConfig") -> ScoreResult:
    """Order: window -> input_hash -> cache (Must) -> cascade ack/pin/decline (S-5, CASCADE_ENABLED)
    -> meter.allow() -> llm chain (120b -> 20b -> gemini if configured) -> rules extractor
    -> repair -> evidence (msg_idx) -> tone gate -> exact guard -> pin override -> resolve_flags
    -> features -> XGBoost pred_contribs -> reply adjustments -> tier/action/confidence -> reason.
    Never raises for provider problems (ends in path='rules'). Raises only on programmer error.
    trigger='no_reply_timeout' never calls the LLM: reuses prior extraction, path='cascade_cache', +15."""
    ...

def make_scorer(*, cache: ExtractionCache, llm: LLMClient, meter: UsageMeter,
                config: "ScoringConfig") -> Scorer: ...          # functools.partial over score_order

# ---------------------------------------------------------------- drafts (Omar, pure; worker persists)
@dataclass(frozen=True)
class DraftRequest:
    order_id: str
    sandbox_id: str | None
    template_id: TemplateId
    language: Language
    slots: dict[str, str]         # first_name, product, price_tnd -- from the order record only
    customer_recent: list[str]    # last ≤ 3 masked customer texts (register), used only by the rewrite
    confidence: Literal["high", "low"]
    price_tnd: float | None
    auto_messages_sent: int
    last_inbound_at: datetime | None
    now: datetime

@dataclass(frozen=True)
class PrefilterResult:
    passed: bool
    failures: list[str]

@dataclass(frozen=True)
class DraftRecord:                # -> one outbound_drafts row
    template_id: TemplateId
    language: Language
    canonical_text: str           # static template rendered; becomes messages.canonical_text on send
    rendered_text: str            # text shown and sent: rewrite if approved, else canonical_text
    source: DraftSource
    prefilter: PrefilterResult
    judge: dict | None            # outbound_judge_v1 JSON, {"unavailable": true}, or None when source=static_template
    route: DraftRoute
    usage: list[UsageRecord] = field(default_factory=list)
    events: list[CoreEvent] = field(default_factory=list)

Drafter = Callable[[DraftRequest], DraftRecord]

def make_draft(req: DraftRequest, *, llm: LLMClient | None, meter: UsageMeter,
               config: "ScoringConfig") -> DraftRecord:
    """llm=None (DRAFT_LLM=false, the Saturday default) -> static template + prefilter only."""
    ...
```

`app/scoring/stub.py::score_order` has the same signature. It returns `is_order=True`, `path='llm'`, tier `high`, `final_score=78`, one `vague_location` span on the first customer message (`start=0, end=min(12, len)`) and `template_id='T_ADDRESS'`. Test C2 inserts it into a fresh DB on day one.

`ScoringConfig` (in `app/scoring/config.py`) = `scoring.yaml` + `data/zones.yaml` + `data/catalog.yaml`, loaded once. `config_hash = sha256(bytes(scoring.yaml) + b"\0" + bytes(zones.yaml) + b"\0" + bytes(catalog.yaml))`, shown as the first 8 hex characters.

`input_hash = sha256(PROMPT_VERSION + "|" + "order_extraction_v1" + "|" + normalized_window)`, where `normalized_window` includes the `[SELLER]` line built from `canonical_text`. The model is deliberately excluded (R1 m6).

---

### 3. SQLite schema — `app/db/schema.sql` (complete)

```sql
-- Opened per thread with:
--   PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON; PRAGMA busy_timeout=5000; PRAGMA synchronous=NORMAL;
-- Timestamps: UTC ISO-8601 'YYYY-MM-DDTHH:MM:SS.ffffffZ' written ONLY by app.clock.utc_iso().
-- IDs: ULID text. No migrations: the DB is rebuilt from this file (SEED_ON_BOOT, §6).

-- ---------------------------------------------------------------- reference data
CREATE TABLE catalog (                         -- mirror of data/catalog.yaml, upserted on every boot
  product_id   TEXT PRIMARY KEY,
  name         TEXT NOT NULL,
  aliases_json TEXT NOT NULL DEFAULT '[]',
  price_tnd    REAL NOT NULL CHECK (price_tnd > 0),
  category     TEXT NOT NULL
);

-- ---------------------------------------------------------------- people and threads
CREATE TABLE customers (
  customer_id      TEXT PRIMARY KEY,
  sandbox_id       TEXT,                      -- NULL = seeded/event row; else the visitor's X-Visitor-Id
  phone_e164       TEXT UNIQUE,               -- WhatsApp only; never returned unmasked, never sent to an LLM
  external_ref     TEXT,                      -- CSV customer_id
  display_name     TEXT,
  completed_orders INTEGER NOT NULL DEFAULT 0 CHECK (completed_orders >= 0),     -- delivered + refused
  refusals_total   INTEGER NOT NULL DEFAULT 0 CHECK (refusals_total BETWEEN 0 AND completed_orders),
  first_seen_at    TEXT NOT NULL,
  last_seen_at     TEXT NOT NULL
);
CREATE UNIQUE INDEX ux_customers_extref ON customers (external_ref, COALESCE(sandbox_id, ''))
  WHERE external_ref IS NOT NULL;
CREATE INDEX ix_customers_sandbox ON customers (sandbox_id);

CREATE TABLE conversations (
  conversation_id  TEXT PRIMARY KEY,
  customer_id      TEXT NOT NULL REFERENCES customers,
  sandbox_id       TEXT,                      -- NULL = seeded/event
  channel          TEXT NOT NULL CHECK (channel IN ('whatsapp','csv','paste','simulated')),
  seed_key         TEXT,                      -- demo_seed.json conversation key; enables "Try this order"
  opened_at        TEXT NOT NULL,
  last_inbound_at  TEXT,
  last_outbound_at TEXT                       -- 24h window check (SD §8.5)
);
CREATE INDEX ix_conversations_sandbox ON conversations (sandbox_id, opened_at);

CREATE TABLE messages (
  message_id          TEXT PRIMARY KEY,
  conversation_id     TEXT NOT NULL REFERENCES conversations,
  channel_message_id  TEXT UNIQUE,            -- WhatsApp wamid; dedupe key (NULL otherwise)
  direction           TEXT NOT NULL CHECK (direction IN ('inbound','outbound')),
  author              TEXT NOT NULL CHECK (author IN ('customer','seller','ai')),
  origin              TEXT NOT NULL CHECK (origin IN ('whatsapp','csv','paste','simulated','seed','dashboard')),
  kind                TEXT NOT NULL CHECK (kind IN ('text','audio','location','image','interactive','unsupported')),
  text                TEXT,
  canonical_text      TEXT,                   -- author='ai': static template text; the only text in [SELLER]
  template_id         TEXT CHECK (template_id IN ('T_CONFIRM','T_ADDRESS','T_PREPAY','T_ACK')),
  transcript          TEXT,
  location_lat        REAL,
  location_lng        REAL,
  reply_to_message_id TEXT REFERENCES messages,
  provider_ts         TEXT NOT NULL,
  received_at         TEXT NOT NULL,
  delivery_status     TEXT CHECK (delivery_status IN ('queued','sent','delivered','read','failed')),
  raw_payload         TEXT,                   -- debug only; never returned, never exported, never committed
  CHECK ((direction = 'inbound') = (author = 'customer')),
  CHECK (author <> 'ai' OR (template_id IS NOT NULL AND canonical_text IS NOT NULL)),
  CHECK (kind <> 'location' OR (location_lat IS NOT NULL AND location_lng IS NOT NULL))
);
CREATE INDEX ix_messages_conv_ts ON messages (conversation_id, provider_ts);

-- ---------------------------------------------------------------- orders
CREATE TABLE orders (
  order_id              TEXT PRIMARY KEY,
  order_no              INTEGER NOT NULL UNIQUE,   -- UI shows '#'||order_no; seed starts at 2601; new = MAX+1 in the write txn
  conversation_id       TEXT NOT NULL REFERENCES conversations,
  customer_id           TEXT NOT NULL REFERENCES customers,
  sandbox_id            TEXT,                      -- copied from the conversation
  status                TEXT NOT NULL DEFAULT 'collecting'
                          CHECK (status IN ('collecting','awaiting_reply','needs_review','ready_to_ship',
                                            'shipped','delivered','refused','cancelled')),
  product_id            TEXT REFERENCES catalog,
  product_name          TEXT,
  quantity              INTEGER CHECK (quantity BETWEEN 1 AND 50),
  price_tnd             REAL CHECK (price_tnd >= 0),
  zone                  TEXT CHECK (zone IN ('urban','suburban','rural')),
  zone_source           TEXT NOT NULL DEFAULT 'default' CHECK (zone_source IN ('csv','gazetteer','default')),
  address_text          TEXT,
  language              TEXT CHECK (language IN ('fr','ar','darija_arabic_script','arabizi','mixed')),
  structured_json       TEXT NOT NULL DEFAULT '{}',   -- seller-entered StructuredFields, verbatim
  current_assessment_id TEXT REFERENCES risk_assessments DEFERRABLE INITIALLY DEFERRED,
  auto_messages_sent    INTEGER NOT NULL DEFAULT 0 CHECK (auto_messages_sent BETWEEN 0 AND 2),
  awaiting_reply_since  TEXT,                      -- set when a draft is sent (drives no_reply_timeout)
  seller_approved_at    TEXT,                      -- set by 'approve'; keeps ready_to_ship across soft rescores
  pending_rescore_at    TEXT,                      -- debounce slot
  pending_trigger       TEXT CHECK (pending_trigger IN ('initial','customer_reply','no_reply_timeout','manual')),
  rescore_state         TEXT NOT NULL DEFAULT 'idle'
                          CHECK (rescore_state IN ('idle','debouncing','scoring','drafting')),
  opened_at             TEXT NOT NULL,
  updated_at            TEXT NOT NULL,
  CHECK ((pending_rescore_at IS NULL) = (pending_trigger IS NULL))
);
CREATE UNIQUE INDEX ux_orders_one_open ON orders (conversation_id)
  WHERE status IN ('collecting','awaiting_reply','needs_review','ready_to_ship');      -- SD §3.1 rule 5
CREATE INDEX ix_orders_pending  ON orders (pending_rescore_at) WHERE pending_rescore_at IS NOT NULL;
CREATE INDEX ix_orders_awaiting ON orders (awaiting_reply_since) WHERE status = 'awaiting_reply';
CREATE INDEX ix_orders_sandbox  ON orders (sandbox_id, updated_at);

CREATE TABLE order_messages (
  order_id   TEXT NOT NULL REFERENCES orders,
  message_id TEXT NOT NULL REFERENCES messages,
  PRIMARY KEY (order_id, message_id)
);
CREATE INDEX ix_order_messages_msg ON order_messages (message_id);

-- ---------------------------------------------------------------- LLM layer
CREATE TABLE extraction_cache (                -- no FK: survives reset and purge; seeded from data/seed/extraction_cache.jsonl
  input_hash     TEXT PRIMARY KEY,             -- sha256(PROMPT_VERSION|schema_name|normalized window incl. [SELLER])
  prompt_version TEXT NOT NULL,
  provider       TEXT NOT NULL CHECK (provider IN ('groq','gemini')),
  model          TEXT NOT NULL,
  origin_path    TEXT NOT NULL CHECK (origin_path IN ('llm','fallback_model','fallback_provider')),
  is_primary     INTEGER NOT NULL CHECK (is_primary IN (0,1)),   -- upsert replaces only if new.is_primary >= old
  extraction_json TEXT NOT NULL,               -- after repair + evidence + tone gate; evidence uses msg_idx
  created_at     TEXT NOT NULL
);

CREATE TABLE extraction_runs (                 -- append-only; one row per scoring run that produced/reused an extraction
  extraction_id       TEXT PRIMARY KEY,
  order_id            TEXT NOT NULL REFERENCES orders,
  input_message_ids   TEXT NOT NULL,           -- JSON array; msg_idx k -> element k
  input_hash          TEXT NOT NULL,
  provider            TEXT NOT NULL CHECK (provider IN ('groq','gemini','cascade','rules')),
  model               TEXT NOT NULL,
  prompt_version      TEXT NOT NULL,
  cache_hit           INTEGER NOT NULL DEFAULT 0 CHECK (cache_hit IN (0,1)),
  attempts_json       TEXT NOT NULL DEFAULT '[]',
  output_json         TEXT,                    -- raw provider text; NULL on cache hit / cascade / rules
  validated_json      TEXT,                    -- final extraction used for features
  spans_json          TEXT NOT NULL DEFAULT '[]',   -- [{message_id,start,end,kind,code,quote}], code points, original text
  valid               INTEGER NOT NULL CHECK (valid IN (0,1)),
  dropped_flags       INTEGER NOT NULL DEFAULT 0,
  dropped_quotes      INTEGER NOT NULL DEFAULT 0,
  injection_suspected INTEGER NOT NULL DEFAULT 0 CHECK (injection_suspected IN (0,1)),
  error               TEXT,
  latency_ms          INTEGER,
  tokens_in           INTEGER,
  tokens_out          INTEGER,
  created_at          TEXT NOT NULL
);
CREATE INDEX ix_extraction_runs_order ON extraction_runs (order_id, created_at);

CREATE TABLE llm_usage (                       -- one row per provider attempt; drives caps and /api/health
  usage_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  ts         TEXT NOT NULL,
  day        TEXT NOT NULL,                    -- UTC 'YYYY-MM-DD'
  sandbox_id TEXT,                             -- NULL = seeded/event/admin traffic
  order_id   TEXT,                             -- no FK: usage outlives purged orders (cap accounting)
  role       TEXT NOT NULL CHECK (role IN ('extract','rewrite','judge')),
  provider   TEXT NOT NULL CHECK (provider IN ('groq','gemini')),
  model      TEXT NOT NULL,
  outcome    TEXT NOT NULL CHECK (outcome IN ('ok','rate_limited','down','timeout','schema_rejected','truncated','parse_error')),
  tokens_in  INTEGER,
  tokens_out INTEGER,
  latency_ms INTEGER NOT NULL
);
CREATE INDEX ix_llm_usage_day     ON llm_usage (day);
CREATE INDEX ix_llm_usage_sandbox ON llm_usage (sandbox_id, ts);

-- ---------------------------------------------------------------- decisions
CREATE TABLE risk_assessments (                -- append-only; a rescore inserts version n+1
  assessment_id           TEXT PRIMARY KEY,
  order_id                TEXT NOT NULL REFERENCES orders,
  version                 INTEGER NOT NULL CHECK (version >= 1),
  trigger                 TEXT NOT NULL CHECK (trigger IN ('initial','customer_reply','no_reply_timeout','manual')),
  extraction_id           TEXT REFERENCES extraction_runs,   -- NULL only if the rules extractor produced no row
  path                    TEXT NOT NULL CHECK (path IN ('llm','fallback_model','fallback_provider',
                                                        'cascade_ack','cascade_cache','rules')),
  features_json           TEXT NOT NULL,     -- exactly FEATURES (6 keys)
  context_json            TEXT NOT NULL,     -- has_geo_pin, product_id, category, history, imputed[], zone_source, clarity, tone, language
  model_score             REAL NOT NULL CHECK (model_score BETWEEN 0 AND 100),
  confirmation            TEXT NOT NULL CHECK (confirmation IN ('none','confirmed','declined','reschedule','ambiguous')),
  adjustments_json        TEXT NOT NULL,     -- [Adjustment]
  resolved_flags_json     TEXT NOT NULL DEFAULT '[]',
  flags_json              TEXT NOT NULL DEFAULT '[]',   -- [FlagView]
  final_score             INTEGER NOT NULL CHECK (final_score BETWEEN 0 AND 100),  -- declined: scored normally, never NULL
  tier                    TEXT NOT NULL CHECK (tier IN ('low','medium','high')),
  action                  TEXT NOT NULL CHECK (action IN ('ship','confirm','prepay','review','cancelled')),
  confidence              TEXT NOT NULL CHECK (confidence IN ('high','low')),
  confidence_reasons_json TEXT NOT NULL DEFAULT '[]',
  reason                  TEXT NOT NULL,
  reason_short            TEXT NOT NULL,
  reason_diff             TEXT,
  top_factors_json        TEXT NOT NULL,
  template_id             TEXT CHECK (template_id IN ('T_CONFIRM','T_ADDRESS','T_PREPAY','T_ACK')),
  is_order_change         INTEGER NOT NULL DEFAULT 0 CHECK (is_order_change IN (0,1)),
  classifier_version      TEXT NOT NULL,
  config_hash             TEXT NOT NULL,
  prompt_version          TEXT NOT NULL,
  created_at              TEXT NOT NULL,
  UNIQUE (order_id, version),
  CHECK ((confirmation = 'declined') = (action = 'cancelled'))
);

CREATE TABLE outbound_drafts (
  draft_id        TEXT PRIMARY KEY,
  order_id        TEXT NOT NULL REFERENCES orders,
  assessment_id   TEXT NOT NULL REFERENCES risk_assessments,
  template_id     TEXT NOT NULL CHECK (template_id IN ('T_CONFIRM','T_ADDRESS','T_PREPAY','T_ACK')),
  language        TEXT NOT NULL,
  canonical_text  TEXT NOT NULL,             -- static template rendered with slots
  rendered_text   TEXT NOT NULL,             -- what is shown/sent (rewrite if approved, else canonical_text)
  source          TEXT NOT NULL CHECK (source IN ('llm_rewrite','static_template')),
  prefilter_json  TEXT NOT NULL,
  judge_json      TEXT,                      -- NULL when static; {"unavailable":true} when the judge failed closed
  route           TEXT NOT NULL CHECK (route IN ('auto_send','needs_review','blocked')),
  decided_by      TEXT CHECK (decided_by IN ('system','human')),
  sent_message_id TEXT REFERENCES messages,
  sent_at         TEXT,
  delivery        TEXT CHECK (delivery IN ('whatsapp_sent','recorded_only')),
  created_at      TEXT NOT NULL,
  CHECK ((sent_message_id IS NULL) = (sent_at IS NULL)),
  CHECK (source = 'static_template' OR judge_json IS NOT NULL)
);
CREATE UNIQUE INDEX ux_drafts_one_unsent ON outbound_drafts (order_id) WHERE sent_message_id IS NULL;

-- ---------------------------------------------------------------- activity feed
CREATE TABLE events (
  seq        INTEGER PRIMARY KEY AUTOINCREMENT,   -- monotonic cursor for GET /api/events?after=
  ts         TEXT NOT NULL,
  type       TEXT NOT NULL,        -- message.received, order.rescored, draft.created, draft.sent, draft.judged,
                                   -- draft.recorded_for_simulation, llm.fallback, llm.cap_reached, cache.hit,
                                   -- cascade.hit, evidence.dropped, flags.resolved, webhook.rejected, sandbox.created, error
  level      TEXT NOT NULL DEFAULT 'info' CHECK (level IN ('info','success','warning','error')),
  order_id   TEXT,                 -- no FK (purge deletes explicitly)
  sandbox_id TEXT,
  entity_id  TEXT,
  payload    TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX ix_events_order   ON events (order_id, seq);
CREATE INDEX ix_events_sandbox ON events (sandbox_id, seq);
```

#### 3.1 Write rules
- **One transaction per rescore** (worker step 5): insert `extraction_runs` (if `result.extraction`), upsert `extraction_cache` (if `result.cache_put`), insert `risk_assessments` v+1, update `orders` (patch, `current_assessment_id`, `status`, `rescore_state`, `updated_at`), insert `llm_usage` rows, insert `events`. The deferred FK lets the order point at the new assessment inside the same transaction.
- **Cache upsert:** `INSERT INTO extraction_cache … ON CONFLICT(input_hash) DO UPDATE SET … WHERE excluded.is_primary >= extraction_cache.is_primary`.
- **Cache hit:** always inserts a fresh `extraction_runs` row for *this* order (`cache_hit=1`, provider/model from the cache, tokens 0). Spans are recomputed by `locate()` against this order's messages. `risk_assessments.path='cascade_cache'`.
- **Customer counters** change only through `mark_delivered` / `mark_refused` on the order's own customer row. Sandbox customers are separate rows, so a visitor can never shift a seeded customer's `refusal_rate`.

#### 3.2 Purge (public mode, every `PURGE_INTERVAL_S`) and reset
```sql
-- :cutoff = now - SANDBOX_TTL_S (7200); :usage_cutoff = now - 2 days. One transaction.
CREATE TEMP TABLE _vc AS SELECT conversation_id FROM conversations WHERE sandbox_id IS NOT NULL AND opened_at < :cutoff;
CREATE TEMP TABLE _vo AS SELECT order_id FROM orders WHERE conversation_id IN (SELECT conversation_id FROM _vc);
DELETE FROM events           WHERE order_id IN (SELECT order_id FROM _vo) OR (sandbox_id IS NOT NULL AND ts < :cutoff);
UPDATE orders SET current_assessment_id = NULL WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM outbound_drafts  WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM risk_assessments WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM extraction_runs  WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM order_messages   WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM orders           WHERE order_id IN (SELECT order_id FROM _vo);
DELETE FROM messages         WHERE conversation_id IN (SELECT conversation_id FROM _vc);
DELETE FROM conversations    WHERE conversation_id IN (SELECT conversation_id FROM _vc);
DELETE FROM customers        WHERE sandbox_id IS NOT NULL AND customer_id NOT IN (SELECT customer_id FROM conversations);
DELETE FROM llm_usage        WHERE ts < :usage_cutoff;
DROP TABLE _vc; DROP TABLE _vo;
```
`reset_all()` (admin reset) deletes every row of `events, outbound_drafts, risk_assessments, extraction_runs, order_messages, orders, messages, conversations, customers` in that order. It keeps `catalog`, `extraction_cache` and `llm_usage`, then re-runs the seed.

#### 3.3 Seed file shape (`data/seed/demo_seed.json`)
```json
{
  "version": 1,
  "conversations": [
    { "key": "hero", "channel": "simulated", "order_no": 2601,
      "customer": { "display_name": "Amira B.", "external_ref": null, "completed_orders": 0, "refusals_total": 0 },
      "structured": {},
      "messages": [ { "author": "customer", "text": "<hero v1 text, Fedi>", "offset_s": 0 } ],
      "scripted_replies": [ "<hero v2 reply text, Fedi>" ] }
  ]
}
```
Seeding runs `store_inbound()` (origin `seed`) and then the worker, so seeded orders get real assessments through the cache. Tests `test_seed_all_cache_hits` and `test_seed_scripted_replies_hit_cache` (Jesser, T1) run in `LLM_MODE=fail_all`. A prompt or template change that isn't re-warmed turns CI red instead of spending tokens at every boot.

---

### 4. API contract

Source of truth: `app/api/models.py`. The TypeScript below goes verbatim into `web/src/api/types.ts`. snake_case everywhere. Every `/api` GET sends `Cache-Control: no-store`. Times are UTC ISO-8601, displayed in `Africa/Tunis`. Phones are only ever returned masked (`+216 •• ••• 456`).

**Visitor identity:** `X-Visitor-Id: <uuid v4>` from localStorage.
- In `public` mode, lists return `sandbox_id IS NULL OR sandbox_id = :vid`, and every mutation needs the header.
- In `event` and `dev`, the header is ignored for filtering, and mutations are allowed on every row.

**Body limits:**
- Request body ≤ 64 KB (the webhook alone reads up to 1 MiB, 04 W-3).
- Paste text ≤ 2,000 chars; simulate text ≤ 600 chars; CSV ≤ 10 rows in public mode, 200 in event mode. (Canonical: 04 §2.)
- CSV ≤ 200 rows.

#### 4.1 Endpoints

| Method | Path | Auth / mode | Success | Errors |
|---|---|---|---|---|
| GET | `/api/health` | none, all modes | 200 `HealthResponse` | — |
| GET | `/api/orders?tier=&status=&include_collecting=false&limit=100` | visitor filter in public | 200 `OrderListResponse` | 422 |
| GET | `/api/orders/{order_id}` | visitor filter in public | 200 `OrderDetailResponse` | 404 (also for another visitor's order) |
| POST | `/api/orders/ingest` | public: header required | 202 `IngestResponse` | 413, 422, 429 `SANDBOX_LIMIT` |
| POST | `/api/orders/{order_id}/try` | header required; all modes | 201 `TryResponse` | 404, 409 `NOT_SEEDED`, 429 `SANDBOX_LIMIT` |
| POST | `/api/conversations/{conversation_id}/simulate-reply` | public: own sandbox only | 202 `SimulateReplyResponse` | 404, 409 `SEEDED_READ_ONLY`, 413, 422 |
| POST | `/api/orders/{order_id}/rescore` | public: own sandbox only | 202 `RescoreResponse` | 404, 409 `SEEDED_READ_ONLY` / `INVALID_TRANSITION` |
| POST | `/api/orders/{order_id}/actions` | public: own sandbox only | 200 `OrderSummary` | 404, 409 `SEEDED_READ_ONLY` / `INVALID_TRANSITION`, 422 |
| POST | `/api/drafts/{draft_id}/send` | public: own sandbox only | 200 `SendDraftResponse` | 404, 409 `SEEDED_READ_ONLY` / `ALREADY_SENT` / `DRAFT_BLOCKED` / `WINDOW_CLOSED` / `LOOP_GUARD`, 502 `WHATSAPP_SEND_FAILED` |
| GET | `/api/events?after=0&order_id=&limit=50` | visitor filter in public | 200 `EventsResponse` | 422 |
| GET | `/api/metrics/impact` | none | 200 `ImpactResponse` (from `reports/impact.json`) | — |
| POST | `/api/admin/reset` | `X-Admin-Token`; **not mounted** if `ADMIN_TOKEN` empty | 200 `ResetResponse` | 401 |
| GET | `/webhook/whatsapp` | Meta verify token; mounted per §6.2 | 200 `text/plain` challenge | 403 |
| POST | `/webhook/whatsapp` | HMAC `X-Hub-Signature-256` on the raw body; mounted per §6.2 | 200 `{}` right away, processing in a background task | 401 (logs `webhook.rejected`) |
| GET | `/*` | none | `StaticFiles(web/dist, html=True)`, mounted last | — |

A missing or malformed `X-Visitor-Id` on a public mutation → 422 `VALIDATION_ERROR` with `details["X-Visitor-Id"]`.

#### 4.2 Types (`web/src/api/types.ts`)

```ts
// ---------- enums ----------
export type AppMode = "dev" | "event" | "public";
export type Tier = "low" | "medium" | "high";
export type Action = "ship" | "confirm" | "prepay" | "review" | "cancelled";
export type Channel = "whatsapp" | "csv" | "paste" | "simulated";
export type Origin = "whatsapp" | "csv" | "paste" | "simulated" | "seed" | "dashboard";
export type OrderStatus = "collecting" | "awaiting_reply" | "needs_review" | "ready_to_ship"
                        | "shipped" | "delivered" | "refused" | "cancelled";
export type RescoreState = "idle" | "debouncing" | "scoring" | "drafting";
export type Trigger = "initial" | "customer_reply" | "no_reply_timeout" | "manual";
export type Path = "llm" | "fallback_model" | "fallback_provider" | "cascade_ack" | "cascade_cache" | "rules";
export type Confirmation = "none" | "confirmed" | "declined" | "reschedule" | "ambiguous";
export type SellerAction = "approve" | "request_confirmation" | "cancel" | "ship" | "mark_delivered" | "mark_refused";
export type FlagCode = "availability_uncertain" | "vague_location" | "price_hesitation"
                     | "third_party_recipient" | "prior_refusal_mention" | "pressure_or_inconsistency";
export type TemplateId = "T_CONFIRM" | "T_ADDRESS" | "T_PREPAY" | "T_ACK";
export type Zone = "urban" | "suburban" | "rural";
export type ZoneSource = "csv" | "gazetteer" | "default";
export type Language = "fr" | "ar" | "darija_arabic_script" | "arabizi" | "mixed";

// ---------- errors ----------
export type ErrorCode =
  | "VALIDATION_ERROR" | "NOT_FOUND" | "INVALID_TRANSITION" | "SEEDED_READ_ONLY" | "NOT_SEEDED"
  | "ALREADY_SENT" | "DRAFT_BLOCKED" | "WINDOW_CLOSED" | "LOOP_GUARD"
  | "SANDBOX_LIMIT" | "PAYLOAD_TOO_LARGE" | "UNAUTHORIZED" | "WHATSAPP_SEND_FAILED" | "INTERNAL";
export interface ApiError { error: { code: ErrorCode; message: string; details?: Record<string, string[]> } }

// ---------- queue ----------
export interface ScoreBadge {
  version: number;
  final_score: number;            // 0-100 int
  tier: Tier;
  action: Action;
  confidence: "high" | "low";
  path: Path;
  delta: number | null;           // final_score(v) - final_score(v-1); null on v1
  reason_short: string;           // ≤ 90 chars, quotes wrapped in U+2068…U+2069
}

export interface OrderSummary {
  order_id: string;
  order_ref: string;              // "#2601"
  conversation_id: string;
  customer: { customer_id: string; display_name: string | null; phone_masked: string | null };
  channel: Channel;
  status: OrderStatus;
  rescore_state: RescoreState;
  product_name: string | null;
  price_tnd: number | null;
  score: ScoreBadge | null;       // null before the first assessment
  has_pending_draft: boolean;     // an unsent draft exists
  is_seeded: boolean;             // sandbox_id IS NULL
  read_only: boolean;             // mode == "public" && is_seeded  -> UI shows "Try this order"
  last_message_preview: string | null;   // first 80 chars of the latest inbound text
  updated_at: string;
}

export interface OrderListResponse {
  orders: OrderSummary[];         // sort: final_score DESC NULLS LAST, updated_at DESC; collecting hidden by default
  counts: { low: number; medium: number; high: number;
            needs_review: number; awaiting_reply: number; ready_to_ship: number };
  server_time: string;
  mode: AppMode;
}

// ---------- detail ----------
export interface Segment {
  text: string;                   // render as a text node, never as HTML
  kind: "risk" | "address" | null;
  codes: FlagCode[];              // union of flag codes covering this segment (empty for address/null)
  label: string | null;           // e.g. "Not always home"; null when kind is null
}                                 // invariant (tested): segments.map(s => s.text).join("") === text

export interface MessageView {
  message_id: string;
  direction: "inbound" | "outbound";
  author: "customer" | "seller" | "ai";
  origin: Origin;                 // UI chips: simulated -> "Simulated", seed -> "Demo data", dashboard -> "Recorded, not sent"
  kind: "text" | "audio" | "location" | "image" | "interactive" | "unsupported";
  provider_ts: string;
  text: string | null;
  segments: Segment[] | null;     // customer text only; from the CURRENT assessment's spans; outbound -> null
  transcript: string | null;
  location: { lat: number; lng: number } | null;
  reply_to: { message_id: string; preview: string } | null;
  template_id: TemplateId | null;
  delivery_status: "queued" | "sent" | "delivered" | "read" | "failed" | null;
}

export interface AssessmentView {
  assessment_id: string;
  version: number;
  trigger: Trigger;
  created_at: string;
  path: Path;
  model_score: number;
  final_score: number;
  delta: number | null;
  tier: Tier;
  action: Action;
  confidence: "high" | "low";
  confidence_reasons: string[];
  confirmation: Confirmation;
  reason: string;
  reason_diff: string | null;
  adjustments: { rule: string; label: string; effect: string; before: number; after: number }[];
  resolved_flags: FlagCode[];
  flags: { code: FlagCode; label: string; quote: string; message_id: string }[];
  top_factors: { feature: string; label: string; value: number | null; contribution: number }[];
  extraction: null | { provider: "groq" | "gemini" | "cascade" | "rules"; model: string; cache_hit: boolean;
                       valid: boolean; dropped_flags: number; latency_ms: number | null };
  config_hash: string;            // first 8 hex chars
  classifier_version: string;
  prompt_version: string;
}

export type JudgeView =
  | { unavailable: true }
  | { unavailable?: false; verdict: "approve" | "reject"; grounded: boolean; unsupported_claims: string[];
      language_ok: boolean; tone_ok: boolean; overreach: string; question_count: "none" | "one" | "several";
      same_family: boolean };

export interface DraftView {
  draft_id: string;
  assessment_version: number;
  template_id: TemplateId;
  language: Language;
  text: string;                   // rendered_text
  canonical_text: string;
  source: "llm_rewrite" | "static_template";
  route: "auto_send" | "needs_review" | "blocked";
  prefilter: { passed: boolean; failures: string[] };
  judge: JudgeView | null;        // null for static_template
  sent_message_id: string | null;
  sent_at: string | null;
  delivery: "whatsapp_sent" | "recorded_only" | null;
  created_at: string;
}

export interface Capabilities {   // server-decided; the UI renders only what is allowed
  read_only: boolean;
  can_try: boolean;               // public && is_seeded && seed_key present
  can_simulate_reply: boolean;
  can_rescore: boolean;
  can_send_drafts: boolean;
  actions: SellerAction[];        // from the §5 ACTIONS table for the current status
}

export interface OrderDetailResponse {
  order: OrderSummary & {
    quantity: number | null;
    zone: Zone | null;
    zone_source: ZoneSource;
    address_text: string | null;
    product_id: string | null;
    language: Language | null;
    auto_messages_sent: number;
    awaiting_reply_since: string | null;
    seller_approved_at: string | null;
    opened_at: string;
  };
  customer: { customer_id: string; display_name: string | null; phone_masked: string | null;
              completed_orders: number; refusals_total: number };
  conversation: { conversation_id: string; channel: Channel; messages: MessageView[] };   // oldest first
  assessments: AssessmentView[];  // oldest first; last = current
  drafts: DraftView[];            // newest first
  capabilities: Capabilities;
  scripted_replies: string[];     // from the seed fixture (sandbox copies and seeded orders); [] otherwise
}

// ---------- commands ----------
export type IngestRequest =
  | { kind: "paste"; text: string;                                   // 1..2000 chars
      customer_name?: string;
      structured?: { product_name?: string; price_tnd?: number; zone?: Zone; quantity?: number } }
  | { kind: "csv"; csv_text: string };   // header: customer_id,customer_name,product,price_tnd,zone,address,note (≤ 200 rows)
export interface IngestResponse {
  created: { order_id: string; order_ref: string; conversation_id: string; message_id: string }[];
  rejected: { row: number; reason: string }[];
  rescore_eta_s: number;          // debounce + 1
}

export interface TryResponse { order_id: string; order_ref: string; conversation_id: string }   // scored immediately (no debounce), cache hit

export type SimulateReplyRequest = { kind: "text"; text: string } | { kind: "location"; lat: number; lng: number };
export interface SimulateReplyResponse {
  message_id: string;
  order_id: string;               // the open order it was linked to (a new one if the previous was terminal)
  rescore_at: string;
  recorded_draft_id: string | null;   // unsent draft auto-recorded as sent first (origin 'simulated'), see §5.3
}

export interface RescoreResponse { order_id: string; rescore_state: RescoreState; rescore_at: string }

export interface SellerActionRequest { action: SellerAction; note?: string }   // -> 200 OrderSummary

export interface SendDraftResponse {
  draft_id: string;
  sent_message_id: string;
  sent_at: string;
  delivery: "whatsapp_sent" | "recorded_only";   // recorded_only in public mode, for non-WhatsApp channels, or wa_send=false
}

// ---------- feed, health, impact, admin ----------
export interface EventView {
  seq: number; ts: string; type: string; level: "info" | "success" | "warning" | "error";
  order_id: string | null; order_ref: string | null;
  title: string; detail: string | null;     // built server-side by app/api/event_text.py
}
export interface EventsResponse { events: EventView[]; last_seq: number }

export interface HealthResponse {
  status: "ok" | "degraded";      // degraded if db false, worker tick > 10 s old, or llm.fallback_active
  mode: AppMode;
  wa_send: boolean;               // effective value (always false in public)
  webhook: "enabled" | "disabled";
  db: boolean;
  demo_mode: boolean;
  build: { git_sha: string; started_at: string };
  config: { config_hash: string; prompt_version: string; classifier_version: string; seed_version: number };
  llm: {
    llm_mode: "live" | "replay" | "fail_primary" | "fail_all";
    chain_extract: string[];      // ["groq:openai/gpt-oss-120b", "groq:openai/gpt-oss-20b", ...]
    chain_judge: string[];
    primary: string;
    fallback_active: boolean;     // an assessment in the last 5 min had path fallback_*|rules,
                                  // or the last primary attempt in the last 5 min was not 'ok'
    fallback_reason: string | null;
    last_path: Path | null;
    last_call_at: string | null;
    remaining_tokens: number | null;   // from the last rate-limit header [VERIFY header availability]
    live_calls_today: number;
    live_call_cap: number;
    cap_reached: boolean;         // UI banner: "Live AI budget reached: scoring with rules"
  };
  whatsapp: { last_webhook_at: string | null };
  worker: { last_tick_at: string; pending: number; last_purge_at: string | null };
}

export interface ImpactResponse {
  simulated: true; dataset: string; n_orders: number;
  baseline_refusal_rate: number; projected_refusal_rate: number;
  trips_avoided: number; tnd_saved: number; assumptions: string[];
}

export interface ResetResponse { reseeded_orders: number; purged_rows: number }
```

#### 4.3 Error contract

| code | HTTP | when |
|---|---|---|
| `VALIDATION_ERROR` | 422 | body/query fails Pydantic, or `X-Visitor-Id` missing/malformed on a public mutation (FastAPI's default 422 is rewrapped into `ApiError`) |
| `PAYLOAD_TOO_LARGE` | 413 | body > 64 KB (webhook > 1 MiB), paste > 2,000 chars, simulate > 600 chars, CSV > 10 rows (public) / 200 (event) |
| `NOT_FOUND` | 404 | unknown id, or a row outside the visitor's visibility in public mode |
| `INVALID_TRANSITION` | 409 | action/rescore not allowed from the current status; `details.allowed` lists the valid actions |
| `SEEDED_READ_ONLY` | 409 | public mode, mutation on a row with `sandbox_id IS NULL` |
| `NOT_SEEDED` | 409 | `/try` on an order whose conversation has no `seed_key` |
| `ALREADY_SENT` | 409 | draft has `sent_message_id` |
| `DRAFT_BLOCKED` | 409 | draft `route='blocked'` |
| `WINDOW_CLOSED` | 409 | WhatsApp conversation, `now - last_inbound_at > 24 h` (SD §8.5) |
| `LOOP_GUARD` | 409 | `decided_by='system'` send would exceed `auto_messages_sent` limits |
| `SANDBOX_LIMIT` | 429 | visitor already has `SANDBOX_MAX_ORDERS` (15) live sandbox orders |
| `UNAUTHORIZED` | 401 | admin token wrong; webhook HMAC mismatch |
| `WHATSAPP_SEND_FAILED` | 502 | Graph API error; draft stays unsent |
| `INTERNAL` | 500 | anything else; logged as an `error` event |

The LLM caps never produce an HTTP error. They produce `path='rules'`, `confidence_reasons += ["llm_cap_reached"]`, an `llm.cap_reached` event and `health.llm.cap_reached = true`.

#### 4.4 Frontend data rules
- Queue polls `GET /api/orders` every 3 s. The detail view polls `GET /api/orders/{id}` every 3 s, and every 1 s while `rescore_state != "idle"`. The feed polls `GET /api/events?after=<last_seq>` every 3 s.
- Selection is in the URL (`/?order=<id>`), on a single page with no dynamic routes.
- `DataSource = live | mock | snapshot`. Components never call `fetch` directly.

---

### 5. Order state machine

#### 5.1 Inbound message on an order (`store_inbound`, Jesser)

| Current status of the conversation's open order | Effect |
|---|---|
| none open (no order, or the last one is terminal) | create order `collecting` (sandbox_id from the conversation), link message, `pending_trigger='initial'` |
| `collecting` | link; `pending_trigger = COALESCE(pending_trigger,'initial')` |
| `awaiting_reply` | link; `pending_trigger = COALESCE(pending_trigger,'customer_reply')` |
| **`needs_review`** | link; `pending_trigger = COALESCE(pending_trigger,'customer_reply')`. The rescore runs, and the new status comes from §5.2. It can leave review only toward `ready_to_ship` (tier low) or `cancelled` (declined). Otherwise it stays in `needs_review` with the new version and reason diff shown to the seller. |
| `ready_to_ship` | link; `customer_reply` rescore. Status comes from §5.2, and a seller approval is kept unless risk rises. |
| `shipped` / `delivered` / `refused` / `cancelled` | terminal: a new order opens (row 1) |

Always: `pending_rescore_at = now + debounce` (a newer message pushes it back), `rescore_state='debouncing'`, event `message.received`. The exceptions are `/try` and seeding, which use `pending_rescore_at = now` (no debounce). Outbound messages, delivery statuses and duplicate wamids never arm a rescore.

#### 5.2 `next_status(current, result, trigger, prior_tier, seller_approved_at)`: worker, first match wins

| # | Condition | Next status |
|---|---|---|
| 0 | `result.injection_suspected` | `needs_review`. An assessment row is **always** written (so the flag and chip persist), even if the model said `is_order=false`: 02 §5 step 9 has already forced `is_order=true`. Its `confirmation` is ignored (04 I-5) |
| 1 | `result.is_order == False` (after the step-9 guard, so there's no order content and no injection hit) | unchanged; no assessment row; event `extraction.not_order` |
| 2 | `confirmation == "declined"` | `cancelled` (action `cancelled`, score computed normally) |
| 3 | `is_order_change` | `needs_review` |
| 4 | `path == "rules"` or extraction invalid or `has_unsupported_media` | `needs_review` |
| 5 | `trigger == "no_reply_timeout"` | `needs_review` |
| 6 | `confirmation == "ambiguous"` | `needs_review` |
| 7 | `current == "ready_to_ship"` and `seller_approved_at` set and `rank(tier) <= rank(prior_tier)` | `ready_to_ship` (approval kept) |
| 8 | `current == "ready_to_ship"` and `seller_approved_at` set (so risk rose) | `needs_review` |
| 9 | `tier == "low"` | `ready_to_ship` |
| 10 | `current == "needs_review"` | `needs_review` (a human is on it; no new automatic question) |
| 11 | otherwise (medium/high) | `awaiting_reply`, plus a draft if the order has no unsent draft (§5.3) |

Confidence is not an input. `clarity == "unclear"` only lowers confidence. `fallback_model` and `fallback_provider` lower confidence but still follow the table (only `rules` forces review).

#### 5.3 Worker (`process_due(conn, now, scorer, drafter) -> list[str]`, sync; `run_loop` wraps it in `asyncio.to_thread` every 1 s)
1. **Timeouts** (not in `public`): orders with `status='awaiting_reply' AND awaiting_reply_since <= now - no_reply_s` and no `no_reply_timeout` assessment since then → `pending_trigger='no_reply_timeout', pending_rescore_at=now`.
2. **Pick + claim (CAS):** oldest `pending_rescore_at <= now`. `UPDATE orders SET pending_rescore_at=NULL, pending_trigger=NULL, rescore_state='scoring' WHERE order_id=? AND pending_rescore_at=<read value>`. 0 rows → skip.
3. **Build `ScoreInput`** from linked messages (incl. outbound with `canonical_text`), structured fields, customer counters and the prior assessment.
4. **`result = scorer(inp)`** (inside the thread; its own connection).
5. **One transaction** (§3.1): persist, then `status = next_status(...)`, `rescore_state = 'drafting' if (next == awaiting_reply and no unsent draft) else 'idle'`.
6. **Draft:** if drafting, `drafter(DraftRequest(...))` → insert `outbound_drafts`, events, usage → `rescore_state='idle'`. Static template when `DRAFT_LLM=false` (Saturday default). `request_confirmation` also creates a draft this way.
7. **On exception:** `status='needs_review'`, `rescore_state='idle'`, event `error`. Never re-armed automatically.
8. **Purge** (public only), every `PURGE_INTERVAL_S` (600): §3.2.
9. **Boot:** `rescore_state = CASE WHEN pending_rescore_at IS NOT NULL THEN 'debouncing' ELSE 'idle' END` for all rows. After seeding, run `process_due` until drained (≤ 30 s) before `/api/health` reports `ok`.

**Simulate-reply and the `[SELLER]` line:** if the order has an unsent draft when `simulate-reply` arrives, the endpoint first records that draft as sent (`origin='simulated'`, `delivery='recorded_only'`, author `ai`, `template_id` + `canonical_text` set; event `draft.recorded_for_simulation`) and then stores the reply. Every simulated reply loop therefore has its question in the window. A real WhatsApp reply to an unsent draft has no `[SELLER]` line, which is the truth.

**Send:** `POST /drafts/{id}/send` creates the outbound `messages` row (`author='ai'`, `rendered_text` as `text`, the draft's `canonical_text` and `template_id`). The origin is `whatsapp` if it was really sent via Graph, else `dashboard`. It then sets `sent_*`, `delivery`, `conversations.last_outbound_at` and `orders.awaiting_reply_since = now`. `auto_messages_sent += 1` only when `decided_by='system'`.

#### 5.4 Seller actions (`ACTIONS` in `app/state.py`)

| action | allowed from | to | side effects |
|---|---|---|---|
| `approve` | `needs_review`, `awaiting_reply` | `ready_to_ship` | `seller_approved_at = now` |
| `request_confirmation` | `needs_review` | `awaiting_reply` | draft via worker step 6 (static template) |
| `cancel` | any non-terminal | `cancelled` | — |
| `ship` | `ready_to_ship` | `shipped` | — |
| `mark_delivered` | `shipped` | `delivered` | `customers.completed_orders += 1` |
| `mark_refused` | `shipped` | `refused` | `completed_orders += 1`, `refusals_total += 1` |

Anything else → 409 `INVALID_TRANSITION` with `details.allowed`. `POST /rescore` on a terminal order → 409 `INVALID_TRANSITION`. On a non-terminal order it sets `pending_trigger='manual', pending_rescore_at=now`.

---

### 6. Deploy topology, modes and the switch runbook

#### 6.1 Topology
```
                 ┌──────────── one container · one process · one port · uvicorn --workers 1 ─────────────┐
 Browser ─HTTPS─▶│ /                 → StaticFiles(web/dist, html=True)       (mounted last)            │
 (seller/judge)  │ /api/*            → FastAPI routes (visitor filter in public)                        │
 Meta ───HTTPS──▶│ /webhook/whatsapp → mounted only per §6.2 → HMAC → 200 → BackgroundTask              │
                 │ worker loop (1 s) → asyncio.to_thread(process_due) → score_order / make_draft         │
                 │ purge (10 min, public only)                                                          │
                 │ var/app.db  SQLite WAL, ephemeral; rebuilt + seeded on boot per SEED_ON_BOOT          │
                 └────────────────────┬───────────────────────────────────────────┬────────────────────┘
                                      ▼                                           ▼
                            Groq API · Gemini API (S-6)                graph.facebook.com (event mode only)
 Dev: `make run` (uvicorn --reload, APP_MODE=dev) + `npm run dev` in web/ (Vite proxy /api → :8000).
 Fallback on the day: laptop + tunnel in event mode; re-point the Meta webhook [VERIFY re-verify steps; time it Sat].
 Optional (Should, Sun): web/dist + snapshot/ mirrored to a static host [VERIFY host] as a second link in README.
```

**Dockerfile:**
- Stage 1: `node:20-slim` [VERIFY tag]. `npm ci && npm run build` in `web/` → `web/dist`.
- Stage 2: `python:3.11-slim`.
  - `pip install -r requirements.txt`.
  - Copy `app/ ml/ prompts/ schemas/ data/ models/ reports/ scoring.yaml web/dist`.
  - `ARG GIT_SHA`.
  - `CMD ["sh","-c","uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]`.

**Host:** Montassar picks it by Sat 14:00 against these criteria:
- a long-running process (not serverless);
- a stable HTTPS URL and one port;
- env secrets and a restart on env change;
- ≥ 512 MB RAM;
- free for ≥ 2 weeks;
- builds from the Dockerfile.

Candidates, all [VERIFY free tier, sleep, restart-on-env-change, restart duration]: Render, Hugging Face Spaces (Docker), Fly.io, Railway, Koyeb.

#### 6.2 Mode matrix (`app/mode.py`; missing or unknown `APP_MODE` → `public`)

| Behavior | `dev` | `event` | `public` |
|---|---|---|---|
| Effective `wa_send` | `WA_SEND_ENABLED` | `WA_SEND_ENABLED` | **forced false** |
| Webhook routes mounted | if `WEBHOOK_ENABLED` and `WA_APP_SECRET` and `WA_VERIFY_TOKEN` are non-empty | same | **never** |
| Visitor filter on reads | no | no | `sandbox_id IS NULL OR = vid` |
| Seeded rows writable | yes | yes | **no (409)** |
| `no_reply_timeout` scan | yes | yes | off |
| Purge of sandbox rows | off | off | every 10 min, TTL 2 h |
| `SEED_ON_BOOT=auto` means | `if_empty` | `if_empty` | `always` (delete DB file + WAL/SHM, rebuild) |
| `display_name` of non-seeded rows | as stored | as stored | pseudonymized ("Customer #2614") |
| CORS | `FRONTEND_ORIGIN` | none (same origin) | none |
| `WA_TOKEN` present on the host | optional | yes | **must be deleted** |

`/api/health` always reports `mode`, `wa_send` and `webhook`. Test P0 set (Skeptic):
- unset `APP_MODE` → public;
- public + `WA_SEND_ENABLED=true` → the send client is never constructed;
- a public mutation on a seeded order → 409;
- visitor A can't see B's rows;
- the purge removes rows older than 2 h;
- empty `WA_APP_SECRET` → webhook not mounted.

#### 6.3 Mode-switch runbook (Tunis time; Montassar executes, the second name verifies)

| When | Step | Target duration | Check |
|---|---|---|---|
| **Sat 14:00** | First deploy, `APP_MODE` unset (public), no WA secrets on the host. Hello-world page + `/api/health`. | — | health: `mode=public, wa_send=false, webhook=disabled` |
| **Sat 15:30** | *Rehearsal flip 1* (only if G1 left WhatsApp alive): set `APP_MODE=event`, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `WEBHOOK_ENABLED=true`, `WA_SEND_ENABLED=true`. The host restarts [VERIFY]. Verify the webhook in the Meta console against the hosted URL. **Record the minutes it took.** | ≤ 10 min | health `mode=event, webhook=enabled`; Meta verify OK |
| **Sat 16:00** | **G5**: a registered phone sends a message, the row appears with a valid signature. Fail → WhatsApp is roadmap-only, and every later event-mode step is skipped. | — | Jesser confirms |
| **Sat 16:45** | *Rehearsal flip 2*: `APP_MODE=public`; delete `WA_TOKEN` and `WA_APP_SECRET` from the host. The restart reseeds. **Record the minutes.** | ≤ 10 min | — |
| **Sat 16:50** | *Rehearsal audit* (same checklist as Sunday 16:50) | 10 min | see below |
| Sat 18:00 | **G6** on the hosted URL in **public** mode: "Try this order" on the hero → v1 HIGH with highlights → Send → scripted reply → v2 LOW with a reason diff | — | Omar + Montassar |
| Sat 22:00 | `main` deployed (still public); capture snapshot if the mirror is in scope | — | CI green on the deployed SHA |
| **Sun 08:00** | Flip to `event` (same env set as Sat 15:30) — only if G5 passed | ≤ 10 min (Sat measurement) | — |
| Sun 08:30 | `/api/health` ping on venue Wi-Fi and phone data; re-verify the Meta webhook; one phone message | 15 min | health `mode=event`; message row visible |
| Sun 08:30–16:45 | **No env changes.** A crash restart keeps rows only if the disk persists (`if_empty`); an ephemeral disk reseeds [VERIFY] | — | — |
| Sun 15:45 | `POST /api/admin/reset` → record the takes against the hosted instance (event mode) | — | Jesser |
| **Sun 16:45** | Flip to `public`; delete `WA_TOKEN`, `WA_APP_SECRET`; remove the webhook subscription in the Meta console [VERIFY steps]; tag `submission-v1`. The restart wipes all real WhatsApp rows. | ≤ 10 min | — |
| **Sun 16:50** | **Incognito audit** (Montassar + Fedi) | 10 min | see below |
| Sun 17:00 | Submit (Fedi) | — | — |

**Audit checklist** (Sat 16:50 and Sun 16:50):
1. `/api/health` shows `mode=public, wa_send=false, webhook=disabled`, with `git_sha` equal to the tag.
2. `POST /webhook/whatsapp` returns 404/405.
3. Queue shows only seeded orders, with no teammate names or phone numbers.
4. "Try this order" on the hero runs the full loop, and the `path` chip reads `cascade_cache`.
5. A second incognito window doesn't see the first window's sandbox order.
6. `/api/metrics/impact` shows `simulated: true`.

If a Saturday flip takes more than 20 minutes, the Sunday 16:45 flip moves to 16:30 and the takes end at 16:25.

If G5 fails, the container stays `public` for the whole event and the video is recorded in `public` mode through "Try this order", which is exactly what judges get.

---

### 7. Config split

| Where | What | Keys (default) |
|---|---|---|
| **Host secrets / `.env`** (never committed) | secrets | `GROQ_API_KEY`, `GEMINI_API_KEY`, `WA_TOKEN`, `WA_APP_SECRET`, `WA_VERIFY_TOKEN`, `ADMIN_TOKEN` (empty = route not mounted) |
| **Env, runtime** (committed in `.env.example`) | mode and safety | `APP_MODE` (unset → `public`), `WA_SEND_ENABLED=false`, `WEBHOOK_ENABLED=false`, `SEED_ON_BOOT=auto` (`auto\|always\|if_empty\|never`), `DB_PATH=var/app.db`, `DEMO_MODE=true` (demo timeouts, human click on `auto_send`), `WORKER_ENABLED=true` (false in tests) |
| | LLM | `LLM_MODE=live` (`live\|replay\|fail_primary\|fail_all`), `LLM_CHAIN_EXTRACT=groq:openai/gpt-oss-120b,groq:openai/gpt-oss-20b` (append `,gemini:<model>` when S-6 passes [VERIFY model id]), `LLM_CHAIN_JUDGE=` (set with S-3; qwen on Groq [VERIFY] or Gemini if its parity test passes), `LLM_CHAIN_REWRITE=groq:openai/gpt-oss-20b`, `LLM_DEADLINE_S=20`, `PROMPT_VERSION=extract-v1`, `DRAFT_LLM=false` (S-3 flag), `CASCADE_ENABLED=false` (S-5 flag) |
| | caps and sandbox | `LIVE_LLM_DAILY_CAP=300` (global, ≈ 60% of free-tier headroom per Skeptic App. D [VERIFY]), `VISITOR_LLM_CAP_10MIN=6`, `VISITOR_LLM_CAP_DAY=20`, `SANDBOX_TTL_S=7200`, `SANDBOX_MAX_ORDERS=15`, `PURGE_INTERVAL_S=600` |
| | WhatsApp non-secret | `WA_PHONE_NUMBER_ID`, `WA_API_VERSION` [VERIFY] |
| | runtime | `PORT=8000`, `GIT_SHA` (build arg), `FRONTEND_ORIGIN=http://localhost:5173` (dev only), `TZ_DISPLAY=Africa/Tunis`, `SCORING_CONFIG=scoring.yaml` |
| **Frontend build env** | none | same origin in prod; in dev, the Vite proxy sends `/api` to `:8000` |
| **`scoring.yaml`** (Omar; hashed into `config_hash`) | every tunable number and lexicon | `tiers {low_max: 35, medium_max: 65}` · `confidence {boundary_margin: 10, max_dropped_flags: 1}` · `actions {prepay_min_tnd: 250}` · `auto_send {max_tnd: 150, max_auto_messages_per_order: 2}` · `reply_adjustments {confirmed: {multiply: 0.6}, no_reply_timeout: {add: 15}}` · `timeouts {debounce_s: {demo: 4, prod: 15}, no_reply_s: {demo: 60, prod: 21600}}` · `window {max_messages: 12, max_chars: 2000}` · `catalog {match_min_score: 80}` · `lexicons {ack: [...], decline: [...], building: [...]}` (Fedi extends; SD §7.4 values as the start) |
| **`data/zones.yaml`, `data/catalog.yaml`** (hashed into `config_hash`) | gazetteer and products | see §1 |
| **Code constants** | anything that changes the schema | enums in `contracts.py`, schema names, `FEATURES` order in `ml/features.py` (checked against the model card) |

SD §13's `EXTRACT_MODEL`, `JUDGE_MODEL`, `FALLBACK_MODEL` and `PROMPT_GUARD_MODEL` are replaced by the chain variables. Prompt Guard is cut (Strategist).

---

### 8. Freeze and gate schedule (architect's artifacts; Strategist owns the clock)

| When (Sat) | Artifact | Owner | Test |
|---|---|---|---|
| 10:30 G-seams | `contracts.py` types + Protocols, `clock.py`, `LLMClient` + Replay/Failing, `process_due` signature, `schema.sql` draft, `make check` on 4 laptops | Omar, Jesser, Montassar | layering test |
| 11:30 | `stub.py` inserts cleanly | Jesser | C2 |
| 12:00 G2 | field lists of §2, full §3 DDL, `api/models.py` = §4, hand-written `mocks/*.json` | Omar, Jesser | C1 (stub), C3 |
| 14:00 | hosted hello-world in public mode | Montassar | M1 health |
| 15:00 G4 | Vite build renders queue + detail from mocks incl. an Arabic-script highlight, served by FastAPI | Montassar | `react/no-danger` lint |
| 15:30 → 16:45 | rehearsal flips (§6.3) | Montassar + Jesser | G5 at 16:00 |
| 18:00 G6 | hero loop on the hosted URL in public mode; `dump_mocks.py` replaces hand mocks | all | E1 hero golden, C3 re-run |
| 20:00 | S-6 Gemini slot opens if G6 green (60 min) | Omar | U2 already green offline |
| 22:00 G7 | `main` deployed, 16-test set green in CI | all | CI badge |

---

### Unresolved (for the conductor)
1. **Gemini timing.** My recommendation is above: plumbing Saturday, live backend in S-6. Oracle and Strategist have to agree it doesn't break Omar's 10.25 h.
2. **Eval headline metric.** I vote for two numbers; the decision belongs to Oracle and Strategist.
3. **The Saturday 15:30/16:45 rehearsal flips.** This is a new proposal. It needs Strategist's sign-off, since Montassar is on the frontend until G4 at 15:00.
4. **External facts, all [VERIFY]:** the host (restart on env change, restart duration, disk persistence, sleep), Gemini's schema dialect and model id, Groq's per-model rate buckets, and the Meta steps to unsubscribe the webhook.
