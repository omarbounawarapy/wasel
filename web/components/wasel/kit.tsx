"use client";

// Wasel UI kit: one card anatomy, one radius (rounded-2xl), one primary (brand navy), reused by every page.
import { useEffect, useState, type ReactNode } from "react";
import { ChevronDown, Info, X } from "lucide-react";

// ---------------------------------------------------------------- shared labels
export const TIER: Record<string, { label: string, cls: string, shape: string, meaning: string }> = {
    high: { label: "High", cls: "bg-red-600 text-white", shape: "●", meaning: "Likely refused at the door. Confirm before shipping." },
    medium: { label: "Medium", cls: "bg-amber-500 text-amber-950", shape: "◆", meaning: "Some doubt. A quick confirmation helps." },
    low: { label: "Low", cls: "bg-emerald-700 text-white", shape: "▲", meaning: "Looks safe. Ship normally." },
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

export const tunisTime = (iso?: string | null) => iso
    ? new Intl.DateTimeFormat("en-GB", { timeZone: "Africa/Tunis", hour: "2-digit", minute: "2-digit" }).format(new Date(iso))
    : "";

export const tnd = (v?: number | null) =>
    v === null || v === undefined ? "–" : `${Number.isInteger(v) ? v : v.toFixed(1)} TND`;

// ---------------------------------------------------------------- page chrome
export function Page({ children }: { children: ReactNode }) {
    return <div className={`w-full max-w-7xl space-y-6`}>{children}</div>;
}

export function PageHeader({ title, subtitle, actions }: { title: string, subtitle: string, actions?: ReactNode }) {
    return (
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
            <div className="min-w-0">
                <h1 className="text-2xl font-bold text-brand-ink text-balance">{title}</h1>
                <p className="text-sm text-gray-600 mt-1 max-w-prose">{subtitle}</p>
            </div>
            {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
        </div>
    );
}

/** A dismissible "how this page works" strip: numbered steps in plain words. Remembered per page. */
export function Guide({ id, steps }: { id: string, steps: string[] }) {
    const key = `wasel_guide_${id}`;
    const [open, setOpen] = useState(true);
    useEffect(() => {
        try { if (localStorage.getItem(key) === "hidden") setOpen(false); } catch { /* storage blocked */ }
    }, [key]);
    const hide = () => { setOpen(false); try { localStorage.setItem(key, "hidden"); } catch { /* ignore */ } };
    const show = () => { setOpen(true); try { localStorage.removeItem(key); } catch { /* ignore */ } };

    if (!open) {
        return (
            <button type="button" onClick={show}
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-teal-ink hover:underline min-h-[44px]">
                <Info className="w-3.5 h-3.5" /> How this page works
            </button>
        );
    }
    return (
        <section aria-label="How this page works" className="rounded-2xl bg-teal-soft border border-teal/20 p-4">
            <div className="flex items-start gap-3">
                <ol className="flex-1 grid gap-3 sm:grid-cols-3">
                    {steps.map((s, i) => (
                        <li key={i} className="flex items-start gap-2.5 min-w-0">
                            <span className="shrink-0 w-6 h-6 rounded-full bg-brand text-white text-xs font-bold flex items-center justify-center">{i + 1}</span>
                            <span className="text-sm text-brand-ink leading-snug">{s}</span>
                        </li>
                    ))}
                </ol>
                <button type="button" onClick={hide} aria-label="Hide this guide"
                        className="shrink-0 -m-2 w-11 h-11 inline-flex items-center justify-center rounded-lg text-gray-600 hover:text-gray-900 hover:bg-white/70">
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
        <section className={`bg-white rounded-2xl border border-gray-200/70 shadow-sm p-5 min-w-0 ${className}`}>
            <div className="flex items-start justify-between gap-3 mb-4">
                <div className="min-w-0">
                    <h2 className="text-base font-bold text-brand-ink flex items-center gap-2">
                        {step !== undefined && (
                            <span className="w-6 h-6 rounded-full bg-brand-soft text-brand text-xs font-bold flex items-center justify-center">{step}</span>
                        )}
                        {title}
                    </h2>
                    {hint && <p className="text-xs text-gray-600 mt-1">{hint}</p>}
                </div>
                {actions}
            </div>
            {children}
        </section>
    );
}

export function StatCard({ label, value, hint, tone = "default", onClick }: {
    label: string, value: ReactNode, hint?: string, tone?: "default" | "brand" | "warn" | "good", onClick?: () => void
}) {
    const toneCls = {
        default: "text-brand-ink",
        brand: "text-brand",
        warn: "text-amber-700",
        good: "text-emerald-700",
    }[tone];
    const Tag = onClick ? "button" : "div";
    return (
        <Tag type={onClick ? "button" : undefined} onClick={onClick}
             className={`text-left bg-white rounded-2xl border border-gray-200/70 shadow-sm p-3 sm:p-5 min-w-0 ${onClick ? "hover:border-brand/40 hover:shadow focus-visible:outline-2 focus-visible:outline-brand transition" : ""}`}>
            <p className="text-xs sm:text-sm font-medium text-gray-600 leading-snug">{label}</p>
            <p className={`text-2xl sm:text-3xl font-bold tabular-nums mt-1 ${toneCls}`}>{value}</p>
            {hint && <p className="hidden sm:block text-xs text-gray-600 mt-1">{hint}</p>}
        </Tag>
    );
}

/** Collapsed-by-default technical detail, so cards show the essentials first. */
export function Details({ label = "Details", open, children }: { label?: string, open?: boolean, children: ReactNode }) {
    return (
        <details className="group mt-3" open={open}>
            <summary className="inline-flex items-center gap-1 text-xs font-medium text-gray-600 hover:text-gray-900 cursor-pointer select-none list-none min-h-[44px]">
                <ChevronDown className="w-3.5 h-3.5 transition-transform group-open:rotate-180" /> {label}
            </summary>
            <div className="mt-2 text-xs text-gray-600 space-y-1">{children}</div>
        </details>
    );
}

export function Chip({ children, tone = "gray" }: { children: ReactNode, tone?: "gray" | "amber" | "blue" | "green" }) {
    const cls = {
        gray: "border-gray-300 text-gray-600 bg-white",
        amber: "border-amber-400 text-amber-800 bg-amber-50",
        blue: "border-brand/30 text-brand bg-brand-soft",
        green: "border-emerald-300 text-emerald-800 bg-emerald-50",
    }[tone];
    return <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full border whitespace-nowrap ${cls}`}>{children}</span>;
}

export function RiskBadge({ tier, score, size = "sm" }: { tier?: string | null, score?: number | null, size?: "sm" | "lg" }) {
    const t = tier ? TIER[tier] : null;
    if (!t || score === null || score === undefined) {
        return <span className="text-xs font-medium text-gray-600 animate-pulse motion-reduce:animate-none whitespace-nowrap">Scoring…</span>;
    }
    return (
        <span aria-label={`${t.label} risk, ${score} out of 100`}
              className={`inline-flex items-center gap-1.5 rounded-full font-bold whitespace-nowrap tabular-nums ${t.cls} ${size === "lg" ? "px-3.5 py-1.5 text-base" : "px-2.5 py-0.5 text-xs"}`}>
            <span aria-hidden="true">{t.shape}</span>{t.label} {score}
        </span>
    );
}

const READ_BY: Record<string, { label: string, tone: "blue" | "gray" | "amber" }> = {
    ai: { label: "Read by AI", tone: "blue" },
    rules: { label: "Read by rules", tone: "amber" },
    recorded: { label: "Recorded sample", tone: "gray" },
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
        <span className={`text-sm font-bold tabular-nums whitespace-nowrap ${down ? "text-emerald-700" : "text-red-600"}`}
              aria-label={down ? `risk down ${-delta} points` : `risk up ${delta} points`}>
            {down ? "▼" : "▲"}{Math.abs(delta)}
        </span>
    );
}

export function Empty({ title, children }: { title: string, children?: ReactNode }) {
    return (
        <div className="text-center py-10 px-4">
            <p className="font-semibold text-brand-ink">{title}</p>
            {children && <div className="text-sm text-gray-600 mt-1 max-w-prose mx-auto">{children}</div>}
        </div>
    );
}

export function LoadError({ what, onRetry }: { what: string, onRetry?: () => void }) {
    return (
        <div role="alert" className="rounded-2xl border border-red-200 bg-red-50 text-red-800 text-sm p-4 flex flex-wrap items-center justify-between gap-3">
            <span>Could not load {what}. Check that the Wasel server is running, then {onRetry ? "try again." : "refresh the page."}</span>
            {onRetry && (
                <button type="button" onClick={onRetry}
                        className="min-h-[44px] px-4 rounded-xl bg-white border border-red-300 font-medium text-red-900 hover:bg-red-100">
                    Retry
                </button>
            )}
        </div>
    );
}
