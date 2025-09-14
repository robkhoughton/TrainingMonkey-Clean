-- Database Verification Queries for Goals Setup Implementation
-- Run these queries in your SQL Editor to verify the changes

-- =====================================================
-- 1. VERIFY GOALS COLUMNS IN user_settings TABLE
-- =====================================================

-- Check if goals columns exist and their properties
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    CASE 
        WHEN column_name IN ('goals_configured', 'goal_type', 'goal_target', 'goal_timeframe', 'goals_setup_date') 
        THEN '✅ REQUIRED' 
        ELSE 'ℹ️ OTHER' 
    END as status
FROM information_schema.columns 
WHERE table_name = 'user_settings' 
AND column_name IN ('goals_configured', 'goal_type', 'goal_target', 'goal_timeframe', 'goals_setup_date')
ORDER BY column_name;

-- Count total columns in user_settings table
SELECT 
    COUNT(*) as total_columns,
    COUNT(CASE WHEN column_name IN ('goals_configured', 'goal_type', 'goal_target', 'goal_timeframe', 'goals_setup_date') THEN 1 END) as goals_columns_count
FROM information_schema.columns 
WHERE table_name = 'user_settings';

-- =====================================================
-- 2. VERIFY onboarding_analytics TABLE
-- =====================================================

-- Check if onboarding_analytics table exists
SELECT 
    table_name,
    table_type,
    CASE 
        WHEN table_name = 'onboarding_analytics' THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END as status
FROM information_schema.tables 
WHERE table_name = 'onboarding_analytics';

-- Check onboarding_analytics table structure
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default,
    CASE 
        WHEN column_name IN ('id', 'user_id', 'event_name', 'event_data', 'timestamp') 
        THEN '✅ REQUIRED' 
        ELSE 'ℹ️ OTHER' 
    END as status
FROM information_schema.columns 
WHERE table_name = 'onboarding_analytics'
ORDER BY ordinal_position;

-- Check foreign key constraint
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    CASE 
        WHEN tc.constraint_type = 'FOREIGN KEY' THEN '✅ FOREIGN KEY'
        ELSE 'ℹ️ OTHER'
    END as constraint_type
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
AND tc.table_name = 'onboarding_analytics';

-- =====================================================
-- 3. VERIFY INDEXES
-- =====================================================

-- Check if analytics index exists
SELECT 
    indexname,
    tablename,
    indexdef,
    CASE 
        WHEN indexname = 'idx_onboarding_analytics_user_timestamp' THEN '✅ EXISTS'
        ELSE 'ℹ️ OTHER'
    END as status
FROM pg_indexes 
WHERE tablename = 'onboarding_analytics'
AND indexname = 'idx_onboarding_analytics_user_timestamp';

-- =====================================================
-- 4. TEST DATA INSERTION (Optional)
-- =====================================================

-- Test inserting a sample goal (run this only if you want to test)
-- INSERT INTO user_settings (user_id, goals_configured, goal_type, goal_target, goal_timeframe, goals_setup_date)
-- VALUES (1, TRUE, 'distance', '50', '1_month', NOW())
-- ON CONFLICT (user_id) DO UPDATE SET
--     goals_configured = EXCLUDED.goals_configured,
--     goal_type = EXCLUDED.goal_type,
--     goal_target = EXCLUDED.goal_target,
--     goal_timeframe = EXCLUDED.goal_timeframe,
--     goals_setup_date = EXCLUDED.goals_setup_date;

-- Test inserting analytics event (run this only if you want to test)
-- INSERT INTO onboarding_analytics (user_id, event_name, event_data)
-- VALUES (1, 'goals_setup_completed', '{"goal_type": "distance", "timeframe": "1_month"}');

-- =====================================================
-- 5. SUMMARY REPORT
-- =====================================================

-- Generate a summary report
WITH goals_columns_check AS (
    SELECT COUNT(*) as goals_columns_found
    FROM information_schema.columns 
    WHERE table_name = 'user_settings' 
    AND column_name IN ('goals_configured', 'goal_type', 'goal_target', 'goal_timeframe', 'goals_setup_date')
),
analytics_table_check AS (
    SELECT COUNT(*) as analytics_table_found
    FROM information_schema.tables 
    WHERE table_name = 'onboarding_analytics'
),
analytics_columns_check AS (
    SELECT COUNT(*) as analytics_columns_found
    FROM information_schema.columns 
    WHERE table_name = 'onboarding_analytics'
    AND column_name IN ('id', 'user_id', 'event_name', 'event_data', 'timestamp')
),
index_check AS (
    SELECT COUNT(*) as index_found
    FROM pg_indexes 
    WHERE tablename = 'onboarding_analytics'
    AND indexname = 'idx_onboarding_analytics_user_timestamp'
)
SELECT 
    'DATABASE VERIFICATION SUMMARY' as report_type,
    CASE 
        WHEN g.goals_columns_found = 5 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as goals_columns_status,
    CASE 
        WHEN a.analytics_table_found = 1 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as analytics_table_status,
    CASE 
        WHEN ac.analytics_columns_found = 5 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as analytics_columns_status,
    CASE 
        WHEN i.index_found = 1 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END as index_status,
    CASE 
        WHEN g.goals_columns_found = 5 
         AND a.analytics_table_found = 1 
         AND ac.analytics_columns_found = 5 
         AND i.index_found = 1 
        THEN '🎉 ALL CHECKS PASSED - READY FOR DEPLOYMENT'
        ELSE '⚠️ SOME CHECKS FAILED - REVIEW REQUIRED'
    END as overall_status
FROM goals_columns_check g
CROSS JOIN analytics_table_check a
CROSS JOIN analytics_columns_check ac
CROSS JOIN index_check i;

