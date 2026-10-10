import type { Metadata } from "next"

export const metadata: Metadata = {
    title: "Live monitor · Wasel",
}

// Server layout only: gives this route its own browser-tab title in the static export.
export default function Layout({ children }: { children: React.ReactNode }) {
    return children
}
