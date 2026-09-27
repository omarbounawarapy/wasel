import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import type { CallDetailResponse, CallsListResponse } from '@/lib/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ||
    (typeof window !== 'undefined'
        ? window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000'
            : `https://${window.location.hostname}`
        : '');

const CALLS_API_BASE_URL = BASE_URL ? `${BASE_URL}/api` : '/api';

class CallsApiClient {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: CALLS_API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        this.client.interceptors.request.use((config) => {
            const token = localStorage.getItem('access_token');
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }

            const tenantId = localStorage.getItem('tenant_id');
            if (tenantId) {
                config.headers['X-Tenant-ID'] = tenantId;
            }

            if (!tenantId) {
                const userStr = localStorage.getItem('user');
                if (userStr) {
                    try {
                        const user = JSON.parse(userStr);
                        if (user.tenant_id) {
                            config.headers['X-Tenant-ID'] = user.tenant_id;
                            localStorage.setItem('tenant_id', user.tenant_id);
                        }
                    } catch (error) {
                        console.error('Error parsing user data for calls API:', error);
                    }
                }
            }

            return config;
        });

        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401 && typeof window !== 'undefined') {
                    localStorage.removeItem('token');
                    localStorage.removeItem('access_token');
                    localStorage.removeItem('user');
                    localStorage.removeItem('tenant_id');
                    window.location.href = '/login';
                }

                if (error.response) {
                    error.message = error.response.data?.detail || error.response.data?.message || error.message;
                }

                return Promise.reject(error);
            }
        );
    }

    async get<T = any>(url: string, config?: AxiosRequestConfig) {
        try {
            const response = await this.client.get<T>(url, config);
            return response.data;
        } catch (error: any) {
            throw this.handleError(error);
        }
    }

    private handleError(error: any) {
        const message = error.response?.data?.detail
            || error.response?.data?.message
            || error.message
            || 'An unexpected error occurred';

        return {
            message,
            status: error.response?.status,
            data: error.response?.data,
        };
    }
}

const callsApiClient = new CallsApiClient();

export const callsApi = {
    list: async (page = 1, limit = 10): Promise<CallsListResponse> => {
        const response = await callsApiClient.get<CallsListResponse>('/calls', {
            params: { page, limit },
        });
        return response;
    },

    get: async (callId: string): Promise<CallDetailResponse> => {
        const normalizedId = String(callId ?? "").trim();
        if (!normalizedId || normalizedId === "undefined" || normalizedId === "null") {
            throw {
                message: "Invalid call ID",
                status: 400,
                data: null,
            };
        }
        const response = await callsApiClient.get<CallDetailResponse>(`/calls/${normalizedId}`);
        return response;
    },
};
