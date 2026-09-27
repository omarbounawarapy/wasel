import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { z } from 'zod';
import { getVisitorId } from './api/visitor';

const StoredUserSchema = z.object({
    id: z.string().optional(),
    tenant_id: z.string().optional(),
    role: z.enum(['user', 'admin', 'owner', 'super_admin']).optional(),
    username: z.string().optional(),
    email: z.string().email().optional(),
});

// The built bundle is served by FastAPI itself (01 §6.1), so it calls its own origin (/api).
// `next dev` (:5173) talks to the API on :8000 (CORS is on in APP_MODE=dev). NEXT_PUBLIC_API_URL overrides both.
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ||
    (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '');

const API_BASE_URL = BASE_URL ? `${BASE_URL}/api` : '/api';

class ApiClient {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Request interceptor to add auth token and tenant ID
        this.client.interceptors.request.use(
            (config) => {
                const token = localStorage.getItem('access_token');
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }

                // Add X-Visitor-Id header (required by backend for ingest/try)
                const vid = getVisitorId();
                if (vid) {
                    config.headers['X-Visitor-Id'] = vid;
                }

                // Add X-Tenant-ID header if available
                const tenantId = localStorage.getItem('tenant_id');
                if (tenantId) {
                    config.headers['X-Tenant-ID'] = tenantId;
                }

                // Fallback: try to get tenant_id from user object (schema-validated)
                if (!tenantId) {
                    const userStr = localStorage.getItem('user');
                    if (userStr) {
                        try {
                            const parsed = StoredUserSchema.safeParse(JSON.parse(userStr));
                            if (parsed.success && parsed.data.tenant_id) {
                                config.headers['X-Tenant-ID'] = parsed.data.tenant_id;
                                localStorage.setItem('tenant_id', parsed.data.tenant_id);
                            } else if (!parsed.success) {
                                localStorage.removeItem('user');
                            }
                        } catch (e) {
                            localStorage.removeItem('user');
                        }
                    }
                }

                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                // Log error details for debugging
                if (typeof window !== 'undefined' && process.env.NODE_ENV === 'development') {
                    console.error('API Error:', {
                        message: error.message,
                        url: error.config?.url,
                        method: error.config?.method,
                        status: error.response?.status,
                        data: error.response?.data,
                        raw: error
                    });
                }

                // Only redirect to login on 401 if it's not a config fetch
                // Config fetch failures should be handled gracefully by the component
                const isConfigEndpoint = error.config?.url?.includes('/admin/config');
                const isWhatsAppStatus = error.config?.url?.includes('/whatsapp/status');

                if (error.response?.status === 401 && !isConfigEndpoint && !isWhatsAppStatus) {
                    // Redirect to login removed for the hackathon version
                }

                // Enhance error object with more details
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

    async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
        try {
            const response = await this.client.post<T>(url, data, config);
            return response.data;
        } catch (error: any) {
            throw this.handleError(error);
        }
    }

    async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
        try {
            const response = await this.client.put<T>(url, data, config);
            return response.data;
        } catch (error: any) {
            throw this.handleError(error);
        }
    }

    async delete<T = any>(url: string, config?: AxiosRequestConfig) {
        try {
            const response = await this.client.delete<T>(url, config);
            return response.data;
        } catch (error: any) {
            throw this.handleError(error);
        }
    }

    async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig) {
        try {
            const response = await this.client.patch<T>(url, data, config);
            return response.data;
        } catch (error: any) {
            throw this.handleError(error);
        }
    }

    private handleError(error: any) {
        // Extract meaningful error message
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

export const apiClient = new ApiClient();
export default apiClient;
