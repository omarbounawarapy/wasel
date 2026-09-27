"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Loader2, PhoneCall } from "lucide-react";
import { callsApi } from "@/lib/api/calls";
import type { CallDetailResponse, CallTranscriptMessage } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

type CallDetailPageProps = {
    callId: string;
    backHref: string;
    backLabel?: string;
};

const formatDate = (value: string | null) => {
    if (!value) return "—";
    return new Date(value).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

const formatDuration = (seconds: number) => `${seconds ?? 0}`;

const MessageBubble = ({ message }: { message: CallTranscriptMessage }) => {
    const isClient = message.role === "client";

    return (
        <div className={`flex ${isClient ? "justify-start" : "justify-end"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 shadow-sm ${isClient ? "bg-slate-100 text-slate-900 rounded-tl-none" : "bg-primary text-primary-foreground rounded-tr-none"}`}>
                <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                {message.timestamp && (
                    <p className={`text-[10px] mt-1 opacity-70 ${!isClient ? "text-primary-foreground" : ""}`}>
                        {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </p>
                )}
            </div>
        </div>
    );
};

export function CallDetailPage({ callId, backHref, backLabel = "Back" }: CallDetailPageProps) {
    const router = useRouter();
    const [call, setCall] = useState<CallDetailResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;
        const normalizedCallId = String(callId ?? "").trim();

        if (!normalizedCallId || normalizedCallId === "undefined" || normalizedCallId === "null") {
            setError("Invalid call ID.");
            setCall(null);
            setLoading(false);
            return () => {
                mounted = false;
            };
        }

        const load = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await callsApi.get(normalizedCallId);
                if (mounted) {
                    setCall(response);
                }
            } catch (err: any) {
                if (!mounted) return;
                setError(err?.message || "Unable to load call details right now.");
                setCall(null);
            } finally {
                if (mounted) setLoading(false);
            }
        };

        load();
        return () => {
            mounted = false;
        };
    }, [callId]);

    const messages = useMemo(() => call?.messages || [], [call]);

    if (loading) {
        return (
            <div className="p-6 flex items-center justify-center min-h-[50vh]">
                <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-5 w-5 animate-spin" />
                    Loading call details...
                </div>
            </div>
        );
    }

    if (error || !call) {
        return (
            <div className="p-6 space-y-4">
                <Button variant="outline" onClick={() => router.push(backHref)}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    {backLabel}
                </Button>
                <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-8 text-center">
                    <PhoneCall className="h-12 w-12 mx-auto mb-3 opacity-50 text-muted-foreground" />
                    <h1 className="text-xl font-semibold mb-2">Call not available</h1>
                    <p className="text-muted-foreground">{error || "We couldn’t find that call. Please try again."}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center gap-4 flex-wrap">
                <Button variant="ghost" size="icon" onClick={() => router.push(backHref)}>
                    <ArrowLeft className="h-4 w-4" />
                </Button>
                <div>
                    <h1 className="text-2xl font-bold mb-1">Call Detail</h1>
                    <p className="text-sm text-muted-foreground">{call.callId}</p>
                </div>
                <div className="ml-auto">
                    <Badge variant={call.status === "ended" ? "default" : "secondary"}>
                        {call.status || "unknown"}
                    </Badge>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-6 gap-4">
                <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4">
                    <p className="text-xs text-muted-foreground mb-1">Call ID</p>
                    <p className="font-semibold break-all">{call.callId}</p>
                </div>
                <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4">
                    <p className="text-xs text-muted-foreground mb-1">Client Number</p>
                    <p className="font-semibold">{call.clientPhoneNumber || "—"}</p>
                </div>
                <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4">
                    <p className="text-xs text-muted-foreground mb-1">Our Number</p>
                    <p className="font-semibold">{call.ourPhoneNumber || "—"}</p>
                </div>
                <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4">
                    <p className="text-xs text-muted-foreground mb-1">Created At</p>
                    <p className="font-semibold">{formatDate(call.createdAt)}</p>
                </div>
                <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4">
                    <p className="text-xs text-muted-foreground mb-1">Duration (sec)</p>
                    <p className="font-semibold">{formatDuration(call.durationSeconds)}</p>
                </div>
                <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4">
                    <p className="text-xs text-muted-foreground mb-1">Ended Reason</p>
                    <p className="font-semibold">{call.endedReason || "—"}</p>
                </div>
            </div>

            <div className="bg-white border border-slate-200 shadow-sm rounded-2xl p-4">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h2 className="text-lg font-semibold">Transcript</h2>
                        <p className="text-sm text-muted-foreground">User messages appear on the left and assistant messages on the right.</p>
                    </div>
                </div>

                {messages.length === 0 ? (
                    <div className="py-12 text-center text-muted-foreground">
                        <PhoneCall className="h-12 w-12 mx-auto mb-3 opacity-50" />
                        <p className="font-medium">No transcript available</p>
                        <p className="text-sm mt-1">This call does not have structured messages or transcript content yet.</p>
                    </div>
                ) : (
                    <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
                        {messages.map((message, index) => (
                            <MessageBubble key={`${message.role}-${index}`} message={message} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
