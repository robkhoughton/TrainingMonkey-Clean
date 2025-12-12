-- Strength Training Support - Database Schema Migration
-- Execute this in SQL Editor per project rules

-- Add sport_type column to classify activities
ALTER TABLE activities ADD COLUMN IF NOT EXISTS sport_type VARCHAR(20);

-- Add strength-specific fields
ALTER TABLE activities ADD COLUMN IF NOT EXISTS strength_equivalent_miles REAL;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS strength_rpe INTEGER;

-- Create index for filtering by sport type
CREATE INDEX IF NOT EXISTS idx_activities_sport_type ON activities(user_id, sport_type);

-- Update existing activities to have sport_type based on activity type
-- Running activities
UPDATE activities 
SET sport_type = 'running' 
WHERE sport_type IS NULL 
  AND (type LIKE '%Run%' OR type LIKE '%run%' OR type = 'Walk' OR type = 'Hike');

-- Cycling activities
UPDATE activities 
SET sport_type = 'cycling'
WHERE sport_type IS NULL
  AND (type LIKE '%Bike%' OR type LIKE '%Ride%' OR type LIKE '%Cycling%' OR type LIKE '%bike%');

-- Swimming activities
UPDATE activities 
SET sport_type = 'swimming'
WHERE sport_type IS NULL
  AND (type LIKE '%Swim%' OR type LIKE '%swim%');

-- Strength activities
UPDATE activities 
SET sport_type = 'strength'
WHERE sport_type IS NULL
  AND (type LIKE '%Weight%' OR type LIKE '%Strength%' OR type LIKE '%Crossfit%' 
       OR type LIKE '%Workout%' OR type = 'Yoga');

-- Default remaining to running for safety
UPDATE activities 
SET sport_type = 'running'
WHERE sport_type IS NULL;

-- Verify migration
SELECT sport_type, COUNT(*) as count 
FROM activities 
GROUP BY sport_type 
ORDER BY count DESC;

