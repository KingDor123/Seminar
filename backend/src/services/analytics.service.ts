import { db } from '../config/databaseConfig.js';
import { AnalyticsRepo } from '../repositories/analytics.repo.js';

const analyticsRepo = new AnalyticsRepo(db);

export const recordMetric = async (sessionId: number, name: string, value: number, context: string = '') => {
    if (!sessionId || !name) {
        throw new Error('Session ID and metric name are required');
    }
    return await analyticsRepo.addMetric(sessionId, name, value, context);
};

export const generateReport = async (sessionId: number, overallScore: number, feedback: string) => {
    return await analyticsRepo.createReport(sessionId, overallScore, feedback);
};

export const getSessionMetrics = async (sessionId: number) => {
    return await analyticsRepo.getMetricsBySession(sessionId);
};

export const getSessionReport = async (sessionId: number) => {
    return await analyticsRepo.getReportBySession(sessionId);
};

export const getSessionsSummary = async (userId: number) => {
    return await analyticsRepo.getSessionsSummary(userId);
};

export const getDashboardStats = async (userId: number) => {
    return await analyticsRepo.getDashboardStats(userId);
};
