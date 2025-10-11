# timezone_utils.py
# Create this new file to handle timezone conversions consistently

import pytz
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Define the app's primary timezone (Pacific)
APP_TIMEZONE = pytz.timezone('US/Pacific')
UTC = pytz.UTC


def get_app_current_date():
    """Get the current date in the app's timezone (Pacific)"""
    utc_now = datetime.now(UTC)
    app_now = utc_now.astimezone(APP_TIMEZONE)
    return app_now.date()


def get_app_current_datetime():
    """Get the current datetime in the app's timezone (Pacific)"""
    utc_now = datetime.now(UTC)
    return utc_now.astimezone(APP_TIMEZONE)


def get_app_date_string():
    """Get the current date as YYYY-MM-DD string in the app's timezone"""
    return get_app_current_date().strftime('%Y-%m-%d')


def get_user_current_date(user_id):
    """
    Get the current date for a specific user based on their timezone preference.
    Falls back to app timezone (Pacific) if user timezone not set.
    """
    try:
        user_tz = get_user_timezone(user_id)
        utc_now = datetime.now(UTC)
        user_now = utc_now.astimezone(user_tz)
        return user_now.date()
    except Exception as e:
        logger.warning(f"Error getting user timezone for user {user_id}: {str(e)}, falling back to app timezone")
        return get_app_current_date()


def get_user_timezone(user_id):
    """
    Get the timezone for a specific user from the database.
    Returns pytz timezone object. Falls back to Pacific timezone if not set.
    Uses caching to avoid excessive database queries.
    """
    # Check cache first
    cache_key = f"user_tz_{user_id}"
    if cache_key in _timezone_cache:
        return _timezone_cache[cache_key]
    
    try:
        from db_utils import execute_query
        
        result = execute_query("""
            SELECT timezone 
            FROM user_settings 
            WHERE id = %s
        """, (user_id,), fetch=True)
        
        if result and len(result) > 0:
            tz_string = result[0].get('timezone', 'US/Pacific')
        else:
            tz_string = 'US/Pacific'
        
        # Validate and convert to pytz timezone
        try:
            user_tz = pytz.timezone(tz_string)
            _timezone_cache[cache_key] = user_tz
            logger.debug(f"User {user_id} timezone: {tz_string}")
            return user_tz
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Invalid timezone '{tz_string}' for user {user_id}, using Pacific")
            user_tz = APP_TIMEZONE
            _timezone_cache[cache_key] = user_tz
            return user_tz
            
    except Exception as e:
        logger.error(f"Error fetching timezone for user {user_id}: {str(e)}")
        return APP_TIMEZONE


# Timezone cache to avoid excessive database queries
_timezone_cache = {}


def clear_timezone_cache(user_id=None):
    """Clear timezone cache for a specific user or all users."""
    global _timezone_cache
    if user_id is not None:
        cache_key = f"user_tz_{user_id}"
        if cache_key in _timezone_cache:
            del _timezone_cache[cache_key]
            logger.info(f"Cleared timezone cache for user {user_id}")
    else:
        _timezone_cache = {}
        logger.info("Cleared all timezone cache")


def validate_timezone(tz_string):
    """Validate that a timezone string is a valid US timezone."""
    try:
        tz = pytz.timezone(tz_string)
        # Validate it's a US timezone
        us_timezones = [
            'US/Alaska', 'US/Aleutian', 'US/Arizona', 'US/Central', 
            'US/East-Indiana', 'US/Eastern', 'US/Hawaii', 'US/Indiana-Starke',
            'US/Michigan', 'US/Mountain', 'US/Pacific', 'US/Samoa',
            'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles',
            'America/Phoenix', 'America/Anchorage', 'America/Honolulu'
        ]
        return tz_string in us_timezones
    except pytz.exceptions.UnknownTimeZoneError:
        return False


def is_date_in_past(date_str, timezone_name='US/Pacific'):
    """Check if a date string is in the past relative to the specified timezone"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        tz = pytz.timezone(timezone_name)
        current_date = datetime.now(tz).date()
        return target_date < current_date
    except Exception as e:
        logger.error(f"Error comparing dates: {str(e)}")
        return False


def is_date_today(date_str, timezone_name='US/Pacific'):
    """Check if a date string is today in the specified timezone"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        tz = pytz.timezone(timezone_name)
        current_date = datetime.now(tz).date()
        return target_date == current_date
    except Exception as e:
        logger.error(f"Error comparing dates: {str(e)}")
        return False


def get_date_range_for_sync(days_back=7):
    """FIXED: Always end with yesterday, never include today"""
    end_date = get_app_current_date() - timedelta(days=1)  # YESTERDAY
    start_date = end_date - timedelta(days=days_back-1)
    return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


def should_create_rest_day(date_str):
    """
    Determine if we should create a rest day for a given date.
    Only create rest days for dates that are actually in the past.
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        current_date = get_app_current_date()

        # Only create rest days for dates that are completely in the past
        # Don't create for today or future dates
        return target_date < current_date

    except Exception as e:
        logger.error(f"Error checking rest day creation for {date_str}: {str(e)}")
        return False


def should_create_rest_day_for_user(user_id, date_str):
    """
    Determine if we should create a rest day for a given user and date.
    User-specific version of should_create_rest_day for multi-user support.
    """
    # Currently uses same logic as should_create_rest_day
    # Future: Could incorporate user-specific timezone preferences
    return should_create_rest_day(date_str)


def log_timezone_debug():
    """Log current time information for debugging"""
    utc_now = datetime.now(UTC)
    app_now = get_app_current_datetime()

    logger.info(f"Timezone Debug:")
    logger.info(f"  UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"  App time: {app_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"  App date: {get_app_current_date()}")