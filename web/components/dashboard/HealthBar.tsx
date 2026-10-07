"use client";

import { useEffect, useState } from "react";
import { ordersApi } from "@/lib/api/orders";
import { CheckCircle2, AlertTriangle, WifiOff } from "lucide-react";

// One plain-language status line; the technical detail sits in the tooltip.
export function HealthBar() {
    const [health, setHealth] = useState<any>(null);
    const [down, setDown] = useState(false);

    useEffect(() => {
        const load = () => ordersApi.health().then(h => { setHealth(h); setDown(false); }).catch(() => setDown(true));
        load();
        const iv = setInterval(load, 10000);
        return () => clearInterval(iv);
    }, []);

    if (down) {
        return (
            <div role="status" className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium border bg-red-50 border-red-200 text-red-800">
                <WifiOff className="w-4 h-4" /> Can't reach the Wasel server. Showing the last data received.
            </div>
        );
    }
    if (!health) return null;

    const llm = health.llm || {};
    const callsLeft = llm.live_call_cap ? Math.max(0, llm.live_call_cap - (llm.live_calls_today ?? 0)) : null;
    const lowBudget = callsLeft !== null && !llm.cap_reached && callsLeft <= Math.max(5, Math.ceil(llm.live_call_cap * 0.1));
    const aiBase = llm.cap_reached ? "AI budget used up: new messages are scored by rules only"
        : llm.fallback_active ? "AI running on its backup model"
        : llm.primary === "rules" ? "AI offline: scoring with rules only"
        : "AI scoring live";
    const ai = callsLeft !== null && !llm.cap_reached && llm.primary !== "rules"
        ? `${aiBase} · ${callsLeft} of ${llm.live_call_cap} AI calls left today` : aiBase;
    const warn = lowBudget || llm.cap_reached || llm.fallback_active || llm.primary === "rules" || health.status !== "ok";
    const whatsapp = health.webhook === "enabled"
        ? (health.wa_send
            ? "WhatsApp connected, replies are sent"
            : "WhatsApp connected, replies are recorded only")
        : "WhatsApp off (demo mode)";
    const mode = { public: "Public demo", event: "Live event", dev: "Development" }[health.mode as string] ?? health.mode;
    const tooltip = [
        `Mode: ${health.mode}`, `AI chain: ${(llm.chain_extract || []).join(" → ") || "rules"}`,
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
            <span className="hidden sm:inline text-gray-400" aria-hidden="true">·</span>
            <span>{whatsapp}</span>
            {health.wa_auto_send && (
                <>
                    <span className="hidden sm:inline text-gray-400" aria-hidden="true">·</span>
                    <span className="font-semibold text-brand" title="Replies cleared by every check are sent without a click">Automatic replies on</span>
                </>
            )}
            <span className="hidden sm:inline text-gray-400" aria-hidden="true">·</span>
            <span className="hidden sm:inline text-gray-500">{mode}</span>
        </div>
    );
}
