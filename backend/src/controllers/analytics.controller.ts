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
        
        // Transform to match frontend expectation if needed (e.g. map fields)
        // Frontend expects: [{ session_id, score, fluency, fillers, date }]
        // Our repo returns: [{ session_id, scenario_id, start_time, score }]
        
        const data = summaries.map(s => ({
            session_id: s.session_id,
            score: s.score || 0,
            fluency: 0, // Placeholder as detailed metrics logic was in AI service sql
            fillers: 0, // Placeholder
            date: s.start_time
        }));

        res.json(data);
    } catch (error: any) {
        console.error('Get Sessions Summary Error:', error);
        res.status(500).json({ error: 'Failed to fetch session summary', details: error.message });
    }
};
