"""
Migration: Add max_hr_is_calculated flag to user_settings table

This migration adds a boolean flag to track whether the user's max HR
was calculated using the Tanaka formula or provided by the user.

Usage:
    python scripts/migrations/add_max_hr_calculated_flag.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.db_utils import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add max_hr_is_calculated column to user_settings table"""

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Add max_hr_is_calculated column
        logger.info("Adding max_hr_is_calculated column to user_settings...")
        cur.execute("""
            ALTER TABLE user_settings
            ADD COLUMN IF NOT EXISTS max_hr_is_calculated BOOLEAN DEFAULT FALSE
        """)

        # Set flag to TRUE for users where max_hr was likely calculated
        # (max_hr is close to Tanaka formula result)
        logger.info("Setting max_hr_is_calculated flag for existing users...")
        cur.execute("""
            UPDATE user_settings
            SET max_hr_is_calculated = TRUE
            WHERE age IS NOT NULL
              AND max_hr IS NOT NULL
              AND ABS(max_hr - (208 - (0.7 * age))) <= 2
        """)

        rows_updated = cur.rowcount

        conn.commit()
        logger.info(f"✓ Migration completed successfully")
        logger.info(f"  - Added max_hr_is_calculated column")
        logger.info(f"  - Updated {rows_updated} existing users with calculated max HR flag")

    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Migration failed: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def verify_migration():
    """Verify the migration was successful"""

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if column exists
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'user_settings'
            AND column_name = 'max_hr_is_calculated'
        """)

        result = cur.fetchone()

        if result:
            logger.info(f"✓ Column exists: {result}")

            # Count users with calculated max HR
            cur.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE max_hr_is_calculated = TRUE) as calculated_count,
                    COUNT(*) FILTER (WHERE max_hr_is_calculated = FALSE) as user_provided_count
                FROM user_settings
                WHERE max_hr IS NOT NULL
            """)

            stats = cur.fetchone()
            logger.info(f"✓ Max HR statistics:")
            logger.info(f"  - Total users with max HR: {stats['total_users']}")
            logger.info(f"  - Calculated max HR: {stats['calculated_count']}")
            logger.info(f"  - User-provided max HR: {stats['user_provided_count']}")
        else:
            logger.error("✗ Column does not exist")

    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Max HR Calculated Flag Migration")
    logger.info("=" * 60)

    run_migration()
    verify_migration()

    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
