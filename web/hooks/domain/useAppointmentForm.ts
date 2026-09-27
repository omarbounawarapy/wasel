import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { servicesApi } from "@/lib/api-endpoints";
import { AppointmentCreate, AppointmentUpdate, AppointmentResponse, ServiceResponse } from "@/lib/types";
import { format } from "date-fns";
import { useAppointments } from "./useAppointments";
import { toast } from "sonner";

interface UseAppointmentFormProps {
    mode: "create" | "edit";
    appointment?: AppointmentResponse | null;
    onSuccess?: () => void;
}

interface FormData {
    client_name: string;
    client_phone: string;
    service: string;
    date: Date | undefined;
    time: string;
    duration_minutes: number;
    notes?: string;
}

export function useAppointmentForm({ mode, appointment, onSuccess }: UseAppointmentFormProps) {
    const { createAsync, updateAsync, isCreating, isUpdating } = useAppointments();

    const [formData, setFormData] = useState<FormData>({
        client_name: "",
        client_phone: "",
        service: "",
        date: undefined,
        time: "09:00",
        duration_minutes: 30,
        notes: "",
    });

    // Fetch services
    const { data: services } = useQuery<ServiceResponse[]>({
        queryKey: ["services"],
        queryFn: () => servicesApi.list({ active_only: true }),
    });

    // Time slots generation
    const timeSlots = Array.from({ length: 24 * 4 }).map((_, i) => {
        const hour = Math.floor(i / 4);
        const minute = (i % 4) * 15;
        const date = new Date();
        date.setHours(hour, minute);
        return {
            value: `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`,
            label: format(date, "h:mm a"),
        };
    });

    // Reset or Populate form
    useEffect(() => {
        if (mode === "edit" && appointment) {
            const dateObj = new Date(appointment.datetime);
            const hours = String(dateObj.getHours()).padStart(2, "0");
            const minutes = String(dateObj.getMinutes()).padStart(2, "0");

            setFormData({
                client_name: appointment.client_name,
                client_phone: appointment.client_phone,
                service: appointment.service || "",
                date: dateObj,
                time: `${hours}:${minutes}`,
                duration_minutes: appointment.duration_minutes || 30,
                notes: appointment.notes || "",
            });
        } else {
            setFormData({
                client_name: "",
                client_phone: "",
                service: "",
                date: undefined,
                time: "09:00",
                duration_minutes: 30,
                notes: "",
            });
        }
    }, [mode, appointment]);

    const submit = async () => {
        if (!formData.client_name || !formData.client_phone || !formData.service || !formData.date || !formData.time) {
            toast.error("Please fill in all required fields");
            return;
        }

        const [hours, minutes] = formData.time.split(":").map(Number);
        const combinedDate = new Date(formData.date);
        combinedDate.setHours(hours, minutes, 0, 0);
        const isoDatetime = combinedDate.toISOString();
        
        // Ensure phone number matches backend pattern '^\+?\d{6,15}$'
        // by stripping spaces, dashes, and parentheses
        const formattedPhone = formData.client_phone.replace(/[^\d+]/g, '');

        try {
            if (mode === "create") {
                await createAsync({
                    client_name: formData.client_name,
                    client_phone: formattedPhone,
                    service: formData.service,
                    datetime: isoDatetime,
                    duration_minutes: formData.duration_minutes,
                    notes: formData.notes,
                });
            } else if (appointment?.id) {
                const updateData: AppointmentUpdate = {};
                // Only include changed fields could be implemented here, but simplistic update is fine for now
                if (formData.client_name !== appointment.client_name) updateData.client_name = formData.client_name;
                if (formData.service !== appointment.service) updateData.service = formData.service;
                if (isoDatetime !== appointment.datetime) updateData.datetime = isoDatetime;
                if (formData.duration_minutes !== appointment.duration_minutes) updateData.duration_minutes = formData.duration_minutes;
                if (formData.notes !== appointment.notes) updateData.notes = formData.notes;

                if (Object.keys(updateData).length > 0) {
                    await updateAsync({ id: appointment.id, data: updateData });
                }
            }
            onSuccess?.();
        } catch (error) {
            // Error handled in hook
        }
    };

    return {
        formData,
        setFormData,
        services,
        timeSlots,
        submit,
        isLoading: isCreating || isUpdating
    };
}
