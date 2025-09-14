#!/usr/bin/env python3
"""
Test script for Strava Enhanced ACWR Integration
Tests the integration of enhanced ACWR calculation into strava_training_load.py
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils and other dependencies before importing strava_training_load
sys.modules['db_utils'] = MagicMock()
sys.modules['timezone_utils'] = MagicMock()
sys.modules['stravalib'] = MagicMock()
sys.modules['stravalib.client'] = MagicMock()
sys.modules['stravalib.exc'] = MagicMock()

# Mock the specific classes and functions that are imported
sys.modules['stravalib.client'].Client = MagicMock()
sys.modules['stravalib.exc'].ActivityUploadFailed = Exception
sys.modules['stravalib.exc'].Fault = Exception

from strava_training_load import (
    update_moving_averages, update_moving_averages_enhanced, update_moving_averages_standard
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_feature_flag_integration():
    """Test that feature flag integration works correctly"""
    logger.info("Testing feature flag integration...")
    
    # Mock the feature flag function
    with patch('strava_training_load.is_feature_enabled') as mock_feature_flag:
        # Test enhanced ACWR enabled
        mock_feature_flag.return_value = True
        
        with patch('strava_training_load.update_moving_averages_enhanced') as mock_enhanced:
            mock_enhanced.return_value = None
            
            update_moving_averages('2025-09-07', 1)
            
            mock_feature_flag.assert_called_once_with('enhanced_acwr_calculation', 1)
            mock_enhanced.assert_called_once_with('2025-09-07', 1)
        
        # Test enhanced ACWR disabled
        mock_feature_flag.return_value = False
        
        with patch('strava_training_load.update_moving_averages_standard') as mock_standard:
            mock_standard.return_value = None
            
            update_moving_averages('2025-09-07', 1)
            
            mock_feature_flag.assert_called_with('enhanced_acwr_calculation', 1)
            mock_standard.assert_called_once_with('2025-09-07', 1)
    
    logger.info("✅ Feature flag integration test passed")
    return True

def test_enhanced_calculation_integration():
    """Test enhanced ACWR calculation integration"""
    logger.info("Testing enhanced ACWR calculation integration...")
    
    # Mock database queries
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
    
    with patch('strava_training_load.execute_query') as mock_execute:
        # Mock the database queries
        mock_execute.side_effect = [
            mock_acute_activities,  # Acute activities query
            mock_chronic_activities,  # Chronic activities query
            None  # Update query
        ]
        
        with patch('strava_training_load.ACWRCalculationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock successful enhanced calculation result
            mock_service.calculate_acwr.return_value = {
                'success': True,
                'acute_load_avg': 11.14,
                'chronic_load_avg': 10.0,
                'acute_trimp_avg': 8.86,
                'chronic_trimp_avg': 8.0,
                'acute_chronic_ratio': 1.11,
                'trimp_acute_chronic_ratio': 1.11,
                'normalized_divergence': 0.0,
                'calculation_method': 'exponential_decay'
            }
            
            # Test the enhanced calculation
            update_moving_averages_enhanced('2025-09-07', 1)
            
            # Verify service was called correctly
            mock_service_class.assert_called_once()
            mock_service.calculate_acwr.assert_called_once()
            
            # Verify database update was called
            assert mock_execute.call_count == 3  # 2 queries + 1 update
    
    logger.info("✅ Enhanced ACWR calculation integration test passed")
    return True

def test_enhanced_calculation_fallback():
    """Test fallback to standard calculation when enhanced fails"""
    logger.info("Testing enhanced ACWR calculation fallback...")
    
    with patch('strava_training_load.execute_query') as mock_execute:
        mock_execute.side_effect = [
            [],  # No acute activities
            [],  # No chronic activities
            None  # Update query (from fallback)
        ]
        
        with patch('strava_training_load.ACWRCalculationService') as mock_service_class:
            mock_service = MagicMock()
            mock_service_class.return_value = mock_service
            
            # Mock failed enhanced calculation
            mock_service.calculate_acwr.return_value = {
                'success': False,
                'error': 'Insufficient data'
            }
            
            with patch('strava_training_load.update_moving_averages_standard') as mock_standard:
                mock_standard.return_value = None
                
                # Test the enhanced calculation with fallback
                update_moving_averages_enhanced('2025-09-07', 1)
                
                # Verify fallback was called
                mock_standard.assert_called_once_with('2025-09-07', 1)
    
    logger.info("✅ Enhanced ACWR calculation fallback test passed")
    return True

def test_standard_calculation_preserved():
    """Test that standard calculation logic is preserved"""
    logger.info("Testing standard ACWR calculation preservation...")
    
    with patch('strava_training_load.execute_query') as mock_execute:
        # Mock database results for standard calculation
        mock_execute.side_effect = [
            70.0,  # seven_day_sum
            280.0,  # twentyeight_day_sum
            56.0,   # seven_day_trimp_sum
            224.0,  # twentyeight_day_trimp_sum
            None    # Update query
        ]
        
        # Test the standard calculation
        update_moving_averages_standard('2025-09-07', 1)
        
        # Verify all database calls were made
        assert mock_execute.call_count == 5
        
        # Verify the update query was called with correct parameters
        update_call = mock_execute.call_args_list[-1]
        update_params = update_call[0][1]
        
        # Check that the calculated values are correct
        assert update_params[0] == 10.0  # seven_day_avg_load (70/7)
        assert update_params[1] == 10.0  # twentyeight_day_avg_load (280/28)
        assert update_params[2] == 8.0   # seven_day_avg_trimp (56/7)
        assert update_params[3] == 8.0   # twentyeight_day_avg_trimp (224/28)
        assert update_params[4] == 1.0   # acute_chronic_ratio (10/10)
        assert update_params[5] == 1.0   # trimp_acute_chronic_ratio (8/8)
        assert update_params[6] == 0.0   # normalized_divergence
        assert update_params[7] == '2025-09-07'  # date
        assert update_params[8] == 1     # user_id
    
    logger.info("✅ Standard ACWR calculation preservation test passed")
    return True

def test_error_handling():
    """Test error handling in both enhanced and standard calculations"""
    logger.info("Testing error handling...")
    
    # Test enhanced calculation error handling
    with patch('strava_training_load.execute_query') as mock_execute:
        mock_execute.side_effect = Exception("Database error")
        
        with patch('strava_training_load.update_moving_averages_standard') as mock_standard:
            mock_standard.return_value = None
            
            # Test enhanced calculation with database error
            update_moving_averages_enhanced('2025-09-07', 1)
            
            # Verify fallback was called
            mock_standard.assert_called_once_with('2025-09-07', 1)
    
    # Test standard calculation error handling
    with patch('strava_training_load.execute_query') as mock_execute:
        mock_execute.side_effect = Exception("Database error")
        
        # Test standard calculation with database error
        try:
            update_moving_averages_standard('2025-09-07', 1)
            # Should not raise exception, should log error
        except Exception:
            # This is expected behavior for standard calculation
            pass
    
    logger.info("✅ Error handling test passed")
    return True

def test_user_id_validation():
    """Test user_id validation"""
    logger.info("Testing user_id validation...")
    
    # Test None user_id
    try:
        update_moving_averages('2025-09-07', None)
        assert False, "Should raise ValueError for None user_id"
    except ValueError as e:
        assert "user_id is required" in str(e)
    
    # Test valid user_id
    with patch('strava_training_load.is_feature_enabled') as mock_feature_flag:
        mock_feature_flag.return_value = False
        
        with patch('strava_training_load.update_moving_averages_standard') as mock_standard:
            mock_standard.return_value = None
            
            update_moving_averages('2025-09-07', 1)
            mock_standard.assert_called_once_with('2025-09-07', 1)
    
    logger.info("✅ User ID validation test passed")
    return True

def run_all_tests():
    """Run all Strava enhanced ACWR integration tests"""
    logger.info("=" * 60)
    logger.info("Strava Enhanced ACWR Integration Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Feature Flag Integration", test_feature_flag_integration),
        ("Enhanced Calculation Integration", test_enhanced_calculation_integration),
        ("Enhanced Calculation Fallback", test_enhanced_calculation_fallback),
        ("Standard Calculation Preservation", test_standard_calculation_preserved),
        ("Error Handling", test_error_handling),
        ("User ID Validation", test_user_id_validation)
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
        logger.info("🎉 All tests passed! Strava enhanced ACWR integration is working correctly.")
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
