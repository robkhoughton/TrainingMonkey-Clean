# Garmin Device Attribution - Troubleshooting Guide

## ✅ ISSUE RESOLVED (December 4, 2025)

**Root Cause Identified**: The code was using Strava's `get_activities()` API which returns SummaryActivity objects that lack the `device_name` field. Device names are only available in DetailedActivity objects returned by `get_activity(id)`.

**Fix Applied**: Modified `strava_training_load.py` to fetch detailed activity information before processing each activity. This ensures device_name is captured correctly.

**Status**:
- ✅ Fix implemented in `strava_training_load.py` (lines 1878-1890)
- ⏳ Awaiting deployment and testing
- ⚠️ Existing 2,842 activities have NULL device_name (will need re-sync or backfill)

---

## Where to Find the Attribution

**Page**: Activities Page (not Dashboard, not Journal)
**Location**: Third column "Activity" → beneath the activity name

### Visual Layout:
```
Date        Type           Activity                    Duration  Miles  ...
-----------------------------------------------------------------------
11/18 Mon   Trail Run      Morning Run                 0:45      5.2
                           Garmin Forerunner 965       ← HERE
                           View on Strava
```

The device name appears:
- **Small gray italic text** (0.7rem font size)
- **Directly below** the activity name
- **Above** the "View on Strava" link
- **Only for Garmin devices** (contains "garmin" in the name)

## Root Cause Analysis

### The Problem
All 2,842 activities in the database have NULL `device_name` values because the original implementation had a critical flaw:

**Original Code** (`strava_training_load.py:754`):
```python
device_name = getattr(activity, 'device_name', None)
```

This code attempted to extract `device_name` from activity objects, but:

### Strava API Activity Types
1. **SummaryActivity** (from `get_activities()`)
   - Lightweight, minimal fields
   - ❌ Does NOT include `device_name`
   - Used for listing multiple activities

2. **DetailedActivity** (from `get_activity(id)`)
   - Complete activity information
   - ✅ Includes `device_name` and other detailed fields
   - Used for individual activity details

### Why It Failed
- The code called `client.get_activities()` which returns SummaryActivity objects
- Attempted to read `device_name` from these summary objects
- Field doesn't exist on summary objects, so `getattr()` always returned None
- Database was populated with NULL values for all activities

## The Fix

### Code Change (December 4, 2025)
Modified `app/strava_training_load.py` around lines 1878-1890:

```python
# Fetch detailed activity to get device_name (required for Garmin attribution)
# Note: get_activities() returns SummaryActivity which lacks device_name
# We need to call get_activity() to get DetailedActivity with all fields
try:
    detailed_activity = client.get_activity(activity_id)
    logger.info(f"Fetched detailed activity {activity_id} for device attribution")
except Exception as e:
    logger.warning(f"Could not fetch detailed activity {activity_id}: {e}. Using summary data.")
    detailed_activity = activity

# Calculate training load (only for supported activities)
logger.info(f"PROCESSING supported activity {activity_id}: {activity_type}")
load_data = calculate_training_load(detailed_activity, client, hr_config, user_id)
```

### What This Does
1. Fetches detailed activity information using `client.get_activity(activity_id)`
2. Passes the detailed activity (with device_name) to `calculate_training_load()`
3. Falls back to summary data if detailed fetch fails (graceful degradation)
4. Logs the fetch for debugging purposes

### Impact
- **New Activities**: Will correctly capture device_name after deployment
- **Existing Activities**: Still have NULL device_name (need backfill)
- **Performance**: Adds one additional API call per activity during sync
- **Rate Limits**: Existing 1-second delay between activities should handle this

## Deployment Steps

### 1. Deploy Backend Code
```bash
# The fix is in app/strava_training_load.py (lines 1878-1890)
# Deploy according to your normal backend deployment process
```

### 2. Test with New Activity Sync

After deployment:
1. Navigate to your Strava sync page/button in the application
2. Click "Sync Strava Data" to fetch recent activities
3. Monitor logs to confirm detailed activities are being fetched:
   - Look for: "Fetched detailed activity [ID] for device attribution"
4. Navigate to Activities page
5. Check if newly synced activities show device attribution

### 3. Verify Database Population

Check that new activities have device_name:
```bash
cd app
python check_device_data.py
```

Expected output after syncing new activities:
```
Total activities: 2842
With device_name: [some number > 0]
Garmin devices: [number of Garmin activities]
```

### 4. Verify Frontend Display

After syncing activities:
1. Navigate to Activities page
2. Look for device attribution beneath activity names for Garmin-recorded activities
3. Open browser DevTools (F12) → Network tab → Check `/api/activities-management` response
4. Verify some activities now have `device_name` populated (not null)

## Backfilling Existing Activities (Optional)

The fix only applies to newly synced activities. To populate device_name for existing 2,842 activities:

### Option 1: Wait for Natural Re-sync
- Device names will be populated as activities naturally get updated
- No action required, but will take time

### Option 2: Create a Backfill Script
A backfill script would:
1. Query all activities with NULL device_name
2. Fetch detailed activity info from Strava for each
3. Update device_name in database
4. Need to respect Strava API rate limits (200 requests per 15 minutes)

**Note**: Backfilling 2,842 activities would require approximately:
- 2,842 API calls
- ~3-4 hours to complete (with rate limiting)
- Consider backfilling only recent activities (e.g., last 90 days)

## Troubleshooting After Fix

### Device Names Still Not Appearing After Sync

**Check 1: Verify Detailed Activity Fetch**
Look in application logs for:
- ✅ "Fetched detailed activity [ID] for device attribution"
- ❌ "Could not fetch detailed activity [ID]" (indicates API issue)

**Check 2: Verify Device Name in Logs**
After the detailed fetch, look for:
- ✅ "Activity [ID] device: [device name]"
- If not present, the activity may not have device info in Strava

**Check 3: Database Query**
```bash
cd app
python -c "
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))
from db_credentials_loader import set_database_url
set_database_url()
import db_utils

results = db_utils.execute_query('''
    SELECT activity_id, date, name, device_name
    FROM activities
    WHERE device_name IS NOT NULL
    ORDER BY date DESC
    LIMIT 5
''', fetch=True)

for row in results:
    print(f\"{row['date']} | {row['name']} | {row['device_name']}\")
"
```

### Common Issues

**Issue**: "Could not fetch detailed activity" errors in logs
- **Cause**: Strava API authentication or rate limiting
- **Solution**: Check Strava access token is valid, verify rate limits

**Issue**: Device name is in database but not displaying
- **Cause**: Frontend deployment issue or device is not Garmin
- **Solution**: Rebuild and deploy frontend; verify device name contains "garmin"

**Issue**: Some activities have device_name, others don't
- **Cause**: Normal behavior - not all Strava activities have device information
- **Solution**: This is expected, only activities with device info will show attribution

## Display Conditions (Code Logic)

Device attribution displays when ALL these are true:
1. ✅ `activity.device_name` exists (not null/undefined)
2. ✅ `activity.device_name.toLowerCase().includes('garmin')` is true
3. ✅ You're on the Activities page (not Dashboard or Journal)
4. ✅ Looking at the "Activity" column (3rd column from left)

## Files Modified

- ✅ `app/strava_training_load.py` (lines 1878-1890) - Added detailed activity fetch
- ✅ `GARMIN_ATTRIBUTION_TROUBLESHOOTING.md` - Updated with root cause and fix

## Summary

**Problem**: SummaryActivity objects lack device_name field
**Solution**: Fetch DetailedActivity objects that include device_name
**Status**: Fixed, awaiting deployment and testing
**Next**: Deploy backend, sync new activities, verify device attribution displays




