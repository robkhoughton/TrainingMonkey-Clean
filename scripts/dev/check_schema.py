#!/usr/bin/env python3
"""Check activities table schema"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_credentials_loader import set_database_url
set_database_url()
import db_utils

print("="*80)
print("ACTIVITIES TABLE SCHEMA")
print("="*80)

# Get column information from information_schema
results = db_utils.execute_query("""
    SELECT
        column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns
    WHERE table_name = 'activities'
    ORDER BY ordinal_position
""", fetch=True)

if results:
    print(f"\nFound {len(results)} columns in 'activities' table:\n")
    for row in results:
        nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {row['column_default']}" if row['column_default'] else ""
        highlight = ">>> " if row['column_name'] == 'device_name' else "    "
        print(f"{highlight}{row['column_name']:30s} {row['data_type']:20s} {nullable:10s}{default}")

    # Check specifically for device_name
    has_device_name = any(row['column_name'] == 'device_name' for row in results)
    print("\n" + "="*80)
    if has_device_name:
        print("✅ device_name column EXISTS")
    else:
        print("❌ device_name column DOES NOT EXIST - Migration needed!")
    print("="*80)
else:
    print("\n❌ Could not retrieve schema information")
