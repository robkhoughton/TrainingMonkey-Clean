#!/usr/bin/env python3
"""
Strava Sync Service for Training Monkey™ Dashboard
Updated version of strava_app.py to use Strava instead of Garmin
"""

import os
import logging

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except FileNotFoundError:
    print("⚠️  No .env file found. Run: python setup_environment.py")
import time
import json
import db_utils
from datetime import datetime, timedelta, date
from timezone_utils import get_app_current_date, log_timezone_debug
from llm_recommendations_module import generate_recommendations, update_recommendations_with_autopsy_learning
from flask import Flask, request, jsonify, redirect, url_for, render_template, send_from_directory, session, flash, Response
from csrf_protection import csrf_protected, require_csrf_token, CSRFTokenType
from enhanced_token_management import SimpleTokenManager, check_token_status
from flask_login import LoginManager, login_required, current_user, login_user, logout_user
from auth import User
from settings_utils import handle_settings_change, track_settings_changes
from werkzeug.security import generate_password_hash
import secrets
from sync_fix import apply_sync_fix

# Import utility functions
from utils import ensure_date_serialization, aggregate_daily_activities_with_rest, is_feature_enabled, get_secret

# Import database optimization modules
from db_connection_manager import initialize_database_pool, get_database_manager
from optimized_token_management import OptimizedTokenManager, batch_refresh_all_tokens
from optimized_acwr_service import OptimizedACWRService, batch_recalculate_all_acwr

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

# API Logging Middleware for Performance Monitoring
@app.before_request
def log_request_start():
    """Log the start of each API request"""
    request.start_time = time.time()
    request.request_size = len(request.get_data()) if request.get_data() else 0

@app.after_request
def log_request_end(response):
    """Log the completion of each API request"""
    try:
        # Calculate response time
        response_time_ms = int((time.time() - getattr(request, 'start_time', time.time())) * 1000)
        
        # Get request details
        endpoint = request.endpoint or request.path
        method = request.method
        status_code = response.status_code
        user_id = getattr(current_user, 'id', None) if hasattr(current_user, 'id') else None
        
        # Get response size (handle direct passthrough mode)
        try:
            response_data = response.get_data()
            response_size = len(response_data) if response_data else 0
        except Exception:
            # Handle direct passthrough mode or other response types
            response_size = 0
        
        # Get client info
        user_agent = request.headers.get('User-Agent', '')
        ip_address = request.remote_addr
        
        # Log to database (async to avoid blocking response)
        log_api_request_async(
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=status_code,
            user_id=user_id,
            request_size=request.request_size,
            response_size=response_size,
            user_agent=user_agent,
            ip_address=ip_address,
            error_message=None if status_code < 400 else f"HTTP {status_code}"
        )
        
    except Exception as e:
        # Don't let logging errors break the response
        logger.warning(f"API logging error: {str(e)}")
    
    return response

def log_api_request_async(endpoint, method, response_time_ms, status_code, user_id=None, 
                         request_size=0, response_size=0, user_agent='', ip_address='', error_message=None):
    """Log API request to database (non-blocking)"""
    try:
        from db_utils import execute_query
        
        execute_query("""
            INSERT INTO api_logs (
                endpoint, method, response_time_ms, status_code, user_id,
                request_size_bytes, response_size_bytes, user_agent, ip_address, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, params=(
            endpoint, method, response_time_ms, status_code, user_id,
            request_size, response_size, user_agent, ip_address, error_message
        ))
        
    except Exception as e:
        # Log to application logger if database logging fails
        logger.error(f"Failed to log API request to database: {str(e)}")

# Initialize database connection pool
def initialize_database_pool_on_startup():
    """Initialize database connection pool for improved performance with robust error handling"""
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("❌ DATABASE_URL environment variable not found")
            logger.warning("⚠️  Falling back to direct database connections")
            return False
            
        logger.info(f"🔗 Initializing database connection pool...")
        logger.info(f"📊 Database URL: {database_url[:50]}...")
        
        # Try to initialize the connection pool
        success = initialize_database_pool(database_url)
        
        if success:
            # Test the connection pool
            try:
                from db_connection_manager import db_manager
                with db_manager.get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        result = cursor.fetchone()
                        if result:
                            logger.info("✅ Database connection pool initialized and tested successfully")
                            return True
                        else:
                            logger.error("❌ Connection pool test failed - no result returned")
                            return False
            except Exception as test_error:
                logger.error(f"❌ Connection pool test failed: {str(test_error)}")
                return False
        else:
            logger.error("❌ Failed to initialize database connection pool")
            logger.warning("⚠️  Falling back to direct database connections")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error initializing database connection pool: {str(e)}")
        logger.warning("⚠️  Falling back to direct database connections")
        return False

# Initialize database pool immediately after app creation
initialize_database_pool_on_startup()

# Cleanup database pool on app shutdown
@app.teardown_appcontext
def cleanup_database_pool(error):
    """Cleanup database connection pool on app shutdown"""
    if error:
        logger.error(f"Application error detected: {str(error)}")
    # Note: Connection pool cleanup is handled automatically by the pool manager

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access your training dashboard.'

@login_manager.unauthorized_handler
def unauthorized():
    """Handle unauthorized access - return JSON for API calls, redirect for pages"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Authentication required',
            'data': []
        }), 401
    # For non-API requests, use default behavior (redirect to login)
    return redirect(url_for('login'))

# Helper function for safe user ID logging
def get_user_id_for_logging():
    """Safely get current user ID for logging, handling anonymous users"""
    try:
        if current_user and current_user.is_authenticated:
            return current_user.id
        return "anonymous"
    except:
        return "unknown"

@login_manager.user_loader
def load_user(user_id):
    """Required by Flask-Login to reload user from session"""
    return User.get(user_id)

def needs_onboarding(user_id):
    """Check if user needs to complete onboarding with robust error handling"""
    try:
        # Use connection pool for onboarding operations
        data = db_utils.execute_query_for_onboarding("""
            SELECT age, gender, training_experience, primary_sport, resting_hr, max_hr, coaching_tone
            FROM user_settings 
            WHERE id = %s
        """, (user_id,), fetch=True)
        
        if not data or len(data) == 0:
            logger.info(f"User {user_id} not found in database - needs onboarding")
            return True  # Needs onboarding
            
        user_data = data[0]
        
        # Check if all required fields are present
        required_fields = ['age', 'gender', 'training_experience', 'primary_sport', 'resting_hr', 'max_hr', 'coaching_tone']
        missing_fields = [field for field in required_fields if not user_data.get(field)]
        
        if missing_fields:
            logger.info(f"User {user_id} missing onboarding fields: {missing_fields}")
            return True  # Needs onboarding
        
        logger.info(f"User {user_id} onboarding complete")
        return False  # Onboarding complete
                
    except Exception as e:
        logger.error(f"Error checking onboarding status for user {user_id}: {e}")
        return True  # Default to needing onboarding on error

# Register blueprints
from acwr_feature_flag_admin import acwr_feature_flag_admin
from acwr_configuration_admin import acwr_configuration_admin
from acwr_migration_admin import acwr_migration_admin
from acwr_visualization_routes import acwr_visualization_routes
app.register_blueprint(acwr_feature_flag_admin)
app.register_blueprint(acwr_configuration_admin)
app.register_blueprint(acwr_migration_admin)
app.register_blueprint(acwr_visualization_routes)


# =============================================================================
# SECTION 1: DATA SYNCHRONIZATION ROUTES
# =============================================================================
# Routes for syncing Strava data, OAuth callbacks, and token management







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
            'resting_hr': 44,
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
            logger.error(f"Strava connection failed: {str(e)}")
            return jsonify({'error': 'Failed to connect to Strava'}), 400

        # Calculate date range using user's timezone
        from timezone_utils import get_user_current_date
        user_current_date = get_user_current_date(user_id)
        end_date = user_current_date
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        logger.info(f"Processing activities from {start_date_str} to {end_date_str} (user timezone)")

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
        try:
            token_response = client.exchange_code_for_token(
                client_id=client_id,
                client_secret=client_secret,
                code=auth_code
            )
        except Exception as token_error:
            error_msg = str(token_error).lower()
            if 'expired' in error_msg or 'invalid' in error_msg or 'code' in error_msg:
                logger.warning(f"OAuth code expired or invalid: {str(token_error)}")
                flash('The authorization code has expired. Please try connecting to Strava again.', 'warning')
                return redirect('/')
            else:
                logger.error(f"Token exchange failed: {str(token_error)}")
                flash('Unable to connect to Strava. Please try again.', 'danger')
                return redirect('/')

        # Get athlete info
        temp_client = Client(access_token=token_response['access_token'])
        athlete = temp_client.get_athlete()
        athlete_id = str(athlete.id)

        # Check if user already exists by Strava athlete ID or by athlete ID in database
        existing_user = User.get_by_email(f"strava_{athlete_id}@training-monkey.com")
        
        # If not found by Strava email, check if user exists with this athlete ID
        if not existing_user:
            athlete_query = """
                SELECT id, email FROM user_settings 
                WHERE strava_athlete_id = %s
            """
            athlete_result = db_utils.execute_query(athlete_query, (int(athlete_id),), fetch=True)
            if athlete_result and athlete_result[0]:
                existing_user = User.get(athlete_result[0]['id'])
                logger.info(f"Found existing user {existing_user.id} by athlete ID {athlete_id}")
        
        if existing_user:
            # Existing user - log them in and update tokens
            login_user(existing_user)
            
            # Update their Strava tokens
            try:
                logger.info(f"Updating tokens for user {existing_user.id} (athlete {athlete_id})")
                logger.info(f"Token expires at: {token_response['expires_at']}")
                
                result = db_utils.execute_query(
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
                
                logger.info(f"Database update result: {result}")
                logger.info(f"Successfully updated tokens for user {existing_user.id}")
                
            except Exception as db_error:
                logger.error(f"Database update failed for user {existing_user.id}: {str(db_error)}")
                flash('Error updating Strava connection. Please try again.', 'danger')
                return redirect('/strava-setup')
            
            flash('Welcome back! Your Strava connection has been updated.', 'success')
            return redirect('/welcome-post-strava')
        
        # New user - create account automatically
        logger.info(f"Creating new user account for Strava athlete {athlete_id}")
        
        import secrets
        from werkzeug.security import generate_password_hash
        
        temp_password = secrets.token_urlsafe(16)
        password_hash = generate_password_hash(temp_password)
        
        # Try to get real email from Strava profile (requires profile:read_all scope)
        real_email = getattr(athlete, 'email', None)
        
        if real_email and '@' in real_email:
            email = real_email
            logger.info(f"Using real email from Strava: {email}")
        else:
            # Fallback to synthetic email if Strava doesn't provide one
            email = f"strava_{athlete_id}@training-monkey.com"
            logger.warning(f"No email provided by Strava, using synthetic: {email}")
        
        first_name = getattr(athlete, 'firstname', '')
        last_name = getattr(athlete, 'lastname', '')
        gender = getattr(athlete, 'sex', 'male')
        resting_hr = getattr(athlete, 'resting_hr', None) or 44
        max_hr = getattr(athlete, 'max_hr', None) or 178
        
        # Create new user and immediately retrieve it in the same connection
        from db_utils import get_db_connection
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Log user creation attempt
                logger.info(f"Attempting to create user with email: {email}, athlete_id: {athlete_id}")
                logger.info(f"Token data - access_token length: {len(token_response['access_token'])}, refresh_token length: {len(token_response['refresh_token'])}, expires_at: {token_response['expires_at']}")
                
                # Insert user
                cursor.execute(
                    """INSERT INTO user_settings (
                        email, password_hash, is_admin, 
                        resting_hr, max_hr, gender,
                        strava_athlete_id, strava_access_token, strava_refresh_token, strava_token_expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (
                        email, password_hash, False,
                        resting_hr, max_hr, gender,
                        int(athlete_id), token_response['access_token'],
                        token_response['refresh_token'], token_response['expires_at']
                    )
                )
                
                result = cursor.fetchone()
                if not result:
                    logger.error("Failed to create new user account - no ID returned")
                    flash('Error creating user account. Please try again.', 'danger')
                    return redirect('/')
                
                # Handle both dictionary and tuple results
                if isinstance(result, dict):
                    new_user_id = result['id']
                else:
                    new_user_id = result[0]
                
                # Notify admin of new user registration
                try:
                    from admin_notifications import notify_admin_of_new_user
                    notify_admin_of_new_user(new_user_id, email)
                except Exception as e:
                    logger.warning(f"Failed to send admin notification: {str(e)}")
                
                logger.info(f"Created user with ID {new_user_id}, now retrieving...")
                logger.info(f"Result type: {type(result)}, Result: {result}")
                
                # Commit the transaction explicitly
                conn.commit()
                logger.info(f"Database transaction committed for user {new_user_id}")
                
                # Immediately retrieve the user in the same connection
                cursor.execute(
                    "SELECT id, email, password_hash, resting_hr, max_hr, gender, is_admin FROM user_settings WHERE id = %s",
                    (new_user_id,)
                )
                
                user_data = cursor.fetchone()
                if not user_data:
                    logger.error(f"Could not retrieve newly created user ID {new_user_id}")
                    flash('Error logging in. Please try again.', 'danger')
                    return redirect('/')
                
                # Convert to User object
                user_dict = dict(user_data)
                new_user = User(
                    id=user_dict['id'],
                    email=user_dict['email'],
                    password_hash=user_dict['password_hash'],
                    resting_hr=user_dict.get('resting_hr'),
                    max_hr=user_dict.get('max_hr'),
                    gender=user_dict.get('gender'),
                    is_admin=user_dict.get('is_admin', False)
                )
                
                logger.info(f"Successfully created and loaded user {new_user_id}")
                
        except Exception as db_error:
            logger.error(f"Database error during user creation: {str(db_error)}")
            logger.error(f"Database error details: {type(db_error).__name__}: {str(db_error)}")
            logger.error(f"Email: {email}, Athlete ID: {athlete_id}")
            
            # Provide more specific error messages based on error type
            if 'onboarding_step' in str(db_error):
                logger.error("OAuth callback failed due to corrupted onboarding_step data")
                flash('System error: Database corruption detected. Please contact support.', 'danger')
            elif 'connection' in str(db_error).lower():
                flash('Database connection error. Please try again in a few moments.', 'danger')
            elif 'constraint' in str(db_error).lower() or 'duplicate' in str(db_error).lower():
                logger.error(f"Database constraint violation: {str(db_error)}")
                flash('Account already exists. Please try logging in instead.', 'warning')
            elif 'unique' in str(db_error).lower():
                logger.error(f"Unique constraint violation: {str(db_error)}")
                flash('Account already exists. Please try logging in instead.', 'warning')
            else:
                logger.error(f"Unexpected database error: {str(db_error)}")
                flash('Error creating user account. Please try again.', 'danger')
            
            return redirect('/')
        
        # Log in the new user
        login_user(new_user)
        session['is_first_login'] = True
        session['signup_source'] = 'landing_page'
        
        # Start Strava sync immediately after OAuth success
        try:
            logger.info(f"Starting Strava sync for new user {new_user.id}")
            # Trigger sync in background for 28 days of data
            import threading
            import time
            def sync_new_user_data():
                # Small delay to ensure database transaction is committed
                time.sleep(1)
                try:
                    # Import the sync function
                    from strava_training_load import process_activities_for_date_range
                    from stravalib.client import Client
                    from datetime import datetime, timedelta
                    
                    # Calculate date range (28 days back)
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=28)
                    
                    # Load tokens from database for this specific user (same as existing users)
                    user_data = db_utils.execute_query(
                        "SELECT strava_access_token, strava_refresh_token, strava_token_expires_at FROM user_settings WHERE id = %s",
                        (new_user.id,),
                        fetch=True
                    )
                    
                    # Log database query result
                    logger.info(f"Database query result for user {new_user.id}: {user_data}")
                    if user_data and len(user_data) > 0:
                        logger.info(f"Token data: access_token exists: {bool(user_data[0].get('strava_access_token'))}, refresh_token exists: {bool(user_data[0].get('strava_refresh_token'))}")
                    else:
                        logger.error(f"No user data found for user {new_user.id}")
                    
                    if not user_data or not user_data[0].get('strava_access_token'):
                        logger.error(f"No Strava tokens found for new user {new_user.id}")
                        # Don't access session in background thread - just log the error
                        return
                    
                    tokens = user_data[0]
                    logger.info(f"Loaded tokens for new user {new_user.id}, expires at: {tokens.get('strava_token_expires_at')}")
                    
                    # Create Strava client with user's tokens
                    client = Client(access_token=tokens['strava_access_token'])
                    
                    # Test connection
                    try:
                        athlete = client.get_athlete()
                        logger.info(f"Connected to Strava as {athlete.firstname} {athlete.lastname} for new user {new_user.id}")
                    except Exception as conn_error:
                        logger.error(f"Strava connection failed for new user {new_user.id}: {str(conn_error)}")
                        # Don't access session in background thread - just log the error
                        return
                    
                    # Process activities for this user
                    process_activities_for_date_range(
                        client=client,
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        user_id=new_user.id
                    )
                    logger.info(f"Strava sync completed for new user {new_user.id}")
                    # Note: Cannot update session from background thread
                    
                except Exception as sync_error:
                    logger.error(f"Strava sync failed for new user {new_user.id}: {str(sync_error)}")
                    # Note: Cannot update session from background thread
            
            # Start sync in background thread
            sync_thread = threading.Thread(target=sync_new_user_data)
            sync_thread.daemon = True
            sync_thread.start()
            
            # Set sync status in session
            session['strava_sync_in_progress'] = True
            session['strava_sync_complete'] = False
            session['strava_sync_failed'] = False
            
            flash('✅ Strava Connection Successful! Syncing your training data...', 'success')
        except Exception as sync_error:
            logger.error(f"Error starting Strava sync for user {new_user.id}: {str(sync_error)}")
            flash('✅ Strava Connection Successful! You can sync your data from the dashboard.', 'success')
        
        return redirect('/welcome-post-strava')

    except Exception as e:
        error_msg = f"OAuth callback error: {str(e)}"
        logger.error(error_msg)
        
        # Provide user-friendly error messages based on error type
        if 'expired' in str(e).lower() or 'invalid' in str(e).lower():
            flash('The authorization code has expired. Please try connecting to Strava again.', 'warning')
        elif 'network' in str(e).lower() or 'connection' in str(e).lower():
            flash('Network error connecting to Strava. Please check your connection and try again.', 'danger')
        else:
            flash('Unable to connect to Strava. Please try again.', 'danger')
        
        return redirect('/')


@login_required
@app.route('/token-status', methods=['GET'])
def get_token_status():
    """Simple endpoint to check token status for current user"""
    try:
        status = check_token_status(user_id=current_user.id)  # ✅ FIXED: Use current user

        return jsonify({
            'success': True,
            'token_status': status,
            'user_id': current_user.id,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting token status for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/oauth-usage', methods=['GET'])
def get_oauth_usage():
    """Check OAuth usage statistics"""
    try:
        # Get basic user count
        total_users = db_utils.execute_query("SELECT COUNT(*) as user_count FROM user_settings", fetch=True)
        total_count = total_users[0]['user_count'] if total_users and total_users[0] else 0
        
        # Get OAuth type breakdown
        centralized_users = db_utils.execute_query(
            "SELECT COUNT(*) as count FROM user_settings WHERE oauth_type = 'centralized'", 
            fetch=True
        )
        centralized_count = centralized_users[0]['count'] if centralized_users and centralized_users[0] else 0
        
        individual_users = db_utils.execute_query(
            "SELECT COUNT(*) as count FROM user_settings WHERE oauth_type = 'individual'", 
            fetch=True
        )
        individual_count = individual_users[0]['count'] if individual_users and individual_users[0] else 0
        
        # Get token status
        users_with_tokens = db_utils.execute_query(
            "SELECT COUNT(*) as count FROM user_settings WHERE strava_access_token IS NOT NULL AND strava_access_token != ''", 
            fetch=True
        )
        tokens_count = users_with_tokens[0]['count'] if users_with_tokens and users_with_tokens[0] else 0
        
        placeholder_tokens = db_utils.execute_query(
            "SELECT COUNT(*) as count FROM user_settings WHERE strava_access_token LIKE 'centralized_%'", 
            fetch=True
        )
        placeholder_count = placeholder_tokens[0]['count'] if placeholder_tokens and placeholder_tokens[0] else 0
        
        # Get user details
        users = db_utils.execute_query(
            "SELECT id, email, oauth_type, migration_status FROM user_settings ORDER BY id", 
            fetch=True
        )
        
        user_details = []
        if users:
            for user in users:
                user_details.append({
                    'id': user['id'],
                    'email': user['email'],
                    'oauth_type': user['oauth_type'],
                    'migration_status': user['migration_status']
                })
        
        return jsonify({
            'success': True,
            'total_users': total_count,
            'centralized_users': centralized_count,
            'individual_users': individual_count,
            'users_with_tokens': tokens_count,
            'users_with_placeholder_tokens': placeholder_count,
            'user_details': user_details,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting OAuth usage: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
@login_required
@app.route('/migration-status', methods=['GET'])
def get_migration_status():
    """Check migration status for current user"""
    try:
        from existing_user_migration import ExistingUserMigration
        
        migration = ExistingUserMigration()
        status = migration.get_migration_status(current_user.id)
        
        # Get user settings to check OAuth type
        query = """
            SELECT oauth_type, migration_status, strava_access_token, strava_refresh_token
            FROM user_settings 
            WHERE id = %s
        """
        user_settings = db_utils.execute_query(query, (current_user.id,), fetch=True)
        
        oauth_type = 'unknown'
        migration_status_db = 'not_started'
        has_individual_tokens = False
        
        if user_settings and len(user_settings) > 0:
            oauth_type = user_settings[0].get('oauth_type', 'individual')
            migration_status_db = user_settings[0].get('migration_status', 'not_started')
            has_individual_tokens = bool(user_settings[0].get('strava_access_token'))
        
        return jsonify({
            'success': True,
            'user_id': current_user.id,
            'oauth_type': oauth_type,
            'migration_status': migration_status_db,
            'has_individual_tokens': has_individual_tokens,
            'migration_info': {
                'status': status.status if status else 'not_started',
                'started_at': status.started_at.isoformat() if status and status.started_at else None,
                'completed_at': status.completed_at.isoformat() if status and status.completed_at else None,
                'error_message': status.error_message if status else None
            },
            'needs_migration': oauth_type == 'individual' and has_individual_tokens,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting migration status for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@login_required
@app.route('/migrate-user', methods=['POST', 'GET'])
def migrate_current_user():
    """Migrate current user to centralized OAuth"""
    try:
        from existing_user_migration import ExistingUserMigration
        
        # Handle different request methods
        if request.method == 'GET':
            # GET request - no JSON body
            data = {}
            force_migration = False
        else:
            # POST request - parse JSON body
            data = request.get_json() or {}
            force_migration = data.get('force', False)
        
        migration = ExistingUserMigration()
        result = migration.migrate_user(current_user.id, force_migration)
        
        return jsonify({
            'success': result['success'],
            'migration_id': result.get('migration_id'),
            'message': result.get('message'),
            'error_message': result.get('error_message'),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error migrating user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@login_required
@app.route('/sync-with-auto-refresh', methods=['POST'])
def sync_with_automatic_token_management():
    """Enhanced sync endpoint that handles both user and scheduled requests"""
    try:
        logger.info("=== SYNC STARTED ===")

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

            # PROACTIVE TOKEN REFRESH: Check and refresh tokens before sync if needed
            try:
                logger.info(f"Checking if tokens need proactive refresh for user {user_id}...")
                token_status_before = token_manager.get_simple_token_status()
                logger.info(f"Token status before proactive refresh: {token_status_before}")
                
                # Handle different token states appropriately
                token_status = token_status_before.get('status')
                
                if token_status == 'invalid_tokens':
                    logger.error(f"❌ Tokens are invalid for user {user_id} - re-authentication required")
                    return jsonify({
                        'success': False,
                        'error': 'Strava tokens are invalid. Please re-authenticate with Strava.',
                        'needs_reauth': True,
                        'token_status': token_status_before
                    }), 401
                    
                elif token_status in ['expired', 'expiring_soon']:
                    logger.info(f"Tokens need refresh for user {user_id} - refreshing proactively...")
                    refresh_result = token_manager.refresh_strava_tokens()
                    
                    if refresh_result:
                        # Check if refresh result indicates re-authentication needed
                        if isinstance(refresh_result, dict) and refresh_result.get('needs_reauth'):
                            logger.error(f"❌ Token refresh failed - invalid tokens for user {user_id}")
                            return jsonify({
                                'success': False,
                                'error': refresh_result.get('error', 'Invalid tokens - re-authentication required'),
                                'needs_reauth': True,
                                'token_status': token_status_before
                            }), 401
                        else:
                            logger.info(f"✅ Proactive token refresh successful for user {user_id}")
                            token_status_after = token_manager.get_simple_token_status()
                            logger.info(f"Token status after proactive refresh: {token_status_after}")
                    else:
                        logger.error(f"❌ Proactive token refresh failed for user {user_id}")
                        return jsonify({
                            'success': False,
                            'error': 'Failed to refresh Strava tokens. Please re-authenticate with Strava.',
                            'needs_reauth': True,
                            'token_status': token_status_before
                        }), 401
                else:
                    logger.info(f"✅ Tokens are still valid for user {user_id} - no refresh needed")
                    
            except Exception as e:
                logger.error(f"❌ Proactive token refresh check failed: {str(e)}")
                return jsonify({'error': f'Token status check error: {str(e)}'}), 500

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

            # If we get here, we have a valid client
            if not client:
                logger.error("Client validation failed after successful creation")
                return jsonify({
                    'success': False,
                    'error': 'Failed to validate Strava client',
                    'needs_reauth': False
                }), 500

            # Calculate date range using user's timezone
            try:
                from timezone_utils import get_user_current_date
                user_current_date = get_user_current_date(user_id)
                end_date = user_current_date
                start_date = end_date - timedelta(days=days)
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                logger.info(f"Processing activities from {start_date_str} to {end_date_str} (user timezone)")
                logger.info(f"User current date: {user_current_date}")
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
                WHERE id = %s
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

        # Calculate date range using user's timezone
        from timezone_utils import get_user_current_date
        user_current_date = get_user_current_date(user_id)
        end_date = user_current_date
        start_date = end_date - timedelta(days=days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')

        logger.info(f"Processing activities for user {user_id} from {start_date_str} to {end_date_str} (user timezone)")

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


# =============================================================================
# SECTION 5: ADMIN ROUTES
# =============================================================================
# Administrative functions and monitoring endpoints

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

@login_required
@app.route('/admin/database-optimization-status', methods=['GET'])
def database_optimization_status():
    """Get database optimization status and performance metrics"""
    try:
        # Get connection pool status
        db_manager = get_database_manager()
        pool_status = db_manager.get_pool_status()
        
        # Get token health summary
        from optimized_token_management import get_token_health_summary
        token_health = get_token_health_summary()
        
        # Get ACWR calculation status
        from optimized_acwr_service import get_acwr_calculation_status
        acwr_status = get_acwr_calculation_status()
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'connection_pool': pool_status,
            'token_health': token_health,
            'acwr_calculations': acwr_status,
            'optimization_status': {
                'connection_pooling': pool_status.get('status') == 'active',
                'batch_operations': True,
                'performance_monitoring': True
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting database optimization status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@login_required
@app.route('/admin/batch-refresh-tokens', methods=['POST'])
def admin_batch_refresh_tokens():
    """Admin endpoint to batch refresh all tokens"""
    try:
        result = batch_refresh_all_tokens()
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'users_checked': result.get('users_checked', 0),
            'users_refreshed': result.get('users_refreshed', 0),
            'users_failed': result.get('users_failed', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in batch token refresh: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@login_required
@app.route('/admin/batch-recalculate-acwr', methods=['POST'])
def admin_batch_recalculate_acwr():
    """Admin endpoint to batch recalculate ACWR values"""
    try:
        days_back = request.json.get('days_back', 30) if request.is_json else 30
        result = batch_recalculate_all_acwr(days_back)
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', 'ACWR recalculation completed'),
            'activities_processed': result.get('activities_processed', 0),
            'users_processed': result.get('users_processed', 0),
            'calculations_successful': result.get('calculations_successful', 0),
            'database_updates': result.get('database_updates', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in batch ACWR recalculation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with database optimization status"""
    logger.info("Health check starting...")
    db_status = "not connected"
    activity_count_status = "unknown"
    current_db_name = "not_available"
    current_db_user = "not_available"
    found_tables = []
    tables_total_count = 0
    pool_status = "not_initialized"

    try:
        logger.info("Testing database connection...")
        db_utils.execute_query("SELECT 1;")
        db_status = "connected"

        # Get database connection pool status
        try:
            db_manager = get_database_manager()
            pool_status_info = db_manager.get_pool_status()
            pool_status = pool_status_info.get('status', 'unknown')
        except Exception as e:
            logger.warning(f"Could not get pool status: {e}")
            pool_status = "error"

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

        # Check activity count
        try:
            activity_count_result = db_utils.execute_query("SELECT COUNT(*) FROM activities;", fetch=True)
            if activity_count_result and activity_count_result[0]:
                # Handle PostgreSQL (dict) response
                activity_count_status = activity_count_result[0].get('count', 0) or activity_count_result[0].get(
                    'COUNT(*)', 0)
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
        "use_postgres": True,
        "database_connection_status": db_status,
        "connection_pool_status": pool_status,
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
            redirect_uri = "https://yourtrainingmonkey.com/oauth-callback"
            auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,activity:read_all"

            # Store credentials temporarily in session for OAuth callback
            session['temp_strava_client_id'] = client_id
            session['temp_strava_client_secret'] = client_secret

            return redirect(auth_url)

    return render_template('strava_setup.html')


# =============================================================================
# SECTION 2: API ROUTES
# =============================================================================
# REST API endpoints for frontend communication

@login_required
@app.route('/api/training-data', methods=['GET'])
def get_training_data():
    """Get training data for dashboard charts - Enhanced with sport breakdown support"""
    try:
        # Get parameters
        date_range = request.args.get('range', '90')  # days
        include_sport_breakdown = request.args.get('include_sport_breakdown', 'false').lower() == 'true'

        # Calculate date filter using user's timezone
        from datetime import datetime, timedelta
        from timezone_utils import get_user_current_date
        user_current_date = get_user_current_date(current_user.id)
        end_date = user_current_date
        start_date = end_date - timedelta(days=int(date_range))
        start_date_str = start_date.strftime('%Y-%m-%d')

        logger.info(f"Getting training data for user {current_user.id}, range: {date_range} days, "
                    f"sport breakdown: {include_sport_breakdown} (user timezone)")

        logger.info(f"Executing database query for user {current_user.id} with date filter: {start_date_str}")
        
        # Try a simpler query first to avoid potential locks
        logger.info(f"Testing simple count query first...")
        count_result = db_utils.execute_query(
            "SELECT COUNT(*) as count FROM activities WHERE user_id = %s",
            (current_user.id,),
            fetch=True
        )
        logger.info(f"Count query result: {count_result}")
        
        # Now try the full query
        activities = db_utils.execute_query(
            """
            SELECT * FROM activities 
            WHERE user_id = %s 
            AND date >= %s
            ORDER BY date ASC, activity_id ASC
            """,
            (current_user.id, start_date_str),
            fetch=True
        )
        logger.info(f"Database query completed. Found {len(activities) if activities else 0} activities")

        if not activities:
            logger.info(f"No activities found for user {current_user.id} - returning empty response")
            
            # Check if user has Strava access token (can sync)
            user_data = db_utils.execute_query(
                "SELECT strava_access_token, strava_athlete_id FROM user_settings WHERE id = %s",
                (current_user.id,),
                fetch=True
            )
            
            has_strava_token = user_data and user_data[0].get('strava_access_token')
            strava_athlete_id = user_data[0].get('strava_athlete_id') if user_data else None
            
            response_data = {
                'success': True,
                'message': 'No activities found',
                'data': [],
                'count': 0,
                'raw_count': 0,
                'can_sync': has_strava_token,
                'strava_athlete_id': strava_athlete_id,
                'has_data': False,
                'needs_sync': has_strava_token
            }

            # Add sport breakdown fields even when no data
            if include_sport_breakdown:
                response_data.update({
                    'has_cycling_data': False,
                    'has_swimming_data': False,
                    'sport_summary': []
                })

            logger.info(f"Returning empty response for user {current_user.id} (can_sync: {has_strava_token})")
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

            # Get sport summary and multi-sport data flags
            from unified_metrics_service import UnifiedMetricsService
            has_cycling_data = UnifiedMetricsService.has_cycling_data(
                current_user.id, start_date_str, end_date.strftime('%Y-%m-%d')
            )
            has_swimming_data = UnifiedMetricsService.has_swimming_data(
                current_user.id, start_date_str, end_date.strftime('%Y-%m-%d')
            )
            sport_summary = UnifiedMetricsService.get_sport_summary(
                current_user.id, start_date_str, end_date.strftime('%Y-%m-%d')
            ) if (has_cycling_data or has_swimming_data) else []
        else:
            # Use existing aggregation for backward compatibility
            aggregated_data = aggregate_daily_activities_with_rest(activity_list)
            has_cycling_data = False
            has_swimming_data = False
            sport_summary = []

        # CRITICAL FIX: Apply date serialization AFTER aggregation too
        aggregated_data = [ensure_date_serialization(activity) for activity in aggregated_data]

        # Check if user has custom dashboard configuration
        dashboard_config = None
        try:
            config_result = db_utils.execute_query("""
                SELECT chronic_period_days, decay_rate, is_active
                FROM user_dashboard_configs 
                WHERE user_id = %s AND is_active = TRUE
                ORDER BY updated_at DESC
                LIMIT 1
            """, (current_user.id,), fetch=True)
            
            if config_result:
                dashboard_config = config_result[0]
                logger.info(f"User {current_user.id} has custom dashboard config: {dashboard_config}")
        except Exception as e:
            logger.warning(f"Could not check dashboard config for user {current_user.id}: {str(e)}")

        # If user has custom configuration, recalculate ACWR values
        if dashboard_config:
            logger.info(f"Recalculating ACWR with custom config: chronic={dashboard_config['chronic_period_days']}d, decay={dashboard_config['decay_rate']}")
            aggregated_data = recalculate_acwr_with_config(aggregated_data, dashboard_config, current_user.id)

        logger.info(f"Processed to {len(aggregated_data)} daily records for dashboard")

        # Build response maintaining existing structure
        response_data = {
            'success': True,
            'data': aggregated_data,  # Now with properly serialized dates
            'count': len(aggregated_data),
            'raw_count': len(activity_list),
            'dashboard_config': dashboard_config  # Include config info for frontend
        }

        # Add sport breakdown fields if requested
        if include_sport_breakdown:
            response_data.update({
                'has_cycling_data': has_cycling_data,
                'has_swimming_data': has_swimming_data,
                'sport_summary': sport_summary
            })

            logger.info(f"Sport breakdown enabled: cycling data={has_cycling_data}, swimming data={has_swimming_data}, "
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
                },
                'dashboard_config': None
            })

        # Count total real activities for the current user
        activity_count_result = db_utils.execute_query(
            "SELECT COUNT(*) FROM activities WHERE user_id = %s AND activity_id > 0",
            (current_user.id,),
            fetch=True
        )

        # Handle PostgreSQL (dict) response format
        if activity_count_result and activity_count_result[0]:
            result_row = activity_count_result[0]
            # PostgreSQL returns dict-like object
            total_activities = result_row.get('count', 0) or result_row.get('COUNT(*)', 0)
        else:
            total_activities = 0

        # Get user's dashboard configuration
        dashboard_config = None
        try:
            config_result = db_utils.execute_query("""
                SELECT chronic_period_days, decay_rate, is_active
                FROM user_dashboard_configs 
                WHERE user_id = %s AND is_active = TRUE
                ORDER BY updated_at DESC
                LIMIT 1
            """, (current_user.id,), fetch=True)
            
            if config_result:
                dashboard_config = config_result[0]
                logger.info(f"User {current_user.id} has custom dashboard config: {dashboard_config}")
        except Exception as e:
            logger.warning(f"Could not check dashboard config for user {current_user.id}: {str(e)}")

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
            },
            'dashboard_config': dashboard_config  # Include config info for frontend
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
            },
            'dashboard_config': None
        }), 500


# =============================================================================
# SECTION 6: MAIN APPLICATION ROUTES
# =============================================================================
# Home page, dashboard, and core application routes

@app.route('/')
def home():
    """Landing page for new users, dashboard for existing users"""
    if current_user.is_authenticated:
        # Existing user - redirect to dashboard
        response = send_from_directory('build', 'index.html')
        # CRITICAL: Prevent caching of index.html so users always get latest JS file references
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # New/unauthenticated user - show landing page
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Serve React dashboard"""
    # Phase 1: Track email enforcement status (passive monitoring only)
    # TODO: Enable Phase 2 in 5-7 days - see EMAIL_ENFORCEMENT_ROADMAP.md
    try:
        from email_enforcement import get_email_urgency_level, log_email_enforcement_status
        
        user_data = {
            'email': current_user.email,
            'registration_date': current_user.registration_date,
            'is_admin': current_user.is_admin,
            'email_modal_dismissals': getattr(current_user, 'email_modal_dismissals', 0)
        }
        
        urgency = get_email_urgency_level(user_data)
        log_email_enforcement_status(current_user.id, urgency)
        
    except Exception as e:
        # Fail silently - don't disrupt user experience
        logger.error(f"Email enforcement tracking error for user {current_user.id}: {e}")
    
    response = send_from_directory('build', 'index.html')
    # CRITICAL: Prevent caching of index.html so users always get latest JS file references
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# =============================================================================
# SECTION 4: STATIC FILE SERVING
# =============================================================================
# Routes for serving static files, favicon, manifest, etc.

# Flask's default static file serving will handle /static/ requests
# No custom route needed since files are now in the default static folder

@app.route('/test-image')
def test_image():
    """Test route to verify training-monkey-runner.webp is accessible"""
    try:
        import os
        static_path = os.path.join(app.static_folder, 'training-monkey-runner.webp')
        if os.path.exists(static_path):
            return f"Image exists at: {static_path}<br>Size: {os.path.getsize(static_path)} bytes"
        else:
            return f"Image NOT found at: {static_path}<br>Static folder: {app.static_folder}<br>Contents: {os.listdir(app.static_folder) if os.path.exists(app.static_folder) else 'Static folder not found'}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory('build', 'favicon.ico')
    except:
        return '', 404

@app.route('/manifest.json')
def manifest():
    """Serve manifest.json"""
    try:
        return send_from_directory('build', 'manifest.json')
    except:
        return '', 404

@app.route('/sitemap.xml')
def sitemap():
    """Serve sitemap.xml for search engines"""
    try:
        return send_from_directory('static', 'sitemap.xml', mimetype='application/xml')
    except Exception as e:
        logger.error(f"Error serving sitemap.xml: {str(e)}")
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


@login_required
@app.route('/api/training-data-raw', methods=['GET'])
def get_training_data_raw():
    """Get raw training data without aggregation for debugging"""
    try:
        activities = db_utils.execute_query(
            """
            SELECT date, activity_id, name, type, total_load_miles, trimp, 
                   acute_chronic_ratio, trimp_acute_chronic_ratio, normalized_divergence
            FROM activities 
            WHERE user_id = %s AND activity_id > 0
            ORDER BY date DESC, activity_id ASC
            LIMIT 20
            """,
            (current_user.id,),
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
        logger.error(f"Error fetching LLM recommendations for user {get_user_id_for_logging()}: {str(e)}")
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


@login_required
@app.route('/api/journal-status', methods=['GET'])
def get_journal_status_endpoint():
    """
    Get journal status for last activity - used by Dashboard to enforce workflow.
    Simple check: Does last activity have journal entry?
    """
    try:
        logger.info(f"Fetching journal status for user {current_user.id}")
        
        # Get journal status for last activity
        status = get_last_activity_journal_status(current_user.id)
        
        # Get latest recommendation to check if autopsy-informed
        from db_utils import get_latest_recommendation
        latest_rec = get_latest_recommendation(current_user.id)
        
        response = {
            'success': True,
            'status': status,
            'has_recommendation': bool(latest_rec),
            'recommendation_is_autopsy_informed': latest_rec.get('is_autopsy_informed', False) if latest_rec else False,
            'recommendation_target_date': latest_rec.get('target_date') if latest_rec else None
        }
        
        logger.info(f"Journal status for user {current_user.id}: {status['reason']}, has_recommendation: {response['has_recommendation']}, autopsy_informed: {response['recommendation_is_autopsy_informed']}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting journal status for user {get_user_id_for_logging()}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'status': {
                'has_activity': False,
                'activity_date': None,
                'has_journal': False,
                'allow_manual_generation': True,
                'reason': 'error'
            }
        }), 500


# =============================================================================
# SECTION 3: AUTHENTICATION & USER MANAGEMENT ROUTES
# =============================================================================
# Login, logout, signup, and user account management

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
                return jsonify({'success': True, 'redirect': '/dashboard'})
            else:
                return redirect('/dashboard')
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


@app.route('/api/user/update-email', methods=['POST'])
@login_required
def update_user_email():
    """Update user's email address"""
    try:
        data = request.get_json()
        new_email = data.get('email', '').strip().lower()
        
        if not new_email or '@' not in new_email or '.' not in new_email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        # Check if email already exists for another user
        existing_check = db_utils.execute_query(
            "SELECT id FROM user_settings WHERE email = %s AND id != %s",
            (new_email, current_user.id),
            fetch=True
        )
        
        if existing_check:
            return jsonify({'error': 'Email already in use by another account'}), 400
        
        # Update email in database
        db_utils.execute_query(
            "UPDATE user_settings SET email = %s WHERE id = %s",
            (new_email, current_user.id),
            fetch=False
        )
        
        # Update current user object
        current_user.email = new_email
        
        # Log the change
        logger.info(f"User {current_user.id} updated email to {new_email}")
        
        return jsonify({
            'success': True, 
            'message': 'Email updated successfully',
            'email': new_email
        })
        
    except Exception as e:
        logger.error(f"Error updating email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user/dismiss-email-modal', methods=['POST'])
@login_required
def dismiss_email_modal():
    """Track email modal dismissals"""
    try:
        # Get current dismiss count - handle if column doesn't exist yet
        try:
            result = db_utils.execute_query(
                "SELECT email_modal_dismissals FROM user_settings WHERE id = %s",
                (current_user.id,),
                fetch=True
            )
            current_count = result.get('email_modal_dismissals', 0) if result else 0
        except:
            # Column might not exist yet, default to 0
            current_count = 0
        
        new_count = current_count + 1
        
        # Try to update dismiss count - will fail if column doesn't exist
        try:
            db_utils.execute_query(
                "UPDATE user_settings SET email_modal_dismissals = %s WHERE id = %s",
                (new_count, current_user.id),
                fetch=False
            )
        except:
            # Column doesn't exist yet - log but don't fail
            logger.warning(f"email_modal_dismissals column not yet added to database")
            pass
        
        logger.info(f"User {current_user.id} dismissed email modal ({new_count}/3)")
        
        return jsonify({'success': True, 'dismissals': new_count})
        
    except Exception as e:
        logger.error(f"Error tracking modal dismissal: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/auth/strava-signup')
def strava_auth_signup():
    """Strava OAuth initiation for new user signup from landing page"""
    try:
        # Use the Strava app's configured redirect URI
        redirect_uri = "https://yourtrainingmonkey.com/oauth-callback"
        client_id = os.environ.get('STRAVA_CLIENT_ID', '').strip()

        if not client_id:
            logger.error("STRAVA_CLIENT_ID not found in environment variables")
            flash('Strava integration not configured. Please contact support.', 'danger')
            return redirect('/')

        # Set session flag to indicate this is a new user signup
        session['is_new_user_signup'] = True
        session['signup_source'] = 'landing_page'

        # Use urllib.parse.urlencode to properly encode parameters
        from urllib.parse import urlencode

        params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'approval_prompt': 'force',
            'scope': 'read,activity:read_all,profile:read_all'  # Added profile scope for email
        }

        auth_url = f"https://www.strava.com/oauth/authorize?{urlencode(params)}"

        logger.info(f"Redirecting new user to Strava OAuth for client_id: {client_id}")
        return redirect(auth_url)

    except Exception as e:
        logger.error(f"Error initiating Strava OAuth for signup: {str(e)}")
        flash('Unable to connect to Strava. Please try again.', 'danger')
        return redirect('/')


# Removed duplicate oauth-callback-signup route - functionality consolidated into oauth-callback


@app.route('/api/landing/analytics', methods=['POST'])
def landing_analytics():
    """Track landing page interactions for optimization"""
    try:
        data = request.get_json()
        event_type = data.get('event_type')
        event_data = data.get('event_data', {})
        
        # Import analytics tracker with fallback
        try:
            from analytics_tracker import track_analytics_event, EventType, IntegrationPoint
        except ImportError:
            logger.warning("analytics_tracker module not available - skipping analytics tracking")
            return jsonify({'success': True, 'message': 'Analytics tracking disabled'})
        
        # Map event types to analytics tracker types
        event_type_mapping = {
            'cta_click': EventType.CTA_CLICK,
            'integration_point_click': EventType.INTEGRATION_POINT_CLICK,
            'getting_started_access': EventType.GETTING_STARTED_ACCESS,
            'tutorial_start': EventType.TUTORIAL_START,
            'tutorial_complete': EventType.TUTORIAL_COMPLETE,
            'tutorial_skip': EventType.TUTORIAL_SKIP,
            'demo_interaction': EventType.DEMO_INTERACTION,
            'page_view': EventType.PAGE_VIEW,
            'scroll_depth': EventType.SCROLL_DEPTH,
            'tutorial_trigger_shown': EventType.TUTORIAL_TRIGGER_SHOWN,
            'tutorial_trigger_clicked': EventType.TUTORIAL_TRIGGER_CLICKED
        }
        
        # Map integration points
        integration_point_mapping = {
            'landing_cta': IntegrationPoint.LANDING_CTA,
            'landing_see_how_it_works': IntegrationPoint.LANDING_SEE_HOW_IT_WORKS,
            'onboarding_help_link': IntegrationPoint.ONBOARDING_HELP_LINK,
            'dashboard_help_button': IntegrationPoint.DASHBOARD_HELP_BUTTON,
            'settings_guide_button': IntegrationPoint.SETTINGS_GUIDE_BUTTON,
            'goals_guide_button': IntegrationPoint.GOALS_GUIDE_BUTTON,
            'replay_tutorial_button': IntegrationPoint.REPLAY_TUTORIAL_BUTTON,
            'contextual_tutorial_trigger': IntegrationPoint.CONTEXTUAL_TUTORIAL_TRIGGER
        }
        
        # Get mapped values
        mapped_event_type = event_type_mapping.get(event_type, EventType.PAGE_VIEW)
        integration_point = None
        if 'integration_point' in event_data:
            integration_point = integration_point_mapping.get(event_data['integration_point'])
        
        # Get user info if available
        user_id = current_user.id if current_user.is_authenticated else None
        session_id = session.get('session_id', request.remote_addr)
        
        # Determine source and target pages
        source_page = event_data.get('source', 'unknown')
        target_page = event_data.get('target', None)
        
        # Track the event
        success = track_analytics_event(
            event_type=mapped_event_type,
            event_data=event_data,
            user_id=user_id,
            session_id=session_id,
            integration_point=integration_point,
            source_page=source_page,
            target_page=target_page,
            request=request
        )
        
        if success:
            # Log analytics event for monitoring
            logger.info(f"Analytics event tracked: {event_type} - {event_data}")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to track event'}), 500

    except Exception as e:
        logger.error(f"Error tracking landing page analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/click-through-rates', methods=['GET'])
@login_required
def get_click_through_rates():
    """Get click-through rate analytics for integration points"""
    try:
        try:
            from analytics_tracker import analytics_tracker
            from dataclasses import asdict
        except ImportError:
            logger.warning("analytics_tracker module not available - returning empty analytics")
            return jsonify({'success': True, 'data': []})
        
        # Get query parameters
        time_period = request.args.get('time_period', '7d')
        integration_points = request.args.getlist('integration_points')
        
        # Get click-through rates
        ctr_data = analytics_tracker.get_click_through_rates(
            time_period=time_period,
            integration_points=integration_points if integration_points else None
        )
        
        return jsonify({
            'success': True,
            'data': [asdict(ctr) for ctr in ctr_data]
        })
        
    except Exception as e:
        logger.error(f"Error getting click-through rates: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/analytics/user-journey-funnel', methods=['GET'])
@login_required
def get_user_journey_funnel():
    """Get user journey conversion funnel analytics"""
    try:
        try:
            from analytics_tracker import analytics_tracker
        except ImportError:
            logger.warning("analytics_tracker module not available - returning empty funnel data")
            return jsonify({'success': True, 'data': []})
        
        # Get query parameters
        time_period = request.args.get('time_period', '7d')
        
        # Get funnel data
        funnel_data = analytics_tracker.get_user_journey_funnel(time_period=time_period)
        
        return jsonify({
            'success': True,
            'data': funnel_data
        })
        
    except Exception as e:
        logger.error(f"Error getting user journey funnel: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/tutorial-metrics', methods=['GET'])
@login_required
def get_tutorial_analytics():
    """Get tutorial analytics and completion rates"""
    try:
        try:
            from analytics_tracker import analytics_tracker
        except ImportError:
            logger.warning("analytics_tracker module not available - returning empty tutorial data")
            return jsonify({'success': True, 'data': []})
        
        # Get query parameters
        time_period = request.args.get('time_period', '7d')
        
        # Get tutorial analytics
        tutorial_data = analytics_tracker.get_tutorial_analytics(time_period=time_period)
        
        return jsonify({
            'success': True,
            'data': tutorial_data
        })
        
    except Exception as e:
        logger.error(f"Error getting tutorial analytics: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PERFORMANCE MONITORING ENDPOINTS (RUM Metrics)
# ============================================================================

@app.route('/api/analytics/rum-metrics', methods=['POST'])
def track_rum_metrics():
    """
    Track Real User Monitoring (RUM) metrics from the frontend
    Captures page load timing, Core Web Vitals, and resource metrics
    """
    try:
        data = request.get_json()
        
        # Extract metrics from request
        page = data.get('page', 'unknown')
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Log to console for immediate visibility
        logger.info(f"RUM Metrics - Page: {page}, TTFB: {data.get('ttfb')}ms, "
                   f"Load Complete: {data.get('load_complete')}ms, "
                   f"LCP: {data.get('lcp', 'N/A')}ms")
        
        # Store in database (using db_utils connection)
        with db_utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rum_metrics (
                    page, user_id, ttfb, fcp, lcp, dns_time, connection_time,
                    request_time, response_time, dom_interactive_time, dom_complete_time,
                    load_complete, resource_count, total_resource_size,
                    user_agent, viewport_width, viewport_height, connection_type,
                    timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                page, user_id,
                data.get('ttfb'), data.get('fcp'), data.get('lcp'),
                data.get('dns_time'), data.get('connection_time'),
                data.get('request_time'), data.get('response_time'),
                data.get('dom_interactive_time'), data.get('dom_complete_time'),
                data.get('load_complete'), data.get('resource_count'),
                data.get('total_resource_size'), data.get('user_agent'),
                data.get('viewport_width'), data.get('viewport_height'),
                data.get('connection_type'), data.get('timestamp')
            ))
            conn.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking RUM metrics: {str(e)}", exc_info=True)
        # Don't fail - monitoring should be non-blocking
        return jsonify({'success': False, 'error': 'Metrics logging failed'}), 200


@app.route('/api/analytics/component-performance', methods=['POST'])
def track_component_performance():
    """
    Track component-level performance metrics
    Captures fetch time, processing time, and render time for React components
    """
    try:
        data = request.get_json()
        
        page = data.get('page', 'unknown')
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Log for visibility
        logger.info(f"Component Performance - {page}: "
                   f"Fetch: {data.get('fetch_time_ms')}ms, "
                   f"Process: {data.get('process_time_ms')}ms, "
                   f"Render: {data.get('render_time_ms')}ms, "
                   f"Total: {data.get('total_time_ms')}ms")
        
        # Store in database
        with db_utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO component_performance (
                    page, user_id, fetch_time_ms, process_time_ms, render_time_ms,
                    total_time_ms, data_points, error, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """, (
                page, user_id,
                data.get('fetch_time_ms'), data.get('process_time_ms'),
                data.get('render_time_ms'), data.get('total_time_ms'),
                data.get('data_points'), data.get('error')
            ))
            conn.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking component performance: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Metrics logging failed'}), 200


@app.route('/api/analytics/api-timing', methods=['POST'])
def track_api_timing():
    """
    Track frontend API call timing
    Captures client-side timing for API requests (complementing server-side api_logs)
    """
    try:
        data = request.get_json()
        
        api_name = data.get('api_name', 'unknown')
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Log for visibility
        if data.get('success'):
            logger.info(f"API Timing - {api_name}: {data.get('duration_ms')}ms")
        else:
            logger.warning(f"API Timing - {api_name} FAILED: {data.get('duration_ms')}ms - {data.get('error')}")
        
        # Store in database
        with db_utils.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO api_timing_client (
                    api_name, user_id, duration_ms, success, error, timestamp
                ) VALUES (
                    %s, %s, %s, %s, %s, NOW()
                )
            """, (
                api_name, user_id, data.get('duration_ms'),
                data.get('success'), data.get('error')
            ))
            conn.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error tracking API timing: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Metrics logging failed'}), 200


# ============================================================================
# END PERFORMANCE MONITORING ENDPOINTS
# ============================================================================


@app.route('/api/tutorials/start', methods=['POST'])
@login_required
def start_tutorial():
    """Start a tutorial and track the start event"""
    try:
        data = request.get_json()
        tutorial_id = data.get('tutorial_id')
        
        if not tutorial_id:
            return jsonify({'success': False, 'error': 'Tutorial ID required'}), 400
        
        # Mark tutorial as started
        from onboarding_tutorial_system import OnboardingTutorialSystem
        tutorial_system = OnboardingTutorialSystem()
        
        success = tutorial_system.mark_tutorial_started(
            user_id=current_user.id,
            tutorial_id=tutorial_id,
            start_data={
                'source': data.get('source', 'unknown'),
                'timestamp': data.get('timestamp')
            }
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Tutorial started successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start tutorial'}), 500
            
    except Exception as e:
        logger.error(f"Error starting tutorial: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tutorials/complete', methods=['POST'])
@login_required
def complete_tutorial():
    """Mark a tutorial as completed and track the completion event"""
    try:
        data = request.get_json()
        tutorial_id = data.get('tutorial_id')
        
        if not tutorial_id:
            return jsonify({'success': False, 'error': 'Tutorial ID required'}), 400
        
        # Mark tutorial as completed
        from onboarding_tutorial_system import OnboardingTutorialSystem
        tutorial_system = OnboardingTutorialSystem()
        
        success = tutorial_system.mark_tutorial_completed(
            user_id=current_user.id,
            tutorial_id=tutorial_id,
            completion_data={
                'source': data.get('source', 'unknown'),
                'timestamp': data.get('timestamp'),
                'completion_time': data.get('completion_time'),
                'steps_completed': data.get('steps_completed')
            }
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Tutorial completed successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to complete tutorial'}), 500
            
    except Exception as e:
        logger.error(f"Error completing tutorial: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tutorials/skip', methods=['POST'])
@login_required
def skip_tutorial():
    """Mark a tutorial as skipped and track the skip event"""
    try:
        data = request.get_json()
        tutorial_id = data.get('tutorial_id')
        
        if not tutorial_id:
            return jsonify({'success': False, 'error': 'Tutorial ID required'}), 400
        
        # Mark tutorial as skipped
        from onboarding_tutorial_system import OnboardingTutorialSystem
        tutorial_system = OnboardingTutorialSystem()
        
        success = tutorial_system.mark_tutorial_skipped(
            user_id=current_user.id,
            tutorial_id=tutorial_id,
            skip_data={
                'source': data.get('source', 'unknown'),
                'timestamp': data.get('timestamp'),
                'skip_reason': data.get('skip_reason'),
                'step_skipped_at': data.get('step_skipped_at')
            }
        )
        
        if success:
            return jsonify({'success': True, 'message': 'Tutorial skipped successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to skip tutorial'}), 500
            
    except Exception as e:
        logger.error(f"Error skipping tutorial: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tutorials/stats', methods=['GET'])
@login_required
def get_tutorial_stats():
    """Get tutorial completion statistics"""
    try:
        from onboarding_tutorial_system import OnboardingTutorialSystem
        
        tutorial_id = request.args.get('tutorial_id')
        time_period = request.args.get('time_period', '7d')
        
        tutorial_system = OnboardingTutorialSystem()
        stats = tutorial_system.get_tutorial_completion_stats(
            tutorial_id=tutorial_id,
            time_period=time_period
        )
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting tutorial stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analytics/detailed-funnel', methods=['GET'])
@login_required
def get_detailed_funnel():
    """Get detailed funnel analysis with cohort tracking"""
    try:
        try:
            from analytics_tracker import analytics_tracker
        except ImportError:
            logger.warning("analytics_tracker module not available - returning empty funnel data")
            return jsonify({'success': True, 'data': []})
        
        # Get query parameters
        time_period = request.args.get('time_period', '7d')
        funnel_type = request.args.get('funnel_type', 'onboarding')
        
        # Get detailed funnel data
        funnel_data = analytics_tracker.get_detailed_funnel_analysis(time_period=time_period)
        
        # Get enhanced funnel data
        enhanced_funnel_data = analytics_tracker.get_user_journey_funnel(
            time_period=time_period, 
            funnel_type=funnel_type
        )
        
        return jsonify({
            'success': True,
            'data': {
                'detailed_funnel': funnel_data,
                'enhanced_funnel': enhanced_funnel_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting detailed funnel: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/dashboard/first-time')
@login_required
def first_time_dashboard():
    """Special dashboard experience for new users from landing page"""
    if not session.get('new_user_onboarding'):
        return redirect('/dashboard')

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
            return redirect('/dashboard?highlight=divergence&new_user=true')
        else:
            return render_template('onboarding.html',
                                   days_needed=max(0, 28 - days_of_data.get('days', 0)) if days_of_data else 28,
                                   activity_count=activity_count.get('count', 0) if activity_count else 0)

    except Exception as e:
        logger.error(f"Error checking user data: {str(e)}")
        return redirect('/dashboard')

# Removed duplicate / route - keeping only the first one
# FIXED: There were two @app.route('/') definitions causing conflicts
# - Line 1679: home() function (KEPT)
# - Line 2176: landing_page() function (REMOVED)
# This was causing 404 errors on /landing route


@app.route('/landing')
def landing_redirect():
    """Redirect /landing to root to prevent duplicate content issues"""
    return redirect('/', code=301)


@app.route('/getting-started')
def getting_started_resources():
    """Unified getting started resources page with context detection"""
    try:
        # Get source parameter for analytics tracking
        source = request.args.get('source', 'direct')
        
        # Initialize user context
        user_context = None
        
        # Check if user is authenticated
        if current_user.is_authenticated:
            user_id = current_user.id
            
            # Get user's onboarding progress
            try:
                from onboarding_manager import get_user_onboarding_progress
                onboarding_progress = get_user_onboarding_progress(user_id)
                
                if onboarding_progress:
                    # Map onboarding step to display name
                    step_display_names = {
                        'welcome': 'Welcome',
                        'strava_connected': 'Strava Connected',
                        'first_activity': 'First Activity',
                        'data_sync': 'Data Sync',
                        'dashboard_intro': 'Dashboard Introduction',
                        'features_tour': 'Features Tour',
                        'goals_setup': 'Goals Setup',
                        'first_recommendation': 'First Recommendation',
                        'journal_intro': 'Journal Introduction',
                        'completed': 'Completed'
                    }
                    
                    # Determine next steps based on current step
                    next_steps_map = {
                        'welcome': 'Create Your Account',
                        'strava_connected': 'Connect with Strava',
                        'first_activity': 'Your first activity has been synced',
                        'data_sync': 'Your data analysis is ready',
                        'dashboard_intro': 'Explore your training dashboard',
                        'features_tour': 'Learn about advanced features',
                        'goals_setup': 'Set your training goals',
                        'first_recommendation': 'Review your AI recommendations',
                        'journal_intro': 'Start tracking your training journal',
                        'completed': 'You\'re all set! Explore all features'
                    }
                    
                    user_context = {
                        'user_id': user_id,
                        'onboarding_step': onboarding_progress.current_step.value,
                        'onboarding_step_display': step_display_names.get(onboarding_progress.current_step.value, 'Unknown'),
                        'next_steps': next_steps_map.get(onboarding_progress.current_step.value, 'Continue with your training'),
                        'features_unlocked': onboarding_progress.features_unlocked,
                        'is_authenticated': True
                    }
                else:
                    # User is authenticated but no onboarding progress found
                    user_context = {
                        'user_id': user_id,
                        'onboarding_step': 'welcome',
                        'onboarding_step_display': 'Welcome',
                        'next_steps': 'Create User Account',
                        'features_unlocked': [],
                        'is_authenticated': True
                    }
                    
            except Exception as e:
                logger.error(f"Error getting onboarding progress for user {user_id}: {str(e)}")
                # Fallback context for authenticated user
                user_context = {
                    'user_id': user_id,
                    'onboarding_step': 'welcome',
                    'onboarding_step_display': 'Welcome',
                    'next_steps': 'Create User Account',
                    'features_unlocked': [],
                    'is_authenticated': True
                }
        else:
            # User not authenticated
            user_context = {
                'user_id': None,
                'onboarding_step': None,
                'onboarding_step_display': None,
                'next_steps': None,
                'features_unlocked': [],
                'is_authenticated': False
            }
        
        # Track analytics for getting started page access
        try:
            track_analytics_event('getting_started_page_accessed', {
                'source': source,
                'user_authenticated': user_context['is_authenticated'] if user_context else False,
                'onboarding_step': user_context['onboarding_step'] if user_context else None
            })
        except Exception as e:
            logger.error(f"Error tracking getting started analytics: {str(e)}")
        
        # Render template with context
        return render_template('getting_started_resources.html', 
                             user_context=user_context,
                             source=source)
                             
    except Exception as e:
        logger.error(f"Error in getting_started_resources route: {str(e)}")
        # Fallback to basic template without context
        return render_template('getting_started_resources.html', 
                             user_context=None,
                             source=request.args.get('source', 'direct'))


@app.route('/guide')
def guide():
    """Guide page with comprehensive tutorials and advanced features"""
    try:
        # Get source parameter for analytics tracking
        source = request.args.get('source', 'direct')
        
        # Initialize user context
        user_context = None
        
        # Check if user is authenticated
        if current_user.is_authenticated:
            user_id = current_user.id
            
            # Get user's onboarding progress for contextual content
            try:
                from onboarding_manager import get_user_onboarding_progress
                onboarding_progress = get_user_onboarding_progress(user_id)
                
                if onboarding_progress:
                    user_context = {
                        'is_authenticated': True,
                        'user_id': user_id,
                        'onboarding_step': onboarding_progress.get('current_step', 'welcome'),
                        'next_steps': onboarding_progress.get('next_steps', 'Continue exploring advanced features')
                    }
                else:
                    user_context = {
                        'is_authenticated': True,
                        'user_id': user_id,
                        'onboarding_step': 'completed',
                        'next_steps': 'Explore advanced features and tutorials'
                    }
            except Exception as e:
                logger.error(f"Error getting onboarding progress for guide: {str(e)}")
                user_context = {
                    'is_authenticated': True,
                    'user_id': user_id,
                    'onboarding_step': 'completed',
                    'next_steps': 'Explore advanced features and tutorials'
                }
        else:
            user_context = {
                'is_authenticated': False,
                'onboarding_step': 'welcome',
                'next_steps': 'Sign up to access personalized tutorials'
            }
        
        # Track analytics
        try:
            from analytics_tracker import track_page_view
            track_page_view(
                page='guide',
                source=source,
                user_id=user_context.get('user_id') if user_context else None
            )
        except Exception as e:
            logger.error(f"Error tracking guide analytics: {str(e)}")
        
        # Render template with context
        return render_template('guide.html', 
                             user_context=user_context,
                             source=source)
                             
    except Exception as e:
        logger.error(f"Error in guide route: {str(e)}")
        # Fallback to basic template without context
        return render_template('guide.html', 
                             user_context=None,
                             source=request.args.get('source', 'direct'))


@app.route('/faq')
def faq():
    """FAQ page with frequently asked questions"""
    try:
        # Get source parameter for analytics tracking
        source = request.args.get('source', 'direct')
        
        # Initialize user context
        user_context = None
        
        # Check if user is authenticated
        if current_user.is_authenticated:
            user_context = {
                'is_authenticated': True,
                'user_id': current_user.id
            }
        else:
            user_context = {
                'is_authenticated': False
            }
        
        # Track analytics
        try:
            from analytics_tracker import track_page_view
            track_page_view(
                page='faq',
                source=source,
                user_id=user_context.get('user_id') if user_context else None
            )
        except Exception as e:
            logger.error(f"Error tracking FAQ analytics: {str(e)}")
        
        # Render template with context
        return render_template('faq.html', 
                             user_context=user_context,
                             source=source)
                             
    except Exception as e:
        logger.error(f"Error in FAQ route: {str(e)}")
        # Fallback to basic template without context
        return render_template('faq.html', 
                             user_context=None,
                             source=request.args.get('source', 'direct'))


@app.route('/tutorials')
def tutorials():
    """Tutorials hub page with comprehensive learning resources"""
    try:
        # Get source parameter for analytics tracking
        source = request.args.get('source', 'direct')
        
        # Initialize user context
        user_context = None
        
        # Check if user is authenticated
        if current_user.is_authenticated:
            user_context = {
                'is_authenticated': True,
                'user_id': current_user.id
            }
        else:
            user_context = {
                'is_authenticated': False
            }
        
        # Track analytics
        try:
            from analytics_tracker import track_page_view
            track_page_view(
                page='tutorials',
                source=source,
                user_id=user_context.get('user_id') if user_context else None
            )
        except Exception as e:
            logger.error(f"Error tracking tutorials analytics: {str(e)}")
        
        # Render template with context
        return render_template('tutorials.html', 
                             user_context=user_context,
                             source=source)
                             
    except Exception as e:
        logger.error(f"Error in tutorials route: {str(e)}")
        # Fallback to basic template without context
        return render_template('tutorials.html', 
                             user_context=None,
                             source=request.args.get('source', 'direct'))


@app.route('/api/start-tutorial', methods=['POST'])
@login_required
@csrf_protected
def start_tutorial():
    """API endpoint to start a tutorial for the current user"""
    try:
        data = request.get_json()
        tutorial_id = data.get('tutorial_id')
        
        if not tutorial_id:
            return jsonify({'success': False, 'error': 'Tutorial ID is required'}), 400
        
        user_id = current_user.id
        
        # Import tutorial system
        from onboarding_tutorial_system import start_tutorial
        
        # Start the tutorial
        tutorial_session = start_tutorial(user_id, tutorial_id)
        
        if tutorial_session:
            # Track analytics
            track_analytics_event('tutorial_started', {
                'tutorial_id': tutorial_id,
                'user_id': user_id
            })
            
            return jsonify({
                'success': True,
                'tutorial_id': tutorial_id,
                'session_id': tutorial_session.session_id
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Unable to start tutorial'
            }), 500
            
    except Exception as e:
        logger.error(f"Error starting tutorial: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
@app.route('/api/tutorials/available', methods=['GET'])
@login_required
def get_available_tutorials():
    """API endpoint to get available tutorials for existing users"""
    try:
        user_id = current_user.id
        
        # Import tutorial system with graceful fallback
        try:
            from onboarding_tutorial_system import get_available_tutorials as get_tutorials_func
            from onboarding_tutorial_system import get_recommended_tutorials as get_recommended_func
            
            # Get all available tutorials
            available_tutorials = get_tutorials_func(user_id)
            
            # Get recommended tutorials
            recommended_tutorials = get_recommended_func(user_id, limit=3)
            
            # Organize tutorials by category
            tutorials_by_category = {}
            for tutorial in available_tutorials:
                category = tutorial.get('category', 'general')
                if category not in tutorials_by_category:
                    tutorials_by_category[category] = []
                tutorials_by_category[category].append(tutorial)
            
            return jsonify({
                'success': True,
                'tutorials': available_tutorials,
                'recommended': recommended_tutorials,
                'by_category': tutorials_by_category
            })
            
        except ImportError as import_err:
            # Tutorial system not available - return empty data
            logger.warning(f"Tutorial system not available (import error): {str(import_err)}")
            return jsonify({
                'success': True,
                'tutorials': [],
                'recommended': [],
                'by_category': {},
                'message': 'Tutorial system is currently unavailable'
            })
        
    except Exception as e:
        logger.error(f"Error getting available tutorials: {str(e)}", exc_info=True)
        # Return empty tutorials rather than 500 error for better UX
        return jsonify({
            'success': True,
            'tutorials': [],
            'recommended': [],
            'by_category': {},
            'message': 'Tutorials temporarily unavailable'
        })


@app.route('/api/tutorials/content/<tutorial_id>', methods=['GET'])
@login_required
def get_tutorial_content(tutorial_id):
    """API endpoint to get tutorial content for existing users"""
    try:
        # Import tutorial system
        from onboarding_tutorial_system import get_tutorial_content
        
        # Get tutorial content
        content = get_tutorial_content(tutorial_id)
        
        if content:
            return jsonify({
                'success': True,
                'content': content
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Tutorial not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error getting tutorial content: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


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
    # Use the configured callback domain
    redirect_uri = "https://yourtrainingmonkey.com/oauth-callback"
    client_id = os.environ.get('STRAVA_CLIENT_ID')

    if not client_id:
        # Fallback to existing setup flow if no global client ID
        return redirect('/strava-setup')

    auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope=read,activity:read_all,profile:read_all"
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

@app.route('/api/sync-status')
@login_required
def sync_status():
    """API endpoint to check Strava sync status"""
    try:
        sync_status = {
            'in_progress': session.get('strava_sync_in_progress', False),
            'complete': session.get('strava_sync_complete', False),
            'failed': session.get('strava_sync_failed', False)
        }
        
        return jsonify(sync_status)
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync-strava-data', methods=['POST'])
@login_required
def sync_strava_data_for_user():
    """API endpoint for existing users to sync their Strava data"""
    try:
        user_id = current_user.id
        logger.info(f"Starting Strava sync for existing user {user_id}")
        
        # Check if user has Strava access token
        user_data = db_utils.execute_query(
            "SELECT strava_access_token, strava_athlete_id FROM user_settings WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        if not user_data or not user_data[0].get('strava_access_token'):
            return jsonify({'success': False, 'error': 'No Strava access token found. Please reconnect Strava.'}), 400
        
        # Set sync status in session
        session['strava_sync_in_progress'] = True
        session['strava_sync_complete'] = False
        session['strava_sync_failed'] = False
        
        # Trigger sync in background for 28 days of data
        import threading
        def sync_existing_user_data():
            try:
                # Import the sync function
                from strava_training_load import process_activities_for_date_range
                from stravalib.client import Client
                from datetime import datetime, timedelta
                
                # Calculate date range (28 days back)
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=28)
                
                # Load tokens from database for this specific user
                user_data = db_utils.execute_query(
                    "SELECT strava_access_token, strava_refresh_token, strava_token_expires_at FROM user_settings WHERE id = %s",
                    (user_id,),
                    fetch=True
                )
                
                if not user_data or not user_data[0].get('strava_access_token'):
                    logger.error(f"No Strava tokens found for user {user_id}")
                    return
                
                tokens = user_data[0]
                logger.info(f"Loaded tokens for user {user_id}, expires at: {tokens.get('strava_token_expires_at')}")
                
                # Create Strava client with user's tokens
                client = Client(access_token=tokens['strava_access_token'])
                
                # Test connection
                try:
                    athlete = client.get_athlete()
                    logger.info(f"Connected to Strava as {athlete.firstname} {athlete.lastname} for user {user_id}")
                except Exception as conn_error:
                    logger.error(f"Strava connection failed for user {user_id}: {str(conn_error)}")
                    return
                
                # Process activities for this user
                process_activities_for_date_range(
                    client=client,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    user_id=user_id
                )
                logger.info(f"Strava sync completed for existing user {user_id}")
                
            except Exception as sync_error:
                logger.error(f"Strava sync failed for user {user_id}: {str(sync_error)}")
                # Note: Cannot update session from background thread
        
        # Start sync in background thread
        sync_thread = threading.Thread(target=sync_existing_user_data)
        sync_thread.daemon = True
        sync_thread.start()
        
        return jsonify({
            'success': True, 
            'message': 'Strava sync started. This may take a few minutes.',
            'sync_in_progress': True
        })
        
    except Exception as e:
        logger.error(f"Error starting Strava sync for user {user_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500





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
        end_date = datetime.now().date()
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
                start_time,
                name,
                type,
                sport_type,
                device_name,
                distance_miles,
                elevation_gain_feet,
                total_load_miles,
                trimp,
                duration_minutes
            FROM activities 
            WHERE user_id = %s 
            AND date BETWEEN %s AND %s
            AND activity_id > 0
            ORDER BY date DESC, activity_id DESC
            LIMIT %s OFFSET %s
            """,
            (current_user.id, start_date_str, end_date_str, per_page, offset),
            fetch=True
        )

        # Get total count for pagination - FIXED: Use db_utils prefix
        total_count = db_utils.execute_query(
            """
            SELECT COUNT(*) as count
            FROM activities 
            WHERE user_id = %s 
            AND date BETWEEN %s AND %s
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
            "SELECT 1 FROM activities WHERE activity_id = %s AND user_id = %s",
            (activity_id, current_user.id),
            fetch=True
        )

        if not activity_check:
            return jsonify({
                'success': False,
                'error': 'Activity not found or access denied'
            }), 404

        # FIX: Get activity type AND distance to determine correct elevation factor
        activity_data = db_utils.execute_query(
            "SELECT distance_miles, sport_type, type FROM activities WHERE activity_id = %s AND user_id = %s",
            (activity_id, current_user.id),
            fetch=True
        )

        if not activity_data:
            return jsonify({
                'success': False,
                'error': 'Activity not found'
            }), 404

        current_distance = activity_data[0]['distance_miles'] or 0
        sport_type = activity_data[0]['sport_type'] or activity_data[0]['type'] or 'running'
        
        # FIX: Use sport-specific elevation factor (matching strava_training_load.py logic)
        if sport_type.lower() == 'cycling':
            elevation_factor = 1100.0  # Cycling uses higher factor
        elif sport_type.lower() == 'swimming':
            elevation_factor = 0.0  # Swimming has no elevation
        else:
            elevation_factor = 750.0  # Running/default uses standard factor
        
        logger.info(f"Activity {activity_id} type: {sport_type}, using elevation factor: {elevation_factor}")

        # FIX: Calculate elevation load with CORRECT sport-specific factor
        elevation_load_miles = elevation_feet / elevation_factor if elevation_factor > 0 else 0.0
        total_load_miles = current_distance + elevation_load_miles

        # Update with correct parameters
        db_utils.execute_query(
            """
            UPDATE activities 
            SET 
                elevation_gain_feet = %s,
                elevation_load_miles = %s,
                total_load_miles = %s,
                elevation_factor_used = %s
            WHERE activity_id = %s AND user_id = %s
            """,
            (elevation_feet, elevation_load_miles, total_load_miles, elevation_factor, activity_id, current_user.id)
        )

        logger.info(f"Updated elevation for activity {activity_id} to {elevation_feet}ft by user {current_user.id}")

        # FIX: Return SAME value that was stored (not recalculated with different factor!)
        return jsonify({
            'success': True,
            'message': f'Elevation updated to {elevation_feet:,.0f} feet',
            'updated_values': {
                'elevation_gain_feet': elevation_feet,
                'elevation_load_miles': round(elevation_load_miles, 2),
                'total_load_miles': round(total_load_miles, 2),
                'elevation_factor_used': elevation_factor,
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
@app.route('/api/activities-management/update-rpe', methods=['PUT'])
def update_activity_rpe():
    """Update RPE for strength activities and recalculate load"""
    try:
        data = request.get_json()
        activity_id = data.get('activity_id')
        rpe_score = data.get('rpe_score')
        
        # Validation
        if not activity_id or rpe_score is None:
            return jsonify({
                'success': False,
                'error': 'Missing activity_id or rpe_score'
            }), 400
        
        # Validate RPE range (1-10)
        try:
            rpe_score = int(rpe_score)
            if not (1 <= rpe_score <= 10):
                return jsonify({
                    'success': False,
                    'error': 'RPE must be between 1 and 10'
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'error': 'Invalid RPE value'
            }), 400
        
        # Check if activity belongs to current user and is a strength activity
        activity = db_utils.execute_query(
            "SELECT duration_minutes, sport_type FROM activities WHERE activity_id = %s AND user_id = %s",
            (activity_id, current_user.id),
            fetch=True
        )
        
        if not activity or not activity[0]:
            return jsonify({
                'success': False,
                'error': 'Activity not found or access denied'
            }), 404
        
        activity_data = dict(activity[0])
        
        if activity_data.get('sport_type') != 'strength':
            return jsonify({
                'success': False,
                'error': 'RPE can only be set for strength activities'
            }), 400
        
        duration = activity_data['duration_minutes'] or 0
        
        if duration <= 0:
            return jsonify({
                'success': False,
                'error': 'Activity has no duration data'
            }), 400
        
        # Recalculate load using formula: (Duration / 60) × RPE × 0.30
        from strava_training_load import calculate_strength_external_load
        running_equiv, _, total_load = calculate_strength_external_load(duration, rpe_score)
        
        # Update database with new RPE and recalculated loads
        db_utils.execute_query(
            """UPDATE activities 
               SET strength_rpe = %s, 
                   strength_equivalent_miles = %s, 
                   total_load_miles = %s,
                   distance_miles = %s
               WHERE activity_id = %s AND user_id = %s""",
            (rpe_score, running_equiv, total_load, running_equiv, activity_id, current_user.id)
        )
        
        logger.info(f"Updated RPE for activity {activity_id}: RPE={rpe_score}, load={total_load:.2f} miles")
        
        return jsonify({
            'success': True,
            'updated_values': {
                'strength_rpe': rpe_score,
                'total_load_miles': round(total_load, 2),
                'strength_equivalent_miles': round(running_equiv, 2)
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating RPE: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update RPE'
        }), 500


@login_required
@app.route('/api/journal', methods=['GET'])
def get_journal_entries():
    """Get journal entries with corrected recommendation lookup."""
    try:
        logger.info(f"Fetching journal entries for user {current_user.id}")

        # Get date parameter or use current date (user timezone)
        from timezone_utils import get_user_current_date
        date_param = request.args.get('date')
        if date_param:
            center_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        else:
            center_date = get_user_current_date(current_user.id)

        # Calculate date range (today + 6 preceding days + tomorrow)
        # Include tomorrow to show next workout recommendation
        start_date = center_date - timedelta(days=6)
        end_date = center_date + timedelta(days=1)  # Include tomorrow

        observations_data = db_utils.execute_query(
            """
            SELECT date, energy_level, rpe_score, pain_percentage, notes
            FROM journal_entries 
            WHERE user_id = %s AND date >= %s AND date <= %s
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
            WHERE user_id = %s AND date >= %s AND date <= %s
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

        # Generate 8-day journal structure (6 past days + today + tomorrow)
        journal_entries = []
        current_date = start_date
        user_current_date = get_user_current_date(current_user.id)

        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            is_today = current_date == user_current_date
            is_future = current_date > user_current_date
            is_tomorrow = current_date == (user_current_date + timedelta(days=1))

            # FIXED: Use unified function that matches Dashboard logic
            todays_decision = get_unified_recommendation_for_date(current_date, current_user.id)

            # Get activity summary for this date (won't exist for future dates)
            activity_summary = get_activity_summary_for_date(current_date, current_user.id) if not is_future else None

            # Build observations from lookup (won't exist for future dates)
            obs_data = obs_by_date.get(date_str, {})
            observations = {
                'energy_level': obs_data.get('energy_level'),
                'rpe_score': obs_data.get('rpe_score'),
                'pain_percentage': obs_data.get('pain_percentage'),
                'notes': obs_data.get('notes', '')
            }

            # Build autopsy from lookup (won't exist for future dates)
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
                'is_future': is_future,
                'is_tomorrow': is_tomorrow,
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

        from timezone_utils import get_user_timezone
        user_tz = get_user_timezone(current_user.id)
        
        response = {
            'success': True,
            'data': journal_entries,
            'center_date': center_date.strftime('%Y-%m-%d'),
            'date_range': f"{start_date} to {end_date}",
            'user_current_date': user_current_date.strftime('%Y-%m-%d'),
            'timezone_info': str(user_tz)
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
    CRITICAL FIX: Query by target_date to prevent timezone-based date attribution errors.
    
    The Journal page must ALWAYS query by target_date, not by "latest" recommendation,
    to avoid showing Friday's recommendation on Thursday's journal entry when it's
    Thursday night in the user's timezone but the system has already generated 
    Friday's recommendation.
    """
    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        from timezone_utils import get_user_current_date
        user_current_date = get_user_current_date(user_id)

        logger.info(f"Getting unified recommendation for user {user_id} on date {date_str} (user timezone)")

        # CRITICAL FIX: Always query by target_date for Journal entries
        # This ensures Thursday's journal entry shows Thursday's recommendation,
        # even if a Friday recommendation has already been generated
        logger.info(f"Searching for target_date recommendation: user={user_id}, date={date_str}")

        recommendation = db_utils.execute_query(
            """
            SELECT daily_recommendation
            FROM llm_recommendations 
            WHERE user_id = %s AND target_date = %s
            ORDER BY id DESC 
            LIMIT 1
            """,
            (user_id, date_str),
            fetch=True
        )

        if recommendation and recommendation[0]:
            recommendation_text = dict(recommendation[0])['daily_recommendation']
            logger.info(
                f"FOUND recommendation for user {user_id} on {date_str}: {len(recommendation_text)} characters")

            # Determine appropriate label based on whether it's today, past, or future
            if date_obj == user_current_date:
                date_label = f"TODAY'S WORKOUT ({date_obj.strftime('%A, %B %d')})"
            elif date_obj < user_current_date:
                date_label = f"WORKOUT for {date_obj.strftime('%A, %B %d')}"
            else:
                # FUTURE date: Frontend adds its own header, so just return the decision text
                return recommendation_text

            return f"🤖 AI Training Decision for {date_label}:\n\n{recommendation_text}"
        
        else:
            # No recommendation found for this target_date
            logger.warning(f"NO recommendation found for user {user_id} on {date_str}")

            # Check what recommendations exist for debugging
            available_recommendations = db_utils.execute_query(
                "SELECT id, target_date, generation_date FROM llm_recommendations WHERE user_id = %s ORDER BY id DESC LIMIT 5",
                (user_id,),
                fetch=True
            )

            if available_recommendations:
                logger.info(f"Available recommendations for user {user_id}: {[dict(row) for row in available_recommendations]}")
            else:
                logger.warning(f"NO recommendations exist for user {user_id}")

            # Determine appropriate label for "no recommendation" message
            if date_obj == user_current_date:
                date_label = f"TODAY'S WORKOUT ({date_obj.strftime('%A, %B %d')})"
            elif date_obj < user_current_date:
                date_label = f"WORKOUT for {date_obj.strftime('%A, %B %d')}"
            else:
                # FUTURE date: Frontend adds its own header
                return "No recommendation available for this date. Generate fresh recommendations on the Dashboard tab."

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
            WHERE user_id = %s 
            AND target_date = %s
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


def classify_workout_by_hr_zones(activity_list):
    """
    Classify workout based on time spent in HR zones rather than TRIMP.
    This provides more accurate categorization that aligns with HR zone training.
    Falls back to TRIMP-based classification when HR zone data is not available.
    """
    if not activity_list:
        return 'Unknown'
    
    # Aggregate HR zone times across all activities for the day
    total_zone_times = [0, 0, 0, 0, 0]  # Zone 1-5 in seconds
    
    for activity in activity_list:
        total_zone_times[0] += activity.get('time_in_zone1', 0)
        total_zone_times[1] += activity.get('time_in_zone2', 0)
        total_zone_times[2] += activity.get('time_in_zone3', 0)
        total_zone_times[3] += activity.get('time_in_zone4', 0)
        total_zone_times[4] += activity.get('time_in_zone5', 0)
    
    # Calculate total time and percentages
    total_time = sum(total_zone_times)
    if total_time == 0:
        return 'Unknown'  # No HR data available
    
    zone_percentages = [time / total_time * 100 for time in total_zone_times]
    
    # Classification logic based on HR zone distribution
    # Zone 1: Recovery (0-60% HRR)
    # Zone 2: Aerobic Base (60-70% HRR) 
    # Zone 3: Aerobic (70-80% HRR)
    # Zone 4: Threshold (80-90% HRR)
    # Zone 5: VO2 Max (90-100% HRR)
    
    # Determine primary training zone
    primary_zone = zone_percentages.index(max(zone_percentages)) + 1
    
    # Classification based on zone distribution
    if zone_percentages[0] > 50:  # Zone 1 dominant
        return 'Easy/Recovery'
    elif zone_percentages[1] > 50:  # Zone 2 dominant
        return 'Moderate'
    elif zone_percentages[2] > 50:  # Zone 3 dominant
        return 'Moderate'
    elif zone_percentages[3] > 30:  # Zone 4 significant
        return 'Tempo/Threshold'
    elif zone_percentages[4] > 20:  # Zone 5 significant
        return 'Intervals/Hard'
    elif zone_percentages[1] + zone_percentages[2] > 70:  # Zones 2+3 dominant
        return 'Moderate'
    elif zone_percentages[3] + zone_percentages[4] > 40:  # Zones 4+5 significant
        return 'Tempo/Threshold'
    else:
        # Mixed zones - classify by primary zone
        if primary_zone <= 2:
            return 'Easy/Recovery'
        elif primary_zone == 3:
            return 'Moderate'
        elif primary_zone == 4:
            return 'Tempo/Threshold'
        else:
            return 'Intervals/Hard'


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
                max_heart_rate,
                time_in_zone1,
                time_in_zone2,
                time_in_zone3,
                time_in_zone4,
                time_in_zone5
            FROM activities 
            WHERE user_id = %s AND date = %s AND activity_id > 0
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

        # Classify workout based on HR zones (more accurate than TRIMP)
        workout_classification = classify_workout_by_hr_zones(activity_list)

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


def get_last_activity_journal_status(user_id):
    """
    Check if last activity has journal entry.
    Single check that handles: bootstrap, rest days, missed journals, normal flow.
    
    Returns dict with:
        - has_activity: bool
        - activity_date: str (YYYY-MM-DD) or None
        - has_journal: bool
        - allow_manual_generation: bool
        - reason: str (for UI messaging)
    """
    try:
        # Get most recent activity with actual Strava sync (activity_id > 0)
        last_activity = db_utils.execute_query(
            """
            SELECT date, activity_id 
            FROM activities 
            WHERE user_id = %s AND activity_id > 0
            ORDER BY date DESC 
            LIMIT 1
            """,
            (user_id,),
            fetch=True
        )
        
        if not last_activity or not last_activity[0]:
            # No activity = permissive (new user, rest period, etc.)
            return {
                'has_activity': False,
                'activity_date': None,
                'has_journal': False,
                'allow_manual_generation': True,
                'reason': 'no_recent_activity'
            }
        
        activity_date = dict(last_activity[0])['date']
        
        # Handle date format conversion if needed
        if hasattr(activity_date, 'strftime'):
            activity_date_str = activity_date.strftime('%Y-%m-%d')
        else:
            activity_date_str = str(activity_date)
        
        # Check if journal entry exists with actual content
        journal_entry = db_utils.execute_query(
            """
            SELECT date FROM journal_entries 
            WHERE user_id = %s AND date = %s
            AND (
                energy_level IS NOT NULL 
                OR rpe_score IS NOT NULL 
                OR pain_percentage IS NOT NULL
                OR (notes IS NOT NULL AND notes != '')
            )
            """,
            (user_id, activity_date_str),
            fetch=True
        )
        
        has_journal = bool(journal_entry and journal_entry[0])
        
        return {
            'has_activity': True,
            'activity_date': activity_date_str,
            'has_journal': has_journal,
            'allow_manual_generation': not has_journal,  # If no journal, allow manual
            'reason': 'journal_complete' if has_journal else 'journal_missing'
        }
        
    except Exception as e:
        logger.error(f"Error checking last activity journal status for user {user_id}: {str(e)}")
        # On error, be permissive
        return {
            'has_activity': False,
            'activity_date': None,
            'has_journal': False,
            'allow_manual_generation': True,
            'reason': 'error'
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
            WHERE user_id = %s 
            AND target_date = %s
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (user_id, date_str),
            fetch=True
        )

        from timezone_utils import get_user_current_date
        user_current_date = get_user_current_date(user_id)

        # Determine appropriate label
        if date_obj == user_current_date:
            date_label = f"TODAY'S WORKOUT ({date_obj.strftime('%A, %B %d')})"
        elif date_obj < user_current_date:
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
                WHERE user_id = %s
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
            # Note: Frontend adds its own header, so just return the decision text
            decision = get_autopsy_informed_decision_for_future(user_id, date_obj)

        if decision and decision.strip():
            # For future dates (tomorrow), don't add date label - frontend handles this
            if date_obj > app_current_date:
                return decision
            else:
                # For today/past, include the date label
                return f"🤖 {date_label}:\n\n{decision}"
        else:
            return f"No recommendation available for this date."

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


        from timezone_utils import get_user_current_date
        user_current_date = get_user_current_date(user_id)
        completed_date_obj = datetime.strptime(completed_date, '%Y-%m-%d').date()

        logger.info(f"Triggering autopsy workflow for user {user_id}, completed date {completed_date}")

        # STEP 1: Generate autopsy for the completed workout
        if completed_date_obj <= user_current_date:
            logger.info(f"Generating autopsy for completed workout: {completed_date}")

            # Generate enhanced autopsy
            autopsy_result = generate_autopsy_for_date(completed_date, user_id)

            if autopsy_result:
                logger.info(f"✅ Autopsy generated for {completed_date}")

                # STEP 2: Update tomorrow's recommendation with autopsy learning
                tomorrow = user_current_date + timedelta(days=1)
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
    This is for TODAY'S workout, informed by yesterday's autopsy.
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
            WHERE user_id = %s AND target_date = %s
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
            WHERE user_id = %s AND valid_until = %s
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
            WHERE user_id = %s 
            AND generation_date >= %s
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
            WHERE user_id = %s AND generation_date = %s
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
            WHERE user_id = %s 
            AND generation_date <= %s
            AND valid_until >= %s
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

        # Database save logic - PostgreSQL only
        query = """
            INSERT INTO journal_entries (user_id, date, energy_level, rpe_score, pain_percentage, notes, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                energy_level = EXCLUDED.energy_level,
                rpe_score = EXCLUDED.rpe_score,
                pain_percentage = EXCLUDED.pain_percentage,
                notes = EXCLUDED.notes,
                updated_at = NOW()
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
        is_rest_day = data.get('is_rest_day', False)  # NEW: Rest day flag

        # NEW: Create rest day activity record if explicitly marked
        if is_rest_day:
            try:
                # Check if rest day activity already exists
                existing_rest_day = db_utils.execute_query(
                    """
                    SELECT activity_id FROM activities 
                    WHERE user_id = %s AND date = %s AND type = 'rest'
                    """,
                    (current_user.id, date_str),
                    fetch=True
                )
                
                if not existing_rest_day or not existing_rest_day[0]:
                    # Generate unique negative activity_id for rest day
                    rest_day_activity_id = -(date_obj.toordinal() * 1000 + current_user.id)
                    
                    # Create rest day activity record so LLM knows today is a rest day
                    rest_day_record = {
                        'activity_id': rest_day_activity_id,
                        'date': date_str,
                        'user_id': current_user.id,
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
                        'notes': 'User-marked rest day'
                    }
                    
                    columns = ', '.join(rest_day_record.keys())
                    placeholders = ', '.join(['%s'] * len(rest_day_record))
                    
                    db_utils.execute_query(
                        f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
                        tuple(rest_day_record.values())
                    )
                    
                    logger.info(f"✅ Created rest day activity record for {date_str}")

                    try:
                        from strava_training_load import update_moving_averages
                        update_moving_averages(date_str, current_user.id)
                        logger.info(f"Updated moving averages after rest day insertion for {date_str}")
                    except Exception as refresh_error:
                        logger.warning(f"Failed to refresh moving averages after rest day insertion: {refresh_error}")
                else:
                     logger.info(f"Rest day activity already exists for {date_str}")
                     
            except Exception as rest_error:
                logger.warning(f"Failed to create rest day activity: {rest_error}")
                # Continue anyway - journal entry is more important

        # ========================================================================
        # SIMPLIFIED WORKFLOW WITH EXPLICIT DATES
        # ========================================================================
        # When saving journal for date X:
        #   - If rest day: Generate recommendation for X+1
        #   - If workout: Generate autopsy for X, then recommendation for X+1
        # ========================================================================
        
        autopsy_generated = False
        recommendation_generated = False
        autopsy_error = None
        recommendation_error = None
        
        # Calculate tomorrow's date explicitly (no timezone magic)
        tomorrow_date = date_obj + timedelta(days=1)
        tomorrow_date_str = tomorrow_date.strftime('%Y-%m-%d')
        
        logger.info(f"📝 Journal saved for {date_str}, will process tomorrow = {tomorrow_date_str}")
        
        if is_rest_day:
            # ===== REST DAY PATH =====
            logger.info(f"🛌 Rest day for {date_str} - generating recommendation for {tomorrow_date_str}")
            try:
                from llm_recommendations_module import generate_autopsy_informed_daily_decision
                recommendation_text = generate_autopsy_informed_daily_decision(
                    user_id=current_user.id,
                    target_date=tomorrow_date
                )
                
                if recommendation_text:
                    # Save recommendation to database with explicit target_date
                    from unified_metrics_service import UnifiedMetricsService
                    current_metrics = UnifiedMetricsService.get_latest_complete_metrics(current_user.id) or {}
                    
                    from llm_recommendations_module import save_llm_recommendation, fix_dates_for_json
                    recommendation_data = {
                        'generation_date': date_str,
                        'target_date': tomorrow_date_str,
                        'valid_until': None,
                        'data_start_date': date_str,
                        'data_end_date': date_str,
                        'metrics_snapshot': current_metrics,
                        'daily_recommendation': recommendation_text,
                        'weekly_recommendation': 'See previous weekly guidance',
                        'pattern_insights': f'Generated after rest day on {date_str}',
                        'raw_response': recommendation_text,
                        'user_id': current_user.id,
                        'is_autopsy_informed': False,
                        'autopsy_count': 0,
                        'avg_alignment_score': None
                    }
                    recommendation_data = fix_dates_for_json(recommendation_data)
                    save_llm_recommendation(recommendation_data)
                    
                    recommendation_generated = True
                    logger.info(f"✅ Generated recommendation for {tomorrow_date_str} after rest day")
                else:
                    logger.warning(f"❌ Failed to generate recommendation for {tomorrow_date_str}")
                    
            except Exception as e:
                recommendation_error = str(e)
                logger.error(f"❌ Error generating recommendation after rest day: {e}", exc_info=True)
        
        else:
            # ===== WORKOUT PATH =====
            logger.info(f"🏃 Workout day for {date_str} - will generate autopsy + recommendation")
            
            # STEP 1: Generate autopsy for THIS date
            autopsy_analysis = None
            alignment_score = None
            try:
                logger.info(f"🔍 Step 1: Generating autopsy for {date_str}")
                generate_autopsy_for_date(date_str, current_user.id)
                autopsy_generated = True
                logger.info(f"✅ Autopsy generated for {date_str}")
                
                # Get the JUST-generated autopsy for use in recommendation
                autopsy_info = db_utils.execute_query(
                    "SELECT autopsy_analysis, alignment_score FROM ai_autopsies WHERE user_id = %s AND date = %s ORDER BY generated_at DESC LIMIT 1",
                    (current_user.id, date_str),
                    fetch=True
                )
                if autopsy_info and autopsy_info[0]:
                    autopsy_analysis = autopsy_info[0]['autopsy_analysis'] if hasattr(autopsy_info[0], 'keys') else autopsy_info[0][0]
                    alignment_score = autopsy_info[0]['alignment_score'] if hasattr(autopsy_info[0], 'keys') else autopsy_info[0][1]
                    logger.info(f"📋 Retrieved autopsy for {date_str}: alignment={alignment_score}/10")
                
            except Exception as e:
                autopsy_error = str(e)
                logger.error(f"❌ Autopsy generation failed for {date_str}: {e}", exc_info=True)
            
            # STEP 2: Generate/update recommendation for TOMORROW using THIS autopsy
            try:
                logger.info(f"🤖 Step 2: Generating recommendation for {tomorrow_date_str} using autopsy from {date_str}")
                
                # Create autopsy insights dict with the JUST-generated autopsy
                if autopsy_analysis and alignment_score:
                    logger.info(f"✅ Using fresh autopsy from {date_str} (alignment: {alignment_score}/10)")
                    autopsy_insights = {
                        'count': 1,
                        'avg_alignment': alignment_score,
                        'latest_insights': autopsy_analysis[:300],  # First 300 chars for context
                        'alignment_trend': [alignment_score]
                    }
                else:
                    logger.warning(f"⚠️ No autopsy available for {date_str}, using recent autopsy data")
                    from llm_recommendations_module import get_recent_autopsy_insights
                    autopsy_insights = get_recent_autopsy_insights(current_user.id, days=3)
                
                # Generate recommendation with explicit autopsy insights
                from llm_recommendations_module import create_autopsy_informed_decision_prompt, call_anthropic_api, get_current_metrics
                current_metrics = get_current_metrics(current_user.id)
                
                if not current_metrics:
                    logger.error(f"❌ No current metrics for user {current_user.id}")
                    recommendation_text = None
                else:
                    prompt = create_autopsy_informed_decision_prompt(
                        current_user.id,
                        tomorrow_date_str,
                        current_metrics,
                        autopsy_insights
                    )
                    recommendation_text = call_anthropic_api(prompt)
                
                if recommendation_text:
                    recommendation_text = recommendation_text.strip()
                    
                    # Check if recommendation already exists for tomorrow
                    existing_rec = db_utils.execute_query(
                        "SELECT id FROM llm_recommendations WHERE user_id = %s AND target_date = %s",
                        (current_user.id, tomorrow_date_str),
                        fetch=True
                    )
                    
                    if existing_rec:
                        # UPDATE existing recommendation
                        logger.info(f"📝 Updating existing recommendation for {tomorrow_date_str}")
                        db_utils.execute_query(
                            """
                            UPDATE llm_recommendations
                            SET daily_recommendation = %s,
                                pattern_insights = %s,
                                raw_response = %s,
                                generated_at = NOW(),
                                is_autopsy_informed = TRUE,
                                autopsy_count = 1,
                                avg_alignment_score = %s
                            WHERE user_id = %s AND target_date = %s
                            """,
                            (
                                recommendation_text,
                                f"Updated with autopsy from {date_str} (alignment: {alignment_score}/10)" if alignment_score else f"Updated with autopsy from {date_str}",
                                recommendation_text,
                                alignment_score,
                                current_user.id,
                                tomorrow_date_str
                            )
                        )
                    else:
                        # INSERT new recommendation
                        logger.info(f"📝 Creating new recommendation for {tomorrow_date_str}")
                        from unified_metrics_service import UnifiedMetricsService
                        current_metrics_for_save = UnifiedMetricsService.get_latest_complete_metrics(current_user.id) or {}
                        
                        from llm_recommendations_module import save_llm_recommendation, fix_dates_for_json
                        recommendation_data = {
                            'generation_date': date_str,
                            'target_date': tomorrow_date_str,
                            'valid_until': None,
                            'data_start_date': date_str,
                            'data_end_date': date_str,
                            'metrics_snapshot': current_metrics_for_save,
                            'daily_recommendation': recommendation_text,
                            'weekly_recommendation': 'See previous weekly guidance',
                            'pattern_insights': f"Generated with autopsy from {date_str} (alignment: {alignment_score}/10)" if alignment_score else f"Generated with autopsy from {date_str}",
                            'raw_response': recommendation_text,
                            'user_id': current_user.id,
                            'is_autopsy_informed': True,
                            'autopsy_count': 1,
                            'avg_alignment_score': alignment_score
                        }
                        recommendation_data = fix_dates_for_json(recommendation_data)
                        save_llm_recommendation(recommendation_data)
                    
                    recommendation_generated = True
                    logger.info(f"✅ Recommendation for {tomorrow_date_str} is autopsy-informed")
                else:
                    logger.warning(f"❌ Failed to generate recommendation for {tomorrow_date_str}")
                    
            except Exception as e:
                recommendation_error = str(e)
                logger.error(f"❌ Error generating recommendation for {tomorrow_date_str}: {e}", exc_info=True)

        # ENHANCED USER RESPONSE - This is the main addition
        response_data = {
            'success': True,
            'message': 'Journal entry saved successfully',
            'date': date_str
        }

        # Add helpful user messaging based on what happened
        if is_rest_day and recommendation_generated:
            response_data['user_message'] = (
                "🛌 Rest day marked! Tomorrow's workout recommendation generated based on your current metrics."
            )
            response_data['is_rest_day'] = True
            response_data['recommendation_generated'] = True
        elif autopsy_generated and recommendation_generated:
            response_data['user_message'] = (
                "✅ Observations saved! AI autopsy generated and tomorrow's recommendation updated with latest insights."
            )
            response_data['autopsy_generated'] = True
            response_data['recommendation_generated'] = True
        elif is_rest_day:
            response_data['user_message'] = (
                f"🛌 Rest day marked! {'Note: Recommendation generation encountered an issue.' if recommendation_error else ''}"
            )
            response_data['is_rest_day'] = True
            response_data['recommendation_generated'] = False
        elif autopsy_generated:
            response_data['user_message'] = (
                "✅ Observations saved! AI autopsy generated. "
                f"{'Note: Recommendation update encountered an issue.' if recommendation_error else ''}"
            )
            response_data['autopsy_generated'] = True
            response_data['recommendation_generated'] = False
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
            "SELECT * FROM journal_entries WHERE user_id = %s AND date = %s",
            (user_id, date_str),
            fetch=True
        )

        observations = dict(journal_entry[0]) if journal_entry else {}

        # Format activity summary text
        actual_activities = f"{activity_summary['type'].title()} workout: {activity_summary['distance']} miles, {activity_summary['elevation']} ft elevation, TRIMP: {activity_summary['total_trimp']} ({activity_summary['workout_classification']} intensity)"

        # Import and use the enhanced autopsy generation
        from llm_recommendations_module import generate_activity_autopsy_enhanced

        autopsy_result = generate_activity_autopsy_enhanced(
            user_id=user_id,
            date_str=date_str,
            prescribed_action=prescribed_action,
            actual_activities=actual_activities,
            observations=observations
        )

        # Extract analysis and alignment score from enhanced result
        if isinstance(autopsy_result, dict):
            autopsy_analysis = autopsy_result.get('analysis', '')
            alignment_score = autopsy_result.get('alignment_score', 5)
        else:
            # Fallback for old format
            autopsy_analysis = autopsy_result if autopsy_result else ''
            alignment_score = extract_alignment_score(autopsy_analysis)

        # Use PostgreSQL syntax
        query = """
            INSERT INTO ai_autopsies (user_id, date, prescribed_action, actual_activities, autopsy_analysis, alignment_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, date)
            DO UPDATE SET
                prescribed_action = EXCLUDED.prescribed_action,
                actual_activities = EXCLUDED.actual_activities,
                autopsy_analysis = EXCLUDED.autopsy_analysis,
                alignment_score = EXCLUDED.alignment_score,
                generated_at = NOW()
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
            "SELECT energy_level, rpe_score, pain_percentage, notes FROM journal_entries WHERE user_id = %s AND date = %s",
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
            from timezone_utils import get_user_current_date
            target_date = (get_user_current_date(user_id) + timedelta(days=1)).strftime('%Y-%m-%d')

        # CRITICAL FIX: Check if recommendation already exists for this target_date
        existing_recommendation = db_utils.execute_query(
            """
            SELECT id FROM llm_recommendations 
            WHERE user_id = %s AND target_date = %s
            """,
            (user_id, target_date),
            fetch=True
        )

        if existing_recommendation:
            logger.info(f"Recommendation already exists for target_date {target_date}, skipping daily generation to preserve historical record")
            return db_utils.get_latest_recommendation(user_id)

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
    Runs daily at 11 AM UTC to prepare next day's recommendations.
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
            WHERE date >= %s
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


@app.route('/cron/token-refresh', methods=['POST'])
def token_refresh_cron():
    """
    Proactive token refresh for all users.
    This endpoint is called by Cloud Scheduler daily at 10 AM UTC.
    """
    try:
        # Verify this is coming from Cloud Scheduler
        if not request.headers.get('X-Cloudscheduler'):
            logger.warning("Unauthorized token refresh request")
            return jsonify({'error': 'Unauthorized'}), 401
        
        logger.info("=== STARTING PROACTIVE TOKEN REFRESH CRON JOB ===")
        
        from enhanced_token_management import proactive_token_refresh_for_all_users
        
        # Run proactive token refresh for all users
        result = proactive_token_refresh_for_all_users()
        
        logger.info(f"Token refresh cron completed: {result}")
        
        return jsonify({
            'success': True,
            'message': 'Proactive token refresh completed',
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error in token refresh cron: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
            WHERE date >= %s AND user_id IS NOT NULL
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


@app.route('/cron/weekly-program', methods=['POST'])
def weekly_program_cron():
    """
    Generate divergence-optimized weekly training programs for Coach page.
    
    Two schedules:
    - Sunday 6 PM UTC: Generate full 7-day program for upcoming week
    - Wednesday 6 PM UTC: Regenerate remaining 4 days (adjust based on Mon-Wed performance)
    
    Runs for active users only (activity in last 14 days).
    """
    try:
        # Verify this is coming from Cloud Scheduler
        if not request.headers.get('X-Cloudscheduler'):
            logger.warning("Unauthorized weekly program generation request")
            return jsonify({'error': 'Unauthorized'}), 401

        logger.info("=== STARTING WEEKLY PROGRAM GENERATION CRON ===")
        
        # Determine generation mode: 'full' (Sunday) or 'adjustment' (Wednesday)
        # Allow override via query parameter for testing, otherwise auto-detect from day of week
        mode = request.args.get('mode')
        
        if not mode:
            # Auto-detect based on day of week (0=Monday, 6=Sunday)
            day_of_week = datetime.now().weekday()
            if day_of_week == 6:  # Sunday
                mode = 'full'
            elif day_of_week == 2:  # Wednesday
                mode = 'adjustment'
            else:
                logger.warning(f"Weekly program cron running on unexpected day: {day_of_week}")
                mode = 'full'  # Default to full generation
        
        logger.info(f"Running in '{mode}' mode")
        
        # Get active users (users with activity in last 14 days)
        cutoff_date = (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')
        active_users = execute_query(
            """
            SELECT DISTINCT user_id,
                   (SELECT email FROM user_settings WHERE id = user_id) as email
            FROM activities 
            WHERE date >= %s AND user_id IS NOT NULL
            """,
            (cutoff_date,),
            fetch=True
        )

        if not active_users:
            logger.info("No active users found for weekly program generation")
            return jsonify({
                'message': 'No active users',
                'mode': mode,
                'processed': 0
            }), 200

        logger.info(f"Found {len(active_users)} active users")

        # Import the generation function
        from coach_recommendations import generate_weekly_program
        
        success_count = 0
        error_count = 0
        skipped_count = 0

        for user_row in active_users:
            user_dict = dict(user_row)
            user_id = user_dict['user_id']
            email = user_dict.get('email', 'unknown')

            try:
                logger.info(f"Generating weekly program for user {user_id} ({email})")
                
                # Calculate target week start based on mode
                if mode == 'full':
                    # Sunday generation: target upcoming Monday
                    today = datetime.now().date()
                    days_until_monday = (7 - today.weekday()) % 7
                    if days_until_monday == 0:
                        days_until_monday = 7  # If today is Monday, target next Monday
                    target_week_start = today + timedelta(days=days_until_monday)
                else:
                    # Wednesday adjustment: target current week's Monday
                    today = datetime.now().date()
                    days_since_monday = today.weekday()
                    target_week_start = today - timedelta(days=days_since_monday)
                
                logger.info(f"Target week start: {target_week_start} (mode: {mode})")
                
                # Check if user has race goals configured
                race_goals = execute_query(
                    "SELECT COUNT(*) as count FROM race_goals WHERE user_id = %s",
                    (user_id,),
                    fetch=True
                )
                
                if race_goals and race_goals[0]['count'] == 0:
                    logger.info(f"Skipping user {user_id}: No race goals configured")
                    skipped_count += 1
                    continue
                
                # Generate the weekly program
                # Force regeneration for adjustment mode, allow cache for full mode
                result = generate_weekly_program(
                    user_id=user_id,
                    target_week_start=target_week_start,
                    force_regenerate=(mode == 'adjustment')
                )

                if result:
                    success_count += 1
                    logger.info(f"✓ Generated weekly program for user {user_id}")
                else:
                    error_count += 1
                    logger.warning(f"✗ Failed to generate program for user {user_id}")

                # Delay between users to avoid API rate limits
                time.sleep(2)

            except Exception as user_error:
                error_count += 1
                logger.error(f"Error generating program for user {user_id}: {str(user_error)}", exc_info=True)

        result_summary = {
            'message': 'Weekly program generation completed',
            'mode': mode,
            'total_users': len(active_users),
            'successful': success_count,
            'errors': error_count,
            'skipped': skipped_count,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"=== WEEKLY PROGRAM CRON COMPLETE: {result_summary} ===")
        return jsonify(result_summary), 200

    except Exception as e:
        logger.error(f"Error in weekly program cron: {str(e)}", exc_info=True)
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
            WHERE user_id = %s
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
            logger.info("No real activities found for landing page chart, using demo data")
            
            # Generate realistic demo data for the landing page
            from datetime import datetime, timedelta
            import random
            
            # Create 30 days of demo data
            demo_data = []
            base_date = datetime.now() - timedelta(days=30)
            
            # Realistic training patterns
            training_patterns = [
                # Week 1: Building up
                {'external': 0.8, 'internal': 0.7, 'distance': 5.2, 'elevation': 800, 'type': 'Trail Run'},
                {'external': 0.9, 'internal': 0.8, 'distance': 6.1, 'elevation': 950, 'type': 'Trail Run'},
                {'external': 1.1, 'internal': 1.0, 'distance': 7.5, 'elevation': 1200, 'type': 'Trail Run'},
                {'external': 0.7, 'internal': 0.8, 'distance': 3.2, 'elevation': 400, 'type': 'Easy Run'},
                {'external': 1.2, 'internal': 1.1, 'distance': 8.2, 'elevation': 1400, 'type': 'Trail Run'},
                {'external': 0.6, 'internal': 0.7, 'distance': 2.8, 'elevation': 200, 'type': 'Recovery'},
                {'external': 0.8, 'internal': 0.9, 'distance': 4.1, 'elevation': 600, 'type': 'Easy Run'},
                
                # Week 2: Peak training
                {'external': 1.3, 'internal': 1.2, 'distance': 9.5, 'elevation': 1800, 'type': 'Trail Run'},
                {'external': 1.4, 'internal': 1.3, 'distance': 10.2, 'elevation': 2100, 'type': 'Trail Run'},
                {'external': 0.9, 'internal': 1.0, 'distance': 5.8, 'elevation': 900, 'type': 'Easy Run'},
                {'external': 1.5, 'internal': 1.4, 'distance': 11.1, 'elevation': 2400, 'type': 'Trail Run'},
                {'external': 1.6, 'internal': 1.5, 'distance': 12.3, 'elevation': 2800, 'type': 'Trail Run'},
                {'external': 0.7, 'internal': 0.8, 'distance': 3.5, 'elevation': 500, 'type': 'Recovery'},
                {'external': 1.1, 'internal': 1.2, 'distance': 7.2, 'elevation': 1100, 'type': 'Trail Run'},
                
                # Week 3: Showing divergence (overtraining risk)
                {'external': 1.7, 'internal': 1.6, 'distance': 13.1, 'elevation': 3200, 'type': 'Trail Run'},
                {'external': 1.8, 'internal': 1.7, 'distance': 14.2, 'elevation': 3600, 'type': 'Trail Run'},
                {'external': 1.9, 'internal': 1.8, 'distance': 15.5, 'elevation': 4000, 'type': 'Trail Run'},
                {'external': 0.8, 'internal': 0.9, 'distance': 4.5, 'elevation': 700, 'type': 'Easy Run'},
                {'external': 2.0, 'internal': 1.9, 'distance': 16.8, 'elevation': 4500, 'type': 'Trail Run'},
                {'external': 2.1, 'internal': 2.0, 'distance': 18.1, 'elevation': 5000, 'type': 'Trail Run'},
                {'external': 0.6, 'internal': 0.7, 'distance': 2.9, 'elevation': 300, 'type': 'Recovery'},
                {'external': 1.2, 'internal': 1.3, 'distance': 8.5, 'elevation': 1300, 'type': 'Trail Run'},
                
                # Week 4: Recovery and balance
                {'external': 0.9, 'internal': 1.0, 'distance': 6.2, 'elevation': 900, 'type': 'Trail Run'},
                {'external': 1.0, 'internal': 1.1, 'distance': 7.1, 'elevation': 1100, 'type': 'Trail Run'},
                {'external': 0.8, 'internal': 0.9, 'distance': 5.5, 'elevation': 800, 'type': 'Easy Run'},
                {'external': 1.1, 'internal': 1.0, 'distance': 7.8, 'elevation': 1200, 'type': 'Trail Run'},
                {'external': 0.7, 'internal': 0.8, 'distance': 4.2, 'elevation': 600, 'type': 'Recovery'},
                {'external': 1.0, 'internal': 1.1, 'distance': 6.9, 'elevation': 1000, 'type': 'Trail Run'},
                {'external': 0.9, 'internal': 0.8, 'distance': 5.8, 'elevation': 850, 'type': 'Easy Run'},
            ]
            
            for i, pattern in enumerate(training_patterns):
                date = base_date + timedelta(days=i)
                formatted_date = f"{date.month}/{date.day}"
                
                # Add some realistic variation
                external_variation = random.uniform(-0.1, 0.1)
                internal_variation = random.uniform(-0.1, 0.1)
                
                demo_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'dateFormatted': formatted_date,
                    'acute_chronic_ratio': round(pattern['external'] + external_variation, 2),
                    'trimp_acute_chronic_ratio': round(pattern['internal'] + internal_variation, 2),
                    'distance_miles': round(pattern['distance'] + random.uniform(-0.5, 0.5), 1),
                    'elevation_gain_feet': int(pattern['elevation'] + random.uniform(-100, 100)),
                    'trimp': int(50 + pattern['external'] * 30 + random.uniform(-10, 10)),
                    'type': pattern['type'],
                    'name': f"{pattern['type']} - {pattern['distance']}mi"
                })

            return jsonify({
                'success': True,
                'data': demo_data,
                'dataPoints': len(demo_data),
                'dateRange': {
                    'start': demo_data[0]['date'] if demo_data else None,
                    'end': demo_data[-1]['date'] if demo_data else None
                },
                'isDemo': True
            })

        # Process real data for chart display
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

        logger.info(f"Serving {len(chart_data)} real data points for landing page chart")

        return jsonify({
            'success': True,
            'data': chart_data,
            'dataPoints': len(chart_data),
            'dateRange': {
                'start': chart_data[0]['date'] if chart_data else None,
                'end': chart_data[-1]['date'] if chart_data else None
            },
            'isDemo': False
        })

    except Exception as e:
        logger.error(f"Error fetching landing page chart data: {str(e)}")
        
        # Even if there's an error, return demo data so the chart still works
        logger.info("Returning fallback demo data due to error")
        
        # Simple fallback demo data
        fallback_data = [
            {'dateFormatted': '11/1', 'acute_chronic_ratio': 0.9, 'trimp_acute_chronic_ratio': 0.8, 'distance_miles': 5.2, 'elevation_gain_feet': 800, 'trimp': 75, 'type': 'Trail Run', 'name': 'Morning Trail'},
            {'dateFormatted': '11/5', 'acute_chronic_ratio': 1.1, 'trimp_acute_chronic_ratio': 1.0, 'distance_miles': 7.1, 'elevation_gain_feet': 1200, 'trimp': 85, 'type': 'Trail Run', 'name': 'Hill Training'},
            {'dateFormatted': '11/10', 'acute_chronic_ratio': 1.3, 'trimp_acute_chronic_ratio': 1.2, 'distance_miles': 9.5, 'elevation_gain_feet': 1800, 'trimp': 95, 'type': 'Trail Run', 'name': 'Long Run'},
            {'dateFormatted': '11/15', 'acute_chronic_ratio': 1.0, 'trimp_acute_chronic_ratio': 1.1, 'distance_miles': 6.8, 'elevation_gain_feet': 1100, 'trimp': 80, 'type': 'Trail Run', 'name': 'Recovery Run'},
            {'dateFormatted': '11/20', 'acute_chronic_ratio': 0.8, 'trimp_acute_chronic_ratio': 0.9, 'distance_miles': 4.2, 'elevation_gain_feet': 600, 'trimp': 65, 'type': 'Easy Run', 'name': 'Easy Day'},
            {'dateFormatted': '11/25', 'acute_chronic_ratio': 1.2, 'trimp_acute_chronic_ratio': 1.3, 'distance_miles': 8.5, 'elevation_gain_feet': 1400, 'trimp': 90, 'type': 'Trail Run', 'name': 'Tempo Run'},
            {'dateFormatted': '11/30', 'acute_chronic_ratio': 0.9, 'trimp_acute_chronic_ratio': 0.8, 'distance_miles': 5.5, 'elevation_gain_feet': 850, 'trimp': 70, 'type': 'Trail Run', 'name': 'Easy Trail'}
        ]
        
        return jsonify({
            'success': True,
            'data': fallback_data,
            'dataPoints': len(fallback_data),
            'dateRange': {'start': '2024-11-01', 'end': '2024-11-30'},
            'isDemo': True,
            'error': str(e)
        })

@app.route('/landing-static/<path:filename>')
def serve_landing_static(filename):
    """Serve landing page assets - FIXED VERSION"""
    logger.info(f"Landing static request: {filename}")

    # CRITICAL FIX 1: acwr-chart.html - serve the updated file
    if filename == 'acwr-chart.html':
        logger.info("Serving acwr-chart.html from static file")
        
        try:
            # Try to serve the actual file first
            return send_from_directory('static', 'acwr-chart.html')
        except Exception as e:
            logger.warning(f"Could not serve acwr-chart.html from file: {e}")
            
            # Fallback to serving the file content directly
            try:
                with open('static/acwr-chart.html', 'r', encoding='utf-8') as f:
                    html_content = f.read()
                return Response(html_content, mimetype='text/html')
            except Exception as e2:
                logger.error(f"Could not read acwr-chart.html file: {e2}")
                return "Chart not available", 404

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
            "SELECT * FROM user_settings WHERE id = %s",
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
            'timezone': user.get('timezone', 'US/Pacific'),
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

        # Validate timezone
        if 'timezone' in data:
            from timezone_utils import validate_timezone, clear_timezone_cache
            if not validate_timezone(data['timezone']):
                errors.append('Invalid timezone. Please select a valid US timezone.')
            else:
                # Clear cache when timezone changes to ensure fresh lookups
                clear_timezone_cache(current_user.id)

        if errors:
            return jsonify({'success': False, 'errors': errors}), 400

        # *** CRITICAL FIX: GET OLD SETTINGS BEFORE UPDATE ***
        old_settings = db_utils.execute_query(
            "SELECT * FROM user_settings WHERE id = %s",
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
            if field in ['resting_hr', 'max_hr', 'gender', 'age', 'timezone', 'hr_zones_method', 'primary_sport',
                         'secondary_sport', 'training_experience', 'current_phase', 'race_goal_date',
                         'weekly_training_hours', 'acwr_alert_threshold', 'injury_risk_alerts',
                         'recommendation_style', 'coaching_tone']:
                update_fields.append(f"{field} = %s")
                update_values.append(value)

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        # Add updated_at timestamp
        update_fields.append("updated_at = NOW()")
        update_values.append(current_user.id)

        # Execute update with proper logging
        update_query = f"UPDATE user_settings SET {', '.join(update_fields)} WHERE id = %s"
        logger.info(f"Executing update for user {current_user.id}: {update_query}")
        logger.info(f"Update values: {update_values}")

        db_utils.execute_query(update_query, tuple(update_values))

        # Get updated settings to verify the save
        updated_user = db_utils.execute_query(
            "SELECT * FROM user_settings WHERE id = %s",
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

            # Log specific HR changes
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
                SET %s = %s
                WHERE id = %s
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
            WHERE id = %s
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
            "SELECT resting_hr, max_hr, hr_zones_method, custom_hr_zones FROM user_settings WHERE id = %s",
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


# New Settings API endpoints
@app.route('/api/settings/profile', methods=['POST'])
@login_required
def update_profile_settings():
    """Update profile settings (birthdate, gender, email)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'birthdate', 'gender']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate and parse birthdate
        from datetime import datetime, date
        try:
            birthdate = datetime.strptime(data['birthdate'], '%Y-%m-%d').date()
            
            # Validate birthdate is reasonable (at least 13 years old, not in future)
            today = date.today()
            min_birthdate = date(today.year - 100, today.month, today.day)
            max_birthdate = date(today.year - 13, today.month, today.day)
            
            if birthdate > max_birthdate:
                return jsonify({'error': 'You must be at least 13 years old'}), 400
            if birthdate < min_birthdate:
                return jsonify({'error': 'Invalid birthdate (too far in the past)'}), 400
                
        except ValueError:
            return jsonify({'error': 'Invalid birthdate format. Use YYYY-MM-DD'}), 400
        
        # Validate gender
        if data['gender'] not in ['male', 'female', 'other']:
            return jsonify({'error': 'Invalid gender selection'}), 400
        
        # Calculate age from birthdate for backward compatibility
        from settings_utils import calculate_age_from_birthdate
        age = calculate_age_from_birthdate(birthdate)
        
        # Update user profile with both birthdate and calculated age
        db_utils.execute_query("""
            UPDATE user_settings 
            SET email = %s, birthdate = %s, age = %s, gender = %s, updated_at = NOW()
            WHERE id = %s
        """, (data['email'], birthdate, age, data['gender'], current_user.id))
        
        return jsonify({'success': True, 'message': 'Profile settings updated successfully'})
        
    except Exception as e:
        app.logger.error(f"Error updating profile settings: {str(e)}")
        return jsonify({'error': 'Failed to update profile settings'}), 500

@app.route('/api/settings/training', methods=['POST'])
@login_required
def update_training_settings():
    """Update training settings (goals, experience, frequency, activities)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['primary_sport', 'training_experience']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate primary sport
        valid_sports = ['running', 'cycling', 'swimming', 'triathlon', 'strength', 'other']
        if data['primary_sport'] not in valid_sports:
            return jsonify({'error': 'Invalid primary sport selection'}), 400
        
        # Validate training experience
        valid_levels = ['beginner', 'intermediate', 'advanced', 'elite']
        if data['training_experience'] not in valid_levels:
            return jsonify({'error': 'Invalid experience level selection'}), 400
        
        # Validate secondary sport (optional)
        secondary_sport = data.get('secondary_sport', '')
        if secondary_sport and secondary_sport not in valid_sports:
            return jsonify({'error': 'Invalid secondary sport selection'}), 400
        
        # Validate weekly training hours
        weekly_hours = int(data.get('weekly_training_hours', 8))
        if weekly_hours < 1 or weekly_hours > 40:
            return jsonify({'error': 'Weekly training hours must be between 1 and 40'}), 400
        
        # Validate current phase
        valid_phases = ['base', 'build', 'peak', 'race', 'recovery']
        current_phase = data.get('current_phase', 'base')
        if current_phase not in valid_phases:
            return jsonify({'error': 'Invalid training phase selection'}), 400
        
        # Handle race goal date (optional)
        race_goal_date = data.get('race_goal_date', '')
        if race_goal_date:
            try:
                from datetime import datetime
                race_goal_date = datetime.strptime(race_goal_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format for race goal date'}), 400
        else:
            race_goal_date = None
        
        # Update user training settings
        db_utils.execute_query("""
            UPDATE user_settings 
            SET primary_sport = %s, secondary_sport = %s, training_experience = %s, 
                weekly_training_hours = %s, current_phase = %s, race_goal_date = %s, updated_at = NOW()
            WHERE id = %s
        """, (data['primary_sport'], secondary_sport, data['training_experience'], 
              weekly_hours, current_phase, race_goal_date, current_user.id))
        
        return jsonify({'success': True, 'message': 'Training settings updated successfully'})
        
    except Exception as e:
        app.logger.error(f"Error updating training settings: {str(e)}")
        return jsonify({'error': 'Failed to update training settings'}), 500


@app.route('/api/settings/coaching', methods=['POST'])
@login_required
def update_coaching_settings():
    """Update coaching settings (style, frequency, focus)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['coaching_tone', 'recommendation_style']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate coaching tone
        valid_tones = ['supportive', 'direct', 'technical', 'casual']
        if data['coaching_tone'] not in valid_tones:
            return jsonify({'error': 'Invalid coaching tone selection'}), 400
        
        # Validate recommendation style
        valid_styles = ['balanced', 'conservative', 'aggressive', 'adaptive']
        if data['recommendation_style'] not in valid_styles:
            return jsonify({'error': 'Invalid recommendation style selection'}), 400
        
        # Update user coaching settings
        db_utils.execute_query("""
            UPDATE user_settings 
            SET coaching_tone = %s, recommendation_style = %s, updated_at = NOW()
            WHERE id = %s
        """, (data['coaching_tone'], data['recommendation_style'], current_user.id))
        
        return jsonify({'success': True, 'message': 'Coaching settings updated successfully'})
        
    except Exception as e:
        app.logger.error(f"Error updating coaching settings: {str(e)}")
        return jsonify({'error': 'Failed to update coaching settings'}), 500

@app.route('/api/settings/alerts', methods=['POST'])
@login_required
def update_alert_settings():
    """Update alert settings (overtraining, injury risk, progress, notification methods)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['acwr_alert_threshold', 'injury_risk_alerts']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate ACWR alert threshold
        acwr_threshold = float(data['acwr_alert_threshold'])
        if acwr_threshold < 1.0 or acwr_threshold > 2.0:
            return jsonify({'error': 'ACWR alert threshold must be between 1.0 and 2.0'}), 400
        
        # Validate injury risk alerts (boolean)
        injury_risk_alerts = bool(data['injury_risk_alerts'])
        
        # Update user alert settings
        db_utils.execute_query("""
            UPDATE user_settings 
            SET acwr_alert_threshold = %s, injury_risk_alerts = %s, updated_at = NOW()
            WHERE id = %s
        """, (acwr_threshold, injury_risk_alerts, current_user.id))
        
        return jsonify({'success': True, 'message': 'Alert settings updated successfully'})
        
    except Exception as e:
        app.logger.error(f"Error updating alert settings: {str(e)}")
        return jsonify({'error': 'Failed to update alert settings'}), 500


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
            "SELECT custom_hr_zones FROM user_settings WHERE id = %s",
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
            "SELECT resting_hr, max_hr, hr_zones_method FROM user_settings WHERE id = %s",
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
            "UPDATE user_settings SET custom_hr_zones = %s, updated_at = NOW() WHERE id = %s",
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


# Legal Document Display Routes
@app.route('/legal/terms')
def display_terms():
    """Display Terms and Conditions"""
    try:
        from legal_document_versioning import get_current_legal_versions
        current_versions = get_current_legal_versions()
        return render_template('legal/terms.html', version=current_versions.get('terms', '2.0'))
    except Exception as e:
        logger.error(f"Error displaying terms: {str(e)}")
        return render_template('legal/terms.html', version='2.0')


@app.route('/legal/privacy')
def display_privacy():
    """Display Privacy Policy"""
    try:
        from legal_document_versioning import get_current_legal_versions
        current_versions = get_current_legal_versions()
        return render_template('legal/privacy.html', version=current_versions.get('privacy', '2.0'))
    except Exception as e:
        logger.error(f"Error displaying privacy policy: {str(e)}")
        return render_template('legal/privacy.html', version='2.0')


@app.route('/legal/disclaimer')
def display_disclaimer():
    """Display Medical Disclaimer"""
    try:
        from legal_document_versioning import get_current_legal_versions
        current_versions = get_current_legal_versions()
        return render_template('legal/disclaimer.html', version=current_versions.get('disclaimer', '2.0'))
    except Exception as e:
        logger.error(f"Error displaying disclaimer: {str(e)}")
        return render_template('legal/disclaimer.html', version='2.0')


@app.route('/legal/accept', methods=['POST'])
@login_required
def accept_legal_document():
    """Accept a legal document"""
    try:
        from legal_compliance import log_user_legal_acceptance
        from legal_document_versioning import get_current_legal_versions
        
        data = request.get_json()
        document_type = data.get('document_type')
        
        if document_type not in ['terms', 'privacy', 'disclaimer']:
            return jsonify({'error': 'Invalid document type'}), 400
        
        current_versions = get_current_legal_versions()
        version = current_versions.get(document_type)
        
        if not version:
            return jsonify({'error': 'Could not determine document version'}), 400
        
        success = log_user_legal_acceptance(current_user.id, document_type, version)
        
        if success:
            logger.info(f"User {current_user.id} accepted {document_type} version {version}")
            return jsonify({
                'success': True,
                'message': f'{document_type.title()} accepted successfully',
                'version': version
            })
        else:
            return jsonify({'error': 'Failed to log acceptance'}), 500
            
    except Exception as e:
        logger.error(f"Error accepting legal document: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/legal/status')
@login_required
def get_legal_status():
    """Get user's legal compliance status"""
    try:
        from legal_compliance import get_legal_compliance_tracker
        
        tracker = get_legal_compliance_tracker()
        status = tracker.get_user_legal_status(current_user.id)
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting legal status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/legal/validate')
@login_required
def validate_legal_compliance():
    """Validate user's legal compliance"""
    try:
        from legal_compliance import get_legal_compliance_tracker
        
        tracker = get_legal_compliance_tracker()
        is_compliant, details = tracker.validate_user_compliance(current_user.id)
        
        return jsonify({
            'is_compliant': is_compliant,
            'details': details
        })
        
    except Exception as e:
        logger.error(f"Error validating legal compliance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# User Registration Routes
@app.route('/signup', methods=['GET', 'POST'])
@require_csrf_token(CSRFTokenType.FORM)
def signup():
    """User registration page"""
    try:
        from registration_validation import registration_validator
        from legal_document_versioning import get_current_legal_versions
        from csrf_protection import csrf_protected, CSRFTokenType
        
        if request.method == 'POST':
            # Apply CSRF protection to POST requests
            @csrf_protected(CSRFTokenType.FORM)
            def process_registration():
                # Validate registration data
                is_valid, errors = registration_validator.validate_registration_data(request.form)
                
                if not is_valid:
                    # Return errors for form display
                    current_versions = get_current_legal_versions()
                    csrf_token = registration_validator.generate_csrf_token()
                    
                    return render_template('signup.html', 
                                         errors=errors, 
                                         legal_versions=current_versions,
                                         csrf_token=csrf_token)
                
                # Create user account
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '')
                
                success, user_id, error_message = registration_validator.create_user_account(email, password)
                
                if success:
                    # Start registration status tracking
                    from registration_status_tracker import registration_status_tracker
                    registration_status_tracker.track_account_creation(user_id)
                    
                    # Log successful registration
                    logger.info(f"New user registration successful: {email} (ID: {user_id})")
                    
                    # Flash success message and redirect to login
                    flash('Account created successfully! Please sign in to continue.', 'success')
                    return redirect(url_for('login'))
                else:
                    # Return error
                    current_versions = get_current_legal_versions()
                    csrf_token = registration_validator.generate_csrf_token()
                    
                    return render_template('signup.html', 
                                         errors={'general': [error_message]}, 
                                         legal_versions=current_versions,
                                         csrf_token=csrf_token)
            
            return process_registration()
        
        # GET request - show signup form
        current_versions = get_current_legal_versions()
        csrf_token = registration_validator.generate_csrf_token()
        
        return render_template('signup.html', 
                             legal_versions=current_versions,
                             csrf_token=csrf_token)
        
    except Exception as e:
        logger.error(f"Error in signup route: {str(e)}")
        flash('An error occurred during registration. Please try again.', 'danger')
        return redirect(url_for('signup'))


@app.route('/api/signup/validate', methods=['POST'])
@csrf_protected(CSRFTokenType.API)
def validate_signup_data():
    """API endpoint for real-time signup validation"""
    try:
        from registration_validation import registration_validator
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate specific field
        field_type = data.get('field_type')
        field_value = data.get('field_value', '')
        
        if field_type == 'email':
            is_valid, error_message = registration_validator.validate_email(field_value)
            return jsonify({
                'is_valid': is_valid,
                'error': error_message if not is_valid else ''
            })
        
        elif field_type == 'password':
            is_valid, errors = registration_validator.validate_password(field_value)
            return jsonify({
                'is_valid': is_valid,
                'errors': errors if not is_valid else []
            })
        
        else:
            return jsonify({'error': 'Invalid field type'}), 400
            
    except Exception as e:
        logger.error(f"Error in signup validation API: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/signup/generate-password', methods=['POST'])
@csrf_protected(CSRFTokenType.API)
def generate_password():
    """API endpoint for generating secure passwords"""
    try:
        from password_generator import password_generator
        
        data = request.get_json() or {}
        password_type = data.get('type', 'strong')
        strength = data.get('strength', 'strong')
        length = data.get('length')
        
        if password_type == 'memorable':
            word_count = data.get('word_count', 4)
            separator = data.get('separator', '-')
            password = password_generator.generate_memorable_password(word_count, separator)
        elif password_type == 'pronounceable':
            password = password_generator.generate_pronounceable_password(length or 12)
        else:  # standard
            password = password_generator.generate_password(strength, length)
        
        # Validate the generated password
        validation = password_generator.validate_generated_password(password)
        
        return jsonify({
            'password': password,
            'validation': validation,
            'type': password_type,
            'strength': strength
        })
        
    except Exception as e:
        logger.error(f"Error generating password: {str(e)}")
        return jsonify({'error': 'Failed to generate password'}), 500


@app.route('/api/signup/password-strength-info', methods=['GET'])
def get_password_strength_info():
    """API endpoint for getting password strength information"""
    try:
        from password_generator import password_generator
        
        strength = request.args.get('strength', 'strong')
        
        try:
            info = password_generator.get_password_strength_info(strength)
            return jsonify(info)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
            
    except Exception as e:
        logger.error(f"Error getting password strength info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# User Account Management API Endpoints
@app.route('/api/user/account-status', methods=['GET'])
@login_required
def get_user_account_status():
    """Get current user's account status"""
    try:
        from user_account_manager import user_account_manager
        
        status = user_account_manager.get_user_account_status(current_user.id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting user account status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
@app.route('/api/user/dashboard-config', methods=['GET'])
@login_required
def get_user_dashboard_config():
    """Get user's dashboard ACWR configuration"""
    try:
        user_id = request.args.get('user_id', type=int)
        if not user_id:
            user_id = current_user.id
        
        # Check if user has custom dashboard configuration
        result = db_utils.execute_query("""
            SELECT chronic_period_days, decay_rate, is_active, updated_at
            FROM user_dashboard_configs 
            WHERE user_id = %s AND is_active = TRUE
            ORDER BY updated_at DESC
            LIMIT 1
        """, (user_id,), fetch=True)
        
        if result:
            config = result[0]
            return jsonify({
                'success': True,
                'config': {
                    'chronic_period_days': config['chronic_period_days'],
                    'decay_rate': config['decay_rate'],
                    'is_active': config['is_active'],
                    'updated_at': config['updated_at'].isoformat() if config['updated_at'] else None
                }
            })
        else:
            return jsonify({
                'success': True,
                'config': None  # Using default configuration
            })
            
    except Exception as e:
        logger.error(f"Error getting user dashboard config: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/user/dashboard-config', methods=['POST'])
@login_required
def set_user_dashboard_config():
    """Set user's dashboard ACWR configuration"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        if not user_id:
            user_id = current_user.id
        
        chronic_period_days = data.get('chronic_period_days')
        decay_rate = data.get('decay_rate')
        is_active = data.get('is_active', True)
        
        if not chronic_period_days or not decay_rate:
            return jsonify({'success': False, 'error': 'chronic_period_days and decay_rate are required'}), 400
        
        # Validate parameters
        if not (28 <= chronic_period_days <= 90):
            return jsonify({'success': False, 'error': 'chronic_period_days must be between 28 and 90'}), 400
        
        if not (0.01 <= decay_rate <= 0.20):
            return jsonify({'success': False, 'error': 'decay_rate must be between 0.01 and 0.20'}), 400
        
        # Deactivate any existing configurations for this user
        db_utils.execute_query("""
            UPDATE user_dashboard_configs 
            SET is_active = FALSE, updated_at = NOW()
            WHERE user_id = %s
        """, (user_id,))
        
        # Insert new configuration
        db_utils.execute_query("""
            INSERT INTO user_dashboard_configs (user_id, chronic_period_days, decay_rate, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (user_id, chronic_period_days, decay_rate, is_active))
        
        return jsonify({
            'success': True,
            'message': 'Dashboard configuration updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error setting user dashboard config: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


def recalculate_acwr_with_config(aggregated_data, config, user_id):
    """Recalculate ACWR values using custom configuration"""
    try:
        from datetime import datetime, timedelta
        import math
        
        chronic_period_days = config['chronic_period_days']
        decay_rate = config['decay_rate']
        
        # Get all activities for the user to calculate proper chronic averages
        # We need more data than what's in aggregated_data to calculate chronic properly
        from timezone_utils import get_user_current_date
        end_date = get_user_current_date(user_id)
        start_date = end_date - timedelta(days=chronic_period_days + 30)  # Extra buffer
        
        activities = db_utils.execute_query("""
            SELECT date, total_load_miles, trimp
            FROM activities 
            WHERE user_id = %s 
            AND date >= %s
            ORDER BY date ASC
        """, (user_id, start_date.strftime('%Y-%m-%d')), fetch=True)
        
        if not activities:
            logger.warning(f"No activities found for ACWR recalculation for user {user_id}")
            return aggregated_data
        
        # Create activities lookup by date
        activities_by_date = {}
        for activity in activities:
            date_str = activity['date'].strftime('%Y-%m-%d') if hasattr(activity['date'], 'strftime') else str(activity['date'])
            activities_by_date[date_str] = {
                'total_load_miles': activity['total_load_miles'] or 0,
                'trimp': activity['trimp'] or 0
            }
        
        # Recalculate ACWR for each day in aggregated_data
        for day_data in aggregated_data:
            date_str = day_data['date']
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Calculate acute averages (7 days)
            acute_load_sum = 0
            acute_trimp_sum = 0
            acute_count = 0
            
            for i in range(7):
                acute_date = date_obj - timedelta(days=i)
                acute_date_str = acute_date.strftime('%Y-%m-%d')
                if acute_date_str in activities_by_date:
                    acute_load_sum += activities_by_date[acute_date_str]['total_load_miles']
                    acute_trimp_sum += activities_by_date[acute_date_str]['trimp']
                    acute_count += 1
            
            acute_load_avg = acute_load_sum / 7.0 if acute_count > 0 else 0
            acute_trimp_avg = acute_trimp_sum / 7.0 if acute_count > 0 else 0
            
            # Calculate chronic averages with exponential decay
            chronic_load_sum = 0
            chronic_trimp_sum = 0
            total_weight = 0
            
            for i in range(chronic_period_days):
                chronic_date = date_obj - timedelta(days=i)
                chronic_date_str = chronic_date.strftime('%Y-%m-%d')
                if chronic_date_str in activities_by_date:
                    days_ago = i
                    weight = math.exp(-decay_rate * days_ago)
                    total_weight += weight
                    
                    chronic_load_sum += activities_by_date[chronic_date_str]['total_load_miles'] * weight
                    chronic_trimp_sum += activities_by_date[chronic_date_str]['trimp'] * weight
            
            chronic_load_avg = chronic_load_sum / total_weight if total_weight > 0 else 0
            chronic_trimp_avg = chronic_trimp_sum / total_weight if total_weight > 0 else 0
            
            # Calculate new ACWR values
            new_external_acwr = acute_load_avg / chronic_load_avg if chronic_load_avg > 0 else 0
            new_internal_acwr = acute_trimp_avg / chronic_trimp_avg if chronic_trimp_avg > 0 else 0
            
            # Calculate normalized divergence
            if new_external_acwr > 0 and new_internal_acwr > 0:
                avg_acwr = (new_external_acwr + new_internal_acwr) / 2
                new_normalized_divergence = (new_external_acwr - new_internal_acwr) / avg_acwr if avg_acwr > 0 else 0
            else:
                new_normalized_divergence = 0
            
            # Update the day data with new values
            day_data['acute_chronic_ratio'] = round(new_external_acwr, 3)
            day_data['trimp_acute_chronic_ratio'] = round(new_internal_acwr, 3)
            day_data['normalized_divergence'] = round(new_normalized_divergence, 3)
        
        logger.info(f"Recalculated ACWR for {len(aggregated_data)} days with config: chronic={chronic_period_days}d, decay={decay_rate}")
        return aggregated_data
        
    except Exception as e:
        logger.error(f"Error recalculating ACWR with config: {str(e)}")
        return aggregated_data  # Return original data if recalculation fails


@app.route('/api/user/activate-account', methods=['POST'])
@login_required
def activate_user_account():
    """Activate user account"""
    try:
        from user_account_manager import user_account_manager
        
        success = user_account_manager.activate_user_account(current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': 'Account activated successfully'})
        else:
            return jsonify({'error': 'Failed to activate account'}), 500
            
    except Exception as e:
        logger.error(f"Error activating user account: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user/update-onboarding', methods=['POST'])
@login_required
def update_onboarding_progress():
    """Update user's onboarding progress"""
    try:
        from user_account_manager import user_account_manager
        
        data = request.get_json()
        step = data.get('step')
        
        if not step:
            return jsonify({'error': 'Onboarding step is required'}), 400
        
        success = user_account_manager.update_onboarding_progress(current_user.id, step)
        
        if success:
            return jsonify({'success': True, 'message': 'Onboarding progress updated'})
        else:
            return jsonify({'error': 'Failed to update onboarding progress'}), 500
            
    except Exception as e:
        logger.error(f"Error updating onboarding progress: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/user/complete-onboarding', methods=['POST'])
@login_required
def complete_onboarding():
    """Complete user's onboarding process"""
    try:
        from user_account_manager import user_account_manager
        
        success = user_account_manager.complete_onboarding(current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': 'Onboarding completed successfully'})
        else:
            return jsonify({'error': 'Failed to complete onboarding'}), 500
            
    except Exception as e:
        logger.error(f"Error completing onboarding: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Admin endpoints for user management
@app.route('/api/admin/pending-registrations', methods=['GET'])
@login_required
def get_pending_registrations():
    """Get list of pending registrations (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from user_account_manager import user_account_manager
        
        pending = user_account_manager.get_pending_registrations()
        return jsonify({'pending_registrations': pending})
        
    except Exception as e:
        logger.error(f"Error getting pending registrations: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/cleanup-expired-registrations', methods=['POST'])
@login_required
def cleanup_expired_registrations():
    """Clean up expired registrations (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from user_account_manager import user_account_manager
        
        data = request.get_json() or {}
        days_old = data.get('days_old', 7)
        
        cleaned_count = user_account_manager.cleanup_expired_registrations(days_old)
        
        return jsonify({
            'success': True, 
            'message': f'Cleaned up {cleaned_count} expired registrations',
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up expired registrations: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Registration Status Tracking API Endpoints
@app.route('/api/registration/status', methods=['GET'])
@login_required
def get_registration_status():
    """Get current user's registration status"""
    try:
        from registration_status_tracker import registration_status_tracker
        
        status = registration_status_tracker.get_registration_status(current_user.id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting registration status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/track-email-verification', methods=['POST'])
@login_required
def track_email_verification():
    """Track email verification completion"""
    try:
        from registration_status_tracker import registration_status_tracker
        
        success = registration_status_tracker.track_email_verification_complete(current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': 'Email verification tracked'})
        else:
            return jsonify({'error': 'Failed to track email verification'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking email verification: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/track-strava-connection', methods=['POST'])
@login_required
def track_strava_connection():
    """Track Strava connection"""
    try:
        from registration_status_tracker import registration_status_tracker
        
        data = request.get_json() or {}
        strava_user_id = data.get('strava_user_id')
        
        success = registration_status_tracker.track_strava_connection(current_user.id, strava_user_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Strava connection tracked'})
        else:
            return jsonify({'error': 'Failed to track Strava connection'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking Strava connection: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/track-onboarding-start', methods=['POST'])
@login_required
def track_onboarding_start():
    """Track onboarding process start"""
    try:
        from registration_status_tracker import registration_status_tracker
        
        success = registration_status_tracker.track_onboarding_start(current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': 'Onboarding start tracked'})
        else:
            return jsonify({'error': 'Failed to track onboarding start'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking onboarding start: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/track-onboarding-complete', methods=['POST'])
@login_required
def track_onboarding_complete():
    """Track onboarding completion"""
    try:
        from registration_status_tracker import registration_status_tracker
        
        success = registration_status_tracker.track_onboarding_complete(current_user.id)
        
        if success:
            return jsonify({'success': True, 'message': 'Onboarding completion tracked'})
        else:
            return jsonify({'error': 'Failed to track onboarding completion'}), 500
            
    except Exception as e:
        logger.error(f"Error tracking onboarding completion: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Admin endpoints for registration status tracking
@app.route('/api/admin/registration-summary', methods=['GET'])
@login_required
def get_registration_summary():
    """Get registration summary statistics (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from registration_status_tracker import registration_status_tracker
        
        summary = registration_status_tracker.get_pending_registrations_summary()
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error getting registration summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/registration-status/<int:user_id>', methods=['GET'])
@login_required
def get_user_registration_status(user_id):
    """Get registration status for specific user (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from registration_status_tracker import registration_status_tracker
        
        status = registration_status_tracker.get_registration_status(user_id)
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting user registration status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/cleanup-registrations-with-tracking', methods=['POST'])
@login_required
def cleanup_registrations_with_tracking():
    """Clean up expired registrations with tracking (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from registration_status_tracker import registration_status_tracker
        
        data = request.get_json() or {}
        days_old = data.get('days_old', 7)
        
        cleaned_count = registration_status_tracker.cleanup_expired_registrations(days_old)
        
        return jsonify({
            'success': True, 
            'message': f'Cleaned up {cleaned_count} expired registrations with tracking',
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up registrations with tracking: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Registration Session Management Routes
@app.route('/signup/resume/<int:user_id>', methods=['GET'])
def resume_registration(user_id):
    """Resume registration process for a user"""
    try:
        from registration_session_manager import registration_session_manager, SessionType
        
        # Check if user has an active session
        session_id = request.args.get('session_id')
        if not session_id:
            return render_template('signup.html', error="No session provided")
        
        # Resume registration
        success, resume_data, error = registration_session_manager.resume_registration(session_id)
        
        if not success:
            return render_template('signup.html', error=error)
        
        # Check if session belongs to the correct user
        if resume_data.get('user_id') != user_id:
            return render_template('signup.html', error="Invalid session")
        
        # Get current legal versions
        from legal_document_versioning import get_current_legal_versions
        current_versions = get_current_legal_versions()
        
        # Generate CSRF token
        from registration_validation import registration_validator
        csrf_token = registration_validator.generate_csrf_token()
        
        return render_template('signup.html', 
                             legal_versions=current_versions,
                             csrf_token=csrf_token,
                             resume_data=resume_data)
        
    except Exception as e:
        logger.error(f"Error resuming registration: {str(e)}")
        return render_template('signup.html', error="Unable to resume registration")


@app.route('/api/registration/create-session', methods=['POST'])
@csrf_protected(CSRFTokenType.API)
def create_registration_session():
    """Create a new registration session"""
    try:
        from registration_session_manager import registration_session_manager, SessionType
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        session_type_str = data.get('session_type', 'registration')
        metadata = data.get('metadata')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Convert session type string to enum
        try:
            session_type = SessionType(session_type_str)
        except ValueError:
            return jsonify({'error': 'Invalid session type'}), 400
        
        # Create session
        success, session_id, error = registration_session_manager.create_registration_session(
            user_id, session_type, metadata
        )
        
        if success:
            return jsonify({
                'success': True,
                'session_id': session_id,
                'message': 'Session created successfully'
            })
        else:
            return jsonify({'error': error}), 400
            
    except Exception as e:
        logger.error(f"Error creating registration session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/validate-session', methods=['POST'])
def validate_registration_session():
    """Validate a registration session"""
    try:
        from registration_session_manager import registration_session_manager
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Validate session
        is_valid, session_data, error = registration_session_manager.validate_session(session_id)
        
        if is_valid:
            return jsonify({
                'success': True,
                'session_data': {
                    'session_id': session_data.session_id,
                    'user_id': session_data.user_id,
                    'session_type': session_data.session_type.value,
                    'expires_at': session_data.expires_at.isoformat(),
                    'last_activity': session_data.last_activity.isoformat()
                },
                'message': 'Session is valid'
            })
        else:
            return jsonify({'error': error}), 400
            
    except Exception as e:
        logger.error(f"Error validating registration session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/resume-session', methods=['POST'])
def resume_registration_session():
    """Resume registration using session"""
    try:
        from registration_session_manager import registration_session_manager
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Resume registration
        success, resume_data, error = registration_session_manager.resume_registration(session_id)
        
        if success:
            return jsonify({
                'success': True,
                'resume_data': resume_data,
                'message': 'Registration resumed successfully'
            })
        else:
            return jsonify({'error': error}), 400
            
    except Exception as e:
        logger.error(f"Error resuming registration session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/complete-session', methods=['POST'])
def complete_registration_session():
    """Complete a registration session"""
    try:
        from registration_session_manager import registration_session_manager
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        completion_data = data.get('completion_data')
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Complete session
        success = registration_session_manager.complete_session(session_id, completion_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session completed successfully'
            })
        else:
            return jsonify({'error': 'Failed to complete session'}), 500
            
    except Exception as e:
        logger.error(f"Error completing registration session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/extend-session', methods=['POST'])
def extend_registration_session():
    """Extend a registration session"""
    try:
        from registration_session_manager import registration_session_manager
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        hours = data.get('hours', 24)
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Extend session
        success = registration_session_manager.extend_session(session_id, hours)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Session extended by {hours} hours'
            })
        else:
            return jsonify({'error': 'Failed to extend session'}), 400
            
    except Exception as e:
        logger.error(f"Error extending registration session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/registration/user-sessions/<int:user_id>', methods=['GET'])
def get_user_registration_sessions(user_id):
    """Get all registration sessions for a user"""
    try:
        from registration_session_manager import registration_session_manager
        
        sessions = registration_session_manager.get_user_sessions(user_id)
        
        session_data = []
        for session_obj in sessions:
            session_data.append({
                'session_id': session_obj.session_id,
                'session_type': session_obj.session_type.value,
                'status': session_obj.status.value,
                'created_at': session_obj.created_at.isoformat(),
                'expires_at': session_obj.expires_at.isoformat(),
                'last_activity': session_obj.last_activity.isoformat(),
                'ip_address': session_obj.ip_address,
                'metadata': session_obj.metadata
            })
        
        return jsonify({
            'success': True,
            'sessions': session_data,
            'count': len(session_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting user registration sessions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Admin endpoints for session management
@app.route('/api/admin/session-analytics', methods=['GET'])
@login_required
def get_session_analytics():
    """Get session analytics (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from registration_session_manager import registration_session_manager
        
        analytics = registration_session_manager.get_session_analytics()
        return jsonify(analytics)
        
    except Exception as e:
        logger.error(f"Error getting session analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/cleanup-expired-sessions', methods=['POST'])
@login_required
def cleanup_expired_sessions():
    """Clean up expired sessions (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from registration_session_manager import registration_session_manager
        
        cleaned_count = registration_session_manager.cleanup_expired_sessions()
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up {cleaned_count} expired sessions',
            'cleaned_count': cleaned_count
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/invalidate-session', methods=['POST'])
@login_required
def invalidate_session():
    """Invalidate a session (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from registration_session_manager import registration_session_manager
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        session_id = data.get('session_id')
        reason = data.get('reason', 'admin_invalidation')
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Invalidate session
        success = registration_session_manager.invalidate_session(session_id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Session invalidated successfully'
            })
        else:
            return jsonify({'error': 'Failed to invalidate session'}), 500
            
    except Exception as e:
        logger.error(f"Error invalidating session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
# Admin endpoints for TRIMP calculation management
@app.route('/api/admin/trimp-settings', methods=['GET'])
@login_required
def get_trimp_settings():
    """Get TRIMP calculation settings and status (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from utils.feature_flags import is_feature_enabled
        from db_utils import get_trimp_schema_status, get_activities_needing_trimp_recalculation
        
        # Get feature flag status
        enhanced_trimp_enabled = is_feature_enabled('enhanced_trimp_calculation', current_user.id)
        
        # Get database schema status
        schema_status = get_trimp_schema_status()
        
        # Get activities needing recalculation
        activities_needing_recalc = get_activities_needing_trimp_recalculation(days_back=30)
        
        # Get user access status
        user_access = {
            'admin': is_feature_enabled('enhanced_trimp_calculation', 1),
            'beta_users': {
                'user_2': is_feature_enabled('enhanced_trimp_calculation', 2),
                'user_3': is_feature_enabled('enhanced_trimp_calculation', 3)
            },
            'regular_users': is_feature_enabled('enhanced_trimp_calculation', 4)
        }
        
        return jsonify({
            'success': True,
            'enhanced_trimp_enabled': enhanced_trimp_enabled,
            'schema_status': schema_status,
            'activities_needing_recalculation': len(activities_needing_recalc),
            'user_access': user_access,
            'rollout_status': {
                'admin_enabled': user_access['admin'],
                'beta_enabled': user_access['beta_users']['user_2'] and user_access['beta_users']['user_3'],
                'general_release': user_access['regular_users']
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting TRIMP settings: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/trimp-recalculate', methods=['POST'])
@login_required
def recalculate_trimp():
    """Trigger TRIMP recalculation for activities (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')  # Optional: specific user, or None for all users
        days_back = data.get('days_back', 30)  # Default to 30 days
        force_recalculation = data.get('force_recalculation', False)  # Force recalc even if recently processed
        
        from historical_trimp_recalculation import historical_recalculator
        
        # Perform batch recalculation
        result = historical_recalculator.recalculate_activities_batch(
            user_id=user_id,
            days_back=days_back,
            force_recalculation=force_recalculation
        )
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f'Batch recalculation completed: {result.success_count} success, {result.error_count} errors',
            'total_activities': result.total_activities,
            'processed_count': result.processed_count,
            'success_count': result.success_count,
            'error_count': result.error_count,
            'skipped_count': result.skipped_count,
            'total_processing_time_ms': result.total_processing_time_ms,
            'errors': result.errors[:10],  # Limit errors in response
            'results_summary': {
                'enhanced_method_count': len([r for r in result.results if r.calculation_method == 'stream']),
                'average_method_count': len([r for r in result.results if r.calculation_method == 'average']),
                'error_count': len([r for r in result.results if r.calculation_method == 'error']),
                'skipped_count': len([r for r in result.results if r.calculation_method == 'skipped_no_access'])
            }
        }
        
        # Add sample results for first few activities
        if result.results:
            response_data['sample_results'] = [
                {
                    'activity_id': r.activity_id,
                    'user_id': r.user_id,
                    'success': r.success,
                    'old_trimp': r.old_trimp,
                    'new_trimp': r.new_trimp,
                    'calculation_method': r.calculation_method,
                    'hr_samples_used': r.hr_samples_used,
                    'processing_time_ms': r.processing_time_ms,
                    'error_message': r.error_message
                }
                for r in result.results[:5]  # First 5 results
            ]
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error recalculating TRIMP: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/trimp-schema-status', methods=['GET'])
@login_required
def get_trimp_schema_status():
    """Get TRIMP database schema status (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from db_utils import get_trimp_schema_status
        
        status = get_trimp_schema_status()
        
        return jsonify({
            'success': True,
            'schema_status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting TRIMP schema status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/trimp-recalculation-stats', methods=['GET'])
@login_required
def get_trimp_recalculation_stats():
    """Get TRIMP recalculation statistics (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from historical_trimp_recalculation import historical_recalculator
        
        # Get query parameters
        user_id = request.args.get('user_id', type=int)  # Optional
        days_back = request.args.get('days_back', 30, type=int)
        
        # Get statistics
        stats = historical_recalculator.get_recalculation_statistics(user_id, days_back)
        
        return jsonify({
            'success': True,
            'statistics': stats,
            'query_params': {
                'user_id': user_id,
                'days_back': days_back
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting TRIMP recalculation statistics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/trimp-operations', methods=['GET'])
@login_required
def get_trimp_operations():
    """Get active and recent TRIMP recalculation operations (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from historical_trimp_recalculation import historical_recalculator
        
        # Get active operations
        active_operations = historical_recalculator.get_active_operations()
        
        # Get operation history
        history_limit = request.args.get('history_limit', 20, type=int)
        operation_history = historical_recalculator.get_operation_history(history_limit)
        
        # Convert operations to dictionaries for JSON serialization
        def operation_to_dict(op):
            return {
                'operation_id': op.operation_id,
                'user_id': op.user_id,
                'days_back': op.days_back,
                'force_recalculation': op.force_recalculation,
                'status': op.status.value,
                'total_activities': op.total_activities,
                'processed_count': op.processed_count,
                'success_count': op.success_count,
                'error_count': op.error_count,
                'skipped_count': op.skipped_count,
                'started_at': op.started_at.isoformat(),
                'completed_at': op.completed_at.isoformat() if op.completed_at else None,
                'total_processing_time_ms': op.total_processing_time_ms,
                'error_message': op.error_message,
                'progress_percentage': (op.processed_count / op.total_activities * 100) if op.total_activities > 0 else 0
            }
        
        return jsonify({
            'success': True,
            'active_operations': [operation_to_dict(op) for op in active_operations],
            'operation_history': [operation_to_dict(op) for op in operation_history],
            'total_active': len(active_operations)
        })
        
    except Exception as e:
        logger.error(f"Error getting TRIMP operations: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/trimp-operations/<operation_id>', methods=['GET'])
@login_required
def get_trimp_operation_status(operation_id):
    """Get status of a specific TRIMP recalculation operation (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from historical_trimp_recalculation import historical_recalculator
        
        # Get operation status
        operation = historical_recalculator.get_operation_status(operation_id)
        
        if not operation:
            return jsonify({'error': 'Operation not found'}), 404
        
        # Convert to dictionary for JSON serialization
        operation_dict = {
            'operation_id': operation.operation_id,
            'user_id': operation.user_id,
            'days_back': operation.days_back,
            'force_recalculation': operation.force_recalculation,
            'status': operation.status.value,
            'total_activities': operation.total_activities,
            'processed_count': operation.processed_count,
            'success_count': operation.success_count,
            'error_count': operation.error_count,
            'skipped_count': operation.skipped_count,
            'started_at': operation.started_at.isoformat(),
            'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
            'total_processing_time_ms': operation.total_processing_time_ms,
            'error_message': operation.error_message,
            'progress_percentage': (operation.processed_count / operation.total_activities * 100) if operation.total_activities > 0 else 0
        }
        
        return jsonify({
            'success': True,
            'operation': operation_dict
        })
        
    except Exception as e:
        logger.error(f"Error getting TRIMP operation status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/trimp-operations/<operation_id>/cancel', methods=['POST'])
@login_required
def cancel_trimp_operation(operation_id):
    """Cancel a TRIMP recalculation operation (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from historical_trimp_recalculation import historical_recalculator
        
        # Cancel operation
        success = historical_recalculator.cancel_operation(operation_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Operation {operation_id} cancelled successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Operation not found or cannot be cancelled'
            }), 400
        
    except Exception as e:
        logger.error(f"Error cancelling TRIMP operation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/feature-flags', methods=['GET'])
@login_required
def get_feature_flags():
    """Get all feature flags and their status (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from utils.feature_flags import is_feature_enabled
        
        # Get feature flag status for different user types
        feature_flags = {
            'enhanced_trimp_calculation': {
                'name': 'Enhanced TRIMP Calculation',
                'description': 'Uses heart rate stream data for improved TRIMP accuracy',
                'admin_enabled': is_feature_enabled('enhanced_trimp_calculation', 1),
                'beta_enabled': is_feature_enabled('enhanced_trimp_calculation', 2),
                'regular_enabled': is_feature_enabled('enhanced_trimp_calculation', 4),
                'rollout_phase': 'beta'
            },
            'settings_page_enabled': {
                'name': 'Settings Page',
                'description': 'Access to user settings and configuration',
                'admin_enabled': is_feature_enabled('settings_page_enabled', 1),
                'beta_enabled': is_feature_enabled('settings_page_enabled', 2),
                'regular_enabled': is_feature_enabled('settings_page_enabled', 4),
                'rollout_phase': 'beta'
            }
        }
        
        return jsonify({
            'success': True,
            'feature_flags': feature_flags
        })
        
    except Exception as e:
        logger.error(f"Error getting feature flags: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/feature-flags/<feature_name>/toggle', methods=['POST'])
@login_required
def toggle_feature_flag(feature_name):
    """Toggle feature flag for specific user types (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_type = data.get('user_type')  # 'admin', 'beta', 'regular'
        enabled = data.get('enabled', True)
        
        if user_type not in ['admin', 'beta', 'regular']:
            return jsonify({'error': 'Invalid user type. Must be admin, beta, or regular'}), 400
        
        # Note: This is a simplified implementation
        # In a production system, you would want to store feature flags in a database
        # For now, we'll just return a success message indicating the change would be made
        
        logger.info(f"Admin {current_user.id} toggled {feature_name} for {user_type} users to {enabled}")
        
        return jsonify({
            'success': True,
            'message': f'Feature flag {feature_name} for {user_type} users set to {enabled}',
            'feature_name': feature_name,
            'user_type': user_type,
            'enabled': enabled
        })
        
    except Exception as e:
        logger.error(f"Error toggling feature flag: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Deployment monitoring endpoints
@app.route('/api/admin/deployment/status', methods=['GET'])
@login_required
def get_deployment_status():
    """Get TRIMP enhancement deployment status (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from trimp_deployment_monitor import deployment_monitor
        
        status = deployment_monitor.get_deployment_status()
        
        return jsonify({
            'success': True,
            'deployment_status': status
        })
        
    except Exception as e:
        logger.error(f"Error getting deployment status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/deployment/validate', methods=['POST'])
@login_required
def run_deployment_validation():
    """Run deployment validation checks (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        validation_type = data.get('validation_type', 'pre_deployment')
        
        from trimp_deployment_monitor import deployment_monitor
        
        if validation_type == 'pre_deployment':
            results = deployment_monitor.run_pre_deployment_validation()
        elif validation_type == 'post_deployment':
            results = deployment_monitor.run_post_deployment_validation()
        elif validation_type == 'admin_testing':
            results = deployment_monitor.run_admin_testing_validation()
        elif validation_type == 'beta_rollout':
            results = deployment_monitor.run_beta_rollout_validation()
        else:
            return jsonify({'error': 'Invalid validation type'}), 400
        
        # Convert results to JSON-serializable format
        validation_results = []
        for result in results:
            validation_results.append({
                'check_name': result.check_name,
                'status': result.status.value,
                'message': result.message,
                'details': result.details,
                'timestamp': result.timestamp.isoformat() if result.timestamp else None
            })
        
        return jsonify({
            'success': True,
            'validation_type': validation_type,
            'results': validation_results,
            'summary': deployment_monitor.get_validation_summary()
        })
        
    except Exception as e:
        logger.error(f"Error running deployment validation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/deployment/advance-phase', methods=['POST'])
@login_required
def advance_deployment_phase():
    """Advance deployment phase (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        new_phase = data.get('new_phase')
        
        if not new_phase:
            return jsonify({'error': 'new_phase is required'}), 400
        
        from trimp_deployment_monitor import deployment_monitor, DeploymentPhase
        
        try:
            phase_enum = DeploymentPhase(new_phase)
        except ValueError:
            return jsonify({'error': f'Invalid deployment phase: {new_phase}'}), 400
        
        deployment_monitor.advance_deployment_phase(phase_enum)
        
        return jsonify({
            'success': True,
            'message': f'Deployment phase advanced to {new_phase}',
            'current_phase': deployment_monitor.deployment_phase.value
        })
        
    except Exception as e:
        logger.error(f"Error advancing deployment phase: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/deployment/metrics', methods=['GET'])
@login_required
def get_deployment_metrics():
    """Get deployment metrics (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from trimp_deployment_monitor import deployment_monitor
        
        # Update metrics
        deployment_monitor.update_metrics()
        
        metrics = deployment_monitor.metrics
        
        return jsonify({
            'success': True,
            'metrics': {
                'total_activities_processed': metrics.total_activities_processed,
                'enhanced_trimp_calculations': metrics.enhanced_trimp_calculations,
                'average_trimp_calculations': metrics.average_trimp_calculations,
                'calculation_errors': metrics.calculation_errors,
                'feature_flag_checks': metrics.feature_flag_checks,
                'admin_users_active': metrics.admin_users_active,
                'beta_users_active': metrics.beta_users_active,
                'regular_users_active': metrics.regular_users_active,
                'last_updated': metrics.last_updated.isoformat() if metrics.last_updated else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting deployment metrics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/trimp-calculation-stats', methods=['GET'])
@login_required
def get_trimp_calculation_stats():
    """Get TRIMP calculation method statistics (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from db_utils import execute_query
        
        # Get calculation method statistics
        query = """
        SELECT 
            trimp_calculation_method,
            COUNT(*) as count,
            AVG(trimp) as avg_trimp,
            MIN(trimp) as min_trimp,
            MAX(trimp) as max_trimp,
            AVG(hr_stream_sample_count) as avg_hr_samples
        FROM activities 
        WHERE trimp_calculation_method IS NOT NULL
        GROUP BY trimp_calculation_method
        ORDER BY count DESC
        """
        
        results = execute_query(query, fetch=True)
        
        # Get total activities with TRIMP data
        total_query = """
        SELECT COUNT(*) as total_activities
        FROM activities 
        WHERE trimp IS NOT NULL
        """
        total_result = execute_query(total_query, fetch=True)
        total_activities = total_result[0]['total_activities'] if total_result else 0
        
        # Get recent calculation trends (last 30 days)
        trend_query = """
        SELECT 
            DATE(trimp_processed_at) as date,
            trimp_calculation_method,
            COUNT(*) as daily_count
        FROM activities 
        WHERE trimp_processed_at >= NOW() - INTERVAL '30 days'
        AND trimp_calculation_method IS NOT NULL
        GROUP BY DATE(trimp_processed_at), trimp_calculation_method
        ORDER BY date DESC
        """
        
        trend_results = execute_query(trend_query, fetch=True)
        
        # Get user-specific statistics
        user_stats_query = """
        SELECT 
            user_id,
            trimp_calculation_method,
            COUNT(*) as count,
            AVG(trimp) as avg_trimp
        FROM activities 
        WHERE trimp_calculation_method IS NOT NULL
        GROUP BY user_id, trimp_calculation_method
        ORDER BY user_id, count DESC
        """
        
        user_stats = execute_query(user_stats_query, fetch=True)
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_activities': total_activities,
                'calculation_methods': results,
                'daily_trends': trend_results,
                'user_statistics': user_stats
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting TRIMP calculation stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/comprehensive-dashboard', methods=['GET'])
@login_required
def get_comprehensive_dashboard():
    """Get comprehensive admin dashboard data (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from comprehensive_admin_dashboard import dashboard
        
        # Get force refresh parameter
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        # Get dashboard data
        dashboard_data = dashboard.get_dashboard_data(force_refresh)
        
        # Check if user wants HTML format
        if request.args.get('format') == 'html':
            return _render_comprehensive_dashboard_html(dashboard_data)
        
        # Return JSON data
        return jsonify({
            'success': True,
            'data': {
                'overall_health_score': dashboard_data.overall_health_score,
                'total_alerts': dashboard_data.total_alerts,
                'critical_alerts': dashboard_data.critical_alerts,
                'components': [
                    {
                        'component': comp.component.value,
                        'status': comp.status,
                        'health_score': comp.health_score,
                        'last_updated': comp.last_updated.isoformat(),
                        'metrics': comp.metrics,
                        'alerts': [
                            {
                                'id': alert.id,
                                'severity': alert.severity.value,
                                'title': alert.title,
                                'message': alert.message,
                                'timestamp': alert.timestamp.isoformat(),
                                'acknowledged': alert.acknowledged,
                                'resolved': alert.resolved,
                                'details': alert.details
                            }
                            for alert in comp.alerts
                        ]
                    }
                    for comp in dashboard_data.components
                ],
                'recent_errors': [
                    {
                        'timestamp': error['timestamp'].isoformat() if isinstance(error['timestamp'], datetime) else error['timestamp'],
                        'component': error['component'],
                        'error_type': error['error_type'],
                        'details': error['details'],
                        'user_id': error['user_id']
                    }
                    for error in dashboard_data.recent_errors
                ],
                'performance_trends': dashboard_data.performance_trends,
                'last_updated': dashboard_data.last_updated.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting comprehensive dashboard: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
def _render_comprehensive_dashboard_html(dashboard_data):
    """Render comprehensive dashboard as HTML"""
    # Calculate status colors
    def get_status_color(status):
        if status == "healthy":
            return "#28a745"
        elif status == "warning":
            return "#ffc107"
        else:
            return "#dc3545"
    
    def get_health_score_color(score):
        if score >= 90:
            return "#28a745"
        elif score >= 70:
            return "#ffc107"
        else:
            return "#dc3545"
    
    # Generate component cards
    component_cards = ""
    for comp in dashboard_data.components:
        status_color = get_status_color(comp.status)
        health_color = get_health_score_color(comp.health_score)
        
        # Generate alerts HTML
        alerts_html = ""
        for alert in comp.alerts:
            severity_color = {
                'critical': '#dc3545',
                'high': '#fd7e14',
                'medium': '#ffc107',
                'low': '#17a2b8',
                'info': '#6c757d'
            }.get(alert.severity.value, '#6c757d')
            
            alerts_html += f"""
                <div class="alert-item" style="border-left: 3px solid {severity_color}; padding: 8px; margin: 5px 0; background: #f8f9fa;">
                    <strong>{alert.title}</strong><br>
                    <small>{alert.message}</small>
                    <div style="float: right; font-size: 0.8em; color: #666;">
                        {alert.timestamp.strftime('%H:%M:%S')}
                    </div>
                </div>
            """
        
        component_cards += f"""
            <div class="component-card" style="background: white; border-radius: 8px; padding: 20px; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #333;">{comp.component.value.replace('_', ' ').title()}</h3>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="padding: 4px 8px; border-radius: 4px; background: {status_color}; color: white; font-size: 0.8em;">
                            {comp.status.upper()}
                        </span>
                        <span style="font-size: 1.2em; font-weight: bold; color: {health_color};">
                            {comp.health_score}%
                        </span>
                    </div>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <strong>Key Metrics:</strong>
                    <ul style="margin: 5px 0; padding-left: 20px;">
        """
        
        # Add key metrics
        for key, value in comp.metrics.items():
            if key != 'error' and not isinstance(value, dict):
                component_cards += f"<li>{key.replace('_', ' ').title()}: {value}</li>"
        
        component_cards += """
                    </ul>
                </div>
        """
        
        # Add alerts if any
        if comp.alerts:
            component_cards += f"""
                <div>
                    <strong>Active Alerts ({len(comp.alerts)}):</strong>
                    {alerts_html}
                </div>
            """
        
        component_cards += """
                <div style="margin-top: 10px; font-size: 0.8em; color: #666;">
                    Last updated: """ + comp.last_updated.strftime('%Y-%m-%d %H:%M:%S') + """
                </div>
            </div>
        """
    
    # Generate recent errors HTML
    recent_errors_html = ""
    for error in dashboard_data.recent_errors[:10]:  # Show last 10 errors
        timestamp = error['timestamp']
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        recent_errors_html += f"""
            <tr>
                <td>{timestamp.strftime('%H:%M:%S')}</td>
                <td>{error['component']}</td>
                <td>{error['error_type']}</td>
                <td>{error['details']}</td>
                <td>{error['user_id'] or 'N/A'}</td>
            </tr>
        """
    
    # Generate performance trends HTML
    trends_html = ""
    if dashboard_data.performance_trends.get('trimp_trends'):
        trends_html += "<h4>TRIMP Performance (Last 7 Days)</h4><table class='trends-table'><tr><th>Date</th><th>Calculations</th><th>Success Rate</th><th>Errors</th></tr>"
        for trend in dashboard_data.performance_trends['trimp_trends'][:7]:
            trends_html += f"""
                <tr>
                    <td>{trend['date']}</td>
                    <td>{trend['total_calculations']}</td>
                    <td>{trend['success_rate']:.1%}</td>
                    <td>{trend['error_count']}</td>
                </tr>
            """
        trends_html += "</table>"
    
    if dashboard_data.performance_trends.get('acwr_trends'):
        trends_html += "<h4>ACWR Performance (Last 7 Days)</h4><table class='trends-table'><tr><th>Date</th><th>Calculations</th><th>Avg Time (ms)</th><th>Slow Calculations</th></tr>"
        for trend in dashboard_data.performance_trends['acwr_trends'][:7]:
            trends_html += f"""
                <tr>
                    <td>{trend['date']}</td>
                    <td>{trend['total_calculations']}</td>
                    <td>{trend['avg_calculation_time']:.0f}</td>
                    <td>{trend['slow_calculations']}</td>
                </tr>
            """
        trends_html += "</table>"
    
    # Main dashboard HTML
    overall_color = get_health_score_color(dashboard_data.overall_health_score)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Comprehensive Admin Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background-color: #f5f7fa; 
                color: #333;
            }}
            .container {{ 
                max-width: 1400px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 12px; 
                box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
                overflow: hidden;
            }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 30px; 
                text-align: center;
            }}
            .header h1 {{ margin: 0; font-size: 2.5em; font-weight: 300; }}
            .header .subtitle {{ margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1em; }}
            .status-overview {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                padding: 30px; 
                background: #f8f9fa;
            }}
            .status-card {{ 
                background: white; 
                padding: 20px; 
                border-radius: 8px; 
                text-align: center; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .status-card .value {{ 
                font-size: 2.5em; 
                font-weight: bold; 
                margin: 10px 0;
            }}
            .status-card .label {{ 
                color: #666; 
                font-size: 0.9em; 
                text-transform: uppercase; 
                letter-spacing: 0.5px;
            }}
            .content {{ padding: 30px; }}
            .section {{ margin-bottom: 40px; }}
            .section h2 {{ 
                color: #333; 
                border-bottom: 2px solid #e9ecef; 
                padding-bottom: 10px; 
                margin-bottom: 20px;
            }}
            .component-card {{ 
                background: white; 
                border-radius: 8px; 
                padding: 20px; 
                margin: 15px 0; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 4px solid #007bff;
            }}
            .alert-item {{ 
                border-left: 3px solid #ffc107; 
                padding: 10px; 
                margin: 8px 0; 
                background: #fff3cd; 
                border-radius: 4px;
            }}
            .alert-item.critical {{ border-left-color: #dc3545; background: #f8d7da; }}
            .alert-item.high {{ border-left-color: #fd7e14; background: #ffeaa7; }}
            .alert-item.medium {{ border-left-color: #ffc107; background: #fff3cd; }}
            .alert-item.low {{ border-left-color: #17a2b8; background: #d1ecf1; }}
            .alert-item.info {{ border-left-color: #6c757d; background: #e2e3e5; }}
            table {{ 
                width: 100%; 
                border-collapse: collapse; 
                margin: 15px 0; 
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th, td {{ 
                padding: 12px; 
                text-align: left; 
                border-bottom: 1px solid #e9ecef;
            }}
            th {{ 
                background: #f8f9fa; 
                font-weight: 600; 
                color: #495057;
            }}
            .trends-table {{ 
                margin: 20px 0; 
                font-size: 0.9em;
            }}
            .controls {{ 
                text-align: center; 
                padding: 20px; 
                background: #f8f9fa; 
                border-top: 1px solid #e9ecef;
            }}
            .btn {{ 
                background: #007bff; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                cursor: pointer; 
                margin: 0 5px; 
                text-decoration: none;
                display: inline-block;
            }}
            .btn:hover {{ background: #0056b3; }}
            .btn-secondary {{ background: #6c757d; }}
            .btn-secondary:hover {{ background: #545b62; }}
            .auto-refresh {{ 
                position: fixed; 
                top: 20px; 
                right: 20px; 
                background: #28a745; 
                color: white; 
                padding: 10px 15px; 
                border-radius: 5px; 
                font-size: 0.9em;
            }}
            .auto-refresh.warning {{ background: #ffc107; color: #333; }}
            .auto-refresh.error {{ background: #dc3545; }}
            @media (max-width: 768px) {{
                .status-overview {{ grid-template-columns: 1fr; }}
                .container {{ margin: 10px; }}
                .content {{ padding: 20px; }}
            }}
        </style>
        <script>
            let autoRefreshInterval;
            let lastUpdate = new Date();
            
            function startAutoRefresh() {{
                autoRefreshInterval = setInterval(() => {{
                    location.reload();
                }}, 30000); // Refresh every 30 seconds
                updateRefreshStatus();
            }}
            
            function stopAutoRefresh() {{
                if (autoRefreshInterval) {{
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }}
                updateRefreshStatus();
            }}
            
            function updateRefreshStatus() {{
                const statusEl = document.getElementById('refresh-status');
                if (autoRefreshInterval) {{
                    statusEl.textContent = 'Auto-refresh: ON (30s)';
                    statusEl.className = 'auto-refresh';
                }} else {{
                    statusEl.textContent = 'Auto-refresh: OFF';
                    statusEl.className = 'auto-refresh warning';
                }}
            }}
            
            function forceRefresh() {{
                window.location.href = '?refresh=true&format=html';
            }}
            
            // Start auto-refresh on page load
            document.addEventListener('DOMContentLoaded', function() {{
                startAutoRefresh();
            }});
        </script>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Comprehensive Admin Dashboard</h1>
                <p class="subtitle">System Health & Performance Monitoring</p>
                <div id="refresh-status" class="auto-refresh">Auto-refresh: ON (30s)</div>
            </div>
            
            <div class="status-overview">
                <div class="status-card">
                    <div class="value" style="color: {overall_color};">{dashboard_data.overall_health_score}%</div>
                    <div class="label">Overall Health</div>
                </div>
                <div class="status-card">
                    <div class="value" style="color: #dc3545;">{dashboard_data.critical_alerts}</div>
                    <div class="label">Critical Alerts</div>
                </div>
                <div class="status-card">
                    <div class="value" style="color: #ffc107;">{dashboard_data.total_alerts}</div>
                    <div class="label">Total Alerts</div>
                </div>
                <div class="status-card">
                    <div class="value" style="color: #007bff;">{len(dashboard_data.components)}</div>
                    <div class="label">Components</div>
                </div>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>System Components</h2>
                    {component_cards}
                </div>
                
                <div class="section">
                    <h2>Recent Errors</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Component</th>
                                <th>Error Type</th>
                                <th>Details</th>
                                <th>User ID</th>
                            </tr>
                        </thead>
                        <tbody>
                            {recent_errors_html}
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>Performance Trends</h2>
                    {trends_html}
                </div>
            </div>
            
            <div class="controls">
                <button class="btn" onclick="forceRefresh()">Force Refresh</button>
                <button class="btn btn-secondary" onclick="startAutoRefresh()">Start Auto-Refresh</button>
                <button class="btn btn-secondary" onclick="stopAutoRefresh()">Stop Auto-Refresh</button>
                <a href="?format=json" class="btn btn-secondary">View JSON</a>
            </div>
        </div>
        
        <div style="text-align: center; margin-top: 20px; color: #666; font-size: 0.9em;">
            Last updated: {dashboard_data.last_updated.strftime('%Y-%m-%d %H:%M:%S')} | 
            Generated by Comprehensive Admin Dashboard
        </div>
    </body>
    </html>
    """
    
    return html


@app.route('/api/admin/trimp-comparison', methods=['POST'])
@login_required
def compare_trimp_calculation_methods():
    """Compare TRIMP calculation methods for selected activities (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = data.get('user_id')
        activity_count = data.get('activity_count', 10)
        days_back = data.get('days_back', 30)
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        from db_utils import execute_query
        from strava_training_load import calculate_banister_trimp
        from datetime import datetime, timedelta
        
        # Get user's HR configuration
        user_hr_query = """
            SELECT resting_hr, max_hr, gender 
            FROM user_settings 
            WHERE id = %s
        """
        user_hr_result = execute_query(user_hr_query, (user_id,), fetch=True)
        
        # Use user's HR config or defaults
        if user_hr_result and user_hr_result[0]:
            hr_data = user_hr_result[0]
            resting_hr = hr_data.get('resting_hr', 50)
            max_hr = hr_data.get('max_hr', 180)
            gender = hr_data.get('gender', 'male')
            logger.info(f"TRIMP_COMPARISON: Using user HR settings - resting_hr={resting_hr}, max_hr={max_hr}, gender={gender}")
        else:
            # Fallback to defaults if user config not found
            resting_hr = 50
            max_hr = 180
            gender = 'male'
            logger.warning(f"TRIMP_COMPARISON: User HR config not found, using defaults - resting_hr={resting_hr}, max_hr={max_hr}, gender={gender}")
        
        # Get activities for comparison
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days_back)
        
        activities_query = """
        SELECT 
            activity_id, date, duration_minutes, avg_heart_rate, trimp, trimp_calculation_method,
            hr_stream_sample_count
        FROM activities 
        WHERE user_id = %s 
        AND date >= %s 
        AND date <= %s
        AND avg_heart_rate IS NOT NULL
        AND duration_minutes > 0
        ORDER BY date DESC
        LIMIT %s
        """
        
        activities = execute_query(activities_query, (user_id, start_date, end_date, activity_count), fetch=True)
        
        if not activities:
            return jsonify({'error': 'No activities found for comparison'}), 404
        
        # Get HR stream data for activities
        hr_streams_query = """
        SELECT activity_id, hr_data
        FROM hr_streams 
        WHERE activity_id IN ({})
        """.format(','.join(['%s' for _ in activities]))
        
        activity_ids = [activity['activity_id'] for activity in activities]
        hr_streams = execute_query(hr_streams_query, activity_ids, fetch=True)
        
        # Create HR stream lookup
        hr_stream_lookup = {stream['activity_id']: stream['hr_data'] for stream in hr_streams}
        
        # Perform comparison calculations
        comparison_results = []
        total_enhanced_trimp = 0
        total_average_trimp = 0
        total_difference = 0
        total_percentage_difference = 0
        
        for activity in activities:
            activity_id = activity['activity_id']
            duration_minutes = activity['duration_minutes']
            avg_hr = activity['avg_heart_rate']
            
            # Get HR stream data if available
            hr_stream_data = hr_stream_lookup.get(activity_id)
            
            # Log HR stream data processing
            logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - HR stream data available: {hr_stream_data is not None}")
            if hr_stream_data:
                logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - HR stream data type: {type(hr_stream_data)}")
                if isinstance(hr_stream_data, list):
                    logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - HR stream data length: {len(hr_stream_data)}")
                elif isinstance(hr_stream_data, str):
                    logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - HR stream data length: {len(hr_stream_data)}")
                else:
                    logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - HR stream data type: {type(hr_stream_data)}")
            
            # Calculate enhanced TRIMP (with HR stream if available)
            if hr_stream_data:
                try:
                    # HR stream data is already a Python list from JSONB column
                    if isinstance(hr_stream_data, str):
                        import json
                        hr_stream = json.loads(hr_stream_data)
                    else:
                        hr_stream = hr_stream_data
                    
                    enhanced_trimp = calculate_banister_trimp(
                        duration_minutes=duration_minutes,
                        avg_hr=avg_hr,
                        resting_hr=resting_hr,
                        max_hr=max_hr,
                        gender=gender,
                        hr_stream=hr_stream
                    )
                    logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - Enhanced TRIMP with stream: {enhanced_trimp}")
                except Exception as e:
                    # Fallback to average HR calculation
                    enhanced_trimp = calculate_banister_trimp(
                        duration_minutes=duration_minutes,
                        avg_hr=avg_hr,
                        resting_hr=resting_hr,
                        max_hr=max_hr,
                        gender=gender
                    )
                    logger.warning(f"TRIMP_COMPARISON: Activity {activity_id} - Enhanced TRIMP fallback: {enhanced_trimp} (error: {str(e)})")
            else:
                # No HR stream data, use average HR calculation
                enhanced_trimp = calculate_banister_trimp(
                    duration_minutes=duration_minutes,
                    avg_hr=avg_hr,
                    resting_hr=resting_hr,
                    max_hr=max_hr,
                    gender=gender
                )
                logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - Enhanced TRIMP (no stream): {enhanced_trimp}")
            
            # Calculate average HR TRIMP
            average_trimp = calculate_banister_trimp(
                duration_minutes=duration_minutes,
                avg_hr=avg_hr,
                resting_hr=resting_hr,
                max_hr=max_hr,
                gender=gender
            )
            logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - Average HR TRIMP: {average_trimp}")
            
            # Calculate differences
            difference = enhanced_trimp - average_trimp
            percentage_difference = (difference / average_trimp * 100) if average_trimp > 0 else 0
            
            logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - Difference: {difference:.2f} ({percentage_difference:.1f}%)")
            
            # Log TRIMP calculation results
            logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - Enhanced TRIMP: {enhanced_trimp}, Average TRIMP: {average_trimp}")
            logger.info(f"TRIMP_COMPARISON: Activity {activity_id} - Difference: {difference}, Percentage: {percentage_difference}%")
            
            # Accumulate totals
            total_enhanced_trimp += enhanced_trimp
            total_average_trimp += average_trimp
            total_difference += difference
            total_percentage_difference += percentage_difference
            
            comparison_results.append({
                'activity_id': activity_id,
                'date': activity['date'],
                'duration': duration_minutes,
                'avg_hr': avg_hr,
                'enhanced_trimp': round(enhanced_trimp, 2),
                'average_trimp': round(average_trimp, 2),
                'difference': round(difference, 2),
                'percentage_difference': round(percentage_difference, 2),
                'has_hr_stream': hr_stream_data is not None,
                'hr_stream_samples': activity.get('hr_stream_sample_count', 0)
            })
        
        # Calculate summary statistics
        avg_enhanced_trimp = total_enhanced_trimp / len(activities)
        avg_average_trimp = total_average_trimp / len(activities)
        avg_difference = total_difference / len(activities)
        avg_percentage_difference = total_percentage_difference / len(activities)
        
        # Count activities with HR stream data
        activities_with_hr_stream = sum(1 for result in comparison_results if result['has_hr_stream'])
        
        summary = {
            'total_activities': len(activities),
            'activities_with_hr_stream': activities_with_hr_stream,
            'avg_enhanced_trimp': round(avg_enhanced_trimp, 2),
            'avg_average_trimp': round(avg_average_trimp, 2),
            'avg_difference': round(avg_difference, 2),
            'avg_percentage_difference': round(avg_percentage_difference, 2),
            'user_id': user_id,
            'days_back': days_back
        }
        
        return jsonify({
            'success': True,
            'comparison_results': comparison_results,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error comparing TRIMP calculation methods: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/feedback/submit', methods=['POST'])
@login_required
def submit_feedback():
    """Submit user feedback for TRIMP enhancement (all users)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title')
        description = data.get('description')
        rating = data.get('rating')  # 1-5 scale
        feedback_type = data.get('feedback_type', 'user_feedback')
        
        if not title or not description:
            return jsonify({'error': 'Title and description are required'}), 400
        
        if rating and (rating < 1 or rating > 5):
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        from feedback_collection_system import feedback_system, FeedbackType
        
        try:
            feedback_type_enum = FeedbackType(feedback_type)
        except ValueError:
            feedback_type_enum = FeedbackType.USER_FEEDBACK
        
        feedback_id = feedback_system.collect_user_feedback(
            user_id=current_user.id,
            title=title,
            description=description,
            rating=rating,
            feedback_type=feedback_type_enum
        )
        
        return jsonify({
            'success': True,
            'feedback_id': feedback_id,
            'message': 'Feedback submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/feedback/accuracy-validation', methods=['POST'])
@login_required
def submit_accuracy_validation():
    """Submit accuracy validation against external sources (all users)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        activity_id = data.get('activity_id')
        external_source = data.get('external_source')
        external_trimp = data.get('external_trimp')
        our_trimp = data.get('our_trimp')
        validation_method = data.get('validation_method', 'manual_comparison')
        
        if not all([activity_id, external_source, external_trimp, our_trimp]):
            return jsonify({'error': 'All fields are required'}), 400
        
        if external_trimp <= 0 or our_trimp <= 0:
            return jsonify({'error': 'TRIMP values must be positive'}), 400
        
        from feedback_collection_system import feedback_system
        
        validation_id = feedback_system.collect_accuracy_validation(
            user_id=current_user.id,
            activity_id=activity_id,
            external_source=external_source,
            external_trimp=external_trimp,
            our_trimp=our_trimp,
            validation_method=validation_method
        )
        
        return jsonify({
            'success': True,
            'validation_id': validation_id,
            'message': 'Accuracy validation submitted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error submitting accuracy validation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/feedback/summary', methods=['GET'])
@login_required
def get_feedback_summary():
    """Get feedback summary (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from feedback_collection_system import feedback_system
        
        days_back = request.args.get('days_back', 30, type=int)
        summary = feedback_system.get_feedback_summary(days_back)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting feedback summary: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/feedback/recent', methods=['GET'])
@login_required
def get_recent_feedback():
    """Get recent feedback items (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from feedback_collection_system import feedback_system
        
        limit = request.args.get('limit', 20, type=int)
        recent_feedback = feedback_system.get_recent_feedback(limit)
        
        return jsonify({
            'success': True,
            'recent_feedback': recent_feedback
        })
        
    except Exception as e:
        logger.error(f"Error getting recent feedback: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/feedback/accuracy-validations', methods=['GET'])
@login_required
def get_accuracy_validations():
    """Get accuracy validations (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from feedback_collection_system import feedback_system
        
        limit = request.args.get('limit', 20, type=int)
        validations = feedback_system.get_accuracy_validations(limit)
        
        return jsonify({
            'success': True,
            'accuracy_validations': validations
        })
        
    except Exception as e:
        logger.error(f"Error getting accuracy validations: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
@app.route('/api/admin/feedback/report', methods=['GET'])
@login_required
def get_feedback_report():
    """Get comprehensive feedback report (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from feedback_collection_system import feedback_system
        
        report = feedback_system.generate_feedback_report()
        
        return jsonify({
            'success': True,
            'report': report
        })
        
    except Exception as e:
        logger.error(f"Error getting feedback report: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/monitoring/dashboard', methods=['GET'])
@login_required
def get_monitoring_dashboard():
    """Get system monitoring dashboard data (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from system_monitoring_dashboard import monitoring_dashboard
        
        hours_back = request.args.get('hours_back', 24, type=int)
        dashboard_data = monitoring_dashboard.get_dashboard_data(hours_back)
        
        return jsonify({
            'success': True,
            'dashboard_data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"Error getting monitoring dashboard: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/monitoring/start', methods=['POST'])
@login_required
def start_monitoring():
    """Start system monitoring (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from system_monitoring_dashboard import monitoring_dashboard
        
        data = request.get_json()
        interval_seconds = data.get('interval_seconds', 60) if data else 60
        
        # Start monitoring in background
        import threading
        monitoring_thread = threading.Thread(
            target=monitoring_dashboard.start_monitoring,
            args=(interval_seconds,),
            daemon=True
        )
        monitoring_thread.start()
        
        return jsonify({
            'success': True,
            'message': f'System monitoring started with {interval_seconds}s interval'
        })
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/monitoring/stop', methods=['POST'])
@login_required
def stop_monitoring():
    """Stop system monitoring (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from system_monitoring_dashboard import monitoring_dashboard
        
        monitoring_dashboard.stop_monitoring()
        
        return jsonify({
            'success': True,
            'message': 'System monitoring stopped'
        })
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/admin/monitoring/collect-metrics', methods=['POST'])
@login_required
def collect_metrics():
    """Manually collect system metrics (admin only)"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        from system_monitoring_dashboard import monitoring_dashboard
        
        monitoring_dashboard.collect_all_metrics()
        monitoring_dashboard.check_alerts()
        
        return jsonify({
            'success': True,
            'message': 'Metrics collected successfully',
            'metrics_count': len(monitoring_dashboard.metrics),
            'alerts_count': len(monitoring_dashboard.alerts)
        })
        
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Settings page routes
@app.route('/settings/profile', methods=['GET'])
@login_required
def settings_profile():
    """Profile settings page"""
    try:
        from datetime import date
        
        # Load complete user settings from database
        user_settings = db_utils.execute_query("""
            SELECT * FROM user_settings WHERE id = %s
        """, (current_user.id,), fetch=True)
        
        if user_settings and user_settings[0]:
            user_data = user_settings[0]
        else:
            user_data = current_user
        
        return render_template('settings_profile.html', 
                             user=user_data, 
                             active_section='profile',
                             today=date.today().isoformat(),
                             user_context={'is_authenticated': True, 'user': user_data})
    except Exception as e:
        app.logger.error(f"Error rendering profile settings: {str(e)}")
        return render_template('error.html', error="Failed to load profile settings"), 500

@app.route('/settings/hrzones', methods=['GET'])
@login_required
def settings_hrzones():
    """Heart Rate Zones settings page"""
    try:
        # Load complete user settings from database
        user_settings = db_utils.execute_query("""
            SELECT * FROM user_settings WHERE id = %s
        """, (current_user.id,), fetch=True)
        
        if user_settings and user_settings[0]:
            user_data = user_settings[0]
        else:
            user_data = current_user
        
        return render_template('settings_hrzones.html', 
                             user=user_data, 
                             active_section='hrzones',
                             user_context={'is_authenticated': True, 'user': user_data})
    except Exception as e:
        app.logger.error(f"Error rendering HR zones settings: {str(e)}")
        return render_template('error.html', error="Failed to load HR zones settings"), 500

@app.route('/settings/training', methods=['GET'])
@login_required
def settings_training():
    """Training settings page"""
    try:
        # Load complete user settings from database
        user_settings = db_utils.execute_query("""
            SELECT * FROM user_settings WHERE id = %s
        """, (current_user.id,), fetch=True)
        
        if user_settings and user_settings[0]:
            user_data = user_settings[0]
        else:
            user_data = current_user
        
        return render_template('settings_training.html', 
                             user=user_data, 
                             active_section='training',
                             user_context={'is_authenticated': True, 'user': user_data})
    except Exception as e:
        app.logger.error(f"Error rendering training settings: {str(e)}")
        return render_template('error.html', error="Failed to load training settings"), 500

@app.route('/settings/coaching', methods=['GET'])
@login_required
def settings_coaching():
    """Coaching settings page"""
    try:
        # Load complete user settings from database
        user_settings = db_utils.execute_query("""
            SELECT * FROM user_settings WHERE id = %s
        """, (current_user.id,), fetch=True)
        
        if user_settings and user_settings[0]:
            user_data = user_settings[0]
        else:
            user_data = current_user
        
        return render_template('settings_coaching.html', 
                             user=user_data, 
                             active_section='coaching',
                             user_context={'is_authenticated': True, 'user': user_data})
    except Exception as e:
        app.logger.error(f"Error rendering coaching settings: {str(e)}")
        return render_template('error.html', error="Failed to load coaching settings"), 500

@app.route('/settings/acwr', methods=['GET'])
@login_required
def settings_acwr():
    """ACWR visualization settings page"""
    try:
        return render_template('settings_acwr.html', 
                             user=current_user, 
                             active_section='acwr',
                             user_context={'is_authenticated': True, 'user': current_user})
    except Exception as e:
        app.logger.error(f"Error rendering ACWR settings: {str(e)}")
        return render_template('error.html', error="Failed to load ACWR settings"), 500

@app.route('/admin/trimp-settings', methods=['GET'])
@login_required
def admin_trimp_settings():
    """Admin interface for TRIMP calculation management"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        return render_template('admin_trimp_settings.html')
        
    except Exception as e:
        logger.error(f"Error loading TRIMP admin interface: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/welcome-post-strava')
@login_required
def welcome_post_strava():
    """Onboarding page - shows form if needed, otherwise redirects to dashboard"""
    user_id = current_user.id
    
    # Check for force_show parameter to bypass onboarding check
    force_show = request.args.get('force_show', 'false').lower() == 'true'
    sync_wait = request.args.get('sync_wait', 'false').lower() == 'true'
    
    # Check if user needs onboarding
    # First check if onboarding is already completed
    from db_utils import execute_query
    onboarding_data = execute_query("""
        SELECT onboarding_completed, onboarding_step 
        FROM user_settings 
        WHERE id = %s
    """, (user_id,), fetch=True)
    
    onboarding_completed = False
    if onboarding_data and len(onboarding_data) > 0:
        onboarding_completed = onboarding_data[0].get('onboarding_completed', False) or onboarding_data[0].get('onboarding_step') == 'completed'
    
    logger.info(f"Welcome page check for user {user_id}: needs_onboarding={needs_onboarding(user_id)}, onboarding_completed={onboarding_completed}, force_show={force_show}, sync_wait={sync_wait}")
    
    if (needs_onboarding(user_id) and not onboarding_completed) or force_show or (sync_wait and not onboarding_completed):
        # Get current legal versions for the template
        from legal_document_versioning import get_current_legal_versions
        current_versions = get_current_legal_versions()
        
        # Check sync status
        sync_status = {
            'in_progress': session.get('strava_sync_in_progress', False),
            'complete': session.get('strava_sync_complete', False),
            'failed': session.get('strava_sync_failed', False)
        }
        
        return render_template('welcome_post_strava.html', 
                             show_onboarding=True, 
                             user_id=user_id,
                             legal_versions=current_versions,
                             sync_status=sync_status)
    else:
        # User is already set up, redirect to dashboard
        return redirect(url_for('dashboard'))


@app.route('/welcome-stage1', methods=['POST'])
@login_required
def welcome_stage1():
    """Handle Stage 1 form submission (Essential Setup) using existing onboarding system"""
    user_id = current_user.id
    
    try:
        age = request.form.get('age')
        gender = request.form.get('gender')
        training_experience = request.form.get('training_experience')
        primary_sport = request.form.get('primary_sport')
        resting_hr = request.form.get('resting_hr')
        max_hr = request.form.get('max_hr')
        coaching_tone = request.form.get('coaching_tone')
        
        # Get legal acceptance status
        terms_accepted = request.form.get('terms_accepted') == 'on'
        privacy_accepted = request.form.get('privacy_accepted') == 'on'
        disclaimer_accepted = request.form.get('disclaimer_accepted') == 'on'
        
        # Validate required fields
        if not all([age, gender, training_experience, primary_sport, resting_hr, max_hr, coaching_tone]):
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('welcome_post_strava'))
        
        # Validate legal acceptance
        if not all([terms_accepted, privacy_accepted, disclaimer_accepted]):
            flash('Please accept all legal agreements to continue.', 'error')
            return redirect(url_for('welcome_post_strava'))
        
        # Map coaching tone to spectrum value
        tone_map = {
            'casual': 12,
            'supportive': 37,
            'motivational': 62,
            'analytical': 87
        }
        coaching_style_spectrum = tone_map.get(coaching_tone, 50)
        
        # Update user settings with all required data
        from db_utils import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Update profile data
                cursor.execute("""
                    UPDATE user_settings 
                    SET age = %s, gender = %s, training_experience = %s, primary_sport = %s,
                        resting_hr = %s, max_hr = %s, coaching_tone = %s, coaching_style_spectrum = %s
                    WHERE id = %s
                """, (age, gender, training_experience, primary_sport, resting_hr, max_hr, coaching_tone, coaching_style_spectrum, user_id))
                
                # Update legal acceptance timestamps
                from datetime import datetime
                current_time = datetime.now()
                cursor.execute("""
                    UPDATE user_settings 
                    SET terms_accepted_at = %s, privacy_policy_accepted_at = %s, disclaimer_accepted_at = %s
                    WHERE id = %s
                """, (current_time, current_time, current_time, user_id))
                
                conn.commit()
        
        # Log legal acceptance - OPTIMIZED VERSION
        if terms_accepted and privacy_accepted and disclaimer_accepted:
            try:
                from legal_document_versioning import get_current_legal_versions
                from db_utils import get_db_connection
                
                current_versions = get_current_legal_versions()
                ip_address = request.remote_addr
                user_agent = request.headers.get('User-Agent', '')
                current_time = datetime.now()
                
                # Batch all legal compliance logging in a single database transaction
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Insert all three legal acceptances in one transaction
                    cursor.execute("""
                        INSERT INTO legal_compliance 
                        (user_id, document_type, version, accepted_at, ip_address, user_agent, created_at)
                        VALUES 
                        (%s, 'terms', %s, %s, %s, %s, %s),
                        (%s, 'privacy', %s, %s, %s, %s, %s),
                        (%s, 'disclaimer', %s, %s, %s, %s, %s)
                    """, (
                        user_id, current_versions.get('terms', '2.0'), current_time, ip_address, user_agent, current_time,
                        user_id, current_versions.get('privacy', '2.0'), current_time, ip_address, user_agent, current_time,
                        user_id, current_versions.get('disclaimer', '2.0'), current_time, ip_address, user_agent, current_time
                    ))
                    
                    conn.commit()
                    logger.info(f"Logged legal compliance for user {user_id}")
                    
            except Exception as e:
                logger.error(f"Error logging legal compliance for user {user_id}: {e}")
                # Don't fail the form submission if legal logging fails
        
        # Update onboarding progress using existing system
        from user_account_manager import user_account_manager
        success = user_account_manager.complete_onboarding(user_id)
        
        if success:
            # Onboarding completed successfully - always redirect to dashboard
            # Clear any sync status from session since onboarding is complete
            session.pop('strava_sync_in_progress', None)
            session.pop('strava_sync_complete', None)
            session.pop('strava_sync_failed', None)
            
            flash('Welcome! Your profile is set up. Let\'s explore your training dashboard!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Onboarding completion failed - stay on welcome page
            flash('Error completing your setup. Please try again.', 'error')
            return redirect(url_for('welcome_post_strava'))
        
    except Exception as e:
        logger.error(f"Error updating Stage 1 data: {e}")
        flash('Error saving your information. Please try again.', 'error')
        return redirect(url_for('welcome_post_strava'))

@app.route('/welcome-skip-stage3')
@login_required
def welcome_skip_stage3():
    """Skip Stage 3 and go directly to dashboard using existing onboarding system"""
    user_id = current_user.id
    
    try:
        # Set default values for Stage 3 fields
        from db_utils import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE user_settings 
                    SET acwr_alert_threshold = 1.3, injury_risk_alerts = true
                    WHERE id = %s
                """, (user_id,))
                conn.commit()
        
        # Complete onboarding using existing system
        from onboarding_manager import complete_onboarding_step, OnboardingStep
        complete_onboarding_step(user_id, OnboardingStep.FEATURES_TOUR)
        
        flash('Welcome to TrainingMonkey! You can adjust advanced settings later.', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Error skipping Stage 3: {e}")
        flash('Error completing setup. Please try again.', 'error')
        return redirect(url_for('welcome_post_strava'))

@app.route('/goals-setup', methods=['GET', 'POST'])
@login_required
def goals_setup():
    """Streamlined goals setup page - addresses 'too many options' and 'time consuming' issues"""
    
    if request.method == 'POST':
        # Get form data
        goal_type = request.form.get('goal_type')
        target_value = request.form.get('target_value')
        timeframe = request.form.get('timeframe')
        
        # Validate input
        if not all([goal_type, target_value, timeframe]):
            flash('Please fill in all fields', 'error')
            return redirect(url_for('goals_setup'))
        
        try:
            # Save goals to database
            user_id = session.get('user_id')
            
            # Update user_settings with goals
            db_utils.execute_query("""
                UPDATE user_settings 
                SET goals_configured = TRUE,
                    goal_type = %s,
                    goal_target = %s,
                    goal_timeframe = %s,
                    goals_setup_date = NOW()
                WHERE user_id = %s
            """, (goal_type, target_value, timeframe, user_id))
            
            # Mark onboarding step as complete
            from onboarding_manager import onboarding_manager
            onboarding_manager.complete_step(user_id, 'goals_configured')
            
            # Track analytics (real data this time!)
            track_analytics_event('goals_setup_completed', {
                'goal_type': goal_type,
                'timeframe': timeframe,
                'user_id': user_id
            })
            
            flash('Goals set successfully! 🎯', 'success')
            # Redirect back to welcome page to continue onboarding flow
            return redirect(url_for('welcome_post_strava'))
            
        except Exception as e:
            flash('Error saving goals. Please try again.', 'error')
            return redirect(url_for('goals_setup'))
    
    # GET request - show goals setup form
    return render_template('goals_setup.html')

def track_analytics_event(event_name, data):
    """Track real analytics events"""
    try:
        # Log to database for real analytics
        db_utils.execute_query("""
            INSERT INTO onboarding_analytics (user_id, event_name, event_data, timestamp)
            VALUES (%s, %s, %s, NOW())
        """, (data.get('user_id'), event_name, json.dumps(data)))
    except Exception as e:
        # Fallback to logging
        logger.error(f"Analytics tracking error: {e}")

@login_required
@app.route('/proactive-token-refresh', methods=['POST'])
def proactive_token_refresh():
    """Proactively refresh tokens for current user if they're expiring soon"""
    try:
        user_id = current_user.id
        logger.info(f"Proactive token refresh requested for user {user_id}")
        
        from enhanced_token_management import SimpleTokenManager
        token_manager = SimpleTokenManager(user_id)
        
        # Check current token status
        token_status = token_manager.get_simple_token_status()
        logger.info(f"Current token status for user {user_id}: {token_status}")
        
        # If tokens need refresh, refresh them proactively
        if token_status.get('status') in ['expired', 'expiring_soon']:
            logger.info(f"Proactively refreshing tokens for user {user_id}")
            refresh_result = token_manager.refresh_strava_tokens()
            
            if refresh_result:
                new_status = token_manager.get_simple_token_status()
                logger.info(f"✅ Proactive token refresh successful for user {user_id}")
                
                return jsonify({
                    'success': True,
                    'message': 'Tokens refreshed proactively',
                    'refreshed': True,
                    'old_status': token_status,
                    'new_status': new_status
                })
            else:
                logger.error(f"❌ Proactive token refresh failed for user {user_id}")
                return jsonify({
                    'success': False,
                    'message': 'Token refresh failed - re-authentication required',
                    'needs_reauth': True,
                    'current_status': token_status
                }), 401
        else:
            logger.info(f"✅ Tokens are still valid for user {user_id} - no refresh needed")
            return jsonify({
                'success': True,
                'message': 'Tokens are still valid - no refresh needed',
                'refreshed': False,
                'current_status': token_status
            })
            
    except Exception as e:
        logger.error(f"Error in proactive token refresh for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# COACH PAGE API ENDPOINTS
# =============================================================================
# API endpoints for YTM Coach page features: race goals, race history, training schedules

@app.route('/api/coach/race-goals', methods=['GET'])
@login_required
def get_race_goals():
    """Get all race goals for current user, ordered by race date"""
    try:
        user_id = current_user.id
        logger.info(f"Fetching race goals for user {user_id}")
        
        # Query race goals
        race_goals = db_utils.execute_query(
            """
            SELECT id, user_id, race_name, race_date, race_type, priority, 
                   target_time, notes, elevation_gain_feet, created_at, updated_at
            FROM race_goals 
            WHERE user_id = %s 
            ORDER BY race_date ASC
            """,
            (user_id,),
            fetch=True
        )
        
        # Convert to list of dicts and serialize dates
        goals_list = []
        if race_goals:
            for goal in race_goals:
                goal_dict = dict(goal) if hasattr(goal, 'keys') else {
                    'id': goal[0],
                    'user_id': goal[1],
                    'race_name': goal[2],
                    'race_date': goal[3],
                    'race_type': goal[4],
                    'priority': goal[5],
                    'target_time': goal[6],
                    'notes': goal[7],
                    'elevation_gain_feet': goal[8],
                    'created_at': goal[9],
                    'updated_at': goal[10]
                }
                
                # Serialize dates
                if isinstance(goal_dict.get('race_date'), date):
                    goal_dict['race_date'] = goal_dict['race_date'].strftime('%Y-%m-%d')
                if isinstance(goal_dict.get('created_at'), datetime):
                    goal_dict['created_at'] = goal_dict['created_at'].isoformat()
                if isinstance(goal_dict.get('updated_at'), datetime):
                    goal_dict['updated_at'] = goal_dict['updated_at'].isoformat()
                    
                goals_list.append(goal_dict)
        
        logger.info(f"Found {len(goals_list)} race goals for user {user_id}")
        
        return jsonify({
            'success': True,
            'goals': goals_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching race goals for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-goals', methods=['POST'])
@login_required
def create_race_goal():
    """Create a new race goal"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        race_name = data.get('race_name')
        race_date = data.get('race_date')
        priority = data.get('priority')
        
        if not race_name:
            return jsonify({'success': False, 'error': 'race_name is required'}), 400
        if not race_date:
            return jsonify({'success': False, 'error': 'race_date is required'}), 400
        if not priority:
            return jsonify({'success': False, 'error': 'priority is required'}), 400
        
        # Validate race_date is future date (allow up to 7 days in past for flexibility)
        try:
            race_date_obj = datetime.strptime(race_date, '%Y-%m-%d').date()
            today = get_app_current_date()
            days_until_race = (race_date_obj - today).days
            
            if days_until_race < -7:
                return jsonify({
                    'success': False, 
                    'error': f'Race date must be in the future or within the last 7 days (race is {abs(days_until_race)} days in the past)'
                }), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'race_date must be in format YYYY-MM-DD'}), 400
        
        # Validate priority
        if priority not in ['A', 'B', 'C']:
            return jsonify({'success': False, 'error': 'priority must be A, B, or C'}), 400
        
        # Enforce only one A race at a time
        if priority == 'A':
            existing_a_race = db_utils.execute_query(
                "SELECT id FROM race_goals WHERE user_id = %s AND priority = 'A'",
                (user_id,),
                fetch=True
            )
            if existing_a_race:
                return jsonify({
                    'success': False, 
                    'error': 'You can only have one A race at a time. Please change your existing A race to B or C first.'
                }), 400
        
        # Optional fields
        race_type = data.get('race_type')
        target_time = data.get('target_time')
        notes = data.get('notes')
        elevation_gain_feet = data.get('elevation_gain_feet')
        
        logger.info(f"Creating race goal for user {user_id}: {race_name} ({priority})")
        
        # Insert new race goal
        result = db_utils.execute_query(
            """
            INSERT INTO race_goals 
                (user_id, race_name, race_date, race_type, priority, target_time, notes, elevation_gain_feet, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, race_name, race_date, race_type, priority, target_time, notes, elevation_gain_feet, created_at, updated_at
            """,
            (user_id, race_name, race_date, race_type, priority, target_time, notes, elevation_gain_feet),
            fetch=True
        )
        
        if result and len(result) > 0:
            goal = result[0]
            goal_dict = dict(goal) if hasattr(goal, 'keys') else {
                'id': goal[0],
                'race_name': goal[1],
                'race_date': goal[2],
                'race_type': goal[3],
                'priority': goal[4],
                'target_time': goal[5],
                'notes': goal[6],
                'elevation_gain_feet': goal[7],
                'created_at': goal[8],
                'updated_at': goal[9]
            }
            
            # Serialize dates
            if isinstance(goal_dict.get('race_date'), date):
                goal_dict['race_date'] = goal_dict['race_date'].strftime('%Y-%m-%d')
            if isinstance(goal_dict.get('created_at'), datetime):
                goal_dict['created_at'] = goal_dict['created_at'].isoformat()
            if isinstance(goal_dict.get('updated_at'), datetime):
                goal_dict['updated_at'] = goal_dict['updated_at'].isoformat()
            
            logger.info(f"Successfully created race goal {goal_dict['id']} for user {user_id}")
            
            return jsonify({
                'success': True,
                'race_goal': goal_dict
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create race goal'}), 500
            
    except Exception as e:
        logger.error(f"Error creating race goal for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-goals/<int:goal_id>', methods=['PUT'])
@login_required
def update_race_goal(goal_id):
    """Update an existing race goal"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Verify goal belongs to current user
        existing_goal = db_utils.execute_query(
            "SELECT id, priority FROM race_goals WHERE id = %s AND user_id = %s",
            (goal_id, user_id),
            fetch=True
        )
        
        if not existing_goal:
            return jsonify({'success': False, 'error': 'Race goal not found'}), 404
        
        # Get current priority
        current_priority = existing_goal[0]['priority'] if hasattr(existing_goal[0], 'keys') else existing_goal[0][1]
        
        # Validate new priority if provided
        new_priority = data.get('priority', current_priority)
        if new_priority not in ['A', 'B', 'C']:
            return jsonify({'success': False, 'error': 'priority must be A, B, or C'}), 400
        
        # If changing to A, enforce only one A race
        if new_priority == 'A' and current_priority != 'A':
            existing_a_race = db_utils.execute_query(
                "SELECT id FROM race_goals WHERE user_id = %s AND priority = 'A' AND id != %s",
                (user_id, goal_id),
                fetch=True
            )
            if existing_a_race:
                return jsonify({
                    'success': False,
                    'error': 'You can only have one A race at a time. Please change your existing A race to B or C first.'
                }), 400
        
        # Validate race_date if being updated (allow up to 7 days in past for flexibility)
        if 'race_date' in data:
            try:
                race_date_obj = datetime.strptime(data['race_date'], '%Y-%m-%d').date()
                today = get_app_current_date()
                days_until_race = (race_date_obj - today).days
                
                if days_until_race < -7:
                    return jsonify({
                        'success': False,
                        'error': f'Race date must be in the future or within the last 7 days (race is {abs(days_until_race)} days in the past)'
                    }), 400
            except ValueError:
                return jsonify({'success': False, 'error': 'race_date must be in format YYYY-MM-DD'}), 400
        
        # Build update query dynamically for provided fields
        update_fields = []
        update_values = []
        
        if 'race_name' in data:
            if not data['race_name']:
                return jsonify({'success': False, 'error': 'race_name cannot be empty'}), 400
            update_fields.append('race_name = %s')
            update_values.append(data['race_name'])
        if 'race_date' in data:
            update_fields.append('race_date = %s')
            update_values.append(data['race_date'])
        if 'race_type' in data:
            update_fields.append('race_type = %s')
            update_values.append(data['race_type'])
        if 'priority' in data:
            update_fields.append('priority = %s')
            update_values.append(new_priority)
        if 'target_time' in data:
            update_fields.append('target_time = %s')
            update_values.append(data['target_time'])
        if 'notes' in data:
            update_fields.append('notes = %s')
            update_values.append(data['notes'])
        if 'elevation_gain_feet' in data:
            update_fields.append('elevation_gain_feet = %s')
            update_values.append(data['elevation_gain_feet'])
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        update_fields.append('updated_at = NOW()')
        update_values.extend([goal_id, user_id])
        
        logger.info(f"Updating race goal {goal_id} for user {user_id}")
        
        # Execute update
        query = f"""
            UPDATE race_goals 
            SET {', '.join(update_fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, race_name, race_date, race_type, priority, target_time, notes, elevation_gain_feet, created_at, updated_at
        """
        
        result = db_utils.execute_query(query, tuple(update_values), fetch=True)
        
        if result and len(result) > 0:
            goal = result[0]
            goal_dict = dict(goal) if hasattr(goal, 'keys') else {
                'id': goal[0],
                'race_name': goal[1],
                'race_date': goal[2],
                'race_type': goal[3],
                'priority': goal[4],
                'target_time': goal[5],
                'notes': goal[6],
                'elevation_gain_feet': goal[7],
                'created_at': goal[8],
                'updated_at': goal[9]
            }
            
            # Serialize dates
            if isinstance(goal_dict.get('race_date'), date):
                goal_dict['race_date'] = goal_dict['race_date'].strftime('%Y-%m-%d')
            if isinstance(goal_dict.get('created_at'), datetime):
                goal_dict['created_at'] = goal_dict['created_at'].isoformat()
            if isinstance(goal_dict.get('updated_at'), datetime):
                goal_dict['updated_at'] = goal_dict['updated_at'].isoformat()
            
            logger.info(f"Successfully updated race goal {goal_id} for user {user_id}")
            
            return jsonify({
                'success': True,
                'race_goal': goal_dict
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update race goal'}), 500
            
    except Exception as e:
        logger.error(f"Error updating race goal {goal_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-goals/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_race_goal(goal_id):
    """Delete a race goal"""
    try:
        user_id = current_user.id
        
        logger.info(f"Deleting race goal {goal_id} for user {user_id}")
        
        # Delete with user_id filter for security
        result = db_utils.execute_query(
            "DELETE FROM race_goals WHERE id = %s AND user_id = %s RETURNING id",
            (goal_id, user_id),
            fetch=True
        )
        
        if result and len(result) > 0:
            logger.info(f"Successfully deleted race goal {goal_id} for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Race goal deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Race goal not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting race goal {goal_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-history', methods=['GET'])
@login_required
def get_race_history():
    """Get all race history for current user (last 5 years), ordered by date DESC"""
    try:
        user_id = current_user.id
        logger.info(f"Fetching race history for user {user_id}")
        
        # Query race history with 5-year filter (enforced by DB constraint)
        race_history = db_utils.execute_query(
            """
            SELECT id, user_id, race_date, race_name, distance_miles, 
                   finish_time_minutes, created_at, updated_at
            FROM race_history 
            WHERE user_id = %s 
              AND race_date >= CURRENT_DATE - INTERVAL '5 years'
            ORDER BY race_date DESC
            """,
            (user_id,),
            fetch=True
        )
        
        # Convert to list of dicts and serialize dates
        history_list = []
        if race_history:
            for race in race_history:
                race_dict = dict(race) if hasattr(race, 'keys') else {
                    'id': race[0],
                    'user_id': race[1],
                    'race_date': race[2],
                    'race_name': race[3],
                    'distance_miles': race[4],
                    'finish_time_minutes': race[5],
                    'created_at': race[6],
                    'updated_at': race[7]
                }
                
                # Serialize dates
                if isinstance(race_dict.get('race_date'), date):
                    race_dict['race_date'] = race_dict['race_date'].strftime('%Y-%m-%d')
                if isinstance(race_dict.get('created_at'), datetime):
                    race_dict['created_at'] = race_dict['created_at'].isoformat()
                if isinstance(race_dict.get('updated_at'), datetime):
                    race_dict['updated_at'] = race_dict['updated_at'].isoformat()
                    
                history_list.append(race_dict)
        
        logger.info(f"Found {len(history_list)} race history records for user {user_id}")
        
        return jsonify({
            'success': True,
            'race_history': history_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching race history for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-history', methods=['POST'])
@login_required
def create_race_history():
    """Create a new race history record"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Validate required fields
        race_name = data.get('race_name')
        race_date = data.get('race_date')
        distance_miles = data.get('distance_miles')
        finish_time_minutes = data.get('finish_time_minutes')
        
        if not race_name:
            return jsonify({'success': False, 'error': 'race_name is required'}), 400
        if not race_date:
            return jsonify({'success': False, 'error': 'race_date is required'}), 400
        if distance_miles is None:
            return jsonify({'success': False, 'error': 'distance_miles is required'}), 400
        if finish_time_minutes is None:
            return jsonify({'success': False, 'error': 'finish_time_minutes is required'}), 400
        
        # Validate distance and time are positive
        try:
            distance_miles = float(distance_miles)
            if distance_miles <= 0:
                return jsonify({'success': False, 'error': 'distance_miles must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'distance_miles must be a valid number'}), 400
        
        try:
            finish_time_minutes = int(finish_time_minutes)
            if finish_time_minutes <= 0:
                return jsonify({'success': False, 'error': 'finish_time_minutes must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'finish_time_minutes must be a valid integer'}), 400
        
        # Validate race_date is within last 5 years
        try:
            race_date_obj = datetime.strptime(race_date, '%Y-%m-%d').date()
            today = get_app_current_date()
            five_years_ago = today - timedelta(days=5*365)
            
            if race_date_obj < five_years_ago:
                return jsonify({
                    'success': False,
                    'error': 'Race date must be within the last 5 years'
                }), 400
            if race_date_obj > today:
                return jsonify({
                    'success': False,
                    'error': 'Race date cannot be in the future (use race goals for upcoming races)'
                }), 400
        except ValueError:
            return jsonify({'success': False, 'error': 'race_date must be in format YYYY-MM-DD'}), 400
        
        logger.info(f"Creating race history for user {user_id}: {race_name} ({distance_miles} mi)")
        
        # Insert new race history
        result = db_utils.execute_query(
            """
            INSERT INTO race_history 
                (user_id, race_date, race_name, distance_miles, finish_time_minutes, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING id, race_date, race_name, distance_miles, finish_time_minutes, created_at, updated_at
            """,
            (user_id, race_date, race_name, distance_miles, finish_time_minutes),
            fetch=True
        )
        
        if result and len(result) > 0:
            race = result[0]
            race_dict = dict(race) if hasattr(race, 'keys') else {
                'id': race[0],
                'race_date': race[1],
                'race_name': race[2],
                'distance_miles': race[3],
                'finish_time_minutes': race[4],
                'created_at': race[5],
                'updated_at': race[6]
            }
            
            # Serialize dates
            if isinstance(race_dict.get('race_date'), date):
                race_dict['race_date'] = race_dict['race_date'].strftime('%Y-%m-%d')
            if isinstance(race_dict.get('created_at'), datetime):
                race_dict['created_at'] = race_dict['created_at'].isoformat()
            if isinstance(race_dict.get('updated_at'), datetime):
                race_dict['updated_at'] = race_dict['updated_at'].isoformat()
            
            logger.info(f"Successfully created race history {race_dict['id']} for user {user_id}")
            
            return jsonify({
                'success': True,
                'race_history': race_dict
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to create race history'}), 500
            
    except Exception as e:
        logger.error(f"Error creating race history for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-history/bulk', methods=['POST'])
@login_required
def create_race_history_bulk():
    """Bulk insert multiple race history records (for screenshot parsing)"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Expect array of races
        races = data.get('races')
        if not races or not isinstance(races, list):
            return jsonify({'success': False, 'error': 'races array is required'}), 400
        
        if len(races) == 0:
            return jsonify({'success': False, 'error': 'races array cannot be empty'}), 400
        
        if len(races) > 100:
            return jsonify({'success': False, 'error': 'Cannot insert more than 100 races at once'}), 400
        
        logger.info(f"Bulk inserting {len(races)} race history records for user {user_id}")
        
        # Validate each race and prepare data
        validated_races = []
        errors = []
        
        for idx, race in enumerate(races):
            race_errors = []
            
            # Validate required fields
            race_name = race.get('race_name')
            race_date = race.get('race_date')
            distance_miles = race.get('distance_miles')
            finish_time_minutes = race.get('finish_time_minutes')
            
            if not race_name:
                race_errors.append(f'Race {idx+1}: race_name is required')
            if not race_date:
                race_errors.append(f'Race {idx+1}: race_date is required')
            if distance_miles is None:
                race_errors.append(f'Race {idx+1}: distance_miles is required')
            if finish_time_minutes is None:
                race_errors.append(f'Race {idx+1}: finish_time_minutes is required')
            
            # Validate types and values
            try:
                distance_miles = float(distance_miles)
                if distance_miles <= 0:
                    race_errors.append(f'Race {idx+1}: distance_miles must be greater than 0')
            except (ValueError, TypeError):
                race_errors.append(f'Race {idx+1}: distance_miles must be a valid number')
                distance_miles = None
            
            try:
                finish_time_minutes = int(finish_time_minutes)
                if finish_time_minutes <= 0:
                    race_errors.append(f'Race {idx+1}: finish_time_minutes must be greater than 0')
            except (ValueError, TypeError):
                race_errors.append(f'Race {idx+1}: finish_time_minutes must be a valid integer')
                finish_time_minutes = None
            
            # Validate date
            try:
                race_date_obj = datetime.strptime(race_date, '%Y-%m-%d').date()
                today = get_app_current_date()
                five_years_ago = today - timedelta(days=5*365)
                
                if race_date_obj < five_years_ago:
                    race_errors.append(f'Race {idx+1}: Race date must be within the last 5 years')
                if race_date_obj > today:
                    race_errors.append(f'Race {idx+1}: Race date cannot be in the future')
            except (ValueError, TypeError):
                race_errors.append(f'Race {idx+1}: race_date must be in format YYYY-MM-DD')
                race_date = None
            
            if race_errors:
                errors.extend(race_errors)
            else:
                validated_races.append((user_id, race_date, race_name, distance_miles, finish_time_minutes))
        
        # If there are validation errors, return them
        if errors:
            return jsonify({
                'success': False,
                'error': 'Validation errors',
                'details': errors
            }), 400
        
        # Bulk insert using executemany pattern
        inserted_count = 0
        try:
            conn = db_utils.get_db_connection()
            cursor = conn.cursor()
            
            cursor.executemany(
                """
                INSERT INTO race_history 
                    (user_id, race_date, race_name, distance_miles, finish_time_minutes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """,
                validated_races
            )
            
            inserted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Successfully bulk inserted {inserted_count} race history records for user {user_id}")
            
            return jsonify({
                'success': True,
                'message': f'Successfully inserted {inserted_count} races',
                'count': inserted_count
            }), 201
            
        except Exception as e:
            logger.error(f"Error during bulk insert for user {user_id}: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Database error during bulk insert: {str(e)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in bulk race history creation for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-history/<int:history_id>', methods=['PUT'])
@login_required
def update_race_history(history_id):
    """Update an existing race history record"""
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Verify race history belongs to current user
        existing_race = db_utils.execute_query(
            "SELECT id FROM race_history WHERE id = %s AND user_id = %s",
            (history_id, user_id),
            fetch=True
        )
        
        if not existing_race:
            return jsonify({'success': False, 'error': 'Race history record not found'}), 404
        
        # Build update query dynamically for provided fields
        update_fields = []
        update_values = []
        
        if 'race_name' in data:
            if not data['race_name']:
                return jsonify({'success': False, 'error': 'race_name cannot be empty'}), 400
            update_fields.append('race_name = %s')
            update_values.append(data['race_name'])
        
        if 'race_date' in data:
            # Validate date
            try:
                race_date_obj = datetime.strptime(data['race_date'], '%Y-%m-%d').date()
                today = get_app_current_date()
                five_years_ago = today - timedelta(days=5*365)
                
                if race_date_obj < five_years_ago:
                    return jsonify({'success': False, 'error': 'Race date must be within the last 5 years'}), 400
                if race_date_obj > today:
                    return jsonify({'success': False, 'error': 'Race date cannot be in the future'}), 400
                
                update_fields.append('race_date = %s')
                update_values.append(data['race_date'])
            except ValueError:
                return jsonify({'success': False, 'error': 'race_date must be in format YYYY-MM-DD'}), 400
        
        if 'distance_miles' in data:
            try:
                distance = float(data['distance_miles'])
                if distance <= 0:
                    return jsonify({'success': False, 'error': 'distance_miles must be greater than 0'}), 400
                update_fields.append('distance_miles = %s')
                update_values.append(distance)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'distance_miles must be a valid number'}), 400
        
        if 'finish_time_minutes' in data:
            try:
                finish_time = int(data['finish_time_minutes'])
                if finish_time <= 0:
                    return jsonify({'success': False, 'error': 'finish_time_minutes must be greater than 0'}), 400
                update_fields.append('finish_time_minutes = %s')
                update_values.append(finish_time)
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'finish_time_minutes must be a valid integer'}), 400
        
        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        update_fields.append('updated_at = NOW()')
        update_values.extend([history_id, user_id])
        
        logger.info(f"Updating race history {history_id} for user {user_id}")
        
        # Execute update
        query = f"""
            UPDATE race_history 
            SET {', '.join(update_fields)}
            WHERE id = %s AND user_id = %s
            RETURNING id, race_date, race_name, distance_miles, finish_time_minutes, created_at, updated_at
        """
        
        result = db_utils.execute_query(query, tuple(update_values), fetch=True)
        
        if result and len(result) > 0:
            race = result[0]
            race_dict = dict(race) if hasattr(race, 'keys') else {
                'id': race[0],
                'race_date': race[1],
                'race_name': race[2],
                'distance_miles': race[3],
                'finish_time_minutes': race[4],
                'created_at': race[5],
                'updated_at': race[6]
            }
            
            # Serialize dates
            if isinstance(race_dict.get('race_date'), date):
                race_dict['race_date'] = race_dict['race_date'].strftime('%Y-%m-%d')
            if isinstance(race_dict.get('created_at'), datetime):
                race_dict['created_at'] = race_dict['created_at'].isoformat()
            if isinstance(race_dict.get('updated_at'), datetime):
                race_dict['updated_at'] = race_dict['updated_at'].isoformat()
            
            logger.info(f"Successfully updated race history {history_id} for user {user_id}")
            
            return jsonify({
                'success': True,
                'race_history': race_dict
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to update race history'}), 500
            
    except Exception as e:
        logger.error(f"Error updating race history {history_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-history/<int:history_id>', methods=['DELETE'])
@login_required
def delete_race_history(history_id):
    """Delete a race history record"""
    try:
        user_id = current_user.id
        
        logger.info(f"Deleting race history {history_id} for user {user_id}")
        
        # Delete with user_id filter for security
        result = db_utils.execute_query(
            "DELETE FROM race_history WHERE id = %s AND user_id = %s RETURNING id",
            (history_id, user_id),
            fetch=True
        )
        
        if result and len(result) > 0:
            logger.info(f"Successfully deleted race history {history_id} for user {user_id}")
            return jsonify({
                'success': True,
                'message': 'Race history deleted successfully'
            })
        else:
            return jsonify({'success': False, 'error': 'Race history record not found'}), 404
            
    except Exception as e:
        logger.error(f"Error deleting race history {history_id} for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-history/screenshot', methods=['POST'])
@login_required
def upload_race_history_screenshot():
    """
    Upload and parse ultrasignup.com screenshot to extract race history
    Returns extracted races for user review before saving
    """
    try:
        user_id = current_user.id
        
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Read file data
        file_data = file.read()
        filename = file.filename
        
        logger.info(f"Processing screenshot upload for user {user_id}: {filename} ({len(file_data)} bytes)")
        
        # Import parser (lazy import to avoid startup issues if anthropic not installed)
        try:
            from ultrasignup_parser import parse_ultrasignup_screenshot
        except ImportError as e:
            logger.error(f"Failed to import ultrasignup_parser: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Screenshot parsing feature is not available. Please contact support.'
            }), 500
        
        # Parse screenshot
        result = parse_ultrasignup_screenshot(file_data, filename)
        
        if not result['success']:
            return jsonify(result), 400
        
        # Log API usage and cost
        api_cost = result.get('api_cost_estimate', 0)
        logger.info(f"Screenshot parsed for user {user_id}: {result['total_valid']} valid races extracted (estimated cost: ${api_cost:.2f})")
        
        # Return extracted races for user review
        return jsonify({
            'success': True,
            'races': result['races'],
            'total_extracted': result.get('total_extracted', len(result['races'])),
            'total_valid': result.get('total_valid', len(result['races'])),
            'warnings': result.get('warnings', []),
            'message': f"Extracted {len(result['races'])} race(s) from screenshot. Please review and edit before saving."
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing screenshot upload for user {current_user.id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Error processing screenshot: {str(e)}'
        }), 500


@app.route('/api/coach/training-schedule', methods=['GET'])
@login_required
def get_training_schedule():
    """
    Get user's training schedule and availability configuration
    Returns training_schedule_json and supplemental training preferences
    """
    try:
        user_id = current_user.id
        logger.info(f"Fetching training schedule for user {user_id}")
        
        # Query user_settings for schedule data
        user_settings = db_utils.execute_query(
            """
            SELECT training_schedule_json, 
                   include_strength_training, strength_hours_per_week,
                   include_mobility, mobility_hours_per_week,
                   include_cross_training, cross_training_type, cross_training_hours_per_week,
                   schedule_last_updated
            FROM user_settings
            WHERE id = %s
            """,
            (user_id,),
            fetch=True
        )
        
        if not user_settings or len(user_settings) == 0:
            return jsonify({'success': False, 'error': 'User settings not found'}), 404
        
        settings = user_settings[0]
        settings_dict = dict(settings) if hasattr(settings, 'keys') else {
            'training_schedule_json': settings[0],
            'include_strength_training': settings[1],
            'strength_hours_per_week': settings[2],
            'include_mobility': settings[3],
            'mobility_hours_per_week': settings[4],
            'include_cross_training': settings[5],
            'cross_training_type': settings[6],
            'cross_training_hours_per_week': settings[7],
            'schedule_last_updated': settings[8]
        }
        
        # Get training schedule JSON or return defaults
        schedule_json = settings_dict.get('training_schedule_json')
        
        if not schedule_json:
            # Generate default schedule (5 days/week, morning and evening availability)
            logger.info(f"No schedule configured for user {user_id}, returning defaults")
            schedule_json = {
                'available_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'saturday', 'sunday'],
                'time_blocks': {
                    'monday': ['morning', 'evening'],
                    'tuesday': ['morning', 'evening'],
                    'wednesday': ['morning', 'evening'],
                    'thursday': ['morning', 'evening'],
                    'saturday': ['morning'],
                    'sunday': ['morning']
                },
                'constraints': []
            }
            is_default = True
        else:
            is_default = False
        
        # Serialize timestamp if present
        schedule_last_updated = settings_dict.get('schedule_last_updated')
        if isinstance(schedule_last_updated, datetime):
            schedule_last_updated = schedule_last_updated.isoformat()
        
        return jsonify({
            'success': True,
            'training_schedule': schedule_json,
            'include_strength_training': settings_dict.get('include_strength_training', False),
            'strength_hours_per_week': float(settings_dict.get('strength_hours_per_week', 0)) if settings_dict.get('strength_hours_per_week') else 0,
            'include_mobility': settings_dict.get('include_mobility', False),
            'mobility_hours_per_week': float(settings_dict.get('mobility_hours_per_week', 0)) if settings_dict.get('mobility_hours_per_week') else 0,
            'include_cross_training': settings_dict.get('include_cross_training', False),
            'cross_training_type': settings_dict.get('cross_training_type'),
            'cross_training_hours_per_week': float(settings_dict.get('cross_training_hours_per_week', 0)) if settings_dict.get('cross_training_hours_per_week') else 0,
            'schedule_last_updated': schedule_last_updated,
            'is_default': is_default
        })
        
    except Exception as e:
        logger.error(f"Error fetching training schedule for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/training-schedule', methods=['POST'])
@login_required
def save_training_schedule():
    """
    Save user's training schedule and availability configuration
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Extract training schedule
        training_schedule = data.get('training_schedule')
        if not training_schedule:
            return jsonify({'success': False, 'error': 'training_schedule is required'}), 400
        
        # Validate training schedule structure
        is_valid, error_message = _validate_training_schedule(training_schedule)
        if not is_valid:
            return jsonify({'success': False, 'error': error_message}), 400
        
        # Extract supplemental training preferences
        include_strength = data.get('include_strength_training', False)
        strength_hours = data.get('strength_hours_per_week', 0)
        include_mobility = data.get('include_mobility', False)
        mobility_hours = data.get('mobility_hours_per_week', 0)
        include_cross_training = data.get('include_cross_training', False)
        cross_training_type = data.get('cross_training_type')
        cross_training_hours = data.get('cross_training_hours_per_week', 0)
        
        # Validate hours are non-negative
        try:
            strength_hours = float(strength_hours) if strength_hours else 0
            mobility_hours = float(mobility_hours) if mobility_hours else 0
            cross_training_hours = float(cross_training_hours) if cross_training_hours else 0
            
            if strength_hours < 0 or mobility_hours < 0 or cross_training_hours < 0:
                return jsonify({'success': False, 'error': 'Hours must be non-negative'}), 400
            
            if strength_hours > 40 or mobility_hours > 40 or cross_training_hours > 40:
                return jsonify({'success': False, 'error': 'Hours per week must be reasonable (<40)'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Hours must be valid numbers'}), 400
        
        logger.info(f"Saving training schedule for user {user_id}")
        
        # Convert training_schedule dict to JSON string for JSONB storage
        import json
        schedule_json_str = json.dumps(training_schedule)
        
        # Update user_settings
        db_utils.execute_query(
            """
            UPDATE user_settings
            SET training_schedule_json = %s,
                include_strength_training = %s,
                strength_hours_per_week = %s,
                include_mobility = %s,
                mobility_hours_per_week = %s,
                include_cross_training = %s,
                cross_training_type = %s,
                cross_training_hours_per_week = %s,
                schedule_last_updated = NOW()
            WHERE id = %s
            """,
            (schedule_json_str, include_strength, strength_hours, include_mobility, 
             mobility_hours, include_cross_training, cross_training_type, 
             cross_training_hours, user_id),
            fetch=False
        )
        
        logger.info(f"Successfully saved training schedule for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Training schedule saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving training schedule for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _calculate_training_stage(a_race_date: date, current_date: date) -> dict:
    """
    Calculate training stage based on weeks until A race
    
    Args:
        a_race_date: Date of A race
        current_date: Current date
        
    Returns:
        Dictionary with stage info: stage, week_number, total_weeks, weeks_remaining, days_until_race
    """
    days_until_race = (a_race_date - current_date).days
    weeks_until_race = days_until_race / 7.0
    
    # Determine training stage based on weeks until race
    if days_until_race < 0:
        # Race has passed - recovery phase
        stage = 'recovery'
        stage_description = 'Post-race recovery'
    elif weeks_until_race < 2:
        # 0-2 weeks: Peak week
        stage = 'peak'
        stage_description = 'Peak week - race ready'
    elif weeks_until_race < 4:
        # 2-4 weeks: Taper
        stage = 'taper'
        stage_description = 'Taper - reducing volume'
    elif weeks_until_race < 8:
        # 4-8 weeks: Specificity (Race-specific preparation)
        stage = 'specificity'
        stage_description = 'Race-specific training'
    elif weeks_until_race < 12:
        # 8-12 weeks: Build phase
        stage = 'build'
        stage_description = 'Building fitness and volume'
    else:
        # 12+ weeks: Base building
        stage = 'base'
        stage_description = 'Base building phase'
    
    # Calculate week number in training cycle (assume 16-week cycle for most ultras)
    # Adjust based on actual race date
    if weeks_until_race > 16:
        total_weeks = int(weeks_until_race)
        week_number = 1
    else:
        total_weeks = 16
        week_number = int(16 - weeks_until_race) + 1
    
    return {
        'stage': stage,
        'stage_description': stage_description,
        'week_number': week_number,
        'total_weeks': total_weeks,
        'weeks_until_race': round(weeks_until_race, 1),
        'days_until_race': days_until_race
    }


def _generate_timeline_data(a_race, b_races, c_races, current_date: date) -> list:
    """
    Generate week-by-week timeline data with training stages and race markers
    
    Args:
        a_race: Primary A race goal (dict with race_date)
        b_races: List of B race goals
        c_races: List of C race goals
        current_date: Current date
        
    Returns:
        List of week objects with: week_start, week_end, stage, is_current_week, races
    """
    if not a_race:
        return []
    
    a_race_date = a_race['race_date']
    if isinstance(a_race_date, str):
        a_race_date = datetime.strptime(a_race_date, '%Y-%m-%d').date()
    
    # Generate timeline from now until race date (or 4 weeks past if race has passed)
    if a_race_date < current_date:
        end_date = current_date + timedelta(weeks=4)
    else:
        end_date = a_race_date
    
    # Start from current week (Monday)
    start_date = current_date - timedelta(days=current_date.weekday())
    
    timeline = []
    current_week_start = start_date
    
    # Generate weeks
    while current_week_start <= end_date:
        week_end = current_week_start + timedelta(days=6)
        
        # Calculate stage for this week
        stage_info = _calculate_training_stage(a_race_date, current_week_start)
        
        # Check if current week
        is_current_week = current_date >= current_week_start and current_date <= week_end
        
        # Find races in this week
        races_this_week = []
        
        # Check A race
        if current_week_start <= a_race_date <= week_end:
            races_this_week.append({
                'priority': 'A',
                'race_name': a_race['race_name'],
                'race_date': a_race_date.strftime('%Y-%m-%d'),
                'race_type': a_race.get('race_type')
            })
        
        # Check B races
        for b_race in b_races:
            b_race_date = b_race['race_date']
            if isinstance(b_race_date, str):
                b_race_date = datetime.strptime(b_race_date, '%Y-%m-%d').date()
            if current_week_start <= b_race_date <= week_end:
                races_this_week.append({
                    'priority': 'B',
                    'race_name': b_race['race_name'],
                    'race_date': b_race_date.strftime('%Y-%m-%d'),
                    'race_type': b_race.get('race_type')
                })
        
        # Check C races
        for c_race in c_races:
            c_race_date = c_race['race_date']
            if isinstance(c_race_date, str):
                c_race_date = datetime.strptime(c_race_date, '%Y-%m-%d').date()
            if current_week_start <= c_race_date <= week_end:
                races_this_week.append({
                    'priority': 'C',
                    'race_name': c_race['race_name'],
                    'race_date': c_race_date.strftime('%Y-%m-%d'),
                    'race_type': c_race.get('race_type')
                })
        
        timeline.append({
            'week_start': current_week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'stage': stage_info['stage'],
            'stage_description': stage_info['stage_description'],
            'is_current_week': is_current_week,
            'races': races_this_week
        })
        
        current_week_start += timedelta(weeks=1)
    
    return timeline


def _validate_training_schedule(schedule: dict) -> tuple:
    """
    Validate training schedule JSON structure
    
    Args:
        schedule: Training schedule dictionary
        
    Returns:
        (is_valid, error_message) - error_message is None if valid
    """
    # Check required keys
    required_keys = ['available_days', 'time_blocks', 'constraints']
    for key in required_keys:
        if key not in schedule:
            return False, f"Missing required field: {key}"
    
    # Validate available_days
    available_days = schedule['available_days']
    if not isinstance(available_days, list):
        return False, "available_days must be an array"
    
    valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    for day in available_days:
        if not isinstance(day, str):
            return False, "available_days must contain strings"
        if day.lower() not in valid_days:
            return False, f"Invalid day name: {day}. Must be one of: {', '.join(valid_days)}"
    
    if len(available_days) == 0:
        return False, "At least one day must be available"
    
    # Validate time_blocks
    time_blocks = schedule['time_blocks']
    if not isinstance(time_blocks, dict):
        return False, "time_blocks must be an object"
    
    valid_time_blocks = ['morning', 'midday', 'evening', 'night']
    for day, blocks in time_blocks.items():
        if day.lower() not in valid_days:
            return False, f"Invalid day in time_blocks: {day}"
        if not isinstance(blocks, list):
            return False, f"time_blocks for {day} must be an array"
        for block in blocks:
            if not isinstance(block, str):
                return False, f"time_blocks for {day} must contain strings"
            if block.lower() not in valid_time_blocks:
                return False, f"Invalid time block '{block}' for {day}. Must be one of: {', '.join(valid_time_blocks)}"
    
    # Validate constraints
    constraints = schedule['constraints']
    if not isinstance(constraints, list):
        return False, "constraints must be an array"
    
    for idx, constraint in enumerate(constraints):
        if not isinstance(constraint, dict):
            return False, f"Constraint {idx + 1} must be an object"
        # Constraints can have any structure, but if they have type/description, validate
        if 'type' in constraint and not isinstance(constraint['type'], str):
            return False, f"Constraint {idx + 1} type must be a string"
        if 'description' in constraint and not isinstance(constraint['description'], str):
            return False, f"Constraint {idx + 1} description must be a string"
    
    return True, None


@app.route('/api/coach/training-stage', methods=['GET'])
@login_required
def get_training_stage():
    """
    Get current training stage and timeline based on race goals
    Returns stage info, timeline data, and race markers
    """
    try:
        user_id = current_user.id
        logger.info(f"Fetching training stage for user {user_id}")
        
        # Get current date
        current_date = get_app_current_date()
        
        # Fetch all race goals
        race_goals = db_utils.execute_query(
            """
            SELECT id, race_name, race_date, race_type, priority, target_time
            FROM race_goals 
            WHERE user_id = %s 
            ORDER BY race_date ASC
            """,
            (user_id,),
            fetch=True
        )
        
        if not race_goals or len(race_goals) == 0:
            return jsonify({
                'success': True,
                'has_race_goals': False,
                'message': 'No race goals configured. Add your A race to see your training stage.',
                'current_stage': None,
                'timeline': []
            })
        
        # Convert to list of dicts
        goals_list = []
        for goal in race_goals:
            goal_dict = dict(goal) if hasattr(goal, 'keys') else {
                'id': goal[0],
                'race_name': goal[1],
                'race_date': goal[2],
                'race_type': goal[3],
                'priority': goal[4],
                'target_time': goal[5]
            }
            # Serialize date
            if isinstance(goal_dict['race_date'], date):
                goal_dict['race_date'] = goal_dict['race_date'].strftime('%Y-%m-%d')
            goals_list.append(goal_dict)
        
        # Find A race
        a_race = next((g for g in goals_list if g['priority'] == 'A'), None)
        
        if not a_race:
            return jsonify({
                'success': True,
                'has_race_goals': True,
                'has_a_race': False,
                'message': 'No A race configured. Set one race as your primary goal to see your training stage.',
                'current_stage': None,
                'timeline': [],
                'race_goals': goals_list
            })
        
        # Parse A race date
        a_race_date = datetime.strptime(a_race['race_date'], '%Y-%m-%d').date()
        
        # Check for manual override
        user_settings = db_utils.execute_query(
            "SELECT manual_training_stage FROM user_settings WHERE id = %s",
            (user_id,),
            fetch=True
        )
        
        manual_override = None
        if user_settings and len(user_settings) > 0:
            manual_override = user_settings[0]['manual_training_stage'] if hasattr(user_settings[0], 'keys') else user_settings[0][0]
        
        # Calculate training stage
        stage_info = _calculate_training_stage(a_race_date, current_date)
        
        # Apply manual override if exists
        if manual_override:
            stage_info['stage'] = manual_override
            stage_info['stage_description'] = f"{manual_override.capitalize()} (manual override)"
            stage_info['is_manual_override'] = True
        else:
            stage_info['is_manual_override'] = False
        
        # Separate B and C races
        b_races = [g for g in goals_list if g['priority'] == 'B']
        c_races = [g for g in goals_list if g['priority'] == 'C']
        
        # Generate timeline
        timeline = _generate_timeline_data(a_race, b_races, c_races, current_date)
        
        logger.info(f"Training stage for user {user_id}: {stage_info['stage']}, {stage_info['days_until_race']} days until A race")
        
        return jsonify({
            'success': True,
            'has_race_goals': True,
            'has_a_race': True,
            'current_stage': stage_info,
            'timeline': timeline,
            'a_race': a_race,
            'b_races': b_races,
            'c_races': c_races,
            'race_goals': goals_list
        })
        
    except Exception as e:
        logger.error(f"Error fetching training stage for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/training-stage/override', methods=['POST'])
@login_required
def set_training_stage_override():
    """
    Manually override the calculated training stage
    """
    try:
        user_id = current_user.id
        data = request.get_json()
        
        # Get override stage (or null to remove override)
        override_stage = data.get('stage')
        
        valid_stages = ['base', 'build', 'specificity', 'taper', 'peak', 'recovery', None]
        
        if override_stage not in valid_stages:
            return jsonify({
                'success': False,
                'error': f'Invalid stage. Must be one of: {", ".join([s for s in valid_stages if s])}, or null to remove override'
            }), 400
        
        logger.info(f"Setting training stage override for user {user_id}: {override_stage}")
        
        # Update user_settings
        db_utils.execute_query(
            "UPDATE user_settings SET manual_training_stage = %s WHERE id = %s",
            (override_stage, user_id),
            fetch=False
        )
        
        if override_stage:
            message = f'Training stage manually set to: {override_stage}'
        else:
            message = 'Training stage override removed. Using calculated stage.'
        
        return jsonify({
            'success': True,
            'message': message,
            'override_stage': override_stage
        })
        
    except Exception as e:
        logger.error(f"Error setting training stage override for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/coach/race-analysis', methods=['GET'])
@login_required
def get_race_analysis():
    """
    Calculate and return race analysis:
    - Personal Records (PRs) at each distance
    - Performance trend (improving/stable/declining)
    - Base fitness assessment
    """
    try:
        user_id = current_user.id
        logger.info(f"Calculating race analysis for user {user_id}")
        
        # Fetch all race history
        race_history = db_utils.execute_query(
            """
            SELECT race_date, race_name, distance_miles, finish_time_minutes
            FROM race_history 
            WHERE user_id = %s 
              AND race_date >= CURRENT_DATE - INTERVAL '5 years'
            ORDER BY race_date DESC
            """,
            (user_id,),
            fetch=True
        )
        
        if not race_history or len(race_history) == 0:
            return jsonify({
                'success': True,
                'prs': [],
                'trend': 'no_data',
                'trend_description': 'No race history available',
                'base_fitness': 'No race history to analyze',
                'total_races': 0
            })
        
        # Convert to list of dicts
        races = []
        for race in race_history:
            race_dict = dict(race) if hasattr(race, 'keys') else {
                'race_date': race[0],
                'race_name': race[1],
                'distance_miles': race[2],
                'finish_time_minutes': race[3]
            }
            # Convert date to datetime for easier manipulation
            if isinstance(race_dict['race_date'], date):
                race_dict['race_date'] = race_dict['race_date']
            races.append(race_dict)
        
        # Calculate PRs at each distance
        prs_by_distance = {}
        for race in races:
            distance = float(race['distance_miles'])
            finish_time = int(race['finish_time_minutes'])
            
            # Round distance to nearest common race distance for grouping
            # Common distances: 5K (3.1), 10K (6.2), Half (13.1), Marathon (26.2), 50K (31), 50M (50), 100K (62), 100M (100)
            if distance < 4:  # ~5K
                distance_key = 3.1
            elif distance < 8:  # ~10K
                distance_key = 6.2
            elif distance < 16:  # ~Half Marathon
                distance_key = 13.1
            elif distance < 30:  # ~Marathon
                distance_key = 26.2
            elif distance < 40:  # ~50K
                distance_key = 31.0
            elif distance < 56:  # ~50 Mile
                distance_key = 50.0
            elif distance < 75:  # ~100K
                distance_key = 62.0
            else:  # ~100 Mile
                distance_key = 100.0
            
            if distance_key not in prs_by_distance or finish_time < prs_by_distance[distance_key]['finish_time_minutes']:
                prs_by_distance[distance_key] = {
                    'distance_miles': distance_key,
                    'finish_time_minutes': finish_time,
                    'race_name': race['race_name'],
                    'race_date': race['race_date'].strftime('%Y-%m-%d') if isinstance(race['race_date'], date) else race['race_date']
                }
        
        # Convert to list
        prs = list(prs_by_distance.values())
        prs.sort(key=lambda x: x['distance_miles'])
        
        # Calculate performance trend
        trend, trend_description = _calculate_performance_trend(races)
        
        # Assess base fitness
        base_fitness_assessment = _assess_base_fitness(races)
        
        logger.info(f"Race analysis for user {user_id}: {len(prs)} PRs, trend: {trend}")
        
        return jsonify({
            'success': True,
            'prs': prs,
            'trend': trend,
            'trend_description': trend_description,
            'base_fitness': base_fitness_assessment,
            'total_races': len(races)
        })
        
    except Exception as e:
        logger.error(f"Error calculating race analysis for user {current_user.id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _calculate_performance_trend(races):
    """
    Calculate performance trend by comparing recent races to older races
    Returns: (trend_status, trend_description)
    """
    if len(races) < 2:
        return 'no_data', 'Not enough race data to determine trend (need at least 2 races)'
    
    today = get_app_current_date()
    
    # Split races into recent (last 12 months) and older (12-24 months ago)
    recent_races = []
    older_races = []
    
    for race in races:
        days_ago = (today - race['race_date']).days
        if days_ago <= 365:
            recent_races.append(race)
        elif days_ago <= 730:
            older_races.append(race)
    
    if len(recent_races) == 0:
        return 'no_recent_data', 'No races in the last 12 months'
    
    if len(older_races) == 0:
        return 'insufficient_history', 'Not enough historical data to determine trend'
    
    # Calculate average pace (min/mile) for similar distances
    # Group races by similar distance and compare
    improvements = 0
    declines = 0
    comparisons = 0
    
    for recent_race in recent_races:
        recent_distance = recent_race['distance_miles']
        recent_pace = recent_race['finish_time_minutes'] / recent_distance
        
        # Find similar distance races in older period (within 20% of distance)
        similar_older_races = [
            r for r in older_races
            if abs(r['distance_miles'] - recent_distance) / recent_distance <= 0.2
        ]
        
        if similar_older_races:
            # Compare to best older pace at similar distance
            best_older_pace = min(r['finish_time_minutes'] / r['distance_miles'] for r in similar_older_races)
            
            pace_improvement = (best_older_pace - recent_pace) / best_older_pace
            
            if pace_improvement > 0.02:  # >2% improvement
                improvements += 1
            elif pace_improvement < -0.02:  # >2% decline
                declines += 1
            
            comparisons += 1
    
    if comparisons == 0:
        return 'insufficient_comparable_data', 'Not enough comparable races to determine trend'
    
    # Determine overall trend
    improvement_ratio = improvements / comparisons
    decline_ratio = declines / comparisons
    
    if improvement_ratio > 0.6:
        return 'improving', f'Improving performance: {improvements} of {comparisons} comparable races show improvement'
    elif decline_ratio > 0.6:
        return 'declining', f'Declining performance: {declines} of {comparisons} comparable races show decline'
    else:
        return 'stable', f'Stable performance: {comparisons} comparable races analyzed'


def _assess_base_fitness(races):
    """
    Assess base fitness from race history
    Returns: fitness assessment string
    """
    if len(races) == 0:
        return 'No race history to analyze'
    
    # Get maximum distance completed
    max_distance = max(race['distance_miles'] for race in races)
    
    # Count races in last year
    today = get_app_current_date()
    races_last_year = len([r for r in races if (today - r['race_date']).days <= 365])
    
    # Count ultra-distance races (> 26.2 miles)
    ultra_races = len([r for r in races if r['distance_miles'] > 26.2])
    
    # Build assessment
    assessment_parts = []
    
    if max_distance >= 100:
        assessment_parts.append('100-mile+ endurance capability')
    elif max_distance >= 62:
        assessment_parts.append('100K endurance capability')
    elif max_distance >= 50:
        assessment_parts.append('50-mile endurance capability')
    elif max_distance >= 31:
        assessment_parts.append('50K endurance capability')
    elif max_distance >= 26.2:
        assessment_parts.append('Marathon endurance capability')
    else:
        assessment_parts.append(f'{max_distance:.1f}-mile maximum distance')
    
    if races_last_year >= 10:
        assessment_parts.append(f'high race frequency ({races_last_year} races/year)')
    elif races_last_year >= 5:
        assessment_parts.append(f'moderate race frequency ({races_last_year} races/year)')
    elif races_last_year > 0:
        assessment_parts.append(f'low race frequency ({races_last_year} races/year)')
    
    if ultra_races >= 5:
        assessment_parts.append(f'experienced ultra runner ({ultra_races} ultras)')
    elif ultra_races > 0:
        assessment_parts.append(f'developing ultra runner ({ultra_races} ultras)')
    
    return '; '.join(assessment_parts)


@app.route('/api/coach/weekly-program', methods=['GET'])
@login_required
def get_weekly_program():
    """
    Get weekly training program (from cache or generate new).
    Query params:
        - week_start: YYYY-MM-DD (defaults to next Monday)
        - force: 'true' to force regeneration
    """
    from coach_recommendations import get_or_generate_weekly_program
    from datetime import datetime, timedelta
    
    try:
        user_id = current_user.id
        
        # Parse query params
        week_start_str = request.args.get('week_start')
        force = request.args.get('force', 'false').lower() == 'true'
        
        # Parse week_start if provided
        week_start = None
        if week_start_str:
            try:
                week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get or generate program
        program = get_or_generate_weekly_program(
            user_id=user_id,
            week_start=week_start,
            force_regenerate=force
        )
        
        return jsonify({
            'success': True,
            'program': program,
            'from_cache': program.get('from_cache', False)
        })
        
    except Exception as e:
        logger.error(f"Error getting weekly program: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/coach/weekly-program/generate', methods=['POST'])
@login_required
def generate_weekly_program_manual():
    """
    Manually generate/regenerate weekly training program.
    Body: { "week_start": "YYYY-MM-DD" } (optional)
    """
    from coach_recommendations import generate_weekly_program, save_weekly_program
    from datetime import datetime
    
    try:
        user_id = current_user.id
        data = request.get_json() or {}
        
        # Parse week_start if provided
        week_start = None
        if 'week_start' in data:
            try:
                week_start = datetime.strptime(data['week_start'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Generate program
        program = generate_weekly_program(user_id=user_id, target_week_start=week_start)
        
        # Save to database
        if not week_start:
            # Calculate week_start from program
            week_start = datetime.strptime(program['week_start_date'], '%Y-%m-%d').date()
        
        save_weekly_program(
            user_id=user_id,
            week_start=week_start,
            program_data=program,
            generation_type='manual'
        )
        
        return jsonify({
            'success': True,
            'program': program,
            'message': 'Weekly program generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error generating weekly program: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# =============================================================================
# CATCH-ALL ROUTE FOR REACT CLIENT-SIDE ROUTING
# =============================================================================
# This MUST be the last route to handle React Router paths like /journal, /activities, etc.

@app.route('/<path:path>')
def catch_all(path):
    """
    Catch-all route for React client-side routing.
    Serves index.html for unmatched routes so React Router can handle them.
    CRITICAL: Must be last route to avoid overriding API/static routes.
    """
    # If path starts with 'api/' or is a known file extension, return 404
    if path.startswith('api/') or '.' in path.split('/')[-1]:
        return '', 404
    
    # Serve index.html for React client-side routes (journal, activities, guide, etc.)
    response = send_from_directory('build', 'index.html')
    # CRITICAL: Prevent caching of index.html so users always get latest JS file references
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    # For local testing
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting Strava Sync Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)