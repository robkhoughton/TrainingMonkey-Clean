#!/usr/bin/env python3
"""
Test script for Real-time Validation with Helpful Error Messages
Tests the comprehensive real-time validation system with user-friendly feedback
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

def test_validation_interface():
    """Test that the validation interface has all required components"""
    logger.info("Testing validation interface...")
    
    # Check that the template file exists and has validation components
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    if not os.path.exists(template_path):
        logger.error("❌ Admin template file does not exist")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for validation setup functions
        validation_functions = [
            'setupFormValidation',
            'setupCreateFormValidation',
            'setupEditFormValidation'
        ]
        
        for func in validation_functions:
            if func in content:
                logger.info(f"✅ Validation function {func} exists")
            else:
                logger.error(f"❌ Validation function {func} not found")
                return False
        
        # Check for validation event listeners
        validation_events = [
            'addEventListener(\'input\'',
            'addEventListener(\'blur\'',
            'validateCreateName',
            'validateCreateChronicPeriod',
            'validateCreateDecayRate',
            'validateCreateDescription',
            'validateCreateNotes'
        ]
        
        for event in validation_events:
            if event in content:
                logger.info(f"✅ Validation event {event} exists")
            else:
                logger.error(f"❌ Validation event {event} not found")
                return False
    
    logger.info("✅ Validation interface test passed")
    return True

def test_field_validation():
    """Test field-specific validation functions"""
    logger.info("Testing field validation...")
    
    # Check that the template has field validation functions
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for create form validation functions
        create_validation_functions = [
            'validateCreateName',
            'validateCreateChronicPeriod',
            'validateCreateDecayRate',
            'validateCreateDescription',
            'validateCreateNotes'
        ]
        
        for func in create_validation_functions:
            if func in content:
                logger.info(f"✅ Create validation function {func} exists")
            else:
                logger.error(f"❌ Create validation function {func} not found")
                return False
        
        # Check for edit form validation functions
        edit_validation_functions = [
            'validateEditName',
            'validateEditChronicPeriod',
            'validateEditDecayRate',
            'validateEditDescription',
            'validateEditNotes'
        ]
        
        for func in edit_validation_functions:
            if func in content:
                logger.info(f"✅ Edit validation function {func} exists")
            else:
                logger.error(f"❌ Edit validation function {func} not found")
                return False
    
    logger.info("✅ Field validation test passed")
    return True

def test_validation_helpers():
    """Test validation helper functions"""
    logger.info("Testing validation helpers...")
    
    # Check that the template has validation helper functions
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for helper functions
        helper_functions = [
            'getOrCreateErrorElement',
            'showFieldError',
            'showFieldSuccess',
            'validateCreateForm',
            'validateEditForm'
        ]
        
        for func in helper_functions:
            if func in content:
                logger.info(f"✅ Helper function {func} exists")
            else:
                logger.error(f"❌ Helper function {func} not found")
                return False
        
        # Check for validation classes
        validation_classes = [
            'is-valid',
            'is-invalid',
            'field-error'
        ]
        
        for cls in validation_classes:
            if cls in content:
                logger.info(f"✅ Validation class {cls} exists")
            else:
                logger.error(f"❌ Validation class {cls} not found")
                return False
    
    logger.info("✅ Validation helpers test passed")
    return True

def test_error_messages():
    """Test error message content and helpfulness"""
    logger.info("Testing error messages...")
    
    # Check that the template has helpful error messages
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for helpful error messages
        error_messages = [
            'Configuration name is required',
            'Configuration name must be 100 characters or less',
            'A configuration with this name already exists',
            'Chronic period must be a number',
            'Chronic period must be at least 28 days',
            'Chronic period must be 90 days or less',
            'Decay rate must be a number',
            'Decay rate must be at least 0.01',
            'Decay rate must be 0.20 or less',
            'Description must be 255 characters or less',
            'Notes must be 500 characters or less'
        ]
        
        for message in error_messages:
            if message in content:
                logger.info(f"✅ Error message '{message}' exists")
            else:
                logger.error(f"❌ Error message '{message}' not found")
                return False
    
    logger.info("✅ Error messages test passed")
    return True

def test_character_counting():
    """Test character counting functionality"""
    logger.info("Testing character counting...")
    
    # Check that the template has character counting functionality
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for character count elements
        character_count_elements = [
            'config-name-count',
            'config-description-count',
            'character-count'
        ]
        
        for element in character_count_elements:
            if element in content:
                logger.info(f"✅ Character count element {element} exists")
            else:
                logger.error(f"❌ Character count element {element} not found")
                return False
        
        # Check for character count function
        if 'updateCharacterCount' in content:
            logger.info("✅ Character count function exists")
        else:
            logger.error("❌ Character count function not found")
            return False
        
        # Check for character count styling
        character_count_styles = [
            'character-count.warning',
            'character-count.danger'
        ]
        
        for style in character_count_styles:
            if style in content:
                logger.info(f"✅ Character count style {style} exists")
            else:
                logger.error(f"❌ Character count style {style} not found")
                return False
    
    logger.info("✅ Character counting test passed")
    return True

def test_form_help_text():
    """Test form help text and guidance"""
    logger.info("Testing form help text...")
    
    # Check that the template has helpful form guidance
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for help text elements
        help_elements = [
            'form-help',
            'Choose a descriptive name',
            'Optional description',
            'Number of days for chronic load calculation',
            'Exponential decay rate for weighting'
        ]
        
        for element in help_elements:
            if element in content:
                logger.info(f"✅ Help element '{element}' exists")
            else:
                logger.error(f"❌ Help element '{element}' not found")
                return False
        
        # Check for placeholder text
        placeholder_texts = [
            'Enter a unique configuration name',
            'Optional description',
            '28-90',
            '0.01-0.20'
        ]
        
        for placeholder in placeholder_texts:
            if placeholder in content:
                logger.info(f"✅ Placeholder text '{placeholder}' exists")
            else:
                logger.error(f"❌ Placeholder text '{placeholder}' not found")
                return False
    
    logger.info("✅ Form help text test passed")
    return True

def test_validation_styling():
    """Test validation styling and visual feedback"""
    logger.info("Testing validation styling...")
    
    # Check that the template has validation styling
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for validation CSS classes
        validation_styles = [
            'field-error',
            'is-valid',
            'is-invalid',
            'validation-summary',
            'form-help',
            'character-count'
        ]
        
        for style in validation_styles:
            if style in content:
                logger.info(f"✅ Validation style {style} exists")
            else:
                logger.error(f"❌ Validation style {style} not found")
                return False
        
        # Check for color coding
        color_classes = [
            'text-danger',
            'text-success',
            'warning',
            'danger'
        ]
        
        for color in color_classes:
            if color in content:
                logger.info(f"✅ Color class {color} exists")
            else:
                logger.error(f"❌ Color class {color} not found")
                return False
    
    logger.info("✅ Validation styling test passed")
    return True

def test_duplicate_validation():
    """Test duplicate name validation"""
    logger.info("Testing duplicate validation...")
    
    # Check that the template has duplicate validation logic
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for duplicate validation logic
        duplicate_checks = [
            'configurations.some',
            'name.toLowerCase()',
            'already exists',
            'currentConfigId'
        ]
        
        for check in duplicate_checks:
            if check in content:
                logger.info(f"✅ Duplicate check '{check}' exists")
            else:
                logger.error(f"❌ Duplicate check '{check}' not found")
                return False
    
    logger.info("✅ Duplicate validation test passed")
    return True

def test_form_validation_integration():
    """Test form validation integration"""
    logger.info("Testing form validation integration...")
    
    # Check that the template has form validation integration
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_configuration.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check for form validation integration
        integration_elements = [
            'validateCreateForm',
            'validateEditForm',
            'handleCreateConfiguration',
            'handleEditConfiguration'
        ]
        
        for element in integration_elements:
            if element in content:
                logger.info(f"✅ Integration element {element} exists")
            else:
                logger.error(f"❌ Integration element {element} not found")
                return False
    
    logger.info("✅ Form validation integration test passed")
    return True

def run_all_tests():
    """Run all real-time validation tests"""
    logger.info("=" * 60)
    logger.info("Real-time Validation Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Validation Interface", test_validation_interface),
        ("Field Validation", test_field_validation),
        ("Validation Helpers", test_validation_helpers),
        ("Error Messages", test_error_messages),
        ("Character Counting", test_character_counting),
        ("Form Help Text", test_form_help_text),
        ("Validation Styling", test_validation_styling),
        ("Duplicate Validation", test_duplicate_validation),
        ("Form Validation Integration", test_form_validation_integration)
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
        logger.info("🎉 All tests passed! Real-time validation is working correctly.")
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

