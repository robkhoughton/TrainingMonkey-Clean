-- ACWR Migration System Complete Database Schema (Safe Version)
-- Consolidated schema for all migration-related tables with safe DROP/CREATE
-- Note: Foreign key constraints to 'users' table removed to avoid dependency issues

-- ============================================================================
-- 1. DROP EXISTING OBJECTS (SAFE)
-- ============================================================================

-- Drop triggers first
DROP TRIGGER IF EXISTS update_enhanced_calculations_updated_at ON acwr_enhanced_calculations;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS update_migration_progress(VARCHAR, INTEGER, INTEGER, INTEGER, INTEGER, VARCHAR);
DROP FUNCTION IF EXISTS cleanup_old_migration_data(INTEGER);

-- Drop views
DROP VIEW IF EXISTS acwr_migration_summary;
DROP VIEW IF EXISTS acwr_migration_current_progress;

-- Drop indexes (they will be recreated)
DROP INDEX IF EXISTS idx_enhanced_calc_user_date;
DROP INDEX IF EXISTS idx_enhanced_calc_config;
DROP INDEX IF EXISTS idx_enhanced_calc_activity;
DROP INDEX IF EXISTS idx_migration_history_user;
DROP INDEX IF EXISTS idx_migration_history_date;
DROP INDEX IF EXISTS idx_migration_history_status;
DROP INDEX IF EXISTS idx_migration_progress_user;
DROP INDEX IF EXISTS idx_migration_progress_status;
DROP INDEX IF EXISTS idx_migration_progress_update;
DROP INDEX IF EXISTS idx_migration_batches_migration;
DROP INDEX IF EXISTS idx_migration_batches_user;
DROP INDEX IF EXISTS idx_migration_log_migration;
DROP INDEX IF EXISTS idx_migration_log_user;
DROP INDEX IF EXISTS idx_migration_log_timestamp;
DROP INDEX IF EXISTS idx_migration_log_level;
DROP INDEX IF EXISTS idx_migration_log_source;
DROP INDEX IF EXISTS idx_migration_alert_migration;
DROP INDEX IF EXISTS idx_migration_alert_user;
DROP INDEX IF EXISTS idx_migration_alert_timestamp;
DROP INDEX IF EXISTS idx_migration_alert_severity;
DROP INDEX IF EXISTS idx_migration_alert_type;
DROP INDEX IF EXISTS idx_migration_alert_acknowledged;
DROP INDEX IF EXISTS idx_migration_alert_resolved;
DROP INDEX IF EXISTS idx_migration_event_migration;
DROP INDEX IF EXISTS idx_migration_event_user;
DROP INDEX IF EXISTS idx_migration_event_timestamp;
DROP INDEX IF EXISTS idx_migration_event_type;
DROP INDEX IF EXISTS idx_migration_event_source;
DROP INDEX IF EXISTS idx_migration_health_migration;
DROP INDEX IF EXISTS idx_migration_health_timestamp;
DROP INDEX IF EXISTS idx_migration_health_status;
DROP INDEX IF EXISTS idx_migration_health_performance;
DROP INDEX IF EXISTS idx_migration_monitoring_config_name;
DROP INDEX IF EXISTS idx_migration_monitoring_config_active;
DROP INDEX IF EXISTS idx_migration_notification_user;
DROP INDEX IF EXISTS idx_migration_notification_type;
DROP INDEX IF EXISTS idx_migration_notification_enabled;
DROP INDEX IF EXISTS idx_checkpoint_migration;
DROP INDEX IF EXISTS idx_checkpoint_user;
DROP INDEX IF EXISTS idx_checkpoint_timestamp;
DROP INDEX IF EXISTS idx_rollback_history_migration;
DROP INDEX IF EXISTS idx_rollback_history_user;
DROP INDEX IF EXISTS idx_rollback_history_scope;
DROP INDEX IF EXISTS idx_rollback_history_status;
DROP INDEX IF EXISTS idx_rollback_history_timestamp;
DROP INDEX IF EXISTS idx_validation_migration;
DROP INDEX IF EXISTS idx_validation_user;
DROP INDEX IF EXISTS idx_validation_type;
DROP INDEX IF EXISTS idx_validation_level;
DROP INDEX IF EXISTS idx_validation_passed;
DROP INDEX IF EXISTS idx_validation_timestamp;
DROP INDEX IF EXISTS idx_rollback_exec_migration;
DROP INDEX IF EXISTS idx_rollback_exec_user;
DROP INDEX IF EXISTS idx_rollback_exec_status;
DROP INDEX IF EXISTS idx_rollback_exec_scope;
DROP INDEX IF EXISTS idx_rollback_exec_start_time;

-- Drop tables (in reverse dependency order)
DROP TABLE IF EXISTS acwr_rollback_executions CASCADE;
DROP TABLE IF EXISTS acwr_data_validation_results CASCADE;
DROP TABLE IF EXISTS acwr_rollback_history CASCADE;
DROP TABLE IF EXISTS acwr_integrity_checkpoints CASCADE;
DROP TABLE IF EXISTS acwr_migration_notification_preferences CASCADE;
DROP TABLE IF EXISTS acwr_migration_monitoring_config CASCADE;
DROP TABLE IF EXISTS acwr_migration_health_metrics CASCADE;
DROP TABLE IF EXISTS acwr_migration_events CASCADE;
DROP TABLE IF EXISTS acwr_migration_alerts CASCADE;
DROP TABLE IF EXISTS acwr_migration_logs CASCADE;
DROP TABLE IF EXISTS acwr_migration_batches CASCADE;
DROP TABLE IF EXISTS acwr_migration_progress CASCADE;
DROP TABLE IF EXISTS acwr_migration_history CASCADE;
DROP TABLE IF EXISTS acwr_enhanced_calculations CASCADE;

-- ============================================================================
-- 2. CORE MIGRATION TABLES
-- ============================================================================

-- Enhanced ACWR calculations table
CREATE TABLE acwr_enhanced_calculations (
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
CREATE TABLE acwr_migration_history (
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
CREATE TABLE acwr_migration_progress (
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
CREATE TABLE acwr_migration_batches (
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

-- ============================================================================
-- 3. MONITORING AND LOGGING TABLES
-- ============================================================================

-- Migration logs table
CREATE TABLE acwr_migration_logs (
    id SERIAL PRIMARY KEY,
    log_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    level VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    source VARCHAR(100) NOT NULL,
    thread_id VARCHAR(100),
    execution_time DECIMAL(10,3), -- seconds
    error_traceback TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_migration_log_level CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

-- Migration alerts table
CREATE TABLE acwr_migration_alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    severity VARCHAR(20) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_migration_alert_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

-- Migration events table
CREATE TABLE acwr_migration_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    data JSONB,
    source VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_migration_event_type CHECK (event_type IN (
        'migration_started', 'migration_completed', 'migration_failed', 'migration_paused',
        'migration_resumed', 'migration_cancelled', 'batch_started', 'batch_completed',
        'batch_failed', 'error_occurred', 'warning_issued', 'performance_degraded',
        'resource_threshold_exceeded', 'alert_triggered', 'status_changed'
    ))
);

-- Migration health metrics table
CREATE TABLE acwr_migration_health_metrics (
    id SERIAL PRIMARY KEY,
    migration_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL,
    progress_percentage DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    estimated_completion_time TIMESTAMP WITH TIME ZONE,
    error_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    performance_score DECIMAL(5,2) NOT NULL DEFAULT 0.0,
    resource_usage JSONB,
    throughput_activities_per_second DECIMAL(10,2) NOT NULL DEFAULT 0.0,
    average_batch_time DECIMAL(10,3) NOT NULL DEFAULT 0.0,
    success_rate DECIMAL(5,4) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_migration_health_status CHECK (status IN (
        'pending', 'running', 'paused', 'completed', 'failed', 'cancelled', 'rolled_back'
    )),
    CONSTRAINT chk_migration_health_progress CHECK (progress_percentage >= 0.0 AND progress_percentage <= 100.0),
    CONSTRAINT chk_migration_health_performance CHECK (performance_score >= 0.0 AND performance_score <= 100.0),
    CONSTRAINT chk_migration_health_success_rate CHECK (success_rate >= 0.0 AND success_rate <= 1.0)
);

-- Migration monitoring configuration table
CREATE TABLE acwr_migration_monitoring_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Migration notification preferences table
CREATE TABLE acwr_migration_notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    severity_threshold VARCHAR(20) NOT NULL DEFAULT 'medium',
    notification_method VARCHAR(50) NOT NULL DEFAULT 'email',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_migration_notification_type CHECK (notification_type IN (
        'migration_started', 'migration_completed', 'migration_failed', 'high_error_rate',
        'performance_degraded', 'resource_threshold_exceeded', 'alert_triggered'
    )),
    CONSTRAINT chk_migration_notification_severity CHECK (severity_threshold IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_migration_notification_method CHECK (notification_method IN ('email', 'sms', 'webhook', 'dashboard')),
    
    -- Unique constraint
    CONSTRAINT uk_migration_notification_user_type UNIQUE (user_id, notification_type)
);

-- ============================================================================
-- 4. INTEGRITY AND ROLLBACK TABLES
-- ============================================================================

-- Integrity checkpoints table
CREATE TABLE acwr_integrity_checkpoints (
    id SERIAL PRIMARY KEY,
    checkpoint_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    batch_id INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    validation_result JSONB NOT NULL,
    data_snapshot JSONB NOT NULL,
    checksum VARCHAR(64) NOT NULL,
    rollback_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rollback history table
CREATE TABLE acwr_rollback_history (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    scope VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    initiated_by INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    affected_records INTEGER NOT NULL DEFAULT 0,
    rollback_data JSONB,
    error_log JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_rollback_scope CHECK (scope IN ('single_batch', 'user_migration', 'configuration', 'full_system')),
    CONSTRAINT chk_rollback_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
);

-- Data validation results table
CREATE TABLE acwr_data_validation_results (
    id SERIAL PRIMARY KEY,
    validation_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    validation_type VARCHAR(50) NOT NULL,
    validation_level VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    passed BOOLEAN NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 0,
    warning_count INTEGER NOT NULL DEFAULT 0,
    details JSONB,
    error_messages JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_validation_type CHECK (validation_type IN ('basic', 'standard', 'strict', 'paranoid')),
    CONSTRAINT chk_validation_level CHECK (validation_level IN ('pre_migration', 'post_migration', 'rollback', 'integrity_check'))
);

-- Rollback execution results table
CREATE TABLE acwr_rollback_executions (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    scope VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    total_duration DECIMAL(10,3), -- seconds
    total_affected_records INTEGER NOT NULL DEFAULT 0,
    backup_location VARCHAR(200),
    verification_passed BOOLEAN NOT NULL DEFAULT FALSE,
    error_log JSONB,
    execution_steps JSONB,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_rollback_exec_scope CHECK (scope IN ('single_batch', 'user_migration', 'configuration', 'full_system')),
    CONSTRAINT chk_rollback_exec_status CHECK (status IN ('pending', 'preparing', 'backing_up', 'validating', 'executing', 'verifying', 'completed', 'failed', 'cancelled'))
);

-- ============================================================================
-- 5. INDEXES FOR PERFORMANCE
-- ============================================================================

-- Core migration indexes
CREATE INDEX idx_enhanced_calc_user_date ON acwr_enhanced_calculations(user_id, calculation_date);
CREATE INDEX idx_enhanced_calc_config ON acwr_enhanced_calculations(configuration_id);
CREATE INDEX idx_enhanced_calc_activity ON acwr_enhanced_calculations(activity_id);

CREATE INDEX idx_migration_history_user ON acwr_migration_history(user_id);
CREATE INDEX idx_migration_history_date ON acwr_migration_history(start_time);
CREATE INDEX idx_migration_history_status ON acwr_migration_history(status);

CREATE INDEX idx_migration_progress_user ON acwr_migration_progress(user_id);
CREATE INDEX idx_migration_progress_status ON acwr_migration_progress(status);
CREATE INDEX idx_migration_progress_update ON acwr_migration_progress(last_update);

CREATE INDEX idx_migration_batches_migration ON acwr_migration_batches(migration_id);
CREATE INDEX idx_migration_batches_user ON acwr_migration_batches(user_id);

-- Monitoring indexes
CREATE INDEX idx_migration_log_migration ON acwr_migration_logs(migration_id);
CREATE INDEX idx_migration_log_user ON acwr_migration_logs(user_id);
CREATE INDEX idx_migration_log_timestamp ON acwr_migration_logs(timestamp);
CREATE INDEX idx_migration_log_level ON acwr_migration_logs(level);
CREATE INDEX idx_migration_log_source ON acwr_migration_logs(source);

CREATE INDEX idx_migration_alert_migration ON acwr_migration_alerts(migration_id);
CREATE INDEX idx_migration_alert_user ON acwr_migration_alerts(user_id);
CREATE INDEX idx_migration_alert_timestamp ON acwr_migration_alerts(timestamp);
CREATE INDEX idx_migration_alert_severity ON acwr_migration_alerts(severity);
CREATE INDEX idx_migration_alert_type ON acwr_migration_alerts(alert_type);
CREATE INDEX idx_migration_alert_acknowledged ON acwr_migration_alerts(acknowledged);
CREATE INDEX idx_migration_alert_resolved ON acwr_migration_alerts(resolved);

CREATE INDEX idx_migration_event_migration ON acwr_migration_events(migration_id);
CREATE INDEX idx_migration_event_user ON acwr_migration_events(user_id);
CREATE INDEX idx_migration_event_timestamp ON acwr_migration_events(timestamp);
CREATE INDEX idx_migration_event_type ON acwr_migration_events(event_type);
CREATE INDEX idx_migration_event_source ON acwr_migration_events(source);

CREATE INDEX idx_migration_health_migration ON acwr_migration_health_metrics(migration_id);
CREATE INDEX idx_migration_health_timestamp ON acwr_migration_health_metrics(timestamp);
CREATE INDEX idx_migration_health_status ON acwr_migration_health_metrics(status);
CREATE INDEX idx_migration_health_performance ON acwr_migration_health_metrics(performance_score);

CREATE INDEX idx_migration_monitoring_config_name ON acwr_migration_monitoring_config(config_name);
CREATE INDEX idx_migration_monitoring_config_active ON acwr_migration_monitoring_config(is_active);

CREATE INDEX idx_migration_notification_user ON acwr_migration_notification_preferences(user_id);
CREATE INDEX idx_migration_notification_type ON acwr_migration_notification_preferences(notification_type);
CREATE INDEX idx_migration_notification_enabled ON acwr_migration_notification_preferences(enabled);

-- Integrity and rollback indexes
CREATE INDEX idx_checkpoint_migration ON acwr_integrity_checkpoints(migration_id);
CREATE INDEX idx_checkpoint_user ON acwr_integrity_checkpoints(user_id);
CREATE INDEX idx_checkpoint_timestamp ON acwr_integrity_checkpoints(timestamp);

CREATE INDEX idx_rollback_history_migration ON acwr_rollback_history(migration_id);
CREATE INDEX idx_rollback_history_user ON acwr_rollback_history(user_id);
CREATE INDEX idx_rollback_history_scope ON acwr_rollback_history(scope);
CREATE INDEX idx_rollback_history_status ON acwr_rollback_history(status);
CREATE INDEX idx_rollback_history_timestamp ON acwr_rollback_history(timestamp);

CREATE INDEX idx_validation_migration ON acwr_data_validation_results(migration_id);
CREATE INDEX idx_validation_user ON acwr_data_validation_results(user_id);
CREATE INDEX idx_validation_type ON acwr_data_validation_results(validation_type);
CREATE INDEX idx_validation_level ON acwr_data_validation_results(validation_level);
CREATE INDEX idx_validation_passed ON acwr_data_validation_results(passed);
CREATE INDEX idx_validation_timestamp ON acwr_data_validation_results(timestamp);

CREATE INDEX idx_rollback_exec_migration ON acwr_rollback_executions(migration_id);
CREATE INDEX idx_rollback_exec_user ON acwr_rollback_executions(user_id);
CREATE INDEX idx_rollback_exec_status ON acwr_rollback_executions(status);
CREATE INDEX idx_rollback_exec_scope ON acwr_rollback_executions(scope);
CREATE INDEX idx_rollback_exec_start_time ON acwr_rollback_executions(start_time);

-- ============================================================================
-- 6. VIEWS FOR EASY QUERYING
-- ============================================================================

-- Migration summary view
CREATE VIEW acwr_migration_summary AS
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

-- Current migration progress view
CREATE VIEW acwr_migration_current_progress AS
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

-- ============================================================================
-- 7. FUNCTIONS FOR MIGRATION MANAGEMENT
-- ============================================================================

-- Function to update migration progress
CREATE FUNCTION update_migration_progress(
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
CREATE FUNCTION cleanup_old_migration_data(
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

-- ============================================================================
-- 8. TRIGGERS
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE FUNCTION update_updated_at_column()
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

-- ============================================================================
-- 9. DEFAULT DATA
-- ============================================================================

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

-- ============================================================================
-- 10. VERIFICATION QUERIES
-- ============================================================================

-- Verify tables were created
SELECT 
    'Tables Created' as verification_type,
    COUNT(*) as count
FROM information_schema.tables 
WHERE table_name LIKE 'acwr_%'
AND table_schema = 'public'

UNION ALL

-- Verify indexes were created
SELECT 
    'Indexes Created' as verification_type,
    COUNT(*) as count
FROM pg_indexes 
WHERE tablename LIKE 'acwr_%'
AND schemaname = 'public'

UNION ALL

-- Verify views were created
SELECT 
    'Views Created' as verification_type,
    COUNT(*) as count
FROM information_schema.views 
WHERE table_name LIKE 'acwr_%'
AND table_schema = 'public'

UNION ALL

-- Verify functions were created
SELECT 
    'Functions Created' as verification_type,
    COUNT(*) as count
FROM information_schema.routines 
WHERE routine_name LIKE '%migration%'
AND routine_schema = 'public'

UNION ALL

-- Verify default configuration
SELECT 
    'Default Configuration' as verification_type,
    COUNT(*) as count
FROM acwr_configurations 
WHERE name = 'Migration Default';
