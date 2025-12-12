"""
General coaching context loader - for general training questions.

Loads context including recent journal notes for injury/fatigue awareness.

Token estimate: ~800-1200
"""

import logging
from coach_recommendations import get_race_goals, get_current_training_stage, get_recent_journal_observations
from db_utils import get_db_connection

logger = logging.getLogger(__name__)


def load_context(user_id: int) -> dict:
    """
    Load minimal context for General Coaching universe.

    Returns:
        {
            'a_race_summary': str (e.g., "Training for Boston Marathon on April 21, 2025"),
            'training_stage': str (e.g., "Build phase"),
            'athlete_profile': str,
            'recent_journal_notes': list (recent observations about injuries, fatigue, etc.)
        }
    """
    # Get A race summary
    a_race_summary = _get_a_race_summary(user_id)

    # Get current training stage
    training_stage_info = _get_training_stage(user_id)

    # Get athlete profile classification
    athlete_profile = _get_athlete_profile(user_id)

    # Get recent journal observations (for injury/fatigue context)
    recent_journal = _get_recent_journal(user_id)

    return {
        'a_race_summary': a_race_summary,
        'training_stage': training_stage_info,
        'athlete_profile': athlete_profile,
        'recent_journal_notes': recent_journal,
    }


def _get_a_race_summary(user_id: int) -> str:
    """Get summary of the A-priority race if exists."""
    try:
        races = get_race_goals(user_id)
        if not races:
            return "No race goals set"

        # Find A race
        a_race = next((r for r in races if r.get('priority') == 'A'), None)
        if not a_race:
            # Fall back to first race
            a_race = races[0]

        race_name = a_race.get('race_name', 'Unknown race')
        race_date = a_race.get('race_date', '')
        race_type = a_race.get('race_type', '')

        return f"Training for {race_name} ({race_type}) on {race_date}"

    except Exception as e:
        logger.warning(f"Could not load A race for user {user_id}: {e}")
        return "No race information available"


def _get_training_stage(user_id: int) -> str:
    """Get current training stage name."""
    try:
        stage_info = get_current_training_stage(user_id)
        if not stage_info:
            return "No active training plan"

        stage_name = stage_info.get('stage', 'Unknown')
        weeks_to_race = stage_info.get('weeks_to_race')

        if weeks_to_race is not None:
            return f"{stage_name} ({weeks_to_race} weeks to race)"
        else:
            return stage_name

    except Exception as e:
        logger.warning(f"Could not load training stage for user {user_id}: {e}")
        return "Training stage information unavailable"


def _get_athlete_profile(user_id: int) -> str:
    """Get athlete's training experience level from user profile."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT training_experience FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result and result[0]:
            # Capitalize first letter: 'elite' -> 'Elite'
            return result[0].capitalize()
        else:
            return "Intermediate"  # Default if not set

    except Exception as e:
        logger.warning(f"Could not load athlete profile for user {user_id}: {e}")
        return "Intermediate"


def _get_recent_journal(user_id: int) -> list:
    """Get recent journal observations (last 7 days) for injury/fatigue context."""
    try:
        journal_notes = get_recent_journal_observations(user_id, days=7)
        if not journal_notes:
            return []

        # Return last 5 observations for token efficiency
        return journal_notes[:5]

    except Exception as e:
        logger.warning(f"Could not load journal observations for user {user_id}: {e}")
        return []
