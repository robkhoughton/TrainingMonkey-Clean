"""
Aerobic Assessment Engine — HR Drift Test Analysis

Pure computation module. No database or Flask dependencies.
Called by strava_app.py endpoints after fetching the HR stream from db_utils.
"""

import statistics
import logging

logger = logging.getLogger(__name__)


def analyze_hr_drift_test(
    hr_data: list,
    sample_rate: float = 1.0,
    warmup_minutes: float = 10.0,
    ant_bpm: float = None,
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

    steady_state = hr_data[warmup_samples:]
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
