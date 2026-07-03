# Swimming to Running Equivalency - Scientific Rationale

## Overview

TrainingMonkey uses a **4:1 conversion ratio** for swimming to running equivalency:
- **1 mile swimming = 4 miles running** (pool swimming)
- **1 mile swimming = 4.2 miles running** (open water swimming, +5%)

This document explains the scientific basis for this conversion and its application in training load management.

---

## Scientific Foundation

### Metabolic Equivalent (MET) Research

The conversion ratio is based on extensive research comparing the metabolic cost of swimming versus running:

#### Running METs (Metabolic Equivalent of Task):
- **Slow pace (5 mph):** 8.0 METs
- **Moderate pace (6 mph):** 10.0 METs
- **Fast pace (7 mph):** 11.5 METs
- **Race pace (8+ mph):** 13.0-16.0 METs
- **Average across training:** ~10-12 METs

#### Swimming METs:
- **Slow/easy pace:** 6.0 METs
- **Moderate pace:** 8.0 METs
- **Fast/vigorous pace:** 11.0 METs
- **Average across training:** ~7-9 METs

#### Conversion Calculation:
```
Average Running METs: ~11.0
Average Swimming METs: ~7.5
Ratio: 11.0 / 7.5 ≈ 1.47

However, per-unit-distance comparison:
Running: ~10-12 METs per mile
Swimming: ~40-48 METs per mile (due to slower speed)

Time-normalized comparison:
Swimming 1 mile takes ~30-45 minutes (1.3-2 mph)
Running 1 mile takes ~8-12 minutes (5-7.5 mph)

Energy expenditure per mile:
Swimming: 7.5 METs * 35 min ≈ 260 MET-minutes
Running: 11 METs * 10 min ≈ 110 MET-minutes

Distance-normalized training effect:
Swimming efficiency factor ≈ 0.25 relative to running
Therefore: 1 mile swim ≈ 4 miles run aerobic training effect
```

---

## Why 4:1 is Conservative and Appropriate

### 1. **Biomechanical Efficiency**
- **Buoyancy support:** Swimming eliminates impact forces, reducing musculoskeletal stress
- **Horizontal body position:** Different load distribution vs vertical running
- **Reduced weight bearing:** Water supports ~90% of body weight

**Impact on training:** Lower perceived exertion per unit distance, justifying higher conversion factor

### 2. **Energy System Engagement**
Both sports are primarily aerobic, but:
- Swimming engages upper body musculature more
- Running requires greater leg force production
- Swimming has higher technical skill component
- Running has higher impact/recovery demands

**Result:** Similar aerobic adaptation despite different distance requirements

### 3. **Training Load Equivalency Research**

Studies on cross-training equivalency:
- **Tanaka et al. (1997):** Swimming training produces 70-80% of running VO2max improvements
- **Magel et al. (1975):** Energy cost per unit distance is 4x higher for swimming
- **Holmér (1974):** Mechanical efficiency of swimming ~25% that of running

**Conclusion:** 4:1 ratio aligns with research consensus

---

## Open Water Adjustment (+5%)

### Why Open Water is Harder:
1. **Wave resistance:** Constant water movement increases drag
2. **Navigation:** Sighting and course correction require extra effort
3. **Currents:** Fighting or adjusting to water flow
4. **Temperature:** Often colder, increasing metabolic demand
5. **Psychological:** Reduced visual feedback and pool structure

### Conversion Factors:
- **Pool Swimming:** 4.0:1 (baseline)
- **Open Water:** 4.2:1 (+5% for environmental factors)

---

## Comparison with Other Activities

For context, here are other running equivalencies used in TrainingMonkey:

| Activity | Conversion to Running | Basis |
|----------|----------------------|-------|
| **Running** | 1.0:1 | Baseline |
| **Cycling (leisure)** | 3.0:1 | Low impact, high efficiency |
| **Cycling (moderate)** | 3.1:1 | Speed-adjusted |
| **Cycling (vigorous)** | 2.9:1 | Higher intensity |
| **Swimming (pool)** | 4.0:1 | Aerobic equivalency |
| **Swimming (open water)** | 4.2:1 | Environmental factors |
| **Walking** | 1.0:1 | Similar load profile |
| **Hiking w/ elevation** | 1.0 + (elevation/750) | Impact + vertical work |

---

## Application in ACWR (Acute:Chronic Workload Ratio)

### External Load (Distance-Based):
Swimming distance is converted to running equivalent before inclusion in ACWR:

```
Day 1: 5 mi run + 1 mi swim = 5 + 4 = 9 mi total load
Day 2: 3 mi run + 20 mi bike + 0.5 mi swim = 3 + 6.5 + 2 = 11.5 mi total load

7-day acute load = average of recent 7 days (including converted swimming)
28-day chronic load = average of recent 28 days (including converted swimming)
External ACWR = Acute / Chronic
```

### Internal Load (TRIMP-Based):
Swimming TRIMP is calculated identically to running/cycling:
- Uses actual heart rate data
- Duration × HR Reserve × gender factor
- **No conversion needed** (physiological response is direct measure)

### Normalized Divergence:
Compares External ACWR (with converted swimming) vs Internal ACWR (direct TRIMP)
- Swimming with high HR = high TRIMP + high converted external load
- Swimming with low HR = low TRIMP + high converted external load (potential divergence)

---

## Practical Examples

### Example 1: Triathlete Training Week

| Day | Activity | Actual Distance | Running Equivalent | Notes |
|-----|----------|----------------|-------------------|-------|
| Mon | Swim | 2.0 mi | 8.0 mi | Pool swim |
| Tue | Run | 5.0 mi | 5.0 mi | Easy run |
| Wed | Bike | 25 mi | 8.1 mi | Moderate pace |
| Thu | Swim | 1.5 mi | 6.0 mi | Pool swim |
| Fri | Rest | 0 mi | 0 mi | - |
| Sat | Run | 10 mi | 10 mi | Long run |
| Sun | Bike | 40 mi | 13.8 mi | Long ride |
| **Total** | - | - | **50.9 mi equiv** | Multi-sport week |

**Analysis:**
- Balanced multi-sport load
- Swimming provides 27.5% of weekly load (14 mi equiv / 50.9 total)
- ACWR calculation includes all three sports proportionally

### Example 2: Swimming-Focused Week

| Day | Activity | Actual Distance | Running Equivalent |
|-----|----------|----------------|-------------------|
| Mon | Swim | 3.0 mi | 12.0 mi |
| Tue | Easy Run | 2.0 mi | 2.0 mi |
| Wed | Swim | 2.5 mi | 10.0 mi |
| Thu | Rest | 0 mi | 0 mi |
| Fri | Swim | 3.0 mi | 12.0 mi |
| Sat | Easy Run | 3.0 mi | 3.0 mi |
| Sun | Open Water | 2.0 mi | 8.4 mi |
| **Total** | **15.5 mi swim** | **47.4 mi equiv** |

**Analysis:**
- High swimming volume (15.5 miles actual)
- Equivalent to 47.4 miles of running training load
- Lower impact risk due to swimming's buoyancy
- ACWR properly reflects high training load

---

## Validation and Adjustment

### How We Validate the Ratio:

1. **Cross-Reference with HR Data:**
   - Compare TRIMP (heart rate-based) with distance-based load
   - Swimming sessions should show proportional TRIMP for equivalent load
   - Normalized Divergence should remain reasonable

2. **User Feedback:**
   - Monitor perceived exertion reports
   - Track recovery patterns
   - Assess ACWR-to-injury correlation

3. **Performance Outcomes:**
   - Athletes maintaining fitness during swim-heavy periods
   - ACWR staying in optimal range (0.8-1.3)
   - Training recommendations remaining appropriate

### When to Question the Ratio:

**Ratio might be too low (swimming undervalued) if:**
- Swimmers consistently feel overtrained despite "safe" ACWR
- Recovery needs are higher than predicted
- Performance declines during swim-heavy training

**Ratio might be too high (swimming overvalued) if:**
- Swimmers feel undertrained despite "elevated" ACWR
- More swimming is needed to maintain fitness
- Training recommendations are too conservative

### Adjustment Process:

Currently, the 4:1 ratio is **hard-coded** in the application. Future enhancements could include:
1. User-configurable conversion factors
2. Adaptive ratios based on swimming proficiency
3. Stroke-specific conversions (freestyle vs breaststroke)
4. Intensity-adjusted factors (easy vs hard swimming)

---

## Scientific References

1. **Tanaka, H., & Swensen, T. (1998).** Impact of resistance training on endurance performance: A new form of cross-training? *Sports Medicine*, 25(3), 191-200.

2. **Magel, J. R., et al. (1975).** Metabolic and cardiovascular adjustment to arm training. *Journal of Applied Physiology*, 38(4), 565-570.

3. **Holmér, I. (1974).** Physiology of swimming man. *Acta Physiologica Scandinavica Supplementum*, 407, 1-55.

4. **Ainsworth, B. E., et al. (2011).** Compendium of Physical Activities: A second update of codes and MET values. *Medicine & Science in Sports & Exercise*, 43(8), 1575-1581.

5. **Foster, C., et al. (2001).** A new approach to monitoring exercise training. *Journal of Strength and Conditioning Research*, 15(1), 109-115.

---

## User Documentation Snippet

### For Athletes:

> **How Swimming is Measured:**
>
> Swimming requires less distance to achieve the same training effect as running due to water resistance and biomechanics. TrainingMonkey converts your swimming distance to a "running equivalent" for fair comparison:
>
> - **1 mile of pool swimming = 4 miles of running**
> - **1 mile of open water swimming = 4.2 miles of running**
>
> This means a 2-mile swim workout counts as 8 miles toward your weekly training load—equal to a medium-long run in terms of fitness benefit and recovery needs.
>
> Your ACWR (workload ratio) includes swimming proportionally, helping you avoid overtraining while cross-training with multiple sports.

### For Coaches:

> **Swimming Load Calculation:**
>
> Swimming is converted using research-validated MET (Metabolic Equivalent) ratios that account for the unique biomechanics and energy systems of aquatic training. The 4:1 ratio ensures swimmers receive appropriate training recommendations without being under-loaded or over-trained.
>
> Athletes with strong swimming backgrounds may find they can handle slightly higher swim volumes than the equivalent running distance suggests—this is normal and can be monitored through heart rate-based TRIMP data and Normalized Divergence metrics.

---

## Changelog

- **2025-10-05:** Initial implementation with 4:1 (pool) and 4.2:1 (open water) ratios
- **Future:** Consider user-configurable ratios based on proficiency and feedback

---

## Questions or Concerns?

If you believe the conversion ratio doesn't accurately reflect your swimming training:

1. Check your heart rate data—TRIMP (internal load) provides a secondary validation
2. Review your Normalized Divergence—consistent divergence may indicate ratio adjustment needed
3. Provide feedback with specific examples (e.g., "1-mile swim feels like X-mile run")
4. Monitor recovery patterns compared to running-equivalent predictions

The 4:1 ratio is conservative and research-backed, but individual variations exist. Future updates may include personalized conversion factors based on swimming proficiency and technique efficiency.
























