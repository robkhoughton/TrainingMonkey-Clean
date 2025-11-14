"""
Email Enforcement Module
Tracks email collection urgency and enforcement for users with synthetic emails.

CURRENT STATUS: Phase 1 - Passive tracking only (no user-facing changes)

NEXT STEPS: See EMAIL_ENFORCEMENT_ROADMAP.md for deployment timeline
  - Phase 2: Enable soft prompts (lines 67, 76)
  - Phase 3: Enable hard blocking (line 85)
  
CHECK BACK: 5-7 days after Phase 1 deployment to enable Phase 2
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
    
    if days <= 3:
        # Phase 1: Grace period - no prompts
        return {
            'level': 'none',
            'days_registered': days,
            'should_show_modal': False,
            'should_block_access': False,
            'message': f'Day {days} - grace period'
        }
    
    elif days <= 7:
        # Phase 2: Soft prompt - dismissible modal once per session
        return {
            'level': 'soft',
            'days_registered': days,
            'should_show_modal': False,  # Phase 1: disabled
            'should_block_access': False,
            'message': f'Day {days} - would show soft modal (disabled in Phase 1)'
        }
    
    elif days <= 14:
        # Phase 2: Medium prompt - persistent banner
        return {
            'level': 'medium',
            'days_registered': days,
            'should_show_modal': False,  # Phase 1: disabled
            'should_block_access': False,
            'message': f'Day {days} - would show persistent banner (disabled in Phase 1)'
        }
    
    else:
        # Phase 3: Hard block - must provide email
        return {
            'level': 'hard',
            'days_registered': days,
            'should_show_modal': False,  # Phase 1: disabled
            'should_block_access': False,  # Phase 1: disabled - no blocking
            'message': f'Day {days} - would block access (disabled in Phase 1)'
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


