#!/usr/bin/env python3
"""
Recalculate last 60 days using direct calculation method
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
from acwr_configuration_service import ACWRConfigurationService

def recalculate_60_days(user_id, days_back=60):
    """Recalculate ACWR for last 60 days using direct method"""

    print(f"\n{'='*80}")
    print(f"Recalculating Last {days_back} Days with New Decay Rate")
    print(f"{'='*80}\n")

    # Get config
    config_result = db_utils.execute_query("""
        SELECT chronic_period_days, decay_rate
        FROM user_dashboard_configs
        WHERE user_id = %s AND is_active = TRUE
        ORDER BY updated_at DESC
        LIMIT 1
    """, (user_id,), fetch=True)

    if not config_result:
        print("No active config found!")
        return

    config = {
        'chronic_period_days': config_result[0]['chronic_period_days'],
        'decay_rate': float(config_result[0]['decay_rate']),
        'is_active': True
    }

    print(f"Config: {config['chronic_period_days']}-day chronic, {config['decay_rate']} decay\n")

    # Get dates to process
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days_back)

    dates = db_utils.execute_query("""
        SELECT DISTINCT date
        FROM activities
        WHERE user_id = %s
        AND date >= %s
        ORDER BY date ASC
    """, (user_id, start_date.strftime('%Y-%m-%d')), fetch=True)

    total = len(dates)
    print(f"Processing {total} dates from {start_date} to {end_date}\n")

    # Create service instance
    config_service = ACWRConfigurationService()

    processed = 0
    errors = 0

    for i, row in enumerate(dates):
        date_str = str(row['date'])

        print(f"[{i+1}/{total}] {date_str}...", end='\r')

        try:
            # Calculate
            result = config_service.calculate_enhanced_acwr(user_id, date_str, config)

            if not result['success']:
                print(f"\n  Error: {result.get('error', 'Unknown')}")
                errors += 1
                continue

            # Update database
            db_utils.execute_query("""
                UPDATE activities
                SET seven_day_avg_load = %s,
                    twentyeight_day_avg_load = %s,
                    seven_day_avg_trimp = %s,
                    twentyeight_day_avg_trimp = %s,
                    acute_chronic_ratio = %s,
                    trimp_acute_chronic_ratio = %s,
                    normalized_divergence = %s
                WHERE user_id = %s AND date = %s
            """, (
                result['acute_load_avg'],
                result['enhanced_chronic_load'],
                result.get('acute_trimp_avg', 0.0),
                result.get('enhanced_chronic_trimp', 0.0),
                result['enhanced_acute_chronic_ratio'],
                result.get('enhanced_trimp_acute_chronic_ratio', 0.0),
                result.get('enhanced_normalized_divergence', 0.0),
                user_id,
                date_str
            ))

            processed += 1

        except Exception as e:
            print(f"\n  Exception on {date_str}: {str(e)}")
            errors += 1

    print(f"\n\n{'='*80}")
    print(f"Recalculation Complete!")
    print(f"{'='*80}")
    print(f"Processed: {processed}/{total}")
    print(f"Errors: {errors}")

    # Show final values
    if dates:
        latest = str(dates[-1]['date'])
        verify = db_utils.execute_query("""
            SELECT acute_chronic_ratio, twentyeight_day_avg_load,
                   trimp_acute_chronic_ratio, normalized_divergence
            FROM activities
            WHERE user_id = %s AND date = %s
        """, (user_id, latest), fetch=True)

        if verify:
            v = verify[0]
            print(f"\nMost Recent Date: {latest}")
            print(f"  External ACWR:    {v['acute_chronic_ratio']:.3f}")
            print(f"  Chronic (42-day): {v['twentyeight_day_avg_load']:.2f} miles/day")
            print(f"  Internal ACWR:    {v['trimp_acute_chronic_ratio']:.3f}")
            print(f"  Divergence:       {v['normalized_divergence']:.3f}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    recalculate_60_days(user_id=1, days_back=60)
