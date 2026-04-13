"""
intervals_icu_sync.py — Daily wellness sync from intervals.icu API.

Pulls HRV, resting HR, sleep, weight, spO2, respiration, and VO2max
for all users with intervals.icu credentials. Writes to journal_entries.

Called from strava_app.py daily scheduler before the 6AM recommendation job.
"""

import logging
from datetime import date, timedelta

import requests

from db_utils import execute_query

logger = logging.getLogger(__name__)

INTERVALS_ICU_BASE = "https://intervals.icu/api/v1"


def sync_wellness_for_user(user_id: int, api_key: str, athlete_id: str, target_date: date) -> bool:
    """
    Fetch one day of wellness data from intervals.icu and upsert into journal_entries.

    intervals.icu dates sleep/HRV by the night it STARTED (e.g. Friday night = April 3).
    Readiness applies to the morning AFTER that sleep (Saturday = April 4).
    So we fetch target_date from intervals.icu but write to target_date + 1 in the DB.

    Returns True if data was found and written, False if no data for that date.
    """
    date_str = target_date.isoformat()                          # for API request
    write_date_str = (target_date + timedelta(days=1)).isoformat()  # for DB write
    url = f"{INTERVALS_ICU_BASE}/athlete/{athlete_id}/wellness"
    params = {"oldest": date_str, "newest": date_str}

    try:
        resp = requests.get(url, params=params, auth=("API_KEY", api_key), timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.error(f"[intervals.icu] API request failed for user {user_id}: {e}")
        return False

    if not data:
        logger.debug(f"[intervals.icu] No wellness data for user {user_id} on {date_str}")
        return False

    w = data[0]

    hrv_value        = w.get("hrv")           # rMSSD ms
    resting_hr       = w.get("restingHR")     # bpm
    sleep_secs       = w.get("sleepSecs")     # seconds
    sleep_score      = w.get("sleepScore")    # 0–100
    weight           = w.get("weight")        # kg
    spo2             = w.get("spO2")          # %
    respiration_rate = w.get("respiration")   # breaths/min
    vo2max           = w.get("vo2max")        # ml/kg/min

    # Skip upsert if all fields are null — nothing to write
    if all(v is None for v in [hrv_value, resting_hr, sleep_secs, sleep_score,
                                weight, spo2, respiration_rate, vo2max]):
        logger.debug(f"[intervals.icu] All fields null for user {user_id} on {date_str} — skipping")
        return False

    execute_query("""
        INSERT INTO journal_entries
            (user_id, date, hrv_value, hrv_source, resting_hr,
             sleep_duration_secs, sleep_score, weight, spo2, respiration_rate, vo2max,
             updated_at)
        VALUES (%s, %s, %s, 'intervals_icu', %s, %s, %s, %s, %s, %s, %s, NOW())
        ON CONFLICT (user_id, date) DO UPDATE SET
            hrv_value           = COALESCE(EXCLUDED.hrv_value,           journal_entries.hrv_value),
            hrv_source          = COALESCE(EXCLUDED.hrv_source,          journal_entries.hrv_source),
            resting_hr          = COALESCE(EXCLUDED.resting_hr,          journal_entries.resting_hr),
            sleep_duration_secs = COALESCE(EXCLUDED.sleep_duration_secs, journal_entries.sleep_duration_secs),
            sleep_score         = COALESCE(EXCLUDED.sleep_score,         journal_entries.sleep_score),
            weight              = COALESCE(EXCLUDED.weight,              journal_entries.weight),
            spo2                = COALESCE(EXCLUDED.spo2,                journal_entries.spo2),
            respiration_rate    = COALESCE(EXCLUDED.respiration_rate,    journal_entries.respiration_rate),
            vo2max              = COALESCE(EXCLUDED.vo2max,              journal_entries.vo2max),
            updated_at          = NOW()
    """, (user_id, write_date_str, hrv_value, resting_hr, sleep_secs,
          sleep_score, weight, spo2, respiration_rate, vo2max))

    logger.info(
        f"[intervals.icu] Synced wellness for user {user_id} on {date_str} → written to {write_date_str}: "
        f"hrv={hrv_value}, rhr={resting_hr}, sleep={sleep_secs}s, "
        f"weight={weight}, spo2={spo2}, resp={respiration_rate}, vo2max={vo2max}"
    )
    return True


def run_daily_sync(target_date: date = None) -> dict:
    """
    Sync wellness data for all users with intervals.icu credentials.
    Called once daily before the 6AM recommendation job.

    Fetches yesterday's date from intervals.icu and writes it to today's journal_entries
    row (date + 1 shift). This correctly maps Friday-night sleep → Saturday readiness.

    If target_date is supplied, only that single date is synced (used by tests/backfills).
    Returns summary: {synced: N, skipped: N, errors: N}
    """
    if target_date is not None:
        dates_to_sync = [target_date]
    else:
        dates_to_sync = [date.today() - timedelta(days=1)]

    users = execute_query(
        """SELECT id, intervals_icu_api_key, intervals_icu_athlete_id
           FROM user_settings
           WHERE intervals_icu_api_key IS NOT NULL
             AND intervals_icu_athlete_id IS NOT NULL""",
        fetch=True
    )

    if not users:
        logger.info("[intervals.icu] No users with intervals.icu credentials — skipping sync")
        return {"synced": 0, "skipped": 0, "errors": 0}

    synced = skipped = errors = 0
    for row in users:
        user_id    = row["id"]
        api_key    = row["intervals_icu_api_key"]
        athlete_id = row["intervals_icu_athlete_id"]
        for d in dates_to_sync:
            try:
                result = sync_wellness_for_user(user_id, api_key, athlete_id, d)
                if result:
                    synced += 1
                else:
                    skipped += 1
            except Exception as e:
                logger.error(f"[intervals.icu] Unexpected error for user {user_id} on {d}: {e}", exc_info=True)
                errors += 1

    logger.info(f"[intervals.icu] Daily sync complete: synced={synced}, skipped={skipped}, errors={errors}")
    return {"synced": synced, "skipped": skipped, "errors": errors}
