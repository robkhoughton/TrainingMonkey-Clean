#!/usr/bin/env python3
"""
Test script for ACWR Main Application Integration
Tests the integration of enhanced ACWR calculation into the main application flow
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
from exponential_decay_engine import ActivityData

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_acwr_integration():
    """Test enhanced ACWR integration with user-specific configuration"""
    logger.info("Testing enhanced ACWR integration...")
    
    service = ACWRCalculationService()
    
    # Create test activity data
    reference_date = date(2025, 9, 7)
    acute_activities = [
        ActivityData(date=date(2025, 9, 1), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 9, 2), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 9, 3), total_load_miles=8.0, trimp=6.0),
        ActivityData(date=date(2025, 9, 4), total_load_miles=15.0, trimp=12.0),
        ActivityData(date=date(2025, 9, 5), total_load_miles=11.0, trimp=9.0),
        ActivityData(date=date(2025, 9, 6), total_load_miles=9.0, trimp=7.0),
        ActivityData(date=date(2025, 9, 7), total_load_miles=13.0, trimp=11.0)
    ]
    
    chronic_activities = [
        ActivityData(date=date(2025, 8, 10), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 8, 11), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 8, 12), total_load_miles=8.0, trimp=6.0),
        # ... more activities for chronic period
    ] * 10  # Simulate chronic period activities
    
    # Mock feature flag enabled
    with patch('acwr_calculation_service.is_feature_enabled') as mock_feature_flag:
        mock_feature_flag.return_value = True
        
        # Mock enhanced ACWR calculation result
        with patch.object(service.acwr_config_service, 'calculate_enhanced_acwr') as mock_enhanced:
            mock_enhanced.return_value = {
                'success': True,
                'acute_load_avg': 11.14,
                'enhanced_chronic_load': 10.0,
                'acute_trimp_avg': 8.86,
                'enhanced_chronic_trimp': 8.0,
                'enhanced_acute_chronic_ratio': 1.11,
                'enhanced_trimp_acute_chronic_ratio': 1.11,
                'enhanced_normalized_divergence': 0.0,
                'calculation_method': 'exponential_decay_engine',
                'data_quality': 'good'
            }
            
            # Test the integration
            result = service.calculate_acwr(acute_activities, chronic_activities, reference_date, 1)
            
            # Verify enhanced calculation was used
            assert result['success'] == True
            assert result['calculation_method'] == 'exponential_decay_engine'
            assert result['acute_load_avg'] == 11.14
            assert result['chronic_load_avg'] == 10.0
            assert result['acute_chronic_ratio'] == 1.11
            assert result['data_quality'] == 'good'
            
            # Verify feature flag was checked
            mock_feature_flag.assert_called_once_with('enhanced_acwr_calculation', 1)
            mock_enhanced.assert_called_once_with(1, '2025-09-07')
    
    logger.info("✅ Enhanced ACWR integration test passed")
    return True

def test_standard_acwr_fallback():
    """Test fallback to standard ACWR when enhanced is disabled"""
    logger.info("Testing standard ACWR fallback...")
    
    service = ACWRCalculationService()
    
    # Create test activity data
    reference_date = date(2025, 9, 7)
    acute_activities = [
        ActivityData(date=date(2025, 9, 1), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 9, 2), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 9, 3), total_load_miles=8.0, trimp=6.0),
        ActivityData(date=date(2025, 9, 4), total_load_miles=15.0, trimp=12.0),
        ActivityData(date=date(2025, 9, 5), total_load_miles=11.0, trimp=9.0),
        ActivityData(date=date(2025, 9, 6), total_load_miles=9.0, trimp=7.0),
        ActivityData(date=date(2025, 9, 7), total_load_miles=13.0, trimp=11.0)
    ]
    
    chronic_activities = [
        ActivityData(date=date(2025, 8, 10), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 8, 11), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 8, 12), total_load_miles=8.0, trimp=6.0),
        # ... more activities for 28 days
    ] * 10  # Simulate 28 days of activities
    
    # Mock feature flag disabled
    with patch('acwr_calculation_service.is_feature_enabled') as mock_feature_flag:
        mock_feature_flag.return_value = False
        
        # Test the fallback
        result = service.calculate_acwr(acute_activities, chronic_activities, reference_date, 1)
        
        # Verify standard calculation was used
        assert result['success'] == True
        assert result['calculation_method'] == 'standard'
        
        # Verify calculated values
        expected_acute_load = sum(a.total_load_miles for a in acute_activities) / 7.0
        expected_chronic_load = sum(a.total_load_miles for a in chronic_activities) / 28.0
        expected_acute_trimp = sum(a.trimp for a in acute_activities) / 7.0
        expected_chronic_trimp = sum(a.trimp for a in chronic_activities) / 28.0
        
        assert abs(result['acute_load_avg'] - expected_acute_load) < 0.01
        assert abs(result['chronic_load_avg'] - expected_chronic_load) < 0.01
        assert abs(result['acute_trimp_avg'] - expected_acute_trimp) < 0.01
        assert abs(result['chronic_trimp_avg'] - expected_chronic_trimp) < 0.01
        
        # Verify feature flag was checked
        mock_feature_flag.assert_called_once_with('enhanced_acwr_calculation', 1)
    
    logger.info("✅ Standard ACWR fallback test passed")
    return True

def test_enhanced_calculation_failure_fallback():
    """Test fallback when enhanced calculation fails"""
    logger.info("Testing enhanced calculation failure fallback...")
    
    service = ACWRCalculationService()
    
    # Create test activity data
    reference_date = date(2025, 9, 7)
    acute_activities = [
        ActivityData(date=date(2025, 9, 1), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 9, 2), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 9, 3), total_load_miles=8.0, trimp=6.0),
        ActivityData(date=date(2025, 9, 4), total_load_miles=15.0, trimp=12.0),
        ActivityData(date=date(2025, 9, 5), total_load_miles=11.0, trimp=9.0),
        ActivityData(date=date(2025, 9, 6), total_load_miles=9.0, trimp=7.0),
        ActivityData(date=date(2025, 9, 7), total_load_miles=13.0, trimp=11.0)
    ]
    
    chronic_activities = [
        ActivityData(date=date(2025, 8, 10), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 8, 11), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 8, 12), total_load_miles=8.0, trimp=6.0),
        # ... more activities for chronic period
    ] * 10  # Simulate chronic period activities
    
    # Mock feature flag enabled
    with patch('acwr_calculation_service.is_feature_enabled') as mock_feature_flag:
        mock_feature_flag.return_value = True
        
        # Mock enhanced ACWR calculation failure
        with patch.object(service.acwr_config_service, 'calculate_enhanced_acwr') as mock_enhanced:
            mock_enhanced.return_value = {
                'success': False,
                'error': 'Database connection failed',
                'fallback_to_standard': True
            }
            
            # Test the fallback
            result = service.calculate_acwr(acute_activities, chronic_activities, reference_date, 1)
            
            # Verify fallback to standard calculation
            assert result['success'] == True
            assert result['calculation_method'] == 'standard'
            
            # Verify standard calculation was performed
            expected_acute_load = sum(a.total_load_miles for a in acute_activities) / 7.0
            expected_chronic_load = sum(a.total_load_miles for a in chronic_activities) / 28.0
            
            assert abs(result['acute_load_avg'] - expected_acute_load) < 0.01
            assert abs(result['chronic_load_avg'] - expected_chronic_load) < 0.01
    
    logger.info("✅ Enhanced calculation failure fallback test passed")
    return True

def test_error_handling():
    """Test error handling in main application integration"""
    logger.info("Testing error handling...")
    
    service = ACWRCalculationService()
    
    # Create test activity data
    reference_date = date(2025, 9, 7)
    acute_activities = [
        ActivityData(date=date(2025, 9, 1), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 9, 2), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 9, 3), total_load_miles=8.0, trimp=6.0),
        ActivityData(date=date(2025, 9, 4), total_load_miles=15.0, trimp=12.0),
        ActivityData(date=date(2025, 9, 5), total_load_miles=11.0, trimp=9.0),
        ActivityData(date=date(2025, 9, 6), total_load_miles=9.0, trimp=7.0),
        ActivityData(date=date(2025, 9, 7), total_load_miles=13.0, trimp=11.0)
    ]
    
    chronic_activities = [
        ActivityData(date=date(2025, 8, 10), total_load_miles=10.0, trimp=8.0),
        ActivityData(date=date(2025, 8, 11), total_load_miles=12.0, trimp=10.0),
        ActivityData(date=date(2025, 8, 12), total_load_miles=8.0, trimp=6.0),
        # ... more activities for chronic period
    ] * 10  # Simulate chronic period activities
    
    # Mock feature flag enabled but service throws exception
    with patch('acwr_calculation_service.is_feature_enabled') as mock_feature_flag:
        mock_feature_flag.return_value = True
        
        with patch.object(service.acwr_config_service, 'calculate_enhanced_acwr') as mock_enhanced:
            mock_enhanced.side_effect = Exception("Service error")
            
            # Test error handling
            result = service.calculate_acwr(acute_activities, chronic_activities, reference_date, 1)
            
            # Verify fallback to standard calculation
            assert result['success'] == True
            assert result['calculation_method'] == 'standard'
    
    logger.info("✅ Error handling test passed")
    return True

def test_empty_activities():
    """Test handling of empty activity lists"""
    logger.info("Testing empty activities handling...")
    
    service = ACWRCalculationService()
    
    # Create test with empty activities
    reference_date = date(2025, 9, 7)
    acute_activities = []
    chronic_activities = []
    
    # Mock feature flag disabled
    with patch('acwr_calculation_service.is_feature_enabled') as mock_feature_flag:
        mock_feature_flag.return_value = False
        
        # Test with empty activities
        result = service.calculate_acwr(acute_activities, chronic_activities, reference_date, 1)
        
        # Verify standard calculation handles empty data
        assert result['success'] == True
        assert result['calculation_method'] == 'standard'
        assert result['acute_load_avg'] == 0.0
        assert result['chronic_load_avg'] == 0.0
        assert result['acute_trimp_avg'] == 0.0
        assert result['chronic_trimp_avg'] == 0.0
        assert result['acute_chronic_ratio'] == 0
        assert result['trimp_acute_chronic_ratio'] == 0
    
    logger.info("✅ Empty activities handling test passed")
    return True

def run_all_tests():
    """Run all main application integration tests"""
    logger.info("=" * 60)
    logger.info("ACWR Main Application Integration Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Enhanced ACWR Integration", test_enhanced_acwr_integration),
        ("Standard ACWR Fallback", test_standard_acwr_fallback),
        ("Enhanced Calculation Failure Fallback", test_enhanced_calculation_failure_fallback),
        ("Error Handling", test_error_handling),
        ("Empty Activities Handling", test_empty_activities)
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
        logger.info("🎉 All tests passed! ACWR main application integration is working correctly.")
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
