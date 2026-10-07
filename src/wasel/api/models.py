"""The /api contract: Pydantic request and response models.

Response models are what the web UI and dashboard receive; none of them carries phone_e164 or raw_payload (numbers
appear only masked). Request models (PasteIngest, CsvIngest, SimulateText, ...) validate input at the route boundary.
`seed_key`, `injection_suspected` and `visitor_cap` are optional additions with defaults, so older clients keep working."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AppMode = Literal["dev", "event", "public"]
Tier = Literal["low", "medium", "high"]
Action = Literal["ship", "confirm", "prepay", "review", "cancelled"]
Channel = Literal["whatsapp", "csv", "paste", "simulated"]
Origin = Literal["whatsapp", "csv", "paste", "simulated", "seed", "dashboard"]
OrderStatus = Literal["collecting", "awaiting_reply", "needs_review", "ready_to_ship", "shipped", "delivered",
                      "refused", "cancelled"]
RescoreState = Literal["idle", "debouncing", "scoring", "drafting"]
Trigger = Literal["initial", "customer_reply", "no_reply_timeout", "manual"]
Path = Literal["llm", "fallback_model", "fallback_provider", "cascade_ack", "cascade_cache", "rules"]
Confirmation = Literal["none", "confirmed", "declined", "reschedule", "ambiguous"]
SellerAction = Literal["approve", "request_confirmation", "cancel", "ship", "mark_delivered", "mark_refused"]
FlagCode = Literal["availability_uncertain", "vague_location", "price_hesitation", "third_party_recipient",
                   "prior_refusal_mention", "pressure_or_inconsistency"]
TemplateId = Literal["T_CONFIRM", "T_ADDRESS", "T_PREPAY", "T_ACK"]
Zone = Literal["urban", "suburban", "rural"]
ZoneSource = Literal["csv", "gazetteer", "default"]
Language = Literal["fr", "ar", "darija_arabic_script", "arabizi", "mixed"]


class ScoreBadge(BaseModel):
    """Latest assessment of an order, as shown on a queue row.

    `delta` is final_score minus the previous version's final_score (None on version 1).
    """
    version: int
    final_score: int
    tier: Tier
    action: Action
    confidence: Literal["high", "low"]
    path: Path
    delta: int | None
    reason_short: str


class CustomerRef(BaseModel):
    """Customer identity as exposed to the UI. `phone_masked` is display-masked; the raw number never leaves the server."""
    customer_id: str
    display_name: str | None
    phone_masked: str | None


class OrderSummary(BaseModel):
    """One row of the order queue.

    `is_seeded` means the order has no sandbox owner (sample/event data). `read_only` is only true for seeded orders in
    public mode. `last_message_preview` is the first 80 characters of the latest inbound text, bidi controls stripped.
    `score` is None until the first assessment exists.
    """
    order_id: str
    order_ref: str
    conversation_id: str
    customer: CustomerRef
    channel: Channel
    status: OrderStatus
    rescore_state: RescoreState
    product_name: str | None
    price_tnd: float | None
    score: ScoreBadge | None
    has_pending_draft: bool
    is_seeded: bool
    read_only: bool
    last_message_preview: str | None
    updated_at: str
    seed_key: str | None = None
    injection_suspected: bool = False            # the latest extraction flagged instruction-like text


class Counts(BaseModel):
    """Tier and status tallies over the orders in the same response, not over the whole table (so they respect the
    filters and the row limit).
    """
    low: int
    medium: int
    high: int
    needs_review: int
    awaiting_reply: int
    ready_to_ship: int


class OrderListResponse(BaseModel):
    """GET /api/orders. Sorted riskiest first, unscored orders last. `server_time` is UTC ISO-8601."""
    orders: list[OrderSummary]
    counts: Counts
    server_time: str
    mode: AppMode


class Segment(BaseModel):
    """A slice of a customer message with the same evidence markup.

    Segments are cut server-side on the original text; concatenating `text` over a message's segments reproduces the
    bidi-stripped text. `kind='risk'` wins over 'address' where spans overlap; `codes` lists the risk flags
    covering the slice.
    """
    text: str
    kind: Literal["risk", "address"] | None
    codes: list[FlagCode]
    label: str | None


class Location(BaseModel):
    """WhatsApp location pin, WGS84 degrees."""
    lat: float
    lng: float


class ReplyTo(BaseModel):
    """The message a WhatsApp reply quotes. `preview` is at most 80 characters."""
    message_id: str
    preview: str


class MessageView(BaseModel):
    """One message in the thread, oldest first.

    author 'ai' is a sent draft (`text` is what was sent, which may be an LLM rewrite of the template). `segments` is set
    only for customer text; `delivery_status` only for outbound messages that went through WhatsApp.
    """
    message_id: str
    direction: Literal["inbound", "outbound"]
    author: Literal["customer", "seller", "ai"]
    origin: Origin
    kind: Literal["text", "audio", "location", "image", "interactive", "unsupported"]
    provider_ts: str
    text: str | None
    segments: list[Segment] | None
    transcript: str | None
    location: Location | None
    reply_to: ReplyTo | None
    template_id: TemplateId | None
    delivery_status: Literal["queued", "sent", "delivered", "read", "failed"] | None


class AdjustmentView(BaseModel):
    """A post-model score adjustment (customer confirmed, declined, ...). `before`/`after` are model-scale scores."""
    rule: str
    label: str
    effect: str
    before: float
    after: float


class FlagViewModel(BaseModel):
    """A surviving, evidence-checked risk flag. `quote` is verbatim text from message `message_id`."""
    code: FlagCode
    label: str
    quote: str
    message_id: str


class FactorView(BaseModel):
    """One of the top feature contributions to the model score. `contribution` is in score points; `value` is None when
    the feature was imputed.
    """
    feature: str
    label: str
    value: float | None
    contribution: float


class ExtractionView(BaseModel):
    """Provenance of the extraction behind an assessment. `provider` 'cascade' and 'rules' mean no LLM call was made;
    `valid` is False when no usable extraction came out of the run.
    """
    provider: Literal["groq", "gemini", "cascade", "rules"]
    model: str
    cache_hit: bool
    valid: bool
    dropped_flags: int
    latency_ms: int | None


class AssessmentView(BaseModel):
    """One scoring run (a version) of an order.

    `model_score` is the raw classifier score and `final_score` is after `adjustments`. Both are 0-100. `reason_diff` is None
    on version 1. `extraction` is None when the run reused a prior extraction (no-reply timeout).
    """
    assessment_id: str
    version: int
    trigger: Trigger
    created_at: str
    path: Path
    model_score: float
    final_score: int
    delta: int | None
    tier: Tier
    action: Action
    confidence: Literal["high", "low"]
    confidence_reasons: list[str]
    confirmation: Confirmation
    reason: str
    reason_diff: str | None
    adjustments: list[AdjustmentView]
    resolved_flags: list[FlagCode]
    flags: list[FlagViewModel]
    top_factors: list[FactorView]
    extraction: ExtractionView | None
    config_hash: str
    classifier_version: str
    prompt_version: str


class PrefilterView(BaseModel):
    """Result of the deterministic checks on a draft. `failures` is empty when `passed`."""
    passed: bool
    failures: list[str]


class DraftView(BaseModel):
    """An outbound message drafted for an order.

    `text` is what would be (or was) sent; `canonical_text` is the static template it derives from. `route` says whether
    it may auto-send, needs a person, or is blocked. `decided_by` is set once sent: 'system' means auto-send, no click.
    """
    draft_id: str
    assessment_version: int
    template_id: TemplateId
    language: Language
    text: str
    canonical_text: str
    source: Literal["llm_rewrite", "static_template"]
    route: Literal["auto_send", "needs_review", "blocked"]
    prefilter: PrefilterView
    judge: dict | None
    sent_message_id: str | None
    sent_at: str | None
    delivery: Literal["whatsapp_sent", "recorded_only"] | None
    created_at: str
    decided_by: Literal["system", "human"] | None = None     # "system" = sent by auto-send, no click


class Capabilities(BaseModel):
    """What the UI may offer for this order right now; derived from mode, seeded state and order status. `actions`
    holds the seller actions valid from the current status.
    """
    read_only: bool
    can_try: bool
    can_simulate_reply: bool
    can_rescore: bool
    can_send_drafts: bool
    actions: list[SellerAction]


class OrderDetailOrder(OrderSummary):
    """OrderSummary plus the resolved order columns. `zone_source` records where the zone came from."""
    quantity: int | None
    zone: Zone | None
    zone_source: ZoneSource
    address_text: str | None
    product_id: str | None
    language: Language | None
    auto_messages_sent: int
    awaiting_reply_since: str | None
    seller_approved_at: str | None
    opened_at: str


class CustomerDetail(CustomerRef):
    """Customer history that feeds the score: delivered plus refused orders, and refusals."""
    completed_orders: int
    refusals_total: int


class ConversationView(BaseModel):
    """The message thread linked to an order."""
    conversation_id: str
    channel: Channel
    messages: list[MessageView]


class OrderDetailResponse(BaseModel):
    """GET /api/orders/{id}. `assessments` run oldest to newest; `drafts` newest first.

    `scripted_replies` are the canned customer replies offered for seeded sample orders (empty otherwise).
    """
    order: OrderDetailOrder
    customer: CustomerDetail
    conversation: ConversationView
    assessments: list[AssessmentView]
    drafts: list[DraftView]
    capabilities: Capabilities
    scripted_replies: list[str]


# ---------------------------------------------------------------- commands
class StructuredIn(BaseModel):
    """Seller-entered order fields. When set they take precedence over the catalog and gazetteer."""
    product_name: str | None = None
    price_tnd: float | None = Field(default=None, ge=0)
    zone: Zone | None = None
    quantity: int | None = Field(default=None, ge=1, le=50)


class PasteIngest(BaseModel):
    """Request body: one pasted customer message becomes one order. Text is at most 2000 characters, name 40."""
    kind: Literal["paste"]
    text: str = Field(min_length=1)
    customer_name: str | None = Field(default=None, max_length=40)
    structured: StructuredIn | None = None


class CsvIngest(BaseModel):
    """Request body: several orders as CSV text (columns in commands.CSV_HEADER).

    At most 10 rows in public mode, 200 otherwise.
    """
    kind: Literal["csv"]
    csv_text: str


class CreatedRef(BaseModel):
    """Identifiers of one order created by ingest."""
    order_id: str
    order_ref: str
    conversation_id: str
    message_id: str | None


class Rejected(BaseModel):
    """A CSV row that was not ingested; `row` is 1-based (header excluded)."""
    row: int
    reason: str


class IngestResponse(BaseModel):
    """Result of an ingest. Scoring is asynchronous: `rescore_eta_s` estimates when the worker will have scored them."""
    created: list[CreatedRef]
    rejected: list[Rejected]
    rescore_eta_s: float


class TryResponse(BaseModel):
    """The visitor's own copy of a seeded sample order."""
    order_id: str
    order_ref: str
    conversation_id: str


class SimulateText(BaseModel):
    """Request body: a simulated customer text reply (max 600 characters)."""
    kind: Literal["text"]
    text: str = Field(min_length=1)


class SimulateLocation(BaseModel):
    """Request body: a simulated customer location pin."""
    kind: Literal["location"]
    lat: float
    lng: float


class SimulateReplyResponse(BaseModel):
    """`rescore_at` is when the debounced rescore is due. `recorded_draft_id` is the unsent draft that was
    marked as sent by this reply, if there was one.
    """
    message_id: str
    order_id: str
    rescore_at: str | None
    recorded_draft_id: str | None


class RescoreResponse(BaseModel):
    """A manual rescore has been queued; `rescore_at` is when it is due."""
    order_id: str
    rescore_state: RescoreState
    rescore_at: str


class SellerActionRequest(BaseModel):
    """Request body for a status-changing seller action. `note` is accepted but not stored."""
    action: SellerAction
    note: str | None = None


class SendDraftResponse(BaseModel):
    """`delivery` is 'whatsapp_sent' only for a real WhatsApp send; 'recorded_only' means the draft was recorded as sent
    in the conversation without leaving the system.
    """
    draft_id: str
    sent_message_id: str
    sent_at: str
    delivery: Literal["whatsapp_sent", "recorded_only"]


class EventView(BaseModel):
    """One activity-feed entry. `title` and `detail` are rendered server-side from the event payload (see event_text)."""
    seq: int
    ts: str
    type: str
    level: Literal["info", "success", "warning", "error"]
    order_id: str | None
    order_ref: str | None
    title: str
    detail: str | None


class EventsResponse(BaseModel):
    """Events with seq greater than the requested cursor, oldest first. `last_seq` is the cursor for the next poll (the
    request's `after` value when nothing is new).
    """
    events: list[EventView]
    last_seq: int


class HealthBuild(BaseModel):
    """Build identity of the running process."""
    git_sha: str
    started_at: str


class HealthConfig(BaseModel):
    """Versions of the artifacts behind every score; `seed_version` is the demo seed file version."""
    config_hash: str
    prompt_version: str
    classifier_version: str
    seed_version: int
    seed_captured_at: str | None = None


class HealthLLM(BaseModel):
    """LLM chain status. `live_calls_today` counts provider calls on the current UTC day; `live_call_cap` is None
    when unlimited. `fallback_active` is true when an assessment in the last five minutes took a fallback or rules path.
    """
    llm_mode: Literal["live", "replay", "fail_primary", "fail_all", "fail_groq"]
    chain_extract: list[str]
    chain_judge: list[str]
    primary: str
    fallback_active: bool
    fallback_reason: str | None
    last_path: Path | None
    last_call_at: str | None
    remaining_tokens: int | None
    live_calls_today: int
    live_call_cap: int | None
    cap_reached: bool
    visitor_cap: dict | None = None              # per-visitor LLM caps (public mode only)


class HealthWhatsApp(BaseModel):
    """`last_webhook_at` is the last POST with a valid signature since process start."""
    last_webhook_at: str | None


class HealthWorker(BaseModel):
    """`pending` is the number of orders with a rescore scheduled."""
    last_tick_at: str | None
    pending: int
    last_purge_at: str | None


class HealthResponse(BaseModel):
    """GET /api/health. `status` is 'degraded' when a fallback path was used in the last five minutes or the worker
    has not ticked for over 10 s. `wa_send` and `wa_auto_send` are the effective settings, already forced off in public mode.
    """
    status: Literal["ok", "degraded"]
    mode: AppMode
    wa_send: bool
    webhook: Literal["enabled", "disabled"]
    db: bool
    demo_mode: bool
    build: HealthBuild
    config: HealthConfig
    llm: HealthLLM
    whatsapp: HealthWhatsApp
    worker: HealthWorker
    wa_token_present: bool = False
    real_rows: int = 0                            # conversations that arrived over WhatsApp
    sandbox_orders: int = 0
    wa_auto_send: bool = False                    # auto_send drafts go out without a click (never public)
    degraded_reason: Literal["seed_unscored"] | None = None   # set when seeded orders have no assessment


class ImpactResponse(BaseModel):
    """GET /api/metrics/impact. Always simulated: numbers come from data/reports/impact.json over the synthetic holdout,
    not from field results. Fields are zero or empty when the report is missing.
    """
    simulated: Literal[True]
    dataset: str
    n_orders: int
    baseline_refusal_rate: float
    projected_refusal_rate: float
    trips_avoided: float
    tnd_saved: float
    assumptions: list[str]


class ResetResponse(BaseModel):
    """Result of the admin reset: `purged_rows` orders deleted and `reseeded_orders` orders recreated from the seed."""
    reseeded_orders: int
    purged_rows: int
