
// ============================================
// APPOINTMENTS
// ============================================

export type AppointmentStatus = 'confirmed' | 'pending' | 'cancelled' | 'completed' | 'no_show';

export interface AppointmentCreate {
    business_id?: string;
    location_id?: string;
    client_id?: string;
    service_id?: string;
    staff_id?: string;
    client_name: string;
    client_phone: string;
    service: string;
    datetime: string; // ISO 8601 datetime string
    duration_minutes: number;
    source?: string;
    notes?: string;
}

export interface AppointmentUpdate {
    client_name?: string;
    service?: string;
    datetime?: string;
    duration_minutes?: number;
    status?: AppointmentStatus;
    notes?: string;
}

export interface AppointmentResponse {
    id: string;
    business_id: string;
    location_id: string;
    client_id?: string;
    service_id?: string;
    staff_id?: string;
    client_name: string;
    client_phone: string;
    service: string;
    datetime: string;
    start_time: string;
    end_time: string;
    duration_minutes: number;
    status: AppointmentStatus;
    source: string;
    notes?: string;
    created_at: string;
    updated_at: string;
}

export interface AppointmentFilters {
    status?: AppointmentStatus;
    date_from?: string;
    date_to?: string;
    client_phone?: string;
    skip?: number;
    limit?: number;
}
