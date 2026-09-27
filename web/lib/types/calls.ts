export interface CallListItem {
    callId: string;
    createdAt: string | null;
    clientPhoneNumber: string | null;
    durationSeconds: number;
    status: string | null;
    endedReason: string | null;
}

export interface CallsListResponse {
    items: CallListItem[];
    page: number;
    limit: number;
    hasMore: boolean;
}

export interface CallTranscriptMessage {
    role: "client" | "ai";
    text: string;
    timestamp?: string | null;
}

export interface CallDetailResponse {
    callId: string;
    clientPhoneNumber: string | null;
    ourPhoneNumber: string | null;
    createdAt: string | null;
    durationSeconds: number;
    status: string | null;
    endedReason: string | null;
    assistantId: string | null;
    messages: CallTranscriptMessage[];
}
