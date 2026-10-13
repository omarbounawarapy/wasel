"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, Section, Details, Chip, LoadError } from "@/components/wasel/kit";

const FEATURE: Record<string, string> = {
    language: "Languages customers write in",
    address_level: "How precise addresses are",
    tier: "Share of high / medium / low risk",
};

const RATES: Record<string, [string, string]> = {
    hallucinated_quotes_per_extraction: ["Invented quotes", "Quotes the AI made up (should be 0)"],
    invalid_extraction_rate: ["Unreadable AI answers", "Answers that didn't match the expected format"],
    injection_rate: ["Trick attempts", "Messages trying to fool the AI"],
    fallback_rate: ["Backup model used", "The main model was busy or failed"],
    dropped_flags_per_extraction: ["Warnings dropped", "Warning signs removed because the quote wasn't real"],
};

const pct = (v: any) => typeof v === "number" ? `${(v * 100).toFixed(v === 0 ? 0 : 1)}%` : "–";

export default function MonitorPage() {
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState(false);
    const [refreshing, setRefreshing] = useState(false);
    const [health, setHealth] = useState<any>(null);

    const load = () => {
        setRefreshing(true);
        ordersApi.health().then(setHealth).catch(() => setHealth(null));
        ordersApi.getMonitor().then(d => { setData(d); setError(false); }).catch(() => setError(true)).finally(() => setRefreshing(false));
    };
    useEffect(() => { load(); }, []);

    const llm = health?.llm || {};
    const chain: string[] = Array.isArray(llm.chain_extract) ? llm.chain_extract : [];

    const drift: any[] = Array.isArray(data?.drift) ? data.drift : [];
    const alerts: any[] = Array.isArray(data?.alerts) ? data.alerts : [];
    const faith = data?.faithfulness || {};
    const live: number = faith.live ?? faith.n ?? 0;
    const recorded: number = faith.recorded ?? 0;
    const noLive = live === 0;
    const good = alerts.length === 0 && !noLive;
    const featureLine = (d: any) => {
        const cur = d.current || {};
        const top = Object.entries(cur).sort((a: any, b: any) => b[1] - a[1]).slice(0, 3);
        return top.length ? top.map(([k, v]) => `${k} ${pct(v)}`).join(", ") : "no data yet";
    };

    return (
        <Page>
            <PageHeader
                title="Live monitor"
                subtitle={`Watches the last messages Wasel scored and warns you if they start to look different from what it was tested on. AI readings: ${live} live, ${recorded} recorded.`}
                actions={
                    <button type="button" onClick={load} disabled={refreshing}
                            className="inline-flex items-center gap-2 px-3 min-h-[44px] rounded-xl bg-white border border-gray-300 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50">
                        <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin motion-reduce:animate-none" : ""}`} /> Refresh
                    </button>
                } />

            {error && <LoadError what="the monitor" />}
            {!data && !error && <p className="text-gray-600">Loading…</p>}

            {data && (
                <>
                    <section className={`rounded-2xl p-5 border flex items-start gap-3 ${good ? "bg-emerald-50 border-emerald-200" : alerts.length ? "bg-amber-50 border-amber-200" : "bg-gray-50 border-gray-200"}`}>
                        {!good ? <AlertTriangle className={`w-6 h-6 shrink-0 ${alerts.length ? "text-amber-600" : "text-gray-500"}`} /> : <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />}
                        <div>
                            <p className={`font-bold ${good ? "text-emerald-900" : alerts.length ? "text-amber-900" : "text-gray-900"}`}>
                                {alerts.length ? `${alerts.length} thing${alerts.length > 1 ? "s" : ""} to look at` : noLive ? "No live AI calls yet" : "Everything looks normal"}
                            </p>
                            {alerts.length > 0 && (
                                <ul className="list-disc pl-5 mt-1 text-sm text-amber-900">
                                    {alerts.map((a, i) => <li key={i}>{typeof a === "string" ? a : a.message ?? JSON.stringify(a)}</li>)}
                                </ul>
                            )}
                            <p className="text-sm text-gray-600 mt-0.5">{noLive ? `Nothing to judge yet. ${recorded} recorded readings are not counted.` : `Based on ${live} recent live AI readings.`}</p>
                        </div>
                    </section>

                    <Section title="Where the AI runs" hint="The host label comes from the server configuration.">
                        {llm.serving_label
                            ? <p className="text-sm text-gray-900 font-medium">{llm.serving_label} <span className="font-normal text-gray-600">· host {llm.serving_host}</span></p>
                            : <p className="text-sm text-gray-600">No self-hosted AI host is configured.</p>}
                        {llm.serving_label && <p className="text-sm text-gray-700 mt-1">{!llm.last_path ? "No assessment recorded yet." : llm.last_host ? `The last AI answer came from ${llm.serving_label}.` : "The last assessment did not come from the self-hosted host (backup or rules)."}</p>}
                        <p className="text-sm text-gray-700 mt-1">Model chain: {chain.join(" → ") || "rules only"}</p>
                        {llm.fallback_active && <p className="text-sm text-amber-900 mt-1">The primary host did not answer in the last 5 minutes; the backup is in use.</p>}
                    </Section>

                    <Section title="Are customers writing differently?" hint="Compared with the test conversations. “Changed” means Wasel is seeing something new.">
                        {drift.length === 0 ? (
                            <p className="text-sm text-gray-600">Not enough scored orders yet (needs {data.min_samples ?? 20}).</p>
                        ) : (
                            <ul className="divide-y divide-gray-100">
                                {drift.map((d: any) => (
                                    <li key={d.feature} className="py-3">
                                        <div className="flex items-center justify-between gap-3">
                                            <span className="text-sm font-medium text-gray-900">{FEATURE[d.feature] ?? d.feature}</span>
                                            {d.n < (data.min_samples ?? 20)
                                                ? <Chip tone="gray">Too few readings</Chip>
                                                : <Chip tone={d.drifted ? "amber" : "green"}>{d.drifted ? "Changed" : "As expected"}</Chip>}
                                        </div>
                                        <p className="text-sm text-gray-700 mt-1">{featureLine(d)}</p>
                                        <Details open>
                                            <p>Drift score (PSI) {typeof d.psi === "number" ? d.psi.toFixed(3) : "–"} · {d.n} readings</p>
                                            {d.current && Object.keys(d.current).map(k => (
                                                <p key={k}>{k}: now {pct(d.current[k])}, tests {pct(d.reference?.[k])}</p>
                                            ))}
                                        </Details>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </Section>

                    <Section title="Is the AI behaving?" hint="Share of recent readings with each problem. Lower is better.">
                        {noLive ? <p className="text-sm text-gray-600">No live AI calls yet, so there is nothing to judge.</p> :
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                            {Object.entries(RATES).filter(([k]) => k in faith).map(([k, [label, hint]]) => (
                                <div key={k} className="min-w-0" title={hint}>
                                    <p className="text-2xl font-bold text-brand-ink tabular-nums">{pct(faith[k])}</p>
                                    <p className="text-xs text-gray-600">{label}</p>
                                </div>
                            ))}
                        </div>}
                        <Details label="Replies and AI service details">
                            {data.safety && <p>Replies drafted {data.safety.drafts ?? 0} · checked by the AI judge {data.safety.judged ?? 0}</p>}
                            {data.ops && <p>AI requests {data.ops.attempts ?? 0} · error rate {pct(data.ops.llm_error_rate)} · refusal rate {pct(data.ops.refusal_rate)}</p>}
                            <p>Reference: {data.reference}</p>
                        </Details>
                    </Section>
                </>
            )}
        </Page>
    );
}
