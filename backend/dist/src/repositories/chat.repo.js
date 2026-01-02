export class ChatRepo {
    db;
    constructor(db) {
        this.db = db;
    }
    async createSession(userId, scenarioId) {
        const sql = 'INSERT INTO sessions (user_id, scenario_id) VALUES ($1, $2) RETURNING *';
        const params = [userId, scenarioId];
        const result = await this.db.execute(sql, params);
        return result[0];
    }
    async addMessage(sessionId, role, content, sentiment) {
        const sql = 'INSERT INTO messages (session_id, role, content, sentiment) VALUES ($1, $2, $3, $4) RETURNING *';
        const params = [sessionId, role, content, sentiment ?? null];
        const result = await this.db.execute(sql, params);
        return result[0];
    }
    async getSessionsByUserId(userId) {
        const sql = 'SELECT * FROM sessions WHERE user_id = $1 ORDER BY start_time DESC';
        const params = [userId];
        return await this.db.execute(sql, params);
    }
    async getMessagesBySessionId(sessionId) {
        const sql = 'SELECT id, session_id, role, content, sentiment, created_at FROM messages WHERE session_id = $1 ORDER BY created_at ASC';
        const params = [sessionId];
        return await this.db.execute(sql, params);
    }
    async getSessionById(sessionId) {
        const sql = 'SELECT * FROM sessions WHERE id = $1';
        const params = [sessionId];
        const result = await this.db.execute(sql, params);
        return result[0];
    }
}
