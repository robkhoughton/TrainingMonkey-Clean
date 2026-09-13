# gait_classifier.py
"""
Gait-mode classification for trail activities.

A single trail activity mixes running and hiking (power-hiking on climbs), and
these have very different natural cadences. Averaging cadence across a whole
activity blends both gaits into a number that isn't meaningful for either. This
module separates the two so cadence/stride metrics can be computed on the
running-mode portion only.

Classification uses grade-adjusted speed ONLY -- never cadence. Using cadence
to decide what counts as "running" would be circular: it would guarantee a
healthy-looking cadence number by construction instead of measuring whether the
runner's actual running cadence is healthy. Cadence is read back afterward,
per bucket, purely as the output metric.

Validated offline (Sept 2026) against ~15 of Rob's own activities: grade-adjusted
speed with hysteresis + minimum dwell cleanly separates running from hiking on
mixed mountain trail runs (cadence came out visibly bimodal across the two
buckets on every activity tested), while correctly classifying flat/road runs as
~running and logged walks as ~hiking. See classifier_version below -- any retune
of the constants in this file must bump that string so old and new aggregates
are never blended in one trend line.
"""

CLASSIFIER_VERSION = "v1_dwell6_gap025_linear"

# Grade-adjusted speed threshold: crude linear interpolation between two
# literature reference points for the walk-run transition speed (classifier
# tuning constants, not physiology claims):
#   ~2.00 m/s preferred transition on level ground
#   ~1.76 m/s at 7.2 degrees incline (~12.6% grade)
_THRESHOLD_FLAT_MS = 2.00
_THRESHOLD_AT_12_6_PCT_MS = 1.76
_THRESHOLD_FLOOR_MS = 0.9  # even brutal grades still allow "running" above this

# Hysteresis + dwell -- Phase 1 calibration grid-swept dwell in {6,12,20} and
# exit-gap in {0.15,0.25,0.35}; dwell=6/gap=0.25 won on both uncertain-fraction
# AND separation quality simultaneously (not a tradeoff pick).
MIN_DWELL_SAMPLES = 6
UPPER_HYST_OFFSET_MS = 0.0   # enter "running" right at threshold
LOWER_HYST_OFFSET_MS = -0.25  # exit "running" only 0.25 m/s below threshold

# Grade bands where Phase 1 found classification confidence degrades even
# though the underlying running-cadence signal itself stays stable (74-85
# across every band tested) -- flagged so a stored aggregate can be weighted
# down rather than silently trusted at full confidence.
_LOW_CONFIDENCE_GRADE_BANDS = ((-100.0, -8.0), (20.0, 100.0))

_REQUIRED_STREAM_KEYS = ("velocity_smooth", "grade_smooth", "moving", "cadence")


def _stream_data(value):
    """Normalize a stravalib StreamData object or a plain list to a plain list."""
    return value.data if hasattr(value, "data") else value


def _grade_adjusted_threshold(grade_pct):
    slope = (_THRESHOLD_FLAT_MS - _THRESHOLD_AT_12_6_PCT_MS) / 12.6
    g = max(grade_pct, 0.0)
    threshold = _THRESHOLD_FLAT_MS - slope * g
    return max(threshold, _THRESHOLD_FLOOR_MS)


def _is_low_confidence_grade(grade_pct):
    return any(lo <= grade_pct < hi for lo, hi in _LOW_CONFIDENCE_GRADE_BANDS)


def _classify_samples(velocity, grade, moving):
    """Per-sample labels: 'running' / 'hiking' / 'uncertain' / 'stopped'.

    Ambiguous samples (transitions, extreme/noisy grade, missing speed) land in
    'uncertain' rather than being forced into a binary label.
    """
    n = min(len(velocity), len(grade), len(moving))
    labels = [None] * n
    grades_out = [None] * n
    state = "hiking"  # start conservative
    dwell_candidate = None
    dwell_count = 0

    for i in range(n):
        if not moving[i]:
            labels[i] = "stopped"
            state = "hiking"
            dwell_candidate = None
            dwell_count = 0
            continue

        v = velocity[i]
        g = grade[i] if grade[i] is not None else 0.0
        grades_out[i] = g

        if v is None:
            labels[i] = "uncertain"
            continue

        if abs(g) > 25:
            labels[i] = "uncertain"
            dwell_candidate = None
            dwell_count = 0
            continue

        threshold = _grade_adjusted_threshold(g)
        upper = threshold + UPPER_HYST_OFFSET_MS
        lower = threshold + LOWER_HYST_OFFSET_MS

        if state == "hiking":
            proposed = "running" if v >= upper else "hiking"
        else:
            proposed = "hiking" if v < lower else "running"

        if proposed == state:
            labels[i] = state
            dwell_candidate = None
            dwell_count = 0
        else:
            if dwell_candidate == proposed:
                dwell_count += 1
            else:
                dwell_candidate = proposed
                dwell_count = 1

            if dwell_count >= MIN_DWELL_SAMPLES:
                state = proposed
                labels[i] = state
                dwell_candidate = None
                dwell_count = 0
            else:
                labels[i] = "uncertain"

    return labels, grades_out


def _mean(values):
    return sum(values) / len(values) if values else None


def _stdev(values):
    if len(values) < 2:
        return None
    m = _mean(values)
    return (sum((x - m) ** 2 for x in values) / len(values)) ** 0.5


def classify_gait_modes(streams):
    """
    Pure function: Strava activity streams in, aggregate gait-mode metrics out.
    No DB access, no network calls.

    `streams` is the dict returned by stravalib's get_activity_streams (values
    are StreamData objects with a `.data` list) -- plain dict-of-lists is also
    accepted (as used during offline validation).

    Returns None if a required stream type (velocity_smooth, grade_smooth,
    moving, cadence) is missing or empty. Otherwise returns a dict matching the
    gait_mode_aggregates table columns (excluding activity_id/user_id, which
    the caller supplies):

        classifier_version, running_seconds, hiking_seconds, uncertain_seconds,
        running_cadence_mean, running_cadence_std, running_cadence_n,
        hiking_cadence_mean, hiking_cadence_std, hiking_cadence_n,
        low_confidence_fraction, running_speed_mean, running_speed_std,
        running_speed_n

    running_speed_* uses RAW velocity_smooth (m/s), never grade-adjusted speed --
    grade-adjustment is a fictional "equivalent flat pace" used only to decide
    running vs. hiking; stride length (speed / cadence, computed downstream)
    needs real ground speed or it misrepresents actual distance per stride.

    Seconds are approximated as sample count (Strava streams are ~1Hz); this
    matches the offline validation methodology and would need revisiting if a
    non-uniform sample rate stream were ever used instead.
    """
    if not streams or not all(k in streams and streams[k] for k in _REQUIRED_STREAM_KEYS):
        return None

    velocity = _stream_data(streams["velocity_smooth"])
    grade = _stream_data(streams["grade_smooth"])
    moving = _stream_data(streams["moving"])
    cadence = _stream_data(streams["cadence"])

    if not velocity or not grade or not moving or not cadence:
        return None

    labels, grades = _classify_samples(velocity, grade, moving)
    n = min(len(labels), len(cadence))

    running_cadence = []
    running_speed = []
    hiking_cadence = []
    running_n = hiking_n = uncertain_n = 0
    low_confidence_running_n = 0

    for i in range(n):
        label = labels[i]
        if label == "running":
            running_n += 1
            if grades[i] is not None and _is_low_confidence_grade(grades[i]):
                low_confidence_running_n += 1
            if cadence[i] and cadence[i] > 0:
                running_cadence.append(cadence[i])
            if i < len(velocity) and velocity[i] is not None:
                running_speed.append(velocity[i])
        elif label == "hiking":
            hiking_n += 1
            if cadence[i] and cadence[i] > 0:
                hiking_cadence.append(cadence[i])
        elif label == "uncertain":
            uncertain_n += 1
        # "stopped" samples are excluded from all three buckets -- not moving time.

    return {
        "classifier_version": CLASSIFIER_VERSION,
        "running_seconds": float(running_n),
        "hiking_seconds": float(hiking_n),
        "uncertain_seconds": float(uncertain_n),
        "running_cadence_mean": _mean(running_cadence),
        "running_cadence_std": _stdev(running_cadence),
        "running_cadence_n": len(running_cadence),
        "hiking_cadence_mean": _mean(hiking_cadence),
        "hiking_cadence_std": _stdev(hiking_cadence),
        "hiking_cadence_n": len(hiking_cadence),
        "low_confidence_fraction": (
            low_confidence_running_n / running_n if running_n else None
        ),
        "running_speed_mean": _mean(running_speed),
        "running_speed_std": _stdev(running_speed),
        "running_speed_n": len(running_speed),
    }
