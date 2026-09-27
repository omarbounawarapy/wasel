
import { AppointmentStatus } from "./appointment";

// ============================================
// API & UTILS
// ============================================

export interface ApiError {
    detail: string;
    status_code: number;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    skip: number;
    limit: number;
}

export interface FormState {
    isSubmitting: boolean;
    error: string | null;
    success: boolean;
}

export interface DashboardStats {
    total_appointments: number;
    upcoming_appointments: number;
    total_conversations: number;
    completed_conversations: number;
    active_services: number;
    total_users: number;
}

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

export interface ChatTestRequest {
    message: string;
    phone_number?: string;
}

export interface CalendarEvent {
    id: string;
    title: string;
    start: Date;
    end: Date;
    backgroundColor?: string;
    borderColor?: string;
    extendedProps?: {
        client_phone: string;
        service: string;
        status: AppointmentStatus;
        notes?: string;
    };
}
