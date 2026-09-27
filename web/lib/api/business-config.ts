import api from '@/lib/api';

export interface OpeningHours {
    day_of_week: number; // 0=Monday, 6=Sunday
    open_time: string; // "HH:MM"
    close_time: string; // "HH:MM"
    is_open: boolean;
}

export interface DaySchedule {
    start: string;
    end: string;
    enabled: boolean;
}

export interface BusinessHours {
    monday: DaySchedule;
    tuesday: DaySchedule;
    wednesday: DaySchedule;
    thursday: DaySchedule;
    friday: DaySchedule;
    saturday: DaySchedule;
    sunday: DaySchedule;
    [key: string]: DaySchedule;
}

export interface ServiceDefinition {
    name: string;
    price: number;
    description?: string;
    is_active?: boolean;
}

export interface AIConfiguration {
    model?: string;
    temperature?: number;
    max_tokens?: number;
    system_prompt?: string;
    voice_enabled?: boolean;
    voice_model?: string;
}

export interface FeatureFlags {
    voice_agent?: boolean;
    email_notifications?: boolean;
    sms_reminders?: boolean;
    online_booking?: boolean;
    [key: string]: boolean | undefined;
}

export interface WhatsAppConfiguration {
    phone_number_id?: string;
    access_token?: string;
    verify_token?: string;
    webhook_url?: string;
}

export interface BusinessConfig {
    business_id: string;
    business_name: string;
    business_email?: string;
    business_phone?: string;
    business_location?: string;
    business_address?: string;
    email?: string;
    phone_number?: string;
    address?: string;
    timezone: string;
    currency?: string;
    business_hours: BusinessHours;
    services: ServiceDefinition[];
    ai_config: AIConfiguration;
    whatsapp_config: WhatsAppConfiguration;
    features_enabled?: FeatureFlags;
    automations?: { [key: string]: boolean };
    created_at?: string;
    updated_at?: string;
    logo_url?: string;
    primary_color?: string;
    secondary_color?: string;
    vapi_api_key?: string;
    twilio_account_sid?: string;
    twilio_auth_token?: string;
    twilio_phone_number?: string;
    is_configured?: boolean;
}

export interface BusinessConfigUpdate {
    business_name?: string;
    business_email?: string;
    business_phone?: string;
    business_location?: string;
    business_address?: string;
    timezone?: string;
    email?: string;
    phone_number?: string;
    address?: string;
    currency?: string;
    business_hours?: BusinessHours;
    services?: ServiceDefinition[];
    ai_config?: AIConfiguration;
    whatsapp_config?: WhatsAppConfiguration;
    features_enabled?: FeatureFlags;
    automations?: { [key: string]: boolean };
    vapi_api_key?: string;
    twilio_account_sid?: string;
    twilio_auth_token?: string;
    twilio_phone_number?: string;
    is_configured?: boolean;
}

export const businessConfigApi = {
    /**
     * Get current business configuration
     */
    getConfig: async (businessId: string = 'default'): Promise<BusinessConfig> => {
        const response = await api.get<BusinessConfig>('/admin/config');
        return response; // ApiClient already returns .data
    },

    /**
     * Update business configuration
     */
    updateConfig: async (
        data: BusinessConfigUpdate,
        businessId: string = 'default'
    ): Promise<BusinessConfig> => {
        const response = await api.put<BusinessConfig>('/admin/config', data);
        return response; // ApiClient already returns .data
    },

    updateFeatureFlags: async (
        features: FeatureFlags,
        businessId: string = 'default'
    ): Promise<BusinessConfig> => {
        // First get current config to merge
        const current = await businessConfigApi.getConfig();
        const updatedFeatures = { ...current.features_enabled, ...features };

        const response = await api.put<BusinessConfig>(
            '/admin/config',
            { automations: updatedFeatures }
        );
        return response; // ApiClient already returns .data
    },

    updateAutomations: async (
        automations: { [key: string]: boolean },
        businessId: string = 'default'
    ): Promise<BusinessConfig> => {
        const response = await api.put<BusinessConfig>(
            '/admin/config',
            { automations }
        );
        return response; // ApiClient already returns .data
    },

    /**
     * Reload configuration (invalidate cache)
     */
    reloadConfig: async (businessId: string = 'default'): Promise<{ message: string }> => {
        return { message: "Config reloaded" };
    },

    /**
     * Get AI prompt configuration
     */
    getAIPrompt: async (businessId: string = 'default'): Promise<{ system_prompt: string }> => {
        const config = await businessConfigApi.getConfig();
        return { system_prompt: config.ai_config?.system_prompt || "" };
    },

    /**
     * Update AI prompt
     */
    updateAIPrompt: async (
        systemPrompt: string,
        businessId: string = 'default'
    ): Promise<BusinessConfig> => {
        const response = await api.put<BusinessConfig>(
            '/admin/config',
            { system_prompt: systemPrompt }
        );
        return response; // ApiClient already returns .data
    },

    /**
     * Update WhatsApp configuration
     */
    updateWhatsAppConfig: async (
        config: WhatsAppConfiguration,
        businessId: string = 'default'
    ): Promise<BusinessConfig> => {
        const response = await api.put<BusinessConfig>('/admin/config', { whatsapp_config: config });
        return response; // ApiClient already returns .data
    },

    /**
     * Get services list
     */
    getServices: async (businessId: string = 'default'): Promise<ServiceDefinition[]> => {
        const response = await api.get<ServiceDefinition[]>('/services/');
        return response; // ApiClient already returns .data
    },
};
