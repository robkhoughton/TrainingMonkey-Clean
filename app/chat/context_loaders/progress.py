"""
Progress context loader - for questions about fitness trends and patterns.

Token estimate: ~3000-3500
"""

import logging
from unified_metrics_service import UnifiedMetricsService
from coach_recommendations import get_race_history, calculate_performance_trend
from llm_recommendations_module import (
    analyze_pattern_flags,
    get_recent_autopsy_insights,
)
from db_utils import get_db_connection

logger = logging.getLogger(__name__)


def load_context(user_id: int) -> dict:
    """
    Load context for My Progress universe.

    Returns:
        {
            'current_metrics': dict,
            'activities_summary': str,
            'pattern_flags': dict,
            'performance_trend': dict,
            'race_history': list,
            'autopsy_insights': dict,
            'athlete_profile': str,
        }
    """
    try:
        # Get current metrics
        metrics_service = UnifiedMetricsService()
        current_metrics = metrics_service.get_latest_complete_metrics(user_id) or {}

        # Get recent activities summary (28 days)
        activities_summary = _get_activities_summary(user_id, days=28)

        # Get pattern flags (simplified without full activities data)
        pattern_flags = {}

        # Get performance trend from race history
        race_history = get_race_history(user_id) or []
        performance_trend = calculate_performance_trend(race_history) if race_history else {}

        # Get autopsy insights (7 days)
        autopsy_insights = get_recent_autopsy_insights(user_id, days=7) or {}

        # Get athlete profile from user settings
        athlete_profile = _get_athlete_profile(user_id)

        return {
            'current_metrics': current_metrics,
            'activities_summary': activities_summary,
            'pattern_flags': pattern_flags,
            'performance_trend': performance_trend,
            'race_history': race_history[:5] if race_history else [],  # Recent 5
            'autopsy_insights': autopsy_insights,
            'athlete_profile': athlete_profile,
        }

    except Exception as e:
        logger.error(f"Error loading progress context for user {user_id}: {e}")
        return {
            'status': 'error',
            'message': 'Could not load progress data. Please try again.',
        }


def _get_activities_summary(user_id: int, days: int) -> str:
    """Generate a summary of recent activities without including all raw data."""
    try:
        metrics_service = UnifiedMetricsService()
        activities = metrics_service.get_recent_activities_for_analysis(days=days, user_id=user_id) or []

        if not activities:
            return "No recent activities."

        # Summarize without including all activity details (token optimization)
        total_activities = len(activities)
        total_distance = sum(a.get('distance', 0) for a in activities)
        total_elevation = sum(a.get('total_elevation_gain', 0) for a in activities)
        avg_hr = sum(a.get('average_heartrate', 0) for a in activities if a.get('average_heartrate', 0)) / max(1, len([a for a in activities if a.get('average_heartrate', 0)]))

        return f"Last {days} days: {total_activities} activities, {total_distance:.1f} miles, {total_elevation:.0f}ft elevation gain, avg HR {avg_hr:.0f}bpm"

    except Exception as e:
        logger.warning(f"Error generating activities summary: {e}")
        return "Activities summary unavailable."


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
            return result[0].capitalize()
        else:
            return "Intermediate"

    except Exception as e:
        logger.warning(f"Could not load athlete profile for user {user_id}: {e}")
        return "Intermediate"
