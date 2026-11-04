---
ContentType:
status: AI Raw
Next Steps:
expert_review:
title: Central Governor Fatigue
description:
agent: Gemini
authors:
  - Rob Houghton
notes:
revision_notes:
manual date created:
created_at: 2026-10-29 14:02
updated_at: 2026-10-29 14:02
tags:
  - type/note
links:
---
# Central Governor Fatigue


That inability to push your heart rate above 120 bpm late in a run is a classic hallmark of deep ultra-endurance fatigue. What you are experiencing isn't the absence of cardiac drift—which typically occurs earlier in a run due to thermoregulation—but rather profound central and neuromuscular fatigue overriding the system.

  

When you hit those late stages, your brain's central governor detects mounting muscle damage, glycogen depletion, and systemic stress. To prevent catastrophic failure, it actively downregulates motor unit recruitment. If your nervous system won't let your leg muscles fire with maximal force, the oxygen demand stays artificially low. Your heart rate physically cannot climb, even though your perceived exertion (RPE) feels maximal.

  

To track this specific type of late-stage fatigue resistance during your 50K, monitor the divergence between your internal effort and external output:

  

- **The RPE/HR Disconnect:** Note the exact mileage where your perceived effort spikes but your heart rate hits that rigid ceiling.
    
      
    
- **Pace Degradation:** Watch how your Flat Equivalent Mile (FEM) pace drops at that 120 bpm ceiling compared to your efficiency in the first 20 miles.
    
      
    
- **Recovery Velocity:** Measure how many days it takes for your ability to hit a 140+ bpm heart rate to return during your normal microcycle.

To automatically detect this specific type of central fatigue in Your Training Monkey, you need to pull high-resolution time-series data using the Strava Streams API and feed it through a Pandas script that isolates your runnable trail metrics.

  

Because trail terrain distorts pace, you must apply the grade-filtering logic you previously established to compare apples to apples.

For the Your Training Monkey architecture and the sub-24 Western States goal, this divergence metric is the primary trigger that manages your adaptive envelope. You use it to actively govern your training prescriptions and race-day execution.

  

**Govern the YTM Algorithm**

When divergence spikes—specifically when your external ACWR (Flat Equivalent Miles) drops while your internal load behaves abnormally (high RPE paired with a suppressed 120 bpm heart rate)—it signals deep central fatigue. Your app should use this exact metric to automatically override the schedule. It is the hard stop that swaps a planned Norwegian 4x4 or lactate shuttle for pure active recovery until your nervous system allows your heart rate to reach 140+ bpm again.

  

**Track Physiological Resilience**

The onset of this divergence is your quantifiable durability score. If the central governor locks your heart rate at 120 bpm at mile 25 in October, but you successfully push that onset back to mile 35 by April, your physiological resilience is objectively improving. Tracking where this decoupling happens during your monthly 50K proves whether your heavy strength training and base miles are working.

  

**Pivot Race-Day Execution**

Because you know this suppression will occur, you can anticipate exactly when your Garmin's heart rate data becomes a liability. Once divergence hits late in a 100-miler, you must switch your pacing strategy entirely. You pivot to RPE, fueling cadence, and mechanical cues—focusing strictly on maintaining stride frequency rather than chasing a heart rate zone your body has locked you out of.

Yes. Your long run distance should be dynamically scaled to your divergence point to maximize adaptation while protecting your recovery velocity. Running 15 miles in a state of severe central suppression does not build durability; it just digs a recovery hole that disrupts your upcoming lactate shuttles and base miles.

  

**Map the Baseline**

Use your next long run to pinpoint exactly when your FEM (Flat Equivalent Mile) pace drops, your journal RPE spikes, and your heart rate locks at that 120 bpm ceiling. This mileage marks your current resilience threshold.

  

**The Overload Margin**

To build durability for a sub-24 Western States finish, program your long runs to extend just 3 to 5 miles past the onset of divergence. This applies enough stimulus to force neuromuscular adaptation without wrecking your 14-day microcycle.

  

**Dynamic Adjustments**

  

- **Late Onset:** If divergence hits at mile 26, complete the 50K. Use those final 5 miles strictly to practice mechanical efficiency, cadence, and fueling under central suppression.
    
      
    
- **Early Onset:** If your heart rate caps at 120 bpm at mile 15, your internal load is flagging residual chronic fatigue. Abort the planned distance to prevent accumulating junk load.
    
      
    

When you enter the divergence phase, abandon the 136-142 bpm FatMax target. The physiological goal shifts entirely to preventing a prolonged ground-contact gait.


Here is how to structure the Python/Pandas logic using the Strava `streams` endpoint (`time`, `distance`, `heart_rate`, `velocity_smooth`, `grade_smooth`, `moving`):

  

### 1. Filter the Trail Noise

First, isolate the data so you are only analyzing runnable terrain. Steep climbs and technical descents will naturally drop your pace and skew the efficiency metrics. Filter the DataFrame to only include active moving time where the grade is between your established -2% to +6% window.

  

### 2. Establish the Baseline Efficiency

Calculate your baseline Flat Equivalent Mile (FEM) pace during the first quarter of the run, ignoring the initial warm-up lag.

Extract the average `velocity_smooth` and `heart_rate` from miles 2 through 10 (or minutes 20 to 90) on those filtered, runnable segments. This is your baseline neuromuscular output before central fatigue sets in.

  

### 3. Apply the Rolling Window

Calculate a rolling average over a sufficient time window to smooth out GPS and HR monitor noise. A 5-minute to 10-minute rolling window (300 to 600 seconds of stream data) works well for tracking macro-trends in pace and heart rate without getting tripped up by momentary pauses or terrain micro-fluctuations.

  

### 4. Code the Divergence Trigger

The script needs to scan the rolling windows in the back half of the run (e.g., past mile 15) for the exact signature of central suppression: a drop in external output paired with a locked internal load.

  

Python

```
import pandas as pd
import numpy as np

# Assuming df contains your Strava stream arrays
# distance (meters), velocity (m/s), grade (%), hr (bpm), moving (bool)

# 1. Filter out steep trail noise and stopped time
df_runnable = df[(df['grade'] >= -2.0) & (df['grade'] <= 6.0) & (df['moving'] == True)].copy()

# Convert units for human readability
df_runnable['pace_min_mile'] = 26.8224 / df_runnable['velocity']
df_runnable['distance_miles'] = df_runnable['distance'] * 0.000621371

# 2. Establish the Baseline (e.g., Miles 2 to 10)
baseline = df_runnable[(df_runnable['distance_miles'] > 2) & (df_runnable['distance_miles'] < 10)]
baseline_pace = baseline['pace_min_mile'].mean()

# 3. Calculate Rolling Averages (e.g., ~10-minute moving window assuming 1Hz data)
window_size = 600 
df_runnable['rolling_pace'] = df_runnable['pace_min_mile'].rolling(window=window_size, min_periods=window_size//2).mean()
df_runnable['rolling_hr'] = df_runnable['hr'].rolling(window=window_size, min_periods=window_size//2).mean()

# 4. Define the Divergence Thresholds
# Trigger: Pace drops by more than 15% AND HR is centrally suppressed below 125 bpm
pace_drop_threshold = baseline_pace * 1.15 
hr_ceiling = 125 

# Find where both conditions are met deep into the run
divergence_data = df_runnable[
    (df_runnable['rolling_pace'] > pace_drop_threshold) & 
    (df_runnable['rolling_hr'] < hr_ceiling) & 
    (df_runnable['distance_miles'] > 15) 
]

# 5. Extract the Onset Point
if not divergence_data.empty:
    divergence_onset_mile = divergence_data.iloc[0]['distance_miles']
    print(f"Central divergence onset detected at mile: {divergence_onset_mile:.1f}")
else:
    print("No central divergence detected. Adaptive envelope intact.")
```

### 5. Correlate with RPE

To confirm this isn't simply a case of you intentionally jogging the cool-down, pull the `perceived_exertion` integer from the activity summary endpoint (`strava_mcp:get_activity_performance`).

If `divergence_onset_mile` is triggered AND your logged RPE is high (e.g., 7 or above on a 1-10 scale), Your Training Monkey can automatically flag this as an early-onset central fatigue event and trigger the logic to rewrite your upcoming microcycle for recovery.