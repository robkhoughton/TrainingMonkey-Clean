"""
Migration: Add structured_output JSONB column to llm_recommendations table

This migration adds a nullable JSONB column to store machine-readable assessment
data extracted from Claude's structured output block. Enables guaranteed-parseable
decisions, persistent athlete learning, and richer analytics.

Usage:
    python scripts/migrations/add_structured_output_column.py
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
    """Add structured_output JSONB column to llm_recommendations table"""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            logger.info("Adding structured_output column to llm_recommendations...")
            cur.execute("""
                ALTER TABLE llm_recommendations
                ADD COLUMN IF NOT EXISTS structured_output JSONB
            """)

            conn.commit()
            logger.info("✓ Migration completed successfully")
            logger.info("  - Added structured_output JSONB column (nullable)")

        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Migration failed: {e}")
            raise
        finally:
            cur.close()


def verify_migration():
    """Verify the migration was successful"""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'llm_recommendations'
                AND column_name = 'structured_output'
            """)

            result = cur.fetchone()

            if result:
                logger.info(f"✓ Column exists: {result}")

                cur.execute("""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT(structured_output) as rows_with_structured_output
                    FROM llm_recommendations
                """)
                stats = cur.fetchone()
                logger.info(f"✓ Table stats:")
                logger.info(f"  - Total recommendations: {stats['total_rows']}")
                logger.info(f"  - With structured output: {stats['rows_with_structured_output']}")
            else:
                logger.error("✗ Column does not exist")

        finally:
            cur.close()


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Add structured_output Column Migration")
    logger.info("=" * 60)

    run_migration()
    verify_migration()

    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
