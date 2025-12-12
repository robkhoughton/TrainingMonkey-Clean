# Swimming Support - Risk Assessment

## Risk Analysis: Adding Swimming to TrainingMonkey

### 🟢 LOW RISK Areas (Safe)

#### 1. **Backend Default Handling - SAFE**
```python
# Line 86 in unified_metrics_service.py
sport_type = activity['sport_type'] or 'running'  # DEFAULT TO RUNNING

# Lines 520-528 in strava_training_load.py  
else:
    # Default to 'running' for safety with existing data
    logger.info(f"Activity type '{activity_type}' not recognized, defaulting to 'running'")
    return 'running'
```

**Why Safe:**
- Code already has defensive defaults
- Unknown/missing sport_type defaults to 'running'
- Existing activities without sport_type won't break
- Walking/Hiking activities already treated as 'running' (no impact)

#### 2. **Database Schema Addition - SAFE**
```sql
ALTER TABLE activities ADD COLUMN IF NOT EXISTS swimming_equivalent_miles REAL;
```

**Why Safe:**
- `IF NOT EXISTS` prevents errors on re-run
- REAL type is nullable (NULL is fine for non-swim activities)
- No foreign key constraints
- Doesn't affect existing queries (column will be NULL for old data)
- PostgreSQL handles this gracefully

#### 3. **Frontend Sport Toggle - SAFE**
```typescript
const [selectedSports, setSelectedSports] = useState(['running', 'cycling', 'swimming']);
const [hasSwimmingData, setHasSwimmingData] = useState(false);
```

**Why Safe:**
- Swimming toggle only shows if `hasSwimmingData === true`
- Backward compatible - if no swimming, behaves exactly as before
- Independent state - doesn't affect running/cycling toggles
- User preference (can turn off if they don't want to see it)

---

### 🟡 MEDIUM RISK Areas (Manageable)

#### 1. **Swimming Activity Type Detection - MEDIUM**
```python
# If Strava sends unexpected swimming type names
swimming_keywords = [
    'swim', 'swimming', 'pool', 'open water', 'openwater'
]
```

**Risk:** Strava might use swimming type names we haven't seen
- "SwimRun" events (combination sport)
- "Kayaking" might contain "swim" in name
- Foreign language activity names

**Mitigation:**
✅ Use lowercase `.lower()` comparison (case-insensitive)  
✅ Check specific keywords first, then fallback to 'running' default  
✅ Log all unrecognized types for monitoring  
⚠️ Consider: Add "aqua", "water" to keywords for broader coverage

**Impact if fails:** Activity gets classified as 'running' (safe default)

#### 2. **Swimming Conversion Factor Accuracy - MEDIUM**
```python
# 1 mile swim = 4 miles running equivalent
conversion_factor = 4.0
```

**Risk:** Users might disagree with conversion ratio
- Some research suggests 3:1, others 5:1
- Depends on swimmer efficiency and intensity
- Pool vs open water differences

**Mitigation:**
✅ Based on peer-reviewed sports science (MET comparisons)  
✅ Conservative 4:1 ratio is middle-ground  
✅ Document in user guide  
✅ Clearly label as "Running Equivalent" in UI  
⚠️ Future: Make configurable per user?

**Impact if wrong:** User sees inflated/deflated training load, but doesn't break functionality

#### 3. **Data Aggregation with Three Sports - MEDIUM**
```python
# Must handle running + cycling + swimming on same day
if sport_type == 'swimming':
    existing['swimming_load'] = existing.get('swimming_load', 0) + load
```

**Risk:** Edge cases with multi-sport days
- What if all three sports on same day? (Triathlon!)
- What if sport_type is missing/NULL in aggregation?
- Day_type classification with 3+ sports

**Mitigation:**
✅ Use `.get('swimming_load', 0)` for safe defaults  
✅ Existing code already handles running+cycling mixed days  
✅ Test with simulated triathlon day (all three sports)  
⚠️ Need to test: What happens if sport_type is missing in aggregate_daily_activities_with_rest?

**Impact if fails:** Chart might show incorrect sport breakdown for that day

---

### 🔴 HIGH RISK Areas (Requires Caution)

#### 1. **Database Migration Timing - HIGH**
```sql
ALTER TABLE activities ADD COLUMN swimming_equivalent_miles REAL;
```

**Risk:** Schema change on live production database
- Must be done BEFORE deploying code that uses it
- If code deploys first, INSERT statements will fail
- If column doesn't exist, queries referencing it will error

**CRITICAL MITIGATION STEPS:**
1. ✅ Run SQL in editor FIRST (before code deploy)
2. ✅ Verify column exists: `\d activities` in psql
3. ✅ Test INSERT with NULL: `INSERT INTO activities (..., swimming_equivalent_miles) VALUES (..., NULL)`
4. ✅ Then deploy code changes
5. ✅ **DEPLOYMENT ORDER MATTERS!**

**Deployment Checklist:**
```
[ ] 1. Run SQL Editor: ADD COLUMN swimming_equivalent_miles
[ ] 2. Verify column exists in database
[ ] 3. Deploy backend code (strava_training_load.py changes)
[ ] 4. Test sync with a swim activity
[ ] 5. Deploy frontend code (dashboard changes)
[ ] 6. Verify swimming toggle appears for users with swims
```

#### 2. **Existing Activities Without sport_type - HIGH**
```python
# What happens to old activities in database?
sport_type = activity.get('sport_type', 'running')  # Line 59 in data_aggregation.py
```

**Risk:** Existing database records might not have sport_type populated
- Activities synced before multi-sport support added
- Missing sport_type → defaults to 'running'
- Walking/Hiking will be classified as 'running'

**Investigation Needed:**
```sql
-- Check for NULL sport_type in database
SELECT COUNT(*) FROM activities WHERE sport_type IS NULL;
SELECT COUNT(*) FROM activities WHERE sport_type IS NOT NULL;

-- Check what sport_types exist
SELECT DISTINCT sport_type, COUNT(*) FROM activities GROUP BY sport_type;
```

**Mitigation:**
✅ Code already has `.get('sport_type', 'running')` defaults  
✅ NULL sport_type won't crash, just defaults to running  
⚠️ **RECOMMENDED:** Backfill sport_type for existing activities:

```python
# Backfill script (run once after deployment)
def backfill_sport_types():
    activities = execute_query("SELECT activity_id, type FROM activities WHERE sport_type IS NULL", fetch=True)
    for activity in activities:
        activity_type = activity['type'].lower()
        if 'bike' in activity_type or 'ride' in activity_type or 'cycling' in activity_type:
            sport = 'cycling'
        elif 'swim' in activity_type:
            sport = 'swimming'
        else:
            sport = 'running'
        
        execute_query("UPDATE activities SET sport_type = %s WHERE activity_id = %s", (sport, activity['activity_id']))
```

**Impact if not addressed:** All old activities show as 'running' in sport breakdown

#### 3. **Chart Performance with Three Sport Series - MEDIUM-HIGH**
```typescript
// Three overlapping bar series in charts
<Bar dataKey="running_load" ... />
<Bar dataKey="cycling_load" ... />
<Bar dataKey="swimming_load" ... />  // NEW - adds rendering complexity
```

**Risk:** Performance degradation with additional chart series
- Three stacked bars per day vs two
- More data points to render
- Longer tooltip content
- Chart re-render on toggle

**Mitigation:**
✅ Chart library (Recharts) already handles stacked bars efficiently  
✅ 90 days × 3 sports = ~270 bars (manageable)  
✅ Toggling sports hides bars (reduces render load)  
⚠️ Test on slower devices/browsers

**Impact if slow:** Slightly longer chart render time (~100-200ms)

---

### 🔴 CRITICAL - Must Test Before Production

#### Test Scenarios:
1. **User with no swimming**
   - ✅ Swimming toggle should NOT appear
   - ✅ Charts should look identical to current

2. **User's first swim activity**
   - ✅ Sync detects swimming activity
   - ✅ Calculates 4:1 running equivalent correctly
   - ✅ Stores swimming_equivalent_miles in database
   - ✅ Swimming toggle appears on next dashboard load
   - ✅ Orange bar appears in charts

3. **Multi-sport day (Triathlon)**
   - ✅ Run 3 mi + Bike 20 mi + Swim 1 mi on same day
   - ✅ Aggregation sums all three sports correctly
   - ✅ Stacked bar shows all three colors
   - ✅ Tooltip lists all three activities
   - ✅ Total load = 3 + 6.5 + 4 = 13.5 mi

4. **Old activities without sport_type**
   - ✅ Default to 'running' classification
   - ✅ Charts still display correctly
   - ✅ No crashes or errors

5. **Edge case: Swimming with no heart rate**
   - ✅ TRIMP = 0 (correct behavior)
   - ✅ Still shows distance and running equivalent
   - ✅ Chart displays correctly

6. **Database NULL handling**
   - ✅ swimming_equivalent_miles = NULL for non-swim activities
   - ✅ Frontend treats NULL as 0
   - ✅ No NaN or undefined errors

---

## Risk Summary Matrix

| Component | Risk Level | Impact if Fails | Likelihood | Mitigation Status |
|-----------|-----------|-----------------|------------|-------------------|
| Backend defaults | 🟢 Low | Minor display issue | Very Low | ✅ Already built-in |
| Database schema | 🔴 High | App crash | Low | ⚠️ Requires careful deployment order |
| Sport classification | 🟡 Medium | Wrong sport label | Low | ✅ Defaults to 'running' |
| Conversion factor | 🟡 Medium | User confusion | Medium | ✅ Document + label clearly |
| Frontend toggle | 🟢 Low | Extra checkbox | Very Low | ✅ Conditional rendering |
| Chart performance | 🟡 Medium | Slight slowdown | Low | ✅ Chart library optimized |
| Multi-sport aggregation | 🟡 Medium | Wrong totals | Medium | ⚠️ Needs testing |
| Old data compatibility | 🔴 High | Missing sport data | High | ⚠️ Consider backfill script |

---

## Recommended Deployment Strategy

### Phase 1: Pre-Deployment (Low Risk)
1. ✅ Add database column (SQL Editor)
2. ✅ Verify column exists
3. ✅ Test backfill script on sample data
4. ✅ Run backfill for existing activities (optional but recommended)

### Phase 2: Backend Deploy (Medium Risk)
1. ✅ Deploy backend code (calculate_swimming_external_load, sport classification)
2. ✅ Test sync with ONE test swim activity
3. ✅ Verify swimming_equivalent_miles is populated
4. ✅ Check logs for errors
5. ⚠️ **ROLLBACK PLAN:** Revert code if sync fails

### Phase 3: Frontend Deploy (Low Risk)
1. ✅ Deploy frontend (swimming toggle, orange bars)
2. ✅ Verify swimming toggle only shows for users with swim data
3. ✅ Test chart rendering
4. ✅ Test tooltip display

### Phase 4: Monitor (Ongoing)
1. ✅ Check logs for "Unknown" activity types
2. ✅ Monitor for swimming activities being misclassified
3. ✅ Watch for performance issues
4. ✅ Collect user feedback on 4:1 conversion ratio

---

## Rollback Plan

If something breaks:

### Backend Rollback:
```bash
# Revert to previous version
git revert <commit-hash>
git push origin master

# Redeploy
cd app && deploy_strava_simple.bat
```

### Database Rollback:
```sql
-- If needed, remove column (won't affect existing data)
ALTER TABLE activities DROP COLUMN IF EXISTS swimming_equivalent_miles;
```

### Frontend Rollback:
```bash
# Revert frontend changes
cd frontend
git revert <commit-hash>
npm run build
# Copy to app/static
```

---

## Overall Risk Assessment

**Overall Risk Level: 🟡 MEDIUM (Manageable)**

### What Makes It Safe:
✅ Defensive coding with defaults throughout  
✅ Backend already supports multi-sport (cycling proves architecture)  
✅ Database change is additive (doesn't modify existing data)  
✅ Frontend changes are conditional (only shows if data exists)  
✅ Rollback plan is straightforward  

### What Requires Care:
⚠️ **Deployment order** (database → backend → frontend)  
⚠️ **Testing multi-sport days** (all three sports)  
⚠️ **Monitoring for edge cases** (unusual swim types)  
⚠️ **Consider backfilling** existing activities  

### Recommended Approach:
1. **Deploy to staging/test environment first**
2. **Test with real swimming data from Strava**
3. **Monitor for 24-48 hours**
4. **Then deploy to production with careful sequencing**

**Confidence Level: HIGH** - Architecture is already multi-sport ready, we're just adding a third sport using the exact same pattern as cycling.
























