#!/usr/bin/env python3
"""
Migration Script: Recalculate ACWR for Users with Custom Dashboard Configs

PURPOSE:
This script fixes the ACWR inconsistency issue where Dashboard showed different
metrics than LLM recommendations. It recalculates all historical ACWR values in
the database for users who have custom dashboard configurations.

ROOT CAUSE FIXED:
Previously, custom ACWR configs only recalculated values on-the-fly for Dashboard
display. This caused LLM recommendations (and other features) to cite different
metrics since they read from database. Now, database becomes single source of truth.

WHAT THIS MIGRATION DOES:
1. Identifies all users with active custom dashboard configurations
2. For each user, recalculates ALL historical ACWR values using their custom config
3. Updates the activities table with recalculated values
4. Ensures consistency across Dashboard, LLM, Autopsy, Coach, and all features

USAGE:
    python scripts/migrations/migrate_custom_acwr_configs.py

AUTHOR: Claude Code (Troubleshooting Protocol Fix)
DATE: 2025-12-13
"""

import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from db_credentials_loader import set_database_url
set_database_url()

# Initialize connection pool for batch operations
from db_connection_manager import initialize_database_pool
initialize_database_pool()

import db_utils
from optimized_acwr_service import OptimizedACWRService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_custom_acwr_configs():
    """
    Migrate existing users with custom dashboard configs to use database-stored ACWR.
    """
    try:
        logger.info("="*80)
        logger.info("STARTING ACWR MIGRATION FOR USERS WITH CUSTOM CONFIGS")
        logger.info("="*80)

        # Get all users with active custom dashboard configurations
        users_with_configs = db_utils.execute_query("""
            SELECT
                user_id,
                chronic_period_days,
                decay_rate,
                created_at,
                updated_at
            FROM user_dashboard_configs
            WHERE is_active = TRUE
            ORDER BY user_id ASC
        """, fetch=True)

        if not users_with_configs:
            logger.info("No users with active custom dashboard configs found. Migration complete.")
            return {
                'success': True,
                'users_processed': 0,
                'message': 'No custom configs to migrate'
            }

        logger.info(f"Found {len(users_with_configs)} users with custom ACWR configs")

        acwr_service = OptimizedACWRService()
        results = []

        for config in users_with_configs:
            user_id = config['user_id']
            chronic_period_days = config['chronic_period_days']
            decay_rate = config['decay_rate']

            logger.info(f"\n{'='*60}")
            logger.info(f"Processing User ID: {user_id}")
            logger.info(f"Custom Config: chronic={chronic_period_days}d, decay={decay_rate}")
            logger.info(f"{'='*60}")

            try:
                # Get user's activity date range
                date_range = db_utils.execute_query("""
                    SELECT MIN(date) as start_date, MAX(date) as end_date
                    FROM activities
                    WHERE user_id = %s AND activity_id > 0
                """, (user_id,), fetch=True)

                if not date_range or not date_range[0]['start_date']:
                    logger.warning(f"User {user_id} has no activities - skipping")
                    results.append({
                        'user_id': user_id,
                        'success': True,
                        'updated_count': 0,
                        'message': 'No activities found'
                    })
                    continue

                start_date = date_range[0]['start_date']
                end_date = date_range[0]['end_date']

                # Format dates
                if hasattr(start_date, 'strftime'):
                    start_date_str = start_date.strftime('%Y-%m-%d')
                else:
                    start_date_str = str(start_date)
                if hasattr(end_date, 'strftime'):
                    end_date_str = end_date.strftime('%Y-%m-%d')
                else:
                    end_date_str = str(end_date)

                logger.info(f"Recalculating ACWR from {start_date_str} to {end_date_str}")

                # Recalculate all ACWR values with custom config
                result = acwr_service.recalculate_user_acwr_range(
                    user_id=user_id,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    chronic_period_days=chronic_period_days,
                    decay_rate=decay_rate
                )

                updated_count = result.get('database_updates', 0)
                logger.info(f"✅ User {user_id}: Successfully updated {updated_count} activities")

                results.append({
                    'user_id': user_id,
                    'success': True,
                    'updated_count': updated_count,
                    'chronic_period_days': chronic_period_days,
                    'decay_rate': decay_rate
                })

            except Exception as user_error:
                logger.error(f"❌ Error processing user {user_id}: {str(user_error)}", exc_info=True)
                results.append({
                    'user_id': user_id,
                    'success': False,
                    'error': str(user_error)
                })

        # Summary
        logger.info(f"\n{'='*80}")
        logger.info("MIGRATION SUMMARY")
        logger.info(f"{'='*80}")

        successful = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])
        total_updated = sum(r.get('updated_count', 0) for r in results if r['success'])

        logger.info(f"Total users processed: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total activities updated: {total_updated}")

        if failed > 0:
            logger.warning("\nFailed users:")
            for r in results:
                if not r['success']:
                    logger.warning(f"  User {r['user_id']}: {r.get('error', 'Unknown error')}")

        logger.info(f"\n{'='*80}")
        logger.info("MIGRATION COMPLETE")
        logger.info(f"{'='*80}")

        return {
            'success': True,
            'users_processed': len(results),
            'successful': successful,
            'failed': failed,
            'total_activities_updated': total_updated,
            'results': results
        }

    except Exception as e:
        logger.error(f"Fatal error in migration: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == '__main__':
    logger.info("Starting ACWR migration script...")
    result = migrate_custom_acwr_configs()

    if result['success']:
        logger.info("Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error(f"Migration failed: {result.get('error')}")
        sys.exit(1)
