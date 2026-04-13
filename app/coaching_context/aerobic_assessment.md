# AEROBIC ASSESSMENT — AeT/AnT GAP AND TRANSITION RULES

**Reference doc:** [[AEROBIC_ASSESSMENT_context]]

## Threshold Definitions

- **AeT (Aerobic Threshold):** Zone 2 ceiling = VT1 ≈ 2 mMol/L lactate. Upper limit of pure aerobic work.
- **AnT (Anaerobic Threshold):** Maximum sustainable intensity = VT2 ≈ 4 mMol/L lactate.
- **Gap:** (AnT_HR − AeT_HR) / AnT_HR × 100. Measured in HR %.

## Evaluating HR Drift Test Engine Output

The aerobic assessment engine returns `valid`, `drift_pct`, `aet_bpm`, `interpretation`, and optionally `gap_pct` / `gap_status`.

**If `valid` is false:** Report the `error` field verbatim. Do not attempt interpretation.

**If `valid` is true — read `drift_pct`:**
- < 1.5%: Test started below AeT. Result is unusable. Tell athlete to retest 3–5 bpm higher. Do not set a Zone 2 ceiling from this result.
- 1.5–5.0%: Valid result. `aet_bpm` is the Zone 2 ceiling. Accept it.
- 5.0–7.0%: Started slightly above AeT. Optionally accept with caveat: actual AeT is likely 3–5 bpm below `aet_bpm`. Recommend retest if precision matters.
- 7.0–10.0%: Started above AeT. Result is unusable. Tell athlete to retest 3–5 bpm lower.
- > 10%: Started significantly above AeT. Tell athlete to retest 8–10 bpm lower.

**Setting Zone 2 ceiling:** `aet_bpm` (first-5-min steady-state average) is the top of Zone 2, not the test average HR.

## Gap-Based Prescription Rules

- `gap_status` = "ready for intensity" (≤ 10%): Reduce Zone 2 volume; introduce structured HIIT.
- `gap_status` = "moderate gap" (11–20%): Prescribe Zone 1–2 base only.
- `gap_status` = "aerobic deficiency" (> 20%): Extended base period required. No intensity. No exceptions.
- If `gap_pct` is null (no AnT test on record): Do not estimate the gap. Tell the athlete an AnT hill time trial is needed for a complete assessment.

## AeT Detection — Field Signals (when no engine result available)

- Upper limit of sustained nose breathing
- Able to hold a full conversation
- HR Drift Test: < 5% HR drift over 60 min at constant effort = at or below AeT

## Coaching Directives

- Do not prescribe intensity if gap > 10% — the base is not ready to amplify it.
- Do not use % of HRmax to set zones — individual accuracy is too low.
- AeT fluctuates with fatigue. If AeT appears to drop unexpectedly, assess recovery status before adjusting prescription.
- After 6 months of Zone 2 base work, AeT HR typically rises significantly; AnT HR changes little. This is expected and correct.
- Never invent an AeT bpm from a failed test. Only valid engine results produce a Zone 2 ceiling.
