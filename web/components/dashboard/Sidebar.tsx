"use client";

import Link from "next/link"
import Image from "next/image";
import { usePathname } from "next/navigation";
import { LangSwitcher, useT } from "@/lib/i18n";

type NavKey = Parameters<ReturnType<typeof useT>["t"]>[0];
import {
    ListChecks, MessageCircle, ClipboardPaste, LineChart, History, ShieldCheck, SearchCheck, Gauge, ScrollText,
} from "lucide-react";

// Grouped by what the seller is doing, in plain words. `title` and `label` are keys of lib/i18n.tsx. The order detail page is reached from a list.
export const NAV_GROUPS: { title: NavKey, items: { icon: typeof ListChecks, label: NavKey, path: string }[] }[] = [
    {
        title: "nav.group.daily",
        items: [
            { icon: ListChecks, label: "nav.orders", path: "/dashboard" },
            { icon: MessageCircle, label: "nav.whatsapp", path: "/dashboard/inbox" },
            { icon: ClipboardPaste, label: "nav.add", path: "/dashboard/paste" },
        ],
    },
    {
        title: "nav.group.results",
        items: [
            { icon: LineChart, label: "nav.money", path: "/dashboard/impact" },
            { icon: History, label: "nav.activity", path: "/dashboard/activity" },
        ],
    },
    {
        title: "nav.group.health",
        items: [
            { icon: ShieldCheck, label: "nav.quality", path: "/dashboard/quality" },
            { icon: Gauge, label: "nav.monitor", path: "/dashboard/monitor" },
            { icon: ScrollText, label: "nav.calls", path: "/dashboard/traces" },
        ],
    },
    {
        // Analyst tool, not part of the seller's daily path or the demo walkthrough.
        title: "nav.group.advanced",
        items: [
            { icon: SearchCheck, label: "nav.failures", path: "/dashboard/failures" },
        ],
    },
];

const norm = (p: string) => (p.length > 1 ? p.replace(/\/$/, "") : p);

export const Sidebar = () => {
    const { t } = useT();
    const pathname = norm(usePathname() || "");
    const isActive = (path: string) =>
        pathname === path || (path === "/dashboard" && pathname === "/dashboard/order");

    return (
        <aside className="w-[248px] flex flex-col h-full overflow-y-auto scrollbar-hide shrink-0">
            <Link prefetch={false} href="/dashboard" className="px-7 pt-8 pb-8 block" aria-label={t("nav.home")}>
                <Image priority src="/wasel-logo-compact.png" alt="Wasel" width={200} height={48} className="logo-plate w-[136px] h-auto" />
            </Link>

            <nav className="px-4 pb-6 space-y-7" aria-label={t("nav.main")}>
                {NAV_GROUPS.map(group => (
                    <div key={group.title}>
                        <p className="px-3 mb-2 text-[11px] font-medium text-gray-500 uppercase tracking-[0.08em]">{t(group.title)}</p>
                        <ul className="flex flex-col gap-0.5">
                            {group.items.map(item => {
                                const active = isActive(item.path);
                                return (
                                    <li key={item.path}>
                                        <Link prefetch={false} href={item.path} aria-current={active ? "page" : undefined}
                                              className={`group flex items-center gap-3 px-3 min-h-[44px] rounded-xl text-[14px] transition-colors focus-visible:outline-2 focus-visible:outline-brand ${active
                                                  ? "bg-card text-brand-ink font-semibold shadow-xs ring-1 ring-border"
                                                  : "text-gray-700 font-medium hover:text-gray-900 hover:bg-white/60"}`}>
                                            <item.icon className={`w-[18px] h-[18px] shrink-0 ${active ? "text-brand" : "text-gray-500 group-hover:text-gray-700"}`} strokeWidth={active ? 2.2 : 1.8} aria-hidden="true" />
                                            <span>{t(item.label)}</span>
                                        </Link>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                ))}
            </nav>
            <div className="px-6 pb-7 mt-auto"><LangSwitcher /></div>
        </aside>
    );
};
