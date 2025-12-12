-- ============================================================================
-- Swimming Support - Database Schema Update
-- ============================================================================
-- PROJECT RULE: Schema changes via SQL Editor ONLY (never in code)
-- DATABASE: PostgreSQL (use %s placeholders, SERIAL PRIMARY KEY, NOW())
-- CONNECTION: postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d
-- ============================================================================

-- Step 1: Add swimming_equivalent_miles column
-- This stores the running-equivalent miles for swimming activities (1 swim mi = 4 run mi)
-- NULL for non-swimming activities (safe default)

ALTER TABLE activities 
ADD COLUMN IF NOT EXISTS swimming_equivalent_miles REAL;

-- Step 2: Add comment for documentation
COMMENT ON COLUMN activities.swimming_equivalent_miles IS 
'Running-equivalent miles for swimming activities using 4:1 conversion ratio (1 mile swim ≈ 4 miles run). NULL for non-swimming activities.';

-- Step 3: Verify column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'activities' 
AND column_name = 'swimming_equivalent_miles';

-- Step 4: Check current sport_type distribution (important for backfill decision)
SELECT 
    sport_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM activities
WHERE activity_id > 0  -- Exclude rest days
GROUP BY sport_type
ORDER BY count DESC;

-- Step 5: Count activities with NULL sport_type (need backfill?)
SELECT 
    CASE 
        WHEN sport_type IS NULL THEN 'NULL (needs backfill)'
        ELSE sport_type 
    END as sport_type_status,
    COUNT(*) as count
FROM activities
WHERE activity_id > 0
GROUP BY sport_type
ORDER BY count DESC;

-- Step 6: Test INSERT with swimming data (dry run)
-- This verifies the schema supports the new column
-- (Uncomment to test, but don't actually insert test data)
/*
INSERT INTO activities (
    activity_id, user_id, date, name, type, sport_type,
    distance_miles, total_load_miles, swimming_equivalent_miles,
    trimp, duration_minutes
) VALUES (
    -999999, 1, '2025-01-01', 'Test Swim', 'Pool Swim', 'swimming',
    1.0, 4.0, 4.0,
    0, 30
);

-- Clean up test data
DELETE FROM activities WHERE activity_id = -999999;
*/

-- ============================================================================
-- DEPLOYMENT CHECKLIST
-- ============================================================================
-- [X] 1. Review this SQL file
-- [ ] 2. Connect to PostgreSQL: postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d
-- [ ] 3. Run the ALTER TABLE command
-- [ ] 4. Verify column exists (Step 3 query)
-- [ ] 5. Check sport_type distribution (Step 4 query)
-- [ ] 6. Review NULL sport_types (Step 5 query)
-- [ ] 7. Proceed to backend code changes ONLY after column verified

-- ============================================================================
-- Expected Results:
-- ============================================================================
-- Step 3: Should show:
--   column_name: swimming_equivalent_miles
--   data_type: real
--   is_nullable: YES
--   column_default: NULL
--
-- Step 4 & 5: Will show current sport_type distribution
--   This helps decide if backfill script is needed
--
-- ============================================================================

