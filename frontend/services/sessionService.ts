import axios from '../lib/api'; // Re-use the existing axios instance for consistency with credentials

interface Session {
    id: number;
    user_id: number;
    scenario_id: string;
    start_time: string; // ISO string
    end_time?: string; // ISO string
}

interface ChatMessage {
    id: number;
    session_id: number;
    role: 'user' | 'ai';
    content: string;
    created_at: string;
}

interface Metric {
    id: number;
    session_id: number;
    metric_name: string;
    metric_value: number;
    context?: string;
    created_at: string;
}

export const sessionService = {
    getUserSessions: async (userId: number): Promise<Session[]> => {
        const response = await axios.get(`/chat/users/${userId}/sessions`);
        return response.data;
    },
    
    getSessionMessages: async (sessionId: number): Promise<ChatMessage[]> => {
        const response = await axios.get(`/chat/sessions/${sessionId}/messages`);
        return response.data;
    },

    getSessionMetrics: async (sessionId: number): Promise<Metric[]> => {
        const response = await axios.get(`/analytics/sessions/${sessionId}/metrics`);
        return response.data;
    }
};
