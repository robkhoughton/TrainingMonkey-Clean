-- HR Stream Data Analysis Queries
-- Use these in your SQL Editor to analyze HR stream data

-- ==============================================
-- 1. OVERVIEW: Activities with HR Stream Data
-- ==============================================
SELECT 
    COUNT(*) as total_activities,
    COUNT(CASE WHEN h.activity_id IS NOT NULL THEN 1 END) as activities_with_hr_stream,
    COUNT(CASE WHEN h.activity_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*) as percentage_with_hr_stream
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.date >= CURRENT_DATE - INTERVAL '30 days'
AND a.trimp > 0;

-- ==============================================
-- 2. DETAILED: Recent Activities with HR Stream Status
-- ==============================================
SELECT 
    a.activity_id,
    a.name,
    a.date,
    a.duration_minutes,
    a.avg_heart_rate,
    a.trimp,
    a.trimp_calculation_method,
    a.hr_stream_sample_count,
    CASE 
        WHEN h.activity_id IS NOT NULL THEN 'YES'
        ELSE 'NO'
    END as has_hr_stream_data,
    CASE 
        WHEN h.hr_data IS NOT NULL THEN jsonb_array_length(h.hr_data)
        ELSE 0
    END as hr_data_length,
    h.sample_rate
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.date >= CURRENT_DATE - INTERVAL '30 days'
AND a.trimp > 0
ORDER BY a.date DESC
LIMIT 20;

-- ==============================================
-- 3. PROBLEM: Activities Claiming HR Stream but Missing Data
-- ==============================================
SELECT 
    a.activity_id,
    a.name,
    a.date,
    a.hr_stream_sample_count,
    a.trimp_calculation_method,
    CASE 
        WHEN h.activity_id IS NULL THEN 'MISSING HR STREAM DATA'
        WHEN h.hr_data IS NULL THEN 'HR STREAM DATA IS NULL'
        WHEN jsonb_array_length(h.hr_data) = 0 THEN 'HR STREAM DATA IS EMPTY'
        ELSE 'HR STREAM DATA EXISTS'
    END as hr_stream_status
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.hr_stream_sample_count > 0
AND a.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY a.date DESC;

-- ==============================================
-- 4. HR STREAM DATA QUALITY ANALYSIS
-- ==============================================
SELECT 
    'Total HR Stream Records' as metric,
    COUNT(*) as count
FROM hr_streams
UNION ALL
SELECT 
    'HR Stream Records with Data' as metric,
    COUNT(*) as count
FROM hr_streams 
WHERE hr_data IS NOT NULL AND jsonb_array_length(hr_data) > 0
UNION ALL
SELECT 
    'HR Stream Records with NULL Data' as metric,
    COUNT(*) as count
FROM hr_streams 
WHERE hr_data IS NULL
UNION ALL
SELECT 
    'HR Stream Records with Empty Data' as metric,
    COUNT(*) as count
FROM hr_streams 
WHERE hr_data = '[]'::jsonb OR jsonb_array_length(hr_data) = 0;

-- ==============================================
-- 5. SAMPLE HR STREAM DATA INSPECTION
-- ==============================================
SELECT 
    h.activity_id,
    a.name,
    a.date,
    h.sample_rate,
    jsonb_array_length(h.hr_data) as data_length,
    h.hr_data->0 as first_sample,
    h.hr_data->1 as second_sample
FROM hr_streams h
JOIN activities a ON h.activity_id = a.activity_id
WHERE h.hr_data IS NOT NULL 
AND jsonb_array_length(h.hr_data) > 0
ORDER BY a.date DESC
LIMIT 5;

-- ==============================================
-- 6. TRIMP CALCULATION METHOD DISTRIBUTION
-- ==============================================
SELECT 
    trimp_calculation_method,
    COUNT(*) as activity_count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM activities 
WHERE date >= CURRENT_DATE - INTERVAL '30 days'
AND trimp > 0
GROUP BY trimp_calculation_method
ORDER BY activity_count DESC;

-- ==============================================
-- 7. ACTIVITIES WITH LARGE HR STREAM SAMPLE COUNTS
-- ==============================================
SELECT 
    a.activity_id,
    a.name,
    a.date,
    a.duration_minutes,
    a.hr_stream_sample_count,
    a.trimp_calculation_method,
    CASE 
        WHEN h.activity_id IS NOT NULL THEN 'YES'
        ELSE 'NO'
    END as has_hr_stream_data
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.hr_stream_sample_count > 1000
AND a.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY a.hr_stream_sample_count DESC;

-- ==============================================
-- 8. SPECIFIC ACTIVITY FROM SCREENSHOT ANALYSIS
-- ==============================================
SELECT 
    a.activity_id,
    a.name,
    a.date,
    a.duration_minutes,
    a.avg_heart_rate,
    a.trimp,
    a.trimp_calculation_method,
    a.hr_stream_sample_count,
    h.activity_id as hr_stream_exists,
    h.sample_rate,
    CASE 
        WHEN h.hr_data IS NOT NULL THEN jsonb_array_length(h.hr_data)
        ELSE 0
    END as hr_data_length
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.activity_id = 15767717105;

-- ==============================================
-- 9. ACTIVITIES THAT SHOULD SHOW TRIMP DIFFERENCES
-- ==============================================
SELECT 
    a.activity_id,
    a.name,
    a.date,
    a.duration_minutes,
    a.avg_heart_rate,
    a.trimp,
    a.hr_stream_sample_count,
    CASE 
        WHEN h.activity_id IS NOT NULL AND h.hr_data IS NOT NULL AND jsonb_array_length(h.hr_data) > 0 THEN 'READY FOR COMPARISON'
        ELSE 'CANNOT COMPARE - NO HR STREAM DATA'
    END as comparison_status
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.hr_stream_sample_count > 500
AND a.date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY a.hr_stream_sample_count DESC;

-- ==============================================
-- 10. SUMMARY FOR TRIMP COMPARISON TESTING
-- ==============================================
SELECT 
    'Activities Ready for TRIMP Comparison' as category,
    COUNT(*) as count
FROM activities a
JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.date >= CURRENT_DATE - INTERVAL '30 days'
AND a.trimp > 0
AND h.hr_data IS NOT NULL 
AND jsonb_array_length(h.hr_data) > 0
AND a.hr_stream_sample_count > 100
UNION ALL
SELECT 
    'Activities with Missing HR Stream Data' as category,
    COUNT(*) as count
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.date >= CURRENT_DATE - INTERVAL '30 days'
AND a.trimp > 0
AND a.hr_stream_sample_count > 0
AND (h.activity_id IS NULL OR h.hr_data IS NULL OR jsonb_array_length(h.hr_data) = 0);
