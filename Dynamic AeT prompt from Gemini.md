---
ContentType:
status: AI Raw
Next Steps:
expert_review:
title: Dynamic AeT
description:
agent: Gemini
authors:
  - Rob Houghton
notes:
revision_notes:
manual date created:
created_at: 2026-06-27 08:14
updated_at: 2026-06-27 08:14
tags:
  - type/note
links:
---
# Dynamic AeT
You are an expert sports data scientist and Python backend engineer. I am building a highly customized AI endurance coaching application called Your Training Monkey (YTM). 

I need you to write a Python script that calculates my daily Aerobic Threshold (AeT), audits my intra-run Heart Rate Recovery (HRR) from a .fit/.tcx file, and uses that dynamically shifted AeT to calculate an accurate daily TRIMP for my macro Acute:Chronic Workload Ratio (ACWR).

Do not use pace, NGP, or power algorithms. The system relies entirely on autonomic metrics and raw terrain physics.

Here is the functional specification for the script:

**1. GLOBAL VARIABLES & INPUTS**
* `BASE_AET`: 135 (My well-rested, lab-tested baseline AeT in bpm).
* `HRV_30_DAY_ARRAY`: A list of my waking rMSSD values from the last 30 days.
* `EXTERNAL_WORKLOAD`: A single float representing today's physical load (calculated elsewhere as horizontal miles + vertical gain).
* `FIT_FILE_PATH`: Path to today's parsed time-series activity data.

**2. MODULE 1: The Waking HRV Offset (Morning Prediction)**
Write a function `calculate_morning_aet_target()`:
* Apply a natural log transformation to all values in the 30-day array and today's rMSSD reading to correct right-skewness.
* Calculate the 30-day rolling mean and standard deviation of the log-transformed HRV.
* Calculate the Z-score for today's log-transformed HRV.
* Return `TODAYS_AET_TARGET` based on this logic:
    * Z-score >= +0.75: Return BASE_AET + 2 
    * -0.75 <= Z-score < +0.75: Return BASE_AET
    * -1.5 <= Z-score < -0.75: Return BASE_AET - 5 
    * Z-score < -1.5: Return BASE_AET - 8 

**3. MODULE 2: The HRR Decay Auditor (Post-Run Validation)**
Write a function `audit_hrr_decay()` that ingests the 1Hz time-series heart rate data from the .fit file:
* Scan the array to identify "Recovery Events" (HR dropping from >= `TODAYS_AET_TARGET` - 10 bpm down to a resting state, usually over crests of hills).
* For each event, calculate the exact number of seconds it takes for the HR to drop by exactly 20 bpm from the local peak.
* Compare the average 20-bpm decay time of the first half of the run against the second half.
* Return `HRR_DRIFT_PCT`: ((Second Half Time - First Half Time) / First Half Time) * 100.

**4. MODULE 3: The Dynamic TRIMP & ACWR Engine**
Write a function `calculate_dynamic_strain()`:
* Calculate today's Internal Load (TRIMP). CRITICAL: You must substitute standard static threshold HR anchors with `TODAYS_AET_TARGET`. If my AeT dropped to 127 today due to fatigue, a 130 bpm effort must be scored exponentially higher as a Zone 3 glycolytic effort.
* Assuming we have access to rolling 28-day databases for both TRIMP and External Workload, calculate the current `ACWR_TRIMP` and `ACWR_EXTERNAL` (7-day acute / 28-day chronic).
* Calculate the Strain-to-Work Index: `SWI = ACWR_TRIMP / ACWR_EXTERNAL`.

**5. MODULE 4: The Veto Engine (Final Diagnostic Output)**
Write a final function that evaluates the macro SWI against the micro HRR Drift. 
Return a JSON diagnostic object containing:
* `todays_aet_target`
* `hrr_drift_pct`
* `swi_ratio`
* `system_status`: Apply the following strict "Micro Vetoes Macro" logic:
    * If SWI < 1.0 AND HRR_DRIFT_PCT < 10%: Return "Green: Peak Adaptation. Engine has unused capacity."
    * If SWI > 1.15 AND HRR_DRIFT_PCT > 15%: Return "Red: Acute Fatigue. Macro strain and autonomic decay align."
    * If SWI < 1.0 BUT HRR_DRIFT_PCT > 15%: Return "Red Alert: Autonomic Exhaustion. Macro ratios show false headroom; nervous system is rejecting the load. Rest immediately."
    * If SWI > 1.15 BUT HRR_DRIFT_PCT < 5%: Return "Yellow: Structural Overreach. Biology is absorbing the load well, but mechanical volume is risky."

Please write modular, well-commented Python code utilizing `numpy` and `fitparse` (or standard array manipulation). Ensure the array-slicing logic for finding the 20-bpm HRR drop in Module 2 is robust against noisy sensor data.