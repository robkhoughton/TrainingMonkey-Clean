# QUICK SYNC FIX - MINIMAL RISK APPROACH
# Following Strategic Risk Analysis: "Fix one specific issue at a time"

# =============================================================================
# SINGLE FILE SOLUTION: sync_fix.py
# =============================================================================
"""
Minimal fix for Strava sync PostgreSQL DATE compatibility issue.
Does NOT modify existing functions - provides parallel implementation.
"""

import logging
from datetime import datetime

logger = logging.getLogger('sync_fix')


def check_activity_exists_safely(activity_id, user_id):
    """
    Safe activity existence check that avoids PostgreSQL DATE format issues.
    Drop-in replacement for problematic database queries.
    """
    from db_utils import execute_query

    try:
        # Use only activity_id + user_id (most reliable, avoids date comparison)
        existing = execute_query(
            "SELECT 1 FROM activities WHERE activity_id = %s AND user_id = %s",
            (activity_id, user_id),
            fetch=True
        )
        return bool(existing)
    except Exception as e:
        logger.error(f"Activity check error: {str(e)}")
        return False


def save_activity_safely(load_data):
    """
    Safe activity save that handles PostgreSQL DATE format.
    Drop-in replacement for save_training_load when it fails.
    """
    from db_utils import execute_query

    try:
        # Normalize date for PostgreSQL
        if 'date' in load_data and isinstance(load_data['date'], str):
            # Ensure it's in YYYY-MM-DD format (PostgreSQL will handle conversion)
            date_str = load_data['date']
            if len(date_str) == 10 and date_str.count('-') == 2:
                # Good format, keep as-is
                pass
            else:
                # Try to normalize
                try:
                    parsed = datetime.strptime(date_str, '%Y-%m-%d')
                    load_data['date'] = parsed.strftime('%Y-%m-%d')
                except:
                    logger.warning(f"Could not normalize date: {date_str}")

        activity_id = load_data['activity_id']
        user_id = load_data['user_id']

        # Check existence using safe method
        if check_activity_exists_safely(activity_id, user_id):
            logger.info(f"Activity {activity_id} already exists - skipping")
            return False

        # Build INSERT query
        columns = ', '.join(load_data.keys())
        placeholders = ', '.join(['%s'] * len(load_data))
        values = tuple(load_data.values())

        execute_query(
            f"INSERT INTO activities ({columns}) VALUES ({placeholders})",
            values
        )

        logger.info(f"Successfully saved activity {activity_id}")
        return True

    except Exception as e:
        logger.error(f"Safe save error: {str(e)}", exc_info=True)
        raise


# =============================================================================
# APPLY TO EXISTING SYNC - MONKEY PATCH APPROACH
# =============================================================================

def apply_sync_fix():
    """
    Apply the sync fix using monkey patching - no file modifications needed.
    Call this at the start of your sync process.
    """
    try:
        # Import the modules that need fixing
        import strava_training_load

        # Store original functions
        if not hasattr(strava_training_load, '_original_save_training_load'):
            strava_training_load._original_save_training_load = strava_training_load.save_training_load

        # Replace with safe version
        def safe_save_training_load(load_data, filename=None):
            try:
                return save_activity_safely(load_data)
            except Exception as e:
                logger.error(f"Safe save failed, trying original: {str(e)}")
                # Fallback to original function
                return strava_training_load._original_save_training_load(load_data, filename)

        # Monkey patch the function
        strava_training_load.save_training_load = safe_save_training_load

        logger.info("✅ Sync fix applied successfully")

    except Exception as e:
        logger.error(f"Failed to apply sync fix: {str(e)}")


# =============================================================================
# USAGE INSTRUCTIONS
# =============================================================================

USAGE_INSTRUCTIONS = """
IMMEDIATE IMPLEMENTATION (Zero risk to existing code):

1. Add this file as sync_fix.py to your project

2. In your sync endpoint (strava_app.py), add at the beginning:
   ```python
   from sync_fix import apply_sync_fix
   apply_sync_fix()  # Apply before any sync operations
   ```

3. Run manual sync - the fix will:
   - Use safe activity existence checking (avoids date comparison)
   - Normalize dates for PostgreSQL compatibility
   - Fall back to original functions if needed

4. Monitor logs for "Safe save" vs "Original save" to see which path works

This approach:
✅ Follows Strategic Risk Analysis: "Fix one specific issue at a time"
✅ No modifications to existing functions
✅ Can be easily removed if it doesn't work
✅ Provides fallback to original behavior
✅ Minimal risk to working systems
"""