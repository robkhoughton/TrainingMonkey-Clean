-- ACWR Migration Integrity and Rollback System Database Schema (Fixed)
-- Creates tables for data integrity validation and rollback operations
-- Note: Foreign key constraints to 'users' table removed to avoid dependency issues

-- Integrity checkpoints table
CREATE TABLE IF NOT EXISTS acwr_integrity_checkpoints (
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
CREATE TABLE IF NOT EXISTS acwr_rollback_history (
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
CREATE TABLE IF NOT EXISTS acwr_data_validation_results (
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

-- Rollback impact analysis table
CREATE TABLE IF NOT EXISTS acwr_rollback_impact_analysis (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,
    affected_tables JSONB NOT NULL,
    estimated_records INTEGER NOT NULL,
    estimated_duration DECIMAL(10,3), -- seconds
    risk_level VARCHAR(20) NOT NULL,
    recommendations JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_impact_analysis_type CHECK (analysis_type IN ('data_loss', 'performance', 'referential_integrity', 'business_rules')),
    CONSTRAINT chk_impact_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
);

-- Rollback execution plans table
CREATE TABLE IF NOT EXISTS acwr_rollback_execution_plans (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(100) NOT NULL UNIQUE,
    rollback_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    plan_name VARCHAR(200) NOT NULL,
    plan_description TEXT,
    execution_steps JSONB NOT NULL,
    estimated_duration DECIMAL(10,3), -- seconds
    risk_assessment JSONB,
    created_by INTEGER NOT NULL,
    approved_by INTEGER,
    approved_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_plan_status CHECK (status IN ('draft', 'pending_approval', 'approved', 'rejected', 'executed', 'cancelled'))
);

-- Rollback monitoring table
CREATE TABLE IF NOT EXISTS acwr_rollback_monitoring (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    monitoring_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(20),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Check constraints
    CONSTRAINT chk_monitoring_type CHECK (monitoring_type IN ('performance', 'data_integrity', 'resource_usage', 'error_rate', 'throughput'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_checkpoint_migration ON acwr_integrity_checkpoints(migration_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_user ON acwr_integrity_checkpoints(user_id);
CREATE INDEX IF NOT EXISTS idx_checkpoint_timestamp ON acwr_integrity_checkpoints(timestamp);

CREATE INDEX IF NOT EXISTS idx_rollback_history_migration ON acwr_rollback_history(migration_id);
CREATE INDEX IF NOT EXISTS idx_rollback_history_user ON acwr_rollback_history(user_id);
CREATE INDEX IF NOT EXISTS idx_rollback_history_scope ON acwr_rollback_history(scope);
CREATE INDEX IF NOT EXISTS idx_rollback_history_status ON acwr_rollback_history(status);
CREATE INDEX IF NOT EXISTS idx_rollback_history_timestamp ON acwr_rollback_history(timestamp);

CREATE INDEX IF NOT EXISTS idx_validation_migration ON acwr_data_validation_results(migration_id);
CREATE INDEX IF NOT EXISTS idx_validation_user ON acwr_data_validation_results(user_id);
CREATE INDEX IF NOT EXISTS idx_validation_type ON acwr_data_validation_results(validation_type);
CREATE INDEX IF NOT EXISTS idx_validation_level ON acwr_data_validation_results(validation_level);
CREATE INDEX IF NOT EXISTS idx_validation_passed ON acwr_data_validation_results(passed);
CREATE INDEX IF NOT EXISTS idx_validation_timestamp ON acwr_data_validation_results(timestamp);

CREATE INDEX IF NOT EXISTS idx_impact_rollback ON acwr_rollback_impact_analysis(rollback_id);
CREATE INDEX IF NOT EXISTS idx_impact_user ON acwr_rollback_impact_analysis(user_id);
CREATE INDEX IF NOT EXISTS idx_impact_type ON acwr_rollback_impact_analysis(analysis_type);
CREATE INDEX IF NOT EXISTS idx_impact_risk ON acwr_rollback_impact_analysis(risk_level);

CREATE INDEX IF NOT EXISTS idx_plan_rollback ON acwr_rollback_execution_plans(rollback_id);
CREATE INDEX IF NOT EXISTS idx_plan_user ON acwr_rollback_execution_plans(user_id);
CREATE INDEX IF NOT EXISTS idx_plan_status ON acwr_rollback_execution_plans(status);
CREATE INDEX IF NOT EXISTS idx_plan_created_by ON acwr_rollback_execution_plans(created_by);

CREATE INDEX IF NOT EXISTS idx_monitoring_rollback ON acwr_rollback_monitoring(rollback_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_user ON acwr_rollback_monitoring(user_id);
CREATE INDEX IF NOT EXISTS idx_monitoring_type ON acwr_rollback_monitoring(monitoring_type);
CREATE INDEX IF NOT EXISTS idx_monitoring_metric ON acwr_rollback_monitoring(metric_name);
CREATE INDEX IF NOT EXISTS idx_monitoring_timestamp ON acwr_rollback_monitoring(timestamp);

-- Views for easy querying (without user table joins)
CREATE OR REPLACE VIEW acwr_integrity_checkpoint_summary AS
SELECT 
    ic.checkpoint_id,
    ic.migration_id,
    ic.user_id,
    ic.batch_id,
    ic.timestamp,
    ic.validation_result,
    ic.checksum,
    ic.created_at,
    CASE 
        WHEN ic.validation_result->>'passed' = 'true' THEN 'PASSED'
        WHEN ic.validation_result->>'passed' = 'false' THEN 'FAILED'
        ELSE 'UNKNOWN'
    END as validation_status
FROM acwr_integrity_checkpoints ic
ORDER BY ic.timestamp DESC;

CREATE OR REPLACE VIEW acwr_rollback_history_summary AS
SELECT 
    rh.rollback_id,
    rh.migration_id,
    rh.user_id,
    rh.scope,
    rh.reason,
    rh.initiated_by,
    rh.timestamp,
    rh.status,
    rh.affected_records,
    rh.created_at,
    CASE 
        WHEN rh.status = 'completed' THEN 'SUCCESS'
        WHEN rh.status = 'failed' THEN 'FAILED'
        WHEN rh.status = 'in_progress' THEN 'RUNNING'
        ELSE 'PENDING'
    END as execution_status
FROM acwr_rollback_history rh
ORDER BY rh.timestamp DESC;

CREATE OR REPLACE VIEW acwr_validation_summary AS
SELECT 
    dvr.validation_id,
    dvr.migration_id,
    dvr.user_id,
    dvr.validation_type,
    dvr.validation_level,
    dvr.timestamp,
    dvr.passed,
    dvr.error_count,
    dvr.warning_count,
    dvr.created_at,
    CASE 
        WHEN dvr.passed = TRUE AND dvr.error_count = 0 AND dvr.warning_count = 0 THEN 'PERFECT'
        WHEN dvr.passed = TRUE AND dvr.warning_count > 0 THEN 'PASSED_WITH_WARNINGS'
        WHEN dvr.passed = TRUE AND dvr.error_count > 0 THEN 'PASSED_WITH_ERRORS'
        ELSE 'FAILED'
    END as validation_status
FROM acwr_data_validation_results dvr
ORDER BY dvr.timestamp DESC;

-- Functions for integrity and rollback management
CREATE OR REPLACE FUNCTION create_integrity_checkpoint(
    p_checkpoint_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_batch_id INTEGER,
    p_validation_result JSONB,
    p_data_snapshot JSONB,
    p_checksum VARCHAR(64),
    p_rollback_data JSONB
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_integrity_checkpoints (
        checkpoint_id, migration_id, user_id, batch_id, timestamp,
        validation_result, data_snapshot, checksum, rollback_data
    ) VALUES (
        p_checkpoint_id, p_migration_id, p_user_id, p_batch_id, CURRENT_TIMESTAMP,
        p_validation_result, p_data_snapshot, p_checksum, p_rollback_data
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_rollback_record(
    p_rollback_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_scope VARCHAR(50),
    p_reason TEXT,
    p_initiated_by INTEGER
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_rollback_history (
        rollback_id, migration_id, user_id, scope, reason, initiated_by, timestamp
    ) VALUES (
        p_rollback_id, p_migration_id, p_user_id, p_scope, p_reason, p_initiated_by, CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_rollback_status(
    p_rollback_id VARCHAR(100),
    p_status VARCHAR(20),
    p_affected_records INTEGER DEFAULT NULL,
    p_error_log JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    UPDATE acwr_rollback_history 
    SET 
        status = p_status,
        affected_records = COALESCE(p_affected_records, affected_records),
        error_log = COALESCE(p_error_log, error_log)
    WHERE rollback_id = p_rollback_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_validation_result(
    p_validation_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_validation_type VARCHAR(50),
    p_validation_level VARCHAR(20),
    p_passed BOOLEAN,
    p_error_count INTEGER DEFAULT 0,
    p_warning_count INTEGER DEFAULT 0,
    p_details JSONB DEFAULT NULL,
    p_error_messages JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_data_validation_results (
        validation_id, migration_id, user_id, validation_type, validation_level,
        timestamp, passed, error_count, warning_count, details, error_messages
    ) VALUES (
        p_validation_id, p_migration_id, p_user_id, p_validation_type, p_validation_level,
        CURRENT_TIMESTAMP, p_passed, p_error_count, p_warning_count, p_details, p_error_messages
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_integrity_data(
    p_checkpoint_retention_days INTEGER DEFAULT 30,
    p_rollback_retention_days INTEGER DEFAULT 90,
    p_validation_retention_days INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old checkpoints
    DELETE FROM acwr_integrity_checkpoints 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_checkpoint_retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old rollback history (only completed/failed ones)
    DELETE FROM acwr_rollback_history 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_rollback_retention_days
    AND status IN ('completed', 'failed');
    
    -- Clean up old validation results
    DELETE FROM acwr_data_validation_results 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_validation_retention_days;
    
    -- Clean up old impact analysis
    DELETE FROM acwr_rollback_impact_analysis 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_rollback_retention_days;
    
    -- Clean up old execution plans (only executed/cancelled ones)
    DELETE FROM acwr_rollback_execution_plans 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_rollback_retention_days
    AND status IN ('executed', 'cancelled');
    
    -- Clean up old monitoring data
    DELETE FROM acwr_rollback_monitoring 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * 7; -- Keep 7 days of monitoring data
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_integrity_checkpoints TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_history TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_data_validation_results TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_impact_analysis TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_execution_plans TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_monitoring TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_integrity_checkpoints_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_history_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_data_validation_results_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_impact_analysis_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_execution_plans_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_monitoring_id_seq TO your_app_user;

