import type { Metadata } from "next"
import QueueDashboard from "@/components/dashboard/QueueDashboard"

export const metadata: Metadata = {
    title: "Orders to check · Wasel",
}

export default function Page() {
    return <QueueDashboard />
}
