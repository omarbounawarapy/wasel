"use client";

import React, { createContext, useContext, useEffect, useState } from 'react';
import Vapi from '@vapi-ai/web';

interface VapiContextType {
    vapi: Vapi | null;
    isSessionActive: boolean;
    startCall: (assistantId?: string) => Promise<void>;
    stopCall: () => void;
    status: 'disconnected' | 'connecting' | 'connected';
}

const VapiContext = createContext<VapiContextType | null>(null);

export function VapiProvider({ children, apiKey }: { children: React.ReactNode, apiKey: string }) {
    const [vapi, setVapi] = useState<Vapi | null>(null);
    const [status, setStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');

    useEffect(() => {
        if (!apiKey) return;

        const vapiInstance = new Vapi(apiKey);
        setVapi(vapiInstance);

        // Event listeners
        vapiInstance.on('call-start', () => setStatus('connected'));
        vapiInstance.on('call-end', () => setStatus('disconnected'));
        vapiInstance.on('error', (e) => {
            console.error('Vapi Error:', e);
            setStatus('disconnected');
        });

        return () => {
            vapiInstance.stop();
        };
    }, [apiKey]);

    const startCall = async (assistantId?: string) => {
        if (!vapi) return;
        setStatus('connecting');
        try {
            if (assistantId) {
                await vapi.start(assistantId);
            } else {
                // Start transient call or default? 
                // Usually we start with assistant ID
                console.warn("No assistant ID provided to startCall in VapiProvider");
                setStatus('disconnected');
            }
        } catch (e) {
            console.error("Failed to start call", e);
            setStatus('disconnected');
        }
    };

    const stopCall = () => {
        if (!vapi) return;
        vapi.stop();
    };

    return (
        <VapiContext.Provider value={{
            vapi,
            isSessionActive: status === 'connected',
            startCall,
            stopCall,
            status
        }}>
            {children}
        </VapiContext.Provider>
    );
}

export function useVapi() {
    const context = useContext(VapiContext);
    if (!context) {
        throw new Error('useVapi must be used within a VapiProvider');
    }
    return context;
}
