-- Quick HR Stream Data Check (Fixed for JSONB)
-- Run this first to get a quick overview

-- 1. Quick Overview
SELECT 
    'Total Recent Activities' as metric,
    COUNT(*) as count
FROM activities 
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
AND trimp > 0

UNION ALL

SELECT 
    'Activities with HR Stream Data' as metric,
    COUNT(*) as count
FROM activities a
JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.date >= CURRENT_DATE - INTERVAL '7 days'
AND a.trimp > 0
AND h.hr_data IS NOT NULL 
AND jsonb_array_length(h.hr_data) > 0;

-- 2. Activities from Last 7 Days with HR Stream Status
SELECT 
    a.activity_id,
    a.name,
    a.date,
    a.duration_minutes,
    a.avg_heart_rate,
    a.trimp,
    a.hr_stream_sample_count,
    CASE 
        WHEN h.activity_id IS NOT NULL AND h.hr_data IS NOT NULL AND jsonb_array_length(h.hr_data) > 0 THEN '✅ HAS HR STREAM'
        WHEN a.hr_stream_sample_count > 0 THEN '⚠️ CLAIMS HR STREAM BUT MISSING DATA'
        ELSE '❌ NO HR STREAM'
    END as hr_stream_status,
    CASE 
        WHEN h.hr_data IS NOT NULL THEN jsonb_array_length(h.hr_data)
        ELSE 0
    END as actual_hr_samples
FROM activities a
LEFT JOIN hr_streams h ON a.activity_id = h.activity_id
WHERE a.date >= CURRENT_DATE - INTERVAL '7 days'
AND a.trimp > 0
ORDER BY a.date DESC;
