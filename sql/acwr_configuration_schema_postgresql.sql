-- ACWR Configuration Schema (PostgreSQL)
-- This file contains the SQL schema for configurable ACWR calculations with exponential decay

-- Table to store ACWR configuration settings
CREATE TABLE IF NOT EXISTS acwr_configurations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    chronic_period_days INTEGER NOT NULL DEFAULT 28 CHECK (chronic_period_days >= 28),
    decay_rate REAL NOT NULL DEFAULT 0.05 CHECK (decay_rate > 0 AND decay_rate <= 1.0),
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER,
    notes TEXT
);

-- Table to store user-specific ACWR configuration assignments
CREATE TABLE IF NOT EXISTS user_acwr_configurations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    configuration_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id) ON DELETE CASCADE,
    UNIQUE(user_id, configuration_id)
);

-- Table to store enhanced ACWR calculation results
CREATE TABLE IF NOT EXISTS enhanced_acwr_calculations (
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
    calculation_timestamp TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(id),
    UNIQUE(user_id, activity_date, configuration_id)
);

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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_acwr_config_user_id ON user_acwr_configurations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_acwr_config_config_id ON user_acwr_configurations(configuration_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_acwr_user_date ON enhanced_acwr_calculations(user_id, activity_date);
CREATE INDEX IF NOT EXISTS idx_enhanced_acwr_config_id ON enhanced_acwr_calculations(configuration_id);
CREATE INDEX IF NOT EXISTS idx_acwr_config_active ON acwr_configurations(is_active);
