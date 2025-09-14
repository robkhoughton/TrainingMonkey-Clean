-- ACWR Migration Monitoring and Logging System Database Schema (Fixed)
-- Creates tables for comprehensive migration monitoring, logging, and alerting
-- Note: Foreign key constraints to 'users' table removed to avoid dependency issues

-- Migration logs table
CREATE TABLE IF NOT EXISTS acwr_migration_logs (
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
CREATE TABLE IF NOT EXISTS acwr_migration_alerts (
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
CREATE TABLE IF NOT EXISTS acwr_migration_events (
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
CREATE TABLE IF NOT EXISTS acwr_migration_health_metrics (
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
CREATE TABLE IF NOT EXISTS acwr_migration_monitoring_config (
    id SERIAL PRIMARY KEY,
    config_name VARCHAR(100) NOT NULL UNIQUE,
    config_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Migration notification preferences table
CREATE TABLE IF NOT EXISTS acwr_migration_notification_preferences (
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_migration_log_migration ON acwr_migration_logs(migration_id);
CREATE INDEX IF NOT EXISTS idx_migration_log_user ON acwr_migration_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_log_timestamp ON acwr_migration_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_migration_log_level ON acwr_migration_logs(level);
CREATE INDEX IF NOT EXISTS idx_migration_log_source ON acwr_migration_logs(source);

CREATE INDEX IF NOT EXISTS idx_migration_alert_migration ON acwr_migration_alerts(migration_id);
CREATE INDEX IF NOT EXISTS idx_migration_alert_user ON acwr_migration_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_alert_timestamp ON acwr_migration_alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_migration_alert_severity ON acwr_migration_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_migration_alert_type ON acwr_migration_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_migration_alert_acknowledged ON acwr_migration_alerts(acknowledged);
CREATE INDEX IF NOT EXISTS idx_migration_alert_resolved ON acwr_migration_alerts(resolved);

CREATE INDEX IF NOT EXISTS idx_migration_event_migration ON acwr_migration_events(migration_id);
CREATE INDEX IF NOT EXISTS idx_migration_event_user ON acwr_migration_events(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_event_timestamp ON acwr_migration_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_migration_event_type ON acwr_migration_events(event_type);
CREATE INDEX IF NOT EXISTS idx_migration_event_source ON acwr_migration_events(source);

CREATE INDEX IF NOT EXISTS idx_migration_health_migration ON acwr_migration_health_metrics(migration_id);
CREATE INDEX IF NOT EXISTS idx_migration_health_timestamp ON acwr_migration_health_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_migration_health_status ON acwr_migration_health_metrics(status);
CREATE INDEX IF NOT EXISTS idx_migration_health_performance ON acwr_migration_health_metrics(performance_score);

CREATE INDEX IF NOT EXISTS idx_migration_monitoring_config_name ON acwr_migration_monitoring_config(config_name);
CREATE INDEX IF NOT EXISTS idx_migration_monitoring_config_active ON acwr_migration_monitoring_config(is_active);

CREATE INDEX IF NOT EXISTS idx_migration_notification_user ON acwr_migration_notification_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_migration_notification_type ON acwr_migration_notification_preferences(notification_type);
CREATE INDEX IF NOT EXISTS idx_migration_notification_enabled ON acwr_migration_notification_preferences(enabled);

-- Views for easy querying (without user table joins)
CREATE OR REPLACE VIEW acwr_migration_log_summary AS
SELECT 
    ml.migration_id,
    ml.user_id,
    COUNT(*) as total_logs,
    COUNT(CASE WHEN ml.level = 'ERROR' THEN 1 END) as error_count,
    COUNT(CASE WHEN ml.level = 'WARNING' THEN 1 END) as warning_count,
    COUNT(CASE WHEN ml.level = 'INFO' THEN 1 END) as info_count,
    MIN(ml.timestamp) as first_log,
    MAX(ml.timestamp) as last_log,
    AVG(ml.execution_time) as avg_execution_time
FROM acwr_migration_logs ml
GROUP BY ml.migration_id, ml.user_id
ORDER BY MAX(ml.timestamp) DESC;

CREATE OR REPLACE VIEW acwr_migration_alert_summary AS
SELECT 
    ma.migration_id,
    ma.user_id,
    COUNT(*) as total_alerts,
    COUNT(CASE WHEN ma.severity = 'critical' THEN 1 END) as critical_alerts,
    COUNT(CASE WHEN ma.severity = 'high' THEN 1 END) as high_alerts,
    COUNT(CASE WHEN ma.severity = 'medium' THEN 1 END) as medium_alerts,
    COUNT(CASE WHEN ma.severity = 'low' THEN 1 END) as low_alerts,
    COUNT(CASE WHEN ma.acknowledged = TRUE THEN 1 END) as acknowledged_alerts,
    COUNT(CASE WHEN ma.resolved = TRUE THEN 1 END) as resolved_alerts,
    MIN(ma.timestamp) as first_alert,
    MAX(ma.timestamp) as last_alert
FROM acwr_migration_alerts ma
GROUP BY ma.migration_id, ma.user_id
ORDER BY MAX(ma.timestamp) DESC;

CREATE OR REPLACE VIEW acwr_migration_health_summary AS
SELECT 
    mhm.migration_id,
    mhm.status,
    mhm.progress_percentage,
    mhm.performance_score,
    mhm.throughput_activities_per_second,
    mhm.success_rate,
    mhm.error_count,
    mhm.warning_count,
    mhm.timestamp as last_updated,
    CASE 
        WHEN mhm.performance_score >= 90 THEN 'EXCELLENT'
        WHEN mhm.performance_score >= 75 THEN 'GOOD'
        WHEN mhm.performance_score >= 50 THEN 'FAIR'
        WHEN mhm.performance_score >= 25 THEN 'POOR'
        ELSE 'CRITICAL'
    END as health_status
FROM acwr_migration_health_metrics mhm
INNER JOIN (
    SELECT migration_id, MAX(timestamp) as max_timestamp
    FROM acwr_migration_health_metrics
    GROUP BY migration_id
) latest ON mhm.migration_id = latest.migration_id AND mhm.timestamp = latest.max_timestamp
ORDER BY mhm.timestamp DESC;

-- Functions for migration monitoring management
CREATE OR REPLACE FUNCTION create_migration_log(
    p_log_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_level VARCHAR(20),
    p_message TEXT,
    p_details JSONB DEFAULT NULL,
    p_source VARCHAR(100) DEFAULT 'system',
    p_execution_time DECIMAL(10,3) DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_migration_logs (
        log_id, migration_id, user_id, timestamp, level, message, details, source, execution_time
    ) VALUES (
        p_log_id, p_migration_id, p_user_id, CURRENT_TIMESTAMP, p_level, p_message, p_details, p_source, p_execution_time
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION create_migration_alert(
    p_alert_id VARCHAR(100),
    p_migration_id VARCHAR(100),
    p_user_id INTEGER,
    p_severity VARCHAR(20),
    p_alert_type VARCHAR(50),
    p_title VARCHAR(200),
    p_message TEXT,
    p_details JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_migration_alerts (
        alert_id, migration_id, user_id, timestamp, severity, alert_type, title, message, details
    ) VALUES (
        p_alert_id, p_migration_id, p_user_id, CURRENT_TIMESTAMP, p_severity, p_alert_type, p_title, p_message, p_details
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION update_migration_health_metrics(
    p_migration_id VARCHAR(100),
    p_status VARCHAR(20),
    p_progress_percentage DECIMAL(5,2),
    p_performance_score DECIMAL(5,2),
    p_throughput DECIMAL(10,2),
    p_success_rate DECIMAL(5,4),
    p_error_count INTEGER,
    p_warning_count INTEGER,
    p_resource_usage JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO acwr_migration_health_metrics (
        migration_id, timestamp, status, progress_percentage, performance_score,
        throughput_activities_per_second, success_rate, error_count, warning_count, resource_usage
    ) VALUES (
        p_migration_id, CURRENT_TIMESTAMP, p_status, p_progress_percentage, p_performance_score,
        p_throughput, p_success_rate, p_error_count, p_warning_count, p_resource_usage
    );
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION cleanup_old_migration_data(
    p_log_retention_days INTEGER DEFAULT 30,
    p_alert_retention_days INTEGER DEFAULT 90,
    p_event_retention_days INTEGER DEFAULT 30
) RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
BEGIN
    -- Clean up old logs
    DELETE FROM acwr_migration_logs 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_log_retention_days;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old alerts (only resolved ones)
    DELETE FROM acwr_migration_alerts 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_alert_retention_days
    AND resolved = TRUE;
    
    -- Clean up old events
    DELETE FROM acwr_migration_events 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_event_retention_days;
    
    -- Clean up old health metrics (keep only recent ones)
    DELETE FROM acwr_migration_health_metrics 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '1 day' * 7; -- Keep 7 days of health metrics
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_logs TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_alerts TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_events TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_health_metrics TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_monitoring_config TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON acwr_migration_notification_preferences TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_logs_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_alerts_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_events_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_health_metrics_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_monitoring_config_id_seq TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE acwr_migration_notification_preferences_id_seq TO your_app_user;
