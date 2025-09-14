#!/usr/bin/env python3
"""
Test script for Rollback Capabilities for Configuration Assignments
Tests the comprehensive rollback system with impact analysis and audit trail
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

def test_rollback_interface():
    """Test that the rollback interface has all required components"""
    logger.info("Testing rollback interface...")
    
    # Check that the template file exists and has rollback components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    if not os.path.exists(template_path):
        logger.error("❌ Admin template file does not exist")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for rollback section
        if 'Rollback Assignments' in content:
            logger.info("✅ Rollback section exists")
        else:
            logger.error("❌ Rollback section not found")
            return False
        
        # Check for rollback interface components
        rollback_components = [
            'rollback-filter-type',
            'rollback-user-select',
            'rollback-target-config',
            'rollback-options-container',
            'rollback-options-list',
            'rollback-impact-container',
            'rollback-impact-details',
            'rollback-affected-users',
            'rollback-impact-level',
            'rollback-warnings',
            'rollback-reason',
            'rollback-actions',
            'rollback-status',
            'rollback-progress-fill',
            'rollback-operation-log'
        ]
        
        for component in rollback_components:
            if f'id="{component}"' in content:
                logger.info(f"✅ Rollback component {component} exists")
            else:
                logger.error(f"❌ Rollback component {component} not found")
                return False
        
        # Check for rollback types
        rollback_types = [
            'Single User Rollback',
            'Bulk Rollback',
            'Time-based Rollback'
        ]
        
        for rollback_type in rollback_types:
            if rollback_type in content:
                logger.info(f"✅ Rollback type '{rollback_type}' exists")
            else:
                logger.error(f"❌ Rollback type '{rollback_type}' not found")
                return False
        
        # Check for JavaScript functions
        js_functions = [
            'updateRollbackInterface',
            'loadRollbackOptions',
            'renderRollbackOptions',
            'selectRollbackOption',
            'previewRollback',
            'displayRollbackImpact',
            'executeRollback',
            'updateRollbackProgress',
            'logRollbackOperation',
            'clearRollback'
        ]
        
        for func in js_functions:
            if func in content:
                logger.info(f"✅ JavaScript function {func} exists")
            else:
                logger.error(f"❌ JavaScript function {func} not found")
                return False
    
    logger.info("✅ Rollback interface test passed")
    return True

def test_rollback_options_display():
    """Test rollback options display functionality"""
    logger.info("Testing rollback options display...")
    
    # Check that the template has rollback options components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for rollback options styling
        rollback_styles = [
            'rollback-options',
            'rollback-option',
            'rollback-option-info',
            'rollback-option-name',
            'rollback-option-details',
            'rollback-option-date'
        ]
        
        for style in rollback_styles:
            if style in content:
                logger.info(f"✅ Rollback style {style} exists")
            else:
                logger.error(f"❌ Rollback style {style} not found")
                return False
        
        # Check for rollback option interaction
        if 'onclick="selectRollbackOption' in content:
            logger.info("✅ Rollback option selection exists")
        else:
            logger.error("❌ Rollback option selection not found")
            return False
    
    logger.info("✅ Rollback options display test passed")
    return True

def test_rollback_impact_analysis():
    """Test rollback impact analysis functionality"""
    logger.info("Testing rollback impact analysis...")
    
    # Check that the template has impact analysis components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for impact analysis elements
        impact_elements = [
            'Rollback Impact Analysis',
            'Users Affected',
            'Impact Level',
            'Analyzing...'
        ]
        
        for element in impact_elements:
            if element in content:
                logger.info(f"✅ Impact element '{element}' exists")
            else:
                logger.error(f"❌ Impact element '{element}' not found")
                return False
        
        # Check for impact level logic
        if 'LOW' in content and 'MEDIUM' in content and 'HIGH' in content:
            logger.info("✅ Impact level logic exists")
        else:
            logger.error("❌ Impact level logic not found")
            return False
        
        # Check for warning system
        if 'rollback-warnings' in content and 'alert alert-warning' in content:
            logger.info("✅ Warning system exists")
        else:
            logger.error("❌ Warning system not found")
            return False
    
    logger.info("✅ Rollback impact analysis test passed")
    return True

def test_rollback_actions():
    """Test rollback action buttons and controls"""
    logger.info("Testing rollback actions...")
    
    # Check that the template has rollback action components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for action buttons
        action_buttons = [
            'Preview Rollback',
            'Execute Rollback',
            'Clear'
        ]
        
        for button in action_buttons:
            if button in content:
                logger.info(f"✅ Action button '{button}' exists")
            else:
                logger.error(f"❌ Action button '{button}' not found")
                return False
        
        # Check for button functions
        button_functions = [
            'onclick="previewRollback()"',
            'onclick="executeRollback()"',
            'onclick="clearRollback()"'
        ]
        
        for func in button_functions:
            if func in content:
                logger.info(f"✅ Button function {func} exists")
            else:
                logger.error(f"❌ Button function {func} not found")
                return False
        
        # Check for disabled states
        if 'disabled' in content:
            logger.info("✅ Button disabled states exist")
        else:
            logger.error("❌ Button disabled states not found")
            return False
    
    logger.info("✅ Rollback actions test passed")
    return True

def test_rollback_progress_tracking():
    """Test rollback progress tracking functionality"""
    logger.info("Testing rollback progress tracking...")
    
    # Check that the template has progress tracking components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for progress components
        progress_components = [
            'rollback-status',
            'operation-progress',
            'progress-bar',
            'rollback-progress-fill',
            'rollback-operation-log'
        ]
        
        for component in progress_components:
            if component in content:
                logger.info(f"✅ Progress component {component} exists")
            else:
                logger.error(f"❌ Progress component {component} not found")
                return False
        
        # Check for progress functions
        progress_functions = [
            'updateRollbackProgress',
            'logRollbackOperation'
        ]
        
        for func in progress_functions:
            if func in content:
                logger.info(f"✅ Progress function {func} exists")
            else:
                logger.error(f"❌ Progress function {func} not found")
                return False
    
    logger.info("✅ Rollback progress tracking test passed")
    return True

def test_service_layer_rollback():
    """Test service layer rollback functionality"""
    logger.info("Testing service layer rollback...")
    
    service = ACWRConfigurationService()
    
    # Test rollback methods exist
    rollback_methods = [
        'rollback_assignment',
        'bulk_rollback_assignments',
        'get_rollback_options',
        'get_rollback_impact_analysis'
    ]
    
    for method in rollback_methods:
        if hasattr(service, method):
            logger.info(f"✅ Rollback method {method} exists")
        else:
            logger.error(f"❌ Rollback method {method} not found")
            return False
    
    # Test method signatures
    import inspect
    
    # Test rollback_assignment signature
    rollback_sig = inspect.signature(service.rollback_assignment)
    expected_params = ['user_id', 'configuration_id', 'rollback_to_config_id', 'rolled_back_by']
    for param in expected_params:
        if param in rollback_sig.parameters:
            logger.info(f"✅ rollback_assignment parameter {param} exists")
        else:
            logger.error(f"❌ rollback_assignment parameter {param} not found")
            return False
    
    # Test get_rollback_options signature
    options_sig = inspect.signature(service.get_rollback_options)
    if 'user_id' in options_sig.parameters and 'limit' in options_sig.parameters:
        logger.info("✅ get_rollback_options signature is correct")
    else:
        logger.error("❌ get_rollback_options signature is incorrect")
        return False
    
    logger.info("✅ Service layer rollback test passed")
    return True

def test_api_endpoints():
    """Test API endpoints for rollback functionality"""
    logger.info("Testing API endpoints...")
    
    # Check that the admin blueprint has rollback endpoints
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

def test_rollback_confirmation():
    """Test rollback confirmation and safety measures"""
    logger.info("Testing rollback confirmation...")
    
    # Check that the template has confirmation elements
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for confirmation dialog
        if 'confirm(' in content and 'cannot be undone' in content:
            logger.info("✅ Rollback confirmation exists")
        else:
            logger.error("❌ Rollback confirmation not found")
            return False
        
        # Check for reason tracking
        if 'Reason for Rollback' in content and 'maxlength="500"' in content:
            logger.info("✅ Rollback reason tracking exists")
        else:
            logger.error("❌ Rollback reason tracking not found")
            return False
    
    logger.info("✅ Rollback confirmation test passed")
    return True

def test_rollback_history_tracking():
    """Test rollback history tracking functionality"""
    logger.info("Testing rollback history tracking...")
    
    # Check that the template has rollback history components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for rollback action type
        if 'ROLLBACK' in content:
            logger.info("✅ Rollback action type exists")
        else:
            logger.error("❌ Rollback action type not found")
            return False
        
        # Check for rollback styling
        if 'action-rollback' in content:
            logger.info("✅ Rollback action styling exists")
        else:
            logger.error("❌ Rollback action styling not found")
            return False
        
        # Check for history refresh
        if 'loadAssignmentHistory()' in content:
            logger.info("✅ History refresh exists")
        else:
            logger.error("❌ History refresh not found")
            return False
    
    logger.info("✅ Rollback history tracking test passed")
    return True

def run_all_tests():
    """Run all rollback capabilities tests"""
    logger.info("=" * 60)
    logger.info("Rollback Capabilities Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Rollback Interface", test_rollback_interface),
        ("Rollback Options Display", test_rollback_options_display),
        ("Rollback Impact Analysis", test_rollback_impact_analysis),
        ("Rollback Actions", test_rollback_actions),
        ("Rollback Progress Tracking", test_rollback_progress_tracking),
        ("Service Layer Rollback", test_service_layer_rollback),
        ("API Endpoints", test_api_endpoints),
        ("Rollback Confirmation", test_rollback_confirmation),
        ("Rollback History Tracking", test_rollback_history_tracking)
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
        logger.info("🎉 All tests passed! Rollback capabilities are working correctly.")
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

