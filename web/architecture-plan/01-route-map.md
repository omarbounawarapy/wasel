# Route Map

## Root
- `app/layout.tsx` is the root shell for the entire frontend.
- `app/page.tsx` is the landing page.
- `app/login/page.tsx` and `app/signup/page.tsx` render the auth screens.

## App Areas
- `app/dashboard/` contains the authenticated business dashboard.
- `app/admin/` contains the admin/super-admin area.
- `app/contact/` and `app/solutions/[industry]/` support marketing/content pages.

## Nested Dashboard Routes
- `dashboard/appointments`
- `dashboard/calls`
- `dashboard/help`
- `dashboard/schedule`
- `dashboard/services`
- `dashboard/settings/*`
- `dashboard/voice-agent/*`
- `dashboard/whatsapp`

## Nested Admin Routes
- `admin/appointments`
- `admin/billing`
- `admin/config`
- `admin/contacts`
- `admin/login`
- `admin/services`
- `admin/settings`
- `admin/system`
- `admin/tenants`
- `admin/users`
- `admin/vapi-test`
