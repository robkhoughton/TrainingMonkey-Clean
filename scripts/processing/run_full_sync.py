from strava_training_load import connect_to_strava, process_activities_for_date_range, ensure_daily_records, update_moving_averages
from datetime import datetime, timedelta

print("Running full Strava sync...")

client = connect_to_strava()
if not client:
    print("❌ Connection failed")
    exit()

# Get 45 days of data
end_date = datetime.now()
start_date = end_date - timedelta(days=45)
start_date_str = start_date.strftime('%Y-%m-%d')
end_date_str = end_date.strftime('%Y-%m-%d')

hr_config = {'resting_hr': 44, 'max_hr': 178, 'gender': 'male'}

print(f"Syncing {start_date_str} to {end_date_str}...")
count = process_activities_for_date_range(client, start_date_str, end_date_str, hr_config)
print(f"Processed {count} activities")

print("Creating rest days...")
ensure_daily_records(start_date_str, end_date_str)

print("Updating moving averages...")
current_date = start_date
while current_date <= end_date:
    date_str = current_date.strftime('%Y-%m-%d')
    update_moving_averages(date_str)
    current_date += timedelta(days=1)

print("✅ Full sync complete!")