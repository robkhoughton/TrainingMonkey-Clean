-- ACWR Migration Rollback Execution System Database Schema
-- Creates tables for rollback execution tracking and backup management

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
    
    -- Foreign key constraints
    CONSTRAINT fk_rollback_exec_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_rollback_exec_scope CHECK (scope IN ('single_batch', 'user_migration', 'configuration', 'full_system')),
    CONSTRAINT chk_rollback_exec_status CHECK (status IN ('pending', 'preparing', 'backing_up', 'validating', 'executing', 'verifying', 'completed', 'failed', 'cancelled')),
    
    -- Indexes
    INDEX idx_rollback_exec_migration ON acwr_rollback_executions(migration_id),
    INDEX idx_rollback_exec_user ON acwr_rollback_executions(user_id),
    INDEX idx_rollback_exec_status ON acwr_rollback_executions(status),
    INDEX idx_rollback_exec_start_time ON acwr_rollback_executions(start_time)
);

-- Rollback backup storage table
CREATE TABLE IF NOT EXISTS acwr_rollback_backups (
    id SERIAL PRIMARY KEY,
    backup_id VARCHAR(100) NOT NULL UNIQUE,
    rollback_id VARCHAR(100) NOT NULL,
    backup_data JSONB NOT NULL,
    backup_size INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_rollback_backup_exec FOREIGN KEY (rollback_id) REFERENCES acwr_rollback_executions(rollback_id) ON DELETE CASCADE,
    
    -- Indexes
    INDEX idx_rollback_backup_rollback ON acwr_rollback_backups(rollback_id),
    INDEX idx_rollback_backup_created ON acwr_rollback_backups(created_at)
);

-- Rollback execution steps table
CREATE TABLE IF NOT EXISTS acwr_rollback_execution_steps (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    step_id VARCHAR(50) NOT NULL,
    step_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    start_time TIMESTAMP WITH TIME ZONE,
    end_time TIMESTAMP WITH TIME ZONE,
    duration DECIMAL(10,3), -- seconds
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,
    affected_records INTEGER NOT NULL DEFAULT 0,
    step_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_rollback_step_exec FOREIGN KEY (rollback_id) REFERENCES acwr_rollback_executions(rollback_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_rollback_step_status CHECK (status IN ('pending', 'preparing', 'backing_up', 'validating', 'executing', 'verifying', 'completed', 'failed', 'cancelled')),
    
    -- Indexes
    INDEX idx_rollback_step_rollback ON acwr_rollback_execution_steps(rollback_id),
    INDEX idx_rollback_step_status ON acwr_rollback_execution_steps(status),
    INDEX idx_rollback_step_start_time ON acwr_rollback_execution_steps(start_time)
);

-- Rollback execution monitoring table
CREATE TABLE IF NOT EXISTS acwr_rollback_monitoring (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    monitoring_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_check TIMESTAMP WITH TIME ZONE,
    check_interval_seconds INTEGER NOT NULL DEFAULT 60,
    alert_threshold INTEGER NOT NULL DEFAULT 5,
    current_errors INTEGER NOT NULL DEFAULT 0,
    monitoring_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_rollback_monitor_exec FOREIGN KEY (rollback_id) REFERENCES acwr_rollback_executions(rollback_id) ON DELETE CASCADE,
    
    -- Check constraints
    CONSTRAINT chk_rollback_monitor_type CHECK (monitoring_type IN ('execution_progress', 'step_completion', 'error_detection', 'performance_monitoring')),
    CONSTRAINT chk_rollback_monitor_status CHECK (status IN ('active', 'paused', 'stopped')),
    
    -- Indexes
    INDEX idx_rollback_monitor_rollback ON acwr_rollback_monitoring(rollback_id),
    INDEX idx_rollback_monitor_status ON acwr_rollback_monitoring(status)
);

-- Rollback execution alerts table
CREATE TABLE IF NOT EXISTS acwr_rollback_alerts (
    id SERIAL PRIMARY KEY,
    rollback_id VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    acknowledged BOOLEAN NOT NULL DEFAULT FALSE,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    CONSTRAINT fk_rollback_alert_exec FOREIGN KEY (rollback_id) REFERENCES acwr_rollback_executions(rollback_id) ON DELETE CASCADE,
    CONSTRAINT fk_rollback_alert_ack_by FOREIGN KEY (acknowledged_by) REFERENCES users(user_id) ON DELETE SET NULL,
    
    -- Check constraints
    CONSTRAINT chk_rollback_alert_type CHECK (alert_type IN ('execution_failed', 'step_failed', 'validation_failed', 'backup_failed', 'performance_degraded', 'timeout_warning')),
    CONSTRAINT chk_rollback_alert_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    
    -- Indexes
    INDEX idx_rollback_alert_rollback ON acwr_rollback_alerts(rollback_id),
    INDEX idx_rollback_alert_severity ON acwr_rollback_alerts(severity),
    INDEX idx_rollback_alert_acknowledged ON acwr_rollback_alerts(acknowledged),
    INDEX idx_rollback_alert_created ON acwr_rollback_alerts(created_at)
);

-- Views for easy querying
CREATE OR REPLACE VIEW acwr_rollback_execution_summary AS
SELECT 
    re.rollback_id,
    re.migration_id,
    re.user_id,
    u.username,
    re.scope,
    re.status,
    re.start_time,
    re.end_time,
    re.total_duration,
    re.total_affected_records,
    re.backup_location,
    re.verification_passed,
    re.success,
    CASE 
        WHEN re.status = 'completed' AND re.success = true THEN 'SUCCESS'
        WHEN re.status = 'failed' OR re.success = false THEN 'FAILED'
        WHEN re.status = 'cancelled' THEN 'CANCELLED'
        ELSE 'IN_PROGRESS'
    END as execution_status
FROM acwr_rollback_executions re
LEFT JOIN users u ON re.user_id = u.user_id
ORDER BY re.start_time DESC;

CREATE OR REPLACE VIEW acwr_rollback_step_summary AS
SELECT 
    res.rollback_id,
    res.step_id,
    res.step_name,
    res.status,
    res.start_time,
    res.end_time,
    res.duration,
    res.success,
    res.affected_records,
    res.error_message
FROM acwr_rollback_execution_steps res
ORDER BY res.rollback_id, res.start_time;

CREATE OR REPLACE VIEW acwr_rollback_alert_summary AS
SELECT 
    ra.rollback_id,
    ra.alert_type,
    ra.severity,
    ra.message,
    ra.acknowledged,
    ra.acknowledged_by,
    ack_user.username as acknowledged_by_username,
    ra.created_at
FROM acwr_rollback_alerts ra
LEFT JOIN users ack_user ON ra.acknowledged_by = ack_user.user_id
ORDER BY ra.created_at DESC;

-- Functions for rollback execution management
CREATE OR REPLACE FUNCTION create_rollback_execution(
    p_rollback_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_scope VARCHAR(50)
) RETURNS VOID AS $$
BEGIN
    -- This function would be called by the application to create rollback executions
    INSERT INTO acwr_rollback_executions (
        rollback_id, migration_id, user_id, scope, status, start_time
    ) VALUES (
        p_rollback_id, p_migration_id, p_user_id, p_scope, 'pending', CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_rollback_execution_status(
    p_rollback_id VARCHAR(100),
    p_status VARCHAR(20),
    p_success BOOLEAN DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Update rollback execution status
    UPDATE acwr_rollback_executions 
    SET status = p_status,
        success = COALESCE(p_success, success),
        end_time = CASE WHEN p_status IN ('completed', 'failed', 'cancelled') THEN CURRENT_TIMESTAMP ELSE end_time END
    WHERE rollback_id = p_rollback_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_rollback_alert(
    p_rollback_id VARCHAR(100),
    p_alert_type VARCHAR(50),
    p_severity VARCHAR(20),
    p_message TEXT,
    p_details JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    -- Create rollback execution alert
    INSERT INTO acwr_rollback_alerts (
        rollback_id, alert_type, severity, message, details
    ) VALUES (
        p_rollback_id, p_alert_type, p_severity, p_message, p_details
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_rollback_data(
    p_days_to_keep INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Clean up old rollback executions
    DELETE FROM acwr_rollback_executions 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old rollback backups
    DELETE FROM acwr_rollback_backups 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    -- Clean up old rollback alerts
    DELETE FROM acwr_rollback_alerts 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic rollback monitoring
CREATE OR REPLACE FUNCTION trigger_rollback_execution_monitoring()
RETURNS TRIGGER AS $$
BEGIN
    -- This trigger would automatically monitor rollback executions
    -- when execution status changes
    
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Create monitoring entry for new executions
        IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND OLD.status != NEW.status) THEN
            INSERT INTO acwr_rollback_monitoring (
                rollback_id, monitoring_type, last_check
            ) VALUES (
                NEW.rollback_id, 'execution_progress', CURRENT_TIMESTAMP
            );
        END IF;
        
        -- Create alerts for failed executions
        IF TG_OP = 'UPDATE' AND NEW.status = 'failed' AND OLD.status != 'failed' THEN
            INSERT INTO acwr_rollback_alerts (
                rollback_id, alert_type, severity, message
            ) VALUES (
                NEW.rollback_id, 'execution_failed', 'high', 
                'Rollback execution failed for migration ' || NEW.migration_id
            );
        END IF;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create trigger on rollback executions table
-- DROP TRIGGER IF EXISTS trigger_rollback_exec_monitoring ON acwr_rollback_executions;
-- CREATE TRIGGER trigger_rollback_exec_monitoring
--     AFTER INSERT OR UPDATE ON acwr_rollback_executions
--     FOR EACH ROW
--     EXECUTE FUNCTION trigger_rollback_execution_monitoring();

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_executions TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_backups TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_execution_steps TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_monitoring TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_rollback_alerts TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_executions_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_backups_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_execution_steps_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_monitoring_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_rollback_alerts_id_seq TO your_app_user;

