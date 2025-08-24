# Training Metrics Reference Guide

## Decision Framework for Daily Training

### Primary Assessment Order:
1. **Safety Check**: Days since rest > 7 → Mandatory rest or pain score 3 or greater on consecutive days
2. **Overtraining Check**: Normalized Divergence < -0.15 → Rest or very light workout
3. **ACWR Check**: Both External & Internal > 1.3 → Reduce intensity/volume
4. **Recovery Check**: Divergence < -0.05 + Days since rest > 5 → Active recovery
5. **Progression Check**: Both ACWR < 0.8 → Gradual load increase opportunity

### Weekly Planning Priorities:
1. Ensure 1-2 rest days per week
2. Limit high-intensity sessions (TRIMP > 70) to 2-3 per week
3. Maintain 80/20 intensity distribution (80% easy, 20% moderate-hard)
4. Plan step-back weeks when ACWR trends > 1.2 for 7+ days

## Advanced Pattern Recognition

### Red Flag Patterns:
- **Chronic Elevation**: ACWR > 1.3 for 5+ consecutive days
- **Divergence Drift**: Normalized divergence trending negative (each day worse than previous) for 5+ days
- **HR Drift**: Increasing resting HR or decreased HRV trends
- **Volume Sensitivity**: >15% weekly load increases causing immediate ACWR spike
- **Intensity Clustering**: >2 consecutive days TRIMP >70 without intermediate recovery
- **Recovery Failure**: TRIMP >70 sessions followed by divergence remaining <-0.05 for 48+ hours
- **Load Spike Sensitivity**: Single high-volume day (>150% of 7-day average) causing ACWR jump >0.15

### Positive Adaptation Patterns:
- **Efficient Loading**: Consistent positive divergence (0.05-0.15) with stable ACWR
- **Progressive Overload**: Gradual ACWR increase (0.05-0.1 per week) in optimal zone
- **Recovery Response**: Quick return to baseline metrics after hard sessions

### Seasonal Considerations:
- **Base Building**: Target ACWR 0.9-1.1, emphasize aerobic development
- **Build Phase**: Allow ACWR 1.1-1.3, include intensity progression
- **Peak Phase**: Brief periods >1.3 acceptable with planned recovery
- **Recovery Phase**: Target ACWR 0.7-0.9, focus on adaptation

## Data Quality Indicators

### High Confidence Metrics:
- Distance, elevation (GPS-based)
- Duration (device-measured)
- Heart rate

### Moderate Confidence:
- TRIMP calculations (dependent on accurate max/resting HR)
- Niggles (pain)

### Lower Confidence:
- Perceived effort (subjective but valuable)

### Missing Data Handling:
- Use alternative metrics when primary data unavailable
- Increase conservatism in recommendations when confidence is low
- Suggest manual verification for unusual readings

## Primary Metrics

### Acute:Chronic Workload Ratio (ACWR)

ACWR quantifies the relationship between recent training (acute load) and longer-term training history (chronic load). It is calculated as:

```
ACWR = 7-day rolling daily average / 28-day rolling daily average
```

#### Interpretation Guidelines:

| ACWR Range | Classification | Interpretation |
|------------|----------------|----------------|
| < 0.8  | Undertraining  | Insufficient acute load relative to chronic capacity. Risk of losing conditioning or training adaptations. May indicate tapering or recovery period. |
| 0.8 - 1.3 | Optimal Zone  | Balanced training that promotes fitness gains with low injury risk. Ideal for sustained training progression. |
| 1.3 - 1.5 | High Risk | Elevated injury risk (~40% higher than optimal zone). Should be used sparingly and intentionally for specific training blocks. |
| > 1.5 | Very High Risk | Significantly increased injury risk (~70%+ higher than optimal zone). Generally should be avoided except during carefully monitored peak training. |

### Normalized Load Divergence

This proprietary metric quantifies the relationship between external loading (distance, elevation) and internal physiological response (TRIMP, heart rate). It's calculated as:

```
Normalized Divergence = (External ACWR - Internal ACWR) / ((External ACWR + Internal ACWR) / 2)
```

#### Interpretation Guidelines:

| Divergence Range | Classification | Interpretation |
|------------------|----------------|----------------|
| < -0.15 | High Overtraining Risk | Internal stress is significantly higher than external work. Indicates poor efficiency, accumulated fatigue, or overtraining. |
| -0.15 to -0.05 | Moderate Risk  | Internal response is disproportionately high. May indicate early fatigue or insufficient recovery. |
| -0.05 to +0.05 | Balanced | Balanced relationship between work completed and physiological response. Ideal for most training. |
| +0.05 to +0.15 | Efficient | External work exceeds relative internal cost. Indicates good adaptation, efficiency, or potential for increased loading. |
| > +0.15 | Potential Undertraining | External work significantly exceeds internal stress. May indicate potential for increased intensity or training stimulus. |

## Secondary Metrics

### Training Impulse (TRIMP)

TRIMP quantifies training load by incorporating both exercise duration and intensity (via heart rate). Our system uses the Banister formula:

```
TRIMP = duration (minutes) × HRR × 0.64e^(k × HRR)
```

Where:
- HRR (Heart Rate Reserve) = (avg_hr - resting_hr) / (max_hr - resting_hr)
- k = 1.92 for males and 1.67 for females

#### Interpretation Guidelines:

| TRIMP Range | Classification | Description |
|-------------|----------------|-------------|
| < 30        | Low Intensity  | Recovery or very easy training sessions |
| 30-70       | Moderate Intensity | Standard aerobic development sessions |
| 70-120      | High Intensity | Hard workouts, typically threshold or interval sessions |
| > 120       | Very High Intensity | Very demanding sessions (long runs, intense intervals) |

### Elevation Load Miles

This metric converts elevation gain into an equivalent distance load to account for the increased energy cost of uphill running/training:

```
Elevation Load Miles = Elevation Gain (feet) / 1000
```

This conversion factor (1000 ft = 1 mile equivalent) is based on research showing that approximately 100 feet of climbing requires similar energy expenditure to running 0.1 miles on flat ground.

### Total Load Miles

The combination of horizontal distance and elevation-based load:

```
Total Load Miles = Distance Miles + Elevation Load Miles
```

This provides a more complete picture of the total external work performed during a training session.

## Wellness Metrics

### Perceived Effort Scale (1-5) - Garmin Compatible
| Score | Description | HR Zone Correlation | RPE Equivalent |
|-------|-------------|-------------------|----------------|
| 1     | Very Easy   | Zone 1-2          | 6-9 RPE        |
| 2     | Easy        | Zone 2            | 10-12 RPE      |
| 3     | Moderate    | Zone 3            | 13-15 RPE      |
| 4     | Hard        | Zone 4            | 16-18 RPE      |
| 5     | Maximum     | Zone 5            | 19-20 RPE      |

### Niggle Score (1-5)

| Score | Description | Interpretation |
|-------|-------------|----------------|
| 1   | Excellent | Pain free |
| 2   | Good | Low level pain (discomfort) during short portion of activity |
| 3   | Okay | Some pain sporadically through activity |
| 4   | Marginal | Persistent pain |
| 5   | Poor | Pain on my mind 100% of the time |


## Optimal Ranges for Health and Performance

| Metric                 | Suboptimal     | Optimal        | Caution Range  | Warning |
|------------------------|------------|--------------------|----------------|---------|
| ACWR (External) | 0.6-0.8 | 0.8-1.3        | 1.3-1.5        | >1.5    |
| ACWR (Internal) | 0.6-0.8 | 0.8-1.3        | 1.3-1.5        | >1.5    |
| Normalized Divergence | +0.05 to +0.15 | -0.05 to +0.05 | -0.15 to -0.05 | <-0.15 |
| Days Since Rest |   | 4-5 | 6-7 | >7 |

## Pattern Recognition

### Heart Rate (HR) Zones (User-Personalized)

**Data Sources:** User Settings (resting_hr, max_hr, hr_zones_method, custom_hr_zones)

**Zone Calculation Logic:**
```
IF user has custom zones (custom_hr_zones not null):
    Use custom zone boundaries from user_settings table
ELSE IF hr_zones_method = 'reserve' (Karvonen method):
    HR Reserve = max_hr - resting_hr
    Zone 1: resting_hr + (HR_reserve × 0.50) to resting_hr + (HR_reserve × 0.60)
    Zone 2: resting_hr + (HR_reserve × 0.60) to resting_hr + (HR_reserve × 0.70)
    Zone 3: resting_hr + (HR_reserve × 0.70) to resting_hr + (HR_reserve × 0.80)
    Zone 4: resting_hr + (HR_reserve × 0.80) to resting_hr + (HR_reserve × 0.90)
    Zone 5: resting_hr + (HR_reserve × 0.90) to max_hr
ELSE (percentage method):
    Zone 1: max_hr × 0.50 to max_hr × 0.60
    Zone 2: max_hr × 0.60 to max_hr × 0.70
    Zone 3: max_hr × 0.70 to max_hr × 0.80
    Zone 4: max_hr × 0.80 to max_hr × 0.90
    Zone 5: max_hr × 0.90 to max_hr
```

**Fallback for Missing User Settings:**
```
IF user settings unavailable:
    Use age-based estimation: max_hr = 220 - age (if age available)
    Default resting_hr = 65 bpm
    Apply percentage method with estimated values
    Note: Reduced confidence in TRIMP calculations
```

**Zone Characteristics (Same for all users):**
- **Zone 1 (Recovery):** Very easy intensity, aerobic base building
- **Zone 2 (Aerobic Base):** Comfortable aerobic pace, primary training zone
- **Zone 3 (Aerobic):** Moderate intensity, tempo efforts
- **Zone 4 (Lactate Threshold):** Hard intensity, threshold training
- **Zone 5 (VO2 Max):** Maximum intensity, high-intensity intervals

**AI Implementation Notes:**
- Always query user_settings table for personalized zones before analysis
- Use personalized zones for TRIMP calculations and intensity classification
- Reference user-specific zones when providing workout intensity guidance
- State confidence level when using fallback estimates

### Diversity in intensity with workload optimally distributed across HR zones as follows:

| HR Zone | % Time in Zone |
|---------|----------------|
| 1   | 5 |
| 2   | 70 |
| 3   | 5 |
| 4   | 10 |
| 5   | 5 |

## Quick Assessment Protocol

**IF** Days since rest >7 **THEN** Mandatory rest day
**ELSE IF** Normalized Divergence <-0.15 **THEN** Rest or recovery walk only
**ELSE IF** External ACWR >1.3 AND Internal ACWR >1.3 **THEN** Reduce volume 25-40%
**ELSE IF** Divergence <-0.05 AND Days since rest >5 **THEN** Active recovery (Zone 1 only)
**ELSE IF** Both ACWR <0.8 **THEN** Progressive load increase opportunity (10-15%)
**ELSE** Normal training progression

### ACWR Management Through Daily Averages

**To Increase ACWR (when <0.8):**
- Add 2-3 miles to planned sessions for 3-4 consecutive days
- Effect: Gradually raises 7-day average relative to stable 28-day average

**To Decrease ACWR (when >1.3):**
- Take rest day (0 miles) - immediately begins lowering 7-day average
- Follow with 2-3 easy days (3-5 miles) below current 7-day average
- Effect: 7-day average drops toward 28-day baseline over 4-5 days

**To Maintain ACWR (0.8-1.3):**
- Daily volume should approximate current 7-day average
- Slight variations (±1-2 miles) maintain stable ratios

**Sample Daily Calculations:**
If 28-day average = 6.0 miles/day:
- ACWR 0.8 = 7-day average of 4.8 miles/day
- ACWR 1.0 = 7-day average of 6.0 miles/day  
- ACWR 1.3 = 7-day average of 7.8 miles/day

Today's session impact: Adding 8 miles today when current 7-day average is 6.0 miles/day will raise tomorrow's 7-day average to approximately 6.3 miles/day.

## Masters Trail Runner Specifications (50+ years)

### Typical Load Ranges:
- **Daily Volume**: 5-12 miles/day sustained average
- **Weekly Elevation**: 3,000-8,000 feet
- **Daily TRIMP Targets**:
  - Easy days: 25-45
  - Moderate days: 50-75
  - Hard days: 80-120
  - Peak sessions: 100-150+

### Recovery Considerations:
- Recovery lag: TRIMP >70 sessions typically require 36-48 hours for full divergence normalization
- Load sensitivity: >15% increases in 7-day average often trigger immediate ACWR elevation
- Rest frequency: Minimum 1 complete rest day per 6-7 training days


## Claude Response Scenarios
### Scenario 1: Undertraining
```
Current Metrics:
External ACWR: 0.71 (7-day avg: 4.6 miles/day, 28-day avg: 6.5 miles/day)
Internal ACWR: 0.68 (7-day avg TRIMP: 41/day, 28-day avg TRIMP: 60/day)
Normalized Divergence: 0.04
Days Since Rest: 1
Recent Pattern: Planned taper completed
```
**Claude Response Framework:** "METRIC ASSESSMENT: ACWR values confirm successful taper execution with 7-day averages appropriately below 28-day baselines. Positive divergence (+0.04) indicates excellent recovery efficiency and readiness for load progression. TODAY: Build session recommended - target 8-10 miles with moderate effort to begin raising 7-day average. Aim for TRIMP 60-70 to restore internal load balance. WEEKLY: Progressive volume increase targeting 7-day average of 5.5-6.0 miles/day by week's end. Add 1-2 miles to each session over next 5 days. MONITOR: Track divergence stability - should remain positive or neutral (+0.02 to -0.02) during load restoration."

### Scenario 2: Overtraining Risk
```
Current Metrics:
External ACWR: 1.41 (7-day avg: 8.3 miles/day, 28-day avg: 5.9 miles/day)
Internal ACWR: 1.52 (7-day avg TRIMP: 66/day, 28-day avg TRIMP: 44/day)
Normalized Divergence: -0.08
Days Since Rest: 6
Recent Pattern: 3 consecutive days >1000ft elevation gain
```
**Claude Response Framework:** "METRIC ASSESSMENT: Critical overtraining signals present. External ACWR (1.41) and Internal ACWR (1.52) both exceed safe thresholds, with internal stress showing disproportionate elevation. Negative divergence (-0.08) indicates physiological stress exceeding mechanical adaptation capacity. TODAY: Mandatory rest day - no running activity to immediately begin reducing 7-day averages. Maximum activity: 30-minute recovery walk. WEEKLY: Implement step-back protocol - target reducing 7-day average below 7.0 miles/day within 4-5 days through continued rest and easy sessions (3-5 miles, Zone 1-2 only). MONITOR: Daily divergence tracking essential - must improve toward -0.05 or better before resuming normal training. Expect 5-7 days for full normalization."

### Scenario 3: Balanced Training
```
Current Metrics:
External ACWR: 1.05 (7-day avg: 7.4 miles/day, 28-day avg: 7.1 miles/day)
Internal ACWR: 1.07 (7-day avg TRIMP: 54/day, 28-day avg TRIMP: 51/day)
Normalized Divergence: -0.02
Days Since Rest: 3
Recent Pattern: Consistent daily volume around 7-8 miles
```
**Claude Response Framework:** "Ideal training zone achieved. 7-day averages slightly above 28-day baselines (7.4 vs 7.1 miles/day) indicating appropriate progressive overload. Near-zero divergence (-0.02) shows balanced physiological adaptation. TODAY: Quality session opportunity - 12-14 miles with race-specific intensity will maintain optimal ACWR range while building fitness. Target TRIMP 85-100. WEEKLY: Continue current loading pattern, can sustain this 7-8 mile daily average. MONITOR: Maintain divergence between -0.05 and +0.05 through next training block."

### Scenario 4:  Returning from Rest
```
Current Metrics:
External ACWR: 0.65 (7-day avg: 1.17 miles/day, 28-day avg: 1.8 miles/day)
Internal ACWR: 0.71 (7-day TRIMP: 45, 28-day TRIMP: 63)
Divergence: -0.09
Days since rest: 2
```
**Claude Response Framework:"METRIC ASSESSMENT:** Severe undertraining phase with both ACWR values well below optimal range. Negative divergence (-0.09) suggests residual physiological stress despite low mechanical load, indicating incomplete recovery from previous issue. TODAY: Conservative return session - target 4-6 miles at easy effort (Zones 1-2) to begin load restoration. Aim for TRIMP 25-35 maximum. WEEKLY: Gradual progression essential - increase 7-day average by 0.5-1.0 miles/day over next week. Focus on aerobic base rebuilding rather than intensity. Target 7-day average of 2.5-3.5 miles/day by week's end. MONITOR: Divergence recovery critical - must trend toward zero (-0.05 or better) within 5-7 days. If divergence worsens, extend easy return period."

### Scenario 5: Efficiency Signal
```
Current Metrics:
External ACWR: 0.95 (7-day avg: 6.65 miles/day, 28-day avg: 7.0 miles/day)
Internal ACWR: 0.82 (7-day avg TRIMP: 42/day, 28-day avg TRIMP: 51/day)
Normalized Divergence: +0.14
Days Since Rest: 4
Recent Pattern: Mostly trail miles, moderate elevation

**Claude Response Framework: "METRIC ASSESSMENT:** Strong positive divergence (+0.14) indicates excellent physiological efficiency - handling current mechanical load with reduced internal stress relative to baseline. External ACWR slightly below optimal suggests volume increase opportunity without overreaching risk. TODAY: Extend session opportunity - target 10-12 miles at comfortable effort to capitalize on efficient state. Can handle moderate intensity (TRIMP 65-80) due to positive adaptation signal. WEEKLY: Volume increase recommended - target raising 7-day average to 7.5-8.0 miles/day over next 5-6 days. Add 1-2 miles to upcoming sessions while maintaining current effort distribution. MONITOR: Divergence stability during load increase - should remain positive (>+0.05) throughout progression. If drops below +0.05, pause volume increases."

###Scenario 6: Divergence Drift Warning 
```
Current Metrics:
External ACWR: 1.18 (7-day avg: 7.7 miles/day, 28-day avg: 6.5 miles/day)
Internal ACWR: 1.34 (7-day avg TRIMP: 61/day, 28-day avg TRIMP: 46/day)
Normalized Divergence: -0.12
Days Since Rest: 5
Recent Pattern: Divergence trending negative for 6 consecutive days

**Claude Response Framework: "METRIC ASSESSMENT:** Concerning divergence drift pattern with 6-day negative trend approaching critical threshold (-0.15). Internal ACWR (1.34) exceeds safe range while external remains acceptable, indicating physiological stress accumulation outpacing mechanical adaptation. TODAY: Active recovery mandatory - limit to 45-60 minutes easy trail hiking or Zone 1 running only. Target TRIMP <30 to arrest internal stress accumulation. WEEKLY: Immediate intervention protocol - reduce intensity for 5-7 days with no sessions above moderate effort (TRIMP <60). Focus on maintaining aerobic volume at reduced intensity until divergence improves. MONITOR: Daily divergence tracking critical - must reverse negative trend within 3-4 days. Target improvement to -0.08 or better before resuming quality sessions. If reaches -0.15, implement full rest protocol."
```
