# Frontend Security Review

This document outlines a basic security review of the `frontend_next` application based on a static code analysis.

## Findings

### 1. Cross-Site Scripting (XSS)
- **`dangerouslySetInnerHTML` Usage:** Found in several places:
  - `app/layout.tsx` and `app/solutions/[industry]/page.tsx` for injecting JSON-LD (`organizationSchema`, `softwareSchema`, `jsonLd`). This is generally safe if the JSON data is hardcoded or properly sanitized, but any dynamic user input mixed into these schemas could lead to XSS.
  - `components/scrolling-logos.tsx` (and `ui/scrolling-logos.tsx`) uses it to render SVGs. If the SVG content comes from an untrusted source, this is a significant XSS vector.
  - `components/ui/chart.tsx` and `components/landing/FAQ.tsx` also use it.

### 2. Insecure Direct Object References (IDOR) / Tenant Isolation
- **Client-Side Tenant ID Injection:** The API client (`lib/api.ts`) automatically injects the `X-Tenant-ID` header based on what is stored in `localStorage` (`tenant_id` or parsed from the `user` object).
- **Risk:** A malicious user could manually modify the `tenant_id` in their browser's local storage. If the backend relies solely on this header for data isolation without verifying that the authenticated user (via the Bearer token) actually belongs to that tenant, an attacker could access or modify another tenant's data.
- **Config API Pattern:** Several methods in `lib/api/business-config.ts` accept a `businessId` parameter but then make requests to fixed endpoints like `/admin/config` without passing the ID in the URL. This relies entirely on the interceptor's `X-Tenant-ID` header, reinforcing the IDOR risk described above.

### 3. Exposed Secrets & Environment Variables
- **API URLs:** `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`, and `NEXT_PUBLIC_VAPI_PUBLIC_KEY` are exposed to the client. Exposing the API and WS URLs is normal. Exposing a VAPI public key might be acceptable depending on VAPI's architecture (if it's truly a public publishable key), but should be verified.
- **No obvious hardcoded private keys** (like Stripe secret keys or database passwords) were found in the frontend code during this initial scan, as expected for a Next.js frontend.

### 4. Authentication & Authorization
- **Token Storage:** JWT access tokens are stored in `localStorage` (`access_token`). This makes them susceptible to theft via XSS attacks. If an attacker successfully executes JavaScript on the page (e.g., via the SVG issue mentioned above), they can easily extract the token and impersonate the user.
- **Role-Based Redirects:** The frontend redirects based on the user's role (e.g., `super_admin` goes to `/admin`, others to `/dashboard`). While helpful for UX, the backend must enforce these boundaries, as frontend checks are easily bypassed.

## Recommendations
1. **Move Tokens to HttpOnly Cookies:** Transition from storing auth tokens in `localStorage` to HttpOnly, secure cookies. This mitigates the risk of token theft via XSS.
2. **Backend Tenant Verification:** Ensure the backend never trusts the `X-Tenant-ID` header blindly. It must securely derive or verify the user's tenant ID from the authenticated JWT token payload on every request.
3. **Audit `dangerouslySetInnerHTML`:** Review all instances where HTML or SVGs are injected directly. Ensure inputs are stringently sanitized (e.g., using DOMPurify) if they originate from user input or external databases.
4. **Review VAPI Key:** Confirm that `NEXT_PUBLIC_VAPI_PUBLIC_KEY` does not grant privileged access that could be abused if extracted by an end-user.
