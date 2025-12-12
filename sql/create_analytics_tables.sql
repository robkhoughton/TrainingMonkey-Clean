-- Analytics Tables Creation
-- Execute this in SQL Editor to create missing analytics tables

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER,
    session_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    integration_point VARCHAR(100),
    source_page VARCHAR(255) NOT NULL,
    target_page VARCHAR(255),
    event_data JSONB,
    timestamp TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET,
    referrer TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create tutorial_sessions table
CREATE TABLE IF NOT EXISTS tutorial_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tutorial_id VARCHAR(100) NOT NULL,
    started_at TIMESTAMP DEFAULT NOW(),
    start_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create tutorial_completions table
CREATE TABLE IF NOT EXISTS tutorial_completions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    tutorial_id VARCHAR(100) NOT NULL,
    completed_at TIMESTAMP DEFAULT NOW(),
    completion_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);

CREATE INDEX IF NOT EXISTS idx_tutorial_sessions_user_id ON tutorial_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_tutorial_sessions_tutorial_id ON tutorial_sessions(tutorial_id);

CREATE INDEX IF NOT EXISTS idx_tutorial_completions_user_id ON tutorial_completions(user_id);
CREATE INDEX IF NOT EXISTS idx_tutorial_completions_tutorial_id ON tutorial_completions(tutorial_id);

-- Verify tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('analytics_events', 'tutorial_sessions', 'tutorial_completions')
ORDER BY table_name;
