-- Add dual-track autopsy scoring: quality_score (intrinsic value), composite_score (weighted blend)
-- and per-user weights for tuning the blend.

ALTER TABLE ai_autopsies
  ADD COLUMN IF NOT EXISTS quality_score INT,
  ADD COLUMN IF NOT EXISTS composite_score NUMERIC(4,2);

ALTER TABLE user_settings
  ADD COLUMN IF NOT EXISTS autopsy_weight_alignment NUMERIC(3,2) DEFAULT 0.50,
  ADD COLUMN IF NOT EXISTS autopsy_weight_quality   NUMERIC(3,2) DEFAULT 0.50;
