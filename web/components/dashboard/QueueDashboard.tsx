"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { MessageCircle, X } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import type { Counts, OrderListResponse, OrderSummary } from "@/lib/api/types";
import {
    Page, PageHeader, Guide, StatCard, ReadBy, RiskBadge, Delta, Empty, LoadError, Chip,
    TIER, NEXT_STEP, STATUS, tnd,
} from "@/components/wasel/kit";

type Filter = "all" | "needs_review" | "awaiting_reply" | "ready_to_ship";

const FILTERS: { key: Exclude<Filter, "all">, label: string }[] = [
    { key: "needs_review", label: "Needs your decision" },
    { key: "awaiting_reply", label: "Waiting for customer" },
    { key: "ready_to_ship", label: "Ready to ship" },
];

// One column grid for the header and every row
const COLS = "md:grid-cols-[minmax(0,1.25fr)_8.5rem_minmax(0,1.15fr)_minmax(0,0.9fr)_minmax(0,1.4fr)]";

export default function QueueDashboard() {
    const router = useRouter();
    const [queueData, setQueueData] = useState<OrderListResponse | null>(null);
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

    const counts: Partial<Counts> = queueData?.counts || {};
    // Messages still being scored come first as "Scoring…"; conversations the AI found
    // not to be orders (collecting + idle, e.g. a lone "salam") stay out of the list.
    const all: OrderSummary[] = queueData?.orders || [];
    const scoring = all.filter(o => o.status === "collecting" && o.rescore_state !== "idle");
    const notOrders = all.filter(o => o.status === "collecting" && o.rescore_state === "idle");
    const scored = all.filter(o => o.status !== "collecting");
    const rows = filter === "all" ? [...scoring, ...scored] : scored.filter(o => o.status === filter);

    return (
        <Page>
            <PageHeader title="Orders to check" subtitle="Every order scored for refusal risk, riskiest first." />

            <Guide id="queue" steps={[
                "A customer message arrives on WhatsApp, or you paste it in.",
                "Wasel scores the refusal risk and explains why, in the customer's own words.",
                "Open an order to confirm with the customer, then ship it.",
            ]} />

            {error && <LoadError what="the orders" />}

            <div className="grid grid-cols-3 gap-2 sm:gap-4">
                {FILTERS.map(f => (
                    <StatCard key={f.key} label={f.label} value={queueData ? counts[f.key] ?? 0 : "–"}
                              tone={f.key === "needs_review" && counts[f.key] ? "warn" : "default"}
                              active={filter === f.key}
                              onClick={() => setFilter(filter === f.key ? "all" : f.key)} />
                ))}
            </div>

            <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
                    <div className="flex items-center gap-2 min-h-[44px]">
                        <h2 className="text-[11px] font-medium uppercase tracking-[0.06em] text-gray-600">
                            {filter === "all" ? "All orders" : FILTERS.find(f => f.key === filter)?.label}
                        </h2>
                        {filter !== "all" && (
                            <button type="button" onClick={() => setFilter("all")}
                                    className="group inline-flex items-center min-h-[44px] px-1">
                                <span className="inline-flex items-center gap-1 h-7 px-2.5 rounded-full bg-gray-100 text-xs font-medium text-gray-700 group-hover:text-gray-900">
                                    <X className="w-3 h-3" aria-hidden="true" /> Show all
                                </span>
                            </button>
                        )}
                    </div>
                    {/* The tier meanings are one hover away; the counts are the point here */}
                    <div role="group" aria-label="Risk levels" className="flex flex-wrap items-center gap-2">
                        {(["high", "medium", "low"] as const).map(t => (
                            <span key={t} title={TIER[t].meaning}
                                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${TIER[t].cls}`}>
                                <span aria-hidden="true" className={`${TIER[t].dot} text-[0.75em]`}>{TIER[t].shape}</span>
                                {TIER[t].label}
                                <span className="tabular-nums font-medium">{queueData ? counts[t] ?? 0 : "–"}</span>
                            </span>
                        ))}
                    </div>
                </div>

                <section aria-label="Orders by risk" className="bg-card rounded-2xl border border-border shadow-sm overflow-hidden">
                    <div className={`hidden md:grid ${COLS} gap-6 px-6 py-3.5 border-b border-border text-[11px] font-medium uppercase tracking-[0.06em] text-gray-600`}>
                        <span>Order</span><span>Risk</span><span>Next step</span><span>Status</span><span>Why</span>
                    </div>
                    {!queueData && !error ? (
                        <div className="divide-y divide-gray-100" aria-busy="true">
                            {[0, 1, 2, 3, 4].map(i => (
                                <div key={i} className="h-[72px] px-6 py-4 space-y-2">
                                    <div className="h-3.5 w-1/3 bg-gray-100 rounded-full animate-pulse motion-reduce:animate-none" />
                                    <div className="h-3 w-1/5 bg-gray-100 rounded-full animate-pulse motion-reduce:animate-none" />
                                </div>
                            ))}
                        </div>
                    ) : rows.length === 0 ? (
                        <Empty title={filter === "all" ? "No orders yet" : "Nothing here right now"}>
                            {filter === "all" ? "New WhatsApp messages appear here automatically. You can also add one from “Add an order”." : "Pick another card above, or show all orders."}
                        </Empty>
                    ) : (
                        <ul className="divide-y divide-gray-100">
                            {rows.map((o: OrderSummary) => (
                                <li key={o.order_id}>
                                    <button type="button" onClick={() => open(o.order_id)}
                                            className={`w-full text-start grid grid-cols-1 ${COLS} gap-x-6 gap-y-2 items-center px-5 md:px-6 py-4 transition-colors hover:bg-gray-50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand`}>
                                        <span className="min-w-0">
                                            <span className="flex items-center gap-2 min-w-0">
                                                <span className="font-semibold text-brand-ink tabular-nums">{o.order_ref}</span>
                                                <bdi className="truncate text-gray-700">{o.customer?.display_name || "Unnamed"}</bdi>
                                                {o.channel === "whatsapp" && <MessageCircle className="w-3.5 h-3.5 text-emerald-600 shrink-0" aria-label="WhatsApp" />}
                                                {o.is_seeded && o.seed_key && <Chip>Example</Chip>}
                                            </span>
                                            <span className="block mt-0.5 text-[13px] text-gray-600 truncate">
                                                {[o.product_name, o.price_tnd != null ? tnd(o.price_tnd) : null].filter(Boolean).join(" · ") || "Details not given yet"}
                                            </span>
                                        </span>
                                        <span className="flex flex-wrap items-center gap-1.5">
                                            <RiskBadge tier={o.score?.tier} score={o.score?.final_score} />
                                            <Delta delta={o.score?.delta} />
                                            <ReadBy value={o.score?.read_by} />
                                        </span>
                                        <span className="text-sm font-medium text-gray-900">{o.score ? NEXT_STEP[o.score.action] ?? o.score.action : "–"}</span>
                                        <span className="text-sm text-gray-600">{STATUS[o.status] ?? o.status}</span>
                                        <span className="text-[13px] text-gray-600 truncate" title={o.score?.reason_short || ""}>
                                            {/* the reason without the tier prefix and the internal point values */}
                                            {(o.score?.reason_short || "").replace(/^(HIGH|MEDIUM|LOW) \d+ · /, "").replace(/ [+−-]\d+(?= ·|$)/g, "")}
                                        </span>
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
                </section>

                {notOrders.length > 0 && (
                    <p className="text-[13px] text-gray-600" title="No product or address in the messages yet">
                        Not orders yet:{" "}
                        {notOrders.map((o, i) => (
                            <span key={o.order_id}>
                                {i > 0 && ", "}
                                <button type="button" className="underline underline-offset-2 hover:text-brand" onClick={() => open(o.order_id)}>
                                    {o.order_ref} <bdi>{o.customer?.display_name || ""}</bdi>
                                </button>
                            </span>
                        ))}
                    </p>
                )}
            </div>
        </Page>
    );
}
