#!/usr/bin/env python
"""Quick script to check birthdate field schema in user_settings table"""

from db_utils import execute_query

try:
    # Check if birthdate column exists and its type
    result = execute_query("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'user_settings'
        AND column_name IN ('birthdate', 'age', 'email', 'gender')
        ORDER BY column_name
    """, fetch=True)

    print("user_settings table columns:")
    print("-" * 60)
    for row in result:
        print(f"Column: {row['column_name']:15} Type: {row['data_type']:20} Nullable: {row['is_nullable']}")

    # Also check if there's any data in birthdate field
    count_result = execute_query("""
        SELECT
            COUNT(*) as total_users,
            COUNT(birthdate) as users_with_birthdate,
            COUNT(age) as users_with_age
        FROM user_settings
    """, fetch=True)

    if count_result:
        print("\nData status:")
        print("-" * 60)
        print(f"Total users: {count_result[0]['total_users']}")
        print(f"Users with birthdate: {count_result[0]['users_with_birthdate']}")
        print(f"Users with age: {count_result[0]['users_with_age']}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
