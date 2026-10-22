"use client";

// Wasel UI kit: one card anatomy, one radius (rounded-2xl), one primary (brand navy), reused by every page.
// Quiet by default: white cards with a hairline on warm paper, small uppercase labels, large light numbers;
// colour is kept for meaning (risk, warnings, the one primary action).
import { useEffect, useState, type ReactNode } from "react";
import { ChevronDown, Info, X } from "lucide-react";

// ---------------------------------------------------------------- shared labels
// Tinted, not filled: the hue and the shape carry the tier, the text stays readable in both themes.
export const TIER: Record<string, { label: string, cls: string, dot: string, shape: string, meaning: string }> = {
    high: { label: "High", cls: "bg-red-50 text-red-800 border border-red-200", dot: "text-red-600", shape: "●", meaning: "Likely refused at the door. Confirm before shipping." },
    medium: { label: "Medium", cls: "bg-amber-50 text-amber-800 border border-amber-200", dot: "text-amber-600", shape: "◆", meaning: "Some doubt. A quick confirmation helps." },
    low: { label: "Low", cls: "bg-emerald-50 text-emerald-800 border border-emerald-200", dot: "text-emerald-600", shape: "▲", meaning: "Looks safe. Ship normally." },
};

export const NEXT_STEP: Record<string, string> = {
    confirm: "Confirm with the customer",
    prepay: "Ask for prepayment",
    ship: "Ship normally",
    review: "Check it yourself",
    cancelled: "Cancelled",
};

export const STATUS: Record<string, string> = {
    collecting: "Not an order yet",
    awaiting_reply: "Waiting for customer",
    needs_review: "Needs your decision",
    ready_to_ship: "Ready to ship",
    shipped: "Shipped",
    delivered: "Delivered",
    refused: "Refused at door",
    cancelled: "Cancelled",
};

// "just now", "7 min ago", "today 20:26" or "9 Oct 20:26", in Tunisia time: every time says its day or its age
export const whenLabel = (iso?: string | null, now: number = Date.now()) => {
    if (!iso) return "";
    const t = new Date(iso).getTime();
    const mins = Math.round((now - t) / 60000);
    if (mins >= 0 && mins < 1) return "just now";
    if (mins >= 1 && mins < 60) return `${mins} min ago`;
    const clock = new Intl.DateTimeFormat("en-GB", { timeZone: "Africa/Tunis", hour: "2-digit", minute: "2-digit" }).format(new Date(iso));
    const dayKey = (ms: number) => new Intl.DateTimeFormat("en-CA", { timeZone: "Africa/Tunis", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms));
    if (dayKey(t) === dayKey(now)) return `today ${clock}`;
    const date = new Intl.DateTimeFormat("en-GB", { timeZone: "Africa/Tunis", day: "numeric", month: "short" }).format(new Date(iso));
    return `${date} ${clock}`;
};

export const tnd = (v?: number | null) =>
    v === null || v === undefined ? "–" : `${Number.isInteger(v) ? v : v.toFixed(1)} TND`;

// ---------------------------------------------------------------- page chrome
export function Page({ children }: { children: ReactNode }) {
    return <div className={`w-full max-w-7xl space-y-8`}>{children}</div>;
}

export function PageHeader({ title, subtitle, actions }: { title: string, subtitle: string, actions?: ReactNode }) {
    return (
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
            <div className="min-w-0">
                <h1 className="text-[28px] sm:text-[34px] leading-[1.1] font-semibold tracking-[-0.035em] text-brand-ink text-balance">{title}</h1>
                <p className="text-[15px] text-gray-600 mt-2 max-w-prose text-pretty">{subtitle}</p>
            </div>
            {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
    );
}

/** A "how this page works" strip: numbered steps in plain words. Closed by default, so the page leads with its data;
 *  opening it is remembered per page. */
export function Guide({ id, steps }: { id: string, steps: string[] }) {
    const key = `wasel_guide_${id}`;
    const [open, setOpen] = useState(false);
    useEffect(() => {
        try { if (localStorage.getItem(key) === "open") setOpen(true); } catch { /* storage blocked */ }
    }, [key]);
    const hide = () => { setOpen(false); try { localStorage.removeItem(key); } catch { /* ignore */ } };
    const show = () => { setOpen(true); try { localStorage.setItem(key, "open"); } catch { /* ignore */ } };

    if (!open) {
        return (
            // 44 px hit area around a 32 px pill, tucked under the page title
            <button type="button" onClick={show} className="group inline-flex items-center min-h-[44px] -mt-4">
                <span className="inline-flex items-center gap-1.5 h-8 px-3 rounded-full border border-gray-200 bg-card text-xs font-medium text-gray-700 shadow-xs transition-colors group-hover:border-gray-300 group-hover:text-gray-900">
                    <Info className="w-3.5 h-3.5" aria-hidden="true" /> How this page works
                </span>
            </button>
        );
    }
    return (
        <section aria-label="How this page works" className="rounded-2xl bg-card border border-border p-4 sm:p-5">
            <div className="flex items-start gap-4">
                <ol className="flex-1 grid gap-4 sm:grid-cols-3">
                    {steps.map((s, i) => (
                        <li key={i} className="flex items-start gap-3 min-w-0">
                            <span className="shrink-0 w-6 h-6 rounded-full border border-gray-300 text-[11px] font-semibold tabular-nums text-gray-700 flex items-center justify-center">{i + 1}</span>
                            <span className="text-sm text-gray-700 leading-snug">{s}</span>
                        </li>
                    ))}
                </ol>
                <button type="button" onClick={hide} aria-label="Hide this guide"
                        className="shrink-0 -m-2 w-11 h-11 inline-flex items-center justify-center rounded-full text-gray-600 hover:text-gray-900 hover:bg-gray-100">
                    <X className="w-4 h-4" />
                </button>
            </div>
        </section>
    );
}

// ---------------------------------------------------------------- cards
export function Section({ title, hint, step, actions, children, className = "" }: {
    title: string, hint?: string, step?: number, actions?: ReactNode, children: ReactNode, className?: string
}) {
    return (
        <section className={`bg-card rounded-2xl border border-border shadow-sm p-5 sm:p-6 min-w-0 ${className}`}>
            <div className="flex items-start justify-between gap-3 mb-5">
                <div className="min-w-0">
                    <h2 className="text-[15px] font-semibold tracking-[-0.01em] text-brand-ink flex items-center gap-2.5">
                        {step !== undefined && (
                            <span className="shrink-0 w-6 h-6 rounded-full border border-gray-300 text-gray-700 text-[11px] font-semibold tabular-nums flex items-center justify-center">{step}</span>
                        )}
                        {title}
                    </h2>
                    {hint && <p className="text-[13px] text-gray-600 mt-1 text-pretty">{hint}</p>}
                </div>
                {actions}
            </div>
            {children}
        </section>
    );
}

/** A label and one large number. With `onClick` it is a toggle (a filter): `active` marks the one that is on. */
export function StatCard({ label, value, hint, tone = "default", onClick, active }: {
    label: string, value: ReactNode, hint?: string, tone?: "default" | "brand" | "warn" | "good", onClick?: () => void, active?: boolean
}) {
    const toneCls = {
        default: "text-brand-ink",
        brand: "text-brand",
        warn: "text-amber-700",
        good: "text-emerald-700",
    }[tone];
    const Tag = onClick ? "button" : "div";
    return (
        <Tag type={onClick ? "button" : undefined} onClick={onClick} aria-pressed={onClick ? !!active : undefined}
             className={`text-start bg-card rounded-2xl border p-4 sm:p-6 min-w-0 transition-[border-color,box-shadow] duration-300 ease-lux ${active
                 ? "border-brand ring-1 ring-brand shadow-md" : "border-border shadow-sm"} ${onClick
                 ? "hover:shadow-md focus-visible:outline-2 focus-visible:outline-brand" : ""}`}>
            <p className="text-[11px] font-medium uppercase tracking-[0.06em] text-gray-600 leading-snug">{label}</p>
            <p className={`mt-3 sm:mt-4 text-[30px] sm:text-[40px] leading-none font-medium tracking-[-0.035em] tabular-nums ${toneCls}`}>{value}</p>
            {hint && <p className="hidden sm:block text-[13px] text-gray-600 mt-2.5">{hint}</p>}
        </Tag>
    );
}

/** Collapsed-by-default technical detail, so cards show the essentials first. */
export function Details({ label = "Details", open, children }: { label?: string, open?: boolean, children: ReactNode }) {
    return (
        <details className="group mt-3" open={open}>
            <summary className="inline-flex items-center gap-1 text-[13px] font-medium text-gray-600 hover:text-gray-900 cursor-pointer select-none list-none min-h-[44px]">
                <ChevronDown className="w-3.5 h-3.5 transition-transform group-open:rotate-180" /> {label}
            </summary>
            <div className="mt-2 text-xs text-gray-600 space-y-1">{children}</div>
        </details>
    );
}

export function Chip({ children, tone = "gray" }: { children: ReactNode, tone?: "gray" | "amber" | "blue" | "green" }) {
    const cls = {
        gray: "text-gray-700 bg-gray-100",
        amber: "text-amber-800 bg-amber-50",
        blue: "text-brand bg-brand-soft",
        green: "text-emerald-800 bg-emerald-50",
    }[tone];
    return <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-md whitespace-nowrap ${cls}`}>{children}</span>;
}

export function RiskBadge({ tier, score, size = "sm" }: { tier?: string | null, score?: number | null, size?: "sm" | "lg" }) {
    const t = tier ? TIER[tier] : null;
    if (!t || score === null || score === undefined) {
        return <span className="text-xs font-medium text-gray-600 animate-pulse motion-reduce:animate-none whitespace-nowrap">Scoring…</span>;
    }
    return (
        <span aria-label={`${t.label} risk, ${score} out of 100`}
              className={`inline-flex items-center gap-1.5 rounded-full font-semibold whitespace-nowrap tabular-nums ${t.cls} ${size === "lg" ? "px-3.5 py-1.5 text-[15px]" : "px-2.5 py-0.5 text-xs"}`}>
            <span aria-hidden="true" className={`${t.dot} text-[0.75em]`}>{t.shape}</span>{t.label} {score}
        </span>
    );
}

/** The score as a headline: one large number, its tier and change beside it. `label` replaces the tier name (translations). */
export function ScoreFigure({ tier, score, delta, label }: { tier?: string | null, score?: number | null, delta?: number | null, label?: string }) {
    const t = tier ? TIER[tier] : null;
    if (!t || score === null || score === undefined) return <RiskBadge tier={tier} score={score} />;
    return (
        <span className="inline-flex items-end gap-3">
            <span className="sr-only">{label ?? `${t.label} risk`}, {score} out of 100.</span>
            <span aria-hidden="true" className="text-[56px] leading-[0.85] font-medium tracking-[-0.05em] tabular-nums text-brand-ink">{score}</span>
            <span className="flex flex-col items-start gap-1.5 pb-0.5">
                <Delta delta={delta} />
                <span aria-hidden="true" className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${t.cls}`}>
                    <span className={`${t.dot} text-[0.75em]`}>{t.shape}</span>{label ?? t.label}
                </span>
            </span>
        </span>
    );
}

const READ_BY: Record<string, { label: string, tone: "blue" | "gray" | "amber" }> = {
    ai: { label: "Read by AI", tone: "blue" },
    rules: { label: "Read by rules", tone: "amber" },
    recorded: { label: "Saved AI read", tone: "gray" },
};

/** Says how a score was produced: a live AI read, the rules alone, or a stored (recorded) AI result. */
export function ReadBy({ value }: { value?: string | null }) {
    const r = value ? READ_BY[value] : null;
    if (!r) return null;
    return <Chip tone={r.tone}>{r.label}</Chip>;
}

export function Delta({ delta }: { delta?: number | null }) {
    if (!delta) return null;
    const down = delta < 0;
    return (
        <span className={`text-xs font-semibold tabular-nums whitespace-nowrap ${down ? "text-emerald-700" : "text-red-600"}`}
              aria-label={down ? `risk down ${-delta} points` : `risk up ${delta} points`}>
            {down ? "▼" : "▲"}{Math.abs(delta)}
        </span>
    );
}

export function Empty({ title, children }: { title: string, children?: ReactNode }) {
    return (
        <div className="text-center py-14 px-4">
            <p className="text-[15px] font-semibold tracking-[-0.01em] text-brand-ink">{title}</p>
            {children && <div className="text-sm text-gray-600 mt-1 max-w-prose mx-auto">{children}</div>}
        </div>
    );
}

/** The message under a field. Pair it with `aria-invalid` and `aria-describedby={id}` on the input so it is read out with it. */
export function FieldError({ id, children }: { id: string, children: ReactNode }) {
    return <p id={id} role="alert" className="mt-1.5 text-sm font-medium text-red-700">{children}</p>;
}

export function LoadError({ what, onRetry }: { what: string, onRetry?: () => void }) {
    return (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 text-red-800 text-sm p-4 flex flex-wrap items-center justify-between gap-3">
            <span>Could not load {what}. Check that the Wasel server is running, then try again.</span>
            {/* Without a page-specific retry, reloading repeats every request the page made */}
            <button type="button" onClick={onRetry ?? (() => window.location.reload())}
                    className="min-h-[44px] px-5 rounded-full bg-white border border-red-300 font-medium text-red-900 hover:bg-red-100">
                Retry
            </button>
        </div>
    );
}
