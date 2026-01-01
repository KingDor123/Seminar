import { Request, Response } from 'express';
import * as analyticsService from '../services/analytics.service.js';
import { AI_SERVICE_BASE_URL, REQUEST_TIMEOUT_MS } from '../config/appConfig.js';

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

        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
        const aiBase = AI_SERVICE_BASE_URL.replace(/\/ai$/, '');
        const url = `${aiBase}/analytics/sessions/summary?user_id=${userId}`;

        const response = await fetch(url, { signal: controller.signal });
        clearTimeout(timeout);

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`AI service responded ${response.status}: ${errText}`);
        }

        const data = await response.json();
        res.json(data);
    } catch (error: any) {
        const status = error.name === 'AbortError' ? 504 : 502;
        console.error('Get Sessions Summary Error:', error);
        res.status(status).json({ error: 'Failed to fetch session summary', details: error.message });
    }
};
