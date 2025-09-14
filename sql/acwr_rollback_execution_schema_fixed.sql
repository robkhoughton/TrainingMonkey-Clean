-- ACWR Migration Rollback Execution System Database Schema (Fixed)
-- Creates tables for rollback execution tracking and backup management
-- Note: Foreign key constraints to 'users' table removed to avoid dependency issues

-- Rollback execution results table
CREATE TABLE IF NOT EXISTS acwr_rollback_executions (
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

-- Rollback step execution details table
CREATE TABLE IF NOT EXISTS acwr_rollback_steps (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    step_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration DECIMAL(10,3), -- seconds
    records_affected INTEGER NOT NULL DEFAULT 0,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_rollback_step_type CHECK (step_type IN ('backup', 'validation', 'data_restoration', 'integrity_check', 'cleanup')),
    CONSTRAINT chk_rollback_step_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    
    -- Unique constraint
    CONSTRAINT uk_rollback_step_unique UNIQUE (rollback_id, step_number)
);

-- Rollback backup information table
CREATE TABLE IF NOT EXISTS acwr_rollback_backups (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    backup_type VARCHAR(50) NOT NULL,
    backup_location VARCHAR(200) NOT NULL,
    backup_size_bytes BIGINT,
    backup_checksum VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_compressed BOOLEAN NOT NULL DEFAULT FALSE,
    compression_ratio DECIMAL(5,2),
    metadata JSONB,
    
    -- Check constraints
    CONSTRAINT chk_rollback_backup_type CHECK (backup_type IN ('full', 'incremental', 'differential', 'selective'))
);

-- Rollback verification results table
CREATE TABLE IF NOT EXISTS acwr_rollback_verifications (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    verification_type VARCHAR(50) NOT NULL,
    verification_status VARCHAR(20) NOT NULL,
    verification_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    details JSONB,
    error_message TEXT,
    
    -- Check constraints
    CONSTRAINT chk_rollback_verification_type CHECK (verification_type IN ('data_integrity', 'referential_integrity', 'business_rules', 'performance', 'completeness')),
    CONSTRAINT chk_rollback_verification_status CHECK (verification_status IN ('passed', 'failed', 'warning', 'skipped'))
);

-- Rollback alerts table
CREATE TABLE IF NOT EXISTS acwr_rollback_alerts (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_rollback_alert_type CHECK (alert_type IN ('rollback_started', 'rollback_completed', 'rollback_failed', 'verification_failed', 'backup_failed', 'data_corruption_detected')),
    CONSTRAINT chk_rollback_alert_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_rollback_exec_migration ON acwr_rollback_executions(migration_id);
CREATE INDEX IF NOT EXISTS idx_rollback_exec_user ON acwr_rollback_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_rollback_exec_status ON acwr_rollback_executions(status);
CREATE INDEX IF NOT EXISTS idx_rollback_exec_scope ON acwr_rollback_executions(scope);
CREATE INDEX IF NOT EXISTS idx_rollback_exec_start_time ON acwr_rollback_executions(start_time);

CREATE INDEX IF NOT EXISTS idx_rollback_step_rollback ON acwr_rollback_steps(rollback_id);
CREATE INDEX IF NOT EXISTS idx_rollback_step_status ON acwr_rollback_steps(status);
CREATE INDEX IF NOT EXISTS idx_rollback_step_type ON acwr_rollback_steps(step_type);

CREATE INDEX IF NOT EXISTS idx_rollback_backup_rollback ON acwr_rollback_backups(rollback_id);
CREATE INDEX IF NOT EXISTS idx_rollback_backup_type ON acwr_rollback_backups(backup_type);
CREATE INDEX IF NOT EXISTS idx_rollback_backup_expires ON acwr_rollback_backups(expires_at);

CREATE INDEX IF NOT EXISTS idx_rollback_verification_rollback ON acwr_rollback_verifications(rollback_id);
CREATE INDEX IF NOT EXISTS idx_rollback_verification_type ON acwr_rollback_verifications(verification_type);
CREATE INDEX IF NOT EXISTS idx_rollback_verification_status ON acwr_rollback_verifications(verification_status);

CREATE INDEX IF NOT EXISTS idx_rollback_alert_rollback ON acwr_rollback_alerts(rollback_id);
CREATE INDEX IF NOT EXISTS idx_rollback_alert_type ON acwr_rollback_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_rollback_alert_severity ON acwr_rollback_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_rollback_alert_acknowledged ON acwr_rollback_alerts(acknowledged);

-- Views for easy querying (without user table joins)
CREATE OR REPLACE VIEW acwr_rollback_execution_summary AS
SELECT 
    re.rollback_id,
    re.migration_id,
    re.user_id,
    re.scope,
    re.status,
    re.start_time,
    re.end_time,
    re.total_duration,
    re.total_affected_records,
    re.verification_passed,
    re.success,
    CASE 
        WHEN re.end_time IS NOT NULL AND re.start_time IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (re.end_time - re.start_time))
        ELSE NULL 
    END as actual_duration_seconds,
    COUNT(rs.id) as total_steps,
    COUNT(CASE WHEN rs.success = TRUE THEN 1 END) as successful_steps,
    COUNT(CASE WHEN rs.success = FALSE THEN 1 END) as failed_steps
FROM acwr_rollback_executions re
LEFT JOIN acwr_rollback_steps rs ON re.rollback_id = rs.rollback_id
GROUP BY re.rollback_id, re.migration_id, re.user_id, re.scope, re.status, 
         re.start_time, re.end_time, re.total_duration, re.total_affected_records, 
         re.verification_passed, re.success
ORDER BY re.start_time DESC;

CREATE OR REPLACE VIEW acwr_rollback_step_summary AS
SELECT 
    rs.rollback_id,
    rs.step_number,
    rs.step_name,
    rs.step_type,
    rs.status,
    rs.start_time,
    rs.end_time,
    rs.duration,
    rs.records_affected,
    rs.success,
    rs.error_message,
    CASE 
        WHEN rs.end_time IS NOT NULL AND rs.start_time IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (rs.end_time - rs.start_time))
        ELSE NULL 
    END as actual_duration_seconds
FROM acwr_rollback_steps rs
ORDER BY rs.rollback_id, rs.step_number;

-- Functions for rollback execution management
CREATE OR REPLACE FUNCTION create_rollback_execution(
    p_rollback_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_scope VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_rollback_executions (
        rollback_id, migration_id, user_id, scope, start_time
    ) VALUES (
        p_rollback_id, p_migration_id, p_user_id, p_scope, CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_rollback_execution_status(
    p_rollback_id VARCHAR(100),
    p_status VARCHAR(20),
    p_success BOOLEAN DEFAULT NULL,
    p_error_log JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE acwr_rollback_executions 
    SET 
        status = p_status,
        success = COALESCE(p_success, success),
        error_log = COALESCE(p_error_log, error_log),
        end_time = CASE WHEN p_status IN ('completed', 'failed', 'cancelled') THEN CURRENT_TIMESTAMP ELSE end_time END
    WHERE rollback_id = p_rollback_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_rollback_step(
    p_rollback_id VARCHAR(100),
    p_step_number INTEGER,
    p_step_name VARCHAR(100),
    p_step_type VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_rollback_steps (
        rollback_id, step_number, step_name, step_type
    ) VALUES (
        p_rollback_id, p_step_number, p_step_name, p_step_type
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_rollback_step_status(
    p_rollback_id VARCHAR(100),
    p_step_number INTEGER,
    p_status VARCHAR(20),
    p_success BOOLEAN DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL,
    p_records_affected INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE acwr_rollback_steps 
    SET 
        status = p_status,
        success = COALESCE(p_success, success),
        error_message = COALESCE(p_error_message, error_message),
        records_affected = COALESCE(p_records_affected, records_affected),
        start_time = CASE WHEN p_status = 'running' AND start_time IS NULL THEN CURRENT_TIMESTAMP ELSE start_time END,
        end_time = CASE WHEN p_status IN ('completed', 'failed', 'skipped') AND end_time IS NULL THEN CURRENT_TIMESTAMP ELSE end_time END
    WHERE rollback_id = p_rollback_id AND step_number = p_step_number;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_rollback_data(
    p_retention_days INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old rollback executions
    DELETE FROM acwr_rollback_executions 
    WHERE start_time < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_retention_days
    AND status IN ('completed', 'failed', 'cancelled');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old rollback steps
    DELETE FROM acwr_rollback_steps 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_retention_days;
    
    -- Clean up old rollback backups
    DELETE FROM acwr_rollback_backups 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_retention_days;
    
    -- Clean up old rollback verifications
    DELETE FROM acwr_rollback_verifications 
    WHERE verification_time < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_retention_days;
    
    -- Clean up old rollback alerts
    DELETE FROM acwr_rollback_alerts 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_retention_days;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_executions TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_steps TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_backups TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_verifications TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_alerts TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_executions_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_steps_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_backups_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_verifications_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_alerts_id_seq TO your_app_user;

