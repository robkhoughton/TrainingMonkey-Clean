"""
Readiness Engine — ANS-based training readiness assessment.

Uses z-score normalization against personal baselines to classify daily
readiness state and detect multi-day overreaching trends.

Four-state matrix:
    RED                    — 4-day overreaching streak. Immediate deload.
    YELLOW_PARASYMPATHETIC — Deep Hole: HRV spike + RHR suppression. Rest only.
    YELLOW_SYMPATHETIC     — Acute fatigue. Zone 1-2 only.
    GREEN                  — Parasympathetic dominant. Cleared for intensity.
    UNKNOWN                — Insufficient baseline data.
"""
import logging
from datetime import timedelta

import numpy as np
import pandas as pd

from db_utils import execute_query
from timezone_utils import get_app_current_date

logger = logging.getLogger(__name__)

# Minimum readings required before baselines are reliable
MIN_HRV_CHRONIC = 14   # 2 weeks
MIN_RHR_CHRONIC = 14   # 2 weeks — same as HRV; interim baseline is better than none

# Variance floors prevent exploding z-scores when readings are unusually stable
MIN_HRV_STD_FLOOR = 3.0  # ms — minimum meaningful HRV variation
MIN_RHR_STD_FLOOR = 1.5  # bpm — minimum meaningful RHR variation

_DEFAULT_DAYS = 90
_OVERREACHING_LOOKBACK = 4


def load_athlete_readiness_dataframe(user_id, days=_DEFAULT_DAYS):
    """Query journal_entries and return a date-ascending DataFrame.

    IMPORTANT: tail() is used throughout this module. Data MUST be sorted
    ascending (oldest first) or window calculations are silently wrong.
    """
    cutoff = get_app_current_date() - timedelta(days=days)
    rows = execute_query(
        """SELECT date, hrv_value, resting_hr, sleep_quality, sleep_score, spo2
           FROM journal_entries
           WHERE user_id = %s AND date >= %s
           ORDER BY date ASC""",
        (user_id, str(cutoff)),
        fetch=True,
    )
    if not rows:
        return pd.DataFrame(columns=['date', 'hrv', 'rhr', 'sleep_quality', 'sleep_score', 'spo2'])
    df = pd.DataFrame([dict(r) for r in rows])
    df = df.rename(columns={'hrv_value': 'hrv', 'resting_hr': 'rhr'})
    df['date'] = pd.to_datetime(df['date'])
    # NUMERIC columns come back as decimal.Decimal — cast to float for numpy arithmetic
    for col in ('hrv', 'rhr', 'sleep_quality', 'sleep_score', 'spo2'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.sort_values('date').reset_index(drop=True)


def _z_score(acute_val, chronic_mean, chronic_std, std_floor):
    return (acute_val - chronic_mean) / max(chronic_std, std_floor)


def get_readiness_metrics(df):
    """Compute HRV and RHR z-scores for the most recent snapshot in df.

    HRV: 7-day acute vs 30-day chronic (HRV is noisy; 7-day smooths outliers)
    RHR: 3-day acute vs 60-day chronic (longer baseline resists drift during
         hard training blocks, preventing signal washout)

    Returns (hrv_z, rhr_z) or (None, None) if data is insufficient.
    """
    hrv = df['hrv'].dropna()
    rhr = df['rhr'].dropna()

    if len(hrv) < MIN_HRV_CHRONIC or len(rhr) < MIN_RHR_CHRONIC:
        return None, None

    hrv_z = _z_score(
        hrv.tail(7).mean(),
        hrv.tail(30).mean(),
        hrv.tail(30).std(),
        MIN_HRV_STD_FLOOR,
    )
    rhr_z = _z_score(
        rhr.tail(3).mean(),
        rhr.tail(60).mean(),
        rhr.tail(60).std(),
        MIN_RHR_STD_FLOOR,
    )
    return hrv_z, rhr_z


def get_sleep_modifier(df):
    """Return a sleep quality signal for use in readiness classification.

    Priority chain:
      1. Subjective sleep_quality (1–5) — preferred; 3-day average.
      2. Garmin sleep_score (0–100) — fallback; only trusted at the extreme low end
         (< 50) where the signal is clear regardless of staging noise.
      3. No data — return 0 (no modifier; HRV/RHR carry the signal).

    Returns:
        -1  poor sleep — apply suppressive pressure
         0  neutral or no data
         1  good sleep — no penalty
    """
    sq = df['sleep_quality'].dropna()
    if len(sq) >= 1:
        avg = sq.tail(3).mean()
        if avg <= 2.0:
            return -1
        if avg >= 4.0:
            return 1
        return 0

    # Fallback: Garmin sleep_score — only trust the clearly-bad end
    ss = df['sleep_score'].dropna()
    if len(ss) >= 1 and ss.tail(3).mean() < 50:
        return -1

    return 0


def get_spo2_flag(df):
    """True if recent overnight SpO2 suggests illness, altitude load, or apnea events.

    Normal resting SpO2 at sea level is ≥ 96%. A 3-day average below 95% is a
    meaningful substrate signal regardless of HRV/RHR state — it overrides GREEN.
    Uses the spo2 field synced from intervals.icu (daily average from Garmin 955).
    """
    spo2 = df['spo2'].dropna()
    if len(spo2) < 1:
        return False
    return bool(spo2.tail(3).mean() < 95.0)


def evaluate_overreaching_trend(df, lookback=_OVERREACHING_LOOKBACK,
                                hrv_threshold=-1.0, rhr_threshold=1.0):
    """True if both HRV suppressed and RHR elevated on every day in the lookback window.

    Requires the same adverse condition present on all lookback_days consecutive
    snapshots — a single day does not constitute a trend.
    """
    if len(df) < MIN_RHR_CHRONIC + lookback:
        return False

    hrv_flagged = rhr_flagged = 0
    for i in range(lookback):
        slice_ = df.iloc[:len(df) - i] if i > 0 else df
        hrv_z, rhr_z = get_readiness_metrics(slice_)
        if hrv_z is None:
            return False
        if hrv_z <= hrv_threshold:
            hrv_flagged += 1
        if rhr_z >= rhr_threshold:
            rhr_flagged += 1

    return hrv_flagged == lookback and rhr_flagged == lookback


def classify_readiness_state(hrv_z, rhr_z, is_overreaching, sleep_modifier=0, spo2_flag=False):
    """Map z-scores and overreaching flag to the four-state ANS readiness matrix.

    Priority order:
      1. UNKNOWN — no baseline yet
      2. RED — multi-day overreaching streak
      3. YELLOW_PARASYMPATHETIC — Deep Hole (HRV spike + RHR suppression)
      4. YELLOW_SYMPATHETIC — SpO2 substrate flag (illness/altitude/apnea)
      5. YELLOW_SYMPATHETIC — poor sleep + borderline HRV/RHR (lowered threshold)
      6. YELLOW_SYMPATHETIC — standard sympathetic dominance thresholds
      7. YELLOW_SYMPATHETIC — GREEN gated by poor sleep on borderline readings
      8. GREEN — cleared for intensity

    sleep_modifier: -1 (poor), 0 (neutral/unknown), 1 (good) — from get_sleep_modifier()
    spo2_flag: True if 3-day SpO2 average < 95% — from get_spo2_flag()
    """
    if hrv_z is None or rhr_z is None:
        return "UNKNOWN", "Insufficient data — baseline still calibrating."
    if is_overreaching:
        return "RED", "Systemic overreaching — immediate deload."
    # Deep Hole: parasympathetic hyperactivity — deceptively positive signals
    if hrv_z >= 1.5 and rhr_z <= -1.0:
        return "YELLOW_PARASYMPATHETIC", "Parasympathetic hyperactivity — rest only, do not load."
    # SpO2 flag: substrate issue takes priority over HRV/RHR state
    if spo2_flag:
        return "YELLOW_SYMPATHETIC", "Low overnight SpO2 — possible illness or altitude load. Zone 1-2 only."
    # Poor sleep lowers the sympathetic threshold — catches borderline cases HRV/RHR would miss
    if sleep_modifier == -1 and (hrv_z <= -0.5 or rhr_z >= 0.5):
        return "YELLOW_SYMPATHETIC", "Acute fatigue + poor sleep — Zone 1-2 only."
    # Standard sympathetic gate
    if hrv_z <= -1.0 or rhr_z >= 1.0 or (hrv_z - rhr_z) < -1.2:
        return "YELLOW_SYMPATHETIC", "Acute fatigue — Zone 1-2 only."
    # GREEN requires confidence: poor sleep on borderline readings holds at YELLOW
    if sleep_modifier == -1 and (hrv_z <= 0.3 or rhr_z >= -0.3):
        return "YELLOW_SYMPATHETIC", "Borderline objective signals + poor sleep — Zone 1-2 only."
    return "GREEN", "Parasympathetic dominant — cleared for intensity."


def get_weekly_ans_summary(user_id):
    """Summarize ANS readiness across the prior 7 days for weekly plan generation.

    The weekly plan needs a trend, not just a snapshot. valid[0] is today (most
    recent slice), valid[-1] is oldest — so valid[:mid] is the recent half and
    valid[mid:] is the older half when computing trend direction.

    Returns dict or None if baseline data is insufficient.
    """
    df = load_athlete_readiness_dataframe(user_id)
    if df.empty:
        return None

    # Entry state (current)
    hrv_z, rhr_z = get_readiness_metrics(df)
    is_overreaching = evaluate_overreaching_trend(df)
    sleep_modifier = get_sleep_modifier(df)
    spo2_flag = get_spo2_flag(df)

    if hrv_z is None:
        return None

    entry_state, entry_narrative = classify_readiness_state(
        hrv_z, rhr_z, is_overreaching, sleep_modifier, spo2_flag
    )

    # Compute daily z-score snapshots across the last 7 days
    n = len(df)
    daily_states = []
    for i in range(min(7, n)):
        slice_ = df.iloc[:n - i] if i > 0 else df
        hz, rz = get_readiness_metrics(slice_)
        sm = get_sleep_modifier(slice_)
        sf = get_spo2_flag(slice_)
        if hz is not None:
            state, _ = classify_readiness_state(hz, rz, False, sm, sf)
            daily_states.append({'hrv_z': hz, 'rhr_z': rz, 'state': state})

    if not daily_states:
        return None

    days_green  = sum(1 for d in daily_states if d['state'] == 'GREEN')
    days_yellow = sum(1 for d in daily_states if 'YELLOW' in d['state'])
    days_red    = sum(1 for d in daily_states if d['state'] == 'RED')
    avg_hrv_z   = round(sum(d['hrv_z'] for d in daily_states) / len(daily_states), 2)
    avg_rhr_z   = round(sum(d['rhr_z'] for d in daily_states) / len(daily_states), 2)

    # Trend: valid[0]=today, valid[-1]=oldest. recent half vs older half.
    if len(daily_states) >= 4:
        mid = len(daily_states) // 2
        recent_hrv = sum(d['hrv_z'] for d in daily_states[:mid]) / mid
        older_hrv  = sum(d['hrv_z'] for d in daily_states[mid:]) / (len(daily_states) - mid)
        trend = ('improving' if recent_hrv > older_hrv + 0.3
                 else 'degrading' if recent_hrv < older_hrv - 0.3
                 else 'stable')
    else:
        trend = 'insufficient_data'

    # Recovery week: overreaching streak, or 2+ red days, or 4+ yellow AND degrading.
    # Yellow days alone are managed load — not a recovery trigger without a worsening trend.
    recovery_week = is_overreaching or days_red >= 2 or (days_yellow >= 4 and trend == 'degrading')

    return {
        'entry_state':               entry_state,
        'entry_narrative':           entry_narrative,
        'avg_hrv_z':                 avg_hrv_z,
        'avg_rhr_z':                 avg_rhr_z,
        'days_green':                days_green,
        'days_yellow':               days_yellow,
        'days_red':                  days_red,
        'trend':                     trend,
        'is_overreaching':           is_overreaching,
        'recovery_week_recommended': recovery_week,
    }


def get_ans_readiness(user_id):
    """Full pipeline: load → z-scores → overreaching trend → state classification.

    Returns:
        dict with keys: state, narrative, hrv_z, rhr_z, is_overreaching
        On any error, returns UNKNOWN state so callers always get a valid dict.
    """
    try:
        df = load_athlete_readiness_dataframe(user_id)
        hrv_reading_count = int(df['hrv'].dropna().shape[0])
        rhr_reading_count = int(df['rhr'].dropna().shape[0])
        hrv_z, rhr_z = get_readiness_metrics(df)
        is_overreaching = evaluate_overreaching_trend(df)
        sleep_modifier = get_sleep_modifier(df)
        spo2_flag = get_spo2_flag(df)
        state, narrative = classify_readiness_state(
            hrv_z, rhr_z, is_overreaching, sleep_modifier, spo2_flag
        )
        return {
            'state': state,
            'narrative': narrative,
            'hrv_z': round(float(hrv_z), 2) if hrv_z is not None else None,
            'rhr_z': round(float(rhr_z), 2) if rhr_z is not None else None,
            'is_overreaching': is_overreaching,
            'sleep_modifier': sleep_modifier,
            'spo2_flag': spo2_flag,
            'hrv_reading_count': hrv_reading_count,
            'rhr_reading_count': rhr_reading_count,
        }
    except Exception as exc:
        logger.error(f"readiness_engine error for user {user_id}: {exc}", exc_info=True)
        return {
            'state': 'UNKNOWN',
            'narrative': 'Readiness data unavailable.',
            'hrv_z': None,
            'rhr_z': None,
            'is_overreaching': False,
            'sleep_modifier': 0,
            'spo2_flag': False,
            'hrv_reading_count': 0,
            'rhr_reading_count': 0,
        }
