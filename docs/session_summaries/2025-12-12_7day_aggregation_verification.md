# Verification: 7-Day Total Load Aggregation Consistency

**Date**: 2025-12-12  
**Purpose**: Verify that Recovery card and chart use identical aggregation logic for 7-day Total Load

---

## Summary

✅ **VERIFIED**: Both the Recovery card (Compact Dashboard) and the External Work chart's 7-day rolling average use **identical aggregation logic** - they both sum `total_load_miles` from all sports in the 7-day window and divide by 7.

## Data Flow

### Recovery Card (Compact Dashboard)
1. **Source**: `/api/stats` endpoint
2. **Backend**: `UnifiedMetricsService.get_latest_complete_metrics(user_id)`
3. **Database Query**: Reads `seven_day_avg_load` from `activities` table (latest activity record)
4. **Calculation**: Stored value calculated by `update_moving_averages_standard()` or `update_moving_averages_enhanced()`

### Chart 7-Day Average Line
1. **Source**: `/api/training-data` endpoint  
2. **Backend**: Returns `seven_day_avg_load` from `activities` table for each day
3. **Frontend**: Uses `dataKey="seven_day_avg_load"` directly from API response
4. **Calculation**: Same stored value from `update_moving_averages_standard()` or `update_moving_averages_enhanced()`

## Aggregation Logic (Both Use Same)

**SQL Query** (from `update_moving_averages_standard()`):
```sql
SELECT COALESCE(SUM(total_load_miles), 0) 
FROM activities 
WHERE date BETWEEN %s AND %s AND user_id = %s
```

**Calculation**:
```python
seven_day_sum = get_sum_result(query, (seven_days_ago, date, user_id))
seven_day_avg_load = round(seven_day_sum / 7.0, 2)
```

**Key Points**:
- ✅ Sums `total_load_miles` from **ALL activities** (all sports) in 7-day window
- ✅ No filtering by `sport_type` - includes running, cycling, swimming, rowing, backcountry skiing, strength
- ✅ `total_load_miles` is already in running-mile equivalents for all sports
- ✅ Divides by 7 to get daily average

## Sport Inclusion Verification

**All sports contribute to `total_load_miles`**:
- **Running**: `total_load_miles = distance_miles + elevation_load_miles`
- **Cycling**: Calculated by `calculate_cycling_external_load()` → running-mile equivalent
- **Swimming**: Calculated by `calculate_swimming_external_load()` → running-mile equivalent  
- **Rowing**: Calculated by `calculate_rowing_external_load()` → running-mile equivalent
- **Backcountry Skiing**: Calculated by `calculate_backcountry_skiing_external_load()` → running-mile equivalent
- **Strength**: Calculated by `calculate_strength_external_load()` → running-mile equivalent

**Aggregation** (from `data_aggregation.py:206`):
```python
existing['total_load_miles'] += activity['total_load_miles'] or 0
```
This sums `total_load_miles` for all activities regardless of sport type.

## Code References

**Recovery Card**:
- Frontend: `frontend/src/CompactDashboardBanner.tsx:754` - `(metrics.sevenDayAvgLoad * 7).toFixed(1)`
- Backend: `app/strava_app.py:1938` - `'sevenDayAvgLoad': round(unified_metrics.get('seven_day_avg_load', 0), 2)`
- Service: `app/unified_metrics_service.py:431` - `'seven_day_avg_load': latest_activity_dict.get('seven_day_avg_load', 0)`

**Chart**:
- Frontend: `frontend/src/TrainingLoadDashboard.tsx:1374` - `dataKey="seven_day_avg_load"`
- Backend: `app/strava_app.py:get_training_data()` - Returns `seven_day_avg_load` from activities table
- Calculation: `app/strava_training_load.py:1938-1959` - `SUM(total_load_miles) / 7.0`

## Conclusion

Both the Recovery card and chart use the **exact same stored value** (`seven_day_avg_load` from `activities` table) which is calculated by summing `total_load_miles` from all sports in the 7-day window and dividing by 7. No inconsistency exists.

**Display Difference**:
- Recovery card shows: `sevenDayAvgLoad * 7` (total for 7 days)
- Chart shows: `seven_day_avg_load` (daily average)
- These are mathematically equivalent (just different units)

