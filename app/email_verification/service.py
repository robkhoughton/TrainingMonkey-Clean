"""
Email Verification Service - Business Logic Layer

Provides high-level business logic for email verification, following
TrainingMonkey's service pattern (similar to ACWRConfigurationService).
"""

import logging
from typing import Tuple, Optional
from .core import send_verification_email, verify_token
from db_utils import execute_query

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """
    Service for managing email verification business logic.
    Follows TrainingMonkey service pattern - stateless methods with clear responsibilities.
    """

    @staticmethod
    def is_verified(user_id: int) -> bool:
        """
        Check if user's email is verified.

        Args:
            user_id: User ID

        Returns:
            bool: True if email is verified, False otherwise
        """
        try:
            result = execute_query(
                "SELECT email_verified FROM user_settings WHERE id = %s",
                (user_id,),
                fetch=True
            )
            return result[0].get('email_verified', False) if result else False
        except Exception as e:
            logger.error(f"Error checking verification status for user {user_id}: {e}")
            return False

    @staticmethod
    def needs_verification(user_id: int) -> bool:
        """
        Check if user needs email verification (skips synthetic emails).

        Args:
            user_id: User ID

        Returns:
            bool: True if user needs to verify email, False otherwise
        """
        try:
            result = execute_query(
                "SELECT email, email_verified FROM user_settings WHERE id = %s",
                (user_id,),
                fetch=True
            )
            if not result:
                return True

            email = result[0].get('email', '')
            verified = result[0].get('email_verified', False)

            # Skip verification for synthetic emails
            if '@training-monkey.com' in email:
                return False

            return not verified
        except Exception as e:
            logger.error(f"Error checking needs_verification for user {user_id}: {e}")
            return False

    @staticmethod
    def get_user_email(user_id: int) -> Optional[str]:
        """
        Get user's email address.

        Args:
            user_id: User ID

        Returns:
            Optional[str]: Email address or None if not found
        """
        try:
            result = execute_query(
                "SELECT email FROM user_settings WHERE id = %s",
                (user_id,),
                fetch=True
            )
            return result[0].get('email') if result else None
        except Exception as e:
            logger.error(f"Error getting email for user {user_id}: {e}")
            return None

    @staticmethod
    def send_verification(user_id: int, email: str, base_url: str) -> Tuple[bool, Optional[str]]:
        """
        Send verification email (wrapper with logging).

        Args:
            user_id: User ID
            email: Email address to send to
            base_url: Base URL for verification link

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        logger.info(f"Sending verification email to user {user_id} ({email})")
        return send_verification_email(user_id, email, base_url)

    @staticmethod
    def verify_email_token(token: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Verify email token (wrapper with logging).

        Args:
            token: Verification token from email link

        Returns:
            Tuple[bool, Optional[int], Optional[str]]: (success, user_id, error_message)
        """
        success, user_id, error = verify_token(token)
        if success:
            logger.info(f"Email verified successfully for user {user_id}")
        else:
            logger.warning(f"Email verification failed: {error}")
        return success, user_id, error
