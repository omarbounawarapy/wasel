"use client";

import { useCallback, useEffect, useState } from "react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, Guide, Section, StatCard, Details, Chip, Empty, LoadError } from "@/components/wasel/kit";

// Group ranked issues by problem (same type), keep the best rank first.
function groupIssues(issues: any[]) {
    const groups = new Map<string, { type: string, title: string, status: string, rank: number, cases: any[] }>();
    for (const i of issues) {
        const g = groups.get(i.type) ?? { type: i.type, title: i.title, status: i.status, rank: i.rank, cases: [] as any[] };
        g.cases.push(i);
        g.rank = Math.min(g.rank, i.rank);
        if (i.status === "failure") g.status = "failure";
        groups.set(i.type, g);
    }
    return [...groups.values()].sort((a, b) => a.rank - b.rank);
}

// The analyzer reports raw identifiers from the synthetic sessions' own tools. Show plain wording instead.
const SIGNATURE_LABELS: Record<string, string> = {
    "confirm_order never called": "Said the order was confirmed, but the confirmation was never made",
    "confirm_order failed": "Said the order was confirmed, but the confirmation failed",
    "closed with an imprecise address": "Closed as done with an address that was still imprecise",
    "lookup_customer returned another customer": "The customer lookup returned another customer's record",
    "asked again: address": "Asked again for the address",
    "asked again: confirm": "Asked again for the confirmation",
    "search_address: same query, no results": "Searched for the address again with the same words and found nothing",
    "update_order failed": "The order update failed, yet the conversation went on as if it worked",
    "customer question left unanswered": "A customer question was left unanswered",
};

// Unknown signatures still lose their underscores, so no raw identifier is shown as-is.
const plainSignature = (sig: string) => SIGNATURE_LABELS[sig] ?? String(sig).replace(/_/g, " ");

export default function FailuresPage() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const load = useCallback(() => {
        setLoading(true);
        ordersApi.getFailures().then(d => { setData(d); setError(false); }).catch(() => setError(true)).finally(() => setLoading(false));
    }, []);
    useEffect(() => { load(); }, [load]);

    const groups = data?.issues ? groupIssues(data.issues) : [];
    const failed = data?.by_status?.failure ?? 0;
    const review = data?.by_status?.needs_review ?? 0;

    return (
        <Page>
            <PageHeader
                title="Silent failures"
                subtitle="A demonstration of the silent-failure analyzer on synthetic test conversations. It is not a measurement of real Wasel conversations." />

            <Guide id="failures" steps={[
                "The analyzer re-reads finished conversations and looks for silent mistakes: cases where nothing crashed, yet the customer was let down.",
                "Problems are grouped and ranked: fix the top card first.",
                "Each card lists the specific cases and how often they happened.",
            ]} />

            {error ? <LoadError what="the silent-failure report" onRetry={load} /> : loading ? <p className="text-gray-600">Loading…</p> : !data?.issues ? (
                <Section title="No report yet"><Empty title="The silent-failure analysis hasn't been run on this server." /></Section>
            ) : (
                <>
                    <div role="note" className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                        <p className="font-semibold">Test data, not real Wasel conversations.</p>
                        <p className="mt-1">
                            The analyzer was run on {data.n_sessions} synthetic conversations of a different, imaginary assistant, to show
                            that it can find silent failures. The percentages below are not a Wasel failure rate.
                        </p>
                    </div>

                    <div className="grid grid-cols-3 gap-2 sm:gap-4">
                        <StatCard label="Test conversations checked" value={data.n_sessions} hint="Synthetic, not real Wasel orders" />
                        <StatCard label="Silent failures" value={failed} tone={failed ? "warn" : "good"}
                                  hint={data.n_sessions ? `${Math.round((failed / data.n_sessions) * 100)}% of the test conversations` : undefined} />
                        <StatCard label="Worth a second look" value={review} hint="Not sure it's a failure" />
                    </div>

                    {groups.length === 0 ? (
                        <Section title="Problems found"><Empty title="No silent failures found in this run." /></Section>
                    ) : (
                        <ol className="space-y-4">
                            {groups.map((g, idx) => {
                                const total = g.cases.reduce((s, c) => s + (c.n_sessions || 0), 0);
                                return (
                                    <li key={g.type}>
                                        <Section step={idx + 1} title={g.title}
                                                 actions={<Chip tone={g.status === "failure" ? "amber" : "gray"}>{g.status === "failure" ? "Failure" : "Needs review"}</Chip>}>
                                            <p className="text-sm text-gray-700 mb-3">
                                                Seen in <span className="font-semibold tabular-nums">{total}</span> conversation{total === 1 ? "" : "s"}.
                                            </p>
                                            <ul className="divide-y divide-gray-100 border-y border-gray-100">
                                                {g.cases.map((c: any) => (
                                                    <li key={c.signature} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                                                        <span className="text-gray-800 min-w-0 break-words">{plainSignature(c.signature)}</span>
                                                        <span className="text-gray-600 tabular-nums shrink-0">{c.n_sessions} × · {Math.round((c.share || 0) * 100)}%</span>
                                                    </li>
                                                ))}
                                            </ul>
                                            <Details>
                                                <p>Problem type: {g.type.replace(/_/g, " ")}</p>
                                                {g.cases.map((c: any) => (
                                                    <p key={c.signature}>{plainSignature(c.signature)}: confidence {Math.round((c.confidence || 0) * 100)}%, priority {Number(c.priority).toFixed(1)}</p>
                                                ))}
                                            </Details>
                                        </Section>
                                    </li>
                                );
                            })}
                        </ol>
                    )}

                    {data.limitations?.length > 0 && (
                        <Details label="Limits of this analysis">
                            <ul className="list-disc pl-5 space-y-1">{data.limitations.map((l: string) => <li key={l}>{l}</li>)}</ul>
                        </Details>
                    )}
                </>
            )}
        </Page>
    );
}
