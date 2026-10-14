"use client";

import { Fragment, useCallback, useEffect, useRef, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Check, Lock, MapPin, X, ShieldAlert } from 'lucide-react';
import { ordersApi } from '@/lib/api/orders';
import type {
    AdjustmentView, AssessmentView, DraftJudge, DraftView, FactorView, FlagView, HealthResponse, MessageView,
    OrderDetailResponse, OrderSummary, Segment,
} from '@/lib/api/types';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import {
    Page, Section, Details, Chip, ReadBy, RiskBadge, Delta, Empty, TIER, NEXT_STEP, STATUS, whenLabel, tnd,
} from '@/components/wasel/kit';

// Server-built strings (reasons, flag labels) are shown verbatim.
const SELLER_ACTIONS: Record<string, string> = {
    approve: "Approve for shipping",
    request_confirmation: "Ask the customer to confirm",
    ship: "Mark as shipped",
    mark_delivered: "Mark as delivered",
    mark_refused: "Refused at the door",
    cancel: "Cancel order",
};

// Primary action per status: exactly one filled button.
const PRIMARY_BY_STATUS: Record<string, string> = {
    needs_review: "approve",
    ready_to_ship: "ship",
    shipped: "mark_delivered",
};

// What the seller should do now, in one sentence, per status.
const GUIDANCE: Record<string, string> = {
    awaiting_reply: "Send the drafted question below, then wait for the customer's answer. Wasel rescores as soon as they reply.",
    needs_review: "Wasel is not sure about this one. Read the conversation, then approve it or ask the customer to confirm.",
    ready_to_ship: "This order looks safe. Ship it.",
    shipped: "On its way. Record what happened at the door.",
    delivered: "Delivered. Nothing left to do.",
    refused: "Refused at the door. Nothing left to do.",
    cancelled: "Cancelled. Nothing left to do.",
    collecting: "Not an order yet: the messages don't mention a product or a delivery address. Wasel scores it as soon as they do.",
};

const TRIGGER: Record<string, string> = {
    initial: "First score",
    customer_reply: "After the customer replied",
    no_reply_timeout: "Customer didn't reply",
    manual: "Rescored by you",
};

const PATH: Record<string, string> = {
    llm: "AI extraction",
    fallback_model: "Backup AI model",
    fallback_provider: "Backup AI provider (Gemini)",
    cascade_ack: "Short reply, no AI call",
    cascade_cache: "Recorded AI result, no new AI call",
    rules: "Rules only, no AI",
};

const FLAG: Record<string, string> = {
    availability_uncertain: "May not be home",
    vague_location: "Vague location",
    price_hesitation: "Hesitates on price",
    third_party_recipient: "Someone else receives it",
    prior_refusal_mention: "Refused before",
    pressure_or_inconsistency: "Pressure or inconsistency",
};

const LANGUAGE: Record<string, string> = {
    arabizi: "Arabizi", darija_arabic_script: "Darija (Arabic script)", ar: "Arabic", fr: "French", mixed: "Mixed",
};

const RESCORE: Record<string, string> = {
    debouncing: "Wasel is rereading the conversation…",
    scoring: "Rescoring…",
    drafting: "Drafting the reply…",
};

// 7200 -> "2 hours", 5400 -> "90 minutes"
const spanWords = (s: number) => s % 3600 === 0 ? `${s / 3600} hour${s === 3600 ? "" : "s"}` : `${Math.round(s / 60)} minutes`;

// Server segments: text nodes only, no HTML; the join of segment texts equals the message text.
function Segments({ segments }: { segments: Segment[] }) {
    return <>{segments.map((s, i) => s.kind
        ? <mark key={i} tabIndex={0} title={s.label ?? ""}
                className={s.kind === "risk"
                    ? "bg-amber-200 text-amber-950 underline decoration-dotted decoration-2 underline-offset-2 decoration-amber-600 rounded-sm"
                    : s.kind === "partial"
                        ? "bg-transparent text-gray-900 border-b-2 border-dashed border-gray-500"
                        : "bg-transparent text-gray-900 border-b-2 border-emerald-600"}>
            {s.text}<span className="sr-only"> ({s.label})</span>
        </mark>
        : <Fragment key={i}>{s.text}</Fragment>)}</>;
}

// resolved_flags can come back empty even when reason_diff lists resolved signs: fall back to the
// previous version's flag codes that are gone from this one.
// Assessment cards with the warning signs this version resolved (computed from the previous version when the API leaves it empty).
type AssessmentCard = AssessmentView & { resolved: string[] };

function resolvedFlags(a: AssessmentView, prev: AssessmentView | undefined): string[] {
    if (a.resolved_flags?.length) return a.resolved_flags;
    if (!prev) return [];
    const now = new Set<string>((a.flags || []).map(f => f.code));
    return [...new Set<string>((prev.flags || []).map(f => f.code))].filter(c => !now.has(c));
}

const stripTier = (s?: string | null) => (s || "").replace(/^(HIGH|MEDIUM|LOW) \d+ · /, "");

function ScoreHistory({ assessments, rescoreState }: { assessments: AssessmentView[], rescoreState: string }) {
    const cards: AssessmentCard[] = assessments.map((a, i) => ({ ...a, resolved: resolvedFlags(a, assessments[i - 1]) })).reverse();
    return (
        <ol className="space-y-3">
            <li aria-live="polite" className="list-none">
                {rescoreState !== "idle" && (
                    <div className="rounded-xl border-2 border-dashed border-gray-300 p-3 text-sm text-gray-600 animate-pulse motion-reduce:animate-none">
                        {RESCORE[rescoreState] ?? "Rescoring…"}
                    </div>
                )}
            </li>
            {cards.map((a: AssessmentCard) => (
                <li key={a.assessment_id} className="rounded-xl border border-gray-200 p-3">
                    <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-semibold text-gray-700">
                            v{a.version} · {TRIGGER[a.trigger] ?? a.trigger} · {whenLabel(a.created_at)}
                        </span>
                        <span className="flex items-center gap-2">
                            <ReadBy value={a.read_by} />
                            <RiskBadge tier={a.tier} score={a.final_score} />
                            <Delta delta={a.delta} />
                        </span>
                    </div>
                    {a.resolved.length > 0 && (
                        <p className="text-sm text-emerald-800 mt-2 flex items-start gap-1.5">
                            <Check className="w-4 h-4 mt-0.5 shrink-0" />
                            Resolved: {a.resolved.map((f: string) => FLAG[f] ?? f).join(", ")}
                        </p>
                    )}
                    {a.flags?.length > 0 && (
                        <p className="text-sm text-gray-700 mt-2">
                            Warning signs: {a.flags.map((f: FlagView, i: number) => (
                                <span key={i}>{i > 0 && ", "}{FLAG[f.code] ?? f.label} (“<bdi dir="auto">{f.quote}</bdi>”)</span>
                            ))}
                        </p>
                    )}
                    {a.rules_alone && (a.rules_alone.tier !== a.tier || a.rules_alone.final_score !== a.final_score) && (
                        <p className="text-xs text-gray-700 mt-2 rounded-lg bg-gray-50 border border-gray-200 px-2.5 py-1.5">
                            <span className="font-semibold">What the rules alone would have said:</span>{" "}
                            {(TIER[a.rules_alone.tier]?.label ?? a.rules_alone.tier)} {a.rules_alone.final_score}
                            {a.rules_alone.tier !== a.tier ? ` (the AI read gave ${TIER[a.tier]?.label ?? a.tier} ${a.final_score})` : ""}
                            {a.rules_alone.reason_short ? `. ${stripTier(a.rules_alone.reason_short)}` : ""}
                        </p>
                    )}
                    {a.path === "rules" && (
                        <p className="text-xs text-gray-600 mt-2">Scored by simple rules, not the AI. This read is coarser, so treat the tier as a rough guide.</p>
                    )}
                    <Details>
                        <p>{a.reason_diff || stripTier(a.reason)}</p>
                        {a.adjustments?.length > 0 && (
                            <p className="font-mono">
                                Model {Math.round(a.model_score)}
                                {a.adjustments.map((adj: AdjustmentView, i: number) => <span key={i}> → {adj.label} ({adj.effect})</span>)}
                                {" "}→ {a.final_score}
                            </p>
                        )}
                        <p>
                            {a.extraction?.cache_hit ? PATH.cascade_cache : (PATH[a.path] ?? a.path)}
                            {a.extraction?.model && !a.extraction?.cache_hit ? ` · ${a.extraction.provider}:${a.extraction.model}` : ""}
                            {a.confidence === "low" ? " · low confidence" : ""}
                        </p>
                    </Details>
                </li>
            ))}
        </ol>
    );
}

function SimulateReplyPanel({ conversationId, scripted, hasUnsentDraft, onSent }: {
    conversationId: string; scripted: string[]; hasUnsentDraft: boolean; onSent: () => void
}) {
    const [replyText, setReplyText] = useState("");
    const [sending, setSending] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSend = async () => {
        if (!replyText.trim()) return;
        setSending(true);
        setError(null);
        try {
            await ordersApi.simulateTextReply(conversationId, replyText.trim());
            setReplyText("");
            onSent();
        } catch (err: any) {
            setError(err?.message || "Could not send the simulated reply.");
        }
        setSending(false);
    };

    return (
        <details className="group bg-white rounded-2xl border-2 border-dashed border-gray-300 p-5" open={scripted.length > 0}>
            <summary className="cursor-pointer list-none select-none">
                <span className="text-sm font-bold text-brand-ink">
                    <span className="text-xs font-bold bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded mr-2">TRY IT</span>
                    Play the customer
                </span>
                <span className="block text-xs text-gray-600 mt-1">
                    Type the customer's reply to see Wasel rescore the order. It goes through the same steps as a real WhatsApp message and is marked “Simulated”.
                </span>
            </summary>
            <div className="mt-4 space-y-3">
                {scripted.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                        {scripted.map((s, i) => (
                            <button key={i} type="button" title={s} onClick={() => setReplyText(s)}
                                    className="text-xs px-3 min-h-[44px] rounded-full border border-gray-300 text-gray-700 hover:bg-gray-50 max-w-full truncate">
                                Scripted: {s.length > 60 ? s.slice(0, 60) + "…" : s}
                            </button>
                        ))}
                    </div>
                )}
                {hasUnsentDraft && (
                    <p className="text-xs text-brand">
                        The message to the customer hasn't been sent yet. Your reply records it as sent first, so the reply answers it.
                    </p>
                )}
                <label className="block">
                    <span className="sr-only">Customer reply</span>
                    <textarea
                        dir="auto"
                        rows={3}
                        maxLength={600}
                        value={replyText}
                        onChange={e => setReplyText(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSend(); }}
                        placeholder="Type what the customer would reply…"
                        className="w-full px-3 py-2 rounded-xl border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-brand/30 focus:border-brand"
                        disabled={sending}
                    />
                </label>
                <div className="flex items-center justify-between">
                    <span className={`text-xs ${error ? "text-red-700" : "text-gray-600"}`}>{error ?? `${replyText.length} / 600`}</span>
                    <Button size="sm" variant="outline" disabled={sending || !replyText.trim()} onClick={handleSend}>
                        {sending ? "Sending…" : "Send simulated reply"}
                    </Button>
                </div>
            </div>
        </details>
    );
}

// The draft guard (docs/subsystems/outbound.md): rules -> local classifier decision -> AI judge.
// Drafts from before the classifier change carry no `decision`: shown as not applicable, never a crash.
const DECISION: Record<string, { label: string, tone: "green" | "amber" | "gray" }> = {
    send: { label: "Clear to send", tone: "green" },
    review: { label: "Owner approval", tone: "amber" },
    block: { label: "Blocked", tone: "amber" },
};
const ROUTE_TEXT: Record<string, string> = {
    auto_send: "Cleared by the checks. It would go out without a click, but automatic sending is off on this server.",
    needs_review: "Waiting for your approval: you decide when it is sent.",
    blocked: "Blocked by the checks: the standard message is used instead.",
};

function DraftChecks({ draft, autoSend }: { draft: DraftView, autoSend: boolean }) {
    const j: DraftJudge = draft.judge || {};
    const clf: NonNullable<DraftJudge['classifier']> = j.classifier || {};
    const decision = clf.decision ? DECISION[clf.decision] : null;
    const rewrite = draft.source === "llm_rewrite";
    const judge = !rewrite ? null
        : j.unavailable ? { label: "AI judge unavailable", tone: "gray" as const }
        : j.decided_by === "llm" ? (j.approved ? { label: "AI judge approved", tone: "green" as const } : { label: "AI judge rejected", tone: "amber" as const })
        : null;
    return (
        <div className="mt-3 space-y-2">
            <div className="flex flex-wrap items-center gap-2 text-xs">
                {draft.prefilter?.passed
                    ? <Chip tone="green"><Check className="w-3 h-3" /> Rule checks passed</Chip>
                    : (draft.prefilter?.failures || []).map((f: string) => <Chip key={f} tone="amber"><X className="w-3 h-3" /> {f}</Chip>)}
                {rewrite && (decision
                    ? <Chip tone={decision.tone}>{decision.label}</Chip>
                    : <Chip>Classifier: n/a</Chip>)}
                {judge && <Chip tone={judge.tone}>{judge.label}</Chip>}
                <span className="text-gray-600">{rewrite ? "AI-adapted wording" : "Standard approved wording"}</span>
            </div>
            {rewrite && ROUTE_TEXT[draft.route] && !draft.sent_message_id && (
                <p className="text-xs text-gray-700">
                    {draft.route === "auto_send" && autoSend
                        ? "Cleared by the checks: Wasel sends it automatically within a few seconds. You can also send it now."
                        : ROUTE_TEXT[draft.route]}
                </p>
            )}
            {clf.decision === "send" && draft.route === "needs_review" && !draft.sent_message_id && (
                <p className="text-xs text-gray-700">The safety model cleared the wording, but another rule keeps it for you: a high price, low confidence in the score, or too many automatic messages already.</p>
            )}
            {clf.decision === "review" && (
                <p className="text-xs text-amber-800">Owner approval: the safety model has doubts about this wording, so it waits for you even if the AI judge approved it.</p>
            )}
            {rewrite && (
                <Details label="How this message was checked">
                    <p>1. Rules: numbers, links, phone numbers, payment or discount words, one question only.</p>
                    <p>2. Safety model (runs locally, no AI service): risk {typeof clf.p_unsafe === "number" ? `${Math.round(clf.p_unsafe * 100)}%` : "n/a"}
                        {clf.label && clf.label !== "ok" ? `, looks like: ${String(clf.label).replace(/_/g, " ")}` : ""}.
                        {typeof clf.hold_at === "number" && typeof clf.block_at === "number"
                            ? ` Below ${Math.round(clf.hold_at * 100)}% it's cleared, ${Math.round(clf.hold_at * 100)}–${Math.round(clf.block_at * 100)}% goes to you for approval, above ${Math.round(clf.block_at * 100)}% it's blocked and the standard message is used.`
                            : ""}</p>
                    <p>3. AI judge: {j.unavailable
                        ? `unavailable (${j.reason ?? "no answer"}), ${clf.decision === "send" ? "sent on the safety model's clear" : "a person must check it"}.`
                        : j.decided_by === "llm" ? `${j.approved ? "approved" : "rejected"}${j.judge_model ? ` by ${j.judge_model}` : ""}; the decision is re-checked in code.`
                        : "not reached (the safety model decided)."}</p>
                    {(j.unsupported_claims ?? []).length > 0 && <p>Claims the order doesn't support: {(j.unsupported_claims ?? []).join("; ")}</p>}
                    {draft.canonical_text && <p>Adapted from the approved message: <bdi dir="auto">{draft.canonical_text}</bdi></p>}
                </Details>
            )}
        </div>
    );
}

function OrderDetailContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const [orderId, setOrderId] = useState<string | null>(searchParams.get('id'));
    const [orderData, setOrderData] = useState<OrderDetailResponse | null>(null);
    const [allOrders, setAllOrders] = useState<OrderSummary[]>([]);
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [notFound, setNotFound] = useState(false);
    const [busy, setBusy] = useState<string | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const fastUntil = useRef(0);
    // The id the page opened with: decides, once on mount, whether to select the newest order.
    const openedWithId = useRef(orderId);

    const loadList = useCallback(() => ordersApi.getOrders({ include_collecting: true }).then((res) => {
        setAllOrders(res.orders || []);
        return res.orders || [];
    }), []);

    const loadOrder = useCallback(async (id: string) => {
        try {
            const res = await ordersApi.getOrder(id);
            setOrderData(res);
            setNotFound(false);
        } catch (err: any) {
            if (err?.status === 404) setNotFound(true);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        ordersApi.health().then(setHealth).catch(() => {});
        loadList().then((orders: OrderSummary[]) => {
            if (!openedWithId.current && orders.length > 0) {
                const firstId = orders[0].order_id;
                setOrderId(firstId);
                router.replace(`/dashboard/order?id=${firstId}`);
            }
        }).catch(() => setLoading(false));
    }, [loadList, router]);

    // Poll the selected order: 1 s while it is rescoring (or right after a reply/Try), else 3 s.
    useEffect(() => {
        if (!orderId) return;
        let stop = false;
        let timer: ReturnType<typeof setTimeout>;
        const tick = async () => {
            if (!document.hidden) await loadOrder(orderId);
            if (stop) return;
            timer = setTimeout(tick, Date.now() < fastUntil.current ? 1000 : 3000);
        };
        setLoading(true);
        tick();
        return () => { stop = true; clearTimeout(timer); };
    }, [orderId, loadOrder]);

    // Stay on the fast cadence while the backend reports a rescore in progress.
    const rescoreState = orderData?.order?.rescore_state ?? "idle";
    useEffect(() => {
        if (rescoreState !== "idle") fastUntil.current = Math.max(fastUntil.current, Date.now() + 5000);
    }, [rescoreState, orderData]);

    const selectOrder = (id: string) => {
        setOrderId(id);
        setOrderData(null);
        router.push(`/dashboard/order?id=${id}`);
    };

    const run = async (key: string, fn: () => Promise<any>) => {
        setBusy(key);
        setActionError(null);
        try {
            const res = await fn();
            fastUntil.current = Date.now() + 60000;
            if (orderId) await loadOrder(orderId);
            loadList();
            return res;
        } catch (err: any) {
            setActionError(err?.data?.error?.message || err?.message || "That didn't work. Try again.");
        } finally {
            setBusy(null);
        }
    };

    if (loading && !orderData) return <Page><p className="text-gray-600">Loading the order…</p></Page>;
    if (notFound) return (
        <Page>
            <Empty title="This order is no longer available">
                Copies you made with “Try this order” are deleted after {health?.sandbox_ttl_s ? spanWords(health.sandbox_ttl_s) : "a while"}.
                <div className="mt-4"><Button variant="outline" onClick={() => router.push('/dashboard')}>Back to orders</Button></div>
            </Empty>
        </Page>
    );
    if (!orderData) return <Page><Empty title="No order selected">Pick an order from “Orders to check”.</Empty></Page>;

    const { order: o, assessments, customer, drafts, scripted_replies, capabilities, conversation } = orderData;
    const latest = assessments?.length ? assessments[assessments.length - 1] : null;
    const messages = [...(conversation?.messages || [])].sort((a: MessageView, b: MessageView) => a.provider_ts.localeCompare(b.provider_ts));
    const currentDraft = [...(drafts || [])].reverse().find((d: DraftView) => d.route !== "blocked") ?? null;
    const unsentDraft = currentDraft && !currentDraft.sent_message_id ? currentDraft : null;
    const waSend = health?.wa_send === true;
    const primary = capabilities?.read_only ? null : PRIMARY_BY_STATUS[o.status];
    const tier = o.score?.tier ? TIER[o.score.tier] : null;
    const history = customer.completed_orders || customer.refusals_total
        ? `${customer.completed_orders} delivered, ${customer.refusals_total} refused before`
        : "New customer";

    return (
        <Page>
            {/* Header: who and what */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                <div className="min-w-0 space-y-1">
                    <Link prefetch={false} href="/dashboard" className="inline-flex items-center gap-1 text-sm font-medium text-brand hover:underline min-h-[44px]">
                        <ArrowLeft className="w-4 h-4" /> All orders
                    </Link>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                        <h1 className="text-2xl font-bold text-brand-ink tabular-nums">{o.order_ref}</h1>
                        <bdi className="text-lg text-gray-800 truncate">{customer.display_name || "Unnamed customer"}</bdi>
                        {capabilities?.read_only && <Chip><Lock className="w-3 h-3" /> Example order</Chip>}
                        {!o.is_seeded && o.seed_key && <Chip tone="blue">Your copy</Chip>}
                    </div>
                    <p className="text-sm text-gray-600">
                        {[o.product_name ? `${o.product_name}${(o.quantity ?? 0) > 1 ? ` × ${o.quantity}` : ""}` : null,
                          o.price_tnd != null ? tnd(o.price_tnd) : null,
                          o.zone ? `${o.zone} zone${o.zone_source === "default" ? " (assumed)" : ""}` : null,
                          history].filter(Boolean).join(" · ")}
                    </p>
                </div>
                <Select value={orderId || ""} onValueChange={selectOrder}>
                    <SelectTrigger className="w-full md:w-[280px] h-11 bg-white" aria-label="Switch order">
                        <SelectValue placeholder="Switch order" />
                    </SelectTrigger>
                    <SelectContent>
                        {allOrders.map((ord: OrderSummary) => (
                            <SelectItem key={ord.order_id} value={ord.order_id}>
                                {ord.order_ref} · {ord.customer?.display_name || '?'} · {ord.score ? `${TIER[ord.score.tier]?.label} ${ord.score.final_score}` : 'scoring'}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
            </div>

            {/* Verdict: the one thing to do now */}
            <section aria-label="Verdict" className="bg-white rounded-2xl border border-gray-200/70 shadow-sm p-5 flex flex-col xl:flex-row xl:items-center gap-5">
                <div className="flex items-center gap-4 shrink-0">
                    <RiskBadge tier={o.score?.tier} score={o.score?.final_score} size="lg" />
                    <Delta delta={o.score?.delta} />
                    <ReadBy value={o.score?.read_by} />
                </div>
                <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold uppercase tracking-wider text-gray-600">{STATUS[o.status]}</p>
                    <p className="text-lg font-bold text-brand-ink">
                        {o.score ? NEXT_STEP[o.score.action] ?? o.score.action : "Nothing to score yet"}
                    </p>
                    <p className="text-sm text-gray-600 mt-0.5 max-w-prose">
                        {capabilities?.read_only
                            ? "Make your own copy to reply to this order and send messages."
                            : GUIDANCE[o.status] ?? tier?.meaning}
                    </p>
                    {o.injection_suspected && (
                        <p className="mt-2 text-sm text-amber-800 flex items-start gap-1.5">
                            <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" />
                            The customer's message contains an instruction aimed at the AI. Wasel ignored it, but check this order yourself.
                        </p>
                    )}
                    {actionError && <p role="alert" className="text-sm text-red-700 mt-2">{actionError}</p>}
                </div>
                <div className="flex flex-wrap gap-2 xl:justify-end xl:max-w-[420px]">
                    {capabilities?.can_try && (
                        <Button className="bg-brand hover:bg-brand-hover text-white min-h-[44px]" disabled={busy !== null}
                                onClick={async () => {
                                    const res = await run("try", () => ordersApi.tryOrder(o.order_id));
                                    if (res?.order_id) selectOrder(res.order_id);
                                }}>
                            {busy === "try" ? "Copying…" : "Try this order"}
                        </Button>
                    )}
                    {capabilities?.can_try && scripted_replies?.length > 0 && (
                        <Button variant="outline" className="min-h-[44px]" disabled={busy !== null}
                                onClick={async () => {
                                    // one click: copy the sample, send the scripted reply to the copy, open the copy while Wasel rereads it
                                    const copy = await run("try", () => ordersApi.tryOrder(o.order_id));
                                    if (!copy?.order_id) return;
                                    const answered = await run("answer", () => ordersApi.simulateTextReply(copy.conversation_id, scripted_replies[0]));
                                    if (answered) selectOrder(copy.order_id);
                                }}>
                            {busy === "try" || busy === "answer" ? "Working…" : `See what happens when ${(customer?.display_name || "the customer").split(" ")[0]} answers`}
                        </Button>
                    )}
                    {unsentDraft && capabilities?.can_send_drafts && (
                        <Button className="bg-brand hover:bg-brand-hover text-white min-h-[44px]" disabled={busy !== null}
                                onClick={() => document.getElementById("message-to-customer")?.scrollIntoView({ behavior: "smooth", block: "center" })}>
                            Review the message ↓
                        </Button>
                    )}
                    {capabilities?.actions?.map((act: string) => {
                        const isPrimary = act === primary && !unsentDraft;
                        return (
                            <Button key={act} disabled={busy !== null} variant={isPrimary ? "default" : "outline"}
                                    className={`min-h-[44px] ${isPrimary ? 'bg-brand hover:bg-brand-hover text-white' : ''}`}
                                    onClick={() => {
                                        if ((act === "cancel" || act === "mark_refused") && !window.confirm(`${SELLER_ACTIONS[act]}?`)) return;
                                        run(act, () => ordersApi.takeAction(o.order_id, act));
                                    }}>
                                {busy === act ? "Working…" : (SELLER_ACTIONS[act] || act)}
                            </Button>
                        );
                    })}
                </div>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1.45fr)_minmax(0,1fr)] gap-6 items-start">
                {/* Left: read, then message */}
                <div className="flex flex-col gap-6 min-w-0">
                    <Section step={1} title="What the customer said"
                             hint="Highlighted words are what Wasel noticed. Hover or focus a highlight to see why.">
                        <div className="bg-wa-bg rounded-xl p-4 max-h-[460px] overflow-y-auto">
                            {messages.length > 0 ? (
                                <div className="flex flex-col gap-2">
                                    {messages.map((m: MessageView) => {
                                        const isCustomer = m.author === 'customer';
                                        const sentDraft = (drafts || []).find((d: DraftView) => d.sent_message_id === m.message_id);
                                        return (
                                            <div key={m.message_id} className={`flex flex-col max-w-[85%] ${isCustomer ? 'self-start' : 'self-end'}`}>
                                                <div className={`p-3 rounded-2xl ${isCustomer ? 'bg-white rounded-bl-sm' : 'bg-wa-out rounded-br-sm'} text-gray-900 shadow-sm`}>
                                                    <p dir="auto" className="whitespace-pre-wrap break-words leading-relaxed text-start">
                                                        {m.segments ? <Segments segments={m.segments} />
                                                            : m.text ?? (m.location
                                                                ? <span className="inline-flex items-center gap-1"><MapPin className="w-4 h-4" /> Location pin {m.location.lat.toFixed(4)}, {m.location.lng.toFixed(4)}</span>
                                                                : `[${m.kind} message]`)}
                                                    </p>
                                                    <div className="text-xs mt-1 text-gray-600 flex items-center gap-1.5 flex-wrap">
                                                        <span>{whenLabel(m.provider_ts)}</span>
                                                        {!isCustomer && <span>· {sentDraft?.source === "llm_rewrite" ? "AI-adapted message" : sentDraft ? "Standard message" : "You"}</span>}
                                                        {!isCustomer && sentDraft?.decided_by === "system" && <Chip tone="blue">Sent automatically</Chip>}
                                                        {m.origin === "simulated" && <Chip tone="amber">Simulated</Chip>}
                                                        {m.origin === "paste" && <Chip>Pasted</Chip>}
                                                        {m.origin === "whatsapp" && isCustomer && <Chip tone="green">WhatsApp</Chip>}
                                                        {!isCustomer && (m.origin === "dashboard" || m.origin === "simulated") && <span>· Sent (simulated)</span>}
                                                        {!isCustomer && m.origin === "whatsapp" && m.delivery_status && <span>· {m.delivery_status}</span>}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <p className="text-sm text-gray-600 text-center py-8">No messages yet.</p>
                            )}
                        </div>
                        <p className="mt-3 text-xs text-gray-600 flex flex-wrap gap-x-4 gap-y-1">
                            <span><mark className="bg-amber-200 text-amber-950 px-1 rounded-sm underline decoration-dotted decoration-2 underline-offset-2 decoration-amber-600">amber</mark> raised the risk</span>
                            <span><span className="border-b-2 border-emerald-600">green underline</span> address detail found</span>
                            <span><span className="border-b-2 border-dashed border-gray-500">grey dashed</span> address not exact enough</span>
                        </p>
                    </Section>

                    {currentDraft && (
                        <div id="message-to-customer">
                            <Section step={2} title="Message to the customer"
                                     hint={`Written in ${LANGUAGE[currentDraft.language] ?? currentDraft.language}, the customer's own language.`}>
                                <p dir="auto" className="text-sm text-gray-900 whitespace-pre-wrap break-words bg-gray-50 rounded-xl p-4 border border-gray-200">
                                    {currentDraft.text}
                                </p>
                                <DraftChecks draft={currentDraft} autoSend={health?.wa_auto_send === true} />
                                {unsentDraft ? (
                                    capabilities?.can_send_drafts ? (
                                        <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-t border-gray-100 pt-4">
                                            <p className="text-xs text-gray-600 max-w-prose">
                                                {waSend ? "Sends this message to the customer on WhatsApp."
                                                    : "Sending adds the message to the conversation."}
                                            </p>
                                            <Button disabled={busy !== null} className="bg-brand hover:bg-brand-hover text-white min-h-[44px] shrink-0"
                                                    onClick={() => run("send", () => ordersApi.sendDraft(unsentDraft.draft_id))}>
                                                {busy === "send" ? "Sending…" : "Send message"}
                                            </Button>
                                        </div>
                                    ) : (
                                        <p className="mt-4 text-xs text-gray-600">Use “Try this order” to work on your own copy.</p>
                                    )
                                ) : (
                                    <p className="mt-4 text-sm text-emerald-800 flex items-center gap-1.5">
                                        <Check className="w-4 h-4" />
                                        {currentDraft.decided_by === "system" ? "Sent automatically" : "Sent"}{currentDraft.delivery === "recorded_only" ? " (simulated)" : " on WhatsApp"} at {whenLabel(currentDraft.sent_at)}
                                    </p>
                                )}
                            </Section>
                        </div>
                    )}

                    {capabilities?.can_simulate_reply && conversation?.conversation_id && (
                        <SimulateReplyPanel
                            conversationId={conversation.conversation_id}
                            scripted={scripted_replies || []}
                            hasUnsentDraft={!!unsentDraft}
                            onSent={() => {
                                fastUntil.current = Date.now() + 60000;
                                if (orderId) loadOrder(orderId);
                            }}
                        />
                    )}
                </div>

                {/* Right: why, then how it changed */}
                <div className="flex flex-col gap-6 min-w-0">
                    <Section title="Why this score" hint="The main reasons, biggest first. Red raises the risk, green lowers it.">
                        {latest ? (
                            <>
                                {latest.top_factors?.length > 0 ? (
                                    <ul className="space-y-3">
                                        {latest.top_factors.slice(0, 4).map((f: FactorView, idx: number) => {
                                            const isRisk = f.contribution > 0;
                                            return (
                                                <li key={idx}>
                                                    <div className="flex justify-between gap-3 text-sm mb-1">
                                                        <span className="text-gray-800 min-w-0 break-words">{f.label}</span>
                                                        <span className={`font-semibold tabular-nums shrink-0 ${isRisk ? 'text-red-700' : 'text-emerald-700'}`}>
                                                            {isRisk ? '+' : '−'}{Math.abs(f.contribution).toFixed(0)}
                                                        </span>
                                                    </div>
                                                    <div className="w-full bg-gray-100 rounded-full h-1.5" aria-hidden="true">
                                                        <div className={`h-1.5 rounded-full ${isRisk ? 'bg-red-500' : 'bg-emerald-500'}`}
                                                             style={{ width: `${Math.min(Math.abs(f.contribution) * 2.5, 100)}%` }} />
                                                    </div>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                ) : <p className="text-sm text-gray-700">{stripTier(latest.reason)}</p>}
                                <Details label="Full explanation">
                                    <p>{latest.reason}</p>
                                </Details>
                            </>
                        ) : (
                            <p className="text-sm text-gray-600">{rescoreState !== "idle" ? "Scoring…" : GUIDANCE.collecting}</p>
                        )}
                    </Section>

                    {(assessments?.length > 0 || rescoreState !== "idle") && (
                        <Section title="Score history" hint="Every time the customer writes, Wasel scores the order again.">
                            <ScoreHistory assessments={assessments || []} rescoreState={rescoreState} />
                        </Section>
                    )}

                    {capabilities?.can_rescore && (
                        <button type="button" disabled={busy !== null}
                                onClick={() => run("rescore", () => ordersApi.rescoreOrder(o.order_id))}
                                className="self-start text-xs font-medium text-gray-600 hover:text-brand hover:underline min-h-[44px]">
                            {busy === "rescore" ? "Rescoring…" : "Rescore this order now"}
                        </button>
                    )}
                </div>
            </div>
        </Page>
    );
}

export default function OrderDetailPage() {
    return (
        <Suspense fallback={<Page><p className="text-gray-600">Loading…</p></Page>}>
            <OrderDetailContent />
        </Suspense>
    );
}
