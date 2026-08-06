"""
Migration: add activities.avg_temp_f — device-reported ambient temperature (Fahrenheit).

Sourced from Strava's per-activity 'temp' stream (Celsius, converted to Fahrenheit at
ingestion in strava_training_load.py to match the codebase's imperial column convention,
e.g. distance_miles, elevation_gain_feet). Only populated when the source device has a
temperature sensor — NULL otherwise.

Forward-only: NULL for activities synced before this field existed (no backfill — would
require re-fetching streams for every historical activity against Strava rate limits).

Run autonomously via the Cloud SQL proxy. Idempotent: ADD COLUMN IF NOT EXISTS.
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

db_utils.execute_query(
    "ALTER TABLE activities ADD COLUMN IF NOT EXISTS avg_temp_f REAL"
)
print("ensured column activities.avg_temp_f REAL")

rows = db_utils.execute_query(
    """SELECT column_name, data_type
       FROM information_schema.columns
       WHERE table_name = 'activities' AND column_name = 'avg_temp_f'""",
    fetch=True,
)
print("Verification:", [dict(r) for r in rows])
print("Done." if rows else "FAILED — column not present.")
