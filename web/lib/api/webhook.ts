/**
 * Webhook & Twilio API Service
 */

import api from '@/lib/api';
import type { WebhookStatus } from '@/lib/types';

export const webhookApi = {
    /**
     * Get webhook status
     */
    getStatus: async (): Promise<WebhookStatus> => {
    const response = await api.get<WebhookStatus>('/whatsapp/status');
    return response;
    },
};
