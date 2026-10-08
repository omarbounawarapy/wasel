"use client";

import Link from "next/link"
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
    ListChecks, MessageCircle, ClipboardPaste, LineChart, History, ShieldCheck, SearchCheck, Gauge, ScrollText,
} from "lucide-react";

// Grouped by what the seller is doing, in plain words. The order detail page is reached from a list.
export const NAV_GROUPS = [
    {
        title: "Daily work",
        items: [
            { icon: ListChecks, label: "Orders to check", path: "/dashboard" },
            { icon: MessageCircle, label: "WhatsApp messages", path: "/dashboard/inbox" },
            { icon: ClipboardPaste, label: "Add an order", path: "/dashboard/paste" },
        ],
    },
    {
        title: "Results",
        items: [
            { icon: LineChart, label: "Money saved", path: "/dashboard/impact" },
            { icon: History, label: "Activity log", path: "/dashboard/activity" },
        ],
    },
    {
        title: "AI health",
        items: [
            { icon: ShieldCheck, label: "Quality checks", path: "/dashboard/quality" },
            { icon: SearchCheck, label: "Silent failures", path: "/dashboard/failures" },
            { icon: Gauge, label: "Live monitor", path: "/dashboard/monitor" },
            { icon: ScrollText, label: "AI call log", path: "/dashboard/traces" },
        ],
    },
];

const norm = (p: string) => (p.length > 1 ? p.replace(/\/$/, "") : p);

export const Sidebar = () => {
    const pathname = norm(usePathname() || "");
    const isActive = (path: string) =>
        pathname === path || (path === "/dashboard" && pathname === "/dashboard/order");

    return (
        <aside className="w-[248px] flex flex-col h-full overflow-y-auto scrollbar-hide shrink-0">
            <Link prefetch={false} href="/dashboard" className="px-5 pt-7 pb-6 block" aria-label="Wasel home">
                <Image priority src="/wasel-logo-compact.png" alt="Wasel, COD order risk assessment" width={200} height={48} className="w-[200px] h-auto" />
            </Link>

            <nav className="px-4 pb-6 space-y-6" aria-label="Main">
                {NAV_GROUPS.map(group => (
                    <div key={group.title}>
                        <p className="px-3 mb-2 text-xs font-semibold text-gray-600 uppercase tracking-wider">{group.title}</p>
                        <ul className="flex flex-col gap-1">
                            {group.items.map(item => {
                                const active = isActive(item.path);
                                return (
                                    <li key={item.path}>
                                        <Link prefetch={false} href={item.path} aria-current={active ? "page" : undefined}
                                              className={`flex items-center gap-3 px-3 min-h-[44px] rounded-xl text-sm transition-colors focus-visible:outline-2 focus-visible:outline-brand ${active
                                                  ? "bg-white text-brand font-semibold shadow-sm"
                                                  : "text-gray-600 font-medium hover:text-brand-ink hover:bg-white/60"}`}>
                                            <item.icon className="w-5 h-5 shrink-0" strokeWidth={active ? 2.4 : 2} />
                                            <span>{item.label}</span>
                                        </Link>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                ))}
            </nav>
        </aside>
    );
};
