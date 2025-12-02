import pkg from 'pg';
import dotenv from 'dotenv';

dotenv.config();

const { Pool } = pkg;

class Database {
  static instance;

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
      };

      Database.instance = this;
      return;
    }

    this.pool = new Pool({
      host: process.env.DB_HOST,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
      database: process.env.DB_NAME,
      port: process.env.DB_PORT || 5432,
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    // Log connection success or failure
    this.pool
      .connect()
      .then(client => {
        console.log('Connected to PostgreSQL successfully');
        client.release();
      })
      .catch(err => {
        console.error('PostgreSQL connection error:', err);
      });

    Database.instance = this;
  }

  async execute(sql, params = []) {
    try {
      const result = await this.pool.query(sql, params);
      return result.rows;
    } catch (error) {
      console.error('PostgreSQL query error:', { sql, params, error });
      throw error;
    }
  }

  async close() {
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
