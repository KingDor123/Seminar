import * as chatService from '../services/chat.service.js';

export const startSession = async (req, res) => {
    try {
        const { userId, scenarioId } = req.body;
        const session = await chatService.startSession(userId, scenarioId);
        res.status(201).json(session);
    } catch (error) {
        console.error('Start Session Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const saveMessage = async (req, res) => {
    try {
        const { sessionId } = req.params;
        const { role, content } = req.body;
        const message = await chatService.saveMessage(sessionId, role, content);
        res.status(201).json(message);
    } catch (error) {
        console.error('Save Message Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getUserSessions = async (req, res) => {
    try {
        const { userId } = req.params;
        const sessions = await chatService.getUserSessions(userId);
        res.json(sessions);
    } catch (error) {
        console.error('Get User Sessions Error:', error);
        res.status(500).json({ error: error.message });
    }
};

export const getSessionHistory = async (req, res) => {
    try {
        const { sessionId } = req.params;
        const messages = await chatService.getSessionHistory(sessionId);
        res.json(messages);
    } catch (error) {
        console.error('Get Session History Error:', error);
        res.status(500).json({ error: error.message });
    }
};
