#!/usr/bin/env python3
"""
Test script for Configuration Creation Form Validation
Tests the form validation for chronic period and decay rate ranges
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

def test_chronic_period_validation():
    """Test chronic period validation (28-90 days)"""
    logger.info("Testing chronic period validation...")
    
    service = ACWRConfigurationService()
    
    # Test valid chronic periods
    valid_periods = [28, 35, 42, 56, 70, 84, 90]
    for period in valid_periods:
        try:
            # This should not raise an exception
            service.create_configuration(
                name=f"Test Config {period}",
                description="Test configuration",
                chronic_period_days=period,
                decay_rate=0.05,
                created_by=1
            )
            logger.info(f"✅ Chronic period {period} days is valid")
        except ValueError as e:
            logger.error(f"❌ Chronic period {period} days should be valid: {str(e)}")
            return False
    
    # Test invalid chronic periods
    invalid_periods = [0, 1, 27, 91, 100, -5]
    for period in invalid_periods:
        try:
            service.create_configuration(
                name=f"Test Config {period}",
                description="Test configuration",
                chronic_period_days=period,
                decay_rate=0.05,
                created_by=1
            )
            logger.error(f"❌ Chronic period {period} days should be invalid")
            return False
        except ValueError as e:
            logger.info(f"✅ Chronic period {period} days correctly rejected: {str(e)}")
    
    logger.info("✅ Chronic period validation test passed")
    return True

def test_decay_rate_validation():
    """Test decay rate validation (0.01-0.20)"""
    logger.info("Testing decay rate validation...")
    
    service = ACWRConfigurationService()
    
    # Test valid decay rates
    valid_rates = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20]
    for rate in valid_rates:
        try:
            # This should not raise an exception
            service.create_configuration(
                name=f"Test Config {rate}",
                description="Test configuration",
                chronic_period_days=42,
                decay_rate=rate,
                created_by=1
            )
            logger.info(f"✅ Decay rate {rate} is valid")
        except ValueError as e:
            logger.error(f"❌ Decay rate {rate} should be valid: {str(e)}")
            return False
    
    # Test invalid decay rates
    invalid_rates = [0.0, 0.005, 0.21, 0.5, 1.0, -0.01]
    for rate in invalid_rates:
        try:
            service.create_configuration(
                name=f"Test Config {rate}",
                description="Test configuration",
                chronic_period_days=42,
                decay_rate=rate,
                created_by=1
            )
            logger.error(f"❌ Decay rate {rate} should be invalid")
            return False
        except ValueError as e:
            logger.info(f"✅ Decay rate {rate} correctly rejected: {str(e)}")
    
    logger.info("✅ Decay rate validation test passed")
    return True

def test_form_field_validation():
    """Test form field validation requirements"""
    logger.info("Testing form field validation...")
    
    service = ACWRConfigurationService()
    
    # Test missing required fields
    try:
        service.create_configuration(
            name="",  # Empty name
            description="Test configuration",
            chronic_period_days=42,
            decay_rate=0.05,
            created_by=1
        )
        logger.error("❌ Empty name should be rejected")
        return False
    except Exception as e:
        logger.info(f"✅ Empty name correctly rejected: {str(e)}")
    
    # Test name length limits
    try:
        long_name = "A" * 101  # Exceeds 100 character limit
        service.create_configuration(
            name=long_name,
            description="Test configuration",
            chronic_period_days=42,
            decay_rate=0.05,
            created_by=1
        )
        logger.error("❌ Long name should be rejected")
        return False
    except Exception as e:
        logger.info(f"✅ Long name correctly rejected: {str(e)}")
    
    # Test description length limits
    try:
        long_description = "A" * 256  # Exceeds 255 character limit
        service.create_configuration(
            name="Test Config",
            description=long_description,
            chronic_period_days=42,
            decay_rate=0.05,
            created_by=1
        )
        logger.error("❌ Long description should be rejected")
        return False
    except Exception as e:
        logger.info(f"✅ Long description correctly rejected: {str(e)}")
    
    # Test notes length limits
    try:
        long_notes = "A" * 501  # Exceeds 500 character limit
        service.create_configuration(
            name="Test Config",
            description="Test configuration",
            chronic_period_days=42,
            decay_rate=0.05,
            created_by=1,
            notes=long_notes
        )
        logger.error("❌ Long notes should be rejected")
        return False
    except Exception as e:
        logger.info(f"✅ Long notes correctly rejected: {str(e)}")
    
    logger.info("✅ Form field validation test passed")
    return True

def test_edge_case_validation():
    """Test edge case validation scenarios"""
    logger.info("Testing edge case validation...")
    
    service = ACWRConfigurationService()
    
    # Test boundary values
    boundary_tests = [
        (28, 0.01, "Minimum valid values"),
        (90, 0.20, "Maximum valid values"),
        (28, 0.20, "Min chronic, max decay"),
        (90, 0.01, "Max chronic, min decay")
    ]
    
    for chronic, decay, description in boundary_tests:
        try:
            service.create_configuration(
                name=f"Boundary Test {description}",
                description="Test configuration",
                chronic_period_days=chronic,
                decay_rate=decay,
                created_by=1
            )
            logger.info(f"✅ Boundary test passed: {description}")
        except ValueError as e:
            logger.error(f"❌ Boundary test failed: {description} - {str(e)}")
            return False
    
    # Test just outside boundary values
    invalid_boundary_tests = [
        (27, 0.01, "Just below min chronic"),
        (91, 0.01, "Just above max chronic"),
        (42, 0.009, "Just below min decay"),
        (42, 0.201, "Just above max decay")
    ]
    
    for chronic, decay, description in invalid_boundary_tests:
        try:
            service.create_configuration(
                name=f"Invalid Boundary Test {description}",
                description="Test configuration",
                chronic_period_days=chronic,
                decay_rate=decay,
                created_by=1
            )
            logger.error(f"❌ Invalid boundary test should fail: {description}")
            return False
        except ValueError as e:
            logger.info(f"✅ Invalid boundary test correctly rejected: {description}")
    
    logger.info("✅ Edge case validation test passed")
    return True

def test_validation_error_messages():
    """Test that validation error messages are helpful and specific"""
    logger.info("Testing validation error messages...")
    
    service = ACWRConfigurationService()
    
    # Test chronic period error message
    try:
        service.create_configuration(
            name="Test Config",
            description="Test configuration",
            chronic_period_days=20,
            decay_rate=0.05,
            created_by=1
        )
        logger.error("❌ Should have raised ValueError for invalid chronic period")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "28" in error_msg and "days" in error_msg:
            logger.info(f"✅ Chronic period error message is helpful: {error_msg}")
        else:
            logger.error(f"❌ Chronic period error message not helpful: {error_msg}")
            return False
    
    # Test decay rate error message
    try:
        service.create_configuration(
            name="Test Config",
            description="Test configuration",
            chronic_period_days=42,
            decay_rate=0.5,
            created_by=1
        )
        logger.error("❌ Should have raised ValueError for invalid decay rate")
        return False
    except ValueError as e:
        error_msg = str(e)
        if "0.01" in error_msg and "0.20" in error_msg:
            logger.info(f"✅ Decay rate error message is helpful: {error_msg}")
        else:
            logger.error(f"❌ Decay rate error message not helpful: {error_msg}")
            return False
    
    logger.info("✅ Validation error messages test passed")
    return True

def test_form_ui_validation():
    """Test that form UI elements have correct validation attributes"""
    logger.info("Testing form UI validation...")
    
    # Check that the template file exists and has correct validation attributes
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    if not os.path.exists(template_path):
        logger.error("❌ Admin template file does not exist")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check chronic period input validation
        if 'min="28"' in content and 'max="90"' in content:
            logger.info("✅ Chronic period input has correct min/max attributes")
        else:
            logger.error("❌ Chronic period input missing min/max attributes")
            return False
        
        # Check decay rate input validation
        if 'min="0.01"' in content and 'max="0.20"' in content:
            logger.info("✅ Decay rate input has correct min/max attributes")
        else:
            logger.error("❌ Decay rate input missing min/max attributes")
            return False
        
        # Check help text
        if "28-90 days" in content and "0.01-0.20" in content:
            logger.info("✅ Help text shows correct ranges")
        else:
            logger.error("❌ Help text missing correct ranges")
            return False
        
        # Check JavaScript validation
        if "decayRate < 0.01 || decayRate > 0.20" in content:
            logger.info("✅ JavaScript validation has correct decay rate range")
        else:
            logger.error("❌ JavaScript validation missing correct decay rate range")
            return False
    
    logger.info("✅ Form UI validation test passed")
    return True

def run_all_tests():
    """Run all configuration form validation tests"""
    logger.info("=" * 60)
    logger.info("Configuration Form Validation Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Chronic Period Validation", test_chronic_period_validation),
        ("Decay Rate Validation", test_decay_rate_validation),
        ("Form Field Validation", test_form_field_validation),
        ("Edge Case Validation", test_edge_case_validation),
        ("Validation Error Messages", test_validation_error_messages),
        ("Form UI Validation", test_form_ui_validation)
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
        logger.info("🎉 All tests passed! Configuration form validation is working correctly.")
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
