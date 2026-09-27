import { useQuery } from "@tanstack/react-query";
import { appointmentsApi, conversationsApi, servicesApi, webhookApi } from "@/lib/api-endpoints";

export function useDashboardStats() {
    // Parallel fetching for dashboard stats
    const results = useQuery({
        queryKey: ["dashboard-stats"],
        queryFn: async () => {
            const [appointments, conversations, services, webhook] = await Promise.all([
                appointmentsApi.list(),
                conversationsApi.list({ limit: 100 }),
                servicesApi.list({ active_only: false }),
                webhookApi.getStatus().catch(() => ({ status: 'unknown' })),
            ]);

            const now = new Date();
            const upcomingAppointments = appointments.filter(
                (apt: any) => new Date(apt.datetime) > now && apt.status === 'confirmed'
            ).length;

            const completedToday = appointments.filter((apt: any) => {
                const aptDate = new Date(apt.datetime);
                return aptDate.toDateString() === now.toDateString() && apt.status === 'completed';
            }).length;

            return {
                appointments,
                conversations,
                services,
                webhookStatus: webhook,
                metrics: {
                    totalAppointments: appointments.length,
                    upcomingAppointments,
                    completedToday,
                    totalConversations: conversations.length,
                    activeServices: services.filter((s: any) => s.active !== false).length,
                }
            };
        },
        // Refresh every minute
        staleTime: 60 * 1000,
    });

    return {
        data: results.data,
        isLoading: results.isLoading,
        error: results.error,
        refetch: results.refetch,
    };
}
