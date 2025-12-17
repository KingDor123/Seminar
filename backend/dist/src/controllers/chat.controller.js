import * as chatService from '../services/chat.service.js';
export const startSession = async (req, res) => {
    try {
        const { userId, scenarioId } = req.body;
        if (!userId || isNaN(parseInt(userId))) {
            res.status(400).json({ error: 'Valid User ID is required' });
            return;
        }
        const session = await chatService.startSession(parseInt(userId), scenarioId);
        res.status(201).json(session);
    }
    catch (error) {
        console.error('Start Session Error:', error);
        res.status(500).json({ error: error.message });
    }
};
export const saveMessage = async (req, res) => {
    try {
        const { sessionId } = req.params;
        const { role, content } = req.body;
        const sId = parseInt(sessionId);
        if (isNaN(sId)) {
            res.status(400).json({ error: 'Valid Session ID is required' });
            return;
        }
        // Ensure sessionId is parsed to a number if your DB expects it, or keep as string if UUID
        const message = await chatService.saveMessage(sId, role, content);
        res.status(201).json(message);
    }
    catch (error) {
        console.error('Save Message Error:', error);
        res.status(500).json({ error: error.message });
    }
};
export const getUserSessions = async (req, res) => {
    try {
        const { userId } = req.params;
        const uId = parseInt(userId);
        if (isNaN(uId)) {
            res.status(400).json({ error: 'Valid User ID is required' });
            return;
        }
        const sessions = await chatService.getUserSessions(uId);
        res.json(sessions);
    }
    catch (error) {
        console.error('Get User Sessions Error:', error);
        res.status(500).json({ error: error.message });
    }
};
export const getSessionHistory = async (req, res) => {
    try {
        const { sessionId } = req.params;
        const sId = parseInt(sessionId);
        if (isNaN(sId)) {
            res.status(400).json({ error: 'Valid Session ID is required' });
            return;
        }
        const messages = await chatService.getSessionHistory(sId);
        res.json(messages);
    }
    catch (error) {
        console.error('Get Session History Error:', error);
        res.status(500).json({ error: error.message });
    }
};
