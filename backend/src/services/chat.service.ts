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

/**
 * Adapter to coerce incoming analysis payload into the legacy DB schema.
 * Handles both:
 * 1. Legacy Schema (confidence, detected_intent, social_impact, reasoning)
 * 2. V2 Schema (metrics, decision, reasons[], passed, current_state)
 */
const coerceAnalysis = (analysis: unknown): TurnAnalysisInput | null => {
    if (!analysis || typeof analysis !== 'object') {
        return null;
    }
    const record = analysis as Record<string, unknown>;
    
    // --- V2 SCHEMA ADAPTER ---
    // Detection: Presence of 'metrics' object or 'decision' string
    if ('metrics' in record || 'decision' in record) {
        try {
            // 1. Sentiment (Preserve or Default)
            const sentiment = normalizeSentiment(record.sentiment) || 'neutral';
            
            // 2. Confidence Mapping (passed -> legacy confidence)
            // passed=true -> 0.9 (High confidence)
            // passed=false -> 0.3 (Low confidence)
            const passed = record.passed === true;
            const confidence = passed ? 0.9 : 0.3;
            
            // 3. Detected Intent -> Decision Label
            const detected_intent = typeof record.decision === 'string' 
                ? record.decision 
                : 'UNKNOWN_DECISION';
                
            // 4. Reasoning -> Join array
            let reasoning = 'No reasons provided';
            if (Array.isArray(record.reasons)) {
                reasoning = record.reasons.join('; ');
            } else if (typeof record.reasons === 'string') {
                reasoning = record.reasons;
            } else if (typeof record.reasoning === 'string') {
                // Fallback if V2 mixed with V1 naming
                reasoning = record.reasoning;
            }

            // 5. Social Impact -> JSON Storage Wrapper
            // We store the full structured data here to preserve it
            const wrapper = {
                _compat: "v2_analysis_to_legacy",
                decision: record.decision,
                passed: record.passed,
                metrics: record.metrics || {},
                state: record.current_state,
                sentiment: sentiment
            };
            
            // Safe Stringify
            let social_impact = '{}';
            try {
                social_impact = JSON.stringify(wrapper);
            } catch (e) {
                console.warn('[Adapter] Failed to stringify metrics for social_impact', e);
                social_impact = JSON.stringify({ error: 'Serialization Failed' });
            }

            // Log once (optional, keeping minimal per instructions)
            // console.warn('[LegacyAdapter] Converted V2 analysis payload to V1 schema');

            return {
                sentiment,
                confidence,
                detected_intent,
                social_impact,
                reasoning
            };

        } catch (err) {
            console.error('[Adapter] V2 Schema conversion failed:', err);
            return null;
        }
    }

    // --- LEGACY SCHEMA VALIDATION ---
    const sentiment = normalizeSentiment(record.sentiment);
    const confidence = typeof record.confidence === 'number' ? record.confidence : parseFloat(String(record.confidence));
    if (!sentiment || Number.isNaN(confidence)) {
        return null;
    }
    const boundedConfidence = Math.max(0, Math.min(1, confidence));
    const detected_intent = typeof record.detected_intent === 'string' ? record.detected_intent : '';
    const social_impact = typeof record.social_impact === 'string' ? record.social_impact : '';
    const reasoning = typeof record.reasoning === 'string' ? record.reasoning : '';
    
    // Strict legacy check: all fields required
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
