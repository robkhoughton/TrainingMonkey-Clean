# YTM Coach Chatbot Implementation Plan

## Overview

Add a streaming chatbot to the Coach page that allows users to ask questions about their training data. The chatbot uses "context universes" - dropdown-selectable categories that load appropriate context while limiting token usage.

**Model:** Claude 3.5 Haiku (streaming)
**Budget:** ~$1/day per user (~200 messages)
**Storage:** No conversation persistence (session only)

---

## Architecture

**IMPORTANT:** The Coach page is a React component (`frontend/src/CoachPage.tsx`), not a Flask template. The chat widget must be implemented as a React component that calls Flask API endpoints.

### File Structure

```
app/
├── chat/                           # NEW MODULE (Flask/Python backend)
│   ├── __init__.py                 # Blueprint export
│   ├── routes.py                   # API endpoints
│   ├── service.py                  # Orchestration and streaming
│   ├── context_manager.py          # NEW: Caching and context orchestration
│   ├── context_loaders/            # NEW: Modular loaders (one per universe)
│   │   ├── __init__.py
│   │   ├── base.py                 # Shared context (coaching tone, thresholds)
│   │   ├── autopsy.py              # Autopsy universe loader
│   │   ├── training_plan.py        # Training plan universe loader
│   │   ├── daily_workout.py        # Today's workout loader
│   │   ├── progress.py             # Progress universe loader
│   │   └── general.py              # General coaching loader
│   ├── rate_limiter.py             # Usage tracking
│   └── prompts.py                  # System prompt templates
└── strava_app.py                   # MODIFY: register chat blueprint

frontend/src/
├── ChatWidget.tsx                  # NEW: React chat component
├── ChatWidget.css                  # NEW: Chat styles
└── CoachPage.tsx                   # MODIFY: integrate ChatWidget
```

### Design Principles

1. **Modular Context Loaders**: Each universe has its own loader module for maintainability and independent testing
2. **Context Caching**: Base context cached per-session to reduce redundant DB queries
3. **Progressive Loading**: Start with essential context; expand only when conversation deepens
4. **Graceful Degradation**: If a data source fails, use fallback (not crash)
5. **Token Budget Awareness**: Each loader reports its token estimate; total checked before API call

---

## Context Universes

Users select from a dropdown which "universe" to ask questions about:

| Universe | Purpose | Token Est. |
|----------|---------|------------|
| `autopsy` | Questions about latest AI workout analysis | ~2,500 |
| `training_plan` | Questions about weekly program, race goals, phases | ~4,000 |
| `todays_workout` | Questions about daily recommendation | ~3,000 |
| `progress` | Questions about fitness trends and patterns | ~3,000 |
| `general` | General coaching questions (minimal context) | ~800 |

---

## Database Migration

Run this SQL to create the usage tracking table:

```sql
CREATE TABLE chat_usage (
    user_id INTEGER REFERENCES user_settings(id),
    date TEXT NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, date)
);
```

---

## Implementation Files

### File 1: `app/chat/__init__.py`

```python
from .routes import chat_blueprint

__all__ = ['chat_blueprint']
```

---

### File 2: `app/chat/prompts.py`

**Purpose:** System prompt templates and universe intro messages.

**Constants to define:**

```python
UNIVERSE_INTROS = {
    'autopsy': "I can explain your latest workout analysis, alignment score, and what I learned from comparing your prescribed vs actual training.",
    'training_plan': "Ask me about your weekly program, race goals, training phases, or how your schedule is structured.",
    'todays_workout': "I can explain today's recommendation, suggest modifications, or discuss how it fits your current metrics.",
    'progress': "Let's talk about your fitness trends, training patterns, or how you're progressing toward your goals.",
    'general': "Ask me general coaching questions about training, nutrition, recovery, or running technique.",
}

SYSTEM_PROMPT_TEMPLATE = """You are a knowledgeable endurance running coach assistant for the YTM (Your Training Monkey) app.

COACHING STYLE:
{coaching_tone}

ATHLETE'S RISK TOLERANCE: {risk_tolerance}
{threshold_description}

REFERENCE FRAMEWORK:
{training_guide}

---

CURRENT CONTEXT ({universe}):
{universe_context}

---

INSTRUCTIONS:
- Answer questions based on the context provided above
- Reference specific data points when relevant (metrics, dates, workouts)
- Stay consistent with the coaching tone specified
- If asked about something outside the provided context, acknowledge the limitation
- Keep responses concise (100-200 words unless more detail is requested)
- Use the athlete's personalized thresholds, not generic ranges
- Do not make up data - only reference what's in the context
"""
```

**Functions to implement:**

```python
def build_system_prompt(base_context: dict, universe_context: dict, universe: str) -> str:
    """
    Assemble the full system prompt from base context and universe-specific context.

    Args:
        base_context: Dict with keys: coaching_tone, risk_tolerance, threshold_description, training_guide
        universe_context: Dict with universe-specific data (formatted as readable text)
        universe: One of 'autopsy', 'training_plan', 'todays_workout', 'progress', 'general'

    Returns:
        Formatted system prompt string
    """
    pass

def get_universe_intro(universe: str) -> str:
    """Return the intro message for a universe."""
    return UNIVERSE_INTROS.get(universe, UNIVERSE_INTROS['general'])

def format_context_section(context_dict: dict) -> str:
    """
    Convert a context dictionary into readable text for the prompt.

    Example input:
        {'current_metrics': {'acwr': 1.2, 'divergence': 0.03}, 'days_since_rest': 3}
    Example output:
        "Current Metrics:\n- ACWR: 1.2\n- Divergence: 0.03\nDays Since Rest: 3"
    """
    pass
```

---

### File 3: `app/chat/rate_limiter.py`

**Purpose:** Track daily token usage per user and enforce limits.

**Configuration (use values from app config or define here):**

```python
DAILY_INPUT_TOKEN_LIMIT = 600000
DAILY_OUTPUT_TOKEN_LIMIT = 150000
DAILY_MESSAGE_LIMIT = 100
```

**Functions to implement:**

```python
def check_usage(user_id: int) -> dict:
    """
    Check if user can send another message.

    Returns:
        {
            'allowed': bool,
            'remaining_messages': int,
            'input_tokens_used': int,
            'output_tokens_used': int,
            'message_count': int,
            'limit': int
        }

    Implementation notes:
    - Query chat_usage table for today's date
    - If no row exists, user has full budget
    - Check against all three limits (input, output, message count)
    - Use user's timezone for "today" (see timezone_utils.get_user_current_date)
    """
    pass

def record_usage(user_id: int, input_tokens: int, output_tokens: int) -> None:
    """
    Record token usage after a chat message.

    Implementation notes:
    - UPSERT into chat_usage table
    - Increment input_tokens, output_tokens, message_count
    - Update updated_at timestamp
    """
    pass

def get_daily_stats(user_id: int) -> dict:
    """
    Get usage statistics for display to user.

    Returns:
        {
            'messages_used': int,
            'messages_remaining': int,
            'percentage_used': float
        }
    """
    pass

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (chars / 4 is a reasonable approximation).
    Used for pre-flight checks before API calls.
    """
    return len(text) // 4
```

---

### File 4: `app/chat/context_manager.py`

**Purpose:** Orchestrate context loading with caching and token budgeting.

```python
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
from functools import lru_cache
import threading

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
        import json
        text = json.dumps(obj, default=str)
        return len(text) // 4

    def _truncate_context(self, context: dict, budget: int) -> dict:
        """Truncate large text fields to fit within budget."""
        # Prioritize keeping structured data, truncate long strings
        import json

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
```

---

### File 5: `app/chat/context_loaders/__init__.py`

```python
"""
Modular context loaders - one module per universe.

Each loader module must implement:
    load_context(user_id: int) -> dict
"""

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
```

---

### File 6: `app/chat/context_loaders/base.py`

**Purpose:** Load context shared by all universes (coaching tone, thresholds, training guide).

```python
"""
Base context loader - shared by all universes.

This loads user-specific settings that remain constant across conversation turns:
- Coaching tone preferences
- Risk tolerance thresholds
- Reference training guide

Token estimate: ~800-1200
"""

import logging
from app.llm_recommendations_module import (
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
```

---

### File 7: `app/chat/context_loaders/autopsy.py`

**Purpose:** Load context for AI Autopsy universe questions.

```python
"""
Autopsy context loader - for questions about AI workout analysis.

Loads the most recent autopsy plus the data it analyzed.

Token estimate: ~2000-2500
"""

import logging
from app.db_utils import get_db_connection
from app.timezone_utils import get_user_current_date
from app.unified_metrics_service import UnifiedMetricsService

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
                    'date': str(row[0]),
                    'alignment_score': row[1],
                    'autopsy_analysis': row[2],
                    'prescribed_action': row[3],
                    'actual_activities': row[4],
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
                    'energy_level': row[0],
                    'rpe_score': row[1],
                    'pain_percentage': row[2],
                    'notes': row[3] or '',
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
```

---

### Files 8-10: Other Context Loaders

**Pattern:** Each loader follows the same structure as `autopsy.py`:

```python
# app/chat/context_loaders/training_plan.py
# app/chat/context_loaders/daily_workout.py
# app/chat/context_loaders/progress.py
# app/chat/context_loaders/general.py

"""
Each file implements:
    load_context(user_id: int) -> dict

Key differences:
- training_plan.py: Loads weekly_program, race_goals, race_history, schedule
- daily_workout.py: Loads today's recommendation + recent journal notes
- progress.py: Loads activity summary, trends, athlete profile
- general.py: Loads minimal context (A race summary, training stage only)

See the Context Universes table for what each should return.
Use the existing functions from:
- app.coach_recommendations (get_race_goals, get_weekly_program, etc.)
- app.llm_recommendations_module (analyze_pattern_flags, get_recent_autopsy_insights)
- app.unified_metrics_service (UnifiedMetricsService)

Always wrap database/service calls in try/except and return graceful fallbacks.
"""
```

---

### DEPRECATED: Old `context_loaders.py` specification

The single-file approach below is replaced by the modular `context_loaders/` directory above. Keeping for reference only.

<details>
<summary>Original monolithic context_loaders.py (deprecated)</summary>

**Imports needed:**

```python
from app.llm_recommendations_module import (
    load_training_guide,
    get_coaching_tone_instructions,
    get_user_coaching_spectrum,
    get_user_recommendation_style,
    get_adjusted_thresholds,
    analyze_pattern_flags,
    get_recent_autopsy_insights,
    classify_athlete_profile,
)

from app.coach_recommendations import (
    get_race_goals,
    get_race_history,
    get_training_schedule,
    get_current_training_stage,
    get_weekly_program,
    calculate_performance_trend,
    get_recent_journal_observations,
)

from app.unified_metrics_service import UnifiedMetricsService
from app.timezone_utils import get_user_current_date
from app.db_utils import get_db_connection
```

</details>

---

### File 11: `app/chat/service.py`

**Purpose:** Orchestrate chat flow and handle Claude API streaming.

```python
"""
Chat Service - Orchestrates the chat flow with streaming responses.

Uses ContextManager for efficient context loading and handles
rate limiting, API calls, and SSE formatting.
"""

import anthropic
import json
import logging
from typing import Generator

from .context_manager import ContextManager
from .prompts import build_system_prompt
from .rate_limiter import check_usage, record_usage

logger = logging.getLogger(__name__)

# Configuration
CHAT_MODEL = 'claude-3-5-haiku-20241022'
MAX_RESPONSE_TOKENS = 500
TEMPERATURE = 0.7
MAX_CONVERSATION_MESSAGES = 10


def stream_chat_response(
    user_id: int,
    universe: str,
    message: str,
    conversation_history: list
) -> Generator[str, None, None]:
    """
    Main entry point for chat. Yields SSE-formatted chunks.

    Args:
        user_id: Authenticated user ID
        universe: One of the allowed universe types
        message: User's new message
        conversation_history: Prior messages [{'role': 'user'|'assistant', 'content': str}]

    Yields:
        SSE-formatted strings:
        - 'data: {"type": "token", "content": "..."}\n\n'
        - 'data: {"type": "done", "usage": {...}}\n\n'
        - 'data: {"type": "error", "message": "..."}\n\n'
    """
    # 1. Check rate limit
    usage_check = check_usage(user_id)
    if not usage_check['allowed']:
        yield _sse_event('error', {
            'message': 'Daily limit reached. Resets at midnight.',
            'usage': usage_check
        })
        return

    # 2. Load context using ContextManager (with caching)
    try:
        manager = ContextManager(user_id)
        base_context, universe_context = manager.get_context(universe)
    except Exception as e:
        logger.error(f"Context loading failed for user {user_id}: {e}")
        yield _sse_event('error', {'message': 'Failed to load context. Please try again.'})
        return

    # 3. Build system prompt
    system_prompt = build_system_prompt(base_context, universe_context, universe)

    # 4. Build messages (trim history, add new message)
    messages = build_messages(conversation_history, message)

    # 5. Stream from Claude API
    total_input = 0
    total_output = 0

    try:
        for event_type, data in call_claude_streaming(system_prompt, messages):
            if event_type == 'token':
                yield _sse_event('token', {'content': data})
            elif event_type == 'done':
                total_input = data['input_tokens']
                total_output = data['output_tokens']
            elif event_type == 'error':
                yield _sse_event('error', {'message': data})
                return
    except Exception as e:
        logger.error(f"Claude API error for user {user_id}: {e}")
        yield _sse_event('error', {'message': 'AI service temporarily unavailable.'})
        return

    # 6. Record usage
    record_usage(user_id, total_input, total_output)

    # 7. Send completion event
    yield _sse_event('done', {
        'usage': {
            'input_tokens': total_input,
            'output_tokens': total_output,
        }
    })


def call_claude_streaming(system_prompt: str, messages: list) -> Generator:
    """
    Call Claude API with streaming.

    Yields:
        Tuples of (event_type, data)
    """
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    try:
        with client.messages.stream(
            model=CHAT_MODEL,
            max_tokens=MAX_RESPONSE_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield ('token', text)

            response = stream.get_final_message()
            yield ('done', {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
            })
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        yield ('error', 'AI service error. Please try again.')
    except Exception as e:
        logger.error(f"Unexpected error in Claude streaming: {e}")
        yield ('error', 'Unexpected error occurred.')


def build_messages(conversation_history: list, new_message: str) -> list:
    """
    Build messages list for API call.

    - Trim history to MAX_CONVERSATION_MESSAGES
    - Ensure proper alternating pattern
    - Append new user message
    """
    # Take last N messages
    trimmed = conversation_history[-MAX_CONVERSATION_MESSAGES:]

    # Ensure we start with a user message (Claude requirement)
    if trimmed and trimmed[0].get('role') == 'assistant':
        trimmed = trimmed[1:]

    # Add new message
    trimmed.append({'role': 'user', 'content': new_message})

    return trimmed


def _sse_event(event_type: str, data: dict) -> str:
    """Format data as SSE event string."""
    payload = {'type': event_type, **data}
    return f"data: {json.dumps(payload)}\n\n"
```

---

### File 6: `app/chat/routes.py`

**Purpose:** Flask routes for chat API.

**Imports needed:**

```python
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
import json

from .service import stream_chat_response
from .rate_limiter import get_daily_stats
from .prompts import get_universe_intro

chat_blueprint = Blueprint('chat', __name__)
```

**Routes to implement:**

```python
@chat_blueprint.route('', methods=['POST'])
@login_required
def chat():
    """
    Main chat endpoint. Streams response via SSE.

    Request body:
        {
            "universe": "autopsy|training_plan|todays_workout|progress|general",
            "message": "User's question",
            "conversation": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }

    Response:
        Server-Sent Events stream with content-type: text/event-stream

    Implementation:
        1. Validate request JSON
        2. Validate universe is one of allowed values
        3. Validate message is non-empty string
        4. Get user_id from current_user
        5. Call stream_chat_response() and return as SSE stream

    Example response stream:
        data: {"type": "token", "content": "Based"}

        data: {"type": "token", "content": " on"}

        data: {"type": "done", "usage": {"input_tokens": 2500, "output_tokens": 150}}
    """
    pass

@chat_blueprint.route('/usage', methods=['GET'])
@login_required
def usage():
    """
    Get current usage statistics.

    Response:
        {
            "messages_used": 12,
            "messages_remaining": 88,
            "percentage_used": 12.0
        }
    """
    stats = get_daily_stats(current_user.id)
    return jsonify(stats)

@chat_blueprint.route('/intro/<universe>', methods=['GET'])
@login_required
def intro(universe: str):
    """
    Get intro message for a universe.

    Response:
        {
            "intro": "I can explain your latest workout analysis..."
        }
    """
    intro_text = get_universe_intro(universe)
    return jsonify({'intro': intro_text})

ALLOWED_UNIVERSES = {'autopsy', 'training_plan', 'todays_workout', 'progress', 'general'}
```

---

### File 7: Modify `app/strava_app.py`

Add these lines near other blueprint registrations:

```python
# Near the top with other imports
from chat import chat_blueprint

# Near other app.register_blueprint() calls
app.register_blueprint(chat_blueprint, url_prefix='/api/chat')
```

---

### File 13: `frontend/src/ChatWidget.tsx`

**Purpose:** React component for the chat widget.

```tsx
/**
 * ChatWidget - Streaming chat interface for the Coach page
 *
 * Features:
 * - Universe selector for context switching
 * - Real-time streaming responses via SSE
 * - Session-based conversation (no persistence)
 * - Usage tracking display
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import './ChatWidget.css';

// Types
interface Message {
  role: 'user' | 'assistant' | 'intro';
  content: string;
}

interface UsageStats {
  messages_used: number;
  messages_remaining: number;
  percentage_used: number;
}

type Universe = 'autopsy' | 'training_plan' | 'todays_workout' | 'progress' | 'general';

const UNIVERSE_OPTIONS: { value: Universe; label: string }[] = [
  { value: 'autopsy', label: 'AI Autopsy' },
  { value: 'training_plan', label: 'Training Plan' },
  { value: 'todays_workout', label: "Today's Workout" },
  { value: 'progress', label: 'My Progress' },
  { value: 'general', label: 'General Coaching' },
];

const ChatWidget: React.FC = () => {
  // State
  const [isExpanded, setIsExpanded] = useState(false);
  const [universe, setUniverse] = useState<Universe>('general');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [usage, setUsage] = useState<UsageStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Refs
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load usage stats
  const loadUsage = useCallback(async () => {
    try {
      const response = await fetch('/api/chat/usage');
      if (response.ok) {
        const data = await response.json();
        setUsage(data);
      }
    } catch (e) {
      console.error('Failed to load usage stats:', e);
    }
  }, []);

  // Load intro message for universe
  const loadIntro = useCallback(async (selectedUniverse: Universe) => {
    try {
      const response = await fetch(`/api/chat/intro/${selectedUniverse}`);
      if (response.ok) {
        const data = await response.json();
        setMessages([{ role: 'intro', content: data.intro }]);
      }
    } catch (e) {
      console.error('Failed to load intro:', e);
    }
  }, []);

  // Initialize on expand
  useEffect(() => {
    if (isExpanded) {
      loadUsage();
      loadIntro(universe);
      inputRef.current?.focus();
    }
  }, [isExpanded, loadUsage, loadIntro, universe]);

  // Handle universe change
  const handleUniverseChange = (newUniverse: Universe) => {
    setUniverse(newUniverse);
    setMessages([]);
    setError(null);
    loadIntro(newUniverse);
  };

  // Send message with streaming
  const sendMessage = async () => {
    if (!inputValue.trim() || isStreaming) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setError(null);

    // Add user message
    const newMessages: Message[] = [
      ...messages.filter(m => m.role !== 'intro'),
      { role: 'user', content: userMessage }
    ];
    setMessages(newMessages);

    // Prepare conversation history for API
    const conversationHistory = newMessages
      .filter(m => m.role !== 'intro')
      .map(m => ({ role: m.role, content: m.content }));

    setIsStreaming(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          universe,
          message: userMessage,
          conversation: conversationHistory.slice(0, -1), // Exclude the message we just added
        }),
      });

      if (!response.ok) {
        throw new Error('Chat request failed');
      }

      // Handle SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantContent = '';

      // Add empty assistant message
      setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'token') {
                assistantContent += data.content;
                setMessages(prev => {
                  const updated = [...prev];
                  updated[updated.length - 1] = {
                    role: 'assistant',
                    content: assistantContent
                  };
                  return updated;
                });
              } else if (data.type === 'done') {
                loadUsage(); // Refresh usage stats
              } else if (data.type === 'error') {
                setError(data.message);
              }
            } catch (e) {
              // Ignore JSON parse errors for incomplete chunks
            }
          }
        }
      }
    } catch (e) {
      setError('Connection error. Please try again.');
      console.error('Chat error:', e);
    } finally {
      setIsStreaming(false);
    }
  };

  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={`chat-widget ${isExpanded ? 'expanded' : 'collapsed'}`}>
      {/* Header */}
      <button
        className="chat-header"
        onClick={() => setIsExpanded(!isExpanded)}
        aria-expanded={isExpanded}
      >
        <span className="chat-title">Ask Your Coach</span>
        <span className="chat-toggle-icon">{isExpanded ? '−' : '+'}</span>
      </button>

      {/* Body - only render when expanded */}
      {isExpanded && (
        <div className="chat-body">
          {/* Universe selector */}
          <div className="chat-universe-selector">
            <label htmlFor="chat-universe">Ask about:</label>
            <select
              id="chat-universe"
              value={universe}
              onChange={(e) => handleUniverseChange(e.target.value as Universe)}
              disabled={isStreaming}
            >
              {UNIVERSE_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                {msg.content}
              </div>
            ))}
            {isStreaming && <div className="chat-streaming-indicator">...</div>}
            {error && <div className="chat-message error">{error}</div>}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="chat-input-area">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question..."
              disabled={isStreaming}
            />
            <button
              onClick={sendMessage}
              disabled={isStreaming || !inputValue.trim()}
            >
              Send
            </button>
          </div>

          {/* Usage display */}
          {usage && (
            <div className={`chat-usage ${usage.percentage_used > 80 ? 'warning' : ''}`}>
              {usage.messages_remaining} messages remaining today
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChatWidget;
```

---

### File 14: `frontend/src/ChatWidget.css`

**Purpose:** Styles for the chat widget.

```css
/* Chat Widget Container */
.chat-widget {
  position: fixed;
  bottom: 20px;
  right: 20px;
  width: 380px;
  max-width: calc(100vw - 40px);
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  font-family: inherit;
  transition: height 0.3s ease;
}

.chat-widget.collapsed {
  height: auto;
}

.chat-widget.expanded {
  height: 500px;
  max-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

/* Header */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #2563eb; /* YTM blue */
  color: white;
  border: none;
  border-radius: 12px 12px 0 0;
  cursor: pointer;
  width: 100%;
  text-align: left;
}

.chat-widget.collapsed .chat-header {
  border-radius: 12px;
}

.chat-title {
  font-weight: 600;
  font-size: 14px;
}

.chat-toggle-icon {
  font-size: 20px;
  font-weight: bold;
}

/* Body */
.chat-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Universe Selector */
.chat-universe-selector {
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-universe-selector label {
  font-size: 13px;
  color: #6b7280;
}

.chat-universe-selector select {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  background: white;
}

/* Messages Area */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-message {
  padding: 10px 14px;
  border-radius: 12px;
  max-width: 85%;
  line-height: 1.5;
  font-size: 14px;
  white-space: pre-wrap;
}

.chat-message.user {
  background: #2563eb;
  color: white;
  align-self: flex-end;
  border-bottom-right-radius: 4px;
}

.chat-message.assistant {
  background: #f3f4f6;
  color: #1f2937;
  align-self: flex-start;
  border-bottom-left-radius: 4px;
}

.chat-message.intro {
  background: #f0f9ff;
  color: #1e40af;
  align-self: flex-start;
  font-style: italic;
  border-left: 3px solid #2563eb;
}

.chat-message.error {
  background: #fef2f2;
  color: #dc2626;
  align-self: center;
  text-align: center;
}

/* Streaming Indicator */
.chat-streaming-indicator {
  color: #6b7280;
  font-style: italic;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* Input Area */
.chat-input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #e5e7eb;
}

.chat-input-area input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
}

.chat-input-area input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
}

.chat-input-area input:disabled {
  background: #f9fafb;
}

.chat-input-area button {
  padding: 10px 18px;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.chat-input-area button:hover:not(:disabled) {
  background: #1d4ed8;
}

.chat-input-area button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

/* Usage Display */
.chat-usage {
  padding: 8px 12px;
  text-align: center;
  font-size: 12px;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 0 0 12px 12px;
}

.chat-usage.warning {
  color: #dc2626;
  background: #fef2f2;
}

/* Mobile Responsiveness */
@media (max-width: 480px) {
  .chat-widget {
    bottom: 0;
    right: 0;
    width: 100%;
    max-width: 100%;
    border-radius: 12px 12px 0 0;
  }

  .chat-widget.expanded {
    height: 70vh;
  }

  .chat-header {
    border-radius: 12px 12px 0 0;
  }
}
```

---

### File 15: Coach Page Integration (`frontend/src/CoachPage.tsx`)

Add the ChatWidget import and render it within the CoachPage component:

```tsx
// At the top of the file, add import:
import ChatWidget from './ChatWidget';

// At the end of the component's JSX (before the closing fragment or div):
<ChatWidget />
```

**Specific location:** Add `<ChatWidget />` as the last child before the closing tag of the main component return. The widget is position:fixed so it will overlay on top.

---

## Testing Checklist

### Unit Tests

- [ ] `rate_limiter.py`: check_usage returns correct values
- [ ] `rate_limiter.py`: record_usage increments correctly
- [ ] `rate_limiter.py`: day rollover resets usage
- [ ] `context_loaders.py`: each loader returns expected structure
- [ ] `context_loaders.py`: handles missing data gracefully
- [ ] `prompts.py`: build_system_prompt formats correctly
- [ ] `service.py`: build_messages trims history correctly

### Integration Tests

- [ ] POST /api/chat returns SSE stream
- [ ] POST /api/chat with invalid universe returns error
- [ ] POST /api/chat when rate limited returns appropriate error
- [ ] GET /api/chat/usage returns correct stats
- [ ] Unauthenticated requests return 401

### Frontend Tests

- [ ] Universe selector changes context
- [ ] Messages display correctly
- [ ] Streaming tokens append smoothly
- [ ] Usage display updates after each message
- [ ] Error messages display appropriately
- [ ] Widget collapse/expand works
- [ ] Mobile responsive layout

### End-to-End Tests

- [ ] Full conversation flow with each universe
- [ ] Rate limiting kicks in after limit reached
- [ ] Context is appropriate for each universe (spot check responses)

---

## Error Handling

### Backend Errors

| Error | Response |
|-------|----------|
| Invalid universe | 400 with message |
| Empty message | 400 with message |
| Rate limit exceeded | 429 with usage stats |
| Claude API error | 500 with generic message (log details) |
| Context loading error | 500 with fallback to minimal context |

### Frontend Errors

| Error | User Message |
|-------|--------------|
| Network error | "Connection error. Please try again." |
| Rate limit | "You've reached your daily limit. Resets at midnight." |
| Server error | "Something went wrong. Please try again later." |

---

## Configuration Reference

These values should be configurable (environment variables or config file):

```python
CHAT_MODEL = 'claude-3-5-haiku-20241022'
CHAT_MAX_RESPONSE_TOKENS = 500
CHAT_TEMPERATURE = 0.7
CHAT_DAILY_INPUT_LIMIT = 600000
CHAT_DAILY_OUTPUT_LIMIT = 150000
CHAT_DAILY_MESSAGE_LIMIT = 100
CHAT_MAX_CONVERSATION_MESSAGES = 10
```

---

## Implementation Order

Execute in this order. Each step should be **tested before proceeding** to the next.

### Phase 1: Backend Foundation (No Frontend Dependencies)

| Step | File | Dependencies | Test |
|------|------|--------------|------|
| 1 | SQL: Create `chat_usage` table | Database access | Verify table exists |
| 2 | `app/chat/prompts.py` | None | Unit test prompt formatting |
| 3 | `app/chat/rate_limiter.py` | Step 1 | Unit test usage tracking |

### Phase 2: Context Loading (Modular)

| Step | File | Dependencies | Test |
|------|------|--------------|------|
| 4 | `app/chat/context_loaders/__init__.py` | None | Import test |
| 5 | `app/chat/context_loaders/base.py` | Existing modules | Unit test base context |
| 6 | `app/chat/context_loaders/general.py` | Step 5 | Unit test (simplest) |
| 7 | `app/chat/context_manager.py` | Steps 4-6 | Test caching, fallbacks |
| 8 | `app/chat/context_loaders/autopsy.py` | Step 7 | Unit test |
| 9 | `app/chat/context_loaders/training_plan.py` | Step 7 | Unit test |
| 10 | `app/chat/context_loaders/daily_workout.py` | Step 7 | Unit test |
| 11 | `app/chat/context_loaders/progress.py` | Step 7 | Unit test |

### Phase 3: API Layer

| Step | File | Dependencies | Test |
|------|------|--------------|------|
| 12 | `app/chat/service.py` | Steps 2, 3, 7 | Manual streaming test |
| 13 | `app/chat/routes.py` | Step 12 | Curl/Postman test |
| 14 | `app/chat/__init__.py` | Step 13 | Import test |
| 15 | `app/strava_app.py` modification | Step 14 | Server starts cleanly |

### Phase 4: Frontend (React)

| Step | File | Dependencies | Test |
|------|------|--------------|------|
| 16 | `frontend/src/ChatWidget.css` | None | Visual inspection |
| 17 | `frontend/src/ChatWidget.tsx` | Steps 13, 16 | Manual browser test |
| 18 | `frontend/src/CoachPage.tsx` modification | Step 17 | Full integration test |

### Phase 5: Verification

| Step | Action | Scope |
|------|--------|-------|
| 19 | Run all unit tests | Backend |
| 20 | Run integration tests | Full stack |
| 21 | Manual E2E testing | All universes |
| 22 | Load/stress testing | Rate limiting |

### Key Checkpoints

After **Step 7**: Backend context loading should work. Test with:
```python
from chat.context_manager import ContextManager
manager = ContextManager(user_id=1)
base, ctx = manager.get_context('general')
print(base, ctx)
```

After **Step 15**: API should respond. Test with:
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"universe":"general","message":"Hello","conversation":[]}'
```

After **Step 18**: Full feature should work in browser.

---

## Notes for Implementer

1. **Reuse existing functions** - The context loaders should import and call existing functions from `llm_recommendations_module.py`, `coach_recommendations.py`, and `unified_metrics_service.py`. Don't duplicate logic.

2. **Token estimation** - The `estimate_tokens()` function is a rough approximation. Claude's actual tokenization may differ, but this is sufficient for budgeting.

3. **Streaming format** - Use Server-Sent Events (SSE) format. Each message is `data: {json}\n\n`. The frontend should handle this streaming format.

4. **Error logging** - Log all errors with enough context to debug, but don't expose internal details to users.

5. **Timezone handling** - Use `timezone_utils.get_user_current_date(user_id)` for determining "today" for rate limiting and context loading.

6. **Missing data** - If a user has no autopsy, no weekly program, etc., the context loaders should return helpful messages like "No autopsy data available yet" rather than crashing.

7. **Conversation trimming** - Keep only the last N messages to prevent context from growing too large. The system prompt + context is already substantial.
