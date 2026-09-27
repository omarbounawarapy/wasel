import React, { useState, useEffect, useCallback } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Phone, Check, Shield, Lock, Loader2, Trash2, RefreshCw } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { useAuth } from '@/contexts/AuthContext';
import { phoneApi } from '@/lib/api-endpoints';

interface PhoneStatus {
    has_phone: boolean;
    phone_number?: string;
    provider?: string;
    is_active: boolean;
    created_at?: string;
}

export function PhoneNumberManager() {
    const { user } = useAuth();
    const { toast } = useToast();
    const [loading, setLoading] = useState(false);
    const [statusLoading, setStatusLoading] = useState(true);
    const [phoneStatus, setPhoneStatus] = useState<PhoneStatus | null>(null);

    const [accountSid, setAccountSid] = useState('');
    const [authToken, setAuthToken] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');

    const fetchStatus = useCallback(async () => {
        try {
            setStatusLoading(true);
            const tenantId = user?.tenant_id;
            if (!tenantId) return;
            const data = await phoneApi.getStatus(tenantId);
            setPhoneStatus(data);
        } catch (error) {
            console.error("Failed to fetch phone status:", error);
        } finally {
            setStatusLoading(false);
        }
    }, [user]);

    useEffect(() => {
        if (user?.tenant_id) fetchStatus();
    }, [user, fetchStatus]);

    const handleProvision = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!accountSid || !authToken || !phoneNumber) {
            toast({ title: "Missing Information", description: "Please fill in all Twilio credentials.", variant: "destructive" });
            return;
        }
        try {
            setLoading(true);
            const tenantId = user?.tenant_id;
            if (!tenantId) throw new Error("Tenant ID not found");
            await phoneApi.provision(tenantId, { twilio_account_sid: accountSid, twilio_auth_token: authToken, phone_number: phoneNumber });
            toast({ title: "Success", description: "Phone number successfully integrated!" });
            setAccountSid(''); setAuthToken(''); setPhoneNumber('');
            fetchStatus();
        } catch (error: any) {
            toast({ title: "Error", description: error.message, variant: "destructive" });
        } finally { setLoading(false); }
    };

    const handleSync = async () => {
        try {
            setLoading(true);
            const tenantId = user?.tenant_id;
            if (!tenantId) throw new Error("Tenant ID not found");
            const result = await phoneApi.syncFromVapi(tenantId);
            if (result.success) {
                toast({ title: "✅ Sync Successful", description: result.synced ? `Synced phone: ${result.phone_number}` : "No phone numbers found in Vapi dashboard" });
                fetchStatus();
            }
        } catch (error: any) {
            toast({ title: "Sync Failed", description: error.message || "Failed to sync", variant: "destructive" });
        } finally { setLoading(false); }
    };

    const handleRemove = async () => {
        if (!confirm("Are you sure you want to remove this phone number?")) return;
        try {
            setLoading(true);
            const tenantId = user?.tenant_id;
            if (!tenantId) throw new Error("Tenant ID not found");
            await phoneApi.remove(tenantId, false);
            toast({ title: "Removed", description: "Phone number disconnected." });
            fetchStatus();
        } catch (error: any) {
            toast({ title: "Error", description: error.message, variant: "destructive" });
        } finally { setLoading(false); }
    };

    if (statusLoading) {
        return (
            <div className="bg-white rounded-[24px] shadow-[0_2px_15px_-4px_rgba(0,0,0,0.03)] border border-gray-100 p-6 flex justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-[#0a4c2f]" />
            </div>
        );
    }

    return (
        <div className="bg-white rounded-[24px] shadow-[0_2px_15px_-4px_rgba(0,0,0,0.03)] border border-gray-100 overflow-hidden">
            {/* Header */}
            <div className="p-6 pb-4">
                <h3 className="font-bold text-lg text-gray-900 flex items-center gap-2"><Phone className="h-5 w-5" />Phone Integration</h3>
                <p className="text-sm text-gray-500 mt-1">Connect your Twilio phone number to enable AI voice management.</p>
            </div>

            <div className="px-6 pb-6">
                {phoneStatus?.has_phone && phoneStatus.is_active ? (
                    <div className="space-y-4">
                        <Alert className="bg-green-50 border-green-200 rounded-xl">
                            <Check className="h-4 w-4 text-green-600" />
                            <AlertTitle className="text-green-800">Active Connection</AlertTitle>
                            <AlertDescription className="text-green-700">
                                Your AI assistant is connected to <strong>{phoneStatus.phone_number}</strong> via <strong>{phoneStatus.provider?.toUpperCase()}</strong>.
                            </AlertDescription>
                        </Alert>

                        <div className="flex justify-between gap-2">
                            <button
                                onClick={handleSync}
                                disabled={loading}
                                className="flex-1 px-4 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors text-sm flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                                Sync from Vapi
                            </button>
                            <button
                                onClick={handleRemove}
                                disabled={loading}
                                className="flex-1 px-4 py-2.5 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-colors text-sm flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                                Disconnect Number
                            </button>
                        </div>
                    </div>
                ) : (
                    <form onSubmit={handleProvision} className="space-y-4">
                        <Alert className="bg-blue-50 border-blue-200 rounded-xl mb-4">
                            <Shield className="h-4 w-4 text-blue-600" />
                            <AlertTitle className="text-blue-800">Secure Integration</AlertTitle>
                            <AlertDescription className="text-blue-700 text-xs">
                                Your credentials are encrypted using AES-256 before storage.
                                <br />
                                <strong className="mt-2 block">💡 Tip:</strong> If you added a phone in the Vapi dashboard manually, click &quot;Sync from Vapi&quot; below.
                            </AlertDescription>
                        </Alert>

                        <div className="flex justify-end mb-4">
                            <button
                                type="button"
                                onClick={handleSync}
                                disabled={loading}
                                className="px-4 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors text-sm flex items-center gap-2"
                            >
                                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
                                Sync from Vapi Dashboard
                            </button>
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="sid" className="text-sm font-semibold text-gray-700">Twilio Account SID</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <input
                                    id="sid"
                                    placeholder="AC..."
                                    value={accountSid}
                                    onChange={(e) => setAccountSid(e.target.value)}
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0a4c2f]/20 focus:border-[#0a4c2f]/30 transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="token" className="text-sm font-semibold text-gray-700">Twilio Auth Token</label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <input
                                    id="token"
                                    type="password"
                                    placeholder="Your auth token"
                                    value={authToken}
                                    onChange={(e) => setAuthToken(e.target.value)}
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0a4c2f]/20 focus:border-[#0a4c2f]/30 transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label htmlFor="phone" className="text-sm font-semibold text-gray-700">Phone Number (E.164)</label>
                            <div className="relative">
                                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                                <input
                                    id="phone"
                                    placeholder="+1234567890"
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    required
                                    className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#0a4c2f]/20 focus:border-[#0a4c2f]/30 transition-all"
                                />
                            </div>
                            <p className="text-xs text-gray-400">Must include country code (e.g. +1 for US)</p>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full px-6 py-3 bg-gradient-to-b from-[#187848] via-[#0a4c2f] to-[#052b19] text-white rounded-xl font-semibold transition-all shadow-[0_4px_16px_rgba(10,76,47,0.3)] relative overflow-hidden"
                        >
                            <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/20 via-transparent to-transparent opacity-50"></div>
                            <span className="relative z-10 flex items-center justify-center gap-2">
                                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                                {loading ? "Connecting..." : "Connect Phone Number"}
                            </span>
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}
