
// ============================================
// CONFIGURATION
// ============================================

export interface BusinessConfig {
    business_name: string;
    timezone: string;
    currency: string;
    phone_number?: string;
    email?: string;
    address?: string;
    vapi_api_key?: string;
    twilio_account_sid?: string;
    twilio_auth_token?: string;
    twilio_phone_number?: string;
    system_prompt?: string;
    is_configured?: boolean;
}

export interface WebhookStatus {
    status: 'active' | 'inactive';
    endpoints: {
        sms: string;
        voice: string;
        voice_menu: string;
    };
}

export interface WhatsAppConfiguration {
    phone_number_id: string;
    access_token: string;
    verify_token: string;
    webhook_url: string;
    is_enabled: boolean;
}

export interface FeatureFlags {
    voice_agent?: boolean;
    email_notifications?: boolean;
    sms_reminders?: boolean;
    online_booking?: boolean;
    [key: string]: boolean | undefined;
}

export interface AISettings {
    model: string;
    temperature: number;
    max_tokens: number;
    greeting_message: string;
    system_prompt: string;
    tone: 'professional' | 'friendly' | 'casual';
}
