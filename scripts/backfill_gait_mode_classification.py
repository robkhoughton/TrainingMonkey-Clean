"""
Backfill gait_mode_aggregates for existing activities.

Scope: user_id=1 (Rob) only, by design -- extending this to all users is an
open decision left to Rob in the cadence/gait-mode coaching plan, not made
here. Only activities with real elevation gain are worth classifying (flat
activities have no hiking mode to separate out).

Idempotent/resumable: skips any activity that already has a FULLY POPULATED row
(all aggregate fields non-null) for the current CLASSIFIER_VERSION, so a re-run
(or a run interrupted partway through) only processes what's missing. This also
means adding a new additive field to classify_gait_modes() (e.g. running_speed_*,
added 2026-09-12) naturally reprocesses existing rows to backfill just that field,
without bumping CLASSIFIER_VERSION or touching classification logic. A real
classifier retune still bumps CLASSIFIER_VERSION, which makes this script
reprocess everything under the new version without touching old rows.

Throttling: 1 second between Strava API calls, matching the existing bulk-sync
pattern in strava_training_load.py (sync_activities_from_strava, ~line 2331).

Run from the app/ directory:
    cd app && python ../scripts/backfill_gait_mode_classification.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from db_credentials_loader import set_database_url
set_database_url()

import db_utils
from stravalib.client import Client
from enhanced_token_management import refresh_tokens_if_needed
from strava_training_load import get_activity_streams
from gait_classifier import classify_gait_modes, CLASSIFIER_VERSION

USER_ID = 1
MIN_ELEVATION_GAIN_FEET = 200  # skip flat activities -- no hiking mode to separate


def main():
    print(f"Backfilling gait-mode aggregates for user_id={USER_ID}, "
          f"classifier_version={CLASSIFIER_VERSION}")

    tokens = refresh_tokens_if_needed(USER_ID)
    if not tokens or not tokens.get('access_token'):
        print("ERROR: could not obtain a valid Strava access token for user_id=1")
        return
    client = Client(access_token=tokens['access_token'])

    candidates = db_utils.execute_query(
        """
        SELECT a.activity_id, a.name, a.date, a.elevation_gain_feet, a.distance_miles
        FROM activities a
        LEFT JOIN gait_mode_aggregates g
            ON g.activity_id = a.activity_id AND g.classifier_version = %s
        WHERE a.user_id = %s
          AND a.elevation_gain_feet >= %s
          AND (g.id IS NULL OR g.running_speed_mean IS NULL)
        ORDER BY a.date DESC
        """,
        (CLASSIFIER_VERSION, USER_ID, MIN_ELEVATION_GAIN_FEET),
        fetch=True
    )

    print(f"Found {len(candidates)} activities needing classification "
          f"(elevation_gain_feet >= {MIN_ELEVATION_GAIN_FEET}, not yet on {CLASSIFIER_VERSION})")

    processed = 0
    skipped_no_streams = 0
    errors = 0
    start_time = time.time()

    for row in candidates:
        activity_id = row['activity_id']
        try:
            streams = get_activity_streams(client, activity_id)
            aggregates = classify_gait_modes(streams) if streams else None

            if not aggregates:
                print(f"  {activity_id} ({row['date']}, {row['name']}): "
                      f"no usable streams -- skipped")
                skipped_no_streams += 1
                continue

            db_utils.save_gait_mode_aggregates(activity_id, USER_ID, aggregates)
            processed += 1
            print(f"  {activity_id} ({row['date']}, {row['name']}): "
                  f"running={aggregates['running_seconds']:.0f}s "
                  f"hiking={aggregates['hiking_seconds']:.0f}s "
                  f"uncertain={aggregates['uncertain_seconds']:.0f}s "
                  f"run_cadence_mean={aggregates['running_cadence_mean']}")

        except Exception as e:
            print(f"  {activity_id}: ERROR - {e}")
            errors += 1

        time.sleep(1)  # matches existing bulk-sync throttle

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.1f}s. Processed={processed} "
          f"skipped_no_streams={skipped_no_streams} errors={errors} "
          f"of {len(candidates)} candidates.")


if __name__ == "__main__":
    main()
