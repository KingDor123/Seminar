import { Database } from '../config/databaseConfig.js';

export interface SessionMetric {
    id: number;
    session_id: number;
    metric_name: string;
    metric_value: number;
    context?: string;
    created_at: Date;
}

export interface SocialReport {
    id: number;
    session_id: number;
    overall_score: number;
    feedback: string;
    created_at: Date;
}

export class AnalyticsRepo {
    private db: Database;

    constructor(db: any) {
        this.db = db;
    }

    async addMetric(sessionId: number, name: string, value: number, context: string = ''): Promise<SessionMetric> {
        const sql = 'INSERT INTO session_metrics (session_id, metric_name, metric_value, context) VALUES ($1, $2, $3, $4) RETURNING *';
        const params = [sessionId, name, value, context];
        const result = await this.db.execute<SessionMetric>(sql, params);
        return result[0];
    }

    async createReport(sessionId: number, overallScore: number, feedback: string): Promise<SocialReport> {
        const sql = 'INSERT INTO social_reports (session_id, overall_score, feedback) VALUES ($1, $2, $3) RETURNING *';
        const params = [sessionId, overallScore, feedback];
        const result = await this.db.execute<SocialReport>(sql, params);
        return result[0];
    }

    async getMetricsBySession(sessionId: number): Promise<SessionMetric[]> {
        const sql = 'SELECT * FROM session_metrics WHERE session_id = $1 ORDER BY created_at ASC';
        const params = [sessionId];
        return await this.db.execute<SessionMetric>(sql, params);
    }

    async getReportBySession(sessionId: number): Promise<SocialReport | undefined> {
        const sql = 'SELECT * FROM social_reports WHERE session_id = $1 ORDER BY created_at DESC LIMIT 1';
        const params = [sessionId];
        const result = await this.db.execute<SocialReport>(sql, params);
        return result[0];
    }

    async getSessionsSummary(userId: number): Promise<any[]> {
        const sql = `
            SELECT 
                s.id AS session_id,
                s.scenario_id,
                s.start_time AS created_at,
                COALESCE(sr.overall_score, 0) as score,
                (SELECT COUNT(*) FROM messages m WHERE m.session_id = s.id) as message_count
            FROM sessions s
            LEFT JOIN social_reports sr ON sr.session_id = s.id
            WHERE s.user_id = $1
            ORDER BY s.start_time DESC
        `;
        const params = [userId];
        return await this.db.execute(sql, params);
    }

    async getDashboardStats(userId: number): Promise<any> {
        // Overview stats
        const overviewSql = `
            SELECT 
                COUNT(DISTINCT s.id) as total_sessions,
                COUNT(m.id) as total_messages,
                COALESCE(AVG(sr.overall_score), 0) as avg_score
            FROM sessions s
            LEFT JOIN messages m ON m.session_id = s.id
            LEFT JOIN social_reports sr ON sr.session_id = s.id
            WHERE s.user_id = $1
        `;
        
        // Sentiment distribution (from messages)
        const sentimentSql = `
            SELECT 
                COALESCE(m.sentiment, 'neutral') as sentiment,
                COUNT(*) as count
            FROM sessions s
            JOIN messages m ON m.session_id = s.id
            WHERE s.user_id = $1
            GROUP BY COALESCE(m.sentiment, 'neutral')
        `;

        const [overviewRes, sentimentRes] = await Promise.all([
            this.db.execute<any>(overviewSql, [userId]),
            this.db.execute<any>(sentimentSql, [userId])
        ]);

        const overview = overviewRes[0] || { total_sessions: 0, total_messages: 0, avg_score: 0 };
        
        // Process sentiment into positive/neutral/negative buckets
        const sentiment = { positive: 0, neutral: 0, negative: 0 };
        sentimentRes.forEach((row: any) => {
            const s = row.sentiment.toLowerCase();
            if (s.includes('positive') || s.includes('joy')) sentiment.positive += parseInt(row.count);
            else if (s.includes('negative') || s.includes('stress') || s.includes('anger')) sentiment.negative += parseInt(row.count);
            else sentiment.neutral += parseInt(row.count);
        });

        return { overview, sentiment };
    }
}
