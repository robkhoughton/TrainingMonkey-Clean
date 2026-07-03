# Swimming Support - Testing Checklist

## Pre-Deployment Verification

### ✅ Database
- [x] `swimming_equivalent_miles` column exists in `activities` table
- [x] Column is REAL type, nullable
- [x] All existing activities have `sport_type` populated
- [x] No NULL sport_types found (0 activities need backfill)

### ✅ Code Quality
- [x] No linter errors in Python files
- [x] No linter errors in TypeScript files
- [x] All functions follow existing patterns
- [x] Defensive defaults in place

---

## Post-Deployment Testing

### Test 1: User Without Swimming (Regression Test)
**Purpose:** Ensure existing users are unaffected

**Steps:**
1. Login as user 1 (robheller@gmail.com)
2. Navigate to Training Load Dashboard
3. Observe dashboard

**Expected Results:**
- [ ] Dashboard loads normally (no errors)
- [ ] Only "Running" and "Cycling" toggles appear (no Swimming)
- [ ] Charts display correctly
- [ ] No performance degradation
- [ ] Console has no errors

**Status:** ___________

---

### Test 2: First Swimming Activity Sync
**Purpose:** Test swimming detection and conversion

**Steps:**
1. Login as user 2 (tballaine@gmail.com) who has swimming activities on Strava
2. Navigate to Settings → Sync from Strava
3. Trigger a sync (last 7 days)
4. Check logs for swimming activity processing
5. Return to dashboard

**Expected Results:**
- [ ] Sync completes successfully
- [ ] Logs show: "Using swimming-specific external load calculation"
- [ ] Logs show conversion: "Swimming conversion results: running_equiv=X.XX"
- [ ] Dashboard automatically shows Swimming toggle (orange)
- [ ] Swimming checkbox is checked by default
- [ ] Orange bars appear in Training Load chart

**SQL Verification:**
```sql
-- Check swimming activity was synced
SELECT 
    activity_id, 
    date, 
    name, 
    type, 
    sport_type,
    distance_miles,
    swimming_equivalent_miles,
    total_load_miles
FROM activities 
WHERE user_id = 2 
AND sport_type = 'swimming'
ORDER BY date DESC 
LIMIT 5;

-- Expected: swimming_equivalent_miles = distance_miles * 4.0 (or 4.2 for open water)
-- Expected: total_load_miles = swimming_equivalent_miles
```

**Status:** ___________

---

### Test 3: Swimming Conversion Accuracy
**Purpose:** Verify 4:1 and 4.2:1 conversion ratios

**Test Case A: Pool Swim**
- Swimming Distance: 1.0 mile
- Expected Equivalent: 4.0 miles
- Expected Calculation: `1.0 * 4.0 = 4.0`

**Test Case B: Open Water Swim**
- Swimming Distance: 1.0 mile
- Activity Type contains "open water" or "openwater"
- Expected Equivalent: 4.2 miles
- Expected Calculation: `1.0 * 4.2 = 4.2`

**SQL Check:**
```sql
SELECT 
    name,
    type,
    distance_miles,
    swimming_equivalent_miles,
    ROUND(swimming_equivalent_miles / distance_miles, 2) as conversion_ratio
FROM activities 
WHERE sport_type = 'swimming'
AND user_id = 2;

-- Expected: conversion_ratio = 4.00 for pool, 4.20 for open water
```

**Status:** ___________

---

### Test 4: Multi-Sport Day (Triathlon)
**Purpose:** Test aggregation with all three sports

**Create Test Scenario:**
If user has a day with:
- 1 Run: 3.0 miles → 3.0 miles load
- 1 Bike: 20.0 miles → 6.5 miles load (approx, depends on speed)
- 1 Swim: 1.0 mile → 4.0 miles load

**Expected Results:**
- [ ] All three activities show in tooltip
- [ ] Stacked bars show all three colors (green + blue + orange)
- [ ] Total load = sum of all three running equivalents
- [ ] Day type = 'mixed'
- [ ] Each sport load tracks separately
- [ ] Tooltip shows breakdown for each activity

**Visual Check:**
```
Tooltip should show:
┌─────────────────────────────┐
│ Oct X, 2024 - Mixed Sports  │
├─────────────────────────────┤
│ 🏃 Morning Run - 3.0 mi     │
│ 🚴 Bike Ride - 20.0 mi      │
│    (6.5 mi equiv)           │
│ 🏊 Pool Swim - 1.0 mi       │
│    (4.0 mi equiv)           │
├─────────────────────────────┤
│ Total Load: 13.5 mi         │
│ TRIMP: XXX                  │
└─────────────────────────────┘
```

**Status:** ___________

---

### Test 5: Swimming Toggle Functionality
**Purpose:** Test show/hide swimming data

**Steps:**
1. Navigate to dashboard with swimming data visible
2. Observe swimming bars (orange) at 70% opacity
3. Uncheck Swimming toggle
4. Observe swimming bars at 30% opacity (faded)
5. Re-check Swimming toggle
6. Observe swimming bars return to 70% opacity

**Expected Results:**
- [ ] Toggle responds immediately (no lag)
- [ ] Bars fade smoothly
- [ ] Running and Cycling toggles still work independently
- [ ] Chart doesn't shift or resize
- [ ] Total load line remains accurate regardless of toggle state

**Status:** ___________

---

### Test 6: Swimming with No Heart Rate
**Purpose:** Test TRIMP calculation with missing HR data

**Scenario:** Swimming activity with no heart rate monitor

**Expected Results:**
- [ ] Activity syncs successfully
- [ ] Distance and equivalent calculated correctly
- [ ] TRIMP = 0 (no heart rate data)
- [ ] Activity still appears in dashboard
- [ ] No errors or crashes
- [ ] Chart displays correctly

**SQL Check:**
```sql
SELECT 
    date, name, distance_miles, swimming_equivalent_miles,
    avg_heart_rate, trimp
FROM activities 
WHERE sport_type = 'swimming' 
AND avg_heart_rate = 0;

-- Expected: trimp = 0, but swimming_equivalent_miles still calculated
```

**Status:** ___________

---

### Test 7: ACWR Calculation with Swimming
**Purpose:** Verify swimming load is included in ACWR

**Steps:**
1. Check user's External ACWR (Acute/Chronic Workload Ratio)
2. Verify swimming load contributes to 7-day and 28-day averages
3. Verify Internal ACWR (TRIMP-based) works with swimming

**Expected Results:**
- [ ] Swimming load (running equivalent) adds to daily total_load_miles
- [ ] 7-day average includes swimming days
- [ ] 28-day average includes swimming days
- [ ] External ACWR reflects swimming load
- [ ] Internal ACWR works (uses TRIMP, which may be 0 for swimming)
- [ ] Normalized Divergence calculates correctly

**SQL Verification:**
```sql
-- Check a day with swimming has correct totals
SELECT 
    date,
    distance_miles,
    swimming_equivalent_miles,
    total_load_miles,
    seven_day_avg_load,
    acute_chronic_ratio
FROM activities 
WHERE sport_type = 'swimming'
AND user_id = 2
ORDER BY date DESC LIMIT 1;

-- Expected: total_load_miles = swimming_equivalent_miles (for swim-only days)
```

**Status:** ___________

---

### Test 8: Sport Summary API
**Purpose:** Verify backend returns swimming data flag

**Test API Response:**
```bash
curl -X GET "http://localhost:5000/api/training-data?include_sport_breakdown=true" \
  -H "Cookie: session=YOUR_SESSION_COOKIE"
```

**Expected JSON Response:**
```json
{
  "success": true,
  "data": [...],
  "has_cycling_data": true,
  "has_swimming_data": true,  // <-- NEW
  "sport_summary": [
    {
      "sport_type": "running",
      "activity_count": 627,
      "total_load": XXX
    },
    {
      "sport_type": "cycling",
      "activity_count": 187,
      "total_load": XXX
    },
    {
      "sport_type": "swimming",  // <-- NEW
      "activity_count": X,
      "total_load": XXX
    }
  ]
}
```

**Status:** ___________

---

### Test 9: Performance & Load Time
**Purpose:** Ensure no performance degradation

**Metrics to Check:**
- [ ] Dashboard load time: < 2 seconds (baseline)
- [ ] Chart render time: < 500ms (baseline)
- [ ] API response time: < 1 second (baseline)
- [ ] No memory leaks (check DevTools)
- [ ] Smooth scrolling and interactions

**Browser Console Check:**
```javascript
// Check for errors
console.error.length === 0

// Check for warnings about performance
// Should see no warnings about slow renders
```

**Status:** ___________

---

### Test 10: Edge Cases

#### A. Swimming activity with unusual type name
- Test if Strava sends "SwimRun" or other variants
- Expected: Classified correctly or defaults to 'running'

#### B. Very long swimming distance
- Test: 5+ mile open water swim
- Expected: Converts correctly (5 * 4.2 = 21 miles equiv)
- Expected: Chart displays without overflow

#### C. Multiple swims same day
- Test: Morning swim + Evening swim
- Expected: Aggregates correctly
- Expected: Shows total swimming load for the day

#### D. Swimming distance = 0
- Test: Activity with 0 distance
- Expected: 0 equivalent miles
- Expected: No division by zero errors

**Status:** ___________

---

## Rollback Criteria

**Trigger rollback if:**
- [ ] Dashboard crashes for any user
- [ ] Data loss or corruption detected
- [ ] Performance degrades by >50%
- [ ] Critical calculation errors in ACWR
- [ ] Swimming conversions are wildly incorrect (>20% off)

**Rollback Steps:**
```bash
# 1. Revert backend
git revert <commit-hash>
cd app && deploy_strava_simple.bat

# 2. Revert frontend
cd frontend
git revert <commit-hash>
npm run build
# Copy to app/static

# 3. Optional: Remove database column (safe to leave)
# ALTER TABLE activities DROP COLUMN IF EXISTS swimming_equivalent_miles;
```

---

## Success Criteria

**Deployment is successful when:**
- [x] Database column added
- [ ] Backend deploys without errors
- [ ] Frontend builds and deploys
- [ ] Test 1-3 pass (core functionality)
- [ ] Test 4-7 pass (advanced features)
- [ ] No critical bugs reported
- [ ] Performance remains acceptable
- [ ] Users with swimming see their data correctly
- [ ] Users without swimming see no changes

---

## Monitoring (First 24-48 Hours)

**Check Logs For:**
- [ ] "Using swimming-specific external load calculation" (confirms swimming detected)
- [ ] "Swimming conversion results: running_equiv=X.XX" (confirms calculation)
- [ ] No errors containing "swimming"
- [ ] No "Unknown activity type" for swimming activities
- [ ] API response times remain normal

**User Feedback:**
- [ ] Any reports of dashboard issues?
- [ ] Any confusion about swimming conversion ratio?
- [ ] Any requests for ratio adjustment?

---

## Post-Deployment Actions

- [ ] Update user documentation with swimming support announcement
- [ ] Add swimming to "Supported Activities" list
- [ ] Monitor for swimming activities in production
- [ ] Collect feedback on 4:1 conversion ratio
- [ ] Consider adding conversion ratio to UI (e.g., in tooltip)

---

## Notes

- Swimming has NO elevation component (always 0)
- Pool vs Open Water: 5% difference in conversion
- TRIMP may be 0 if no heart rate monitor used (this is expected)
- Swimming equivalent is ALWAYS calculated from distance * ratio
- Total load for swim-only days = swimming equivalent miles

---

**Tester Name:** _______________  
**Test Date:** _______________  
**Environment:** Production / Staging  
**Overall Status:** Pass / Fail / Partial  
























