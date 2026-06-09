#!/usr/bin/env python3
"""
Recalculate all ACWR values using update_moving_averages
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from datetime import datetime, timedelta

# Load database credentials BEFORE importing db_utils
from db_credentials_loader import set_database_url
set_database_url()

# Now import modules
import db_utils
from strava_training_load import update_moving_averages

def recalculate_all_acwr(user_id):
    """Recalculate ACWR for all activity dates"""

    print(f"\n{'='*80}")
    print(f"Recalculating ACWR for User {user_id}")
    print(f"{'='*80}\n")

    # Get all unique dates with activities
    dates = db_utils.execute_query("""
        SELECT DISTINCT date
        FROM activities
        WHERE user_id = %s
        ORDER BY date ASC
    """, (user_id,), fetch=True)

    total_dates = len(dates)
    print(f"Found {total_dates} unique dates to process\n")

    # Process each date
    processed = 0
    errors = 0

    for i, row in enumerate(dates):
        date_str = str(row['date'])

        if (i + 1) % 10 == 0 or i == 0:
            print(f"Processing {i+1}/{total_dates}: {date_str}...", end='\r')

        try:
            update_moving_averages(date_str, user_id)
            processed += 1
        except Exception as e:
            print(f"\nError processing {date_str}: {str(e)}")
            errors += 1

    print(f"\n\n{'='*80}")
    print(f"Recalculation Complete!")
    print(f"{'='*80}")
    print(f"Dates processed: {processed}")
    print(f"Errors: {errors}")

    # Show new values for most recent date
    if dates:
        latest_date = str(dates[-1]['date'])
        print(f"\nMost Recent Date: {latest_date}")

        latest = db_utils.execute_query("""
            SELECT seven_day_avg_load,
                   twentyeight_day_avg_load,
                   acute_chronic_ratio,
                   trimp_acute_chronic_ratio,
                   normalized_divergence
            FROM activities
            WHERE user_id = %s AND date = %s
            LIMIT 1
        """, (user_id, latest_date), fetch=True)

        if latest:
            data = latest[0]
            print(f"\nNew ACWR Values:")
            print(f"  Acute (7-day):        {data['seven_day_avg_load']:.2f} miles/day")
            print(f"  Chronic (42-day):     {data['twentyeight_day_avg_load']:.2f} miles/day")
            print(f"  External ACWR:        {data['acute_chronic_ratio']:.3f}")
            print(f"  Internal ACWR:        {data['trimp_acute_chronic_ratio']:.3f}")
            print(f"  Divergence:           {data['normalized_divergence']:.3f}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    recalculate_all_acwr(user_id=1)
