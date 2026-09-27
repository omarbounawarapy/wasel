import { apiClient } from '../api';

export const ordersApi = {
    // Health & System
    health: async () => {
        return apiClient.get('/health');
    },

    // Orders & Queue
    getOrders: async (params?: { tier?: string; include_collecting?: boolean; limit?: number }) => {
        return apiClient.get('/orders', { params });
    },
    
    getOrder: async (orderId: string) => {
        return apiClient.get(`/orders/${orderId}`);
    },

    // Ingestion
    ingestPaste: async (data: { text: string; customer_name?: string; structured?: any }) => {
        return apiClient.post('/orders/ingest', {
            kind: 'paste',
            ...data
        });
    },

    // Actions & Rescoring
    tryOrder: async (orderId: string) => {
        return apiClient.post(`/orders/${orderId}/try`);
    },

    rescoreOrder: async (orderId: string) => {
        return apiClient.post(`/orders/${orderId}/rescore`);
    },

    takeAction: async (orderId: string, action: string) => {
        return apiClient.post(`/orders/${orderId}/actions`, { action });
    },

    // Drafts
    sendDraft: async (draftId: string) => {
        return apiClient.post(`/drafts/${draftId}/send`);
    },

    // Conversations
    simulateTextReply: async (conversationId: string, text: string) => {
        return apiClient.post(`/conversations/${conversationId}/simulate-reply`, {
            kind: 'text',
            text
        });
    },

    simulateLocationReply: async (conversationId: string, lat: number, lng: number) => {
        return apiClient.post(`/conversations/${conversationId}/simulate-reply`, {
            kind: 'location',
            lat,
            lng
        });
    },

    // Events (for activity and toast updates)
    getEvents: async (params?: { after?: number; order_id?: string; limit?: number }) => {
        return apiClient.get('/events', { params });
    },

    // Analytics
    getImpact: async () => {
        return apiClient.get('/metrics/impact');
    },
    
    getEvalReports: async () => {
        return apiClient.get('/eval');
    },
    
    getFailures: async (source: string = 'synthetic') => {
        return apiClient.get('/failures', { params: { source } });
    },

    getFailureSession: async (sessionId: string, source: string = 'synthetic') => {
        return apiClient.get(`/failures/sessions/${sessionId}`, { params: { source } });
    },

    // Observability
    getMonitor: async () => {
        return apiClient.get('/monitor');
    },

    getTraces: async (params?: { role?: string; order_id?: string; limit?: number }) => {
        return apiClient.get('/traces', { params });
    },
};
