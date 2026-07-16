"""
One-off data cleanup: delete stale synthetic rest-day placeholder rows
(activity_id < 0) that share a date with a real activity (activity_id > 0).

Root cause: auto_mark_rest_day_and_generate_recommendation() and
ensure_daily_records() both insert a synthetic 'Rest Day' row (negative
activity_id) when no activity has synced yet for a date. If the real Strava
activity for that date syncs in later, nothing reconciled the two rows,
corrupting _calculate_days_since_rest_time_based()'s "last rest day" query
(unified_metrics_service.py) since it matches on activity_id < 0 alone with
no check for a contradicting same-date real activity.

save_training_load() (strava_training_load.py) now deletes any same-date
placeholder when a real activity is inserted going forward. This script is
the one-off backfill for placeholders that predate that fix.

Reference/documentation only per project convention — run via
db_credentials_loader + db_utils.execute_query() from app/, not the Cloud
SQL Editor (this is a data cleanup, not a schema change).
"""
import sys
sys.path.insert(0, '.')  # run from app/ so app modules resolve
from db_credentials_loader import set_database_url
set_database_url()
import db_utils

# Find every date with both a synthetic placeholder and a real activity.
duplicates = db_utils.execute_query(
    """
    SELECT r.user_id, r.date, r.activity_id AS placeholder_id
    FROM activities r
    WHERE r.activity_id < 0
      AND EXISTS (
          SELECT 1 FROM activities real
          WHERE real.user_id = r.user_id
            AND real.date = r.date
            AND real.activity_id > 0
      )
    """,
    fetch=True
)

print(f"Found {len(duplicates)} stale rest-day placeholder(s) contradicted by a real activity:")
for row in duplicates:
    print(f"  user_id={row['user_id']} date={row['date']} placeholder_id={row['placeholder_id']}")

if duplicates:
    deleted = db_utils.execute_query(
        """
        DELETE FROM activities r
        WHERE r.activity_id < 0
          AND EXISTS (
              SELECT 1 FROM activities real
              WHERE real.user_id = r.user_id
                AND real.date = r.date
                AND real.activity_id > 0
          )
        RETURNING user_id, date, activity_id
        """,
        fetch=True
    )
    print(f"Deleted {len(deleted)} row(s).")
else:
    print("Nothing to clean up.")
