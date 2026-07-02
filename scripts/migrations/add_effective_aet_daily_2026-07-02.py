"""
Migration: create effective_aet_daily — one row per user per day recording the APPLIED
effective (dynamic) AeT.

Why store it (not just recompute): get_effective_aet(as_of_date) recomputes with the
CURRENT offset params, so once those params are calibrated/changed, historical
reconstruction no longer reflects what was actually applied that day. Only a stored record
preserves the true applied value. This series is the substrate for (1) trending the
effective vs baseline AeT (SeasonPage chart), (2) calibrating the per-athlete offset from
(hrv_z, offset, effective_aet) pairs against measured drift/LT1 tests, and (3) the lactate
validation experiment.

Column note: the offset is stored as `aet_offset` because OFFSET is a reserved word in
PostgreSQL.

Run autonomously via the Cloud SQL proxy. Idempotent.
"""
import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app')
sys.path.insert(0, APP_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(APP_DIR, '.env'))
from db_credentials_loader import set_database_url
set_database_url()
import db_utils

db_utils.execute_query("""
    CREATE TABLE IF NOT EXISTS effective_aet_daily (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        date DATE NOT NULL,
        baseline_aet INTEGER,
        effective_aet INTEGER,
        aet_offset REAL,
        hrv_z REAL,
        readiness_state VARCHAR(32),
        fallback_reason VARCHAR(32),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW(),
        UNIQUE (user_id, date)
    )
""")
print("ensured table effective_aet_daily")

cols = db_utils.execute_query(
    """SELECT column_name, data_type FROM information_schema.columns
       WHERE table_name = 'effective_aet_daily' ORDER BY ordinal_position""",
    fetch=True,
)
print("Verification — columns:")
for c in cols:
    print("  ", dict(c))
print("Done." if cols else "FAILED — table not present.")
