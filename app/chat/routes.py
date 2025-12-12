"""
Flask routes for chat API.

Provides endpoints for:
- Chat streaming (/api/chat)
- Usage statistics (/api/chat/usage)
- Universe intro messages (/api/chat/intro/<universe>)
"""

from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
import json

from .service import stream_chat_response
from .rate_limiter import get_daily_stats
from .prompts import get_universe_intro

chat_blueprint = Blueprint('chat', __name__)

ALLOWED_UNIVERSES = {'autopsy', 'training_plan', 'todays_workout', 'progress', 'general'}


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
    """
    # Validate request
    if not request.json:
        return jsonify({'error': 'Request must be JSON'}), 400

    universe = request.json.get('universe')
    message = request.json.get('message')
    conversation = request.json.get('conversation', [])

    # Validate universe
    if not universe or universe not in ALLOWED_UNIVERSES:
        return jsonify({'error': f'Invalid universe. Must be one of: {", ".join(ALLOWED_UNIVERSES)}'}), 400

    # Validate message
    if not message or not isinstance(message, str) or not message.strip():
        return jsonify({'error': 'Message must be a non-empty string'}), 400

    # Validate conversation format
    if not isinstance(conversation, list):
        return jsonify({'error': 'Conversation must be a list'}), 400

    # Get user ID
    user_id = current_user.id

    # Stream response
    def generate():
        try:
            for chunk in stream_chat_response(user_id, universe, message, conversation):
                yield chunk
        except Exception as e:
            # Log error and send error event
            import logging
            logging.error(f"Error in chat stream: {e}")
            error_event = f"data: {json.dumps({'type': 'error', 'message': 'Stream error occurred'})}\n\n"
            yield error_event

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # Disable nginx buffering
        }
    )


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
    if universe not in ALLOWED_UNIVERSES:
        return jsonify({'error': 'Invalid universe'}), 400

    intro_text = get_universe_intro(universe)
    return jsonify({'intro': intro_text})
