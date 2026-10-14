"use client";

import { useEffect, useRef, useState } from "react";
import { ordersApi } from "@/lib/api/orders";
import { CheckCircle2, AlertTriangle, WifiOff, Loader2 } from "lucide-react";
import { useT } from "@/lib/i18n";

// A first answer later than this means the free host is waking up: say so instead of showing nothing.
const WAKING_AFTER_MS = 3000;

// One plain-language status line; the technical detail sits in the tooltip.
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
            <div role="status" className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium border bg-red-50 border-red-200 text-red-800">
                <WifiOff className="w-4 h-4" /> Can't reach the Wasel server. {seenUp.current ? "Showing the last data received." : "It may be starting up; this page keeps trying."}
            </div>
        );
    }
    if (!health) {
        if (!waking) return null;
        return (
            <div role="status" className="flex items-start gap-2 px-4 py-3 rounded-xl text-sm border bg-amber-50 border-amber-200 text-amber-900">
                <Loader2 className="w-4 h-4 mt-0.5 shrink-0 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                <span><strong className="font-semibold">{t("waking.title")}.</strong> {t("waking.body")}</span>
            </div>
        );
    }

    const llm = health.llm || {};
    const callsLeft = llm.live_call_cap ? Math.max(0, llm.live_call_cap - (llm.live_calls_today ?? 0)) : null;
    const lowBudget = callsLeft !== null && !llm.cap_reached && callsLeft <= Math.max(5, Math.ceil(llm.live_call_cap * 0.1));
    const aiBase = llm.cap_reached ? "AI budget used up: new messages are scored by rules only"
        : llm.fallback_active ? "AI running on its backup model"
        : llm.primary === "rules" ? "Scoring with rules"
        : "AI scoring live";
    const ai = callsLeft !== null && !llm.cap_reached && llm.primary !== "rules"
        ? `${aiBase} · ${callsLeft} of ${llm.live_call_cap} AI calls left today` : aiBase;
    const warn = lowBudget || llm.cap_reached || llm.fallback_active || (llm.primary === "rules" && health.mode !== "public") || health.status !== "ok";
    const whatsapp = health.webhook === "enabled"
        ? (health.wa_send
            ? "WhatsApp connected, replies are sent"
            : "WhatsApp connected, replies are recorded only")
        : "WhatsApp: demo mode";
    const mode = { public: "Public demo", event: "Live event", dev: "Development" }[health.mode as string] ?? health.mode;
    const tooltip = [
        `Mode: ${health.mode}`, `AI chain: ${(llm.chain_extract || []).join(" → ") || "rules"}`,
        ...(llm.serving_label && !llm.fallback_active ? [`AI hosted on: ${llm.serving_label} (${llm.serving_host})`] : []),
        ...(llm.serving_label && llm.fallback_active
            ? [`Primary AI host (${llm.serving_label}) did not answer in the last 5 min; the backup is in use`] : []),
        ...(llm.observed || []).map((o: any) =>
            `${o.endpoint}: last call ${o.last_call_at}, ${o.last_outcome}${o.breaker_open ? " (paused)" : ""}`),
        `AI calls today: ${llm.live_calls_today ?? 0}${llm.live_call_cap ? ` / ${llm.live_call_cap}` : ""}`,
        `Scoring queue: ${health.worker?.pending ?? 0}`, `Config ${health.config?.config_hash ?? "–"}`,
    ].join("\n");

    return (
        <div role="status" title={tooltip}
             className={`flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2 rounded-xl text-xs font-medium border ${warn
                 ? "bg-amber-50 border-amber-200 text-amber-900" : "bg-white border-gray-200 text-gray-700"}`}>
            <span className="flex items-center gap-1.5">
                {warn ? <AlertTriangle className="w-4 h-4 text-amber-600" /> : <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
                {ai}
            </span>
            <span className="hidden sm:inline text-gray-500" aria-hidden="true">·</span>
            <span>{whatsapp}</span>
            {health.wa_auto_send && (
                <>
                    <span className="hidden sm:inline text-gray-500" aria-hidden="true">·</span>
                    <span className="font-semibold text-brand" title="Replies cleared by every check are sent without a click">Automatic replies on</span>
                </>
            )}
            <span className="hidden sm:inline text-gray-500" aria-hidden="true">·</span>
            <span className="hidden sm:inline text-gray-600">{mode}</span>
        </div>
    );
}
