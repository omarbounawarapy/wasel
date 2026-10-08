"use client";

import { useEffect, useState } from "react";
import { ArrowRight } from "lucide-react";
import { ordersApi } from "@/lib/api/orders";
import { Page, PageHeader, Section, StatCard, Details, Empty } from "@/components/wasel/kit";

const pct = (v: number) => `${(v * 100).toFixed(0)}%`;
const num = (v: number) => Math.round(v).toLocaleString("en-US");

export default function ImpactPage() {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        ordersApi.getImpact().then(setData).catch(() => {}).finally(() => setLoading(false));
    }, []);

    const sens = data?.tnd_saved_per_1000_by_confirm_rate;
    const vals: number[] = sens ? Object.values(sens).map(Number) : [];
    const range = vals.length > 1 ? [Math.min(...vals), Math.max(...vals)] : null;

    return (
        <Page>
            <PageHeader
                title="Money saved"
                subtitle="How much wasted delivery cost Wasel avoids when you follow its advice. This is a simulation on synthetic orders, not real sales." />

            {loading ? <p className="text-gray-600">Loading…</p> : !data?.n_orders ? (
                <Section title="No estimate yet"><Empty title="The impact report hasn't been generated on this server." /></Section>
            ) : (
                <>
                    <section className="rounded-2xl bg-brand text-white p-6 shadow-sm">
                        <p className="text-sm font-medium text-white/80">Estimated wasted-trip cost avoided, per 1,000 orders</p>
                        <p className="text-4xl font-bold tabular-nums mt-1">
                            {range ? `${num(range[0])} to ${num(range[1])} TND` : `${num(data.tnd_saved_per_1000_orders)} TND`}
                        </p>
                        <p className="text-sm text-white/85 mt-2 max-w-prose">
                            {range ? `Best guess ${num(data.tnd_saved_per_1000_orders)} TND, depending on how many customers answer a confirmation. ` : ""}
                            Measured on synthetic orders drawn from the same prior the model was trained on, so it must be re-measured on real orders.
                        </p>
                        <p className="text-sm text-white/85 mt-2 max-w-prose">
                            In this run: {num(data.tnd_saved)} TND on {num(data.n_orders)} orders ({num(data.trips_avoided)} refused deliveries avoided, if every recommendation is followed).
                        </p>
                        <p className="mt-3 inline-block text-xs font-bold uppercase tracking-wider bg-white/15 rounded-full px-2.5 py-1">Simulated</p>
                    </section>

                    <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] items-center gap-4">
                        <StatCard label="Refused at the door today" value={pct(data.baseline_refusal_rate)} hint="Without Wasel (synthetic data)" />
                        <ArrowRight className="w-6 h-6 text-gray-500 mx-auto rotate-90 sm:rotate-0" aria-hidden="true" />
                        <StatCard label="Refused with Wasel" value={pct(data.projected_refusal_rate)} tone="good"
                                  hint={`${((data.baseline_refusal_rate - data.projected_refusal_rate) * 100).toFixed(1)} points fewer refusals`} />
                    </div>

                    <Section title="How this was estimated" hint="The numbers above rest on these assumptions. A real pilot would measure them.">
                        <p className="text-sm text-gray-700 max-w-prose">
                            Real savings = refusals avoided × cost of a trip − sales lost to extra questions, measured against a small group of orders shipped without Wasel.
                        </p>
                        <Details label={`Assumptions (${data.assumptions?.length ?? 0})`}>
                            <ul className="list-disc pl-5 space-y-1">
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
