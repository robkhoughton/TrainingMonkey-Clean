"""
Email Enforcement Module
Tracks email collection urgency and enforcement for users with synthetic emails.

CURRENT STATUS: Phase 3 - Full enforcement active
  - Days 0-6: Grace period (no prompts)
  - Days 7+: Hard block — redirect to /collect-email
"""

from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def has_real_email(email):
    """Check if user has a real email address (not synthetic)."""
    if not email:
        return False
    return '@training-monkey.com' not in email.lower()


def get_days_since_registration(registration_date):
    """Calculate days since user registered."""
    if not registration_date:
        return 0
    
    # Handle both timezone-aware and naive datetimes
    if registration_date.tzinfo is None:
        reg_date = registration_date.replace(tzinfo=timezone.utc)
    else:
        reg_date = registration_date
    
    now = datetime.now(timezone.utc)
    delta = now - reg_date
    return delta.days


def get_email_urgency_level(user_data):
    """
    Determine email collection urgency level based on user data.
    
    Returns:
        dict with:
        - level: 'none', 'soft', 'medium', 'hard'
        - days_registered: int
        - should_show_modal: bool (Phase 2+)
        - should_block_access: bool (Phase 3)
        - message: str (for logging/display)
    """
    email = user_data.get('email', '')
    registration_date = user_data.get('registration_date')
    is_admin = user_data.get('is_admin', False)
    modal_dismissals = user_data.get('email_modal_dismissals', 0)
    
    # Bypass logic
    if is_admin:
        return {
            'level': 'none',
            'days_registered': 0,
            'should_show_modal': False,
            'should_block_access': False,
            'message': 'Admin - email enforcement bypassed'
        }
    
    if has_real_email(email):
        return {
            'level': 'none',
            'days_registered': get_days_since_registration(registration_date),
            'should_show_modal': False,
            'should_block_access': False,
            'message': 'User has real email'
        }
    
    # Calculate urgency for users with synthetic emails
    days = get_days_since_registration(registration_date)
    
    if days <= 6:
        # Grace period — no prompts for first week
        return {
            'level': 'none',
            'days_registered': days,
            'should_show_modal': False,
            'should_block_access': False,
            'message': f'Day {days} - grace period'
        }

    else:
        # Hard block — must provide real email
        return {
            'level': 'hard',
            'days_registered': days,
            'should_show_modal': False,
            'should_block_access': True,
            'message': f'Day {days} - blocking access until email provided'
        }


def log_email_enforcement_status(user_id, urgency_data):
    """
    Log email enforcement status for monitoring.
    Phase 1: Pure tracking - helps us understand impact before enabling.
    """
    if urgency_data['level'] != 'none':
        logger.info(
            f"[EMAIL_TRACKING] User {user_id} | "
            f"Level: {urgency_data['level']} | "
            f"Days: {urgency_data['days_registered']} | "
            f"Message: {urgency_data['message']}"
        )


