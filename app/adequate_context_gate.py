"""
Adequate Context Gate — model-confidence redesign, ticket 04.

Merged from the original separate tickets 04 (Data Reliability gates Rx) and
05 (season-goal hard gate): a season goal is exactly as hard a requirement as
training history or recent journaling — YTM cannot prescribe a session
without knowing what it's for, regardless of data quality. One gate, three
must-pass floors, none softer than the others:

  1. Chronic training-load depth — at least 1 activity logged from 28+ days
     ago. Reused from the old 8-component composite's own activity_history
     check (see get_athlete_model_api() in strava_app.py), not a new
     invented number. An ACWR/divergence verdict needs a real chronic
     baseline; without one the load-based portion of the Rx is fabricated.
  2. Recent journaling — at least 2 journal entries in the past 7 days. A Rx
     generated blind to how the athlete is actually responding (energy,
     RPE, pain, sleep) is the concrete failure mode that justified this
     whole redesign — one entry three weeks ago proves nothing about today.
  3. Season goal present — race or non-race (see ticket 01, season_goals
     table). Cannot prescribe a session without knowing what it's for.

Data Reliability's composite score (app/data_reliability.py) is NOT part of
this gate — floors 1 and 2 above are direct checks that don't need it. The
composite is informational only (tickets 06/07).

Checked at the top of every Rx/autopsy generation entry point in
llm_recommendations_module.py — generate_recommendations(),
generate_recommendations_agentic(), generate_activity_autopsy_enhanced(),
and generate_autopsy_informed_daily_decision() — rather than inside
assemble_daily_context(). All four are confirmed call targets for every
cron/manual/journal-triggered path into Rx generation (see
.scratch/model-confidence-redesign/issues/04-adequate-context-gate.md), so
checking here gives full coverage without touching the shared context seam.
See test_adequate_context_gate.py for the test asserting every generator
calls this.

See /api/coach/adequate-context-status (strava_app.py) for the user-facing
status endpoint TodayPage.tsx polls to render the blocking message — this
module only returns machine-readable pass/fail, not display copy.
"""
from datetime import date, timedelta
from typing import Dict, Optional

from db_utils import execute_query
from timezone_utils import get_app_current_date

CHRONIC_DEPTH_DAYS = 28
JOURNAL_RECENCY_WINDOW_DAYS = 7
JOURNAL_RECENCY_MIN_COUNT = 2

# Ordered hardest-to-fix first (ticket 04's message-ordering rule) — also the
# order failing floors are reported in.
FLOOR_ORDER = ('chronic_depth', 'journal_recency', 'season_goal')


def _check_chronic_depth(user_id: int, as_of: date) -> bool:
    cutoff = as_of - timedelta(days=CHRONIC_DEPTH_DAYS)
    row = execute_query(
        """SELECT COUNT(*) AS c FROM activities
           WHERE user_id = %s AND date <= %s AND activity_id > 0 AND type != 'rest'""",
        (user_id, cutoff), fetch=True,
    )
    return int(dict(row[0]).get('c') or 0) >= 1 if row else False


def _check_recent_journaling(user_id: int, as_of: date) -> bool:
    """A journal_entries row is not proof of engagement on its own:
    intervals_icu_sync.py upserts a row daily for every connected user with
    wellness fields (hrv_value, resting_hr, sleep_score, ...) regardless of
    whether the athlete ever opens YTM — confirmed live against real
    accounts (users connected to intervals.icu with energy_level/rpe_score/
    pain_percentage/notes all NULL for a full week). Require at least one
    athlete-provided subjective field to count a day, not just row
    existence, or this floor is trivially satisfied by a passive wearable
    sync with zero real signal.
    """
    cutoff = as_of - timedelta(days=JOURNAL_RECENCY_WINDOW_DAYS - 1)
    row = execute_query(
        """SELECT COUNT(*) AS c FROM journal_entries
           WHERE user_id = %s AND date >= %s AND date <= %s
             AND (energy_level IS NOT NULL OR rpe_score IS NOT NULL
                  OR pain_percentage IS NOT NULL OR NULLIF(notes, '') IS NOT NULL)""",
        (user_id, cutoff, as_of), fetch=True,
    )
    return int(dict(row[0]).get('c') or 0) >= JOURNAL_RECENCY_MIN_COUNT if row else False


def _check_season_goal(user_id: int) -> bool:
    # Lazy import: coach_recommendations.py imports from this module's sibling
    # llm_recommendations_module.py, so a module-level import here would be
    # circular. Same pattern already used throughout strava_app.py route
    # handlers for this exact reason.
    from coach_recommendations import has_season_goal
    return has_season_goal(user_id)


def check_adequate_context(user_id: int, as_of_date: Optional[date] = None) -> Dict:
    """Evaluate the three hard floors. Does not call the LLM or have side
    effects — pure read/evaluate.

    Returns:
        {
            'passes': bool,
            'floors': {'chronic_depth': bool, 'journal_recency': bool, 'season_goal': bool},
            'failing_floors_ordered': [names of failing floors, hardest-to-fix first],
        }
    """
    as_of = as_of_date or get_app_current_date()

    floors = {
        'chronic_depth': _check_chronic_depth(user_id, as_of),
        'journal_recency': _check_recent_journaling(user_id, as_of),
        'season_goal': _check_season_goal(user_id),
    }

    return {
        'passes': all(floors.values()),
        'floors': floors,
        'failing_floors_ordered': [name for name in FLOOR_ORDER if not floors[name]],
    }
