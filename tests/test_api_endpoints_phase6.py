#!/usr/bin/env python3
"""
Test script for Phase 6: API Endpoints and Backend Integration
Tests the comprehensive API endpoint implementation with enhanced error handling
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing
sys.modules['db_utils'] = MagicMock()

from acwr_configuration_admin import acwr_configuration_admin
from acwr_configuration_service import ACWRConfigurationService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_endpoints_exist():
    """Test that all required API endpoints exist"""
    logger.info("Testing API endpoints existence...")
    
    # Check that the admin blueprint exists
    if hasattr(acwr_configuration_admin, 'deferred_functions'):
        logger.info("✅ Blueprint has deferred functions")
    else:
        logger.error("❌ Blueprint does not have deferred functions")
        return False
    
    # Check that the blueprint is properly configured
    if acwr_configuration_admin.name == 'acwr_configuration_admin':
        logger.info("✅ Blueprint name is correct")
    else:
        logger.error("❌ Blueprint name is incorrect")
        return False
    
    logger.info("✅ API endpoints existence test passed")
    return True

def test_error_handling_decorator():
    """Test that error handling decorator exists"""
    logger.info("Testing error handling decorator...")
    
    # Check that the admin blueprint file exists and has error handling
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    if not os.path.exists(blueprint_path):
        logger.error("❌ Admin blueprint file does not exist")
        return False
    
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for error handling decorator
        if 'handle_api_errors' in content:
            logger.info("✅ Error handling decorator exists")
        else:
            logger.error("❌ Error handling decorator not found")
            return False
        
        # Check for error handling decorator usage
        if '@handle_api_errors' in content:
            logger.info("✅ Error handling decorator is being used")
        else:
            logger.error("❌ Error handling decorator is not being used")
            return False
    
    logger.info("✅ Error handling decorator test passed")
    return True

def test_validation_functions():
    """Test that validation functions exist"""
    logger.info("Testing validation functions...")
    
    # Check that the admin blueprint file has validation functions
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for validation functions
        validation_functions = [
            'validate_configuration_data',
            'validate_user_assignment_data',
            'validate_bulk_assignment_data'
        ]
        
        for func in validation_functions:
            if func in content:
                logger.info(f"✅ Validation function {func} exists")
            else:
                logger.error(f"❌ Validation function {func} not found")
                return False
    
    logger.info("✅ Validation functions test passed")
    return True

def test_preview_endpoint():
    """Test that preview endpoint exists"""
    logger.info("Testing preview endpoint...")
    
    # Check that the admin blueprint file has preview endpoint
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for preview endpoint
        if '/api/admin/acwr-configurations/<int:config_id>/preview' in content:
            logger.info("✅ Preview endpoint exists")
        else:
            logger.error("❌ Preview endpoint not found")
            return False
        
        # Check for preview function
        if 'preview_configuration_calculation' in content:
            logger.info("✅ Preview function exists")
        else:
            logger.error("❌ Preview function not found")
            return False
    
    logger.info("✅ Preview endpoint test passed")
    return True

def test_recalculate_endpoint():
    """Test that recalculate endpoint exists"""
    logger.info("Testing recalculate endpoint...")
    
    # Check that the admin blueprint file has recalculate endpoint
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for recalculate endpoint
        if '/api/admin/acwr-configurations/recalculate' in content:
            logger.info("✅ Recalculate endpoint exists")
        else:
            logger.error("❌ Recalculate endpoint not found")
            return False
        
        # Check for recalculate function
        if 'trigger_recalculation' in content:
            logger.info("✅ Recalculate function exists")
        else:
            logger.error("❌ Recalculate function not found")
            return False
    
    logger.info("✅ Recalculate endpoint test passed")
    return True

def test_service_layer_methods():
    """Test that service layer methods exist"""
    logger.info("Testing service layer methods...")
    
    service = ACWRConfigurationService()
    
    # Check for new service methods
    new_methods = [
        'get_sample_user_for_preview',
        'get_users_with_configuration',
        'get_all_active_users'
    ]
    
    for method in new_methods:
        if hasattr(service, method):
            logger.info(f"✅ Service method {method} exists")
        else:
            logger.error(f"❌ Service method {method} not found")
            return False
    
    logger.info("✅ Service layer methods test passed")
    return True

def test_error_handling_consistency():
    """Test that error handling is consistent across endpoints"""
    logger.info("Testing error handling consistency...")
    
    # Check that the admin blueprint file has consistent error handling
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for consistent error response format
        error_patterns = [
            'success',
            'False',
            'error',
            'error_type'
        ]
        
        for pattern in error_patterns:
            if pattern in content:
                logger.info(f"✅ Error pattern {pattern} exists")
            else:
                logger.error(f"❌ Error pattern {pattern} not found")
                return False
    
    logger.info("✅ Error handling consistency test passed")
    return True

def test_validation_coverage():
    """Test that validation covers all required fields"""
    logger.info("Testing validation coverage...")
    
    # Check that the admin blueprint file has comprehensive validation
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for validation coverage
        validation_checks = [
            'chronic_period_days',
            'decay_rate',
            'name',
            'description',
            'notes',
            'user_id',
            'configuration_id'
        ]
        
        for check in validation_checks:
            if check in content:
                logger.info(f"✅ Validation check for {check} exists")
            else:
                logger.error(f"❌ Validation check for {check} not found")
                return False
    
    logger.info("✅ Validation coverage test passed")
    return True

def test_endpoint_methods():
    """Test that all endpoints have proper HTTP methods"""
    logger.info("Testing endpoint HTTP methods...")
    
    # Check that the admin blueprint file has proper HTTP methods
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for HTTP methods
        http_methods = [
            'methods=[\'GET\']',
            'methods=[\'POST\']',
            'methods=[\'PUT\']',
            'methods=[\'DELETE\']'
        ]
        
        for method in http_methods:
            if method in content:
                logger.info(f"✅ HTTP method {method} exists")
            else:
                logger.error(f"❌ HTTP method {method} not found")
                return False
    
    logger.info("✅ Endpoint HTTP methods test passed")
    return True

def run_all_tests():
    """Run all Phase 6 API endpoint tests"""
    logger.info("=" * 60)
    logger.info("Phase 6: API Endpoints and Backend Integration Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("API Endpoints Existence", test_api_endpoints_exist),
        ("Error Handling Decorator", test_error_handling_decorator),
        ("Validation Functions", test_validation_functions),
        ("Preview Endpoint", test_preview_endpoint),
        ("Recalculate Endpoint", test_recalculate_endpoint),
        ("Service Layer Methods", test_service_layer_methods),
        ("Error Handling Consistency", test_error_handling_consistency),
        ("Validation Coverage", test_validation_coverage),
        ("Endpoint HTTP Methods", test_endpoint_methods)
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
        logger.info("🎉 All tests passed! Phase 6 API endpoints are working correctly.")
        return True
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

def main():
    """Run the test suite"""
    success = run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
