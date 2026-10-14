"use client"

import Link from "next/link"
import Image from "next/image"
import { Sidebar } from "@/components/dashboard/Sidebar"
import { MobileFootbar } from "@/components/dashboard/MobileFootbar"
import { HealthBar } from "@/components/dashboard/HealthBar"
import ErrorBoundary from "@/components/ErrorBoundary"
import SiteFooter from "@/components/SiteFooter"
import { LangSwitcher, useT } from "@/lib/i18n"

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode
}) {
    const { t } = useT()
    return (
        <ErrorBoundary>
                <a href="#main" className="skip-link">{t("skip")}</a>
                <div className="flex bg-surface text-gray-800 font-sans h-dvh w-full overflow-hidden">
                    <div className="hidden lg:flex bg-surface-sidebar border-e border-brand/15 flex-shrink-0">
                        <Sidebar />
                    </div>

                    <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
                        <header className="lg:hidden flex items-center justify-between gap-3 px-4 pt-3">
                            <Link prefetch={false} href="/dashboard" aria-label={t("nav.home")} className="inline-flex items-center min-h-[44px]">
                                <Image priority src="/wasel-logo-compact.png" alt="Wasel" width={140} height={34} className="logo-plate w-[140px] h-auto" />
                            </Link>
                            <LangSwitcher />
                        </header>
                        <div className="px-4 lg:px-8 pt-3 w-full max-w-7xl">
                            <HealthBar />
                        </div>
                        <main id="main" tabIndex={-1} className="flex-1 overflow-y-auto px-4 lg:px-8 pt-5 pb-40 lg:pb-10 focus:outline-none">
                            {children}
                            <SiteFooter className="mt-10" />
                        </main>
                    </div>
                </div>
                <MobileFootbar />
        </ErrorBoundary>
    )
}
