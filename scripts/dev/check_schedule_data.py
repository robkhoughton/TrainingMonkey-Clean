"""
Check training schedule data for the current user
"""
import sys
import json
sys.path.insert(0, 'C:\\Users\\robho\\documents\\trainingmonkey-clean')

from app import db_utils

# Get user ID (update this to your user ID)
user_id = 1  # Change this to your actual user ID

result = db_utils.execute_query(
    """
    SELECT training_schedule_json
    FROM user_settings
    WHERE id = %s
    """,
    (user_id,),
    fetch=True
)

if result and len(result) > 0:
    schedule_json = result[0].get('training_schedule_json')
    if schedule_json:
        if isinstance(schedule_json, str):
            schedule = json.loads(schedule_json)
        else:
            schedule = schedule_json

        print("Current training schedule data:")
        print(json.dumps(schedule, indent=2))

        if 'available_days' in schedule:
            days = schedule['available_days']
            print(f"\nAvailable days count: {len(days)}")
            print(f"Available days: {days}")

            # Check for duplicates
            unique_days = list(set(days))
            if len(unique_days) != len(days):
                print(f"\n⚠️ DUPLICATES FOUND! Unique count: {len(unique_days)}")
                print(f"Unique days: {unique_days}")
    else:
        print("No training schedule configured")
else:
    print(f"No user found with ID {user_id}")
