"use client";

import Image from "next/image";
import Link from "next/link";
import { useT } from "@/lib/i18n";
import SiteFooter from "@/components/SiteFooter";

export default function NotFound() {
    const { t } = useT();
    return (
        <main className="min-h-screen w-full flex items-center justify-center bg-surface p-4">
            <div className="max-w-md w-full bg-white rounded-2xl border border-gray-200/70 shadow-sm p-8 text-center space-y-5">
                <Image src="/wasel-logo-compact.png" alt="Wasel" width={180} height={43} className="logo-plate w-[180px] h-auto mx-auto" />
                <div className="space-y-1">
                    <h1 className="text-xl font-bold text-brand-ink">{t("notfound.title")}</h1>
                    <p className="text-sm text-gray-600">{t("notfound.body")}</p>
                </div>
                <Link prefetch={false} href="/dashboard"
                      className="inline-flex items-center justify-center px-5 min-h-[44px] rounded-xl bg-brand hover:bg-brand-hover text-white text-sm font-semibold">
                    {t("notfound.back")}
                </Link>
                <SiteFooter className="justify-center border-t border-gray-200 pt-3" />
            </div>
        </main>
    );
}
