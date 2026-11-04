Type: research
Status: open

## Question

Does HR lag on short interval reps lower TRIMP per load mile enough to push Normalized Divergence positive (read as recovery) during interval blocks? If so, by how much, and how does it compare with the athlete's calibrated divergence thresholds?

## Why this is suspected

intervals.icu forum users report that HR-based load "often underestimates the true intensity because HR lags behind actual effort, especially for reps under 1 km" ([thread](https://forum.intervals.icu/t/running-load-threshold-intervals-vs-easy-runs/100899)). Divergence = `2(x−1)/(x+1)` with `x = r_chronic / r_acute`, where `r` is TRIMP per load mile. If interval sessions undercount TRIMP, `r_acute` falls during an interval block, `x` rises, and divergence moves positive even if internal stress actually rose.

This is separate from `.scratch/session-classification-intervals/issues/01-measure-interval-misclassification.md`, which covers the effect of HR lag on session classification, not on load.

## Approach

Offline analysis only. No code change.

1. Take the interval-session set identified in session-classification-intervals ticket 01.
2. For each session, estimate the TRIMP shortfall from HR lag: for example, compare rep-onset HR against steady-state HR within each rep, or compare TRIMP with the session's pace or load-mile intensity.
3. Recompute the acute-window divergence for the surrounding dates with and without a lag correction.
4. Report the size of the shift against the athlete's `apply_athlete_model_to_thresholds()` bands, not the population defaults.

## Constraints

- Internal load is HR only. Terrain or grade proxies for internal load are prohibited.
- Do not infer a day's divergence from that day's session alone. Divergence is a 7d/28d rolling quantity.

## Done when

The divergence shift during interval blocks is quantified, and the result says whether it crosses a calibrated threshold.
