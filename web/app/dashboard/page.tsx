import { pageMeta } from "@/lib/meta"
import QueueDashboard from "@/components/dashboard/QueueDashboard"

export const metadata = pageMeta("/dashboard")

export default function Page() {
    return <QueueDashboard />
}
