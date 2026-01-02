
import { Database } from '../config/databaseConfig.js';

export interface ChatSession {
    id: number;
    user_id: number;
    scenario_id: string;
    start_time: Date;
    end_time?: Date;
}

export interface ChatMessage {
    id: number;
    session_id: number;
    role: 'user' | 'ai' | 'system';
    content: string;
    sentiment?: string | null;
    created_at: Date;
}

export interface TurnAnalysis {
    id: number;
    session_id: number;
    message_id: number;
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number;
    detected_intent: string;
    social_impact: string;
    reasoning: string;
    created_at: Date;
}

export interface TurnAnalysisInput {
    sentiment: 'positive' | 'negative' | 'neutral';
    confidence: number;
    detected_intent: string;
    social_impact: string;
    reasoning: string;
}

export interface ChatMessageWithAnalysis extends ChatMessage {
    analysis?: TurnAnalysis | null;
}

export class ChatRepo {
    private db: Database;

    constructor(db: any) { // Type as 'any' or import the class type from databaseConfig if exported
        this.db = db;
    }

    async createSession(userId: number, scenarioId: string): Promise<ChatSession> {
        const sql = 'INSERT INTO sessions (user_id, scenario_id) VALUES ($1, $2) RETURNING *';
        const params = [userId, scenarioId];
        const result = await this.db.execute<ChatSession>(sql, params);
        return result[0];
    }

    async addMessage(sessionId: number, role: string, content: string, sentiment?: string | null): Promise<ChatMessage> {
        const sql = 'INSERT INTO messages (session_id, role, content, sentiment) VALUES ($1, $2, $3, $4) RETURNING *';
        const params = [sessionId, role, content, sentiment ?? null];
        const result = await this.db.execute<ChatMessage>(sql, params);
        return result[0];
    }

    async addMessageWithAnalysis(
        sessionId: number,
        role: string,
        content: string,
        analysis: TurnAnalysisInput
    ): Promise<ChatMessage> {
        return await this.db.transaction(async (client) => {
            const messageSql = `
                INSERT INTO messages (session_id, role, content, sentiment)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            `;
            const messageParams = [sessionId, role, content, analysis.sentiment];
            const messageRows = await this.db.executeWithClient<ChatMessage>(client, messageSql, messageParams);
            const message = messageRows[0];

            const analysisSql = `
                INSERT INTO turn_analyses (
                    session_id,
                    message_id,
                    sentiment,
                    confidence,
                    detected_intent,
                    social_impact,
                    reasoning
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            `;
            const analysisParams = [
                sessionId,
                message.id,
                analysis.sentiment,
                analysis.confidence,
                analysis.detected_intent,
                analysis.social_impact,
                analysis.reasoning
            ];
            await this.db.executeWithClient(client, analysisSql, analysisParams);
            return message;
        });
    }

    async updateLatestUserSentiment(sessionId: number, sentiment: string): Promise<ChatMessage | undefined> {
        const sql = `
            WITH latest AS (
                SELECT id
                FROM messages
                WHERE session_id = $1 AND role = 'user'
                ORDER BY created_at DESC, id DESC
                LIMIT 1
            )
            UPDATE messages m
            SET sentiment = $2
            FROM latest
            WHERE m.id = latest.id
            RETURNING m.*
        `;
        const params = [sessionId, sentiment];
        const result = await this.db.execute<ChatMessage>(sql, params);
        return result[0];
    }

    async getSessionsByUserId(userId: number): Promise<ChatSession[]> {
        const sql = 'SELECT * FROM sessions WHERE user_id = $1 ORDER BY start_time DESC';
        const params = [userId];
        return await this.db.execute<ChatSession>(sql, params);
    }

    async getMessagesBySessionId(sessionId: number): Promise<ChatMessage[]> {
        const sql = 'SELECT id, session_id, role, content, sentiment, created_at FROM messages WHERE session_id = $1 ORDER BY created_at ASC';
        const params = [sessionId];
        return await this.db.execute<ChatMessage>(sql, params);
    }

    async getMessagesBySessionIdWithAnalysis(sessionId: number): Promise<ChatMessageWithAnalysis[]> {
        const sql = `
            SELECT
                m.id,
                m.session_id,
                m.role,
                m.content,
                m.sentiment,
                m.created_at,
                ta.id AS analysis_id,
                ta.sentiment AS analysis_sentiment,
                ta.confidence AS analysis_confidence,
                ta.detected_intent AS analysis_detected_intent,
                ta.social_impact AS analysis_social_impact,
                ta.reasoning AS analysis_reasoning,
                ta.created_at AS analysis_created_at
            FROM messages m
            LEFT JOIN turn_analyses ta ON ta.message_id = m.id
            WHERE m.session_id = $1
            ORDER BY m.created_at ASC, m.id ASC
        `;
        const params = [sessionId];
        const rows = await this.db.execute<any>(sql, params);
        return rows.map((row) => ({
            id: row.id,
            session_id: row.session_id,
            role: row.role,
            content: row.content,
            sentiment: row.sentiment,
            created_at: row.created_at,
            analysis: row.analysis_id
                ? {
                    id: row.analysis_id,
                    session_id: row.session_id,
                    message_id: row.id,
                    sentiment: row.analysis_sentiment,
                    confidence: row.analysis_confidence,
                    detected_intent: row.analysis_detected_intent,
                    social_impact: row.analysis_social_impact,
                    reasoning: row.analysis_reasoning,
                    created_at: row.analysis_created_at
                }
                : null
        }));
    }

    async getSessionById(sessionId: number): Promise<ChatSession | undefined> {
        const sql = 'SELECT * FROM sessions WHERE id = $1';
        const params = [sessionId];
        const result = await this.db.execute<ChatSession>(sql, params);
        return result[0];
    }
}
