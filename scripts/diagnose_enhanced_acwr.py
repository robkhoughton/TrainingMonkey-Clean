#!/usr/bin/env python3
"""
Diagnostic script for Enhanced ACWR with custom config
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from datetime import datetime, timedelta

# Load database credentials BEFORE importing db_utils
from db_credentials_loader import set_database_url
set_database_url()

# Now import db_utils
import db_utils

def calculate_enhanced_chronic(user_id, target_date, chronic_period_days=42, decay_rate=0.05):
    """Calculate what the enhanced chronic average SHOULD be"""

    print(f"\n{'='*80}")
    print(f"Enhanced ACWR Calculation Verification")
    print(f"User: {user_id} | Date: {target_date}")
    print(f"Config: {chronic_period_days}-day chronic, {decay_rate} decay rate")
    print(f"{'='*80}\n")

    # Get activities for the chronic period
    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
    chronic_start = (date_obj - timedelta(days=chronic_period_days-1)).strftime('%Y-%m-%d')

    activities = db_utils.execute_query("""
        SELECT date, total_load_miles, trimp
        FROM activities
        WHERE user_id = %s
        AND date BETWEEN %s AND %s
        ORDER BY date DESC
    """, (user_id, chronic_start, target_date), fetch=True)

    print(f"Chronic Window: {chronic_start} to {target_date} ({chronic_period_days} days)")
    print(f"Activities found: {len(activities)}\n")

    # Calculate exponential weights
    total_weighted_load = 0
    total_weight = 0
    total_raw_load = 0

    print(f"{'Date':<12} {'Load':<10} {'Days Ago':<10} {'Weight':<12} {'Weighted':<12}")
    print(f"{'-'*66}")

    for activity in activities:
        act_date = datetime.strptime(str(activity['date']), '%Y-%m-%d')
        days_ago = (date_obj - act_date).days

        # Exponential decay weight: exp(-decay_rate * days_ago)
        import math
        weight = math.exp(-decay_rate * days_ago)

        weighted_load = activity['total_load_miles'] * weight
        total_weighted_load += weighted_load
        total_weight += weight
        total_raw_load += activity['total_load_miles']

        print(f"{str(activity['date']):<12} {activity['total_load_miles']:<10.2f} {days_ago:<10} {weight:<12.4f} {weighted_load:<12.2f}")

    # Calculate weighted average
    if total_weight > 0:
        enhanced_chronic_avg = total_weighted_load / total_weight
    else:
        enhanced_chronic_avg = 0

    # Simple average for comparison
    simple_avg = total_raw_load / chronic_period_days if chronic_period_days > 0 else 0

    print(f"\n{'='*80}")
    print(f"CALCULATION RESULTS:")
    print(f"{'='*80}")
    print(f"Total Raw Load Sum:        {total_raw_load:.2f} miles")
    print(f"Total Weighted Load Sum:   {total_weighted_load:.2f}")
    print(f"Total Weight Sum:          {total_weight:.4f}")
    print(f"\nSimple {chronic_period_days}-day average:   {simple_avg:.2f} miles/day")
    print(f"Enhanced weighted average: {enhanced_chronic_avg:.2f} miles/day")

    # Get what's actually stored
    stored = db_utils.execute_query("""
        SELECT twentyeight_day_avg_load, acute_chronic_ratio
        FROM activities
        WHERE user_id = %s AND date = %s
        LIMIT 1
    """, (user_id, target_date), fetch=True)

    if stored:
        stored_chronic = stored[0]['twentyeight_day_avg_load']
        stored_acwr = stored[0]['acute_chronic_ratio']
        print(f"\nSTORED in database:        {stored_chronic:.2f} miles/day")
        print(f"STORED ACWR:               {stored_acwr:.3f}")

        if abs(stored_chronic - enhanced_chronic_avg) > 0.01:
            print(f"\nWARNING: MISMATCH!")
            print(f"Expected: {enhanced_chronic_avg:.2f}")
            print(f"Stored:   {stored_chronic:.2f}")
            print(f"Difference: {stored_chronic - enhanced_chronic_avg:.2f} miles/day")

    print(f"\n{'='*80}\n")

    return enhanced_chronic_avg

if __name__ == '__main__':
    calculate_enhanced_chronic(1, '2025-12-13', 42, 0.05)
