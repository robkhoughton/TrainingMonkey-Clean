-- ================================================================
-- REVISED MIGRATION: ACTIVITIES TABLE TEXT → DATE CONVERSION
-- Based on actual database assessment results
-- ================================================================

BEGIN;

-- Step 1: activities table conversion (TEXT → DATE)
-- This is the critical fix for ACWR calculations
ALTER TABLE activities ADD COLUMN date_new DATE;

-- Convert TEXT dates to proper DATE format
-- This handles YYYY-MM-DD text format
UPDATE activities SET date_new = date::DATE;

-- Verify data integrity for activities conversion
DO $
DECLARE
    original_count INTEGER;
    converted_count INTEGER;
    sample_original TEXT;
    sample_converted DATE;
BEGIN
    SELECT COUNT(*) INTO original_count FROM activities WHERE date IS NOT NULL;
    SELECT COUNT(*) INTO converted_count FROM activities WHERE date_new IS NOT NULL;

    -- Get sample values for verification
    SELECT date INTO sample_original FROM activities WHERE date IS NOT NULL LIMIT 1;
    SELECT date_new INTO sample_converted FROM activities WHERE date_new IS NOT NULL LIMIT 1;

    IF original_count != converted_count THEN
        RAISE EXCEPTION 'Data integrity check failed for activities: % original vs % converted',
                        original_count, converted_count;
    END IF;

    RAISE NOTICE 'activities conversion verified: % records', converted_count;
    RAISE NOTICE 'Sample: TEXT "%" converted to DATE "%"', sample_original, sample_converted;
END $;

-- Drop old TEXT column and rename new DATE column
ALTER TABLE activities DROP COLUMN date;
ALTER TABLE activities RENAME COLUMN date_new TO date;

-- Recreate constraints
ALTER TABLE activities ALTER COLUMN date SET NOT NULL;

-- Step 2: Create/update optimized indexes for all tables
CREATE INDEX IF NOT EXISTS idx_activities_user_date ON activities (user_id, date);
CREATE INDEX IF NOT EXISTS idx_journal_entries_user_date ON journal_entries (user_id, date);
CREATE INDEX IF NOT EXISTS idx_ai_autopsies_user_date ON ai_autopsies (user_id, date);

-- Step 3: Handle llm_recommendations table (create if not exists)
CREATE TABLE IF NOT EXISTS llm_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_settings(id) NOT NULL,
    date DATE NOT NULL,
    recommendation_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Create index for llm_recommendations
CREATE INDEX IF NOT EXISTS idx_llm_recommendations_user_date ON llm_recommendations (user_id, date);

-- Final verification
DO $
DECLARE
    activities_count INTEGER;
    journal_count INTEGER;
    autopsies_count INTEGER;
    recommendations_table_exists BOOLEAN;
BEGIN
    SELECT COUNT(*) INTO activities_count FROM activities;
    SELECT COUNT(*) INTO journal_count FROM journal_entries;
    SELECT COUNT(*) INTO autopsies_count FROM ai_autopsies;

    -- Check if llm_recommendations table exists
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = 'llm_recommendations'
    ) INTO recommendations_table_exists;

    RAISE NOTICE 'MIGRATION COMPLETED SUCCESSFULLY:';
    RAISE NOTICE '  activities: % records (converted TEXT → DATE)', activities_count;
    RAISE NOTICE '  journal_entries: % records (already DATE)', journal_count;
    RAISE NOTICE '  ai_autopsies: % records (already DATE)', autopsies_count;
    RAISE NOTICE '  llm_recommendations: table exists = %', recommendations_table_exists;
    RAISE NOTICE 'All tables now use DATE format consistently for date columns';
END $;

COMMIT;