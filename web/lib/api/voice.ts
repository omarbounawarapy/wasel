import api from '@/lib/api';
import type {
    VoiceStartCallRequest,
    VoiceStartCallResponse,
    VoiceTestResponse,
    VoiceCallHistoryResponse,
    VoiceWebRTCResponse,
    VoiceConfiguration,
    VoiceModel,
    VoiceOption,
    VoiceTool,
} from '@/lib/types';

export const voiceApi = {
    startCall: async (payload: VoiceStartCallRequest): Promise<VoiceStartCallResponse> => {
    const response = await api.post<VoiceStartCallResponse>('/voice/start-call', payload);
    return response;
    },
    testAgent: async (): Promise<VoiceTestResponse> => {
    const response = await api.get<VoiceTestResponse>('/voice/test-agent');
    return response;
    },
    callHistory: async (limit = 20): Promise<VoiceCallHistoryResponse> => {
    const response = await api.get<VoiceCallHistoryResponse>('/voice/call-history', { params: { limit } });
    return response;
    },
    webrtcTest: async (): Promise<VoiceWebRTCResponse> => {
    const response = await api.get<VoiceWebRTCResponse>('/voice/test');
    return response;
    },
    getConfig: async (): Promise<VoiceConfiguration> => {
    const response = await api.get<VoiceConfiguration>('/voice/config');
    return response;
    },
    updateConfig: async (config: VoiceConfiguration): Promise<{ status: string; message: string }> => {
    const response = await api.put('/voice/config', config);
    return response;
    },
    getModels: async (): Promise<{ groq: VoiceModel[]; openai: VoiceModel[] }> => {
    const response = await api.get('/voice/models');
    return response;
    },
    getVoices: async (forceRefresh = false): Promise<{ voices: VoiceOption[]; count: number; elevenlabs_configured: boolean }> => {
    const response = await api.get('/voice/voices', { params: { force_refresh: forceRefresh } });
    return response;
    },
    getTools: async (): Promise<{ tools: VoiceTool[] }> => {
    const response = await api.get('/voice/tools');
    return response;
    },
    getVapiConfig: async (): Promise<{ publicKey: string; assistantId: string }> => {
    const response = await api.get('/voice/vapi-config');
    return response;
    },
};
