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


def log_timezone_debug():
    """Log current time information for debugging"""
    utc_now = datetime.now(UTC)
    app_now = get_app_current_datetime()

    logger.info(f"Timezone Debug:")
    logger.info(f"  UTC time: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"  App time: {app_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info(f"  App date: {get_app_current_date()}")