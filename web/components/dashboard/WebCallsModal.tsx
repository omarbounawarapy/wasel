"use client";

import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, Phone, Globe } from "lucide-react";

interface WebCall {
    id: string;
    phoneNumber: string;
    duration?: number;
    createdAt?: string;
    endedAt?: string;
    transcript?: string;
    status?: string;
    cost?: number;
}

interface WebCallsModalProps {
    isOpen: boolean;
    onClose: () => void;
    calls: WebCall[];
    isLoading?: boolean;
}

const formatDuration = (seconds?: number) => {
    if (!seconds) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const formatDate = (dateStr?: string) => {
    if (!dateStr) return "—";
    return new Date(dateStr).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

const formatCost = (cost?: number) => {
    if (typeof cost !== "number") return "—";
    return `$${cost.toFixed(2)}`;
};

const getStatusStyle = (status?: string) => {
    switch (status) {
        case "ended": return "bg-green-100 text-green-700";
        case "in-progress": return "bg-amber-100 text-amber-700";
        case "failed": return "bg-red-100 text-red-700";
        default: return "bg-gray-100 text-gray-600";
    }
};

export function WebCallsModal({ isOpen, onClose, calls, isLoading = false }: WebCallsModalProps) {
    return (
        <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <DialogContent className="max-w-3xl max-h-[85vh] overflow-hidden p-0 rounded-[24px]">
                <div className="px-6 pt-6 pb-4 border-b border-gray-100">
                    <DialogHeader>
                        <DialogTitle className="text-xl font-bold text-gray-900">All Web Calls</DialogTitle>
                        <DialogDescription className="text-sm text-gray-500">
                            Review recent calls with duration, status, and cost.
                        </DialogDescription>
                    </DialogHeader>
                </div>

                <div className="overflow-y-auto px-6 pb-6 pt-4 max-h-[65vh]">
                    {isLoading ? (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-[#0a4c2f]" />
                        </div>
                    ) : calls.length === 0 ? (
                        <div className="text-center py-8">
                            <Phone className="h-10 w-10 mx-auto mb-2 text-gray-300" />
                            <p className="text-gray-500">No web calls found</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {calls.map((call) => (
                                <div
                                    key={call.id}
                                    className="rounded-xl border border-gray-100 p-4 bg-white hover:bg-gray-50 transition-colors"
                                >
                                    <div className="flex items-center justify-between gap-4">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center shrink-0">
                                                <Globe className="w-5 h-5 text-blue-500" />
                                            </div>
                                            <div>
                                                <p className="font-bold text-gray-900 text-sm">{call.phoneNumber || "Web Call"}</p>
                                                <p className="text-xs text-gray-500 mt-0.5">
                                                    {formatDate(call.createdAt)}
                                                </p>
                                            </div>
                                        </div>
                                        <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${getStatusStyle(call.status)}`}>
                                            {call.status || "unknown"}
                                        </span>
                                    </div>

                                    <div className="mt-3 grid grid-cols-3 gap-3">
                                        {[
                                            { label: "Duration", value: formatDuration(call.duration) },
                                            { label: "Cost", value: formatCost(call.cost) },
                                            { label: "Ended", value: formatDate(call.endedAt) },
                                        ].map((stat, i) => (
                                            <div key={i} className="bg-gray-50 rounded-lg px-3 py-2">
                                                <p className="text-[10px] text-gray-400 font-medium uppercase">{stat.label}</p>
                                                <p className="text-sm font-bold text-gray-900">{stat.value}</p>
                                            </div>
                                        ))}
                                    </div>

                                    {call.transcript && (
                                        <p className="mt-3 text-sm text-gray-500 line-clamp-3 bg-gray-50 rounded-lg p-3">
                                            {call.transcript}
                                        </p>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    );
}
