"""Canonical training-stage calculation — the single source of truth for stage boundaries.

Phase order, counting back from the A race:
    base (12+ wk) → build (8–12) → specificity (to taper start) → taper (to 2 wk)
    → peak (final 2 wk) → race → recovery

"peak" means peak READINESS — arriving at the start line fresh — not peak training
load. Highest load comes in build/specificity; peak sits AFTER taper.

Taper starts 3 weeks out (Bompa & Haff 2009: 8–14 day taper; Bosquet et al. 2007
meta-analysis: ~2 wk optimal) and 4 weeks out for athletes 60+, whose recovery from
the final hard sessions is slower.
"""
from datetime import date
from typing import Optional

MASTERS_TAPER_AGE = 60
TAPER_START_WEEKS = 3
MASTERS_TAPER_START_WEEKS = 4
PEAK_START_WEEKS = 2
SPECIFICITY_START_WEEKS = 8
BUILD_START_WEEKS = 12

_PEAK_EXPLANATION = (
    "Peak readiness — final taper and race week. 'Peak' means arriving at peak "
    "READINESS, not peak training load: the highest load came in build and "
    "specificity, and this phase comes after taper."
)


def taper_start_weeks(athlete_age: Optional[int] = None) -> int:
    if athlete_age is not None and int(athlete_age) >= MASTERS_TAPER_AGE:
        return MASTERS_TAPER_START_WEEKS
    return TAPER_START_WEEKS


def calculate_training_stage(race_date: date, current_date: date,
                             athlete_age: Optional[int] = None) -> dict:
    days_until_race = (race_date - current_date).days
    weeks_until_race = days_until_race / 7.0
    taper_start = taper_start_weeks(athlete_age)

    if days_until_race < 0:
        stage, description = 'recovery', 'Post-race recovery'
        details = description
    elif weeks_until_race < PEAK_START_WEEKS:
        stage, description = 'peak', 'Peak readiness — final taper and race week'
        details = _PEAK_EXPLANATION
    elif weeks_until_race < taper_start:
        stage, description = 'taper', 'Taper — reducing volume, keeping intensity'
        details = description
    elif weeks_until_race < SPECIFICITY_START_WEEKS:
        stage, description = 'specificity', 'Race-specific training'
        details = description
    elif weeks_until_race < BUILD_START_WEEKS:
        stage, description = 'build', 'Building fitness and volume'
        details = description
    else:
        stage, description = 'base', 'Base building phase'
        details = description

    if weeks_until_race > 16:
        total_weeks = int(weeks_until_race)
        week_number = 1
    else:
        total_weeks = 16
        week_number = int(16 - weeks_until_race) + 1

    return {
        'stage': stage,
        'stage_description': description,
        'details': details,
        'week_number': week_number,
        'total_weeks': total_weeks,
        'weeks_until_race': round(weeks_until_race, 1),
        'days_until_race': days_until_race,
        'taper_start_weeks': taper_start,
    }


def in_race_preparation_window(stage_info: dict) -> bool:
    """Taper, peak, or the final specificity week before taper starts."""
    stage = stage_info.get('stage')
    if stage in ('taper', 'peak'):
        return True
    weeks = stage_info.get('weeks_until_race')
    taper_start = stage_info.get('taper_start_weeks', TAPER_START_WEEKS)
    return stage == 'specificity' and weeks is not None and weeks < taper_start + 1
