-- Migration: add early warning columns to athlete_models
-- Purpose: stores physical distress pattern warning state so the journal
-- can surface a banner when the athlete shows repeated physical distress signals.
-- Auto-cleared by update_athlete_model() when pattern improves.
-- Run in Google Cloud SQL Editor.

ALTER TABLE athlete_models
ADD COLUMN IF NOT EXISTS early_warning_active BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS early_warning_message TEXT;
