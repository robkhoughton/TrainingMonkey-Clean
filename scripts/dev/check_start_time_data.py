#!/usr/bin/env python3
"""
Check if start_time and device_name fields are populated in the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url

# Load credentials BEFORE importing db_utils
if not set_database_url():
    print("ERROR: Could not load DATABASE_URL")
    sys.exit(1)

import db_utils

def check_data():
    
    print("=" * 60)
    print("Checking start_time and device_name data")
    print("=" * 60)
    
    try:
        # Check if columns exist
        print("\n1. Checking if columns exist...")
        columns = db_utils.execute_query("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'activities' 
            AND column_name IN ('start_time', 'device_name')
            ORDER BY column_name
        """, fetch=True)
        
        if columns:
            print(f"[OK] Found {len(columns)} columns:")
            for col in columns:
                print(f"  - {col.get('column_name') or col[0]}")
        else:
            print("[ERROR] Columns not found!")
            return False
        
        # Check total activities
        print("\n2. Checking total activities...")
        total = db_utils.execute_query("""
            SELECT COUNT(*) as count 
            FROM activities 
            WHERE activity_id > 0
        """, fetch=True)
        
        # Handle both dict and tuple results
        if hasattr(total[0], 'get'):
            total_count = total[0].get('count')
        else:
            total_count = total[0][0] if len(total[0]) > 0 else 0
        print(f"Total activities: {total_count}")
        
        # Check activities with start_time
        print("\n3. Checking activities with start_time...")
        with_time = db_utils.execute_query("""
            SELECT COUNT(*) as count 
            FROM activities 
            WHERE activity_id > 0 
            AND start_time IS NOT NULL
        """, fetch=True)
        
        # Handle both dict and tuple results
        if hasattr(with_time[0], 'get'):
            with_time_count = with_time[0].get('count')
        else:
            with_time_count = with_time[0][0] if len(with_time[0]) > 0 else with_time[0]['count']
        print(f"Activities with start_time: {with_time_count}")
        
        # Check activities with device_name
        print("\n4. Checking activities with device_name...")
        with_device = db_utils.execute_query("""
            SELECT COUNT(*) as count 
            FROM activities 
            WHERE activity_id > 0 
            AND device_name IS NOT NULL
        """, fetch=True)
        
        # Handle both dict and tuple results
        if hasattr(with_device[0], 'get'):
            with_device_count = with_device[0].get('count')
        else:
            with_device_count = with_device[0][0] if len(with_device[0]) > 0 else 0
        print(f"Activities with device_name: {with_device_count}")
        
        # Show sample of recent activities
        print("\n5. Sample of 5 most recent activities:")
        samples = db_utils.execute_query("""
            SELECT 
                date, 
                name, 
                start_time, 
                device_name,
                activity_id
            FROM activities 
            WHERE activity_id > 0
            ORDER BY date DESC 
            LIMIT 5
        """, fetch=True)
        
        for activity in samples:
            if hasattr(activity, 'get'):
                date = activity.get('date')
                name = activity.get('name')
                start_time = activity.get('start_time')
                device_name = activity.get('device_name')
                activity_id = activity.get('activity_id')
            else:
                date, name, start_time, device_name, activity_id = activity
            
            print(f"\n  Activity {activity_id}: {name}")
            print(f"    Date: {date}")
            print(f"    Start Time: {start_time if start_time else '(NULL - needs sync)'}")
            print(f"    Device: {device_name if device_name else '(NULL - needs sync)'}")
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        if with_time_count == 0:
            print("[WARNING] No activities have start_time data yet")
            print("ACTION REQUIRED: Trigger a Strava sync to populate the fields")
            print("\nHow to sync:")
            print("  1. Log into your app")
            print("  2. Go to Settings or Dashboard")
            print("  3. Click 'Sync with Strava'")
            print("  4. Wait for sync to complete")
            print("  5. Refresh Activities page")
        else:
            percentage = (with_time_count / total_count) * 100
            print(f"[OK] {with_time_count}/{total_count} activities have start_time ({percentage:.1f}%)")
            
            if percentage < 100:
                print(f"[WARNING] Some activities still need to be synced")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_data()
    sys.exit(0 if success else 1)

