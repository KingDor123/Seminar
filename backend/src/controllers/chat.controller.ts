import { Request, Response } from 'express';
import * as chatService from '../services/chat.service.js';

export const startSession = async (req: Request, res: Response) => {
    try {
        const { userId, scenarioId } = req.body;
        if (!userId || isNaN(parseInt(userId))) {
            res.status(400).json({ error: 'Valid User ID is required' });
            return;
        }
        const session = await chatService.startSession(parseInt(userId), scenarioId);
        res.status(201).json(session);
    } catch (error: any) {
        console.error('Start Session Error:', error);
        const message = error?.message || 'Unknown error';
        if (message === 'Valid Scenario ID is required' || message === 'Scenario not found' || message === 'User ID is required') {
            res.status(400).json({ error: message });
            return;
        }
        res.status(500).json({ error: message });
    }
};

export const saveMessage = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const { role, content, sentiment, analysis } = req.body;
        
        const sId = parseInt(sessionId);
        if (isNaN(sId)) {
             res.status(400).json({ error: 'Valid Session ID is required' });
             return;
        }

        // Ensure sessionId is parsed to a number if your DB expects it, or keep as string if UUID
        const message = await chatService.saveMessage(sId, role, content, sentiment, analysis);
        res.status(201).json(message);
    } catch (error: any) {
        console.error('Save Message Error:', error);
        const message = error?.message || 'Unknown error';
        const badRequestErrors = new Set([
            'Valid Session ID is required',
            'Valid role (user/ai) is required',
            'Message content cannot be empty',
            'Invalid analysis payload'
        ]);
        if (badRequestErrors.has(message)) {
            res.status(400).json({ error: message });
            return;
        }
        res.status(500).json({ error: message });
    }
};

export const getUserSessions = async (req: Request, res: Response) => {
    try {
        const { userId } = req.params;
        const uId = parseInt(userId);
        if (isNaN(uId)) {
            res.status(400).json({ error: 'Valid User ID is required' });
            return;
        }
        const sessions = await chatService.getUserSessions(uId);
        res.json(sessions);
    } catch (error: any) {
        console.error('Get User Sessions Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getSessionHistory = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const includeAnalysis = req.query.include_analysis === 'true';
        const sId = parseInt(sessionId);
        if (isNaN(sId)) {
            res.status(400).json({ error: 'Valid Session ID is required' });
            return;
        }
        const messages = await chatService.getSessionHistory(sId, includeAnalysis);
        res.json(messages);
    } catch (error: any) {
        console.error('Get Session History Error:', error);
        res.status(500).json({ error: error.message });
    }
};
