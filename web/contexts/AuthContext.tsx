"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { authApi } from '@/lib/api/auth';
import { UserResponse, LoginCredentials, UserCreate, RegistrationResponse } from '@/lib/types';
import { logUserAction, logClientError } from '@/lib/errorLogging';

interface AuthContextType {
    user: UserResponse | null;
    isLoading: boolean;
    login: (credentials: LoginCredentials) => Promise<void>;
    register: (data: UserCreate) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<UserResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        const initAuth = async () => {
            setUser({ id: '1', email: 'test@example.com', username: 'Test', role: 'admin', tenant_id: 'default' } as any);
            setIsLoading(false);
        };
        initAuth();
    }, []);

    const login = async (credentials: LoginCredentials) => {
        setIsLoading(true);
        logUserAction('login_attempt', { email: credentials.email });

        try {
            const token = await authApi.login(credentials);
            localStorage.setItem('access_token', token.access_token);

            // Fetch user profile immediately
            const userData = await authApi.getCurrentUser();
            setUser(userData);

            // Store user data in localStorage for components that need it
            localStorage.setItem('user', JSON.stringify(userData));

            if (userData.tenant_id) {
                localStorage.setItem('tenant_id', userData.tenant_id);
            }

            logUserAction('login_success', {
                user_id: userData.id,
                tenant_id: userData.tenant_id,
                role: userData.role
            }, {
                userId: userData.id,
                tenantId: userData.tenant_id,
            });

            // Redirect based on role
            if (userData.role === 'super_admin') {
                window.location.href = '/admin';
            } else {
                window.location.href = '/dashboard';
            }
        } catch (error) {
            console.error('Login failed:', error);
            await logClientError('Login failed', {
                metadata: { email: credentials.email },
                stack: error instanceof Error ? error.stack : undefined,
            });
            logUserAction('login_failed', { email: credentials.email }, {
                userId: user?.id,
                tenantId: user?.tenant_id,
                success: false,
            });
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    const register = async (data: UserCreate) => {
        setIsLoading(true);
        logUserAction('registration_attempt', {
            email: data.email,
            username: data.username,
            business_name: data.business_name
        });

        try {
            // Backend returns pending response (no token)
            const response = await authApi.register(data) as RegistrationResponse;

            logUserAction('registration_pending', {
                email: data.email,
                status: response.status,
                message: response.message
            });

            // Throw error with pending message to trigger auth component to show pending screen
            throw new Error('PENDING_APPROVAL:' + response.message);
        } catch (error) {
            console.error('Registration failed:', error);
            await logClientError('Registration failed', {
                metadata: {
                    email: data.email,
                    username: data.username,
                    business_name: data.business_name,
                },
                stack: error instanceof Error ? error.stack : undefined,
            });
            logUserAction('registration_failed', {
                email: data.email,
                error: error instanceof Error ? error.message : 'Unknown error'
            }, {
                userId: null,
                tenantId: null,
                success: false,
            });
            throw error;
        } finally {
            setIsLoading(false);
        }
    };

    const logout = () => {
        logUserAction('logout', { user_id: user?.id }, {
            userId: user?.id ?? undefined,
            tenantId: user?.tenant_id ?? undefined,
        });
        authApi.logout();
        localStorage.removeItem('tenant_id');
        localStorage.removeItem('user');
        setUser(null);
        router.push('/login');
    };

    return (
        <AuthContext.Provider value={{
            user,
            isLoading,
            login,
            register,
            logout,
            isAuthenticated: !!user
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
