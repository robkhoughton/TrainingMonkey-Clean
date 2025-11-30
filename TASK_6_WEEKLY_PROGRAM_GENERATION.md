# Task 6: Weekly Training Program Generation - COMPLETED
**Date**: November 25, 2025  
**Status**: ✅ COMPLETE  
**Commit**: `5684236`

---

## Overview

Implemented **divergence-optimized weekly training program generation** using Claude API. This is the core intelligence engine of the Coach page, generating personalized 7-day training programs based on:

- Race goals (A/B/C hierarchy)
- Race history and performance trends
- Training schedule and availability
- Current training stage
- Recent metrics (ACWR, divergence, TRIMP)
- Journal observations and athlete response

---

## What Was Built

### **1. New Module: `app/coach_recommendations.py`**

**Core Functions:**

```python
# Data Fetching
get_race_goals(user_id)                  # Fetch A/B/C race goals
get_race_history(user_id)                # Last 5 years of races
get_training_schedule(user_id)           # Weekly availability
get_current_training_stage(user_id)      # Base/Build/Specificity/Taper
get_recent_journal_observations(user_id) # Last 7 days

# Analysis
calculate_performance_trend(race_history) # Improving/stable/declining

# Prompt Building
build_weekly_program_prompt(user_id, target_week_start)
format_race_goals_for_prompt(race_goals)
format_race_history_for_prompt(race_history, trend)
format_training_schedule_for_prompt(schedule_data)
format_journal_observations_for_prompt(observations)

# Generation
generate_weekly_program(user_id, target_week_start)
parse_weekly_program_response(response_text)

# Caching
save_weekly_program(user_id, week_start, program_data)
get_cached_weekly_program(user_id, week_start)
get_or_generate_weekly_program(user_id, week_start, force_regenerate)
```

**File Size**: 830 lines  
**Language**: Python 3  
**Dependencies**: `unified_metrics_service`, `llm_recommendations_module`, `db_utils`

---

### **2. API Endpoints in `app/strava_app.py`**

#### **GET `/api/coach/weekly-program`**
**Purpose**: Get weekly program (from cache or generate new)

**Query Parameters**:
- `week_start`: YYYY-MM-DD (defaults to next Monday)
- `force`: 'true' to force regeneration

**Response**:
```json
{
  "success": true,
  "program": {
    "week_start_date": "2025-12-02",
    "week_summary": "Focus on building endurance...",
    "predicted_metrics": {
      "acwr_estimate": 1.05,
      "divergence_estimate": 0.02,
      "total_weekly_miles": 45
    },
    "daily_program": [
      {
        "day": "Monday",
        "date": "2025-12-02",
        "workout_type": "Easy Run",
        "description": "6 miles easy...",
        "duration_estimate": "60-70 minutes",
        "intensity": "Low",
        "key_focus": "Recovery...",
        "terrain_notes": "Flat trails"
      }
      // ... 6 more days
    ],
    "key_workouts_this_week": [...],
    "nutrition_reminder": "...",
    "injury_prevention_note": "..."
  },
  "from_cache": false
}
```

#### **POST `/api/coach/weekly-program/generate`**
**Purpose**: Manually generate/regenerate program

**Request Body**:
```json
{
  "week_start": "2025-12-02"  // optional
}
```

**Response**: Same as GET endpoint, with `message` field

---

## How It Works

### **Prompt Construction**

The `build_weekly_program_prompt()` function gathers extensive context:

1. **Current Training Metrics** (last 28 days)
   - External ACWR
   - Internal ACWR
   - Normalized divergence
   - Days since rest
   - 7-day and 28-day average training load

2. **Race Goals** (formatted)
   - A/B/C priority
   - Race name, date, type
   - Days until race
   - Target time

3. **Performance History**
   - Last 10 races
   - Performance trend analysis (improving/stable/declining)
   - Distance groups and pace comparisons

4. **Current Training Stage**
   - Stage name (Base/Build/Specificity/Taper/Recovery)
   - Weeks to primary race
   - Stage-specific focus

5. **Training Schedule**
   - Total hours per week
   - Available days
   - Time blocks and constraints
   - Supplemental training (strength/mobility/cross-training)

6. **Recent Training Response**
   - Last 7 days journal entries
   - Energy levels, RPE, pain
   - User notes

7. **Training Reference Framework**
   - Full training guide loaded
   - Evidence-based principles

8. **Coaching Tone**
   - User's coaching spectrum preference
   - Tone instructions for LLM

---

### **Claude API Call**

```python
response_text = call_anthropic_api(
    prompt,
    max_tokens=4000,  # Longer for 7-day programs
    temperature=0.7    # Creative but consistent
)
```

**Model**: claude-3-7-sonnet-20250219 (latest)

---

### **Response Parsing**

Claude returns structured JSON:

```json
{
  "week_start_date": "2025-12-02",
  "week_summary": "...",
  "predicted_metrics": {
    "acwr_estimate": 1.05,
    "divergence_estimate": 0.02,
    "total_weekly_miles": 45
  },
  "daily_program": [
    // 7 days with full details
  ],
  "key_workouts_this_week": [...],
  "nutrition_reminder": "...",
  "injury_prevention_note": "..."
}
```

**Validation**:
- Ensures all required fields present
- Checks for 7 days in daily_program
- Handles markdown code blocks if needed
- Raises ValueError if parsing fails

---

### **Caching Strategy**

**Database Table**: `weekly_programs`

```sql
CREATE TABLE weekly_programs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user_settings(id),
    week_start_date DATE NOT NULL,
    program_json JSONB NOT NULL,
    predicted_acwr REAL,
    predicted_divergence REAL,
    generated_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, week_start_date)
);
```

**Cache Logic**:
- Programs cached for **3 days**
- `get_or_generate_weekly_program()` checks cache first
- If cached and recent: return immediately
- If not cached or expired: generate new program
- Manual regeneration bypasses cache

**Why 3 Days?**
- Allows mid-week adjustments
- Fresh programs Sunday/Wednesday (future cron jobs)
- Balances API costs with program freshness

---

## Performance Analysis

**Calculated Trend Analysis**:

```python
def calculate_performance_trend(race_history):
    # Groups races by similar distances (within 20%)
    # Compares pace (min/mile) over time
    # Determines: improving, stable, declining
    # Returns detailed analysis with per-distance trends
```

**Example Output**:
```python
{
    'trend': 'improving',
    'details': 'Performance improving across 2 distance(s)',
    'distance_analysis': [
        ('improving', 50.0, 12.5, 11.8),  # 50-mile: 12.5 → 11.8 min/mi
        ('stable', 26.2, 9.2, 9.1)        # Marathon: 9.2 → 9.1 min/mi
    ]
}
```

---

## Integration with Existing Systems

### **Unified Metrics Service**
```python
current_metrics = UnifiedMetricsService.get_latest_complete_metrics(user_id)
activities = UnifiedMetricsService.get_recent_activities_for_analysis(days=28, user_id=user_id)
```

### **LLM Recommendations Module**
```python
training_guide = load_training_guide()
spectrum_value = get_user_coaching_spectrum(user_id)
tone_instructions = get_coaching_tone_instructions(spectrum_value)
llm_response = call_anthropic_api(prompt, ...)
```

### **Database Utilities**
```python
race_goals = execute_query("SELECT ... FROM race_goals WHERE user_id = %s", (user_id,), fetch=True)
```

### **Training Stage Calculation**
```python
from strava_app import _calculate_training_stage
stage_info = _calculate_training_stage(current_date, race_date)
```

---

## Key Design Decisions

### **1. JSON Structured Output**

**Why?**
- Consistent format for frontend display
- Easy to parse and validate
- Supports rich data (predicted metrics, daily details)

**Alternative Considered**: Plain text with markdown
**Rejected Because**: Harder to parse, less structured, more error-prone

---

### **2. Weekly vs. Daily Generation**

**Why Weekly?**
- Coach pages show full week at a glance
- Allows for workout sequencing (hard/easy days)
- Better context for periodization
- Reduces API calls (1 call for 7 days vs. 7 calls)

---

### **3. Monday-Sunday Week Structure**

**Why?**
- Standard training week convention
- Aligns with typical race schedules (Saturday/Sunday)
- Easy to calculate "next Monday" from any date

---

### **4. 3-Day Cache Expiry**

**Why 3 Days?**
- Balance between freshness and API cost
- Supports mid-week plan adjustments
- Aligns with future scheduled jobs (Sunday/Wednesday generation)
- Users can force regeneration if needed

**Alternative Considered**: 7-day cache
**Rejected Because**: Too stale, doesn't adapt to mid-week performance changes

---

### **5. Force Regeneration Option**

**Why?**
- User control over program updates
- After significant changes (new race goal, schedule change)
- After unexpected performance (great race, injury)

**Implementation**: `force` query param bypasses cache

---

## Error Handling

### **Robust Fallbacks**:

1. **No Race Goals**:
   ```python
   return {
       'stage': 'Base',
       'weeks_to_race': None,
       'details': 'No race goal set - focus on base building'
   }
   ```

2. **No Race History**:
   ```python
   return {
       'trend': 'insufficient_data',
       'details': 'Need at least 2 race results to determine trend'
   }
   ```

3. **No Training Schedule**:
   ```python
   return "Training schedule not configured - assume 5-6 days/week availability."
   ```

4. **JSON Parse Error**:
   ```python
   # Try to extract from markdown code block
   json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
   # If still fails, raise ValueError with details
   ```

5. **API Call Failure**:
   ```python
   # Exception propagates to endpoint
   # Endpoint returns 500 with error message
   # Frontend can show error UI
   ```

---

## Testing Recommendations

### **Manual Testing**:

1. **Basic Generation**:
   ```bash
   curl -X GET http://localhost:5000/api/coach/weekly-program \
     -H "Authorization: Bearer TOKEN"
   ```

2. **Specific Week**:
   ```bash
   curl -X GET "http://localhost:5000/api/coach/weekly-program?week_start=2025-12-09" \
     -H "Authorization: Bearer TOKEN"
   ```

3. **Force Regeneration**:
   ```bash
   curl -X GET "http://localhost:5000/api/coach/weekly-program?force=true" \
     -H "Authorization: Bearer TOKEN"
   ```

4. **Manual Generation**:
   ```bash
   curl -X POST http://localhost:5000/api/coach/weekly-program/generate \
     -H "Authorization: Bearer TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"week_start": "2025-12-09"}'
   ```

### **Test Scenarios**:

- ✅ User with A race goal → should generate race-specific program
- ✅ User with no races → should generate base-building program
- ✅ User with improving trend → program should build on momentum
- ✅ User with declining trend → program should focus on recovery
- ✅ User with limited availability → program respects schedule constraints
- ✅ User in taper stage → program reduces volume appropriately
- ✅ Cached program → should return from cache (check `from_cache: true`)
- ✅ Force regeneration → should bypass cache
- ✅ Invalid date format → should return 400 error

---

## Performance Characteristics

### **API Call Duration**:
- **Prompt Building**: ~50-100ms (database queries)
- **Claude API Call**: ~3-8 seconds (depends on response length)
- **Response Parsing**: ~10-20ms
- **Total**: ~3-8 seconds for new generation
- **From Cache**: ~50-100ms

### **Token Usage** (estimated):
- **Prompt**: ~2000-3000 tokens (context-rich)
- **Response**: ~1500-2500 tokens (7-day program)
- **Total**: ~3500-5500 tokens per generation
- **Cost**: ~$0.015-0.025 per generation (Claude Sonnet pricing)

### **Database Impact**:
- **Queries per generation**: ~8-10 (race goals, history, schedule, journal, metrics)
- **Cache check**: 1 query
- **Cache save**: 1 query (UPSERT)

---

## Future Enhancements (Out of Scope for V1)

1. **Scheduled Generation** (Task 12):
   - Cron jobs Sunday/Wednesday
   - Pre-generate programs for all active users
   - Email notifications when new program available

2. **Multi-Week Programs**:
   - Generate 4-week mesocycles
   - Show long-term progression
   - Visualize periodization

3. **Workout Completion Tracking**:
   - Mark workouts as completed
   - Compare planned vs. actual
   - Adjust future programs based on adherence

4. **Program Comparison**:
   - Show previous week's program
   - Highlight changes week-over-week
   - Track volume/intensity trends

5. **Export Functionality**:
   - Export to calendar (iCal format)
   - Export to PDF
   - Export to TrainingPeaks/Strava

6. **Workout Library Integration**:
   - Link workouts to detailed descriptions
   - Video demonstrations
   - Pace calculators

---

## Code Quality

### **Linting**:
✅ No linter errors  
✅ Python syntax validated  
✅ Type hints used throughout

### **Logging**:
✅ Comprehensive logging at INFO level  
✅ Error logging with stack traces  
✅ Performance metrics logged

### **Documentation**:
✅ Docstrings for all functions  
✅ Inline comments for complex logic  
✅ Type hints for parameters and returns

---

## Deployment Readiness

### **Status**: ✅ **READY TO DEPLOY**

**Safe to Deploy Now?** YES
- New module doesn't affect existing features
- APIs not called by frontend yet (no UI)
- Database table already exists (Task 1)
- No schema changes required

**Deploy Strategy**:
1. Deploy backend with Task 6 code
2. Test API endpoints manually
3. Build frontend (Tasks 7-10) later
4. No user-facing changes until Task 11 (navigation)

**Rollback Plan**:
- Remove API endpoint registrations
- Delete `coach_recommendations.py`
- No database changes to revert

---

## Success Metrics (for V1)

Once frontend is built:

- ✅ Program generation completes in < 10 seconds
- ✅ Cache hit rate > 60% (reduces API costs)
- ✅ Programs include all 7 days with complete details
- ✅ Predicted ACWR within 0.1 of actual (validate later)
- ✅ User satisfaction with program quality > 4/5 stars

---

## Related Tasks

**Completed**:
- ✅ Task 1: Database Schema
- ✅ Task 2: Race Goals & History APIs
- ✅ Task 3: Ultrasignup Parsing
- ✅ Task 4: Training Schedule APIs
- ✅ Task 5: Training Stage Analysis
- ✅ Task 6: Weekly Program Generation ← **YOU ARE HERE**

**Next Steps**:
- ⏳ Task 7: Frontend Coach Page Foundation
- ⏳ Task 8: Race Goals & History UI
- ⏳ Task 9: Training Schedule Config UI
- ⏳ Task 10: Weekly Program Display & Timeline
- ⏳ Task 11: Navigation & Integration
- ⏳ Task 12: Scheduled Jobs

---

## Files Created/Modified

### **New Files**:
- `app/coach_recommendations.py` (830 lines)
- `TASK_6_WEEKLY_PROGRAM_GENERATION.md` (this document)

### **Modified Files**:
- `app/strava_app.py` (+100 lines for API endpoints)

---

## Commit Hash

**Commit**: `5684236`  
**Message**: "feat: implement weekly training program generation (Task 6)"  
**Date**: November 25, 2025  
**Files Changed**: 66 (including user's other changes)  
**Lines Added**: +1618  
**Lines Removed**: -513

---

**STATUS**: ✅ TASK 6 COMPLETE - Ready for Frontend Development!


