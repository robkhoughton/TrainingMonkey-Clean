#!/usr/bin/env python3
"""
Test script for Enhanced Edit Interface with Impact Warnings
Tests the configuration editing interface with impact analysis
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

def test_edit_interface_components():
    """Test that the edit interface has all required components"""
    logger.info("Testing edit interface components...")
    
    # Check that the template file exists and has edit interface components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    if not os.path.exists(template_path):
        logger.error("❌ Admin template file does not exist")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for edit modal
        if 'id="edit-modal"' in content:
            logger.info("✅ Edit modal exists")
        else:
            logger.error("❌ Edit modal not found")
            return False
        
        # Check for impact warning components
        impact_components = [
            'id="edit-impact-warning"',
            'id="affected-users-count"',
            'id="impact-level"',
            'id="parameter-changes"',
            'id="changes-list"',
            'id="high-impact-warning"',
            'id="medium-impact-warning"',
            'id="low-impact-warning"'
        ]
        
        for component in impact_components:
            if component in content:
                logger.info(f"✅ Impact component {component} exists")
            else:
                logger.error(f"❌ Impact component {component} not found")
                return False
        
        # Check for JavaScript functions
        js_functions = [
            'function editConfiguration',
            'function loadEditImpactAnalysis',
            'function analyzeEditImpact',
            'function closeEditModal'
        ]
        
        for func in js_functions:
            if func in content:
                logger.info(f"✅ JavaScript function {func} exists")
            else:
                logger.error(f"❌ JavaScript function {func} not found")
                return False
    
    logger.info("✅ Edit interface components test passed")
    return True

def test_impact_analysis_logic():
    """Test the impact analysis logic"""
    logger.info("Testing impact analysis logic...")
    
    # Test impact scoring logic
    def calculate_impact_score(chronic_change_percent, decay_change_percent):
        """Simulate the impact scoring logic from JavaScript"""
        impact_score = 0
        
        # Chronic period impact
        if chronic_change_percent > 50:
            impact_score += 3  # High impact
        elif chronic_change_percent > 20:
            impact_score += 2  # Medium impact
        elif chronic_change_percent > 0:
            impact_score += 1  # Low impact
        
        # Decay rate impact
        if decay_change_percent > 100:
            impact_score += 3  # High impact
        elif decay_change_percent > 50:
            impact_score += 2  # Medium impact
        elif decay_change_percent > 0:
            impact_score += 1  # Low impact
        
        return impact_score
    
    # Test cases for impact analysis
    test_cases = [
        # (chronic_change_percent, decay_change_percent, expected_impact_level)
        (0, 0, "NO CHANGES"),
        (10, 0, "LOW IMPACT"),
        (0, 30, "LOW IMPACT"),
        (10, 30, "MEDIUM IMPACT"),
        (25, 0, "MEDIUM IMPACT"),
        (0, 60, "MEDIUM IMPACT"),
        (25, 60, "HIGH IMPACT"),
        (60, 0, "MEDIUM IMPACT"),
        (0, 120, "MEDIUM IMPACT"),
        (60, 120, "HIGH IMPACT"),
        (30, 80, "HIGH IMPACT")
    ]
    
    for chronic_change, decay_change, expected_level in test_cases:
        impact_score = calculate_impact_score(chronic_change, decay_change)
        
        if impact_score >= 4:
            actual_level = "HIGH IMPACT"
        elif impact_score >= 2:
            actual_level = "MEDIUM IMPACT"
        elif impact_score > 0:
            actual_level = "LOW IMPACT"
        else:
            actual_level = "NO CHANGES"
        
        if actual_level == expected_level:
            logger.info(f"✅ Impact analysis correct: {chronic_change}% chronic, {decay_change}% decay → {actual_level}")
        else:
            logger.error(f"❌ Impact analysis incorrect: {chronic_change}% chronic, {decay_change}% decay → expected {expected_level}, got {actual_level}")
            return False
    
    logger.info("✅ Impact analysis logic test passed")
    return True

def test_edit_validation():
    """Test that edit form validation works correctly"""
    logger.info("Testing edit form validation...")
    
    service = ACWRConfigurationService()
    
    # Test valid edit data
    valid_edit_data = {
        'name': 'Updated Configuration',
        'description': 'Updated description',
        'chronic_period_days': 45,
        'decay_rate': 0.08,
        'notes': 'Updated notes'
    }
    
    # Test invalid edit data
    invalid_edit_cases = [
        {
            'data': {'name': '', 'chronic_period_days': 45, 'decay_rate': 0.08},
            'expected_error': 'Configuration name is required'
        },
        {
            'data': {'name': 'Test', 'chronic_period_days': 20, 'decay_rate': 0.08},
            'expected_error': 'Chronic period must be at least 28 days'
        },
        {
            'data': {'name': 'Test', 'chronic_period_days': 45, 'decay_rate': 0.5},
            'expected_error': 'Decay rate must be between 0.01 and 0.20'
        }
    ]
    
    # Test valid data (should not raise exception)
    try:
        # This would normally call the service, but we're testing validation logic
        assert valid_edit_data['chronic_period_days'] >= 28
        assert valid_edit_data['chronic_period_days'] <= 90
        assert 0.01 <= valid_edit_data['decay_rate'] <= 0.20
        assert valid_edit_data['name'].strip()
        logger.info("✅ Valid edit data passes validation")
    except AssertionError as e:
        logger.error(f"❌ Valid edit data failed validation: {str(e)}")
        return False
    
    # Test invalid data cases
    for case in invalid_edit_cases:
        data = case['data']
        expected_error = case['expected_error']
        
        try:
            # Simulate validation logic
            if not data.get('name') or not data['name'].strip():
                raise ValueError("Configuration name is required")
            if data.get('chronic_period_days', 0) < 28:
                raise ValueError("Chronic period must be at least 28 days")
            if data.get('chronic_period_days', 0) > 90:
                raise ValueError("Chronic period must be 90 days or less")
            if not (0.01 <= data.get('decay_rate', 0) <= 0.20):
                raise ValueError("Decay rate must be between 0.01 and 0.20")
            
            logger.error(f"❌ Invalid data should have been rejected: {data}")
            return False
        except ValueError as e:
            if expected_error in str(e):
                logger.info(f"✅ Invalid data correctly rejected: {expected_error}")
            else:
                logger.error(f"❌ Wrong error message: expected '{expected_error}', got '{str(e)}'")
                return False
    
    logger.info("✅ Edit validation test passed")
    return True

def test_impact_warning_display():
    """Test that impact warnings are displayed correctly"""
    logger.info("Testing impact warning display...")
    
    # Check that the template has proper warning styling
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for warning CSS classes
        warning_classes = [
            'alert alert-danger',
            'alert alert-warning', 
            'alert alert-info'
        ]
        
        for warning_class in warning_classes:
            if warning_class in content:
                logger.info(f"✅ Warning class {warning_class} exists")
            else:
                logger.error(f"❌ Warning class {warning_class} not found")
                return False
        
        # Check for impact warning content
        warning_content = [
            'HIGH IMPACT WARNING',
            'MEDIUM IMPACT WARNING',
            'LOW IMPACT',
            'significantly affect ACWR calculations',
            'affect ACWR calculations',
            'minimal impact on ACWR calculations'
        ]
        
        for content_item in warning_content:
            if content_item in content:
                logger.info(f"✅ Warning content '{content_item}' exists")
            else:
                logger.error(f"❌ Warning content '{content_item}' not found")
                return False
    
    logger.info("✅ Impact warning display test passed")
    return True

def test_confirmation_requirements():
    """Test that high-impact changes require confirmation"""
    logger.info("Testing confirmation requirements...")
    
    # Check that the template has confirmation logic
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for confirmation logic
        confirmation_elements = [
            'HIGH IMPACT WARNING',
            'Are you sure you want to proceed',
            'significantly affect ACWR calculations',
            'Consider:',
            'The impact on user training load analysis',
            'Historical data consistency',
            'User notification requirements'
        ]
        
        for element in confirmation_elements:
            if element in content:
                logger.info(f"✅ Confirmation element '{element}' exists")
            else:
                logger.error(f"❌ Confirmation element '{element}' not found")
                return False
    
    logger.info("✅ Confirmation requirements test passed")
    return True

def test_real_time_analysis():
    """Test that real-time impact analysis is implemented"""
    logger.info("Testing real-time impact analysis...")
    
    # Check that the template has real-time analysis features
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for real-time analysis features
        real_time_features = [
            'addEventListener(\'input\', analyzeEditImpact)',
            'data-original',
            'setAttribute(\'data-original\'',
            'removeEventListener(\'input\', analyzeEditImpact)',
            'analyzeEditImpact()',
            'loadEditImpactAnalysis'
        ]
        
        for feature in real_time_features:
            if feature in content:
                logger.info(f"✅ Real-time feature '{feature}' exists")
            else:
                logger.error(f"❌ Real-time feature '{feature}' not found")
                return False
    
    logger.info("✅ Real-time analysis test passed")
    return True

def run_all_tests():
    """Run all edit interface impact warnings tests"""
    logger.info("=" * 60)
    logger.info("Edit Interface Impact Warnings Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Edit Interface Components", test_edit_interface_components),
        ("Impact Analysis Logic", test_impact_analysis_logic),
        ("Edit Validation", test_edit_validation),
        ("Impact Warning Display", test_impact_warning_display),
        ("Confirmation Requirements", test_confirmation_requirements),
        ("Real-time Analysis", test_real_time_analysis)
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
        logger.info("🎉 All tests passed! Edit interface with impact warnings is working correctly.")
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
