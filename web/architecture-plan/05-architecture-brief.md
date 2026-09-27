# Frontend Architecture Brief

## What This Frontend Is
- A Next.js App Router application built with React and TypeScript.
- It serves a marketing site, auth flows, a business dashboard, and an admin console.
- It is designed as a multi-tenant SaaS frontend.

## Main Building Blocks
- `app/layout.tsx` is the global shell with metadata, font setup, JSON-LD, and top-level providers.
- `components/providers.tsx` stacks React Query, auth, config, and tenant context.
- `contexts/AuthContext.tsx` owns session restoration, login, registration, and logout.
- `contexts/ConfigContext.tsx` and `contexts/TenantContext.tsx` expose tenant-specific business state.
- `lib/api.ts` is the shared HTTP client.
- `lib/api-endpoints.ts` and `lib/api/*` hold feature-specific API wrappers.
- `components/ui/*` provides the reusable component library.

## How Data Flows
- The user logs in through `FrostedGlassAuth`.
- `AuthContext` stores the token and user profile.
- `api.ts` injects auth and tenant headers into requests.
- `ConfigContext` fetches tenant-scoped config through React Query.
- Dashboard and admin components consume that state through hooks and contexts.

## Key Things to Understand Next
- Routing behavior in the App Router.
- Session and tenant persistence in `localStorage`.
- How the dashboard/admin shells differ.
- Which API files are active versus legacy or duplicated wrappers.
- Which style tokens and UI primitives define the visual system.
