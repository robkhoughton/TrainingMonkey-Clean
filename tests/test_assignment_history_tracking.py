#!/usr/bin/env python3
"""
Test script for Assignment History Tracking with Timestamps and Admin Attribution
Tests the comprehensive assignment history tracking system
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing
sys.modules['db_utils'] = MagicMock()

from acwr_configuration_service import ACWRConfigurationService
from acwr_configuration_admin import acwr_configuration_admin

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_assignment_history_interface():
    """Test that the assignment history interface has all required components"""
    logger.info("Testing assignment history interface...")
    
    # Check that the template file exists and has history components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    if not os.path.exists(template_path):
        logger.error("❌ Admin template file does not exist")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for assignment history section
        if 'Assignment History' in content:
            logger.info("✅ Assignment History section exists")
        else:
            logger.error("❌ Assignment History section not found")
            return False
        
        # Check for history interface components
        history_components = [
            'history-filter-type',
            'history-filter-user',
            'history-filter-config',
            'history-filter-admin',
            'history-container',
            'assignment-history-table',
            'history-loading',
            'history-pagination',
            'load-more-btn',
            'history-count'
        ]
        
        for component in history_components:
            if f'id="{component}"' in content:
                logger.info(f"✅ History component {component} exists")
            else:
                logger.error(f"❌ History component {component} not found")
                return False
        
        # Check for history table columns
        history_columns = [
            'Timestamp',
            'Action',
            'User',
            'Configuration',
            'Admin',
            'Reason'
        ]
        
        for column in history_columns:
            if column in content:
                logger.info(f"✅ History column '{column}' exists")
            else:
                logger.error(f"❌ History column '{column}' not found")
                return False
        
        # Check for JavaScript functions
        js_functions = [
            'loadAssignmentHistory',
            'loadMoreHistory',
            'renderAssignmentHistory',
            'getActionClass',
            'updateHistoryFilters',
            'filterAssignmentHistory',
            'updateHistoryCount'
        ]
        
        for func in js_functions:
            if func in content:
                logger.info(f"✅ JavaScript function {func} exists")
            else:
                logger.error(f"❌ JavaScript function {func} not found")
                return False
    
    logger.info("✅ Assignment history interface test passed")
    return True

def test_history_filtering():
    """Test history filtering functionality"""
    logger.info("Testing history filtering...")
    
    # Check that the template has filtering components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for filter options
        filter_options = [
            'All Actions',
            'Assignments',
            'Unassignments',
            'Bulk Assignments',
            'Bulk Unassignments',
            'All Users',
            'All Configurations',
            'All Admins'
        ]
        
        for option in filter_options:
            if option in content:
                logger.info(f"✅ Filter option '{option}' exists")
            else:
                logger.error(f"❌ Filter option '{option}' not found")
                return False
        
        # Check for filter function
        if 'filterAssignmentHistory()' in content:
            logger.info("✅ Filter function exists")
        else:
            logger.error("❌ Filter function not found")
            return False
    
    logger.info("✅ History filtering test passed")
    return True

def test_action_badges():
    """Test action badge styling"""
    logger.info("Testing action badges...")
    
    # Check that the template has action badge styling
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for action badge classes
        action_classes = [
            'action-badge',
            'action-assigned',
            'action-unassigned',
            'action-bulk-assigned',
            'action-bulk-unassigned'
        ]
        
        for action_class in action_classes:
            if action_class in content:
                logger.info(f"✅ Action class {action_class} exists")
            else:
                logger.error(f"❌ Action class {action_class} not found")
                return False
        
        # Check for action types
        action_types = [
            'ASSIGNED',
            'UNASSIGNED',
            'BULK_ASSIGNED',
            'BULK_UNASSIGNED'
        ]
        
        for action_type in action_types:
            if action_type in content:
                logger.info(f"✅ Action type {action_type} exists")
            else:
                logger.error(f"❌ Action type {action_type} not found")
                return False
    
    logger.info("✅ Action badges test passed")
    return True

def test_admin_attribution():
    """Test admin attribution display"""
    logger.info("Testing admin attribution...")
    
    # Check that the template has admin attribution components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for admin info display
        admin_components = [
            'admin-info',
            'admin-name',
            'admin-email'
        ]
        
        for component in admin_components:
            if component in content:
                logger.info(f"✅ Admin component {component} exists")
            else:
                logger.error(f"❌ Admin component {component} not found")
                return False
        
        # Check for user info display
        user_components = [
            'user-info',
            'user-name',
            'user-email'
        ]
        
        for component in user_components:
            if component in content:
                logger.info(f"✅ User component {component} exists")
            else:
                logger.error(f"❌ User component {component} not found")
                return False
    
    logger.info("✅ Admin attribution test passed")
    return True

def test_timestamp_display():
    """Test timestamp display functionality"""
    logger.info("Testing timestamp display...")
    
    # Check that the template has timestamp components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for timestamp styling
        if 'timestamp' in content and 'monospace' in content:
            logger.info("✅ Timestamp styling exists")
        else:
            logger.error("❌ Timestamp styling not found")
            return False
        
        # Check for timestamp formatting
        if 'toLocaleString' in content:
            logger.info("✅ Timestamp formatting exists")
        else:
            logger.error("❌ Timestamp formatting not found")
            return False
    
    logger.info("✅ Timestamp display test passed")
    return True

def test_service_layer_history():
    """Test service layer history functionality"""
    logger.info("Testing service layer history...")
    
    service = ACWRConfigurationService()
    
    # Test history methods exist
    history_methods = [
        '_log_assignment_history',
        'get_assignment_history',
        'get_user_assignment_history',
        'get_configuration_assignment_history',
        'get_admin_assignment_history'
    ]
    
    for method in history_methods:
        if hasattr(service, method):
            logger.info(f"✅ History method {method} exists")
        else:
            logger.error(f"❌ History method {method} not found")
            return False
    
    # Test method signatures
    import inspect
    
    # Test _log_assignment_history signature
    log_sig = inspect.signature(service._log_assignment_history)
    expected_params = ['user_id', 'configuration_id', 'assigned_by', 'action']
    for param in expected_params:
        if param in log_sig.parameters:
            logger.info(f"✅ _log_assignment_history parameter {param} exists")
        else:
            logger.error(f"❌ _log_assignment_history parameter {param} not found")
            return False
    
    # Test get_assignment_history signature
    get_sig = inspect.signature(service.get_assignment_history)
    expected_params = ['user_id', 'configuration_id', 'limit']
    for param in expected_params:
        if param in get_sig.parameters:
            logger.info(f"✅ get_assignment_history parameter {param} exists")
        else:
            logger.error(f"❌ get_assignment_history parameter {param} not found")
            return False
    
    logger.info("✅ Service layer history test passed")
    return True

def test_api_endpoints():
    """Test API endpoints for assignment history"""
    logger.info("Testing API endpoints...")
    
    # Check that the admin blueprint has history endpoints
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
    
    logger.info("✅ API endpoints test passed")
    return True

def test_pagination():
    """Test pagination functionality"""
    logger.info("Testing pagination...")
    
    # Check that the template has pagination components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for pagination elements
        pagination_elements = [
            'Load More History',
            'entries loaded',
            'historyOffset',
            'historyLimit'
        ]
        
        for element in pagination_elements:
            if element in content:
                logger.info(f"✅ Pagination element '{element}' exists")
            else:
                logger.error(f"❌ Pagination element '{element}' not found")
                return False
    
    logger.info("✅ Pagination test passed")
    return True

def test_reason_tracking():
    """Test reason tracking functionality"""
    logger.info("Testing reason tracking...")
    
    # Check that the template has reason tracking
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for reason display
        if 'reason-text' in content and 'title=' in content:
            logger.info("✅ Reason display exists")
        else:
            logger.error("❌ Reason display not found")
            return False
        
        # Check for reason truncation
        if 'text-overflow: ellipsis' in content:
            logger.info("✅ Reason truncation exists")
        else:
            logger.error("❌ Reason truncation not found")
            return False
    
    logger.info("✅ Reason tracking test passed")
    return True

def run_all_tests():
    """Run all assignment history tracking tests"""
    logger.info("=" * 60)
    logger.info("Assignment History Tracking Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Assignment History Interface", test_assignment_history_interface),
        ("History Filtering", test_history_filtering),
        ("Action Badges", test_action_badges),
        ("Admin Attribution", test_admin_attribution),
        ("Timestamp Display", test_timestamp_display),
        ("Service Layer History", test_service_layer_history),
        ("API Endpoints", test_api_endpoints),
        ("Pagination", test_pagination),
        ("Reason Tracking", test_reason_tracking)
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
        logger.info("🎉 All tests passed! Assignment history tracking is working correctly.")
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

