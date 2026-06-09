#!/usr/bin/env python3
"""
Update user's decay rate and recalculate all ACWR values
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
from optimized_acwr_service import OptimizedACWRService

def update_decay_rate(user_id, new_decay_rate):
    """Update decay rate and recalculate ACWR"""

    print(f"\n{'='*80}")
    print(f"Updating Decay Rate for User {user_id}")
    print(f"{'='*80}\n")

    # Get current config
    current_config = db_utils.execute_query("""
        SELECT chronic_period_days, decay_rate, is_active
        FROM user_dashboard_configs
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY updated_at DESC
        LIMIT 1
    """, (user_id,), fetch=True)

    if current_config:
        old_decay = float(current_config[0]['decay_rate'])
        chronic_days = current_config[0]['chronic_period_days']
        print(f"Current Configuration:")
        print(f"  Chronic Period: {chronic_days} days")
        print(f"  Decay Rate: {old_decay}")
        print(f"\nNew Configuration:")
        print(f"  Chronic Period: {chronic_days} days (unchanged)")
        print(f"  Decay Rate: {new_decay_rate} (changed from {old_decay})")
    else:
        print(f"No active configuration found for user {user_id}")
        return

    # Deactivate existing configs
    print(f"\n1. Deactivating old configurations...")
    db_utils.execute_query("""
        UPDATE user_dashboard_configs
        SET is_active = FALSE, updated_at = NOW()
        WHERE user_id = %s
    """, (user_id,))
    print(f"   Done.")

    # Insert new configuration
    print(f"\n2. Creating new configuration...")
    db_utils.execute_query("""
        INSERT INTO user_dashboard_configs
        (user_id, chronic_period_days, decay_rate, is_active, created_at, updated_at)
        VALUES (%s, %s, %s, TRUE, NOW(), NOW())
    """, (user_id, chronic_days, new_decay_rate))
    print(f"   Done.")

    # Get date range for recalculation (all user's activities)
    print(f"\n3. Finding date range for recalculation...")
    date_range = db_utils.execute_query("""
        SELECT MIN(date) as start_date, MAX(date) as end_date
        FROM activities
        WHERE user_id = %s
    """, (user_id,), fetch=True)

    if date_range:
        start_date = str(date_range[0]['start_date'])
        end_date = str(date_range[0]['end_date'])
        print(f"   Date range: {start_date} to {end_date}")
    else:
        print(f"   No activities found for user {user_id}")
        return

    # Recalculate ACWR for all dates
    print(f"\n4. Recalculating ACWR values with new decay rate...")
    print(f"   This may take a moment...")

    acwr_service = OptimizedACWRService()
    result = acwr_service.recalculate_user_acwr_range(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        chronic_period_days=chronic_days,
        decay_rate=new_decay_rate
    )

    print(f"\n   Recalculation complete!")
    print(f"   Activities processed: {result.get('activities_processed', 0)}")
    print(f"   Updates applied: {result.get('updates_applied', 0)}")

    # Verify new values
    print(f"\n5. Verifying new ACWR values...")
    latest = db_utils.execute_query("""
        SELECT date,
               seven_day_avg_load,
               twentyeight_day_avg_load,
               acute_chronic_ratio,
               trimp_acute_chronic_ratio
        FROM activities
        WHERE user_id = %s
        AND date = %s
        LIMIT 1
    """, (user_id, end_date), fetch=True)

    if latest:
        data = latest[0]
        print(f"\n   Most Recent Date: {data['date']}")
        print(f"   Acute (7-day):    {data['seven_day_avg_load']:.2f} miles/day")
        print(f"   Chronic (42-day): {data['twentyeight_day_avg_load']:.2f} miles/day")
        print(f"   External ACWR:    {data['acute_chronic_ratio']:.3f}")
        print(f"   Internal ACWR:    {data['trimp_acute_chronic_ratio']:.3f}")

    print(f"\n{'='*80}")
    print(f"Update Complete!")
    print(f"{'='*80}\n")

    return result

if __name__ == '__main__':
    user_id = 1
    new_decay_rate = 0.02

    update_decay_rate(user_id, new_decay_rate)
