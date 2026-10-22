"use client";

import { useEffect, useRef, useState } from "react";
import { ordersApi } from "@/lib/api/orders";
import { AlertTriangle, WifiOff, Loader2 } from "lucide-react";
import { useT } from "@/lib/i18n";

// A first answer later than this means the free host is waking up: say so instead of showing nothing.
const WAKING_AFTER_MS = 3000;

// One short status pill; the technical detail sits in the tooltip. Problems (server down, waking up) get a full-width banner.
export function HealthBar() {
    const [health, setHealth] = useState<any>(null);
    const [down, setDown] = useState(false);
    const [waking, setWaking] = useState(false);
    const seenUp = useRef(false);
    const { t } = useT();

    useEffect(() => {
        const load = () => ordersApi.health().then(h => { seenUp.current = true; setHealth(h); setDown(false); }).catch(() => setDown(true));
        load();
        const iv = setInterval(load, 10000);
        const slow = setTimeout(() => setWaking(true), WAKING_AFTER_MS);
        return () => { clearInterval(iv); clearTimeout(slow); };
    }, []);

    if (down) {
        return (
            <div role="status" className="w-full flex items-center gap-2 px-4 py-2.5 rounded-2xl text-[13px] font-medium border bg-red-50 border-red-200 text-red-800">
                <WifiOff className="w-4 h-4" /> Can't reach the Wasel server. {seenUp.current ? "Showing the last data received." : "It may be starting up; this page keeps trying."}
            </div>
        );
    }
    if (!health) {
        if (!waking) return null;
        return (
            <div role="status" className="w-full flex items-start gap-2 px-4 py-3 rounded-2xl text-sm border bg-amber-50 border-amber-200 text-amber-900">
                <Loader2 className="w-4 h-4 mt-0.5 shrink-0 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                <span><strong className="font-semibold">{t("waking.title")}.</strong> {t("waking.body")}</span>
            </div>
        );
    }

    const llm = health.llm || {};
    const callsLeft = llm.live_call_cap ? Math.max(0, llm.live_call_cap - (llm.live_calls_today ?? 0)) : null;
    const lowBudget = callsLeft !== null && !llm.cap_reached && callsLeft <= Math.max(5, Math.ceil(llm.live_call_cap * 0.1));
    const ai = llm.cap_reached ? "AI budget used up: rules only"
        : llm.fallback_active ? "AI on its backup model"
        : llm.primary === "rules" ? "Scoring with rules"
        : "AI scoring live";
    const calls = callsLeft !== null && !llm.cap_reached && llm.primary !== "rules" ? `${callsLeft} AI calls left today` : null;
    const warn = lowBudget || llm.cap_reached || llm.fallback_active || (llm.primary === "rules" && health.mode !== "public") || health.status !== "ok";
    const whatsapp = health.webhook === "enabled"
        ? (health.wa_send ? "WhatsApp live" : "WhatsApp: replies recorded only")
        : "WhatsApp demo";
    const mode = { public: "Public demo", event: "Live event", dev: "Development" }[health.mode as string] ?? health.mode;
    const tooltip = [
        `Mode: ${mode}`, `AI: ${ai}`, `WhatsApp: ${health.webhook === "enabled" ? (health.wa_send ? "connected, replies are sent" : "connected, replies are recorded only") : "demo mode"}`,
        `AI chain: ${(llm.chain_extract || []).join(" → ") || "rules"}`,
        ...(llm.serving_label && !llm.fallback_active ? [`AI hosted on: ${llm.serving_label} (${llm.serving_host})`] : []),
        ...(llm.serving_label && llm.fallback_active
            ? [`Primary AI host (${llm.serving_label}) did not answer in the last 5 min; the backup is in use`] : []),
        ...(llm.observed || []).map((o: any) =>
            `${o.endpoint}: last call ${o.last_call_at}, ${o.last_outcome}${o.breaker_open ? " (paused)" : ""}`),
        `AI calls today: ${llm.live_calls_today ?? 0}${llm.live_call_cap ? ` / ${llm.live_call_cap}` : ""}`,
        `Scoring queue: ${health.worker?.pending ?? 0}`, `Config ${health.config?.config_hash ?? "–"}`,
    ].join("\n");

    const dot = <span className="hidden sm:inline text-gray-500" aria-hidden="true">·</span>;
    return (
        <div role="status" title={tooltip}
             className={`inline-flex flex-wrap items-center gap-x-2.5 gap-y-1 min-h-9 px-3.5 py-1.5 rounded-full text-xs font-medium border shadow-xs ${warn
                 ? "bg-amber-50 border-amber-200 text-amber-900" : "bg-card border-border text-gray-700"}`}>
            <span className="flex items-center gap-2">
                {warn
                    ? <AlertTriangle className="w-3.5 h-3.5 text-amber-600" aria-hidden="true" />
                    : <span className="relative flex w-2 h-2" aria-hidden="true">
                        <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-60 animate-ping motion-reduce:animate-none" />
                        <span className="relative inline-flex w-2 h-2 rounded-full bg-emerald-500" />
                      </span>}
                {ai}
            </span>
            {calls && <>{dot}<span className="hidden sm:inline tabular-nums">{calls}</span></>}
            {dot}
            <span>{whatsapp}</span>
            {health.wa_auto_send && (
                <>
                    {dot}
                    <span className="font-semibold text-brand" title="Replies cleared by every check are sent without a click">Automatic replies on</span>
                </>
            )}
            {dot}
            <span className="hidden sm:inline text-gray-600">{mode}</span>
        </div>
    );
}
