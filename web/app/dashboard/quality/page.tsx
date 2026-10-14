"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, Guide, Section, Details, Empty, LoadError } from "@/components/wasel/kit";

// Plain names and the few numbers that matter per test suite; everything else sits under "All results".
const SUITES: Record<string, { name: string, what: string, key: [string, string][] }> = {
    extraction: { name: "Reading customer messages", what: "Does Wasel understand what the customer wrote?",
        key: [["is_order_acc", "Spots real orders"], ["address_within1_acc", "Reads the address correctly"], ["language_acc", "Recognises the language"]] },
    outbound: { name: "Safety of drafted replies", what: "Are bad replies stopped before they reach a customer?",
        key: [["unsafe_blocked", "Unsafe replies blocked"], ["safe_passed", "Good replies allowed"], ["task_success", "Overall"]] },
    injection: { name: "Resisting tricks", what: "Messages that try to fool the AI (“ignore your instructions…”).",
        key: [["flagged_rate", "Tricks detected"], ["still_scored_rate", "Order still scored"], ["not_promoted_rate", "Score not lowered by the trick"]] },
    g1_conversations: { name: "Real conversations by a native speaker", what: "Conversations written by a Tunisian speaker.",
        key: [["is_order_acc", "Spots real orders"], ["address_within1_acc", "Reads the address correctly"], ["flag_precision", "Warning signs are right"]] },
    g3_injection: { name: "Tricks written by a native speaker", what: "Manipulation attempts in Darija, Arabizi and French.",
        key: [["flagged_rate", "Tricks detected"], ["still_scored_rate", "Order still scored"], ["not_promoted_rate", "Score not lowered by the trick"]] },
    g3_injection_holdout: { name: "Tricks never seen while building", what: "Attacks written without reading the detector's word list, never used to change it.",
        key: [["flagged_rate", "Tricks detected"], ["still_scored_rate", "Order still scored"], ["not_promoted_rate", "Score not lowered by the trick"]] },
    prefilter_cases: { name: "Reply rule checks", what: "Hand-written replies that must pass or fail the rules.",
        key: [["task_success", "Handled as expected"], ["unsafe_blocked", "Unsafe replies blocked"], ["safe_passed", "Good replies allowed"]] },
};

// rates are named *_acc, *_rate, precision, recall, f1, success, blocked, passed; everything else is a count
const isRate = (k: string) => /(_acc|_rate|precision|recall|f1|success|blocked|passed)$/.test(k);
// per-case rates can be shown as "k of n"; precision, recall and f1 count flags, not cases
const isCaseRate = (k: string) => isRate(k) && !/(precision|recall|f1)$/.test(k);
const big = (v: any, k: string, n?: number) =>
    typeof v === "number" && n && n < 100 && isCaseRate(k) ? `${Math.round(v * n)} of ${n}` : fmt(v, k);
const HIDDEN = ["n", "example", "provenance", "near_misses", "misses"];
const fmt = (v: any, k = "") =>
    typeof v === "number" ? (isRate(k) ? `${(v * 100).toFixed(v === 1 || v === 0 ? 0 : 1)}%` : v.toLocaleString("en-US"))
        : v === null || v === undefined ? "–" : typeof v === "object" ? Object.entries(v).map(([x, y]) => `${x}: ${y}`).join(", ") : String(v);

function Report({ report, title, subtitle }: { report: any, title: string, subtitle: string }) {
    const failures: string[] = report.gate_failures || [];
    const ok = failures.length === 0;
    return (
        <div className="space-y-4">
            <section className={`rounded-2xl p-5 border flex items-start gap-3 ${ok ? "bg-emerald-50 border-emerald-200" : "bg-red-50 border-red-200"}`}>
                {ok ? <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" /> : <XCircle className="w-6 h-6 text-red-600 shrink-0" />}
                <div className="min-w-0">
                    <p className={`font-bold ${ok ? "text-emerald-900" : "text-red-900"}`}>
                        {title}: {ok ? "all checks passed" : `${failures.length} check${failures.length > 1 ? "s" : ""} below target`}
                    </p>
                    <p className={`text-sm mt-0.5 ${ok ? "text-emerald-800" : "text-red-800"}`}>{subtitle}</p>
                    {!ok && <ul className="list-disc pl-5 mt-2 text-sm text-red-800">{failures.map(f => <li key={f}>{f}</li>)}</ul>}
                </div>
            </section>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(report.results || {}).map(([task, metrics]: [string, any]) => {
                    if (!metrics || typeof metrics !== "object") return null;
                    const s = SUITES[task] ?? { name: task.replace(/_/g, " "), what: "", key: [] };
                    const keys = s.key.length ? s.key.filter(([k]) => k in metrics)
                        : Object.keys(metrics).filter(k => typeof metrics[k] === "number" && k !== "n").slice(0, 3).map(k => [k, k.replace(/_/g, " ")] as [string, string]);
                    return (
                        <Section key={task} title={s.name} hint={`${s.what}${metrics.n ? ` Tested on ${metrics.n} cases.` : ""}`}>
                            {metrics.provenance && (
                                <p className={`text-xs font-semibold mb-3 ${metrics.provenance === "held_out" ? "text-emerald-800" : "text-amber-800"}`}>
                                    {metrics.provenance === "held_out" ? "Held out: never tuned against" : "Used while building: the rules were tuned on these cases"}
                                </p>
                            )}
                            <div className="grid grid-cols-3 gap-3">
                                {keys.map(([k, label]) => (
                                    <div key={k} className="min-w-0">
                                        <p className="text-2xl font-bold text-brand-ink tabular-nums">{big(metrics[k], k, metrics.n)}</p>
                                        <p className="text-xs text-gray-600 leading-snug">{label}</p>
                                    </div>
                                ))}
                            </div>
                            {typeof metrics.near_misses === "number" && (
                                <p className="text-xs text-gray-600 mt-3">Near-misses: {metrics.near_misses} of {metrics.n} cases.</p>
                            )}
                            {metrics.example && (
                                <Details label={metrics.example.outcome === "missed" ? "Example: a case it got wrong" : "Example: one real case"}>
                                    <p><span className="font-medium">Input:</span> {metrics.example.input}</p>
                                    <p><span className="font-medium">Expected:</span> {metrics.example.expected}</p>
                                    <p><span className="font-medium">Got:</span> {metrics.example.got}</p>
                                </Details>
                            )}
                            <Details label="All results">
                                <table className="w-full">
                                    <tbody>
                                        {Object.entries(metrics).filter(([k]) => !HIDDEN.includes(k)).map(([k, v]) => (
                                            <tr key={k} className="border-b border-gray-100 last:border-0">
                                                <td className="py-1 pr-3">{k.replace(/_/g, " ")}</td>
                                                <td className="py-1 text-right tabular-nums font-medium text-gray-900">{fmt(v, k)}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </Details>
                        </Section>
                    );
                })}
            </div>

            <Details label="Technical details (versions, run time, AI usage)">
                <p>Run time {report.runtime_s?.toFixed?.(1) ?? "–"} s · config {report.config_hash ?? "–"}</p>
                {report.versions && <p>{Object.entries(report.versions).map(([k, v]) => `${k} ${v}`).join(" · ")}</p>}
                {report.llm_usage && Object.entries(report.llm_usage).map(([role, u]: [string, any]) => (
                    <p key={role}>{role}: {u.requests} calls, {u.cache_hits} cached, {u.tokens_in?.toLocaleString?.()} tokens in, {u.tokens_out?.toLocaleString?.()} out, p50 {u.p50_ms} ms, p95 {u.p95_ms} ms</p>
                ))}
            </Details>
        </div>
    );
}

export default function QualityPage() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [llm, setLlm] = useState<any>(null);

    const load = useCallback(() => {
        setLoading(true);
        ordersApi.health().then(h => setLlm(h.llm)).catch(() => setLlm(null));
        ordersApi.getEvalReports().then(d => { setData(d); setError(false); }).catch(() => setError(true)).finally(() => setLoading(false));
    }, []);
    useEffect(() => { load(); }, [load]);

    return (
        <Page>
            <PageHeader
                title="Quality checks"
                subtitle="Before every release, Wasel is tested on hundreds of example conversations. The offline checks must pass in CI before a change is deployed; the live AI run below is measured separately and can show checks below target." />

            <p className="text-sm text-gray-700">
                {llm?.serving_label
                    ? <>AI on this server runs on <span className="font-medium text-gray-900">{llm.serving_label}</span> (host {llm.serving_host}). The reports below do not record where they were run.</>
                    : "AI on this server uses the hosted model API; no self-hosted host is configured."}
            </p>

            <Guide id="quality" steps={[
                "Each card is one family of tests, named after what it protects.",
                "The big numbers are test cases Wasel got right, out of the cases in that set.",
                "A label says whether a set was used while building (an optimistic score) or held out (an honest one).",
                "Open “All results” on a card for the detailed numbers.",
            ]} />

            {error ? <LoadError what="the quality reports" onRetry={load} /> : loading ? <p className="text-gray-600">Loading…</p> : !data?.offline && !data?.live ? (
                <Section title="No test results yet"><Empty title="The quality reports haven't been generated on this server." /></Section>
            ) : (
                <div className="space-y-10">
                    {data.offline && <Report report={data.offline} title="Release checks" subtitle="Run automatically on every change, without calling any AI service." />}
                    {data.live && <Report report={data.live} title="Live AI checks" subtitle="The same tests run through the real AI models, run by hand." />}
                </div>
            )}
        </Page>
    );
}
