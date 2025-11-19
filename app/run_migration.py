#!/usr/bin/env python3
"""
Schema migration script to add start_time and device_name fields to activities table
Uses the existing db_utils module for database connection
"""

import sys
import os

# Ensure we're in the app directory context
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load database credentials from .env file
from db_credentials_loader import set_database_url
if not set_database_url():
    print("ERROR: Could not load DATABASE_URL from .env file")
    print("Please ensure .env file exists in project root with DATABASE_URL set")
    sys.exit(1)

import db_utils

def run_migration():
    """Execute the schema migration using db_utils"""
    
    print("=" * 60)
    print("SCHEMA MIGRATION: Adding start_time and device_name columns")
    print("=" * 60)
    
    try:
        # Migration 1: Add start_time column
        print("\n[1/2] Adding start_time column...")
        migration_1 = "ALTER TABLE activities ADD COLUMN IF NOT EXISTS start_time TEXT"
        
        try:
            db_utils.execute_query(migration_1)
            print("[OK] Successfully added start_time column")
        except Exception as e:
            print(f"[ERROR] Error adding start_time column: {str(e)}")
            if "already exists" not in str(e).lower():
                raise
            else:
                print("  (Column already exists, skipping)")
        
        # Migration 2: Add device_name column
        print("\n[2/2] Adding device_name column...")
        migration_2 = "ALTER TABLE activities ADD COLUMN IF NOT EXISTS device_name TEXT"
        
        try:
            db_utils.execute_query(migration_2)
            print("[OK] Successfully added device_name column")
        except Exception as e:
            print(f"[ERROR] Error adding device_name column: {str(e)}")
            if "already exists" not in str(e).lower():
                raise
            else:
                print("  (Column already exists, skipping)")
        
        # Verify the columns exist
        print("\n[Verification] Checking columns...")
        verification_query = """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'activities' 
            AND column_name IN ('start_time', 'device_name')
            ORDER BY column_name
        """
        
        columns = db_utils.execute_query(verification_query, fetch=True)
        
        if columns and len(columns) >= 2:
            print(f"\n[OK] Verified {len(columns)} new columns exist:")
            for row in columns:
                col_name = row.get('column_name') or row[0]
                col_type = row.get('data_type') or row[1]
                print(f"  - {col_name} ({col_type})")
        else:
            print(f"\n[WARNING] Expected 2 columns, found {len(columns) if columns else 0}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Deploy updated backend code")
        print("2. Deploy updated frontend")
        print("3. Trigger Strava sync to populate new fields")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("[FAILED] MIGRATION FAILED!")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

