# Journal Date Fix - 14-Day Recommendation Retention

**⚠️ UPDATE (October 17, 2025):** This fix was incomplete. A timezone-based date attribution bug was discovered and fixed separately. See `TIMEZONE_DATE_ATTRIBUTION_FIX.md` for the complete solution.

## Problem Identified
Training recommendations were being overwritten when new activities were logged, causing the Journal page to show incorrect recommendations for historical dates. For example, Friday's recommendation would show Saturday's workout because after logging Friday's activity, the system generated a new recommendation for Saturday that replaced or obscured Friday's original recommendation.

## Root Cause
The `generate_recommendations()` function would create new recommendations with a `target_date` based on current activity status:
- If user completed today's workout → generate recommendation FOR tomorrow
- If user hasn't worked out today → generate recommendation FOR today

However, there was no check to prevent overwriting existing `target_date` records, so historical recommendations were lost.

## Solution Implemented
**3 key changes** to preserve historical recommendations with 14-day retention:

### 1. Added Cleanup Function (`app/db_utils.py` lines 468-497)
```python
def cleanup_old_recommendations(user_id, keep_days=14):
    """
    Remove old recommendations, keeping only those from the last N days.
    Prevents database bloat while maintaining Journal page history.
    """
```

**Purpose**: Automatically delete recommendations older than 14 days to prevent database bloat while maintaining sufficient history for the Journal page's weekly view.

### 2. Added Duplicate Prevention (`app/llm_recommendations_module.py` lines 705-718)
```python
# Check if recommendation already exists for this target_date
existing_recommendation = db_utils.execute_query(
    """
    SELECT id FROM llm_recommendations 
    WHERE user_id = %s AND target_date = %s
    """,
    (user_id, target_date),
    fetch=True
)

if existing_recommendation:
    logger.info(f"Recommendation already exists for target_date {target_date}, skipping generation")
    return get_latest_recommendation(user_id)
```

**Purpose**: Before generating a new recommendation, check if one already exists for the `target_date`. If it does, return the existing recommendation instead of overwriting it.

### 3. Added Cleanup Call (`app/llm_recommendations_module.py` lines 785-787)
```python
# Clean up old recommendations (keep last 14 days)
from db_utils import cleanup_old_recommendations
cleanup_old_recommendations(user_id, keep_days=14)
```

**Purpose**: After successfully saving a new recommendation, automatically clean up old ones to maintain 14 days of history.

## How It Works Now

### Scenario 1: First Recommendation of the Day
1. User opens Dashboard Monday morning (no activity logged yet)
2. System checks: does recommendation exist for `target_date = Monday`? **No**
3. System generates recommendation FOR Monday (`target_date = '2025-10-13'`)
4. After saving, cleanup runs (keeps last 14 days)

### Scenario 2: After Logging Activity
1. User completes Monday's workout
2. User refreshes Dashboard
3. System checks: does recommendation exist for `target_date = Tuesday`? **No**
4. System generates recommendation FOR Tuesday (`target_date = '2025-10-14'`)
5. Monday's recommendation is **preserved** (not overwritten)
6. After saving, cleanup runs

### Scenario 3: Multiple Refreshes
1. User refreshes Dashboard multiple times on Monday (after workout)
2. Each time, system checks: does recommendation exist for `target_date = Tuesday`? **Yes**
3. System returns existing Tuesday recommendation (no new generation)
4. Historical records remain intact

### Scenario 4: Cleanup (Day 15)
1. User logs an activity on Day 15
2. New recommendation generated for Day 16
3. Cleanup runs: deletes recommendations with `target_date < (today - 14 days)`
4. Recommendations for Days 1-14 are kept, Day 0 and earlier are deleted

## Journal Page Behavior

### For Dates Within Last 14 Days
- Shows the **original prescriptive recommendation** that was generated FOR that date
- AI Autopsy correctly compares "what was recommended" vs "what you actually did"
- Alignment scores are meaningful

### For Dates Older Than 14 Days
- Shows: "No recommendation available for this date"
- This is expected behavior (historical data cleaned up)

## Verification Steps

### 1. Check Logs After Generating Recommendation
Look for these log messages:
```
INFO - User {user_id} has activity for {date}, targeting tomorrow: {tomorrow_date}
INFO - Saved enhanced recommendation with ID {id} for user {user_id} with target_date {target_date}
INFO - Cleaned up recommendations older than {cutoff_date} for user {user_id} (keeping 14 days)
```

### 2. Check Database
```sql
-- View all recommendations for a user (should see max 14-15 records)
SELECT id, target_date, generation_date, generated_at 
FROM llm_recommendations 
WHERE user_id = {your_user_id} 
ORDER BY target_date DESC;

-- Verify no duplicates for target_date
SELECT target_date, COUNT(*) as count 
FROM llm_recommendations 
WHERE user_id = {your_user_id} 
GROUP BY target_date 
HAVING COUNT(*) > 1;
-- Should return 0 rows
```

### 3. Test Journal Page
1. Go to Journal page
2. Navigate to different dates within last 14 days
3. Each date should show its **original** recommendation (not tomorrow's)
4. The recommendation text should reference the **correct date** and **correct prior activity**

### 4. Test Duplicate Prevention
1. Open Dashboard (generates recommendation for today/tomorrow)
2. Immediately refresh Dashboard
3. Check logs - should see: "Recommendation already exists for target_date {date}, skipping generation"
4. No duplicate database record should be created

## Expected Database State

For an active user on Day 14:
- Recommendations exist for: Day 1 through Day 14 (14-15 total records)
- Each `target_date` is unique
- Older recommendations automatically deleted

## Benefits

✅ **Journal page shows correct historical recommendations**  
✅ **AI Autopsy compares correct prescribed vs actual workouts**  
✅ **No database bloat** (14-day retention limit)  
✅ **No duplicate recommendations** (check before generating)  
✅ **Automatic cleanup** (maintenance-free)

## Adjusting Retention Period

To keep more/less history, modify the `keep_days` parameter in:
```python
# app/llm_recommendations_module.py line 787
cleanup_old_recommendations(user_id, keep_days=14)  # Change 14 to desired days
```

**Recommended values:**
- `keep_days=7`: One week (minimal storage)
- `keep_days=14`: Two weeks (current setting, good for weekly reviews)
- `keep_days=30`: One month (more storage, good for monthly analysis)

## Files Modified

1. `app/db_utils.py` - Added `cleanup_old_recommendations()` function
2. `app/llm_recommendations_module.py` - Added duplicate check and cleanup call

## Related Fixes

**IMPORTANT:** This fix addressed recommendation retention and duplicate prevention, but a **second issue** was discovered related to timezone-based date attribution:

- **This Document:** Prevents duplicate recommendations and implements 14-day retention
- **`TIMEZONE_DATE_ATTRIBUTION_FIX.md`:** Fixes Journal page showing wrong date's recommendation due to timezone handling

Both fixes are required for correct Journal page behavior.

## Deployment Notes

- No database schema changes required
- Existing recommendations remain intact
- Cleanup only affects recommendations older than 14 days
- Changes are backward compatible
- ⚠️ **Additional fix required:** See `TIMEZONE_DATE_ATTRIBUTION_FIX.md`

