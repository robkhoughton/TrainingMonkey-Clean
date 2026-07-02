"""
Migration: test-segment pace support for the aerobic (AeT) assessment.

Part D of the "surface effective-AeT history" work. Two forward-looking changes:

  1. hr_streams.distance_data  JSONB (nullable)
       Per-sample cumulative distance (meters), index-aligned with hr_data. Strava
       already returns this stream (get_activity_streams requests 'distance') but the
       sync discarded everything except heartrate. Capturing it lets us compute an
       EXACT average pace over the selected steady-state test segment — valid here
       (unlike trail running) because the drift/LT1 test is a controlled treadmill/flat
       condition. FORWARD-ONLY: NULL for all history; populates on activities synced
       from this deploy onward.

  2. aerobic_assessments: avg_pace_sec_per_mi REAL, pace_source VARCHAR, cooldown_minutes REAL
       Persist the computed test-segment pace and how it was derived:
         pace_source = 'stream'  -> exact, from the stored distance stream
                     = 'notes'   -> parsed from the athlete's free-text notes (fallback
                                    for past tests with no stored distance stream)
                     = NULL      -> unknown
       cooldown_minutes is stored so the steady-state segment bounds [warmup, -cooldown]
       are known exactly at read time (only warmup_minutes was persisted before).

PostgreSQL only. Idempotent (IF NOT EXISTS guards). Per this task's constraint the
migration is authored for review — run it (or hand it to whoever runs migrations) rather
than executing from application code. Run from app/ via the Cloud SQL proxy per
.claude/CLAUDE.md § Local Development.
"""
import os
import sys

APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app')
sys.path.insert(0, APP_DIR)

from dotenv import load_dotenv  # noqa: E402
load_dotenv(os.path.join(APP_DIR, '.env'))
from db_credentials_loader import set_database_url  # noqa: E402
set_database_url()
import db_utils  # noqa: E402


def run():
    # ── 1. hr_streams.distance_data ─────────────────────────────────────────
    db_utils.execute_query(
        "ALTER TABLE hr_streams ADD COLUMN IF NOT EXISTS distance_data JSONB"
    )
    print("OK hr_streams.distance_data ready (nullable, forward-only)")

    # ── 2. aerobic_assessments pace columns ─────────────────────────────────
    db_utils.execute_query(
        "ALTER TABLE aerobic_assessments ADD COLUMN IF NOT EXISTS avg_pace_sec_per_mi REAL"
    )
    db_utils.execute_query(
        "ALTER TABLE aerobic_assessments ADD COLUMN IF NOT EXISTS pace_source VARCHAR(16)"
    )
    db_utils.execute_query(
        "ALTER TABLE aerobic_assessments ADD COLUMN IF NOT EXISTS cooldown_minutes REAL"
    )
    print("OK aerobic_assessments pace columns ready")

    # ── verify ──────────────────────────────────────────────────────────────
    for tbl, col in (('hr_streams', 'distance_data'),
                     ('aerobic_assessments', 'avg_pace_sec_per_mi'),
                     ('aerobic_assessments', 'pace_source'),
                     ('aerobic_assessments', 'cooldown_minutes')):
        chk = db_utils.execute_query(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = %s AND column_name = %s",
            (tbl, col), fetch=True,
        )
        print(f"{tbl}.{col} present:", bool(chk))


if __name__ == '__main__':
    run()
    print("Migration complete.")
