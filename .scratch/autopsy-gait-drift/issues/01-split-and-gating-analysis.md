Type: task
Status: claimed

## Question

What temporal split (halves? thirds? something distance-based rather than
time-based?) and what gating thresholds (minimum qualifying running duration,
minimum deviation magnitude) produce a stable, non-noise-dominated
cadence/stride-length drift signal within a single activity — worth surfacing
in the autopsy?

Run an offline analysis against real data (existing `gait_mode_aggregates`
rows, and cached streams from the original classifier validation work where
needed) mirroring the methodology already used to calibrate the classifier
itself: try candidate splits and thresholds, judge by whether the resulting
signal is stable across qualifying activities rather than noise-dominated, and
report findings — a recommended split, recommended thresholds, and the
evidence for them. Do not decide the final values unilaterally; that's ticket
02, which depends on this one's findings.
