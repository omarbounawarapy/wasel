import api from '@/lib/api';

export interface BillingSubscriptionStatus {
    status: string;
    plan_name: string;
    plan_price: string;
    trial_end: string | null;
    current_period_end: string;
    cancel_at_period_end: boolean;
    is_mock: boolean;
}

export interface DashboardBillingSummary {
    plan: string;
    plan_price: string;
    subscription_status: string;
    current_period_end: string | null;
    assistant_id: string | null;
    usage: {
        total_calls: number;
        total_minutes: number;
        total_cost: number;
        avg_cost_per_minute: number;
    };
    tenant_credit_balance: number | null;
    is_mock: boolean;
}

export const billingApi = {
    getSubscription: async (): Promise<BillingSubscriptionStatus> => {
        return api.get<BillingSubscriptionStatus>('/billing/subscription');
    },

    getDashboardSummary: async (): Promise<DashboardBillingSummary> => {
        return api.get<DashboardBillingSummary>('/billing/dashboard-summary');
    },
};
