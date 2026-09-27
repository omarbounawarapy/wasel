"use client";

import { useEffect, useState } from "react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, Guide, Section, StatCard, Details, Chip, Empty } from "@/components/wasel/kit";

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

export default function FailuresPage() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        ordersApi.getFailures().then(setData).catch(() => {}).finally(() => setLoading(false));
    }, []);

    const groups = data?.issues ? groupIssues(data.issues) : [];
    const failed = data?.by_status?.failure ?? 0;
    const review = data?.by_status?.needs_review ?? 0;

    return (
        <Page wide>
            <PageHeader
                title="Silent failures"
                subtitle="Conversations where nothing crashed, yet the customer was still let down: for example the assistant said an order was confirmed when it wasn't." />

            <Guide id="failures" steps={[
                "Wasel re-reads finished conversations and looks for silent mistakes.",
                "Problems are grouped and ranked: fix the top card first.",
                "Each card lists the specific cases and how often they happened.",
            ]} />

            {loading ? <p className="text-gray-600">Loading…</p> : !data?.issues ? (
                <Section title="No report yet"><Empty title="The silent-failure analysis hasn't been run on this server." /></Section>
            ) : (
                <>
                    <div className="grid grid-cols-3 gap-2 sm:gap-4">
                        <StatCard label="Conversations checked" value={data.n_sessions} hint="Synthetic test conversations" />
                        <StatCard label="Silent failures" value={failed} tone={failed ? "warn" : "good"}
                                  hint={data.n_sessions ? `${Math.round((failed / data.n_sessions) * 100)}% of conversations` : undefined} />
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
                                            <ul className="divide-y divide-gray-100 border border-gray-100 rounded-xl">
                                                {g.cases.map((c: any) => (
                                                    <li key={c.signature} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                                                        <span className="text-gray-800 min-w-0 break-words">{c.signature}</span>
                                                        <span className="text-gray-500 tabular-nums shrink-0">{c.n_sessions} × · {Math.round((c.share || 0) * 100)}%</span>
                                                    </li>
                                                ))}
                                            </ul>
                                            <Details>
                                                <p>Problem type: {g.type.replace(/_/g, " ")}</p>
                                                {g.cases.map((c: any) => (
                                                    <p key={c.signature}>{c.signature}: confidence {Math.round((c.confidence || 0) * 100)}%, priority {Number(c.priority).toFixed(1)}</p>
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
