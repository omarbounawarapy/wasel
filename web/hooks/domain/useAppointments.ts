import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { appointmentsApi } from "@/lib/api-endpoints";
import { AppointmentCreate, AppointmentUpdate, AppointmentResponse, AppointmentFilters } from "@/lib/types";
import { toast } from "sonner";

export function useAppointments(filters?: AppointmentFilters) {
    const queryClient = useQueryClient();
    const queryKey = ["appointments", filters];

    const {
        data: appointments = [],
        isLoading,
        error
    } = useQuery({
        queryKey,
        queryFn: () => appointmentsApi.list(filters),
    });

    const createMutation = useMutation({
        mutationFn: appointmentsApi.create,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["appointments"] });
            toast.success("Appointment created successfully! 🎉");
        },
        onError: (error: any) => {
            console.error("Create error:", error);
            const detail = error.response?.data?.detail;
            const message = Array.isArray(detail) ? detail.map((d: any) => d.msg).join(", ") : (detail || "Failed to create appointment");
            toast.error(message);
        },
    });

    const updateMutation = useMutation({
        mutationFn: ({ id, data }: { id: string; data: AppointmentUpdate }) =>
            appointmentsApi.update(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["appointments"] });
            toast.success("Appointment updated successfully!");
        },
        onError: (error: any) => {
            console.error("Update error:", error);
            const detail = error.response?.data?.detail;
            const message = Array.isArray(detail) ? detail.map((d: any) => d.msg).join(", ") : (detail || "Failed to update appointment");
            toast.error(message);
        },
    });

    const deleteMutation = useMutation({
        mutationFn: appointmentsApi.delete,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["appointments"] });
            toast.success("Appointment deleted successfully");
        },
        onError: (error: any) => {
            console.error("Delete error:", error);
            const detail = error.response?.data?.detail;
            const message = Array.isArray(detail) ? detail.map((d: any) => d.msg).join(", ") : (detail || "Failed to delete appointment");
            toast.error(message);
        },
    });

    return {
        appointments,
        isLoading,
        error,
        create: createMutation.mutate,
        createAsync: createMutation.mutateAsync,
        update: updateMutation.mutate,
        updateAsync: updateMutation.mutateAsync,
        remove: deleteMutation.mutate,
        isCreating: createMutation.isPending,
        isUpdating: updateMutation.isPending,
        isDeleting: deleteMutation.isPending,
    };
}
