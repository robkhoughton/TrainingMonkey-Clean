Type: research
Status: open

## Question

Does `classify_session_polarized` classify well-executed interval sessions as `Moderate` (black hole) or fail them on `insufficient_intensity`, because it works from whole-session heart-rate time-in-zone? If so, how often does it happen on real sessions, and what change would stop it without breaking the single-classification design?

## Why this is suspected

`classify_session_polarized` (`app/llm_recommendations_module.py`) reads only zone times. It does not read the prescribed session intent, and `classify_session_dates` sums every activity on a date. Thresholds:

- Hard: Z4+Z5 >= 20% or Z4 >= 15%
- Easy: Z4+Z5 < 10% and Z3 <= `BLACK_HOLE_Z3_PCT` (15%)
- Moderate: everything else

Warm-up, cool-down, jog recoveries and heart-rate lag at the start of each rep all dilute the Z4+Z5 share. Seiler (2010, IJSPP 5:276-291, p. 279) makes the same point: heart-rate time-in-zone underestimates high-intensity work and misrepresents session effort, and he prefers the "session goal approach", classifying a session by the intensity of its main work.

Modeled session (not athlete data): 4 x 4 min at 95% VO2max, 20 min warm-up, 3 x 3 min jog recoveries, 20 min cool-down, 65 min total, run through the real function:

| Time in Z4/Z5 per 4-min rep | Z4+Z5 share | Class |
|---|---|---|
| 2.5 min | 15.4% | Moderate |
| 3.0 min | 18.4% | Moderate |
| 3.3 min | 20.4% | Hard |
| 4.0 min | 24.6% | Hard |

The same session at 3.0 min per rep gives 12 min of Z4+Z5, which is under the 15 min `insufficient_intensity` line in `compute_zone_compliance`.

A 30-min Z4 tempo with 15 min warm-up and cool-down classifies Hard (50% Z4), so continuous work is not affected.

## What to do

Run an offline analysis against real data. Do not change classification in this ticket.

1. For a set of past sessions where the prescription was a structured interval session (use `structured_output.decision.hard_session_type == "intervals"` or `"hills"`), compute the class the pipeline assigned and the Z4+Z5 share and `quality_minutes`.
2. Report how many were classed Moderate or flagged `insufficient_intensity` despite the prescription being Hard, and how many interval sessions were classed Hard.
3. Check the same for sessions where two activities share a date (an easy run plus an interval session), since the zone times are summed.
4. Report findings and candidate fixes with the evidence for each. Candidates, not decisions:
   - Classify from the prescribed intent when one exists, falling back to zone time otherwise.
   - Compute Z4+Z5 share over the working portion of the session only (for example, a rolling window or lap-based).
   - Lower the Hard threshold, or measure Z4+Z5 minutes rather than a share.

## Constraints from earlier decisions

- One classification, one zone source: every consumer calls `classify_session_dates()`. A fix must keep that, not add a second classifier. (Open Brain, YTM polarized pipeline, 2026-11-02.)
- Only heart-rate bpm thresholds count toward load; terrain proxies are prohibited.
- Z3 on a prescribed Hard session is expected and must not be flagged.
- `BLACK_HOLE_Z3_PCT` is a single constant shared by the daily flag and the weekly count.

## Out of scope

- Changing the Easy/Hard/Moderate thresholds or the black-hole line for easy days.
- The age-based +5% easy target (no supporting evidence in the reviewed literature).
- Reclassifying where the Z3/Z4 boundary falls relative to VT1 and VT2.

## Reference

Research note with the paper-by-paper review and the zone-mapping detail: `C:\Users\robho\Documents\VAULT\BeyondAge\CoAuthor\02_RESEARCH\Zone3_Moderate_Intensity_Primary_Review_2026-11-04.md`
