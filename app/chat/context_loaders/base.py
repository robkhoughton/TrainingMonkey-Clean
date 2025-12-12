"""
Base context loader - shared by all universes.

This loads user-specific settings that remain constant across conversation turns:
- Coaching tone preferences
- Risk tolerance thresholds
- Reference training guide

Token estimate: ~800-1200
"""

import logging
from llm_recommendations_module import (
    load_training_guide,
    get_coaching_tone_instructions,
    get_user_coaching_spectrum,
    get_user_recommendation_style,
    get_adjusted_thresholds,
)

logger = logging.getLogger(__name__)


def load_base_context(user_id: int) -> dict:
    """
    Load context shared by all universes.

    Returns:
        {
            'training_guide': str (truncated to ~1500 chars),
            'coaching_tone': str,
            'risk_tolerance': str,
            'threshold_description': str,
            'thresholds': dict,
        }
    """
    try:
        spectrum = get_user_coaching_spectrum(user_id)
        coaching_tone = get_coaching_tone_instructions(spectrum)
    except Exception as e:
        logger.warning(f"Could not load coaching spectrum for user {user_id}: {e}")
        coaching_tone = "Provide balanced, supportive coaching advice."
        spectrum = 50

    try:
        risk_style = get_user_recommendation_style(user_id)
        thresholds = get_adjusted_thresholds(risk_style)
    except Exception as e:
        logger.warning(f"Could not load thresholds for user {user_id}: {e}")
        risk_style = "BALANCED"
        thresholds = {'acwr_high_risk': 1.3, 'acwr_optimal_max': 1.2, 'max_days_rest': 7}

    try:
        full_guide = load_training_guide()
        # Truncate to save tokens - keep most relevant sections
        training_guide = _truncate_training_guide(full_guide, max_chars=1500)
    except Exception as e:
        logger.warning(f"Could not load training guide: {e}")
        training_guide = "Reference the athlete's specific metrics and goals when providing advice."

    threshold_description = _format_thresholds(thresholds)

    return {
        'training_guide': training_guide,
        'coaching_tone': coaching_tone,
        'risk_tolerance': risk_style,
        'threshold_description': threshold_description,
        'thresholds': thresholds,
    }


def _truncate_training_guide(guide: str, max_chars: int) -> str:
    """Keep essential training principles, drop verbose examples."""
    if len(guide) <= max_chars:
        return guide

    # Keep first portion which typically has core principles
    truncated = guide[:max_chars]
    # Try to break at a paragraph boundary
    last_para = truncated.rfind('\n\n')
    if last_para > max_chars * 0.7:
        truncated = truncated[:last_para]

    return truncated + "\n[Guide truncated for brevity]"


def _format_thresholds(thresholds: dict) -> str:
    """Format thresholds as readable text for the prompt."""
    lines = []
    if 'acwr_high_risk' in thresholds:
        lines.append(f"ACWR High Risk: >{thresholds['acwr_high_risk']}")
    if 'acwr_optimal_max' in thresholds:
        lines.append(f"ACWR Optimal Range: ≤{thresholds['acwr_optimal_max']}")
    if 'max_days_rest' in thresholds:
        lines.append(f"Max Consecutive Rest Days: {thresholds['max_days_rest']}")

    return ", ".join(lines) if lines else "Using default thresholds"
