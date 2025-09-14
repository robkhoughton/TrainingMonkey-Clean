#!/usr/bin/env python3
"""
Feature flags utility for Training Monkey™
Handles gradual feature rollout and beta user access
"""

import logging

logger = logging.getLogger(__name__)

# Import monitoring functions
try:
    from acwr_feature_flag_monitor import log_acwr_feature_access, log_acwr_feature_error
except ImportError:
    # Fallback if monitoring is not available
    def log_acwr_feature_access(feature_name, user_id, granted, details=None):
        pass
    def log_acwr_feature_error(feature_name, user_id, error_message, details=None):
        pass


def is_feature_enabled(feature_name, user_id=None):
    """
    Check if feature is enabled - allows gradual rollout to beta users

    PHASE 1 ROLLOUT PLAN:
    - Rob (user_id=1): Admin access (already enabled)
    - tballaine (user_id=2): Beta user #1
    - iz.houghton (user_id=3): Beta user #2

    Args:
        feature_name (str): Name of the feature to check
        user_id (int): User ID to check feature access for

    Returns:
        bool: True if feature is enabled for the user, False otherwise
    """

    # Feature flag configuration
    feature_flags = {
        'settings_page_enabled': False,  # Default OFF for general users
        'hr_zone_recalculation': False,  # Default OFF
        'enhanced_ai_context': False,  # Default OFF
        'settings_validation_strict': True,  # Default ON for safety
        'enhanced_trimp_calculation': False,  # Default OFF - uses heart rate stream data
        'enhanced_acwr_calculation': False  # Default OFF - uses exponential decay weighting
    }

    # Get base enabled state
    base_enabled = feature_flags.get(feature_name, False)

    # Special handling for Settings page rollout
    if feature_name == 'settings_page_enabled':

        # PHASE 1: Admin + Beta Users (Rob, tballaine, iz.houghton)
        beta_user_ids = [1, 2, 3]  # Rob (admin), tballaine, iz.houghton

        if user_id in beta_user_ids:
            logger.info(f"🎉 Settings page access granted to user {user_id} (beta rollout)")
            return True

        # All other users: Settings page disabled
        logger.info(f"⏳ Settings page access denied to user {user_id} (not in beta rollout)")
        return False

    # Special handling for Enhanced TRIMP Calculation rollout
    if feature_name == 'enhanced_trimp_calculation':

        # PHASE 1: Admin + Beta Users (Rob, tballaine, iz.houghton)
        beta_user_ids = [1, 2, 3]  # Rob (admin), tballaine, iz.houghton

        if user_id in beta_user_ids:
            logger.info(f"🎉 Enhanced TRIMP calculation access granted to user {user_id} (beta rollout)")
            return True

        # All other users: Enhanced TRIMP calculation disabled (uses average HR method)
        logger.info(f"⏳ Enhanced TRIMP calculation access denied to user {user_id} (not in beta rollout)")
        return False

    # Special handling for Enhanced ACWR Calculation rollout
    if feature_name == 'enhanced_acwr_calculation':

        # PHASE 1: Admin + Beta Users (Rob, tballaine, iz.houghton)
        beta_user_ids = [1, 2, 3]  # Rob (admin), tballaine, iz.houghton

        if user_id in beta_user_ids:
            logger.info(f"🎉 Enhanced ACWR calculation access granted to user {user_id} (beta rollout)")
            # Log access for monitoring
            log_acwr_feature_access('enhanced_acwr_calculation', user_id, True, {
                'rollout_phase': 'beta',
                'user_type': 'beta_user' if user_id != 1 else 'admin'
            })
            return True

        # All other users: Enhanced ACWR calculation disabled (uses standard 28-day calculation)
        logger.info(f"⏳ Enhanced ACWR calculation access denied to user {user_id} (not in beta rollout)")
        # Log access denial for monitoring
        log_acwr_feature_access('enhanced_acwr_calculation', user_id, False, {
            'rollout_phase': 'beta',
            'user_type': 'regular_user'
        })
        return False

    # For other features, check admin access first
    if user_id == 1:  # Rob's admin account gets early access to all new features
        logger.info(f"🔧 Admin early access granted for {feature_name} to user {user_id}")
        return True

    # Return base flag state for non-admin users
    return base_enabled
