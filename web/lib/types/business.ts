
import { AISettings, FeatureFlags, WhatsAppConfiguration } from './config';

// ============================================
// BUSINESS SETTINGS & SERVICES
// ============================================

export interface ServiceCreate {
    name: string;
    description: string;
    price: number;
    active?: boolean;
}

export interface ServiceUpdate {
    name?: string;
    description?: string;
    price?: number;
    active?: boolean;
}

export interface ServiceResponse {
    id: string;
    name: string;
    description: string;
    price: number;
    active: boolean;
    created_at: string;
    updated_at: string;
}

export interface ServiceFilters {
    active_only?: boolean;
    skip?: number;
    limit?: number;
}

export interface OpeningHours {
    day_of_week: number;
    open_time: string;
    close_time: string;
    is_open: boolean;
}

export interface BusinessSettings {
    business_name: string;
    business_phone: string;
    business_email: string;
    business_address: string;
    timezone: string;
    opening_hours: OpeningHours[];
    services: ServiceResponse[];
    ai_config: AISettings;
    whatsapp_config: WhatsAppConfiguration;
    features_enabled: FeatureFlags;
}

// ============================================
// LOCATIONS
// ============================================

export interface LocationOpeningHours {
    day: string;
    open: string;
    close: string;
    closed: boolean;
}

export interface Location {
    id: string;
    business_id: string;
    name: string;
    timezone: string;
    opening_hours: LocationOpeningHours[];
}

// ============================================
// STAFF
// ============================================

export interface StaffMember {
    id: string;
    business_id: string;
    name: string;
    services: string[];
    active: boolean;
}

// ============================================
// TENANTS (Multi-tenancy)
// ============================================

export type TenantStatus = 'active' | 'suspended' | 'pending';
export type TenantPlan = 'free' | 'premium' | 'enterprise';

export interface TenantCreate {
    owner_id: string;
    name: string;
    country?: string;
    timezone?: string;
    plan?: TenantPlan;
}

export interface TenantUpdate {
    name?: string;
    country?: string;
    timezone?: string;
    plan?: TenantPlan;
    status?: TenantStatus;
}

export interface TenantResponse {
    id: string;
    owner_id: string;
    name: string;
    country?: string;
    timezone: string;
    plan: TenantPlan;
    status: TenantStatus;
    total_calls: number;
    total_minutes: number;
    created_at: string;
    updated_at: string;
    is_configured?: boolean;
}
