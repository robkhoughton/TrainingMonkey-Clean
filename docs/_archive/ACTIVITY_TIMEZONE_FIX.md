# Activity Timezone Date Fix

## Problem

A bug in `app/strava_training_load.py:903` caused activity dates to be extracted from `activity.start_date` (UTC) instead of `activity.start_date_local` (athlete's local timezone).

### Impact

Activities recorded in the evening hours (typically after 4-5 PM local time, depending on timezone) were assigned to the **next day** in the database.

**Example:**
- Activity: Yoga at 8:50 PM Pacific on 12/11/2025
- **Incorrect (bug)**: Stored as 12/12/2025 (because 8:50 PM Pacific = 4:50 AM UTC next day)
- **Correct (fixed)**: Should be 12/11/2025 (athlete's local date)

## The Fix

### Code Fix (Completed)
Changed line 903 in `app/strava_training_load.py`:
```python
# BEFORE (incorrect - used UTC)
activity_date = activity.start_date.strftime('%Y-%m-%d')

# AFTER (correct - uses local timezone)
activity_date = activity.start_date_local.strftime('%Y-%m-%d')
```

### Data Fix (This Script)
The code fix only affects **new** activities synced after the fix. Existing activities with incorrect dates need to be corrected.

## How to Fix Existing Activities

### Step 1: Find Your User ID

Run this query in your PostgreSQL database:
```sql
SELECT id, username, email FROM user_settings;
```

Or check the application logs when you log in - your user ID is displayed.

### Step 2: Dry-Run Mode (Recommended First)

Run the script in dry-run mode to see what would be fixed **without making any changes**:

```cmd
cd scripts
fix_activity_dates.bat YOUR_USER_ID
```

**Example:**
```cmd
fix_activity_dates.bat 1
```

This will:
- ✅ Check all activities from the last 90 days
- ✅ Compare stored dates with correct Strava dates
- ✅ Report which activities have incorrect dates
- ❌ **NOT** make any database changes

### Step 3: Review the Output

The script will show:
```
Checking activity 12345678: 'Evening Yoga' (stored: 2025-12-12)
  ❌ INCORRECT: Activity 12345678
     Stored: 2025-12-12
     Correct (local): 2025-12-11
     UTC: 2025-12-12
     Start time: 20:50:00
     Timezone: (GMT-08:00) America/Los_Angeles
```

### Step 4: Apply the Fix

If the dry-run looks correct, run again with `--fix` flag:

```cmd
cd scripts
fix_activity_dates.bat YOUR_USER_ID --fix
```

**Example:**
```cmd
fix_activity_dates.bat 1 --fix
```

You'll be prompted for confirmation before any changes are made.

## What the Script Does

1. **Fetches activities** from your database (last 90 days by default)
2. **Re-queries Strava API** to get the correct `start_date_local` for each activity
3. **Compares** stored date with correct local date
4. **Updates** activities with incorrect dates
5. **Recalculates** ACWR and moving averages for affected dates

## Advanced Options

### Check More/Fewer Days

By default, the script checks the last 90 days. To check a different range:

```cmd
python fix_activity_timezone_dates.py USER_ID --days 180
```

### Full Command-Line Usage

```cmd
python fix_activity_timezone_dates.py USER_ID [--days DAYS] [--fix]

Arguments:
  USER_ID       Your user ID (required)
  --days DAYS   Number of days to check (default: 90)
  --fix         Actually fix the dates (default is dry-run)
```

## Example Output

### Dry-Run Mode
```
[2025-12-12 10:30:15] INFO - Starting activity date fix for user 1
[2025-12-12 10:30:15] INFO - Checking activities from 2025-09-13 to 2025-12-12
[2025-12-12 10:30:16] INFO - Found 45 activities to check

[2025-12-12 10:30:17] INFO - Checking activity 12345678: 'Evening Yoga' (stored: 2025-12-12)
[2025-12-12 10:30:17] WARNING -   ❌ INCORRECT: Activity 12345678
[2025-12-12 10:30:17] WARNING -      Stored: 2025-12-12
[2025-12-12 10:30:17] WARNING -      Correct (local): 2025-12-11
[2025-12-12 10:30:17] WARNING -      UTC: 2025-12-12
[2025-12-12 10:30:17] WARNING -      Start time: 20:50:00

[2025-12-12 10:30:18] INFO - Checking activity 87654321: 'Morning Run' (stored: 2025-12-11)
[2025-12-12 10:30:18] INFO -   ✅ OK: Date is correct (2025-12-11)

======================================================================
SUMMARY
======================================================================
Total activities checked: 45
Activities with incorrect dates: 8

⚠️  DRY RUN MODE - No changes were made
Run with --fix flag to apply corrections
```

### Fix Mode
```
[2025-12-12 10:35:20] INFO - Starting activity date fix for user 1
[2025-12-12 10:35:21] INFO - Found 45 activities to check

[2025-12-12 10:35:22] INFO - Updating activity 12345678: 2025-12-12 -> 2025-12-11
[2025-12-12 10:35:22] INFO -   ✅ Fixed activity 12345678

[2025-12-12 10:35:30] INFO - Recalculating metrics for 12 affected dates...
[2025-12-12 10:35:31] INFO - Recalculating metrics for 2025-12-11
[2025-12-12 10:35:31] INFO - Recalculating metrics for 2025-12-12

======================================================================
SUMMARY
======================================================================
Total activities checked: 45
Activities with incorrect dates: 8
Activities fixed: 8
Dates affected: 12
Metrics recalculated: 12

✅ Fix completed successfully
```

## Verification

After running the fix:

1. **Check the Activities page** - Evening activities should now appear on the correct date
2. **Check the Dashboard** - ACWR values should be recalculated for affected dates
3. **Check the Journal** - Recommendations should align with the correct activity dates

## Troubleshooting

### "No Strava tokens found for user X"
- Make sure the user ID is correct
- Verify the user has connected their Strava account

### "Failed to connect to Strava"
- Check your Strava API credentials in the `.env` file
- Verify your internet connection

### "Could not fetch activity from Strava"
- The activity may have been deleted from Strava
- Strava API rate limits may apply (script automatically handles rate limiting)

## Safety Features

- **Dry-run by default** - No changes are made unless you use `--fix` flag
- **Confirmation prompt** - Asks for confirmation before applying fixes
- **Detailed logging** - Shows exactly what will be/was changed
- **Automatic recalculation** - Updates ACWR and moving averages for affected dates

## Related Documentation

- **Bug Fix**: See git commit for code change in `strava_training_load.py`
- **Timezone Policy**: See `docs/reference/guiding_principles_summary.md`
- **Timezone History**: See `archive/old_docs/TIMEZONE_DATE_ATTRIBUTION_FIX.md`
