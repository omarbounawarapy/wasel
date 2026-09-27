
// ============================================
// VOICE AGENT
// ============================================

export interface VoiceStartCallRequest {
    customer_number: string;
    customer_name?: string;
    metadata?: Record<string, any>;
}

export interface VoiceStartCallResponse {
    status: string;
    call_id: string;
    assistant_id?: string;
}

export interface VoiceTestResponse {
    status: string;
    message: string;
    agent_id?: string;
}

export interface VoiceAgentStatus {
    configured: boolean;
    url: string;
    agent_queue: string;
    agent_name: string;
    voice_agent_enabled: boolean;
    tenant_id: string;
    phone_number?: string;
    number_status?: string;
    country?: string;
    sip_trunks?: any;
}



export interface VoiceCallHistoryItem {
    id: string;
    call_id?: string;
    status: string;
    customer?: {
        number?: string;
        name?: string;
    };
    cost?: number;
    created_at?: string;
    metadata?: Record<string, any>;
    business_id?: string;
    assistant_id?: string;
}

export interface VoiceCallHistoryResponse {
    items: VoiceCallHistoryItem[];
    count: number;
}

export interface VoiceWebRTCResponse {
    room_name: string;
    token: string;
    url: string;
    agent_queue: string;
    agent_name: string;
}

// Voice Configuration Types
export interface VoiceConfiguration {
    model_provider: string;
    model_name: string;
    temperature: number;
    max_tokens: number;
    voice_provider: string;
    voice_id: string;
    first_message: string;
    system_prompt: string;
    enabled_tools: string[];
    end_call_on_goodbye: boolean;
    record_calls: boolean;
    silence_timeout_seconds: number;
}

export interface VoiceModel {
    id: string;
    name: string;
    provider: string;
}

export interface VoiceOption {
    voice_id: string;
    name: string;
    category: string;
    description?: string;
    provider?: string;
    accent?: string;
    gender?: string;
    age?: string;
    preview_url?: string;
    use_case?: string;
}

export interface VoiceTool {
    type: string;
    function: {
        name: string;
        description: string;
        parameters: {
            type: string;
            properties: Record<string, any>;
            required: string[];
        };
    };
}

export type AgentStatus = 'draft' | 'active' | 'paused';
export type VoiceProvider = 'elevenlabs' | 'openai' | 'deepgram' | 'cartesia';

export interface VoiceSettings {
    provider: VoiceProvider;
    voice_id: string;
    model?: string;
    stability?: number;
    similarity_boost?: number;
}

export interface AgentTools {
    check_availability: boolean;
    book_appointment: boolean;
    cancel_appointment: boolean;
    update_appointment: boolean;
    get_business_info: boolean;
}

export interface Agent {
    _id: string; // Alias for id in backend but generic here
    id: string;
    name: string;
    tenant_id: string;
    system_prompt: string;
    voice_settings: VoiceSettings;
    llm_model: string;
    llm_temperature: number;
    stt_model: string;
    tts_model: string;
    tools_config: AgentTools;
    greeting_enabled: boolean;
    greeting_message: string;
    webhook_urls?: {
        get_slots: string;
        book: string;
        update: string;
        cancel: string;
    };
    avatar_url?: string;
    phone_number?: string;
    description?: string;
    status: AgentStatus;
    created_at: string;
    updated_at: string;
}

export interface AgentUpdate {
    name?: string;
    system_prompt?: string;
    voice_settings?: VoiceSettings;
    llm_model?: string;
    llm_temperature?: number;
    stt_model?: string;
    tts_model?: string;
    tools_config?: AgentTools;
    greeting_enabled?: boolean;
    greeting_message?: string;
    avatar_url?: string;
    status?: AgentStatus;
}
