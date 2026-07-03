"""
Aerobic Assessment Engine — HR Drift Test Analysis

Pure computation module. No database or Flask dependencies.
Called by strava_app.py endpoints after fetching the HR stream from db_utils.
"""

import re
import statistics
import logging

logger = logging.getLogger(__name__)

# Distance streams from Strava are cumulative metres.
METERS_TO_MILES = 1.0 / 1609.344


def analyze_hr_drift_test(
    hr_data: list,
    sample_rate: float = 1.0,
    warmup_minutes: float = 10.0,
    ant_bpm: float = None,
    cooldown_minutes: float = 0.0,
) -> dict:
    """Analyze a stored HR stream as an AeT HR Drift Test.

    Args:
        hr_data:        List of HR integer values (1 value per sample).
        sample_rate:    Samples per second (Hz). Default 1.0.
        warmup_minutes: Minutes to skip at the start as warm-up. Default 10.
        ant_bpm:        Optional AnT bpm from a separate hill time trial.

    Returns:
        dict with keys:
            valid (bool)
            first_half_avg_hr, second_half_avg_hr, drift_pct,
            aet_bpm, interpretation, steady_state_minutes,
            ant_bpm, gap_pct, gap_status
        On invalid input:
            valid (bool = False), error (str)
    """
    if not hr_data or not isinstance(hr_data, list):
        return {"valid": False, "error": "No HR data provided."}

    # Filter out zero/null samples that some devices emit
    hr_data = [h for h in hr_data if isinstance(h, (int, float)) and h > 30]

    if len(hr_data) == 0:
        return {"valid": False, "error": "HR stream contains no valid samples."}

    samples_per_minute = 60.0 * sample_rate
    warmup_samples = int(warmup_minutes * samples_per_minute)

    if warmup_samples >= len(hr_data):
        return {
            "valid": False,
            "error": f"Activity is shorter than the warm-up window ({warmup_minutes} min). "
                     "Reduce warm-up duration or choose a longer activity.",
        }

    cooldown_samples = int(cooldown_minutes * samples_per_minute)
    end_idx = len(hr_data) - cooldown_samples if cooldown_samples > 0 else len(hr_data)
    steady_state = hr_data[warmup_samples:end_idx]
    steady_state_minutes = len(steady_state) / samples_per_minute

    # Require at least 20 min of steady-state data for a meaningful split
    if steady_state_minutes < 20:
        return {
            "valid": False,
            "error": f"Only {steady_state_minutes:.1f} min of steady-state data after warm-up. "
                     "Need at least 20 min. Try reducing the warm-up window.",
        }

    # Split into two equal halves
    mid = len(steady_state) // 2
    first_half = steady_state[:mid]
    second_half = steady_state[mid:]

    first_half_avg = statistics.mean(first_half)
    second_half_avg = statistics.mean(second_half)

    drift_pct = ((second_half_avg / first_half_avg) - 1) * 100

    # AeT bpm = avg HR of first 5 min of steady state (the locked-in starting HR)
    aet_window = steady_state[:int(min(5 * samples_per_minute, mid))]
    aet_bpm = statistics.mean(aet_window)

    interpretation = _interpret_drift(drift_pct, aet_bpm)

    # AnT gap
    gap_pct = None
    gap_status = None
    if ant_bpm and ant_bpm > aet_bpm:
        gap_pct = (ant_bpm - aet_bpm) / ant_bpm * 100
        gap_status = _interpret_gap(gap_pct)

    return {
        "valid": True,
        "first_half_avg_hr": round(first_half_avg, 1),
        "second_half_avg_hr": round(second_half_avg, 1),
        "drift_pct": round(drift_pct, 2),
        "aet_bpm": round(aet_bpm, 0),
        "interpretation": interpretation,
        "steady_state_minutes": round(steady_state_minutes, 1),
        "ant_bpm": ant_bpm,
        "gap_pct": round(gap_pct, 1) if gap_pct is not None else None,
        "gap_status": gap_status,
    }


def _interpret_drift(drift_pct: float, aet_bpm: float) -> str:
    """Return a human-readable interpretation of the drift result."""
    if drift_pct < 1.5:
        return (
            f"Started below AeT — drift of {drift_pct:.1f}% is too low for a reliable result. "
            "Try starting 3–5 bpm higher next time."
        )
    elif drift_pct <= 5.0:
        return (
            f"Valid test — drift of {drift_pct:.1f}% confirms steady-state was at or near AeT. "
            f"Your aerobic threshold is approximately {aet_bpm:.0f} bpm."
        )
    elif drift_pct <= 10.0:
        return (
            f"Started above AeT — drift of {drift_pct:.1f}% indicates intensity exceeded threshold. "
            "Try starting 3–5 bpm lower next time."
        )
    else:
        return (
            f"Significantly above AeT — drift of {drift_pct:.1f}% is too high for a usable result. "
            "Try starting 8–10 bpm lower next time."
        )


def _interpret_gap(gap_pct: float) -> str:
    """Return AeT/AnT gap status label."""
    if gap_pct <= 10:
        return "ready for intensity"
    elif gap_pct <= 20:
        return "moderate gap — continue base"
    else:
        return "aerobic deficiency — prioritise Zone 2"


# ============================================================================
# TEST-SEGMENT PACE
#
# Pace-at-HR is invalid for trail runs (terrain variability — YTM rejects it), but
# VALID here: the AeT drift/LT1 test is a controlled treadmill/flat condition, so the
# pace held over the steady-state segment is a meaningful, comparable readout. Labelled
# downstream as "test-condition pace", never as a general fitness pace.
#
# Exact pace needs a per-sample distance stream aligned to the HR stream. That stream is
# stored FORWARD-ONLY (hr_streams.distance_data), so past tests fall back to a pace parsed
# from the athlete's free-text notes. Both paths are deterministic (category-1): the value
# is computed/extracted in code, never invented.
# ============================================================================


def segment_pace_from_distance(distance_data, sample_rate=1.0,
                               warmup_minutes=10.0, cooldown_minutes=0.0):
    """Exact average pace over the steady-state segment, from a cumulative-distance stream.

    Mirrors analyze_hr_drift_test's segment selection: skip `warmup_minutes` at the start
    and `cooldown_minutes` at the end, both converted to sample indices at `sample_rate`.
    The distance stream is index-aligned with the HR stream (same Strava request), so the
    same time window applies.

    Returns {avg_pace_sec_per_mi, segment_distance_mi, segment_minutes, pace_source:'stream'}
    or None when the data can't yield a meaningful pace.
    """
    if not distance_data or not isinstance(distance_data, list):
        return None

    samples_per_minute = 60.0 * sample_rate
    if samples_per_minute <= 0:
        return None

    n = len(distance_data)
    start_idx = int(warmup_minutes * samples_per_minute)
    end_idx = n - int(cooldown_minutes * samples_per_minute)
    if end_idx <= start_idx or start_idx < 0 or end_idx > n:
        return None

    def _nearest_valid(seq, idx, step):
        """First numeric value at/after (step=+1) or at/before (step=-1) idx."""
        i = idx
        while 0 <= i < len(seq):
            v = seq[i]
            if isinstance(v, (int, float)):
                return v
            i += step
        return None

    d_start = _nearest_valid(distance_data, start_idx, 1)
    d_end = _nearest_valid(distance_data, end_idx - 1, -1)
    if d_start is None or d_end is None:
        return None

    meters = d_end - d_start
    seconds = (end_idx - start_idx) / sample_rate
    miles = meters * METERS_TO_MILES
    if miles <= 0 or seconds <= 0:
        return None

    return {
        "avg_pace_sec_per_mi": round(seconds / miles, 1),
        "segment_distance_mi": round(miles, 2),
        "segment_minutes": round(seconds / 60.0, 1),
        "pace_source": "stream",
    }


# Free-text pace patterns, tried in order. Each yields seconds-per-mile.
# Conservative: every pattern requires an explicit unit/keyword so we never mistake a
# clock time or arbitrary number for a pace.
_MI = r'(?:mi\b|miles?)'
_KM = r'km\b'
# Optional "min" unit word between the clock value and the distance: matches
# min / mins / minute / minutes, with an optional trailing period ("8:06 minute/mile").
_MIN = r'(?:min(?:ute)?s?\.?\s*)?'
_PACE_PATTERNS = (
    # "8:30/mi", "8:30 min/mile", "8:06 minute/mile", "8:30 per mile"
    (re.compile(r'(\d{1,2}):(\d{2})\s*' + _MIN + r'(?:/|per\s+)?\s*' + _MI, re.I),
     lambda m: int(m.group(1)) * 60 + int(m.group(2))),
    # "8:30 pace"
    (re.compile(r'(\d{1,2}):(\d{2})\s*pace\b', re.I),
     lambda m: int(m.group(1)) * 60 + int(m.group(2))),
    # "5:00/km", "5:00 minute/km" -> sec/mi
    (re.compile(r'(\d{1,2}):(\d{2})\s*' + _MIN + r'(?:/|per\s+)?\s*' + _KM, re.I),
     lambda m: (int(m.group(1)) * 60 + int(m.group(2))) * 1.609344),
    # "8.5 mph" -> sec/mi
    (re.compile(r'(\d{1,2}(?:\.\d+)?)\s*mph\b', re.I),
     lambda m: 3600.0 / float(m.group(1)) if float(m.group(1)) > 0 else None),
    # "13 kph" / "13 km/h" -> sec/mi
    (re.compile(r'(\d{1,2}(?:\.\d+)?)\s*k(?:ph|m/h)\b', re.I),
     lambda m: 3600.0 / (float(m.group(1)) * 0.621371) if float(m.group(1)) > 0 else None),
)


def parse_pace_from_notes(notes):
    """Deterministically extract a test-condition pace (sec/mile) from free-text notes.

    Fallback for past tests that predate the stored distance stream. Returns
    {avg_pace_sec_per_mi, pace_source:'notes'} or None when no clear pace is present.
    Requires an explicit unit/keyword so a bare number is never treated as a pace.
    """
    if not notes or not isinstance(notes, str):
        return None
    for pattern, to_sec in _PACE_PATTERNS:
        m = pattern.search(notes)
        if not m:
            continue
        sec = to_sec(m)
        if sec and 180 <= sec <= 1800:  # 3:00–30:00 /mi sanity band
            return {"avg_pace_sec_per_mi": round(sec, 1), "pace_source": "notes"}
    return None


def format_pace(sec_per_mi):
    """Format seconds-per-mile as m:ss (e.g. 510 -> '8:30'). None-safe -> None."""
    if sec_per_mi is None:
        return None
    try:
        total = int(round(float(sec_per_mi)))
    except (TypeError, ValueError):
        return None
    if total <= 0:
        return None
    return f"{total // 60}:{total % 60:02d}"
