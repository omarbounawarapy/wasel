"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ChevronLeft, ChevronRight, Loader2, PhoneCall, RefreshCw, Globe, Phone } from "lucide-react";
import { callsApi } from "@/lib/api/calls";
import type { CallDetailResponse, CallListItem } from "@/lib/types";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";

const PAGE_SIZE = 10;

const formatDate = (value: string | null) => {
    if (!value) return "—";
    return new Date(value).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

const formatDuration = (seconds: number) => {
    if (!seconds) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const getStatusStyle = (status: string | null) => {
    switch (status) {
        case "ended": return "bg-green-100 text-green-700";
        case "in-progress": return "bg-amber-100 text-amber-700";
        case "failed": return "bg-red-100 text-red-700";
        default: return "bg-gray-100 text-gray-600";
    }
};

/** Determine caller display name based on available data */
const getCallerDisplay = (call: CallListItem) => {
    // If the call has a phone number, show it
    if (call.clientPhoneNumber && call.clientPhoneNumber.trim() && call.clientPhoneNumber !== "null") {
        return { label: call.clientPhoneNumber, isWebCall: false };
    }
    // Otherwise it's a web call
    return { label: "Web Call", isWebCall: true };
};

/** Extract caller name from transcript messages if available */
const getCallerNameFromDetail = (detail: CallDetailResponse) => {
    // Check main phone number first
    if (detail.clientPhoneNumber && detail.clientPhoneNumber.trim() && detail.clientPhoneNumber !== "null") {
        return { label: detail.clientPhoneNumber, isWebCall: false };
    }

    // Try to extract a name from the transcript
    if (detail.messages && detail.messages.length > 0) {
        for (const msg of detail.messages) {
            if (msg.role === "client" && msg.text) {
                // Common patterns: "My name is X", "I'm X", "This is X"
                const namePatterns = [
                    /my name is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/i,
                    /(?:i'm|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/i,
                    /this is\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)/i,
                ];
                for (const pattern of namePatterns) {
                    const match = msg.text.match(pattern);
                    if (match?.[1]) {
                        return { label: match[1], isWebCall: true };
                    }
                }
            }
        }
    }

    return { label: "Web Call", isWebCall: true };
};

export function CallHistoryPage() {
    const router = useRouter();
    const [page, setPage] = useState(1);
    const [items, setItems] = useState<CallListItem[]>([]);
    const [hasMore, setHasMore] = useState(false);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedCallId, setSelectedCallId] = useState<string | null>(null);
    const [selectedCall, setSelectedCall] = useState<CallDetailResponse | null>(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [detailError, setDetailError] = useState<string | null>(null);

    useEffect(() => {
        let mounted = true;

        const load = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await callsApi.list(page, PAGE_SIZE);
                if (!mounted) return;
                const sanitizedItems = (response.items || []).map((item: any) => ({
                    callId: item?.callId || item?.id || item?.call?.id || null,
                    createdAt: item?.createdAt || item?.created_at || item?.startedAt || null,
                    clientPhoneNumber: item?.clientPhoneNumber || item?.client_phone_number || item?.customer_phone || null,
                    durationSeconds: Number(item?.durationSeconds ?? item?.duration ?? 0),
                    status: item?.status || null,
                    endedReason: item?.endedReason || item?.ended_reason || null,
                })).filter((item: any) => Boolean(item.callId));

                setItems(sanitizedItems);
                setHasMore(Boolean(response.hasMore));
            } catch (err: any) {
                if (!mounted) return;
                setError(err?.message || "Unable to load call history right now.");
                setItems([]);
                setHasMore(false);
            } finally {
                if (mounted) setLoading(false);
            }
        };

        load();
        return () => { mounted = false; };
    }, [page]);

    const emptyState = useMemo(() => {
        if (error) return error;
        return "No calls yet.";
    }, [error]);

    const openCallDetails = async (callId: string | null | undefined) => {
        const normalizedId = String(callId ?? "").trim();
        if (!normalizedId || normalizedId === "undefined" || normalizedId === "null") return;

        setSelectedCallId(normalizedId);
        setSelectedCall(null);
        setDetailError(null);
        setDetailLoading(true);

        try {
            const detail = await callsApi.get(normalizedId);
            setSelectedCall(detail);
        } catch (err: any) {
            setDetailError(err?.message || "Unable to load call details.");
        } finally {
            setDetailLoading(false);
        }
    };

    return (
        <div>
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h1 className="text-[32px] font-bold tracking-tight text-gray-900 mb-1 leading-none">Call History</h1>
                    <p className="text-[14px] text-gray-500 font-medium">Review recent AI calls and transcripts.</p>
                </div>
                <button
                    onClick={() => setPage(1)}
                    disabled={loading}
                    className="px-4 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-[20px] font-semibold hover:bg-gray-50 transition-colors flex items-center gap-2 text-sm shadow-sm"
                >
                    <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    Refresh
                </button>
            </div>

            {/* Calls as Cards */}
            <div className="bg-white rounded-[24px] shadow-[0_2px_15px_-4px_rgba(0,0,0,0.03)] border border-gray-100 p-6">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <div className="w-8 h-8 border-2 border-[#0a4c2f] border-t-transparent rounded-full animate-spin"></div>
                    </div>
                ) : items.length === 0 ? (
                    <div className="py-12 text-center">
                        <PhoneCall className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                        <p className="font-semibold text-gray-900">{emptyState}</p>
                        <p className="text-sm text-gray-500 mt-1">
                            {error ? "Please try again in a moment." : "Your call history will appear here once calls come in."}
                        </p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {items.map((call) => {
                            const caller = getCallerDisplay(call);
                            return (
                                <div
                                    key={call.callId}
                                    className="flex justify-between items-center p-4 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer border border-gray-100"
                                    onClick={() => {
                                        if (!call.callId) return;
                                        openCallDetails(call.callId);
                                    }}
                                >
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${caller.isWebCall ? 'bg-blue-50' : 'bg-[#f3f5f4]'}`}>
                                            {caller.isWebCall ? (
                                                <Globe className="w-5 h-5 text-blue-500" />
                                            ) : (
                                                <Phone className="w-5 h-5 text-gray-500" />
                                            )}
                                        </div>
                                        <div className="min-w-0 pr-2">
                                            <h4 className="text-[14px] font-bold text-gray-900 mb-0.5 truncate">
                                                {caller.label}
                                            </h4>
                                            <p className="text-[12px] text-gray-500 font-medium truncate">
                                                {formatDate(call.createdAt)} • {formatDuration(call.durationSeconds)}
                                                {call.endedReason ? ` • ${call.endedReason}` : ""}
                                            </p>
                                        </div>
                                    </div>
                                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold tracking-wide shrink-0 ${getStatusStyle(call.status)}`}>
                                        {call.status || "unknown"}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                )}

                {/* Pagination */}
                <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-100">
                    <span className="text-sm text-gray-500 font-medium">Page {page}</span>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage((current) => Math.max(1, current - 1))}
                            disabled={page === 1 || loading}
                            className="px-3 py-1.5 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors text-sm disabled:opacity-40 flex items-center gap-1"
                        >
                            <ChevronLeft className="h-4 w-4" />Previous
                        </button>
                        <button
                            onClick={() => setPage((current) => current + 1)}
                            disabled={!hasMore || loading}
                            className="px-3 py-1.5 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors text-sm disabled:opacity-40 flex items-center gap-1"
                        >
                            Next<ChevronRight className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Call Detail Dialog - Callem Styled */}
            <Dialog open={Boolean(selectedCallId)} onOpenChange={(open) => {
                if (!open) {
                    setSelectedCallId(null);
                    setSelectedCall(null);
                    setDetailError(null);
                    setDetailLoading(false);
                }
            }}>
                <DialogContent className="w-[96vw] max-w-[96vw] sm:max-w-[92vw] lg:max-w-[84vw] xl:max-w-[74vw] 2xl:max-w-[68vw] max-h-[92vh] overflow-hidden p-0 rounded-[24px] border border-gray-100">
                    <div className="px-6 pt-6 pb-4 border-b border-gray-100">
                        <DialogHeader>
                            <DialogTitle className="text-xl font-bold text-gray-900">Call Details</DialogTitle>
                            <DialogDescription className="text-sm text-gray-500">Detailed call metadata and transcript.</DialogDescription>
                        </DialogHeader>
                    </div>

                    <div className="overflow-y-auto px-6 pb-6 pt-4">
                        {detailLoading ? (
                            <div className="flex items-center justify-center py-12 text-gray-500">
                                <div className="w-6 h-6 border-2 border-[#0a4c2f] border-t-transparent rounded-full animate-spin mr-3"></div>
                                Loading call details...
                            </div>
                        ) : detailError ? (
                            <div className="py-10 text-center">
                                <PhoneCall className="h-10 w-10 mx-auto mb-3 text-gray-300" />
                                <p className="font-bold text-gray-900">Could not load details</p>
                                <p className="text-sm text-gray-500 mt-1">{detailError}</p>
                            </div>
                        ) : !selectedCall ? (
                            <div className="py-10 text-center text-gray-500">No call selected.</div>
                        ) : (() => {
                            const callerInfo = getCallerNameFromDetail(selectedCall);
                            return (
                                <div className="space-y-5">
                                    {/* Caller header */}
                                    <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl">
                                        <div className={`w-12 h-12 rounded-full flex items-center justify-center shrink-0 ${callerInfo.isWebCall ? 'bg-blue-100' : 'bg-[#0a4c2f]/10'}`}>
                                            {callerInfo.isWebCall ? <Globe className="w-6 h-6 text-blue-500" /> : <Phone className="w-6 h-6 text-[#0a4c2f]" />}
                                        </div>
                                        <div>
                                            <h3 className="font-bold text-lg text-gray-900">{callerInfo.label}</h3>
                                            <p className="text-sm text-gray-500">{callerInfo.isWebCall ? "Web Call" : "Phone Call"} • {formatDate(selectedCall.createdAt)}</p>
                                        </div>
                                        <div className="ml-auto">
                                            <span className={`px-3 py-1.5 rounded-full text-xs font-bold ${getStatusStyle(selectedCall.status)}`}>
                                                {selectedCall.status || "unknown"}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Stats grid */}
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                        {[
                                            { label: "Caller", value: callerInfo.label },
                                            { label: "Created At", value: formatDate(selectedCall.createdAt) },
                                            { label: "Duration", value: formatDuration(selectedCall.durationSeconds) },
                                            { label: "Status", value: selectedCall.status || "unknown" },
                                        ].map((stat, i) => (
                                            <div key={i} className="border border-gray-100 rounded-xl p-3 bg-white">
                                                <p className="text-[11px] text-gray-400 font-medium mb-1 uppercase tracking-wide">{stat.label}</p>
                                                <p className="font-bold text-gray-900 text-sm capitalize">{stat.value}</p>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Transcript */}
                                    <div className="border border-gray-100 rounded-xl overflow-hidden">
                                        <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-100">
                                            <h3 className="font-bold text-gray-900 text-sm">Transcript</h3>
                                        </div>

                                        <div className="p-4">
                                            {!selectedCall.messages || selectedCall.messages.length === 0 ? (
                                                <div className="py-8 text-center text-gray-500">
                                                    <p className="font-medium">No transcript available</p>
                                                    <p className="text-sm mt-1">This call does not have structured transcript messages yet.</p>
                                                </div>
                                            ) : (
                                                <div className="space-y-3 max-h-[46vh] overflow-y-auto pr-1 scrollbar-hide">
                                                    {selectedCall.messages.map((message, index) => {
                                                        const isClient = message.role === "client";
                                                        return (
                                                            <div key={`${message.role}-${index}`} className={`flex ${isClient ? "justify-start" : "justify-end"}`}>
                                                                <div className={`max-w-[82%] rounded-2xl px-4 py-2.5 ${isClient ? "bg-gray-100 text-gray-900 rounded-tl-none" : "bg-[#0a4c2f] text-white rounded-tr-none"}`}>
                                                                    <p className="text-sm whitespace-pre-wrap">{message.text}</p>
                                                                    {message.timestamp && (
                                                                        <p className="text-[10px] opacity-60 mt-1">
                                                                            {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                                                                        </p>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex justify-end">
                                        <button
                                            onClick={() => {
                                                if (!selectedCall.callId) return;
                                                router.push(`/dashboard/calls/${selectedCall.callId}`);
                                            }}
                                            className="px-5 py-2.5 bg-gradient-to-b from-[#187848] via-[#0a4c2f] to-[#052b19] text-white rounded-[20px] font-semibold transition-all shadow-[0_4px_16px_rgba(10,76,47,0.3)] relative overflow-hidden text-sm"
                                        >
                                            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/20 via-transparent to-transparent opacity-50"></div>
                                            <span className="relative z-10">Open full page</span>
                                        </button>
                                    </div>
                                </div>
                            );
                        })()}
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
}
