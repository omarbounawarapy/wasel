
// ============================================
// AUTHENTICATION & USERS
// ============================================

export interface UserCreate {
    email: string;
    username: string;
    password: string;
    full_name: string;
    business_name?: string;
    phone?: string;
    role?: string;
    business_id?: string;
    tenant_id?: string;
    permissions?: string[];
    active?: boolean;
}

export interface UserUpdate {
    email?: string;
    full_name?: string;
    role?: 'owner' | 'admin' | 'staff' | 'viewer';
    active?: boolean;
}

export interface UserResponse {
    id: string;
    username: string;
    email: string;
    full_name: string;
    role: 'owner' | 'admin' | 'staff' | 'viewer' | 'barber' | 'manager' | 'super_admin';
    business_id?: string;
    tenant_id?: string;
    permissions: string[];
    active: boolean;
    approval_status?: 'pending' | 'approved' | 'rejected';
    created_at: string;
    updated_at?: string;
    last_login?: string;
}

export interface RegistrationResponse {
    message: string;
    status: 'pending';
    email: string;
}

export interface Token {
    access_token: string;
    token_type: string;
}

export interface LoginCredentials {
    username: string;
    password: string;
    email?: string; // Optional email field for flexibility
}

