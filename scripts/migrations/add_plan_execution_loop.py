"""
Migration: Plan Execution Loop — Phase A (Weekly Context Storage)

Adds strategic context columns to weekly_programs and creates the
alignment_queries table for mid-week deviation tracking.

Schema changes:
  weekly_programs:
    - strategic_summary   JSONB     — structured coaching context snapshot
    - deviation_log       JSONB     — running list of daily alignment entries
    - revision_pending    BOOLEAN   — flag: plan needs mid-week revision
    - revision_proposal   JSONB     — proposed revised plan from LLM

  alignment_queries:
    - New table for per-day alignment scoring and athlete response tracking

Usage:
    python scripts/migrations/add_plan_execution_loop.py
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
    """Alter weekly_programs and create alignment_queries table."""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # ----------------------------------------------------------------
            # Step 1: Extend weekly_programs with strategic context columns
            # ----------------------------------------------------------------
            logger.info("Adding strategic context columns to weekly_programs...")

            cur.execute("""
                ALTER TABLE weekly_programs
                    ADD COLUMN IF NOT EXISTS strategic_summary JSONB,
                    ADD COLUMN IF NOT EXISTS deviation_log JSONB DEFAULT '[]',
                    ADD COLUMN IF NOT EXISTS revision_pending BOOLEAN DEFAULT FALSE,
                    ADD COLUMN IF NOT EXISTS revision_proposal JSONB
            """)
            logger.info("✓ weekly_programs columns added (or already exist)")

            # ----------------------------------------------------------------
            # Step 2: Create alignment_queries table
            # ----------------------------------------------------------------
            logger.info("Creating alignment_queries table...")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS alignment_queries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES user_settings(id),
                    activity_date DATE NOT NULL,
                    alignment_score INTEGER NOT NULL,
                    status VARCHAR(20) DEFAULT 'pending',
                    response TEXT,
                    snooze_until DATE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE (user_id, activity_date)
                )
            """)
            logger.info("✓ alignment_queries table created (or already exists)")

            # ----------------------------------------------------------------
            # Step 3: Create index on alignment_queries
            # ----------------------------------------------------------------
            logger.info("Creating index on alignment_queries (user_id, status)...")

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_alignment_queries_user_status
                    ON alignment_queries (user_id, status)
            """)
            logger.info("✓ Index created (or already exists)")

            conn.commit()
            logger.info("✓ Migration completed successfully")

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
            # Verify new columns on weekly_programs
            cur.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'weekly_programs'
                  AND column_name IN (
                      'strategic_summary', 'deviation_log',
                      'revision_pending', 'revision_proposal'
                  )
                ORDER BY column_name
            """)
            cols = [row['column_name'] for row in cur.fetchall()]
            logger.info(f"✓ weekly_programs new columns present: {cols}")

            expected = {'deviation_log', 'revision_pending', 'revision_proposal', 'strategic_summary'}
            missing = expected - set(cols)
            if missing:
                logger.warning(f"  ⚠ Missing columns: {missing}")
            else:
                logger.info("  ✓ All 4 columns confirmed")

            # Verify alignment_queries table
            cur.execute("SELECT COUNT(*) as row_count FROM alignment_queries")
            result = cur.fetchone()
            logger.info(f"✓ alignment_queries table exists with {result['row_count']} rows")

            # Verify index
            cur.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE tablename = 'alignment_queries'
                  AND indexname = 'idx_alignment_queries_user_status'
            """)
            idx = cur.fetchone()
            if idx:
                logger.info(f"✓ Index idx_alignment_queries_user_status present")
            else:
                logger.warning("  ⚠ Index idx_alignment_queries_user_status not found")

        except Exception as e:
            logger.error(f"✗ Verification failed: {e}")
            raise
        finally:
            cur.close()


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Phase A: Plan Execution Loop — Weekly Context Storage")
    logger.info("=" * 60)

    run_migration()
    verify_migration()

    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
