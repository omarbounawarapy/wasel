"use client"

// Interface language (English, French, Arabic). The choice is kept in this browser only; the page starts in English
// so the static export and the first paint always match, then switches after mount. `lang` and `dir` on <html> follow it.
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react"

export type Lang = "en" | "fr" | "ar"
export const LANGS: { code: Lang, label: string, name: string }[] = [
  { code: "en", label: "EN", name: "English" },
  { code: "fr", label: "FR", name: "Français" },
  { code: "ar", label: "عربي", name: "العربية" },
]

const STORAGE_KEY = "wasel_lang"

const EN = {
  "skip": "Skip to content",
  "lang.label": "Language",
  "nav.main": "Main",
  "nav.group.daily": "Daily work",
  "nav.group.results": "Results",
  "nav.group.health": "AI health",
  "nav.group.advanced": "Advanced",
  "nav.orders": "Orders to check",
  "nav.whatsapp": "WhatsApp messages",
  "nav.add": "Add an order",
  "nav.money": "Money saved",
  "nav.activity": "Activity log",
  "nav.quality": "Quality checks",
  "nav.monitor": "Live monitor",
  "nav.calls": "AI call log",
  "nav.failures": "Silent failures",
  "nav.bar.orders": "Orders",
  "nav.bar.whatsapp": "WhatsApp",
  "nav.bar.add": "Add",
  "nav.bar.money": "Money saved",
  "nav.bar.more": "More",
  "nav.home": "Wasel home",
  "cta.add": "Add an order",
  "footer.privacy": "Privacy",
  "footer.contact": "Contact",
  "footer.demo": "Demo with synthetic data.",
  "landing.eyebrow": "COD order risk for Tunisian shops",
  "landing.title": "Know which cash-on-delivery orders will be refused, before you ship.",
  "landing.body": "Paste what the customer wrote, in Darija, Arabizi, Arabic or French. Wasel scores the refusal risk and drafts the confirmation message. You approve every reply.",
  "landing.primary": "Add an order",
  "landing.secondary": "See the sample queue",
  "landing.note": "The demo runs on synthetic data. Nothing is sent to a real customer.",
  "landing.demo.label": "Example order",
  "landing.demo.high": "High risk",
  "landing.demo.low": "Low risk",
  "landing.demo.confirm": "Confirm first",
  "landing.demo.ship": "Ship it",
  "landing.demo.after": "After one reply",
  "notfound.title": "This page doesn't exist",
  "notfound.body": "The link may be old, or the order may have been deleted.",
  "notfound.back": "Back to orders",
  "waking.title": "Wasel is starting up",
  "waking.body": "The free demo server was asleep. This takes about a minute, then the page loads by itself.",
  "retry": "Retry",
} as const

type Key = keyof typeof EN

const FR: Record<Key, string> = {
  "skip": "Aller au contenu",
  "lang.label": "Langue",
  "nav.main": "Principale",
  "nav.group.daily": "Travail du jour",
  "nav.group.results": "Résultats",
  "nav.group.health": "Santé de l'IA",
  "nav.group.advanced": "Avancé",
  "nav.orders": "Commandes à vérifier",
  "nav.whatsapp": "Messages WhatsApp",
  "nav.add": "Ajouter une commande",
  "nav.money": "Argent économisé",
  "nav.activity": "Journal d'activité",
  "nav.quality": "Contrôles qualité",
  "nav.monitor": "Suivi en direct",
  "nav.calls": "Journal des appels IA",
  "nav.failures": "Erreurs silencieuses",
  "nav.bar.orders": "Commandes",
  "nav.bar.whatsapp": "WhatsApp",
  "nav.bar.add": "Ajouter",
  "nav.bar.money": "Économies",
  "nav.bar.more": "Plus",
  "nav.home": "Accueil Wasel",
  "cta.add": "Ajouter une commande",
  "footer.privacy": "Confidentialité",
  "footer.contact": "Contact",
  "footer.demo": "Démo avec des données synthétiques.",
  "landing.eyebrow": "Risque de refus à la livraison pour les boutiques tunisiennes",
  "landing.title": "Sachez quelles commandes avec paiement à la livraison seront refusées, avant d'expédier.",
  "landing.body": "Collez le message du client, en derja, arabizi, arabe ou français. Wasel calcule le risque de refus et rédige le message de confirmation. Vous validez chaque réponse.",
  "landing.primary": "Ajouter une commande",
  "landing.secondary": "Voir la file d'exemple",
  "landing.note": "La démo utilise des données synthétiques. Rien n'est envoyé à un vrai client.",
  "landing.demo.label": "Exemple de commande",
  "landing.demo.high": "Risque élevé",
  "landing.demo.low": "Risque faible",
  "landing.demo.confirm": "Confirmer d'abord",
  "landing.demo.ship": "Expédier",
  "landing.demo.after": "Après une réponse",
  "notfound.title": "Cette page n'existe pas",
  "notfound.body": "Le lien est peut-être ancien, ou la commande a été supprimée.",
  "notfound.back": "Retour aux commandes",
  "waking.title": "Wasel démarre",
  "waking.body": "Le serveur de démonstration gratuit dormait. Cela prend environ une minute, puis la page se charge seule.",
  "retry": "Réessayer",
}

const AR: Record<Key, string> = {
  "skip": "انتقل إلى المحتوى",
  "lang.label": "اللغة",
  "nav.main": "الرئيسية",
  "nav.group.daily": "العمل اليومي",
  "nav.group.results": "النتائج",
  "nav.group.health": "حالة الذكاء الاصطناعي",
  "nav.group.advanced": "متقدم",
  "nav.orders": "طلبات للمراجعة",
  "nav.whatsapp": "رسائل واتساب",
  "nav.add": "إضافة طلب",
  "nav.money": "المال الموفَّر",
  "nav.activity": "سجل النشاط",
  "nav.quality": "فحوصات الجودة",
  "nav.monitor": "المراقبة المباشرة",
  "nav.calls": "سجل نداءات الذكاء الاصطناعي",
  "nav.failures": "الأخطاء الصامتة",
  "nav.bar.orders": "الطلبات",
  "nav.bar.whatsapp": "واتساب",
  "nav.bar.add": "إضافة",
  "nav.bar.money": "الموفَّر",
  "nav.bar.more": "المزيد",
  "nav.home": "الصفحة الرئيسية لواصل",
  "cta.add": "إضافة طلب",
  "footer.privacy": "الخصوصية",
  "footer.contact": "التواصل",
  "footer.demo": "عرض تجريبي ببيانات اصطناعية.",
  "landing.eyebrow": "خطر رفض الطلبات عند الدفع عند الاستلام للمتاجر التونسية",
  "landing.title": "اعرف أي طلبات الدفع عند الاستلام سيتم رفضها، قبل أن تشحنها.",
  "landing.body": "الصق رسالة الحريف بالدارجة أو الأرابيزي أو العربية أو الفرنسية. يحسب واصل خطر الرفض ويكتب رسالة التأكيد. أنت توافق على كل ردّ.",
  "landing.primary": "إضافة طلب",
  "landing.secondary": "عرض قائمة العيّنة",
  "landing.note": "العرض التجريبي يعمل ببيانات اصطناعية. لا يُرسل شيء إلى حريف حقيقي.",
  "landing.demo.label": "مثال على طلب",
  "landing.demo.high": "خطر مرتفع",
  "landing.demo.low": "خطر منخفض",
  "landing.demo.confirm": "أكّد أولاً",
  "landing.demo.ship": "اشحنه",
  "landing.demo.after": "بعد ردّ واحد",
  "notfound.title": "هذه الصفحة غير موجودة",
  "notfound.body": "قد يكون الرابط قديماً أو تم حذف الطلب.",
  "notfound.back": "العودة إلى الطلبات",
  "waking.title": "واصل قيد التشغيل",
  "waking.body": "كان الخادم التجريبي المجاني نائماً. يستغرق ذلك نحو دقيقة ثم تُحمَّل الصفحة تلقائياً.",
  "retry": "إعادة المحاولة",
}

const DICT: Record<Lang, Record<Key, string>> = { en: EN, fr: FR, ar: AR }

type Ctx = { lang: Lang, setLang: (l: Lang) => void, t: (k: Key) => string }
const LangContext = createContext<Ctx>({ lang: "en", setLang: () => {}, t: (k) => EN[k] })

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en")

  useEffect(() => {
    let saved: string | null = null
    try { saved = localStorage.getItem(STORAGE_KEY) } catch { /* storage blocked */ }
    if (saved === "fr" || saved === "ar") setLangState(saved)
  }, [])

  useEffect(() => {
    document.documentElement.lang = lang
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr"
  }, [lang])

  const setLang = useCallback((l: Lang) => {
    setLangState(l)
    try { localStorage.setItem(STORAGE_KEY, l) } catch { /* ignore */ }
  }, [])

  const value = useMemo<Ctx>(() => ({ lang, setLang, t: (k) => DICT[lang][k] ?? EN[k] }), [lang, setLang])
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}

export const useT = () => useContext(LangContext)

/** Three-way language buttons. Each carries its own `lang` so a screen reader says the name in its language. */
export function LangSwitcher({ className = "" }: { className?: string }) {
  const { lang, setLang, t } = useT()
  return (
    <div role="group" aria-label={t("lang.label")} className={`inline-flex rounded-full border border-gray-200 bg-card p-0.5 shadow-xs ${className}`}>
      {LANGS.map(l => (
        <button key={l.code} type="button" lang={l.code} aria-pressed={lang === l.code} aria-label={l.name}
                onClick={() => setLang(l.code)}
                className={`min-h-[44px] min-w-[44px] px-3 rounded-full text-xs font-semibold transition-colors ${lang === l.code ? "bg-brand text-white" : "text-gray-600 hover:text-gray-900"}`}>
          {l.label}
        </button>
      ))}
    </div>
  )
}
