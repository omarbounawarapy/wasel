"use client";

import React from 'react';
import { useVapi } from './VapiProvider';
import { Mic, PhoneOff, Loader2 } from 'lucide-react';

interface CallButtonProps {
    assistantId: string;
    onCallStart?: () => void;
    onCallEnd?: () => void;
    onError?: (message: string) => void;
    className?: string;
}

export function CallButton({ assistantId, onCallStart, onCallEnd, onError, className }: CallButtonProps) {
    const { startCall, stopCall, status } = useVapi();

    const handleToggleCall = async () => {
        if (status === 'connected' || status === 'connecting') {
            stopCall();
            if (onCallEnd) onCallEnd();
        } else {
            if (onCallStart) onCallStart();
            await startCall(assistantId);
        }
    };

    const isActive = status === 'connected';
    const isConnecting = status === 'connecting';

    return (
        <button
            onClick={handleToggleCall}
            disabled={isConnecting}
            className={`
                relative overflow-hidden font-semibold transition-all flex items-center justify-center gap-2.5 min-w-[150px]
                ${isActive
                    ? 'bg-red-500 hover:bg-red-600 text-white rounded-xl shadow-[0_4px_16px_rgba(239,68,68,0.3)]'
                    : 'bg-gradient-to-b from-[#187848] via-[#0a4c2f] to-[#052b19] text-white rounded-xl shadow-[0_4px_16px_rgba(10,76,47,0.3)]'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
                ${className}
            `}
        >
            {!isActive && (
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/20 via-transparent to-transparent opacity-50"></div>
            )}
            {isConnecting ? (
                <>
                    <Loader2 className="h-5 w-5 animate-spin relative z-10" />
                    <span className="relative z-10">Connecting...</span>
                </>
            ) : isActive ? (
                <>
                    <PhoneOff className="h-5 w-5" />
                    <span>End Call</span>
                </>
            ) : (
                <>
                    <Mic className="h-5 w-5 relative z-10" />
                    <span className="relative z-10">Start Call</span>
                </>
            )}
        </button>
    );
}
