"""
Chat Service - Orchestrates the chat flow with streaming responses.

Uses ContextManager for efficient context loading and handles
rate limiting, API calls, and SSE formatting.
"""

import anthropic
import json
import logging
import os
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


def get_api_key():
    """Get the Anthropic API key from environment variable or config file."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        try:
            # Try loading from config.json (same pattern as llm_recommendations_module)
            import json
            with open('config.json', 'r') as f:
                config = json.load(f)
                api_key = config.get('anthropic_api_key')
        except Exception as e:
            logger.warning(f"Could not load config.json: {e}")

    if not api_key:
        logger.error("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or add to config.json.")
        raise ValueError("Anthropic API key not found")

    return api_key.strip()


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
    api_key = get_api_key()
    client = anthropic.Anthropic(api_key=api_key)

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
