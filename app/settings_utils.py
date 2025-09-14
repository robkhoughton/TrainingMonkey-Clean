#!/usr/bin/env python3
"""
Settings utilities for Training Monkey - Settings to Analytics Integration

This module handles the critical connection between Settings page changes
and analytics recalculation, ensuring user settings immediately affect their training data.
"""

import logging
from datetime import datetime
from db_utils import execute_query
from strava_training_load import calculate_banister_trimp, update_moving_averages

logger = logging.getLogger(__name__)


def handle_settings_change(user_id, changed_settings, old_values, new_values):
    """
    Handle settings changes and trigger appropriate recalculations.

    This is the MISSING PIECE - Settings page saves but doesn't trigger analytics updates.

    Args:
        user_id (int): User ID for multi-user support
        changed_settings (dict): Fields that changed
        old_values (dict): Previous values
        new_values (dict): New values

    Returns:
        dict: Status of recalculation tasks
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    logger.info(f"Processing settings changes for user {user_id}")
    logger.info(f"Changed fields: {list(changed_settings.keys())}")

    recalculation_tasks = []

    try:
        # Heart rate changes require TRIMP recalculation for ALL activities
        hr_fields = ['resting_hr', 'max_hr', 'hr_zones_method']
        if any(field in changed_settings for field in hr_fields):
            logger.warning(f"Heart rate settings changed - triggering TRIMP recalculation for user {user_id}")

            # Get current complete settings for recalculation
            current_settings = get_complete_user_settings(user_id)
            if current_settings:
                recalc_result = recalculate_trimp_for_user(user_id, current_settings)
                if recalc_result['success']:
                    recalculation_tasks.append(f"TRIMP recalculated for {recalc_result['activity_count']} activities")
                else:
                    recalculation_tasks.append(
                        f"TRIMP recalculation failed: {recalc_result.get('error', 'Unknown error')}")

        # Sport focus affects calculation weights (future enhancement)
        if 'primary_sport' in changed_settings:
            logger.info(f"Primary sport changed to {new_values.get('primary_sport')} for user {user_id}")
            recalculation_tasks.append("Sport focus updated (calculation weights)")

        # ACWR threshold affects alerting
        if 'acwr_alert_threshold' in changed_settings:
            logger.info(f"ACWR threshold changed to {new_values.get('acwr_alert_threshold')} for user {user_id}")
            recalculation_tasks.append("ACWR alert threshold updated")

        return {
            'success': True,
            'user_id': user_id,
            'recalculation_tasks': recalculation_tasks,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error processing settings changes for user {user_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'user_id': user_id,
            'recalculation_tasks': recalculation_tasks  # Include any partial success
        }


def get_complete_user_settings(user_id):
    """
    Get complete user settings for recalculation.

    Args:
        user_id (int): User ID

    Returns:
        dict: Complete user settings or None
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        settings = execute_query(
            """
            SELECT resting_hr, max_hr, hr_zones_method, primary_sport, 
                   acwr_alert_threshold, recommendation_style
            FROM user_settings 
            WHERE id = %s
            """,
            (user_id,),
            fetch=True
        )

        if not settings:
            logger.error(f"No settings found for user {user_id}")
            return None

        return dict(settings[0])

    except Exception as e:
        logger.error(f"Error getting settings for user {user_id}: {str(e)}")
        return None


def recalculate_trimp_for_user(user_id, user_settings):
    """
    Recalculate TRIMP values when heart rate settings change.

    Args:
        user_id (int): User ID
        user_settings (dict): Complete user settings

    Returns:
        dict: Recalculation result
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        # Get current heart rate settings
        resting_hr = user_settings.get('resting_hr')
        max_hr = user_settings.get('max_hr')
        hr_method = user_settings.get('hr_zones_method', 'percentage')

        # Validate required settings
        if not all([resting_hr, max_hr]):
            error_msg = f"Missing HR settings for user {user_id}: resting_hr={resting_hr}, max_hr={max_hr}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg, 'activity_count': 0}

        if resting_hr >= max_hr:
            error_msg = f"Invalid HR settings for user {user_id}: resting ({resting_hr}) >= max ({max_hr})"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg, 'activity_count': 0}

        # Get all activities with heart rate data for this user
        activities = execute_query(
            """
            SELECT activity_id as id, avg_heart_rate as average_heartrate, duration_minutes, date, type
            FROM activities 
            WHERE user_id = %s 
            AND avg_heart_rate IS NOT NULL
            AND avg_heart_rate > 0
            ORDER BY date
            """,
            (user_id,),
            fetch=True
        )

        if not activities:
            logger.warning(f"No activities with HR data found for user {user_id}")
            return {'activity_count': 0, 'success': True, 'message': 'No HR activities to recalculate'}

        logger.info(f"Recalculating TRIMP for {len(activities)} activities for user {user_id}")

        updated_count = 0
        errors = []

        for activity in activities:
            try:
                # Calculate new TRIMP with updated settings
                new_trimp = calculate_trimp_with_settings(
                    activity['average_heartrate'],
                    activity['duration_minutes'] * 60,  # Convert to seconds
                    resting_hr,
                    max_hr,
                    hr_method
                )

                if new_trimp is not None:
                    # Update the activity with new TRIMP
                    execute_query(
                        "UPDATE activities SET %s = %s WHERE activity_id = %s AND user_id = %s",
                        (new_trimp, activity['id'], user_id)
                    )
                    updated_count += 1
                else:
                    errors.append(f"Could not calculate TRIMP for activity {activity['id']}")

            except Exception as e:
                error_msg = f"Error recalculating TRIMP for activity {activity['id']}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        logger.info(f"TRIMP recalculation complete for user {user_id}: {updated_count}/{len(activities)} activities")

        # OPTIMIZED: Trigger moving average recalculation more efficiently
        try:
            logger.info(f"Triggering optimized moving average recalculation for user {user_id}")

            # Call the helper function that recalculates only actual activity dates
            recalculate_all_moving_averages(user_id)

            logger.info(f"Moving average and divergence recalculation completed for user {user_id}")

        except Exception as moving_avg_error:
            logger.error(f"Moving average recalculation failed: {str(moving_avg_error)}")
            # Don't fail the whole operation if moving averages fail
            errors.append(f"Moving average recalculation failed: {str(moving_avg_error)}")

        return {
            'activity_count': updated_count,
            'total_activities': len(activities),
            'success': True,
            'success_rate': (updated_count / len(activities) * 100) if activities else 0,
            'errors': len(errors)
        }

    except Exception as e:
        error_msg = f"Error in TRIMP recalculation for user {user_id}: {str(e)}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'activity_count': 0}


def calculate_trimp_with_settings(avg_hr, duration_seconds, resting_hr, max_hr, hr_method):
    """
    Calculate TRIMP using user-specific heart rate settings.

    Args:
        avg_hr (float): Average heart rate for the activity
        duration_seconds (int): Activity duration in seconds
        resting_hr (int): User's resting heart rate
        max_hr (int): User's maximum heart rate
        hr_method (str): 'percentage' or 'karvonen'/'reserve'

    Returns:
        float: TRIMP value or None if calculation fails
    """
    if not all([avg_hr, duration_seconds, resting_hr, max_hr]):
        return None

    try:
        duration_minutes = duration_seconds / 60

        if hr_method == 'karvonen' or hr_method == 'reserve':
            # Karvonen method: (HR - HRrest) / (HRmax - HRrest)
            hr_reserve = max_hr - resting_hr
            if hr_reserve <= 0:
                logger.warning(f"Invalid HR reserve: {hr_reserve} (max: {max_hr}, rest: {resting_hr})")
                return None
            hr_intensity = max(0, min(1, (avg_hr - resting_hr) / hr_reserve))
        else:
            # Percentage method: HR / HRmax
            hr_intensity = max(0, min(1, avg_hr / max_hr))

        # Banister TRIMP formula
        trimp = duration_minutes * hr_intensity

        return round(trimp, 2)

    except Exception as e:
        logger.error(f"Error calculating TRIMP: {str(e)}")
        return None

def recalculate_all_moving_averages(user_id):
    """
    Efficiently recalculate moving averages and divergence for all user activity dates.
    Only processes dates that actually have activities, not empty days.
    """

    try:
        # Get all unique dates that have activities for this user
        dates = execute_query(
            """
            SELECT DISTINCT date 
            FROM activities 
            WHERE user_id = %s 
            ORDER BY date
            """,
            (user_id,),
            fetch=True
        )

        if not dates:
            logger.warning(f"No activity dates found for user {user_id}")
            return

        logger.info(f"Recalculating moving averages for {len(dates)} activity dates for user {user_id}")

        # Process each date (this automatically recalculates ACWR and divergence)
        for date_row in dates:
            date_str = date_row['date']
            try:
                # This function recalculates:
                # - 7-day and 28-day moving averages
                # - External and Internal ACWR
                # - Normalized divergence
                update_moving_averages(date_str, user_id)

            except Exception as date_error:
                logger.warning(f"Moving average update failed for {date_str}, user {user_id}: {str(date_error)}")
                continue

        logger.info(f"Successfully recalculated moving averages for {len(dates)} dates for user {user_id}")

    except Exception as e:
        logger.error(f"Error in recalculate_all_moving_averages for user {user_id}: {str(e)}")
        raise


def track_settings_changes(old_settings, new_settings):
    """
    Track which settings fields have changed.

    Args:
        old_settings (dict): Previous settings values
        new_settings (dict): New settings values

    Returns:
        dict: Fields that changed with old/new values
    """
    changed_fields = {}

    for key, new_value in new_settings.items():
        old_value = old_settings.get(key)
        if old_value != new_value:
            changed_fields[key] = {
                'old': old_value,
                'new': new_value
            }

    return changed_fields