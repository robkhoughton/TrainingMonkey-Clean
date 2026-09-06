"""
Data Reliability score — model-confidence redesign, ticket 02.

Answers "is today's signal trustworthy enough to generate a Rx from" — as
distinct from Specification Clarity (ticket 03), which answers "do we know
who this athlete is and what they're training for." This module computes
and exposes the score only; it does NOT gate Rx generation. Ticket 04 (the
Adequate Context Gate) uses three independent, direct floor checks instead
(chronic training-load depth, a recent-journaling count, season-goal
presence) — none of which need this composite. This score's role is purely
informational: the athlete-model panel (ticket 06) and Rx-prompt narration
(ticket 07), neither wired in yet.

Replaces the "is this field present" binary checks in the old 8-component
model_confidence_pct composite (see get_athlete_model_api() in strava_app.py)
with decay/coverage functions, per component:

  - load_coverage:        density of logged training days in the ACWR chronic
                           window — the continuous version of that composite's
                           binary activity_history check.
  - hr_calibration:       PROVISIONAL, validity-blind — profile-level
                           max_hr/resting_hr presence (the same signal the
                           old composite used). This measures whether HR
                           data exists, not whether it's meaningful: this
                           app doesn't yet ingest whether an activity had a
                           heart-rate sensor paired, so a dense stream of
                           silent-zero HR values (`average_heartrate or 0`
                           in strava_training_load.py, no sensor) would
                           score as highly reliable here — exactly backwards,
                           since that's the user whose internal-load numbers
                           are most wrong. Swap in true per-activity density
                           once has_heartrate ingestion lands (separate,
                           not-yet-scoped backlog item); until then this
                           component can't discriminate "calibrated" from
                           "never trained" — treat it as provisional.
  - hrv_rhr_baseline:     reuses readiness_engine's own baseline-sufficiency
                           gate (MIN_HRV_CHRONIC/MIN_RHR_CHRONIC) rather than
                           re-deriving new logic, plus recency of the latest
                           reading.
  - journal_recency:      decay-weighted density over the last few days,
                           replacing journal_power's flat 30-day average.
  - aerobic_staleness:    decays with time since the last aerobic assessment
                           instead of a hard 28-day cutoff.

Autopsy count/recency was considered and dropped: generate_autopsy_for_date()
is only ever invoked from inside save_journal_entry() for that same date, so
an autopsy never exists without a same-day journal entry — a standalone
autopsy component would just double-count journal_recency.

Why gate on this score at all rather than reuse the old composite: the old
composite double-weighted journal_power but capped it at roughly a fifth of
the total score, so a user could clear "good enough to prescribe" purely on
hr_calibration + load_coverage with ZERO recent journaling. journal_recency
here decays fast (5-day half-life) and isn't diluted by unrelated components
for exactly that reason.

MIN_AUTOPSIES (llm_recommendations_module.py:4248, `total_autopsies < 3`) is
a separate, intentionally untouched gate — it controls a lifetime-cumulative
prompt-block decision (show the alignment/divergence context, or "LEARNING"),
not a today's-signal-trustworthy decision. Not folded in here; not related.

Decay half-lives (journal: 5 days, aerobic: 21 days) and the HR-density
interim definition are STARTING VALUES per the ticket, not final — sanity-
checked against a handful of real accounts (see module docstring test notes
in the ticket file) but not yet reviewed against the full user base. Revisit
before ticket 04 sets a gating threshold on this score.
"""
import math
from datetime import timedelta
from typing import Dict, Optional

from db_utils import execute_query
from timezone_utils import get_app_current_date
from readiness_engine import (
    load_athlete_readiness_dataframe,
    get_readiness_metrics,
    MIN_HRV_CHRONIC,
    MIN_RHR_CHRONIC,
)
from exponential_decay_engine import ExponentialDecayEngine

_decay_engine = ExponentialDecayEngine()

# Chronic ACWR window — matches the convention already used throughout this
# codebase (readiness_engine, acwr_configuration_service) rather than a new one.
LOAD_COVERAGE_WINDOW_DAYS = 28

JOURNAL_RECENCY_HALF_LIFE_DAYS = 5
JOURNAL_RECENCY_WINDOW_DAYS = 25  # ~5 half-lives; weight beyond this is negligible

AEROBIC_STALENESS_HALF_LIFE_DAYS = 21

# Component weights — equal by default; revisit alongside the half-lives
# during the real-account validation pass.
COMPONENT_WEIGHTS = {
    'load_coverage': 1.0,
    'hr_calibration': 1.0,
    'hrv_rhr_baseline': 1.0,
    'journal_recency': 1.0,
    'aerobic_staleness': 1.0,
}


def _half_life_weight(days_ago: int, half_life_days: float) -> float:
    """0..1 decay weight: 1.0 at days_ago=0, 0.5 at days_ago=half_life_days."""
    if days_ago <= 0:
        return 1.0
    decay_rate = math.log(2) / half_life_days
    return _decay_engine.calculate_exponential_weight(days_ago, decay_rate)


def _load_coverage_component(user_id: int, as_of) -> Dict:
    """Continuous version of the old composite's binary activity_history
    check: density of logged training days (activity_id > 0, non-rest) in
    the ACWR chronic window, rather than a >=1-in-60-days binary."""
    row = execute_query(
        """SELECT COUNT(DISTINCT date) AS days_logged
           FROM activities
           WHERE user_id = %s AND date >= %s AND date <= %s
             AND activity_id > 0 AND type != 'rest'""",
        (user_id, as_of - timedelta(days=LOAD_COVERAGE_WINDOW_DAYS - 1), as_of),
        fetch=True,
    )
    days_logged = int(dict(row[0]).get('days_logged') or 0) if row else 0
    density = min(days_logged / LOAD_COVERAGE_WINDOW_DAYS, 1.0)
    return {
        'score': round(density * 100),
        'days_logged': days_logged,
        'window_days': LOAD_COVERAGE_WINDOW_DAYS,
    }


def _hr_calibration_component(user_id: int) -> Dict:
    """INTERIM: profile-level HR presence, not per-activity density.
    See module docstring — swap in has_heartrate density once ingested."""
    row = execute_query(
        "SELECT max_hr, resting_hr FROM user_settings WHERE id = %s",
        (user_id,), fetch=True,
    )
    hr = dict(row[0]) if row else {}
    has_max = bool(hr.get('max_hr'))
    has_resting = bool(hr.get('resting_hr'))
    score = 50 * (int(has_max) + int(has_resting))
    return {'score': score, 'max_hr': has_max, 'resting_hr': has_resting, 'interim_definition': True}


def _hrv_rhr_baseline_component(user_id: int, as_of) -> Dict:
    """Reuses readiness_engine's own baseline-sufficiency gate rather than
    re-deriving new logic, plus recency of the latest HRV/RHR reading."""
    df = load_athlete_readiness_dataframe(user_id, as_of_date=as_of)
    hrv = df['hrv'].dropna()
    rhr = df['rhr'].dropna()
    baseline_established = get_readiness_metrics(df) != (None, None)

    last_reading_date = None
    if len(df) > 0:
        has_reading = df[df['hrv'].notna() | df['rhr'].notna()]
        if len(has_reading) > 0:
            last_reading_date = has_reading['date'].max().date()

    if not baseline_established:
        # Not yet trustworthy — partial credit for progress toward the gate,
        # capped low so it can't compete with an established baseline.
        progress = min(len(hrv) / MIN_HRV_CHRONIC, len(rhr) / MIN_RHR_CHRONIC, 1.0)
        score = round(progress * 30)
    elif last_reading_date is None:
        score = 0
    else:
        # HRV/RHR are synced into the same journal_entries rows as journal
        # notes, so reuse that half-life rather than inventing a third one.
        days_since = (as_of - last_reading_date).days
        score = round(100 * _half_life_weight(days_since, JOURNAL_RECENCY_HALF_LIFE_DAYS))

    return {
        'score': score,
        'baseline_established': baseline_established,
        'hrv_reading_count': len(hrv),
        'rhr_reading_count': len(rhr),
        'days_since_last_reading': (as_of - last_reading_date).days if last_reading_date else None,
    }


def _journal_recency_component(user_id: int, as_of) -> Dict:
    """Decay-weighted density over the last few days — a lapsed journaling
    habit shows up immediately rather than being smoothed away like
    journal_power's flat 30-day average."""
    window_start = as_of - timedelta(days=JOURNAL_RECENCY_WINDOW_DAYS - 1)
    rows = execute_query(
        "SELECT date FROM journal_entries WHERE user_id = %s AND date >= %s AND date <= %s",
        (user_id, window_start, as_of), fetch=True,
    )
    entry_dates = {dict(r)['date'] for r in rows} if rows else set()

    max_possible = 0.0
    actual = 0.0
    for days_ago in range(JOURNAL_RECENCY_WINDOW_DAYS):
        weight = _half_life_weight(days_ago, JOURNAL_RECENCY_HALF_LIFE_DAYS)
        max_possible += weight
        if (as_of - timedelta(days=days_ago)) in entry_dates:
            actual += weight

    score = round(100 * actual / max_possible) if max_possible > 0 else 0
    return {
        'score': score,
        'entries_in_window': len(entry_dates),
        'window_days': JOURNAL_RECENCY_WINDOW_DAYS,
        'half_life_days': JOURNAL_RECENCY_HALF_LIFE_DAYS,
    }


def _aerobic_staleness_component(user_id: int, as_of) -> Dict:
    """Decays with time since the last aerobic assessment rather than the
    old composite's hard 28-day cutoff."""
    row = execute_query(
        "SELECT MAX(test_date) AS last_test FROM aerobic_assessments WHERE user_id = %s",
        (user_id,), fetch=True,
    )
    last_test = dict(row[0]).get('last_test') if row else None
    if not last_test:
        return {'score': 0, 'days_since_last_test': None, 'half_life_days': AEROBIC_STALENESS_HALF_LIFE_DAYS}

    days_since = (as_of - last_test).days
    score = round(100 * _half_life_weight(days_since, AEROBIC_STALENESS_HALF_LIFE_DAYS))
    return {'score': score, 'days_since_last_test': days_since, 'half_life_days': AEROBIC_STALENESS_HALF_LIFE_DAYS}


def compute_data_reliability(user_id: int, as_of_date: Optional[object] = None) -> Dict:
    """Compute the Data Reliability score (0-100) with a per-component
    breakdown. Does not gate anything — see module docstring.
    """
    as_of = as_of_date or get_app_current_date()

    components = {
        'load_coverage': _load_coverage_component(user_id, as_of),
        'hr_calibration': _hr_calibration_component(user_id),
        'hrv_rhr_baseline': _hrv_rhr_baseline_component(user_id, as_of),
        'journal_recency': _journal_recency_component(user_id, as_of),
        'aerobic_staleness': _aerobic_staleness_component(user_id, as_of),
    }

    total_weight = sum(COMPONENT_WEIGHTS.values())
    weighted_sum = sum(
        components[name]['score'] * COMPONENT_WEIGHTS[name]
        for name in components
    )
    composite = round(weighted_sum / total_weight)

    return {
        'score': composite,
        'components': components,
        'as_of_date': str(as_of),
    }
