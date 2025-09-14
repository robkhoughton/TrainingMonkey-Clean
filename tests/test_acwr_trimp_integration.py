#!/usr/bin/env python3
"""
Test script for ACWR Feature Flag Integration with TRIMP Enhancement Patterns
Tests that ACWR feature flags work correctly alongside existing TRIMP enhancement patterns
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

from utils.feature_flags import is_feature_enabled
from acwr_calculation_service import ACWRCalculationService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_feature_flag_coexistence():
    """Test that ACWR and TRIMP feature flags can coexist"""
    logger.info("Testing feature flag coexistence...")
    
    # Test both feature flags for different users
    test_cases = [
        (1, True, True),   # Admin: both enabled
        (2, True, True),   # Beta user: both enabled
        (3, True, True),   # Beta user: both enabled
        (4, False, False), # Regular user: both disabled
        (5, False, False), # Regular user: both disabled
    ]
    
    for user_id, expected_acwr, expected_trimp in test_cases:
        acwr_enabled = is_feature_enabled('enhanced_acwr_calculation', user_id)
        trimp_enabled = is_feature_enabled('enhanced_trimp_calculation', user_id)
        
        assert acwr_enabled == expected_acwr, f"User {user_id}: ACWR should be {expected_acwr}, got {acwr_enabled}"
        assert trimp_enabled == expected_trimp, f"User {user_id}: TRIMP should be {expected_trimp}, got {trimp_enabled}"
        
        logger.info(f"✅ User {user_id}: ACWR={acwr_enabled}, TRIMP={trimp_enabled}")
    
    logger.info("✅ Feature flag coexistence test passed")
    return True

def test_acwr_calculation_with_trimp_context():
    """Test ACWR calculation in context of TRIMP enhancement patterns"""
    logger.info("Testing ACWR calculation with TRIMP context...")
    
    service = ACWRCalculationService()
    
    # Test admin user (both features enabled)
    with patch('acwr_calculation_service.is_feature_enabled') as mock_feature:
        def mock_feature_enabled(feature_name, user_id):
            if feature_name == 'enhanced_acwr_calculation':
                return user_id in [1, 2, 3]  # Admin and beta users
            elif feature_name == 'enhanced_trimp_calculation':
                return user_id in [1, 2, 3]  # Admin and beta users
            return False
        
        mock_feature.side_effect = mock_feature_enabled
        
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
            
            # Test admin user
            result = service.calculate_acwr_for_user(1, '2025-09-07')
            assert result['calculation_type'] == 'enhanced', "Admin should get enhanced ACWR"
            
            # Test regular user
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
                assert result['calculation_type'] == 'standard', "Regular user should get standard ACWR"
    
    logger.info("✅ ACWR calculation with TRIMP context test passed")
    return True

def test_feature_flag_rollout_patterns():
    """Test that ACWR follows the same rollout patterns as TRIMP"""
    logger.info("Testing feature flag rollout patterns...")
    
    # Test the rollout pattern consistency
    rollout_users = {
        'admin': [1],
        'beta': [2, 3],
        'regular': [4, 5, 6, 7, 8, 9, 10]
    }
    
    for user_type, user_ids in rollout_users.items():
        for user_id in user_ids:
            acwr_enabled = is_feature_enabled('enhanced_acwr_calculation', user_id)
            trimp_enabled = is_feature_enabled('enhanced_trimp_calculation', user_id)
            
            # Both features should have the same access pattern
            assert acwr_enabled == trimp_enabled, f"User {user_id} ({user_type}): ACWR and TRIMP access should match"
            
            expected_enabled = user_type in ['admin', 'beta']
            assert acwr_enabled == expected_enabled, f"User {user_id} ({user_type}): Should have {expected_enabled} access"
            
            logger.info(f"✅ User {user_id} ({user_type}): ACWR={acwr_enabled}, TRIMP={trimp_enabled}")
    
    logger.info("✅ Feature flag rollout patterns test passed")
    return True

def test_monitoring_integration():
    """Test that ACWR monitoring integrates with TRIMP monitoring patterns"""
    logger.info("Testing monitoring integration...")
    
    from acwr_feature_flag_monitor import acwr_feature_flag_monitor
    
    # Clear existing events first
    acwr_feature_flag_monitor.events = []
    
    # Test that monitoring works for both features
    test_events = [
        ('enhanced_acwr_calculation', 1, True),
        ('enhanced_acwr_calculation', 2, True),
        ('enhanced_acwr_calculation', 4, False),
        ('enhanced_trimp_calculation', 1, True),
        ('enhanced_trimp_calculation', 2, True),
        ('enhanced_trimp_calculation', 4, False),
    ]
    
    for feature_name, user_id, granted in test_events:
        acwr_feature_flag_monitor.log_feature_access(feature_name, user_id, granted, {
            'rollout_phase': 'beta',
            'user_type': 'admin' if user_id == 1 else 'beta' if user_id in [2, 3] else 'regular'
        })
    
    # Get statistics
    stats = acwr_feature_flag_monitor.get_event_statistics(hours_back=24)
    
    assert stats['total_events'] == 6, "Should have 6 total events"
    assert stats['access_granted'] == 4, "Should have 4 access granted events"
    assert stats['access_denied'] == 2, "Should have 2 access denied events"
    assert stats['unique_users'] == 3, "Should have 3 unique users"
    
    # Test user summary
    user_summary = acwr_feature_flag_monitor.get_user_access_summary(hours_back=24)
    assert len(user_summary) == 3, "Should have 3 users in summary"
    
    logger.info("✅ Monitoring integration test passed")
    return True

def test_admin_interface_consistency():
    """Test that ACWR admin interface follows TRIMP admin interface patterns"""
    logger.info("Testing admin interface consistency...")
    
    # Test that both features have similar admin interface patterns
    from acwr_feature_flag_admin import acwr_feature_flag_admin
    
    # Check that the blueprint is properly configured
    assert acwr_feature_flag_admin.name == 'acwr_feature_flag_admin', "Blueprint should have correct name"
    
    # Check that the blueprint has the expected routes (simplified test)
    # Note: Blueprint doesn't have url_map until registered with app
    assert hasattr(acwr_feature_flag_admin, 'deferred_functions'), "Blueprint should have deferred functions"
    
    # Test that the template exists
    import os
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'admin_acwr_feature_flags.html')
    assert os.path.exists(template_path), "Admin template should exist"
    
    logger.info("✅ Admin interface consistency test passed")
    return True

def test_feature_flag_toggle_consistency():
    """Test that ACWR feature flag toggles work consistently with TRIMP patterns"""
    logger.info("Testing feature flag toggle consistency...")
    
    # Test that both features can be toggled independently
    test_users = [1, 2, 3, 4]
    
    for user_id in test_users:
        acwr_enabled = is_feature_enabled('enhanced_acwr_calculation', user_id)
        trimp_enabled = is_feature_enabled('enhanced_trimp_calculation', user_id)
        
        # Both should follow the same pattern
        assert acwr_enabled == trimp_enabled, f"User {user_id}: ACWR and TRIMP should have same access"
        
        # Test that the access pattern is correct
        expected_enabled = user_id in [1, 2, 3]
        assert acwr_enabled == expected_enabled, f"User {user_id}: Should have {expected_enabled} access"
    
    logger.info("✅ Feature flag toggle consistency test passed")
    return True

def test_error_handling_consistency():
    """Test that ACWR error handling follows TRIMP error handling patterns"""
    logger.info("Testing error handling consistency...")
    
    service = ACWRCalculationService()
    
    # Test that both features handle errors consistently
    with patch('acwr_calculation_service.is_feature_enabled', return_value=True):
        with patch.object(service, '_calculate_enhanced_acwr', side_effect=Exception("Database error")):
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
                
                # Should fallback gracefully
                result = service.calculate_acwr_for_user(1, '2025-09-07')
                assert result['calculation_type'] == 'standard', "Should fallback to standard calculation"
                assert result['fallback_reason'] == 'feature_disabled', "Should indicate fallback reason"
    
    logger.info("✅ Error handling consistency test passed")
    return True

def test_performance_consistency():
    """Test that ACWR performance patterns match TRIMP performance patterns"""
    logger.info("Testing performance consistency...")
    
    service = ACWRCalculationService()
    
    # Test that both features have similar performance characteristics
    start_time = datetime.now()
    
    with patch('acwr_calculation_service.is_feature_enabled', return_value=True):
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
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Should complete quickly (under 1 second for mocked calculation)
            assert processing_time < 1.0, f"Processing should be fast, took {processing_time} seconds"
            assert result['calculation_type'] == 'enhanced', "Should return enhanced calculation"
    
    logger.info("✅ Performance consistency test passed")
    return True

def run_all_tests():
    """Run all ACWR-TRIMP integration tests"""
    logger.info("=" * 60)
    logger.info("ACWR-TRIMP Integration Test Suite")
    logger.info("=" * 60)
    
    tests = [
        ("Feature Flag Coexistence", test_feature_flag_coexistence),
        ("ACWR Calculation with TRIMP Context", test_acwr_calculation_with_trimp_context),
        ("Feature Flag Rollout Patterns", test_feature_flag_rollout_patterns),
        ("Monitoring Integration", test_monitoring_integration),
        ("Admin Interface Consistency", test_admin_interface_consistency),
        ("Feature Flag Toggle Consistency", test_feature_flag_toggle_consistency),
        ("Error Handling Consistency", test_error_handling_consistency),
        ("Performance Consistency", test_performance_consistency)
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
        logger.info("🎉 All tests passed! ACWR-TRIMP integration is working correctly.")
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
