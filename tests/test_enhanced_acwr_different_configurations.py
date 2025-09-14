#!/usr/bin/env python3
"""
Test script for Enhanced ACWR Calculation with Different Configurations
Tests the enhanced ACWR calculation with various user configurations
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

from acwr_calculation_service import ACWRCalculationService
from acwr_configuration_service import ACWRConfigurationService
from exponential_decay_engine import ActivityData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_short_chronic_period_configuration():
    """Test enhanced ACWR with short chronic period (28 days)"""
    logger.info("Testing short chronic period configuration (28 days)...")
    
    service = ACWRConfigurationService()
    
    # Configuration with short chronic period
    config = {
        'id': 1,
        'chronic_period_days': 28,
        'decay_rate': 0.1
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
        # ... more activities for 28 days
    ] * 10  # Simulate 28 days of activities
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(1, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['chronic_period_days'] == 28
        assert result['decay_rate'] == 0.1
        assert result['calculation_method'] == 'exponential_decay_engine'
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Short chronic period configuration test passed")
    return True

def test_medium_chronic_period_configuration():
    """Test enhanced ACWR with medium chronic period (42 days)"""
    logger.info("Testing medium chronic period configuration (42 days)...")
    
    service = ACWRConfigurationService()
    
    # Configuration with medium chronic period
    config = {
        'id': 2,
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
        
        result = service.calculate_enhanced_acwr(2, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['chronic_period_days'] == 42
        assert result['decay_rate'] == 0.05
        assert result['calculation_method'] == 'exponential_decay_engine'
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Medium chronic period configuration test passed")
    return True

def test_long_chronic_period_configuration():
    """Test enhanced ACWR with long chronic period (90 days)"""
    logger.info("Testing long chronic period configuration (90 days)...")
    
    service = ACWRConfigurationService()
    
    # Configuration with long chronic period
    config = {
        'id': 3,
        'chronic_period_days': 90,
        'decay_rate': 0.02
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
        # ... more activities for 90 days
    ] * 30  # Simulate 90 days of activities
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(3, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['chronic_period_days'] == 90
        assert result['decay_rate'] == 0.02
        assert result['calculation_method'] == 'exponential_decay_engine'
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Long chronic period configuration test passed")
    return True

def test_high_decay_rate_configuration():
    """Test enhanced ACWR with high decay rate (0.1)"""
    logger.info("Testing high decay rate configuration (0.1)...")
    
    service = ACWRConfigurationService()
    
    # Configuration with high decay rate
    config = {
        'id': 4,
        'chronic_period_days': 42,
        'decay_rate': 0.1
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
        # ... more activities for chronic period
    ] * 15  # Simulate chronic period activities
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(4, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['chronic_period_days'] == 42
        assert result['decay_rate'] == 0.1
        assert result['calculation_method'] == 'exponential_decay_engine'
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ High decay rate configuration test passed")
    return True

def test_low_decay_rate_configuration():
    """Test enhanced ACWR with low decay rate (0.01)"""
    logger.info("Testing low decay rate configuration (0.01)...")
    
    service = ACWRConfigurationService()
    
    # Configuration with low decay rate
    config = {
        'id': 5,
        'chronic_period_days': 42,
        'decay_rate': 0.01
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
        # ... more activities for chronic period
    ] * 15  # Simulate chronic period activities
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(5, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['chronic_period_days'] == 42
        assert result['decay_rate'] == 0.01
        assert result['calculation_method'] == 'exponential_decay_engine'
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Low decay rate configuration test passed")
    return True

def test_configuration_comparison():
    """Test comparison between different configurations"""
    logger.info("Testing configuration comparison...")
    
    service = ACWRConfigurationService()
    
    # Test configurations
    configs = [
        {'id': 1, 'chronic_period_days': 28, 'decay_rate': 0.1},
        {'id': 2, 'chronic_period_days': 42, 'decay_rate': 0.05},
        {'id': 3, 'chronic_period_days': 90, 'decay_rate': 0.02}
    ]
    
    results = []
    
    for config in configs:
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
        ] * (config['chronic_period_days'] // 3)  # Simulate chronic period activities
        
        with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
            mock_execute.side_effect = [
                mock_acute_activities,  # Acute activities query
                mock_chronic_activities,  # Chronic activities query
            ]
            
            result = service.calculate_enhanced_acwr(config['id'], '2025-09-07', config)
            results.append(result)
    
    # Verify all configurations worked
    for i, result in enumerate(results):
        assert result['success'] == True
        assert result['chronic_period_days'] == configs[i]['chronic_period_days']
        assert result['decay_rate'] == configs[i]['decay_rate']
        assert result['calculation_method'] == 'exponential_decay_engine'
    
    # Verify different configurations produce different results
    assert results[0]['chronic_period_days'] != results[1]['chronic_period_days']
    assert results[1]['chronic_period_days'] != results[2]['chronic_period_days']
    assert results[0]['decay_rate'] != results[1]['decay_rate']
    assert results[1]['decay_rate'] != results[2]['decay_rate']
    
    logger.info("✅ Configuration comparison test passed")
    return True

def test_edge_case_configurations():
    """Test edge case configurations"""
    logger.info("Testing edge case configurations...")
    
    service = ACWRConfigurationService()
    
    # Test minimum valid configuration
    min_config = {
        'id': 6,
        'chronic_period_days': 28,  # Minimum
        'decay_rate': 0.001  # Very low
    }
    
    # Test maximum valid configuration
    max_config = {
        'id': 7,
        'chronic_period_days': 90,  # Maximum
        'decay_rate': 1.0  # Maximum
    }
    
    configs = [min_config, max_config]
    
    for config in configs:
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
        ] * (config['chronic_period_days'] // 3)  # Simulate chronic period activities
        
        with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
            mock_execute.side_effect = [
                mock_acute_activities,  # Acute activities query
                mock_chronic_activities,  # Chronic activities query
            ]
            
            result = service.calculate_enhanced_acwr(config['id'], '2025-09-07', config)
            
            assert result['success'] == True
            assert result['chronic_period_days'] == config['chronic_period_days']
            assert result['decay_rate'] == config['decay_rate']
            assert result['calculation_method'] == 'exponential_decay_engine'
    
    logger.info("✅ Edge case configurations test passed")
    return True

def run_all_tests():
    """Run all enhanced ACWR configuration tests"""
    logger.info("=" * 60)
    logger.info("Enhanced ACWR Different Configurations Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Short Chronic Period Configuration", test_short_chronic_period_configuration),
        ("Medium Chronic Period Configuration", test_medium_chronic_period_configuration),
        ("Long Chronic Period Configuration", test_long_chronic_period_configuration),
        ("High Decay Rate Configuration", test_high_decay_rate_configuration),
        ("Low Decay Rate Configuration", test_low_decay_rate_configuration),
        ("Configuration Comparison", test_configuration_comparison),
        ("Edge Case Configurations", test_edge_case_configurations)
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
        logger.info("🎉 All tests passed! Enhanced ACWR calculation with different configurations is working correctly.")
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

