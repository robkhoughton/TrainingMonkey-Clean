"""
Autopsy context loader - for questions about AI workout analysis.

Loads the most recent autopsy plus the data it analyzed.

Token estimate: ~2000-2500
"""

import logging
from db_utils import get_db_connection
from timezone_utils import get_user_current_date
from unified_metrics_service import UnifiedMetricsService

logger = logging.getLogger(__name__)


def load_context(user_id: int) -> dict:
    """
    Load context for AI Autopsy universe.

    Returns:
        {
            'autopsy': dict with latest autopsy analysis,
            'observations': dict with journal observations for that day,
            'metrics_at_time': dict with metrics snapshot,
        }
    """
    autopsy = _load_latest_autopsy(user_id)

    if not autopsy:
        return {
            'status': 'no_data',
            'message': 'No autopsy data available yet. Complete a workout and check back tomorrow for AI analysis.',
        }

    autopsy_date = autopsy.get('date')
    observations = _load_observations_for_date(user_id, autopsy_date)
    metrics = _load_metrics_for_date(user_id, autopsy_date)

    return {
        'autopsy': autopsy,
        'observations': observations,
        'metrics_at_time': metrics,
    }


def _load_latest_autopsy(user_id: int) -> dict:
    """Query ai_autopsies for most recent entry."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT date, alignment_score, autopsy_analysis,
                           prescribed_action, actual_activities
                    FROM ai_autopsies
                    WHERE user_id = %s
                    ORDER BY date DESC
                    LIMIT 1
                """, (user_id,))
                row = cur.fetchone()

                if not row:
                    return None

                return {
                    'date': str(row['date']),
                    'alignment_score': row['alignment_score'],
                    'autopsy_analysis': row['autopsy_analysis'],
                    'prescribed_action': row['prescribed_action'],
                    'actual_activities': row['actual_activities'],
                }
    except Exception as e:
        logger.error(f"Error loading autopsy for user {user_id}: {e}")
        return None


def _load_observations_for_date(user_id: int, date: str) -> dict:
    """Load journal entry for the autopsy date."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT energy_level, rpe_score, pain_percentage, notes
                    FROM journal_entries
                    WHERE user_id = %s AND entry_date = %s
                """, (user_id, date))
                row = cur.fetchone()

                if not row:
                    return {'status': 'no_journal_entry'}

                return {
                    'energy_level': row['energy_level'],
                    'rpe_score': row['rpe_score'],
                    'pain_percentage': row['pain_percentage'],
                    'notes': row['notes'] or '',
                }
    except Exception as e:
        logger.warning(f"Error loading observations: {e}")
        return {'status': 'error'}


def _load_metrics_for_date(user_id: int, date: str) -> dict:
    """Load metrics snapshot for the autopsy date."""
    try:
        service = UnifiedMetricsService()
        metrics = service.get_metrics_for_date(user_id, date)

        if not metrics:
            return {'status': 'no_metrics'}

        return {
            'external_acwr': round(metrics.get('external_acwr', 0), 2),
            'internal_acwr': round(metrics.get('internal_acwr', 0), 2),
            'normalized_divergence': round(metrics.get('normalized_divergence', 0), 3),
            'days_since_rest': metrics.get('days_since_rest', 0),
        }
    except Exception as e:
        logger.warning(f"Error loading metrics: {e}")
        return {'status': 'error'}
