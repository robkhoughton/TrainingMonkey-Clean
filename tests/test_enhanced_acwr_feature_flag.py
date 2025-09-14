#!/usr/bin/env python3
"""
Test script for Enhanced ACWR feature flag functionality
Tests the feature flag system without requiring database connection
"""

import sys
import os
import logging

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.feature_flags import is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_acwr_feature_flag():
    """Test the enhanced ACWR feature flag functionality"""
    logger.info("Testing Enhanced ACWR feature flag...")
    
    # Test admin user (user_id=1) - should have access
    admin_access = is_feature_enabled('enhanced_acwr_calculation', user_id=1)
    assert admin_access == True, "Admin user should have access to enhanced ACWR calculation"
    logger.info("✅ Admin user (user_id=1) has access to enhanced ACWR calculation")
    
    # Test beta user (user_id=2) - should have access
    beta_user_access = is_feature_enabled('enhanced_acwr_calculation', user_id=2)
    assert beta_user_access == True, "Beta user should have access to enhanced ACWR calculation"
    logger.info("✅ Beta user (user_id=2) has access to enhanced ACWR calculation")
    
    # Test beta user (user_id=3) - should have access
    beta_user2_access = is_feature_enabled('enhanced_acwr_calculation', user_id=3)
    assert beta_user2_access == True, "Beta user should have access to enhanced ACWR calculation"
    logger.info("✅ Beta user (user_id=3) has access to enhanced ACWR calculation")
    
    # Test regular user (user_id=4) - should NOT have access
    regular_user_access = is_feature_enabled('enhanced_acwr_calculation', user_id=4)
    assert regular_user_access == False, "Regular user should NOT have access to enhanced ACWR calculation"
    logger.info("✅ Regular user (user_id=4) does NOT have access to enhanced ACWR calculation")
    
    # Test with no user_id - should default to False
    no_user_access = is_feature_enabled('enhanced_acwr_calculation')
    assert no_user_access == False, "No user_id should default to False"
    logger.info("✅ No user_id defaults to False for enhanced ACWR calculation")
    
    logger.info("🎉 All Enhanced ACWR feature flag tests passed!")
    return True

def test_feature_flag_integration():
    """Test that the feature flag integrates properly with existing system"""
    logger.info("Testing feature flag integration...")
    
    # Test that the feature flag is properly registered
    from utils.feature_flags import is_feature_enabled
    
    # Test with admin user to ensure it works
    result = is_feature_enabled('enhanced_acwr_calculation', user_id=1)
    assert isinstance(result, bool), "Feature flag should return a boolean"
    
    logger.info("✅ Feature flag integration test passed")
    return True

def main():
    """Run all feature flag tests"""
    logger.info("=" * 60)
    logger.info("Enhanced ACWR Feature Flag Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Enhanced ACWR Feature Flag", test_enhanced_acwr_feature_flag),
        ("Feature Flag Integration", test_feature_flag_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} PASSED")
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"Test Results: {passed}/{total} tests passed")
    logger.info("=" * 60)
    
    if passed == total:
        logger.info("🎉 All tests passed! Enhanced ACWR feature flag is working correctly.")
        return True
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

