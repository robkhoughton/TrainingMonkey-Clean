-- ============================================================================
-- Multi-Discipline Cross-Training Support
-- ============================================================================
-- This migration adds support for multiple cross-training disciplines
-- Users can now enable multiple activities (cycling, swimming, rowing, etc.)
-- with independent allocation settings (hours OR percentage)
-- ============================================================================

-- Create new table for storing multiple cross-training disciplines per user
CREATE TABLE IF NOT EXISTS user_cross_training_disciplines (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    discipline VARCHAR(50) NOT NULL CHECK (discipline IN ('cycling', 'swimming', 'rowing', 'backcountry_skiing', 'hiking', 'other')),
    enabled BOOLEAN DEFAULT TRUE,
    allocation_type VARCHAR(10) NOT NULL CHECK (allocation_type IN ('hours', 'percentage')),
    allocation_value REAL NOT NULL CHECK (allocation_value >= 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Foreign key to user_settings
    CONSTRAINT fk_cross_training_user
        FOREIGN KEY (user_id)
        REFERENCES user_settings(id)
        ON DELETE CASCADE,

    -- Ensure unique discipline per user
    CONSTRAINT uq_user_discipline
        UNIQUE (user_id, discipline)
);

-- Index for efficient user lookups
CREATE INDEX IF NOT EXISTS idx_cross_training_user
    ON user_cross_training_disciplines(user_id);

-- Add validation constraints
ALTER TABLE user_cross_training_disciplines
    ADD CONSTRAINT chk_percentage_range
    CHECK (allocation_type != 'percentage' OR (allocation_value >= 0 AND allocation_value <= 100));

ALTER TABLE user_cross_training_disciplines
    ADD CONSTRAINT chk_hours_reasonable
    CHECK (allocation_type != 'hours' OR allocation_value <= 40);

-- Add table and column comments for documentation
COMMENT ON TABLE user_cross_training_disciplines IS 'Multi-discipline cross-training configurations per user. Allows users to specify multiple cross-training activities with hours or percentage allocation.';
COMMENT ON COLUMN user_cross_training_disciplines.discipline IS 'Cross-training activity type: cycling, swimming, rowing, backcountry_skiing, hiking, or other';
COMMENT ON COLUMN user_cross_training_disciplines.allocation_type IS 'Allocation method: hours (hours per week) or percentage (% of total training time)';
COMMENT ON COLUMN user_cross_training_disciplines.allocation_value IS 'Either hours per week (0-40) or percentage (0-100) depending on allocation_type';

-- ============================================================================
-- Migrate existing single-discipline cross-training data to new table
-- ============================================================================
INSERT INTO user_cross_training_disciplines (user_id, discipline, enabled, allocation_type, allocation_value)
SELECT
    id as user_id,
    LOWER(REPLACE(COALESCE(cross_training_type, 'cycling'), ' ', '_')) as discipline,
    include_cross_training as enabled,
    'hours' as allocation_type,
    COALESCE(cross_training_hours_per_week, 0) as allocation_value
FROM user_settings
WHERE include_cross_training = TRUE
    AND cross_training_type IS NOT NULL
    AND cross_training_hours_per_week > 0
ON CONFLICT (user_id, discipline) DO NOTHING;

-- ============================================================================
-- Keep legacy columns for backward compatibility and rollback safety
-- DO NOT DROP: include_cross_training, cross_training_type, cross_training_hours_per_week
-- ============================================================================
-- These columns will remain in user_settings for:
-- 1. Backward compatibility with existing code during transition
-- 2. Rollback safety if migration needs to be reverted
-- 3. Legacy API support

-- Add comment to legacy columns
COMMENT ON COLUMN user_settings.include_cross_training IS 'DEPRECATED: Legacy single cross-training flag. Use user_cross_training_disciplines table instead.';
COMMENT ON COLUMN user_settings.cross_training_type IS 'DEPRECATED: Legacy single cross-training type. Use user_cross_training_disciplines table instead.';
COMMENT ON COLUMN user_settings.cross_training_hours_per_week IS 'DEPRECATED: Legacy single cross-training hours. Use user_cross_training_disciplines table instead.';

-- Verification query (uncomment to test after migration)
-- SELECT
--     us.id,
--     us.username,
--     us.include_cross_training AS legacy_enabled,
--     us.cross_training_type AS legacy_type,
--     us.cross_training_hours_per_week AS legacy_hours,
--     COUNT(uctd.id) AS new_disciplines_count
-- FROM user_settings us
-- LEFT JOIN user_cross_training_disciplines uctd ON us.id = uctd.user_id
-- GROUP BY us.id, us.username, us.include_cross_training, us.cross_training_type, us.cross_training_hours_per_week
-- ORDER BY us.id;
