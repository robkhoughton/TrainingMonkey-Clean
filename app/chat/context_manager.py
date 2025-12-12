"""
Context Manager - Orchestrates context loading with caching and token awareness.

Key responsibilities:
1. Cache base context per user session (5-minute TTL)
2. Coordinate parallel loading of independent context sources
3. Track token budgets and truncate if needed
4. Provide fallback values when data sources fail
"""

import logging
from typing import Dict, Tuple, Optional
from datetime import datetime, timedelta
import threading
import json

logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_context_cache: Dict[str, Tuple[dict, datetime]] = {}
_cache_lock = threading.Lock()
CACHE_TTL_SECONDS = 300  # 5 minutes

# Token budget per universe (approximate)
TOKEN_BUDGETS = {
    'autopsy': 3000,
    'training_plan': 5000,
    'todays_workout': 3500,
    'progress': 3500,
    'general': 1000,
}


class ContextManager:
    """
    Manages context loading with caching and graceful degradation.

    Usage:
        manager = ContextManager(user_id)
        base_ctx, universe_ctx = manager.get_context('autopsy')
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self._base_context: Optional[dict] = None

    def get_context(self, universe: str) -> Tuple[dict, dict]:
        """
        Main entry point. Returns (base_context, universe_context).

        - Checks cache for base context first
        - Loads universe-specific context
        - Applies token budget constraints
        - Returns fallback values if loading fails
        """
        base = self._get_cached_base_context()

        try:
            universe_ctx = self._load_universe_context(universe)
        except Exception as e:
            logger.error(f"Failed to load {universe} context for user {self.user_id}: {e}")
            universe_ctx = self._get_fallback_context(universe)

        # Apply token budget
        universe_ctx = self._apply_token_budget(universe_ctx, universe)

        return base, universe_ctx

    def _get_cached_base_context(self) -> dict:
        """Load base context, using cache if available and fresh."""
        cache_key = f"base_{self.user_id}"

        with _cache_lock:
            if cache_key in _context_cache:
                cached, timestamp = _context_cache[cache_key]
                if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL_SECONDS):
                    logger.debug(f"Using cached base context for user {self.user_id}")
                    return cached

        # Load fresh
        from .context_loaders.base import load_base_context
        base = load_base_context(self.user_id)

        with _cache_lock:
            _context_cache[cache_key] = (base, datetime.now())

        return base

    def _load_universe_context(self, universe: str) -> dict:
        """Dynamically load the appropriate universe context."""
        loaders = {
            'autopsy': 'context_loaders.autopsy',
            'training_plan': 'context_loaders.training_plan',
            'todays_workout': 'context_loaders.daily_workout',
            'progress': 'context_loaders.progress',
            'general': 'context_loaders.general',
        }

        module_name = loaders.get(universe, 'context_loaders.general')

        # Import dynamically for modularity
        import importlib
        loader_module = importlib.import_module(f'.{module_name}', package='chat')
        return loader_module.load_context(self.user_id)

    def _get_fallback_context(self, universe: str) -> dict:
        """Return minimal fallback context when loading fails."""
        return {
            'status': 'partial',
            'message': f'Some {universe} data could not be loaded. I can still answer general questions.',
        }

    def _apply_token_budget(self, context: dict, universe: str) -> dict:
        """Truncate context if it exceeds the universe's token budget."""
        budget = TOKEN_BUDGETS.get(universe, 3000)
        estimated = self._estimate_tokens(context)

        if estimated > budget:
            logger.warning(f"Context for {universe} exceeds budget ({estimated} > {budget}), truncating")
            context = self._truncate_context(context, budget)

        return context

    def _estimate_tokens(self, obj) -> int:
        """Rough token estimate: ~4 chars per token."""
        text = json.dumps(obj, default=str)
        return len(text) // 4

    def _truncate_context(self, context: dict, budget: int) -> dict:
        """Truncate large text fields to fit within budget."""
        # Prioritize keeping structured data, truncate long strings
        for key, value in context.items():
            if isinstance(value, str) and len(value) > 500:
                # Keep first 400 chars of long strings
                context[key] = value[:400] + "... [truncated]"

        return context


def clear_user_cache(user_id: int) -> None:
    """Clear cached context for a user (call when their data changes)."""
    with _cache_lock:
        keys_to_remove = [k for k in _context_cache if k.endswith(f"_{user_id}")]
        for key in keys_to_remove:
            del _context_cache[key]
