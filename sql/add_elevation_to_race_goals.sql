-- Add elevation_gain_feet to race_goals table
-- Aligns race goal tracking with training activity elevation tracking

ALTER TABLE race_goals 
ADD COLUMN elevation_gain_feet INTEGER;

-- Add comment for documentation
COMMENT ON COLUMN race_goals.elevation_gain_feet IS 'Target elevation gain in feet for the race';

-- Optional: Add index if we plan to query/sort by elevation
CREATE INDEX idx_race_goals_elevation ON race_goals(elevation_gain_feet) WHERE elevation_gain_feet IS NOT NULL;




