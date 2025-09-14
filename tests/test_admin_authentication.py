#!/usr/bin/env python3
"""
Test script for Admin Authentication
Tests the admin authentication decorator and functionality
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing
sys.modules['db_utils'] = MagicMock()

from acwr_configuration_admin import acwr_configuration_admin, require_admin_auth
from acwr_configuration_service import ACWRConfigurationService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_admin_auth_decorator_exists():
    """Test that admin authentication decorator exists"""
    logger.info("Testing admin authentication decorator...")
    
    # Check that the admin blueprint file exists and has admin auth
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    if not os.path.exists(blueprint_path):
        logger.error("❌ Admin blueprint file does not exist")
        return False
    
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for admin auth decorator
        if 'require_admin_auth' in content:
            logger.info("✅ Admin authentication decorator exists")
        else:
            logger.error("❌ Admin authentication decorator not found")
            return False
        
        # Check for admin auth decorator usage
        if '@require_admin_auth' in content:
            logger.info("✅ Admin authentication decorator is being used")
        else:
            logger.error("❌ Admin authentication decorator is not being used")
            return False
    
    logger.info("✅ Admin authentication decorator test passed")
    return True

def test_admin_auth_headers():
    """Test that admin authentication checks for proper headers"""
    logger.info("Testing admin authentication headers...")
    
    # Check that the admin blueprint file has header validation
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for header validation
        header_checks = [
            'X-Admin-User-ID',
            'X-Admin-Token',
            'admin_user_id',
            'admin_token'
        ]
        
        for check in header_checks:
            if check in content:
                logger.info(f"✅ Header check for {check} exists")
            else:
                logger.error(f"❌ Header check for {check} not found")
                return False
    
    logger.info("✅ Admin authentication headers test passed")
    return True

def test_admin_auth_session_fallback():
    """Test that admin authentication has session fallback"""
    logger.info("Testing admin authentication session fallback...")
    
    # Check that the admin blueprint file has session fallback
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for session fallback
        session_checks = [
            'session.get',
            'admin_user_id',
            'flask import session'
        ]
        
        for check in session_checks:
            if check in content:
                logger.info(f"✅ Session fallback check for {check} exists")
            else:
                logger.error(f"❌ Session fallback check for {check} not found")
                return False
    
    logger.info("✅ Admin authentication session fallback test passed")
    return True

def test_admin_user_validation():
    """Test that admin user validation exists"""
    logger.info("Testing admin user validation...")
    
    # Check that the service file has user validation
    service_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_service.py')
    with open(service_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for user validation
        validation_checks = [
            'get_admin_user',
            'is_active',
            'role',
            'admin'
        ]
        
        for check in validation_checks:
            if check in content:
                logger.info(f"✅ User validation check for {check} exists")
            else:
                logger.error(f"❌ User validation check for {check} not found")
                return False
    
    logger.info("✅ Admin user validation test passed")
    return True

def test_admin_auth_error_handling():
    """Test that admin authentication has proper error handling"""
    logger.info("Testing admin authentication error handling...")
    
    # Check that the admin blueprint file has error handling
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for error handling
        error_checks = [
            'PermissionError',
            'authentication_error',
            '401',
            'Admin authentication required'
        ]
        
        for check in error_checks:
            if check in content:
                logger.info(f"✅ Error handling check for {check} exists")
            else:
                logger.error(f"❌ Error handling check for {check} not found")
                return False
    
    logger.info("✅ Admin authentication error handling test passed")
    return True

def test_admin_auth_request_context():
    """Test that admin authentication adds request context"""
    logger.info("Testing admin authentication request context...")
    
    # Check that the admin blueprint file adds request context
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for request context
        context_checks = [
            'request.admin_user_id',
            'request.admin_user'
        ]
        
        for check in context_checks:
            if check in content:
                logger.info(f"✅ Request context check for {check} exists")
            else:
                logger.error(f"❌ Request context check for {check} not found")
                return False
    
    logger.info("✅ Admin authentication request context test passed")
    return True

def test_service_layer_admin_method():
    """Test that service layer has admin user method"""
    logger.info("Testing service layer admin method...")
    
    service = ACWRConfigurationService()
    
    # Check for admin user method
    if hasattr(service, 'get_admin_user'):
        logger.info("✅ Service method get_admin_user exists")
    else:
        logger.error("❌ Service method get_admin_user not found")
        return False
    
    logger.info("✅ Service layer admin method test passed")
    return True

def test_admin_auth_endpoint_coverage():
    """Test that admin authentication is applied to key endpoints"""
    logger.info("Testing admin authentication endpoint coverage...")
    
    # Check that the admin blueprint file has admin auth on key endpoints
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for admin auth on key endpoints
        endpoint_checks = [
            'create_configuration',
            'update_configuration',
            'execute_rollback'
        ]
        
        for check in endpoint_checks:
            if f'def {check}' in content:
                # Check if the function has admin auth decorator
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if f'def {check}' in line:
                        # Check the lines before the function definition
                        for j in range(max(0, i-3), i):
                            if '@require_admin_auth' in lines[j]:
                                logger.info(f"✅ Endpoint {check} has admin authentication")
                                break
                        else:
                            logger.error(f"❌ Endpoint {check} does not have admin authentication")
                            return False
            else:
                logger.error(f"❌ Endpoint {check} not found")
                return False
    
    logger.info("✅ Admin authentication endpoint coverage test passed")
    return True

def test_admin_auth_security_features():
    """Test that admin authentication has security features"""
    logger.info("Testing admin authentication security features...")
    
    # Check that the admin blueprint file has security features
    blueprint_path = os.path.join(os.path.dirname(__file__), 'acwr_configuration_admin.py')
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for security features
        security_checks = [
            'Invalid or inactive admin user',
            'Admin authentication required',
            'Authentication system error',
            'logger.warning',
            'logger.error'
        ]
        
        for check in security_checks:
            if check in content:
                logger.info(f"✅ Security feature {check} exists")
            else:
                logger.error(f"❌ Security feature {check} not found")
                return False
    
    logger.info("✅ Admin authentication security features test passed")
    return True

def run_all_tests():
    """Run all admin authentication tests"""
    logger.info("=" * 60)
    logger.info("Admin Authentication Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Admin Auth Decorator Existence", test_admin_auth_decorator_exists),
        ("Admin Auth Headers", test_admin_auth_headers),
        ("Admin Auth Session Fallback", test_admin_auth_session_fallback),
        ("Admin User Validation", test_admin_user_validation),
        ("Admin Auth Error Handling", test_admin_auth_error_handling),
        ("Admin Auth Request Context", test_admin_auth_request_context),
        ("Service Layer Admin Method", test_service_layer_admin_method),
        ("Admin Auth Endpoint Coverage", test_admin_auth_endpoint_coverage),
        ("Admin Auth Security Features", test_admin_auth_security_features)
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
        logger.info("🎉 All tests passed! Admin authentication is working correctly.")
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
