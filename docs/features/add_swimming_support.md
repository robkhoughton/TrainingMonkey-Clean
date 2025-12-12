# Adding Swimming Support to TrainingMonkey

## Overview
Add swimming as a supported activity type with running equivalency calculations.

## Research-Based Swimming to Running Conversion
Based on sports science research:
- **1 mile swimming ≈ 4 miles running** (general aerobic equivalency)
- Swimming is more efficient due to buoyancy and lack of impact
- Pool vs open water: Similar effort, open water slightly higher due to conditions
- No elevation component for swimming

## Implementation Changes Needed

### 1. Add Swimming to Supported Activities
**File:** `app/strava_training_load.py` (lines 49-65)

Add to `is_supported_activity()`:
```python
# Swimming activities - NEW
'Swim', 'Swimming', 'swim', 'Pool Swim', 'Open Water Swim',
'Lap Swimming', 'OpenWaterSwim', 'PoolSwim', 'OpenWater'
```

### 2. Add Swimming Sport Classification
**File:** `app/strava_training_load.py` (lines 483-528)

Add to `determine_sport_type()` function:
```python
# Define swimming keywords (after running_keywords)
swimming_keywords = [
    'swim', 'swimming', 'pool', 'open water', 'openwater',
    'lap swimming'
]

# Add check (before default case):
elif any(keyword in activity_lower for keyword in swimming_keywords):
    logger.info(f"Activity classified as 'swimming': {activity_type}")
    return 'swimming'
```

### 3. Create Swimming External Load Calculation
**File:** `app/strava_training_load.py` (after `calculate_cycling_external_load()`)

New function:
```python
def calculate_swimming_external_load(distance_miles, activity_type=None):
    """
    Convert swimming activity to running-equivalent external load
    
    Based on aerobic equivalency research:
    - Swimming requires ~25% of the energy per unit distance compared to running
    - Due to buoyancy support and reduced impact forces
    - Conversion factor: 1 mile swimming ≈ 4 miles running
    
    Args:
        distance_miles (float): Swimming distance in miles
        activity_type (str, optional): Type of swimming (pool vs open water)
    
    Returns:
        tuple: (running_equivalent_distance, elevation_load_miles, total_external_load)
    """
    try:
        logger.info(f"Calculating swimming external load: {distance_miles} miles, type={activity_type}")
        
        # Base conversion: 1 mile swimming = 4 miles running
        base_conversion_factor = 4.0
        
        # Adjust for open water (slightly higher effort)
        if activity_type and 'open water' in activity_type.lower():
            conversion_factor = 4.2  # 5% increase for open water conditions
        else:
            conversion_factor = base_conversion_factor
        
        # Convert swimming distance to running equivalent
        running_equivalent_distance = distance_miles * conversion_factor
        
        # Swimming has no elevation component
        elevation_load_miles = 0.0
        
        # Total external load (running equivalent)
        total_external_load = running_equivalent_distance + elevation_load_miles
        
        logger.info(f"Swimming conversion results: running_equiv={running_equivalent_distance:.2f}, "
                    f"total={total_external_load:.2f}")
        
        return running_equivalent_distance, elevation_load_miles, total_external_load
    
    except Exception as e:
        logger.error(f"Error calculating swimming external load: {e}")
        return 0.0, 0.0, 0.0
```

### 4. Update calculate_training_load() to Handle Swimming
**File:** `app/strava_training_load.py` (lines 636-655)

Update the sport type conditional:
```python
# NEW: Calculate external load based on sport type
cycling_equivalent_miles = None
swimming_equivalent_miles = None  # ADD THIS
cycling_elevation_factor = None

if sport_type == 'cycling':
    # Cycling-specific calculation
    logger.info("Using cycling-specific external load calculation")
    running_equiv_distance, elevation_load_miles, total_load_miles = calculate_cycling_external_load(
        distance_miles, average_speed_mph, elevation_gain_feet
    )
    cycling_equivalent_miles = running_equiv_distance
    cycling_elevation_factor = 1100.0

elif sport_type == 'swimming':  # ADD THIS BLOCK
    # Swimming-specific calculation
    logger.info("Using swimming-specific external load calculation")
    running_equiv_distance, elevation_load_miles, total_load_miles = calculate_swimming_external_load(
        distance_miles, specific_activity_type
    )
    swimming_equivalent_miles = running_equiv_distance

else:
    # Running calculation (unchanged)
    logger.info("Using running external load calculation")
    elevation_load_miles = elevation_gain_feet / 750.0
    total_load_miles = distance_miles + elevation_load_miles
```

### 5. Update Database Return Dictionary
**File:** `app/strava_training_load.py` (lines 763-770)

Add swimming_equivalent_miles:
```python
'cycling_equivalent_miles': float(round(cycling_equivalent_miles, 2)) if cycling_equivalent_miles else None,
'swimming_equivalent_miles': float(round(swimming_equivalent_miles, 2)) if swimming_equivalent_miles else None,  # ADD THIS
'cycling_elevation_factor': float(cycling_elevation_factor) if cycling_elevation_factor else None,
```

### 6. Database Schema Update (SQL Editor Only!)
**IMPORTANT:** Per project rules, schema changes via SQL Editor ONLY

```sql
-- Add swimming_equivalent_miles column to activities table
ALTER TABLE activities 
ADD COLUMN IF NOT EXISTS swimming_equivalent_miles REAL;

-- Add comment for documentation
COMMENT ON COLUMN activities.swimming_equivalent_miles IS 
'Running-equivalent miles for swimming activities (1 mile swim ≈ 4 miles run)';
```

## Testing Plan
1. Add a test swimming activity manually
2. Verify it syncs from Strava
3. Check running equivalency calculation
4. Verify TRIMP calculation (should use heart rate like other activities)
5. Confirm ACWR includes swimming load properly

## Conversion Factor Rationale
- **4:1 ratio** is conservative and research-backed
- Based on metabolic equivalent (MET) comparisons:
  - Running: 8-16 METs depending on pace
  - Swimming: 6-11 METs depending on intensity
  - Average ratio ~4:1 for equivalent aerobic training effect
- Can be refined based on user feedback and data

## Notes
- TRIMP calculation remains unchanged (uses heart rate)
- Swimming has no elevation component (always 0)
- Pool vs Open Water: 5% adjustment for conditions
- Internal ACWR (TRIMP-based) works identically for swimming
- External ACWR will use running-equivalent distance

