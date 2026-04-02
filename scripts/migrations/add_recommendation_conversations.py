"""
Migration: Add recommendation_conversations table and extend athlete_models (Phase 1)

Creates the recommendation_conversations table to persist coach recommendation
chat history per user per day, and adds injury_notes / preference_notes columns
to athlete_models for long-term athlete context.

Usage:
    python scripts/migrations/add_recommendation_conversations.py
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
    """Create recommendation_conversations table and extend athlete_models."""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # ----------------------------------------------------------------
            # Step 1: Create recommendation_conversations table
            # ----------------------------------------------------------------
            logger.info("Creating recommendation_conversations table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS recommendation_conversations (
                    id                  SERIAL PRIMARY KEY,
                    user_id             INTEGER NOT NULL REFERENCES user_settings(id),
                    recommendation_date DATE NOT NULL,
                    messages            JSONB NOT NULL DEFAULT '[]',
                    extraction_result   JSONB,
                    extraction_done     BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at          TIMESTAMP DEFAULT NOW(),
                    updated_at          TIMESTAMP DEFAULT NOW(),
                    UNIQUE (user_id, recommendation_date)
                )
            """)
            logger.info("✓ recommendation_conversations table created (or already exists)")

            # ----------------------------------------------------------------
            # Step 2: Create index on (user_id, recommendation_date)
            # ----------------------------------------------------------------
            logger.info("Creating index idx_rec_conv_user_date...")
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_rec_conv_user_date
                    ON recommendation_conversations (user_id, recommendation_date)
            """)
            logger.info("✓ idx_rec_conv_user_date index created (or already exists)")

            # ----------------------------------------------------------------
            # Step 3: Add injury_notes column to athlete_models
            # ----------------------------------------------------------------
            logger.info("Adding injury_notes column to athlete_models...")
            cur.execute("""
                ALTER TABLE athlete_models
                    ADD COLUMN IF NOT EXISTS injury_notes TEXT
            """)
            logger.info("✓ athlete_models.injury_notes column added (or already exists)")

            # ----------------------------------------------------------------
            # Step 4: Add preference_notes column to athlete_models
            # ----------------------------------------------------------------
            logger.info("Adding preference_notes column to athlete_models...")
            cur.execute("""
                ALTER TABLE athlete_models
                    ADD COLUMN IF NOT EXISTS preference_notes TEXT
            """)
            logger.info("✓ athlete_models.preference_notes column added (or already exists)")

            conn.commit()
            logger.info("✓ Migration completed successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"✗ Migration failed: {e}")
            raise
        finally:
            cur.close()


def verify_migration():
    """Verify all migration steps completed successfully."""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # Check 1: recommendation_conversations table exists
            cur.execute("""
                SELECT COUNT(*) AS count
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'recommendation_conversations'
            """)
            result = cur.fetchone()
            if result['count'] == 0:
                raise Exception("recommendation_conversations table does NOT exist")
            logger.info("✓ recommendation_conversations table exists")

            # Check 2: idx_rec_conv_user_date index exists
            cur.execute("""
                SELECT COUNT(*) AS count
                FROM pg_indexes
                WHERE schemaname = 'public'
                  AND tablename  = 'recommendation_conversations'
                  AND indexname  = 'idx_rec_conv_user_date'
            """)
            result = cur.fetchone()
            if result['count'] == 0:
                raise Exception("idx_rec_conv_user_date index does NOT exist")
            logger.info("✓ idx_rec_conv_user_date index exists")

            # Check 3: athlete_models.injury_notes column exists
            cur.execute("""
                SELECT COUNT(*) AS count
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'athlete_models'
                  AND column_name  = 'injury_notes'
            """)
            result = cur.fetchone()
            if result['count'] == 0:
                raise Exception("athlete_models.injury_notes column does NOT exist")
            logger.info("✓ athlete_models.injury_notes column exists")

            # Check 4: athlete_models.preference_notes column exists
            cur.execute("""
                SELECT COUNT(*) AS count
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = 'athlete_models'
                  AND column_name  = 'preference_notes'
            """)
            result = cur.fetchone()
            if result['count'] == 0:
                raise Exception("athlete_models.preference_notes column does NOT exist")
            logger.info("✓ athlete_models.preference_notes column exists")

        except Exception as e:
            logger.error(f"✗ Verification failed: {e}")
            raise
        finally:
            cur.close()


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Phase 1: Add recommendation_conversations Table Migration")
    logger.info("=" * 60)

    run_migration()
    verify_migration()

    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
