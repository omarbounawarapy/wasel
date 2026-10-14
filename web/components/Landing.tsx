"use client"

import Image from "next/image"
import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { LangSwitcher, useT } from "@/lib/i18n"
import SiteFooter from "@/components/SiteFooter"

export default function Landing() {
  const { t } = useT()
  return (
    <div className="min-h-dvh bg-surface flex flex-col">
      <a href="#main" className="skip-link">{t("skip")}</a>
      <header className="w-full max-w-5xl mx-auto px-4 pt-4 flex items-center justify-between gap-3">
        <Image priority src="/wasel-logo-compact.png" alt="Wasel" width={160} height={38} className="logo-plate w-[160px] h-auto" />
        <LangSwitcher />
      </header>
      <main id="main" tabIndex={-1} className="flex-1 w-full max-w-5xl mx-auto px-4 py-8 sm:py-16 grid gap-10 lg:grid-cols-2 lg:items-center">
        <div className="space-y-6">
          <p className="text-sm font-semibold text-teal-ink">{t("landing.eyebrow")}</p>
          <h1 className="text-3xl sm:text-4xl font-bold text-brand-ink text-balance leading-tight">{t("landing.title")}</h1>
          <p className="text-base text-gray-700 max-w-prose">{t("landing.body")}</p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link prefetch={false} href="/dashboard/paste"
                  className="inline-flex items-center justify-center gap-2 px-6 min-h-[48px] rounded-xl bg-brand hover:bg-brand-hover text-white text-base font-semibold">
              {t("landing.primary")} <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link prefetch={false} href="/dashboard"
                  className="inline-flex items-center justify-center px-6 min-h-[48px] rounded-xl border border-gray-300 bg-white text-gray-800 text-base font-semibold hover:border-brand/40">
              {t("landing.secondary")}
            </Link>
          </div>
          <p className="text-xs text-gray-600">{t("landing.note")}</p>
        </div>
        <section aria-labelledby="how" className="bg-white rounded-2xl border border-gray-200/70 shadow-sm p-6 space-y-4">
          <h2 id="how" className="text-base font-bold text-brand-ink">{t("landing.how.title")}</h2>
          <ol className="space-y-4">
            {(["landing.how.1", "landing.how.2", "landing.how.3"] as const).map((k, i) => (
              <li key={k} className="flex items-start gap-3">
                <span className="shrink-0 w-7 h-7 rounded-full bg-brand text-white text-sm font-bold flex items-center justify-center">{i + 1}</span>
                <span className="text-sm text-gray-800 leading-snug pt-1">{t(k)}</span>
              </li>
            ))}
          </ol>
        </section>
      </main>
      <SiteFooter className="w-full max-w-5xl mx-auto px-4 pb-6" />
    </div>
  )
}
