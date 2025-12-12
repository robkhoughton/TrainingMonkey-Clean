-- ============================================================================
-- Rowing Support - Database Schema Update
-- ============================================================================
-- PROJECT RULE: Schema changes via SQL Editor ONLY (never in code)
-- DATABASE: PostgreSQL (use %s placeholders, SERIAL PRIMARY KEY, NOW())
-- CONNECTION: Load from .env file via db_credentials_loader (never hardcode credentials)
-- ============================================================================

-- Step 1: Add rowing_equivalent_miles column
-- This stores the running-equivalent miles for rowing activities
-- Conversion: 1 rowing mile = 1.5 running miles (indoor/erg)
-- Conversion: 1 rowing mile = 1.7 running miles (on-water)
-- NULL for non-rowing activities (safe default)

ALTER TABLE activities
ADD COLUMN IF NOT EXISTS rowing_equivalent_miles REAL;

-- Step 2: Add comment for documentation
COMMENT ON COLUMN activities.rowing_equivalent_miles IS
'Running-equivalent miles for rowing activities using 1.5:1 conversion ratio for indoor/ergometer (1 mile row ≈ 1.5 miles run) and 1.7:1 for on-water rowing. NULL for non-rowing activities.';

-- Step 3: Verify column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'activities'
AND column_name = 'rowing_equivalent_miles';

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

-- Step 6: Check for any existing rowing activities (if Strava already logged them)
SELECT
    activity_id,
    date,
    name,
    type,
    sport_type,
    distance_miles,
    total_load_miles
FROM activities
WHERE type ILIKE '%row%' OR type ILIKE '%erg%'
ORDER BY date DESC
LIMIT 20;

-- Step 7: Test INSERT with rowing data (dry run)
-- This verifies the schema supports the new column
-- (Uncomment to test, but don't actually insert test data)
/*
INSERT INTO activities (
    activity_id, user_id, date, name, type, sport_type,
    distance_miles, total_load_miles, rowing_equivalent_miles,
    trimp, duration_minutes
) VALUES (
    -999999, 1, '2025-01-01', 'Test Row', 'Rowing', 'rowing',
    5.0, 7.5, 7.5,
    0, 45
);

-- Clean up test data
DELETE FROM activities WHERE activity_id = -999999;
*/

-- ============================================================================
-- DEPLOYMENT CHECKLIST
-- ============================================================================
-- [ ] 1. Review this SQL file
-- [ ] 2. Connect to PostgreSQL using credentials from .env file (via db_credentials_loader)
-- [ ] 3. Run the ALTER TABLE command
-- [ ] 4. Verify column exists (Step 3 query)
-- [ ] 5. Check sport_type distribution (Step 4 query)
-- [ ] 6. Review NULL sport_types (Step 5 query)
-- [ ] 7. Check for existing rowing activities (Step 6 query)
-- [ ] 8. Proceed to backend code changes ONLY after column verified

-- ============================================================================
-- Expected Results:
-- ============================================================================
-- Step 3: Should show:
--   column_name: rowing_equivalent_miles
--   data_type: real
--   is_nullable: YES
--   column_default: NULL
--
-- Step 4 & 5: Will show current sport_type distribution
--   This helps decide if backfill script is needed
--
-- Step 6: Will show any rowing activities already in database
--   These will need to be recalculated after deployment
--
-- ============================================================================
-- TECHNICAL JUSTIFICATION FOR CONVERSION FACTORS:
-- ============================================================================
--
-- Rowing 1.5:1 (Indoor/Ergometer) Rationale:
-- - METs: Rowing 7.0-8.5 vs Running 9.8-11.0 (moderate intensity)
-- - Caloric expenditure: ~130-150 cal/mile rowing vs 100-110 cal/mile running
-- - Industry consensus: 1000m rowing ≈ 1 mile running (CrossFit/rowing community)
-- - Full-body recruitment: 86% of muscles vs 70% for running
-- - Result: Higher training load per mile than running
--
-- Rowing 1.7:1 (On-Water) Rationale:
-- - 13% increase over indoor rowing due to:
--   * Wind and current resistance
--   * Boat stability challenges
--   * Less controlled environment
-- - Similar to open water swimming adjustment (5% increase)
--
-- Comparison to other sports:
-- - Cycling: 2.4-4.0:1 (divide) - lower energy per mile
-- - Swimming: 4.0-4.2:1 (multiply) - higher energy per mile
-- - Rowing: 1.5-1.7:1 (multiply) - moderate-high energy per mile
-- ============================================================================
