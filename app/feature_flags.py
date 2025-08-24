# Feature flag system for safe rollout
FEATURE_FLAGS = {
    'settings_page_enabled': False,  # Start with OFF
    'hr_zone_recalculation': False,  # Start with OFF
    'enhanced_ai_context': False,  # Start with OFF
    'settings_validation_strict': True  # Start with ON for safety
}


def is_feature_enabled(feature_name, user_id=None):
    """Check if feature is enabled - allows gradual rollout"""
    base_enabled = FEATURE_FLAGS.get(feature_name, False)

    # Admin user (ID=1) gets early access for testing
    if user_id == 1:
        return True

    return base_enabled  # Default: new features OFF for production users


def enable_feature_for_user(feature_name, user_id):
    """Enable specific feature for specific user (for testing)"""
    # This will be expanded later for beta user management
    pass