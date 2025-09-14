-- ACWR Migration System Database Schema (Fixed)
-- Creates tables for tracking migration operations and storing enhanced calculations
-- Note: Foreign key constraints to 'users' table removed to avoid dependency issues

-- Enhanced ACWR calculations table
CREATE TABLE IF NOT EXISTS acwr_enhanced_calculations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    configuration_id INTEGER NOT NULL,
    acwr_ratio DECIMAL(10,4),
    acute_load DECIMAL(10,2),
    chronic_load DECIMAL(10,2),
    calculation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    calculation_method VARCHAR(50) DEFAULT 'enhanced',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints (only to acwr_configurations, not users)
    CONSTRAINT fk_enhanced_calc_config FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate calculations
    CONSTRAINT uk_enhanced_calc_unique UNIQUE (user_id, activity_id, configuration_id)
);

-- Migration history table
CREATE TABLE IF NOT EXISTS acwr_migration_history (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(100) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    total_activities INTEGER NOT NULL DEFAULT 0,
    successful_calculations INTEGER NOT NULL DEFAULT 0,
    failed_calculations INTEGER NOT NULL DEFAULT 0,
    configuration_id INTEGER NOT NULL,
    performance_metrics JSONB,
    error_log JSONB,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints (only to acwr_configurations, not users)
    CONSTRAINT fk_migration_config FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id) ON DELETE CASCADE
);

-- Migration progress tracking table (for real-time updates)
CREATE TABLE IF NOT EXISTS acwr_migration_progress (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    current_batch INTEGER NOT NULL DEFAULT 0,
    total_batches INTEGER NOT NULL DEFAULT 0,
    processed_activities INTEGER NOT NULL DEFAULT 0,
    total_activities INTEGER NOT NULL DEFAULT 0,
    successful_calculations INTEGER NOT NULL DEFAULT 0,
    failed_calculations INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint
    CONSTRAINT uk_progress_migration UNIQUE (migration_id)
);

-- Migration batch results table
CREATE TABLE IF NOT EXISTS acwr_migration_batches (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(100) NOT NULL,
    batch_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    activities_processed INTEGER NOT NULL DEFAULT 0,
    successful_calculations INTEGER NOT NULL DEFAULT 0,
    failed_calculations INTEGER NOT NULL DEFAULT 0,
    processing_time_seconds DECIMAL(10,3),
    errors JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Unique constraint
    CONSTRAINT uk_batch_unique UNIQUE (migration_id, batch_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_enhanced_calc_user_date ON acwr_enhanced_calculations(user_id, calculation_date);
CREATE INDEX IF NOT EXISTS idx_enhanced_calc_config ON acwr_enhanced_calculations(configuration_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_calc_activity ON acwr_enhanced_calculations(activity_id);

CREATE INDEX IF NOT EXISTS idx_migration_history_user ON acwr_migration_history(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_history_date ON acwr_migration_history(start_time);
CREATE INDEX IF NOT EXISTS idx_migration_history_status ON acwr_migration_history(status);

CREATE INDEX IF NOT EXISTS idx_migration_progress_user ON acwr_migration_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_progress_status ON acwr_migration_progress(status);
CREATE INDEX IF NOT EXISTS idx_migration_progress_update ON acwr_migration_progress(last_update);

CREATE INDEX IF NOT EXISTS idx_migration_batches_migration ON acwr_migration_batches(migration_id);
CREATE INDEX IF NOT EXISTS idx_migration_batches_user ON acwr_migration_batches(user_id);

-- Views for easy querying (without user table joins)
CREATE OR REPLACE VIEW acwr_migration_summary AS
SELECT 
    mh.migration_id,
    mh.user_id,
    mh.start_time,
    mh.end_time,
    mh.total_activities,
    mh.successful_calculations,
    mh.failed_calculations,
    mh.configuration_id,
    ac.name as configuration_name,
    mh.status,
    CASE 
        WHEN mh.end_time IS NOT NULL AND mh.start_time IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (mh.end_time - mh.start_time))
        ELSE NULL 
    END as processing_time_seconds,
    CASE 
        WHEN mh.total_activities > 0 
        THEN (mh.successful_calculations::DECIMAL / mh.total_activities) * 100
        ELSE 0 
    END as success_rate_percent
FROM acwr_migration_history mh
LEFT JOIN acwr_configurations ac ON mh.configuration_id = ac.id
ORDER BY mh.start_time DESC;

-- View for current migration progress (without user table joins)
CREATE OR REPLACE VIEW acwr_migration_current_progress AS
SELECT 
    mp.migration_id,
    mp.user_id,
    mp.current_batch,
    mp.total_batches,
    mp.processed_activities,
    mp.total_activities,
    mp.successful_calculations,
    mp.failed_calculations,
    mp.status,
    mp.error_message,
    mp.last_update,
    CASE 
        WHEN mp.total_batches > 0 
        THEN (mp.current_batch::DECIMAL / mp.total_batches) * 100
        ELSE 0 
    END as batch_progress_percent,
    CASE 
        WHEN mp.total_activities > 0 
        THEN (mp.processed_activities::DECIMAL / mp.total_activities) * 100
        ELSE 0 
    END as activity_progress_percent
FROM acwr_migration_progress mp
WHERE mp.status IN ('pending', 'running', 'paused')
ORDER BY mp.last_update DESC;

-- Function to update migration progress
CREATE OR REPLACE FUNCTION update_migration_progress(
    p_migration_id VARCHAR(100),
    p_current_batch INTEGER,
    p_processed_activities INTEGER,
    p_successful_calculations INTEGER,
    p_failed_calculations INTEGER,
    p_status VARCHAR(20)
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_migration_progress (
        migration_id, current_batch, processed_activities,
        successful_calculations, failed_calculations, status, last_update
    ) VALUES (
        p_migration_id, p_current_batch, p_processed_activities,
        p_successful_calculations, p_failed_calculations, p_status, CURRENT_TIMESTAMP
    )
    ON CONFLICT (migration_id) 
    DO UPDATE SET
        current_batch = EXCLUDED.current_batch,
        processed_activities = EXCLUDED.processed_activities,
        successful_calculations = EXCLUDED.successful_calculations,
        failed_calculations = EXCLUDED.failed_calculations,
        status = EXCLUDED.status,
        last_update = EXCLUDED.last_update;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old migration data
CREATE OR REPLACE FUNCTION cleanup_old_migration_data(
    p_days_to_keep INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete old migration progress records
    DELETE FROM acwr_migration_progress 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep
    AND status IN ('completed', 'failed', 'cancelled');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Delete old batch records
    DELETE FROM acwr_migration_batches 
    WHERE started_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_enhanced_calculations_updated_at
    BEFORE UPDATE ON acwr_enhanced_calculations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default migration configuration
INSERT INTO acwr_configurations (name, description, chronic_period_days, decay_rate, is_active, created_by)
VALUES (
    'Migration Default',
    'Default configuration for historical data migration',
    42,
    0.05,
    true,
    1
) ON CONFLICT (name) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_enhanced_calculations TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_history TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_progress TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_batches TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_enhanced_calculations_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_history_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_progress_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_batches_id_seq TO your_app_user;
