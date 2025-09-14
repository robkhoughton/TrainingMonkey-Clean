#!/usr/bin/env python3
"""
Test script for Enhanced ACWR Edge Cases
Tests edge cases in enhanced ACWR calculation
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

def test_no_activities():
    """Test enhanced ACWR with no activities"""
    logger.info("Testing no activities edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration
    config = {
        'id': 1,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    # Mock empty database results
    mock_acute_activities = []
    mock_chronic_activities = []
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(1, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['acute_load_avg'] == 0.0
        assert result['enhanced_chronic_load'] == 0.0
        assert result['acute_trimp_avg'] == 0.0
        assert result['enhanced_chronic_trimp'] == 0.0
        assert result['enhanced_acute_chronic_ratio'] == 0
        assert result['enhanced_trimp_acute_chronic_ratio'] == 0
    
    logger.info("✅ No activities edge case test passed")
    return True

def test_single_activity():
    """Test enhanced ACWR with single activity"""
    logger.info("Testing single activity edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration
    config = {
        'id': 2,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    # Mock single activity
    mock_acute_activities = [
        ('2025-09-07', 10.0, 8.0)
    ]
    mock_chronic_activities = [
        ('2025-09-07', 10.0, 8.0)
    ]
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(2, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['acute_load_avg'] == 1.43  # 10.0 / 7.0 (single activity divided by 7 days)
        assert result['enhanced_chronic_load'] == 10.0
        assert result['acute_trimp_avg'] == 1.14  # 8.0 / 7.0 (single activity divided by 7 days)
        assert result['enhanced_chronic_trimp'] == 8.0
        assert result['enhanced_acute_chronic_ratio'] == 0.14  # 1.43 / 10.0
        assert result['enhanced_trimp_acute_chronic_ratio'] == 0.14  # 1.14 / 8.0
    
    logger.info("✅ Single activity edge case test passed")
    return True

def test_insufficient_acute_activities():
    """Test enhanced ACWR with insufficient acute activities (less than 7 days)"""
    logger.info("Testing insufficient acute activities edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration
    config = {
        'id': 3,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    # Mock insufficient acute activities (only 3 days)
    mock_acute_activities = [
        ('2025-09-05', 10.0, 8.0),
        ('2025-09-06', 12.0, 10.0),
        ('2025-09-07', 8.0, 6.0)
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
        
        result = service.calculate_enhanced_acwr(3, '2025-09-07', config)
        
        assert result['success'] == True
        # Should still calculate with available data
        assert result['acute_load_avg'] == 4.29  # (10+12+8)/7 = 4.29 (3 activities divided by 7 days)
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Insufficient acute activities edge case test passed")
    return True

def test_insufficient_chronic_activities():
    """Test enhanced ACWR with insufficient chronic activities"""
    logger.info("Testing insufficient chronic activities edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration
    config = {
        'id': 4,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    # Mock sufficient acute activities
    mock_acute_activities = [
        ('2025-09-01', 10.0, 8.0),
        ('2025-09-02', 12.0, 10.0),
        ('2025-09-03', 8.0, 6.0),
        ('2025-09-04', 15.0, 12.0),
        ('2025-09-05', 11.0, 9.0),
        ('2025-09-06', 9.0, 7.0),
        ('2025-09-07', 13.0, 11.0)
    ]
    
    # Mock insufficient chronic activities (only 5 days)
    mock_chronic_activities = [
        ('2025-09-03', 8.0, 6.0),
        ('2025-09-04', 15.0, 12.0),
        ('2025-09-05', 11.0, 9.0),
        ('2025-09-06', 9.0, 7.0),
        ('2025-09-07', 13.0, 11.0)
    ]
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(4, '2025-09-07', config)
        
        assert result['success'] == True
        # Should still calculate with available data
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Insufficient chronic activities edge case test passed")
    return True

def test_zero_values():
    """Test enhanced ACWR with zero values"""
    logger.info("Testing zero values edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration
    config = {
        'id': 5,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    # Mock activities with zero values
    mock_acute_activities = [
        ('2025-09-01', 0.0, 0.0),
        ('2025-09-02', 0.0, 0.0),
        ('2025-09-03', 0.0, 0.0),
        ('2025-09-04', 0.0, 0.0),
        ('2025-09-05', 0.0, 0.0),
        ('2025-09-06', 0.0, 0.0),
        ('2025-09-07', 0.0, 0.0)
    ]
    mock_chronic_activities = [
        ('2025-08-10', 0.0, 0.0),
        ('2025-08-11', 0.0, 0.0),
        ('2025-08-12', 0.0, 0.0),
        # ... more zero activities for chronic period
    ] * 15  # Simulate chronic period activities
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(5, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['acute_load_avg'] == 0.0
        assert result['enhanced_chronic_load'] == 0.0
        assert result['acute_trimp_avg'] == 0.0
        assert result['enhanced_chronic_trimp'] == 0.0
        assert result['enhanced_acute_chronic_ratio'] == 0
        assert result['enhanced_trimp_acute_chronic_ratio'] == 0
    
    logger.info("✅ Zero values edge case test passed")
    return True

def test_mixed_zero_and_nonzero_values():
    """Test enhanced ACWR with mixed zero and nonzero values"""
    logger.info("Testing mixed zero and nonzero values edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration
    config = {
        'id': 6,
        'chronic_period_days': 42,
        'decay_rate': 0.05
    }
    
    # Mock activities with mixed values
    mock_acute_activities = [
        ('2025-09-01', 10.0, 8.0),
        ('2025-09-02', 0.0, 0.0),
        ('2025-09-03', 8.0, 6.0),
        ('2025-09-04', 0.0, 0.0),
        ('2025-09-05', 11.0, 9.0),
        ('2025-09-06', 0.0, 0.0),
        ('2025-09-07', 13.0, 11.0)
    ]
    mock_chronic_activities = [
        ('2025-08-10', 10.0, 8.0),
        ('2025-08-11', 0.0, 0.0),
        ('2025-08-12', 8.0, 6.0),
        # ... more mixed activities for chronic period
    ] * 15  # Simulate chronic period activities
    
    with patch('acwr_configuration_service.db_utils.execute_query') as mock_execute:
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
        ]
        
        result = service.calculate_enhanced_acwr(6, '2025-09-07', config)
        
        assert result['success'] == True
        # Should handle mixed values correctly
        assert result['acute_load_avg'] > 0  # Should be positive despite zeros
        assert result['enhanced_chronic_load'] > 0  # Should be positive despite zeros
        assert 'enhanced_acute_chronic_ratio' in result
        assert 'enhanced_trimp_acute_chronic_ratio' in result
    
    logger.info("✅ Mixed zero and nonzero values edge case test passed")
    return True

def test_very_short_chronic_period():
    """Test enhanced ACWR with very short chronic period (28 days)"""
    logger.info("Testing very short chronic period edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration with minimum chronic period
    config = {
        'id': 7,
        'chronic_period_days': 28,
        'decay_rate': 0.1
    }
    
    # Mock activities
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
        
        result = service.calculate_enhanced_acwr(7, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['chronic_period_days'] == 28
        assert result['decay_rate'] == 0.1
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Very short chronic period edge case test passed")
    return True

def test_very_long_chronic_period():
    """Test enhanced ACWR with very long chronic period (90 days)"""
    logger.info("Testing very long chronic period edge case...")
    
    service = ACWRConfigurationService()
    
    # Configuration with maximum chronic period
    config = {
        'id': 8,
        'chronic_period_days': 90,
        'decay_rate': 0.01
    }
    
    # Mock activities
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
        
        result = service.calculate_enhanced_acwr(8, '2025-09-07', config)
        
        assert result['success'] == True
        assert result['chronic_period_days'] == 90
        assert result['decay_rate'] == 0.01
        assert 'acute_load_avg' in result
        assert 'enhanced_chronic_load' in result
        assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Very long chronic period edge case test passed")
    return True

def test_extreme_decay_rates():
    """Test enhanced ACWR with extreme decay rates"""
    logger.info("Testing extreme decay rates edge case...")
    
    service = ACWRConfigurationService()
    
    # Test configurations with extreme decay rates
    configs = [
        {'id': 9, 'chronic_period_days': 42, 'decay_rate': 0.001},  # Very low
        {'id': 10, 'chronic_period_days': 42, 'decay_rate': 1.0}    # Maximum
    ]
    
    for config in configs:
        # Mock activities
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
            
            result = service.calculate_enhanced_acwr(config['id'], '2025-09-07', config)
            
            assert result['success'] == True
            assert result['chronic_period_days'] == config['chronic_period_days']
            assert result['decay_rate'] == config['decay_rate']
            assert 'acute_load_avg' in result
            assert 'enhanced_chronic_load' in result
            assert 'enhanced_acute_chronic_ratio' in result
    
    logger.info("✅ Extreme decay rates edge case test passed")
    return True

def run_all_tests():
    """Run all enhanced ACWR edge case tests"""
    logger.info("=" * 60)
    logger.info("Enhanced ACWR Edge Cases Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("No Activities", test_no_activities),
        ("Single Activity", test_single_activity),
        ("Insufficient Acute Activities", test_insufficient_acute_activities),
        ("Insufficient Chronic Activities", test_insufficient_chronic_activities),
        ("Zero Values", test_zero_values),
        ("Mixed Zero and Nonzero Values", test_mixed_zero_and_nonzero_values),
        ("Very Short Chronic Period", test_very_short_chronic_period),
        ("Very Long Chronic Period", test_very_long_chronic_period),
        ("Extreme Decay Rates", test_extreme_decay_rates)
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
        logger.info("🎉 All tests passed! Enhanced ACWR edge cases are handled correctly.")
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
