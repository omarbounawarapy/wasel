"use client"

import Link from "next/link"
import { Sidebar } from "@/components/dashboard/Sidebar"
import { MobileFootbar } from "@/components/dashboard/MobileFootbar"
import { HealthBar } from "@/components/dashboard/HealthBar"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Toaster } from "@/components/ui/toaster"
import { Toaster as Sonner } from "@/components/ui/sonner"
import ErrorBoundary from "@/components/ErrorBoundary"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <ErrorBoundary>
            <TooltipProvider>
                <div className="flex bg-[#f4f6f9] text-gray-800 font-sans h-screen w-full overflow-hidden">
                    <div className="hidden lg:flex bg-[#eef2f7] border-r border-gray-200/70 flex-shrink-0">
                        <Sidebar />
                    </div>

                    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                        <header className="lg:hidden flex items-center px-4 pt-3">
                            <Link prefetch={false} href="/dashboard" aria-label="Wasel home">
                                <img src="/wasel-logo.png" alt="Wasel" width={140} height={34} className="w-[140px] h-auto" />
                            </Link>
                        </header>
                        <div className="px-4 lg:px-8 pt-3">
                            <HealthBar />
                        </div>
                        <main className="flex-1 overflow-y-auto px-4 lg:px-8 pt-5 pb-28 lg:pb-10">
                            {children}
                        </main>
                    </div>
                </div>
                <MobileFootbar />
                <Toaster />
                <Sonner />
            </TooltipProvider>
        </ErrorBoundary>
    )
}
