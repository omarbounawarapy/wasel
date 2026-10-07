"""Contract between the persistence/worker layer and the scoring core.
The core is DB-free: everything it needs is passed in; everything it produces is returned.

The implementations live in src/wasel/scoring/score_order.py (score_order, make_scorer) and
src/wasel/outbound/make_draft.py (make_draft).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol

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
    """One stored message as the scorer sees it (built by repo.window_messages). Immutable."""
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
    """Order fields the seller entered (CSV or paste form). They win over catalog and gazetteer values."""
    product_name: str | None = None
    price_tnd: float | None = None
    zone: Zone | None = None
    quantity: int | None = None


@dataclass(frozen=True)
class CustomerHistory:
    """Outcome counts for the customer."""
    completed_orders: int         # delivered + refused, excluding this order, outcomes known before opened_at
    refusals_total: int


@dataclass(frozen=True)
class PriorAssessment:
    """The order's latest stored assessment, passed back in so the next rescore can compute a reason diff and keep the
    prior confirmation on T_ACK. None (in ScoreInput) for a first score.
    """
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
    # Per-feature points of that version, so reason_diff can compare v(k-1) with v(k). Empty dict when unknown.
    points: dict[str, float] = field(default_factory=dict)
    confirmation: Confirmation = "none"     # T_ACK keeps the prior confirmation


@dataclass(frozen=True)
class ScoreInput:
    """Everything the scorer needs for one rescore of one order; it does no DB access."""
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
    """A stored LLM extraction, keyed by the hash of the extraction input."""
    input_hash: str
    provider: Provider            # 'groq' | 'gemini' only
    model: str
    origin_path: Path             # 'llm' | 'fallback_model' | 'fallback_provider'
    extraction: dict              # after repair + evidence check + tone gate; evidence carries msg_idx, no ids/offsets


class ExtractionCache(Protocol):
    """Read side of the extraction cache. Implemented by SqliteExtractionCache; tests use a dict-backed version."""

    def get(self, input_hash: str) -> CachedExtraction | None:
        """The cached extraction for `input_hash`, or None."""
        ...


class UsageMeter(Protocol):
    """Gate on LLM provider calls. Implemented by SqliteUsageMeter (over llm_usage); tests use a counter."""

    def allow(self, role: Role, sandbox_id: str | None, now: datetime) -> CapDecision:
        """Return 'ok' or the cap that refuses the call. A refusal means 'score with rules', never an error."""
        ...


class LLMClient(Protocol):
    """The LLM chain the scorer calls for extraction. The implementation is llm.client.ChainClient: over live
    providers, or over recorded fixtures or forced failures when LLM_MODE selects them (build_client)."""
    primary: str                  # "provider:model" of the first step, or "rules" when the chain is empty
    # full method set lives in src/wasel/llm/base.py; the worker never calls it directly


# ---------------------------------------------------------------- output
@dataclass(frozen=True)
class EvidenceSpan:
    """A verified span of a customer message: `message_id[start:end] == quote` on the original text."""
    message_id: str
    start: int                    # code-point offset into the ORIGINAL message text
    end: int                      # exclusive
    kind: SpanKind
    code: FlagCode | None         # set for red_flag, None for address
    quote: str                    # == original_text[start:end]


@dataclass(frozen=True)
class Attempt:
    """One provider call within an extraction run."""
    provider: Literal["groq", "gemini"]
    model: str
    outcome: AttemptOutcome
    latency_ms: int


@dataclass(frozen=True)
class ExtractionRecord:           # -> one extraction_runs row
    """One extraction run, persisted as an extraction_runs row."""
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
    """A valid LLM extraction to upsert into the extraction cache. Never produced for rules or cascade results."""
    input_hash: str
    prompt_version: str
    provider: Literal["groq", "gemini"]
    model: str
    origin_path: Path
    extraction: dict


@dataclass(frozen=True)
class Adjustment:
    """A post-model rule that changed the score (from the customer's reply or a timeout)."""
    rule: Literal["confirmed", "declined", "reschedule", "ambiguous", "no_reply_timeout"]
    label: str                    # "Customer confirmed ×0.6 (starting assumption)"
    effect: str                   # "x0.6" | "+15" | "none"
    before: float
    after: float


@dataclass(frozen=True)
class Factor:                     # top-3 SHAP contributions
    """One feature's contribution to the model score, in score points."""
    feature: str                  # one of ml.features.FEATURES
    label: str
    value: float | int | None
    contribution: float           # score points


@dataclass(frozen=True)
class FlagView:
    """A risk flag that survived evidence checking."""
    code: FlagCode
    quote: str
    message_id: str


@dataclass(frozen=True)
class AssessmentRecord:           # -> one risk_assessments row (ids, version, trigger, created_at added by the persistence layer)
    """One scoring result, persisted as a risk_assessments row.

    Persistence adds ids, version, trigger and created_at. `final_score` is never None; a declined order is scored
    normally and gets action 'cancelled'.
    """
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
    action: Action                            # 'cancelled' iff confirmation == 'declined'; else by tier
                                              # (the rules path included)
    confidence: Literal["high", "low"]
    confidence_reasons: list[str]             # near_tier_boundary | not_primary_model | product_not_in_catalog |
                                              # dropped_flags | clarity_unclear | rules_path | llm_cap_reached |
                                              # injection_suspected | imputed_inputs | no_reply_timeout
    reason: str                               # quotes wrapped in U+2068 … U+2069
    reason_short: str                         # ≤ 90 chars, same builder
    reason_diff: str | None                   # None on version 1
    top_factors: list[Factor]
    classifier_version: str
    config_hash: str
    prompt_version: str
    injection_suspected: bool = False
    points: dict[str, float] = field(default_factory=dict)   # all 6 feature points, feeds the next reason_diff


@dataclass(frozen=True)
class OrderPatch:                 # -> resolved columns on `orders`
    """Columns to write back onto `orders` after scoring. `price_tnd` comes from the seller or the catalog, never the LLM."""
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
    """One LLM provider attempt, persisted as an llm_usage row."""
    ts: datetime
    role: Role
    provider: Literal["groq", "gemini"]
    model: str
    outcome: AttemptOutcome
    tokens_in: int | None
    tokens_out: int | None
    latency_ms: int


@dataclass(frozen=True)
class CoreEvent:                  # -> events row; the persistence layer adds seq, ts, order_id, sandbox_id
    """An event emitted by the scorer or drafter; persistence adds seq, timestamp and order/sandbox ids."""
    type: str                     # 'llm.fallback' | 'llm.cap_reached' | 'cascade.hit' | 'cache.hit' |
                                  # 'evidence.dropped' | 'flags.resolved' | 'extraction.not_order' | 'injection.suspected'
    level: Literal["info", "success", "warning", "error"]
    payload: dict


@dataclass(frozen=True)
class ScoreResult:
    """Everything the scorer produced. The persistence layer writes it in one transaction (repo.persist_result).

    With `is_order` False, `assessment` and `order_patch` are None.
    """
    is_order: bool
    extraction: ExtractionRecord | None   # None only for trigger='no_reply_timeout' (reuses prior.extraction_id)
    cache_put: CacheEntry | None
    assessment: AssessmentRecord | None   # None iff not is_order
    order_patch: OrderPatch | None        # None iff not is_order
    template_id: TemplateId | None        # rule: vague_location -> T_ADDRESS, prepay -> T_PREPAY, else T_CONFIRM
    usage: list[UsageRecord] = field(default_factory=list)
    events: list[CoreEvent] = field(default_factory=list)
    injection_suspected: bool = False     # read by the state machine (next_status checks it first)


# ---------------------------------------------------------------- the calls
Scorer = Callable[[ScoreInput], ScoreResult]
# score_order(inp, *, cache, llm, meter, config) -> ScoreResult      src/wasel/scoring/score_order.py
# make_scorer(*, cache, llm, meter, config) -> Scorer                  functools.partial over score_order


# ---------------------------------------------------------------- drafts (pure; the worker persists)
@dataclass(frozen=True)
class DraftRequest:
    """Inputs to make_draft. Slots come from the order record only, never from customer text."""
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
    """Outcome of the deterministic draft checks."""
    passed: bool
    failures: list[str]


@dataclass(frozen=True)
class DraftRecord:                # -> one outbound_drafts row
    """One drafted outbound message, persisted as an outbound_drafts row (see make_draft)."""
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
# make_draft(req, *, llm, meter, config) -> DraftRecord                src/wasel/outbound/make_draft.py
#   llm=None (DRAFT_LLM=false, the default) -> static template + prefilter only.
