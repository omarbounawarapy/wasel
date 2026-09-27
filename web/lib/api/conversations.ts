/**
 * Conversations API Service
 */

import api from '@/lib/api';
import type { ConversationResponse, ConversationFilters } from '@/lib/types';

export const conversationsApi = {
    /**
     * List all conversations with optional search
     */
    list: async (filters?: ConversationFilters): Promise<ConversationResponse[]> => {
        const response = await api.get<ConversationResponse[]>('/conversations/', {
            params: filters,
        });
        return response;
    },

    /**
     * Get a single conversation by ID
     */
    get: async (conversationId: string): Promise<ConversationResponse> => {
    const response = await api.get<ConversationResponse>(`/conversations/${conversationId}`);
    return response;
    },

    /**
     * Search conversations by phone number
     */
    searchByPhone: async (phoneNumber: string): Promise<ConversationResponse[]> => {
        return conversationsApi.list({ search: phoneNumber });
    },

    /**
     * Get recent conversations (last 50)
     */
    getRecent: async (limit: number = 50): Promise<ConversationResponse[]> => {
        return conversationsApi.list({ limit });
    },

    /**
     * Delete a conversation by ID
     */
    delete: async (conversationId: string): Promise<void> => {
        await api.delete(`/conversations/${conversationId}`);
    },
};
