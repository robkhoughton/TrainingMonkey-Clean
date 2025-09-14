-- Data Migration Script: enhanced_acwr_calculations -> acwr_enhanced_calculations
-- Run this ONLY if enhanced_acwr_calculations has data that needs to be preserved

-- ============================================================================
-- IMPORTANT: Run the analysis script first to check if this migration is needed
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. BACKUP EXISTING DATA (Safety measure)
-- ============================================================================

-- Create backup table for enhanced_acwr_calculations
CREATE TABLE IF NOT EXISTS enhanced_acwr_calculations_backup AS 
SELECT * FROM enhanced_acwr_calculations;

-- ============================================================================
-- 2. DATA MIGRATION
-- ============================================================================

-- Insert data from enhanced_acwr_calculations into acwr_enhanced_calculations
-- Note: This requires mapping activity_date to activity_id
INSERT INTO acwr_enhanced_calculations (
    user_id,
    activity_id,
    configuration_id,
    acwr_ratio,
    acute_load,
    chronic_load,
    calculation_method,
    created_at,
    updated_at
)
SELECT 
    eac.user_id,
    a.activity_id,  -- Map activity_date to activity_id
    eac.configuration_id,
    eac.enhanced_acute_chronic_ratio as acwr_ratio,
    eac.enhanced_chronic_load as acute_load,
    eac.enhanced_chronic_trimp as chronic_load,
    'migrated' as calculation_method,
    eac.calculation_timestamp as created_at,
    eac.calculation_timestamp as updated_at
FROM enhanced_acwr_calculations eac
JOIN activities a ON (
    a.user_id = eac.user_id 
    AND a.date = eac.activity_date
)
WHERE NOT EXISTS (
    -- Avoid duplicates: don't insert if record already exists
    SELECT 1 FROM acwr_enhanced_calculations aec
    WHERE aec.user_id = eac.user_id
    AND aec.activity_id = a.activity_id
    AND aec.configuration_id = eac.configuration_id
);

-- ============================================================================
-- 3. VERIFICATION
-- ============================================================================

-- Check migration results
SELECT 
    'Migration Results' as status,
    COUNT(*) as migrated_records
FROM acwr_enhanced_calculations 
WHERE calculation_method = 'migrated';

-- Check for any failed migrations (records that couldn't be mapped)
SELECT 
    'Failed Migrations' as status,
    COUNT(*) as failed_records
FROM enhanced_acwr_calculations eac
LEFT JOIN activities a ON (
    a.user_id = eac.user_id 
    AND a.date = eac.activity_date
)
WHERE a.activity_id IS NULL;

-- ============================================================================
-- 4. ROLLBACK INSTRUCTIONS (if needed)
-- ============================================================================

-- If something goes wrong, you can rollback with:
-- DELETE FROM acwr_enhanced_calculations WHERE calculation_method = 'migrated';
-- DROP TABLE enhanced_acwr_calculations_backup;

COMMIT;

-- ============================================================================
-- 5. POST-MIGRATION CLEANUP (run after verification)
-- ============================================================================

-- After verifying the migration was successful, you can:
-- 1. Drop the backup table: DROP TABLE enhanced_acwr_calculations_backup;
-- 2. Drop the original table: DROP TABLE enhanced_acwr_calculations;
