"""
Training Plan context loader - for questions about weekly programs and race goals.

Token estimate: ~4000-5000
"""

import logging
from coach_recommendations import (
    get_race_goals,
    get_race_history,
    get_training_schedule,
    get_current_training_stage,
    get_cached_weekly_program,
    calculate_performance_trend,
    get_recent_journal_observations,
)
from unified_metrics_service import UnifiedMetricsService
from llm_recommendations_module import analyze_pattern_flags, get_recent_autopsy_insights
from timezone_utils import get_user_current_date
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def load_context(user_id: int) -> dict:
    """
    Load context for Training Plan universe.

    Returns:
        {
            'weekly_program': dict,
            'race_goals': list,
            'race_history': list,
            'performance_trend': dict,
            'training_stage': dict,
            'schedule': dict,
            'current_metrics': dict,
            'pattern_flags': dict,
            'autopsy_insights': dict,
            'journal_observations': list,
        }
    """
    try:
        # Get current week start (Monday)
        current_date = get_user_current_date(user_id)
        days_since_monday = current_date.weekday()
        week_start = current_date - timedelta(days=days_since_monday)

        weekly_program = get_cached_weekly_program(user_id, week_start) or {}
        race_goals = get_race_goals(user_id) or []
        race_history = get_race_history(user_id) or []
        performance_trend = calculate_performance_trend(race_history) if race_history else {}
        training_stage = get_current_training_stage(user_id) or {}
        schedule = get_training_schedule(user_id) or {}

        # Get current metrics
        metrics_service = UnifiedMetricsService()
        current_metrics = metrics_service.get_latest_complete_metrics(user_id) or {}

        # Get pattern flags and autopsy insights
        pattern_flags = {}  # Simplified - would need activities data
        autopsy_insights = get_recent_autopsy_insights(user_id, days=7) or {}
        journal_observations = get_recent_journal_observations(user_id) or []

        return {
            'weekly_program': weekly_program,
            'race_goals': race_goals[:3] if race_goals else [],  # Limit to top 3
            'race_history': race_history[:5] if race_history else [],  # Recent 5
            'performance_trend': performance_trend,
            'training_stage': training_stage,
            'schedule': schedule,
            'current_metrics': current_metrics,
            'pattern_flags': pattern_flags,
            'autopsy_insights': autopsy_insights,
            'journal_observations': journal_observations[:5] if journal_observations else [],
        }

    except Exception as e:
        logger.error(f"Error loading training plan context for user {user_id}: {e}")
        return {
            'status': 'error',
            'message': 'Could not load training plan data. Please try again.',
        }
