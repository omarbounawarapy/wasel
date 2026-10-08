"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Info, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, StatCard, Empty, LoadError, tunisTime } from "@/components/wasel/kit";

// the server titles seller actions as "Order <action>": say them in plain words
const ACTION_TITLE: Record<string, string> = {
    approve: "Approved for shipping", request_confirmation: "Asked the customer to confirm", ship: "Marked as shipped",
    mark_delivered: "Marked as delivered", mark_refused: "Refused at the door", cancel: "Order cancelled",
};
const plainTitle = (t: string) => {
    const m = /^Order (\w+)$/.exec(t || "");
    return m && ACTION_TITLE[m[1]] ? ACTION_TITLE[m[1]] : t;
};

const LEVEL: Record<string, { icon: typeof Info, cls: string, label: string }> = {
    info: { icon: Info, cls: "text-gray-600", label: "Info" },
    success: { icon: CheckCircle2, cls: "text-emerald-600", label: "Done" },
    warning: { icon: AlertTriangle, cls: "text-amber-600", label: "Warning" },
    error: { icon: XCircle, cls: "text-red-600", label: "Error" },
};

export default function ActivityPage() {
    const router = useRouter();
    const [events, setEvents] = useState<any[] | null>(null);
    const [error, setError] = useState(false);
    const [onlyWarnings, setOnlyWarnings] = useState(false);

    useEffect(() => {
        const load = async () => {
            try {
                // the API pages forward from `after`: walk to the end, keep the newest 300
                let after = 0, out: any[] = [];
                for (let i = 0; i < 10; i++) {
                    const page = await ordersApi.getEvents({ after, limit: 200 });
                    out = out.concat(page.events || []);
                    if ((page.events || []).length < 200) break;
                    after = page.last_seq;
                }
                setEvents(out.slice(-300).reverse());
                setError(false);
            } catch { setError(true); }
        };
        load();
        const iv = setInterval(load, 5000);
        return () => clearInterval(iv);
    }, []);

    const list = events || [];
    const count = (types: string[]) => list.filter(x => types.includes(x.type)).length;
    const shown = onlyWarnings ? list.filter(e => e.level === "warning" || e.level === "error") : list;

    return (
        <Page>
            <PageHeader
                title="Activity log"
                subtitle="Everything Wasel did, newest first: messages received, scores, drafted replies and anything that needed attention." />

            {error && <LoadError what="the activity log" />}

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard label="Messages received" value={count(["message.received"])} />
                <StatCard label="Orders scored" value={count(["order.rescored"])} />
                <StatCard label="Replies drafted" value={count(["draft.created"])} />
                <StatCard label="Tricks blocked" value={count(["injection.suspected"])} hint="Messages trying to fool the AI"
                          tone={count(["injection.suspected"]) ? "warn" : "default"} />
            </div>

            <section aria-label="Events" className="bg-white rounded-2xl border border-gray-200/70 shadow-sm overflow-hidden">
                <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-gray-100">
                    <p className="text-sm font-semibold text-brand-ink">{shown.length} events</p>
                    <label className="flex items-center gap-2 text-sm text-gray-700 min-h-[44px] cursor-pointer">
                        <input type="checkbox" checked={onlyWarnings} onChange={e => setOnlyWarnings(e.target.checked)} className="w-4 h-4 accent-brand" />
                        Only warnings
                    </label>
                </div>
                {events === null && !error ? (
                    <p className="p-5 text-sm text-gray-600">Loading…</p>
                ) : shown.length === 0 ? (
                    <Empty title={onlyWarnings ? "No warnings" : "Nothing has happened yet"} />
                ) : (
                    <ul className="divide-y divide-gray-100">
                        {shown.map(ev => {
                            const lvl = LEVEL[ev.level] ?? LEVEL.info;
                            const Icon = lvl.icon;
                            return (
                                <li key={ev.seq} className="flex items-start gap-3 px-5 py-3">
                                    <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${lvl.cls}`} aria-label={lvl.label} />
                                    <span className="w-12 shrink-0 text-xs text-gray-600 tabular-nums mt-0.5">{tunisTime(ev.ts)}</span>
                                    <span className="flex-1 min-w-0">
                                        <span className="block text-sm text-gray-900" title={ev.type}>{plainTitle(ev.title)}</span>
                                        {ev.detail && <span className="block text-xs text-gray-600 break-words">{ev.detail}</span>}
                                    </span>
                                    {ev.order_ref && ev.order_id && (
                                        <button type="button" onClick={() => router.push(`/dashboard/order?id=${ev.order_id}`)}
                                                className="shrink-0 text-xs font-semibold text-brand hover:underline tabular-nums min-h-[44px] min-w-[44px]">
                                            {ev.order_ref}
                                        </button>
                                    )}
                                </li>
                            );
                        })}
                    </ul>
                )}
            </section>
        </Page>
    );
}
