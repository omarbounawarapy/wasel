"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, StatCard, Chip, Empty, LoadError, tunisTime } from "@/components/wasel/kit";

const ROLE: Record<string, string> = { extract: "Read a message", judge: "Checked a reply", rewrite: "Wrote a reply", failure_label: "Labelled a failure" };
const ROLES = [["", "All calls"], ["extract", "Reading messages"], ["judge", "Checking replies"], ["rewrite", "Writing replies"]];

export default function TracesPage() {
    const router = useRouter();
    const [traces, setTraces] = useState<any[] | null>(null);
    const [error, setError] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [role, setRole] = useState("");

    const load = () => {
        setRefreshing(true);
        ordersApi.getTraces({ limit: 100, ...(role ? { role } : {}) })
            .then(res => { setTraces(res?.traces || []); setError(false); })
            .catch(() => setError(true))
            .finally(() => setRefreshing(false));
    };
    useEffect(() => { load(); }, [role]);

    const list = traces || [];
    const live = list.filter(t => !t.cache_hit);
    const avg = live.length ? live.reduce((s, t) => s + (t.latency_ms || 0), 0) / live.length : 0;
    const fallbacks = list.filter(t => (t.attempts || []).length > 1).length;

    return (
        <Page>
            <PageHeader
                title="AI call log"
                subtitle="Every request Wasel made to an AI model: what it was for, which model answered and how long it took. Customer text is never stored here."
                actions={
                    <>
                        <label className="sr-only" htmlFor="role">Show</label>
                        <select id="role" value={role} onChange={e => setRole(e.target.value)}
                                className="px-3 min-h-[44px] rounded-xl bg-white border border-gray-300 text-sm">
                            {ROLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                        </select>
                        <button type="button" onClick={load} disabled={refreshing}
                                className="inline-flex items-center gap-2 px-3 min-h-[44px] rounded-xl bg-white border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
                            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin motion-reduce:animate-none" : ""}`} /> Refresh
                        </button>
                    </>
                } />

            {error && <LoadError what="the AI call log" />}

            <div className="grid grid-cols-3 gap-2 sm:gap-4">
                <StatCard label="AI calls" value={list.length} hint="Since the server started" />
                <StatCard label="Typical answer time" value={live.length ? `${(avg / 1000).toFixed(1)} s` : "–"} />
                <StatCard label="Backup model used" value={fallbacks} tone={fallbacks ? "warn" : "default"} hint="The main model was busy or failed" />
            </div>

            <section aria-label="AI calls" className="bg-white rounded-2xl border border-gray-200/70 shadow-sm overflow-hidden">
                {traces === null && !error ? <p className="p-5 text-sm text-gray-600">Loading…</p>
                    : list.length === 0 ? <Empty title="No AI calls yet">They appear here as soon as a new message is scored with the AI.</Empty>
                    : (
                        <ul className="divide-y divide-gray-100">
                            {list.map(t => (
                                <li key={t.trace_id ?? t.ts}>
                                    <button type="button" disabled={!t.order_id}
                                            onClick={() => t.order_id && router.push(`/dashboard/order?id=${t.order_id}`)}
                                            className="w-full text-left flex flex-wrap items-center gap-x-4 gap-y-1 px-5 py-3 hover:bg-gray-50 disabled:hover:bg-transparent focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand">
                                        <span className="w-12 text-xs text-gray-600 tabular-nums">{tunisTime(t.ts)}</span>
                                        <span className="w-40 text-sm font-medium text-gray-900">{ROLE[t.role] ?? t.role}</span>
                                        <span className="flex-1 min-w-0 text-xs text-gray-600 truncate">
                                            {t.cache_hit ? "Recorded answer reused" : `${t.provider ?? ""} ${t.model ?? ""}`}
                                            {(t.attempts || []).length > 1 && ` · tried ${t.attempts.length} models`}
                                        </span>
                                        <span className="text-xs text-gray-600 tabular-nums w-16 text-right">{t.latency_ms ? `${(t.latency_ms / 1000).toFixed(1)} s` : "–"}</span>
                                        <Chip tone={t.outcome === "ok" ? "green" : t.cache_hit ? "blue" : "amber"}>{t.outcome === "ok" ? "OK" : t.cache_hit ? "From memory" : t.outcome}</Chip>
                                    </button>
                                </li>
                            ))}
                        </ul>
                    )}
            </section>
        </Page>
    );
}
