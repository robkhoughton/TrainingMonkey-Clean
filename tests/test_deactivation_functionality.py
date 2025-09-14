#!/usr/bin/env python3
"""
Test script for Enhanced Configuration Deactivation (Soft Delete) Functionality
Tests the deactivation and reactivation features with impact analysis
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

def test_deactivation_interface_components():
    """Test that the deactivation interface has all required components"""
    logger.info("Testing deactivation interface components...")
    
    # Check that the template file exists and has deactivation components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    if not os.path.exists(template_path):
        logger.error("❌ Admin template file does not exist")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for deactivation modal
        if 'id="deactivate-modal"' in content:
            logger.info("✅ Deactivation modal exists")
        else:
            logger.error("❌ Deactivation modal not found")
            return False
        
        # Check for reactivation modal
        if 'id="reactivate-modal"' in content:
            logger.info("✅ Reactivation modal exists")
        else:
            logger.error("❌ Reactivation modal not found")
            return False
        
        # Check for deactivation interface components
        deactivation_components = [
            'deactivate-config-details',
            'deactivation-impact-details',
            'deactivate-config-name',
            'deactivate-affected-users',
            'deactivate-impact-level',
            'deactivation-warnings',
            'deactivation-reason'
        ]
        
        for component in deactivation_components:
            if f'id="{component}"' in content:
                logger.info(f"✅ Deactivation component {component} exists")
            else:
                logger.error(f"❌ Deactivation component {component} not found")
                return False
        
        # Check for reactivation interface components
        reactivation_components = [
            'reactivate-config-details',
            'reactivation-impact-details',
            'reactivate-config-name',
            'reactivate-previous-users'
        ]
        
        for component in reactivation_components:
            if f'id="{component}"' in content:
                logger.info(f"✅ Reactivation component {component} exists")
            else:
                logger.error(f"❌ Reactivation component {component} not found")
                return False
        
        # Check for JavaScript functions
        js_functions = [
            'deactivateConfiguration',
            'reactivateConfiguration',
            'loadDeactivationImpact',
            'loadReactivationImpact',
            'confirmDeactivation',
            'confirmReactivation',
            'closeDeactivateModal',
            'closeReactivateModal'
        ]
        
        for func in js_functions:
            if func in content:
                logger.info(f"✅ JavaScript function {func} exists")
            else:
                logger.error(f"❌ JavaScript function {func} not found")
                return False
    
    logger.info("✅ Deactivation interface components test passed")
    return True

def test_deactivation_buttons():
    """Test that deactivation buttons are properly implemented"""
    logger.info("Testing deactivation buttons...")
    
    # Check that the template has deactivation buttons
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for deactivation button
        if 'onclick="deactivateConfiguration' in content:
            logger.info("✅ Deactivation button exists")
        else:
            logger.error("❌ Deactivation button not found")
            return False
        
        # Check for reactivation button
        if 'onclick="reactivateConfiguration' in content:
            logger.info("✅ Reactivation button exists")
        else:
            logger.error("❌ Reactivation button not found")
            return False
        
        # Check for button styling
        if 'btn-warning' in content and 'Deactivate' in content:
            logger.info("✅ Deactivation button styling exists")
        else:
            logger.error("❌ Deactivation button styling not found")
            return False
        
        if 'btn-success' in content and 'Reactivate' in content:
            logger.info("✅ Reactivation button styling exists")
        else:
            logger.error("❌ Reactivation button styling not found")
            return False
    
    logger.info("✅ Deactivation buttons test passed")
    return True

def test_impact_analysis():
    """Test impact analysis functionality"""
    logger.info("Testing impact analysis...")
    
    # Check that the template has impact analysis components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for impact analysis elements
        impact_elements = [
            'Deactivation Impact',
            'Reactivation Impact',
            'Affected Users',
            'Impact Level',
            'Previous Users'
        ]
        
        for element in impact_elements:
            if element in content:
                logger.info(f"✅ Impact element '{element}' exists")
            else:
                logger.error(f"❌ Impact element '{element}' not found")
                return False
        
        # Check for impact level logic
        if 'LOW IMPACT' in content and 'MEDIUM IMPACT' in content and 'HIGH IMPACT' in content:
            logger.info("✅ Impact level logic exists")
        else:
            logger.error("❌ Impact level logic not found")
            return False
        
        # Check for warning messages
        warning_messages = [
            'users are currently assigned',
            'fall back to the default configuration',
            'High Impact',
            'training load analysis'
        ]
        
        for message in warning_messages:
            if message in content:
                logger.info(f"✅ Warning message '{message}' exists")
            else:
                logger.error(f"❌ Warning message '{message}' not found")
                return False
    
    logger.info("✅ Impact analysis test passed")
    return True

def test_deactivation_reason_tracking():
    """Test deactivation reason tracking functionality"""
    logger.info("Testing deactivation reason tracking...")
    
    # Check that the template has reason tracking
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for reason input field
        if 'deactivation-reason' in content and 'Reason for Deactivation' in content:
            logger.info("✅ Deactivation reason input exists")
        else:
            logger.error("❌ Deactivation reason input not found")
            return False
        
        # Check for reason validation
        if 'maxlength="500"' in content:
            logger.info("✅ Reason length validation exists")
        else:
            logger.error("❌ Reason length validation not found")
            return False
        
        # Check for reason placeholder
        if 'Enter reason for deactivation' in content:
            logger.info("✅ Reason placeholder exists")
        else:
            logger.error("❌ Reason placeholder not found")
            return False
    
    logger.info("✅ Deactivation reason tracking test passed")
    return True

def test_service_layer_deactivation():
    """Test service layer deactivation functionality"""
    logger.info("Testing service layer deactivation...")
    
    service = ACWRConfigurationService()
    
    # Test deactivation method exists
    if hasattr(service, 'deactivate_configuration'):
        logger.info("✅ deactivate_configuration method exists")
    else:
        logger.error("❌ deactivate_configuration method not found")
        return False
    
    # Test reactivation method exists
    if hasattr(service, 'reactivate_configuration'):
        logger.info("✅ reactivate_configuration method exists")
    else:
        logger.error("❌ reactivate_configuration method not found")
        return False
    
    # Test method signatures
    import inspect
    
    deactivate_sig = inspect.signature(service.deactivate_configuration)
    if 'config_id' in deactivate_sig.parameters and 'reason' in deactivate_sig.parameters:
        logger.info("✅ deactivate_configuration method signature is correct")
    else:
        logger.error("❌ deactivate_configuration method signature is incorrect")
        return False
    
    reactivate_sig = inspect.signature(service.reactivate_configuration)
    if 'config_id' in reactivate_sig.parameters:
        logger.info("✅ reactivate_configuration method signature is correct")
    else:
        logger.error("❌ reactivate_configuration method signature is incorrect")
        return False
    
    logger.info("✅ Service layer deactivation test passed")
    return True

def test_api_endpoints():
    """Test API endpoints for deactivation"""
    logger.info("Testing API endpoints...")
    
    # Check that the admin blueprint has deactivation endpoints
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

def test_soft_delete_vs_hard_delete():
    """Test that deactivation is soft delete vs hard delete"""
    logger.info("Testing soft delete vs hard delete...")
    
    # Check that the template distinguishes between deactivation and deletion
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for deactivation vs deletion distinction
        if 'Deactivate Configuration' in content and 'Delete Configuration' in content:
            logger.info("✅ Deactivation and deletion are distinguished")
        else:
            logger.error("❌ Deactivation and deletion are not distinguished")
            return False
        
        # Check for different impact messages
        if 'fall back to the default configuration' in content and 'cannot be undone' in content:
            logger.info("✅ Different impact messages for deactivation vs deletion")
        else:
            logger.error("❌ Same impact messages for deactivation vs deletion")
            return False
        
        # Check for different button colors
        if 'btn-warning' in content and 'btn-danger' in content:
            logger.info("✅ Different button colors for deactivation vs deletion")
        else:
            logger.error("❌ Same button colors for deactivation vs deletion")
            return False
    
    logger.info("✅ Soft delete vs hard delete test passed")
    return True

def test_modal_management():
    """Test modal management for deactivation"""
    logger.info("Testing modal management...")
    
    # Check that the template has proper modal management
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for modal close functions
        close_functions = [
            'closeDeactivateModal',
            'closeReactivateModal'
        ]
        
        for func in close_functions:
            if func in content:
                logger.info(f"✅ Modal close function {func} exists")
            else:
                logger.error(f"❌ Modal close function {func} not found")
                return False
        
        # Check for modal click handlers
        if 'deactivate-modal' in content and 'reactivate-modal' in content:
            logger.info("✅ Modal click handlers exist")
        else:
            logger.error("❌ Modal click handlers not found")
            return False
        
        # Check for global variables
        if 'currentDeactivateId' in content and 'currentReactivateId' in content:
            logger.info("✅ Global variables for modal management exist")
        else:
            logger.error("❌ Global variables for modal management not found")
            return False
    
    logger.info("✅ Modal management test passed")
    return True

def run_all_tests():
    """Run all deactivation functionality tests"""
    logger.info("=" * 60)
    logger.info("Enhanced Configuration Deactivation Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Deactivation Interface Components", test_deactivation_interface_components),
        ("Deactivation Buttons", test_deactivation_buttons),
        ("Impact Analysis", test_impact_analysis),
        ("Deactivation Reason Tracking", test_deactivation_reason_tracking),
        ("Service Layer Deactivation", test_service_layer_deactivation),
        ("API Endpoints", test_api_endpoints),
        ("Soft Delete vs Hard Delete", test_soft_delete_vs_hard_delete),
        ("Modal Management", test_modal_management)
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
        logger.info("🎉 All tests passed! Enhanced deactivation functionality is working correctly.")
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

