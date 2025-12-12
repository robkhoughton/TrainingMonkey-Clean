"""
Rate limiting for chat feature.

Tracks daily token usage and message counts per user to enforce budget limits.
"""

import logging
from typing import Dict
from db_utils import get_db_connection
from timezone_utils import get_user_current_date

logger = logging.getLogger(__name__)

# Daily limits per user
DAILY_INPUT_TOKEN_LIMIT = 600000
DAILY_OUTPUT_TOKEN_LIMIT = 150000
DAILY_MESSAGE_LIMIT = 100


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
    - Use user's timezone for "today"
    """
    try:
        # Get today's date in user's timezone
        today = str(get_user_current_date(user_id))

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT input_tokens, output_tokens, message_count
                    FROM chat_usage
                    WHERE user_id = %s AND date = %s
                """, (user_id, today))

                row = cur.fetchone()

                if not row:
                    # No usage yet today
                    return {
                        'allowed': True,
                        'remaining_messages': DAILY_MESSAGE_LIMIT,
                        'input_tokens_used': 0,
                        'output_tokens_used': 0,
                        'message_count': 0,
                        'limit': DAILY_MESSAGE_LIMIT
                    }

                input_tokens = row['input_tokens'] or 0
                output_tokens = row['output_tokens'] or 0
                message_count = row['message_count'] or 0

                # Check all limits
                message_limit_ok = message_count < DAILY_MESSAGE_LIMIT
                input_limit_ok = input_tokens < DAILY_INPUT_TOKEN_LIMIT
                output_limit_ok = output_tokens < DAILY_OUTPUT_TOKEN_LIMIT

                allowed = message_limit_ok and input_limit_ok and output_limit_ok

                return {
                    'allowed': allowed,
                    'remaining_messages': max(0, DAILY_MESSAGE_LIMIT - message_count),
                    'input_tokens_used': input_tokens,
                    'output_tokens_used': output_tokens,
                    'message_count': message_count,
                    'limit': DAILY_MESSAGE_LIMIT
                }

    except Exception as e:
        logger.error(f"Error checking usage for user {user_id}: {e}")
        # On error, allow the request (fail open)
        return {
            'allowed': True,
            'remaining_messages': DAILY_MESSAGE_LIMIT,
            'input_tokens_used': 0,
            'output_tokens_used': 0,
            'message_count': 0,
            'limit': DAILY_MESSAGE_LIMIT
        }


def record_usage(user_id: int, input_tokens: int, output_tokens: int) -> None:
    """
    Record token usage after a chat message.

    Implementation notes:
    - UPSERT into chat_usage table
    - Increment input_tokens, output_tokens, message_count
    - Update updated_at timestamp
    """
    try:
        # Get today's date in user's timezone
        today = str(get_user_current_date(user_id))

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # UPSERT: Insert or update on conflict
                cur.execute("""
                    INSERT INTO chat_usage (user_id, date, input_tokens, output_tokens, message_count)
                    VALUES (%s, %s, %s, %s, 1)
                    ON CONFLICT (user_id, date) DO UPDATE
                    SET input_tokens = chat_usage.input_tokens + %s,
                        output_tokens = chat_usage.output_tokens + %s,
                        message_count = chat_usage.message_count + 1,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, today, input_tokens, output_tokens, input_tokens, output_tokens))

                conn.commit()
                logger.info(f"Recorded usage for user {user_id}: +{input_tokens} input, +{output_tokens} output tokens")

    except Exception as e:
        logger.error(f"Error recording usage for user {user_id}: {e}")
        # Don't raise - usage tracking failures shouldn't break the chat


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
    try:
        usage = check_usage(user_id)

        messages_used = usage['message_count']
        messages_remaining = usage['remaining_messages']
        percentage_used = (messages_used / DAILY_MESSAGE_LIMIT) * 100 if DAILY_MESSAGE_LIMIT > 0 else 0

        return {
            'messages_used': messages_used,
            'messages_remaining': messages_remaining,
            'percentage_used': round(percentage_used, 1)
        }

    except Exception as e:
        logger.error(f"Error getting daily stats for user {user_id}: {e}")
        return {
            'messages_used': 0,
            'messages_remaining': DAILY_MESSAGE_LIMIT,
            'percentage_used': 0.0
        }


def estimate_tokens(text: str) -> int:
    """
    Rough token estimation (chars / 4 is a reasonable approximation).
    Used for pre-flight checks before API calls.
    """
    return len(text) // 4
