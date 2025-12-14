-- יצירת ENUM לתפקידים (אופציונלי אבל מקצועי)
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('user', 'admin');
    END IF;
END $$;

-- טבלת משתמשים
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    role user_role NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- טבלת סשנים (שיחות)
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    scenario_id VARCHAR(50) NOT NULL,
    start_time TIMESTAMP DEFAULT NOW(),
    end_time TIMESTAMP
);

-- טבלת הודעות
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'ai', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- טבלת מדדים (Metrics)
CREATE TABLE IF NOT EXISTS session_metrics (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    metric_name VARCHAR(50) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    context TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- טבלת דוחות (Reports)
CREATE TABLE IF NOT EXISTS social_reports (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id) ON DELETE CASCADE,
    overall_score DOUBLE PRECISION,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- טריגר לעדכון updated_at אוטומטי
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_timestamp ON users;

CREATE TRIGGER update_users_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_timestamp();

-- dummy data
INSERT INTO users (full_name, email, password_hash, role)
VALUES ('Admin User', 'admin@example.com', 'hashed-password-here', 'admin')
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (full_name, email, password_hash, role)
VALUES ('Demo User', 'user@example.com', 'hashed-password-here', 'user')
ON CONFLICT (email) DO NOTHING;