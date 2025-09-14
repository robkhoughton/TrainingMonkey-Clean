-- Fix Missing Columns in assignment_history and user_acwr_configurations Tables
-- This script adds the missing columns that the ACWRConfigurationService expects

-- Add missing columns to assignment_history table
ALTER TABLE assignment_history 
ADD COLUMN IF NOT EXISTS previous_config_id INTEGER,
ADD COLUMN IF NOT EXISTS timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

-- Add foreign key constraint for previous_config_id
ALTER TABLE assignment_history 
ADD CONSTRAINT fk_assignment_history_previous_config 
FOREIGN KEY (previous_config_id) REFERENCES acwr_configurations(id) ON DELETE SET NULL;

-- Update existing records to have timestamp if it's NULL
UPDATE assignment_history 
SET timestamp = assigned_at 
WHERE timestamp IS NULL;

-- Add index for previous_config_id
CREATE INDEX IF NOT EXISTS idx_assignment_history_previous_config_id ON assignment_history(previous_config_id);

-- Add index for timestamp
CREATE INDEX IF NOT EXISTS idx_assignment_history_timestamp ON assignment_history(timestamp);

-- Add missing columns to user_acwr_configurations table
ALTER TABLE user_acwr_configurations 
ADD COLUMN IF NOT EXISTS unassigned_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS unassigned_by INTEGER,
ADD COLUMN IF NOT EXISTS assignment_reason TEXT;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_user_acwr_config_unassigned_at ON user_acwr_configurations(unassigned_at);
CREATE INDEX IF NOT EXISTS idx_user_acwr_config_unassigned_by ON user_acwr_configurations(unassigned_by);

-- Verify the table structures
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'assignment_history'
ORDER BY ordinal_position;

SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'user_acwr_configurations'
ORDER BY ordinal_position;
