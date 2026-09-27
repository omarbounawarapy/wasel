import api from '@/lib/api';
import {
    UserResponse,
    AppointmentResponse,
    ServiceResponse,
    ConversationResponse,
    TenantResponse,
    BusinessConfig,
    Token,
} from '@/lib/types';

export type User = UserResponse;
export type Appointment = AppointmentResponse;
export type Service = ServiceResponse;
export type Conversation = ConversationResponse;
export type Tenant = TenantResponse;
export type { BusinessConfig };

export interface CrewJob {
    id: string;
    status: 'queued' | 'running' | 'completed' | 'failed';
    task?: string;
    created_at?: string;
    updated_at?: string;
    metadata?: Record<string, unknown>;
}

type Paginated<T> = {
    items: T[];
    total: number;
    page?: number;
    limit?: number;
};

type PaginatedOrList<T> = Paginated<T> | T[];

export interface TenantBillingSummary {
    tenant_id: string;
    name: string;
    email: string;
    plan: string;
    subscription_status: string;
    monthly_subscription_usd: number;
    credit_balance: number;
    total_calls: number;
    total_minutes: number;
    total_vapi_cost_usd: number;
    profit_usd: number;
    assistants: { assistant_id: string; total_calls: number; total_cost_usd: number; total_minutes: number }[];
}

export interface BillingOverview {
    tenants: TenantBillingSummary[];
    platform_summary: {
        total_tenants: number;
        active_tenants: number;
        total_subscription_revenue_usd: number;
        total_vapi_cost_usd: number;
        platform_margin_usd: number;
    };
}

interface GlobalAnalytics {
    tenants: {
        total: number;
        active: number;
    };
    users: number;
    appointments: number;
    conversations: number;
}

interface JobTriggerResponse {
    message: string;
    job_id?: string;
}

interface JobStatusResponse {
    job_id: string;
    status: CrewJob['status'];
    progress?: number;
    result?: Record<string, unknown>;
    error?: string;
}

// Admin API Functions
export const adminApi = {
    // Users
    getUsers: async (skip = 0, limit = 100): Promise<UserResponse[]> => {
        const response = await api.get<UserResponse[]>(`/admin/users?skip=${skip}&limit=${limit}`);
        return response;
    },
    createUser: async (data: Partial<UserResponse>): Promise<UserResponse> => {
        const response = await api.post<UserResponse>('/admin/users', data);
        return response;
    },
    updateUser: async (id: string, data: Partial<UserResponse>): Promise<UserResponse> => {
        const response = await api.put<UserResponse>(`/admin/users/${id}`, data);
        return response;
    },
    deleteUser: async (id: string) => {
        await api.delete(`/admin/users/${id}`);
    },
    impersonateUser: async (id: string): Promise<Token> => {
        const response = await api.post<Token>(`/admin/users/${id}/impersonate`);
        return response;
    },
    approveUser: async (id: string): Promise<UserResponse> => {
        const response = await api.post<UserResponse>(`/admin/users/${id}/approve`);
        return response;
    },
    rejectUser: async (id: string): Promise<UserResponse> => {
        const response = await api.post<UserResponse>(`/admin/users/${id}/reject`);
        return response;
    },
    getPendingUsers: async (): Promise<UserResponse[]> => {
        const response = await api.get<UserResponse[]>('/admin/users/pending');
        return response;
    },

    // Appointments
    getAppointments: async (
        skip = 0,
        limit = 100,
        status?: string
    ): Promise<PaginatedOrList<AppointmentResponse>> => {
        let url = `/admin/appointments?skip=${skip}&limit=${limit}`;
        if (status) url += `&status=${status}`;
        const response = await api.get<PaginatedOrList<AppointmentResponse>>(url);
        return response;
    },
    createAppointment: async (data: AppointmentResponse | Partial<AppointmentResponse>): Promise<AppointmentResponse> => {
        const response = await api.post<AppointmentResponse>('/admin/appointments', data);
        return response;
    },
    updateAppointment: async (id: string, data: Partial<AppointmentResponse>): Promise<AppointmentResponse> => {
        const response = await api.put<AppointmentResponse>(`/admin/appointments/${id}`, data);
        return response;
    },
    deleteAppointment: async (id: string) => {
        await api.delete(`/admin/appointments/${id}`);
    },

    // Services
    getServices: async (skip = 0, limit = 100): Promise<PaginatedOrList<ServiceResponse>> => {
        const response = await api.get<PaginatedOrList<ServiceResponse>>(`/admin/services?skip=${skip}&limit=${limit}`);
        return response;
    },
    createService: async (data: ServiceResponse | Partial<ServiceResponse>): Promise<ServiceResponse> => {
        const response = await api.post<ServiceResponse>('/admin/services', data);
        return response;
    },
    updateService: async (id: string, data: Partial<ServiceResponse>): Promise<ServiceResponse> => {
        const response = await api.put<ServiceResponse>(`/admin/services/${id}`, data);
        return response;
    },
    deleteService: async (id: string) => {
        await api.delete(`/admin/services/${id}`);
    },

    // Conversations
    getConversations: async (
        skip = 0,
        limit = 100,
        phone?: string
    ): Promise<PaginatedOrList<ConversationResponse>> => {
        let url = `/admin/conversations?skip=${skip}&limit=${limit}`;
        if (phone) url += `&phone=${phone}`;
        const response = await api.get<PaginatedOrList<ConversationResponse>>(url);
        return response;
    },
    deleteConversation: async (id: string) => {
        await api.delete(`/admin/conversations/${id}`);
    },

    // Business Config
    getConfig: async (): Promise<BusinessConfig> => {
        const response = await api.get<BusinessConfig>('/admin/config');
        return response;
    },
    updateConfig: async (data: Partial<BusinessConfig>): Promise<BusinessConfig> => {
        const response = await api.put<BusinessConfig>('/admin/config', data);
        return response;
    },

    // Tenants
    getTenants: async (
        skip = 0,
        limit = 100,
        search?: string
    ): Promise<PaginatedOrList<TenantResponse>> => {
        let url = `/admin/tenants?skip=${skip}&limit=${limit}`;
        if (search) url += `&search=${search}`;
        const response = await api.get<PaginatedOrList<TenantResponse>>(url);
        return response;
    },
    createTenant: async (data: Partial<TenantResponse>): Promise<TenantResponse> => {
        const response = await api.post<TenantResponse>('/admin/tenants', data);
        return response;
    },
    updateTenant: async (id: string, data: Partial<TenantResponse>): Promise<TenantResponse> => {
        const response = await api.put<TenantResponse>(`/admin/tenants/${id}`, data);
        return response;
    },
    deleteTenant: async (id: string): Promise<void> => {
        await api.delete(`/admin/tenants/${id}`);
    },

    // Analytics
    getGlobalAnalytics: async (): Promise<GlobalAnalytics> => {
        const response = await api.get<GlobalAnalytics>('/admin/analytics/global');
        return response;
    },

    // Billing Overview
    getBillingOverview: async (): Promise<BillingOverview> => {
        return api.get<BillingOverview>('/admin/billing/overview');
    },
    addCredits: async (tenantId: string, amountUsd: number, note?: string): Promise<{ success: boolean; new_balance: number }> => {
        return api.post(`/admin/billing/add-credits/${tenantId}`, { amount_usd: amountUsd, note });
    },

    // CrewAI
    triggerDataCleaning: async (): Promise<JobTriggerResponse> => {
        const response = await api.post<JobTriggerResponse>('/crew/clean-data');
        return response;
    },
    triggerAnalytics: async (): Promise<JobTriggerResponse> => {
        const response = await api.post<JobTriggerResponse>('/crew/analyze');
        return response;
    },
    getJobStatus: async (jobId: string): Promise<JobStatusResponse> => {
        const response = await api.get<JobStatusResponse>(`/crew/status/${jobId}`);
        return response;
    },
    getJobs: async (limit = 10): Promise<CrewJob[]> => {
        const response = await api.get<CrewJob[]>(`/crew/jobs?limit=${limit}`);
        return response;
    }
};
