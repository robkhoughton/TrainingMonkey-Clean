"""
Chat module - Streaming chatbot for the Coach page.

Exports the chat_blueprint for registration with the Flask app.
"""

from .routes import chat_blueprint

__all__ = ['chat_blueprint']
