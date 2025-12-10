import { db } from '../config/databaseConfig.js';

export const runMigrations = async (): Promise<void> => {
    console.log('Running database migrations...');
    try {
        // Ensure users table exists with correct schema
        await db.execute(`
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        `);

        // Add password_hash column if it doesn't exist
        await db.execute(`
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='password_hash') THEN
                    ALTER TABLE users ADD COLUMN password_hash VARCHAR(200);
                END IF;
            END $$;
        `);

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
    }
};