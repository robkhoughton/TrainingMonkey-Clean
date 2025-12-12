-- ================================================================
-- ADD AUTOPSY-INFORMED TRACKING FIELDS TO llm_recommendations
-- Purpose: Track whether recommendations are generated with autopsy insights
-- Date: 2025-10-31
-- ================================================================

BEGIN;

-- Add autopsy tracking columns to llm_recommendations table
ALTER TABLE llm_recommendations 
ADD COLUMN IF NOT EXISTS is_autopsy_informed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS autopsy_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS avg_alignment_score DECIMAL(3,1);

-- Add index for filtering autopsy-informed recommendations
CREATE INDEX IF NOT EXISTS idx_llm_recommendations_autopsy_informed 
ON llm_recommendations (user_id, is_autopsy_informed, target_date);

-- Verify the changes
DO $$
DECLARE
    autopsy_informed_exists BOOLEAN;
    autopsy_count_exists BOOLEAN;
    avg_alignment_exists BOOLEAN;
BEGIN
    -- Check if columns exist
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'llm_recommendations' 
        AND column_name = 'is_autopsy_informed'
    ) INTO autopsy_informed_exists;
    
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'llm_recommendations' 
        AND column_name = 'autopsy_count'
    ) INTO autopsy_count_exists;
    
    SELECT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'llm_recommendations' 
        AND column_name = 'avg_alignment_score'
    ) INTO avg_alignment_exists;
    
    IF autopsy_informed_exists AND autopsy_count_exists AND avg_alignment_exists THEN
        RAISE NOTICE 'SUCCESS: All autopsy tracking columns added to llm_recommendations';
        RAISE NOTICE '  - is_autopsy_informed: %', autopsy_informed_exists;
        RAISE NOTICE '  - autopsy_count: %', autopsy_count_exists;
        RAISE NOTICE '  - avg_alignment_score: %', avg_alignment_exists;
    ELSE
        RAISE EXCEPTION 'Failed to add one or more columns';
    END IF;
END $$;

COMMIT;

-- Display summary
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'llm_recommendations'
AND column_name IN ('is_autopsy_informed', 'autopsy_count', 'avg_alignment_score')
ORDER BY column_name;












