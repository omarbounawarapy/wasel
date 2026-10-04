"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ListChecks, MessageCircle, ClipboardPaste, LineChart, MoreHorizontal } from "lucide-react";
import { NAV_GROUPS } from "@/components/dashboard/Sidebar";

// Phone-width navigation: the four daily destinations plus "More".
// "More" lists every desktop sidebar page that is not already in the bar, with the sidebar's own names.
const ITEMS = [
    { icon: ListChecks, label: "Orders", path: "/dashboard" },
    { icon: MessageCircle, label: "WhatsApp", path: "/dashboard/inbox" },
    { icon: ClipboardPaste, label: "Add", path: "/dashboard/paste" },
    { icon: LineChart, label: "Money saved", path: "/dashboard/impact" },
];

const BAR_PATHS = new Set(ITEMS.map(i => i.path));
const MORE_ITEMS = NAV_GROUPS.flatMap(g => g.items).filter(i => !BAR_PATHS.has(i.path));

export function MobileFootbar() {
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
        `flex flex-col items-center justify-center gap-0.5 min-h-[56px] w-full text-[11px] font-medium whitespace-nowrap ${active ? "text-brand" : "text-gray-500"}`;

    return (
        <nav aria-label="Main" className="lg:hidden fixed bottom-3 left-3 right-3 z-50 bg-white rounded-2xl border border-gray-200 shadow-lg">
            {open && (
                <>
                    {/* Tap outside to close */}
                    <button type="button" aria-label="Close menu" onClick={() => setOpen(false)}
                            className="fixed inset-0 -z-10 cursor-default" />
                    <ul className="absolute bottom-full right-0 mb-2 w-60 bg-white rounded-2xl border border-gray-200 shadow-lg p-1">
                        {MORE_ITEMS.map(m => {
                            const active = pathname === m.path;
                            return (
                                <li key={m.path}>
                                    <Link prefetch={false} href={m.path} aria-current={active ? "page" : undefined}
                                          className={`flex items-center gap-3 px-3 min-h-[44px] rounded-xl text-sm ${active ? "text-brand font-semibold bg-gray-50" : "text-gray-700 font-medium"}`}>
                                        <m.icon className="w-5 h-5 shrink-0" strokeWidth={active ? 2.4 : 2} />
                                        <span>{m.label}</span>
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
                                {item.label}
                            </Link>
                        </li>
                    );
                })}
                <li>
                    <button type="button" onClick={() => setOpen(o => !o)}
                            aria-expanded={open} aria-haspopup="true"
                            className={itemClass(open || moreActive)}>
                        <MoreHorizontal className="w-5 h-5" strokeWidth={open || moreActive ? 2.4 : 2} />
                        More
                    </button>
                </li>
            </ul>
        </nav>
    );
}
