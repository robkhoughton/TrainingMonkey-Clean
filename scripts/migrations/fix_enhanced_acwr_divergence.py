#!/usr/bin/env python3
"""
Migration Script: Fix Normalized Divergence for Enhanced ACWR Users

PURPOSE:
Fixes the normalized divergence calculation bug in ExponentialDecayEngine that affected
users with enhanced ACWR configurations. The bug calculated raw difference instead of
normalized (mean-based) divergence, and used absolute value instead of preserving valence.

WHAT WAS WRONG:
    # OLD (BUGGY):
    normalized_divergence = abs(acute_chronic_ratio - trimp_acute_chronic_ratio)
    # Missing division step! And used abs() instead of preserving sign.

WHAT'S CORRECT:
    # NEW (FIXED):
    avg_acwr = (acute_chronic_ratio + trimp_acute_chronic_ratio) / 2
    normalized_divergence = (acute_chronic_ratio - trimp_acute_chronic_ratio) / avg_acwr
    # Mean-normalized with preserved valence (sign indicates direction of imbalance)

IMPACT:
All users with enhanced ACWR enabled had incorrect divergence values stored in database.
This affected LLM recommendations, dashboard displays, and coach advice.

USAGE:
    python scripts/migrations/fix_enhanced_acwr_divergence.py

AUTHOR: Claude Code (Architectural Audit Fix)
DATE: 2025-12-13
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from db_credentials_loader import set_database_url
set_database_url()

import db_utils
from unified_metrics_service import UnifiedMetricsService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_divergence_for_all_users():
    """
    Recalculate normalized divergence for all activities using the corrected formula.
    """
    try:
        logger.info("="*80)
        logger.info("STARTING NORMALIZED DIVERGENCE FIX MIGRATION")
        logger.info("="*80)

        # Get all activities with ACWR values that need divergence recalculation
        activities = db_utils.execute_query("""
            SELECT
                activity_id,
                user_id,
                date,
                acute_chronic_ratio,
                trimp_acute_chronic_ratio,
                normalized_divergence as old_divergence
            FROM activities
            WHERE
                acute_chronic_ratio IS NOT NULL
                AND trimp_acute_chronic_ratio IS NOT NULL
                AND activity_id > 0
            ORDER BY user_id, date ASC
        """, fetch=True)

        if not activities:
            logger.info("No activities found with ACWR values. Migration complete.")
            return {
                'success': True,
                'activities_processed': 0,
                'message': 'No activities to migrate'
            }

        logger.info(f"Found {len(activities)} activities with ACWR values to recalculate")

        updated_count = 0
        unchanged_count = 0
        error_count = 0

        for activity in activities:
            try:
                activity_id = activity['activity_id']
                external_acwr = float(activity['acute_chronic_ratio'] or 0)
                internal_acwr = float(activity['trimp_acute_chronic_ratio'] or 0)
                old_divergence = float(activity['old_divergence'] or 0)

                # Calculate correct normalized divergence using canonical formula
                new_divergence = UnifiedMetricsService._calculate_normalized_divergence(
                    external_acwr,
                    internal_acwr
                )

                # Only update if value actually changed (avoid unnecessary writes)
                if abs(new_divergence - old_divergence) > 0.001:
                    db_utils.execute_query("""
                        UPDATE activities
                        SET normalized_divergence = %s
                        WHERE activity_id = %s
                    """, (new_divergence, activity_id))

                    updated_count += 1

                    if updated_count % 100 == 0:
                        logger.info(f"Progress: {updated_count} activities updated...")
                else:
                    unchanged_count += 1

            except Exception as activity_error:
                logger.error(f"Error processing activity {activity.get('activity_id')}: {str(activity_error)}")
                error_count += 1

        # Summary
        logger.info(f"\n{'='*80}")
        logger.info("MIGRATION SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total activities processed: {len(activities)}")
        logger.info(f"Updated with corrected divergence: {updated_count}")
        logger.info(f"Unchanged (already correct): {unchanged_count}")
        logger.info(f"Errors: {error_count}")

        logger.info(f"\n{'='*80}")
        logger.info("MIGRATION COMPLETE")
        logger.info(f"{'='*80}")

        return {
            'success': True,
            'activities_processed': len(activities),
            'updated': updated_count,
            'unchanged': unchanged_count,
            'errors': error_count
        }

    except Exception as e:
        logger.error(f"Fatal error in migration: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    logger.info("Starting normalized divergence fix migration...")
    result = fix_divergence_for_all_users()

    if result['success']:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error(f"Migration failed: {result.get('error')}")
        sys.exit(1)
