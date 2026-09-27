# UI System

## Shared Shells
- `components/auth/FrostedGlassAuth.tsx` drives login, signup, and placeholder auth flows.
- `components/dashboard/Sidebar.tsx` builds the main business dashboard navigation.
- `components/admin/AdminSidebar.tsx` builds the admin navigation.
- `components/providers.tsx` supplies React Query and context providers to the app.

## Page Composition
- Landing pages are assembled from `components/landing/*` sections like `Hero`, `Navbar`, `Pricing`, and `FAQ`.
- Dashboard pages use a responsive app shell with sidebar, header, and mobile footbar.
- Admin pages use a separate sidebar-driven shell.

## UI Primitives
- `components/ui/*` contains the reusable design system primitives.
- The folder includes shadcn/Radix-style controls such as `button`, `input`, `dialog`, `tooltip`, `table`, `tabs`, `toast`, and `sonner`.

## Styling Pattern
- Tailwind CSS 4 is used through `app/globals.css`.
- The app relies on CSS variables for theme tokens such as `--primary`, `--sage`, `--forest`, and `--lime`.
- Dark mode is class-based via `.dark`.

## Notable UX Choices
- The app favors custom branded shells over generic admin layouts.
- Navigation uses `next/link` in most places, but some auth flows still use `window.location.href` or `router.push` for redirects.
- The dashboard and admin areas are visually and behaviorally separate.
