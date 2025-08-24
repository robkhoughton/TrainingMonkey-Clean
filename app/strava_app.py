#!/usr/bin/env python3
"""
Strava Sync Service for Training Monkey™ Dashboard
Updated version of strava_app.py to use Strava instead of Garmin
"""

import os
import logging
import time
import json
import db_utils
from datetime import datetime, timedelta, date
from timezone_utils import get_app_current_date, log_timezone_debug
from llm_recommendations_module import generate_recommendations, update_recommendations_with_autopsy_learning
from flask import Flask, request, jsonify, redirect, url_for, render_template, send_from_directory, session, flash, Response
from google.cloud import secretmanager
from enhanced_token_management import SimpleTokenManager, check_token_status
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from auth import User
from settings_utils import handle_settings_change, track_settings_changes
from werkzeug.security import generate_password_hash
import secrets
from sync_fix import apply_sync_fix

# Import Strava processing functions
from strava_training_load import (
    connect_to_strava,
    process_activities_for_date_range,
    ensure_daily_records,
    update_moving_averages,
    load_tokens,
    save_tokens
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access your training dashboard.'

@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to reload user from session"""
    return User.get(user_id)

def get_secret(secret_name, project_id=None):
    """Get secret from Google Secret Manager"""
    try:
        if not project_id:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'dev-ruler-460822-e8')

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error getting secret {secret_name}: {str(e)}")
        return None

def ensure_date_serialization(data):
    """
    Ensure all date objects in data are properly serialized for JSON
    Handles the conversion from PostgreSQL DATE type to frontend-compatible strings
    CRITICAL FIX: After database DATE standardization, PostgreSQL returns date objects
    that need to be converted to ISO strings for React compatibility
    """

    if isinstance(data, dict):
        for key, value in data.items():
            if key in ['date', 'created_at', 'updated_at', 'generation_date', 'latest_activity_date', 'lastActivity']:
                if isinstance(value, date):
                    # PostgreSQL DATE type → ISO string
                    data[key] = value.isoformat()
                elif isinstance(value, datetime):
                    # PostgreSQL TIMESTAMP type → ISO string
                    data[key] = value.isoformat()
                elif isinstance(value, str) and value:
                    # Validate and normalize string dates
                    try:
                        # Try parsing as date first
                        parsed = datetime.strptime(value, '%Y-%m-%d')
                        data[key] = parsed.strftime('%Y-%m-%d')
                    except:
                        try:
                            # Try parsing as datetime
                            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            data[key] = parsed.isoformat()
                        except:
                            # Leave as-is if can't parse
                            pass
            else:
                # Recursively handle nested objects
                data[key] = ensure_date_serialization(value)
    elif isinstance(data, list):
        return [ensure_date_serialization(item) for item in data]

    return data


def aggregate_daily_activities_with_rest(activities):
    """
    ENHANCED: Aggregate activities by day but preserve rest days AND sport breakdown.

    Now tracks running vs cycling breakdown for multi-sport visualization while
    maintaining all existing logic and backward compatibility.
    """
    daily_aggregates = {}

    for activity in activities:
        date = activity['date']
        activity_id = activity['activity_id']

        # If it's a rest day (negative activity_id), keep it as-is
        if activity_id <= 0:
            if date not in daily_aggregates:
                daily_aggregates[date] = activity.copy()
                daily_aggregates[date]['is_rest_day'] = True
                # Initialize sport breakdown fields for rest days
                daily_aggregates[date]['running_load'] = 0
                daily_aggregates[date]['cycling_load'] = 0
                daily_aggregates[date]['running_distance'] = 0
                daily_aggregates[date]['cycling_distance'] = 0
                daily_aggregates[date]['sport_types'] = []
                daily_aggregates[date]['activities'] = []
                daily_aggregates[date]['day_type'] = 'rest'
            # If there's already an entry for this date and it's not a rest day,
            # the real activities take precedence
            elif not daily_aggregates[date].get('is_rest_day', False):
                continue  # Keep the real activity
            else:
                daily_aggregates[date] = activity.copy()
                daily_aggregates[date]['is_rest_day'] = True
                # Initialize sport breakdown fields for rest days
                daily_aggregates[date]['running_load'] = 0
                daily_aggregates[date]['cycling_load'] = 0
                daily_aggregates[date]['running_distance'] = 0
                daily_aggregates[date]['cycling_distance'] = 0
                daily_aggregates[date]['sport_types'] = []
                daily_aggregates[date]['activities'] = []
                daily_aggregates[date]['day_type'] = 'rest'

        else:
            # Real activity - aggregate if there are multiple
            if date not in daily_aggregates or daily_aggregates[date].get('is_rest_day', False):
                # First real activity of the day, or replacing a rest day
                daily_aggregates[date] = activity.copy()
                daily_aggregates[date]['activity_count'] = 1
                daily_aggregates[date]['is_rest_day'] = False

                # NEW: Initialize sport breakdown fields
                sport_type = activity.get('sport_type', 'running')
                daily_aggregates[date]['sport_types'] = [sport_type]
                daily_aggregates[date]['activities'] = [{
                    'type': activity.get('type', 'Unknown'),
                    'sport': sport_type,
                    'distance': activity.get('distance_miles', 0),
                    'load': activity.get('total_load_miles', 0),
                    'cycling_equivalent': activity.get('cycling_equivalent_miles'),
                    'average_speed': activity.get('average_speed_mph')
                }]

                # Set sport-specific loads
                if sport_type == 'cycling':
                    daily_aggregates[date]['cycling_load'] = activity.get('total_load_miles', 0)
                    daily_aggregates[date]['running_load'] = 0
                    daily_aggregates[date]['cycling_distance'] = activity.get('distance_miles', 0)
                    daily_aggregates[date]['running_distance'] = 0
                    daily_aggregates[date]['day_type'] = 'cycling'
                else:  # running or other
                    daily_aggregates[date]['running_load'] = activity.get('total_load_miles', 0)
                    daily_aggregates[date]['cycling_load'] = 0
                    daily_aggregates[date]['running_distance'] = activity.get('distance_miles', 0)
                    daily_aggregates[date]['cycling_distance'] = 0
                    daily_aggregates[date]['day_type'] = 'running'

            else:
                # Additional real activity - aggregate
                existing = daily_aggregates[date]
                sport_type = activity.get('sport_type', 'running')

                # EXISTING AGGREGATION LOGIC (preserved exactly from your current function)
                existing['distance_miles'] += activity['distance_miles'] or 0
                existing['elevation_gain_feet'] += activity['elevation_gain_feet'] or 0
                existing['elevation_load_miles'] += activity['elevation_load_miles'] or 0
                existing['total_load_miles'] += activity['total_load_miles'] or 0
                existing['duration_minutes'] += activity['duration_minutes'] or 0
                existing['trimp'] += activity['trimp'] or 0

                # Sum HR zone times (your existing logic)
                for i in range(1, 6):
                    existing[f'time_in_zone{i}'] += activity[f'time_in_zone{i}'] or 0

                # Duration-weighted average of heart rates (your existing logic)
                total_duration = existing['duration_minutes']
                if total_duration > 0 and activity['duration_minutes'] > 0:
                    existing_duration = total_duration - activity['duration_minutes']

                    if existing['avg_heart_rate'] > 0 and activity['avg_heart_rate'] > 0:
                        existing['avg_heart_rate'] = (
                                (existing['avg_heart_rate'] * existing_duration +
                                 activity['avg_heart_rate'] * activity['duration_minutes']) / total_duration
                        )

                    # Take max of max HR (your existing logic)
                    if activity['max_heart_rate'] > existing['max_heart_rate']:
                        existing['max_heart_rate'] = activity['max_heart_rate']

                # Keep the latest calculated metrics (your existing logic)
                existing['seven_day_avg_load'] = activity['seven_day_avg_load']
                existing['twentyeight_day_avg_load'] = activity['twentyeight_day_avg_load']
                existing['seven_day_avg_trimp'] = activity['seven_day_avg_trimp']
                existing['twentyeight_day_avg_trimp'] = activity['twentyeight_day_avg_trimp']
                existing['acute_chronic_ratio'] = activity['acute_chronic_ratio']
                existing['trimp_acute_chronic_ratio'] = activity['trimp_acute_chronic_ratio']
                existing['normalized_divergence'] = activity['normalized_divergence']

                # Update activity count and name (your existing logic)
                existing['activity_count'] += 1
                if existing['activity_count'] == 2:
                    existing['name'] = f"{existing['name']} + 1 more"
                else:
                    base_name = existing['name'].split(' + ')[0]
                    existing['name'] = f"{base_name} + {existing['activity_count'] - 1} more"

                existing['activity_id'] = activity['activity_id']  # Use latest
                existing['is_aggregated'] = True

                # NEW: Update sport breakdown tracking
                if sport_type not in existing.get('sport_types', []):
                    if 'sport_types' not in existing:
                        existing['sport_types'] = []
                    existing['sport_types'].append(sport_type)

                # Add to sport-specific loads
                if sport_type == 'cycling':
                    existing['cycling_load'] = existing.get('cycling_load', 0) + activity.get('total_load_miles', 0)
                    existing['cycling_distance'] = existing.get('cycling_distance', 0) + activity.get('distance_miles',
                                                                                                      0)
                else:  # running or other
                    existing['running_load'] = existing.get('running_load', 0) + activity.get('total_load_miles', 0)
                    existing['running_distance'] = existing.get('running_distance', 0) + activity.get('distance_miles',
                                                                                                      0)

                # Add activity details
                if 'activities' not in existing:
                    existing['activities'] = []
                existing['activities'].append({
                    'type': activity.get('type', 'Unknown'),
                    'sport': sport_type,
                    'distance': activity.get('distance_miles', 0),
                    'load': activity.get('total_load_miles', 0),
                    'cycling_equivalent': activity.get('cycling_equivalent_miles'),
                    'average_speed': activity.get('average_speed_mph')
                })

                # Update day type based on sport types
                if len(existing.get('sport_types', [])) > 1:
                    existing['day_type'] = 'mixed'
                elif 'cycling' in existing.get('sport_types', []):
                    existing['day_type'] = 'cycling'
                else:
                    existing['day_type'] = 'running'

    # Convert back to list, sorted by date (your existing logic)
    result = sorted(daily_aggregates.values(), key=lambda x: x['date'])

    # Ensure all entries have sport breakdown fields for backward compatibility
    for daily_data in result:
        if 'running_load' not in daily_data:
            daily_data['running_load'] = daily_data.get('total_load_miles', 0) if not daily_data.get(
                'is_rest_day') else 0
        if 'cycling_load' not in daily_data:
            daily_data['cycling_load'] = 0
        if 'running_distance' not in daily_data:
            daily_data['running_distance'] = daily_data.get('distance_miles', 0) if not daily_data.get(
                'is_rest_day') else 0
        if 'cycling_distance' not in daily_data:
            daily_data['cycling_distance'] = 0
        if 'sport_types' not in daily_data:
            daily_data['sport_types'] = [] if daily_data.get('is_rest_day') else ['running']
        if 'activities' not in daily_data:
            if daily_data.get('is_rest_day'):
                daily_data['activities'] = []
            else:
                daily_data['activities'] = [{
                    'type': daily_data.get('type', 'Unknown'),
                    'sport': 'running',
                    'distance': daily_data.get('distance_miles', 0),
                    'load': daily_data.get('total_load_miles', 0)
                }]
        if 'day_type' not in daily_data:
            daily_data['day_type'] = 'rest' if daily_data.get('is_rest_day') else 'running'

    return result


def is_feature_enabled(feature_name, user_id=None):
    """
    Check if feature is enabled - allows gradual rollout to beta users

    PHASE 1 ROLLOUT PLAN:
    - Rob (user_id=1): Admin access (already enabled)
    - tballaine (user_id=2): Beta user #1
    - iz.houghton (user_id=3): Beta user #2

    Args:
        feature_name (str): Name of the feature to check
        user_id (int): User ID to check feature access for

    Returns:
        bool: True if feature is enabled for the user, False otherwise
    """

    # Feature flag configuration
    feature_flags = {
        'settings_page_enabled': False,  # Default OFF for general users
        'hr_zone_recalculation': False,  # Default OFF
        'enhanced_ai_context': False,  # Default OFF
        'settings_validation_strict': True  # Default ON for safety
    }

    # Get base enabled state
    base_enabled = feature_flags.get(feature_name, False)

    # Special handling for Settings page rollout
    if feature_name == 'settings_page_enabled':

        # PHASE 1: Admin + Beta Users (Rob, tballaine, iz.houghton)
        beta_user_ids = [1, 2, 3]  # Rob (admin), tballaine, iz.houghton

        if user_id in beta_user_ids:
            logger.info(f"🎉 Settings page access granted to user {user_id} (beta rollout)")
            return True

        # All other users: Settings page disabled
        logger.info(f"⏳ Settings page access denied to user {user_id} (not in beta rollout)")
        return False

    # For other features, check admin access first
    if user_id == 1:  # Rob's admin account gets early access to all new features
        logger.info(f"🔧 Admin early access granted for {feature_name} to user {user_id}")
        return True

    # Return base flag state for non-admin users
    return base_enabled

@app.route('/sync', methods=['POST'])
def sync_strava_data():
    """Main sync endpoint - processes Strava data"""
    try:
        logger.info("=== STARTING STRAVA SYNC ===")
        data = request.get_json() or {}
        logger.info(f"Received sync request with data keys: {list(data.keys())}")

        # Get parameters from request
        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        days = data.get('days', 7)
        user_id = data.get('user_id')  # Get user_id from request

        # If no user_id provided, try to use current_user if available
        if not user_id:
            try:
                user_id = current_user.id
            except:
                return jsonify({'error': 'user_id required for multi-user support'}), 400

        logger.info(f"Sync parameters: days={days}")

        # Get HR config from request or use defaults
        hr_config = data.get('hr_config', {
            'resting_hr': 44,  # Your values from testing
            'max_hr': 178,
            'gender': 'male'
        })

        logger.info(f"HR config: {hr_config}")

        # Validate required parameters
        if not access_token:
            logger.error("Missing Strava access token")
            return jsonify({'error': 'Strava access token required'}), 400

        # Save tokens for the session
        if refresh_token:
            tokens = {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_at': int(time.time()) + 21600  # 6 hours from now
            }
            save_tokens(tokens)

        # Connect to Strava using token
        logger.info("Attempting to connect to Strava...")
        from stravalib.client import Client
        client = Client(access_token=access_token)

        # Test connection
        try:
            athlete = client.get_athlete()
            logger.info(f"Connected to Strava as {athlete.firstname} {athlete.lastname}")
        except Exception as e:
            logger.error(f"Strava connection test failed: {str(e)}")
            return jsonify({'error': 'Failed to connect to Strava'}), 400

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        logger.info(f"Processing activities from {start_date_str} to {end_date_str}")

        # Process activities
        logger.info("Starting activity processing...")
        activities_count = process_activities_for_date_range(
            client,
            start_date_str,
            end_date_str,
            hr_config,
            user_id=user_id
        )

        logger.info(f"Processed {activities_count} activities")

        # Ensure daily records exist for all dates
        logger.info("Ensuring daily records...")
        ensure_daily_records(start_date_str, end_date_str, user_id=user_id)

        # Update moving averages for the entire range
        logger.info("Updating moving averages...")
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Updating averages for {date_str}")
            update_moving_averages(date_str, user_id=user_id)
            current_date += timedelta(days=1)

        # Success response
        result = {
            'success': True,
            'message': f'Successfully processed {activities_count} activities',
            'activities_processed': activities_count,
            'date_range': f'{start_date_str} to {end_date_str}',
            'sync_timestamp': datetime.now().isoformat()
        }

        logger.info(f"=== SYNC COMPLETED SUCCESSFULLY: {result} ===")
        return jsonify(result)

    except Exception as e:
        error_msg = f"Sync error: {str(e)}"
        logger.error(f"=== SYNC FAILED: {error_msg} ===", exc_info=True)

        return jsonify({
            'error': error_msg,
            'error_type': type(e).__name__,
            'success': False
        }), 500


@app.route('/test-connection', methods=['POST'])
def test_strava_connection():
    """Test Strava connection without syncing data"""
    try:
        data = request.get_json() or {}
        access_token = data.get('access_token')

        if not access_token:
            return jsonify({'error': 'Strava access token required'}), 400

        logger.info("Testing Strava connection...")
        from stravalib.client import Client
        client = Client(access_token=access_token)

        try:
            athlete = client.get_athlete()
            return jsonify({
                'success': True,
                'message': f'Successfully connected to Strava as {athlete.firstname} {athlete.lastname}',
                'athlete_id': athlete.id,
                'connection_test': True
            })
        except Exception as e:
            logger.error(f"Strava connection failed: {str(e)}")
            return jsonify({'error': f'Strava connection failed: {str(e)}'}), 400

    except Exception as e:
        error_msg = f"Connection test error: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500


@login_required
@app.route('/oauth-callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callback - supports both shared app and user-provided credentials"""
    try:
        import os

        # Get the authorization code from URL parameters
        auth_code = request.args.get('code')

        if not auth_code:
            return jsonify({'error': 'No authorization code received'}), 400

        # Try to get credentials from session first (user-provided), then environment (shared app)
        client_id = session.get('temp_strava_client_id') or os.environ.get('STRAVA_CLIENT_ID')
        client_secret = session.get('temp_strava_client_secret') or os.environ.get('STRAVA_CLIENT_SECRET')

        if not client_id or not client_secret:
            return jsonify({'error': 'Missing Strava application credentials'}), 400

        logger.info("Processing OAuth callback...")

        from stravalib.client import Client
        client = Client()

        # Exchange code for tokens
        token_response = client.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=auth_code
        )

        # Get athlete info
        temp_client = Client(access_token=token_response['access_token'])
        athlete = temp_client.get_athlete()

        # Save tokens to database
        token_manager = SimpleTokenManager(user_id=current_user.id)

        tokens = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at']
        }

        success = token_manager.save_tokens_to_database(tokens, athlete.id)

        if session.get('temp_strava_client_id') and session.get('temp_strava_client_secret'):
            # These are user-provided credentials, save them permanently
            credentials_saved = token_manager.save_user_strava_credentials(
                session.get('temp_strava_client_id'),
                session.get('temp_strava_client_secret')
            )

            if credentials_saved:
                logger.info(f"Saved user-specific Strava credentials for user {current_user.id}")
            else:
                logger.warning(f"Failed to save user-specific Strava credentials for user {current_user.id}")

        # Clear temporary session data
        session.pop('temp_strava_client_id', None)
        session.pop('temp_strava_client_secret', None)

        if success:
            logger.info(f"OAuth tokens saved for {athlete.firstname} {athlete.lastname}")
            return f'''
            <html>
            <head><title>Strava Connected</title></head>
            <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center;">
                <h2>✅ Strava Account Connected!</h2>
                <p>Successfully connected to Strava as <strong>{athlete.firstname} {athlete.lastname}</strong></p>

                <div style="background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Next Step: Sync Your Training Data</h3>
                    <p>Click below to import your recent activities:</p>
                    <button onclick="syncData()" id="syncBtn" style="background: #007bff; color: white; padding: 12px 25px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin: 10px;">
                        Sync Strava Activities
                    </button>
                    <div id="syncStatus" style="margin-top: 15px;"></div>
                </div>

                <p><a href="/static/index.html" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go to Dashboard</a></p>

                <script>
                async function syncData() {{
                    const btn = document.getElementById('syncBtn');
                    const status = document.getElementById('syncStatus');

                    btn.disabled = true;
                    btn.textContent = 'Syncing...';
                    status.innerHTML = '<p>Syncing your Strava activities...</p>';

                    try {{
                        const response = await fetch('/sync-with-auto-refresh', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ days: 30 }})
                        }});

                        const result = await response.json();

                        if (result.success) {{
                            status.innerHTML = '<p style="color: green;">✅ Sync completed! ' + result.message + '</p>';
                            btn.textContent = 'Sync Complete';
                        }} else {{
                            status.innerHTML = '<p style="color: red;">❌ Sync failed: ' + result.error + '</p>';
                            btn.textContent = 'Retry Sync';
                            btn.disabled = false;
                        }}
                    }} catch (error) {{
                        status.innerHTML = '<p style="color: red;">❌ Error: ' + error.message + '</p>';
                        btn.textContent = 'Retry Sync';
                        btn.disabled = false;
                    }}
                }}
                </script>
            </body>
            </html>
            ''', 200, {'Content-Type': 'text/html'}

        else:
            return jsonify({'error': 'Failed to save tokens to database'}), 500

    except Exception as e:
        error_msg = f"OAuth callback error: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500


@login_required
@app.route('/token-status', methods=['GET'])
def get_token_status():
    """Simple endpoint to check token status for current user"""
    try:
        status = check_token_status(user_id=current_user.id)  # ✅ FIXED: Use current user

        return jsonify({
            'success': True,
            'token_status': status,
            'user_id': current_user.id,  # Add for debugging
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting token status for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/sync-with-auto-refresh', methods=['POST'])
def sync_with_automatic_token_management():
    """Enhanced sync endpoint that handles both user and scheduled requests"""
    try:
        logger.info("=== SYNC STARTED - Testing basic functionality ===")

        # Test basic imports
        try:
            logger.info("✅ sync_fix import successful")
            apply_sync_fix()
            logger.info("✅ apply_sync_fix() completed")
        except Exception as e:
            logger.error(f"❌ sync_fix error: {str(e)}")

        # Test user authentication
        try:
            user_id = current_user.id
            logger.info(f"✅ User authenticated: {user_id}")
        except Exception as e:
            logger.error(f"❌ Authentication error: {str(e)}")
            return jsonify({'error': f'Authentication failed: {str(e)}'}), 401

        logger.info("=== STARTING ENHANCED STRAVA SYNC WITH AUTO TOKEN REFRESH ===")

        data = request.get_json() or {}
        days = data.get('days', 7)
        logger.info(f"Sync parameters: days={days}")

        # Check if this is a scheduled request (from Cloud Scheduler)
        is_scheduled_request = request.headers.get('X-Cloudscheduler') == 'true'

        if is_scheduled_request:
            logger.info("Processing scheduled sync request for all users")

            # Get all users with Strava tokens for scheduled sync
            query = """
                SELECT id, email 
                FROM user_settings 
                WHERE strava_access_token IS NOT NULL 
                  AND strava_refresh_token IS NOT NULL
                ORDER BY id
            """

            try:
                users = db_utils.execute_query(query, fetch=True)
                logger.info(f"Found {len(users) if users else 0} users for scheduled sync")
            except Exception as e:
                logger.error(f"❌ Database query for users failed: {str(e)}")
                return jsonify({'error': f'Database error: {str(e)}'}), 500

            if not users:
                logger.info("No users with Strava tokens found for scheduled sync")
                return jsonify({
                    'success': True,
                    'message': 'No users to sync',
                    'users_processed': 0,
                    'sync_timestamp': datetime.now().isoformat()
                })

            # Process each user
            results = []
            total_activities = 0

            for user in users:
                user_id = user['id']
                logger.info(f"Processing scheduled sync for user {user_id}")

                try:
                    result = process_user_sync(user_id, days)
                    results.append(result)
                    total_activities += result.get('activities_processed', 0)
                except Exception as e:
                    logger.error(f"Error processing user {user_id}: {str(e)}")
                    results.append({
                        'user_id': user_id,
                        'success': False,
                        'error': str(e)
                    })

            return jsonify({
                'success': True,
                'message': f'Scheduled sync completed for {len(users)} users',
                'users_processed': len(users),
                'total_activities_processed': total_activities,
                'results': results,
                'sync_timestamp': datetime.now().isoformat()
            })

        else:
            # Manual sync request - single user
            logger.info(f"Processing manual sync request for user {user_id}")

            # Get token manager for this user
            try:
                from enhanced_token_management import SimpleTokenManager
                token_manager = SimpleTokenManager(user_id)
                logger.info("✅ SimpleTokenManager created successfully")
            except Exception as e:
                logger.error(f"❌ SimpleTokenManager creation failed: {str(e)}")
                return jsonify({'error': f'Token manager error: {str(e)}'}), 500

            # Get token status before sync
            try:
                token_status_before = token_manager.get_simple_token_status()
                logger.info(f"Token status before sync: {token_status_before}")
            except Exception as e:
                logger.error(f"❌ Token status check failed: {str(e)}")
                return jsonify({'error': f'Token status error: {str(e)}'}), 500

            # Get authenticated client (auto-refreshes if needed)
            try:
                client = token_manager.get_working_strava_client()
                if not client:
                    logger.error("Failed to get authenticated client - client is None")
                    return jsonify({
                        'success': False,
                        'error': 'Failed to get Strava client. Check token status.',
                        'token_status': token_status_before
                    })
                else:
                    logger.info("✅ Strava client obtained successfully")
            except Exception as e:
                logger.error(f"❌ Strava client creation failed: {str(e)}")
                return jsonify({'error': f'Strava client error: {str(e)}'}), 500

            # Calculate date range
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                logger.info(f"Processing activities from {start_date_str} to {end_date_str}")
                logger.info(f"Current time: {end_date}")
            except Exception as e:
                logger.error(f"❌ Date calculation failed: {str(e)}")
                return jsonify({'error': f'Date calculation error: {str(e)}'}), 500

            # Get HR config
            hr_config = {
                'resting_hr': 44,
                'max_hr': 178,
                'gender': 'male'
            }
            logger.info(f"HR config: {hr_config}")

            # Process activities using existing function
            try:
                logger.info("Starting activity processing...")
                from strava_training_load import process_activities_for_date_range
                activities_count = process_activities_for_date_range(
                    client,
                    start_date_str,
                    end_date_str,
                    hr_config,
                    user_id=user_id
                )
                logger.info(f"✅ Processed {activities_count} activities for user {user_id}")
            except Exception as e:
                logger.error(f"❌ Activity processing failed: {str(e)}")
                return jsonify({'error': f'Activity processing error: {str(e)}'}), 500

            # Ensure daily records and update averages
            try:
                logger.info("Ensuring daily records...")
                from strava_training_load import ensure_daily_records, update_moving_averages
                ensure_daily_records(start_date_str, end_date_str, user_id=user_id)
                logger.info("✅ Daily records ensured")
            except Exception as e:
                logger.error(f"❌ Daily records failed: {str(e)}")
                return jsonify({'error': f'Daily records error: {str(e)}'}), 500

            try:
                logger.info("Updating moving averages...")
                current_date = start_date
                while current_date <= end_date:
                    date_str = current_date.strftime('%Y-%m-%d')
                    update_moving_averages(date_str, user_id=user_id)
                    current_date += timedelta(days=1)
                logger.info("✅ Moving averages updated")
            except Exception as e:
                logger.error(f"❌ Moving averages failed: {str(e)}")
                return jsonify({'error': f'Moving averages error: {str(e)}'}), 500

            # Get final token status
            try:
                final_token_status = token_manager.get_simple_token_status()
                logger.info(f"Final token status: {final_token_status}")
            except Exception as e:
                logger.error(f"❌ Final token status failed: {str(e)}")
                final_token_status = {'error': str(e)}

            return jsonify({
                'success': True,
                'message': f'Successfully processed {activities_count} activities',
                'activities_processed': activities_count,
                'date_range': f'{start_date_str} to {end_date_str}',
                'token_management': {
                    'initial_status': token_status_before,
                    'final_status': final_token_status
                },
                'sync_timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        import traceback
        full_error = traceback.format_exc()
        logger.error("=== FULL SYNC ERROR ===")
        logger.error(full_error)
        return jsonify({
            'error': str(e),
            'full_error': full_error,
            'success': False
        }), 500


def process_user_sync(user_id, days):
    """Process sync for a specific user"""
    try:
        # Get HR config from user settings or use defaults
        hr_config = {
            'resting_hr': 44,
            'max_hr': 178,
            'gender': 'male'
        }

        # Try to get user's HR settings from database
        try:
            user_hr_query = """
                SELECT resting_hr, max_hr, gender 
                FROM user_settings 
                WHERE id = ?
            """
            user_hr_result = db_utils.execute_query(user_hr_query, (user_id,), fetch=True)

            if user_hr_result and user_hr_result[0]:
                hr_data = user_hr_result[0]
                if hr_data.get('resting_hr'):
                    hr_config['resting_hr'] = hr_data['resting_hr']
                if hr_data.get('max_hr'):
                    hr_config['max_hr'] = hr_data['max_hr']
                if hr_data.get('gender'):
                    hr_config['gender'] = hr_data['gender']

        except Exception as e:
            logger.warning(f"Could not load HR config for user {user_id}, using defaults: {str(e)}")

        logger.info(f"Enhanced sync parameters: days={days}, user_id={user_id}")

        # Use token manager to get valid client (handles refresh automatically)
        token_manager = SimpleTokenManager(user_id)

        # Get token status before sync
        token_status_before = token_manager.get_simple_token_status()
        logger.info(f"Token status before sync for user {user_id}: {token_status_before}")

        # Get valid client (this will refresh tokens if needed)
        client = token_manager.get_working_strava_client()

        if not client:
            error_status = token_manager.get_simple_token_status()
            logger.error(f"Failed to obtain valid Strava client for user {user_id}")
            return {
                'success': False,
                'error': 'Failed to obtain valid Strava client. Token refresh may have failed.',
                'token_status': error_status
            }

        # Get token status after getting client (may have refreshed)
        token_status_after = token_manager.get_simple_token_status()
        token_was_refreshed = (token_status_before.get('expires_in_hours', 0) !=
                               token_status_after.get('expires_in_hours', 0))

        if token_was_refreshed:
            logger.info(f"Tokens were automatically refreshed for user {user_id}")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        logger.info(f"Processing activities for user {user_id} from {start_date_str} to {end_date_str}")

        # Process activities using existing function
        from strava_training_load import process_activities_for_date_range
        activities_count = process_activities_for_date_range(
            client,
            start_date_str,
            end_date_str,
            hr_config,
            user_id=user_id
        )

        logger.info(f"Processed {activities_count} activities for user {user_id}")

        # Ensure daily records and update averages (existing functions)
        from strava_training_load import ensure_daily_records, update_moving_averages
        ensure_daily_records(start_date_str, end_date_str, user_id=user_id)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            update_moving_averages(date_str, user_id=user_id)
            current_date += timedelta(days=1)

        # Get final token status
        final_token_status = token_manager.get_simple_token_status()

        return {
            'success': True,
            'message': f'Successfully processed {activities_count} activities',
            'activities_processed': activities_count,
            'date_range': f'{start_date_str} to {end_date_str}',
            'token_management': {
                'token_refreshed': token_was_refreshed,
                'status_before': token_status_before,
                'status_after': final_token_status
            }
        }

    except Exception as e:
        logger.error(f"Error in process_user_sync for user {user_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'activities_processed': 0
        }


@login_required
@app.route('/refresh-tokens', methods=['POST'])
def manual_refresh_tokens():
    """Simple endpoint to manually refresh tokens for current user"""
    try:
        logger.info(f"Manual token refresh requested for user {current_user.id}...")

        token_manager = SimpleTokenManager(user_id=current_user.id)  # ✅ FIXED

        # Get status before refresh
        old_status = token_manager.get_simple_token_status()

        new_tokens = token_manager.refresh_strava_tokens()

        if new_tokens:
            new_status = token_manager.get_simple_token_status()
            logger.info(f"Manual token refresh successful for user {current_user.id}")

            return jsonify({
                'success': True,
                'message': 'Tokens refreshed successfully',
                'old_status': old_status,
                'new_status': new_status
            })
        else:
            logger.error(f"Manual token refresh failed for user {current_user.id}")
            return jsonify({
                'success': False,
                'message': 'Token refresh failed',
                'current_status': old_status
            }), 400

    except Exception as e:
        logger.error(f"Manual refresh error for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@login_required
@app.route('/admin/token-health-report', methods=['GET'])
def token_health_report():
    """Detailed token health report for monitoring"""
    try:
        user_id = current_user.id  # ✅ FIXED: Use current user
        token_manager = SimpleTokenManager(user_id)

        # Get comprehensive token status
        token_status = token_manager.get_simple_token_status()

        # Test API connectivity
        api_test_result = None
        try:
            # CORRECTED: Use the correct method name
            client = token_manager.get_working_strava_client()
            if client:
                athlete = client.get_athlete()
                api_test_result = {
                    'success': True,
                    'athlete_name': f"{athlete.firstname} {athlete.lastname}",
                    'athlete_id': athlete.id,
                    'test_timestamp': datetime.now().isoformat()
                }
            else:
                api_test_result = {
                    'success': False,
                    'error': 'Failed to get valid client',
                    'test_timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            api_test_result = {
                'success': False,
                'error': str(e),
                'test_timestamp': datetime.now().isoformat()
            }

        # Calculate time until refresh needed
        refresh_recommendation = "No action needed"
        if token_status['status'] == 'expired':
            refresh_recommendation = "URGENT: Manual re-authorization required"
        elif token_status['status'] == 'expiring_soon':
            refresh_recommendation = "Automatic refresh should occur within 30 minutes"
        elif token_status['status'] == 'valid':
            hours_until_refresh = token_status.get('expires_in_hours', 0) - 0.5  # 30 min buffer
            if hours_until_refresh > 0:
                refresh_recommendation = f"Next automatic refresh in ~{hours_until_refresh:.1f} hours"

        report = {
            'report_timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'token_status': token_status,
            'api_connectivity': api_test_result,
            'refresh_recommendation': refresh_recommendation,
            'system_health': {
                'database_connected': True,  # If we got here, DB is working
                'service_operational': True,
                'last_check': datetime.now().isoformat()
            }
        }

        # Determine alert level
        if token_status['status'] == 'expired' or not api_test_result['success']:
            alert_level = 'CRITICAL'
            http_status = 503
        elif token_status['status'] == 'expiring_soon':
            alert_level = 'WARNING'
            http_status = 200
        else:
            alert_level = 'OK'
            http_status = 200

        report['alert_level'] = alert_level

        return jsonify(report), http_status

    except Exception as e:
        error_report = {
            'report_timestamp': datetime.now().isoformat(),
            'alert_level': 'CRITICAL',
            'error': str(e),
            'message': 'Token health monitoring system failure'
        }
        logger.error(f"Token health report error: {str(e)}")
        return jsonify(error_report), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check starting...")
    db_status = "not connected"
    activity_count_status = "unknown"
    current_db_name = "not_available"
    current_db_user = "not_available"
    found_tables = []
    tables_total_count = 0

    try:
        logger.info("Testing basic database connection...")
        db_utils.execute_query("SELECT 1;")
        db_status = "connected"

        # For SQLite, we don't have current_database() function
        if db_utils.USE_POSTGRES:
            # Get current database name (PostgreSQL only)
            db_name_result = db_utils.execute_query("SELECT current_database();", fetch=True)
            if db_name_result and db_name_result[0]:
                current_db_name = db_name_result[0].get('current_database', 'unknown')

            # Get current user (PostgreSQL only)
            db_user_result = db_utils.execute_query("SELECT current_user;", fetch=True)
            if db_user_result and db_user_result[0]:
                current_db_user = db_user_result[0].get('current_user', 'unknown')

            # Get all table names (PostgreSQL only)
            tables_result = db_utils.execute_query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';",
                fetch=True
            )
            if tables_result:
                found_tables = [table.get('table_name', 'unknown') for table in tables_result]
                tables_total_count = len(found_tables)
        else:
            # SQLite - simpler approach
            current_db_name = "SQLite database"
            current_db_user = "local"
            tables_result = db_utils.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table';",
                fetch=True
            )
            if tables_result:
                found_tables = [table[0] if isinstance(table, tuple) else table['name'] for table in tables_result]
                tables_total_count = len(found_tables)

        # Check activity count
        try:
            activity_count_result = db_utils.execute_query("SELECT COUNT(*) FROM activities;", fetch=True)
            if activity_count_result and activity_count_result[0]:
                # Handle both SQLite (tuple) and PostgreSQL (dict) responses
                if hasattr(activity_count_result[0], 'keys'):
                    activity_count_status = activity_count_result[0].get('count', 0) or activity_count_result[0].get(
                        'COUNT(*)', 0)
                else:
                    activity_count_status = activity_count_result[0][0]
            else:
                activity_count_status = 0
        except Exception as e:
            logger.warning(f"Activities table query failed: {e}")
            activity_count_status = "table_not_found"

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "not connected"
        activity_count_status = "error_during_connection"

    return jsonify({
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "service": "strava-sync",
        "timestamp": datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"),
        "use_postgres": db_utils.USE_POSTGRES,
        "database_connection_status": db_status,
        "current_database_name": current_db_name,
        "current_database_user": current_db_user,
        "tables_in_schema": found_tables,
        "total_tables": tables_total_count,
        "activity_count_check": activity_count_status
    })


@login_required
@app.route('/strava-setup', methods=['GET', 'POST'])
def strava_setup():
    """Strava connection setup where users provide their own app credentials"""
    if request.method == 'POST':
        # Handle the form submission
        client_id = request.form.get('client_id')
        client_secret = request.form.get('client_secret')

        if client_id and client_secret:
            # Generate OAuth URL with user's credentials
            redirect_uri = "https://strava-training-personal-382535371225.us-central1.run.app/oauth-callback"
            auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,activity:read_all"

            # Store credentials temporarily in session for OAuth callback
            session['temp_strava_client_id'] = client_id
            session['temp_strava_client_secret'] = client_secret

            return redirect(auth_url)

    return '''
    <html>
    <head>
        <title>Connect Strava - Your Training Monkey</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                max-width: 700px;
                margin: 30px auto;
                padding: 20px;
                line-height: 1.6;
                color: #333;
            }
            .info-box {
                background: #e7f3ff;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #2196F3;
            }
            .form-box {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                border: 1px solid #e9ecef;
            }
            .warning-box {
                background: #fff3cd;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                border-left: 4px solid #ffc107;
            }
            .form-group {
                margin: 15px 0;
            }
            .form-group label {
                display: block;
                font-weight: 600;
                margin-bottom: 5px;
                color: #495057;
            }
            .form-group input {
                width: 100%;
                padding: 12px;
                border: 1px solid #ced4da;
                border-radius: 6px;
                font-size: 14px;
                transition: border-color 0.15s ease-in-out;
                box-sizing: border-box;
            }
            .form-group input:focus {
                outline: none;
                border-color: #FC5200;
                box-shadow: 0 0 0 2px rgba(252, 82, 0, 0.1);
            }
            .strava-button-container {
                text-align: center;
                margin: 30px 0;
            }
            .strava-button-wrapper {
                display: inline-block;
                cursor: pointer;
                transition: transform 0.2s ease;
            }
            .strava-button-wrapper:hover {
                transform: scale(1.05);
            }
            .strava-button-wrapper img {
                height: 48px;
                width: auto;
            }
            .back-link {
                display: inline-block;
                margin-top: 30px;
                color: #6c757d;
                text-decoration: none;
                padding: 10px 0;
            }
            .back-link:hover {
                color: #495057;
                text-decoration: underline;
            }
            .strava-branding {
                text-align: center;
                margin: 40px 0 20px 0;
                padding: 20px 0;
                border-top: 1px solid #e9ecef;
            }
            .strava-logo {
                height: 20px;
                width: auto;
            }
            @media (max-width: 768px) {
                body {
                    margin: 15px;
                    padding: 15px;
                }
                .info-box, .form-box, .warning-box {
                    padding: 15px;
                }
            }
        </style>
    </head>
    <body>
        <h1 style="color: #2c3e50; margin-bottom: 10px;">Connect Your Strava Account</h1>
        <p style="color: #6c757d; margin-bottom: 30px;">Set up your personal connection to sync training data with Your Training Monkey</p>

        <div class="info-box">
            <h3 style="margin-top: 0; color: #1976d2;">🔑 Step 1: Create Your Personal Strava App</h3>
            <p>Each user needs their own Strava application (this is temporary while we wait for multi-user approval).</p>
            <ol style="margin: 15px 0;">
                <li>Go to <a href="https://www.strava.com/settings/api" target="_blank" style="color: #FC5200; font-weight: 500;">Strava API Settings</a></li>
                <li>Click <strong>"Create App"</strong></li>
                <li>Fill in the form with these exact values:
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li><strong>Application Name:</strong> [Your choice, e.g. "My Training Monkey"]</li>
                        <li><strong>Category:</strong> Training</li>
                        <li><strong>Club:</strong> [Leave blank]</li>
                        <li><strong>Website:</strong> <code>https://strava-training-personal-382535371225.us-central1.run.app</code></li>
                        <li><strong>Application Description:</strong> Personal training analytics dashboard</li>
                        <li><strong>Authorization Callback Domain:</strong> <code>strava-training-personal-382535371225.us-central1.run.app</code></li>
                    </ul>
                </li>
                <li>Click <strong>"Create"</strong></li>
                <li>Copy your <strong>Client ID</strong> and <strong>Client Secret</strong> from the app details page</li>
            </ol>
        </div>

        <div class="form-box">
            <h3 style="margin-top: 0; color: #495057;">🔗 Step 2: Enter Your App Credentials</h3>
            <form method="POST" id="stravaForm">
                <div class="form-group">
                    <label for="client_id">Client ID</label>
                    <input type="text" 
                           id="client_id" 
                           name="client_id" 
                           required 
                           placeholder="Enter your Strava app Client ID">
                </div>

                <div class="form-group">
                    <label for="client_secret">Client Secret</label>
                    <input type="text" 
                           id="client_secret" 
                           name="client_secret" 
                           required 
                           placeholder="Enter your Strava app Client Secret">
                </div>

                <!-- OFFICIAL STRAVA CONNECT BUTTON -->
                <div class="strava-button-container">
                    <div class="strava-button-wrapper" onclick="submitStravaForm()">
                        <img 
                            src="/static/connect-with-strava-orange.svg" 
                            alt="Connect with Strava"
                            class="strava-connect-button"
                            onerror="handleButtonError(this)"
                        >
                    </div>
                </div>
            </form>
        </div>

        <div class="warning-box">
            <h4 style="margin-top: 0; color: #856404;">ℹ️ Why do I need my own app?</h4>
            <p style="margin-bottom: 0;">This is a temporary setup while we wait for Strava to approve our application for multiple users. Once approved, this step won't be necessary and you'll connect with a single click.</p>
        </div>

        <!-- OFFICIAL STRAVA BRANDING FOOTER -->
        <div class="strava-branding">
            <img 
                src="/static/powered-by-strava-orange.svg" 
                alt="Powered by Strava"
                class="strava-logo"
                onerror="handleLogoError(this)"
            >
        </div>

        <a href="/static/index.html" class="back-link">← Back to Dashboard</a>

        <script>
        function submitStravaForm() {
            const clientId = document.getElementById('client_id').value.trim();
            const clientSecret = document.getElementById('client_secret').value.trim();

            if (!clientId || !clientSecret) {
                alert('Please enter both Client ID and Client Secret before connecting to Strava.');
                return;
            }

            // Add visual feedback
            const button = document.querySelector('.strava-button-wrapper');
            button.style.opacity = '0.7';
            button.style.transform = 'scale(0.95)';

            // Submit the form
            document.getElementById('stravaForm').submit();
        }

        function handleButtonError(img) {
            // Fallback for Connect button if SVG fails to load
            img.style.display = 'none';
            const fallbackButton = document.createElement('button');
            fallbackButton.innerHTML = 'CONNECT WITH STRAVA';
            fallbackButton.type = 'button';
            fallbackButton.onclick = submitStravaForm;
            fallbackButton.style.cssText = `
                background: #FC5200;
                color: white;
                border: none;
                padding: 14px 28px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                cursor: pointer;
                height: 48px;
                transition: all 0.2s;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            `;
            fallbackButton.onmouseover = function() {
                this.style.backgroundColor = '#e73c00';
                this.style.transform = 'scale(1.05)';
            };
            fallbackButton.onmouseout = function() {
                this.style.backgroundColor = '#FC5200';
                this.style.transform = 'scale(1)';
            };
            img.parentNode.appendChild(fallbackButton);
        }

        function handleLogoError(img) {
            // Fallback for Powered by Strava logo if SVG fails to load
            img.style.display = 'none';
            const fallbackText = document.createElement('span');
            fallbackText.innerHTML = 'POWERED BY STRAVA';
            fallbackText.style.cssText = `
                font-weight: bold;
                color: #FC5200;
                font-size: 14px;
                letter-spacing: 0.5px;
            `;
            img.parentNode.appendChild(fallbackText);
        }

        // Form validation feedback
        document.addEventListener('DOMContentLoaded', function() {
            const inputs = document.querySelectorAll('input[required]');
            inputs.forEach(input => {
                input.addEventListener('blur', function() {
                    if (this.value.trim() === '') {
                        this.style.borderColor = '#dc3545';
                    } else {
                        this.style.borderColor = '#28a745';
                    }
                });
            });
        });
        </script>
    </body>
    </html>
    ''', 200, {'Content-Type': 'text/html'}


@login_required
@app.route('/api/training-data', methods=['GET'])
def get_training_data():
    """Get training data for dashboard charts - Enhanced with sport breakdown support"""
    try:
        # Get parameters
        date_range = request.args.get('range', '90')  # days
        include_sport_breakdown = request.args.get('include_sport_breakdown', 'false').lower() == 'true'

        # Calculate date filter
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=int(date_range))
        start_date_str = start_date.strftime('%Y-%m-%d')

        logger.info(f"Getting training data for user {current_user.id}, range: {date_range} days, "
                    f"sport breakdown: {include_sport_breakdown}")

        activities = db_utils.execute_query(
            """
            SELECT * FROM activities 
            WHERE user_id = ? 
            AND date >= ?
            ORDER BY date ASC, activity_id ASC
            """,
            (current_user.id, start_date_str),
            fetch=True
        )

        if not activities:
            response_data = {
                'success': True,
                'message': 'No activities found',
                'data': [],
                'count': 0,
                'raw_count': 0
            }

            # Add sport breakdown fields even when no data
            if include_sport_breakdown:
                response_data.update({
                    'has_cycling_data': False,
                    'sport_summary': []
                })

            return jsonify(response_data)

        # Convert to list of dictionaries
        activity_list = []
        for activity in activities:
            activity_dict = {}
            if hasattr(activity, 'keys'):
                for key in activity.keys():
                    activity_dict[key] = activity[key]
            else:
                activity_dict = dict(activity)
            activity_list.append(activity_dict)

        logger.info(f"Retrieved {len(activity_list)} records from database (including rest days)")

        # CRITICAL FIX: Apply date serialization BEFORE aggregation
        activity_list = [ensure_date_serialization(activity) for activity in activity_list]

        # Enhanced aggregation with sport breakdown support
        if include_sport_breakdown:
            # Use enhanced aggregation that provides sport breakdown
            aggregated_data = aggregate_daily_activities_with_rest(activity_list)

            # Get sport summary and cycling data flag
            from unified_metrics_service import UnifiedMetricsService
            has_cycling_data = UnifiedMetricsService.has_cycling_data(
                current_user.id, start_date_str, end_date.strftime('%Y-%m-%d')
            )
            sport_summary = UnifiedMetricsService.get_sport_summary(
                current_user.id, start_date_str, end_date.strftime('%Y-%m-%d')
            ) if has_cycling_data else []
        else:
            # Use existing aggregation for backward compatibility
            aggregated_data = aggregate_daily_activities_with_rest(activity_list)
            has_cycling_data = False
            sport_summary = []

        # CRITICAL FIX: Apply date serialization AFTER aggregation too
        aggregated_data = [ensure_date_serialization(activity) for activity in aggregated_data]

        logger.info(f"Processed to {len(aggregated_data)} daily records for dashboard")

        # Build response maintaining existing structure
        response_data = {
            'success': True,
            'data': aggregated_data,  # Now with properly serialized dates
            'count': len(aggregated_data),
            'raw_count': len(activity_list)
        }

        # Add sport breakdown fields if requested
        if include_sport_breakdown:
            response_data.update({
                'has_cycling_data': has_cycling_data,
                'sport_summary': sport_summary
            })

            logger.info(f"Sport breakdown enabled: cycling data={has_cycling_data}, "
                        f"sport summary entries={len(sport_summary)}")

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error fetching training data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500


@login_required
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get training statistics for the dashboard - FIXED for DATE standardization"""
    try:
        from unified_metrics_service import UnifiedMetricsService

        logger.info(f"Calculating training statistics for user {current_user.id} using unified metrics...")

        # UPDATED: Pass current_user.id to unified metrics service
        unified_metrics = UnifiedMetricsService.get_latest_complete_metrics(current_user.id)

        if not unified_metrics:
            logger.warning(f"No unified metrics available for user {current_user.id}")
            return jsonify({
                'totalActivities': 0,
                'lastActivity': None,
                'daysSinceRest': 0,
                'latestMetrics': {
                    'externalAcwr': 0,
                    'internalAcwr': 0,
                    'sevenDayAvgLoad': 0,
                    'sevenDayAvgTrimp': 0,
                    'normalizedDivergence': 0
                }
            })

        # Count total real activities for the current user
        activity_count_result = db_utils.execute_query(
            "SELECT COUNT(*) FROM activities WHERE user_id = ? AND activity_id > 0",
            (current_user.id,),
            fetch=True
        )

        # Handle both PostgreSQL (dict) and SQLite (tuple) response formats
        if activity_count_result and activity_count_result[0]:
            result_row = activity_count_result[0]
            if hasattr(result_row, 'keys'):
                # PostgreSQL returns dict-like object
                total_activities = result_row.get('count', 0) or result_row.get('COUNT(*)', 0)
            else:
                # SQLite returns tuple
                total_activities = result_row[0]
        else:
            total_activities = 0

        # Build response using unified metrics
        stats = {
            'totalActivities': total_activities,
            'lastActivity': unified_metrics.get('latest_activity_date'),  # This will be fixed by serialization
            'daysSinceRest': unified_metrics.get('days_since_rest', 0),
            'latestMetrics': {
                'externalAcwr': round(unified_metrics.get('external_acwr', 0), 3),
                'internalAcwr': round(unified_metrics.get('internal_acwr', 0), 3),
                'sevenDayAvgLoad': round(unified_metrics.get('seven_day_avg_load', 0), 2),
                'sevenDayAvgTrimp': round(unified_metrics.get('seven_day_avg_trimp', 0), 1),
                'normalizedDivergence': round(unified_metrics.get('normalized_divergence', 0), 3)
            }
        }

        # CRITICAL FIX: Apply date serialization BEFORE returning JSON
        stats = ensure_date_serialization(stats)

        logger.info(f"Unified stats for user {current_user.id}: {stats}")
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error calculating stats for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({
            'totalActivities': 0,
            'lastActivity': None,
            'daysSinceRest': 0,
            'latestMetrics': {
                'externalAcwr': 0,
                'internalAcwr': 0,
                'sevenDayAvgLoad': 0,
                'sevenDayAvgTrimp': 0,
                'normalizedDivergence': 0
            }
        }), 500


@app.route('/')
def home():
    """Landing page for new users, dashboard for existing users"""
    if current_user.is_authenticated:
        # Existing user - redirect to dashboard
        return send_from_directory('/app/static', 'index.html')

    # New/unauthenticated user - show landing page
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Serve React dashboard"""
    return send_from_directory('/app/static', 'index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve React static files (CSS, JS, etc.)"""
    try:
        return send_from_directory('/app/static/static', filename)
    except Exception as e:
        logger.error(f"Static file error: {str(e)}")
        return f"Error serving {filename}: {str(e)}", 404

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory('static', 'favicon.ico')
    except:
        return '', 404

@app.route('/manifest.json')
def manifest():
    """Serve manifest.json"""
    try:
        return send_from_directory('static', 'manifest.json')
    except:
        return '', 404

@app.route('/logo192.png')
def logo192():
    """Serve logo192.png"""
    try:
        return send_from_directory('static', 'logo192.png')
    except:
        return '', 404

@app.route('/init-database', methods=['POST'])
def init_database():
    """Initialize the database tables"""
    try:
        from db_utils import initialize_db

        logger.info("Initializing database tables...")
        result = initialize_db(force=True)

        count_result = db_utils.execute_query("SELECT COUNT(*) FROM activities", fetch=True)
        if count_result and count_result[0]:
            if hasattr(count_result[0], 'keys'):
                activity_count = count_result[0].get('count', 0) or count_result[0].get('COUNT(*)', 0)
            else:
                activity_count = count_result[0][0]
        else:
            activity_count = 0

        return jsonify({
            "success": True,
            "message": "Database initialized successfully",
            "tables_created": result,
            "activity_count": activity_count
        })

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Database initialization failed: {str(e)}"
        }), 500


@app.route('/api/training-data-raw', methods=['GET'])
def get_training_data_raw():
    """Get raw training data without aggregation for debugging"""
    try:
        activities = db_utils.execute_query(
            """
            SELECT date, activity_id, name, type, total_load_miles, trimp, 
                   acute_chronic_ratio, trimp_acute_chronic_ratio, normalized_divergence
            FROM activities 
            WHERE activity_id > 0
            ORDER BY date DESC, activity_id ASC
            LIMIT 20
            """,
            fetch=True
        )

        activity_list = []
        for activity in activities:
            activity_dict = {}
            if hasattr(activity, 'keys'):
                for key in activity.keys():
                    activity_dict[key] = activity[key]
            else:
                activity_dict = dict(activity)
            activity_list.append(activity_dict)

        return jsonify({
            'success': True,
            'data': activity_list,
            'count': len(activity_list)
        })

    except Exception as e:
        logger.error(f"Error fetching raw training data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500

@login_required
@app.route('/api/llm-recommendations', methods=['GET'])
def get_llm_recommendations():
    """Get existing LLM recommendations for the current user"""
    try:
        logger.info(f"Fetching LLM recommendations for user {current_user.id}...")

        # Import here to avoid circular imports
        from db_utils import get_latest_recommendation

        recommendation = get_latest_recommendation(current_user.id)

        if recommendation:
            logger.info(f"Found recommendation for user {current_user.id} from {recommendation['generation_date']}")
            return jsonify({
                'success': True,
                'recommendation': recommendation
            })
        else:
            logger.info(f"No recommendations found for user {current_user.id}")
            return jsonify({
                'success': False,
                'message': 'No recommendations available',
                'recommendation': None
            })

    except Exception as e:
        logger.error(f"Error fetching LLM recommendations for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'recommendation': None
        }), 500


@login_required
@app.route('/api/llm-recommendations/generate', methods=['POST'])
def generate_llm_recommendations():
    """Generate new comprehensive LLM recommendations for the current user"""
    try:
        logger.info(f"Generating new comprehensive LLM recommendations for user {current_user.id}...")

        # Generate comprehensive recommendation with force=True to override cache
        recommendation = generate_recommendations(force=True, user_id=current_user.id)

        if recommendation:
            logger.info(f"Successfully generated comprehensive recommendation for user {current_user.id}")
            return jsonify({
                'success': True,
                'message': 'New comprehensive recommendation generated successfully',
                'recommendation': recommendation
            })
        else:
            logger.error(f"Failed to generate comprehensive recommendation for user {current_user.id}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate comprehensive recommendation',
                'recommendation': None
            }), 500

    except Exception as e:
        logger.error(f"Error generating comprehensive recommendations for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'recommendation': None
        }), 500


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')

        user = User.get_by_email(email)
        if user and user.check_password(password):
            login_user(user)
            logger.info(f"User {email} logged in successfully")

            if request.is_json:
                return jsonify({'success': True, 'redirect': '/static/index.html'})
            else:
                return redirect('/static/index.html')
        else:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            else:
                flash('Invalid email or password', 'danger')
                return render_template('login.html')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))


@app.route('/api/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    return jsonify({
        'id': current_user.id,
        'email': current_user.email,
        'resting_hr': current_user.resting_hr,
        'max_hr': current_user.max_hr,
        'gender': current_user.gender,
        'is_admin': current_user.is_admin
    })

@app.route('/verify-functions')
def verify_functions():
    """Verify which functions are loaded."""
    try:
        import inspect
        from strava_training_load import save_training_load
        source = inspect.getsource(save_training_load)
        has_diagnosis = "DIAGNOSIS:" in source
        return {
            "save_training_load_has_diagnosis": has_diagnosis,
            "function_length": len(source),
            "first_100_chars": source[:100]
        }
    except Exception as e:
        return {"error": str(e)}


@app.route('/auth/strava-signup')
def strava_auth_signup():
    """Strava OAuth initiation for new user signup from landing page"""
    try:
        # Construct redirect URI more carefully
        base_url = request.url_root.rstrip('/')
        redirect_uri = f"{base_url}/oauth-callback-signup"
        client_id = os.environ.get('STRAVA_CLIENT_ID')

        if not client_id:
            logger.error("STRAVA_CLIENT_ID not found in environment variables")
            flash('Strava integration not configured. Please contact support.', 'danger')
            return redirect('/')

        # Use urllib.parse.urlencode to properly encode parameters
        from urllib.parse import urlencode

        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'approval_prompt': 'force',
            'scope': 'read,activity:read_all'
        }

        auth_url = f"https://www.strava.com/oauth/authorize?{urlencode(params)}"

        logger.info(f"Redirecting new user to Strava OAuth for client_id: {client_id}")
        return redirect(auth_url)

    except Exception as e:
        logger.error(f"Error initiating Strava OAuth for signup: {str(e)}")
        flash('Unable to connect to Strava. Please try again.', 'danger')
        return redirect('/')


@app.route('/oauth-callback-signup', methods=['GET'])
def oauth_callback_signup():
    """Handle OAuth callback for NEW users from landing page - NO login required"""
    try:
        # Get the authorization code from URL parameters
        auth_code = request.args.get('code')
        error = request.args.get('error')

        if error:
            logger.error(f"Strava OAuth error: {error}")
            flash(f'Strava authorization failed: {error}', 'danger')
            return redirect('/')

        if not auth_code:
            logger.error("No authorization code received from Strava")
            flash('No authorization code received from Strava', 'danger')
            return redirect('/')

        # Use global app credentials
        client_id = os.environ.get('STRAVA_CLIENT_ID')
        client_secret = os.environ.get('STRAVA_CLIENT_SECRET')

        if not client_id or not client_secret:
            logger.error("Strava app credentials not configured")
            flash('Strava app credentials not configured. Please contact support.', 'danger')
            return redirect('/')

        logger.info("Processing OAuth callback for new user signup...")

        # Exchange code for tokens using stravalib (following your existing pattern)
        from stravalib.client import Client
        client = Client()

        token_response = client.exchange_code_for_token(
            client_id=client_id,
            client_secret=client_secret,
            code=auth_code
        )

        # Get athlete info
        temp_client = Client(access_token=token_response['access_token'])
        athlete = temp_client.get_athlete()
        athlete_id = str(athlete.id)

        if not athlete_id:
            logger.error("No athlete ID received from Strava")
            flash('Failed to get athlete information from Strava', 'danger')
            return redirect('/')

        logger.info(f"Retrieved athlete info for Strava ID: {athlete_id}")

        # Check if user already exists (by email pattern from your existing code)
        existing_user = User.get_by_email(f"strava_{athlete_id}@training-monkey.com")

        if existing_user:
            logger.info(f"Existing user found for athlete ID {athlete_id}, logging them in")

            # Update their Strava tokens in the database
            db_utils.execute_query(
                """UPDATE user_settings 
                   SET strava_access_token = %s, 
                       strava_refresh_token = %s, 
                       strava_token_expires_at = %s,
                       strava_athlete_id = %s
                   WHERE id = %s""",
                (token_response['access_token'],
                 token_response['refresh_token'],
                 token_response['expires_at'],
                 int(athlete_id),
                 existing_user.id),
                fetch=False
            )

            # Log them in
            login_user(existing_user)
            flash('Welcome back! Your Strava connection has been updated.', 'success')
            return redirect('/static/index.html')

        # Create new user - using direct database insert to handle Strava fields
        logger.info(f"Creating new user account for Strava athlete {athlete_id}")

        # Generate a secure random password for the new user
        temp_password = secrets.token_urlsafe(16)
        password_hash = generate_password_hash(temp_password)

        # Extract athlete info with defaults
        email = f"strava_{athlete_id}@training-monkey.com"
        first_name = getattr(athlete, 'firstname', '')
        last_name = getattr(athlete, 'lastname', '')
        gender = getattr(athlete, 'sex', 'male')  # Default to male as per your schema
        resting_hr = getattr(athlete, 'resting_hr', None) or 44  # Your schema default
        max_hr = getattr(athlete, 'max_hr', None) or 178  # Your schema default

        # Create new user using direct database insert (to include Strava fields)
        result = db_utils.execute_query(
            """INSERT INTO user_settings (
                email, password_hash, is_admin, 
                resting_hr, max_hr, gender,
                strava_athlete_id, strava_access_token, strava_refresh_token, strava_token_expires_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            (
                email,
                password_hash,
                False,  # is_admin
                resting_hr,
                max_hr,
                gender,
                int(athlete_id),  # strava_athlete_id
                token_response['access_token'],  # strava_access_token
                token_response['refresh_token'],  # strava_refresh_token
                token_response['expires_at']  # strava_token_expires_at
            ),
            fetch=True
        )

        if not result:
            logger.error("Failed to insert new user - no result returned")
            flash('Error creating user account. Please try again.', 'danger')
            return redirect('/')

        new_user_id = result[0]['id']
        logger.info(f"Successfully created user with ID {new_user_id}")

        # Load the new user object and log them in (using your existing User.get method)
        new_user = User.get(new_user_id)
        if not new_user:
            logger.error(f"Failed to load new user object for user ID {new_user_id}")
            flash('Error logging in. Please try again.', 'danger')
            return redirect('/')

        # Log in the new user
        login_user(new_user)

        # Set onboarding flag for first-time experience
        session['is_first_login'] = True
        session['signup_source'] = 'landing_page'

        # Flash welcome message
        flash(f'Welcome to Your Training Monkey, {first_name}! Let\'s analyze your training data.', 'success')

        # Redirect to dashboard (which will handle first-time user flow)
        return redirect('/static/index.html')

    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback signup: {str(e)}")
        flash('An unexpected error occurred. Please try again or contact support.', 'danger')
        return redirect('/')


@app.route('/api/landing/analytics', methods=['POST'])
def landing_analytics():
    """Track landing page interactions for optimization"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})

        # Log analytics event
        logger.info(f"Landing page analytics: {event_type} - {event_data}")

        # Here you could store in analytics database if needed
        # For now, just log for monitoring

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error tracking landing page analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/dashboard/first-time')
@login_required
def first_time_dashboard():
    """Special dashboard experience for new users from landing page"""
    if not session.get('new_user_onboarding'):
        return redirect('/static/index.html')

    try:
        # Use correct date formatting pattern
        twenty_eight_days_ago = (datetime.now().date() - timedelta(days=28)).strftime('%Y-%m-%d')

        days_of_data = db_utils.execute_query(
            "SELECT COUNT(DISTINCT date) as days FROM activities WHERE user_id = %s AND date >= %s",
            (current_user.id, twenty_eight_days_ago),
            fetch=True
        )

        activity_count = db_utils.execute_query(
            "SELECT COUNT(*) as count FROM activities WHERE user_id = %s",
            (current_user.id,),
            fetch=True
        )

        if days_of_data and days_of_data.get('days', 0) >= 14:
            session.pop('new_user_onboarding', None)
            return redirect('/static/index.html?highlight=divergence&new_user=true')
        else:
            return render_template('onboarding.html',
                                   days_needed=max(0, 28 - days_of_data.get('days', 0)) if days_of_data else 28,
                                   activity_count=activity_count.get('count', 0) if activity_count else 0)

    except Exception as e:
        logger.error(f"Error checking user data: {str(e)}")
        return redirect('/static/index.html')

@app.route('/')
def landing_page():
    """Landing page for new users"""
    # Check if user is already logged in
    if current_user.is_authenticated:
        # If user is logged in, redirect to dashboard
        return redirect('/static/index.html')

    # For new/unauthenticated users, show landing page
    return render_template('landing.html')


@app.route('/landing')
def landing_redirect():
    """Explicit landing page route"""
    return render_template('landing.html')


@app.route('/auth/strava')
def strava_auth():
    """Enhanced Strava authentication for landing page users"""
    # Store referral source for analytics
    session['signup_source'] = 'landing_page'

    # Check if user already has account
    if current_user.is_authenticated:
        # Existing user - go to normal Strava connect flow
        return redirect('/strava-setup')

    # New user from landing page - initiate Strava OAuth
    # You'll need to modify this based on your existing Strava auth implementation
    redirect_uri = request.url_root + "oauth-callback"
    client_id = os.environ.get('STRAVA_CLIENT_ID')

    if not client_id:
        # Fallback to existing setup flow if no global client ID
        return redirect('/strava-setup')

    auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,activity:read_all"
    return redirect(auth_url)

@app.route('/api/user/onboarding-status')
@login_required
def onboarding_status():
    """API endpoint to check if user has enough data for full analysis"""
    try:
        # Calculate date 28 days ago in the format your app uses
        twenty_eight_days_ago = (datetime.now().date() - timedelta(days=28)).strftime('%Y-%m-%d')
        days_of_data = db_utils.execute_query(
            "SELECT COUNT(DISTINCT date) as days FROM activities WHERE user_id = %s AND date >= %s",
            (current_user.id, twenty_eight_days_ago),
            fetch=True
        )

        total_activities = db_utils.execute_query(
            "SELECT COUNT(*) as count FROM activities WHERE user_id = %s",
            (current_user.id,),
            fetch=True
        )

        has_sufficient_data = days_of_data and days_of_data.get('days', 0) >= 14

        return jsonify({
            'has_sufficient_data': has_sufficient_data,
            'days_of_data': days_of_data.get('days', 0) if days_of_data else 0,
            'total_activities': total_activities.get('count', 0) if total_activities else 0,
            'days_needed': max(0, 28 - days_of_data.get('days', 0)) if days_of_data else 28
        })

    except Exception as e:
        logger.error(f"Error getting onboarding status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/debug/static-files')
def list_static_files():
    """Enhanced debug endpoint to list all static files including nested directories"""
    try:
        import os

        static_dir = os.path.join(app.root_path, 'static')
        files = {}

        # Walk through all directories and subdirectories
        for root, dirs, filenames in os.walk(static_dir):
            for filename in filenames:
                # Get the full file path
                full_path = os.path.join(root, filename)
                # Get the relative path from the static directory
                rel_path = os.path.relpath(full_path, static_dir)
                # Convert backslashes to forward slashes for web paths
                web_path = rel_path.replace('\\', '/')

                # Determine the URL path that would be used to access this file
                if web_path.startswith('static/'):
                    # Files in static/static/ subdirectory
                    url_path = f"/static/{web_path}"
                else:
                    # Files directly in static/ directory
                    url_path = f"/static/{web_path}"

                files[web_path] = {
                    'file_path': web_path,
                    'url_path': url_path,
                    'full_system_path': full_path,
                    'size_bytes': os.path.getsize(full_path)
                }

        # Filter for Strava-related files
        strava_files = {k: v for k, v in files.items() if 'strava' in k.lower()}
        svg_files = {k: v for k, v in files.items() if k.endswith('.svg')}

        return jsonify({
            'success': True,
            'static_directory': static_dir,
            'total_files': len(files),
            'all_files': files,
            'strava_files': strava_files,
            'svg_files': svg_files,
            'strava_connect_buttons': {
                k: v for k, v in files.items()
                if 'btn_strava_connect' in k
            },
            'powered_by_strava': {
                k: v for k, v in files.items()
                if 'pwrdby_strava' in k or 'powered-by-strava' in k
            },
            'suggested_paths': {
                'white_connect_button': '/static/static/btn_strava_connect_with_white.svg',
                'orange_connect_button': '/static/static/btn_strava_connect_with_orange.svg',
                'orange_powered_by': '/static/static/api_logo_pwrdBy_strava_horiz_orange.svg',
                'white_powered_by': '/static/static/api_logo_pwrdBy_strava_horiz_white.svg'
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'static_directory': 'Could not determine'
        }), 500

@login_required
@app.route('/api/activities-management', methods=['GET'])
def get_activities_for_management():
    """Get activities data for the Activities management page"""
    try:
        # Get query parameters
        days = request.args.get('days', '30', type=int)
        page = request.args.get('page', '1', type=int)
        per_page = 50

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        # Get activities with pagination - FIXED: Use db_utils prefix
        offset = (page - 1) * per_page

        activities = db_utils.execute_query(
            """
            SELECT 
                activity_id,
                date,
                name,
                type,
                distance_miles,
                elevation_gain_feet,
                total_load_miles,
                trimp,
                duration_minutes
            FROM activities 
            WHERE user_id = ? 
            AND date BETWEEN ? AND ?
            AND activity_id > 0
            ORDER BY date DESC, activity_id DESC
            LIMIT ? OFFSET ?
            """,
            (current_user.id, start_date_str, end_date_str, per_page, offset),
            fetch=True
        )

        # Get total count for pagination - FIXED: Use db_utils prefix
        total_count = db_utils.execute_query(
            """
            SELECT COUNT(*) as count
            FROM activities 
            WHERE user_id = ? 
            AND date BETWEEN ? AND ?
            AND activity_id > 0
            """,
            (current_user.id, start_date_str, end_date_str),
            fetch=True
        )

        # Handle the count result safely (matching your existing pattern)
        if total_count and len(total_count) > 0:
            total_row = total_count[0]
            if hasattr(total_row, 'keys'):
                total = total_row.get('count', 0) or total_row.get('COUNT(*)', 0)
            else:
                total = total_row[0]
        else:
            total = 0

        # Convert to list of dictionaries
        activities_list = []
        for activity in activities:
            activity_dict = dict(activity)

            # Add missing elevation indicator
            activity_dict['has_missing_elevation'] = (
                    activity_dict['elevation_gain_feet'] is None or
                    activity_dict['elevation_gain_feet'] == 0
            )

            # Add data source info (simplified for now)
            activity_dict['elevation_data_source'] = 'strava'
            activity_dict['elevation_updated_by'] = None
            activity_dict['elevation_updated_at'] = None

            activities_list.append(activity_dict)

        activities_list = [ensure_date_serialization(entry) for entry in activities_list]

        return jsonify({
            'success': True,
            'data': activities_list,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_items': total,
                'total_pages': (total + per_page - 1) // per_page,
                'has_next': (page * per_page) < total,
                'has_prev': page > 1
            },
            'date_range': f'{start_date_str} to {end_date_str}'
        })

    except Exception as e:
        logger.error(f"Error fetching activities for management: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/admin/migration/elevation', methods=['GET', 'POST'])
@login_required
def elevation_migration():
    """Admin-only elevation migration endpoint"""
    if not current_user.is_admin:
        return "Access denied - admin only", 403

    if request.method == 'GET':
        # Show migration form
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Elevation Factor Migration</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .warning { background: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 5px; margin: 20px 0; }
                .form-group { margin: 15px 0; }
                label { display: block; margin: 5px 0; }
                button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
                button:hover { background: #0056b3; }
            </style>
        </head>
        <body>
            <h2>Elevation Factor Migration</h2>
            <p><strong>Purpose:</strong> Migrate from 1000ft = 1 mile to research-optimized 750ft = 1 mile conversion factor</p>

            <div class="warning">
                <strong>⚠️ Important:</strong> This will recalculate ALL historical elevation loads and ACWR values for mathematical consistency.
                The 750ft factor will increase elevation loads by ~17.6% for better accuracy.
            </div>

            <form method="POST" onsubmit="return confirm('Are you sure you want to run this migration?')">
                <div class="form-group">
                    <label>
                        <input type="checkbox" name="confirm" required> 
                        I confirm I want to run the elevation migration with database backup completed
                    </label>
                </div>

                <div class="form-group">
                    <label>
                        <input type="radio" name="mode" value="dry_run" checked> 
                        <strong>Dry Run</strong> - Preview changes without applying them
                    </label>
                    <label>
                        <input type="radio" name="mode" value="live"> 
                        <strong>Live Migration</strong> - Apply changes to production database
                    </label>
                </div>

                <button type="submit">Run Migration</button>
                <a href="/dashboard" style="margin-left: 20px;">Cancel</a>
            </form>
        </body>
        </html>
        '''

    # POST - run the migration
    if request.form.get('confirm') != 'on':
        return "Migration not confirmed", 400

    dry_run = request.form.get('mode') == 'dry_run'

    try:
        # Import and run the migration
        from elevation_migration_module import run_elevation_migration

        success, results = run_elevation_migration(dry_run)

        # Format results for display
        mode_text = "DRY RUN" if dry_run else "LIVE MIGRATION"
        status_text = "✅ SUCCESS" if success else "❌ FAILED"

        html_response = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Migration Results</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .success {{ background: #d4edda; padding: 15px; border: 1px solid #c3e6cb; border-radius: 5px; margin: 20px 0; }}
                .error {{ background: #f8d7da; padding: 15px; border: 1px solid #f5c6cb; border-radius: 5px; margin: 20px 0; }}
                .info {{ background: #d1ecf1; padding: 15px; border: 1px solid #bee5eb; border-radius: 5px; margin: 20px 0; }}
                pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h2>Elevation Migration Results</h2>
            <h3>{mode_text} - {status_text}</h3>

            <div class="{'success' if success else 'error'}">
                <h4>Summary</h4>
                <ul>
                    <li>Total Activities: {results['total_activities']}</li>
                    <li>Activities with Elevation: {results['elevation_activities']}</li>
                    <li>Activities Updated: {results['updated_activities']}</li>
                    <li>Users Processed: {results['updated_users']}</li>
                </ul>
            </div>
        '''

        # Add sample calculations
        if results['sample_calculations']:
            html_response += '''
            <div class="info">
                <h4>Sample Calculations (1000ft → 750ft factor)</h4>
                <table>
                    <tr><th>Activity</th><th>Elevation</th><th>Current Load</th><th>New Load</th><th>% Increase</th></tr>
            '''
            for calc in results['sample_calculations'][:5]:
                if 'activity_id' in calc:  # Skip user summaries
                    html_response += f'''
                    <tr>
                        <td>{calc['activity_id']}</td>
                        <td>{calc['elevation_feet']:.0f}ft</td>
                        <td>{calc['current_load']:.3f} mi</td>
                        <td>{calc['new_load']:.3f} mi</td>
                        <td>+{calc['percent_increase']:.1f}%</td>
                    </tr>
                    '''
            html_response += '</table></div>'

        # Add errors if any
        if results['errors']:
            html_response += '<div class="error"><h4>Errors</h4><ul>'
            for error in results['errors']:
                html_response += f'<li>{error}</li>'
            html_response += '</ul></div>'

        # Add warnings if any
        if results['warnings']:
            html_response += '<div class="info"><h4>Warnings</h4><ul>'
            for warning in results['warnings']:
                html_response += f'<li>{warning}</li>'
            html_response += '</ul></div>'

        if dry_run and success:
            html_response += '''
            <div class="info">
                <h4>Next Steps</h4>
                <p>This was a dry run - no changes were made to the database.</p>
                <p>If the results look correct, run the migration again with "Live Migration" selected.</p>
                <a href="/admin/migration/elevation">Run Again</a>
            </div>
            '''
        elif success:
            html_response += '''
            <div class="success">
                <h4>Migration Complete!</h4>
                <p>✅ All elevation loads updated to use 750ft factor</p>
                <p>✅ All ACWR values recalculated for consistency</p>
                <p>🔧 Next: Update application code constants to use 750ft factor</p>
            </div>
            '''

        html_response += '''
            <p><a href="/dashboard">Return to Dashboard</a></p>
        </body>
        </html>
        '''

        return html_response, 200, {'Content-Type': 'text/html'}

    except Exception as e:
        logger.error(f"Migration endpoint error: {str(e)}")
        return f"Migration failed: {str(e)}", 500

@login_required
@app.route('/api/activities-management/update-elevation', methods=['PUT'])
def update_activity_elevation():
    """Update elevation data for a specific activity"""
    try:
        data = request.get_json()
        activity_id = data.get('activity_id')
        elevation_feet = data.get('elevation_gain_feet')

        if not activity_id or elevation_feet is None:
            return jsonify({
                'success': False,
                'error': 'Missing activity_id or elevation_gain_feet'
            }), 400

        # Validate elevation value
        try:
            elevation_feet = float(elevation_feet)
            if elevation_feet < 0 or elevation_feet > 15000:
                return jsonify({
                    'success': False,
                    'error': 'Elevation must be between 0 and 15,000 feet'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid elevation value'
            }), 400

        # Check if activity belongs to current user - FIXED: Use db_utils prefix
        activity_check = db_utils.execute_query(
            "SELECT 1 FROM activities WHERE activity_id = ? AND user_id = ?",
            (activity_id, current_user.id),
            fetch=True
        )

        if not activity_check:
            return jsonify({
                'success': False,
                'error': 'Activity not found or access denied'
            }), 404

        activity_data = db_utils.execute_query(
            "SELECT distance_miles FROM activities WHERE activity_id = ? AND user_id = ?",
            (activity_id, current_user.id),
            fetch=True
        )

        if not activity_data:
            return jsonify({
                'success': False,
                'error': 'Activity not found'
            }), 404

        current_distance = activity_data[0]['distance_miles'] or 0

        # Calculate elevation load and total load with 850ft factor
        elevation_load_miles = elevation_feet / 850.0  # Use new factor!
        total_load_miles = current_distance + elevation_load_miles

        # Update with correct parameters
        db_utils.execute_query(
            """
            UPDATE activities 
            SET 
                elevation_gain_feet = ?,
                elevation_load_miles = ?,
                total_load_miles = ?,
                elevation_factor_used = ?
            WHERE activity_id = ? AND user_id = ?
            """,
            (elevation_feet, elevation_load_miles, total_load_miles, 850.0, activity_id, current_user.id)
        )

        logger.info(f"Updated elevation for activity {activity_id} to {elevation_feet}ft by user {current_user.id}")

        # Calculate the new total load for response
        new_elevation_load = round(elevation_feet / 750.0, 2)

        return jsonify({
            'success': True,
            'message': f'Elevation updated to {elevation_feet:,.0f} feet',
            'updated_values': {
                'elevation_gain_feet': elevation_feet,
                'elevation_load_miles': new_elevation_load,
                'data_source': 'user_input'
            }
        })

    except Exception as e:
        logger.error(f"Error updating activity elevation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update elevation data'
        }), 500


@login_required
@app.route('/api/journal', methods=['GET'])
def get_journal_entries():
    """Get journal entries with corrected recommendation lookup."""
    try:
        logger.info(f"Fetching journal entries for user {current_user.id}")

        # Get date parameter or use current date
        date_param = request.args.get('date')
        if date_param:
            center_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        else:
            center_date = get_app_current_date()

        # Calculate date range (today + 6 preceding days)
        start_date = center_date - timedelta(days=6)
        end_date = center_date

        observations_data = db_utils.execute_query(
            """
            SELECT date, energy_level, rpe_score, pain_percentage, notes
            FROM journal_entries 
            WHERE user_id = ? AND date >= ? AND date <= ?
            """,
            (current_user.id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
            fetch=True
        )

        obs_by_date = {}
        if observations_data:
            for row in observations_data:
                obs_dict = dict(row)
                date_key = obs_dict['date']

                if hasattr(date_key, 'date'):
                    date_str_key = date_key.date().strftime('%Y-%m-%d')
                elif hasattr(date_key, 'strftime'):
                    date_str_key = date_key.strftime('%Y-%m-%d')
                else:
                    date_str_key = str(date_key)

                obs_by_date[date_str_key] = obs_dict

        # Get autopsies (this part works correctly)
        autopsy_data = db_utils.execute_query(
            """
            SELECT date, autopsy_analysis, alignment_score, generated_at
            FROM ai_autopsies 
            WHERE user_id = ? AND date >= ? AND date <= ?
            """,
            (current_user.id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')),
            fetch=True
        )

        autopsy_by_date = {}
        if autopsy_data:
            for row in autopsy_data:
                autopsy_dict = dict(row)
                date_key = autopsy_dict['date']

                if hasattr(date_key, 'date'):
                    date_str_key = date_key.date().strftime('%Y-%m-%d')
                elif hasattr(date_key, 'strftime'):
                    date_str_key = date_key.strftime('%Y-%m-%d')
                elif isinstance(date_key, str) and 'T' in date_key:
                    date_str_key = date_key.split('T')[0]
                else:
                    date_str_key = str(date_key)

                autopsy_by_date[date_str_key] = {
                    'autopsy_analysis': autopsy_dict.get('autopsy_analysis'),
                    'alignment_score': autopsy_dict.get('alignment_score'),
                    'generated_at': autopsy_dict.get('generated_at')
                }

        # Generate 7-day journal structure
        journal_entries = []
        current_date = start_date
        app_current_date = get_app_current_date()

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            is_today = current_date == app_current_date

            # FIXED: Use unified function that matches Dashboard logic
            todays_decision = get_unified_recommendation_for_date(current_date, current_user.id)

            # Get activity summary for this date
            activity_summary = get_activity_summary_for_date(current_date, current_user.id)

            # Build observations from lookup
            observations_data = obs_by_date.get(date_str, {})
            observations = {
                'energy_level': observations_data.get('energy_level'),
                'rpe_score': observations_data.get('rpe_score'),
                'pain_percentage': observations_data.get('pain_percentage'),
                'notes': observations_data.get('notes', '')
            }

            # Build autopsy from lookup
            autopsy_info = autopsy_by_date.get(date_str, {})
            ai_autopsy = {
                'autopsy_analysis': autopsy_info.get('autopsy_analysis'),
                'alignment_score': autopsy_info.get('alignment_score'),
                'generated_at': autopsy_info.get('generated_at').isoformat() if autopsy_info.get(
                    'generated_at') else None
            }

            journal_entry = {
                'date': date_str,
                'is_today': is_today,
                'day_name': current_date.strftime('%A'),
                'formatted_date': current_date.strftime('%B %d'),
                'todays_decision': todays_decision,
                'activity_summary': activity_summary,
                'observations': observations,
                'ai_autopsy': ai_autopsy
            }

            journal_entries.append(journal_entry)
            current_date += timedelta(days=1)

        journal_entries = [ensure_date_serialization(entry) for entry in journal_entries]
        journal_entries.sort(key=lambda x: x['date'], reverse=True)

        response = {
            'success': True,
            'data': journal_entries,
            'center_date': center_date.strftime('%Y-%m-%d'),
            'date_range': f"{start_date} to {end_date}",
            'app_current_date': app_current_date.strftime('%Y-%m-%d'),
            'timezone_info': 'Pacific'
        }

        logger.info(f"Successfully returned {len(journal_entries)} journal entries for user {current_user.id}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error fetching journal entries for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e),
            'data': []
        }), 500


# CRITICAL FIX for strava_app.py
# Replace the existing get_unified_recommendation_for_date function with this corrected version

def get_unified_recommendation_for_date(date_obj, user_id):
    """
    FIXED: Unified function ensuring Dashboard and Journal show IDENTICAL data
    CRITICAL CHANGE: Removed date::text casting that was breaking queries
    """
    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        app_current_date = get_app_current_date()

        logger.info(f"Getting unified recommendation for user {user_id} on date {date_str}")

        # CRITICAL: Use the SAME logic as Dashboard for ALL dates
        if date_obj == app_current_date:
            # For TODAY: Use same logic as Dashboard (get latest record)
            from db_utils import get_latest_recommendation
            latest_rec = get_latest_recommendation(user_id)

            if latest_rec and latest_rec.get('daily_recommendation'):
                logger.info(f"Found TODAY recommendation for user {user_id}")
                return f"🤖 AI Training Decision for TODAY'S WORKOUT ({date_obj.strftime('%A, %B %d')}):\n\n{latest_rec['daily_recommendation']}"
            else:
                logger.warning(f"No TODAY recommendation found for user {user_id}")
                return f"🤖 AI Training Decision for TODAY'S WORKOUT ({date_obj.strftime('%A, %B %d')}):\nNo recommendation available."

        else:
            # FIXED: Remove ::date casting - database now uses proper DATE format
            logger.info(f"Searching for target_date recommendation: user={user_id}, date={date_str}")

            recommendation = db_utils.execute_query(
                """
                SELECT daily_recommendation
                FROM llm_recommendations 
                WHERE user_id = ? AND target_date = ?
                ORDER BY id DESC 
                LIMIT 1
                """,
                (user_id, date_str),
                fetch=True
            )

            # Add comprehensive logging for debugging
            if recommendation and recommendation[0]:
                recommendation_text = dict(recommendation[0])['daily_recommendation']
                logger.info(
                    f"FOUND recommendation for user {user_id} on {date_str}: {len(recommendation_text)} characters")

                # Determine appropriate label
                if date_obj < app_current_date:
                    date_label = f"WORKOUT for {date_obj.strftime('%A, %B %d')}"
                else:
                    date_label = f"PLANNED WORKOUT ({date_obj.strftime('%A, %B %d')})"

                return f"🤖 AI Training Decision for {date_label}:\n\n{recommendation_text}"
            else:
                logger.warning(f"NO recommendation found for user {user_id} on {date_str}")

                # Verify what data exists for debugging
                debug_query = db_utils.execute_query(
                    "SELECT id, target_date, generation_date FROM llm_recommendations WHERE user_id = ? ORDER BY id DESC LIMIT 5",
                    (user_id,),
                    fetch=True
                )

                if debug_query:
                    logger.info(f"Available recommendations for user {user_id}: {[dict(row) for row in debug_query]}")
                else:
                    logger.warning(f"NO recommendations exist for user {user_id}")

                # Determine appropriate label for "no recommendation" message
                if date_obj < app_current_date:
                    date_label = f"WORKOUT for {date_obj.strftime('%A, %B %d')}"
                else:
                    date_label = f"PLANNED WORKOUT ({date_obj.strftime('%A, %B %d')})"

                return f"🤖 AI Training Decision for {date_label}:\nNo recommendation available for this date. Generate fresh recommendations on the Dashboard tab."

    except Exception as e:
        logger.error(f"Error in get_unified_recommendation_for_date for user {user_id}, date {date_str}: {str(e)}",
                     exc_info=True)
        return f"🤖 AI Training Decision:\nError retrieving recommendation: {str(e)}"


def get_date_specific_decision_with_label(date_obj, user_id, recommendations_lookup):
    """
    Get date-specific recommendation with clear labeling
    Uses pre-fetched recommendations lookup for performance
    """
    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        app_current_date = get_app_current_date()

        # Get the stored recommendation for this specific date
        stored_recommendation = recommendations_lookup.get(date_str)

        # Determine appropriate label
        if date_obj == app_current_date:
            date_label = f"TODAY'S WORKOUT ({date_obj.strftime('%A, %B %d')})"
        elif date_obj < app_current_date:
            date_label = f"WORKOUT for {date_obj.strftime('%A, %B %d')}"
        else:
            date_label = f"PLANNED WORKOUT ({date_obj.strftime('%A, %B %d')})"

        if stored_recommendation and stored_recommendation.strip():
            return f"🤖 AI Training Decision for {date_label}:\n\n{stored_recommendation}"
        else:
            return f"🤖 AI Training Decision for {date_label}:\nNo recommendation available for this date. Generate fresh recommendations on the Dashboard tab."

    except Exception as e:
        logger.error(f"Error getting date-specific decision for {date_str}: {str(e)}")
        return f"Error retrieving recommendation for {date_obj.strftime('%A, %B %d')}"


def get_dashboard_training_decision(user_id):
    """
    Dashboard training decision - shows NEXT actionable workout with clear labeling
    This ensures Dashboard and Journal are consistent
    """
    try:
        app_current_date = get_app_current_date()
        tomorrow = app_current_date + timedelta(days=1)

        # Get tomorrow's recommendation (what user should do next)
        tomorrow_recommendation = db_utils.execute_query(
            """
            SELECT daily_recommendation
            FROM llm_recommendations 
            WHERE user_id = ? 
            AND target_date = ?
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (user_id, tomorrow.strftime('%Y-%m-%d')),
            fetch=True
        )

        date_label = f"NEXT WORKOUT - {tomorrow.strftime('%A, %B %d')}"

        if tomorrow_recommendation and tomorrow_recommendation[0]:
            recommendation_text = dict(tomorrow_recommendation[0])['daily_recommendation']
            return f"🤖 AI Training Decision for {date_label}:\n\n{recommendation_text}"
        else:
            return f"🤖 AI Training Decision for {date_label}:\nNo recommendation available. Generate fresh recommendations on the Dashboard tab."

    except Exception as e:
        logger.error(f"Error getting dashboard training decision: {str(e)}")
        return f"Error retrieving next workout recommendation"


def get_activity_summary_for_date(date_obj, user_id):
    """Generate activity summary for a specific date - FIXED for Journal Page"""
    try:
        date_str = date_obj.strftime('%Y-%m-%d')

        logger.info(f"Getting activity summary for date {date_str}, user {user_id}")

        # Get all activities for this date - SAME QUERY AS ACTIVITIES PAGE
        activities = db_utils.execute_query(
            """
            SELECT 
                activity_id,
                name,
                type,
                distance_miles,
                elevation_gain_feet,
                trimp,
                duration_minutes,
                avg_heart_rate,
                max_heart_rate
            FROM activities 
            WHERE user_id = ? AND date = ? AND activity_id > 0
            ORDER BY activity_id DESC
            """,
            (user_id, date_str),
            fetch=True
        )

        logger.info(f"Found {len(activities) if activities else 0} activities for {date_str}")

        # If no activities, return rest day
        if not activities:
            return {
                'type': 'rest',
                'distance': 0,
                'elevation': 0,
                'workout_classification': 'Rest',
                'total_trimp': 0,
                'activity_id': None  # CRITICAL: Include activity_id for Strava links
            }

        # Convert activities to dict format for easier processing
        activity_list = [dict(activity) for activity in activities]

        # Aggregate activities for the day
        total_distance = sum(float(act.get('distance_miles', 0) or 0) for act in activity_list)
        total_elevation = sum(float(act.get('elevation_gain_feet', 0) or 0) for act in activity_list)
        total_trimp = sum(float(act.get('trimp', 0) or 0) for act in activity_list)

        # Determine primary activity type and ID
        # Use the activity with the longest distance as primary
        primary_activity = max(activity_list, key=lambda x: x.get('distance_miles', 0) or 0)
        activity_type = primary_activity.get('type', 'Unknown')
        primary_activity_id = primary_activity.get('activity_id')

        # Classify workout based on TRIMP (improved classifications)
        if total_trimp <= 30:
            workout_classification = 'Easy/Recovery'
        elif total_trimp <= 70:
            workout_classification = 'Moderate'
        elif total_trimp <= 120:
            workout_classification = 'Tempo/Threshold'
        else:
            workout_classification = 'Intervals/Hard'

        result = {
            'type': activity_type,
            'distance': round(total_distance, 2),
            'elevation': round(total_elevation, 0),
            'workout_classification': workout_classification,
            'total_trimp': round(total_trimp, 1),
            'activity_id': primary_activity_id  # CRITICAL: Include for "View on Strava" links
        }

        logger.info(f"Activity summary for {date_str}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error getting activity summary for {date_str}, user {user_id}: {str(e)}")
        return {
            'type': 'Error',
            'distance': 0,
            'elevation': 0,
            'workout_classification': 'Error',
            'total_trimp': 0,
            'activity_id': None
        }


def get_todays_decision_for_date(date_obj, user_id):
    """
    UPDATED: Get training recommendation for specific date with proper date labeling
    This replaces the existing function to fix the "same decision every day" issue
    """
    try:
        date_str = date_obj.strftime('%Y-%m-%d')

        # Get the stored recommendation for this SPECIFIC date
        specific_recommendation = db_utils.execute_query(
            """
            SELECT daily_recommendation
            FROM llm_recommendations 
            WHERE user_id = ? 
            AND target_date = ?
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (user_id, date_str),
            fetch=True
        )

        app_current_date = get_app_current_date()

        # Determine appropriate label
        if date_obj == app_current_date:
            date_label = f"TODAY'S WORKOUT ({date_obj.strftime('%A, %B %d')})"
        elif date_obj < app_current_date:
            date_label = f"WORKOUT for {date_obj.strftime('%A, %B %d')}"
        else:
            date_label = f"PLANNED WORKOUT ({date_obj.strftime('%A, %B %d')})"

        if specific_recommendation and specific_recommendation[0]:
            recommendation_text = dict(specific_recommendation[0])['daily_recommendation']
            return f"🤖 AI Training Decision for {date_label}:\n\n{recommendation_text}"
        else:
            # Fallback to most recent recommendation if no date-specific one exists
            fallback_recommendation = db_utils.execute_query(
                """
                SELECT daily_recommendation
                FROM llm_recommendations 
                WHERE user_id = ?
                ORDER BY generated_at DESC
                LIMIT 1
                """,
                (user_id,),
                fetch=True
            )

            if fallback_recommendation and fallback_recommendation[0]:
                recommendation_text = dict(fallback_recommendation[0])['daily_recommendation']
                return f"🤖 AI Training Decision for {date_label}:\n\n{recommendation_text}"
            else:
                return f"🤖 AI Training Decision for {date_label}:\nNo recommendation available. Generate fresh recommendations on the Dashboard tab."

    except Exception as e:
        logger.error(f"Error getting training decision for {date_str}, user {user_id}: {str(e)}", exc_info=True)
        return f"Error retrieving AI recommendation for {date_obj.strftime('%A, %B %d')}"


def get_training_decision_for_journal_date(date_obj, user_id):
    """
    Separate function for Journal page that shows historical decisions
    This shows what the AI recommended FOR that specific date (not what's next)
    """
    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        app_current_date = get_app_current_date()

        if date_obj == app_current_date:
            # TODAY: Show what AI recommended for today's workout
            date_label = f"TODAY'S RECOMMENDED WORKOUT ({date_obj.strftime('%A, %B %d')})"
            decision = get_historical_decision_for_date(user_id, date_obj)

        elif date_obj < app_current_date:
            # PAST: Show what AI recommended for that day's workout
            date_label = f"RECOMMENDED WORKOUT for {date_obj.strftime('%A, %B %d')}"
            decision = get_historical_decision_for_date(user_id, date_obj)

        else:
            # FUTURE: Show planned workout for that future date
            date_label = f"PLANNED WORKOUT for {date_obj.strftime('%A, %B %d')}"
            decision = get_autopsy_informed_decision_for_future(user_id, date_obj)

        if decision and decision.strip():
            return f"🤖 {date_label}:\n\n{decision}"
        else:
            return f"🤖 {date_label}:\nNo recommendation available for this date."

    except Exception as e:
        logger.error(f"Error getting journal decision for {date_str}, user {user_id}: {str(e)}", exc_info=True)
        return f"Error retrieving recommendation: {str(e)}"


def trigger_autopsy_and_update_recommendations(user_id, completed_date):
    """
    Complete workflow triggered when user saves observations after completing workout

    PROPER SEQUENCING:
    1. Generate autopsy for completed workout
    2. Use autopsy learning to update tomorrow's recommendation
    3. Update any relevant future decisions
    """
    try:


        app_current_date = get_app_current_date()
        completed_date_obj = datetime.strptime(completed_date, '%Y-%m-%d').date()

        logger.info(f"Triggering autopsy workflow for user {user_id}, completed date {completed_date}")

        # STEP 1: Generate autopsy for the completed workout
        if completed_date_obj <= app_current_date:
            logger.info(f"Generating autopsy for completed workout: {completed_date}")

            # Generate enhanced autopsy
            autopsy_result = generate_autopsy_for_date(completed_date, user_id)

            if autopsy_result:
                logger.info(f"✅ Autopsy generated for {completed_date}")

                # STEP 2: Update tomorrow's recommendation with autopsy learning
                tomorrow = app_current_date + timedelta(days=1)
                logger.info(f"Updating recommendation for {tomorrow} with autopsy learning")

                # Trigger learning-based recommendation update
                update_recommendations_with_autopsy_learning(user_id, completed_date)

                return {
                    'autopsy_generated': True,
                    'recommendations_updated': True,
                    'next_workout_date': tomorrow.strftime('%Y-%m-%d')
                }
            else:
                logger.warning(f"❌ Failed to generate autopsy for {completed_date}")
                return {'autopsy_generated': False, 'recommendations_updated': False}
        else:
            logger.info(f"⏭️ Skipping autopsy for future date: {completed_date}")
            return {'autopsy_generated': False, 'recommendations_updated': False}

    except Exception as e:
        logger.error(f"Error in autopsy workflow: {str(e)}", exc_info=True)
        return {'error': str(e)}


def get_autopsy_informed_decision_for_today(user_id, target_date):
    """
    Get today's decision that incorporates yesterday's autopsy learning.
    This is for TODAY's workout, informed by yesterday's autopsy.
    """
    try:
        logger.info(f"Getting autopsy-informed decision for TODAY: {target_date}")

        # Try to get autopsy-informed decision first
        from llm_recommendations_module import generate_autopsy_informed_daily_decision

        autopsy_informed_decision = generate_autopsy_informed_daily_decision(user_id, target_date)

        if autopsy_informed_decision:
            logger.info(f"Using autopsy-informed decision for user {user_id}")
            return autopsy_informed_decision
        else:
            # Fallback to standard decision
            logger.info(f"Using standard decision fallback for user {user_id}")
            return get_standard_daily_decision(user_id, target_date)

    except Exception as e:
        logger.error(f"Error getting autopsy-informed decision for today: {str(e)}")
        return get_standard_daily_decision(user_id, target_date)


def get_autopsy_informed_decision_for_future(user_id, target_date):
    """
    Get future decision (like tomorrow's workout).
    This would be for planning ahead.
    """
    try:
        logger.info(f"Getting decision for future date: {target_date}")

        # For future dates, we can use the same autopsy-informed logic
        from llm_recommendations_module import generate_autopsy_informed_daily_decision

        future_decision = generate_autopsy_informed_daily_decision(user_id, target_date)

        if future_decision:
            return future_decision
        else:
            return get_standard_daily_decision(user_id, target_date)

    except Exception as e:
        logger.error(f"Error getting future decision: {str(e)}")
        return get_standard_daily_decision(user_id, target_date)


# USER EXPERIENCE FLOW DOCUMENTATION:

"""
MONDAY EVENING (after completing workout):
1. User completes Monday's workout
2. User opens Journal page
3. User sees "TODAY'S RECOMMENDED WORKOUT (Monday)" - what AI suggested for today
4. User saves observations (energy, RPE, pain, notes)
5. Backend triggers:
   - Generate autopsy for Monday's workout (prescribed vs actual vs felt)
   - Update Tuesday's recommendation using Monday's autopsy learning
6. User refreshes Dashboard
7. User sees "NEXT WORKOUT - Tuesday" with autopsy-informed recommendation

TUESDAY MORNING:
1. User opens Dashboard
2. User sees "NEXT WORKOUT - Tuesday" (clear, actionable for today)
3. User opens Journal page
4. User sees Monday's row with autopsy analysis
5. User sees "TODAY'S RECOMMENDED WORKOUT (Tuesday)" for reference
6. Cycle continues...

KEY FEATURES:
✅ Clear date labeling removes confusion
✅ "NEXT WORKOUT" always shows actionable recommendation
✅ Journal shows historical "RECOMMENDED WORKOUT for [DATE]"
✅ Autopsy workflow automatically updates future recommendations
✅ User gets clear feedback on what happened behind the scenes
"""


def get_recommendation_by_target_date(user_id, target_date_str):
    """Simple lookup by target_date for Journal page."""
    try:
        result = db_utils.execute_query(
            """
            SELECT daily_recommendation 
            FROM llm_recommendations 
            WHERE user_id = ? AND target_date = ?
            ORDER BY generation_date DESC 
            LIMIT 1
            """,
            (user_id, target_date_str),
            fetch=True
        )

        if result and result[0]:
            return dict(result[0])['daily_recommendation']

        # Fallback: if no target_date match, try valid_until (for transition period)
        fallback_result = db_utils.execute_query(
            """
            SELECT daily_recommendation 
            FROM llm_recommendations 
            WHERE user_id = ? AND valid_until = ?
            ORDER BY generation_date DESC 
            LIMIT 1
            """,
            (user_id, target_date_str),
            fetch=True
        )

        if fallback_result and fallback_result[0]:
            return dict(fallback_result[0])['daily_recommendation']

        return None

    except Exception as e:
        logger.error(f"Error getting recommendation for target_date {target_date_str}: {str(e)}")
        return None

def get_standard_daily_decision(user_id, target_date):
    """Get standard daily decision without autopsy learning (fallback)."""
    try:
        target_date_str = target_date.strftime('%Y-%m-%d')

        # Look for recent recommendation
        recent_recommendation = db_utils.execute_query(
            """
            SELECT daily_recommendation
            FROM llm_recommendations 
            WHERE user_id = ? 
            AND generation_date >= ?
            ORDER BY generation_date DESC
            LIMIT 1
            """,
            (user_id, (target_date - timedelta(days=2)).strftime('%Y-%m-%d')),
            fetch=True
        )

        if recent_recommendation and recent_recommendation[0]:
            return dict(recent_recommendation[0])['daily_recommendation']

        return "No recent recommendation available. Generate fresh recommendations on the Dashboard tab."

    except Exception as e:
        logger.error(f"Error getting standard daily decision: {str(e)}")
        return "Error retrieving standard recommendation."


def get_historical_decision_for_date(user_id, date_obj):
    """Get the training decision that was originally generated for a specific historical date."""
    try:
        date_str = date_obj.strftime('%Y-%m-%d')

        # Look for decision generated ON that date (for that day's training)
        historical_decision = db_utils.execute_query(
            """
            SELECT daily_recommendation
            FROM llm_recommendations 
            WHERE user_id = ? AND generation_date = ?
            ORDER BY generation_date DESC
            LIMIT 1
            """,
            (user_id, date_str),
            fetch=True
        )

        if historical_decision and historical_decision[0]:
            return dict(historical_decision[0])['daily_recommendation']

        # Fallback: Look for most recent decision valid for that date
        fallback_decision = db_utils.execute_query(
            """
            SELECT daily_recommendation
            FROM llm_recommendations 
            WHERE user_id = ? 
            AND generation_date <= ?
            AND valid_until >= ?
            ORDER BY generation_date DESC
            LIMIT 1
            """,
            (user_id, date_str, date_str),
            fetch=True
        )

        if fallback_decision and fallback_decision[0]:
            return dict(fallback_decision[0])['daily_recommendation']

        return "No historical recommendation found for this date."

    except Exception as e:
        logger.error(f"Error getting historical decision: {str(e)}")
        return "Error retrieving historical recommendation."


@login_required
@app.route('/api/journal', methods=['POST'])
def save_journal_entry():
    """
    EXISTING FUNCTION - Only adding minimal enhancements for user feedback
    All the core logic remains the same as the working implementation
    """
    try:
        data = request.get_json()

        # Validate required data
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        date_str = data.get('date')
        if not date_str:
            return jsonify({'success': False, 'error': 'Date is required'}), 400

        # Validate date format
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

        # Validate ranges (EXISTING LOGIC - UNCHANGED)
        energy_level = data.get('energy_level')
        if energy_level is not None and (energy_level < 1 or energy_level > 5):
            return jsonify({'success': False, 'error': 'Energy level must be between 1 and 5'}), 400

        rpe_score = data.get('rpe_score')
        if rpe_score is not None and (rpe_score < 1 or rpe_score > 10):
            return jsonify({'success': False, 'error': 'RPE score must be between 1 and 10'}), 400

        pain_percentage = data.get('pain_percentage')
        if pain_percentage is not None and pain_percentage not in [0, 20, 40, 60, 80, 100]:
            return jsonify({'success': False, 'error': 'Pain percentage must be 0, 20, 40, 60, 80, or 100'}), 400

        # EXISTING DATABASE SAVE LOGIC - UNCHANGED
        if db_utils.USE_POSTGRES:
            query = """
                INSERT INTO journal_entries (user_id, date, energy_level, rpe_score, pain_percentage, notes, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id, date)
                DO UPDATE SET
                    energy_level = EXCLUDED.energy_level,
                    rpe_score = EXCLUDED.rpe_score,
                    pain_percentage = EXCLUDED.pain_percentage,
                    notes = EXCLUDED.notes,
                    updated_at = CURRENT_TIMESTAMP
            """
        else:
            query = """
                INSERT OR REPLACE INTO journal_entries 
                (user_id, date, energy_level, rpe_score, pain_percentage, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """

        db_utils.execute_query(query, (
            current_user.id,
            date_str,
            energy_level,
            rpe_score,
            pain_percentage,
            data.get('notes', '')
        ))

        logger.info(f"Saved journal entry for user {current_user.id} on {date_str}")

        # EXISTING AUTOPSY TRIGGER LOGIC - ONLY ENHANCED WITH BETTER TRACKING
        autopsy_generated = False
        autopsy_error = None

        try:
            # Get prescribed action for this date (EXISTING LOGIC)
            prescribed_action = get_todays_decision_for_date(date_obj, current_user.id)

            # Get activity summary for this date (EXISTING LOGIC)
            activity_summary = get_activity_summary_for_date(date_obj, current_user.id)

            # Check if we have both prescribed action AND actual activity (EXISTING LOGIC)
            has_prescribed_action = (
                    prescribed_action and
                    prescribed_action != "No AI recommendation available for this date. Generate fresh recommendations on the Dashboard tab."
                    and "No specific recommendation available" not in prescribed_action
                    and "Error retrieving" not in prescribed_action
            )

            has_actual_activity = (
                    activity_summary and
                    activity_summary.get('distance', 0) > 0 and
                    activity_summary.get('type') != 'rest'
            )

            # EXISTING AUTOPSY GENERATION CALL - UNCHANGED
            if has_prescribed_action and has_actual_activity:
                logger.info(f"Generating autopsy for {date_str} - has both prescribed action and actual activity")
                generate_autopsy_for_date(date_str, current_user.id)  # EXISTING FUNCTION CALL
                autopsy_generated = True
                logger.info(f"✅ Autopsy generation completed for {date_str}")
            else:
                logger.info(f"Skipping autopsy for {date_str} - missing prescribed action or activity")

        except Exception as autopsy_error_ex:
            autopsy_error = str(autopsy_error_ex)
            logger.warning(f"Autopsy generation failed for {date_str}: {autopsy_error}")
            # Don't fail the journal save if autopsy generation fails (EXISTING BEHAVIOR)

        # ENHANCED USER RESPONSE - This is the main addition
        response_data = {
            'success': True,
            'message': 'Journal entry saved successfully',
            'date': date_str
        }

        # Add helpful user messaging based on what happened
        if autopsy_generated:
            response_data['user_message'] = (
                "✅ Observations saved! AI analysis generated for your workout. "
                "Go to Dashboard → Refresh AI Analysis to see updated recommendations."
            )
            response_data['autopsy_generated'] = True
        elif autopsy_error:
            response_data['user_message'] = (
                "✅ Observations saved! Note: AI analysis generation encountered an issue. "
                "Your data is safe - try refreshing AI Analysis on the Dashboard."
            )
            response_data['autopsy_error'] = autopsy_error
        else:
            response_data['user_message'] = "✅ Observations saved successfully!"
            response_data['autopsy_generated'] = False

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error saving journal entry: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to save journal entry',
            'details': str(e) if app.debug else None
        }), 500


def generate_autopsy_for_date(date_str, user_id):
    """Generate AI autopsy for a specific date using enhanced LLM analysis with proper validation"""
    try:
        logger.info(f"Starting autopsy generation for user {user_id} on {date_str}")

        # Get the prescribed action
        prescribed_action = get_todays_decision_for_date(
            datetime.strptime(date_str, '%Y-%m-%d').date(),
            user_id
        )

        # Validate prescribed action
        if not prescribed_action or "No AI recommendation available" in prescribed_action:
            logger.warning(f"No valid prescribed action for {date_str}, user {user_id}")
            return

        # Get activity summary
        activity_summary = get_activity_summary_for_date(
            datetime.strptime(date_str, '%Y-%m-%d').date(),
            user_id
        )

        # Validate activity data
        if not activity_summary or activity_summary['type'] == 'rest':
            logger.warning(f"No significant activity for {date_str}, user {user_id}")
            return

        # Get user observations from database
        journal_entry = db_utils.execute_query(
            "SELECT * FROM journal_entries WHERE user_id = ? AND date = ?",
            (user_id, date_str),
            fetch=True
        )

        observations = dict(journal_entry[0]) if journal_entry else {}

        # Format activity summary text
        actual_activities = f"{activity_summary['type'].title()} workout: {activity_summary['distance']} miles, {activity_summary['elevation']} ft elevation, TRIMP: {activity_summary['total_trimp']} ({activity_summary['workout_classification']} intensity)"

        # Import and use the enhanced autopsy generation
        from llm_recommendations_module import generate_activity_autopsy

        autopsy_analysis = generate_activity_autopsy(
            user_id=user_id,
            date_str=date_str,
            prescribed_action=prescribed_action,
            actual_activities=actual_activities,
            observations=observations
        )

        # Save autopsy to database with alignment score
        alignment_score = extract_alignment_score(autopsy_analysis)

        # Use proper SQL syntax based on database type
        if db_utils.USE_POSTGRES:
            query = """
                INSERT INTO ai_autopsies (user_id, date, prescribed_action, actual_activities, autopsy_analysis, alignment_score)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, date)
                DO UPDATE SET
                    prescribed_action = EXCLUDED.prescribed_action,
                    actual_activities = EXCLUDED.actual_activities,
                    autopsy_analysis = EXCLUDED.autopsy_analysis,
                    alignment_score = EXCLUDED.alignment_score,
                    generated_at = CURRENT_TIMESTAMP
            """
        else:
            query = """
                INSERT OR REPLACE INTO ai_autopsies 
                (user_id, date, prescribed_action, actual_activities, autopsy_analysis, alignment_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """

        db_utils.execute_query(query, (
            user_id,
            date_str,
            prescribed_action,
            actual_activities,
            autopsy_analysis,
            alignment_score
        ))

        logger.info(f"Successfully generated and saved enhanced AI autopsy for user {user_id} on {date_str}")

    except Exception as e:
        logger.error(f"Error generating enhanced autopsy for {date_str}, user {user_id}: {str(e)}")
        raise


def create_daily_focused_prompt(metrics, target_date, user_id):
    """
    Create a focused prompt for daily recommendations only.
    Much shorter and more specific than the full analysis prompt.
    """
    try:
        # Get yesterday's journal observations for context
        yesterday = (datetime.strptime(target_date, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')

        yesterday_obs = db_utils.execute_query(
            "SELECT energy_level, rpe_score, pain_percentage, notes FROM journal_entries WHERE user_id = ? AND date = ?",
            (user_id, yesterday),
            fetch=True
        )

        yesterday_context = ""
        if yesterday_obs:
            obs = dict(yesterday_obs[0])
            yesterday_context = f"""
YESTERDAY'S OBSERVATIONS:
- Energy Level: {obs.get('energy_level', 'Not recorded')}/5
- RPE Score: {obs.get('rpe_score', 'Not recorded')}/10  
- Pain Level: {obs.get('pain_percentage', 'Not recorded')}%
- Notes: {obs.get('notes', 'None')}
"""

        prompt = f"""You are an expert endurance coach providing today's specific training decision.

TARGET DATE: {target_date}

CURRENT METRICS:
- External ACWR: {metrics.get('external_acwr', 0):.2f} (Optimal: 0.8-1.3)
- Internal ACWR: {metrics.get('internal_acwr', 0):.2f} (Optimal: 0.8-1.3)
- Normalized Divergence: {metrics.get('normalized_divergence', 0):.3f} (Balance zone: -0.05 to +0.05)
- Days Since Rest: {metrics.get('days_since_rest', 0)}
- 7-day Avg Load: {metrics.get('seven_day_avg_load', 0):.2f} miles/day

{yesterday_context}

RESPONSE INSTRUCTIONS:
Provide SPECIFIC TRAINING DECISION for the target date.

Format as: "ASSESSMENT: [Current state analysis] YOUR WORKOUT: [Specific workout recommendation with volume/intensity targets] MONITORING: [What to watch for]"

Keep response concise (150-200 words). Focus on actionable guidance for today's session only.
"""

        return prompt

    except Exception as e:
        logger.error(f"Error creating daily prompt: {str(e)}")
        return "Error creating prompt for daily recommendation."


def generate_daily_recommendation_only(user_id, target_date=None):
    """Generate ONLY the daily recommendation component with proper target_date."""
    try:
        # If no target_date provided, generate for tomorrow (next day's workout)
        if target_date is None:
            target_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        logger.info(f"DEBUG: target_date value: {target_date}, type: {type(target_date)}")
        logger.info(f"Generating daily recommendation for user {user_id}, target_date {target_date}")

        # Get current date for generation_date
        generation_date = datetime.now().strftime('%Y-%m-%d')

        # Get current metrics for daily analysis
        from unified_metrics_service import UnifiedMetricsService
        current_metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id)

        if not current_metrics:
            logger.warning(f"No metrics available for daily recommendation for user {user_id}")
            return None

        # Create focused daily prompt
        daily_prompt = create_daily_focused_prompt(current_metrics, target_date, user_id)

        # Call LLM for daily recommendation only
        from llm_recommendations_module import call_anthropic_api
        daily_response = call_anthropic_api(daily_prompt, temperature=0.7)

        if not daily_response:
            logger.error(f"Failed to get daily LLM response for user {user_id}")
            return None

        # FIXED: Proper date logic for target-specific recommendations
        recommendation = {
            'generation_date': generation_date,        # When it was created (today)
            'target_date': target_date,               # What date it's FOR (tomorrow or specified date)
            'valid_until': None,               # never expires for specific dates
            'data_start_date': generation_date,       # Data analysis period start
            'data_end_date': generation_date,         # Data analysis period end
            'metrics_snapshot': current_metrics,
            'daily_recommendation': daily_response.strip(),
            'weekly_recommendation': "See recent comprehensive recommendations",
            'pattern_insights': f"Generated on {generation_date} for target date {target_date}",
            'raw_response': daily_response,
            'user_id': user_id
        }

        # Save to database
        from db_utils import save_llm_recommendation
        recommendation_id = save_llm_recommendation(recommendation)
        recommendation['id'] = recommendation_id

        logger.info(f"Generated daily recommendation {recommendation_id} for user {user_id}, target_date {target_date}")
        return recommendation

    except Exception as e:
        logger.error(f"Error generating daily recommendation: {str(e)}")
        return None


@app.route('/cron/daily-recommendations', methods=['POST'])
def daily_recommendations_cron():
    """
    Generate recommendations for tomorrow's workouts.
    Runs daily at 6 AM UTC to prepare next day's recommendations.
    """
    try:
        # Verify this is coming from Cloud Scheduler
        if not request.headers.get('X-Cloudscheduler'):
            logger.warning("Unauthorized daily recommendations request")
            return jsonify({'error': 'Unauthorized'}), 401

        logger.info("Starting daily recommendations generation")

        # Generate recommendations for TOMORROW's workout
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Get active users (users with activity in last 7 days)
        cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        active_users = db_utils.execute_query(
            """
            SELECT DISTINCT user_id, 
                   (SELECT email FROM user_settings WHERE id = user_id) as email
            FROM activities 
            WHERE date >= ?
            """,
            (cutoff_date,),
            fetch=True
        )

        if not active_users:
            logger.info("No active users found for recommendations")
            return jsonify({'message': 'No active users'}), 200

        successful_generations = 0
        failed_generations = 0

        for user_row in active_users:
            user_data = dict(user_row)
            user_id = user_data['user_id']

            try:
                # Generate recommendation for tomorrow
                recommendation = generate_daily_recommendation_only(user_id, tomorrow)

                if recommendation:
                    successful_generations += 1
                    logger.info(f"Generated recommendation for user {user_id}, target_date {tomorrow}")
                else:
                    failed_generations += 1
                    logger.warning(f"Failed to generate recommendation for user {user_id}")

            except Exception as user_error:
                failed_generations += 1
                logger.error(f"Error generating recommendation for user {user_id}: {str(user_error)}")

        logger.info(f"Daily recommendations complete: {successful_generations} successful, {failed_generations} failed")

        return jsonify({
            'message': f'Generated {successful_generations} daily recommendations for {tomorrow}',
            'successful': successful_generations,
            'failed': failed_generations,
            'target_date': tomorrow
        }), 200

    except Exception as e:
        logger.error(f"Error in daily recommendations cron: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/cron/weekly-comprehensive', methods=['POST'])
def weekly_comprehensive_cron():
    """
    Weekly comprehensive analysis that generates full recommendations.
    Runs once per week to update weekly strategy and pattern insights.
    """
    try:
        # Verify this is coming from Cloud Scheduler
        if not request.headers.get('X-Cloudscheduler'):
            logger.warning("Unauthorized weekly comprehensive request")
            return jsonify({'error': 'Unauthorized'}), 401

        logger.info("Starting weekly comprehensive recommendations")

        # Get all active users (users with activity in last 14 days)
        cutoff_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        active_users = db_utils.execute_query(
            """
            SELECT DISTINCT user_id,
                   (SELECT email FROM user_settings WHERE id = user_id) as email
            FROM activities 
            WHERE date >= ? AND user_id IS NOT NULL
            """,
            (cutoff_date,),
            fetch=True
        )

        if not active_users:
            logger.info("No active users found for weekly comprehensive")
            return jsonify({'message': 'No active users', 'processed': 0})

        success_count = 0
        error_count = 0

        for user_row in active_users:
            user_dict = dict(user_row)
            user_id = user_dict['user_id']
            email = user_dict.get('email', 'unknown')

            try:
                logger.info(f"Generating weekly comprehensive for user {user_id} ({email})")

                # Generate full comprehensive recommendation
                from llm_recommendations_module import generate_recommendations
                recommendation = generate_recommendations(force=True, user_id=user_id)

                if recommendation:
                    success_count += 1
                    logger.info(f"Successfully generated weekly comprehensive for user {user_id}")
                else:
                    error_count += 1
                    logger.warning(f"Failed to generate weekly comprehensive for user {user_id}")

                # Longer delay for comprehensive generation
                time.sleep(3)

            except Exception as user_error:
                error_count += 1
                logger.error(f"Weekly generation error for user {user_id}: {str(user_error)}")

        result = {
            'message': 'Weekly comprehensive completed',
            'total_users': len(active_users),
            'successful': success_count,
            'errors': error_count,
            'type': 'weekly_comprehensive',
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Weekly comprehensive completed: {result}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in weekly comprehensive cron: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def extract_alignment_score(autopsy_text):
    """Extract alignment score from autopsy analysis"""
    import re

    # Look for alignment score in the text
    score_match = re.search(r'alignment.*?(\d+)/10', autopsy_text, re.IGNORECASE)
    if score_match:
        return int(score_match.group(1))

    # Look for rating patterns
    rating_match = re.search(r'rate.*?(\d+).*?out of.*?10', autopsy_text, re.IGNORECASE)
    if rating_match:
        return int(rating_match.group(1))

    # Default to 5 if no score found
    return 5

@login_required
@app.route('/api/training-data-sport-breakdown', methods=['GET'])
def get_training_data_with_sport_breakdown():
    """
    Enhanced training data endpoint that includes detailed sport breakdown.
    Optional endpoint for frontend that wants detailed multi-sport analysis.
    """
    try:
        # Get all activities (same logic as existing endpoint)
        activities = db_utils.execute_query(
            """
            SELECT * FROM activities 
            WHERE user_id = ?
            ORDER BY date ASC, activity_id ASC
            """,
            (current_user.id,),
            fetch=True
        )

        if not activities:
            return jsonify({
                'success': True,
                'message': 'No activities found',
                'data': [],
                'sport_summary': {
                    'has_cycling_data': False,
                    'has_running_data': False,
                    'total_cycling_activities': 0,
                    'total_running_activities': 0
                }
            })

        # Convert to list of dictionaries and apply date serialization
        activity_list = [ensure_date_serialization(dict(activity)) for activity in activities]

        # Use enhanced aggregation
        aggregated_data = aggregate_daily_activities_with_rest(activity_list)
        aggregated_data = [ensure_date_serialization(activity) for activity in aggregated_data]

        # Calculate sport summary for frontend decision making
        sport_summary = {
            'has_cycling_data': any(day['cycling_load'] > 0 for day in aggregated_data),
            'has_running_data': any(day['running_load'] > 0 for day in aggregated_data),
            'total_cycling_activities': sum(
                len([act for act in day.get('activities', []) if act.get('sport') == 'cycling'])
                for day in aggregated_data
            ),
            'total_running_activities': sum(
                len([act for act in day.get('activities', []) if act.get('sport') == 'running'])
                for day in aggregated_data
            ),
            'mixed_sport_days': len([day for day in aggregated_data if day.get('day_type') == 'mixed'])
        }

        return jsonify({
            'success': True,
            'data': aggregated_data,
            'count': len(aggregated_data),
            'raw_count': len(activity_list),
            'sport_summary': sport_summary
        })

    except Exception as e:
        logger.error(f"Error fetching enhanced training data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': [],
            'sport_summary': {
                'has_cycling_data': False,
                'has_running_data': False,
                'total_cycling_activities': 0,
                'total_running_activities': 0
            }
        }), 500


@app.route('/api/landing-chart-data', methods=['GET'])
def get_landing_chart_data():
    """
    Public endpoint to serve ACWR chart data for landing page demonstration.
    Uses admin user data (user_id = 1) to showcase real training metrics.
    """
    try:
        # Use admin user data for demonstration (your account)
        admin_user_id = 1

        # Get the last 60 days of data for a good demonstration
        activities = db_utils.execute_query(
            """
            SELECT date, acute_chronic_ratio, trimp_acute_chronic_ratio, 
                   distance_miles, elevation_gain_feet, trimp, type, name
            FROM activities 
            WHERE user_id = %s 
              AND date >= CURRENT_DATE - INTERVAL '60 days'
              AND date <= CURRENT_DATE
            ORDER BY date ASC
            """,
            (admin_user_id,),
            fetch=True
        )

        if not activities:
            logger.warning("No activities found for landing page chart")
            return jsonify({
                'success': False,
                'error': 'No data available for chart'
            }), 404

        # Process data for chart display
        chart_data = []
        for activity in activities:
            # Format date for display
            date_obj = datetime.strptime(activity['date'], '%Y-%m-%d')
            formatted_date = f"{date_obj.month}/{date_obj.day}"

            chart_data.append({
                'date': activity['date'],
                'dateFormatted': formatted_date,
                'acute_chronic_ratio': round(activity.get('acute_chronic_ratio', 0), 2),
                'trimp_acute_chronic_ratio': round(activity.get('trimp_acute_chronic_ratio', 0), 2),
                'distance_miles': round(activity.get('distance_miles', 0), 1),
                'elevation_gain_feet': int(activity.get('elevation_gain_feet', 0)),
                'trimp': int(activity.get('trimp', 0)),
                'type': activity.get('type', 'Unknown'),
                'name': activity.get('name', 'Workout')
            })

        logger.info(f"Serving {len(chart_data)} data points for landing page chart")

        return jsonify({
            'success': True,
            'data': chart_data,
            'dataPoints': len(chart_data),
            'dateRange': {
                'start': chart_data[0]['date'] if chart_data else None,
                'end': chart_data[-1]['date'] if chart_data else None
            }
        })

    except Exception as e:
        logger.error(f"Error fetching landing page chart data: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Unable to load chart data'
        }), 500


@app.route('/landing-static/<path:filename>')
def serve_landing_static(filename):
    """Serve landing page assets - FIXED VERSION"""
    logger.info(f"Landing static request: {filename}")

    # CRITICAL FIX 1: acwr-chart.html - provide the content directly
    if filename == 'acwr-chart.html':
        logger.info("Serving acwr-chart.html directly from knowledge base")

        # Return the complete HTML with React chart
        html_content = '''<!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>ACWR Demo Chart</title>
                <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
                <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
                <script src="https://unpkg.com/recharts@2.8.0/umd/Recharts.js"></script>
                <style>
                    body { margin: 0; padding: 20px; font-family: -apple-system, sans-serif; }
                    .chart-demo { background: white; border-radius: 12px; padding: 1.5rem; }
                    .chart-title { font-size: 1.3rem; font-weight: 600; color: #1e293b; margin-bottom: 1rem; }
                    .chart-container { width: 100%; height: 380px; }
                    .chart-loading { display: flex; align-items: center; justify-content: center; height: 380px; color: #64748b; }
                    .data-info { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; font-size: 0.85rem; color: #64748b; }
                </style>
            </head>
            <body>
                <div id="chart-root"></div>
                <script>
                    if (typeof React === 'undefined' || typeof Recharts === 'undefined') {
                        document.getElementById('chart-root').innerHTML = 
                            '<div class="chart-demo"><div class="chart-loading">Loading chart libraries...</div></div>';
                    } else {
                        const { useState, useEffect, createElement } = React;
                        const { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea } = Recharts;
            
                        const DemoChart = () => {
                            const [data, setData] = useState([]);
                            const [loading, setLoading] = useState(true);
            
                            useEffect(() => {
                                fetch('/api/landing-chart-data')
                                    .then(res => res.json())
                                    .then(result => {
                                        if (result.success && result.data) {
                                            setData(result.data);
                                        } else {
                                            // Fallback demo data if API fails
                                            setData([
                                                {dateFormatted: '11/1', acute_chronic_ratio: 0.9, trimp_acute_chronic_ratio: 0.8},
                                                {dateFormatted: '11/5', acute_chronic_ratio: 1.1, trimp_acute_chronic_ratio: 1.0},
                                                {dateFormatted: '11/10', acute_chronic_ratio: 1.3, trimp_acute_chronic_ratio: 1.2},
                                                {dateFormatted: '11/15', acute_chronic_ratio: 1.0, trimp_acute_chronic_ratio: 1.1},
                                                {dateFormatted: '11/20', acute_chronic_ratio: 0.8, trimp_acute_chronic_ratio: 0.9}
                                            ]);
                                        }
                                        setLoading(false);
                                    })
                                    .catch(() => {
                                        setData([
                                            {dateFormatted: '11/1', acute_chronic_ratio: 0.9, trimp_acute_chronic_ratio: 0.8},
                                            {dateFormatted: '11/5', acute_chronic_ratio: 1.1, trimp_acute_chronic_ratio: 1.0},
                                            {dateFormatted: '11/10', acute_chronic_ratio: 1.3, trimp_acute_chronic_ratio: 1.2}
                                        ]);
                                        setLoading(false);
                                    });
                            }, []);
            
                            if (loading) {
                                return createElement('div', { className: 'chart-demo' },
                                    createElement('div', { className: 'chart-loading' }, 'Loading real training data...')
                                );
                            }
            
                            return createElement('div', { className: 'chart-demo' }, [
                                createElement('h3', { key: 'title', className: 'chart-title' }, 'Real Training Data: ACWR Analysis'),
            
                                createElement('div', { key: 'chart', className: 'chart-container' },
                                    createElement(ResponsiveContainer, { width: '100%', height: '100%' },
                                        createElement(LineChart, { data: data, margin: { top: 20, right: 30, left: 20, bottom: 20 } }, [
                                            createElement(CartesianGrid, { key: 'grid', strokeDasharray: '3 3', stroke: '#f1f5f9' }),
                                            createElement(XAxis, { key: 'x', dataKey: 'dateFormatted', tick: { fontSize: 12 } }),
                                            createElement(YAxis, { key: 'y', domain: [0.5, 1.6], tick: { fontSize: 12 } }),
                                            createElement(Tooltip, { key: 'tooltip' }),
            
                                            createElement(ReferenceArea, { key: 'danger', y1: 1.5, y2: 1.6, fill: '#ef4444', fillOpacity: 0.1 }),
                                            createElement(ReferenceArea, { key: 'warning', y1: 1.3, y2: 1.5, fill: '#f59e0b', fillOpacity: 0.1 }),
                                            createElement(ReferenceArea, { key: 'optimal', y1: 0.8, y2: 1.3, fill: '#10b981', fillOpacity: 0.1 }),
            
                                            createElement(Line, {
                                                key: 'external',
                                                type: 'monotone',
                                                dataKey: 'acute_chronic_ratio',
                                                stroke: '#3b82f6',
                                                strokeWidth: 3,
                                                name: 'External ACWR'
                                            }),
                                            createElement(Line, {
                                                key: 'internal',
                                                type: 'monotone',
                                                dataKey: 'trimp_acute_chronic_ratio',
                                                stroke: '#8b5cf6',
                                                strokeWidth: 3,
                                                name: 'Internal ACWR'
                                            })
                                        ])
                                    )
                                ),
            
                                createElement('div', { key: 'info', className: 'data-info' },
                                    'Live data from our founder\\'s trail running • External = Distance + Terrain • Internal = Heart Rate Response'
                                )
                            ]);
                        };
            
                        ReactDOM.render(createElement(DemoChart), document.getElementById('chart-root'));
                    }
                </script>
            </body>
            </html>'''

        return Response(html_content, mimetype='text/html')

    # CRITICAL FIX 2: wireframe-runner.jpg - try actual file first, then SVG fallback
    elif filename == 'images/wireframe-runner.jpg' or filename == 'wireframe-runner.jpg':
        logger.info("Looking for wireframe runner image")
        
        # Try to serve the actual image file first
        try:
            if filename.startswith('images/'):
                return send_from_directory('static/images', 'wireframe-runner.jpg')
            else:
                return send_from_directory('static', filename)
        except:
            logger.info("Actual image not found, providing wireframe runner SVG fallback")

        svg_fallback = '''<svg width="1200" height="600" viewBox="0 0 1200 600" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <linearGradient id="trailGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#667eea;stop-opacity:0.4" />
                <stop offset="100%" style="stop-color:#764ba2;stop-opacity:0.4" />
            </linearGradient>
        </defs>

        <!-- Background -->
        <rect width="1200" height="600" fill="url(#trailGradient)"/>

        <!-- Mountain silhouettes -->
        <path d="M0,450 L150,250 L300,350 L450,200 L600,300 L750,180 L900,320 L1050,240 L1200,350 L1200,600 L0,600 Z" 
              fill="rgba(255,255,255,0.15)"/>
        <path d="M0,500 L200,350 L400,420 L600,280 L800,380 L1000,300 L1200,400 L1200,600 L0,600 Z" 
              fill="rgba(255,255,255,0.1)"/>

        <!-- Trail path -->
        <path d="M0,520 Q300,480 600,510 T1200,530" 
              stroke="rgba(255,255,255,0.2)" 
              stroke-width="25" 
              fill="none"/>

        <!-- Runner silhouette -->
        <g transform="translate(450,420)">
            <!-- Body -->
            <ellipse cx="0" cy="25" rx="12" ry="35" fill="rgba(255,255,255,0.9)"/>
            <!-- Head -->
            <circle cx="0" cy="-15" r="10" fill="rgba(255,255,255,0.9)"/>
            <!-- Running arms -->
            <line x1="-8" y1="5" x2="-20" y2="-10" stroke="rgba(255,255,255,0.9)" stroke-width="3"/>
            <line x1="8" y1="5" x2="22" y2="25" stroke="rgba(255,255,255,0.9)" stroke-width="3"/>
            <!-- Running legs -->
            <line x1="-4" y1="50" x2="-12" y2="80" stroke="rgba(255,255,255,0.9)" stroke-width="4"/>
            <line x1="4" y1="50" x2="18" y2="75" stroke="rgba(255,255,255,0.9)" stroke-width="4"/>
        </g>

        <!-- Motion lines -->
        <path d="M380,450 L420,445 M375,470 L410,465 M370,490 L400,485" 
              stroke="rgba(255,255,255,0.6)" 
              stroke-width="2" 
              fill="none"/>

        <!-- Decorative elements -->
        <circle cx="120" cy="180" r="3" fill="rgba(255,255,255,0.6)"/>
        <circle cx="280" cy="120" r="2" fill="rgba(255,255,255,0.5)"/>
        <circle cx="850" cy="160" r="4" fill="rgba(255,255,255,0.7)"/>
        <circle cx="1000" cy="200" r="2" fill="rgba(255,255,255,0.4)"/>

        <!-- Training data overlay -->
        <text x="50" y="100" fill="rgba(255,255,255,0.8)" font-family="Arial, sans-serif" font-size="24" font-weight="bold">
            Training Analytics
        </text>
        <text x="50" y="130" fill="rgba(255,255,255,0.7)" font-family="Arial, sans-serif" font-size="16">
            Performance • Load • Recovery
        </text>
    </svg>'''

        return Response(svg_fallback, mimetype='image/svg+xml')

    # CRITICAL FIX 3: Strava button - try existing files then fallback
    elif filename == 'btn_strava_connect_with_orange_x2.svg':
        logger.info("Looking for Strava connect button")

        # Try different possible locations for Strava button
        possible_paths = [
            ('static', 'btn_strava_connect_with_orange.svg'),
            ('static', 'api_logo_pwrdBy_strava_horiz_orange.svg'),
            ('static', 'btn_strava_connect_with_orange_x2.svg'),
            ('static/static', 'btn_strava_connect_with_orange.svg')
        ]

        for directory, alt_filename in possible_paths:
            try:
                return send_from_directory(directory, alt_filename)
            except:
                continue

        # Fallback: Create our own Strava button
        logger.info("Creating Strava button fallback")
        strava_svg = '''<svg width="264" height="48" viewBox="0 0 264 48" xmlns="http://www.w3.org/2000/svg">
        <rect width="264" height="48" rx="6" fill="#FC5200"/>

        <!-- Strava logo -->
        <g transform="translate(16, 12)">
            <path d="M12 6L16 14H8L12 6Z M20 6L24 14H16L20 6Z" fill="white"/>
        </g>

        <!-- Text -->
        <text x="50" y="30" fill="white" font-family="Arial, sans-serif" font-size="16" font-weight="bold">
            Connect with Strava
        </text>
    </svg>'''

        return Response(strava_svg, mimetype='image/svg+xml')

    # Standard file serving - try multiple directories
    search_paths = [
        'landing_static',
        'templates',
        'static',
        'static/static'
    ]

    for directory in search_paths:
        try:
            logger.debug(f"Trying {filename} from {directory}")
            return send_from_directory(directory, filename)
        except Exception as e:
            logger.debug(f"Failed {directory}: {str(e)}")
            continue

    # File not found
    logger.error(f"Landing static file not found anywhere: {filename}")
    return f"File not found: {filename}", 404

@app.route('/settings', methods=['GET'])
@login_required
def get_settings():
    """Get current user's settings"""
    try:
        # Feature flag check - admin only initially
        if not is_feature_enabled('settings_page_enabled', current_user.id):
            return jsonify({'error': 'Settings page not available'}), 403

        # Get user data (your user_settings table serves as both user and settings)
        user_data = db_utils.execute_query(
            "SELECT * FROM user_settings WHERE id = ?",
            (current_user.id,),
            fetch=True
        )

        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        user = user_data[0]

        # Handle race_goal_date formatting
        race_goal_date = user.get('race_goal_date')
        if race_goal_date:
            if hasattr(race_goal_date, 'strftime'):
                # It's already a date object
                race_goal_date_str = race_goal_date.strftime('%Y-%m-%d')
            elif isinstance(race_goal_date, str):
                # It's already a string, try to parse and reformat
                try:
                    from datetime import datetime
                    parsed_date = datetime.strptime(race_goal_date, '%Y-%m-%d')
                    race_goal_date_str = parsed_date.strftime('%Y-%m-%d')
                except:
                    race_goal_date_str = race_goal_date  # Use as-is if parsing fails
            else:
                race_goal_date_str = str(race_goal_date) if race_goal_date else None
        else:
            race_goal_date_str = None

        # Prepare settings response (remove sensitive fields)
        settings_data = {
            'id': user['id'],
            'email': user['email'],
            'resting_hr': user.get('resting_hr', 65),
            'max_hr': user.get('max_hr', 185),
            'gender': user.get('gender', 'male'),
            'hr_zones_method': user.get('hr_zones_method', 'percentage'),
            'primary_sport': user.get('primary_sport', 'running'),
            'secondary_sport': user.get('secondary_sport'),
            'training_experience': user.get('training_experience', 'intermediate'),
            'current_phase': user.get('current_phase', 'base'),
            'race_goal_date': race_goal_date_str,  # Properly formatted date string
            'weekly_training_hours': user.get('weekly_training_hours', 8),
            'acwr_alert_threshold': float(user.get('acwr_alert_threshold', 1.30)),
            'injury_risk_alerts': user.get('injury_risk_alerts', True),
            'recommendation_style': user.get('recommendation_style', 'balanced'),
            'coaching_tone': user.get('coaching_tone', 'supportive'),
            'is_admin': user.get('is_admin', False),
            'created_at': user.get('created_at'),
            'updated_at': user.get('updated_at')
        }

        logger.info(f"Returning race_goal_date: {race_goal_date_str} for user {current_user.id}")

        return jsonify({
            'success': True,
            'settings': settings_data
        })

    except Exception as e:
        logger.error(f"Error fetching settings for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/settings', methods=['POST', 'PUT'])
@login_required
def update_settings():
    """Update current user's settings with analytics integration"""
    try:
        # Feature flag check - admin only initially
        if not is_feature_enabled('settings_page_enabled', current_user.id):
            return jsonify({'error': 'Settings updates not available'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Remove any fields that shouldn't be updated via this endpoint
        protected_fields = ['id', 'email', 'password_hash', 'strava_access_token',
                            'strava_refresh_token', 'created_at']
        for field in protected_fields:
            data.pop(field, None)

        # Validate heart rate settings
        errors = []
        if 'resting_hr' in data:
            if not isinstance(data['resting_hr'], int) or not 30 <= data['resting_hr'] <= 100:
                errors.append("Resting heart rate must be between 30-100 bpm")

        if 'max_hr' in data:
            if not isinstance(data['max_hr'], int) or not 120 <= data['max_hr'] <= 220:
                errors.append("Maximum heart rate must be between 120-220 bpm")

        # Handle race_goal_date conversion
        if 'race_goal_date' in data:
            if data['race_goal_date']:
                try:
                    from datetime import datetime
                    if isinstance(data['race_goal_date'], str):
                        # Convert from "YYYY-MM-DD" string to date object
                        data['race_goal_date'] = datetime.strptime(data['race_goal_date'], '%Y-%m-%d').date()
                except ValueError:
                    errors.append('Invalid date format for race goal date. Use YYYY-MM-DD format.')
            else:
                # Empty string or null - set to None to clear the date
                data['race_goal_date'] = None

        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        # *** CRITICAL FIX: GET OLD SETTINGS BEFORE UPDATE ***
        old_settings = db_utils.execute_query(
            "SELECT * FROM user_settings WHERE id = ?",
            (current_user.id,),
            fetch=True
        )[0]
        old_settings_dict = dict(old_settings)

        logger.info(
            f"🔍 OLD settings before update: resting_hr={old_settings_dict.get('resting_hr')}, max_hr={old_settings_dict.get('max_hr')}")

        # Build update query
        update_fields = []
        update_values = []

        for field, value in data.items():
            if field in ['resting_hr', 'max_hr', 'gender', 'hr_zones_method', 'primary_sport',
                         'secondary_sport', 'training_experience', 'current_phase', 'race_goal_date',
                         'weekly_training_hours', 'acwr_alert_threshold', 'injury_risk_alerts',
                         'recommendation_style', 'coaching_tone']:
                update_fields.append(f"{field} = ?")
                update_values.append(value)

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        update_values.append(current_user.id)

        # Execute update with proper logging
        update_query = f"UPDATE user_settings SET {', '.join(update_fields)} WHERE id = ?"
        logger.info(f"Executing update for user {current_user.id}: {update_query}")
        logger.info(f"Update values: {update_values}")

        db_utils.execute_query(update_query, tuple(update_values))

        # Get updated settings to verify the save
        updated_user = db_utils.execute_query(
            "SELECT * FROM user_settings WHERE id = ?",
            (current_user.id,),
            fetch=True
        )[0]
        new_settings_dict = dict(updated_user)

        logger.info(f"Settings updated for user {current_user.id}: {list(data.keys())}")
        logger.info(
            f"🔍 NEW settings after update: resting_hr={new_settings_dict.get('resting_hr')}, max_hr={new_settings_dict.get('max_hr')}")
        logger.info(f"Race goal date after update: {updated_user.get('race_goal_date')}")

        # *** NEW INTEGRATION CODE ***
        try:
            # Track what actually changed by comparing old vs new database values
            changed_fields = track_settings_changes(old_settings_dict, new_settings_dict)

            logger.info(f"🔍 CHANGE DETECTION RESULT: {list(changed_fields.keys())}")

            # Log specific HR changes for debugging
            if 'resting_hr' in changed_fields:
                logger.info(
                    f"🔍 RESTING HR CHANGED: {changed_fields['resting_hr']['old']} → {changed_fields['resting_hr']['new']}")
            if 'max_hr' in changed_fields:
                logger.info(f"🔍 MAX HR CHANGED: {changed_fields['max_hr']['old']} → {changed_fields['max_hr']['new']}")

            if changed_fields:
                logger.info("🔍 Triggering analytics recalculation...")

                # Trigger analytics recalculation for changed settings
                recalc_result = handle_settings_change(
                    user_id=current_user.id,
                    changed_settings=changed_fields,
                    old_values=old_settings_dict,
                    new_values=new_settings_dict
                )

                logger.info(f"🔍 Recalculation result: {recalc_result}")

                if recalc_result['success'] and recalc_result.get('recalculation_tasks'):
                    return jsonify({
                        'success': True,
                        'message': 'Settings saved successfully',
                        'recalculation_status': recalc_result,
                        'updated_fields': list(changed_fields.keys()),
                        'user_message': f"Settings saved! {', '.join(recalc_result.get('recalculation_tasks', []))}"
                    })
                else:
                    logger.warning(f"Settings saved but recalculation had issues: {recalc_result}")
                    return jsonify({
                        'success': True,
                        'message': 'Settings saved successfully',
                        'recalculation_status': recalc_result,
                        'user_message': 'Settings saved successfully!'
                    })
            else:
                logger.info("🔍 No changed fields requiring recalculation")
                return jsonify({
                    'success': True,
                    'message': 'Settings updated successfully',
                    'user_message': 'Settings saved successfully!'
                })

        except Exception as recalc_error:
            logger.error(f"🔍 Settings integration error: {str(recalc_error)}", exc_info=True)
            # Settings were saved successfully, don't fail the request
            return jsonify({
                'success': True,
                'message': 'Settings saved (integration error)',
                'warning': f'Integration error: {str(recalc_error)}',
                'user_message': 'Settings saved! Analytics will update shortly.'
            })

    except Exception as e:
        logger.error(f"Error updating settings for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/settings/validate', methods=['POST'])
@login_required
def validate_settings():
    """Validate settings without saving"""
    try:
        # Feature flag check - admin only initially
        if not is_feature_enabled('settings_page_enabled', current_user.id):
            return jsonify({'error': 'Settings validation not available'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        errors = []

        # Heart rate validation
        if 'resting_hr' in data:
            if not isinstance(data['resting_hr'], int) or not 30 <= data['resting_hr'] <= 100:
                errors.append("Resting heart rate must be between 30-100 bpm")

        if 'max_hr' in data:
            if not isinstance(data['max_hr'], int) or not 120 <= data['max_hr'] <= 220:
                errors.append("Maximum heart rate must be between 120-220 bpm")

        # Cross-validation
        if 'resting_hr' in data and 'max_hr' in data:
            if data['resting_hr'] >= data['max_hr']:
                errors.append("Resting heart rate must be lower than maximum heart rate")

        return jsonify({
            'valid': len(errors) == 0,
            'errors': errors
        })

    except Exception as e:
        logger.error(f"Error validating settings for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user-settings', methods=['POST'])
@login_required
def update_user_settings():
    """Update user settings including coaching style spectrum"""
    try:
        data = request.get_json()
        coaching_spectrum = data.get('coaching_style_spectrum')

        if coaching_spectrum is not None:
            # Validate range
            if not (0 <= coaching_spectrum <= 100):
                return jsonify({'error': 'Invalid spectrum value'}), 400

            # Update only the spectrum column (remove coaching_style_description)
            db_utils.execute_query("""
                UPDATE user_settings 
                SET coaching_style_spectrum = ?
                WHERE id = ?
            """, (coaching_spectrum, current_user.id))

            logger.info(f"Updated coaching style spectrum to {coaching_spectrum} for user {current_user.id}")

        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Error updating user settings: {str(e)}")
        return jsonify({'error': 'Failed to update settings'}), 500


@app.route('/api/user-settings', methods=['GET'])
@login_required
def get_user_settings():
    """Get current user settings"""
    try:
        # Remove coaching_style_description from the query
        result = db_utils.execute_query("""
            SELECT coaching_style_spectrum, coaching_tone
            FROM user_settings 
            WHERE id = ?
        """, (current_user.id,), fetch=True)

        if result and len(result) > 0:
            settings = result[0]
            return jsonify({
                'coaching_style_spectrum': settings.get('coaching_style_spectrum', 50),
                'coaching_tone': settings.get('coaching_tone', 'supportive')
            })
        else:
            return jsonify({
                'coaching_style_spectrum': 50,
                'coaching_tone': 'supportive'
            })

    except Exception as e:
        logger.error(f"Error fetching user settings: {str(e)}")
        return jsonify({'error': 'Failed to fetch settings'}), 500


@app.route('/api/settings/heart-rate-zones', methods=['GET'])
@login_required
def get_heart_rate_zones():
    """Calculate heart rate zones based on current settings"""
    try:
        if not is_feature_enabled('settings_page_enabled', current_user.id):
            return jsonify({'error': 'Heart rate zones not available'}), 403

        # Get user settings
        user_data = db_utils.execute_query(
            "SELECT resting_hr, max_hr, hr_zones_method, custom_hr_zones FROM user_settings WHERE id = ?",
            (current_user.id,),
            fetch=True
        )

        if not user_data:
            return jsonify({'error': 'User not found'}), 404

        user = user_data[0]
        resting_hr = user.get('resting_hr', 65)
        max_hr = user.get('max_hr', 185)
        method = user.get('hr_zones_method', 'percentage')
        custom_zones = user.get('custom_hr_zones')  # JSON string of custom boundaries

        # Parse custom zones if they exist
        custom_boundaries = None
        if custom_zones:
            try:
                custom_boundaries = json.loads(custom_zones)
            except:
                custom_boundaries = None

        # Calculate default zones with formulas
        if method == 'percentage':
            # Simple percentage method
            calculated_zones = {
                'zone1': {
                    'min': int(max_hr * 0.50),
                    'max': int(max_hr * 0.60),
                    'name': 'Recovery',
                    'min_formula': f'50% × {max_hr} = {int(max_hr * 0.50)}',
                    'max_formula': f'60% × {max_hr} = {int(max_hr * 0.60)}',
                    'min_calculation': 0.50,
                    'max_calculation': 0.60
                },
                'zone2': {
                    'min': int(max_hr * 0.60),
                    'max': int(max_hr * 0.70),
                    'name': 'Aerobic Base',
                    'min_formula': f'60% × {max_hr} = {int(max_hr * 0.60)}',
                    'max_formula': f'70% × {max_hr} = {int(max_hr * 0.70)}',
                    'min_calculation': 0.60,
                    'max_calculation': 0.70
                },
                'zone3': {
                    'min': int(max_hr * 0.70),
                    'max': int(max_hr * 0.80),
                    'name': 'Aerobic',
                    'min_formula': f'70% × {max_hr} = {int(max_hr * 0.70)}',
                    'max_formula': f'80% × {max_hr} = {int(max_hr * 0.80)}',
                    'min_calculation': 0.70,
                    'max_calculation': 0.80
                },
                'zone4': {
                    'min': int(max_hr * 0.80),
                    'max': int(max_hr * 0.90),
                    'name': 'Threshold',
                    'min_formula': f'80% × {max_hr} = {int(max_hr * 0.80)}',
                    'max_formula': f'90% × {max_hr} = {int(max_hr * 0.90)}',
                    'min_calculation': 0.80,
                    'max_calculation': 0.90
                },
                'zone5': {
                    'min': int(max_hr * 0.90),
                    'max': max_hr,
                    'name': 'VO2 Max',
                    'min_formula': f'90% × {max_hr} = {int(max_hr * 0.90)}',
                    'max_formula': f'Max HR = {max_hr}',
                    'min_calculation': 0.90,
                    'max_calculation': 1.00
                }
            }
        else:
            # Heart Rate Reserve method (Karvonen)
            hr_reserve = max_hr - resting_hr
            calculated_zones = {
                'zone1': {
                    'min': int(resting_hr + hr_reserve * 0.50),
                    'max': int(resting_hr + hr_reserve * 0.60),
                    'name': 'Recovery',
                    'min_formula': f'{resting_hr} + (50% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.50)}',
                    'max_formula': f'{resting_hr} + (60% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.60)}',
                    'min_calculation': 0.50,
                    'max_calculation': 0.60
                },
                'zone2': {
                    'min': int(resting_hr + hr_reserve * 0.60),
                    'max': int(resting_hr + hr_reserve * 0.70),
                    'name': 'Aerobic Base',
                    'min_formula': f'{resting_hr} + (60% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.60)}',
                    'max_formula': f'{resting_hr} + (70% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.70)}',
                    'min_calculation': 0.60,
                    'max_calculation': 0.70
                },
                'zone3': {
                    'min': int(resting_hr + hr_reserve * 0.70),
                    'max': int(resting_hr + hr_reserve * 0.80),
                    'name': 'Aerobic',
                    'min_formula': f'{resting_hr} + (70% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.70)}',
                    'max_formula': f'{resting_hr} + (80% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.80)}',
                    'min_calculation': 0.70,
                    'max_calculation': 0.80
                },
                'zone4': {
                    'min': int(resting_hr + hr_reserve * 0.80),
                    'max': int(resting_hr + hr_reserve * 0.90),
                    'name': 'Threshold',
                    'min_formula': f'{resting_hr} + (80% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.80)}',
                    'max_formula': f'{resting_hr} + (90% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.90)}',
                    'min_calculation': 0.80,
                    'max_calculation': 0.90
                },
                'zone5': {
                    'min': int(resting_hr + hr_reserve * 0.90),
                    'max': max_hr,
                    'name': 'VO2 Max',
                    'min_formula': f'{resting_hr} + (90% × {hr_reserve}) = {int(resting_hr + hr_reserve * 0.90)}',
                    'max_formula': f'Max HR = {max_hr}',
                    'min_calculation': 0.90,
                    'max_calculation': 1.00
                }
            }

        # Apply custom overrides if they exist
        final_zones = calculated_zones.copy()
        if custom_boundaries:
            for zone_key, zone_data in final_zones.items():
                if zone_key in custom_boundaries:
                    custom_zone = custom_boundaries[zone_key]
                    if 'min' in custom_zone:
                        zone_data['min'] = custom_zone['min']
                        zone_data['min_formula'] = f"Custom: {custom_zone['min']}"
                        zone_data['is_custom_min'] = True
                    if 'max' in custom_zone:
                        zone_data['max'] = custom_zone['max']
                        zone_data['max_formula'] = f"Custom: {custom_zone['max']}"
                        zone_data['is_custom_max'] = True

        return jsonify({
            'success': True,
            'zones': final_zones,
            'method': method,
            'resting_hr': resting_hr,
            'max_hr': max_hr,
            'hr_reserve': max_hr - resting_hr if method == 'reserve' else None,
            'has_custom_zones': custom_boundaries is not None,
            'calculated_zones': calculated_zones  # Always include calculated for reference
        })

    except Exception as e:
        logger.error(f"Error calculating heart rate zones for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/settings/heart-rate-zones', methods=['POST'])
@login_required
def save_custom_heart_rate_zones():
    """Save custom heart rate zone boundaries"""
    try:
        if not is_feature_enabled('settings_page_enabled', current_user.id):
            return jsonify({'error': 'Custom heart rate zones not available'}), 403

        data = request.get_json()
        new_custom_zones = data.get('custom_zones', {})

        # Get existing custom zones
        existing_data = db_utils.execute_query(
            "SELECT custom_hr_zones FROM user_settings WHERE id = ?",
            (current_user.id,),
            fetch=True
        )

        existing_custom_zones = {}
        if existing_data and existing_data[0]['custom_hr_zones']:
            try:
                import json
                existing_custom_zones = json.loads(existing_data[0]['custom_hr_zones'])
            except:
                existing_custom_zones = {}

        # Merge new zones with existing (new zones override existing)
        merged_zones = existing_custom_zones.copy()
        for zone_key, zone_data in new_custom_zones.items():
            if zone_key not in merged_zones:
                merged_zones[zone_key] = {}

            # Update only the boundaries that are specified
            if 'min' in zone_data:
                merged_zones[zone_key]['min'] = zone_data['min']
            if 'max' in zone_data:
                merged_zones[zone_key]['max'] = zone_data['max']

            # Remove empty zone entries
            if not merged_zones[zone_key]:
                del merged_zones[zone_key]

        # Validate merged zones
        errors = []

        # Extract all boundary values for validation
        all_boundaries = []
        for zone_key in ['zone1', 'zone2', 'zone3', 'zone4', 'zone5']:
            if zone_key in merged_zones:
                zone_data = merged_zones[zone_key]
                if 'min' in zone_data:
                    try:
                        min_val = int(zone_data['min'])
                        if min_val < 40 or min_val > 220:
                            errors.append(f"Zone boundary {min_val} is outside valid range (40-220 bpm)")
                        all_boundaries.append((min_val, f"{zone_key}_min"))
                    except ValueError:
                        errors.append(f"Invalid heart rate value: {zone_data['min']}")

                if 'max' in zone_data:
                    try:
                        max_val = int(zone_data['max'])
                        if max_val < 40 or max_val > 220:
                            errors.append(f"Zone boundary {max_val} is outside valid range (40-220 bpm)")
                        all_boundaries.append((max_val, f"{zone_key}_max"))
                    except ValueError:
                        errors.append(f"Invalid heart rate value: {zone_data['max']}")

        # Validate that adjacent zones connect properly
        # Get current calculated zones for reference
        user_data = db_utils.execute_query(
            "SELECT resting_hr, max_hr, hr_zones_method FROM user_settings WHERE id = ?",
            (current_user.id,),
            fetch=True
        )[0]

        resting_hr = user_data.get('resting_hr', 65)
        max_hr = user_data.get('max_hr', 185)
        method = user_data.get('hr_zones_method', 'percentage')

        # Build complete zone boundaries for validation
        if method == 'percentage':
            calculated_boundaries = [
                int(max_hr * 0.50), int(max_hr * 0.60), int(max_hr * 0.70),
                int(max_hr * 0.80), int(max_hr * 0.90), max_hr
            ]
        else:
            hr_reserve = max_hr - resting_hr
            calculated_boundaries = [
                int(resting_hr + hr_reserve * 0.50), int(resting_hr + hr_reserve * 0.60),
                int(resting_hr + hr_reserve * 0.70), int(resting_hr + hr_reserve * 0.80),
                int(resting_hr + hr_reserve * 0.90), max_hr
            ]

        # Apply custom overrides to calculated boundaries
        final_boundaries = calculated_boundaries.copy()
        zone_names = ['zone1', 'zone2', 'zone3', 'zone4', 'zone5']

        for i, zone_key in enumerate(zone_names):
            if zone_key in merged_zones:
                if 'min' in merged_zones[zone_key]:
                    final_boundaries[i] = merged_zones[zone_key]['min']
                if 'max' in merged_zones[zone_key]:
                    final_boundaries[i + 1] = merged_zones[zone_key]['max']

        # Validate ascending order
        for i in range(len(final_boundaries) - 1):
            if final_boundaries[i] >= final_boundaries[i + 1]:
                errors.append(
                    f"Heart rate zones must be in ascending order. {final_boundaries[i]} >= {final_boundaries[i + 1]}")

        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        # Save merged zones as JSON
        import json
        custom_zones_json = json.dumps(merged_zones) if merged_zones else None

        db_utils.execute_query(
            "UPDATE user_settings SET custom_hr_zones = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (custom_zones_json, current_user.id)
        )

        logger.info(f"Custom heart rate zones saved for user {current_user.id}: {list(merged_zones.keys())}")

        return jsonify({
            'success': True,
            'message': 'Custom heart rate zones saved successfully',
            'saved_zones': merged_zones
        })

    except Exception as e:
        logger.error(f"Error saving custom heart rate zones for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # For local testing
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Strava Sync Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)