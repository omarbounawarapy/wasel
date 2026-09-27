# Detailed Security Deep Dive

This document follows up the initial security review with an architectural and implementation-level security scan of the `frontend_next` application.

## Transport, Headers & Infrastructure

1. **Missing HTTP Security Headers:** 
   - `next.config.mjs` currently has an external API rewrite but lacks standard security boundary headers. 
   - **Risk:** Without `Content-Security-Policy (CSP)`, `X-Frame-Options`, `Strict-Transport-Security (HSTS)`, `X-Content-Type-Options: nosniff`, and `Referrer-Policy`, the application is more susceptible to clickjacking, mime-sniffing, and iframe embeddings from external sites.
   - **Recommendation:** Add a `headers()` block to `next.config.mjs` to inject standard web security headers globally.

2. **CORS and `withCredentials` configurations:**
   - In `lib/api.ts`, the Axios client is instantiated with `withCredentials: true`. This setting directs the browser to send cookies, TLS client certificates, and basic auth headers across domains.
   - **Risk:** The app currently relies on `Authorization: Bearer <token>` (stored in `localStorage`), which makes CSRF (Cross-Site Request Forgery) extremely difficult since tokens aren't sent automatically. However, if the backend ever sets a session cookie (e.g., from an OAuth provider like Google or a forgotten auth handler), `withCredentials: true` immediately introduces CSRF risks unless the backend strictly validates Origins and SameSite cookies.
   - **Recommendation:** Only use `withCredentials: true` if an HttpOnly Cookie architecture natively uses it. If sticking to Bearer tokens, remove this setting to reduce the attack surface.

## Input Validation & State Integrity

1. **Absence of Strict Schema Validation (Zod/Yup) in Auth Flows:**
   - In `components/auth/FrostedGlassAuth.tsx`, user inputs (like email, password, business name) are validated manually (e.g., `formData.name && formData.email ...`).
   - **Risk:** Manual validation is prone to edge-case bypasses, type confusion, or unexpected input lengths (e.g., submitting a 10,000-character payload causing a backend DoS, or bypassing specific data structures).
   - **Recommendation:** Integrate the installed `zod` library (seen in `package.json`) combined with `react-hook-form` and `@hookform/resolvers` for rigorous boundary validation (max lengths, regex constraints, data typing).

2. **Unvalidated Object Types in Payload:**
   - A potential issue is present in `lib/api/business-config.ts` where partial `BusinessConfig` updates are pushed to the backend via uncontrolled `data` objects.
   - **Risk:** Without explicit payload pruning on the frontend, an attacker could intercept the API request and inject extra backend properties (Mass Assignment/Overposting risk). E.g., modifying `is_configured` or `features_enabled` if the backend doesn't sanitize the update schema.
   - **Recommendation:** Strip payloads cleanly on the frontend and ensure the backend strictly maps allowable update parameters.

## Handling of Sensitive Data & Logging

1. **Client-Side Diagnostics & Error Leaks:**
   - `lib/errorLogging.ts` implements robust frontend diagnostics reporting (`postDiagnostics`). However, when network requests fail, it logs `preview.substring(0, 1000)` of the response payload directly to the diagnosis endpoint (`frontend-error`).
   - **Risk:** This can lead to sensitive PII, backend stack traces, or credentials being sent broadly to the monitoring infrastructure if a failure occurs during authentication, database querying, or third-party integration sync.
   - **Recommendation:** Create a redaction phase in the `logClientError` service that scrubs tokens, emails, and passwords from the payload strings before posting diagonally.

2. **Client-Side Route Authorization vs Server Validation:**
   - `components/auth/ProtectedRoute.tsx` and layouts (`app/dashboard/layout.tsx`, `app/admin/layout.tsx`) verify whether a user can see a page purely by checking `user.role` from `localStorage` derived `AuthContext`.
   - **Risk:** While totally standard for SPAs (rendering components), it is crucial to ensure that any API requests performed on these specific routes (e.g., `/admin/tenants`) are authenticated server-side against the *actor's* valid role permissions, not the frontend UI boundaries.

## Architecture Notes
- **VAPI Usage:** Exposing `NEXT_PUBLIC_VAPI_PUBLIC_KEY` in env is confirmed correctly handled, as VAPI explicitly separates the "Public" key for web-client WebRTC connections and the "Private" token for backend configuration APIs.
- Next.js Image Component has `unoptimized: true` enabled in configuration. This sacrifices intrinsic XSS protections (SVG payload stripping and metadata destruction algorithms) within Next.js processing. Any remote user-uploaded avatars should be strictly sanitized on the backend before returning image URLs.
