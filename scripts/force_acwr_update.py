#!/usr/bin/env python3
"""
Force update ACWR by directly calling calculation service
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from datetime import datetime

# Load database credentials BEFORE importing db_utils
from db_credentials_loader import set_database_url
set_database_url()

# Now import modules
import db_utils
from acwr_configuration_service import ACWRConfigurationService

def force_update_acwr(user_id, date_str):
    """Force update ACWR for a specific date"""

    print(f"\nForce updating ACWR for user {user_id}, date {date_str}\n")

    # Create a fresh instance of the service
    config_service = ACWRConfigurationService()

    # Get the user's current configuration directly from database
    config_result = db_utils.execute_query("""
        SELECT chronic_period_days, decay_rate, is_active
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
        'is_active': config_result[0]['is_active']
    }

    print(f"Using config: {config}")

    # Calculate enhanced ACWR directly
    result = config_service.calculate_enhanced_acwr(user_id, date_str, config)

    if not result['success']:
        print(f"Calculation failed: {result.get('error', 'Unknown error')}")
        return

    # Extract values
    seven_day_avg_load = result['acute_load_avg']
    chronic_avg_load = result['enhanced_chronic_load']
    seven_day_avg_trimp = result.get('acute_trimp_avg', 0.0)
    chronic_avg_trimp = result.get('enhanced_chronic_trimp', 0.0)
    external_acwr = result['enhanced_acute_chronic_ratio']
    internal_acwr = result.get('enhanced_trimp_acute_chronic_ratio', 0.0)
    divergence = result.get('enhanced_normalized_divergence', 0.0)

    print(f"\nCalculated values:")
    print(f"  Acute (7-day):    {seven_day_avg_load:.2f} miles/day")
    print(f"  Chronic (42-day): {chronic_avg_load:.2f} miles/day")
    print(f"  External ACWR:    {external_acwr:.3f}")
    print(f"  Internal ACWR:    {internal_acwr:.3f}")
    print(f"  Divergence:       {divergence:.3f}")

    # Update database
    print(f"\nUpdating database...")
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
    """, (seven_day_avg_load, chronic_avg_load, seven_day_avg_trimp, chronic_avg_trimp,
          external_acwr, internal_acwr, divergence, user_id, date_str))

    print(f"Database updated!\n")

    # Verify
    verify = db_utils.execute_query("""
        SELECT acute_chronic_ratio, twentyeight_day_avg_load
        FROM activities
        WHERE user_id = %s AND date = %s
    """, (user_id, date_str), fetch=True)

    if verify:
        print(f"Verified in database:")
        print(f"  External ACWR:    {verify[0]['acute_chronic_ratio']:.3f}")
        print(f"  Chronic (42-day): {verify[0]['twentyeight_day_avg_load']:.2f} miles/day\n")

if __name__ == '__main__':
    force_update_acwr(1, '2025-12-13')
