# Shared State and App Wiring

## Provider Stack
- `components/providers.tsx` wraps the app with `QueryClientProvider`, `AuthProvider`, `ConfigProvider`, and `TenantProvider`.
- React Query is the main server-state cache layer.

## Auth Flow
- `contexts/AuthContext.tsx` restores the session from `localStorage` on mount.
- It calls `authApi.getCurrentUser()` to load the user profile.
- It stores `access_token`, `user`, and `tenant_id` in `localStorage`.
- Login redirects to `/admin` for `super_admin`, otherwise to `/dashboard`.

## Config Flow
- `contexts/ConfigContext.tsx` derives `tenantId` from the authenticated user.
- It calls `useConfig(tenantId, isAuthenticated)` to fetch tenant-specific business config.
- This is intended to prevent cache sharing across tenants.

## Tenant Flow
- `contexts/TenantContext.tsx` exposes `tenantId`, `businessId`, `config`, `isConfigured`, and `isLoading`.
- It combines auth state and config state for page-level consumers.

## Key Hook
- `hooks/use-config.ts` uses React Query for config fetch/update/reload operations.
- Query keys include the tenant/business ID to keep tenant data isolated.
