"""
backfill_rhr_from_oura.py

Re-syncs resting_hr (and hrv_value) from intervals.icu for a given date range,
force-overwriting existing values. Use after disconnecting Garmin wellness so
intervals.icu now serves Oura's values exclusively for these fields.

Run from the app/ directory:
    cd app && python ../scripts/migrations/backfill_rhr_from_oura.py

Args (optional env vars):
    BACKFILL_DAYS  — how many days back to cover (default 90)
    DRY_RUN        — set to "1" to print without writing
"""
import os
import sys
from datetime import date, timedelta

# Must be run from the app/ directory (app modules use relative imports)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'app'))

from dotenv import load_dotenv
load_dotenv()

from db_credentials_loader import set_database_url
import db_utils
import requests

set_database_url()

INTERVALS_BASE = "https://intervals.icu/api/v1"
BACKFILL_DAYS  = int(os.environ.get("BACKFILL_DAYS", 90))
DRY_RUN        = os.environ.get("DRY_RUN", "0") == "1"


def fetch_wellness(api_key: str, athlete_id: str, target_date: date):
    url = f"{INTERVALS_BASE}/athlete/{athlete_id}/wellness"
    resp = requests.get(
        url,
        params={"oldest": target_date.isoformat(), "newest": target_date.isoformat()},
        auth=("API_KEY", api_key),
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    return data[0] if data else None


def run():
    # Load Rob's credentials
    row = db_utils.execute_query(
        """SELECT id, intervals_icu_api_key, intervals_icu_athlete_id
           FROM user_settings WHERE email = %s""",
        ("rob.houghton.ca@gmail.com",),
        fetch=True,
    )
    if not row or not row[0].get("intervals_icu_api_key"):
        print("ERROR: No intervals.icu credentials found.")
        return

    user_id    = row[0]["id"]
    api_key    = row[0]["intervals_icu_api_key"]
    athlete_id = row[0]["intervals_icu_athlete_id"]

    today     = date.today()
    start     = today - timedelta(days=BACKFILL_DAYS)
    days      = [(start + timedelta(days=i)) for i in range(BACKFILL_DAYS + 1)]

    print(f"Backfilling {len(days)} days ({start} to {today})"
          + (" [DRY RUN]" if DRY_RUN else ""))
    print(f"{'date':<12} {'old_rhr':>7} {'new_rhr':>7} {'old_hrv':>7} {'new_hrv':>7}  action")
    print("-" * 60)

    changed = skipped = no_data = 0

    for d in days:
        # Fetch existing values
        existing = db_utils.execute_query(
            "SELECT resting_hr, hrv_value FROM journal_entries WHERE user_id = %s AND date = %s",
            (user_id, d.isoformat()),
            fetch=True,
        )
        old_rhr = existing[0]["resting_hr"] if existing else None
        old_hrv = existing[0]["hrv_value"]  if existing else None

        # Fetch from intervals.icu
        try:
            w = fetch_wellness(api_key, athlete_id, d)
        except requests.RequestException as e:
            print(f"{d}  FETCH ERROR: {e}")
            continue

        if w is None:
            no_data += 1
            continue

        new_rhr = w.get("restingHR")
        new_hrv = w.get("hrv")

        rhr_changed = new_rhr is not None and new_rhr != old_rhr
        hrv_changed = new_hrv is not None and new_hrv != old_hrv

        if not rhr_changed and not hrv_changed:
            skipped += 1
            continue

        action = []
        if rhr_changed: action.append(f"rhr {old_rhr}->{new_rhr}")
        if hrv_changed: action.append(f"hrv {old_hrv}->{new_hrv}")

        print(f"{d}  {str(old_rhr):>7} {str(new_rhr):>7} {str(old_hrv):>7} {str(new_hrv):>7}  {', '.join(action)}")

        if not DRY_RUN:
            db_utils.execute_query(
                """INSERT INTO journal_entries (user_id, date, resting_hr, hrv_value, hrv_source, updated_at)
                   VALUES (%s, %s, %s, %s, 'intervals_icu', NOW())
                   ON CONFLICT (user_id, date) DO UPDATE SET
                       resting_hr = CASE WHEN EXCLUDED.resting_hr IS NOT NULL
                                         THEN EXCLUDED.resting_hr
                                         ELSE journal_entries.resting_hr END,
                       hrv_value  = CASE WHEN EXCLUDED.hrv_value IS NOT NULL
                                         THEN EXCLUDED.hrv_value
                                         ELSE journal_entries.hrv_value END,
                       hrv_source = CASE WHEN EXCLUDED.hrv_value IS NOT NULL
                                         THEN 'intervals_icu'
                                         ELSE journal_entries.hrv_source END,
                       updated_at = NOW()""",
                (user_id, d.isoformat(), new_rhr, new_hrv),
            )
        changed += 1

    print("-" * 60)
    print(f"Done. Changed: {changed}  Unchanged: {skipped}  No data: {no_data}"
          + (" [DRY RUN — nothing written]" if DRY_RUN else ""))


if __name__ == "__main__":
    run()
