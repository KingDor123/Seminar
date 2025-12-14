import axios from '../lib/api'; // Re-use the existing axios instance for consistency with credentials

interface Session {
    id: number;
    user_id: number;
    scenario_id: string;
    start_time: string; // ISO string
    end_time?: string; // ISO string
}

export const sessionService = {
    getUserSessions: async (userId: number): Promise<Session[]> => {
        const response = await axios.get(`/chat/users/${userId}/sessions`);
        return response.data;
    },
    // Potentially add other session-related calls here if needed, e.g., ending a session
};
