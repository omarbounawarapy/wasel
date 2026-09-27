"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, Guide, Section, Details, Empty } from "@/components/wasel/kit";

// Plain names and the few numbers that matter per test suite; everything else sits under "All results".
const SUITES: Record<string, { name: string, what: string, key: [string, string][] }> = {
    extraction: { name: "Reading customer messages", what: "Does Wasel understand what the customer wrote?",
        key: [["is_order_acc", "Spots real orders"], ["address_within1_acc", "Reads the address correctly"], ["language_acc", "Recognises the language"]] },
    outbound: { name: "Safety of drafted replies", what: "Are bad replies stopped before they reach a customer?",
        key: [["unsafe_blocked", "Unsafe replies blocked"], ["safe_passed", "Good replies allowed"], ["task_success", "Overall"]] },
    injection: { name: "Resisting tricks", what: "Messages that try to fool the AI (“ignore your instructions…”).",
        key: [["flagged_rate", "Tricks detected"], ["still_scored_rate", "Order still scored"], ["not_promoted_rate", "Score not lowered by the trick"]] },
    g1_conversations: { name: "Real conversations by a native speaker", what: "24 conversations written by a Tunisian speaker.",
        key: [["is_order_acc", "Spots real orders"], ["address_within1_acc", "Reads the address correctly"], ["flag_precision", "Warning signs are right"]] },
    g3_injection: { name: "Tricks written by a native speaker", what: "8 manipulation attempts in Darija, Arabizi and French.",
        key: [["flagged_rate", "Tricks detected"], ["still_scored_rate", "Order still scored"], ["not_promoted_rate", "Score not lowered by the trick"]] },
    prefilter_cases: { name: "Reply rule checks", what: "12 hand-written replies that must pass or fail the rules.",
        key: [["task_success", "Handled as expected"], ["unsafe_blocked", "Unsafe replies blocked"], ["safe_passed", "Good replies allowed"]] },
};

// rates are named *_acc, *_rate, precision, recall, f1, success, blocked, passed; everything else is a count
const isRate = (k: string) => /(_acc|_rate|precision|recall|f1|success|blocked|passed)$/.test(k);
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
                            <div className="grid grid-cols-3 gap-3">
                                {keys.map(([k, label]) => (
                                    <div key={k} className="min-w-0">
                                        <p className="text-2xl font-bold text-brand-ink tabular-nums">{fmt(metrics[k], k)}</p>
                                        <p className="text-xs text-gray-600 leading-snug">{label}</p>
                                    </div>
                                ))}
                            </div>
                            <Details label="All results">
                                <table className="w-full">
                                    <tbody>
                                        {Object.entries(metrics).filter(([k]) => k !== "n").map(([k, v]) => (
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

    useEffect(() => {
        ordersApi.getEvalReports().then(setData).catch(() => {}).finally(() => setLoading(false));
    }, []);

    return (
        <Page wide>
            <PageHeader
                title="Quality checks"
                subtitle="Before every release, Wasel is tested on hundreds of example conversations. A release only ships when all checks pass." />

            <Guide id="quality" steps={[
                "Each card is one family of tests, named after what it protects.",
                "The big numbers are the share of test cases Wasel got right.",
                "Open “All results” on a card for the detailed numbers.",
            ]} />

            {loading ? <p className="text-gray-600">Loading…</p> : !data?.offline && !data?.live ? (
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
