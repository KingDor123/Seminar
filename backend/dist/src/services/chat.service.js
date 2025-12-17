import { db } from '../config/databaseConfig.js';
import { ChatRepo } from '../repositories/chat.repo.js';
const chatRepo = new ChatRepo(db);
export const startSession = async (userId, scenarioId) => {
    if (!userId)
        throw new Error('User ID is required');
    if (!scenarioId || typeof scenarioId !== 'string' || scenarioId.trim().length === 0) {
        throw new Error('Valid Scenario ID is required');
    }
    return await chatRepo.createSession(userId, scenarioId);
};
export const saveMessage = async (sessionId, role, content) => {
    if (!sessionId)
        throw new Error('Session ID is required');
    if (!role || !['user', 'ai'].includes(role)) {
        throw new Error('Valid role (user/ai) is required');
    }
    if (!content || content.trim().length === 0) {
        throw new Error('Message content cannot be empty');
    }
    return await chatRepo.addMessage(sessionId, role, content);
};
export const getUserSessions = async (userId) => {
    return await chatRepo.getSessionsByUserId(userId);
};
export const getSessionHistory = async (sessionId) => {
    return await chatRepo.getMessagesBySessionId(sessionId);
};
