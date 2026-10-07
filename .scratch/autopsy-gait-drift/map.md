Label: wayfinder:map

## Destination

Lock the remaining design decisions for surfacing gait-mechanics drift (cadence
and stride length, first-half vs. second-half of a single activity) in the
activity autopsy. Ends when nothing is left to decide before implementation
begins — no code changes happen on this map.

## Notes

**Background (shipped, not part of this route):** gait-mode classification —
grade-adjusted-speed classifier, cadence never used for classification,
athlete-relative baselines, Rob-only (`user_id=1`) scoping — is already live in
production as a cross-activity trend chart on the dashboard, backed by
`gait_mode_aggregates` (`classifier_version=v1_dwell6_gap025_linear`). That
work happened outside any tracker and isn't restated here; this map covers only
the autopsy-specific extension.

**Settled constraints for this effort** (decided while naming the destination,
not separate tickets):
- Store the half-split at sync time as additional columns on
  `gait_mode_aggregates`, not recomputed live when an autopsy is generated —
  avoids adding a live Strava round-trip on top of the autopsy's existing LLM
  call.
- Show both cadence and stride length in the autopsy's drift line, not one —
  the pair together is what distinguishes a pace effect from a form effect.
- Inject bare numbers only, no interpretive framing (e.g. "may reflect
  fatigue"). That framing is category-3 judgment per this repo's
  `llm-determinism.md` — the model weighs it against the day's other context
  (pain report, RPE, notes); it isn't a category-1 fact to assert.

**Precedent to reference, not assume transfers unmodified:** the unbuilt
`trail_aerobic_decoupling` design (grade-filtered intra-workout aerobic
decoupling, time-based half-split) is the closest prior art in this codebase
for a within-activity time-split computation.

**Methodology for the analysis ticket:** mirror the offline-validation approach
already used for the classifier itself (negative controls, grid-sweep over
candidate parameters, judge by signal stability rather than intuition) —
documented in this session's history, not yet written up as a repo doc.

## Decisions so far

<!-- empty at charting time — populated as tickets close -->

## Not yet specified

<!-- none currently sharp enough to name; may open once the first ticket resolves -->

## Out of scope

- Extending gait-mode classification beyond `user_id=1` to all users.
- Band-matching stride length by speed in the cross-activity trend chart (the
  original design called for this; the shipped version uses simple
  per-activity means instead).
- Validating or revisiting the `MIN_ELEVATION_GAIN_FEET = 200` backfill cutoff.
