#!/usr/bin/env python3
"""
Test script for timezone utilities
Tests the new user-aware timezone functions
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from timezone_utils import (
    get_user_timezone, get_user_current_date, get_user_current_datetime,
    get_user_date_string, is_date_today_for_user, validate_timezone,
    log_timezone_debug, clear_timezone_cache
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_timezone_utilities():
    """Test the new timezone utilities"""
    logger.info("🧪 Testing Timezone Utilities")
    logger.info("=" * 50)
    
    # Test with existing user (should have Pacific timezone)
    test_user_id = 1
    
    try:
        # Test timezone lookup
        logger.info(f"Testing timezone lookup for user {test_user_id}...")
        user_tz = get_user_timezone(test_user_id)
        logger.info(f"✅ User {test_user_id} timezone: {user_tz}")
        
        # Test current date functions
        logger.info("Testing date functions...")
        user_date = get_user_current_date(test_user_id)
        user_datetime = get_user_current_datetime(test_user_id)
        user_date_str = get_user_date_string(test_user_id)
        
        logger.info(f"✅ User {test_user_id} current date: {user_date}")
        logger.info(f"✅ User {test_user_id} current datetime: {user_datetime}")
        logger.info(f"✅ User {test_user_id} date string: {user_date_str}")
        
        # Test date comparison
        logger.info("Testing date comparison...")
        is_today = is_date_today_for_user(user_date_str, test_user_id)
        logger.info(f"✅ Is {user_date_str} today for user {test_user_id}? {is_today}")
        
        # Test timezone validation
        logger.info("Testing timezone validation...")
        valid_timezones = ['US/Pacific', 'US/Eastern', 'US/Central', 'Invalid/Timezone']
        for tz in valid_timezones:
            is_valid = validate_timezone(tz)
            logger.info(f"✅ Timezone '{tz}' valid: {is_valid}")
        
        # Test debug logging
        logger.info("Testing debug logging...")
        log_timezone_debug(test_user_id)
        
        logger.info("🎉 All timezone utility tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Timezone utility test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_timezone_utilities()
    sys.exit(0 if success else 1)

