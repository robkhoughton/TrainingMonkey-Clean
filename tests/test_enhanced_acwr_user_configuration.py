#!/usr/bin/env python3
"""
Test script for Enhanced ACWR User Configuration Integration
Tests the updated calculate_enhanced_acwr method with user-specific configurations
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing
sys.modules['db_utils'] = MagicMock()

from acwr_configuration_service import ACWRConfigurationService
from exponential_decay_engine import ActivityData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_user_configuration_retrieval():
    """Test that user configuration is retrieved when not provided"""
    logger.info("Testing user configuration retrieval...")
    
    service = ACWRConfigurationService()
    
    # Mock user configuration
    mock_config = {
        'id': 1,
        'name': 'Test Configuration',
        'chronic_period_days': 42,
        'decay_rate': 0.05,
        'is_active': True
    }
    
    with patch.object(service, 'get_user_configuration') as mock_get_config:
        mock_get_config.return_value = mock_config
        
        with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
            mock_execute.side_effect = [
                [('2025-09-07', 10.0, 8.0)],  # Acute activities
                [('2025-09-07', 10.0, 8.0)] * 10,  # Chronic activities
            ]
            
            # Call without providing configuration
            result = service.calculate_enhanced_acwr(1, '2025-09-07')
            
            # Verify configuration was retrieved
            mock_get_config.assert_called_once_with(1)
            assert result['success'] == True
            assert result['configuration_id'] == 1
    
    logger.info("✅ User configuration retrieval test passed")
    return True

def test_no_configuration_fallback():
    """Test fallback when no user configuration is found"""
    logger.info("Testing no configuration fallback...")
    
    service = ACWRConfigurationService()
    
    with patch.object(service, 'get_user_configuration') as mock_get_config:
        mock_get_config.return_value = None
        
        # Call without providing configuration
        result = service.calculate_enhanced_acwr(1, '2025-09-07')
        
        # Verify fallback response
        assert result['success'] == False
        assert 'No ACWR configuration found' in result['error']
        assert result['fallback_to_standard'] == True
    
    logger.info("✅ No configuration fallback test passed")
    return True

def test_enhanced_calculation_with_exponential_decay():
    """Test enhanced calculation using exponential decay engine"""
    logger.info("Testing enhanced calculation with exponential decay engine...")
    
    service = ACWRConfigurationService()
    
    # Mock configuration
    mock_config = {
        'id': 1,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    # Mock database results
    mock_acute_activities = [
        ('2025-09-01', 10.0, 8.0),
        ('2025-09-02', 12.0, 10.0),
        ('2025-09-03', 8.0, 6.0),
        ('2025-09-04', 15.0, 12.0),
        ('2025-09-05', 11.0, 9.0),
        ('2025-09-06', 9.0, 7.0),
        ('2025-09-07', 13.0, 11.0)
    ]
    
    mock_chronic_activities = [
        ('2025-08-10', 10.0, 8.0),
        ('2025-08-11', 12.0, 10.0),
        ('2025-08-12', 8.0, 6.0),
        # ... more activities for 42 days
    ] * 15  # Simulate 42 days of activities
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        # Test the enhanced calculation
        result = service.calculate_enhanced_acwr(1, '2025-09-07', mock_config)
        
        # Verify result structure
        assert result['success'] == True
        assert result['user_id'] == 1
        assert result['activity_date'] == '2025-09-07'
        assert result['configuration_id'] == 1
        assert result['chronic_period_days'] == 42
        assert result['decay_rate'] == 0.05
        assert result['calculation_method'] == 'exponential_decay_engine'
        
        # Verify calculated values are present
        assert 'acute_load_avg' in result
        assert 'acute_trimp_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_chronic_trimp' in result
        assert 'enhanced_acute_chronic_ratio' in result
        assert 'enhanced_trimp_acute_chronic_ratio' in result
        assert 'enhanced_normalized_divergence' in result
    
    logger.info("✅ Enhanced calculation with exponential decay engine test passed")
    return True

def test_error_handling():
    """Test error handling in enhanced calculation"""
    logger.info("Testing error handling...")
    
    service = ACWRConfigurationService()
    
    # Mock configuration
    mock_config = {
        'id': 1,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = Exception("Database error")
        
        # Test error handling
        result = service.calculate_enhanced_acwr(1, '2025-09-07', mock_config)
        
        # Verify error response
        assert result['success'] == False
        assert 'Database error' in result['error']
        assert result['fallback_to_standard'] == True
    
    logger.info("✅ Error handling test passed")
    return True

def test_activity_data_conversion():
    """Test conversion of database results to ActivityData objects"""
    logger.info("Testing activity data conversion...")
    
    service = ACWRConfigurationService()
    
    # Mock configuration
    mock_config = {
        'id': 1,
        'chronic_period_days': 28,
        'decay_rate': 0.1
    }
    
    # Mock database results with various data types
    mock_activities = [
        ('2025-09-01', 10.0, 8.0),      # Normal data
        ('2025-09-02', None, 10.0),     # Missing load
        ('2025-09-03', 8.0, None),      # Missing trimp
        ('2025-09-04', 0.0, 0.0),       # Zero values
    ]
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_activities,  # Acute activities
            mock_activities,  # Chronic activities
        ]
        
        # Test the conversion
        result = service.calculate_enhanced_acwr(1, '2025-09-07', mock_config)
        
        # Verify conversion handled missing values correctly
        assert result['success'] == True
        # Should not crash on None values
    
    logger.info("✅ Activity data conversion test passed")
    return True

def test_different_configurations():
    """Test with different user configurations"""
    logger.info("Testing different user configurations...")
    
    service = ACWRConfigurationService()
    
    # Test different configurations
    configs = [
        {'chronic_period_days': 28, 'decay_rate': 0.1},
        {'chronic_period_days': 42, 'decay_rate': 0.05},
        {'chronic_period_days': 56, 'decay_rate': 0.03},
    ]
    
    for i, config in enumerate(configs):
        mock_config = {
            'id': i + 1,
            'chronic_period_days': config['chronic_period_days'],
            'decay_rate': config['decay_rate']
        }
        
        with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
            mock_execute.side_effect = [
                [('2025-09-07', 10.0, 8.0)],  # Acute activities
                [('2025-09-07', 10.0, 8.0)] * 10,  # Chronic activities
            ]
            
            result = service.calculate_enhanced_acwr(i + 1, '2025-09-07', mock_config)
            
            assert result['success'] == True
            assert result['chronic_period_days'] == config['chronic_period_days']
            assert result['decay_rate'] == config['decay_rate']
    
    logger.info("✅ Different configurations test passed")
    return True

def run_all_tests():
    """Run all enhanced ACWR user configuration tests"""
    logger.info("=" * 60)
    logger.info("Enhanced ACWR User Configuration Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("User Configuration Retrieval", test_user_configuration_retrieval),
        ("No Configuration Fallback", test_no_configuration_fallback),
        ("Enhanced Calculation with Exponential Decay", test_enhanced_calculation_with_exponential_decay),
        ("Error Handling", test_error_handling),
        ("Activity Data Conversion", test_activity_data_conversion),
        ("Different Configurations", test_different_configurations)
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
        logger.info("🎉 All tests passed! Enhanced ACWR user configuration integration is working correctly.")
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
