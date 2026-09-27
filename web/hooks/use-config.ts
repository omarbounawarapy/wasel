import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { businessConfigApi, BusinessConfigUpdate, WhatsAppConfiguration } from '@/lib/api/business-config';
import { useToast } from '@/hooks/use-toast';

const QUERY_KEY = 'businessConfig';

/**
 * Hook for business configuration management
 * 
 * TENANT ISOLATION: This hook MUST receive a unique businessId (tenant_id) per tenant
 * to ensure proper data isolation in React Query's cache. Without this, all tenants
 * would share the same cached configuration data.
 * 
 * @param businessId - Unique identifier for the tenant/business (defaults to 'default' if not provided)
 * @param enabled - Whether to enable the query (should be false if user is not authenticated)
 */
export function useConfig(businessId: string = 'default', enabled: boolean = true) {
    const queryClient = useQueryClient();
    const { toast } = useToast();

    // Get configuration
    const {
        data: config,
        isLoading,
        error,
        refetch
    } = useQuery({
        queryKey: [QUERY_KEY, businessId],
        queryFn: () => businessConfigApi.getConfig(businessId),
        enabled: enabled, // Only fetch if enabled (user is authenticated)
        staleTime: 5 * 60 * 1000, // 5 minutes (matches backend cache)
        retry: (failureCount, error: any) => {
            // Don't retry on 401 (unauthorized) - user needs to login
            if (error?.response?.status === 401) {
                return false;
            }
            // Retry other errors up to 2 times
            return failureCount < 2;
        },
        // Don't throw errors, let components handle them
        throwOnError: false,
    });

    // Update configuration
    const updateConfig = useMutation({
        mutationFn: (data: BusinessConfigUpdate) =>
            businessConfigApi.updateConfig(data, businessId),
        onSuccess: (data) => {
            queryClient.setQueryData([QUERY_KEY, businessId], data);
            toast({
                title: 'Configuration Updated',
                description: 'Business configuration has been saved successfully.',
            });
        },
        onError: (error: any) => {
            toast({
                title: 'Update Failed',
                description: error.response?.data?.detail || 'Failed to update configuration',
                variant: 'destructive',
            });
        },
    });

    // Reload configuration (invalidate cache)
    const reloadConfig = useMutation({
        mutationFn: () => businessConfigApi.reloadConfig(businessId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: [QUERY_KEY, businessId] });
            toast({
                title: 'Configuration Reloaded',
                description: 'Latest configuration loaded from database.',
            });
        },
    });

    // Update AI prompt
    const updateAIPrompt = useMutation({
        mutationFn: (systemPrompt: string) =>
            businessConfigApi.updateAIPrompt(systemPrompt, businessId),
        onSuccess: (data) => {
            queryClient.setQueryData([QUERY_KEY, businessId], data);
            toast({
                title: 'AI Prompt Updated',
                description: 'AI system prompt has been saved.',
            });
        },
        onError: (error: any) => {
            toast({
                title: 'Update Failed',
                description: error.response?.data?.detail || 'Failed to update AI prompt',
                variant: 'destructive',
            });
        },
    });

    // Update WhatsApp configuration
    const updateWhatsApp = useMutation({
        mutationFn: (whatsappConfig: WhatsAppConfiguration) =>
            businessConfigApi.updateWhatsAppConfig(whatsappConfig, businessId),
        onSuccess: (data) => {
            queryClient.setQueryData([QUERY_KEY, businessId], data);
            toast({
                title: 'WhatsApp Updated',
                description: 'WhatsApp configuration has been saved.',
            });
        },
        onError: (error: any) => {
            toast({
                title: 'Update Failed',
                description: error.response?.data?.detail || 'Failed to update WhatsApp config',
                variant: 'destructive',
            });
        },
    });

    return {
        config,
        isLoading,
        error,
        refetch,
        updateConfig: updateConfig.mutate,
        isUpdating: updateConfig.isPending,
        reloadConfig: reloadConfig.mutate,
        isReloading: reloadConfig.isPending,
        updateAIPrompt: updateAIPrompt.mutate,
        isUpdatingAIPrompt: updateAIPrompt.isPending,
        updateWhatsApp: updateWhatsApp.mutate,
        isUpdatingWhatsApp: updateWhatsApp.isPending,
    };
}

/**
 * Hook for AI prompt configuration
 */
export function useAIPrompt(businessId: string = 'default') {
    const {
        data,
        isLoading,
        error
    } = useQuery({
        queryKey: ['aiPrompt', businessId],
        queryFn: () => businessConfigApi.getAIPrompt(businessId),
        staleTime: 10 * 60 * 1000, // 10 minutes
    });

    return {
        systemPrompt: data?.system_prompt,
        isLoading,
        error,
    };
}

/**
 * Hook for services list
 */
export function useServices(businessId: string = 'default') {
    const {
        data: services,
        isLoading,
        error
    } = useQuery({
        queryKey: ['services', businessId],
        queryFn: () => businessConfigApi.getServices(businessId),
        staleTime: 5 * 60 * 1000,
    });

    return {
        services: services || [],
        isLoading,
        error,
    };
}
