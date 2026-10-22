"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ordersApi } from "@/lib/api/orders";
import type { HealthResponse, OrderListResponse, OrderSummary } from "@/lib/api/types";
import { Page, PageHeader, Guide, Section, StatCard, ReadBy, RiskBadge, Empty, LoadError, STATUS, whenLabel } from "@/components/wasel/kit";
import { messageLang } from "@/lib/utils";

export default function InboxPage() {
    const router = useRouter();
    const [data, setData] = useState<OrderListResponse | null>(null);
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        const load = () => ordersApi.getOrders({ include_collecting: true })
            .then(res => { setData(res); setError(false); })
            .catch(() => setError(true));
        load();
        ordersApi.health().then(setHealth).catch(() => {});
        const interval = setInterval(load, 3000);
        return () => clearInterval(interval);
    }, []);

    const rows = (data?.orders || [])
        .filter((r: OrderSummary) => r.channel === "whatsapp")
        .sort((a: OrderSummary, b: OrderSummary) => b.updated_at.localeCompare(a.updated_at));
    const count = (s: string) => rows.filter((r: OrderSummary) => r.status === s).length;
    const connected = health?.webhook === "enabled";
    // Public demo without WhatsApp: nothing will ever arrive here, so explain the page instead of showing zeros.
    const publicDemo = health?.mode === "public" && !connected && rows.length === 0;

    return (
        <Page>
            <PageHeader
                title="WhatsApp messages"
                subtitle="Customer messages from your WhatsApp number, scored within seconds." />

            <Guide id="inbox" steps={[
                "A customer writes to your WhatsApp business number.",
                "Wasel reads it: if it's an order, it gets a risk score. A plain “hello” waits until they give details.",
                "Click a conversation to see the score and the suggested reply.",
            ]} />

            {health && !connected && (
                <p role="status" className="rounded-2xl border border-amber-200 bg-amber-50 text-amber-900 text-sm p-4">
                    WhatsApp is not connected on this server (demo mode), so no real messages will arrive. Use “Add an order” to try Wasel with a pasted message.
                </p>
            )}
            {error && <LoadError what="the WhatsApp messages" />}

            {publicDemo ? (
                <Section title="What arrives here on a live server">
                    <p className="text-sm text-gray-700 max-w-prose">
                        Each WhatsApp message a customer sends to your business number lands on this page within seconds, already scored.
                        The public demo has no WhatsApp number connected, so nothing arrives here.
                    </p>
                    <button type="button" onClick={() => router.push("/dashboard/paste")}
                            className="mt-4 min-h-[44px] px-4 rounded-xl bg-brand text-white text-sm font-semibold hover:bg-brand-hover">
                        Try it with a pasted message
                    </button>
                </Section>
            ) : (<>
            <div className="grid grid-cols-3 gap-2 sm:gap-4">
                <StatCard label="Conversations" value={data ? rows.length : "–"} hint="From WhatsApp" />
                <StatCard label="Needs your decision" value={data ? count("needs_review") : "–"} tone={count("needs_review") ? "warn" : "default"} hint="Open them first" />
                <StatCard label="Waiting for customer" value={data ? count("awaiting_reply") : "–"} hint="A question was sent" />
            </div>

            <section aria-label="WhatsApp conversations" className="bg-white rounded-2xl border border-gray-200/70 shadow-sm overflow-hidden">
                {!data && !error ? (
                    <p className="p-5 text-sm text-gray-600">Loading…</p>
                ) : rows.length === 0 ? (
                    <Empty title="No WhatsApp messages yet">
                        {connected ? "Send a message to your WhatsApp business number: it will appear here within a few seconds." : "Messages appear here once WhatsApp is connected."}
                    </Empty>
                ) : (
                    <ul className="divide-y divide-gray-100">
                        {rows.map((o: OrderSummary) => (
                            <li key={o.order_id}>
                                <button type="button" onClick={() => router.push(`/dashboard/order?id=${o.order_id}`)}
                                        className="w-full text-start flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4 px-5 py-3.5 hover:bg-gray-50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand">
                                    <span className="sm:w-[190px] shrink-0 min-w-0">
                                        <bdi className="block font-semibold text-brand-ink truncate">{o.customer.display_name || o.customer.phone_masked || "Unknown"}</bdi>
                                        <span className="block text-xs text-gray-600 tabular-nums">{o.order_ref} · {whenLabel(o.updated_at)}</span>
                                    </span>
                                    <bdi dir="auto" lang={messageLang(o.last_message_preview)} className="flex-1 min-w-0 text-sm text-gray-700 truncate">{o.last_message_preview || ""}</bdi>
                                    <span className="flex items-center gap-3 shrink-0">
                                        {o.score ? <><ReadBy value={o.score.read_by} /><RiskBadge tier={o.score.tier} score={o.score.final_score} /></>
                                            : o.rescore_state !== "idle" ? <RiskBadge tier={null} score={null} />
                                            : <span className="text-xs font-medium text-gray-600 border border-gray-300 rounded-full px-2.5 py-0.5"
                                                    title="No product or delivery address in these messages yet, so there is nothing to score. Wasel rescores as soon as the customer sends order details.">
                                                Not an order yet
                                            </span>}
                                        <span className="text-xs text-gray-600 w-[140px] hidden md:inline">{o.score ? STATUS[o.status] : ""}</span>
                                    </span>
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </section>
            </>)}
        </Page>
    );
}
