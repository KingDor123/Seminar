import { db } from '../config/databaseConfig.js';
import { ChatRepo, TurnAnalysisInput } from '../repositories/chat.repo.js';
import { fetchScenarioById } from './scenario.service.js';

const chatRepo = new ChatRepo(db);

const normalizeSentiment = (value: unknown): 'positive' | 'negative' | 'neutral' | null => {
    if (typeof value !== 'string') return null;
    const normalized = value.toLowerCase().trim();
    if (normalized === 'positive' || normalized === 'negative' || normalized === 'neutral') {
        return normalized;
    }
    return null;
};

const coerceAnalysis = (analysis: unknown): TurnAnalysisInput | null => {
    if (!analysis || typeof analysis !== 'object') {
        return null;
    }
    const record = analysis as Record<string, unknown>;
    const sentiment = normalizeSentiment(record.sentiment);
    const confidence = typeof record.confidence === 'number' ? record.confidence : parseFloat(String(record.confidence));
    if (!sentiment || Number.isNaN(confidence)) {
        return null;
    }
    const boundedConfidence = Math.max(0, Math.min(1, confidence));
    const detected_intent = typeof record.detected_intent === 'string' ? record.detected_intent : '';
    const social_impact = typeof record.social_impact === 'string' ? record.social_impact : '';
    const reasoning = typeof record.reasoning === 'string' ? record.reasoning : '';
    if (!detected_intent || !social_impact || !reasoning) {
        return null;
    }
    return {
        sentiment,
        confidence: boundedConfidence,
        detected_intent,
        social_impact,
        reasoning
    };
};

export const startSession = async (userId: number, scenarioId: string) => {
    if (!userId) throw new Error('User ID is required');
    if (!scenarioId || typeof scenarioId !== 'string' || scenarioId.trim().length === 0) {
        throw new Error('Valid Scenario ID is required');
    }
    const scenario = fetchScenarioById(scenarioId);
    if (!scenario) {
        throw new Error('Scenario not found');
    }
    return await chatRepo.createSession(userId, scenarioId);
};

export const saveMessage = async (
    sessionId: number,
    role: string,
    content: string,
    sentiment?: string,
    analysis?: TurnAnalysisInput
) => {
    if (!sessionId) throw new Error('Session ID is required');
    const normalizedRole = role === 'assistant' ? 'ai' : role;
    if (!normalizedRole || !['user', 'ai'].includes(normalizedRole)) {
         throw new Error('Valid role (user/ai) is required');
    }
    if (!content || content.trim().length === 0) {
        throw new Error('Message content cannot be empty');
    }
    const normalizedAnalysis = coerceAnalysis(analysis);
    if (analysis && normalizedRole === 'user' && !normalizedAnalysis) {
        throw new Error('Invalid analysis payload');
    }
    if (normalizedAnalysis && normalizedRole === 'user') {
        return await chatRepo.addMessageWithAnalysis(sessionId, normalizedRole, content, normalizedAnalysis);
    }

    if (sentiment && normalizedRole === 'ai') {
        await chatRepo.updateLatestUserSentiment(sessionId, sentiment);
    }

    const sentimentToStore = normalizedRole === 'ai' ? null : sentiment;
    return await chatRepo.addMessage(sessionId, normalizedRole, content, sentimentToStore);
};

export const getUserSessions = async (userId: number) => {
    return await chatRepo.getSessionsByUserId(userId);
};

export const getSessionHistory = async (sessionId: number, includeAnalysis = false) => {
    if (includeAnalysis) {
        return await chatRepo.getMessagesBySessionIdWithAnalysis(sessionId);
    }
    return await chatRepo.getMessagesBySessionId(sessionId);
};
