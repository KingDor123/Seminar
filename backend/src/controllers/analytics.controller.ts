import { Request, Response } from 'express';
import * as analyticsService from '../services/analytics.service.js';

export const saveMetric = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const { name, value, context } = req.body;
        const metric = await analyticsService.recordMetric(parseInt(sessionId), name, value, context);
        res.status(201).json(metric);
    } catch (error: any) {
        console.error('Save Metric Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const saveReport = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const { overallScore, feedback } = req.body;
        const report = await analyticsService.generateReport(parseInt(sessionId), overallScore, feedback);
        res.status(201).json(report);
    } catch (error: any) {
        console.error('Save Report Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getMetrics = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const metrics = await analyticsService.getSessionMetrics(parseInt(sessionId));
        res.json(metrics);
    } catch (error: any) {
        console.error('Get Metrics Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getReport = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const report = await analyticsService.getSessionReport(parseInt(sessionId));
        if (!report) {
             res.status(404).json({ message: 'Report not found' });
             return;
        }
        res.json(report);
    } catch (error: any) {
        console.error('Get Report Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getSessionsSummary = async (req: Request, res: Response) => {
    try {
        const userId = req.user?.id;
        if (!userId) {
            res.status(401).json({ error: 'Authentication required' });
            return;
        }

        const summaries = await analyticsService.getSessionsSummary(userId);
        
        // Frontend expects: SessionListItem { session_id, created_at, scenario_id, message_count, overall_sentiment }
        const data = summaries.map(s => ({
            session_id: s.session_id,
            created_at: s.created_at,
            scenario_id: s.scenario_id,
            message_count: parseInt(s.message_count || '0'),
            overall_sentiment: s.score > 8 ? 'Positive' : (s.score < 5 ? 'Negative' : 'Neutral') // Infer sentiment from score if not stored
        }));

        res.json(data);
    } catch (error: any) {
        console.error('Get Sessions Summary Error:', error);
        res.status(500).json({ error: 'Failed to fetch session summary', details: error.message });
    }
};

export const getDashboardStats = async (req: Request, res: Response) => {
    try {
        const userId = req.user?.id;
        if (!userId) {
            res.status(401).json({ error: 'Authentication required' });
            return;
        }

        const stats = await analyticsService.getDashboardStats(userId);
        res.json(stats);
    } catch (error: any) {
        console.error('Get Dashboard Stats Error:', error);
        res.status(500).json({ error: 'Failed to fetch dashboard stats', details: error.message });
    }
};
