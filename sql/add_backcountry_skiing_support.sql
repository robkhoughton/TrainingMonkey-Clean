-- ============================================================================
-- Backcountry Skiing Support - Database Schema Update
-- ============================================================================
-- PROJECT RULE: Schema changes via SQL Editor ONLY (never in code)
-- DATABASE: PostgreSQL (use %s placeholders, SERIAL PRIMARY KEY, NOW())
-- CONNECTION: postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d
-- ============================================================================

-- Step 1: Add backcountry_skiing_equivalent_miles column
-- This stores the running-equivalent miles for backcountry skiing activities
-- Conversion: Base distance × 1.2 + (ascent_feet / 500)
-- NULL for non-backcountry skiing activities (safe default)

ALTER TABLE activities
ADD COLUMN IF NOT EXISTS backcountry_skiing_equivalent_miles REAL;

-- Step 2: Add comment for documentation
COMMENT ON COLUMN activities.backcountry_skiing_equivalent_miles IS
'Running-equivalent miles for backcountry skiing activities. Formula: (distance × 1.2) + (ascent / 500). Base factor accounts for equipment/snow, ascent factor accounts for skinning uphill (harder than running). NULL for non-backcountry skiing activities.';

-- Step 3: Verify column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'activities'
AND column_name = 'backcountry_skiing_equivalent_miles';

-- Step 4: Check current sport_type distribution
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

-- Step 6: Check for any existing backcountry skiing activities
SELECT
    activity_id,
    date,
    name,
    type,
    sport_type,
    distance_miles,
    elevation_gain_feet,
    total_load_miles
FROM activities
WHERE type ILIKE '%ski%' OR type ILIKE '%touring%' OR type ILIKE '%backcountry%'
ORDER BY date DESC
LIMIT 20;

-- Step 7: Test INSERT with backcountry skiing data (dry run)
-- This verifies the schema supports the new column
-- (Uncomment to test, but don't actually insert test data)
/*
INSERT INTO activities (
    activity_id, user_id, date, name, type, sport_type,
    distance_miles, elevation_gain_feet, total_load_miles, backcountry_skiing_equivalent_miles,
    trimp, duration_minutes
) VALUES (
    -999999, 1, '2025-01-01', 'Test Alpine Tour', 'Backcountry Ski', 'backcountry_skiing',
    5.0, 3000, 12.0, 12.0,
    0, 180
);

-- Clean up test data
DELETE FROM activities WHERE activity_id = -999999;
*/

-- ============================================================================
-- DEPLOYMENT CHECKLIST
-- ============================================================================
-- [ ] 1. Review this SQL file
-- [ ] 2. Connect to PostgreSQL: postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d
-- [ ] 3. Run the ALTER TABLE command
-- [ ] 4. Verify column exists (Step 3 query)
-- [ ] 5. Check sport_type distribution (Step 4 query)
-- [ ] 6. Review NULL sport_types (Step 5 query)
-- [ ] 7. Check for existing backcountry skiing activities (Step 6 query)
-- [ ] 8. Proceed to backend code changes ONLY after column verified

-- ============================================================================
-- Expected Results:
-- ============================================================================
-- Step 3: Should show:
--   column_name: backcountry_skiing_equivalent_miles
--   data_type: real
--   is_nullable: YES
--   column_default: NULL
--
-- Step 4 & 5: Will show current sport_type distribution
--   This helps decide if backfill script is needed
--
-- Step 6: Will show any backcountry skiing activities already in database
--   These will need to be recalculated after deployment
--
-- ============================================================================
-- TECHNICAL JUSTIFICATION FOR CONVERSION FORMULA:
-- ============================================================================
--
-- Backcountry Skiing Conversion: (distance × 1.2) + (ascent / 500)
--
-- Base Distance Factor (1.2x):
-- - Skinning with skis, boots, and pack is harder than running on flat
-- - Snow resistance and equipment weight increase effort
-- - ~20% harder than running equivalent distance
--
-- Ascent Factor (500 ft/mile):
-- - Skinning uphill significantly harder than running uphill
-- - Running: 750 ft/mile elevation factor
-- - Backcountry skiing: 500 ft/mile (50% more credit for ascent)
-- - Accounts for equipment weight and snow conditions
--
-- Alpine Touring Characteristics:
-- - METs: 8-12 (high intensity)
-- - Full-body workout with equipment
-- - Typical ascent ratio: 1000-1500 ft/mile
-- - Descent is momentum-assisted (already in base distance)
--
-- Example Calculation:
-- - Activity: 5 miles, 3000 ft ascent
-- - Base: 5 × 1.2 = 6.0 miles
-- - Ascent: 3000 / 500 = 6.0 miles
-- - Total: 12.0 miles running equivalent
--
-- Comparison to other sports:
-- - Running: distance + (ascent / 750)
-- - Cycling: (distance / 2.4-4.0) + (ascent / 1100)
-- - Swimming: distance × 4.0-4.2
-- - Rowing: distance × 1.5-1.7
-- - Backcountry Skiing: (distance × 1.2) + (ascent / 500)
--
-- Pattern: Similar to running (distance + ascent surcharge)
-- Simpler than cycling (no speed-based factors)
-- Appropriate for alpine touring with discrete ascent/descent tracking
-- ============================================================================
