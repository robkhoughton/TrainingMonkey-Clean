-- ============================================================================
-- YTM Coach Page Database Schema Migration
-- Created: 2025-11-14
-- Description: Creates tables for race goals, race history, and weekly training programs
--              Adds training schedule fields to user_settings
-- ============================================================================

-- IMPORTANT: This uses PostgreSQL syntax
-- - Use %s for parameterized queries (NOT ?)
-- - Use SERIAL PRIMARY KEY (NOT AUTOINCREMENT)
-- - Use NOW() (NOT CURRENT_TIMESTAMP)
-- - Execute this script manually in SQL Editor (per project rules)

-- ============================================================================
-- TABLE: race_goals
-- Purpose: Store user's race goals with A/B/C priority system
-- ============================================================================
CREATE TABLE IF NOT EXISTS race_goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    race_name VARCHAR(200) NOT NULL,
    race_date DATE NOT NULL,
    race_type VARCHAR(100),
    priority CHAR(1) NOT NULL CHECK (priority IN ('A', 'B', 'C')),
    target_time VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key to user_settings
    CONSTRAINT fk_race_goals_user 
        FOREIGN KEY (user_id) 
        REFERENCES user_settings(id) 
        ON DELETE CASCADE
);

-- Index for efficient user-based queries sorted by date
CREATE INDEX IF NOT EXISTS idx_race_goals_user_date 
    ON race_goals(user_id, race_date);

-- Index for priority filtering (find A races quickly)
CREATE INDEX IF NOT EXISTS idx_race_goals_priority 
    ON race_goals(user_id, priority);

COMMENT ON TABLE race_goals IS 'User race goals with A/B/C priority system';
COMMENT ON COLUMN race_goals.priority IS 'A = Primary goal race, B = Performance evaluation, C = Training volume';

-- ============================================================================
-- TABLE: race_history
-- Purpose: Store user's past race results (last 5 years only)
-- ============================================================================
CREATE TABLE IF NOT EXISTS race_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    race_date DATE NOT NULL,
    race_name VARCHAR(200) NOT NULL,
    distance_miles REAL NOT NULL CHECK (distance_miles > 0),
    finish_time_minutes INTEGER NOT NULL CHECK (finish_time_minutes > 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key to user_settings
    CONSTRAINT fk_race_history_user 
        FOREIGN KEY (user_id) 
        REFERENCES user_settings(id) 
        ON DELETE CASCADE,
    
    -- Enforce 5-year limit
    CONSTRAINT chk_race_history_date_limit 
        CHECK (race_date >= CURRENT_DATE - INTERVAL '5 years')
);

-- Index for chronological queries (most recent first)
CREATE INDEX IF NOT EXISTS idx_race_history_user_date 
    ON race_history(user_id, race_date DESC);

-- Index for PR calculations by distance
CREATE INDEX IF NOT EXISTS idx_race_history_user_distance 
    ON race_history(user_id, distance_miles);

COMMENT ON TABLE race_history IS 'User race results from last 5 years for performance analysis';
COMMENT ON COLUMN race_history.distance_miles IS 'Race distance in miles (not kilometers)';
COMMENT ON COLUMN race_history.finish_time_minutes IS 'Total finish time in minutes';

-- ============================================================================
-- TABLE: weekly_programs
-- Purpose: Cache LLM-generated weekly training programs
-- ============================================================================
CREATE TABLE IF NOT EXISTS weekly_programs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    week_start_date DATE NOT NULL,
    program_json JSONB NOT NULL,
    predicted_acwr REAL,
    predicted_divergence REAL,
    generated_at TIMESTAMP DEFAULT NOW(),
    generation_type VARCHAR(20) DEFAULT 'scheduled' CHECK (generation_type IN ('scheduled', 'manual')),
    
    -- Foreign key to user_settings
    CONSTRAINT fk_weekly_programs_user 
        FOREIGN KEY (user_id) 
        REFERENCES user_settings(id) 
        ON DELETE CASCADE,
    
    -- Ensure only one program per user per week
    CONSTRAINT uq_weekly_programs_user_week 
        UNIQUE (user_id, week_start_date)
);

-- Index for fetching current/recent programs
CREATE INDEX IF NOT EXISTS idx_weekly_programs_user_week 
    ON weekly_programs(user_id, week_start_date DESC);

-- Index for cleanup queries (delete old programs)
CREATE INDEX IF NOT EXISTS idx_weekly_programs_generated_at 
    ON weekly_programs(generated_at);

COMMENT ON TABLE weekly_programs IS 'Cached LLM-generated weekly training programs';
COMMENT ON COLUMN weekly_programs.program_json IS 'Full 7-day program with workouts, rationale, and metrics';
COMMENT ON COLUMN weekly_programs.generation_type IS 'scheduled = cron job, manual = user-triggered';

-- ============================================================================
-- ALTER TABLE: user_settings
-- Purpose: Add training schedule and supplemental training preferences
-- ============================================================================

-- Add training schedule JSON field
ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS training_schedule_json JSONB;

-- Add supplemental training fields
ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS include_strength_training BOOLEAN DEFAULT FALSE;

ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS strength_hours_per_week REAL DEFAULT 0 CHECK (strength_hours_per_week >= 0);

ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS include_mobility BOOLEAN DEFAULT FALSE;

ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS mobility_hours_per_week REAL DEFAULT 0 CHECK (mobility_hours_per_week >= 0);

ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS include_cross_training BOOLEAN DEFAULT FALSE;

ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS cross_training_type VARCHAR(50);

ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS cross_training_hours_per_week REAL DEFAULT 0 CHECK (cross_training_hours_per_week >= 0);

ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS schedule_last_updated TIMESTAMP;

-- Add manual training stage override field
ALTER TABLE user_settings 
    ADD COLUMN IF NOT EXISTS manual_training_stage VARCHAR(20);

COMMENT ON COLUMN user_settings.training_schedule_json IS 'User availability: {available_days: [], time_blocks: {}, constraints: []}';
COMMENT ON COLUMN user_settings.manual_training_stage IS 'User can manually override calculated training stage';

-- ============================================================================
-- ROLLBACK SCRIPT (for reference - do not execute unless reverting)
-- ============================================================================
/*
-- Drop tables in reverse order (respecting foreign keys)
DROP TABLE IF EXISTS weekly_programs CASCADE;
DROP TABLE IF EXISTS race_history CASCADE;
DROP TABLE IF EXISTS race_goals CASCADE;

-- Remove added columns from user_settings
ALTER TABLE user_settings DROP COLUMN IF EXISTS training_schedule_json;
ALTER TABLE user_settings DROP COLUMN IF EXISTS include_strength_training;
ALTER TABLE user_settings DROP COLUMN IF EXISTS strength_hours_per_week;
ALTER TABLE user_settings DROP COLUMN IF EXISTS include_mobility;
ALTER TABLE user_settings DROP COLUMN IF EXISTS mobility_hours_per_week;
ALTER TABLE user_settings DROP COLUMN IF EXISTS include_cross_training;
ALTER TABLE user_settings DROP COLUMN IF EXISTS cross_training_type;
ALTER TABLE user_settings DROP COLUMN IF EXISTS cross_training_hours_per_week;
ALTER TABLE user_settings DROP COLUMN IF EXISTS schedule_last_updated;
ALTER TABLE user_settings DROP COLUMN IF EXISTS manual_training_stage;
*/

-- ============================================================================
-- VERIFICATION QUERIES (run after migration to verify success)
-- ============================================================================
/*
-- Check that tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('race_goals', 'race_history', 'weekly_programs');

-- Check indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('race_goals', 'race_history', 'weekly_programs');

-- Check new user_settings columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'user_settings'
  AND column_name LIKE '%training%' OR column_name LIKE '%strength%' 
  OR column_name LIKE '%mobility%' OR column_name LIKE '%cross_training%';

-- Test constraints (should fail with proper error)
-- INSERT INTO race_goals (user_id, race_name, race_date, priority) 
-- VALUES (1, 'Test', '2025-01-01', 'X');  -- Should fail: invalid priority

-- INSERT INTO race_history (user_id, race_name, race_date, distance_miles, finish_time_minutes)
-- VALUES (1, 'Old Race', '2019-01-01', 26.2, 240);  -- Should fail: too old
*/

-- ============================================================================
-- END OF MIGRATION SCRIPT
-- ============================================================================

