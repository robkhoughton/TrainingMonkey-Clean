#!/usr/bin/env python3
"""Check device_name column in activities table"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
set_database_url()
import db_utils

print("="*80)
print("CHECKING DEVICE_NAME COLUMN IN ACTIVITIES TABLE")
print("="*80)

# Check if column exists and get counts
print("\n1. Column existence and data population:")
results = db_utils.execute_query("""
    SELECT
        COUNT(*) as total_activities,
        COUNT(device_name) as has_device_name,
        COUNT(CASE WHEN device_name ILIKE '%garmin%' THEN 1 END) as garmin_devices
    FROM activities
    WHERE activity_id > 0
""", fetch=True)

if results:
    row = results[0]
    total = row['total_activities']
    has_device = row['has_device_name']
    garmin = row['garmin_devices']
    print(f"  Total activities: {total}")
    print(f"  With device_name: {has_device} ({has_device/total*100 if total > 0 else 0:.1f}%)")
    print(f"  Garmin devices:   {garmin} ({garmin/total*100 if total > 0 else 0:.1f}%)")

# Show recent activities with device names
print("\n2. Sample of recent activities (last 20):")
print("-" * 80)
results = db_utils.execute_query("""
    SELECT
        activity_id,
        date,
        name,
        type,
        device_name
    FROM activities
    WHERE activity_id > 0
    ORDER BY date DESC
    LIMIT 20
""", fetch=True)

if results:
    for row in results:
        device = row['device_name'] or 'NULL'
        is_garmin = '🟢 GARMIN' if row['device_name'] and 'garmin' in row['device_name'].lower() else ''
        print(f"{row['date']} | {row['type']:15s} | {device:30s} {is_garmin}")
else:
    print("  No activities found")

# Show unique device names
print("\n3. All unique device names:")
print("-" * 80)
results = db_utils.execute_query("""
    SELECT
        device_name,
        COUNT(*) as count
    FROM activities
    WHERE activity_id > 0 AND device_name IS NOT NULL
    GROUP BY device_name
    ORDER BY count DESC
""", fetch=True)

if results:
    for row in results:
        is_garmin = '🟢' if 'garmin' in row['device_name'].lower() else ''
        print(f"  {is_garmin} {row['device_name']:40s} ({row['count']} activities)")
else:
    print("  No device names found in database")

print("\n" + "="*80)
