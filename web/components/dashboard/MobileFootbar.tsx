"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ListChecks, MessageCircle, ClipboardPaste, LineChart } from "lucide-react";

// Phone-width navigation: the four daily destinations (the full list lives in the desktop sidebar).
const ITEMS = [
    { icon: ListChecks, label: "Orders", path: "/dashboard" },
    { icon: MessageCircle, label: "WhatsApp", path: "/dashboard/inbox" },
    { icon: ClipboardPaste, label: "Add", path: "/dashboard/paste" },
    { icon: LineChart, label: "Saved", path: "/dashboard/impact" },
];

export function MobileFootbar() {
    const pathname = (usePathname() || "").replace(/\/$/, "") || "/";
    return (
        <nav aria-label="Main" className="lg:hidden fixed bottom-3 left-3 right-3 z-50 bg-white rounded-2xl border border-gray-200 shadow-lg">
            <ul className="grid grid-cols-4">
                {ITEMS.map(item => {
                    const active = pathname === item.path || (item.path === "/dashboard" && pathname === "/dashboard/order");
                    return (
                        <li key={item.path}>
                            <Link prefetch={false} href={item.path} aria-current={active ? "page" : undefined}
                                  className={`flex flex-col items-center justify-center gap-0.5 min-h-[56px] text-[11px] font-medium ${active ? "text-brand" : "text-gray-500"}`}>
                                <item.icon className="w-5 h-5" strokeWidth={active ? 2.4 : 2} />
                                {item.label}
                            </Link>
                        </li>
                    );
                })}
            </ul>
        </nav>
    );
}
