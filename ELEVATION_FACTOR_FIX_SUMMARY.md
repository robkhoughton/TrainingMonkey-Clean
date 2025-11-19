# Elevation Factor Consistency Fix

## Problem Identified

The manual elevation update feature had three different conversion factors being used inconsistently:

1. **Database stored**: 850 ft/mile (incorrect - didn't match any sport type)
2. **API response returned**: 750 ft/mile (hardcoded running factor)
3. **Frontend displayed**: 1000 ft/mile (outdated legacy factor)

This created inconsistent training load calculations across the system.

## Root Cause

The `/api/activities-management/update-elevation` endpoint was using a **hardcoded 850 ft/mile** factor without considering the activity's sport type, resulting in incorrect calculations for:
- Running activities (should use 750 ft/mile)
- Cycling activities (should use 1100 ft/mile)
- Swimming activities (should use 0 ft/mile - no elevation)

## Solution Implemented

### Backend Fix (`app/strava_app.py`)

**Changes Made:**
1. Query now fetches `sport_type` and `type` fields along with `distance_miles`
2. Determines correct elevation factor based on activity type:
   - **Cycling**: 1100.0 ft/mile (matches `calculate_cycling_external_load`)
   - **Swimming**: 0.0 ft/mile (no elevation for swimming)
   - **Running/Default**: 750.0 ft/mile (matches `calculate_training_load`)
3. Calculates `elevation_load_miles` using the sport-specific factor
4. Stores the actual factor used in `elevation_factor_used` column
5. Returns the **same calculated values** in API response (no recalculation)

**Key Code:**
```python
# Determine sport-specific elevation factor
if sport_type.lower() == 'cycling':
    elevation_factor = 1100.0
elif sport_type.lower() == 'swimming':
    elevation_factor = 0.0
else:
    elevation_factor = 750.0

# Calculate with correct factor
elevation_load_miles = elevation_feet / elevation_factor if elevation_factor > 0 else 0.0
total_load_miles = current_distance + elevation_load_miles

# Return same values stored in database
return jsonify({
    'updated_values': {
        'elevation_gain_feet': elevation_feet,
        'elevation_load_miles': round(elevation_load_miles, 2),
        'total_load_miles': round(total_load_miles, 2),
        'elevation_factor_used': elevation_factor,
    }
})
```

### Frontend Fix (`frontend/src/ActivitiesPage.tsx`)

**Changes Made:**
1. Removed frontend recalculation using incorrect 1000 ft/mile factor
2. Now uses `total_load_miles` value returned from backend API
3. Ensures single source of truth (backend calculation only)

**Key Code:**
```typescript
// Use backend-calculated values instead of recalculating
setActivities(prev => prev.map(activity =>
  activity.activity_id === activityId
    ? {
        ...activity,
        elevation_gain_feet: result.updated_values.elevation_gain_feet,
        total_load_miles: result.updated_values.total_load_miles,
        has_missing_elevation: false,
        user_edited_elevation: true,
      }
    : activity
));
```

## Benefits

✅ **Sport-Specific Accuracy**: Running, cycling, and swimming now use correct conversion factors  
✅ **Consistency**: Database, API, and frontend all use the same values  
✅ **Alignment**: Matches the main training load calculation logic in `strava_training_load.py`  
✅ **Transparency**: Logs which factor is used for each activity  
✅ **Audit Trail**: Stores `elevation_factor_used` in database for tracking  

## Standard Elevation Factors

For reference, here are the research-validated conversion factors used throughout the system:

- **Running**: 750 feet = 1 mile equivalent
- **Cycling**: 1100 feet = 1 mile equivalent (less demanding due to gears and momentum)
- **Swimming**: No elevation component

## Testing Recommendations

1. Test manual elevation update on a **running** activity → Should use 750 ft/mile
2. Test manual elevation update on a **cycling** activity → Should use 1100 ft/mile
3. Verify `total_load_miles` matches between database and frontend display
4. Check that `elevation_factor_used` column is correctly populated
5. Verify consistency across Activities page, Dashboard charts, and Journal entries

## Files Modified

- `app/strava_app.py` - Lines 3598-3655
- `frontend/src/ActivitiesPage.tsx` - Lines 145-165

## Related Code

- `app/strava_training_load.py` - Contains main elevation factor logic
- `app/elevation_migration_module.py` - Migration from old 850 ft/mile standard

---

**Date**: October 13, 2025  
**Issue**: Inconsistent elevation factor calculations in manual updates  
**Resolution**: Sport-specific elevation factors now applied consistently


















