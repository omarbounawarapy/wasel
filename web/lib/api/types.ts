// Response types for the /api contract. Mirrors src/wasel/api/models.py; tests/fixtures/api/*.json are the frozen
// examples. Renaming a field in the backend models must be mirrored here, or `tsc --noEmit` fails on the pages.

export type AppMode = 'dev' | 'event' | 'public';
export type Tier = 'low' | 'medium' | 'high';
export type Action = 'ship' | 'confirm' | 'prepay' | 'review' | 'cancelled';
export type Channel = 'whatsapp' | 'csv' | 'paste' | 'simulated';
export type Origin = 'whatsapp' | 'csv' | 'paste' | 'simulated' | 'seed' | 'dashboard';
export type OrderStatus = 'collecting' | 'awaiting_reply' | 'needs_review' | 'ready_to_ship' | 'shipped' | 'delivered' | 'refused' | 'cancelled';
export type RescoreState = 'idle' | 'debouncing' | 'scoring' | 'drafting';
export type ScorePath = 'llm' | 'fallback_model' | 'fallback_provider' | 'cascade_ack' | 'cascade_cache' | 'rules';
export type SellerAction = 'approve' | 'request_confirmation' | 'cancel' | 'ship' | 'mark_delivered' | 'mark_refused';
export type FlagCode = 'availability_uncertain' | 'vague_location' | 'price_hesitation' | 'third_party_recipient' | 'prior_refusal_mention' | 'pressure_or_inconsistency';
export type Zone = 'urban' | 'suburban' | 'rural';
export type ReadBy = 'ai' | 'rules' | 'recorded';

export interface ScoreBadge {
    version: number;
    final_score: number;
    tier: Tier;
    action: Action;
    confidence: 'high' | 'low';
    path: ScorePath;
    read_by: ReadBy;
    delta: number | null;
    reason_short: string;
}

export interface CustomerRef {
    customer_id: string;
    display_name: string | null;
    phone_masked: string | null;
}

export interface OrderSummary {
    order_id: string;
    order_ref: string;
    conversation_id: string;
    customer: CustomerRef;
    channel: Channel;
    status: OrderStatus;
    rescore_state: RescoreState;
    product_name: string | null;
    price_tnd: number | null;
    score: ScoreBadge | null;
    has_pending_draft: boolean;
    is_seeded: boolean;
    read_only: boolean;
    last_message_preview: string | null;
    updated_at: string;
    seed_key?: string | null;
    injection_suspected?: boolean;
}

export interface Counts {
    low: number;
    medium: number;
    high: number;
    needs_review: number;
    awaiting_reply: number;
    ready_to_ship: number;
}

export interface OrderListResponse {
    orders: OrderSummary[];
    counts: Counts;
    server_time: string;
    mode: AppMode;
}

export interface Segment {
    text: string;
    kind: 'risk' | 'address' | null;
    codes: FlagCode[];
    label: string | null;
}

export interface MessageView {
    message_id: string;
    direction: 'inbound' | 'outbound';
    author: 'customer' | 'seller' | 'ai';
    origin: Origin;
    kind: 'text' | 'audio' | 'location' | 'image' | 'interactive' | 'unsupported';
    provider_ts: string;
    text: string | null;
    segments: Segment[] | null;
    transcript: string | null;
    location: { lat: number; lng: number } | null;
    reply_to: { message_id: string; preview: string } | null;
    template_id: 'T_CONFIRM' | 'T_ADDRESS' | 'T_PREPAY' | 'T_ACK' | null;
    delivery_status: 'queued' | 'sent' | 'delivered' | 'read' | 'failed' | null;
}

export interface AdjustmentView {
    rule: string;
    label: string;
    effect: string;
    before: number;
    after: number;
}

export interface FactorView {
    feature: string;
    label: string;
    value: number | null;
    contribution: number;
}

export interface FlagView {
    code: FlagCode;
    label: string;
    quote: string;
    message_id: string;
}

export interface ExtractionView {
    provider: 'groq' | 'gemini' | 'cascade' | 'rules';
    model: string;
    cache_hit: boolean;
    valid: boolean;
    dropped_flags: number;
    latency_ms: number | null;
}

// What the deterministic rules alone would have scored, kept next to the AI read (absent on rules-only runs).
export interface RulesAlone {
    tier: Tier;
    final_score: number;
    reason_short: string;
    top_factor: string | null;
}

export interface AssessmentView {
    assessment_id: string;
    version: number;
    trigger: 'initial' | 'customer_reply' | 'no_reply_timeout' | 'manual';
    created_at: string;
    path: ScorePath;
    read_by: ReadBy;
    model_score: number;
    final_score: number;
    delta: number | null;
    tier: Tier;
    action: Action;
    confidence: 'high' | 'low';
    confidence_reasons: string[];
    confirmation: 'none' | 'confirmed' | 'declined' | 'reschedule' | 'ambiguous';
    reason: string;
    reason_diff: string | null;
    flags: FlagView[];
    resolved_flags: FlagCode[];
    adjustments: AdjustmentView[];
    top_factors: FactorView[];
    rules_alone: RulesAlone | null;
    extraction: ExtractionView | null;
    config_hash: string;
    classifier_version: string;
    prompt_version: string;
}

// The safety checks behind a draft. Fields are optional: the judge is skipped on some paths.
export interface DraftJudge {
    unavailable?: boolean;
    reason?: string;
    decided_by?: string;
    approved?: boolean;
    judge_model?: string;
    unsupported_claims?: string[];
    classifier?: { decision?: 'send' | 'review' | 'block' | string; label?: string; p_unsafe?: number };
}

export interface DraftView {
    draft_id: string;
    assessment_version: number;
    template_id: 'T_CONFIRM' | 'T_ADDRESS' | 'T_PREPAY' | 'T_ACK';
    language: 'fr' | 'ar' | 'darija_arabic_script' | 'arabizi' | 'mixed';
    text: string;
    canonical_text: string;
    source: 'llm_rewrite' | 'static_template';
    route: 'auto_send' | 'needs_review' | 'blocked';
    prefilter: { passed: boolean; failures: string[] };
    judge: DraftJudge | null;
    sent_message_id: string | null;
    sent_at: string | null;
    delivery: 'whatsapp_sent' | 'recorded_only' | null;
    created_at: string;
    decided_by: 'system' | 'human' | null;
}

export interface OrderDetailOrder extends OrderSummary {
    quantity: number | null;
    zone: Zone | null;
    zone_source: 'csv' | 'gazetteer' | 'default';
    address_text: string | null;
    product_id: string | null;
    language: DraftView['language'] | null;
    auto_messages_sent: number;
    awaiting_reply_since: string | null;
    seller_approved_at: string | null;
    opened_at: string;
}

export interface OrderDetailResponse {
    order: OrderDetailOrder;
    customer: CustomerRef & { completed_orders: number; refusals_total: number };
    conversation: { conversation_id: string; channel: Channel; messages: MessageView[] };
    assessments: AssessmentView[];
    drafts: DraftView[];
    capabilities: {
        read_only: boolean;
        can_try: boolean;
        can_simulate_reply: boolean;
        can_rescore: boolean;
        can_send_drafts: boolean;
        actions: SellerAction[];
    };
    scripted_replies: string[];
}

export interface CreatedRef {
    order_id: string;
    order_ref: string;
}

export interface IngestResponse {
    created: CreatedRef[];
    rejected?: { row: number; reason: string }[];
}

export interface EventView {
    seq: number;
    ts: string;
    type: string;
    level: 'info' | 'success' | 'warning' | 'error';
    order_id: string | null;
    order_ref: string | null;
    title: string;
    detail: string | null;
    sample?: boolean;
}

export interface EventsResponse {
    events: EventView[];
    last_seq: number;
}

export interface HealthResponse {
    status: 'ok' | 'degraded';
    mode: AppMode;
    wa_send: boolean;
    webhook: 'enabled' | 'disabled';
    db: boolean;
    demo_mode: boolean;
    real_rows: number;
    sandbox_orders: number;
    wa_auto_send: boolean;
    degraded_reasons: string[];
    degraded_detail: string | null;
}

export interface ImpactResponse {
    simulated: true;
    dataset: string;
    n_orders: number;
    baseline_refusal_rate: number;
    projected_refusal_rate: number;
    trips_avoided: number;
    tnd_saved: number;
    tnd_saved_per_1000_orders: number;
    tnd_saved_per_1000_by_confirm_rate: Record<string, number>;
    assumptions: string[];
}

// The error envelope the API returns on a failed request: {"error": {"code", "message", "details"?}}.
export interface ApiErrorEnvelope {
    error: { code: string; message: string; details?: Record<string, unknown> };
}
