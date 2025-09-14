-- Quick Database Cleanup Status Check
-- Run this to quickly see the current state

-- Check which tables exist
SELECT 'Tables Status' as check_type, table_name, 'EXISTS' as status
FROM information_schema.tables 
WHERE table_name IN ('acwr_enhanced_calculations', 'enhanced_acwr_calculations')
ORDER BY table_name;

-- Check record counts
SELECT 'Record Counts' as check_type, 
       'acwr_enhanced_calculations' as table_name, 
       COUNT(*) as record_count
FROM acwr_enhanced_calculations
UNION ALL
SELECT 'Record Counts' as check_type,
       'enhanced_acwr_calculations' as table_name,
       COUNT(*) as record_count
FROM enhanced_acwr_calculations
ORDER BY table_name;

-- Check if cleanup is needed
SELECT 
    CASE 
        WHEN (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'enhanced_acwr_calculations') > 0 
        THEN 'CLEANUP NEEDED - enhanced_acwr_calculations still exists'
        ELSE 'CLEANUP COMPLETE - Only acwr_enhanced_calculations exists'
    END as cleanup_status;
