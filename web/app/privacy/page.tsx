import Image from "next/image"
import Link from "next/link"
import SiteFooter from "@/components/SiteFooter"
import { pageMeta } from "@/lib/meta"
import { CONTACT_EMAIL } from "@/lib/site"

export const metadata = pageMeta("/privacy")

// What the demo stores, read from src/wasel/settings.py (SANDBOX_TTL_S 7200, RETENTION_* days) and
// docs/architecture/data-model.md. Update this page in the same change as any of those.
export default function PrivacyPage() {
  return (
    <div className="min-h-dvh bg-surface">
      <main id="main" className="w-full max-w-3xl mx-auto px-4 py-8 sm:py-12">
        <Link prefetch={false} href="/" aria-label="Wasel home" className="inline-flex items-center min-h-[44px]">
          <Image priority src="/wasel-logo-compact.png" alt="Wasel" width={150} height={36} className="logo-plate w-[150px] h-auto" />
        </Link>
        <article className="mt-6 bg-white rounded-2xl border border-gray-200/70 shadow-sm p-6 sm:p-8 space-y-6 text-sm text-gray-800 leading-relaxed">
          <header className="space-y-2">
            <h1 className="text-2xl font-bold text-brand-ink">Privacy</h1>
            <p className="text-gray-600">This page describes the public Wasel demo at wasel.runs-on.dev. It is a demonstration with synthetic data, not a service for real customers.</p>
          </header>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-brand-ink">What is collected</h2>
            <ul className="list-disc ps-5 space-y-1.5">
              <li><strong>The message text you type</strong> into Add an order or into the simulated customer reply. It is sent to the server to be scored.</li>
              <li><strong>A visitor id</strong>: a random identifier your browser creates and sends with each request, so you see only your own orders. It is not linked to your name, email or phone.</li>
              <li><strong>Usage events</strong> of the product itself (an order scored, a draft created). They hold no name or contact detail.</li>
              <li>The customer name field is <strong>not stored</strong> in the demo: the server discards it.</li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-brand-ink">How long it is kept</h2>
            <ul className="list-disc ps-5 space-y-1.5">
              <li>Orders, messages, drafts and events you create are deleted <strong>2 hours</strong> after your conversation was opened, and the demo database is rebuilt whenever the server restarts.</li>
              <li>Counters of AI calls (no message text) are kept for up to 30 days; recorded AI read results up to 30 days.</li>
              <li>Hosting providers keep their own request logs (address, time, path) under their own policies.</li>
            </ul>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-brand-ink">Who receives the text</h2>
            <p>To read a message, the server sends its text to a language model provider: <strong>Groq</strong>. If the operator turns on <strong>AMD Token Factory</strong> (AMD's hosted model API), the text goes there first and Groq becomes its backup. A Google Gemini backup exists in the code and is used only if the operator enables it. Wasel does not sell or share your text with anyone else, and does not use it for advertising.</p>
            <p>The site is served through Render and Cloudflare, which see your IP address and the pages you request, as any web host does.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-brand-ink">Cookies and storage</h2>
            <p>The demo sets <strong>no cookies</strong> and runs <strong>no analytics or advertising scripts</strong>. Your browser's local storage holds three things, all needed for the site to work: your visitor id, your language choice, and which how-to guides you closed. Clear them from the browser's site settings at any time. Because only strictly necessary storage is used, there is no cookie banner.</p>
          </section>

          <section className="space-y-2">
            <h2 className="text-base font-bold text-brand-ink">Your questions and requests</h2>
            <p>To ask what is held about your visitor id, or to have it deleted, write to <a className="underline underline-offset-2 text-brand" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>. Include the visitor id (browser developer tools, Application, Local storage, <code className="font-mono text-xs">cod_visitor_id</code>).</p>
            <p>Operator: Z-Team, the team that builds Wasel (see the <a className="underline underline-offset-2 text-brand" href="https://github.com/omarbounawarapy/wasel/blob/main/TEAM.md">team page</a>).</p>
          </section>

          <p lang="fr" className="text-xs text-gray-600">Résumé en français : la démo ne dépose aucun cookie, ne fait aucune mesure d'audience, supprime vos données après 2 heures et envoie le texte des messages à Groq pour les analyser. Contact : {CONTACT_EMAIL}.</p>
          <p lang="ar" dir="rtl" className="text-xs text-gray-600">ملخص بالعربية: لا يضع العرض التجريبي أي ملفات تعريف ارتباط ولا يقيس الزيارات، ويحذف بياناتك بعد ساعتين، ويرسل نص الرسائل إلى Groq لتحليلها. للتواصل: {CONTACT_EMAIL}.</p>
        </article>
        <SiteFooter className="mt-6" />
      </main>
    </div>
  )
}
