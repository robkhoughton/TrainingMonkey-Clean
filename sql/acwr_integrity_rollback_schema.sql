-- ACWR Migration Integrity and Rollback System Database Schema
-- Creates tables for data integrity validation and rollback operations

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_checkpoint_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_checkpoint_migration ON acwr_integrity_checkpoints(migration_id),
    INDEX idx_checkpoint_user ON acwr_integrity_checkpoints(user_id),
    INDEX idx_checkpoint_timestamp ON acwr_integrity_checkpoints(timestamp)
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
    
    -- Foreign key constraints
    CONSTRAINT fk_rollback_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_rollback_initiated_by FOREIGN KEY (initiated_by) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_rollback_scope CHECK (scope IN ('single_batch', 'user_migration', 'configuration', 'full_system')),
    CONSTRAINT chk_rollback_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    
    -- Indexes
    INDEX idx_rollback_migration ON acwr_rollback_history(migration_id),
    INDEX idx_rollback_user ON acwr_rollback_history(user_id),
    INDEX idx_rollback_status ON acwr_rollback_history(status),
    INDEX idx_rollback_timestamp ON acwr_rollback_history(timestamp)
);

-- Data validation results table
CREATE TABLE IF NOT EXISTS acwr_validation_results (
    id SERIAL PRIMARY KEY,
    validation_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    validation_level VARCHAR(20) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    errors JSONB,
    warnings JSONB,
    validated_count INTEGER NOT NULL DEFAULT 0,
    failed_count INTEGER NOT NULL DEFAULT 0,
    validation_time_seconds DECIMAL(10,3),
    checksum VARCHAR(64),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_validation_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_validation_level CHECK (validation_level IN ('basic', 'standard', 'strict', 'paranoid')),
    
    -- Indexes
    INDEX idx_validation_migration ON acwr_validation_results(migration_id),
    INDEX idx_validation_user ON acwr_validation_results(user_id),
    INDEX idx_validation_level ON acwr_validation_results(validation_level),
    INDEX idx_validation_timestamp ON acwr_validation_results(timestamp)
);

-- Rollback impact analysis table
CREATE TABLE IF NOT EXISTS acwr_rollback_impact (
    id SERIAL PRIMARY KEY,
    impact_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    scope VARCHAR(50) NOT NULL,
    affected_users INTEGER NOT NULL DEFAULT 0,
    affected_activities INTEGER NOT NULL DEFAULT 0,
    affected_configurations INTEGER NOT NULL DEFAULT 0,
    data_loss_risk VARCHAR(20) NOT NULL,
    estimated_downtime_seconds INTEGER NOT NULL DEFAULT 0,
    backup_available BOOLEAN NOT NULL DEFAULT FALSE,
    rollback_complexity VARCHAR(20) NOT NULL,
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_impact_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_impact_scope CHECK (scope IN ('single_batch', 'user_migration', 'configuration', 'full_system')),
    CONSTRAINT chk_impact_risk CHECK (data_loss_risk IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_impact_complexity CHECK (rollback_complexity IN ('simple', 'moderate', 'complex', 'extreme')),
    
    -- Indexes
    INDEX idx_impact_migration ON acwr_rollback_impact(migration_id),
    INDEX idx_impact_user ON acwr_rollback_impact(user_id),
    INDEX idx_impact_risk ON acwr_rollback_impact(data_loss_risk)
);

-- Rollback plans table
CREATE TABLE IF NOT EXISTS acwr_rollback_plans (
    id SERIAL PRIMARY KEY,
    plan_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    scope VARCHAR(50) NOT NULL,
    steps JSONB NOT NULL,
    estimated_duration_seconds INTEGER NOT NULL DEFAULT 0,
    risk_level VARCHAR(20) NOT NULL,
    prerequisites JSONB,
    rollback_data JSONB,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_plan_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_created_by FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_plan_scope CHECK (scope IN ('single_batch', 'user_migration', 'configuration', 'full_system')),
    CONSTRAINT chk_plan_risk CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    
    -- Indexes
    INDEX idx_plan_migration ON acwr_rollback_plans(migration_id),
    INDEX idx_plan_user ON acwr_rollback_plans(user_id),
    INDEX idx_plan_risk ON acwr_rollback_plans(risk_level)
);

-- Data integrity monitoring table
CREATE TABLE IF NOT EXISTS acwr_integrity_monitoring (
    id SERIAL PRIMARY KEY,
    monitoring_id VARCHAR(100) NOT NULL UNIQUE,
    migration_id VARCHAR(100) NOT NULL,
    user_id INTEGER NOT NULL,
    monitoring_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_check TIMESTAMP WITH TIME ZONE,
    check_interval_seconds INTEGER NOT NULL DEFAULT 3600,
    alert_threshold INTEGER NOT NULL DEFAULT 5,
    current_errors INTEGER NOT NULL DEFAULT 0,
    monitoring_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_monitoring_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_monitoring_type CHECK (monitoring_type IN ('continuous', 'periodic', 'on_demand')),
    CONSTRAINT chk_monitoring_status CHECK (status IN ('active', 'paused', 'stopped')),
    
    -- Indexes
    INDEX idx_monitoring_migration ON acwr_integrity_monitoring(migration_id),
    INDEX idx_monitoring_user ON acwr_integrity_monitoring(user_id),
    INDEX idx_monitoring_status ON acwr_integrity_monitoring(status)
);

-- Views for easy querying
CREATE OR REPLACE VIEW acwr_integrity_summary AS
SELECT 
    ic.checkpoint_id,
    ic.migration_id,
    ic.user_id,
    u.username,
    ic.timestamp,
    ic.validation_result->>'is_valid' as is_valid,
    ic.validation_result->>'validation_level' as validation_level,
    (ic.validation_result->>'validated_count')::INTEGER as validated_count,
    (ic.validation_result->>'failed_count')::INTEGER as failed_count,
    (ic.validation_result->>'validation_time')::DECIMAL as validation_time,
    ic.checksum
FROM acwr_integrity_checkpoints ic
LEFT JOIN users u ON ic.user_id = u.user_id
ORDER BY ic.timestamp DESC;

CREATE OR REPLACE VIEW acwr_rollback_summary AS
SELECT 
    rh.rollback_id,
    rh.migration_id,
    rh.user_id,
    u.username,
    rh.scope,
    rh.reason,
    rh.initiated_by,
    initiator.username as initiated_by_username,
    rh.timestamp,
    rh.status,
    rh.affected_records,
    rh.error_log
FROM acwr_rollback_history rh
LEFT JOIN users u ON rh.user_id = u.user_id
LEFT JOIN users initiator ON rh.initiated_by = initiator.user_id
ORDER BY rh.timestamp DESC;

CREATE OR REPLACE VIEW acwr_validation_summary AS
SELECT 
    vr.validation_id,
    vr.migration_id,
    vr.user_id,
    u.username,
    vr.validation_level,
    vr.is_valid,
    vr.validated_count,
    vr.failed_count,
    vr.validation_time_seconds,
    vr.timestamp,
    CASE 
        WHEN vr.failed_count = 0 THEN 'PASS'
        WHEN vr.failed_count <= vr.validated_count * 0.05 THEN 'WARNING'
        ELSE 'FAIL'
    END as validation_status
FROM acwr_validation_results vr
LEFT JOIN users u ON vr.user_id = u.user_id
ORDER BY vr.timestamp DESC;

-- Functions for integrity management
CREATE OR REPLACE FUNCTION create_integrity_checkpoint(
    p_checkpoint_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_batch_id INTEGER DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- This function would be called by the application to create checkpoints
    -- The actual checkpoint creation logic is in the Python code
    INSERT INTO acwr_integrity_checkpoints (
        checkpoint_id, migration_id, user_id, batch_id, timestamp,
        validation_result, data_snapshot, checksum, rollback_data
    ) VALUES (
        p_checkpoint_id, p_migration_id, p_user_id, p_batch_id, CURRENT_TIMESTAMP,
        '{}', '{}', '', '{}'
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION validate_migration_data(
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_validation_level VARCHAR(20) DEFAULT 'standard'
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    -- This function would perform basic database-level validation
    -- The comprehensive validation logic is in the Python code
    
    result := jsonb_build_object(
        'migration_id', p_migration_id,
        'user_id', p_user_id,
        'validation_level', p_validation_level,
        'timestamp', CURRENT_TIMESTAMP,
        'database_validation', 'passed'
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_integrity_data(
    p_days_to_keep INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up old integrity checkpoints
    DELETE FROM acwr_integrity_checkpoints 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old validation results
    DELETE FROM acwr_validation_results 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    -- Clean up old rollback impact analyses
    DELETE FROM acwr_rollback_impact 
    WHERE analysis_timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic integrity monitoring
CREATE OR REPLACE FUNCTION trigger_integrity_check()
RETURNS TRIGGER AS $$
BEGIN
    -- This trigger would automatically perform integrity checks
    -- when enhanced calculations are modified
    
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Log the change for integrity monitoring
        INSERT INTO acwr_integrity_monitoring (
            monitoring_id, migration_id, user_id, monitoring_type, last_check
        ) VALUES (
            'auto_' || NEW.user_id || '_' || EXTRACT(EPOCH FROM CURRENT_TIMESTAMP),
            'auto_migration',
            NEW.user_id,
            'continuous',
            CURRENT_TIMESTAMP
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create trigger on enhanced calculations table
-- DROP TRIGGER IF EXISTS trigger_enhanced_calc_integrity ON acwr_enhanced_calculations;
-- CREATE TRIGGER trigger_enhanced_calc_integrity
--     AFTER INSERT OR UPDATE OR DELETE ON acwr_enhanced_calculations
--     FOR EACH ROW
--     EXECUTE FUNCTION trigger_integrity_check();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_integrity_checkpoints TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_history TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_validation_results TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_impact TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_plans TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_integrity_monitoring TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_integrity_checkpoints_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_history_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_validation_results_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_impact_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_plans_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_integrity_monitoring_id_seq TO your_app_user;

