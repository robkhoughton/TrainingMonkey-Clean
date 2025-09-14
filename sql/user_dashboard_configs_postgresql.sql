-- User Dashboard Configuration Table (PostgreSQL)
-- Stores per-user ACWR configuration settings for the dashboard
-- Last Updated: 2025-01-27

CREATE TABLE IF NOT EXISTS user_dashboard_configs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    chronic_period_days INTEGER NOT NULL CHECK (chronic_period_days >= 28 AND chronic_period_days <= 90),
    decay_rate DECIMAL(5,4) NOT NULL CHECK (decay_rate >= 0.01 AND decay_rate <= 0.20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key constraint
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- Unique constraint to ensure only one active config per user
    UNIQUE(user_id, is_active) DEFERRABLE INITIALLY DEFERRED
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_dashboard_configs_user_id ON user_dashboard_configs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_dashboard_configs_active ON user_dashboard_configs(user_id, is_active);

-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_user_dashboard_configs_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update updated_at timestamp
DROP TRIGGER IF EXISTS update_user_dashboard_configs_timestamp ON user_dashboard_configs;
CREATE TRIGGER update_user_dashboard_configs_timestamp 
    BEFORE UPDATE ON user_dashboard_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_user_dashboard_configs_timestamp();

-- Verify table creation
SELECT 'user_dashboard_configs table created successfully' as status;
