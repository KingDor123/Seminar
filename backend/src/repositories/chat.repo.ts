
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
    created_at: Date;
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

    async addMessage(sessionId: number, role: string, content: string): Promise<ChatMessage> {
        const sql = 'INSERT INTO messages (session_id, role, content) VALUES ($1, $2, $3) RETURNING *';
        const params = [sessionId, role, content];
        const result = await this.db.execute<ChatMessage>(sql, params);
        return result[0];
    }

    async getSessionsByUserId(userId: number): Promise<ChatSession[]> {
        const sql = 'SELECT * FROM sessions WHERE user_id = $1 ORDER BY start_time DESC';
        const params = [userId];
        return await this.db.execute<ChatSession>(sql, params);
    }

    async getMessagesBySessionId(sessionId: number): Promise<ChatMessage[]> {
        const sql = 'SELECT * FROM messages WHERE session_id = $1 ORDER BY created_at ASC';
        const params = [sessionId];
        return await this.db.execute<ChatMessage>(sql, params);
    }

    async getSessionById(sessionId: number): Promise<ChatSession | undefined> {
        const sql = 'SELECT * FROM sessions WHERE id = $1';
        const params = [sessionId];
        const result = await this.db.execute<ChatSession>(sql, params);
        return result[0];
    }
}
