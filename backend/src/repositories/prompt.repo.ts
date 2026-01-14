import { Database } from '../config/databaseConfig.js';

export interface Prompt {
    id: number;
    key: string;
    type: string;
    scenario_id?: string;
    persona_name?: string;
    version: number;
    is_active: boolean;
    content: string;
    created_at: Date;
    updated_at: Date;
}

export class PromptRepo {
    private db: Database;

    constructor(db: Database) {
        this.db = db;
    }

    /**
     * Fetches a single active prompt by its unique key.
     */
    async getPromptByKey(key: string): Promise<Prompt | null> {
        const sql = `
            SELECT * FROM prompts 
            WHERE key = $1 AND is_active = TRUE 
            LIMIT 1
        `;
        const rows = await this.db.execute<Prompt>(sql, [key]);
        return rows[0] || null;
    }

    /**
     * Fetches the latest active system prompt for a specific scenario.
     * Assumes one main system prompt per scenario for now.
     */
    async getSystemPromptByScenarioId(scenarioId: string): Promise<Prompt | null> {
        const sql = `
            SELECT * FROM prompts 
            WHERE scenario_id = $1 AND type = 'system' AND is_active = TRUE
            ORDER BY version DESC
            LIMIT 1
        `;
        const rows = await this.db.execute<Prompt>(sql, [scenarioId]);
        return rows[0] || null;
    }
}
