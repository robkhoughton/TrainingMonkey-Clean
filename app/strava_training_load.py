#!/usr/bin/env python3
"""
DEPLOYMENT VERIFICATION: 2025-07-06 7:15 PM - WITH FIXES
Strava Training Load Tracker with Banister TRIMP
Replaces garmin_training_load.py with Strava API integration
Based on your existing Garmin processing logic
"""

import os
import json
import logging
import time
import numpy as np
import argparse
from datetime import datetime, date, timedelta
import pytz
from stravalib.client import Client
from stravalib.exc import ActivityUploadFailed, Fault
from timezone_utils import should_create_rest_day, get_app_current_date, log_timezone_debug
from db_utils import get_db_connection, execute_query, initialize_db, DB_FILE

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='strava_training_load.log'
)
logger = logging.getLogger('strava_training_load')

# Configuration
CONFIG_FILE = 'strava_config.json'
TOKENS_FILE = 'strava_tokens.json'
MAX_RETRIES = 3
RETRY_DELAY = 30  # seconds

# Unit conversion constants
METERS_TO_FEET = 3.28084
METERS_TO_MILES = 0.000621371

# Default HR parameters - will be overridden by user input
DEFAULT_RESTING_HR = 44
DEFAULT_MAX_HR = 178
DEFAULT_GENDER = 'male'


def is_supported_activity(activity_type):
    """Check if activity type should be processed by the app (running, cycling, walking, hiking)."""
    supported_types = {
        # Running activities
        'Trail Run', 'Road Run', 'Treadmill Run', 'Track Run',
        'VirtualRun', 'Run', 'run',
        "root='Run'",

        # Cycling activities - NEW
        'Ride', 'Road Bike', 'Mountain Bike', 'Gravel Bike', 'Cyclocross',
        'Hand Cycle', 'Bike', 'Cycling', 'Indoor Bike', 'Virtual Bike',
        'E-Bike', 'E-Mountain Bike', 'Velomobile', 'ride',

        # Walking and hiking activities (relevant for trail runners)
        'Walk', 'walk', 'Hike', 'hike'
    }
    return activity_type in supported_types

def safe_date_parse(date_input):
    """
    Safely convert date input to datetime.date object
    Handles both strings and date objects after database DATE standardization

    CRITICAL: After PostgreSQL DATE migration, database returns date objects instead of strings
    This function ensures compatibility with both old string format and new date objects
    """

    if date_input is None:
        return None
    elif isinstance(date_input, str):
        # String format - parse it
        try:
            return datetime.strptime(date_input, '%Y-%m-%d').date()
        except ValueError:
            # Try alternative format if needed
            return datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S').date()
    elif isinstance(date_input, date):
        # Already a date object
        return date_input
    elif hasattr(date_input, 'date') and callable(date_input.date):
        # It's a datetime object - extract date
        return date_input.date()
    else:
        # Last resort - convert to string and parse
        return datetime.strptime(str(date_input), '%Y-%m-%d').date()

def convert_numpy_types(data):
    """Converts numpy types within a dictionary (or list of dicts) to native Python types."""
    # Ensure 'import numpy as np' is at the very top of the strava_training_load.py file.
    # Remove 'import numpy as np' if it's currently inside this function.

    if isinstance(data, dict):
        return {k: convert_numpy_types(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(elem) for elem in data]
    # Check if it's any common NumPy scalar type (float, int, bool)
    elif isinstance(data, (np.integer, np.floating, np.bool_)):
        return data.item() # Use .item() to get the native Python scalar value
    else:
        return data

def load_config():
    """Load configuration from JSON file."""
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
                    config.get('client_id'),
                    config.get('client_secret'),
                    hr_config
                )
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            return None, None, None
    else:
        logger.error("No configuration found. Create a strava_config.json file.")
        return None, None, None


def load_tokens():
    """Load saved Strava tokens."""
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("No tokens found. Run authentication flow first.")
        return None


def save_tokens(tokens):
    """Save Strava tokens to file."""
    try:
        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
        os.chmod(TOKENS_FILE, 0o600)
        logger.info("Tokens saved successfully")
    except Exception as e:
        logger.error(f"Error saving tokens: {str(e)}")


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


def save_config(client_id, client_secret, hr_config=None):
    """Save configuration to JSON file."""
    if hr_config is None:
        hr_config = {
            'resting_hr': DEFAULT_RESTING_HR,
            'max_hr': DEFAULT_MAX_HR,
            'gender': DEFAULT_GENDER
        }

    config_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'resting_hr': hr_config['resting_hr'],
        'max_hr': hr_config['max_hr'],
        'gender': hr_config['gender']
    }

    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)
        logger.info("Configuration saved successfully")
        print("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving configuration: {str(e)}")
        print(f"Error saving configuration: {str(e)}")


def connect_to_strava():
    """Connect to Strava using saved tokens with retry logic."""
    tokens = load_tokens()
    if not tokens:
        logger.error("No tokens available. Run authentication first.")
        return None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Connecting to Strava (Attempt {attempt + 1}/{MAX_RETRIES})")

            client = Client(access_token=tokens['access_token'])

            # Test connection
            athlete = client.get_athlete()
            logger.info(f"Connected as {athlete.firstname} {athlete.lastname}")
            return client

        except Exception as e:
            logger.error(f"Error connecting to Strava: {str(e)}")

            # Try to refresh token if it's expired
            if 'invalid' in str(e).lower() or 'expired' in str(e).lower():
                logger.info("Token appears expired, attempting refresh...")
                refreshed_client = refresh_strava_token()
                if refreshed_client:
                    return refreshed_client

            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error("Max retries reached. Unable to connect to Strava.")
                return None


def refresh_strava_token():
    """Refresh expired Strava token."""
    try:
        tokens = load_tokens()
        if not tokens or 'refresh_token' not in tokens:
            logger.error("No refresh token available")
            return None

        config = load_config()
        client_id, client_secret, _ = config

        if not client_id or not client_secret:
            logger.error("No client credentials available for token refresh")
            return None

        client = Client()
        refresh_response = client.refresh_access_token(
            client_id=client_id,
            client_secret=client_secret,
            refresh_token=tokens['refresh_token']
        )

        # Save new tokens
        new_tokens = {
            'access_token': refresh_response['access_token'],
            'refresh_token': refresh_response['refresh_token'],
            'expires_at': refresh_response['expires_at']
        }
        save_tokens(new_tokens)

        # Return new client
        return Client(access_token=new_tokens['access_token'])

    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None


def get_activities(client, start_date, end_date=None, limit=200):
    """
    FIXED: Get activities between start_date and end_date with proper timezone handling.
    This fixes the July 29th missing activity issue.
    """
    if end_date is None:
        end_date = start_date

    try:
        logger.info(f"Fetching activities from {start_date} to {end_date}")

        # CRITICAL FIX: Expand the date range to account for all possible timezones
        # This ensures we don't miss activities due to timezone edge cases

        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        # Expand range by 1 day on each side to catch timezone edge cases
        start_expanded = start_date_obj - timedelta(days=1)
        end_expanded = end_date_obj + timedelta(days=1)

        # Create UTC datetime objects with expanded range
        start_utc = datetime(start_expanded.year, start_expanded.month, start_expanded.day, 0, 0, 0, tzinfo=pytz.UTC)
        end_utc = datetime(end_expanded.year, end_expanded.month, end_expanded.day, 23, 59, 59, tzinfo=pytz.UTC)

        logger.info(f"FIXED: Strava API query parameters:")
        logger.info(f"  Original range: {start_date} to {end_date}")
        logger.info(f"  Expanded range: {start_expanded.strftime('%Y-%m-%d')} to {end_expanded.strftime('%Y-%m-%d')}")
        logger.info(f"  UTC start: {start_utc}")
        logger.info(f"  UTC end: {end_utc}")

        # Get activities using stravalib with corrected timezone-aware dates
        activities = list(client.get_activities(
            before=end_utc,
            after=start_utc,
            limit=limit
        ))

        logger.info(f"Found {len(activities)} activities")

        # DEBUG: Log each activity's date to verify coverage
        for activity in activities:
            local_date = activity.start_date_local.strftime('%Y-%m-%d')
            utc_date = activity.start_date.strftime('%Y-%m-%d %H:%M:%S UTC')
            logger.info(f"  Activity {activity.id}: {activity.name} on {local_date} (UTC: {utc_date})")

        return activities

    except Exception as e:
        logger.error(f"Error fetching activities: {str(e)}")
        return []


def get_activity_streams(client, activity_id):
    """Get detailed streams for an activity."""
    try:
        logger.info(f"Fetching streams for activity {activity_id}")

        # Request all available stream types
        stream_types = [
            'time', 'distance', 'heartrate', 'altitude', 'velocity_smooth',
            'cadence', 'watts', 'temp', 'moving', 'grade_smooth'
        ]

        streams = client.get_activity_streams(activity_id, types=stream_types)

        logger.info(f"Successfully fetched streams for activity {activity_id}")
        return streams

    except Exception as e:
        logger.error(f"Error fetching activity streams: {str(e)}")
        return None


def determine_specific_activity_type(activity):
    """
    FIXED: Determine specific activity type from Strava activity data.
    Returns clean string values like "Trail Run", "Track Run", etc.
    """
    try:
        activity_id = activity.id if hasattr(activity, 'id') else 'No ID'
        activity_name = activity.name if hasattr(activity, 'name') else 'No name'

        logger.info(f"Determining activity type for {activity_id}: '{activity_name}'")

        # FIXED: Handle both sport_type and type fields properly
        specific_type = None
        basic_type = None

        # Try sport_type first (this gives specific types like "TrailRun", "VirtualRun")
        if hasattr(activity, 'sport_type') and activity.sport_type:
            sport_type_raw = activity.sport_type
            # Handle complex objects by converting to string and cleaning
            if hasattr(sport_type_raw, 'value'):
                specific_type = str(sport_type_raw.value)
            else:
                specific_type = str(sport_type_raw)

            # Clean up the format (remove 'root=' stuff)
            if 'root=' in specific_type:
                specific_type = specific_type.split("root='")[1].split("'")[0]

            logger.info(f"Raw sport_type: {sport_type_raw}, Cleaned: {specific_type}")

        # Try basic type as fallback
        if hasattr(activity, 'type') and activity.type:
            type_raw = activity.type
            if hasattr(type_raw, 'value'):
                basic_type = str(type_raw.value)
            else:
                basic_type = str(type_raw)

            # Clean up the format
            if 'root=' in basic_type:
                basic_type = basic_type.split("root='")[1].split("'")[0]

            logger.info(f"Raw type: {type_raw}, Cleaned: {basic_type}")

        # MAPPING: Convert Strava's naming to readable format
        type_mapping = {
            # Running activities
            'TrailRun': 'Trail Run',
            'Run': 'Road Run',
            'VirtualRun': 'Treadmill Run',
            'Treadmill': 'Treadmill Run',
            'Track': 'Track Run',
            'RoadRun': 'Road Run',

            # Other activities
            'Ride': 'Road Bike',
            'MountainBikeRide': 'Mountain Bike',
            'VirtualRide': 'Indoor Bike',
            'Walk': 'Walk',
            'Hike': 'Hike',
            'WeightTraining': 'Weight Training',
            'Yoga': 'Yoga',
            'Swimming': 'Swimming'
        }

        # Use specific_type if available, otherwise basic_type
        raw_type = specific_type if specific_type else basic_type

        if raw_type:
            # Apply mapping or use cleaned raw value
            final_type = type_mapping.get(raw_type, raw_type)
            logger.info(f"Final activity type for {activity_id}: '{final_type}'")
            return final_type
        else:
            logger.warning(f"No activity type found for {activity_id}, using 'Unknown'")
            return 'Unknown'

    except Exception as e:
        logger.error(f"Error determining activity type for {activity_id}: {e}")
        return 'Unknown'


def determine_sport_type(activity):
    """
    Classify activity as 'running' or 'cycling' based on Strava activity type

    Args:
        activity: Strava activity object

    Returns:
        str: 'running' | 'cycling' | 'other'
    """
    try:
        # Use existing function to get the specific activity type
        activity_type = determine_specific_activity_type(activity)
        logger.info(f"Determining sport type for activity type: '{activity_type}'")

        # Define cycling keywords (from Strava activity types)
        cycling_keywords = [
            'bike', 'cycling', 'ride', 'mountain bike', 'road bike', 'indoor bike',
            'mountainbikeride', 'roadbike', 'virtualride', 'ebike'
        ]

        # Define running keywords (from Strava activity types)
        running_keywords = [
            'run', 'jog', 'trail', 'track', 'treadmill', 'virtualrun',
            'trail run', 'road run', 'track run', 'treadmill run'
        ]

        activity_lower = activity_type.lower()

        # Check for cycling keywords
        if any(keyword in activity_lower for keyword in cycling_keywords):
            logger.info(f"Activity classified as 'cycling': {activity_type}")
            return 'cycling'
        # Check for running keywords
        elif any(keyword in activity_lower for keyword in running_keywords):
            logger.info(f"Activity classified as 'running': {activity_type}")
            return 'running'
        else:
            # Default to 'running' for safety with existing data
            logger.info(f"Activity type '{activity_type}' not recognized, defaulting to 'running'")
            return 'running'

    except Exception as e:
        logger.error(f"Error determining sport type: {e}")
        # Default to running for safety
        return 'running'


def calculate_cycling_external_load(distance_miles, average_speed_mph=None, elevation_gain_feet=0):
    """
    Convert cycling activity to running-equivalent external load

    Based on research-validated conversion factors that account for cycling efficiency
    compared to running biomechanics and energy expenditure.

    Args:
        distance_miles (float): Cycling distance in miles
        average_speed_mph (float, optional): Average cycling speed in mph
        elevation_gain_feet (int): Total elevation gain in feet

    Returns:
        tuple: (running_equivalent_distance, elevation_load_miles, total_external_load)
    """
    try:
        logger.info(
            f"Calculating cycling external load: {distance_miles} miles, {average_speed_mph} mph, {elevation_gain_feet} ft")

        # Speed-based distance conversion (research-validated ratios)
        # These factors account for cycling efficiency vs running energy expenditure
        if average_speed_mph is None or average_speed_mph <= 12:
            conversion_factor = 3.0  # Leisure cycling - higher factor due to low intensity
        elif average_speed_mph <= 16:
            conversion_factor = 3.1  # Moderate cycling - peak efficiency difference
        elif average_speed_mph <= 20:
            conversion_factor = 2.9  # Vigorous cycling - approaching running intensity
        else:
            conversion_factor = 2.5  # Racing pace - high intensity, closer to running

        # Convert cycling distance to running equivalent
        running_equivalent_distance = distance_miles / conversion_factor

        # Cycling-specific elevation factor
        # Cycling handles elevation differently than running due to:
        # - Gear ratios allowing for more efficient climbing
        # - Momentum assistance on descents
        # - Different biomechanical efficiency
        CYCLING_ELEVATION_FACTOR = 1100.0  # feet per mile equivalent (vs 750 for running)
        elevation_load_miles = elevation_gain_feet / CYCLING_ELEVATION_FACTOR

        # Total external load (running equivalent)
        total_external_load = running_equivalent_distance + elevation_load_miles

        logger.info(f"Cycling conversion results: running_equiv={running_equivalent_distance:.2f}, "
                    f"elevation_load={elevation_load_miles:.2f}, total={total_external_load:.2f}")

        return running_equivalent_distance, elevation_load_miles, total_external_load

    except Exception as e:
        logger.error(f"Error calculating cycling external load: {e}")
        # Return safe defaults
        return 0.0, 0.0, 0.0


def calculate_training_load(activity, client, hr_config=None):
    """
    Calculate custom training load based on Strava activity data.
    ENHANCED VERSION: Now supports both running and cycling activities
    """
    if hr_config is None:
        hr_config = {
            'resting_hr': DEFAULT_RESTING_HR,
            'max_hr': DEFAULT_MAX_HR,
            'gender': DEFAULT_GENDER
        }

    # Extract base metrics from Strava activity
    activity_id = activity.id
    activity_date = activity.start_date.strftime('%Y-%m-%d')
    activity_name = activity.name

    logger.info(f"DEBUG: Starting calculate_training_load for activity {activity_id}: '{activity_name}'")

    # Get the specific activity type and determine sport classification
    specific_activity_type = determine_specific_activity_type(activity)
    sport_type = determine_sport_type(activity)  # NEW: Get sport classification

    logger.info(f"DEBUG: Activity {activity_id} type: '{specific_activity_type}' -> sport: '{sport_type}'")

    # Get distance, elevation, and duration
    distance_meters = float(activity.distance or 0)
    elevation_gain_meters = float(activity.total_elevation_gain or 0)

    # Handle Strava's Duration object properly
    if activity.moving_time:
        try:
            duration_seconds = float(int(activity.moving_time))
        except (ValueError, TypeError, AttributeError) as e:
            logger.warning(f"Could not convert moving_time {activity.moving_time} to seconds: {e}")
            duration_seconds = 0
    else:
        duration_seconds = 0

    # Convert units to match your system format
    distance_miles = distance_meters * METERS_TO_MILES
    elevation_gain_feet = elevation_gain_meters * METERS_TO_FEET
    duration_minutes = duration_seconds / 60.0

    # NEW: Calculate average speed for cycling analysis
    average_speed_mph = None
    if distance_miles > 0 and duration_seconds > 0:
        average_speed_mph = distance_miles / (duration_seconds / 3600.0)
        logger.info(f"DEBUG: Calculated average speed: {average_speed_mph:.2f} mph")

    # NEW: Calculate external load based on sport type
    cycling_equivalent_miles = None
    cycling_elevation_factor = None

    if sport_type == 'cycling':
        # NEW: Cycling-specific calculation
        logger.info("DEBUG: Using cycling-specific external load calculation")
        running_equiv_distance, elevation_load_miles, total_load_miles = calculate_cycling_external_load(
            distance_miles, average_speed_mph, elevation_gain_feet
        )
        cycling_equivalent_miles = running_equiv_distance
        cycling_elevation_factor = 1100.0

    else:
        # EXISTING: Running calculation (unchanged for safety)
        logger.info("DEBUG: Using running external load calculation")
        elevation_load_miles = elevation_gain_feet / 750.0
        total_load_miles = distance_miles + elevation_load_miles
        # cycling fields remain None for running activities

    logger.info(f"DEBUG: External load calculated: distance={distance_miles:.2f}, "
                f"elevation_load={elevation_load_miles:.2f}, total={total_load_miles:.2f}")

    # Get heart rate data (UNCHANGED - your existing logic)
    avg_hr = float(activity.average_heartrate or 0)
    max_hr = float(activity.max_heartrate or 0)

    # Get detailed HR streams for zone calculation (UNCHANGED - your existing logic)
    hr_zone_times = [0, 0, 0, 0, 0]  # Default to zeros
    try:
        streams = get_activity_streams(client, activity_id)
        if streams:
            hr_zone_times = calculate_hr_zones_from_streams(
                streams,
                hr_config['max_hr'],
                hr_config['resting_hr']
            )
    except Exception as e:
        logger.warning(f"Could not get HR streams for activity {activity_id}: {str(e)}")

    # Calculate Banister TRIMP (UNCHANGED - your existing logic)
    trimp = 0
    if avg_hr > 0 and duration_minutes > 0:
        trimp = calculate_banister_trimp(
            duration_minutes,
            avg_hr,
            hr_config['resting_hr'],
            hr_config['max_hr'],
            hr_config['gender']
        )

    # Enhanced debug logging (UNCHANGED - your existing logic)
    logger.info(f"DEBUG: Activity {activity_id} final data:")
    logger.info(f"  - Name: '{activity_name}'")
    logger.info(f"  - Type: '{specific_activity_type}' (Sport: {sport_type})")  # Enhanced
    logger.info(f"  - Distance: {distance_miles:.2f} miles")
    logger.info(f"  - Elevation: {elevation_gain_feet:.1f} feet")
    logger.info(f"  - Duration: {duration_minutes:.1f} minutes")
    logger.info(
        f"  - Average Speed: {average_speed_mph:.2f} mph" if average_speed_mph else "  - Average Speed: N/A")  # NEW
    logger.info(f"  - TRIMP: {trimp:.2f}")

    # Return enhanced data structure with new cycling fields
    result = {
        'activity_id': int(activity_id),
        'date': activity_date,
        'name': activity_name,
        'type': specific_activity_type,
        'sport_type': sport_type,  # NEW
        'distance_miles': float(round(distance_miles, 2)),
        'elevation_gain_feet': float(round(elevation_gain_feet, 2)),
        'elevation_load_miles': float(round(elevation_load_miles, 2)),
        'total_load_miles': float(round(total_load_miles, 2)),
        'average_speed_mph': float(round(average_speed_mph, 2)) if average_speed_mph else None,  # NEW
        'cycling_equivalent_miles': float(round(cycling_equivalent_miles, 2)) if cycling_equivalent_miles else None,
        # NEW
        'cycling_elevation_factor': float(cycling_elevation_factor) if cycling_elevation_factor else None,  # NEW
        'avg_heart_rate': float(avg_hr),
        'max_heart_rate': float(max_hr),
        'duration_minutes': float(round(duration_minutes, 2)),
        'trimp': float(trimp.item()) if hasattr(trimp, 'item') else float(trimp),
        'time_in_zone1': int(hr_zone_times[0]),
        'time_in_zone2': int(hr_zone_times[1]),
        'time_in_zone3': int(hr_zone_times[2]),
        'time_in_zone4': int(hr_zone_times[3]),
        'time_in_zone5': int(hr_zone_times[4])
    }

    logger.info(
        f"DEBUG: Returning result for activity {activity_id} with type='{result['type']}', sport='{result['sport_type']}'")
    return result


def calculate_banister_trimp(duration_minutes, avg_hr, resting_hr, max_hr, gender='male', hr_stream=None):
    """
    Calculate Banister TRIMP (Training Impulse) using the exponential heart rate weighting.
    Enhanced to support heart rate stream data for improved accuracy on variable-intensity workouts.
    
    Args:
        duration_minutes (float): Activity duration in minutes
        avg_hr (float): Average heart rate for the activity
        resting_hr (float): Resting heart rate
        max_hr (float): Maximum heart rate
        gender (str): Gender for coefficient calculation ('male' or 'female')
        hr_stream (list, optional): Heart rate stream data array for enhanced calculation
    
    Returns:
        float: Calculated TRIMP value rounded to 2 decimal places
    """
    try:
        # Comprehensive input validation
        if not isinstance(duration_minutes, (int, float)) or duration_minutes <= 0:
            logger.error(f"Invalid duration: {duration_minutes} (must be positive number)")
            return 0.0

        if not isinstance(avg_hr, (int, float)) or avg_hr <= 0:
            logger.error(f"Invalid average HR: {avg_hr} (must be positive number)")
            return 0.0

        if not isinstance(resting_hr, (int, float)) or resting_hr <= 0:
            logger.error(f"Invalid resting HR: {resting_hr} (must be positive number)")
            return 0.0

        if not isinstance(max_hr, (int, float)) or max_hr <= 0:
            logger.error(f"Invalid max HR: {max_hr} (must be positive number)")
            return 0.0

        if max_hr <= resting_hr:
            logger.error(f"Invalid HR range: max_hr={max_hr} must be greater than resting_hr={resting_hr}")
            return 0.0

        if not isinstance(gender, str):
            logger.error(f"Invalid gender: {gender} (must be string)")
            return 0.0

        # Validate reasonable ranges
        if duration_minutes > 1440:  # 24 hours
            logger.warning(f"Duration seems unusually long: {duration_minutes} minutes")

        if avg_hr < 30 or avg_hr > 250:
            logger.warning(f"Average HR outside normal range: {avg_hr} bpm")

        if resting_hr < 30 or resting_hr > 100:
            logger.warning(f"Resting HR outside normal range: {resting_hr} bpm")

        if max_hr < 120 or max_hr > 250:
            logger.warning(f"Max HR outside normal range: {max_hr} bpm")

        # Set gender constant with validation
        gender_lower = gender.lower()
        if gender_lower not in ['male', 'female']:
            logger.warning(f"Unknown gender '{gender}', defaulting to male")
            gender_lower = 'male'
        
        k = 1.92 if gender_lower == 'male' else 1.67

        # Check if heart rate stream data is available for enhanced calculation
        if hr_stream and len(hr_stream) > 0:
            # Enhanced calculation using heart rate stream data
            logger.info(f"TRIMP_CALC: Using heart rate stream data (stream_length={len(hr_stream)}, duration={duration_minutes}min)")
            result = _calculate_trimp_from_stream(duration_minutes, hr_stream, resting_hr, max_hr, k)
            logger.info(f"TRIMP_CALC: Stream calculation completed, result={result}")
            return result
        else:
            # Fallback to average heart rate calculation
            logger.info(f"TRIMP_CALC: Using average heart rate calculation (avg_hr={avg_hr}, duration={duration_minutes}min)")
            result = _calculate_trimp_from_average(duration_minutes, avg_hr, resting_hr, max_hr, k)
            logger.info(f"TRIMP_CALC: Average calculation completed, result={result}")
            return result
    except Exception as e:
        logger.error(f"Error calculating Banister TRIMP: {str(e)}")
        return 0.0  # Return Python float, not int


def _round_trimp_value(trimp_value):
    """
    Ensure mathematical precision for TRIMP values with proper rounding.
    
    Args:
        trimp_value (float): Raw TRIMP calculation result
    
    Returns:
        float: TRIMP value rounded to 2 decimal places with validation
    """
    try:
        # Validate input
        if not isinstance(trimp_value, (int, float)):
            logger.error(f"TRIMP_CALC: Invalid TRIMP value type: {type(trimp_value)}")
            return 0.0
        
        # Handle special cases
        if trimp_value < 0:
            logger.warning(f"TRIMP_CALC: Negative TRIMP value detected: {trimp_value}, returning 0.0")
            return 0.0
        
        if trimp_value == float('inf') or trimp_value == float('-inf'):
            logger.error(f"TRIMP_CALC: Infinite TRIMP value detected: {trimp_value}")
            return 0.0
        
        if trimp_value != trimp_value:  # NaN check
            logger.error(f"TRIMP_CALC: NaN TRIMP value detected: {trimp_value}")
            return 0.0
        
        # Round to 2 decimal places
        rounded_value = round(float(trimp_value), 2)
        
        # Validate rounded value is reasonable
        if rounded_value > 10000:  # Unreasonably high TRIMP
            logger.warning(f"TRIMP_CALC: Unusually high TRIMP value: {rounded_value}")
        
        # Ensure we return a proper float
        return float(rounded_value)
        
    except Exception as e:
        logger.error(f"TRIMP_CALC: Error rounding TRIMP value {trimp_value}: {str(e)}")
        return 0.0


def _validate_hr_stream_data(hr_stream, duration_minutes, resting_hr, max_hr):
    """
    Comprehensive validation of heart rate stream data and parameters.
    
    Args:
        hr_stream (list): Heart rate stream data array
        duration_minutes (float): Total activity duration in minutes
        resting_hr (float): Resting heart rate
        max_hr (float): Maximum heart rate
    
    Returns:
        tuple: (is_valid, error_message, valid_samples_count)
    """
    try:
        # Validate stream data type and structure
        if hr_stream is None:
            return False, "Heart rate stream is None", 0
        
        if not isinstance(hr_stream, (list, tuple)):
            return False, f"Heart rate stream must be list or tuple, got {type(hr_stream)}", 0
        
        if len(hr_stream) == 0:
            return False, "Heart rate stream is empty", 0
        
        # Validate duration
        if not isinstance(duration_minutes, (int, float)):
            return False, f"Duration must be numeric, got {type(duration_minutes)}", 0
        
        if duration_minutes <= 0:
            return False, f"Duration must be positive, got {duration_minutes}", 0
        
        if duration_minutes > 1440:  # 24 hours
            return False, f"Duration seems too long ({duration_minutes} minutes), possible data error", 0
        
        # Validate heart rate parameters
        if not isinstance(resting_hr, (int, float)) or resting_hr <= 0:
            return False, f"Invalid resting HR: {resting_hr}", 0
        
        if not isinstance(max_hr, (int, float)) or max_hr <= 0:
            return False, f"Invalid max HR: {max_hr}", 0
        
        if max_hr <= resting_hr:
            return False, f"Max HR ({max_hr}) must be greater than resting HR ({resting_hr})", 0
        
        # Validate heart rate range
        if resting_hr < 30 or resting_hr > 100:
            return False, f"Resting HR ({resting_hr}) outside reasonable range (30-100 bpm)", 0
        
        if max_hr < 120 or max_hr > 250:
            return False, f"Max HR ({max_hr}) outside reasonable range (120-250 bpm)", 0
        
        # Validate stream data quality
        valid_samples = 0
        invalid_samples = 0
        hr_values = []
        
        for i, hr_sample in enumerate(hr_stream):
            if not isinstance(hr_sample, (int, float)):
                invalid_samples += 1
                continue
            
            if hr_sample <= 0:
                invalid_samples += 1
                continue
            
            if hr_sample < 30 or hr_sample > 250:
                invalid_samples += 1
                continue
            
            valid_samples += 1
            hr_values.append(hr_sample)
        
        # Check data quality
        if valid_samples == 0:
            return False, "No valid heart rate samples found in stream", 0
        
        if invalid_samples > len(hr_stream) * 0.8:  # More than 80% invalid
            return False, f"Too many invalid samples ({invalid_samples}/{len(hr_stream)})", valid_samples
        
        # Check for reasonable heart rate distribution
        if hr_values:
            avg_hr = sum(hr_values) / len(hr_values)
            if avg_hr < resting_hr * 0.8:  # Average HR too low
                return False, f"Average HR ({avg_hr:.1f}) suspiciously low compared to resting HR ({resting_hr})", valid_samples
            
            if avg_hr > max_hr * 1.1:  # Average HR too high
                return False, f"Average HR ({avg_hr:.1f}) suspiciously high compared to max HR ({max_hr})", valid_samples
        
        return True, "Validation passed", valid_samples
        
    except Exception as e:
        return False, f"Validation error: {str(e)}", 0


def _calculate_trimp_from_stream(duration_minutes, hr_stream, resting_hr, max_hr, k):
    """
    Calculate TRIMP using heart rate stream data for enhanced accuracy.
    Includes comprehensive validation and fallback to average calculation if stream processing fails.
    
    Args:
        duration_minutes (float): Total activity duration in minutes
        hr_stream (list): Heart rate stream data array
        resting_hr (float): Resting heart rate
        max_hr (float): Maximum heart rate
        k (float): Gender coefficient (1.92 for male, 1.67 for female)
    
    Returns:
        float: Calculated TRIMP value rounded to 2 decimal places
    """
    try:
        # Comprehensive validation of input data
        is_valid, error_message, valid_samples_count = _validate_hr_stream_data(
            hr_stream, duration_minutes, resting_hr, max_hr
        )
        
        if not is_valid:
            logger.warning(f"TRIMP_CALC: HR stream validation failed: {error_message}")
            return 0.0
        
        logger.info(f"TRIMP_CALC: Stream validation passed (valid_samples={valid_samples_count}, total_samples={len(hr_stream)})")
        
        # Calculate duration per sample (in minutes)
        # Handle edge case where stream length is 0 (should not happen due to validation above)
        if len(hr_stream) == 0:
            logger.error("Stream length is 0 - cannot distribute duration")
            return 0.0
            
        duration_per_sample = duration_minutes / len(hr_stream)
        
        # Validate duration per sample is reasonable (not too small or too large)
        if duration_per_sample <= 0:
            logger.error(f"Invalid duration per sample: {duration_per_sample}")
            return 0.0
        
        # Log duration distribution for debugging
        logger.info(f"TRIMP_CALC: Duration distribution: {duration_minutes} minutes across {len(hr_stream)} samples = {duration_per_sample:.4f} minutes per sample")
        
        total_trimp = 0.0
        valid_samples = 0
        hr_sum = 0.0  # For fallback average calculation
        skipped_samples = 0
        
        for i, hr_sample in enumerate(hr_stream):
            # Skip invalid heart rate samples
            if hr_sample <= 0:
                skipped_samples += 1
                continue
                
            # Calculate heart rate reserve for this sample
            hr_reserve = (hr_sample - resting_hr) / (max_hr - resting_hr)
            
            # Clamp HR reserve to valid range [0, 1]
            hr_reserve = max(0, min(1, hr_reserve))
            
            # Calculate TRIMP for this sample using Banister's formula
            # Each sample represents duration_per_sample minutes of activity
            sample_trimp = duration_per_sample * hr_reserve * 0.64 * np.exp(k * hr_reserve)
            total_trimp += sample_trimp
            valid_samples += 1
            hr_sum += hr_sample
            
            # Log first few samples for debugging
            if i < 3:
                logger.info(f"TRIMP_CALC: Sample {i}: HR={hr_sample}, HRR={hr_reserve:.3f}, TRIMP={sample_trimp:.4f}")
        
        # Log summary of duration distribution
        if skipped_samples > 0:
            logger.info(f"TRIMP_CALC: Duration distribution: {valid_samples} valid samples, {skipped_samples} skipped samples")
        else:
            logger.info(f"TRIMP_CALC: Duration distribution: {valid_samples} valid samples, no skipped samples")
        
        if valid_samples == 0:
            logger.warning("No valid heart rate samples in stream data - cannot calculate TRIMP")
            return 0.0
        
        # Check if we have enough valid samples (at least 50% of stream)
        if valid_samples < len(hr_stream) * 0.5:
            logger.warning(f"TRIMP_CALC: Low valid sample count ({valid_samples}/{len(hr_stream)}) - using average fallback")
            avg_hr = hr_sum / valid_samples
            logger.info(f"TRIMP_CALC: Falling back to average calculation (avg_hr={avg_hr:.1f})")
            return _calculate_trimp_from_average(duration_minutes, avg_hr, resting_hr, max_hr, k)
        
        # Validate duration distribution is mathematically correct
        expected_total_duration = valid_samples * duration_per_sample
        duration_tolerance = 0.01  # 0.01 minutes tolerance
        
        if abs(expected_total_duration - duration_minutes) > duration_tolerance:
            logger.warning(f"Duration distribution validation failed: expected {expected_total_duration:.4f}, actual {duration_minutes:.4f}")
            # This shouldn't happen with proper math, but log for debugging
        
        # Ensure mathematical precision with proper rounding
        trimp_rounded = _round_trimp_value(total_trimp)
        logger.info(f"TRIMP_CALC: Stream calculation successful: {trimp_rounded} (samples={valid_samples}, duration={duration_minutes}, duration_per_sample={duration_per_sample:.4f})")
        return trimp_rounded
        
    except Exception as e:
        logger.error(f"Error calculating TRIMP from stream: {str(e)} - falling back to average calculation")
        # Fallback to average calculation if stream processing fails
        try:
            # Calculate average HR from stream for fallback
            valid_hrs = [hr for hr in hr_stream if hr > 0]
            if valid_hrs:
                avg_hr = sum(valid_hrs) / len(valid_hrs)
                logger.info(f"TRIMP_CALC: Using fallback average calculation (avg_hr={avg_hr:.1f})")
                return _calculate_trimp_from_average(duration_minutes, avg_hr, resting_hr, max_hr, k)
            else:
                logger.error("No valid heart rate data available for fallback calculation")
                return 0.0
        except Exception as fallback_error:
            logger.error(f"Fallback calculation also failed: {str(fallback_error)}")
            return 0.0


def _calculate_trimp_from_average(duration_minutes, avg_hr, resting_hr, max_hr, k):
    """
    Calculate TRIMP using average heart rate (original method).
    
    Args:
        duration_minutes (float): Activity duration in minutes
        avg_hr (float): Average heart rate for the activity
        resting_hr (float): Resting heart rate
        max_hr (float): Maximum heart rate
        k (float): Gender coefficient (1.92 for male, 1.67 for female)
    
    Returns:
        float: Calculated TRIMP value rounded to 2 decimal places
    """
    try:
        # Calculate heart rate reserve (HRR) as a fraction
        hr_reserve = (avg_hr - resting_hr) / (max_hr - resting_hr)

        # Ensure HR reserve is within valid range (0-1)
        hr_reserve = max(0, min(1, hr_reserve))

        # Calculate TRIMP using Banister's formula
        trimp = duration_minutes * hr_reserve * 0.64 * np.exp(k * hr_reserve)

        # Ensure mathematical precision with proper rounding
        trimp_rounded = _round_trimp_value(trimp)
        logger.info(f"TRIMP_CALC: Average calculation successful: {trimp_rounded} (duration={duration_minutes}, avg_hr={avg_hr}, HRR={hr_reserve:.2f})")
        return trimp_rounded
        
    except Exception as e:
        logger.error(f"Error calculating TRIMP from average: {str(e)}")
        return 0.0


def calculate_hr_zones_from_streams(hr_stream, max_hr=180, resting_hr=60):
    """
    Calculate time spent in heart rate zones from stream data.
    Returns array of seconds in each zone [zone1, zone2, zone3, zone4, zone5].
    """
    if not hr_stream or 'heartrate' not in hr_stream:
        return [0, 0, 0, 0, 0]

    try:
        hr_data = hr_stream['heartrate'].data
        if not hr_data:
            return [0, 0, 0, 0, 0]

        # Calculate HR zones using same logic as Garmin version
        hr_reserve = max_hr - resting_hr

        zones = [
            (resting_hr + 0.5 * hr_reserve, resting_hr + 0.6 * hr_reserve),  # Zone 1
            (resting_hr + 0.6 * hr_reserve, resting_hr + 0.7 * hr_reserve),  # Zone 2
            (resting_hr + 0.7 * hr_reserve, resting_hr + 0.8 * hr_reserve),  # Zone 3
            (resting_hr + 0.8 * hr_reserve, resting_hr + 0.9 * hr_reserve),  # Zone 4
            (resting_hr + 0.9 * hr_reserve, max_hr),  # Zone 5
        ]

        zone_times = [0, 0, 0, 0, 0]

        for hr in hr_data:
            if hr <= 0:
                continue

            for i, (zone_min, zone_max) in enumerate(zones):
                if zone_min <= hr < zone_max:
                    zone_times[i] += 1
                    break

        logger.info(f"HR zone times (seconds): {zone_times}")
        return zone_times

    except Exception as e:
        logger.error(f"Error calculating HR zones: {str(e)}")
        return [0, 0, 0, 0, 0]


def save_training_load(load_data, filename=None):
    """Save training load data to database."""
    try:
        # DIAGNOSTIC LOGGING - START
        logger.info(f"DIAGNOSIS: Starting save_training_load for activity {load_data.get('activity_id')}")

        # Extract data types for logging (avoiding backslash in f-string)
        input_types = [(k, type(v).__name__) for k, v in load_data.items()]
        logger.info(f"DIAGNOSIS: Input data types: {input_types}")

        # Check for specific numpy types in the data
        numpy_types_found = []
        for k, v in load_data.items():
            type_str = str(type(v))
            if type_str.startswith('<class \'numpy.'):
                numpy_types_found.append(f"{k}: {type(v)}")

        if numpy_types_found:
            logger.warning(f"DIAGNOSIS: NumPy types detected BEFORE conversion: {numpy_types_found}")
        else:
            logger.info("DIAGNOSIS: No NumPy types detected in input data")

        # Test if convert_numpy_types function is accessible
        try:
            logger.info("DIAGNOSIS: Testing convert_numpy_types function access...")
            test_result = convert_numpy_types({'test': 42})
            logger.info(f"DIAGNOSIS: convert_numpy_types function is accessible, test result: {test_result}")
        except Exception as func_error:
            logger.error(f"DIAGNOSIS: convert_numpy_types function failed: {func_error}")
            raise

        # In save_training_load(), before conversion:
        numpy_fields = {k: type(v) for k, v in load_data.items() if 'numpy' in str(type(v))}
        if numpy_fields:
            logger.warning(f"SPECIFIC NumPy fields detected: {numpy_fields}")

        # Perform the actual conversion
        try:
            logger.info("DIAGNOSIS: Starting numpy type conversion...")
            load_data = convert_numpy_types(load_data)
            logger.info("DIAGNOSIS: Conversion completed successfully")
        except Exception as conv_error:
            logger.error(f"DIAGNOSIS: Conversion failed with error: {conv_error}")
            raise

        # Check data types after conversion
        after_types = [(k, type(v).__name__) for k, v in load_data.items()]
        logger.info(f"DIAGNOSIS: After conversion types: {after_types}")

        # Check for remaining numpy types after conversion
        remaining_numpy_types = []
        for k, v in load_data.items():
            type_str = str(type(v))
            if type_str.startswith('<class \'numpy.'):
                remaining_numpy_types.append(f"{k}: {type(v)}")

        if remaining_numpy_types:
            logger.error(f"DIAGNOSIS: NumPy types STILL PRESENT after conversion: {remaining_numpy_types}")
        else:
            logger.info("DIAGNOSIS: All NumPy types successfully converted")
        # DIAGNOSTIC LOGGING - END

        # Check if this activity is already in the database
        activity_id = load_data['activity_id']
        user_id = load_data['user_id']
        existing = execute_query(
            "SELECT 1 FROM activities WHERE activity_id = ? AND user_id = ?",
            (activity_id, user_id),
            fetch=True
        )

        if existing:
            logger.info(f"Activity {activity_id} already in database - skipping")
            return

        # Build the INSERT query
        columns = ', '.join(load_data.keys())
        placeholders = ', '.join(['?'] * len(load_data))
        values = tuple(load_data.values())

        # DIAGNOSTIC LOGGING - SQL PREPARATION
        logger.info(f"DIAGNOSIS: SQL columns: {columns}")
        logger.info(f"DIAGNOSIS: SQL placeholders: {placeholders}")

        # Extract types for logging
        sql_value_types = [type(v).__name__ for v in values]
        logger.info(f"DIAGNOSIS: Final SQL values types: {sql_value_types}")

        # Check for numpy types in final SQL values
        sql_numpy_types = []
        problematic_values = []
        for i, v in enumerate(values):
            type_str = str(type(v))
            if type_str.startswith('<class \'numpy.'):
                sql_numpy_types.append(f"Position {i}: {type(v)}")
                problematic_values.append(v)

        if sql_numpy_types:
            logger.error(f"DIAGNOSIS: NumPy types in FINAL SQL VALUES: {sql_numpy_types}")
            logger.error(f"DIAGNOSIS: Problematic values: {problematic_values}")
        else:
            logger.info("DIAGNOSIS: No NumPy types in final SQL values - should work")

        # Insert the record
        logger.info("DIAGNOSIS: About to execute SQL INSERT...")
        execute_query(
            f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
            values
        )

        logger.info(f"DIAGNOSIS: Successfully saved training load data for activity {activity_id}")
        logger.info(f"Saved training load data for activity {activity_id} to database")

    except Exception as e:
        logger.error(f"DIAGNOSIS: Error in save_training_load: {str(e)}")
        logger.error(f"Error saving training load to database: {str(e)}")
        raise


def ensure_daily_records(start_date_str, end_date_str, user_id=None):
    """
    Ensure there are records for every day in the date range for a specific user.
    If no activity exists for a day, a 'Rest Day' record is created.
    FIXED: Only creates rest days for dates that are actually in the past.
    """
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    # Log timezone debug info
    log_timezone_debug()

    start_date = safe_date_parse(start_date_str)
    end_date = safe_date_parse(end_date_str)
    current_date = start_date

    logger.info(f"Ensuring daily records from {start_date_str} to {end_date_str} for user {user_id}")

    # Get current app date for comparison
    app_current_date = get_app_current_date()
    logger.info(f"Current app date (Pacific): {app_current_date}")

    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')

        # Check if any record exists for this date for this user
        existing_record_for_date = execute_query(
            "SELECT 1 FROM activities WHERE date = ? AND user_id = ?",
            (date_str, user_id),
            fetch=True
        )

        if not existing_record_for_date:
            # CRITICAL FIX: Only create rest days for dates that are actually in the past
            if should_create_rest_day(date_str):
                # Double-check that no rest day already exists for this user and date
                existing_rest_day = execute_query(
                    "SELECT 1 FROM activities WHERE date = ? AND user_id = ? AND activity_id < 0",
                    (date_str, user_id),
                    fetch=True
                )

                if existing_rest_day:
                    logger.info(f"Rest day already exists for user {user_id} on {date_str} - skipping")
                else:
                    logger.info(f"Creating rest day for user {user_id} on {date_str} (date is in the past)")

                    # Generate a unique negative activity_id for rest days
                    rest_day_activity_id = -(current_date.toordinal() * 1000 + user_id)

                    new_record = {
                        'activity_id': rest_day_activity_id,
                        'date': date_str,
                        'user_id': user_id,
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

                    execute_query(
                        f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
                        tuple(new_record.values())
                    )

                    logger.info(f"Created rest day record for user {user_id} on {date_str}")
            else:
                logger.info(f"Skipping rest day creation for user {user_id} on {date_str} (date is today or in future)")

        current_date += timedelta(days=1)

    logger.info("Daily records check completed")


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


def update_moving_averages(date, user_id):
    """
    Update moving averages using time-based aggregation.
    Handles SQLite row objects correctly.
    """
    try:
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        logger.info(f"Updating moving averages for {date}, user {user_id} using time-based aggregation")

        # Calculate date ranges
        date_obj = safe_date_parse(date)
        seven_days_ago = (date_obj - timedelta(days=6)).strftime('%Y-%m-%d')
        twentyeight_days_ago = (date_obj - timedelta(days=27)).strftime('%Y-%m-%d')

        logger.info(f"Date ranges: 7-day ({seven_days_ago} to {date}), 28-day ({twentyeight_days_ago} to {date})")

        # Helper function to safely get sum result
        def get_sum_result(query, params):
            try:
                result = execute_query(query, params, fetch=True)
                if result and len(result) > 0:
                    row = result[0]
                    # For SQLite, row is sqlite3.Row object - access by index
                    # For PostgreSQL, row would be dict-like
                    try:
                        # Try direct index access first (works for both SQLite and PostgreSQL)
                        return row[0] or 0
                    except (KeyError, TypeError):
                        # Fallback for dict-like objects
                        if hasattr(row, 'values'):
                            return list(row.values())[0] or 0
                        else:
                            return 0
                return 0
            except Exception as e:
                logger.error(f"Error in get_sum_result: {str(e)}")
                return 0

        # Time-based aggregation for load
        seven_day_sum = get_sum_result(
            "SELECT COALESCE(SUM(total_load_miles), 0) FROM activities WHERE date BETWEEN ? AND ? AND user_id = ?",
            (seven_days_ago, date, user_id)
        )

        twentyeight_day_sum = get_sum_result(
            "SELECT COALESCE(SUM(total_load_miles), 0) FROM activities WHERE date BETWEEN ? AND ? AND user_id = ?",
            (twentyeight_days_ago, date, user_id)
        )

        # Time-based aggregation for TRIMP
        seven_day_trimp_sum = get_sum_result(
            "SELECT COALESCE(SUM(trimp), 0) FROM activities WHERE date BETWEEN ? AND ? AND user_id = ?",
            (seven_days_ago, date, user_id)
        )

        twentyeight_day_trimp_sum = get_sum_result(
            "SELECT COALESCE(SUM(trimp), 0) FROM activities WHERE date BETWEEN ? AND ? AND user_id = ?",
            (twentyeight_days_ago, date, user_id)
        )

        # Calculate daily averages
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

        # Log the calculated values
        logger.info(f"Calculated values for {date}:")
        logger.info(f"  7-day avg load: {seven_day_avg_load} (sum: {seven_day_sum})")
        logger.info(f"  28-day avg load: {twentyeight_day_avg_load} (sum: {twentyeight_day_sum})")
        logger.info(f"  External ACWR: {acute_chronic_ratio}")
        logger.info(f"  Internal ACWR: {trimp_acute_chronic_ratio}")
        logger.info(f"  Normalized divergence: {normalized_divergence}")

        # Update the record
        execute_query(
            """
            UPDATE activities SET 
                seven_day_avg_load = ?,
                twentyeight_day_avg_load = ?,
                seven_day_avg_trimp = ?,
                twentyeight_day_avg_trimp = ?,
                acute_chronic_ratio = ?,
                trimp_acute_chronic_ratio = ?,
                normalized_divergence = ?
            WHERE date = ? AND user_id = ?
            """,
            (seven_day_avg_load, twentyeight_day_avg_load, seven_day_avg_trimp, twentyeight_day_avg_trimp,
             acute_chronic_ratio, trimp_acute_chronic_ratio, normalized_divergence, date, user_id)
        )

        logger.info(f"Successfully updated moving averages for {date}")

    except Exception as e:
        logger.error(f"Error updating moving averages for {date}: {str(e)}")
        raise

def process_activities_for_date_range(client, start_date, end_date=None, hr_config=None, user_id=None):
    """Process Strava activities for the given date range."""
    # Add validation
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    logger.info(f"Processing Strava activities for user {user_id}, date range: {start_date} to {end_date}")

    # Set end_date if not provided
    if end_date is None:
        end_date = start_date

    # Get activities from Strava
    activities = get_activities(client, start_date, end_date)
    processed_count = 0
    skipped_count = 0  # Track skipped activities

    logger.info(f"get_activities returned {len(activities)} activities")

    # Process each activity
    for activity in activities:
        try:
            activity_id = activity.id

            # Determine activity type FIRST
            activity_type = determine_specific_activity_type(activity)
            logger.info(f"Activity {activity_id} type: {activity_type}")

            # Check if this activity type should be processed
            if not is_supported_activity(activity_type):
                logger.info(f"SKIPPING unsupported activity {activity_id}: {activity_type}")
                skipped_count += 1
                continue

            # Check if activity already exists in database
            existing = execute_query(
                "SELECT 1 FROM activities WHERE activity_id = ? AND user_id = ?",
                (activity_id, user_id),
                fetch=True
            )

            if existing:
                logger.info(f"Activity {activity_id} already in database - skipping")
                continue

            # Calculate training load (only for supported activities)
            logger.info(f"PROCESSING supported activity {activity_id}: {activity_type}")
            load_data = calculate_training_load(activity, client, hr_config)
            load_data['user_id'] = user_id

            # Save to database
            save_training_load(load_data)
            processed_count += 1

            # Add small delay to avoid API rate limits
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error processing activity {activity_id}: {str(e)}")
            continue

    logger.info(f"Processed {processed_count} NEW supported activities out of {len(activities)} found")
    logger.info(f"Skipped {skipped_count} unsupported activities")
    return processed_count

def setup_strava_authentication():
    """Set up initial Strava authentication flow."""
    import webbrowser

    print("\n🔑 Strava Authentication Setup")
    print("=" * 40)

    # Get credentials
    client_id = input("Enter your Strava Client ID: ").strip()
    client_secret = input("Enter your Strava Client Secret: ").strip()

    if not client_id or not client_secret:
        print("❌ Client ID and Secret are required")
        return False

    # Create client and get auth URL
    client = Client()
    auth_url = client.authorization_url(
        client_id=client_id,
        redirect_uri="http://localhost",
        scope=['read', 'activity:read_all']
    )

    print(f"\n1. Opening authorization URL in browser...")
    print(f"2. After authorizing, copy the 'code' from the redirect URL")
    webbrowser.open(auth_url)

    auth_code = input("\nEnter authorization code: ").strip()

    if not auth_code:
        print("❌ Authorization code required")
        return False

    try:
        # Exchange code for tokens
        token_response = client.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=auth_code
        )

        # Save tokens
        tokens = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }
        save_tokens(tokens)

        # Get HR config
        hr_config = setup_hr_parameters()

        # Save config
        save_config(client_id, client_secret, hr_config)

        print("✅ Strava authentication setup complete!")
        return True

    except Exception as e:
        print(f"❌ Authentication failed: {str(e)}")
        return False


def main():
    """Main function - same approach as run_full_sync.py."""
    parser = argparse.ArgumentParser(description='Strava Training Load Tracker with Banister TRIMP')
    parser.add_argument('--days', type=int, default=7, help='Number of days to process (default: 7)')
    parser.add_argument('--setup', action='store_true', help='Run initial setup/authentication')
    args = parser.parse_args()

    print("\nStrava Training Load Tracker with Banister TRIMP")
    print("------------------------------------------------")

    # Initialize database
    initialize_db()

    # Check if setup is needed
    if args.setup or not os.path.exists(CONFIG_FILE) or not os.path.exists(TOKENS_FILE):
        if not setup_strava_authentication():
            return

    # Load configuration
    client_id, client_secret, hr_config = load_config()
    if not client_id or not client_secret:
        print("❌ Configuration missing. Run with --setup")
        return

    if not hr_config:
        print("❌ HR configuration missing. Run with --setup")
        return

    # Connect to Strava
    print("\nConnecting to Strava...")
    client = connect_to_strava()
    if not client:
        print("❌ Failed to connect to Strava")
        return

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Process activities (same approach as run_full_sync.py)
    print(f"Processing activities from {start_date_str} to {end_date_str}...")
    count = process_activities_for_date_range(client, start_date_str, end_date_str, hr_config)
    print(f"Processed {count} new activities.")

    # Ensure daily records for dashboard range (same as run_full_sync.py)
    dashboard_start = (end_date - timedelta(days=90)).strftime('%Y-%m-%d')
    print(f"Ensuring daily records for dashboard range: {dashboard_start} to {end_date_str}...")
    ensure_daily_records(dashboard_start, end_date_str)

    # Update moving averages for all affected dates
    print("Updating moving averages...")
    dashboard_start_date = end_date - timedelta(days=90)
    current_date = dashboard_start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        update_moving_averages(date_str)
        current_date += timedelta(days=1)

    print("\n✅ Strava processing complete!")


if __name__ == "__main__":
    main()