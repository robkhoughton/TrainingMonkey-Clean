-- Final Database Cleanup Script
-- Run this AFTER data migration and code updates are complete

-- ============================================================================
-- IMPORTANT: Only run this after:
-- 1. Running the analysis script
-- 2. Migrating data (if needed)
-- 3. Updating all code references
-- 4. Testing the application
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. FINAL VERIFICATION
-- ============================================================================

-- Verify that acwr_enhanced_calculations has all the data we need
SELECT 
    'Final Data Check' as status,
    COUNT(*) as total_records,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT configuration_id) as unique_configurations,
    MIN(calculation_date) as earliest_calculation,
    MAX(calculation_date) as latest_calculation
FROM acwr_enhanced_calculations;

-- Check that enhanced_acwr_calculations is no longer needed
SELECT 
    'Enhanced Table Check' as status,
    COUNT(*) as remaining_records
FROM enhanced_acwr_calculations;

-- ============================================================================
-- 2. DROP REDUNDANT TABLE
-- ============================================================================

-- Drop the redundant enhanced_acwr_calculations table
DROP TABLE IF EXISTS enhanced_acwr_calculations;

-- ============================================================================
-- 3. CLEAN UP BACKUP TABLE (if it exists)
-- ============================================================================

-- Drop the backup table if it was created during migration
DROP TABLE IF EXISTS enhanced_acwr_calculations_backup;

-- ============================================================================
-- 4. VERIFY CLEANUP
-- ============================================================================

-- Verify that only the correct table remains
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE '%acwr%enhanced%calculations%'
ORDER BY table_name;

-- ============================================================================
-- 5. UPDATE TABLE STATISTICS
-- ============================================================================

-- Update table statistics for better query performance
ANALYZE acwr_enhanced_calculations;

COMMIT;

-- ============================================================================
-- 6. FINAL VERIFICATION QUERIES
-- ============================================================================

-- These queries should work after cleanup:
-- SELECT COUNT(*) FROM acwr_enhanced_calculations;
-- SELECT * FROM acwr_enhanced_calculations LIMIT 5;

-- These queries should fail (table no longer exists):
-- SELECT COUNT(*) FROM enhanced_acwr_calculations;  -- Should fail
-- SELECT COUNT(*) FROM enhanced_acwr_calculations_backup;  -- Should fail
