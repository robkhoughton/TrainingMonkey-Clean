-- Fix Missing ACWR Configuration Tables
-- This script adds the missing core ACWR tables that are required for the configuration system

-- Drop existing tables if they exist (for safe re-execution)
DROP TABLE IF EXISTS assignment_history CASCADE;
DROP TABLE IF EXISTS enhanced_acwr_calculations CASCADE;
DROP TABLE IF EXISTS user_acwr_configurations CASCADE;
DROP TABLE IF EXISTS acwr_configurations CASCADE;

-- Create acwr_configurations table
CREATE TABLE acwr_configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    chronic_period_days INTEGER NOT NULL DEFAULT 28 CHECK (chronic_period_days >= 28 AND chronic_period_days <= 90),
    decay_rate REAL NOT NULL DEFAULT 0.05 CHECK (decay_rate > 0 AND decay_rate <= 1.0),
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    notes TEXT
);

-- Create user_acwr_configurations table
CREATE TABLE user_acwr_configurations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    configuration_id INTEGER NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id) ON DELETE CASCADE,
    UNIQUE(user_id, configuration_id)
);

-- Create enhanced_acwr_calculations table
CREATE TABLE enhanced_acwr_calculations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    activity_date DATE NOT NULL,
    configuration_id INTEGER NOT NULL,
    chronic_period_days INTEGER NOT NULL,
    decay_rate REAL NOT NULL,
    enhanced_chronic_load REAL,
    enhanced_chronic_trimp REAL,
    enhanced_acute_chronic_ratio REAL,
    enhanced_trimp_acute_chronic_ratio REAL,
    enhanced_normalized_divergence REAL,
    calculation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id) ON DELETE CASCADE,
    UNIQUE(user_id, activity_date, configuration_id)
);

-- Create assignment_history table
CREATE TABLE assignment_history (
    history_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    configuration_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL CHECK (action IN ('assigned', 'unassigned', 'updated')),
    assigned_by INTEGER NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    notes TEXT,
    
    -- Foreign key constraints (only to acwr_configurations, not users to avoid deployment issues)
    CONSTRAINT fk_assignment_history_config FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_user_acwr_config_user_id ON user_acwr_configurations(user_id);
CREATE INDEX idx_user_acwr_config_config_id ON user_acwr_configurations(configuration_id);
CREATE INDEX idx_enhanced_acwr_user_date ON enhanced_acwr_calculations(user_id, activity_date);
CREATE INDEX idx_enhanced_acwr_config_id ON enhanced_acwr_calculations(configuration_id);
CREATE INDEX idx_acwr_config_active ON acwr_configurations(is_active);
CREATE INDEX idx_assignment_history_user_id ON assignment_history(user_id);
CREATE INDEX idx_assignment_history_configuration_id ON assignment_history(configuration_id);
CREATE INDEX idx_assignment_history_assigned_by ON assignment_history(assigned_by);
CREATE INDEX idx_assignment_history_assigned_at ON assignment_history(assigned_at);
CREATE INDEX idx_assignment_history_action ON assignment_history(action);

-- Insert default configuration
INSERT INTO acwr_configurations (
    name, 
    description, 
    chronic_period_days, 
    decay_rate, 
    is_active,
    created_by,
    notes
) VALUES (
    'default_enhanced',
    'Default enhanced ACWR with 42-day chronic period and moderate decay',
    42,
    0.05,
    TRUE,
    1,
    'Default configuration for enhanced ACWR calculation'
);

-- Insert a sample assignment history record
INSERT INTO assignment_history (user_id, configuration_id, action, assigned_by, reason, notes)
VALUES (1, 1, 'assigned', 1, 'Initial setup', 'Default configuration assigned to admin user during system setup');

-- Add comments for documentation
COMMENT ON TABLE acwr_configurations IS 'ACWR configuration settings with configurable chronic period and decay rate';
COMMENT ON TABLE user_acwr_configurations IS 'User assignments to specific ACWR configurations';
COMMENT ON TABLE enhanced_acwr_calculations IS 'Enhanced ACWR calculation results using exponential decay';
COMMENT ON TABLE assignment_history IS 'Tracks assignment history of ACWR configurations to users';

-- Verify all tables were created successfully
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_name IN ('acwr_configurations', 'user_acwr_configurations', 'enhanced_acwr_calculations', 'assignment_history')
ORDER BY table_name;
