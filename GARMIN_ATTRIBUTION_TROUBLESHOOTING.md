# Garmin Device Attribution - Troubleshooting Guide

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

## Most Likely Reason: Device Names Not Populated Yet

The `device_name` field was just added to the database. **Existing activities don't have device names yet.**

### Why Device Names Are Missing:
1. ✅ Database field added successfully
2. ✅ Backend code updated to capture device names
3. ✅ Frontend code updated to display device names
4. ⚠️ **BUT**: Only NEW activities synced AFTER deployment will have device names

### Solution: Sync Recent Activities

Device names will appear when you:
1. **Sync new activities from Strava** (using the sync button)
2. **Or**: Manually trigger a re-sync for recent activities

The device name is captured from Strava's API during the sync process, so only activities synced after this deployment will show device attribution.

## Verification Steps

### 1. Check Frontend Deployment
- Navigate to Activities page
- Open browser DevTools (F12)
- Go to Network tab
- Refresh the page
- Look for `/api/activities-management?days=30...` request
- Click on it → Preview → data → Check if any activity has `device_name` field

### 2. Check Backend Deployment
If you see `device_name: null` for all activities in the API response, it means:
- ✅ Backend is deployed (field is in the response)
- ⚠️ No activities have device names yet (need to sync)

If you DON'T see `device_name` field at all in the API response:
- ⚠️ Backend code not deployed yet
- ⚠️ Or frontend build not deployed yet

### 3. Check Database
After syncing a new activity from Strava, you can verify it has device_name:
```sql
SELECT activity_id, date, name, device_name 
FROM activities 
ORDER BY date DESC 
LIMIT 5;
```

## Quick Test

1. Go to Activities page
2. Click "Sync Strava Data" button
3. Wait for sync to complete
4. Refresh the Activities page
5. Look for device attribution beneath activity names

## If Still Not Showing After Sync

### Scenario A: Your Activities Don't Use Garmin Devices
- Device attribution only shows for Garmin devices
- If you use Apple Watch, Wahoo, etc., no attribution will show
- Check Strava activity details to see what device recorded it

### Scenario B: Strava API Doesn't Provide Device Name
- Some activities may not have device_name in Strava API
- This is expected and not an error

### Scenario C: Frontend Build Not Deployed
- Run the frontend build commands:
```bash
cd frontend
npm run build
cd ..
# Then copy build files per deployment script
```

## Display Conditions (Code Logic)

The device name will ONLY display if ALL these are true:
1. `activity.device_name` exists (not null/undefined)
2. `activity.device_name.toLowerCase().includes('garmin')` is true
3. You're on the Activities page (not Dashboard or Journal)
4. Looking at the "Activity" column (3rd column from left)

## Next Steps

1. **Sync some recent Strava activities**
2. **Check the Activities page** (not Dashboard)
3. **Look in the Activity column** beneath activity names
4. If still not showing, check browser console for errors
5. Verify backend deployment included the updated `strava_training_load.py` file


