# Conversation Summary: Rowing Activity Double-Counting Fix
**Date**: 2025-12-12
**Session Focus**: Investigate and fix double-counting issue in External Work chart for rowing activities

---

## Main Objectives
Fix unrealistic ACWR values caused by rowing activities being double-counted in the External Work visualization. User suspected rowing distance was counted both as base mileage AND as mileage equivalents.

## Key Discussions
- **Root Cause Analysis**: Traced data flow from activity fetch → calculation → aggregation → chart display
- **Architecture Review**: Examined how different sports (running, cycling, rowing, swimming) are processed and displayed
- **Design Intent**: Clarified that cross-training should show ONLY as running-mile equivalents in colored bars, while running shows distance + elevation breakdown
- **Solution Selection**: Chose sport-specific field approach (Option 2) over backward-compatible hack, since app is in beta

## Code Changes
- **Files Modified**:
  - `app/utils/data_aggregation.py` (lines 23-302)
  - `frontend/src/TrainingLoadDashboard.tsx` (lines 1256-1289)

- **Features Changed**:
  - External Work chart now uses `running_distance` + `running_elevation` bars (stacked) for running
  - Cross-training sports (cycling, rowing, swimming, backcountry skiing) display as separate single bars
  - All bars show running-mile equivalents for consistent comparison

## Issues Identified
1. **Double-Counting Bug**: Rowing activities displayed as both:
   - Generic `distance_miles` bar (5.0 actual rowing miles)
   - Sport-specific `rowing_load` bar (7.5 running-equivalent miles)
   - Result: 12.5 miles shown instead of 7.5

2. **Multi-Sport Day Problem**: On days with running + rowing:
   - `distance_miles` summed actual run miles + actual row miles (mixing units)
   - Chart showed meaningless total (e.g., 3 run + 5 row = "8 miles")

3. **Architectural Confusion**: Generic fields (`distance_miles`, `elevation_load_miles`) used for two conflicting purposes:
   - Activities page: store actual distances
   - Dashboard chart: display running distances

## Solutions Implemented
**Backend (`app/utils/data_aggregation.py`)**:
- Added `running_distance` and `running_elevation` fields to all sport initialization blocks
- Cross-training activities now zero out generic `distance_miles` and `elevation_load_miles` fields
- Multi-sport day aggregation only adds to `distance_miles` if activity is running
- Each sport maintains separate `{sport}_load` and `{sport}_distance` fields

**Frontend (`frontend/src/TrainingLoadDashboard.tsx`)**:
- Replaced generic bars with sport-specific bars:
  - `dataKey="distance_miles"` → `dataKey="running_distance"`
  - `dataKey="elevation_load_miles"` → `dataKey="running_elevation"`
- Updated tooltip labels to match new field names

## Decisions Made
1. **No Backward Compatibility Constraints**: Since app is in beta, implemented cleanest solution rather than hack
2. **Running is Special**: Running shows breakdown (distance + elevation stacked), cross-training shows single equivalent bar
3. **All Equivalents**: Every bar on External Work chart represents running-mile equivalents for fair comparison
4. **Field Separation**: Keep actual distances in sport-specific fields (`rowing_distance`, etc.) separate from chart display fields

## Next Steps
**User Actions Required**:
1. Build frontend: `cd frontend && npm run build`
2. Copy to static: `scripts\build_and_copy.bat`
3. Test locally: `scripts\start_mock_server.bat` → visit `http://localhost:5001/dashboard`
4. Verify:
   - Single rowing activity shows 7.5 miles (not 12.5)
   - Multi-sport day (3 run + 5 row) shows 11.0 total (3.5 + 7.5)
   - Chart bars are color-coded by sport
5. Deploy when ready

**Future Considerations**:
- Activities page unchanged (still shows actual distances)
- Journal page displays cumulative mile equivalents
- AI Autopsy should review activities as listed on Activities page, not Journal summary

## Technical Details
**Data Flow Example (5-mile rowing activity)**:

```python
# Database (unchanged):
distance_miles = 5.0              # Actual rowing distance
total_load_miles = 7.5            # Running-equivalent (1.5x multiplier)
rowing_equivalent_miles = 7.5
sport_type = 'rowing'

# Aggregated data (NEW):
running_distance = 0
running_elevation = 0
rowing_load = 7.5                 # Running-equivalent
distance_miles = 0                # Zeroed for chart
elevation_load_miles = 0          # Zeroed for chart

# Chart displays:
- Rowing bar (purple): 7.5 miles  ✅ CORRECT
```

**Multi-Sport Day Example (3-mile run + 5-mile row)**:

```python
# Aggregated data:
running_distance = 3.0
running_elevation = 0.5
running_load = 3.5
rowing_load = 7.5
total_load_miles = 11.0

# Chart displays:
- Running distance (orange): 3.0
- Running elevation (light orange, stacked): 0.5
- Rowing (purple): 7.5
- Total visual: 11.0 miles         ✅ CORRECT
```

**Key Code Changes**:

File: `app/utils/data_aggregation.py:103-130`
```python
elif sport_type == 'rowing':
    daily_aggregates[date]['rowing_load'] = activity.get('total_load_miles', 0)
    daily_aggregates[date]['running_distance'] = 0
    daily_aggregates[date]['running_elevation'] = 0
    # Zero out generic fields for chart
    daily_aggregates[date]['distance_miles'] = 0
    daily_aggregates[date]['elevation_load_miles'] = 0
```

File: `frontend/src/TrainingLoadDashboard.tsx:1256-1278`
```typescript
<Bar dataKey="running_distance" stackId="running" />
<Bar dataKey="running_elevation" stackId="running" />
// Cross-training bars unchanged (cycling_load, rowing_load, etc.)
```
