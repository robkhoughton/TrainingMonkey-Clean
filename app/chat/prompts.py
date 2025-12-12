"""
System prompt templates and universe intro messages for the chat feature.

This module provides:
- Universe-specific intro messages
- System prompt template assembly
- Context formatting utilities
"""

import json

# Universe intro messages shown when user selects a context
UNIVERSE_INTROS = {
    'autopsy': "I can explain your latest workout analysis, alignment score, and what I learned from comparing your prescribed vs actual training.",
    'training_plan': "Ask me about your weekly program, race goals, training phases, or how your schedule is structured.",
    'todays_workout': "I can explain today's recommendation, suggest modifications, or discuss how it fits your current metrics.",
    'progress': "Let's talk about your fitness trends, training patterns, or how you're progressing toward your goals.",
    'general': "Ask me general coaching questions about training, nutrition, recovery, or running technique.",
}

# System prompt template for Claude
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
- IMPORTANT: If an athlete_profile is provided in the context, always use it when describing the athlete's level (e.g., "elite", "advanced", "intermediate", "beginner"). Never assume a different level.
- Reference specific data points when relevant (metrics, dates, workouts)
- Stay consistent with the coaching tone specified
- If asked about something outside the provided context, acknowledge the limitation
- Keep responses concise (100-200 words unless more detail is requested)
- Use the athlete's personalized thresholds, not generic ranges
- Do not make up data - only reference what's in the context
"""


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
    # Format universe context into readable text
    universe_context_text = format_context_section(universe_context)

    # Build the prompt
    return SYSTEM_PROMPT_TEMPLATE.format(
        coaching_tone=base_context.get('coaching_tone', 'Provide balanced, supportive coaching advice.'),
        risk_tolerance=base_context.get('risk_tolerance', 'BALANCED'),
        threshold_description=base_context.get('threshold_description', 'Using default thresholds'),
        training_guide=base_context.get('training_guide', ''),
        universe=universe,
        universe_context=universe_context_text
    )


def get_universe_intro(universe: str) -> str:
    """Return the intro message for a universe."""
    return UNIVERSE_INTROS.get(universe, UNIVERSE_INTROS['general'])


def format_context_section(context_dict: dict) -> str:
    """
    Convert a context dictionary into readable text for the prompt.

    Handles nested dictionaries, lists, and various data types.

    Example input:
        {'current_metrics': {'acwr': 1.2, 'divergence': 0.03}, 'days_since_rest': 3}
    Example output:
        "Current Metrics:\n- ACWR: 1.2\n- Divergence: 0.03\nDays Since Rest: 3"
    """
    if not context_dict:
        return "No context available"

    lines = []

    def format_value(key: str, value, indent: int = 0) -> list:
        """Recursively format a value into readable lines."""
        prefix = "  " * indent

        if value is None or value == '':
            return []

        # Handle status messages (partial data, errors, etc.)
        if key == 'status':
            return [f"{prefix}{value}"]

        if key == 'message' and isinstance(value, str):
            return [f"{prefix}{value}"]

        # Format key as title case with spaces
        display_key = key.replace('_', ' ').title()

        # Handle different types
        if isinstance(value, dict):
            result = [f"{prefix}{display_key}:"]
            for k, v in value.items():
                result.extend(format_value(k, v, indent + 1))
            return result
        elif isinstance(value, list):
            if not value:
                return []
            result = [f"{prefix}{display_key}:"]
            for item in value:
                if isinstance(item, dict):
                    result.extend(format_value('item', item, indent + 1))
                else:
                    result.append(f"{prefix}  - {item}")
            return result
        elif isinstance(value, bool):
            return [f"{prefix}{display_key}: {'Yes' if value else 'No'}"]
        elif isinstance(value, (int, float)):
            # Format numbers nicely
            if isinstance(value, float):
                formatted = f"{value:.2f}" if abs(value) >= 0.01 else f"{value:.4f}"
            else:
                formatted = str(value)
            return [f"{prefix}{display_key}: {formatted}"]
        else:
            # String or other types
            return [f"{prefix}{display_key}: {value}"]

    # Process each top-level key
    for key, value in context_dict.items():
        lines.extend(format_value(key, value))

    return '\n'.join(lines) if lines else "No context available"
