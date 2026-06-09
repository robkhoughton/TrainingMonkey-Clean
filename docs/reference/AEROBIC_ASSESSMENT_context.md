# Aerobic Assessment — AeT/AnT Testing and Transition Framework

**Source:** [Evoke Endurance — Zone 2: A Comprehensive Look](https://evokeendurance.com/resources/zone-2-a-comprehensive-look/)  
**Author:** Scott Johnston  
**Coaching context:** [[aerobic_assessment]]

---

## Two Critical Thresholds

**Aerobic Threshold (AeT):** Upper boundary of Zone 2 / pure aerobic work (≈ blood lactate 2 mMol/L = VT1). Below this, aerobic metabolism is fully adequate.

**Anaerobic Threshold (AnT):** Maximum sustainable effort — the highest intensity maintainable for extended durations (≈ blood lactate 4 mMol/L = VT2 / lactate threshold).

---

## The 10% Transition Rule

When the AeT–AnT gap narrows to **≤10%** (measured by HR), the aerobic base is sufficiently developed to support high-intensity work.

- Gap > 10% → continue Zone 2 base; adding intensity will underperform and add fatigue
- Gap ≤ 10% → aerobic base is ready; reduce Zone 2 duration, introduce structured HIIT

**Aerobic Deficiency Syndrome (ADS):** Gap > 20–25% indicates excessive high-intensity history with underdeveloped aerobic base. Prescription: extended Zone 2 period before any intensity is added.

---

## Testing AeT — HR Drift Test (Primary Method)

One hour at constant effort. If HR drifts > 5% between the first and second 30-minute halves (or pace slows > 5% to hold constant HR), starting intensity exceeded AeT.

**Indoor protocol (treadmill / StairMaster):**
1. Warm up 10+ minutes at nose-breathing pace
2. Stabilize HR for 3–4 minutes, then lock speed
3. Hold constant speed for 60 minutes without adjustment
4. Use Training Peaks (or similar) to compare average HR in minutes 1–30 vs. 31–60
5. < 5% drift = at or below AeT; ≥ 5% = above AeT, reduce intensity for next test

**Outdoor protocol:**
- Use flat loops with minimal elevation change
- Monitor pace drift at constant HR (or HR drift at constant pace)
- < 3–5% drift = within aerobic capacity

**No-tech field check:** Upper limit of sustained nose breathing. Can hold a full conversation. Same ceiling as HR Drift Test, less precise.

---

## Testing AnT — Hill Time Trial

All-out effort on a steep hill, 20–60 minutes depending on fitness. Treat it like a race. Average HR from the effort = AnT heart rate.

**Prerequisite:** Only conduct when well-rested. A fatigued test underestimates AnT and produces an incorrect gap calculation.

---

## Reading the Gap — Worked Example

| Metric | Base-Deficient Athlete | After 6 Months Zone 2 |
|--------|------------------------|------------------------|
| AeT HR | 136 bpm / 11:30/mi | 155 bpm / 9:45/mi |
| AnT HR | 168 bpm / 9:20/mi | 168 bpm (unchanged) |
| HR gap | 23.5% → ADS | 8% → ready for intensity |

AeT improved dramatically; AnT unchanged because no anaerobic stimulus was applied. This is the expected pattern: Zone 2 raises the aerobic floor; intensity work raises the anaerobic ceiling.

---

## Retesting Protocol

- Retest every 4–6 weeks during active base development
- Use identical course and conditions for valid comparisons
- Monitor breathing patterns alongside HR for integrated metabolic feedback
- AeT fluctuates with fatigue — if threshold appears to drop unexpectedly, check recovery status before changing training prescription

---

## Interpreting HR Drift Test Results

**Source:** Evoke Endurance Masterclass — *Interpreting the Heart Rate Drift Test* (Scott Johnston)

### Drift Outcome Table

| Drift % | Verdict | Corrective Action |
|---------|---------|-------------------|
| < 1.5% | Started below AeT — result unusable | Retest 3–5 bpm higher |
| 1.5–5% | **Valid** — at or near AeT | Accept. AeT bpm = starting steady-state HR |
| 5–10% | Started above AeT — result unusable | Retest 3–5 bpm lower |
| > 10% | Significantly above AeT — result unusable | Retest 8–10 bpm lower |

**Target:** ~5% drift is ideal. The starting HR of the steady-state portion becomes the top of Zone 2 (AeT bpm).

### Reading the Result (Engine Output)

The aerobic assessment engine returns `drift_pct`, `aet_bpm`, and an `interpretation` string. When the result is **valid** (1.5–5% drift):

- `aet_bpm` = average HR over the first 5 minutes of steady state = the ceiling of Zone 2
- If `ant_bpm` is also supplied, `gap_pct` = (AnT − AeT) / AnT × 100 → see gap rules below

When the result is **invalid**, the `interpretation` field already contains the corrective instruction (bpm adjustment to try next time). Do not invent alternative interpretations.

### When to Accept vs. Retest

- Drift 1.5–5%: accept and set Zone 2 ceiling. Athlete does not need to retest.
- Drift just above 5% (≤ 7%): consider accepting with a note that actual AeT may be 3–5 bpm lower than the recorded starting HR. Acceptable if athlete does not want to retest.
- Drift > 7%: must retest at lower intensity for a usable AeT number.
- Drift < 1.5%: can either retest or estimate AeT as 3–5 bpm above the recorded starting HR if the athlete is unwilling to retest.

### Test Validity Prerequisites (Outdoor)

- Course must be flat — minimal cumulative elevation gain/loss (< ~70 ft per hour)
- Out-and-back courses are invalid (asymmetric grade changes alter the HR response)
- Conditions should be similar across tests for valid longitudinal comparison

### Zone 2 Ceiling Setting

> **AeT bpm = starting steady-state HR** (first ~5 min after warm-up stabilisation). This is the top of Zone 2, not the average HR for the full test.

### AeT–AnT Gap Rules

| Gap | Status | Prescription |
|-----|--------|--------------|
| ≤ 10% | Ready for intensity | Reduce Zone 2 volume; introduce structured HIIT |
| 11–20% | Moderate gap | Continue base; no intensity block yet |
| > 20% | Aerobic Deficiency Syndrome | Extended Zone 2 period; no intensity exceptions |
