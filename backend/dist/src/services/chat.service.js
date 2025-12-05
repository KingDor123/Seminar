import { db } from '../config/databaseConfig.js';
import { ChatRepo } from '../repositories/chat.repo.js';
const chatRepo = new ChatRepo(db);
export const startSession = async (userId, scenarioId) => {
    if (!userId || !scenarioId) {
        throw new Error('User ID and Scenario ID are required');
    }
    return await chatRepo.createSession(userId, scenarioId);
};
export const saveMessage = async (sessionId, role, content) => {
    if (!sessionId || !role || !content) {
        throw new Error('Session ID, role, and content are required');
    }
    return await chatRepo.addMessage(sessionId, role, content);
};
export const getUserSessions = async (userId) => {
    return await chatRepo.getSessionsByUserId(userId);
};
export const getSessionHistory = async (sessionId) => {
    return await chatRepo.getMessagesBySessionId(sessionId);
};
