# Deployment Checklist: Autopsy-Informed Workflow Fix

## Pre-Deployment (REQUIRED)

### ⚠️ CRITICAL: Run SQL Migration First
**MUST DO BEFORE DEPLOYING CODE**

```sql
-- Run this in your PostgreSQL SQL Editor
-- File: sql/add_autopsy_informed_tracking.sql
```

1. Connect to PostgreSQL cloud database:
   - Host: `35.223.144.85:5432`
   - Database: `train-d`
   - User: `appuser`

2. Load and execute: `sql/add_autopsy_informed_tracking.sql`

3. Verify output shows:
   ```
   SUCCESS: All autopsy tracking columns added to llm_recommendations
     - is_autopsy_informed: true
     - autopsy_count: true
     - avg_alignment_score: true
   ```

4. If migration fails, **DO NOT DEPLOY** - fix schema issues first

---

## Build & Deploy

### Step 1: Build Frontend
```bash
cd frontend
npm run build
```

**Expected**: Creates optimized production build in `frontend/build/`

### Step 2: Copy Frontend Build to Backend
```bash
# From project root
scripts\build_and_copy.bat
```

**Expected**: Copies `frontend/build/*` to `app/static/`

### Step 3: Deploy to Google Cloud
```bash
scripts\deploy_strava_simple.bat
```

**Expected**: 
- Uploads code to App Engine
- Installs Python dependencies
- Restarts application
- Returns deployment URL

---

## Post-Deployment Verification

### Test Sequence (15 minutes)

#### Test 1: Verify Schema Migration
```sql
-- Run in SQL Editor to verify columns exist
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'llm_recommendations'
AND column_name IN ('is_autopsy_informed', 'autopsy_count', 'avg_alignment_score')
ORDER BY column_name;
```

**Expected**: 3 rows returned showing the new columns

#### Test 2: Complete Workflow Test
1. Log into production site: `https://yourtrainingmonkey.com`
2. Navigate to **Journal** page
3. Find today's entry (should have activity from Strava)
4. Enter observations:
   - Energy: 3
   - RPE: 4
   - Pain: 0%
   - Notes: "Test autopsy workflow"
5. Click **💾 Save**
6. **Verify**: Success message mentions "autopsy generated and tomorrow's recommendation updated"
7. **Verify**: Tomorrow's row appears with recommendation
8. **Verify**: "🧠 Autopsy-Informed" badge shows (if you have prior autopsies)

#### Test 3: Dashboard Badge Check
1. Navigate to **Dashboard** page
2. Scroll to "Training Recommendations & Analysis" section
3. **Verify**: "🤖 AI Analysis" heading shows recommendation
4. **Verify**: If autopsy-informed, green badge appears: "🧠 Autopsy-Informed"
5. Hover over badge
6. **Verify**: Tooltip shows autopsy count and average alignment

#### Test 4: Autopsy Analysis Check
1. Return to **Journal** page
2. Find yesterday's entry (with completed workout)
3. Click **🔍 Analysis** button
4. **Verify**: Autopsy analysis expands
5. **Verify**: Alignment score shown (e.g., "8/10")
6. **Verify**: Analysis includes sections:
   - ALIGNMENT ASSESSMENT
   - PHYSIOLOGICAL RESPONSE ANALYSIS
   - LEARNING INSIGHTS & TOMORROW'S IMPLICATIONS

#### Test 5: Multi-Day Learning Cycle
1. Complete another workout tomorrow
2. Repeat Test 2 workflow
3. **Verify**: Recommendation badge shows updated autopsy count
4. **Verify**: Recommendation text shows learning from patterns
5. Compare Friday → Saturday → Sunday recommendations
6. **Verify**: Recommendations evolve based on your adherence/response

---

## Rollback Plan (If Issues Occur)

### Option 1: Revert Code Only (Keep Schema)
```bash
git log --oneline -5  # Find previous commit
git checkout <previous-commit-hash>
gcloud app deploy
```

**When to use**: Application errors but database is fine

### Option 2: Revert Schema (Remove Columns)
```sql
-- ONLY if absolutely necessary
BEGIN;
ALTER TABLE llm_recommendations 
DROP COLUMN IF EXISTS is_autopsy_informed,
DROP COLUMN IF EXISTS autopsy_count,
DROP COLUMN IF EXISTS avg_alignment_score;
COMMIT;
```

**When to use**: Schema migration causes database issues

**⚠️ Warning**: This loses autopsy tracking data

---

## Monitoring After Deployment

### Check Application Logs
```bash
gcloud app logs tail -s default
```

**Look for**:
- ✅ `Auto-generating autopsy-informed recommendation after journal save`
- ✅ `Recommendation is autopsy-informed with X recent autopsies`
- ✅ `Saved enhanced autopsy for YYYY-MM-DD, alignment: X/10`
- ❌ Any errors mentioning `autopsy` or `recommendation`

### Check User Experience
Monitor for 48 hours:
- Users successfully saving journal entries?
- Autopsy generation happening automatically?
- Recommendations showing badges?
- Any 500 errors on `/api/journal` POST?

### Database Checks
After 24 hours, verify data:
```sql
-- Check autopsy-informed recommendations
SELECT 
    target_date,
    is_autopsy_informed,
    autopsy_count,
    avg_alignment_score,
    generated_at
FROM llm_recommendations
WHERE user_id = <your-user-id>
ORDER BY generated_at DESC
LIMIT 10;
```

**Expected**: Recent recommendations show `is_autopsy_informed = true`

---

## Known Issues & Solutions

### Issue 1: "Column does not exist" error
**Symptom**: 500 error when saving journal entry  
**Cause**: SQL migration not run  
**Solution**: Run `sql/add_autopsy_informed_tracking.sql` immediately

### Issue 2: Badge not showing on Dashboard
**Symptom**: No green badge even with autopsies  
**Cause**: Old recommendation in cache (generated before deployment)  
**Solution**: Complete new journal entry to trigger fresh generation

### Issue 3: Tomorrow's row not appearing
**Symptom**: Journal only shows 7 days, no tomorrow  
**Cause**: Frontend build not copied to backend  
**Solution**: Re-run `scripts\build_and_copy.bat` and redeploy

### Issue 4: Slow journal save (>5 seconds)
**Symptom**: Save button stays "Saving..." for long time  
**Cause**: LLM API call in save flow (expected)  
**Solution**: This is normal! Auto-generation takes 2-4 seconds.  
If >10 seconds, check LLM API status.

---

## Success Metrics

After 1 week, check:
- ✅ 100% of journal saves trigger autopsy (if conditions met)
- ✅ 90%+ of recommendations show autopsy-informed badge
- ✅ Average alignment scores trending upward (users following recommendations better)
- ✅ No increase in 500 errors
- ✅ Journal save time <5 seconds p95

---

## Support

If issues arise:
1. Check application logs first
2. Verify SQL migration ran successfully
3. Test with your own account before investigating user reports
4. Roll back if critical functionality broken

**Remember**: Schema changes can't be easily undone once users start generating new recommendations. Test thoroughly!









