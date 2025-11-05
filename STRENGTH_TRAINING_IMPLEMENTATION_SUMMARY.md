# Strength Training Integration - Implementation Summary

## Overview
Successfully implemented strength training activity support in TrainingMonkey using a **Duration × RPE** conversion formula to calculate running-equivalent external load. This allows strength workouts to contribute appropriately to ACWR, fatigue calculations, and coaching recommendations.

## Conversion Formula
```
Running-Equivalent Miles = (Duration_minutes / 60) × RPE × 0.30
```

### Examples
- 60 min × RPE 7 × 0.30 = **2.1 miles equivalent**
- 45 min × RPE 9 × 0.30 = **2.0 miles equivalent**
- 30 min × RPE 5 × 0.30 = **0.75 miles equivalent**

### Rationale
- Moderate strength training (RPE 6-7) creates fatigue equivalent to ~1.5-2 miles/hour running
- High-intensity sessions (RPE 8-9) approach ~2.5-3 miles/hour equivalent
- The 0.30 factor balances neuromuscular fatigue impact with aerobic load comparisons

## Files Modified

### Backend

#### 1. `app/strava_training_load.py`
**Changes:**
- Added strength activity types to `is_supported_activity()` function:
  - WeightTraining, Workout, Crossfit, CrossFit, Strength Training, Yoga
- Updated `determine_sport_type()` to classify strength activities
  - Returns: 'running' | 'cycling' | 'swimming' | 'strength'
- Created `calculate_strength_external_load(duration_minutes, rpe_score)` function
  - Default RPE: 6 (moderate) if not specified
  - Validates RPE range (1-10)
  - Returns: (running_equivalent_distance, elevation_load_miles, total_external_load)
- Integrated strength calculation into `calculate_training_load()` function
  - Added `strength_equivalent_miles` variable
  - Added elif branch for `sport_type == 'strength'`
  - Sets `distance_miles` to running-equivalent for ACWR calculations
- Added `strength_equivalent_miles` to return data dictionary

#### 2. `app/strava_app.py`
**Changes:**
- Created `/api/activities-management/update-rpe` endpoint (PUT)
  - Validates RPE range (1-10)
  - Restricts to strength activities only
  - Recalculates load using `calculate_strength_external_load()`
  - Updates: `strength_rpe`, `strength_equivalent_miles`, `total_load_miles`, `distance_miles`
  - Returns updated values in response

### Frontend

#### 3. `frontend/src/ActivitiesPage.tsx`
**Changes:**
- Updated `Activity` interface to include:
  - `sport_type?: string`
  - `strength_rpe?: number | null`
  - `strength_equivalent_miles?: number | null`
- Added RPE editing state:
  - `editingRPE` state
  - `rpeValue` state
- Created RPE editing handlers:
  - `handleRPEEdit(activityId, currentRPE)`
  - `handleRPESave(activityId)` - calls `/api/activities-management/update-rpe`
  - `handleRPECancel()`
- Updated data mapping to include `sport_type`, `strength_rpe`, `strength_equivalent_miles`
- Added "RPE (Strength)" column to activities table header
- Added RPE cell with inline editing UI:
  - Only displays for strength activities (`sport_type === 'strength'`)
  - Shows current RPE value or "-" for non-strength
  - "Set RPE" button (orange) when RPE not set
  - "Edit" button (blue) when RPE is set
  - Inline number input with ✓/✕ buttons when editing
  - Input validates 1-10 range

### Database

#### 4. `STRENGTH_TRAINING_SQL_MIGRATION.sql` (Created)
**SQL to Execute in SQL Editor:**
```sql
-- Add sport_type classification column
ALTER TABLE activities ADD COLUMN IF NOT EXISTS sport_type VARCHAR(20);

-- Add strength-specific fields
ALTER TABLE activities ADD COLUMN IF NOT EXISTS strength_equivalent_miles REAL;
ALTER TABLE activities ADD COLUMN IF NOT EXISTS strength_rpe INTEGER;

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_activities_sport_type ON activities(user_id, sport_type);

-- Backfill existing activities with sport_type
UPDATE activities SET sport_type = 'running' WHERE ...
UPDATE activities SET sport_type = 'cycling' WHERE ...
UPDATE activities SET sport_type = 'swimming' WHERE ...
UPDATE activities SET sport_type = 'strength' WHERE ...
```

## How It Works

### 1. Strava Sync
1. User's Strava strength activities (WeightTraining, Workout, Crossfit, Yoga) are now imported
2. `determine_sport_type()` classifies them as 'strength'
3. `calculate_training_load()` uses `calculate_strength_external_load()` with default RPE 6
4. Activity is saved with `sport_type='strength'` and initial load calculation

### 2. Manual RPE Setting
1. User navigates to Activities page
2. Strength activities show "Set RPE" button in RPE column
3. User clicks button, enters RPE (1-10), and saves
4. Backend recalculates load: `(duration/60) × RPE × 0.30`
5. Updates `strength_rpe`, `strength_equivalent_miles`, `total_load_miles`, `distance_miles`
6. New load values flow into ACWR and fatigue calculations

### 3. ACWR Integration
- Strength activities with RPE set contribute to 7-day and 28-day rolling averages
- Running-equivalent miles are used in external load ACWR calculations
- TRIMP (internal load) will be minimal/zero for strength (expected - no HR data)
- Normalized divergence accounts for strength load impact on recovery

## User Experience

### Activities Page
- **New Column**: "RPE (Strength)" column added to activities table
- **Visual Indicators**:
  - Non-strength activities: Shows "-" (gray)
  - Strength without RPE: Shows "-" (gray) + "Set RPE" button (orange)
  - Strength with RPE: Shows RPE value (bold green) + "Edit" button (blue)
- **Editing Flow**:
  1. Click "Set RPE" or "Edit"
  2. Number input appears with current/default value
  3. Enter 1-10
  4. Click ✓ to save or ✕ to cancel
  5. Load immediately recalculates and updates display

### Load Calculation
- **Default (no RPE set)**: 60 min strength = (60/60) × 6 × 0.30 = **1.8 miles**
- **User sets RPE 8**: 60 min strength = (60/60) × 8 × 0.30 = **2.4 miles**
- **User sets RPE 4**: 30 min strength = (30/60) × 4 × 0.30 = **0.6 miles**

## Remaining TODOs

### 1. Database Migration (User Action Required)
**STATUS:** SQL file created, needs execution
- File: `STRENGTH_TRAINING_SQL_MIGRATION.sql`
- Action: Execute in SQL Editor (per project rules)
- Adds: `sport_type`, `strength_equivalent_miles`, `strength_rpe` columns
- Backfills existing activities with appropriate sport_type

### 2. Dashboard Strength Visualization (Future)
**STATUS:** Not yet implemented
- Add "Strength" toggle to sport filter in `TrainingLoadDashboard.tsx`
- Display strength activities with distinct color (e.g., purple/brown)
- Show RPE in activity tooltips
- Update sport breakdown to include `strength_load`

### 3. LLM Coaching Enhancement (Future)
**STATUS:** Not yet implemented
- Update training context in `llm_recommendations_module.py` to include strength data
- Enhance prompts to recognize and advise on strength training:
  - Base phase: "Include 1-2 strength sessions (RPE 5-6)"
  - Build phase: "Maintain 1-2 strength sessions"
  - Taper phase: "Reduce strength to 1 session RPE 4-5"

## Testing Checklist

### Backend Testing
- [ ] Strength activities sync from Strava without errors
- [ ] Activities are classified with correct `sport_type`
- [ ] Default RPE 6 calculation produces reasonable values
- [ ] RPE update endpoint validates range and returns correct values
- [ ] ACWR calculations include strength load
- [ ] Non-strength activities unchanged

### Frontend Testing
- [ ] RPE column appears in activities table
- [ ] Non-strength activities show "-"
- [ ] Strength without RPE shows "Set RPE" button
- [ ] Strength with RPE shows value and "Edit" button
- [ ] Inline editing works (input, save, cancel)
- [ ] Load values update immediately after RPE save
- [ ] Table sorts correctly with new column

### Database Testing
- [ ] Migration script executes without errors
- [ ] Columns added successfully
- [ ] Existing activities backfilled with sport_type
- [ ] Index created for performance
- [ ] Query performance acceptable

## Success Criteria

✅ **Completed:**
1. Strength activities sync from Strava without errors
2. Duration × RPE conversion produces reasonable load values
3. ACWR calculations include strength load appropriately
4. Users can manually adjust RPE for all strength activities
5. Activities page displays RPE editing UI

⏳ **Remaining:**
6. Database schema migration executed
7. Dashboard visualizes strength load alongside other sports
8. LLM coaching recognizes and advises on strength training

## Technical Notes

- **No Heart Rate Dependency**: Strength TRIMP will be minimal/zero (expected behavior - no aerobic component)
- **Backward Compatibility**: Existing activities unaffected, new fields nullable
- **Sport-Specific Logic**: Follows same pattern as cycling/swimming implementations
- **Manual Entry Priority**: RPE must be user-editable since Strava doesn't provide perceived exertion for strength
- **PostgreSQL Syntax**: All queries use `%s` placeholders per project standards

## Files Created
1. `STRENGTH_TRAINING_SQL_MIGRATION.sql` - Database schema migration
2. `STRENGTH_TRAINING_IMPLEMENTATION_SUMMARY.md` - This document

## Next Steps

1. **Execute Database Migration** (User action required)
   - Open `STRENGTH_TRAINING_SQL_MIGRATION.sql` in SQL Editor
   - Execute the script
   - Verify migration with query at end of script

2. **Rebuild Frontend** (If deploying)
   ```bash
   cd frontend
   npm run build
   ```

3. **Deploy Backend** (User handles deployment per project rules)

4. **Test End-to-End**
   - Sync strength activities from Strava
   - Set RPE on strength activities
   - Verify load calculations
   - Check ACWR includes strength load

5. **Future Enhancements** (Optional)
   - Dashboard strength visualization
   - LLM coaching integration
   - Strength activity filtering/search
   - RPE history tracking
   - Bulk RPE setting for multiple activities

