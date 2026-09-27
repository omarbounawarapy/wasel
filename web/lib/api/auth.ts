import api from '@/lib/api';
import type { LoginCredentials, Token, UserResponse, UserCreate, RegistrationResponse } from '@/lib/types';

export const authApi = {
    /**
     * Login user and get JWT token
     * Sends email as username since backend supports both
     */
    login: async (credentials: LoginCredentials): Promise<Token> => {
        const formData = new URLSearchParams();
        // Send email as username - backend now supports email lookup
        const username = credentials.username || credentials.email || '';
        formData.append('username', username);
        formData.append('password', credentials.password);

        const response = await api.post<Token>('/users/token', formData, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });

        return response; // ApiClient already returns .data
    },

    /**
     * Register a new user (returns pending status - requires admin approval)
     */
    register: async (userData: UserCreate): Promise<RegistrationResponse> => {
        const response = await api.post<RegistrationResponse>('/users/register', userData);
        return response; // ApiClient already returns .data
    },

    /**
     * Get current authenticated user
     */
    getCurrentUser: async (): Promise<UserResponse> => {
        const response = await api.get<UserResponse>('/users/me');
        return response; // ApiClient already returns .data
    },

    /**
     * Logout user (client-side only)
     */
    logout: (): void => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('username');
        }
    },
};
