import { Pool, QueryResult, PoolClient } from 'pg';
import dotenv from 'dotenv';

dotenv.config();

export class Database {
  private static instance: Database;
  private pool!: Pool;

  constructor() {
    if (Database.instance) {
      return Database.instance;
    }

    if (process.env.NODE_ENV === 'test') {
      this.pool = {
        query: async () => {
          throw new Error('Database access is disabled in test mode');
        },
        end: async () => {},
      } as unknown as Pool;

      Database.instance = this;
      return;
    }

    if (!process.env.DB_USER || !process.env.DB_PASSWORD) {
      throw new Error('Missing required database credentials (DB_USER, DB_PASSWORD). Check your .env file.');
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

    const connectWithRetry = async (retries: number) => {
      try {
        const client = await this.pool.connect();
        console.log('Connected to PostgreSQL successfully');
        client.release();
      } catch (err) {
        console.error(`PostgreSQL connection error: ${(err as any).message}. Retries left: ${retries}`);
        if (retries > 0) {
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
          await connectWithRetry(retries - 1);
        } else {
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

  async execute<T = any>(sql: string, params: any[] = []): Promise<T[]> {
    try {
      const result: QueryResult = await this.pool.query(sql, params);
      return result.rows;
    } catch (error) {
      console.error('PostgreSQL query error:', { sql, params, error });
      throw error;
    }
  }

  async executeWithClient<T = any>(client: PoolClient, sql: string, params: any[] = []): Promise<T[]> {
    try {
      const result = await client.query(sql, params);
      return result.rows as T[];
    } catch (error) {
      console.error('PostgreSQL query error (transaction):', { sql, params, error });
      throw error;
    }
  }

  async transaction<T>(fn: (client: PoolClient) => Promise<T>): Promise<T> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const result = await fn(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async close(): Promise<void> {
    try {
      await this.pool.end();
      console.log('PostgreSQL pool closed');
    } catch (error) {
      console.error('Error closing PostgreSQL connection:', error);
      throw error;
    }
  }
}

export const db = new Database();
