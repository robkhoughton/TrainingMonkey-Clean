"""
Migration: Create athlete_models table (Phase 3 — Persistent Athlete Model)

Creates a per-user persistent model that accumulates learning across autopsy sessions.
Bootstraps initial values from existing ai_autopsies data.

Usage:
    python scripts/migrations/add_athlete_models_table.py
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
    """Create athlete_models table and bootstrap initial rows."""

    with get_db_connection() as conn:
        cur = conn.cursor()
        try:
            # ----------------------------------------------------------------
            # Step 1: Create the table
            # ----------------------------------------------------------------
            logger.info("Creating athlete_models table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS athlete_models (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES user_settings(id),
                    acwr_sweet_spot_low FLOAT DEFAULT 0.8,
                    acwr_sweet_spot_high FLOAT DEFAULT 1.2,
                    acwr_sweet_spot_confidence FLOAT DEFAULT 0.0,
                    typical_divergence_low FLOAT DEFAULT -0.05,
                    typical_divergence_high FLOAT DEFAULT 0.05,
                    divergence_injury_threshold FLOAT DEFAULT 0.15,
                    rpe_calibration_offset FLOAT DEFAULT 0.0,
                    rpe_sample_count INTEGER DEFAULT 0,
                    avg_days_recover_after_hard FLOAT DEFAULT 1.5,
                    total_autopsies INTEGER DEFAULT 0,
                    avg_lifetime_alignment FLOAT DEFAULT 5.0,
                    recent_alignment_trend VARCHAR(20) DEFAULT 'insufficient_data',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    last_autopsy_date DATE
                )
            """)
            logger.info("✓ athlete_models table created (or already exists)")

            # ----------------------------------------------------------------
            # Step 2: Bootstrap from existing ai_autopsies data
            # ----------------------------------------------------------------
            logger.info("Fetching existing autopsy data for bootstrap...")
            cur.execute("""
                SELECT user_id, alignment_score, date
                FROM ai_autopsies
                WHERE alignment_score IS NOT NULL
                ORDER BY user_id, date DESC
            """)
            rows = cur.fetchall()

            # Aggregate per user
            from collections import defaultdict
            user_autopsies = defaultdict(list)
            for row in rows:
                uid = row['user_id']
                score = row['alignment_score']
                dt = row['date']
                user_autopsies[uid].append({'score': score, 'date': dt})

            # Also get all users from user_settings so every user gets a row
            cur.execute("SELECT id FROM user_settings")
            all_users = [r['id'] for r in cur.fetchall()]

            bootstrapped = 0
            default_rows = 0

            for uid in all_users:
                autopsies = user_autopsies.get(uid, [])
                n = len(autopsies)

                if n >= 3:
                    # Compute bootstrapped values
                    scores = [a['score'] for a in autopsies]
                    avg_alignment = sum(scores) / n

                    # Compute recent_alignment_trend from last 3
                    last3 = scores[:3]  # already sorted DESC
                    if len(last3) == 3:
                        if last3[0] > last3[1] > last3[2]:
                            trend = 'improving'
                        elif last3[0] < last3[1] < last3[2]:
                            trend = 'declining'
                        else:
                            trend = 'stable'
                    else:
                        trend = 'insufficient_data'

                    # Confidence: 0.05 per autopsy, capped at 1.0
                    confidence = min(1.0, n * 0.05)

                    # last_autopsy_date
                    last_date = autopsies[0]['date']  # most recent first

                    cur.execute("""
                        INSERT INTO athlete_models (
                            user_id,
                            total_autopsies,
                            avg_lifetime_alignment,
                            recent_alignment_trend,
                            acwr_sweet_spot_confidence,
                            last_autopsy_date
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (user_id) DO UPDATE SET
                            total_autopsies = EXCLUDED.total_autopsies,
                            avg_lifetime_alignment = EXCLUDED.avg_lifetime_alignment,
                            recent_alignment_trend = EXCLUDED.recent_alignment_trend,
                            acwr_sweet_spot_confidence = EXCLUDED.acwr_sweet_spot_confidence,
                            last_autopsy_date = EXCLUDED.last_autopsy_date,
                            updated_at = NOW()
                    """, (uid, n, round(avg_alignment, 2), trend, round(confidence, 4), last_date))
                    bootstrapped += 1

                else:
                    # Default row — confidence stays 0.0
                    cur.execute("""
                        INSERT INTO athlete_models (user_id)
                        VALUES (%s)
                        ON CONFLICT (user_id) DO NOTHING
                    """, (uid,))
                    default_rows += 1

            conn.commit()
            logger.info(f"✓ Migration completed successfully")
            logger.info(f"  - Bootstrapped {bootstrapped} users with ≥3 autopsies")
            logger.info(f"  - Created default rows for {default_rows} users with <3 autopsies")

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
            # Check table exists
            cur.execute("""
                SELECT COUNT(*) as row_count
                FROM athlete_models
            """)
            result = cur.fetchone()
            total_rows = result['row_count']
            logger.info(f"✓ athlete_models table exists with {total_rows} rows")

            # Bootstrap stats
            cur.execute("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE total_autopsies >= 3) as bootstrapped_users,
                    COUNT(*) FILTER (WHERE total_autopsies < 3) as default_users,
                    AVG(avg_lifetime_alignment) as avg_alignment,
                    AVG(acwr_sweet_spot_confidence) as avg_confidence
                FROM athlete_models
            """)
            stats = cur.fetchone()
            logger.info(f"✓ Bootstrap statistics:")
            logger.info(f"  - Total users: {stats['total_users']}")
            logger.info(f"  - Bootstrapped (≥3 autopsies): {stats['bootstrapped_users']}")
            logger.info(f"  - Default rows (<3 autopsies): {stats['default_users']}")
            if stats['avg_alignment'] is not None:
                logger.info(f"  - Average lifetime alignment: {stats['avg_alignment']:.2f}/10")
                logger.info(f"  - Average model confidence: {stats['avg_confidence']:.4f}")

        except Exception as e:
            logger.error(f"✗ Verification failed: {e}")
            raise
        finally:
            cur.close()


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Phase 3: Add athlete_models Table Migration")
    logger.info("=" * 60)

    run_migration()
    verify_migration()

    logger.info("=" * 60)
    logger.info("Migration complete!")
    logger.info("=" * 60)
