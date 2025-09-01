# db_utils.py

import sqlite3
import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging # <--- Ensure this line is at the very top of your db_utils.py
import re # Make sure re is imported for the regex parsing

# Configure logger for db_utils.py
logger = logging.getLogger(__name__) # <--- Ensure this line is here, after import logging

def clean_database_url(url):
    """Clean database URL by removing Windows line endings and whitespace"""
    if not url:
        return url

    # Remove carriage returns, line feeds, and extra whitespace
    cleaned = url.replace('\r', '').replace('\n', '').strip()

    # Log the cleaning for debugging
    if cleaned != url:
        print(f"Cleaned DATABASE_URL: removed {len(url) - len(cleaned)} unwanted characters")
        logger.info(f"db_utils: Cleaned DATABASE_URL, removed {len(url) - len(cleaned)} characters")

    return cleaned

# Database configuration - supports both SQLite (local) and PostgreSQL (cloud)
DATABASE_URL = clean_database_url(os.environ.get('DATABASE_URL'))  # PostgreSQL connection string for cloud
DB_FILE = os.environ.get('DB_PATH', '../training_data.db')  # SQLite file for local

# Determine which database to use
USE_POSTGRES = DATABASE_URL is not None

# Import psycopg2 only if we're using PostgreSQL
if USE_POSTGRES:
    try:
        import psycopg2
        import psycopg2.extras

        print(f"Using PostgreSQL with connection: {DATABASE_URL[:50]}...")
        logger.info(f"db_utils: Attempting to use PostgreSQL. URL: {DATABASE_URL[:50]}...") # Added logging
    except ImportError:
        print("psycopg2 not available, falling back to SQLite")
        logger.warning("db_utils: psycopg2 not available, falling back to SQLite.") # Added logging
        USE_POSTGRES = False
else:
    logger.info("db_utils: Using SQLite database.") # Added logging for SQLite

def configure_database(custom_path=None):
    """Configure the database path, allowing for runtime configuration"""
    global DB_FILE
    old_path = DB_FILE
    if custom_path and not USE_POSTGRES:
        DB_FILE = custom_path
        print(f"Database path changed from {old_path} to {DB_FILE}")
        logger.info(f"db_utils: Database path changed from {old_path} to {DB_FILE}") # Added logging
    return DB_FILE


@contextmanager
def get_db_connection():
    """Context manager for database connections - supports both SQLite and PostgreSQL."""
    conn = None
    try:
        if USE_POSTGRES:
            print("Attempting PostgreSQL connection...")
            print(f"DATABASE_URL: {DATABASE_URL[:80]}...") #
            logger.info("db_utils: Attempting PostgreSQL connection within context manager.") # Added logging
            logger.info(f"db_utils: DATABASE_URL: {DATABASE_URL[:80]}...") # Added logging

            # For Cloud SQL, use a simpler approach
            if '/cloudsql/' in DATABASE_URL: #
                # Parse the connection string for Cloud SQL
                # Format: postgresql://user:pass@host/db?host=/cloudsql/project:region:instance
                pattern = r'postgresql://([^:]+):([^@]+)@[^/]*/([^?]+)\?host=([^&]+)' #
                match = re.match(pattern, DATABASE_URL) #

                if match: #
                    username, password, database, socket_dir = match.groups() #

                    print(f"Connecting to Cloud SQL:") #
                    print(f"  Username: {username}") #
                    print(f"  Database: {database}") #
                    print(f"  Socket directory: {socket_dir}") #
                    logger.info(f"db_utils: Connecting to Cloud SQL with socket: {socket_dir}") # Added logging

                    # Connect using the socket directory
                    conn = psycopg2.connect( #
                        host=socket_dir,
                        database=database,
                        user=username,
                        password=password
                    )
                else:
                    print("Could not parse Cloud SQL connection string, trying direct connection") #
                    logger.warning("db_utils: Could not parse Cloud SQL connection string, trying direct connection.") # Added logging
                    conn = psycopg2.connect(DATABASE_URL) #
            else:
                # Standard PostgreSQL connection
                print("Using standard PostgreSQL connection") #
                logger.info("db_utils: Using standard PostgreSQL connection.") # Added logging
                conn = psycopg2.connect(DATABASE_URL) #

            # Use RealDictCursor to get dictionary-like row access
            conn.cursor_factory = psycopg2.extras.RealDictCursor #
            print("PostgreSQL connection successful") #
            logger.info("db_utils: PostgreSQL connection successful!") # Added logging

        else:
            # SQLite connection for local development
            print("Using SQLite connection") #
            logger.info(f"db_utils: Using SQLite connection to {DB_FILE}.") # Added logging
            conn = sqlite3.connect(DB_FILE) #
            conn.row_factory = sqlite3.Row  # Allows column access by name

        yield conn #

    except Exception as e:
        error_msg = f"Database connection error: {str(e)}"
        print(error_msg) #
        logger.error(f"db_utils: {error_msg}", exc_info=True) # Added detailed logging
        if conn: #
            conn.rollback() #
        raise #

    finally:
        if conn: #
            conn.close() #
            logger.info("db_utils: Database connection closed.") # Added logging


def execute_query(query, params=(), fetch=False):
    """Execute a database query with optional parameter binding."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute("SET search_path TO public;")  # Explicitly set search path

            # Convert SQLite-style queries to PostgreSQL if needed
            if USE_POSTGRES:
            # Convert ? placeholders to %s for PostgreSQL
                if '?' in query:
                    # Count the number of ? to ensure we have the right number of %s
                    param_count = query.count('?')
                    query = query.replace('?', '%s')
                    logger.debug(f"db_utils: Converted {param_count} placeholders for PostgreSQL")

            logger.debug(f"db_utils: Executing: {query}")
            logger.debug(f"db_utils: Parameters: {params}")

            cursor.execute(query, params)

            if fetch:
                result = cursor.fetchall()
                logger.debug(f"db_utils: Fetched {len(result)} rows")
                return result

            conn.commit()
            logger.debug("db_utils: Query committed successfully")

            # Return appropriate ID based on database type
            if USE_POSTGRES:
                return cursor.rowcount
            else:
                return cursor.lastrowid

    except Exception as e:
        logger.error(f"db_utils: Query failed: {str(e)}")
        logger.error(f"db_utils: Query was: {query}")
        logger.error(f"db_utils: Params were: {params}")
        raise


def safe_execute_query(query, params=(), fetch=False): #
    """Execute a query with proper error handling""" #
    try: #
        return execute_query(query, params, fetch) #
    except Exception as e: #
        error_msg = str(e).lower() #
        if "no such table" in error_msg or "does not exist" in error_msg: #
            print(f"Table doesn't exist. Initializing database.") #
            logger.warning("db_utils: Table doesn't exist. Attempting to re-initialize database.") # Added logging
            initialize_db(force=True) #
            # Try once more after initialization
            logger.info("db_utils: Retrying query after database initialization.") # Added logging
            return execute_query(query, params, fetch) #
        else: #
            logger.error(f"db_utils: Unhandled error in safe_execute_query: {e}", exc_info=True) # Added logging
            raise #


def initialize_db(force=False):
    """
    Create database tables if they don't exist
    Supports both SQLite and PostgreSQL
    """
    print(f"Application: Database initialization attempted during startup. Force: {force}") # Modified print statement
    logger.info(f"db_utils: Attempting database initialization. Force: {force}.") # Added logger.info here

    try:
        if not USE_POSTGRES: #
            db_exists = os.path.exists(DB_FILE) #
            logger.info(f"db_utils: Checking SQLite DB existence: {db_exists}") # Added logging
        else:
            db_exists = True  # For PostgreSQL, assume database exists
            logger.info("db_utils: Assuming PostgreSQL database exists for initialization check.") # Added logging

        if not db_exists or force: #
            print(f"Initializing database ({'PostgreSQL' if USE_POSTGRES else 'SQLite'})") #
            logger.info(f"db_utils: Proceeding with database initialization ({'PostgreSQL' if USE_POSTGRES else 'SQLite'}).") # Added logging

            # Activities table - with PostgreSQL-compatible syntax
            if USE_POSTGRES: #
                activities_sql = '''
                CREATE TABLE IF NOT EXISTS activities (
                    activity_id SERIAL PRIMARY KEY,
                    date TEXT,
                    name TEXT,
                    type TEXT,
                    distance_miles REAL,
                    elevation_gain_feet REAL,
                    elevation_load_miles REAL,
                    total_load_miles REAL,
                    avg_heart_rate REAL,
                    max_heart_rate REAL,
                    duration_minutes REAL,
                    trimp REAL,
                    time_in_zone1 REAL,
                    time_in_zone2 REAL,
                    time_in_zone3 REAL,
                    time_in_zone4 REAL,
                    time_in_zone5 REAL,
                    seven_day_avg_load REAL,
                    twentyeight_day_avg_load REAL,
                    seven_day_avg_trimp REAL,
                    twentyeight_day_avg_trimp REAL,
                    acute_chronic_ratio REAL,
                    trimp_acute_chronic_ratio REAL,
                    normalized_divergence REAL,
                    weight_lbs REAL,
                    perceived_effort INTEGER,
                    feeling_score INTEGER,
                    notes TEXT
                );
                '''
            else: #
                activities_sql = '''
                CREATE TABLE IF NOT EXISTS activities (
                    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    name TEXT,
                    type TEXT,
                    distance_miles REAL,
                    elevation_gain_feet REAL,
                    elevation_load_miles REAL,
                    total_load_miles REAL,
                    avg_heart_rate REAL,
                    max_heart_rate REAL,
                    duration_minutes REAL,
                    trimp REAL,
                    time_in_zone1 REAL,
                    time_in_zone2 REAL,
                    time_in_zone3 REAL,
                    time_in_zone4 REAL,
                    time_in_zone5 REAL,
                    seven_day_avg_load REAL,
                    twentyeight_day_avg_load REAL,
                    seven_day_avg_trimp REAL,
                    twentyeight_day_avg_trimp REAL,
                    acute_chronic_ratio REAL,
                    trimp_acute_chronic_ratio REAL,
                    normalized_divergence REAL,
                    weight_lbs REAL,
                    perceived_effort INTEGER,
                    feeling_score INTEGER,
                    notes TEXT
                );
                '''

            execute_query(activities_sql) #
            print("Created activities table") #
            logger.info("db_utils: Successfully created activities table.") # Add logger.info here

            # User settings table
            if USE_POSTGRES: #
                user_settings_sql = '''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id SERIAL PRIMARY KEY,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    resting_hr INTEGER,
                    max_hr INTEGER,
                    gender TEXT,
                    last_sync_date TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    garmin_email TEXT,
                    garmin_password_encrypted TEXT,
                    garmin_last_sync TIMESTAMP,
                    strava_access_token TEXT,
                    strava_refresh_token TEXT,
                    strava_token_expires_at BIGINT,
                    strava_athlete_id BIGINT,
                    strava_token_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_strava_client_id VARCHAR(255),
                    user_strava_client_secret VARCHAR(255),
                    terms_accepted_at TIMESTAMP,
                    privacy_policy_accepted_at TIMESTAMP,
                    disclaimer_accepted_at TIMESTAMP,
                    onboarding_completed_at TIMESTAMP,
                    account_status VARCHAR(20) DEFAULT 'pending_verification',
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                '''
            else: #
                user_settings_sql = '''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    password_hash TEXT,
                    resting_hr INTEGER,
                    max_hr INTEGER,
                    gender TEXT,
                    last_sync_date TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    garmin_email TEXT,
                    garmin_password_encrypted TEXT,
                    garmin_last_sync TIMESTAMP,
                    strava_access_token TEXT,
                    strava_refresh_token TEXT,
                    strava_token_expires_at BIGINT,
                    strava_athlete_id BIGINT,
                    strava_token_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_strava_client_id VARCHAR(255),
                    user_strava_client_secret VARCHAR(255),
                    terms_accepted_at TIMESTAMP,
                    privacy_policy_accepted_at TIMESTAMP,
                    disclaimer_accepted_at TIMESTAMP,
                    onboarding_completed_at TIMESTAMP,
                    account_status VARCHAR(20) DEFAULT 'pending_verification',
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                '''

            execute_query(user_settings_sql) #
            print("Created user_settings table") #
            logger.info("db_utils: Successfully created user_settings table.") # Add logger.info here

            # LLM recommendations table
            if USE_POSTGRES: #
                llm_recommendations_sql = '''
                CREATE TABLE IF NOT EXISTS llm_recommendations (
                    id SERIAL PRIMARY KEY,
                    generation_date TEXT,
                    valid_until TEXT,
                    data_start_date TEXT,
                    data_end_date TEXT,
                    metrics_snapshot TEXT,
                    daily_recommendation TEXT,
                    weekly_recommendation TEXT,
                    pattern_insights TEXT,
                    raw_response TEXT
                );
                '''
            else: #
                llm_recommendations_sql = '''
                CREATE TABLE IF NOT EXISTS llm_recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation_date TEXT,
                    valid_until TEXT,
                    data_start_date TEXT,
                    data_end_date TEXT,
                    metrics_snapshot TEXT,
                    daily_recommendation TEXT,
                    weekly_recommendation TEXT,
                    pattern_insights TEXT,
                    raw_response TEXT
                );
                '''

            execute_query(llm_recommendations_sql) #
            print("Created llm_recommendations table") #
            logger.info("db_utils: Successfully created llm_recommendations table.") # Add logger.info here

            # Legal compliance table for audit trail
            if USE_POSTGRES: #
                legal_compliance_sql = '''
                CREATE TABLE IF NOT EXISTS legal_compliance (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES user_settings(id),
                    document_type VARCHAR(50) NOT NULL,
                    version VARCHAR(20) NOT NULL,
                    accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address INET,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                '''
            else: #
                legal_compliance_sql = '''
                CREATE TABLE IF NOT EXISTS legal_compliance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    document_type VARCHAR(50) NOT NULL,
                    version VARCHAR(20) NOT NULL,
                    accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_settings(id)
                );
                '''

            execute_query(legal_compliance_sql) #
            print("Created legal_compliance table") #
            logger.info("db_utils: Successfully created legal_compliance table.") # Add logger.info here

            print("Database initialization complete") #
            logger.info("db_utils: Database initialization complete.") # Add logger.info here
            return True #

        print("db_utils: Database already initialized and 'force' not set.") # Added print for existing DB
        logger.info("db_utils: Database already initialized and 'force' not set. Skipping initialization.") # Added logging

        # Always run migration to ensure schema is up to date
        migrate_user_settings_schema()
        migrate_legal_compliance_table()
        
        return False #

    except Exception as e:
        print(f"Database initialization error: {str(e)}") #
        logger.error(f"db_utils: Database initialization failed: {e}", exc_info=True) # Add this for traceback
        raise #

def validate_database():
    """Validate database structure and return True if valid"""
    try:
        # Test basic connection and table existence
        activity_count = execute_query("SELECT COUNT(*) FROM activities", fetch=True)
        user_count = execute_query("SELECT COUNT(*) FROM user_settings", fetch=True)

        print(f"Database validation successful: {activity_count[0][0]} activities, {user_count[0][0]} users")
        return True

    except Exception as e:
        print(f"Database validation error: {str(e)}")
        return False


def get_last_activity_date(user_id=None):
    """Get the date of the last activity in the database for a specific user"""
    if user_id is None:
        # Keep backward compatibility - if no user_id provided, get global last activity
        try:
            result = execute_query(
                "SELECT date FROM activities ORDER BY date DESC LIMIT 1",
                fetch=True
            )
            if result:
                last_date = result[0]['date']
                logger.info(f"db_utils: get_last_activity_date returning: {last_date}")
                return last_date
            else:
                logger.info("db_utils: No activities found in the database for get_last_activity_date.")
                return None
        except Exception as e:
            logger.error(f"db_utils: Error in get_last_activity_date: {e}", exc_info=True)
            return None
    else:
        # User-specific version
        try:
            result = execute_query(
                "SELECT date FROM activities WHERE user_id = ? ORDER BY date DESC LIMIT 1",
                (user_id,),
                fetch=True
            )
            if result:
                last_date = result[0]['date']
                logger.info(f"db_utils: get_last_activity_date for user {user_id} returning: {last_date}")
                return last_date
            else:
                logger.info(f"db_utils: No activities found for user {user_id}")
                return None
        except Exception as e:
            logger.error(f"db_utils: Error in get_last_activity_date for user {user_id}: {e}", exc_info=True)
            return None


def save_llm_recommendation(recommendation):
    """Save LLM recommendation to database with proper target_date handling."""
    try:
        # Extract user_id from recommendation
        user_id = recommendation.get('user_id')
        if user_id is None:
            raise ValueError("user_id is required for multi-user support")

        # Convert metrics_snapshot to JSON string if it's a dict
        metrics_json = json.dumps(recommendation['metrics_snapshot']) if isinstance(recommendation['metrics_snapshot'],
                                                                                    dict) else recommendation[
            'metrics_snapshot']

        # CRITICAL FIX: Include target_date in the INSERT statement
        query = """
            INSERT INTO llm_recommendations (
                generation_date, target_date, valid_until, data_start_date, data_end_date,
                metrics_snapshot, daily_recommendation, weekly_recommendation,
                pattern_insights, raw_response, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # CRITICAL FIX: Include target_date in the parameters (was missing before)
        params = (
            recommendation['generation_date'],
            recommendation.get('target_date'),  # ADD: target_date parameter
            recommendation['valid_until'],
            recommendation['data_start_date'],
            recommendation['data_end_date'],
            metrics_json,
            recommendation['daily_recommendation'],
            recommendation['weekly_recommendation'],
            recommendation['pattern_insights'],
            recommendation['raw_response'],
            user_id
        )

        result = execute_query(query, params)
        logger.info(f"Saved LLM recommendation to database for user {user_id} with target_date {recommendation.get('target_date')}")
        return result

    except Exception as e:
        logger.error(f"Error saving LLM recommendation: {str(e)}")
        raise


def get_latest_recommendation(user_id=None):
    """Get the most recent LLM recommendation from the database for a specific user."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        result = execute_query(
            """
            SELECT * FROM llm_recommendations 
            WHERE user_id = ?
            ORDER BY generated_at DESC 
            LIMIT 1
            """,
            (user_id,),
            fetch=True
        )

        if result and result[0]:
            recommendation = dict(result[0])

            # CRITICAL FIX: Clean up target_date format for frontend
            if recommendation.get('target_date'):
                target_date_raw = recommendation['target_date']

                # Handle timestamp format "2025-08-11T00:00:00Z" -> "2025-08-11"
                if isinstance(target_date_raw, str) and 'T' in target_date_raw:
                    recommendation['target_date'] = target_date_raw.split('T')[0]
                # Handle datetime objects
                elif hasattr(target_date_raw, 'strftime'):
                    recommendation['target_date'] = target_date_raw.strftime('%Y-%m-%d')

            # Also clean generation_date for consistency
            if recommendation.get('generation_date'):
                gen_date_raw = recommendation['generation_date']
                if isinstance(gen_date_raw, str) and 'T' in gen_date_raw:
                    recommendation['generation_date'] = gen_date_raw.split('T')[0]
                elif hasattr(gen_date_raw, 'strftime'):
                    recommendation['generation_date'] = gen_date_raw.strftime('%Y-%m-%d')

            logger.info(
                f"Retrieved latest recommendation for user {user_id} with cleaned target_date: {recommendation.get('target_date')}")
            return recommendation
        else:
            logger.info(f"No recommendations found for user {user_id}")
            return None

    except Exception as e:
        logger.error(f"Error getting latest recommendation for user {user_id}: {str(e)}")
        return None


def recommendation_needs_update(user_id=None):
    """Check if we need to generate a new recommendation for a specific user."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        latest = get_latest_recommendation(user_id)
        if not latest:
            return True

        # Check if recommendation is still valid
        valid_until = datetime.strptime(latest['valid_until'], '%Y-%m-%d').date()
        today = datetime.now().date()

        return today > valid_until

    except Exception as e:
        logger.error(f"Error checking recommendation update need for user {user_id}: {str(e)}")
        return True


# Replace the existing clear_old_recommendations function with this version:

def clear_old_recommendations(keep_count=10, user_id=None):
    """Clean up old recommendations for a specific user, keeping only the most recent ones."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        # Get count of current recommendations for this user
        count_result = execute_query("SELECT COUNT(*) FROM llm_recommendations WHERE user_id = ?", (user_id,),
                                     fetch=True)
        if count_result and count_result[0]:
            if hasattr(count_result[0], 'keys'):
                total_count = count_result[0].get('count', 0) or count_result[0].get('COUNT(*)', 0)
            else:
                total_count = count_result[0][0]
        else:
            total_count = 0

        if total_count > keep_count:
            # Delete oldest recommendations for this user
            execute_query(
                """
                DELETE FROM llm_recommendations 
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM llm_recommendations 
                    WHERE user_id = ?
                    ORDER BY generation_date DESC 
                    LIMIT ?
                )
                """,
                (user_id, user_id, keep_count)
            )
            logger.info(f"Cleaned up old recommendations for user {user_id}, kept {keep_count} most recent")

    except Exception as e:
        logger.error(f"Error cleaning up recommendations for user {user_id}: {str(e)}")


def migrate_user_settings_schema():
    """
    Migrate user_settings table to add legal compliance tracking columns
    This function safely adds new columns to existing tables
    """
    logger.info("db_utils: Starting user_settings schema migration")
    
    try:
        # Add legal compliance tracking columns
        migration_queries = [
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS terms_accepted_at TIMESTAMP;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS privacy_policy_accepted_at TIMESTAMP;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS disclaimer_accepted_at TIMESTAMP;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS onboarding_completed_at TIMESTAMP;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS account_status VARCHAR(20) DEFAULT 'pending_verification';",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"
        ]
        
        for query in migration_queries:
            try:
                execute_query(query, fetch=False)
                logger.info(f"db_utils: Successfully executed migration query: {query}")
            except Exception as e:
                logger.warning(f"db_utils: Migration query may have failed (column might already exist): {query} - {str(e)}")
        
        logger.info("db_utils: User settings schema migration completed")
        return True
        
    except Exception as e:
        logger.error(f"db_utils: Error during user_settings schema migration: {str(e)}")
        return False


def migrate_legal_compliance_table():
    """
    Migrate to add legal_compliance table for audit trail
    This function safely creates the legal_compliance table if it doesn't exist
    """
    logger.info("db_utils: Starting legal_compliance table migration")
    
    try:
        # Create legal_compliance table if it doesn't exist
        if USE_POSTGRES: #
            legal_compliance_sql = '''
            CREATE TABLE IF NOT EXISTS legal_compliance (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES user_settings(id),
                document_type VARCHAR(50) NOT NULL,
                version VARCHAR(20) NOT NULL,
                accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address INET,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            '''
        else: #
            legal_compliance_sql = '''
            CREATE TABLE IF NOT EXISTS legal_compliance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                document_type VARCHAR(50) NOT NULL,
                version VARCHAR(20) NOT NULL,
                accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_settings(id)
            );
            '''
        
        execute_query(legal_compliance_sql, fetch=False)
        logger.info("db_utils: Successfully created legal_compliance table")
        
        # Create index for better query performance
        index_sql = "CREATE INDEX IF NOT EXISTS idx_legal_compliance_user_id ON legal_compliance(user_id);"
        execute_query(index_sql, fetch=False)
        logger.info("db_utils: Successfully created legal_compliance index")
        
        return True
        
    except Exception as e:
        logger.error(f"db_utils: Error during legal_compliance table migration: {str(e)}")
        return False


# Database schema changes should be done via SQL Editor, not in code
# See docs/database_schema_rules.md for guidelines

# Also update the __all__ list to include these new functions:
__all__ = [
    'get_db_connection',
    'execute_query',
    'initialize_db',
    'validate_database',
    'DB_FILE',
    'configure_database',
    'USE_POSTGRES',
    'DATABASE_URL',
    'save_llm_recommendation',
    'get_latest_recommendation',
    'recommendation_needs_update',
    'clear_old_recommendations',
    'get_last_activity_date',
    'migrate_user_settings_schema',
    'migrate_legal_compliance_table',
]