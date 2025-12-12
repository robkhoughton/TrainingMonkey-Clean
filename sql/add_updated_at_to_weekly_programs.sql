-- Add updated_at column to weekly_programs table (optional enhancement)
-- Note: The code has been updated to work without this column
-- This migration can be run later for consistency with the original schema design

ALTER TABLE weekly_programs 
ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();

-- Update existing rows to have updated_at = generated_at
UPDATE weekly_programs SET updated_at = generated_at WHERE updated_at IS NULL;

-- Add comment
COMMENT ON COLUMN weekly_programs.updated_at IS 'Timestamp when the program was last regenerated (optional tracking field)';




