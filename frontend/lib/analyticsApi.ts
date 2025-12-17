import axios from './api'; // Re-use the existing axios instance for consistency with credentials

export const analyticsApi = {
    getMetricsForSession: async (sessionId: number) => {
        const response = await axios.get(`/analytics/sessions/${sessionId}/metrics`);
        return response.data;
    },
    getReportForSession: async (sessionId: number) => {
        const response = await axios.get(`/analytics/sessions/${sessionId}/report`);
        return response.data;
    },
    generateSessionReport: async (sessionId: number) => {
        const response = await axios.post(`/report/generate/${sessionId}`);
        return response.data;
    }
};
