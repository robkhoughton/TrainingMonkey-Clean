# Journal Page LLM Recommendation Parsing Fix

**Date**: December 3, 2025
**Issue**: Journal "Today's Training Decision" displaying all 3 LLM sections instead of just Daily Recommendation
**Status**: ✅ FIXED

---

## PROBLEM SUMMARY

### What Was Broken
- **Journal page** was displaying:
  1. DAILY RECOMMENDATION (~150-200 words) ✅ Should show
  2. WEEKLY PLANNING (~100-150 words) ❌ Should NOT show
  3. PATTERN INSIGHTS (~100-150 words) ❌ Should NOT show
- Too many blank lines in formatting
- User confused by excessive content in daily decision view

### Root Cause
The autopsy-informed recommendation generation (`app/strava_app.py:5112`) was:
1. Calling LLM and getting full response with all 3 sections
2. Saving the **UNPARSED** full text directly to `daily_recommendation` column
3. NOT using the `parse_llm_response()` function that separates sections

**Code location**: `app/strava_app.py` lines 5112-5172

---

## THE FIX

### Backend Changes (`app/strava_app.py:5117-5131`)

Added parsing step after LLM call:

```python
# CRITICAL FIX: Parse LLM response into separate sections
from llm_recommendations_module import parse_llm_response
sections = parse_llm_response(recommendation_text)

daily_rec = sections.get('daily_recommendation', '')
weekly_rec = sections.get('weekly_recommendation', '')
pattern_insights_text = sections.get('pattern_insights', '')
```

### Database Storage (lines 5146-5159, 5180-5182)

Now saves **3 separate sections** to their respective columns:

**UPDATE statement**:
```sql
UPDATE llm_recommendations
SET daily_recommendation = %s,      -- ONLY daily section
    weekly_recommendation = %s,     -- ONLY weekly section
    pattern_insights = %s,          -- ONLY pattern section
    raw_response = %s               -- Full LLM response preserved
```

**INSERT statement**: Same structure via `recommendation_data` dict

### What `parse_llm_response()` Does

From `app/llm_recommendations_module.py:1077-1171`:

1. **Tries 4 format patterns** (most to least specific):
   - Plain text headers (`DAILY RECOMMENDATION`)
   - Bold with colons (`**DAILY RECOMMENDATION:**`)
   - Double-hash markdown (`## DAILY RECOMMENDATION`)
   - Single-hash markdown (`# DAILY RECOMMENDATION`)

2. **Extracts each section** using regex patterns

3. **Removes excessive whitespace**:
   ```python
   sections[key] = re.sub(r'\n{3,}', '\n\n', sections[key])  # 3+ newlines → 2
   ```

4. **Returns dict** with 3 sections separated

---

## VERIFICATION

### Database Structure ✅
From `app/db_utils.py:344-358`:

```sql
CREATE TABLE llm_recommendations (
    ...
    daily_recommendation TEXT,      -- ✅ Daily section only
    weekly_recommendation TEXT,     -- ✅ Weekly section only
    pattern_insights TEXT,          -- ✅ Pattern section only
    raw_response TEXT,              -- ✅ Full LLM response preserved
    ...
);
```

### Retention Policy ✅
From `app/db_utils.py:505-528`:
- **Default**: 14 days
- Function: `cleanup_old_recommendations(user_id, keep_days=14)`
- Keeps last 14 days of recommendations for Journal page history

### Journal Display ✅
From `app/strava_app.py:4155`:

```sql
SELECT daily_recommendation  -- ✅ Queries ONLY daily section
FROM llm_recommendations
WHERE user_id = %s AND target_date = %s
```

---

## BENEFITS

### Immediate
1. **Journal page clean**: Shows only relevant daily decision
2. **No more clutter**: Removed weekly planning and pattern insights from daily view
3. **Better formatting**: Excessive blank lines removed by parser
4. **Proper separation**: Each section stored in correct column

### Future Roadmap Support
1. **Weekly autopsy feature**: Can access `weekly_recommendation` column for weekly analysis
2. **Pattern tracking**: `pattern_insights` column available for trend analysis
3. **Historical comparison**: All 3 sections preserved separately for analytics

---

## HISTORY

### Original Design (Working)
- Dashboard showed all 3 sections (removed in November)
- Journal showed ONLY daily section (was working correctly)

### What Broke
- When Dashboard LLM recommendations were removed
- Autopsy-informed generation was added
- **Parser was NOT integrated** into new autopsy flow
- Full LLM response saved to `daily_recommendation` column

### Fix Attempts (Dec 2-3, 2025)
- Investigated frontend formatting
- Checked timezone issues
- Reviewed git history
- **Found root cause**: Missing parser integration
- **Implemented fix**: Added parsing to autopsy recommendation flow

---

## TESTING CHECKLIST

When deploying, verify:

1. ✅ Journal "Today's Training Decision" shows ONLY daily recommendation
2. ✅ No "WEEKLY PLANNING" or "PATTERN INSIGHTS" headers visible
3. ✅ Blank lines reduced (max 2 consecutive newlines)
4. ✅ Database has 3 separate columns populated
5. ✅ Raw LLM response preserved in `raw_response` column
6. ✅ Logs show: `✅ Parsed LLM sections - Daily: X chars, Weekly: Y chars, Insights: Z chars`

---

## RELATED FILES

### Modified
- `app/strava_app.py` (lines 5117-5190) - Added parsing to autopsy-informed recommendations

### Referenced
- `app/llm_recommendations_module.py` - Parser function with whitespace compression
- `app/db_utils.py` - Table structure and retention policy
- `frontend/src/JournalPage.tsx` - Display formatting (no changes needed)

---

## CONCLUSION

The autopsy-informed recommendation generation now correctly parses LLM responses into 3 separate sections and stores them in dedicated database columns. The Journal page displays only the daily recommendation as originally designed.

**This fix restores the clean, focused daily decision view** while preserving all recommendation data for future features (weekly autopsy, pattern analysis).
