-- Add missing assignment_history table for ACWR configuration system
-- This table tracks when configurations are assigned/unassigned to users

-- Drop if exists (for safe re-execution)
DROP TABLE IF EXISTS assignment_history CASCADE;

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
    
    -- Indexes for performance
    CONSTRAINT fk_assignment_history_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_assignment_history_config FOREIGN KEY (configuration_id) REFERENCES acwr_configurations(configuration_id) ON DELETE CASCADE,
    CONSTRAINT fk_assignment_history_admin FOREIGN KEY (assigned_by) REFERENCES users(user_id) ON DELETE RESTRICT
);

-- Create indexes for better query performance
CREATE INDEX idx_assignment_history_user_id ON assignment_history(user_id);
CREATE INDEX idx_assignment_history_configuration_id ON assignment_history(configuration_id);
CREATE INDEX idx_assignment_history_assigned_by ON assignment_history(assigned_by);
CREATE INDEX idx_assignment_history_assigned_at ON assignment_history(assigned_at);
CREATE INDEX idx_assignment_history_action ON assignment_history(action);

-- Add comments for documentation
COMMENT ON TABLE assignment_history IS 'Tracks assignment history of ACWR configurations to users';
COMMENT ON COLUMN assignment_history.history_id IS 'Unique identifier for assignment history record';
COMMENT ON COLUMN assignment_history.user_id IS 'User who was assigned/unassigned the configuration';
COMMENT ON COLUMN assignment_history.configuration_id IS 'ACWR configuration that was assigned/unassigned';
COMMENT ON COLUMN assignment_history.action IS 'Type of action: assigned, unassigned, or updated';
COMMENT ON COLUMN assignment_history.assigned_by IS 'Admin user who performed the assignment action';
COMMENT ON COLUMN assignment_history.assigned_at IS 'Timestamp when the assignment action occurred';
COMMENT ON COLUMN assignment_history.reason IS 'Reason for the assignment action';
COMMENT ON COLUMN assignment_history.notes IS 'Additional notes about the assignment action';

-- Insert a sample record to verify the table works
INSERT INTO assignment_history (user_id, configuration_id, action, assigned_by, reason, notes)
VALUES (1, 1, 'assigned', 1, 'Initial setup', 'Default configuration assigned to admin user during system setup');

-- Verify the table was created successfully
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'assignment_history'
ORDER BY ordinal_position;
