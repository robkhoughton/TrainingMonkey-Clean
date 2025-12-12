#!/usr/bin/env python3
"""
Independent Database Script: Add Timezone Column to user_settings
TrainingMonkey - Phase 1 of Multi-Timezone Support

This script adds a timezone column to the user_settings table and sets all
existing users to 'US/Pacific' since they are all currently in Pacific timezone.

This is an independent script, not part of the application codebase.
"""

import psycopg2
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection string - load from .env file (never hardcode credentials)
from db_credentials_loader import set_database_url
import os

set_database_url()
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    logger.error("ERROR: DATABASE_URL not found. Please ensure .env file exists with DATABASE_URL set.")
    sys.exit(1)

def add_timezone_column():
    """Add timezone column to user_settings table"""
    try:
        # Connect to database
        logger.info("Connecting to database...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if column already exists
        logger.info("Checking if timezone column already exists...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_settings' AND column_name = 'timezone'
        """)
        
        if cursor.fetchone():
            logger.info("✅ Timezone column already exists")
            return True
        
        # Add timezone column with US/Pacific default
        logger.info("Adding timezone column to user_settings table...")
        cursor.execute("""
            ALTER TABLE user_settings 
            ADD COLUMN timezone VARCHAR(50) DEFAULT 'US/Pacific'
        """)
        
        # Commit the change
        conn.commit()
        logger.info("✅ Successfully added timezone column")
        
        # Verify the column was added
        logger.info("Verifying column was added...")
        cursor.execute("""
            SELECT column_name, data_type, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'user_settings' AND column_name = 'timezone'
        """)
        
        result = cursor.fetchone()
        if result:
            logger.info(f"✅ Column verified: {result[0]} ({result[1]}) DEFAULT {result[2]}")
        else:
            logger.error("❌ Column verification failed")
            return False
        
        # Check current user count and timezone distribution
        logger.info("Checking existing users...")
        cursor.execute("SELECT COUNT(*) FROM user_settings")
        user_count = cursor.fetchone()[0]
        logger.info(f"Total users: {user_count}")
        
        cursor.execute("SELECT timezone, COUNT(*) FROM user_settings GROUP BY timezone")
        timezone_dist = cursor.fetchall()
        for tz, count in timezone_dist:
            logger.info(f"  {tz}: {count} users")
        
        return True
        
    except psycopg2.Error as e:
        logger.error(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        logger.info("Database connection closed")

def main():
    """Main function"""
    logger.info("🕐 TrainingMonkey: Adding Timezone Column to user_settings")
    logger.info("=" * 60)
    
    success = add_timezone_column()
    
    if success:
        logger.info("🎉 Phase 1 completed successfully!")
        logger.info("All existing users are now set to 'US/Pacific' timezone")
        logger.info("Ready to proceed with Phase 2: timezone utilities")
    else:
        logger.error("❌ Phase 1 failed - please check errors above")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

