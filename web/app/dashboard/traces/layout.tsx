import { pageMeta } from "@/lib/meta"

export const metadata = pageMeta("/dashboard/traces")

// Server layout only: gives this route its own browser-tab title, description and canonical URL in the static export.
export default function Layout({ children }: { children: React.ReactNode }) {
    return children
}
