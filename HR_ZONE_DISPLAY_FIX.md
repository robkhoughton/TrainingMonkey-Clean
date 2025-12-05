# Heart Rate Zone Display Fix

## Problem Report
User 3 reported that after entering max HR and resting HR and selecting the Karvonen calculation method, the "Your Active Zones" column did not match the "Karvonen Method" column values.

## Root Causes Identified

### Bug 1: Method Name Mismatch in API
**Location:** `app/strava_app.py` line 6666

**Issue:** The API only included `hr_reserve` in the response when method was exactly `'reserve'`, but the HTML form uses `value="karvonen"`. This caused `hr_reserve` to be `None` when Karvonen was selected.

**Fix:** Changed condition from `method == 'reserve'` to `method in ['reserve', 'karvonen']`

### Bug 2: Frontend Recalculation Instead of Using API Data
**Location:** `app/templates/settings_hrzones.html` lines 288-294

**Issue:** The JavaScript was recalculating zone values using hardcoded formulas instead of using the pre-calculated values from the API. This led to:
1. Rounding differences between frontend and backend
2. Potential calculation inconsistencies
3. The comparison columns not matching the active zones

**Fix:** 
1. Backend now calculates BOTH percentage and Karvonen methods regardless of which one is selected
2. API response includes `percentage_zones` and `karvonen_zones` for comparison
3. Frontend uses these pre-calculated values instead of recalculating

## Changes Made

### Backend Changes (`app/strava_app.py`)

1. **Lines 6544-6643**: Refactored zone calculation logic
   - Always calculate both percentage and karvonen methods
   - Store them in separate variables: `percentage_zones` and `karvonen_zones`
   - Select the appropriate method as `calculated_zones` based on user preference

2. **Lines 6660-6670**: Updated API response
   - Added `percentage_zones` to response
   - Added `karvonen_zones` to response
   - Changed `hr_reserve` to always be included (not conditional)
   - Kept `calculated_zones` as the active method's zones

### Frontend Changes (`app/templates/settings_hrzones.html`)

**Lines 272-306**: Updated zone display logic
- Retrieve `percentage_zones` and `karvonen_zones` from API response
- Use pre-calculated values: `percentageZone.min/max` and `karvonenZone.min/max`
- Use pre-calculated formulas: `percentageZone.min_formula/max_formula` etc.
- Removed all frontend zone recalculation logic

## Benefits of This Fix

1. **Consistency**: All zone calculations now happen in one place (backend)
2. **Accuracy**: "Your Active Zones" will always exactly match the selected method's column
3. **Maintainability**: Any future changes to zone calculation logic only need to be made in one place
4. **Debugging**: Easier to troubleshoot because calculations are centralized

## Testing Instructions

1. Navigate to Settings > Heart Rate Zones
2. Enter Max HR (e.g., 185) and Resting HR (e.g., 65)
3. Select "Karvonen (Heart Rate Reserve)" method
4. Click "Calculate Zones"
5. Verify that:
   - The "Karvonen Method" column displays calculated zones
   - The "Your Active Zones" column exactly matches the "Karvonen Method" column
   - The "Percentage Method" column shows different values (as expected)
6. Switch to "Percentage of Max HR" method
7. Verify that:
   - The "Your Active Zones" column now matches the "Percentage Method" column
   - Both comparison columns still display correctly

## Example Zone Comparison

With Max HR = 185 and Resting HR = 65 (HR Reserve = 120):

| Zone | Percentage Method | Karvonen Method | Expected Active (Karvonen) |
|------|------------------|-----------------|----------------------------|
| Zone 1 | 93 - 111 | 125 - 137 | 125 - 137 ✓ |
| Zone 2 | 111 - 130 | 137 - 149 | 137 - 149 ✓ |
| Zone 3 | 130 - 148 | 149 - 161 | 149 - 161 ✓ |
| Zone 4 | 148 - 167 | 161 - 173 | 161 - 173 ✓ |
| Zone 5 | 167 - 185 | 173 - 185 | 173 - 185 ✓ |

The bug was that "Your Active Zones" was not matching "Karvonen Method" even when Karvonen was selected.

## Deployment Notes

These changes require a frontend rebuild and backend deployment:

1. **Frontend Rebuild**: The HTML template changes require copying to `app/build/`
2. **Backend Deployment**: The API changes require restarting the Flask application
3. **No Database Changes**: This fix is purely display logic, no schema changes needed
4. **No Data Migration**: Existing zone calculations remain unchanged

## Related Files

- `app/strava_app.py` - Backend API endpoint
- `app/templates/settings_hrzones.html` - Frontend display
- `app/settings_utils.py` - TRIMP calculation (unchanged, already handles both methods correctly)
- `app/Training_Metrics_Reference_Guide.md` - Documentation reference

## Future Considerations

- Consider consolidating method names: standardize on either "karvonen" or "reserve" throughout codebase
- Add automated tests for zone calculation logic
- Consider adding visual indicator when "Your Active Zones" has custom overrides


