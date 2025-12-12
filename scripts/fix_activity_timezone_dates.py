#!/usr/bin/env python3
"""
Fix Activity Timezone Dates
============================
Corrects activity dates that were incorrectly stored due to UTC vs local timezone bug.

The bug: activity dates were extracted from activity.start_date (UTC) instead of
activity.start_date_local (athlete's timezone), causing evening activities to be
assigned to the next day.

This script:
1. Re-fetches activity details from Strava API
2. Compares stored date with correct local date
3. Updates activities with incorrect dates
4. Recalculates ACWR and moving averages for affected dates
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app')))

from db_credentials_loader import set_database_url
set_database_url()

import db_utils
from strava_training_load import connect_to_strava, update_moving_averages
from timezone_utils import get_user_timezone
from stravalib.client import Client
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_activities_needing_fix(user_id, days_back=90):
    """
    Get activities that might have incorrect dates.
    We'll check all activities from the last N days.
    """
    from datetime import date

    end_date = date.today()
    start_date = end_date - timedelta(days=days_back)

    logger.info(f"Checking activities from {start_date} to {end_date} for user {user_id}")

    activities = db_utils.execute_query("""
        SELECT activity_id, date, name, type, start_time
        FROM activities
        WHERE user_id = %s
        AND date >= %s
        AND activity_id > 0
        ORDER BY date DESC, activity_id DESC
    """, (user_id, start_date), fetch=True)

    if not activities:
        logger.warning(f"No activities found for user {user_id} in the specified date range")
        return []

    logger.info(f"Found {len(activities)} activities to check")
    return activities


def get_correct_date_from_strava(client, activity_id):
    """
    Fetch the activity from Strava and get the correct local date.
    """
    try:
        activity = client.get_activity(activity_id)

        if not activity or not hasattr(activity, 'start_date_local'):
            logger.warning(f"Activity {activity_id} missing start_date_local")
            return None

        correct_date = activity.start_date_local.strftime('%Y-%m-%d')
        utc_date = activity.start_date.strftime('%Y-%m-%d')

        return {
            'correct_date': correct_date,
            'utc_date': utc_date,
            'start_time': activity.start_date_local.strftime('%H:%M:%S'),
            'timezone': activity.timezone if hasattr(activity, 'timezone') else None
        }

    except Exception as e:
        logger.error(f"Error fetching activity {activity_id} from Strava: {str(e)}")
        return None


def update_activity_date(activity_id, user_id, old_date, new_date, new_start_time):
    """
    Update the activity date in the database.
    """
    try:
        logger.info(f"Updating activity {activity_id}: {old_date} -> {new_date}")

        db_utils.execute_query("""
            UPDATE activities
            SET date = %s, start_time = %s
            WHERE activity_id = %s AND user_id = %s
        """, (new_date, new_start_time, activity_id, user_id))

        return True

    except Exception as e:
        logger.error(f"Error updating activity {activity_id}: {str(e)}")
        return False


def recalculate_date_metrics(user_id, date_str):
    """
    Recalculate moving averages and ACWR for a specific date.
    """
    try:
        logger.info(f"Recalculating metrics for {date_str}")
        update_moving_averages(date_str, user_id)
        return True
    except Exception as e:
        logger.error(f"Error recalculating metrics for {date_str}: {str(e)}")
        return False


def fix_activity_dates(user_id, days_back=90, dry_run=True):
    """
    Main function to fix activity dates.

    Args:
        user_id: User ID to fix activities for
        days_back: Number of days to check (default 90)
        dry_run: If True, only report issues without fixing (default True)
    """
    logger.info(f"{'[DRY RUN] ' if dry_run else ''}Starting activity date fix for user {user_id}")

    # Load Strava tokens from database
    user_data = db_utils.execute_query("""
        SELECT strava_access_token, strava_refresh_token
        FROM user_settings
        WHERE id = %s
    """, (user_id,), fetch=True)

    if not user_data or not user_data[0].get('strava_access_token'):
        logger.error(f"No Strava tokens found for user {user_id}")
        return

    access_token = user_data[0]['strava_access_token']

    # Connect to Strava
    client = Client(access_token=access_token)
    if not client:
        logger.error("Failed to connect to Strava")
        return

    # Get activities to check
    activities = get_activities_needing_fix(user_id, days_back)
    if not activities:
        return

    # Track statistics
    total_checked = 0
    total_incorrect = 0
    total_fixed = 0
    affected_dates = set()

    # Check each activity
    for activity in activities:
        total_checked += 1
        activity_id = activity['activity_id']
        stored_date = activity['date']
        activity_name = activity['name']

        # Convert date object to string if needed
        if isinstance(stored_date, datetime):
            stored_date_str = stored_date.strftime('%Y-%m-%d')
        elif hasattr(stored_date, 'strftime'):
            stored_date_str = stored_date.strftime('%Y-%m-%d')
        else:
            stored_date_str = str(stored_date)

        logger.info(f"Checking activity {activity_id}: '{activity_name}' (stored: {stored_date_str})")

        # Get correct date from Strava
        strava_data = get_correct_date_from_strava(client, activity_id)
        if not strava_data:
            logger.warning(f"Skipping activity {activity_id} - could not fetch from Strava")
            continue

        correct_date = strava_data['correct_date']
        utc_date = strava_data['utc_date']

        # Check if date is incorrect
        if stored_date_str != correct_date:
            total_incorrect += 1
            logger.warning(f"  ❌ INCORRECT: Activity {activity_id}")
            logger.warning(f"     Stored: {stored_date_str}")
            logger.warning(f"     Correct (local): {correct_date}")
            logger.warning(f"     UTC: {utc_date}")
            logger.warning(f"     Start time: {strava_data['start_time']}")
            logger.warning(f"     Timezone: {strava_data.get('timezone', 'Unknown')}")

            if not dry_run:
                # Update the activity
                if update_activity_date(activity_id, user_id, stored_date_str,
                                       correct_date, strava_data['start_time']):
                    total_fixed += 1
                    affected_dates.add(stored_date_str)
                    affected_dates.add(correct_date)
                    logger.info(f"  ✅ Fixed activity {activity_id}")
                else:
                    logger.error(f"  ❌ Failed to fix activity {activity_id}")
        else:
            logger.info(f"  ✅ OK: Date is correct ({correct_date})")

    # Recalculate metrics for affected dates
    if not dry_run and affected_dates:
        logger.info(f"\nRecalculating metrics for {len(affected_dates)} affected dates...")
        for date_str in sorted(affected_dates):
            recalculate_date_metrics(user_id, date_str)

    # Print summary
    logger.info("\n" + "="*70)
    logger.info("SUMMARY")
    logger.info("="*70)
    logger.info(f"Total activities checked: {total_checked}")
    logger.info(f"Activities with incorrect dates: {total_incorrect}")

    if dry_run:
        logger.info("\n⚠️  DRY RUN MODE - No changes were made")
        logger.info("Run with --fix flag to apply corrections")
    else:
        logger.info(f"Activities fixed: {total_fixed}")
        logger.info(f"Dates affected: {len(affected_dates)}")
        logger.info(f"Metrics recalculated: {len(affected_dates)}")
        logger.info("\n✅ Fix completed successfully")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Fix activity dates that were incorrectly stored due to timezone bug'
    )
    parser.add_argument(
        'user_id',
        type=int,
        help='User ID to fix activities for'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Number of days to check (default: 90)'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Actually fix the dates (default is dry-run mode)'
    )

    args = parser.parse_args()

    # Run the fix
    fix_activity_dates(
        user_id=args.user_id,
        days_back=args.days,
        dry_run=not args.fix
    )
