import { Request, Response } from 'express';
import * as chatService from '../services/chat.service.js';

export const startSession = async (req: Request, res: Response) => {
    try {
        const { userId, scenarioId } = req.body;
        const session = await chatService.startSession(userId, scenarioId);
        res.status(201).json(session);
    } catch (error: any) {
        console.error('Start Session Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const saveMessage = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const { role, content } = req.body;
        // Ensure sessionId is parsed to a number if your DB expects it, or keep as string if UUID
        const message = await chatService.saveMessage(parseInt(sessionId), role, content);
        res.status(201).json(message);
    } catch (error: any) {
        console.error('Save Message Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getUserSessions = async (req: Request, res: Response) => {
    try {
        const { userId } = req.params;
        const sessions = await chatService.getUserSessions(parseInt(userId));
        res.json(sessions);
    } catch (error: any) {
        console.error('Get User Sessions Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getSessionHistory = async (req: Request, res: Response) => {
    try {
        const { sessionId } = req.params;
        const messages = await chatService.getSessionHistory(parseInt(sessionId));
        res.json(messages);
    } catch (error: any) {
        console.error('Get Session History Error:', error);
        res.status(500).json({ error: error.message });
    }
};
