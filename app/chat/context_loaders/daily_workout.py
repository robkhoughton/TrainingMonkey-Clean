"""
Daily Workout context loader - for questions about today's recommendation.

Token estimate: ~3000-3500
"""

import logging
from db_utils import get_db_connection
from coach_recommendations import get_cached_weekly_program
from llm_recommendations_module import get_recent_autopsy_insights
from unified_metrics_service import UnifiedMetricsService
from timezone_utils import get_user_current_date
from datetime import timedelta

logger = logging.getLogger(__name__)


def load_context(user_id: int) -> dict:
    """
    Load context for Today's Workout universe.

    Returns:
        {
            'daily_recommendation': str,
            'weekly_program_today': dict,
            'current_metrics': dict,
            'pattern_flags': dict,
            'autopsy_insights': dict,
            'recent_journal_notes': str,
        }
    """
    try:
        current_date = get_user_current_date(user_id)
        today_str = str(current_date)

        # Get today's recommendation
        daily_recommendation = _get_todays_recommendation(user_id, today_str)

        # Get weekly program and extract today's workout
        days_since_monday = current_date.weekday()
        week_start = current_date - timedelta(days=days_since_monday)
        weekly_program = get_cached_weekly_program(user_id, week_start) or {}
        weekly_program_today = weekly_program.get('days', {}).get(current_date.strftime('%A'), {})

        # Get current metrics
        metrics_service = UnifiedMetricsService()
        current_metrics = metrics_service.get_latest_complete_metrics(user_id) or {}

        # Get autopsy insights (last 3 days)
        autopsy_insights = get_recent_autopsy_insights(user_id, days=3) or {}

        # Get recent journal notes
        recent_journal_notes = _get_recent_journal_notes(user_id, days=3)

        return {
            'daily_recommendation': daily_recommendation,
            'weekly_program_today': weekly_program_today,
            'current_metrics': current_metrics,
            'pattern_flags': {},  # Simplified
            'autopsy_insights': autopsy_insights,
            'recent_journal_notes': recent_journal_notes,
        }

    except Exception as e:
        logger.error(f"Error loading daily workout context for user {user_id}: {e}")
        return {
            'status': 'error',
            'message': 'Could not load daily workout data. Please try again.',
        }


def _get_todays_recommendation(user_id: int, date: str) -> str:
    """Get today's LLM recommendation."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT recommendation_text
                    FROM llm_recommendations
                    WHERE user_id = %s AND target_date = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (user_id, date))
                row = cur.fetchone()
                return row['recommendation_text'] if row else "No recommendation generated yet for today."
    except Exception as e:
        logger.warning(f"Error loading today's recommendation: {e}")
        return "Recommendation unavailable."


def _get_recent_journal_notes(user_id: int, days: int) -> str:
    """Get concatenated journal notes from recent days."""
    try:
        current_date = get_user_current_date(user_id)
        start_date = current_date - timedelta(days=days)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT entry_date, notes
                    FROM journal_entries
                    WHERE user_id = %s AND entry_date >= %s
                    ORDER BY entry_date DESC
                """, (user_id, str(start_date)))
                rows = cur.fetchall()

                if not rows:
                    return "No recent journal entries."

                notes_list = [f"{row['entry_date']}: {row['notes']}" for row in rows if row['notes']]
                return "\n".join(notes_list) if notes_list else "No recent notes."

    except Exception as e:
        logger.warning(f"Error loading recent journal notes: {e}")
        return "Journal notes unavailable."
