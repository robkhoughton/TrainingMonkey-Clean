-- Migration: add deviation_reason to ai_autopsies
-- Purpose: stores Phase C cause classification (physical/external/unknown) per autopsy date
-- so update_athlete_model() can anchor breakdown threshold calibration to physical-cause events only.
-- Run in Google Cloud SQL Editor.

ALTER TABLE ai_autopsies
ADD COLUMN IF NOT EXISTS deviation_reason TEXT;
