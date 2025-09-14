-- Fix Missing Columns in assignment_history and user_acwr_configurations Tables (Safe Version)
-- This script safely adds missing columns without failing on existing constraints

-- Add missing columns to assignment_history table (ignore if already exist)
DO $$ 
BEGIN
    -- Add previous_config_id column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'assignment_history' AND column_name = 'previous_config_id') THEN
        ALTER TABLE assignment_history ADD COLUMN previous_config_id INTEGER;
    END IF;
    
    -- Add timestamp column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'assignment_history' AND column_name = 'timestamp') THEN
        ALTER TABLE assignment_history ADD COLUMN timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Add foreign key constraint for previous_config_id (ignore if already exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.table_constraints 
                   WHERE constraint_name = 'fk_assignment_history_previous_config') THEN
        ALTER TABLE assignment_history 
        ADD CONSTRAINT fk_assignment_history_previous_config 
        FOREIGN KEY (previous_config_id) REFERENCES acwr_configurations(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Update existing records to have timestamp if it's NULL
UPDATE assignment_history 
SET timestamp = assigned_at 
WHERE timestamp IS NULL;

-- Add indexes (ignore if already exist)
CREATE INDEX IF NOT EXISTS idx_assignment_history_previous_config_id ON assignment_history(previous_config_id);
CREATE INDEX IF NOT EXISTS idx_assignment_history_timestamp ON assignment_history(timestamp);

-- Add missing columns to user_acwr_configurations table (ignore if already exist)
DO $$ 
BEGIN
    -- Add unassigned_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_acwr_configurations' AND column_name = 'unassigned_at') THEN
        ALTER TABLE user_acwr_configurations ADD COLUMN unassigned_at TIMESTAMP WITH TIME ZONE;
    END IF;
    
    -- Add unassigned_by column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_acwr_configurations' AND column_name = 'unassigned_by') THEN
        ALTER TABLE user_acwr_configurations ADD COLUMN unassigned_by INTEGER;
    END IF;
    
    -- Add assignment_reason column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'user_acwr_configurations' AND column_name = 'assignment_reason') THEN
        ALTER TABLE user_acwr_configurations ADD COLUMN assignment_reason TEXT;
    END IF;
END $$;

-- Add indexes for new columns (ignore if already exist)
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
