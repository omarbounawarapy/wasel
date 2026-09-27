/**
 * Services API Service
 */

import api from '@/lib/api';
import type {
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse,
    ServiceFilters,
} from '@/lib/types';

export const servicesApi = {
    /**
     * List all services
     */
    list: async (filters?: ServiceFilters): Promise<ServiceResponse[]> => {
        const response = await api.get<ServiceResponse[]>('/services/', {
            params: filters,
        });
        return response;
    },

    /**
     * Get a single service by ID
     */
    get: async (serviceId: string): Promise<ServiceResponse> => {
    const response = await api.get<ServiceResponse>(`/services/${serviceId}`);
    return response;
    },

    /**
     * Create a new service
     */
    create: async (data: ServiceCreate): Promise<ServiceResponse> => {
    const response = await api.post<ServiceResponse>('/services/', data);
    return response;
    },

    /**
     * Update an existing service
     */
    update: async (serviceId: string, data: ServiceUpdate): Promise<ServiceResponse> => {
    const response = await api.put<ServiceResponse>(`/services/${serviceId}`, data);
    return response;
    },

    /**
     * Delete/deactivate a service
     */
    delete: async (serviceId: string): Promise<void> => {
        await api.delete(`/services/${serviceId}`);
    },

    /**
     * Get only active services
     */
    getActive: async (): Promise<ServiceResponse[]> => {
        return servicesApi.list({ active_only: true });
    },

    /**
     * Get all services (including inactive)
     */
    getAll: async (): Promise<ServiceResponse[]> => {
        return servicesApi.list({ active_only: false });
    },

    /**
     * Toggle service active status
     */
    toggleActive: async (serviceId: string, active: boolean): Promise<ServiceResponse> => {
        return servicesApi.update(serviceId, { active });
    },
};
