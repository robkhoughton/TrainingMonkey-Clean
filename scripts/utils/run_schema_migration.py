#!/usr/bin/env python3
"""
Schema migration script to add start_time and device_name fields to activities table
"""

import os
import sys

# Add app directory to path to import db_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

import psycopg2
from psycopg2 import sql

def run_migration():
    """Execute the schema migration"""
    
    # Get database URL from environment variable (same as app uses)
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        print("Please set it using: set DATABASE_URL=postgresql://...")
        return False
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("Connected successfully!")
        
        # Execute migrations
        migrations = [
            ("start_time", "ALTER TABLE activities ADD COLUMN IF NOT EXISTS start_time TEXT"),
            ("device_name", "ALTER TABLE activities ADD COLUMN IF NOT EXISTS device_name TEXT")
        ]
        
        for field_name, migration_sql in migrations:
            print(f"\nExecuting migration for {field_name}...")
            try:
                cursor.execute(migration_sql)
                conn.commit()
                print(f"✓ Successfully added {field_name} field")
            except Exception as e:
                print(f"✗ Error adding {field_name} field: {str(e)}")
                conn.rollback()
                raise
        
        # Verify the columns exist
        print("\nVerifying columns...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'activities' 
            AND column_name IN ('start_time', 'device_name')
            ORDER BY column_name
        """)
        
        columns = cursor.fetchall()
        print(f"\nFound {len(columns)} new columns:")
        for col_name, col_type in columns:
            print(f"  - {col_name} ({col_type})")
        
        cursor.close()
        conn.close()
        
        print("\n✓ Migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    exit(0 if success else 1)

