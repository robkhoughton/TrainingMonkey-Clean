-- SQL to add device_name field to activities table
-- Supports Garmin branding guidelines requiring device attribution (effective Nov 1, 2025)
-- Run this in your SQL Editor before deploying the code changes

ALTER TABLE activities 
ADD COLUMN IF NOT EXISTS device_name VARCHAR(255);

-- Comment: Stores the device name from Strava API (e.g., "Garmin Forerunner 965")
-- Used to display Garmin device attribution per compliance requirements
-- Will be populated during the next Strava sync for existing activities




