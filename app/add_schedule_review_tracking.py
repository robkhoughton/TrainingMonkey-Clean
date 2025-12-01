#!/usr/bin/env python3
"""
Migration: Add schedule review tracking to user_settings table.

Adds:
- schedule_review_week_start: DATE - tracks which week's schedule was last reviewed
- schedule_review_status: VARCHAR - 'pending', 'accepted', 'updated'
- schedule_review_timestamp: TIMESTAMP - when review was completed

This enables the Sunday afternoon schedule review prompt system.

NOTE: Run this on the server where DATABASE_URL is configured, or manually execute the SQL.
"""

# SQL to run manually if needed:
SQL_MIGRATION = """
ALTER TABLE user_settings
ADD COLUMN IF NOT EXISTS schedule_review_week_start DATE,
ADD COLUMN IF NOT EXISTS schedule_review_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS schedule_review_timestamp TIMESTAMP;
"""

if __name__ == '__main__':
    print("=" * 60)
    print("SCHEDULE REVIEW TRACKING MIGRATION")
    print("=" * 60)
    print("\nExecute this SQL on your PostgreSQL database:\n")
    print(SQL_MIGRATION)
    print("\n" + "=" * 60)
    
    try:
        from db_credentials_loader import set_database_url
        import db_utils
        import logging
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        set_database_url()
        logger.info("Running migration...")
        
        db_utils.execute_query(SQL_MIGRATION)
        logger.info("✅ Migration successful!")
        
    except Exception as e:
        print(f"\n⚠️  Could not run automatically: {e}")
        print("Please run the SQL above manually on your database.")


