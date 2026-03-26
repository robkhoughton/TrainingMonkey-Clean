"""Shared prompt constants for LLM prompt builders."""

from typing import Optional

NORMALIZED_DIVERGENCE_FORMULA = (
    "Normalized Divergence = (External ACWR − Internal ACWR) / avg(External, Internal). "
    "THREE ZONES — "
    "POSITIVE (>0): Recovery zone — external load exceeds internal stress, athlete has unused capacity; potential detraining if sustained. "
    "NEGATIVE to div_low: Productive training window — real adaptation territory, affirm this zone. "
    "NEGATIVE beyond breakdown threshold: Danger zone — use athlete-specific threshold from ATHLETE MODEL, not a population constant. "
    "NEVER flag positive divergence as overtraining or injury risk. "
    "Use athlete-specific thresholds from the ATHLETE MODEL section."
)


def format_divergence_for_prompt(value: Optional[float], precision: str = '.3f') -> str:
    """Format normalized_divergence for LLM prompt injection.

    Always bundles the sign convention with the value — use this everywhere
    divergence appears in a prompt string. Never format divergence inline with
    a raw f-string, as that makes it possible to omit the valence definition.

    Returns 'N/A' (no formula appended) when value is None.
    """
    if value is None:
        return 'N/A'
    return f"{value:{precision}} [{NORMALIZED_DIVERGENCE_FORMULA}]"
