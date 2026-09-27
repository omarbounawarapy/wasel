"use client";

import React, { createContext, useContext, ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { BusinessConfig } from '@/lib/api/business-config';
import { useConfig } from './ConfigContext';

interface TenantContextType {
    tenantId: string | null;
    businessId: string | null;
    config: BusinessConfig | undefined;
    isConfigured: boolean;
    isLoading: boolean;
}

const TenantContext = createContext<TenantContextType | undefined>(undefined);

export function TenantProvider({ children }: { children: ReactNode }) {
    const { user, isLoading: authLoading } = useAuth();
    const { config, isLoading: configLoading } = useConfig();

    const tenantId = user?.tenant_id || null;
    const businessId = user?.business_id || user?.tenant_id || null;
    const isConfigured = config?.is_configured ?? false;
    const isLoading = authLoading || configLoading;

    return (
        <TenantContext.Provider
            value={{
                tenantId,
                businessId,
                config,
                isConfigured,
                isLoading,
            }}
        >
            {children}
        </TenantContext.Provider>
    );
}

export function useTenant() {
    const context = useContext(TenantContext);
    if (context === undefined) {
        throw new Error('useTenant must be used within a TenantProvider');
    }
    return context;
}
