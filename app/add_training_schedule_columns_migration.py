#!/usr/bin/env python3
"""
Migration: Add training schedule columns to user_settings table
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
if not set_database_url():
    print("ERROR: Could not load DATABASE_URL")
    sys.exit(1)

import db_utils

def run_migration():
    print("=" * 60)
    print("Adding training schedule columns to user_settings")
    print("=" * 60)
    
    try:
        print("[1/8] Adding training_schedule_json column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS training_schedule_json JSONB
        """)
        print("    OK")
        
        print("[2/8] Adding include_strength_training column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS include_strength_training BOOLEAN DEFAULT FALSE
        """)
        print("    OK")
        
        print("[3/8] Adding strength_hours_per_week column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS strength_hours_per_week REAL DEFAULT 0
        """)
        print("    OK")
        
        print("[4/8] Adding include_mobility column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS include_mobility BOOLEAN DEFAULT FALSE
        """)
        print("    OK")
        
        print("[5/8] Adding mobility_hours_per_week column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS mobility_hours_per_week REAL DEFAULT 0
        """)
        print("    OK")
        
        print("[6/8] Adding include_cross_training column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS include_cross_training BOOLEAN DEFAULT FALSE
        """)
        print("    OK")
        
        print("[7/8] Adding cross_training_type column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS cross_training_type VARCHAR(50)
        """)
        print("    OK")
        
        print("[8/8] Adding cross_training_hours_per_week column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS cross_training_hours_per_week REAL DEFAULT 0
        """)
        print("    OK")
        
        print("[9/9] Adding schedule_last_updated column...")
        db_utils.execute_query("""
            ALTER TABLE user_settings 
            ADD COLUMN IF NOT EXISTS schedule_last_updated TIMESTAMP
        """)
        print("    OK")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Migration completed successfully")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)


