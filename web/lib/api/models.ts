export type AppMode = "dev" | "event" | "public";
export type Tier = "low" | "medium" | "high";
export type Action = "ship" | "confirm" | "prepay" | "review" | "cancelled";
export type Channel = "whatsapp" | "csv" | "paste" | "simulated";
export type Origin = "whatsapp" | "csv" | "paste" | "simulated" | "seed" | "dashboard";
export type OrderStatus = "collecting" | "awaiting_reply" | "needs_review" | "ready_to_ship" | "shipped" | "delivered" | "refused" | "cancelled";
export type RescoreState = "idle" | "debouncing" | "scoring" | "drafting";
export type Trigger = "initial" | "customer_reply" | "no_reply_timeout" | "manual";
export type Path = "llm" | "fallback_model" | "fallback_provider" | "cascade_ack" | "cascade_cache" | "rules";
export type Confirmation = "none" | "confirmed" | "declined" | "reschedule" | "ambiguous";
export type SellerAction = "approve" | "request_confirmation" | "cancel" | "ship" | "mark_delivered" | "mark_refused";
export type FlagCode = "availability_uncertain" | "vague_location" | "price_hesitation" | "third_party_recipient" | "prior_refusal_mention" | "pressure_or_inconsistency";
export type TemplateId = "T_CONFIRM" | "T_ADDRESS" | "T_PREPAY" | "T_ACK";
export type Zone = "urban" | "suburban" | "rural";
export type ZoneSource = "csv" | "gazetteer" | "default";
export type Language = "fr" | "ar" | "darija_arabic_script" | "arabizi" | "mixed";

export interface ScoreBadge {
    version: number;
    final_score: number;
    tier: Tier;
    action: Action;
    confidence: "high" | "low";
    path: Path;
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
