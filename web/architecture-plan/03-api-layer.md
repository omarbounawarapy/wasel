# API Layer

## Core Client
- `lib/api.ts` creates a shared Axios client.
- It reads `NEXT_PUBLIC_API_URL` and falls back to localhost or relative `/api/v1`.
- Request interceptors attach `Authorization: Bearer <token>` and `X-Tenant-ID` from `localStorage`.
- Response interceptors clear auth state and redirect to `/login` on unauthorized responses.

## API Organization
- `lib/api/index.ts` re-exports module-specific API objects.
- `lib/api/auth.ts` handles login, register, current-user lookup, and logout.
- `lib/api/business-config.ts` handles tenant/business configuration.
- `lib/api-endpoints.ts` contains a broad collection of endpoint wrappers for appointments, services, conversations, users, phone numbers, Vapi, and onboarding.

## Types
- `lib/types.ts` re-exports modular type files from `lib/types/*`.
- `lib/types/api.ts` defines API helpers, dashboard stats, chat message shapes, and common response types.
- The codebase uses TypeScript types heavily for request/response safety.

## Important Behavior
- Auth tokens are stored in `localStorage`.
- Tenant context is also derived from `localStorage`, which makes tenant scoping client-driven.
- `businessConfigApi` accepts a `businessId`, but several methods still call fixed `/admin/config` endpoints, so the parameter is not always truly used.
- `next.config.mjs` adds a rewrite for `/api/v1/:path*` to the backend, which supports local/Docker deployment.
