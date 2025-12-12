#!/usr/bin/env python3
"""Check device_name data in activities table"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
set_database_url()
import db_utils

print("="*80)
print("DEVICE_NAME DATA CHECK")
print("="*80)

# Simple count query
print("\n1. Data population counts:")
results = db_utils.execute_query("""
    SELECT COUNT(*) as count FROM activities WHERE activity_id > 0
""", fetch=True)
total = results[0]['count'] if results else 0
print(f"  Total activities: {total}")

results = db_utils.execute_query("""
    SELECT COUNT(*) as count FROM activities WHERE activity_id > 0 AND device_name IS NOT NULL
""", fetch=True)
with_device = results[0]['count'] if results else 0
print(f"  With device_name: {with_device} ({with_device/total*100 if total > 0 else 0:.1f}%)")

results = db_utils.execute_query("""
    SELECT COUNT(*) as count FROM activities WHERE activity_id > 0 AND device_name ILIKE '%garmin%'
""", fetch=True)
garmin = results[0]['count'] if results else 0
print(f"  Garmin devices:   {garmin}")

# Show recent activities
print("\n2. Recent 10 activities:")
print("-" * 80)
results = db_utils.execute_query("""
    SELECT activity_id, date, name, type, device_name
    FROM activities
    WHERE activity_id > 0
    ORDER BY date DESC
    LIMIT 10
""", fetch=True)

if results:
    for row in results:
        device = row['device_name'] if row['device_name'] else 'NULL'
        print(f"{row['date']} | {row['type']:20s} | {device}")
else:
    print("  No activities found")

# Show unique devices
print("\n3. Unique device names:")
print("-" * 80)
results = db_utils.execute_query("""
    SELECT device_name, COUNT(*) as count
    FROM activities
    WHERE activity_id > 0 AND device_name IS NOT NULL
    GROUP BY device_name
    ORDER BY count DESC
    LIMIT 10
""", fetch=True)

if results:
    for row in results:
        print(f"  {row['device_name']:40s} ({row['count']} activities)")
else:
    print("  No device names found in database")

print("\n" + "="*80)
