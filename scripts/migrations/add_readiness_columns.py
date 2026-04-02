"""
Migration: Add sleep_quality and morning_soreness columns to journal_entries table

Adds two nullable integer columns for the Morning Readiness Check-In feature (Phase 6B).
- sleep_quality: 1-5 scale
- morning_soreness: 0-100 scale

Usage:
    python scripts/migrations/add_readiness_columns.py
"""

import sys
import os

# Add project root and app/ to path so all internal imports resolve
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, _project_root)
sys.path.insert(0, os.path.join(_project_root, 'app'))

from app.db_credentials_loader import set_database_url
set_database_url()

from app.db_utils import get_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Add sleep_quality and morning_soreness columns to journal_entries table."""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            logger.info("Adding sleep_quality column to journal_entries...")
            cur.execute("""
                ALTER TABLE journal_entries
                ADD COLUMN IF NOT EXISTS sleep_quality INTEGER
            """)

            logger.info("Adding morning_soreness column to journal_entries...")
            cur.execute("""
                ALTER TABLE journal_entries
                ADD COLUMN IF NOT EXISTS morning_soreness INTEGER
            """)

            conn.commit()
            logger.info("✓ Migration completed successfully")
            logger.info("  - Added sleep_quality INTEGER column (nullable, 1-5)")
            logger.info("  - Added morning_soreness INTEGER column (nullable, 0-100)")

        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Migration failed: {e}")
            raise
        finally:
            cur.close()


def verify_migration():
    """Verify the migration was successful."""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'journal_entries'
                AND column_name IN ('sleep_quality', 'morning_soreness')
                ORDER BY column_name
            """)

            results = cur.fetchall()

            if len(results) == 2:
                for row in results:
                    logger.info(f"✓ Column exists: {dict(row)}")
            else:
                found = [dict(r)['column_name'] for r in results]
                logger.error(f"✗ Expected 2 columns, found: {found}")

        finally:
            cur.close()


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Add Morning Readiness Columns Migration")
    logger.info("=" * 60)

    run_migration()
    verify_migration()

    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
