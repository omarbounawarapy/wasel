import type { Metadata } from "next";
import NotFound from "@/components/NotFound";

export const metadata: Metadata = {
    title: "Page not found · Wasel",
    description: "This page does not exist. Go back to the list of orders to check.",
    robots: { index: false, follow: false },
};

export default function NotFoundPage() {
    return <NotFound />;
}
