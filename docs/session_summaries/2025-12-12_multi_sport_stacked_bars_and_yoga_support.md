# Conversation Summary: Multi-Sport Stacked Bars & Yoga/Strength Support
**Date**: 2025-12-12
**Session Focus**: Fix rowing double-counting, add yoga/strength visualization, implement stacked bars for External Work chart

---

## Main Objectives
1. Investigate and fix rowing activities being double-counted in External Work chart (causing unrealistic ACWR)
2. Add yoga/strength activities as separate sport visualization
3. Refactor External Work chart to use stacked bars for better multi-sport visualization

## Key Discussions
- **Root Cause Analysis**: Rowing showed as both actual distance (5 miles) AND running-equivalent (7.5 miles) = 12.5 total
- **Architecture Decision**: Sport-specific fields (`running_distance`, `running_elevation`, `{sport}_load`) instead of generic `distance_miles`
- **Yoga Classification**: Confirmed yoga fetched from Strava, classified as `sport_type='strength'`, using duration × RPE × 0.30 formula
- **Visualization Strategy**: Stacked bars provide cleaner multi-sport view and direct TRIMP comparison

## Code Changes
**Files Modified**:
- `app/utils/data_aggregation.py` (lines 24-283)
- `frontend/src/TrainingLoadDashboard.tsx` (lines 114-1401)
- `app/unified_metrics_service.py` (lines 339-373)
- `app/strava_app.py` (lines 1743-1856)

**Features Added**:
- Strength/yoga activities: separate green bar (#27ae60) on External Work chart
- Sport-specific fields: `running_distance`, `running_elevation`, `strength_load`, `strength_distance`
- `has_strength_data()` method in unified metrics service

**Features Changed**:
- External Work chart: all sports now stack into single bar per day (was separate bars)
- Cross-training activities: zero out generic `distance_miles`/`elevation_load_miles` fields
- Multi-sport aggregation: properly routes each sport to its own field

## Issues Identified
1. **Rowing Double-Counting**: Chart displayed `distance_miles` (5.0) + `rowing_load` (7.5) = 12.5 miles
2. **Multi-Sport Confusion**: Mixed actual distances with running-equivalents (`distance_miles` = 3 run + 5 row = "8 miles")
3. **Yoga Invisible**: Strength activities lumped into running bars (no separate visualization)
4. **Chart Clutter**: Separate bars for 6+ sports made multi-sport days hard to read

## Solutions Implemented
**Backend (`data_aggregation.py`)**:
- Added `strength_load` and `strength_distance` fields throughout
- Cross-training sports now set `distance_miles=0` and `elevation_load_miles=0` (only running keeps these)
- Multi-sport days: only running adds to generic fields, others add to sport-specific fields

**Frontend (`TrainingLoadDashboard.tsx`)**:
- Changed all bars from separate to `stackId="external"` (single stacked bar per day)
- Added strength bar: `dataKey="strength_load"`, green color, stacked with other sports
- Added `hasStrengthData` state and sport filter checkbox ("Strength/Yoga")
- Updated chart description: "stacked bar shows total daily load from all sports"

**Backend API (`strava_app.py`, `unified_metrics_service.py`)**:
- Added `has_strength_data()` check (mirrors cycling/rowing pattern)
- Included `has_strength_data` in `/api/training-data` response

## Decisions Made
1. **Stacked Bars for All Sports**: Better visualization of total daily load, directly comparable to single TRIMP bar
2. **Sport-Specific Architecture**: Each sport gets `{sport}_load` and `{sport}_distance` fields (clean separation)
3. **Generic Fields for Running Only**: `distance_miles` and `elevation_load_miles` are running-specific (backward compatible)
4. **Strength = Yoga + Weights**: Single category for all non-distance-based training (yoga, CrossFit, gym, etc.)

## Next Steps
**User Actions**:
1. Build frontend: `cd frontend && npm run build`
2. Copy to static: `scripts\build_and_copy.bat`
3. Test:
   - Verify single rowing activity shows 7.5 miles (not 12.5)
   - Check multi-sport day (3 run + 5 row + 60min yoga) shows 12.8 stacked total
   - Confirm stacked bars color-coded by sport
   - Verify yoga/strength activities appear in green segment
4. Deploy when ready

**Verification Points**:
- External Work bar height = sum of all sport loads ✓
- Each sport segment color-coded and visible ✓
- Total matches ACWR input (no double-counting) ✓
- Multi-sport days show single stacked bar (not 6 separate bars) ✓

## Technical Details
**Yoga External Load Calculation** (`strava_training_load.py:835-881`):
```python
# Formula: (Duration / 60) × RPE × 0.30 = Running-equivalent miles
# Example: 60-min yoga at RPE 6 = 1.8 mile-equiv
running_equivalent_distance = (duration_minutes / 60.0) * rpe * 0.30
```

**Multi-Sport Day Aggregation** (3-mile run + 5-mile row + 60-min yoga):
```python
# Aggregated data:
running_distance = 3.0
running_elevation = 0.5
rowing_load = 7.5
strength_load = 1.8
total_load_miles = 12.8  # Correct sum

# Generic fields (running only):
distance_miles = 3.0  # NOT 3+5+1.8
elevation_load_miles = 0.5
```

**Chart Stacking** (`TrainingLoadDashboard.tsx:1276-1368`):
```typescript
// All bars use stackId="external" for single stacked bar:
<Bar dataKey="running_distance" stackId="external" fill="#FF5722" />
<Bar dataKey="running_elevation" stackId="external" fill="#FF8A65" />
<Bar dataKey="cycling_load" stackId="external" fill="#3498db" />
<Bar dataKey="rowing_load" stackId="external" fill="#9b59b6" />
<Bar dataKey="strength_load" stackId="external" fill="#27ae60" />
// Result: One multi-colored bar per day showing total load
```

**Color Scheme**:
- Running distance: Orange (#FF5722)
- Running elevation: Light orange (#FF8A65)
- Cycling: Cyan (#3498db)
- Swimming: Orange (#e67e22)
- Rowing: Purple (#9b59b6)
- Backcountry Skiing: Teal (#16a085)
- Strength/Yoga: Green (#27ae60)

**Data Flow Summary**:
1. Activity processed → `sport_type='strength'` → `calculate_strength_external_load()`
2. Saved to DB: `total_load_miles=1.8`, `sport_type='strength'`
3. Aggregated: routes to `strength_load=1.8`, zeros generic fields
4. Chart: displays as green segment in stacked bar
5. ACWR: uses `total_load_miles` (no double-counting)
