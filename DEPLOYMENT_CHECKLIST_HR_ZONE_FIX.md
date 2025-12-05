# Deployment Checklist: Heart Rate Zone Display Fix

## Issue
User 3 reported that "Your Active Zones" column didn't match "Karvonen Method" values when Karvonen method was selected.

## Files Modified
- ✅ `app/strava_app.py` (Backend API - 2 changes)
- ✅ `app/templates/settings_hrzones.html` (Frontend display - 1 change)
- ✅ `HR_ZONE_DISPLAY_FIX.md` (Documentation)

## Pre-Deployment Steps

### 1. Code Review
- [x] Backend changes reviewed
- [x] Frontend changes reviewed
- [x] No linter errors

### 2. Testing (Before Deployment)
Not applicable - changes are to production cloud database only. Testing will occur post-deployment.

## Deployment Steps

### Step 1: Prepare Frontend Build
```cmd
cd frontend
npm run build
cd ..
```

### Step 2: Clean Old Build Files
```cmd
del /Q app\static\js\main.*.js
del /Q app\static\js\main.*.LICENSE.txt
del /Q app\static\css\main.*.css
del /Q app\build\static\js\main.*.js
del /Q app\build\static\js\main.*.LICENSE.txt
del /Q app\build\static\css\main.*.css
```

### Step 3: Copy New Build Files
```cmd
xcopy frontend\build\* app\build\ /E /Y
xcopy frontend\build\static\* app\static\ /E /Y
copy frontend\build\training-monkey-runner.webp app\static\training-monkey-runner.webp
```

### Step 4: Deploy to Google Cloud Run
```cmd
cd app
deploy_strava_simple.bat
```

## Post-Deployment Testing

### Test Case 1: Karvonen Method
1. Log in as any user (or create test account)
2. Navigate to Settings > Heart Rate Zones
3. Enter:
   - Max HR: 185
   - Resting HR: 65
   - Method: "Karvonen (Heart Rate Reserve)"
4. Click "Calculate Zones"
5. **Expected Result:**
   - "Karvonen Method" column shows: 125-137, 137-149, 149-161, 161-173, 173-185
   - "Your Active Zones" column shows: 125-137, 137-149, 149-161, 161-173, 173-185 (EXACT MATCH)
   - "Percentage Method" column shows: 93-111, 111-130, 130-148, 148-167, 167-185 (different values)

### Test Case 2: Percentage Method
1. Same settings, but select "Percentage of Max HR"
2. Click "Calculate Zones"
3. **Expected Result:**
   - "Percentage Method" column shows: 93-111, 111-130, 130-148, 148-167, 167-185
   - "Your Active Zones" column shows: 93-111, 111-130, 130-148, 148-167, 167-185 (EXACT MATCH)
   - "Karvonen Method" column shows: 125-137, 137-149, 149-161, 161-173, 173-185 (different values)

### Test Case 3: Show Formulas Button
1. Click "Show Formulas" button
2. **Expected Result:**
   - Formulas appear under each zone value
   - Karvonen formulas show: "65 + (50% × 120) = 125" format
   - Percentage formulas show: "50% × 185 = 93" format
   - All formulas match the displayed values

### Test Case 4: Custom Zone Override
1. With Karvonen method selected
2. Enter custom values in "Custom Override" column for Zone 1:
   - Min: 120
   - Max: 135
3. Click "Save Zone Changes"
4. **Expected Result:**
   - "Your Active Zones" column shows custom values: 120-135 for Zone 1
   - Other zones remain at calculated Karvonen values
   - "Karvonen Method" column still shows original calculated value: 125-137

## Rollback Plan

If issues are detected:

1. **Revert Backend Changes:**
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **Redeploy Previous Version:**
   ```cmd
   cd app
   deploy_strava_simple.bat
   ```

3. **Alternative:** Hotfix by reverting just the problematic changes:
   - Lines 6544-6670 in `app/strava_app.py`
   - Lines 272-306 in `app/templates/settings_hrzones.html`

## Success Criteria

- ✅ "Your Active Zones" matches selected method column exactly
- ✅ Both comparison columns display correctly regardless of selected method
- ✅ Formulas match displayed values
- ✅ Custom zone overrides still work
- ✅ No console errors in browser
- ✅ No server errors in logs

## Communication

### To User 3
"The heart rate zone display issue has been fixed. When you select Karvonen method, your Active Zones will now correctly match the Karvonen Method column. Please test and let us know if you see any issues."

### To All Users (if needed)
"Fixed: Heart rate zone calculations now display correctly in Settings. The comparison table will now show accurate values for both Percentage and Karvonen methods."

## Notes

- No database schema changes required
- No data migration needed
- Existing user zone configurations remain unchanged
- This fix only affects the display logic, not the underlying TRIMP calculations
- All TRIMP calculations already used the correct method (verified in `settings_utils.py`)

## Completed
- [ ] Frontend built
- [ ] Build files copied
- [ ] Deployed to Cloud Run
- [ ] Test Case 1 passed
- [ ] Test Case 2 passed
- [ ] Test Case 3 passed
- [ ] Test Case 4 passed
- [ ] User 3 notified
- [ ] Issue closed


