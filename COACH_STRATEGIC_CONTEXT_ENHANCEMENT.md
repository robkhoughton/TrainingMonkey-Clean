# Coach Page Strategic Context Enhancement

**Date**: November 30, 2025
**Status**: ✅ Complete

---

## Overview

Enhanced the Coach page to include strategic narrative context alongside the structured weekly workout plan. This creates a complete coaching ecosystem that integrates with the Journal page:

- **Coach Page** = Strategic planning (weekly structure + context)
- **Journal Page** = Daily execution (tactical decisions + autopsy feedback)

---

## Changes Implemented

### 1. Backend Enhancement (`app/coach_recommendations.py`)

#### Prompt Enhancement
- Added `strategic_context` section to JSON output format
- Requests three narrative subsections:
  - **weekly_focus**: Primary training goal and stage alignment
  - **load_management_strategy**: ACWR targets and volume/intensity rationale
  - **pattern_insights**: Recent training response observations

#### Response Parsing
- Updated `parse_weekly_program_response()` to validate and extract `strategic_context`
- Added backward compatibility with default values if missing
- No breaking changes to existing program structure

### 2. Frontend Enhancement (`frontend/src/`)

#### WeeklyProgramDisplay.tsx
- Updated `WeeklyProgram` interface to include optional `strategic_context` field
- Maintains backward compatibility

#### CoachPage.tsx
- Added strategic context display section below weekly workout plan
- Three color-coded cards with clear visual hierarchy:
  - **🎯 This Week's Focus** (blue) - Training goal and stage context
  - **📈 Load Management Strategy** (yellow) - ACWR and volume guidance
  - **🔍 Recent Training Patterns** (green) - Pattern insights
- Added integration hint directing users to Journal for daily execution

---

## User Experience Flow

### Weekly Planning (Coach Page)
1. User visits Coach page (Sunday/Monday)
2. Views structured 7-day workout plan (Mon-Sun)
3. Reads strategic context to understand:
   - Why each workout matters (weekly focus)
   - How load is being managed (ACWR/divergence)
   - What patterns are emerging (recent response)
4. Mental commit to week's structure

### Daily Execution (Journal Page)
1. User visits Journal daily
2. Reads today's specific decision (tactical adjustments)
3. Executes workout
4. Logs observations (energy, RPE, pain, notes)
5. Reviews AI autopsy (validation + tomorrow's preview)

---

## API Structure

### Response Format
```json
{
  "success": true,
  "program": {
    "week_start_date": "2025-12-02",
    "week_summary": "...",
    "predicted_metrics": { ... },
    "daily_program": [ ... ],
    "key_workouts_this_week": [ ... ],
    "strategic_context": {
      "weekly_focus": "2-3 sentences about primary goal and stage alignment",
      "load_management_strategy": "2-3 sentences about ACWR targets and volume balance",
      "pattern_insights": "2-3 sentences about recent response and monitoring points"
    }
  }
}
```

---

## Visual Design

- **Color-coded sections** for easy scanning
- **Left border accent** (4px) for visual hierarchy
- **Consistent spacing** (1rem between sections)
- **Prominent headers** with emojis and color-matched text
- **Integration hint** at bottom linking to Journal page

---

## Backward Compatibility

✅ Existing weekly programs without `strategic_context` still work
✅ Default values provided if LLM doesn't return context
✅ Optional rendering - section only shows if context exists

---

## Benefits

1. **Complete Picture**: Users understand both WHAT to do and WHY
2. **Strategic Thinking**: Elevates from task execution to intelligent planning
3. **Context Integration**: Explains how week fits into bigger training arc
4. **Load Awareness**: Clear ACWR/divergence guidance prevents overtraining
5. **Pattern Recognition**: Highlights trends user might miss
6. **Journal Integration**: Clear division between weekly planning and daily execution

---

## Next Steps (Future Enhancements)

- Add expandable/collapsible strategic context section
- Include visual ACWR trend chart in load management
- Add "compare to last week" insights
- Link pattern insights to specific journal entries
- Add coaching tone adjustment based on user preference

---

## Technical Notes

- LLM model: Claude Sonnet 4.5
- Prompt length: ~1500 tokens
- Response time: ~8-15 seconds for full weekly program
- Cache strategy: Database cache with weekly expiration
- Frontend rendering: Conditional display with graceful fallback

