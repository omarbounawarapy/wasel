"use client"

import Link from "next/link"
import Image from "next/image"
import { Sidebar } from "@/components/dashboard/Sidebar"
import { MobileFootbar } from "@/components/dashboard/MobileFootbar"
import { HealthBar } from "@/components/dashboard/HealthBar"
import ErrorBoundary from "@/components/ErrorBoundary"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <ErrorBoundary>
                <div className="flex bg-surface text-gray-800 font-sans h-dvh w-full overflow-hidden">
                    <div className="hidden lg:flex bg-surface-sidebar border-r border-brand/15 flex-shrink-0">
                        <Sidebar />
                    </div>

                    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                        <header className="lg:hidden flex items-center px-4 pt-3">
                            <Link prefetch={false} href="/dashboard" aria-label="Wasel home" className="inline-flex items-center min-h-[44px]">
                                <Image priority src="/wasel-logo-compact.png" alt="Wasel" width={140} height={34} className="w-[140px] h-auto" />
                            </Link>
                        </header>
                        <div className="px-4 lg:px-8 pt-3 w-full max-w-7xl">
                            <HealthBar />
                        </div>
                        <main className="flex-1 overflow-y-auto px-4 lg:px-8 pt-5 pb-32 lg:pb-10">
                            {children}
                        </main>
                    </div>
                </div>
                <MobileFootbar />
        </ErrorBoundary>
    )
}
