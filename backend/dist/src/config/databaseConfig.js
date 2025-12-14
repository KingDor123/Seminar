import { Pool } from 'pg';
import dotenv from 'dotenv';
dotenv.config();
export class Database {
    static instance;
    pool;
    constructor() {
        if (Database.instance) {
            return Database.instance;
        }
        if (process.env.NODE_ENV === 'test') {
            this.pool = {
                query: async () => {
                    throw new Error('Database access is disabled in test mode');
                },
                end: async () => { },
            };
            Database.instance = this;
            return;
        }
        this.pool = new Pool({
            host: process.env.DB_HOST,
            user: process.env.DB_USER,
            password: process.env.DB_PASSWORD,
            database: process.env.DB_NAME,
            port: parseInt(process.env.DB_PORT || '5432', 10),
            max: 10,
            idleTimeoutMillis: 30000,
            connectionTimeoutMillis: 2000,
        });
        // Log connection success or failure with retry mechanism
        const MAX_RETRIES = 5;
        const RETRY_DELAY_MS = 3000; // 3 seconds
        const connectWithRetry = async (retries) => {
            try {
                const client = await this.pool.connect();
                console.log('Connected to PostgreSQL successfully');
                client.release();
            }
            catch (err) {
                console.error(`PostgreSQL connection error: ${err.message}. Retries left: ${retries}`);
                if (retries > 0) {
                    await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
                    await connectWithRetry(retries - 1);
                }
                else {
                    console.error('Max retries reached. Could not connect to PostgreSQL.');
                    throw err; // Re-throw error if max retries are reached
                }
            }
        };
        connectWithRetry(MAX_RETRIES).catch(err => {
            console.error('Failed to establish PostgreSQL connection after multiple attempts:', err);
            // Depending on desired behavior, you might want to exit the process here
            // process.exit(1); 
        });
        Database.instance = this;
    }
    async execute(sql, params = []) {
        try {
            const result = await this.pool.query(sql, params);
            return result.rows;
        }
        catch (error) {
            console.error('PostgreSQL query error:', { sql, params, error });
            throw error;
        }
    }
    async close() {
        try {
            await this.pool.end();
            console.log('PostgreSQL pool closed');
        }
        catch (error) {
            console.error('Error closing PostgreSQL connection:', error);
            throw error;
        }
    }
}
export const db = new Database();
