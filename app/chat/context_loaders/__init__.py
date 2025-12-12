"""
Modular context loaders - one module per universe.

Each loader module must implement:
    load_context(user_id: int) -> dict

This allows each universe to have its own independent loader with
appropriate error handling and data fetching logic.
"""

# Import loaders as they are implemented
from .base import load_base_context
from .autopsy import load_context as load_autopsy
from .training_plan import load_context as load_training_plan
from .daily_workout import load_context as load_daily_workout
from .progress import load_context as load_progress
from .general import load_context as load_general

__all__ = [
    'load_base_context',
    'load_autopsy',
    'load_training_plan',
    'load_daily_workout',
    'load_progress',
    'load_general',
]
