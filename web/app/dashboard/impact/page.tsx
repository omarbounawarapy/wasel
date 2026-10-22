"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, Section, StatCard, Details, Empty, LoadError } from "@/components/wasel/kit";

const pct = (v: number) => `${(v * 100).toFixed(0)}%`;
const num = (v: number) => Math.round(v).toLocaleString("en-US");

export default function ImpactPage() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    const load = useCallback(() => {
        setLoading(true);
        ordersApi.getImpact().then(d => { setData(d); setError(false); }).catch(() => setError(true)).finally(() => setLoading(false));
    }, []);
    useEffect(() => { load(); }, [load]);

    const sens = data?.tnd_saved_per_1000_by_confirm_rate;
    const vals: number[] = sens ? Object.values(sens).map(Number) : [];
    const range = vals.length > 1 ? [Math.min(...vals), Math.max(...vals)] : null;

    return (
        <Page>
            <PageHeader
                title="Money saved"
                subtitle="Delivery cost avoided when you follow Wasel's advice." />

            {error ? <LoadError what="the money-saved report" onRetry={load} /> : loading ? <p className="text-gray-600">Loading…</p> : !data?.n_orders ? (
                <Section title="No estimate yet"><Empty title="The impact report hasn't been generated on this server." /></Section>
            ) : (
                <>
                    <section aria-labelledby="saved-per-1000" className="rounded-[28px] bg-brand text-white p-6 sm:p-10 shadow-md">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                            <h2 id="saved-per-1000" className="text-[11px] font-medium uppercase tracking-[0.08em] text-white/80">Wasted-trip cost avoided, per 1,000 orders</h2>
                            <span className="text-[11px] font-semibold uppercase tracking-[0.08em] bg-white/15 rounded-full px-2.5 py-1">Simulated</span>
                        </div>
                        <p className="mt-6 text-[44px] sm:text-[72px] leading-none font-medium tracking-[-0.045em] tabular-nums">
                            {range ? `${num(range[0])}–${num(range[1])}` : num(data.tnd_saved_per_1000_orders)}
                            <span className="ms-3 text-[0.35em] font-medium tracking-normal text-white/80">TND</span>
                        </p>
                        {/* The figures behind the headline, then the caveat that matters */}
                        <dl className="mt-8 pt-6 border-t border-white/15 grid grid-cols-1 sm:grid-cols-3 gap-5 sm:gap-8">
                            {range && (
                                <div>
                                    <dt className="text-[13px] text-white/80">Best guess</dt>
                                    <dd className="mt-1 text-2xl font-medium tracking-[-0.02em] tabular-nums">{num(data.tnd_saved_per_1000_orders)} TND</dd>
                                </div>
                            )}
                            <div>
                                <dt className="text-[13px] text-white/80">Refused trips avoided</dt>
                                <dd className="mt-1 text-2xl font-medium tracking-[-0.02em] tabular-nums">
                                    {num(data.trips_avoided)}<span className="text-base text-white/80"> in {num(data.n_orders)} orders</span>
                                </dd>
                            </div>
                            <div>
                                <dt className="text-[13px] text-white/80">Saved in this run</dt>
                                <dd className="mt-1 text-2xl font-medium tracking-[-0.02em] tabular-nums">{num(data.tnd_saved)} TND</dd>
                            </div>
                        </dl>
                        <p className="mt-6 text-[13px] text-white/80 max-w-prose">
                            {range ? "The range depends on how many customers answer a confirmation. " : ""}
                            Measured on synthetic orders from the model&apos;s own training prior, with every recommendation followed. Real orders must confirm it.
                        </p>
                    </section>

                    <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] items-center gap-4">
                        <StatCard label="Refused at the door today" value={pct(data.baseline_refusal_rate)} hint="Without Wasel (simulated)" />
                        <ArrowRight className="w-6 h-6 text-gray-500 mx-auto rotate-90 sm:rotate-0" aria-hidden="true" />
                        <StatCard label="Refused with Wasel" value={pct(data.projected_refusal_rate)} tone="good"
                                  hint={`${((data.baseline_refusal_rate - data.projected_refusal_rate) * 100).toFixed(1)} points fewer refusals`} />
                    </div>

                    {data.this_server?.n_orders > 0 && (
                        <Section title="On the orders on this server"
                                 hint="The same assumptions applied to the orders you can see here. Each order's chance of refusal is its score; this is an expectation, not an outcome.">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                                <StatCard label="Orders scored" value={num(data.this_server.n_orders)}
                                          hint={`${data.this_server.ship} ship · ${data.this_server.confirm} confirm · ${data.this_server.prepay} prepay`} />
                                <StatCard label="Refusals expected" value={data.this_server.expected_refusals.toFixed(1)}
                                          hint="Sum of the orders' refusal chances" />
                                <StatCard label="Cost avoided if advice is followed" value={`${data.this_server.expected_tnd_saved.toFixed(0)} TND`} tone="good"
                                          hint={`${data.this_server.expected_trips_avoided.toFixed(1)} refused deliveries avoided`} />
                            </div>
                        </Section>
                    )}

                    <Section title="How this was estimated" hint="The numbers above rest on these assumptions. A real pilot would measure them.">
                        <p className="text-sm text-gray-700 max-w-prose">
                            Real savings = refusals avoided × cost of a trip − sales lost to extra questions, measured against a small group of orders shipped without Wasel.
                        </p>
                        <Details label={`Assumptions (${data.assumptions?.length ?? 0})`}>
                            <ul className="list-disc ps-5 space-y-1">
                                {data.assumptions?.map((x: string, i: number) => <li key={i}>{x}</li>)}
                            </ul>
                            <p className="pt-1">Dataset: {data.dataset}</p>
                        </Details>
                    </Section>
                </>
            )}
        </Page>
    );
}
