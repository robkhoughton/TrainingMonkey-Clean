#!/usr/bin/env python3
"""
Diagnostic script to investigate external ACWR calculation issue
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

def diagnose_acwr(user_id):
    """Diagnose ACWR calculation for a specific user"""

    print(f"\n{'='*80}")
    print(f"ACWR Diagnostic Report for User {user_id}")
    print(f"{'='*80}\n")

    # Get the most recent activity date
    recent = db_utils.execute_query("""
        SELECT date,
               seven_day_avg_load,
               twentyeight_day_avg_load,
               acute_chronic_ratio,
               seven_day_avg_trimp,
               twentyeight_day_avg_trimp,
               trimp_acute_chronic_ratio,
               normalized_divergence,
               total_load_miles,
               activity_id,
               name,
               type
        FROM activities
        WHERE user_id = %s
        AND date <= CURRENT_DATE
        ORDER BY date DESC
        LIMIT 1
    """, (user_id,), fetch=True)

    if not recent:
        print(f"ERROR: No activities found for user {user_id}")
        return

    latest = recent[0]
    latest_date = latest['date']

    print(f"Most Recent Activity Date: {latest_date}")
    print(f"   Activity: {latest['name']} ({latest['type']})")
    print(f"   Load: {latest['total_load_miles']} miles\n")

    print(f"EXTERNAL (Load-based) Metrics:")
    print(f"  Acute (7-day avg):     {latest['seven_day_avg_load']:.2f} miles/day")
    print(f"  Chronic (28-day avg):  {latest['twentyeight_day_avg_load']:.2f} miles/day")
    print(f"  ACWR (stored):         {latest['acute_chronic_ratio']:.3f}")

    # Verify the math
    if latest['twentyeight_day_avg_load'] > 0:
        calculated_acwr = latest['seven_day_avg_load'] / latest['twentyeight_day_avg_load']
        print(f"  ACWR (calculated):     {calculated_acwr:.3f}")

        if abs(latest['acute_chronic_ratio'] - calculated_acwr) > 0.01:
            print(f"  WARNING: MISMATCH! Stored ({latest['acute_chronic_ratio']:.3f}) != Calculated ({calculated_acwr:.3f})")
    else:
        print(f"  WARNING: Chronic is zero - cannot calculate ACWR")

    print(f"\nINTERNAL (TRIMP-based) Metrics:")
    print(f"  Acute (7-day avg):     {latest['seven_day_avg_trimp']:.2f} TRIMP/day")
    print(f"  Chronic (28-day avg):  {latest['twentyeight_day_avg_trimp']:.2f} TRIMP/day")
    print(f"  ACWR:                  {latest['trimp_acute_chronic_ratio']:.3f}")

    print(f"\nDivergence: {latest['normalized_divergence']:.3f}\n")

    # Now check the raw data used for calculation
    print(f"{'='*80}")
    print(f"RAW DATA VERIFICATION")
    print(f"{'='*80}\n")

    seven_days_ago = (datetime.strptime(str(latest_date), '%Y-%m-%d') - timedelta(days=6)).strftime('%Y-%m-%d')
    twentyeight_days_ago = (datetime.strptime(str(latest_date), '%Y-%m-%d') - timedelta(days=27)).strftime('%Y-%m-%d')

    # 7-day sum
    seven_day_data = db_utils.execute_query("""
        SELECT SUM(total_load_miles) as sum, COUNT(*) as count
        FROM activities
        WHERE user_id = %s
        AND date BETWEEN %s AND %s
    """, (user_id, seven_days_ago, latest_date), fetch=True)

    # 28-day sum
    twentyeight_day_data = db_utils.execute_query("""
        SELECT SUM(total_load_miles) as sum, COUNT(*) as count
        FROM activities
        WHERE user_id = %s
        AND date BETWEEN %s AND %s
    """, (user_id, twentyeight_days_ago, latest_date), fetch=True)

    seven_sum = seven_day_data[0]['sum'] or 0
    seven_count = seven_day_data[0]['count']
    twentyeight_sum = twentyeight_day_data[0]['sum'] or 0
    twentyeight_count = twentyeight_day_data[0]['count']

    print(f"7-Day Window ({seven_days_ago} to {latest_date}):")
    print(f"  Total Load Sum:  {seven_sum:.2f} miles")
    print(f"  Record Count:    {seven_count}")
    print(f"  Average/Day:     {seven_sum / 7:.2f} miles/day")
    print(f"  Stored Average:  {latest['seven_day_avg_load']:.2f} miles/day")
    if abs(seven_sum / 7 - latest['seven_day_avg_load']) > 0.01:
        print(f"  WARNING: MISMATCH!")

    print(f"\n28-Day Window ({twentyeight_days_ago} to {latest_date}):")
    print(f"  Total Load Sum:  {twentyeight_sum:.2f} miles")
    print(f"  Record Count:    {twentyeight_count}")
    print(f"  Average/Day:     {twentyeight_sum / 28:.2f} miles/day")
    print(f"  Stored Average:  {latest['twentyeight_day_avg_load']:.2f} miles/day")
    if abs(twentyeight_sum / 28 - latest['twentyeight_day_avg_load']) > 0.01:
        print(f"  WARNING: MISMATCH!")

    # Show daily breakdown
    print(f"\n{'='*80}")
    print(f"LAST 7 DAYS DETAIL")
    print(f"{'='*80}\n")

    recent_activities = db_utils.execute_query("""
        SELECT date, name, type, total_load_miles, activity_id
        FROM activities
        WHERE user_id = %s
        AND date BETWEEN %s AND %s
        ORDER BY date DESC
    """, (user_id, seven_days_ago, latest_date), fetch=True)

    print(f"{'Date':<12} {'Load (mi)':<12} {'Activity':<30}")
    print(f"{'-'*60}")
    for act in recent_activities:
        print(f"{str(act['date']):<12} {act['total_load_miles']:<12.2f} {act['name'][:28]:<30}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    else:
        user_id = 1  # Default to user 1

    diagnose_acwr(user_id)
