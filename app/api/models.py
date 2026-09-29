"""THE API CONTRACT: Pydantic request/response models mirroring web/src/api/types.ts.
Additive fields per R8: OrderSummary.seed_key, OrderSummary.injection_suspected, HealthResponse.llm.visitor_cap.
No response model carries phone_e164 or raw_payload (P6)."""
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
    version: int
    final_score: int
    tier: Tier
    action: Action
    confidence: Literal["high", "low"]
    path: Path
    delta: int | None
    reason_short: str


class CustomerRef(BaseModel):
    customer_id: str
    display_name: str | None
    phone_masked: str | None


class OrderSummary(BaseModel):
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
    seed_key: str | None = None                  # R8 additive
    injection_suspected: bool = False            # R8 additive


class Counts(BaseModel):
    low: int
    medium: int
    high: int
    needs_review: int
    awaiting_reply: int
    ready_to_ship: int


class OrderListResponse(BaseModel):
    orders: list[OrderSummary]
    counts: Counts
    server_time: str
    mode: AppMode


class Segment(BaseModel):
    text: str
    kind: Literal["risk", "address"] | None
    codes: list[FlagCode]
    label: str | None


class Location(BaseModel):
    lat: float
    lng: float


class ReplyTo(BaseModel):
    message_id: str
    preview: str


class MessageView(BaseModel):
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
    rule: str
    label: str
    effect: str
    before: float
    after: float


class FlagViewModel(BaseModel):
    code: FlagCode
    label: str
    quote: str
    message_id: str


class FactorView(BaseModel):
    feature: str
    label: str
    value: float | None
    contribution: float


class ExtractionView(BaseModel):
    provider: Literal["groq", "gemini", "cascade", "rules"]
    model: str
    cache_hit: bool
    valid: bool
    dropped_flags: int
    latency_ms: int | None


class AssessmentView(BaseModel):
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
    passed: bool
    failures: list[str]


class DraftView(BaseModel):
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
    decided_by: Literal["system", "human"] | None = None     # additive: "system" = sent by auto-send, no click


class Capabilities(BaseModel):
    read_only: bool
    can_try: bool
    can_simulate_reply: bool
    can_rescore: bool
    can_send_drafts: bool
    actions: list[SellerAction]


class OrderDetailOrder(OrderSummary):
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
    completed_orders: int
    refusals_total: int


class ConversationView(BaseModel):
    conversation_id: str
    channel: Channel
    messages: list[MessageView]


class OrderDetailResponse(BaseModel):
    order: OrderDetailOrder
    customer: CustomerDetail
    conversation: ConversationView
    assessments: list[AssessmentView]
    drafts: list[DraftView]
    capabilities: Capabilities
    scripted_replies: list[str]


# ---------------------------------------------------------------- commands
class StructuredIn(BaseModel):
    product_name: str | None = None
    price_tnd: float | None = Field(default=None, ge=0)
    zone: Zone | None = None
    quantity: int | None = Field(default=None, ge=1, le=50)


class PasteIngest(BaseModel):
    kind: Literal["paste"]
    text: str = Field(min_length=1)
    customer_name: str | None = Field(default=None, max_length=40)
    structured: StructuredIn | None = None


class CsvIngest(BaseModel):
    kind: Literal["csv"]
    csv_text: str


class CreatedRef(BaseModel):
    order_id: str
    order_ref: str
    conversation_id: str
    message_id: str | None


class Rejected(BaseModel):
    row: int
    reason: str


class IngestResponse(BaseModel):
    created: list[CreatedRef]
    rejected: list[Rejected]
    rescore_eta_s: float


class TryResponse(BaseModel):
    order_id: str
    order_ref: str
    conversation_id: str


class SimulateText(BaseModel):
    kind: Literal["text"]
    text: str = Field(min_length=1)


class SimulateLocation(BaseModel):
    kind: Literal["location"]
    lat: float
    lng: float


class SimulateReplyResponse(BaseModel):
    message_id: str
    order_id: str
    rescore_at: str | None
    recorded_draft_id: str | None


class RescoreResponse(BaseModel):
    order_id: str
    rescore_state: RescoreState
    rescore_at: str


class SellerActionRequest(BaseModel):
    action: SellerAction
    note: str | None = None


class SendDraftResponse(BaseModel):
    draft_id: str
    sent_message_id: str
    sent_at: str
    delivery: Literal["whatsapp_sent", "recorded_only"]


class EventView(BaseModel):
    seq: int
    ts: str
    type: str
    level: Literal["info", "success", "warning", "error"]
    order_id: str | None
    order_ref: str | None
    title: str
    detail: str | None


class EventsResponse(BaseModel):
    events: list[EventView]
    last_seq: int


class HealthBuild(BaseModel):
    git_sha: str
    started_at: str


class HealthConfig(BaseModel):
    config_hash: str
    prompt_version: str
    classifier_version: str
    seed_version: int
    seed_captured_at: str | None = None          # R8


class HealthLLM(BaseModel):
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
    visitor_cap: dict | None = None              # R8 additive


class HealthWhatsApp(BaseModel):
    last_webhook_at: str | None


class HealthWorker(BaseModel):
    last_tick_at: str | None
    pending: int
    last_purge_at: str | None


class HealthResponse(BaseModel):
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
    real_rows: int = 0                            
    sandbox_orders: int = 0
    wa_auto_send: bool = False                    # additive: auto_send drafts go out without a click (never public)


class ImpactResponse(BaseModel):
    simulated: Literal[True]
    dataset: str
    n_orders: int
    baseline_refusal_rate: float
    projected_refusal_rate: float
    trips_avoided: float
    tnd_saved: float
    assumptions: list[str]


class ResetResponse(BaseModel):
    reseeded_orders: int
    purged_rows: int
