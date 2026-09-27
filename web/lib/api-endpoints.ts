import api from "@/lib/api"
import type {
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentFilters,
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceFilters,
    ConversationResponse,
    UserResponse,
    VoiceAgentStatus,
    VoiceWebRTCResponse,
} from "@/lib/types"

// API Base URL for direct fetch calls
// In production (Vercel), this MUST be set to the Railway backend URL
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== 'undefined'
        ? window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : `http://${window.location.hostname}:8000`
        : '');

// Check for placeholder URLs
if (typeof window !== 'undefined' && BASE_URL && BASE_URL.includes('your-railway-url')) {
    console.error(
        '❌ NEXT_PUBLIC_API_URL contains placeholder value! ' +
        'Please update it in Vercel environment variables to your actual Railway backend URL.'
    );
}

const API_BASE_URL = BASE_URL ? `${BASE_URL}/api/v1` : '/api/v1';

export const appointmentsApi = {
    list: async (filters?: AppointmentFilters): Promise<AppointmentResponse[]> => {
        const response = await api.get<AppointmentResponse[]>("/appointments/", {
            params: filters,
        })
        return response
    },

    get: async (appointmentId: string): Promise<AppointmentResponse> => {
        const response = await api.get<AppointmentResponse>(`/appointments/${appointmentId}`)
        return response
    },

    create: async (data: AppointmentCreate): Promise<AppointmentResponse> => {
        const response = await api.post<AppointmentResponse>("/appointments/", data)
        return response
    },

    update: async (appointmentId: string, data: AppointmentUpdate): Promise<AppointmentResponse> => {
        const response = await api.put<AppointmentResponse>(`/appointments/${appointmentId}`, data)
        return response
    },

    delete: async (appointmentId: string): Promise<void> => {
        await api.delete(`/appointments/${appointmentId}`)
    },

    cancel: async (appointmentId: string): Promise<AppointmentResponse> => {
        const response = await api.post<AppointmentResponse>(`/appointments/${appointmentId}/cancel`)
        return response
    },

    checkAvailability: async (
        date: string,
        time: string,
        durationMinutes: number = 30,
    ): Promise<{
        available: boolean
        requested_datetime: string
        duration_minutes: number
        reason: string
    }> => {
        const response = await api.get("/appointments/availability/check", {
            params: {
                date,
                time,
                duration_minutes: durationMinutes,
            },
        })
        return response
    },

    getStats: async (): Promise<{
        total: number
        upcoming: number
        by_status: Record<string, number>
    }> => {
        const response = await api.get("/appointments/stats/summary")
        return response
    },
}

export const servicesApi = {
    list: async (filters?: ServiceFilters): Promise<ServiceResponse[]> => {
        const response = await api.get<ServiceResponse[]>("/services/", {
            params: filters,
        })
        return response
    },

    get: async (serviceId: string): Promise<ServiceResponse> => {
        const response = await api.get<ServiceResponse>(`/services/${serviceId}`)
        return response
    },

    create: async (data: ServiceCreate): Promise<ServiceResponse> => {
        const response = await api.post<ServiceResponse>("/services/", data)
        return response
    },

    update: async (serviceId: string, data: ServiceUpdate): Promise<ServiceResponse> => {
        const response = await api.put<ServiceResponse>(`/services/${serviceId}`, data)
        return response
    },

    delete: async (serviceId: string): Promise<void> => {
        await api.delete(`/services/${serviceId}`)
    },

    getActive: async (): Promise<ServiceResponse[]> => {
        return servicesApi.list({ active_only: true })
    },

    toggleActive: async (serviceId: string, isActive: boolean): Promise<ServiceResponse> => {
        return servicesApi.update(serviceId, { active: isActive })
    },
}

export const conversationsApi = {
    list: async (params?: { search?: string; limit?: number }): Promise<ConversationResponse[]> => {
        const response = await api.get<ConversationResponse[]>("/conversations/", {
            params,
        })
        return response
    },

    get: async (id: string): Promise<ConversationResponse> => {
        const response = await api.get<ConversationResponse>(`/conversations/${id}`)
        return response
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`/conversations/${id}`)
    },
}

export const webhookApi = {
    getStatus: async (): Promise<any> => {
        const response = await api.get("/whatsapp/status")
        return response
    },

    updateSettings: async (settings: any): Promise<any> => {
        const response = await api.post("/whatsapp/settings", settings)
        return response
    }
}

export const usersApi = {
    list: async (tenantId?: string): Promise<UserResponse[]> => {
        const response = await api.get<UserResponse[]>("/admin/users", {
            params: { tenant_id: tenantId },
        })
        return response
    },

    create: async (data: Partial<UserResponse>): Promise<UserResponse> => {
        const response = await api.post<UserResponse>("/admin/users", data)
        return response
    },

    delete: async (id: string): Promise<void> => {
        await api.delete(`/admin/users/${id}`)
    },
}

// Agents API with proper typing
export const apiEndpoints = {
    agents: {
        getMyAgent: (): string => `${API_BASE_URL}/agents/my-agent`,
        updateMyAgent: (): string => `${API_BASE_URL}/agents/my-agent`,
        // Deprecated: Old multi-agent endpoints kept for backward compatibility
        list: (): string => `${API_BASE_URL}/agents`,
        get: (id: string): string => `${API_BASE_URL}/agents/${id}`,
        create: (): string => `${API_BASE_URL}/agents`,
        update: (id: string): string => `${API_BASE_URL}/agents/${id}`,
        delete: (id: string): string => `${API_BASE_URL}/agents/${id}`,
    },
    voiceAgent: {
        // Temporarily keep but point to Vapi stats if possible, or dead endpoint
        stats: (): string => `${API_BASE_URL}/voice-agent/stats`,
        phoneNumbers: (): string => `${API_BASE_URL}/voice-agent/numbers`,
        searchNumbers: (): string => `${API_BASE_URL}/voice-agent/search-numbers`,
        purchaseNumber: (): string => `${API_BASE_URL}/voice-agent/purchase-number`,
    },
    phoneNumbers: {
        test: (): string => `${API_BASE_URL}/phone-numbers/test`,
        search: (): string => `${API_BASE_URL}/phone-numbers/search`,
        purchase: (): string => `${API_BASE_URL}/phone-numbers/purchase`,
        list: (): string => `${API_BASE_URL}/phone-numbers/list`,
        assign: (id: string): string => `${API_BASE_URL}/phone-numbers/${id}/assign`,
        delete: (id: string): string => `${API_BASE_URL}/phone-numbers/${id}`,
    },
    onboarding: {
        getStatus: (): string => `${API_BASE_URL}/onboarding/status`,
        skipOnboarding: (): string => `${API_BASE_URL}/onboarding/skip`,
    },
    vapi: {
        createAssistant: (tenantId: string): string => `${API_BASE_URL}/vapi/tenants/${tenantId}/assistant`,
        updateAssistant: (tenantId: string, assistantId: string): string => `${API_BASE_URL}/vapi/tenants/${tenantId}/assistant/${assistantId}`,
        getAssistant: (tenantId: string): string => `${API_BASE_URL}/vapi/tenants/${tenantId}/assistant`,
        // 'Me' endpoints
        getMyAssistant: (): string => `${API_BASE_URL}/vapi/assistant/me`,
        createMyAssistant: (): string => `${API_BASE_URL}/vapi/assistant/me`,
        updateMyAssistant: (): string => `${API_BASE_URL}/vapi/assistant/me`,
    }
}

export const phoneApi = {
    // Get phone number status
    getStatus: async (tenantId: string): Promise<any> => {
        return await api.get(`/phone-numbers/status/${tenantId}`);
    },
    // Sync phone numbers from Vapi dashboard
    syncFromVapi: async (tenantId: string): Promise<any> => {
        return await api.post(`/phone-numbers/sync/${tenantId}`, {});
    },
    // Provision new phone number
    provision: async (tenantId: string, data: any): Promise<any> => {
        return await api.post(`/phone-numbers/provision/${tenantId}`, data);
    },
    // Remove phone number
    remove: async (tenantId: string, deleteFromVapi: boolean = false): Promise<any> => {
        return await api.delete(`/phone-numbers/${tenantId}?delete_from_vapi=${deleteFromVapi}`);
    }
};

export const vapiApi = {
    // Legacy methods - kept for backward compatibility
    getMyAssistant: async (): Promise<any> => {
        const response = await api.get(`/assistant/me`)
        return response
    },
    createMyAssistant: async (data: any): Promise<any> => {
        const response = await api.post(`/assistant/me`, data)
        return response
    },
    updateMyAssistant: async (data: any): Promise<any> => {
        const response = await api.put(`/assistant/me`, data)
        return response
    },

    // File Management (now under assistant/me/knowledge-base)
    uploadFile: async (file: File): Promise<any> => {
        const formData = new FormData();
        formData.append("file", file);
        const response = await api.post(`/assistant/me/knowledge-base/upload`, formData, {
            headers: {
                "Content-Type": "multipart/form-data"
            }
        });
        return response;
    },
    listFiles: async (): Promise<any> => {
        const response = await api.get(`/assistant/me/knowledge-base`);
        return response;
    }
}

// Comprehensive Assistant API
export const assistantApi = {
    // Core CRUD
    get: async (): Promise<any> => {
        return await api.get(`/assistant/me`)
    },
    create: async (data: any): Promise<any> => {
        return await api.post(`/assistant/me`, data)
    },
    update: async (data: any): Promise<any> => {
        return await api.put(`/assistant/me`, data)
    },
    delete: async (): Promise<any> => {
        return await api.delete(`/assistant/me`)
    },

    // Voice Configuration
    getVoice: async (): Promise<any> => {
        return await api.get(`/assistant/me/voice`)
    },
    updateVoice: async (data: any): Promise<any> => {
        return await api.put(`/assistant/me/voice`, data)
    },
    getVoiceProviders: async (): Promise<any> => {
        return await api.get(`/voice-providers`)
    },

    // Personality Configuration
    getPersonality: async (): Promise<any> => {
        return await api.get(`/assistant/me/personality`)
    },
    updatePersonality: async (data: any): Promise<any> => {
        return await api.put(`/assistant/me/personality`, data)
    },

    // Knowledge Base
    getKnowledgeBase: async (): Promise<any> => {
        return await api.get(`/assistant/me/knowledge-base`)
    },
    uploadDocument: async (file: File): Promise<any> => {
        const formData = new FormData();
        formData.append("file", file);
        return await api.post(`/assistant/me/knowledge-base/upload`, formData, {
            headers: { "Content-Type": "multipart/form-data" }
        });
    },
    deleteDocument: async (docId: string): Promise<any> => {
        return await api.delete(`/assistant/me/knowledge-base/${docId}`)
    },
    addFAQs: async (faqs: Array<{ question: string, answer: string }>): Promise<any> => {
        return await api.post(`/assistant/me/knowledge-base/faq`, faqs)
    },

    // Tools Management
    getBuiltInTools: async (): Promise<any> => {
        return await api.get(`/tools/built-in`)
    },
    getEnabledTools: async (): Promise<any> => {
        return await api.get(`/assistant/me/tools`)
    },
    enableTool: async (toolId: string, config?: any): Promise<any> => {
        return await api.post(`/assistant/me/tools/${toolId}/enable`, config || {})
    },
    disableTool: async (toolId: string): Promise<any> => {
        return await api.delete(`/assistant/me/tools/${toolId}`)
    },

    // Analytics
    getCallAnalytics: async (days: number = 30): Promise<any> => {
        return await api.get(`/assistant/me/analytics/calls?days=${days}`)
    },
    getConversations: async (limit: number = 50, skip: number = 0): Promise<any> => {
        return await api.get(`/assistant/me/conversations?limit=${limit}&skip=${skip}`)
    },
    getConversation: async (callId: string): Promise<any> => {
        return await api.get(`/assistant/me/conversations/${callId}`)
    },

    // Testing
    getTestConfig: async (): Promise<any> => {
        return await api.post(`/assistant/me/test`)
    }
}
