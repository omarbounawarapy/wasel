"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageCircle } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import {
    Page, PageHeader, Guide, StatCard, ReadBy, RiskBadge, Delta, Empty, LoadError, Chip,
    TIER, NEXT_STEP, STATUS, tnd,
} from "@/components/wasel/kit";

type Filter = "all" | "needs_review" | "awaiting_reply" | "ready_to_ship";

const FILTERS: { key: Exclude<Filter, "all">, label: string, hint: string }[] = [
    { key: "needs_review", label: "Needs your decision", hint: "Wasel is unsure: you decide" },
    { key: "awaiting_reply", label: "Waiting for customer", hint: "A question was sent" },
    { key: "ready_to_ship", label: "Ready to ship", hint: "Confirmed or low risk" },
];

export default function QueueDashboard() {
    const router = useRouter();
    const [queueData, setQueueData] = useState<any>(null);
    const [error, setError] = useState(false);
    const [filter, setFilter] = useState<Filter>("all");

    useEffect(() => {
        const load = () => ordersApi.getOrders({ include_collecting: true })
            .then(res => { setQueueData(res); setError(false); })
            .catch(() => setError(true));
        load();
        const interval = setInterval(load, 3000);
        return () => clearInterval(interval);
    }, []);

    const open = (orderId: string) => router.push(`/dashboard/order?id=${orderId}`);

    const counts = queueData?.counts || {};
    // Messages still being scored come first as "Scoring…"; conversations the AI found
    // not to be orders (collecting + idle, e.g. a lone "salam") stay out of the list.
    const all: any[] = queueData?.orders || [];
    const scoring = all.filter(o => o.status === "collecting" && o.rescore_state !== "idle");
    const notOrders = all.filter(o => o.status === "collecting" && o.rescore_state === "idle");
    const scored = all.filter(o => o.status !== "collecting");
    const rows = filter === "all" ? [...scoring, ...scored] : scored.filter(o => o.status === filter);

    return (
        <Page wide>
            <PageHeader
                title="Orders to check"
                subtitle="Wasel reads what each customer wrote and scores how likely the order is to be refused at the door. Riskiest orders are at the top." />

            <Guide id="queue" steps={[
                "A customer message arrives on WhatsApp, or you paste it in.",
                "Wasel scores the refusal risk and explains why, in the customer's own words.",
                "Open an order to confirm with the customer, then ship it.",
            ]} />

            {error && <LoadError what="the orders" />}

            <div className="grid grid-cols-3 gap-2 sm:gap-4">
                {FILTERS.map(f => (
                    <StatCard key={f.key} label={f.label} hint={f.hint} value={counts[f.key] ?? 0}
                              tone={f.key === "needs_review" && counts[f.key] ? "warn" : "default"}
                              onClick={() => setFilter(filter === f.key ? "all" : f.key)} />
                ))}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-gray-600" aria-label="Risk levels">
                    {(["high", "medium", "low"] as const).map(t => (
                        <span key={t} className="flex items-center gap-1.5">
                            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 font-bold ${TIER[t].cls}`}>
                                <span aria-hidden="true">{TIER[t].shape}</span>{TIER[t].label}
                            </span>
                            <span className="tabular-nums font-semibold text-gray-800">{counts[t] ?? 0}</span>
                            <span className="hidden xl:inline">· {TIER[t].meaning}</span>
                        </span>
                    ))}
                </div>
                {filter !== "all" && (
                    <button type="button" onClick={() => setFilter("all")}
                            className="text-sm font-medium text-brand hover:underline min-h-[36px]">
                        Show all orders
                    </button>
                )}
            </div>

            {notOrders.length > 0 && (
                <p className="text-xs text-gray-600">
                    {notOrders.length} conversation{notOrders.length > 1 ? "s are" : " is"} not an order yet (no product or address in the messages):{" "}
                    {notOrders.map((o, i) => (
                        <span key={o.order_id}>
                            {i > 0 && ", "}
                            <button type="button" className="underline hover:text-brand" onClick={() => open(o.order_id)}>
                                {o.order_ref} <bdi>{o.customer?.display_name || ""}</bdi>
                            </button>
                        </span>
                    ))}
                </p>
            )}

            <section aria-label="Orders by risk" className="bg-white rounded-2xl border border-gray-200/70 shadow-sm overflow-hidden">
                <div className="hidden md:grid grid-cols-[minmax(0,1.3fr)_auto_minmax(0,1fr)_minmax(0,0.9fr)_minmax(0,1.6fr)] gap-4 px-5 py-3 bg-brand-soft text-[11px] font-bold uppercase tracking-wider text-brand">
                    <span>Order</span><span className="w-[120px]">Risk</span><span>Next step</span><span>Status</span><span>Why</span>
                </div>
                {!queueData && !error ? (
                    <div className="divide-y divide-gray-100" aria-busy="true">
                        {[0, 1, 2, 3, 4].map(i => <div key={i} className="h-16 px-5 py-3"><div className="h-4 w-2/3 bg-gray-100 rounded animate-pulse" /></div>)}
                    </div>
                ) : rows.length === 0 ? (
                    <Empty title={filter === "all" ? "No orders yet" : "Nothing here right now"}>
                        {filter === "all" ? "New WhatsApp messages appear here automatically. You can also add one from “Add an order”." : "Pick another card above, or show all orders."}
                    </Empty>
                ) : (
                    <ul className="divide-y divide-gray-100">
                        {rows.map((o: any) => (
                            <li key={o.order_id}>
                                <button type="button" onClick={() => open(o.order_id)}
                                        className="w-full text-left grid grid-cols-1 md:grid-cols-[minmax(0,1.3fr)_auto_minmax(0,1fr)_minmax(0,0.9fr)_minmax(0,1.6fr)] gap-x-4 gap-y-1.5 items-center px-5 py-3.5 hover:bg-gray-50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand">
                                    <span className="min-w-0">
                                        <span className="flex items-center gap-2 min-w-0">
                                            <span className="font-semibold text-brand-ink tabular-nums">{o.order_ref}</span>
                                            <bdi className="truncate text-gray-700">{o.customer?.display_name || "Unnamed"}</bdi>
                                            {o.channel === "whatsapp" && <MessageCircle className="w-3.5 h-3.5 text-emerald-600 shrink-0" aria-label="WhatsApp" />}
                                            {o.is_seeded && o.seed_key && <Chip>Sample</Chip>}
                                        </span>
                                        <span className="block text-xs text-gray-500 truncate">
                                            {[o.product_name, o.price_tnd != null ? tnd(o.price_tnd) : null].filter(Boolean).join(" · ") || "Details not given yet"}
                                        </span>
                                    </span>
                                    <span className="flex items-center gap-1.5 md:w-[120px]">
                                        <RiskBadge tier={o.score?.tier} score={o.score?.final_score} />
                                        <Delta delta={o.score?.delta} />
                                        <ReadBy value={o.score?.read_by} />
                                    </span>
                                    <span className="text-sm font-medium text-gray-800">{o.score ? NEXT_STEP[o.score.action] ?? o.score.action : "–"}</span>
                                    <span className="text-sm text-gray-600">{STATUS[o.status] ?? o.status}</span>
                                    <span className="text-xs text-gray-500 truncate" title={o.score?.reason_short || ""}>
                                        {/* the reason without the tier prefix and the internal point values */}
                                        {(o.score?.reason_short || "").replace(/^(HIGH|MEDIUM|LOW) \d+ · /, "").replace(/ [+−-]\d+(?= ·|$)/g, "")}
                                    </span>
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
        </Page>
    );
}
