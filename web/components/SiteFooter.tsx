"use client"

import Link from "next/link"
import { useT } from "@/lib/i18n"
import { CONTACT_EMAIL } from "@/lib/site"

/** One footer for the landing, privacy and 404 pages and the dashboard: privacy and a contact are two clicks away everywhere. */
export default function SiteFooter({ className = "" }: { className?: string }) {
  const { t } = useT()
  return (
    <footer className={`text-xs text-gray-600 flex flex-wrap items-center gap-x-4 gap-y-1 ${className}`}>
      <span>{t("footer.demo")}</span>
      <Link prefetch={false} href="/privacy" className="inline-flex items-center min-h-[44px] underline underline-offset-2 hover:text-brand">{t("footer.privacy")}</Link>
      <a href={`mailto:${CONTACT_EMAIL}`} className="inline-flex items-center min-h-[44px] underline underline-offset-2 hover:text-brand">{t("footer.contact")}: {CONTACT_EMAIL}</a>
    </footer>
  )
}
