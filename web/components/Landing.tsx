"use client"

import { Fragment } from "react"
import Image from "next/image"
import Link from "next/link"
import { ArrowRight } from "lucide-react"
import { LangSwitcher, useT } from "@/lib/i18n"
import { ScoreFigure } from "@/components/wasel/kit"
import SiteFooter from "@/components/SiteFooter"

// The seeded hero order (#2601, data/seed/demo_seed.json and tests/golden/hero.json), shown instead of described:
// the customer's words with what Wasel noticed marked, the score, then the same order after one reply.
// Marks use the order page's highlight styles: amber raises the risk, a green underline lowers it.
type Part = string | { text: string, kind: "risk" | "good" }
const BEFORE: Part[][] = [
  ["Douar Ouled Ali, ", { text: "9rib el jemaa", kind: "risk" }],
  ["ama ", { text: "ghali chwaya", kind: "risk" }, ". ", { text: "mouch dima fi dar", kind: "risk" }, "…"],
]
const AFTER: Part[][] = [
  [{ text: "ey behi", kind: "good" }, ". ", { text: "Douar Ouled Ali, triq el jemaa, dar 14", kind: "good" }, "…"],
]

function Bubble({ parts }: { parts: Part[] }) {
  return (
    <p dir="auto" className="w-fit max-w-full rounded-2xl rounded-ss-md bg-gray-100 px-4 py-2.5 text-[14px] leading-relaxed text-gray-900 text-start">
      {parts.map((p, i) => typeof p === "string"
        ? <Fragment key={i}>{p}</Fragment>
        : <mark key={i} className={p.kind === "risk"
            ? "bg-amber-200 text-amber-950 underline decoration-dotted decoration-2 underline-offset-2 decoration-amber-600 rounded-sm"
            : "bg-transparent text-gray-900 border-b-2 border-emerald-600"}>{p.text}</mark>)}
    </p>
  )
}

function Verdict({ score, tier, label, action, delta }: { score: number, tier: "high" | "low", label: string, action: string, delta?: number }) {
  return (
    <div className="mt-4 flex items-end justify-between gap-4">
      <ScoreFigure tier={tier} score={score} delta={delta} label={label} />
      <span className="inline-flex items-center gap-1.5 pb-0.5 text-[13px] font-medium text-gray-800 whitespace-nowrap">
        <ArrowRight className="w-3.5 h-3.5 rtl:rotate-180" aria-hidden="true" /> {action}
      </span>
    </div>
  )
}

function ScoreStory() {
  const { t } = useT()
  return (
    <section aria-label={t("landing.demo.label")}
             className="rounded-[28px] bg-card border border-border shadow-lg p-5 sm:p-7 animate-in fade-in slide-in-from-bottom-2 duration-700">
      <div className="flex items-center justify-between gap-3 text-[13px]">
        <span className="font-semibold text-brand-ink tabular-nums">#2601 · Sami</span>
        <span className="text-gray-600 truncate">casque bluetooth · 220 TND</span>
      </div>

      <div className="mt-5 flex flex-col gap-2">{BEFORE.map((parts, i) => <Bubble key={i} parts={parts} />)}</div>
      <Verdict score={87} tier="high" label={t("landing.demo.high")} action={t("landing.demo.confirm")} />

      <div className="my-6 flex items-center gap-3">
        <span className="h-px flex-1 bg-border" />
        <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-gray-600">{t("landing.demo.after")}</span>
        <span className="h-px flex-1 bg-border" />
      </div>

      <div className="flex flex-col gap-2">{AFTER.map((parts, i) => <Bubble key={i} parts={parts} />)}</div>
      <Verdict score={16} tier="low" label={t("landing.demo.low")} action={t("landing.demo.ship")} delta={-71} />
    </section>
  )
}

export default function Landing() {
  const { t } = useT()
  return (
    <div className="min-h-dvh bg-surface flex flex-col">
      <a href="#main" className="skip-link">{t("skip")}</a>
      <header className="w-full max-w-6xl mx-auto px-5 sm:px-8 pt-5 flex items-center justify-between gap-3">
        <Image priority src="/wasel-logo-compact.png" alt="Wasel" width={160} height={38} className="logo-plate w-[132px] h-auto" />
        <LangSwitcher />
      </header>
      <main id="main" tabIndex={-1}
            className="flex-1 w-full max-w-6xl mx-auto px-5 sm:px-8 py-12 sm:py-20 grid gap-12 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:gap-20 lg:items-center focus:outline-none">
        <div>
          <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-teal-ink">{t("landing.eyebrow")}</p>
          <h1 className="mt-5 text-[clamp(36px,4.4vw,56px)] leading-[1.04] font-semibold tracking-[-0.045em] text-brand-ink text-balance">{t("landing.title")}</h1>
          <p className="mt-6 text-[17px] leading-relaxed text-gray-600 max-w-[34rem]">{t("landing.body")}</p>
          <div className="mt-9 flex flex-col sm:flex-row gap-3">
            <Link prefetch={false} href="/dashboard/paste"
                  className="inline-flex items-center justify-center gap-2 px-7 min-h-[52px] rounded-full bg-brand hover:bg-brand-hover text-white text-[15px] font-semibold shadow-md transition-colors">
              {t("landing.primary")} <ArrowRight className="w-4 h-4 rtl:rotate-180" aria-hidden="true" />
            </Link>
            <Link prefetch={false} href="/dashboard"
                  className="inline-flex items-center justify-center px-7 min-h-[52px] rounded-full border border-gray-300 bg-card text-gray-800 text-[15px] font-semibold hover:border-gray-500 transition-colors">
              {t("landing.secondary")}
            </Link>
          </div>
          <p className="mt-6 text-xs text-gray-600">{t("landing.note")}</p>
        </div>
        <ScoreStory />
      </main>
      <SiteFooter className="w-full max-w-6xl mx-auto px-5 sm:px-8 pb-6" />
    </div>
  )
}
