
// ============================================
// CONVERSATIONS
// ============================================

export type MessageRole = 'client' | 'ai';

export interface Message {
    role: MessageRole;
    text: string;
    timestamp: string;
    metadata?: Record<string, any>;
}

export interface ConversationState {
    intent: string;
    collected_info: {
        service?: string;
        date?: string;
        time?: string;
        client_name?: string;
        client_phone?: string;
        [key: string]: any;
    };
    next_question?: string;
    completed: boolean;
}

export interface ConversationResponse {
    id: string;
    conversation_id: string;
    business_id: string;
    phone_number: string;
    client_phone: string;
    source: string;
    messages: Message[];
    state: ConversationState;
    appointment_id?: string;
    created_at: string;
    updated_at: string;
    last_updated: string;
}

export interface ConversationFilters {
    search?: string;
    limit?: number;
}
