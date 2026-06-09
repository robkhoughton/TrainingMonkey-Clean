"""
Backfill journal_power_score for all existing journal_entries rows.

Run from the app/ directory with the SQL proxy running:
    cd app && python ../scripts/migrations/backfill_journal_power_score.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../../app')

from db_credentials_loader import set_database_url
import db_utils
from strava_app import compute_journal_power

set_database_url()

rows = db_utils.execute_query(
    """SELECT id, user_id, date,
              energy_level, rpe_score, pain_percentage, notes,
              sleep_quality, morning_soreness, hrv_value, resting_hr
       FROM journal_entries
       ORDER BY date""",
    fetch=True
)

if not rows:
    print("No journal entries found.")
    sys.exit(0)

print(f"Scoring {len(rows)} journal entries...")
updated = 0
for row in rows:
    r = dict(row)
    score = compute_journal_power(r)
    db_utils.execute_query(
        "UPDATE journal_entries SET journal_power_score = %s WHERE id = %s",
        (score, r['id'])
    )
    updated += 1

print(f"Done. Updated {updated} rows.")
