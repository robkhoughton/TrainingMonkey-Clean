-- Migration System Database Schema
-- This schema supports the existing user migration system

-- Migration status tracking table
CREATE TABLE IF NOT EXISTS migration_status (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed', 'rolled_back'
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP NULL,
    error_message TEXT NULL,
    rollback_available BOOLEAN DEFAULT TRUE,
    data_preserved BOOLEAN DEFAULT TRUE,
    strava_connected BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Migration snapshots table
CREATE TABLE IF NOT EXISTS migration_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_id VARCHAR(100) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'created', -- 'created', 'validated', 'expired'
    snapshot_size BIGINT NULL,
    checksum VARCHAR(64) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Migration snapshot data table (stores JSON data)
CREATE TABLE IF NOT EXISTS migration_snapshot_data (
    id SERIAL PRIMARY KEY,
    snapshot_id VARCHAR(100) NOT NULL,
    data_type VARCHAR(50) NOT NULL, -- 'user_data', 'user_settings', 'legal_compliance', 'activities', 'goals'
    data_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (snapshot_id) REFERENCES migration_snapshots(snapshot_id) ON DELETE CASCADE
);

-- Migration notifications table
CREATE TABLE IF NOT EXISTS migration_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL, -- 'migration_status', 'rollback_available', 'migration_complete'
    status VARCHAR(50) NOT NULL, -- 'sent', 'delivered', 'failed'
    message TEXT NOT NULL,
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMP NULL,
    read_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add migration-related columns to user_settings table
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_status VARCHAR(50) DEFAULT 'not_started';
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_completed_at TIMESTAMP NULL;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS oauth_type VARCHAR(50) DEFAULT 'individual'; -- 'individual', 'centralized'
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_priority INTEGER DEFAULT 0;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS last_migration_attempt TIMESTAMP NULL;
ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS migration_attempts INTEGER DEFAULT 0;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_migration_status_user_id ON migration_status(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_status_status ON migration_status(status);
CREATE INDEX IF NOT EXISTS idx_migration_status_started_at ON migration_status(started_at);

CREATE INDEX IF NOT EXISTS idx_migration_snapshots_user_id ON migration_snapshots(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_snapshots_created_at ON migration_snapshots(created_at);

CREATE INDEX IF NOT EXISTS idx_migration_snapshot_data_snapshot_id ON migration_snapshot_data(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_migration_snapshot_data_type ON migration_snapshot_data(data_type);

CREATE INDEX IF NOT EXISTS idx_migration_notifications_user_id ON migration_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_notifications_sent_at ON migration_notifications(sent_at);

CREATE INDEX IF NOT EXISTS idx_user_settings_migration_status ON user_settings(migration_status);
CREATE INDEX IF NOT EXISTS idx_user_settings_oauth_type ON user_settings(oauth_type);
CREATE INDEX IF NOT EXISTS idx_user_settings_migration_priority ON user_settings(migration_priority);

-- Create views for easier querying
CREATE OR REPLACE VIEW migration_summary AS
SELECT 
    ms.status,
    COUNT(*) as count,
    AVG(EXTRACT(EPOCH FROM (ms.completed_at - ms.started_at))) as avg_duration_seconds,
    MIN(ms.started_at) as earliest_start,
    MAX(ms.completed_at) as latest_completion
FROM migration_status ms
GROUP BY ms.status;

CREATE OR REPLACE VIEW migration_candidates AS
SELECT 
    u.id as user_id,
    u.email,
    us.strava_access_token,
    us.strava_refresh_token,
    us.onboarding_completed,
    us.account_status,
    us.migration_status,
    us.oauth_type,
    us.migration_priority,
    u.created_at as user_created_at
FROM users u
JOIN user_settings us ON u.id = us.user_id
WHERE us.strava_access_token IS NOT NULL 
AND us.strava_access_token != ''
AND us.account_status = 'active'
AND (us.oauth_type = 'individual' OR us.oauth_type IS NULL)
ORDER BY us.migration_priority DESC, u.created_at ASC;

-- Create functions for migration operations
CREATE OR REPLACE FUNCTION update_migration_status(
    p_migration_id VARCHAR(100),
    p_status VARCHAR(50),
    p_error_message TEXT DEFAULT NULL
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE migration_status 
    SET status = p_status,
        completed_at = CASE WHEN p_status IN ('completed', 'failed', 'rolled_back') THEN NOW() ELSE completed_at END,
        error_message = p_error_message,
        updated_at = NOW()
    WHERE migration_id = p_migration_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_migration_statistics() RETURNS TABLE(
    total_users BIGINT,
    migration_candidates BIGINT,
    migrations_completed BIGINT,
    migrations_failed BIGINT,
    migrations_in_progress BIGINT,
    migrations_rolled_back BIGINT,
    success_rate NUMERIC(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM users WHERE account_status = 'active') as total_users,
        (SELECT COUNT(*) FROM migration_candidates) as migration_candidates,
        (SELECT COUNT(*) FROM migration_status WHERE status = 'completed') as migrations_completed,
        (SELECT COUNT(*) FROM migration_status WHERE status = 'failed') as migrations_failed,
        (SELECT COUNT(*) FROM migration_status WHERE status = 'in_progress') as migrations_in_progress,
        (SELECT COUNT(*) FROM migration_status WHERE status = 'rolled_back') as migrations_rolled_back,
        CASE 
            WHEN (SELECT COUNT(*) FROM migration_status WHERE status IN ('completed', 'failed')) = 0 THEN 0.0
            ELSE ROUND(
                (SELECT COUNT(*)::NUMERIC FROM migration_status WHERE status = 'completed') / 
                (SELECT COUNT(*)::NUMERIC FROM migration_status WHERE status IN ('completed', 'failed')) * 100, 2
            )
        END as success_rate;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_migration_status_updated_at
    BEFORE UPDATE ON migration_status
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional)
-- INSERT INTO migration_status (migration_id, user_id, status, started_at) 
-- VALUES ('test_migration_001', 1, 'completed', NOW() - INTERVAL '1 hour');

-- Grant permissions (adjust as needed for your database setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

