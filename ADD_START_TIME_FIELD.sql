-- SQL to add start_time and device_name fields to activities table
-- These fields support:
-- 1. Activity start time display on Activities page
-- 2. Garmin device attribution (branding compliance, effective Nov 1, 2025)

ALTER TABLE activities 
ADD COLUMN IF NOT EXISTS start_time TEXT;

ALTER TABLE activities 
ADD COLUMN IF NOT EXISTS device_name TEXT;

-- Comments:
-- start_time: Stores the local time of activity start in 'HH:MM:SS' format
-- device_name: Stores the device/watch name used to record the activity
-- Both will be populated during the next Strava sync for existing activities

