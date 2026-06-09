"""
Migration: Add pending_session_adjustments JSONB column to athlete_models

Stores session-type-specific adjustments extracted from autopsies, keyed by
hard_session_type (tempo|intervals|hills|race_sim), with a 14-day expiry.

SQL to run in Google Cloud SQL Editor:

    ALTER TABLE athlete_models
    ADD COLUMN IF NOT EXISTS pending_session_adjustments JSONB;

No bootstrapping needed — column starts NULL for all existing rows and
is populated the next time update_athlete_model() runs after an autopsy
that contains a NEXT_SESSION_ADJUSTMENT.
"""

SQL = """
ALTER TABLE athlete_models
ADD COLUMN IF NOT EXISTS pending_session_adjustments JSONB;
"""
