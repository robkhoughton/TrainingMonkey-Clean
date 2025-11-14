# Swimming Dashboard Changes - UI/UX Overview

## Current Dashboard State
The dashboard already has **multi-sport support** infrastructure for Running and Cycling:
- Sport-specific load tracking (`running_load`, `cycling_load`)
- Sport type checkboxes to toggle visibility
- Color coding: Running (green), Cycling (blue)
- Sport summary statistics
- Mixed-sport day detection

## What Swimming Will Look Like

### 1. **Sport Toggle Controls** (TrainingLoadDashboard.tsx)
**Current:**
```
Show Sports: [ ] Running (green)  [ ] Cycling (blue)
```

**With Swimming:**
```
Show Sports: [ ] Running (green)  [ ] Cycling (blue)  [ ] Swimming (orange)
```

**Visual:**
- Only shows if user has swimming data (like cycling)
- Orange color theme for swimming
- Users can toggle swimming on/off independent of other sports

### 2. **Training Load Chart**
**Current:** Stacked bars showing running (green) + cycling (blue)

**With Swimming:** Stacked bars showing:
- Running load (green) - bottom
- Cycling load (blue) - middle  
- Swimming load (orange) - top

**Example Day:**
```
Total Load: 10.5 miles
├─ Running: 5.0 mi (green bar)
├─ Cycling: 3.0 mi equiv (blue bar)  
└─ Swimming: 2.5 mi equiv (orange bar)
```

### 3. **Activity Tooltip** (when hovering over chart)
**Current:**
```
Oct 5, 2024
Morning Run - 5.2 mi
TRIMP: 65.3 | Load: 6.1 mi
```

**With Swimming (Mixed Day):**
```
Oct 5, 2024
Morning Run - 5.0 mi
Swim Workout - 0.5 mi (2.0 mi equiv)
TRIMP: 85.5 | Total Load: 7.0 mi
Sport Breakdown:
  Running: 5.0 mi
  Swimming: 2.0 mi equiv
```

### 4. **Sport Summary Panel** (if implemented)
**Shows totals for the period:**
```
┌─────────────────────────────────────┐
│ Last 30 Days                        │
├─────────────────────────────────────┤
│ 🏃 Running:   45 activities, 125 mi │
│ 🚴 Cycling:   12 activities, 240 mi │
│                (80 mi equiv)        │
│ 🏊 Swimming:   8 activities, 12 mi  │
│                (48 mi equiv)        │
├─────────────────────────────────────┤
│ Total Load: 253 mi equiv            │
└─────────────────────────────────────┘
```

### 5. **Activity Type Icons**
- 🏃 Running (green)
- 🚴 Cycling (blue)
- 🏊 Swimming (orange)
- 🏃🚴 Mixed (if running + cycling same day)
- 🏃🏊 Mixed (if running + swimming same day)
- 🏃🚴🏊 Triathlon day!

## Required Code Changes

### Frontend Changes (TypeScript/React)

#### 1. TrainingLoadDashboard.tsx - Add Swimming State
```typescript
// Line ~89: Add swimming to selected sports
const [selectedSports, setSelectedSports] = useState(['running', 'cycling', 'swimming']);
const [hasSwimmingData, setHasSwimmingData] = useState(false);
```

#### 2. TrainingLoadDashboard.tsx - Add Swimming Checkbox
```typescript
// After line ~817: Add swimming checkbox
<label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
  <input
    type="checkbox"
    checked={selectedSports.includes('swimming')}
    onChange={() => setSelectedSports(prev =>
      prev.includes('swimming') ? prev.filter(s => s !== 'swimming') : [...prev, 'swimming']
    )}
  />
  <span style={{ color: '#e67e22' }}>Swimming</span>
</label>
```

#### 3. TrainingLoadDashboard.tsx - Add Swimming Bar to Charts
```typescript
// In chart components: Add swimming bar (similar to cycling)
<Bar
  dataKey="swimming_load"
  name="Swimming (Running Equivalent)"
  stackId="a"
  fill="#e67e22"
  opacity={selectedSports.includes('swimming') ? 0.7 : 0.3}
/>
```

#### 4. Update Data Fetching Logic
```typescript
// Check for swimming data (similar to cycling check)
const hasSwimming = filtered.some(day => day.swimming_load > 0);
setHasSwimmingData(hasSwimming);
```

### Backend Changes (Python)

#### 1. data_aggregation.py - Add Swimming Breakdown
```python
# Line ~27-32: Add swimming_load and swimming_distance fields
daily_aggregates[date]['swimming_load'] = 0
daily_aggregates[date]['swimming_distance'] = 0

# Line ~70-82: Add swimming sport type handling
elif sport_type == 'swimming':
    daily_aggregates[date]['swimming_load'] = activity.get('total_load_miles', 0)
    daily_aggregates[date]['running_load'] = 0
    daily_aggregates[date]['cycling_load'] = 0
    daily_aggregates[date]['swimming_distance'] = activity.get('distance_miles', 0)
    daily_aggregates[date]['day_type'] = 'swimming'

# Line ~143-148: Add swimming to aggregation logic
elif sport_type == 'swimming':
    existing['swimming_load'] = existing.get('swimming_load', 0) + activity.get('total_load_miles', 0)
    existing['swimming_distance'] = existing.get('swimming_distance', 0) + activity.get('distance_miles', 0)

# Line ~163-168: Update day type logic for swimming
elif 'swimming' in existing.get('sport_types', []):
    existing['day_type'] = 'swimming'

# Line ~174-183: Ensure swimming fields exist (backward compatibility)
if 'swimming_load' not in daily_data:
    daily_data['swimming_load'] = 0
if 'swimming_distance' not in daily_data:
    daily_data['swimming_distance'] = 0
```

#### 2. unified_metrics_service.py - Add Swimming Detection
```python
# Add has_swimming_data() method (similar to has_cycling_data)
@staticmethod
def has_swimming_data(user_id, start_date=None, end_date=None):
    """Check if user has any swimming activities in date range"""
    try:
        result = execute_query(
            """
            SELECT COUNT(*) as count 
            FROM activities 
            WHERE user_id = %s 
            AND sport_type = 'swimming'
            AND date BETWEEN %s AND %s
            """,
            (user_id, start_date, end_date),
            fetch=True
        )
        return result[0]['count'] > 0 if result else False
    except Exception as e:
        logger.error(f"Error checking swimming data: {e}")
        return False
```

#### 3. strava_app.py - Update API Response
```python
# Line ~1682-1687: Add swimming detection
has_swimming_data = UnifiedMetricsService.has_swimming_data(
    current_user.id, start_date_str, end_date.strftime('%Y-%m-%d')
)

# Add to response JSON:
'has_swimming_data': has_swimming_data,
```

#### 4. Activity Detail Tooltips
```python
# Add swimming_equivalent to activity detail:
{
    'type': activity.get('type', 'Unknown'),
    'sport': sport_type,
    'distance': activity.get('distance_miles', 0),
    'load': activity.get('total_load_miles', 0),
    'cycling_equivalent': activity.get('cycling_equivalent_miles'),
    'swimming_equivalent': activity.get('swimming_equivalent_miles'),  # ADD THIS
    'average_speed': activity.get('average_speed_mph')
}
```

## Color Scheme
- **Running:** `#2ecc71` (green) - existing
- **Cycling:** `#3498db` (blue) - existing  
- **Swimming:** `#e67e22` (orange) - NEW
- **Mixed Day:** Gradient or layered colors

## User Experience Flow

### First Swimming Activity Synced:
1. User syncs Strava data including a swim
2. Backend calculates swimming equivalent (1 mi → 4 mi running equiv)
3. Dashboard automatically detects `has_swimming_data: true`
4. "Swimming" checkbox appears next to Running and Cycling
5. Orange bars appear in load charts (if Swimming is checked)
6. Tooltip shows actual swim distance + running equivalent

### Triathlete Multi-Sport Day:
```
Morning Workout:
├─ Swim: 1 mile (30 min) → 4.0 mi equiv
├─ Bike: 20 miles (60 min) → 6.5 mi equiv
└─ Run: 3 miles (24 min) → 3.0 mi equiv
───────────────────────────────────────
Total Load: 13.5 mi equiv
TRIMP: 145
Day Type: TRIATHLON! 🏊🚴🏃
```

## Summary

### What's Great:
✅ **Infrastructure already exists** - just add swimming as third sport  
✅ **Minimal UI changes** - one checkbox, one color, one bar series  
✅ **Backwards compatible** - no impact on users without swimming  
✅ **Automatic detection** - shows only if user has swimming data  

### Changes Required:
- **Frontend:** ~40 lines (add checkbox, bar, colors, state)
- **Backend:** ~60 lines (add swimming fields to aggregation)
- **Database:** 1 column (`swimming_equivalent_miles`)

### Effort Estimate:
- **Frontend:** 30 minutes
- **Backend:** 20 minutes (already done if swimming support added)
- **Testing:** 15 minutes
- **Total:** ~1 hour

### Design Consistency:
Swimming will look and feel **exactly like cycling** does now:
- Same toggle mechanism
- Same stacked bar visualization
- Same tooltip structure
- Just with orange color instead of blue




















