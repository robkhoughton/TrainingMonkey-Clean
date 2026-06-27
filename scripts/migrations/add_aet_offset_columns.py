"""
Migration: add dynamic-AeT offset calibration columns to athlete_models.

Part of the Dynamic AeT build (Phase 0). These columns hold the per-athlete offset
function parameters that modulate baseline AeT by autonomic readiness. They are SEEDED
with population defaults (decision c, 2026-06-27) and personalized over time via
drift-test anchoring. Defaults live here (column DEFAULT) and as fallback constants in
app/dynamic_aet.py — never as magic numbers buried in logic.

  aet_offset_deadband      sigma; no AeT shift within +/- this z-score band
  aet_offset_slope_neg     bpm per sigma below the dead-band (downward gain)
  aet_offset_slope_pos     bpm per sigma above the dead-band (upward gain, gentler)
  aet_offset_cap_neg       max downward offset (bpm)
  aet_offset_cap_pos       max upward offset (bpm)
  aet_offset_staleness_days  latest HRV older than this -> decay offset toward 0
  aet_offset_n             count of drift-test calibration pairs accumulated
  aet_offset_confidence    0..1 calibration confidence (mirrors acwr_sweet_spot_confidence)

Run autonomously via the Cloud SQL proxy (see .claude/CLAUDE.md § Local Development).
Idempotent: ADD COLUMN IF NOT EXISTS.
"""
import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app')
sys.path.insert(0, APP_DIR)

# db_utils validates DATABASE_URL at import time, so load env + set the URL first.
from dotenv import load_dotenv
load_dotenv(os.path.join(APP_DIR, '.env'))
from db_credentials_loader import set_database_url
set_database_url()
import db_utils

COLUMNS = [
    ("aet_offset_deadband",      "double precision", "0.5"),
    ("aet_offset_slope_neg",     "double precision", "4.0"),
    ("aet_offset_slope_pos",     "double precision", "1.5"),
    ("aet_offset_cap_neg",       "double precision", "-8.0"),
    ("aet_offset_cap_pos",       "double precision", "3.0"),
    ("aet_offset_staleness_days", "integer",         "3"),
    ("aet_offset_n",             "integer",          "0"),
    ("aet_offset_confidence",    "double precision", "0.0"),
]

for name, dtype, default in COLUMNS:
    db_utils.execute_query(
        f"ALTER TABLE athlete_models ADD COLUMN IF NOT EXISTS {name} {dtype} DEFAULT {default}"
    )
    print(f"  ensured column {name} {dtype} DEFAULT {default}")

# Verify
rows = db_utils.execute_query(
    """SELECT column_name, data_type, column_default
       FROM information_schema.columns
       WHERE table_name = 'athlete_models' AND column_name LIKE 'aet_offset%%'
       ORDER BY column_name""",
    fetch=True,
)
print("\nVerification — aet_offset_* columns now present:")
for r in rows:
    print(" ", dict(r))
print(f"\nDone: {len(rows)} offset columns present.")
