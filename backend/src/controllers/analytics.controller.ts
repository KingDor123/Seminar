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
