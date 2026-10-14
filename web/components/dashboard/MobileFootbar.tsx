"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ListChecks, MessageCircle, ClipboardPaste, LineChart, MoreHorizontal } from "lucide-react";
import { NAV_GROUPS } from "@/components/dashboard/Sidebar";
import { useT } from "@/lib/i18n";

// Phone-width navigation: the four daily destinations plus "More".
// "More" lists every desktop sidebar page that is not already in the bar, with the sidebar's own names.
const ITEMS: { icon: typeof ListChecks, label: Parameters<ReturnType<typeof useT>["t"]>[0], path: string }[] = [
    { icon: ListChecks, label: "nav.bar.orders", path: "/dashboard" },
    { icon: MessageCircle, label: "nav.bar.whatsapp", path: "/dashboard/inbox" },
    { icon: ClipboardPaste, label: "nav.bar.add", path: "/dashboard/paste" },
    { icon: LineChart, label: "nav.bar.money", path: "/dashboard/impact" },
];

const BAR_PATHS = new Set(ITEMS.map(i => i.path));
const MORE_ITEMS = NAV_GROUPS.flatMap(g => g.items).filter(i => !BAR_PATHS.has(i.path));

export function MobileFootbar() {
    const { t } = useT();
    const pathname = (usePathname() || "").replace(/\/$/, "") || "/";
    const [open, setOpen] = useState(false);

    const moreActive = MORE_ITEMS.some(m => pathname === m.path);

    // Close the menu after navigating.
    useEffect(() => { setOpen(false); }, [pathname]);

    // Close the menu with the Escape key.
    useEffect(() => {
        if (!open) return;
        const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
        window.addEventListener("keydown", onKey);
        return () => window.removeEventListener("keydown", onKey);
    }, [open]);

    const itemClass = (active: boolean) =>
        `flex flex-col items-center justify-center gap-0.5 min-h-[56px] w-full text-xs font-medium whitespace-nowrap ${active ? "text-brand" : "text-gray-600"}`;

    return (
        <>
        {/* The one primary action, always in reach on the queue. Not shown on the Add an order page itself. */}
        {pathname === "/dashboard" && (
            <Link prefetch={false} href="/dashboard/paste"
                  className="lg:hidden fixed bottom-[88px] end-3 start-3 sm:start-auto z-40 inline-flex items-center justify-center gap-2 px-5 min-h-[48px] rounded-2xl bg-brand hover:bg-brand-hover text-white text-sm font-semibold shadow-lg">
                <ClipboardPaste className="w-5 h-5" aria-hidden="true" /> {t("cta.add")}
            </Link>
        )}
        <nav aria-label={t("nav.main")} className="lg:hidden fixed bottom-3 start-3 end-3 z-50 bg-white rounded-2xl border border-gray-200 shadow-lg">
            {open && (
                <>
                    {/* Tap outside to close */}
                    <button type="button" aria-label="Close menu" onClick={() => setOpen(false)}
                            className="fixed inset-0 -z-10 cursor-default" />
                    <ul className="absolute bottom-full end-0 mb-2 w-60 bg-white rounded-2xl border border-gray-200 shadow-lg p-1">
                        {MORE_ITEMS.map(m => {
                            const active = pathname === m.path;
                            return (
                                <li key={m.path}>
                                    <Link prefetch={false} href={m.path} aria-current={active ? "page" : undefined}
                                          className={`flex items-center gap-3 px-3 min-h-[44px] rounded-xl text-sm ${active ? "text-brand font-semibold bg-gray-50" : "text-gray-700 font-medium"}`}>
                                        <m.icon className="w-5 h-5 shrink-0" strokeWidth={active ? 2.4 : 2} />
                                        <span>{t(m.label)}</span>
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </>
            )}
            <ul className="grid grid-cols-5">
                {ITEMS.map(item => {
                    const active = pathname === item.path || (item.path === "/dashboard" && pathname === "/dashboard/order");
                    return (
                        <li key={item.path}>
                            <Link prefetch={false} href={item.path} aria-current={active ? "page" : undefined} className={itemClass(active)}>
                                <item.icon className="w-5 h-5" strokeWidth={active ? 2.4 : 2} />
                                {t(item.label)}
                            </Link>
                        </li>
                    );
                })}
                <li>
                    <button type="button" onClick={() => setOpen(o => !o)}
                            aria-expanded={open} aria-haspopup="true"
                            className={itemClass(open || moreActive)}>
                        <MoreHorizontal className="w-5 h-5" strokeWidth={open || moreActive ? 2.4 : 2} />
                        {t("nav.bar.more")}
                    </button>
                </li>
            </ul>
        </nav>
        </>
    );
}
