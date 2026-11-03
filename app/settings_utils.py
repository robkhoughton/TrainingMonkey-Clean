#!/usr/bin/env python3
"""
Settings utilities for Training Monkey - Settings to Analytics Integration

This module handles the critical connection between Settings page changes
and analytics recalculation, ensuring user settings immediately affect their training data.
"""

import json
import logging
from datetime import datetime
from db_utils import execute_query
from strava_training_load import compute_activity_trimp, update_moving_averages

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
    """Recalculate every activity's TRIMP after heart rate settings change, then the
    moving averages, ACWR and divergence that depend on it.

    Uses strava_training_load.compute_activity_trimp, the same computation as sync: stream
    TRIMP from the stored HR stream (time-weighted), average-HR TRIMP only for activities
    with no stored stream.
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    resting_hr = user_settings.get('resting_hr')
    max_hr = user_settings.get('max_hr')
    if not resting_hr or not max_hr or resting_hr >= max_hr:
        error_msg = f"Invalid HR settings for user {user_id}: resting_hr={resting_hr}, max_hr={max_hr}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'activity_count': 0}

    gender_row = execute_query("SELECT gender FROM user_settings WHERE id = %s", (user_id,), fetch=True)
    hr_config = {
        'resting_hr': resting_hr,
        'max_hr': max_hr,
        'gender': (gender_row[0].get('gender') if gender_row else None) or 'male',
    }

    activities = execute_query(
        """
        SELECT a.activity_id, a.duration_minutes, a.avg_heart_rate, s.hr_data, s.time_data
        FROM activities a
        LEFT JOIN LATERAL (
            SELECT hr_data, time_data FROM hr_streams h
            WHERE h.activity_id = a.activity_id AND h.user_id = a.user_id
            ORDER BY h.created_at DESC LIMIT 1
        ) s ON TRUE
        WHERE a.user_id = %s AND a.activity_id > 0
          AND (s.hr_data IS NOT NULL OR a.avg_heart_rate > 0)
        """,
        (user_id,),
        fetch=True
    ) or []

    updated = 0
    for a in activities:
        hr_data, time_data = a['hr_data'], a['time_data']
        hr_data = json.loads(hr_data) if isinstance(hr_data, str) else hr_data
        time_data = json.loads(time_data) if isinstance(time_data, str) else time_data
        trimp, method, sample_count = compute_activity_trimp(
            float(a['duration_minutes'] or 0), float(a['avg_heart_rate'] or 0), hr_config,
            hr_data, time_data)
        execute_query(
            """UPDATE activities SET trimp = %s, trimp_calculation_method = %s,
                      hr_stream_sample_count = %s, trimp_processed_at = NOW()
               WHERE activity_id = %s AND user_id = %s""",
            (trimp, method, sample_count, a['activity_id'], user_id)
        )
        updated += 1
    logger.info(f"TRIMP recalculated for {updated} activities for user {user_id}")

    recalculate_all_moving_averages(user_id)
    return {'activity_count': updated, 'total_activities': len(activities), 'success': True}


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


def calculate_age_from_birthdate(birthdate):
    """
    Calculate age from birthdate.
    
    Args:
        birthdate: Date object, string in 'YYYY-MM-DD' format, or None
        
    Returns:
        int: Age in years, or None if birthdate is invalid
    """
    if birthdate is None:
        return None
        
    try:
        from datetime import date
        
        # Handle string input
        if isinstance(birthdate, str):
            birthdate = datetime.strptime(birthdate, '%Y-%m-%d').date()
        
        # Get today's date
        today = date.today()
        
        # Calculate age
        age = today.year - birthdate.year
        
        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            age -= 1
            
        return age
        
    except (ValueError, TypeError, AttributeError) as e:
        logger.error(f"Error calculating age from birthdate {birthdate}: {str(e)}")
        return None


def get_user_age(user_id):
    """
    Get user's current age from their birthdate.
    Falls back to age field if birthdate is not set.
    
    Args:
        user_id (int): User ID
        
    Returns:
        int: User's age, or None if neither birthdate nor age is available
    """
    if user_id is None:
        raise ValueError("user_id is required")
        
    try:
        result = execute_query(
            "SELECT birthdate, age FROM user_settings WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        if not result:
            logger.error(f"No user found with id {user_id}")
            return None
            
        user_data = result[0]
        birthdate = user_data.get('birthdate')
        age = user_data.get('age')
        
        # Try birthdate first
        if birthdate:
            calculated_age = calculate_age_from_birthdate(birthdate)
            if calculated_age is not None:
                return calculated_age
        
        # Fall back to stored age
        return age
        
    except Exception as e:
        logger.error(f"Error getting user age for user {user_id}: {str(e)}")
        return None