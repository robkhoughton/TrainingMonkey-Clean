"""
Retroactive Recalculation of Cycling Training Loads
====================================================

Updates existing cycling activities with new research-aligned conversion factors:
- Old: 3.0-3.1 for easy/moderate cycling
- New: 4.0-3.5 for easy/moderate cycling

This script:
1. Finds all cycling activities for a user
2. Recalculates cycling_equivalent_miles using updated factors
3. Updates total_load_miles and affected metrics
4. Triggers ACWR/divergence recalculation

Usage:
    python app/recalculate_cycling_loads.py --user_id 3 --days 30
    python app/recalculate_cycling_loads.py --user_id 3 --all
"""

import sys
import argparse
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load database credentials
from db_credentials_loader import set_database_url
set_database_url()

import db_utils
from db_utils import execute_query

def calculate_new_cycling_conversion_factor(average_speed_mph):
    """
    Calculate cycling conversion factor using NEW research-aligned values.
    
    Based on Dr. Edward Coyle's research (University of Texas).
    """
    if average_speed_mph is None or average_speed_mph <= 12:
        return 4.0  # Leisure cycling (research: 4.2 @ 10mph)
    elif average_speed_mph <= 16:
        return 3.5  # Moderate cycling (research: 3.5 @ 15mph)
    elif average_speed_mph <= 20:
        return 2.9  # Vigorous cycling (research: 2.9 @ 20mph)
    else:
        return 2.4  # Racing pace (research: 2.3-1.9 @ 25-30mph)

def get_old_cycling_conversion_factor(average_speed_mph):
    """
    Get the OLD conversion factor for comparison.
    """
    if average_speed_mph is None or average_speed_mph <= 12:
        return 3.0
    elif average_speed_mph <= 16:
        return 3.1
    elif average_speed_mph <= 20:
        return 2.9
    else:
        return 2.5

def get_cycling_activities(user_id, days_back=None):
    """
    Get all cycling activities for a user, optionally limited by date range.
    
    Args:
        user_id (int): User ID to process
        days_back (int, optional): Limit to last N days. If None, process all.
    
    Returns:
        list: List of cycling activity records
    """
    logger.info(f"Fetching cycling activities for user {user_id}")
    
    if days_back:
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        query = """
            SELECT 
                activity_id,
                date,
                distance_miles,
                elevation_gain_feet,
                duration_minutes,
                cycling_equivalent_miles,
                elevation_load_miles,
                total_load_miles
            FROM activities
            WHERE user_id = %s 
            AND sport_type = 'cycling'
            AND date >= %s
            ORDER BY date DESC
        """
        params = (user_id, cutoff_date)
        logger.info(f"Filtering to activities since {cutoff_date}")
    else:
        query = """
            SELECT 
                activity_id,
                date,
                distance_miles,
                elevation_gain_feet,
                duration_minutes,
                cycling_equivalent_miles,
                elevation_load_miles,
                total_load_miles
            FROM activities
            WHERE user_id = %s 
            AND sport_type = 'cycling'
            ORDER BY date DESC
        """
        params = (user_id,)
        logger.info("Processing ALL cycling activities")
    
    activities = execute_query(query, params, fetch=True)
    logger.info(f"Found {len(activities)} cycling activities to process")
    return activities

def recalculate_cycling_activity(activity, user_id):
    """
    Recalculate a single cycling activity with new conversion factors.
    
    Args:
        activity (dict): Activity record from database
        user_id (int): User ID
    
    Returns:
        dict: Summary of changes
    """
    activity_id = activity['activity_id']
    date = activity['date']
    distance_miles = activity['distance_miles'] or 0
    elevation_gain_feet = activity['elevation_gain_feet'] or 0
    duration_minutes = activity['duration_minutes'] or 0
    
    # Calculate average speed
    if distance_miles > 0 and duration_minutes > 0:
        average_speed_mph = distance_miles / (duration_minutes / 60.0)
    else:
        average_speed_mph = None
    
    # Get old and new conversion factors
    old_factor = get_old_cycling_conversion_factor(average_speed_mph)
    new_factor = calculate_new_cycling_conversion_factor(average_speed_mph)
    
    # Calculate NEW running equivalent distance
    new_running_equiv = distance_miles / new_factor if new_factor > 0 else 0
    
    # Elevation load (unchanged - still uses 1100 ft/mile for cycling)
    CYCLING_ELEVATION_FACTOR = 1100.0
    elevation_load_miles = elevation_gain_feet / CYCLING_ELEVATION_FACTOR
    
    # New total load
    new_total_load = new_running_equiv + elevation_load_miles
    
    # Get old values for comparison
    old_running_equiv = activity['cycling_equivalent_miles'] or 0
    old_total_load = activity['total_load_miles'] or 0
    
    # Calculate changes
    equiv_change = new_running_equiv - old_running_equiv
    total_change = new_total_load - old_total_load
    percent_change = ((new_running_equiv / old_running_equiv) - 1) * 100 if old_running_equiv > 0 else 0
    
    logger.info(f"Activity {activity_id} ({date}, {distance_miles:.1f}mi @ {average_speed_mph:.1f}mph):")
    logger.info(f"  Old factor: {old_factor}, New factor: {new_factor}")
    logger.info(f"  Old equiv: {old_running_equiv:.2f}mi → New equiv: {new_running_equiv:.2f}mi ({equiv_change:+.2f}mi, {percent_change:+.1f}%)")
    logger.info(f"  Old total: {old_total_load:.2f}mi → New total: {new_total_load:.2f}mi ({total_change:+.2f}mi)")
    
    # Update database
    execute_query(
        """
        UPDATE activities 
        SET 
            cycling_equivalent_miles = %s,
            total_load_miles = %s,
            distance_miles = %s
        WHERE activity_id = %s AND user_id = %s
        """,
        (new_running_equiv, new_total_load, new_running_equiv, activity_id, user_id)
    )
    
    return {
        'activity_id': activity_id,
        'date': date,
        'old_factor': old_factor,
        'new_factor': new_factor,
        'old_equiv': old_running_equiv,
        'new_equiv': new_running_equiv,
        'equiv_change': equiv_change,
        'percent_change': percent_change,
        'old_total': old_total_load,
        'new_total': new_total_load,
        'total_change': total_change
    }

def recalculate_user_cycling_loads(user_id, days_back=None):
    """
    Recalculate all cycling activities for a user with new conversion factors.
    
    Args:
        user_id (int): User ID to process
        days_back (int, optional): Limit to last N days. If None, process all.
    
    Returns:
        dict: Summary statistics
    """
    logger.info(f"=== Starting Cycling Load Recalculation for User {user_id} ===")
    
    # Get cycling activities
    activities = get_cycling_activities(user_id, days_back)
    
    if not activities:
        logger.warning(f"No cycling activities found for user {user_id}")
        return {
            'success': True,
            'activities_processed': 0,
            'total_equiv_change': 0,
            'avg_percent_change': 0,
            'message': 'No cycling activities to process'
        }
    
    # Process each activity
    results = []
    total_equiv_change = 0
    factor_changes = {'4.0': 0, '3.5': 0, '2.9': 0, '2.4': 0}
    
    for activity in activities:
        try:
            result = recalculate_cycling_activity(activity, user_id)
            results.append(result)
            total_equiv_change += result['equiv_change']
            
            # Track which factors changed
            if result['old_factor'] != result['new_factor']:
                factor_changes[str(result['new_factor'])] += 1
        
        except Exception as e:
            logger.error(f"Error processing activity {activity['activity_id']}: {e}")
            continue
    
    # Calculate statistics
    activities_processed = len(results)
    avg_percent_change = sum(r['percent_change'] for r in results) / activities_processed if activities_processed > 0 else 0
    
    logger.info(f"\n=== Recalculation Complete ===")
    logger.info(f"Activities processed: {activities_processed}")
    logger.info(f"Total equivalent change: {total_equiv_change:+.2f} miles")
    logger.info(f"Average percent change: {avg_percent_change:+.1f}%")
    logger.info(f"Factor changes breakdown:")
    for factor, count in factor_changes.items():
        if count > 0:
            logger.info(f"  Factor {factor}: {count} activities")
    
    # Trigger ACWR/divergence recalculation
    logger.info("\n=== Recalculating Moving Averages and ACWR ===")
    try:
        from settings_utils import recalculate_all_moving_averages
        recalculate_all_moving_averages(user_id)
        logger.info("Moving averages and ACWR recalculation complete")
    except Exception as e:
        logger.error(f"Error recalculating moving averages: {e}")
    
    return {
        'success': True,
        'activities_processed': activities_processed,
        'total_equiv_change': total_equiv_change,
        'avg_percent_change': avg_percent_change,
        'factor_changes': factor_changes,
        'details': results
    }

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Recalculate cycling activities with new research-aligned conversion factors'
    )
    parser.add_argument('--user_id', type=int, required=True, help='User ID to process')
    parser.add_argument('--days', type=int, help='Process only last N days (default: all)')
    parser.add_argument('--all', action='store_true', help='Process all cycling activities')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without updating database')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.warning("DRY RUN MODE - No database updates will be made")
        # TODO: Implement dry-run mode
        logger.error("Dry-run mode not yet implemented")
        return
    
    days_back = None if args.all else args.days
    
    try:
        result = recalculate_user_cycling_loads(args.user_id, days_back)
        
        if result['success']:
            logger.info(f"\n✅ SUCCESS: Processed {result['activities_processed']} activities")
            logger.info(f"Total load reduction: {abs(result['total_equiv_change']):.2f} miles ({result['avg_percent_change']:+.1f}%)")
        else:
            logger.error("❌ FAILED: Recalculation did not complete successfully")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()




