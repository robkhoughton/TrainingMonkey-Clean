#!/usr/bin/env python3
"""
Phase 4 — Agentic Context Assembly: Tool definitions and executors.

Defines 5 tool functions that the LLM can call to request specific context
instead of receiving all data in a single monolithic prompt.

Table / column names verified against live queries in strava_app.py and
coach_recommendations.py — no guessing.
"""

import json
import logging
from datetime import datetime, date, timedelta

from db_utils import execute_query, get_athlete_model

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _serialize(obj):
    """Recursively convert non-JSON-serializable types for JSON safety."""
    from decimal import Decimal
    if obj is None:
        return obj
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Tool 1 — recent activities
# ---------------------------------------------------------------------------

def get_activities(user_id: int, days: int) -> list:
    """Return last N days of activities.

    days must be 7, 14, or 28.

    Columns returned (all verified against activities table):
        date, type, distance_miles, elevation_gain_feet, trimp,
        acute_chronic_ratio, trimp_acute_chronic_ratio, normalized_divergence
    """
    if days not in (7, 14, 28):
        raise ValueError(f"days must be 7, 14, or 28; got {days}")

    cutoff = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    rows = execute_query(
        """
        SELECT date, type,
               distance_miles, elevation_gain_feet, trimp,
               acute_chronic_ratio, trimp_acute_chronic_ratio,
               normalized_divergence
        FROM activities
        WHERE user_id = %s AND date >= %s
        ORDER BY date ASC
        """,
        (user_id, cutoff),
        fetch=True
    )

    if not rows:
        return []

    result = []
    for row in rows:
        r = dict(row)
        result.append(_serialize(r))

    logger.info(f"get_activities(user={user_id}, days={days}): returned {len(result)} rows")
    return result


# ---------------------------------------------------------------------------
# Tool 2 — race goals
# ---------------------------------------------------------------------------

def get_race_goals(user_id: int) -> dict:
    """Return active race goals + training stage + weeks to A race.

    Columns verified against race_goals table:
        id, race_name, race_date, race_type, priority, target_time,
        notes, elevation_gain_feet
    """
    rows = execute_query(
        """
        SELECT id, race_name, race_date, race_type, priority,
               target_time, notes, elevation_gain_feet
        FROM race_goals
        WHERE user_id = %s
        ORDER BY race_date ASC
        """,
        (user_id,),
        fetch=True
    )

    if not rows:
        return {"has_race_goals": False, "goals": []}

    goals = [_serialize(dict(r)) for r in rows]

    # Identify the A race for training stage calculation
    a_race = next((g for g in goals if (g.get('priority') or '').strip().upper() == 'A'), None)

    weeks_to_a_race = None
    training_stage = None
    if a_race:
        try:
            a_race_date = datetime.strptime(a_race['race_date'], '%Y-%m-%d').date()
            days_until = (a_race_date - date.today()).days
            weeks_to_a_race = round(days_until / 7, 1)

            # Simple stage bucketing (mirrors _calculate_training_stage logic)
            if days_until <= 14:
                training_stage = 'taper'
            elif days_until <= 42:
                training_stage = 'peak'
            elif days_until <= 84:
                training_stage = 'build'
            else:
                training_stage = 'base'
        except (ValueError, TypeError):
            pass

    logger.info(
        f"get_race_goals(user={user_id}): {len(goals)} goals, "
        f"a_race={'yes' if a_race else 'no'}, stage={training_stage}"
    )
    return {
        "has_race_goals": True,
        "goals": goals,
        "a_race": a_race,
        "training_stage": training_stage,
        "weeks_to_a_race": weeks_to_a_race,
    }


# ---------------------------------------------------------------------------
# Tool 3 — weekly program day
# ---------------------------------------------------------------------------

def get_weekly_program_day(user_id: int, target_date: str) -> dict:
    """Return the planned workout for target_date from the weekly_programs table.

    weekly_programs stores program_json as a JSON blob with a 'daily_program'
    array where each element has: day, date, workout_type, description,
    duration_estimate, intensity, key_focus, terrain_notes.

    target_date format: YYYY-MM-DD
    """
    try:
        target_dt = datetime.strptime(target_date, '%Y-%m-%d').date()
    except ValueError:
        logger.warning(f"get_weekly_program_day: invalid date {target_date!r}")
        return {}

    # Find the Sunday of the week containing target_date (weeks are Sunday-Saturday,
    # matching how coach_recommendations.py stores week_start_date via get_current_week_start())
    days_since_sunday = (target_dt.weekday() + 1) % 7  # Sun=0, Mon=1, ..., Sat=6
    week_start = target_dt - timedelta(days=days_since_sunday)

    # Look back up to 4 weeks for a relevant program
    for week_offset in range(4):
        candidate_week = week_start - timedelta(weeks=week_offset)
        rows = execute_query(
            """
            SELECT program_json
            FROM weekly_programs
            WHERE user_id = %s AND week_start_date = %s
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (user_id, candidate_week.strftime('%Y-%m-%d')),
            fetch=True
        )
        if not rows:
            continue

        row = rows[0]
        program_json = row['program_json'] if hasattr(row, 'keys') else row[0]

        if isinstance(program_json, str):
            try:
                program = json.loads(program_json)
            except (json.JSONDecodeError, ValueError):
                continue
        else:
            program = program_json

        daily_program = program.get('daily_program', [])
        for day_entry in daily_program:
            if day_entry.get('date') == target_date:
                logger.info(
                    f"get_weekly_program_day(user={user_id}, date={target_date}): "
                    f"found in week starting {candidate_week}"
                )
                return _serialize(day_entry)

    logger.info(
        f"get_weekly_program_day(user={user_id}, date={target_date}): no planned workout found"
    )
    return {}


# ---------------------------------------------------------------------------
# Tool 4 — journal entries
# ---------------------------------------------------------------------------

def get_journal_entries(user_id: int, days: int) -> list:
    """Return recent journal observations.

    Columns verified against journal_entries table:
        date, energy_level, rpe_score, pain_percentage, notes
    """
    cutoff = (date.today() - timedelta(days=days)).strftime('%Y-%m-%d')
    rows = execute_query(
        """
        SELECT date, energy_level, rpe_score, pain_percentage, notes
        FROM journal_entries
        WHERE user_id = %s AND date >= %s
        ORDER BY date DESC
        """,
        (user_id, cutoff),
        fetch=True
    )

    if not rows:
        return []

    result = [_serialize(dict(r)) for r in rows]
    logger.info(f"get_journal_entries(user={user_id}, days={days}): returned {len(result)} rows")
    return result


# ---------------------------------------------------------------------------
# Tool 5 — athlete model
# ---------------------------------------------------------------------------

def get_athlete_model_tool(user_id: int) -> dict:
    """Return the athlete's persistent model (Phase 3).

    Delegates to get_athlete_model() from db_utils.
    Returns empty dict if no model exists.
    """
    model = get_athlete_model(user_id)
    if not model:
        logger.info(f"get_athlete_model_tool(user={user_id}): no model found")
        return {}
    result = _serialize(model)
    logger.info(
        f"get_athlete_model_tool(user={user_id}): "
        f"autopsies={result.get('total_autopsies')}, "
        f"div_low_n={result.get('div_low_n')}, threshold_n={result.get('threshold_n')}"
    )
    return result


# ---------------------------------------------------------------------------
# Anthropic SDK tool definitions
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "name": "get_activities",
        "description": (
            "Get recent training activities for the athlete. "
            "Choose days=7 for recent trends, days=14 for medium-term patterns, "
            "days=28 for a full training block. Returns date, type, distance, "
            "elevation, TRIMP, ACWR (external + internal), and normalised divergence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "enum": [7, 14, 28],
                    "description": "Number of days to look back (7, 14, or 28)"
                }
            },
            "required": ["days"]
        }
    },
    {
        "name": "get_race_goals",
        "description": (
            "Get the athlete's active race goals, including race name, date, type, "
            "priority (A/B/C), target time, and elevation. Also returns calculated "
            "training stage (base/build/peak/taper) and weeks to the A race."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_weekly_program_day",
        "description": (
            "Get the planned workout for a specific date from the athlete's weekly "
            "training program. Returns workout_type, description, duration_estimate, "
            "intensity, key_focus, and terrain_notes. Returns empty dict if no "
            "program exists for that date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format to look up the planned workout for"
                }
            },
            "required": ["target_date"]
        }
    },
    {
        "name": "get_journal_entries",
        "description": (
            "Get recent journal observations: energy level (1-5), RPE (1-10), "
            "pain percentage, and athlete notes. Useful for understanding subjective "
            "fatigue, injury status, and training response over recent days."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (e.g. 7, 14)"
                }
            },
            "required": ["days"]
        }
    },
    {
        "name": "get_athlete_model",
        "description": (
            "Get the athlete's persistent model built from autopsy learning (Phase 3). "
            "Contains athlete-specific ACWR sweet spot, typical divergence range, "
            "injury threshold, average alignment score, and trend. Returns empty dict "
            "if insufficient data has been collected yet."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]
