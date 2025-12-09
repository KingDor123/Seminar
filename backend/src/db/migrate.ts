import { db } from '../config/databaseConfig.js';

export const runMigrations = async (): Promise<void> => {
    console.log('Running database migrations...');
    try {
        // Create sessions table
        await db.execute(`
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                scenario_id VARCHAR(50) NOT NULL,
                start_time TIMESTAMP DEFAULT NOW(),
                end_time TIMESTAMP
            );
        `);

        // Create messages table
        await db.execute(`
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
                role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'ai', 'system')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
        `);
        
        console.log('Migrations completed successfully.');
    } catch (error) {
        console.error('Migration failed:', error);
        // Don't crash the app, but log the error.
        // Tables might already exist or connection might be flaky.
    }
};
