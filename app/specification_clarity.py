"""
Specification Clarity score — model-confidence redesign, ticket 03.

Answers "do we know who this athlete is and what they're training for" —
as distinct from Data Reliability (app/data_reliability.py), which answers
"is today's data trustworthy." Presence-based, not decaying: a season goal
set on day one is just as clear as one set on day 200. Components:

  - athlete_profile:      age, gender, primary_sport, training_experience
                          present in user_settings (same fields the old
                          8-component composite used for this).
  - season_goal:          race or non-race (ticket 01) — a non-race goal
                          scores identically to an equivalently-complete
                          race goal. A race goal with a known distance
                          scores higher than one without, since distance is
                          real additional clarity about what's being
                          trained for; a non-race goal has no equivalent
                          field to be penalized for lacking.
  - weekly_schedule:      training_schedule_json.available_days present.
  - recommendation_style: user_settings.recommendation_style IS NOT NULL.
                          Moved here from the excluded "pure tone" bucket
                          after a review found it drives real safety
                          thresholds via get_adjusted_thresholds() and
                          silently defaults to 'balanced' when unset — an
                          unset value must count as missing here, not as
                          complete, even though get_user_recommendation_style()
                          masks the NULL for threshold purposes.

Does not gate Rx generation on its own. The season-goal piece specifically
is one of three hard floors in the Adequate Context Gate
(app/adequate_context_gate.py, ticket 04) — checked there independently,
not derived from this score.
"""
from typing import Dict, List

from db_utils import execute_query

PROFILE_FIELDS = ('age', 'gender', 'primary_sport', 'training_experience')


def _athlete_profile_component(user_id: int) -> Dict:
    row = execute_query(
        "SELECT age, gender, primary_sport, training_experience FROM user_settings WHERE id = %s",
        (user_id,), fetch=True,
    )
    profile = dict(row[0]) if row else {}
    missing = [f for f in PROFILE_FIELDS if profile.get(f) in (None, '')]
    score = round((len(PROFILE_FIELDS) - len(missing)) / len(PROFILE_FIELDS) * 100)
    return {'score': score, 'missing': missing}


def _season_goal_component(user_id: int) -> Dict:
    race_rows = execute_query(
        """SELECT race_name, race_date, distance_miles FROM race_goals
           WHERE user_id = %s ORDER BY (priority = 'A') DESC, race_date ASC LIMIT 1""",
        (user_id,), fetch=True,
    )
    if race_rows:
        has_distance = bool(dict(race_rows[0]).get('distance_miles'))
        score = 100 if has_distance else 50
        return {'score': score, 'goal_type': 'race', 'has_distance': has_distance}

    season_rows = execute_query(
        "SELECT id FROM season_goals WHERE user_id = %s LIMIT 1",
        (user_id,), fetch=True,
    )
    if season_rows:
        # Non-race goals have no race-specific field to be penalized for
        # lacking — presence alone is full clarity, same as ticket 01 requires.
        return {'score': 100, 'goal_type': 'non_race', 'has_distance': None}

    return {'score': 0, 'goal_type': None, 'has_distance': None}


def _weekly_schedule_component(user_id: int) -> Dict:
    row = execute_query(
        "SELECT training_schedule_json FROM user_settings WHERE id = %s",
        (user_id,), fetch=True,
    )
    sched_json = dict(row[0]).get('training_schedule_json') if row else None
    if isinstance(sched_json, str):
        import json as _json
        try:
            sched_json = _json.loads(sched_json)
        except Exception:
            sched_json = {}
    has_schedule = bool((sched_json or {}).get('available_days'))
    return {'score': 100 if has_schedule else 0, 'has_schedule': has_schedule}


def _recommendation_style_component(user_id: int) -> Dict:
    row = execute_query(
        "SELECT recommendation_style FROM user_settings WHERE id = %s",
        (user_id,), fetch=True,
    )
    # Raw column check, not get_user_recommendation_style() — that function
    # masks NULL with 'balanced' for threshold purposes, which must NOT
    # count as "complete" here.
    is_set = bool(row) and dict(row[0]).get('recommendation_style') not in (None, '')
    return {'score': 100 if is_set else 0, 'is_set': is_set}


def compute_specification_clarity(user_id: int) -> Dict:
    """Compute the Specification Clarity score (0-100) with a per-component
    breakdown. Presence-based — does not decay, unlike Data Reliability.
    """
    components = {
        'athlete_profile': _athlete_profile_component(user_id),
        'season_goal': _season_goal_component(user_id),
        'weekly_schedule': _weekly_schedule_component(user_id),
        'recommendation_style': _recommendation_style_component(user_id),
    }

    composite = round(sum(c['score'] for c in components.values()) / len(components))

    return {
        'score': composite,
        'components': components,
    }
