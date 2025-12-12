"""
Email Verification Module

Provides email verification functionality for new user accounts.
Follows TrainingMonkey's modular architecture pattern.
"""

from .routes import email_verification_blueprint

__all__ = ['email_verification_blueprint']
