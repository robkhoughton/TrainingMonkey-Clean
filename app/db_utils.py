# db_utils.py

import os
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
import re
import psycopg2
import psycopg2.extras

# Import connection pool manager
from db_connection_manager import db_manager, initialize_database_pool

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

# Database configuration - PostgreSQL only
DATABASE_URL = clean_database_url(os.environ.get('DATABASE_URL'))

if not DATABASE_URL:
    raise ValueError('DATABASE_URL environment variable is required for PostgreSQL connection')

print(f"Using PostgreSQL with connection: {DATABASE_URL[:50]}...")
logger.info(f"db_utils: Using PostgreSQL. URL: {DATABASE_URL[:50]}...")

# Legacy compatibility variables (PostgreSQL only)
DB_FILE = None
USE_POSTGRES = True

# configure_database() removed - PostgreSQL doesn't use file paths
# This was a legacy compatibility function that was never actually called


@contextmanager
def get_db_connection():
    """Context manager for PostgreSQL database connections."""
    conn = None
    try:
        print("Attempting PostgreSQL connection...")
        print(f"DATABASE_URL: {DATABASE_URL[:80]}...")
        logger.info("db_utils: Attempting PostgreSQL connection within context manager.")
        logger.info(f"db_utils: DATABASE_URL: {DATABASE_URL[:80]}...")

        # Parse connection string to avoid URL parsing issues with database names
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)
        
        # For Cloud SQL, use a simpler approach
        if '/cloudsql/' in DATABASE_URL:
            # Parse the connection string for Cloud SQL
            # Format: postgresql://user:pass@host/db?host=/cloudsql/project:region:instance
            pattern = r'postgresql://([^:]+):([^@]+)@[^/]*/([^?]+)\?host=([^&]+)'
            match = re.match(pattern, DATABASE_URL)

            if match:
                username, password, database, socket_dir = match.groups()

                print(f"Connecting to Cloud SQL:")
                print(f"  Username: {username}")
                print(f"  Database: {database}")
                print(f"  Socket directory: {socket_dir}")
                logger.info(f"db_utils: Connecting to Cloud SQL with socket: {socket_dir}")

                # Connect using the socket directory
                conn = psycopg2.connect(
                    host=socket_dir,
                    database=database,
                    user=username,
                    password=password
                )
            else:
                print("Could not parse Cloud SQL connection string, using parsed parameters")
                logger.warning("db_utils: Could not parse Cloud SQL connection string, using parsed parameters.")
                # Use parsed parameters for Cloud SQL fallback
                conn = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    database=parsed.path.lstrip('/'),
                    user=parsed.username,
                    password=parsed.password
                )
        else:
            # Standard PostgreSQL connection - use parsed parameters
            print("Using standard PostgreSQL connection")
            logger.info("db_utils: Using standard PostgreSQL connection.")
            # Parse and use individual parameters to avoid issues with database names containing hyphens
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path.lstrip('/'),  # Remove leading slash
                user=parsed.username,
                password=parsed.password
            )

        # Use RealDictCursor to get dictionary-like row access
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        print("PostgreSQL connection successful")
        logger.info("db_utils: PostgreSQL connection successful!")

        yield conn

    except Exception as e:
        error_msg = f"Database connection error: {str(e)}"
        print(error_msg)
        logger.error(f"db_utils: {error_msg}", exc_info=True)
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()
            logger.info("db_utils: Database connection closed.")


def execute_query_direct(query, params=(), fetch=False):
    """Execute a database query using direct connection (fallback when pool is unavailable)."""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from urllib.parse import urlparse
    
    database_url = clean_database_url(os.environ.get('DATABASE_URL'))
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not found")
    
    try:
        # Parse connection string to avoid URL parsing issues with database names
        parsed = urlparse(database_url)
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.lstrip('/')  # Remove leading slash
        user = parsed.username
        password = parsed.password
        
        # Use individual parameters instead of connection string
        # This ensures database names with hyphens (like 'train-d') are handled correctly
        with psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            cursor_factory=RealDictCursor
        ) as conn:
            with conn.cursor() as cursor:
                # Convert ? placeholders to %s for PostgreSQL compatibility
                if '?' in query:
                    param_count = query.count('?')
                    query = query.replace('?', '%s')
                    logger.debug(f"Converted {param_count} placeholders for PostgreSQL")
                
                logger.debug(f"Executing direct query: {query[:100]}...")
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    logger.debug(f"Direct query fetched {len(result)} rows")
                    return result
                
                conn.commit()
                return cursor.rowcount
                
    except Exception as e:
        logger.error(f"Direct query failed: {str(e)}")
        logger.error(f"Query was: {query[:200]}...")
        logger.error(f"Params were: {params}")
        raise

def execute_query(query, params=(), fetch=False, use_pool=False):
    """
    Execute a database query with optional parameter binding.
    
    Args:
        query: SQL query string
        params: Query parameters
        fetch: Whether to fetch results
        use_pool: Whether to use connection pool (for onboarding operations)
    """
    if use_pool:
        # Use connection pool for onboarding and user management operations
        try:
            logger.debug("Using connection pool for operation")
            return db_manager.execute_query(query, params, fetch)
        except Exception as e:
            logger.warning(f"Connection pool failed, falling back to direct connection: {str(e)}")
            return execute_query_direct(query, params, fetch)
    else:
        # Use direct connection for sync operations (more reliable)
        logger.debug("Using direct connection for sync operations")
        return execute_query_direct(query, params, fetch)

def execute_query_for_onboarding(query, params=(), fetch=False):
    """
    Execute a database query using connection pool for onboarding operations.
    This is a convenience function for onboarding-related database operations.
    """
    return execute_query(query, params, fetch, use_pool=True)

def execute_query_for_sync(query, params=(), fetch=False):
    """
    Execute a database query using direct connection for sync operations.
    This is a convenience function for sync-related database operations.
    """
    return execute_query(query, params, fetch, use_pool=False)


def execute_batch_queries(queries_with_params):
    """Execute multiple queries in single connection for better performance"""
    try:
        return db_manager.execute_batch_queries(queries_with_params)
    except Exception as e:
        logger.error(f"db_utils: Batch query execution failed: {str(e)}")
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
    PostgreSQL only
    """
    print(f"Application: Database initialization attempted during startup. Force: {force}")
    logger.info(f"db_utils: Attempting database initialization. Force: {force}.")

    try:
        # For PostgreSQL, assume database exists
        db_exists = True
        logger.info("db_utils: Assuming PostgreSQL database exists for initialization check.")

        if not db_exists or force:
            print("Initializing database (PostgreSQL)")
            logger.info("db_utils: Proceeding with database initialization (PostgreSQL).")

            # Activities table - PostgreSQL syntax
            activities_sql = '''
            CREATE TABLE IF NOT EXISTS activities (
                activity_id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES user_settings(id),
                date TEXT NOT NULL,
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
                notes TEXT,
                trimp_calculation_method VARCHAR(20) DEFAULT 'average',
                hr_stream_sample_count INTEGER DEFAULT 0,
                trimp_processed_at TIMESTAMP DEFAULT NOW()
            );
            '''

            execute_query(activities_sql)
            print("Created activities table")
            logger.info("db_utils: Successfully created activities table.")

            # User settings table - PostgreSQL syntax
            user_settings_sql = '''
            CREATE TABLE IF NOT EXISTS user_settings (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE,
                password_hash TEXT,
                age INTEGER,
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
                strava_token_created_at TIMESTAMP DEFAULT NOW(),
                user_strava_client_id VARCHAR(255),
                user_strava_client_secret VARCHAR(255),
                terms_accepted_at TIMESTAMP,
                privacy_policy_accepted_at TIMESTAMP,
                disclaimer_accepted_at TIMESTAMP,
                onboarding_completed_at TIMESTAMP,
                account_status VARCHAR(20) DEFAULT 'pending_verification',
                registration_date TIMESTAMP DEFAULT NOW()
            );
            '''

            execute_query(user_settings_sql)
            print("Created user_settings table")
            logger.info("db_utils: Successfully created user_settings table.")

            # LLM recommendations table - PostgreSQL syntax
            llm_recommendations_sql = '''
            CREATE TABLE IF NOT EXISTS llm_recommendations (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES user_settings(id),
                generation_date TEXT,
                target_date TEXT,
                valid_until TEXT,
                data_start_date TEXT,
                data_end_date TEXT,
                metrics_snapshot TEXT,
                daily_recommendation TEXT,
                weekly_recommendation TEXT,
                pattern_insights TEXT,
                raw_response TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            '''

            execute_query(llm_recommendations_sql)
            print("Created llm_recommendations table")
            logger.info("db_utils: Successfully created llm_recommendations table.")

            # Legal compliance table for audit trail - PostgreSQL syntax
            legal_compliance_sql = '''
            CREATE TABLE IF NOT EXISTS legal_compliance (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES user_settings(id),
                document_type VARCHAR(50) NOT NULL,
                version VARCHAR(20) NOT NULL,
                accepted_at TIMESTAMP DEFAULT NOW(),
                ip_address INET,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
            '''

            execute_query(legal_compliance_sql)
            print("Created legal_compliance table")
            logger.info("db_utils: Successfully created legal_compliance table.")

            print("Database initialization complete")
            logger.info("db_utils: Database initialization complete.")
            return True

        print("db_utils: Database already initialized and 'force' not set.")
        logger.info("db_utils: Database already initialized and 'force' not set. Skipping initialization.")

        # Always run migration to ensure schema is up to date
        migrate_user_settings_schema()
        migrate_legal_compliance_table()
        
        return False

    except Exception as e:
        print(f"Database initialization error: {str(e)}")
        logger.error(f"db_utils: Database initialization failed: {e}", exc_info=True)
        raise

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
                "SELECT date FROM activities WHERE user_id = %s ORDER BY date DESC LIMIT 1",
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

        # CRITICAL FIX: Include target_date and autopsy tracking in the INSERT statement
        query = """
            INSERT INTO llm_recommendations (
                generation_date, target_date, valid_until, data_start_date, data_end_date,
                metrics_snapshot, daily_recommendation, weekly_recommendation,
                pattern_insights, raw_response, user_id,
                is_autopsy_informed, autopsy_count, avg_alignment_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # CRITICAL FIX: Include target_date and autopsy tracking in the parameters
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
            user_id,
            recommendation.get('is_autopsy_informed', False),  # NEW: autopsy tracking
            recommendation.get('autopsy_count', 0),  # NEW: autopsy count
            recommendation.get('avg_alignment_score')  # NEW: average alignment score
        )

        result = execute_query(query, params)
        logger.info(f"Saved LLM recommendation to database for user {user_id} with target_date {recommendation.get('target_date')}")
        return result

    except Exception as e:
        logger.error(f"Error saving LLM recommendation: {str(e)}")
        raise


def cleanup_old_recommendations(user_id, keep_days=14):
    """
    Remove old recommendations, keeping only those from the last N days.
    This prevents database bloat while maintaining enough history for the Journal page.
    
    Args:
        user_id: The user ID to clean up recommendations for
        keep_days: Number of days of history to retain (default 14)
    """
    try:
        from datetime import timedelta
        from timezone_utils import get_user_current_date
        
        user_current_date = get_user_current_date(user_id)
        cutoff_date = (user_current_date - timedelta(days=keep_days)).strftime('%Y-%m-%d')
        
        # Delete recommendations older than the cutoff date
        query = """
            DELETE FROM llm_recommendations
            WHERE user_id = %s AND target_date < %s
        """
        
        result = execute_query(query, (user_id, cutoff_date))
        logger.info(f"Cleaned up recommendations older than {cutoff_date} for user {user_id} (keeping {keep_days} days)")
        return result
        
    except Exception as e:
        logger.error(f"Error cleaning up old recommendations for user {user_id}: {str(e)}")
        # Don't raise - cleanup failure shouldn't break recommendation generation
        return None


def cleanup_api_logs(days_to_keep=90):
    """
    Remove old API logs, keeping only the last N days for performance monitoring.
    Retains sufficient data for debugging, security analysis, and trend monitoring.
    
    Args:
        days_to_keep: Number of days of logs to retain (default 90)
        
    Returns:
        Number of rows deleted, or None if error
    """
    try:
        query = """
            DELETE FROM api_logs 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """ % days_to_keep
        
        result = execute_query(query)
        logger.info(f"Cleaned up api_logs older than {days_to_keep} days (deleted {result} rows)")
        return result
        
    except Exception as e:
        logger.error(f"Error cleaning up old api_logs: {str(e)}")
        # Don't raise - cleanup failure shouldn't break application
        return None


def cleanup_analytics_events(days_to_keep=90):
    """
    Remove old analytics events, keeping only the last N days for analysis.
    Retains sufficient data for quarterly trend analysis.
    
    Args:
        days_to_keep: Number of days of analytics to retain (default 90)
        
    Returns:
        Number of rows deleted, or None if error
    """
    try:
        query = """
            DELETE FROM analytics_events 
            WHERE timestamp < NOW() - INTERVAL '%s days'
        """ % days_to_keep
        
        result = execute_query(query)
        logger.info(f"Cleaned up analytics_events older than {days_to_keep} days (deleted {result} rows)")
        return result
        
    except Exception as e:
        logger.error(f"Error cleaning up old analytics_events: {str(e)}")
        # Don't raise - cleanup failure shouldn't break application
        return None


def get_latest_recommendation(user_id=None):
    """Get the most recent LLM recommendation from the database for a specific user."""
    if user_id is None:
        raise ValueError("user_id is required for multi-user support")

    try:
        result = execute_query(
            """
            SELECT * FROM llm_recommendations 
            WHERE user_id = %s
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
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS registration_date TIMESTAMP DEFAULT NOW();"
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
        # Create legal_compliance table if it doesn't exist - PostgreSQL syntax
        legal_compliance_sql = '''
        CREATE TABLE IF NOT EXISTS legal_compliance (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES user_settings(id),
            document_type VARCHAR(50) NOT NULL,
            version VARCHAR(20) NOT NULL,
            accepted_at TIMESTAMP DEFAULT NOW(),
            ip_address INET,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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


def validate_trimp_schema():
    """
    Validate that the new TRIMP calculation fields exist in the activities table
    Returns True if all required fields are present, False otherwise
    """
    logger.info("db_utils: Validating TRIMP schema fields")
    
    try:
        # Check if the new TRIMP fields exist in activities table
        required_fields = [
            'trimp_calculation_method',
            'hr_stream_sample_count', 
            'trimp_processed_at'
        ]
        
        # Get table schema information - PostgreSQL only
        schema_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'activities' 
            AND column_name = ANY(%s)
        """
        result = execute_query(schema_query, (required_fields,), fetch=True)
        existing_fields = [row['column_name'] for row in result] if result else []
        
        missing_fields = [field for field in required_fields if field not in existing_fields]
        
        if missing_fields:
            logger.warning(f"db_utils: Missing TRIMP schema fields: {missing_fields}")
            return False
        
        logger.info("db_utils: All TRIMP schema fields validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"db_utils: Error validating TRIMP schema: {str(e)}")
        return False


def validate_hr_streams_table():
    """
    Validate that the hr_streams table exists and has the correct structure
    Returns True if table exists with correct schema, False otherwise
    """
    logger.info("db_utils: Validating hr_streams table")
    
    try:
        # Check if hr_streams table exists - PostgreSQL only
        table_check = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'hr_streams'
            )
        """
        
        result = execute_query(table_check, fetch=True)
        
        if not result or not result[0]['exists']:
            logger.warning("db_utils: hr_streams table does not exist")
            return False
        
        # Check required columns in hr_streams table
        required_columns = [
            'id', 'activity_id', 'user_id', 'hr_data', 
            'sample_rate', 'created_at', 'updated_at'
        ]
        
        column_check = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'hr_streams' 
            AND column_name = ANY(%s)
        """
        result = execute_query(column_check, (required_columns,), fetch=True)
        existing_columns = [row['column_name'] for row in result] if result else []
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            logger.warning(f"db_utils: Missing hr_streams table columns: {missing_columns}")
            return False
        
        logger.info("db_utils: hr_streams table validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"db_utils: Error validating hr_streams table: {str(e)}")
        return False


def get_trimp_schema_status():
    """
    Get comprehensive status of TRIMP schema implementation
    Returns a dictionary with validation results for all TRIMP-related schema components
    """
    logger.info("db_utils: Getting TRIMP schema status")
    
    status = {
        'trimp_fields_valid': False,
        'hr_streams_table_valid': False,
        'overall_valid': False,
        'missing_components': []
    }
    
    try:
        # Validate TRIMP fields in activities table
        status['trimp_fields_valid'] = validate_trimp_schema()
        if not status['trimp_fields_valid']:
            status['missing_components'].append('TRIMP fields in activities table')
        
        # Validate hr_streams table
        status['hr_streams_table_valid'] = validate_hr_streams_table()
        if not status['hr_streams_table_valid']:
            status['missing_components'].append('hr_streams table')
        
        # Overall validation
        status['overall_valid'] = status['trimp_fields_valid'] and status['hr_streams_table_valid']
        
        logger.info(f"db_utils: TRIMP schema status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"db_utils: Error getting TRIMP schema status: {str(e)}")
        status['error'] = str(e)
        return status


def save_hr_stream_data(activity_id, user_id, hr_data, sample_rate=1.0):
    """
    Save heart rate stream data to the hr_streams table
    Args:
        activity_id (int): The activity ID this HR stream belongs to
        user_id (int): The user ID who owns this activity
        hr_data (list): List of heart rate values
        sample_rate (float): Sample rate in Hz (default 1.0)
    Returns:
        int: The ID of the inserted record, or None if failed
    """
    logger.info(f"db_utils: Saving HR stream data for activity {activity_id}, user {user_id}")
    
    try:
        # Validate inputs
        if not activity_id or not user_id:
            raise ValueError("activity_id and user_id are required")
        
        if not hr_data or not isinstance(hr_data, list):
            raise ValueError("hr_data must be a non-empty list")
        
        if not isinstance(sample_rate, (int, float)) or sample_rate <= 0:
            raise ValueError("sample_rate must be a positive number")
        
        # Convert hr_data to JSON string
        hr_data_json = json.dumps(hr_data)
        
        # Insert HR stream data
        query = """
            INSERT INTO hr_streams (activity_id, user_id, hr_data, sample_rate, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())
        """
        
        params = (activity_id, user_id, hr_data_json, sample_rate)
        result = execute_query(query, params)
        
        logger.info(f"db_utils: Successfully saved HR stream data for activity {activity_id} ({len(hr_data)} samples)")
        return result
        
    except Exception as e:
        logger.error(f"db_utils: Error saving HR stream data for activity {activity_id}: {str(e)}")
        return None


def get_hr_stream_data(activity_id, user_id=None):
    """
    Retrieve heart rate stream data for a specific activity
    Args:
        activity_id (int): The activity ID to retrieve HR data for
        user_id (int, optional): User ID for additional security (if provided)
    Returns:
        dict: Dictionary containing hr_data, sample_rate, and metadata, or None if not found
    """
    logger.info(f"db_utils: Retrieving HR stream data for activity {activity_id}")
    
    try:
        # Build query with optional user_id filter
        if user_id:
            query = """
                SELECT id, activity_id, user_id, hr_data, sample_rate, created_at, updated_at
                FROM hr_streams 
                WHERE activity_id = %s AND user_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """
            params = (activity_id, user_id)
        else:
            query = """
                SELECT id, activity_id, user_id, hr_data, sample_rate, created_at, updated_at
                FROM hr_streams 
                WHERE activity_id = %s
                ORDER BY created_at DESC
                LIMIT 1
            """
            params = (activity_id,)
        
        result = execute_query(query, params, fetch=True)
        
        if result and result[0]:
            row = result[0]
            
            # Parse JSON data
            try:
                hr_data = json.loads(row['hr_data']) if isinstance(row['hr_data'], str) else row['hr_data']
            except (json.JSONDecodeError, TypeError):
                logger.error(f"db_utils: Invalid JSON data in hr_streams for activity {activity_id}")
                return None
            
            hr_stream_info = {
                'id': row['id'],
                'activity_id': row['activity_id'],
                'user_id': row['user_id'],
                'hr_data': hr_data,
                'sample_rate': row['sample_rate'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'sample_count': len(hr_data) if isinstance(hr_data, list) else 0
            }
            
            logger.info(f"db_utils: Retrieved HR stream data for activity {activity_id} ({hr_stream_info['sample_count']} samples)")
            return hr_stream_info
        else:
            logger.info(f"db_utils: No HR stream data found for activity {activity_id}")
            return None
            
    except Exception as e:
        logger.error(f"db_utils: Error retrieving HR stream data for activity {activity_id}: {str(e)}")
        return None


def update_activity_trimp_metadata(activity_id, user_id, calculation_method, sample_count, trimp_value):
    """
    Update activity with TRIMP calculation metadata
    Args:
        activity_id (int): The activity ID to update
        user_id (int): The user ID who owns this activity
        calculation_method (str): 'stream' or 'average'
        sample_count (int): Number of HR samples used (0 for average method)
        trimp_value (float): The calculated TRIMP value
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"db_utils: Updating TRIMP metadata for activity {activity_id}")
    
    try:
        # Validate inputs
        if not activity_id or not user_id:
            raise ValueError("activity_id and user_id are required")
        
        if calculation_method not in ['stream', 'average', 'rest_day']:
            raise ValueError("calculation_method must be 'stream', 'average', or 'rest_day'")
        
        if not isinstance(sample_count, int) or sample_count < 0:
            raise ValueError("sample_count must be a non-negative integer")
        
        if not isinstance(trimp_value, (int, float)) or trimp_value < 0:
            raise ValueError("trimp_value must be a non-negative number")
        
        # Update activity with TRIMP metadata
        query = """
            UPDATE activities 
            SET %s = %s, trimp_calculation_method = %s, 
                hr_stream_sample_count = %s, 
                trimp_processed_at = NOW()
            WHERE activity_id = %s AND user_id = %s
        """
        
        params = (trimp_value, calculation_method, sample_count, activity_id, user_id)
        result = execute_query(query, params)
        
        if result > 0:
            logger.info(f"db_utils: Successfully updated TRIMP metadata for activity {activity_id} (method: {calculation_method}, samples: {sample_count})")
            return True
        else:
            logger.warning(f"db_utils: No activity found to update for activity_id {activity_id}, user_id {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"db_utils: Error updating TRIMP metadata for activity {activity_id}: {str(e)}")
        return False


def get_activities_needing_trimp_recalculation(user_id=None, days_back=30):
    """
    Get activities that need TRIMP recalculation (either missing TRIMP or using old method)
    Args:
        user_id (int, optional): Filter by specific user, or None for all users
        days_back (int): Number of days back to look for activities (default 30)
    Returns:
        list: List of activity records that need recalculation
    """
    logger.info(f"db_utils: Getting activities needing TRIMP recalculation (user_id: {user_id}, days_back: {days_back})")
    
    try:
        # Build query based on parameters
        if user_id:
            query = """
                SELECT activity_id, user_id, date, name, type, duration_minutes, 
                       avg_heart_rate, max_heart_rate, trimp, trimp_calculation_method,
                       hr_stream_sample_count, trimp_processed_at
                FROM activities 
                WHERE user_id = %s 
                AND date >= CURRENT_DATE - INTERVAL '{} days'
                AND activity_id > 0
                AND (
                    trimp IS NULL 
                    OR trimp_calculation_method = 'average'
                    OR trimp_processed_at IS NULL
                )
                ORDER BY date DESC
            """.format(days_back)
            params = (user_id,)
        else:
            query = """
                SELECT activity_id, user_id, date, name, type, duration_minutes,
                       avg_heart_rate, max_heart_rate, trimp, trimp_calculation_method,
                       hr_stream_sample_count, trimp_processed_at
                FROM activities 
                WHERE date >= CURRENT_DATE - INTERVAL '{} days'
                AND activity_id > 0
                AND (
                    trimp IS NULL 
                    OR trimp_calculation_method = 'average'
                    OR trimp_processed_at IS NULL
                )
                ORDER BY date DESC
            """.format(days_back)
            params = ()
        
        result = execute_query(query, params, fetch=True)
        
        if result:
            activities = [dict(row) for row in result]
            logger.info(f"db_utils: Found {len(activities)} activities needing TRIMP recalculation")
            return activities
        else:
            logger.info("db_utils: No activities found needing TRIMP recalculation")
            return []
            
    except Exception as e:
        logger.error(f"db_utils: Error getting activities needing TRIMP recalculation: {str(e)}")
        return []


def delete_hr_stream_data(activity_id, user_id=None):
    """
    Delete heart rate stream data for a specific activity
    Args:
        activity_id (int): The activity ID to delete HR data for
        user_id (int, optional): User ID for additional security (if provided)
    Returns:
        bool: True if successful, False otherwise
    """
    logger.info(f"db_utils: Deleting HR stream data for activity {activity_id}")
    
    try:
        # Build query with optional user_id filter
        if user_id:
            query = "DELETE FROM hr_streams WHERE activity_id = %s AND user_id = %s"
            params = (activity_id, user_id)
        else:
            query = "DELETE FROM hr_streams WHERE activity_id = %s"
            params = (activity_id,)
        
        result = execute_query(query, params)
        
        if result > 0:
            logger.info(f"db_utils: Successfully deleted HR stream data for activity {activity_id}")
            return True
        else:
            logger.info(f"db_utils: No HR stream data found to delete for activity {activity_id}")
            return False
            
    except Exception as e:
        logger.error(f"db_utils: Error deleting HR stream data for activity {activity_id}: {str(e)}")
        return False


# Database schema changes should be done via SQL Editor, not in code
# See docs/database_schema_rules.md for guidelines

# Also update the __all__ list to include these new functions:
__all__ = [
    'get_db_connection',
    'execute_query',
    'execute_batch_queries',
    'initialize_db',
    'validate_database',
    'DATABASE_URL',
    'DB_FILE',  # Legacy compatibility variable
    'USE_POSTGRES',  # Legacy compatibility variable
    'save_llm_recommendation',
    'get_latest_recommendation',
    'recommendation_needs_update',
    'cleanup_old_recommendations',  # Use this instead of removed clear_old_recommendations
    'get_last_activity_date',
    'migrate_user_settings_schema',
    'migrate_legal_compliance_table',
    'validate_trimp_schema',
    'validate_hr_streams_table',
    'get_trimp_schema_status',
    'save_hr_stream_data',
    'get_hr_stream_data',
    'update_activity_trimp_metadata',
    'get_activities_needing_trimp_recalculation',
    'delete_hr_stream_data',
]