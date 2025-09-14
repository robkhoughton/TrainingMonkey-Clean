#!/usr/bin/env python3
"""
Garmin Connect Training Load Tracker with Banister TRIMP and Wellness Metrics
-----------------------------------
This script automatically fetches your activities from Garmin Connect,
calculates a custom training load metric that accounts for elevation gain/loss,
adds Banister TRIMP calculation based on heart rate data, and saves the results to a database.
It also retrieves wellness metrics such as weight, perceived effort, and feeling scores.
"""

import os
import json
import logging
import time
import pandas as pd
import numpy as np
import argparse
from datetime import datetime, timedelta
from db_utils import get_db_connection, execute_query, initialize_db, DB_FILE
from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectAuthenticationError,
    GarminConnectTooManyRequestsError,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='garmin_training_load.log'
)
logger = logging.getLogger('garmin_training_load')

# Configuration
CONFIG_FILE = 'garmin_config.json'
MAX_RETRIES = 5
RETRY_DELAY = 60  # seconds

# Get database file path from db_utils
from db_utils import DB_FILE

# Activity types to include (empty list means include all)
ACTIVITY_TYPES = []  # Empty list means include all activity types

# Unit conversion constants
METERS_TO_FEET = 3.28084
KILOMETERS_TO_MILES = 0.621371

# Default HR parameters - will be overridden by user input
DEFAULT_RESTING_HR = 44
DEFAULT_MAX_HR = 178
DEFAULT_GENDER = 'male'

def load_config():
    """Load configuration from JSON file or environment variables."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)

                # Check if HR parameters exist in config
                if 'resting_hr' not in config or 'max_hr' not in config or 'gender' not in config:
                    logger.warning("HR parameters missing from config file")
                    hr_config = None
                else:
                    hr_config = {
                        'resting_hr': config.get('resting_hr', DEFAULT_RESTING_HR),
                        'max_hr': config.get('max_hr', DEFAULT_MAX_HR),
                        'gender': config.get('gender', DEFAULT_GENDER)
                    }

                return (
                    config.get('email'),
                    config.get('password'),
                    hr_config
                )
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            return None, None, None
    else:
        # Try environment variables
        email = os.environ.get('GARMIN_EMAIL')
        password = os.environ.get('GARMIN_PASSWORD')

        if email and password:
            # Check if HR parameters exist in environment
            if 'GARMIN_RESTING_HR' in os.environ and 'GARMIN_MAX_HR' in os.environ:
                hr_config = {
                    'resting_hr': int(os.environ.get('GARMIN_RESTING_HR')),
                    'max_hr': int(os.environ.get('GARMIN_MAX_HR')),
                    'gender': os.environ.get('GARMIN_GENDER', DEFAULT_GENDER)
                }
            else:
                hr_config = None

            return email, password, hr_config
        else:
            logger.error("No configuration found. Create a garmin_config.json file or set environment variables.")
            return None, None, None


def setup_hr_parameters():
    """Set up heart rate parameters for Banister TRIMP calculation."""
    print("\nEnter heart rate parameters for Banister TRIMP calculation:")

    try:
        resting_hr = int(input(f"Resting heart rate (bpm) [{DEFAULT_RESTING_HR}]: ") or DEFAULT_RESTING_HR)
        max_hr = int(input(f"Maximum heart rate (bpm) [{DEFAULT_MAX_HR}]: ") or DEFAULT_MAX_HR)

        gender = input(
            f"Gender for TRIMP calculation (male/female) [{DEFAULT_GENDER}]: ").lower().strip() or DEFAULT_GENDER
        gender = 'male' if gender not in ['female', 'f'] else 'female'

        print(f"\nUsing: Resting HR = {resting_hr} bpm, Max HR = {max_hr} bpm, Gender = {gender}")

        return {
            'resting_hr': resting_hr,
            'max_hr': max_hr,
            'gender': gender
        }
    except Exception as e:
        logger.error(f"Error setting up HR parameters: {str(e)}")
        print(f"Error: {str(e)}. Using default values.")
        return {
            'resting_hr': DEFAULT_RESTING_HR,
            'max_hr': DEFAULT_MAX_HR,
            'gender': DEFAULT_GENDER
        }


def save_config(email, password, hr_config=None):
    """Save configuration to JSON file."""
    if hr_config is None:
        hr_config = {
            'resting_hr': DEFAULT_RESTING_HR,
            'max_hr': DEFAULT_MAX_HR,
            'gender': DEFAULT_GENDER
        }

    config_data = {
        'email': email,
        'password': password,
        'resting_hr': hr_config['resting_hr'],
        'max_hr': hr_config['max_hr'],
        'gender': hr_config['gender']
    }

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f)
        # Set file permissions to be readable only by owner
        os.chmod(CONFIG_FILE, 0o600)
        logger.info("Configuration saved successfully")
        print("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        print(f"Error saving configuration: {str(e)}")


def connect_to_garmin(email, password):
    """Connect to Garmin Connect with retry logic."""
    api = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Connecting to Garmin Connect (Attempt {attempt + 1}/{MAX_RETRIES})")
            api = Garmin(email, password)
            api.login()

            # Verify connection
            user_name = api.get_full_name()
            logger.info(f"Connected as {user_name}")
            return api

        except (GarminConnectConnectionError, GarminConnectAuthenticationError,
                GarminConnectTooManyRequestsError) as e:
            logger.error(f"Error connecting to Garmin: {str(e)}")
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Unable to connect to Garmin.")
                return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None


def get_activities(api, start_date, end_date=None):
    """
    Fetches activities from Garmin Connect API for a given date range using get_activities_by_date.
    This is generally more reliable for fetching specific date ranges.
    """
    if end_date is None:
        end_date = start_date

    logger.info(f"Attempting to fetch activities for date range: {start_date} to {end_date} using get_activities_by_date.")

    try:
        # Use get_activities_by_date as it's designed for specific date ranges
        activities = api.get_activities_by_date(start_date, end_date)

        logger.info(f"API response type for get_activities_by_date: {type(activities)}")

        # get_activities_by_date is expected to return a list, but we'll still check for robustness
        if isinstance(activities, list):
            logger.info(f"Received a list of {len(activities)} activities from get_activities_by_date.")
            # No further filtering by date is explicitly needed here as the API call already does it
            # However, you might still want to apply ACTIVITY_TYPES filter.
            filtered_activities = activities
        elif isinstance(activities, dict):
            logger.warning("Received a dictionary from get_activities_by_date. This is unexpected for this method.")
            logger.info(f"Full API response content (if dict, first 500 chars): {json.dumps(activities, indent=4)[:500]}")
            logger.info("Please inspect the full dictionary logged above if activities are not found.")

            # Attempt to find the list of activities within the dictionary if it unexpectedly returns one
            if 'activities' in activities and isinstance(activities['activities'], list):
                logger.info("Found 'activities' key with a list within the dictionary response (unexpected but handled).")
                filtered_activities = activities['activities']
            else:
                logger.warning("API response is a dictionary, but no recognizable activity list found under 'activities' key. Returning empty list.")
                return []
        else:
            logger.error(f"Unexpected API response type from get_activities_by_date: {type(activities)}. Returning empty list.")
            return []

        logger.info(f"Found {len(filtered_activities)} relevant activities from the API call.")

        # Apply ACTIVITY_TYPES filter if specified
        if ACTIVITY_TYPES:
            initial_count = len(filtered_activities)
            filtered_activities = [
                activity for activity in filtered_activities
                if activity.get('activityType', {}).get('typeKey', '').lower() in ACTIVITY_TYPES
            ]
            logger.info(f"Filtered down to {len(filtered_activities)} activities after applying ACTIVITY_TYPES filter (removed {initial_count - len(filtered_activities)} activities).")

        return filtered_activities

    except GarminConnectConnectionError as e:
        logger.error(f"Garmin Connect Connection Error: {e}")
        return []
    except GarminConnectAuthenticationError as e:
        logger.error(f"Garmin Connect Authentication Error: {e}. Please check your credentials.")
        return []
    except GarminConnectTooManyRequestsError as e:
        logger.warning(f"Garmin Connect Too Many Requests Error: {e}. Waiting and retrying...")
        # Implement retry logic if needed
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching activities: {e}", exc_info=True)
        return []

def get_detailed_activity(api, activity_id):
    """Get detailed activity data for a specific activity."""
    try:
        logger.info(f"Fetching detailed data for activity {activity_id}")
        # Get the full activity details
        detailed = api.get_activity(activity_id)
        if detailed:
            logger.info(f"Successfully fetched detailed data for activity {activity_id}")
            # Log sample of the data to help with debugging
            if 'averageHR' in detailed:
                logger.info(f"Average HR: {detailed['averageHR']}")
            if 'maxHR' in detailed:
                logger.info(f"Max HR: {detailed['maxHR']}")

        return detailed
    except Exception as e:
        logger.error(f"Error fetching activity details: {str(e)}")
        return None


def get_activity_heart_rate_data(api, activity_id):
    """
    Get heart rate data for an activity using various API methods.
    Tries multiple methods to ensure we get data.
    """
    try:
        # First try to get the heart rate time in zones
        logger.info(f"Fetching heart rate zone data for activity {activity_id}")
        try:
            # Most direct method, if available
            hr_zones_data = api.get_activity_hr_in_timezones(activity_id)
            if hr_zones_data and 'heartRateZones' in hr_zones_data:
                logger.info(f"Successfully fetched HR zone data via get_activity_hr_in_timezones")
                return hr_zones_data
        except Exception as zone_e:
            logger.warning(f"Error getting HR zones via get_activity_hr_in_timezones: {str(zone_e)}")

        # If that fails, try the activity details themselves
        logger.info(f"Trying to get HR data from activity details")
        activity_details = api.get_activity(activity_id)

        # If HR data exists in activity details
        if activity_details and ('averageHR' in activity_details or 'maxHR' in activity_details):
            # Create a simplified zones structure
            hr_data = {
                'heartRateZones': [],
                'averageHR': activity_details.get('averageHR', 0),
                'maxHR': activity_details.get('maxHR', 0)
            }
            logger.info(f"Using HR data from activity details: avg={hr_data['averageHR']}, max={hr_data['maxHR']}")
            return hr_data

        # Try stats API as last resort
        logger.info(f"Trying to get HR data from activity stats")
        try:
            activity_stats = api.get_activity_stats(activity_id)
            if activity_stats and 'heartRateValues' in activity_stats:
                # Process heartRateValues into a simplified format
                hr_values = activity_stats['heartRateValues']
                if hr_values and len(hr_values) > 0:
                    # Calculate average HR from the values
                    hr_list = [v[1] for v in hr_values if v[1] > 0]
                    avg_hr = sum(hr_list) / len(hr_list) if len(hr_list) > 0 else 0
                    max_hr = max(hr_list) if len(hr_list) > 0 else 0

                    hr_data = {
                        'heartRateZones': [],
                        'averageHR': avg_hr,
                        'maxHR': max_hr
                    }
                    logger.info(f"Using HR data from activity stats: avg={avg_hr}, max={max_hr}")
                    return hr_data
        except Exception as stats_e:
            logger.warning(f"Error getting HR data from stats: {str(stats_e)}")

        logger.warning(f"Could not get heart rate data for activity {activity_id}")
        return None
    except Exception as e:
        logger.error(f"Error fetching any heart rate data: {str(e)}")
        return None


def get_activity_hr_time_in_zones(api, activity_id):
    """Get time spent in each heart rate zone for an activity."""
    try:
        logger.info(f"Fetching heart rate zone data for activity {activity_id}")

        # The direct endpoint should work based on your JSON data
        hr_zones_data = api.get_activity_hr_in_timezones(activity_id)

        # Check if we got valid data - in your case it should be an array of zone objects
        if hr_zones_data and isinstance(hr_zones_data, list) and len(hr_zones_data) > 0:
            logger.info(f"Successfully fetched HR zone data for activity {activity_id}")
            # Log the first zone to verify format
            logger.info(f"Sample zone data: {hr_zones_data[0]}")
            return hr_zones_data
        else:
            logger.warning(f"Retrieved empty or invalid HR zone data for activity {activity_id}")
            return None

    except Exception as e:
        logger.error(f"Error fetching heart rate zone data: {str(e)}")
        return None


def calculate_banister_trimp(duration_minutes, avg_hr, resting_hr, max_hr, gender='male'):
    """
    Calculate Banister TRIMP (Training Impulse) using the exponential heart rate weighting.

    TRIMP = duration (minutes) × HRR × 0.64e^(k × HRR)
    where:
        - HRR = (avg_hr - resting_hr) / (max_hr - resting_hr)
        - k = 1.92 for males and 1.67 for females
        - e = base of natural logarithm
    """
    try:
        # Validate inputs
        if avg_hr <= 0 or duration_minutes <= 0:
            logger.warning(f"Invalid HR or duration: avg_hr={avg_hr}, duration={duration_minutes}")
            return 0

        if max_hr <= resting_hr:
            logger.warning(f"Invalid HR range: max_hr={max_hr}, resting_hr={resting_hr}")
            return 0

        # Set gender constant
        k = 1.92 if gender.lower() == 'male' else 1.67

        # Calculate heart rate reserve (HRR) as a fraction
        hr_reserve = (avg_hr - resting_hr) / (max_hr - resting_hr)

        # Ensure HR reserve is within valid range (0-1)
        hr_reserve = max(0, min(1, hr_reserve))

        # Calculate TRIMP using Banister's formula
        trimp = duration_minutes * hr_reserve * 0.64 * np.exp(k * hr_reserve)

        trimp_rounded = round(trimp, 2)
        logger.info(
            f"Calculated Banister TRIMP: {trimp_rounded} (duration={duration_minutes}, avg_hr={avg_hr}, HRR={hr_reserve:.2f})")
        return trimp_rounded
    except Exception as e:
        logger.error(f"Error calculating Banister TRIMP: {str(e)}")
        return 0

def calculate_training_load(activity, api, hr_config=None):
    """
    Calculate custom training load based on distance, elevation, and Banister TRIMP.
    Returns a dictionary with the load calculation and activity details.
    """
    if hr_config is None:
        hr_config = {
            'resting_hr': DEFAULT_RESTING_HR,
            'max_hr': DEFAULT_MAX_HR,
            'gender': DEFAULT_GENDER
        }

    # Extract base metrics
    activity_id = activity.get('activityId')
    activity_date = activity.get('startTimeLocal', '').split(' ')[0] if 'startTimeLocal' in activity else None
    activity_name = activity.get('activityName', '')

    # Handle different activity structures
    if 'activityType' in activity and isinstance(activity['activityType'], dict):
        activity_type = activity['activityType'].get('typeKey', '')
    elif 'activityTypeDTO' in activity and isinstance(activity['activityTypeDTO'], dict):
        activity_type = activity['activityTypeDTO'].get('typeKey', '')
    else:
        activity_type = ''

    # Get distance, elevation, and duration - check both structures
    distance = 0
    elevation_gain = 0
    duration_seconds = 0

    # Check for summaryDTO structure as in your JSON
    if 'summaryDTO' in activity and activity['summaryDTO']:
        summary = activity['summaryDTO']
        distance = summary.get('distance', 0)
        elevation_gain = summary.get('elevationGain', 0)
        duration_seconds = summary.get('duration', 0)

        # Also get HR data from summary
        avg_hr = summary.get('averageHR', 0)
        max_hr = summary.get('maxHR', 0)

    # Also check direct properties
    else:
        distance = activity.get('distance', 0)
        elevation_gain = activity.get('elevationGain', 0)
        duration_seconds = activity.get('duration', 0)
        avg_hr = activity.get('averageHR', 0)
        max_hr = activity.get('maxHR', 0)

    # Convert distance to miles
    distance_km = distance / 1000.0
    distance_miles = distance_km * KILOMETERS_TO_MILES

    # Convert elevation to feet and calculate elevation load
    elevation_gain_feet = elevation_gain * METERS_TO_FEET
    elevation_load_miles = elevation_gain_feet / 1000.0
    total_load_miles = distance_miles + elevation_load_miles

    # Convert duration to minutes
    duration_minutes = duration_seconds / 60.0

    # If we don't have HR data yet, try to get detailed activity
    if avg_hr == 0:
        detailed_activity = get_detailed_activity(api, activity_id)
        if detailed_activity:
            if 'summaryDTO' in detailed_activity:
                summary = detailed_activity['summaryDTO']
                avg_hr = summary.get('averageHR', 0)
                max_hr = summary.get('maxHR', 0)
            else:
                avg_hr = detailed_activity.get('averageHR', 0)
                max_hr = detailed_activity.get('maxHR', 0)

    # Get HR zone data - make sure to handle the array format properly
    hr_zone_times = [0, 0, 0, 0, 0]  # Default to zeros
    hr_zone_data = get_activity_hr_time_in_zones(api, activity_id)

    if hr_zone_data and isinstance(hr_zone_data, list):
        # Your HR zone data is an array of zone objects
        for zone in hr_zone_data:
            zone_number = zone.get('zoneNumber', 0)
            if 1 <= zone_number <= 5:  # Ensure zone number is valid
                hr_zone_times[zone_number - 1] = zone.get('secsInZone', 0)

    # Calculate Banister TRIMP
    trimp = 0
    if avg_hr > 0 and duration_minutes > 0:
        trimp = calculate_banister_trimp(
            duration_minutes,
            avg_hr,
            hr_config['resting_hr'],
            hr_config['max_hr'],
            hr_config['gender']
        )

    # Log HR data and TRIMP calculation to help with debugging
    logger.info(f"HR data for activity {activity_id}: avg={avg_hr}, max={max_hr}, TRIMP={trimp}")
    logger.info(f"HR zone times (seconds): {hr_zone_times}")

    result = {
        'activity_id': activity_id,
        'date': activity_date,
        'name': activity_name,
        'type': activity_type,
        'distance_miles': round(distance_miles, 2),
        'elevation_gain_feet': round(elevation_gain_feet, 2),
        'elevation_load_miles': round(elevation_load_miles, 2),
        'total_load_miles': round(total_load_miles, 2),
        'avg_heart_rate': avg_hr,
        'max_heart_rate': max_hr,
        'duration_minutes': round(duration_minutes, 2),
        'trimp': trimp,
        'time_in_zone1': hr_zone_times[0],
        'time_in_zone2': hr_zone_times[1],
        'time_in_zone3': hr_zone_times[2],
        'time_in_zone4': hr_zone_times[3],
        'time_in_zone5': hr_zone_times[4]
    }

    logger.info(
        f"Calculated load for activity {activity_id}: {total_load_miles:.2f} miles, Banister TRIMP: {trimp:.2f}")
    return result


# In save_training_load, remove the call to update_moving_averages
def save_training_load(load_data, filename=None):
    """Save training load data to database."""
    try:
        # Check if this activity is already in the database
        activity_id = load_data['activity_id']
        existing = execute_query(
            "SELECT 1 FROM activities WHERE activity_id = %s",
            (activity_id,),
            fetch=True
        )

        if existing:
            logger.info(f"Activity {activity_id} already in database - skipping")
            return

        # Prepare data for insertion
        # Ensure column names match the database schema
        column_mapping = {
            '7day_avg_load': 'seven_day_avg_load',
            '28day_avg_load': 'twentyeight_day_avg_load',
            '7day_avg_trimp': 'seven_day_avg_trimp',
            '28day_avg_trimp': 'twentyeight_day_avg_trimp'
        }

        # Create a copy of load_data with correct column names
        db_data = {}
        for key, value in load_data.items():
            db_key = column_mapping.get(key, key)
            db_data[db_key] = value

        # Build the INSERT query
        columns = ', '.join(db_data.keys())
        placeholders = ', '.join(['?'] * len(db_data))
        values = tuple(db_data.values())

        # Insert the record
        execute_query(
            f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
            values
        )

        # Removed: update_moving_averages(db_data['date'])
        logger.info(f"Saved training load data for activity {activity_id} to database")

    except Exception as e:
        logger.error(f"Error saving training load to database: {str(e)}")
        raise


def ensure_daily_records(start_date_str, end_date_str):
    """
    Ensures that a record exists for every day in the given date range.
    If no activity exists for a day, a 'Rest Day' record is created.
    """
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    current_date = start_date

    logger.info(f"Ensuring daily records from {start_date_str} to {end_date_str}")

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')

        # Check if *any* record exists for this date.
        # This query is sufficient as we only need to know if a record exists for the date,
        # regardless of whether it's an actual activity or a previously inserted rest day.
        existing_record_for_date = execute_query(
            "SELECT 1 FROM activities WHERE date = %s",
            (date_str,),
            fetch=True
        )

        if not existing_record_for_date:
            logger.info(f"No activity record found for {date_str}. Creating a rest day record.")

            # Generate a unique negative activity_id for rest days
            # Using negative ordinal to ensure uniqueness and avoid conflict with Garmin IDs
            rest_day_activity_id = -current_date.toordinal()

            new_record = {
                'activity_id': rest_day_activity_id,
                'date': date_str,
                'name': 'Rest Day',
                'type': 'rest',
                'distance_miles': 0,
                'elevation_gain_feet': 0,
                'elevation_load_miles': 0,
                'total_load_miles': 0,
                'avg_heart_rate': 0,
                'max_heart_rate': 0,
                'duration_minutes': 0,
                'trimp': 0,
                'time_in_zone1': 0,
                'time_in_zone2': 0,
                'time_in_zone3': 0,
                'time_in_zone4': 0,
                'time_in_zone5': 0,
                'weight_lbs': None,
                'perceived_effort': None,
                'feeling_score': None,
                'notes': 'Automatically generated rest day record.'
            }

            columns = ', '.join(new_record.keys())
            placeholders = ', '.join(['?'] * len(new_record))
            values = tuple(new_record.values())

            execute_query(
                f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
                values
            )
            logger.info(f"Created rest day record {rest_day_activity_id} for {date_str}")

        current_date += timedelta(days=1)


# Updated functions for garmin_training_load.py
# Replace the existing update_moving_averages() function with this version
def calculate_normalized_divergence(external_acwr, internal_acwr):
    """Calculate the normalized divergence between external and internal ACWR"""
    if external_acwr is None or internal_acwr is None:
        return None
    if external_acwr == 0 and internal_acwr == 0:
        return 0

    avg_acwr = (external_acwr + internal_acwr) / 2
    if avg_acwr == 0:
        return 0

    return round((external_acwr - internal_acwr) / avg_acwr, 3)


def update_moving_averages(date):
    if date == "2025-05-30":  # Test with known working case
        seven_days_ago = "2025-05-23"
        twentyeight_days_ago = "2025-05-02"
    """
    Update moving averages using time-based aggregation.
    This method treats missing days as zeros, providing mathematically correct ACWR calculations.
    """
    try:
        logger.info(f"Updating moving averages for {date} using time-based aggregation")

        # Calculate date ranges
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        seven_days_ago = (date_obj - timedelta(days=6)).strftime('%Y-%m-%d')
        twentyeight_days_ago = (date_obj - timedelta(days=27)).strftime('%Y-%m-%d')

        logger.info(f"Date ranges: 7-day ({seven_days_ago} to {date}), 28-day ({twentyeight_days_ago} to {date})")

        # Time-based aggregation for load (missing days automatically count as zero)
        seven_day_sum = execute_query(
            "SELECT COALESCE(SUM(total_load_miles), 0) FROM activities WHERE date BETWEEN %s AND %s",
            (seven_days_ago, date),
            fetch=True
        )[0][0]

        twentyeight_day_sum = execute_query(
            "SELECT COALESCE(SUM(total_load_miles), 0) FROM activities WHERE date BETWEEN %s AND %s",
            (twentyeight_days_ago, date),
            fetch=True
        )[0][0]

        # Time-based aggregation for TRIMP
        seven_day_trimp_sum = execute_query(
            "SELECT COALESCE(SUM(trimp), 0) FROM activities WHERE date BETWEEN %s AND %s",
            (seven_days_ago, date),
            fetch=True
        )[0][0]

        twentyeight_day_trimp_sum = execute_query(
            "SELECT COALESCE(SUM(trimp), 0) FROM activities WHERE date BETWEEN %s AND %s",
            (twentyeight_days_ago, date),
            fetch=True
        )[0][0]

        # Calculate daily averages (divide by actual days, not record count)
        seven_day_avg_load = round(seven_day_sum / 7.0, 2)
        twentyeight_day_avg_load = round(twentyeight_day_sum / 28.0, 2)
        seven_day_avg_trimp = round(seven_day_trimp_sum / 7.0, 2)
        twentyeight_day_avg_trimp = round(twentyeight_day_trimp_sum / 28.0, 2)

        # Calculate ACWR ratios
        acute_chronic_ratio = 0
        if twentyeight_day_avg_load > 0:
            acute_chronic_ratio = round(seven_day_avg_load / twentyeight_day_avg_load, 2)

        trimp_acute_chronic_ratio = 0
        if twentyeight_day_avg_trimp > 0:
            trimp_acute_chronic_ratio = round(seven_day_avg_trimp / twentyeight_day_avg_trimp, 2)

        # Calculate normalized divergence
        normalized_divergence = calculate_normalized_divergence(acute_chronic_ratio, trimp_acute_chronic_ratio)

        # Log the calculated values for verification
        logger.info(f"Calculated values for {date}:")
        logger.info(f"  7-day avg load: {seven_day_avg_load} (sum: {seven_day_sum})")
        logger.info(f"  28-day avg load: {twentyeight_day_avg_load} (sum: {twentyeight_day_sum})")
        logger.info(f"  External ACWR: {acute_chronic_ratio}")
        logger.info(f"  Internal ACWR: {trimp_acute_chronic_ratio}")
        logger.info(f"  Normalized divergence: {normalized_divergence}")

        # Add these debug prints:
        print(f"\n=== DEBUGGING {date} ===")
        print(f"7-day range: {seven_days_ago} to {date}")
        print(f"28-day range: {twentyeight_days_ago} to {date}")

        # Check what the queries are actually returning
        print(f"7-day sum: {seven_day_sum}")
        print(f"28-day sum: {twentyeight_day_sum}")
        print(f"7-day average: {seven_day_sum / 7.0}")
        print(f"28-day average: {twentyeight_day_sum / 28.0}")
        print(f"Raw date calculation check:")
        print(f"Input date: {date}")
        print(f"Date object: {date_obj}")
        print(f"7 days ago calculation: {date_obj - timedelta(days=6)}")
        print(f"28 days ago calculation: {date_obj - timedelta(days=27)}")

        # Check how many activities are found
        count_7day = execute_query(
            "SELECT COUNT(*) FROM activities WHERE date BETWEEN %s AND %s",
            (seven_days_ago, date), fetch=True
        )[0][0]

        count_28day = execute_query(
            "SELECT COUNT(*) FROM activities WHERE date BETWEEN %s AND %s",
            (twentyeight_days_ago, date), fetch=True
        )[0][0]

        print(f"Activities found: 7-day={count_7day}, 28-day={count_28day}")

        if acute_chronic_ratio > 0:
            print(f"ACWR: {acute_chronic_ratio}")
        print("=" * 40)

        # Update the record
        execute_query(
            """
            UPDATE activities SET 
                seven_day_avg_load = %s,
                twentyeight_day_avg_load = %s,
                seven_day_avg_trimp = %s,
                twentyeight_day_avg_trimp = %s,
                acute_chronic_ratio = %s,
                trimp_acute_chronic_ratio = %s,
                normalized_divergence = %s
            WHERE date = %s
            """,
            (seven_day_avg_load, twentyeight_day_avg_load, seven_day_avg_trimp, twentyeight_day_avg_trimp,
             acute_chronic_ratio, trimp_acute_chronic_ratio, normalized_divergence, date)
        )

        logger.info(f"Successfully updated moving averages for {date}")

    except Exception as e:
        logger.error(f"Error updating moving averages for {date}: {str(e)}")
        raise


# In process_activities_for_date_range, no need to call update_moving_averages here
def process_activities_for_date_range(api, start_date, end_date=None, hr_config=None):
    """Process all activities in the given date range."""
    if end_date is None:
        end_date = start_date

    activities = get_activities(api, start_date, end_date)
    processed_count = 0

    # # TEMPORARY: Limit to last 10 activities (keep this for testing, remove for full run)
    # activities = activities[-10:] if len(activities) > 10 else activities
    # print(f"TESTING: Processing only the last {len(activities)} activities")


    for activity in activities:
        activity_id = activity.get('activityId')

        # Check if activity already exists in database
        existing = execute_query(
            "SELECT 1 FROM activities WHERE activity_id = %s",
            (activity_id,),
            fetch=True
        )

        if existing:
            logger.info(f"Activity {activity_id} already in database - skipping")
            continue

        # Calculate training load with Banister TRIMP
        load_data = calculate_training_load(activity, api, hr_config)

        # Save to database
        save_training_load(load_data) # Removed update_moving_averages call from here
        processed_count += 1

        # Add small delay to avoid API rate limits
        time.sleep(1)

    return processed_count


def ensure_wellness_columns():
    """Ensure the database has columns for wellness metrics."""
    try:
        # Check if columns exist by trying to query them
        try:
            execute_query(
                "SELECT weight_lbs, perceived_effort, feeling_score FROM activities LIMIT 1",
                fetch=True
            )
            logger.info("Wellness columns already exist in database")
            return True
        except Exception:
            # Columns don't exist, add them
            logger.info("Adding wellness columns to activities table")

            # Add the columns one by one to handle errors gracefully
            try:
                execute_query("ALTER TABLE activities ADD COLUMN weight_lbs REAL")
                logger.info("Added weight_lbs column")
            except Exception as e:
                logger.warning(f"Error adding weight_lbs column: {str(e)}")

            try:
                execute_query("ALTER TABLE activities ADD COLUMN perceived_effort INTEGER")
                logger.info("Added perceived_effort column")
            except Exception as e:
                logger.warning(f"Error adding perceived_effort column: {str(e)}")

            try:
                execute_query("ALTER TABLE activities ADD COLUMN feeling_score INTEGER")
                logger.info("Added feeling_score column")
            except Exception as e:
                logger.warning(f"Error adding feeling_score column: {str(e)}")

            try:
                execute_query("ALTER TABLE activities ADD COLUMN notes TEXT")
                logger.info("Added notes column")
            except Exception as e:
                logger.warning(f"Error adding notes column: {str(e)}")

            return True
    except Exception as e:
        logger.error(f"Error ensuring wellness columns: {str(e)}")
        return False

def get_user_weight_data(api, start_date, end_date=None):
    """
    Get weight data from Garmin Connect.

    Args:
        api: The Garmin Connect API client
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: Optional end date in 'YYYY-MM-DD' format

    Returns:
        List of weight data points
    """
    if end_date is None:
        end_date = start_date

    try:
        logger.info(f"Fetching weight data from {start_date} to {end_date}")

        # Convert string dates to datetime objects
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

        # Use the get_body_composition API endpoint
        # The exact method name may vary depending on your garminconnect version
        weight_data = []

        try:
            # Try standard method first
            response = api.get_body_composition(start_date, end_date)
            logger.info(f"Weight data response: {type(response)}")

            # Check for dateWeightList format (seen in your logs)
            if isinstance(response, dict) and 'dateWeightList' in response:
                logger.info(f"Found dateWeightList with {len(response['dateWeightList'])} entries")
                # Process weight data in the dateWeightList format
                for weight_entry in response['dateWeightList']:
                    # Format the entry into our standard format
                    if 'calendarDate' in weight_entry and 'weight' in weight_entry:
                        weight_data.append({
                            'date': weight_entry['calendarDate'],
                            'weight': weight_entry['weight'],
                            'weightLbs': weight_entry['weight'] / 453.592  # Convert from grams to pounds
                        })
            elif isinstance(response, list):
                # Standard list response
                weight_data = response
            else:
                # Single entry
                weight_data = [response] if response else []

        except (AttributeError, TypeError):
            try:
                # Try alternative methods if standard fails
                logger.info("Trying alternative weight data methods")
                weight_response = None

                # Try each method and use the first one that works
                try:
                    weight_response = api.get_weight_data(start_date, end_date)
                except:
                    pass

                if not weight_response:
                    try:
                        weight_response = api.get_user_weights(start_date, end_date)
                    except:
                        pass

                if not weight_response:
                    try:
                        weight_response = api.get_body_compositions(start_date, end_date)
                    except:
                        pass

                # Check response format
                if weight_response:
                    logger.info(f"Alternative method returned: {type(weight_response)}")

                    if isinstance(weight_response, dict) and 'dateWeightList' in weight_response:
                        # Process dateWeightList format
                        for weight_entry in weight_response['dateWeightList']:
                            if 'calendarDate' in weight_entry and 'weight' in weight_entry:
                                weight_data.append({
                                    'date': weight_entry['calendarDate'],
                                    'weight': weight_entry['weight'],
                                    'weightLbs': weight_entry['weight'] / 453.592  # Convert from grams to pounds
                                })
                    elif isinstance(weight_response, list):
                        weight_data = weight_response
                    else:
                        weight_data = [weight_response] if weight_response else []

            except Exception as e:
                logger.warning(f"Alternative weight data methods failed: {str(e)}")

        # Log the processed weight data
        if weight_data:
            logger.info(f"Processed {len(weight_data)} weight records")
            for record in weight_data:
                logger.info(f"Weight record: {record}")
            return weight_data
        else:
            logger.warning("No weight data processed from Garmin Connect")
            return []

    except Exception as e:
        logger.error(f"Error fetching weight data: {str(e)}")
        return []

def get_user_daily_summary(api, start_date, end_date=None):
    """
    Get daily summary data from Garmin Connect including perceived effort and feeling.

    Args:
        api: The Garmin Connect API client
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: Optional end date in 'YYYY-MM-DD' format

    Returns:
        List of daily summary data points
    """
    if end_date is None:
        end_date = start_date

    try:
        logger.info(f"Fetching daily summary data from {start_date} to {end_date}")

        # Convert string dates to datetime objects
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

        # Try different methods depending on the garminconnect library version
        try:
            # Try standard method first
            daily_data = api.get_user_summary(start_date, end_date)
        except (AttributeError, TypeError):
            try:
                # Try alternative method with ISO format
                daily_data = api.get_user_summary(start_datetime.isoformat(), end_datetime.isoformat())
            except (AttributeError, TypeError):
                try:
                    # Try daily summary endpoint
                    daily_data = api.get_daily_summary(start_date, end_date)
                except Exception:
                    logger.warning("All daily summary fetch methods failed")
                    return []

        if daily_data:
            logger.info(f"Retrieved {len(daily_data) if isinstance(daily_data, list) else 1} daily summary records")
            # Convert to list if it's a single item
            if not isinstance(daily_data, list):
                daily_data = [daily_data]
            return daily_data
        else:
            logger.warning("No daily summary data returned from Garmin Connect")
            return []

    except Exception as e:
        logger.error(f"Error fetching daily summary: {str(e)}")
        return []


def get_activity_wellness_metrics(api, activity_id):
    """
    Get wellness metrics (perceived effort, feeling) for a specific activity.

    Args:
        api: The Garmin Connect API client
        activity_id: The activity ID

    Returns:
        Dictionary with wellness metrics
    """
    try:
        logger.info(f"Fetching wellness metrics for activity {activity_id}")

        # Try to get activity details which sometimes include wellness metrics
        detailed = get_detailed_activity(api, activity_id)
        if not detailed:
            return None

        # Extract any wellness metrics from the detailed activity
        wellness = {}

        # Dump all the keys to the log to help with debugging
        logger.info(f"Activity detail keys: {', '.join(detailed.keys())}")

        # Look for different possible field names in the API response
        # Perceived effort (scale of 1-10)
        effort_fields = ['userEffortRating', 'userPerceived', 'effort', 'effortRating',
                         'perceivedEffort', 'perceivedExertion', 'rpe', 'userRPE']
        for field in effort_fields:
            if field in detailed and detailed[field] is not None:
                wellness['perceived_effort'] = detailed[field]
                logger.info(f"Found perceived effort in field '{field}': {detailed[field]}")
                break

        # Feeling score (scale of 1-10)
        feeling_fields = ['userFeelingRating', 'userFeeling', 'feeling', 'feelingRating',
                          'feelingScore', 'wellness', 'wellnessScore']
        for field in feeling_fields:
            if field in detailed and detailed[field] is not None:
                wellness['feeling_score'] = detailed[field]
                logger.info(f"Found feeling score in field '{field}': {detailed[field]}")
                break

        # Notes
        note_fields = ['description', 'notes', 'activityDescription', 'comment', 'comments']
        for field in note_fields:
            if field in detailed and detailed[field] is not None and detailed[field] != '':
                wellness['notes'] = detailed[field]
                logger.info(f"Found notes in field '{field}': {detailed[field]}")
                break

        # Look for smiley face ratings or other indicators
        if 'userFaceRating' in detailed:
            face_rating = detailed['userFaceRating']
            if face_rating is not None:
                # Convert face rating (usually 1-5) to feeling score (1-10)
                feeling_score = min(10, face_rating * 2)  # Simple conversion
                wellness['feeling_score'] = feeling_score
                logger.info(f"Converted face rating {face_rating} to feeling score {feeling_score}")

        # Try to derive effort from heartrate data if not found directly
        if 'perceived_effort' not in wellness and 'averageHR' in detailed and 'maxHR' in detailed:
            avg_hr = detailed.get('averageHR', 0)
            max_hr = detailed.get('maxHR', 0)
            if avg_hr > 0 and max_hr > 0:
                # Rough estimate: effort based on percentage of max HR
                hr_percentage = avg_hr / max_hr
                if hr_percentage > 0.9:
                    effort = 10
                elif hr_percentage > 0.8:
                    effort = 8
                elif hr_percentage > 0.7:
                    effort = 6
                elif hr_percentage > 0.6:
                    effort = 4
                else:
                    effort = 2
                wellness['perceived_effort'] = effort
                logger.info(f"Derived perceived effort {effort} from HR data: avg={avg_hr}, max={max_hr}")

        if wellness:
            logger.info(f"Found wellness metrics for activity {activity_id}: {wellness}")
            return wellness
        else:
            logger.info(f"No wellness metrics found for activity {activity_id}")
            return None

    except Exception as e:
        logger.error(f"Error fetching activity wellness metrics: {str(e)}")
        return None


def process_wellness_data(api, start_date, end_date=None, hr_config=None):
    """
    Process wellness data from Garmin Connect and save to database.

    Args:
        api: The Garmin Connect API client
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: Optional end date in 'YYYY-MM-DD' format
        hr_config: Optional heart rate configuration

    Returns:
        Number of processed records
    """
    if end_date is None:
        end_date = start_date

    processed_count = 0

    # Get weight data
    weight_data = get_user_weight_data(api, start_date, end_date)

    # Process weight data
    for record in weight_data:
        try:
            # Extract date and weight from the record
            record_date = None
            weight_lbs = None

            # Try different field names for date
            if 'date' in record:
                record_date = record['date']
            elif 'calendarDate' in record:
                record_date = record['calendarDate']
            elif 'startTime' in record:
                # Convert timestamp to date string
                if isinstance(record['startTime'], (int, float)):
                    record_date = datetime.fromtimestamp(record['startTime']/1000).strftime('%Y-%m-%d')
                else:
                    record_date = record['startTime'].split('T')[0]

            # Try different field names for weight
            if 'weightLbs' in record:
                weight_lbs = record['weightLbs']
            elif 'weight' in record:
                # Check if weight is in grams (typical Garmin format)
                weight = record['weight']
                # If weight is very large (over 1000), it's likely in grams
                if weight > 1000:
                    weight_lbs = weight / 453.592  # Convert grams to pounds
                else:
                    # Assume it's already in kg
                    weight_lbs = weight * 2.20462  # Convert kg to lbs

            if not record_date or weight_lbs is None:
                logger.warning(f"Missing date or weight in record: {record}")
                continue

            logger.info(f"Processing weight for date {record_date}: {weight_lbs:.1f} lbs")

            # Find existing activities on this date to update
            activities = execute_query(
                "SELECT activity_id FROM activities WHERE date = %s",
                (record_date,),
                fetch=True
            )

            if activities:
                # Update existing activities with weight data
                for activity in activities:
                    execute_query(
                        "UPDATE activities SET %s = %s WHERE activity_id = %s",
                        (weight_lbs, activity['activity_id'])
                    )
                    logger.info(f"Updated activity {activity['activity_id']} with weight: {weight_lbs:.1f} lbs")
                    processed_count += 1
            else:
                # If no activity exists for this date, create a rest day record
                # Only do this if we have wellness data but no activity
                # This ensures we have continuous data for wellness metrics
                logger.info(f"No activity found for {record_date}, creating rest day record with wellness data")

                # Check if rest day record already exists
                existing_rest = execute_query(
                    "SELECT 1 FROM activities WHERE date = %s AND activity_id = 0",
                    (record_date,),
                    fetch=True
                )

                if existing_rest:
                    # Update existing rest day
                    execute_query(
                        "UPDATE activities SET %s = %s WHERE date = %s AND activity_id = 0",
                        (weight_lbs, record_date)
                    )
                    logger.info(f"Updated existing rest day for {record_date} with weight data")
                else:
                    # Create a new rest day record
                    # Use 0 as the activity_id for rest days
                    new_record = {
                        'activity_id': 0,
                        'date': record_date,
                        'name': 'Rest Day',
                        'type': 'rest',
                        'weight_lbs': weight_lbs,
                        'distance_miles': 0,
                        'elevation_gain_feet': 0,
                        'elevation_load_miles': 0,
                        'total_load_miles': 0,
                        'avg_heart_rate': 0,
                        'max_heart_rate': 0,
                        'duration_minutes': 0,
                        'trimp': 0,
                        'time_in_zone1': 0,
                        'time_in_zone2': 0,
                        'time_in_zone3': 0,
                        'time_in_zone4': 0,
                        'time_in_zone5': 0
                    }

                    # Insert the rest day record
                    columns = ', '.join(new_record.keys())
                    placeholders = ', '.join(['?'] * len(new_record))
                    values = tuple(new_record.values())

                    execute_query(
                        f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
                        values
                    )

                    logger.info(f"Created rest day record for {record_date} with weight data")

                processed_count += 1

                # # Make sure to update moving averages
                # update_moving_averages(record_date)

        except Exception as e:
            logger.error(f"Error processing weight record: {str(e)}")

    # Since daily summary fetch is failing, try to get perceived effort and feeling data from activities
    activities = get_activities(api, start_date, end_date)
    for activity in activities:
        try:
            activity_id = activity.get('activityId')
            activity_date = activity.get('startTimeLocal', '').split(' ')[0] if 'startTimeLocal' in activity else None

            if not activity_id or not activity_date:
                continue

            # Get wellness metrics for this activity (notes, effort, feeling)
            wellness = get_activity_wellness_metrics(api, activity_id)

            if not wellness:
                continue

            # Update the activity with wellness metrics
            updates = []
            params = []

            if 'perceived_effort' in wellness and wellness['perceived_effort'] is not None:
                updates.append("perceived_effort = ?")
                params.append(wellness['perceived_effort'])

            if 'feeling_score' in wellness and wellness['feeling_score'] is not None:
                updates.append("feeling_score = ?")
                params.append(wellness['feeling_score'])

            if 'notes' in wellness and wellness['notes'] is not None:
                updates.append("notes = ?")
                params.append(wellness['notes'])

            if updates:
                params.append(activity_id)
                execute_query(
                    f"UPDATE activities SET {', '.join(updates)} WHERE activity_id = %s",
                    tuple(params)
                )
                logger.info(f"Updated activity {activity_id} with wellness metrics from activity details")
                processed_count += 1

        except Exception as e:
            logger.error(f"Error processing activity wellness metrics: {str(e)}")

    # For good measure, try to fetch effort and feeling from each activity separately
    # and add a more thorough search for specific fields
    for activity in activities:
        try:
            activity_id = activity.get('activityId')
            activity_date = activity.get('startTimeLocal', '').split(' ')[0] if 'startTimeLocal' in activity else None

            if not activity_id or not activity_date:
                continue

            # Get detailed activity data
            detailed = get_detailed_activity(api, activity_id)
            if not detailed:
                continue

            # Search more extensively for effort and feeling scores
            updates = []
            params = []

            # Try various possible field names for effort
            effort_fields = ['userEffortRating', 'effort', 'effortRating', 'perceivedEffort',
                            'perceivedExertion', 'rpe', 'userRPE', 'userPerceived']
            for field in effort_fields:
                if field in detailed and detailed[field] is not None:
                    updates.append("perceived_effort = ?")
                    params.append(detailed[field])
                    logger.info(f"Found perceived effort in field {field}: {detailed[field]}")
                    break

            # Try various possible field names for feeling
            feeling_fields = ['userFeelingRating', 'feeling', 'feelingRating', 'userFeeling',
                             'feelingScore', 'wellness', 'wellnessScore']
            for field in feeling_fields:
                if field in detailed and detailed[field] is not None:
                    updates.append("feeling_score = ?")
                    params.append(detailed[field])
                    logger.info(f"Found feeling score in field {field}: {detailed[field]}")
                    break

            if updates:
                params.append(activity_id)
                execute_query(
                    f"UPDATE activities SET {', '.join(updates)} WHERE activity_id = %s",
                    tuple(params)
                )
                logger.info(f"Updated activity {activity_id} with additional wellness metrics")
                processed_count += 1

        except Exception as e:
            logger.error(f"Error processing additional activity wellness metrics: {str(e)}")

    return processed_count


def debug_database_info():
    """Print debug information about the database."""
    print(f"Current working directory: {os.getcwd()}")
    print(f"Database file path: {os.path.abspath(DB_FILE)}")
    print(f"Log file path: {os.path.abspath('garmin_training_load.log')}")

    if os.path.exists('garmin_training_load.log'):
        print("Log file exists. Last 10 lines:")
        with open('garmin_training_load.log', 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:
                print(f"  {line.strip()}")
    else:
        print("Log file does not exist.")

    if os.path.exists(DB_FILE):
        print(f"\nDatabase exists with these statistics:")
        try:
            activity_count = execute_query("SELECT COUNT(*) FROM activities", fetch=True)[0][0]
            print(f"  Number of activities: {activity_count}")

            if activity_count > 0:
                # Get the latest activity date
                latest_date = execute_query(
                    "SELECT date FROM activities ORDER BY date DESC LIMIT 1",
                    fetch=True
                )[0][0]
                print(f"  Latest activity date: {latest_date}")

                # Count activities with HR data
                hr_count = execute_query(
                    "SELECT COUNT(*) FROM activities WHERE avg_heart_rate > 0",
                    fetch=True
                )[0][0]
                print(
                    f"  Activities with heart rate data: {hr_count} of {activity_count} ({hr_count / activity_count * 100:.1f}%)")

                # Count activities with TRIMP data
                trimp_count = execute_query(
                    "SELECT COUNT(*) FROM activities WHERE trimp > 0",
                    fetch=True
                )[0][0]
                print(
                    f"  Activities with TRIMP data: {trimp_count} of {activity_count} ({trimp_count / activity_count * 100:.1f}%)")

                # Show TRIMP range
                trimp_stats = execute_query(
                    "SELECT MIN(trimp), MAX(trimp), AVG(trimp) FROM activities WHERE trimp > 0",
                    fetch=True
                )[0]
                print(f"  TRIMP range: {trimp_stats[0]} - {trimp_stats[1]}")
                print(f"  Avg TRIMP: {trimp_stats[2]:.2f}")
        except Exception as e:
            print(f"  Error reading database: {str(e)}")
    else:
        print("\nDatabase file does not exist yet.")


def debug_wellness_info():
    """Print debug information about wellness metrics in the database."""
    print("\nWellness Metrics Information:")

    try:
        # Count records with wellness data
        weight_count = execute_query(
            "SELECT COUNT(*) FROM activities WHERE weight_lbs IS NOT NULL",
            fetch=True
        )[0][0]

        effort_count = execute_query(
            "SELECT COUNT(*) FROM activities WHERE perceived_effort IS NOT NULL",
            fetch=True
        )[0][0]

        feeling_count = execute_query(
            "SELECT COUNT(*) FROM activities WHERE feeling_score IS NOT NULL",
            fetch=True
        )[0][0]

        print(f"  Records with weight data: {weight_count}")
        print(f"  Records with perceived effort data: {effort_count}")
        print(f"  Records with feeling score data: {feeling_count}")

        # Show latest wellness data
        latest_weight = execute_query(
            "SELECT date, weight_lbs FROM activities WHERE weight_lbs IS NOT NULL ORDER BY date DESC LIMIT 1",
            fetch=True
        )

        if latest_weight:
            print(f"  Latest weight record: {latest_weight[0]['date']} - {latest_weight[0]['weight_lbs']} lbs")

        # Show weight range
        weight_range = execute_query(
            "SELECT MIN(weight_lbs), MAX(weight_lbs), AVG(weight_lbs) FROM activities WHERE weight_lbs IS NOT NULL",
            fetch=True
        )

        if weight_range and weight_range[0][0] is not None:
            print(f"  Weight range: {weight_range[0][0]} - {weight_range[0][1]} lbs")
            print(f"  Average weight: {weight_range[0][2]:.1f} lbs")

    except Exception as e:
        print(f"  Error retrieving wellness info: {str(e)}")


def main():
    """Main function."""
    # Add command line argument parsing
    parser = argparse.ArgumentParser(description='Garmin Training Load Tracker with Wellness Metrics')
    parser.add_argument('--include-wellness', action='store_true',
                        help='Include wellness metrics (weight, effort, feeling)')
    parser.add_argument('--wellness-only', action='store_true',
                        help='Only process wellness metrics, skip activity data')
    parser.add_argument('--days', type=int, default=5, help='Number of days to process (default: 5)')
    args = parser.parse_args()

    print("\nGarmin Training Load Tracker with Banister TRIMP")
    print("------------------------------------------------")

    # Initialize database
    db_exists = initialize_db() # This function needs to create the tables if they don't exist
    ensure_wellness_columns()

    # Load configuration
    email, password, hr_config = load_config()
    if not email or not password:
        print("\nNo configuration found. Let's set up your account.")
        email = input("Enter your Garmin Connect email: ")
        password = input("Enter your Garmin Connect password: ")

        # Connect to Garmin to verify credentials before asking for HR parameters
        print("\nConnecting to Garmin Connect to verify credentials...")
        api = connect_to_garmin(email, password)
        if not api:
            print("Failed to connect to Garmin. Please check your credentials and try again.")
            return

        print("\nConnection successful!")

        # Setup heart rate parameters
        hr_config = setup_hr_parameters()

        # Save configuration
        save_config(email, password, hr_config)

        # Save user settings to database
        # Ensure user_settings table is created if it doesn't exist
        execute_query(
            """
            INSERT INTO user_settings (email, resting_hr, max_hr, gender) 
            VALUES (%s)
            """,
            (email, hr_config['resting_hr'], hr_config['max_hr'], hr_config['gender'])
        )
    else:
        # Connect to Garmin
        print("\nConnecting to Garmin Connect...")
        api = connect_to_garmin(email, password)
        if not api:
            print("Failed to connect to Garmin. Please check your credentials and try again.")
            return

        # If HR config is missing or incomplete, prompt for it
        if hr_config is None:
            print("\nHeart rate parameters not found in configuration.")
            hr_config = setup_hr_parameters()
            save_config(email, password, hr_config)

            # Update user settings in database
            execute_query(
                """
                UPDATE user_settings 
                SET %s = %s WHERE email = %s
                """,
                (hr_config['resting_hr'], hr_config['max_hr'], hr_config['gender'], email)
            )

    # Determine the full date range for processing and average calculation
    end_date_obj = datetime.now()
    # For initial run or update, it's good to go back at least 28 days to ensure ACWR is meaningful
    # Or for a fresh DB, go even further back (e.g., 84 days)
    initial_process_days = 7 # For a fresh DB, or if starting far back
    regular_process_days = args.days # User specified days for regular updates

    # Define the range for fetching new activities
    end_date_obj = datetime.now()
    fetch_end_date = end_date_obj.strftime('%Y-%m-%d')

    # Temporarily set the fetch range to a longer period (e.g., 84 days)
    # This will ensure sufficient historical data is fetched from Garmin.
    fetch_start_date = (end_date_obj - timedelta(days=7)).strftime('%Y-%m-%d')  # Use 84 days for comprehensive fetch

    # Define the range for fetching new activities
    # Use regular_process_days (from args.days) for daily updates
    # fetch_start_date = (end_date_obj - timedelta(days=regular_process_days)).strftime('%Y-%m-%d')

    # Define the full range for calculating moving averages.
    # This should be at least 28 days back from the latest data.
    # If the database is new, we need to go back further.
    latest_activity_date_in_db = None
    if execute_query("SELECT COUNT(*) FROM activities", fetch=True)[0][0] > 0:
        latest_activity_date_in_db_str = execute_query(
            "SELECT date FROM activities ORDER BY date DESC LIMIT 1",
            fetch=True
        )[0][0]
        latest_activity_date_in_db = datetime.strptime(latest_activity_date_in_db_str, '%Y-%m-%d')


    # Calculate the range for which moving averages should be re-calculated
    # This range should extend from 28 days before the earliest activity date in the
    # current run, up to the current date.
    if latest_activity_date_in_db:
        # For existing databases, calculate averages from (latest_activity_date_in_db - 28 days) to today
        calculation_start_date_obj = latest_activity_date_in_db - timedelta(days=28)
        calculation_end_date_obj = end_date_obj
    else:
        # For a brand new database, calculate averages from 84 days ago to today
        calculation_start_date_obj = end_date_obj - timedelta(days=initial_process_days)
        calculation_end_date_obj = end_date_obj

    calculation_start_date_str = calculation_start_date_obj.strftime('%Y-%m-%d')
    calculation_end_date_str = calculation_end_date_obj.strftime('%Y-%m-%d')

    # Process activities if not wellness only
    if not args.wellness_only:
        print(f"\nFetching and processing activities from {fetch_start_date} to {fetch_end_date}...")
        count = process_activities_for_date_range(api, fetch_start_date, fetch_end_date, hr_config)
        print(f"Processed {count} activities.")

    # Always ensure daily records for the calculation range, and then update moving averages
    print(f"\nEnsuring daily records and updating moving averages for range: {calculation_start_date_str} to {calculation_end_date_str}")
    ensure_daily_records(calculation_start_date_str, calculation_end_date_str)

    current_date_for_avg_update = datetime.strptime(calculation_start_date_str, '%Y-%m-%d')
    while current_date_for_avg_update <= calculation_end_date_obj:
        date_to_update = current_date_for_avg_update.strftime('%Y-%m-%d')
        print(f"Calculating averages for {date_to_update}...")
        update_moving_averages(date_to_update)
        current_date_for_avg_update += timedelta(days=1)

    # Process wellness data if requested
    if args.include_wellness or args.wellness_only:
        print("\nProcessing wellness data...")
        wellness_count = process_wellness_data(api, fetch_start_date, fetch_end_date, hr_config)
        print(f"Processed wellness data for {wellness_count} days/activities.")

    print("\nProcessing complete!")
    debug_database_info()  # Standard database debug info
    debug_wellness_info()  # New wellness-specific debug info


if __name__ == "__main__":
    main()