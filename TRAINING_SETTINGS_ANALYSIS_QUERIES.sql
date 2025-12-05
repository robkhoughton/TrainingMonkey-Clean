-- ==============================================================================
-- TRAINING SETTINGS DATA ANALYSIS QUERIES
-- Run these queries manually to assess current state
-- ==============================================================================

-- QUERY 1: OVERVIEW - Field Population Count
-- Purpose: See how many users have populated each training settings field
-- ==============================================================================

SELECT 
    COUNT(*) as total_users,
    COUNT(primary_sport) as has_primary_sport,
    COUNT(secondary_sport) as has_secondary_sport,
    COUNT(training_experience) as has_experience,
    COUNT(weekly_training_hours) as has_weekly_hours,
    COUNT(current_phase) as has_current_phase,
    COUNT(race_goal_date) as has_legacy_race_date,
    COUNT(training_schedule_json) as has_detailed_schedule,
    COUNT(include_strength_training) as has_strength_config,
    COUNT(include_mobility) as has_mobility_config,
    COUNT(include_cross_training) as has_cross_training_config
FROM user_settings
WHERE email IS NOT NULL;


-- QUERY 2: USERS WITH LEGACY RACE GOAL DATE
-- Purpose: Identify users with the deprecated race_goal_date field
-- ==============================================================================

SELECT 
    id as user_id,
    email,
    race_goal_date,
    current_phase,
    weekly_training_hours,
    primary_sport,
    training_experience,
    (SELECT COUNT(*) FROM race_goals WHERE user_id = user_settings.id) as race_goals_count
FROM user_settings
WHERE race_goal_date IS NOT NULL
ORDER BY race_goal_date ASC;


-- QUERY 3: CONFLICT ANALYSIS - Legacy vs New System
-- Purpose: Categorize users by migration status
-- ==============================================================================

SELECT 
    us.id as user_id,
    us.email,
    us.race_goal_date as legacy_race_date,
    COALESCE(rg.race_count, 0) as new_race_goals_count,
    COALESCE(rg.earliest_race_date, NULL) as new_earliest_race,
    CASE 
        WHEN us.race_goal_date IS NOT NULL AND COALESCE(rg.race_count, 0) > 0 THEN 'CONFLICT'
        WHEN us.race_goal_date IS NOT NULL AND COALESCE(rg.race_count, 0) = 0 THEN 'MIGRATE'
        WHEN us.race_goal_date IS NULL AND COALESCE(rg.race_count, 0) > 0 THEN 'OK'
        ELSE 'EMPTY'
    END as status
FROM user_settings us
LEFT JOIN (
    SELECT user_id, 
           COUNT(*) as race_count,
           MIN(race_date) as earliest_race_date
    FROM race_goals
    GROUP BY user_id
) rg ON us.id = rg.user_id
WHERE us.email IS NOT NULL
ORDER BY status, us.id;


-- QUERY 4: STATUS SUMMARY
-- Purpose: Get counts for each migration status category
-- ==============================================================================

WITH status_data AS (
    SELECT 
        CASE 
            WHEN us.race_goal_date IS NOT NULL AND COALESCE(rg.race_count, 0) > 0 THEN 'CONFLICT'
            WHEN us.race_goal_date IS NOT NULL AND COALESCE(rg.race_count, 0) = 0 THEN 'MIGRATE'
            WHEN us.race_goal_date IS NULL AND COALESCE(rg.race_count, 0) > 0 THEN 'OK'
            ELSE 'EMPTY'
        END as status
    FROM user_settings us
    LEFT JOIN (
        SELECT user_id, COUNT(*) as race_count
        FROM race_goals
        GROUP BY user_id
    ) rg ON us.id = rg.user_id
    WHERE us.email IS NOT NULL
)
SELECT 
    status,
    COUNT(*) as user_count
FROM status_data
GROUP BY status
ORDER BY 
    CASE status
        WHEN 'CONFLICT' THEN 1
        WHEN 'MIGRATE' THEN 2
        WHEN 'OK' THEN 3
        WHEN 'EMPTY' THEN 4
    END;


-- QUERY 5: TRAINING VOLUME COMPARISON
-- Purpose: Compare basic weekly_training_hours vs detailed schedule
-- ==============================================================================

SELECT 
    id as user_id,
    email,
    weekly_training_hours as basic_hours,
    CASE WHEN training_schedule_json IS NOT NULL 
         THEN (training_schedule_json::jsonb->>'total_hours_per_week')::text 
         ELSE NULL 
    END as schedule_hours,
    CASE 
        WHEN training_schedule_json IS NOT NULL AND weekly_training_hours IS NOT NULL 
        THEN 'Both configured'
        WHEN training_schedule_json IS NOT NULL 
        THEN 'Detailed only'
        WHEN weekly_training_hours IS NOT NULL 
        THEN 'Basic only'
        ELSE 'Neither'
    END as training_volume_status
FROM user_settings
WHERE email IS NOT NULL
ORDER BY training_volume_status, user_id;


-- QUERY 6: COACH PAGE FEATURE ADOPTION
-- Purpose: See how many users are using new Coach page features
-- ==============================================================================

SELECT 
    (SELECT COUNT(*) FROM user_settings WHERE email IS NOT NULL) as total_users,
    (SELECT COUNT(DISTINCT user_id) FROM race_goals) as users_with_race_goals,
    (SELECT COUNT(DISTINCT user_id) FROM race_history) as users_with_race_history,
    (SELECT COUNT(*) FROM user_settings WHERE training_schedule_json IS NOT NULL AND email IS NOT NULL) as users_with_detailed_schedule,
    (SELECT COUNT(*) FROM user_settings WHERE include_strength_training = TRUE AND email IS NOT NULL) as users_with_strength,
    (SELECT COUNT(*) FROM user_settings WHERE include_mobility = TRUE AND email IS NOT NULL) as users_with_mobility,
    (SELECT COUNT(*) FROM user_settings WHERE include_cross_training = TRUE AND email IS NOT NULL) as users_with_cross_training;


