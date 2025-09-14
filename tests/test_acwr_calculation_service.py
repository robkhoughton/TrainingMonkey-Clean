#!/usr/bin/env python3
"""
Test script for ACWR Calculation Service
Tests the fallback functionality and feature flag integration
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock db_utils before importing any modules that depend on it
sys.modules['db_utils'] = MagicMock()

from acwr_calculation_service import ACWRCalculationService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_service_initialization():
    """Test ACWRCalculationService initialization"""
    logger.info("Testing service initialization...")
    
    service = ACWRCalculationService()
    
    assert service is not None, "Service should be initialized"
    assert service.acwr_config_service is not None, "ACWR config service should be initialized"
    
    logger.info("✅ Service initialization test passed")
    return True

def test_enhanced_calculation_with_feature_enabled():
    """Test enhanced calculation when feature is enabled"""
    logger.info("Testing enhanced calculation with feature enabled...")
    
    service = ACWRCalculationService()
    
    # Mock feature flag to return True
    with patch('acwr_calculation_service.is_feature_enabled', return_value=True):
        # Mock the enhanced calculation
        with patch.object(service, '_calculate_enhanced_acwr') as mock_enhanced:
            mock_enhanced.return_value = {
                'calculation_type': 'enhanced',
                'configuration_used': 'default_enhanced',
                'chronic_period_days': 42,
                'decay_rate': 0.05,
                'enhanced_chronic_load': 10.5,
                'enhanced_chronic_trimp': 8.2,
                'enhanced_acute_chronic_ratio': 1.2,
                'enhanced_trimp_acute_chronic_ratio': 1.1,
                'enhanced_normalized_divergence': 0.1
            }
            
            result = service.calculate_acwr_for_user(1, '2025-09-07')
            
            assert result['calculation_type'] == 'enhanced', "Should use enhanced calculation"
            assert result['chronic_period_days'] == 42, "Should use enhanced chronic period"
            assert result['decay_rate'] == 0.05, "Should use enhanced decay rate"
            
            # Verify enhanced calculation was called
            mock_enhanced.assert_called_once_with(1, '2025-09-07')
    
    logger.info("✅ Enhanced calculation with feature enabled test passed")
    return True

def test_standard_calculation_with_feature_disabled():
    """Test standard calculation when feature is disabled"""
    logger.info("Testing standard calculation with feature disabled...")
    
    service = ACWRCalculationService()
    
    # Mock feature flag to return False
    with patch('acwr_calculation_service.is_feature_enabled', return_value=False):
        # Mock the standard calculation
        with patch.object(service, '_calculate_standard_acwr') as mock_standard:
            mock_standard.return_value = {
                'calculation_type': 'standard',
                'configuration_used': 'standard_28day',
                'chronic_period_days': 28,
                'decay_rate': 0.0,
                'enhanced_chronic_load': 8.5,
                'enhanced_chronic_trimp': 7.2,
                'enhanced_acute_chronic_ratio': 1.1,
                'enhanced_trimp_acute_chronic_ratio': 1.0,
                'enhanced_normalized_divergence': 0.1,
                'fallback_reason': 'feature_disabled'
            }
            
            result = service.calculate_acwr_for_user(4, '2025-09-07')
            
            assert result['calculation_type'] == 'standard', "Should use standard calculation"
            assert result['chronic_period_days'] == 28, "Should use standard chronic period"
            assert result['decay_rate'] == 0.0, "Should use no decay rate"
            assert result['fallback_reason'] == 'feature_disabled', "Should indicate fallback reason"
            
            # Verify standard calculation was called
            mock_standard.assert_called_once_with(4, '2025-09-07')
    
    logger.info("✅ Standard calculation with feature disabled test passed")
    return True

def test_fallback_on_enhanced_error():
    """Test fallback to standard calculation when enhanced calculation fails"""
    logger.info("Testing fallback on enhanced calculation error...")
    
    service = ACWRCalculationService()
    
    # Mock feature flag to return True
    with patch('acwr_calculation_service.is_feature_enabled', return_value=True):
        # Mock enhanced calculation to raise an exception
        with patch.object(service, '_calculate_enhanced_acwr', side_effect=Exception("Database error")):
            # Mock standard calculation
            with patch.object(service, '_calculate_standard_acwr') as mock_standard:
                mock_standard.return_value = {
                    'calculation_type': 'standard',
                    'configuration_used': 'standard_28day',
                    'chronic_period_days': 28,
                    'decay_rate': 0.0,
                    'enhanced_chronic_load': 8.5,
                    'enhanced_chronic_trimp': 7.2,
                    'enhanced_acute_chronic_ratio': 1.1,
                    'enhanced_trimp_acute_chronic_ratio': 1.0,
                    'enhanced_normalized_divergence': 0.1,
                    'fallback_reason': 'feature_disabled'
                }
                
                result = service.calculate_acwr_for_user(1, '2025-09-07')
                
                assert result['calculation_type'] == 'standard', "Should fallback to standard calculation"
                assert result['chronic_period_days'] == 28, "Should use standard chronic period"
                
                # Verify standard calculation was called as fallback
                mock_standard.assert_called_once_with(1, '2025-09-07')
    
    logger.info("✅ Fallback on enhanced calculation error test passed")
    return True

def test_calculation_summary():
    """Test getting calculation summary"""
    logger.info("Testing calculation summary...")
    
    service = ACWRCalculationService()
    
    # Mock feature flag
    with patch('acwr_calculation_service.is_feature_enabled', return_value=True):
        # Mock config service
        with patch.object(service.acwr_config_service, 'get_user_configuration') as mock_config:
            mock_config.return_value = {
                'name': 'default_enhanced',
                'chronic_period_days': 42,
                'decay_rate': 0.05
            }
            
            summary = service.get_acwr_calculation_summary(1, '2025-09-07')
            
            assert summary['user_id'] == 1, "Should have correct user ID"
            assert summary['activity_date'] == '2025-09-07', "Should have correct activity date"
            assert summary['enhanced_enabled'] == True, "Should show enhanced enabled"
            assert summary['calculation_type'] == 'enhanced', "Should show enhanced calculation type"
            assert summary['configuration']['name'] == 'default_enhanced', "Should have correct config name"
    
    logger.info("✅ Calculation summary test passed")
    return True

def test_calculation_summary_with_feature_disabled():
    """Test getting calculation summary when feature is disabled"""
    logger.info("Testing calculation summary with feature disabled...")
    
    service = ACWRCalculationService()
    
    # Mock feature flag to return False
    with patch('acwr_calculation_service.is_feature_enabled', return_value=False):
        summary = service.get_acwr_calculation_summary(4, '2025-09-07')
        
        assert summary['user_id'] == 4, "Should have correct user ID"
        assert summary['activity_date'] == '2025-09-07', "Should have correct activity date"
        assert summary['enhanced_enabled'] == False, "Should show enhanced disabled"
        assert summary['calculation_type'] == 'standard', "Should show standard calculation type"
        assert summary['configuration'] is None, "Should have no configuration"
    
    logger.info("✅ Calculation summary with feature disabled test passed")
    return True

def test_standard_calculation_logic():
    """Test the standard calculation logic"""
    logger.info("Testing standard calculation logic...")
    
    service = ACWRCalculationService()
    
    # Mock db_utils
    with patch('acwr_calculation_service.db_utils') as mock_db:
        mock_db.execute_query.side_effect = [
            [{'sum_load': 70.0, 'sum_trimp': 56.0}],  # Acute result
            [{'sum_load': 280.0, 'sum_trimp': 224.0}]  # Chronic result
        ]
        
        result = service._calculate_standard_acwr(1, '2025-09-07')
        
        assert result['calculation_type'] == 'standard', "Should be standard calculation"
        assert result['configuration_used'] == 'standard_28day', "Should use standard config"
        assert result['chronic_period_days'] == 28, "Should use 28-day period"
        assert result['decay_rate'] == 0.0, "Should have no decay"
        assert result['enhanced_chronic_load'] == 10.0, "Should calculate chronic load correctly (280/28)"
        assert result['enhanced_chronic_trimp'] == 8.0, "Should calculate chronic TRIMP correctly (224/28)"
        assert result['enhanced_acute_chronic_ratio'] == 1.0, "Should calculate ratio correctly (10/10)"
        assert result['enhanced_trimp_acute_chronic_ratio'] == 1.0, "Should calculate TRIMP ratio correctly (8/8)"
        assert result['fallback_reason'] == 'feature_disabled', "Should indicate fallback reason"
    
    logger.info("✅ Standard calculation logic test passed")
    return True

def test_comparison_methods():
    """Test comparing calculation methods"""
    logger.info("Testing comparison methods...")
    
    service = ACWRCalculationService()
    
    # Mock both calculation methods
    with patch.object(service, '_calculate_enhanced_acwr') as mock_enhanced:
        with patch.object(service, '_calculate_standard_acwr') as mock_standard:
            mock_enhanced.return_value = {
                'enhanced_chronic_load': 12.0,
                'enhanced_chronic_trimp': 10.0,
                'enhanced_acute_chronic_ratio': 1.2
            }
            
            mock_standard.return_value = {
                'enhanced_chronic_load': 10.0,
                'enhanced_chronic_trimp': 8.0,
                'enhanced_acute_chronic_ratio': 1.0
            }
            
            comparison = service.compare_calculation_methods(1, '2025-09-07')
            
            assert comparison['user_id'] == 1, "Should have correct user ID"
            assert comparison['activity_date'] == '2025-09-07', "Should have correct activity date"
            assert 'enhanced' in comparison, "Should have enhanced results"
            assert 'standard' in comparison, "Should have standard results"
            assert 'differences' in comparison, "Should have differences"
            
            # Check differences
            diff = comparison['differences']
            assert diff['chronic_load_difference'] == 2.0, "Should calculate load difference correctly"
            assert diff['chronic_trimp_difference'] == 2.0, "Should calculate TRIMP difference correctly"
            assert abs(diff['acute_chronic_ratio_difference'] - 0.2) < 0.001, "Should calculate ratio difference correctly"
            assert diff['chronic_load_percentage_diff'] == 20.0, "Should calculate percentage difference correctly"
    
    logger.info("✅ Comparison methods test passed")
    return True

def test_error_handling():
    """Test error handling in calculations"""
    logger.info("Testing error handling...")
    
    service = ACWRCalculationService()
    
    # Mock feature flag to return True
    with patch('acwr_calculation_service.is_feature_enabled', return_value=True):
        # Mock enhanced calculation to raise an exception
        with patch.object(service, '_calculate_enhanced_acwr', side_effect=Exception("Database error")):
            # Mock standard calculation to also raise an exception
            with patch.object(service, '_calculate_standard_acwr', side_effect=Exception("Standard error")):
                
                try:
                    result = service.calculate_acwr_for_user(1, '2025-09-07')
                    assert False, "Should have raised an exception"
                except Exception as e:
                    assert "Standard error" in str(e), "Should raise the standard calculation error"
    
    logger.info("✅ Error handling test passed")
    return True

def run_all_tests():
    """Run all ACWR calculation service tests"""
    logger.info("=" * 60)
    logger.info("ACWR Calculation Service Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Service Initialization", test_service_initialization),
        ("Enhanced Calculation with Feature Enabled", test_enhanced_calculation_with_feature_enabled),
        ("Standard Calculation with Feature Disabled", test_standard_calculation_with_feature_disabled),
        ("Fallback on Enhanced Error", test_fallback_on_enhanced_error),
        ("Calculation Summary", test_calculation_summary),
        ("Calculation Summary with Feature Disabled", test_calculation_summary_with_feature_disabled),
        ("Standard Calculation Logic", test_standard_calculation_logic),
        ("Comparison Methods", test_comparison_methods),
        ("Error Handling", test_error_handling)
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
        logger.info("🎉 All tests passed! ACWR Calculation Service is working correctly.")
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
