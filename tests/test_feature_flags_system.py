#!/usr/bin/env python3
"""
Test suite for the feature flag system
Tests the enhanced TRIMP calculation feature flag functionality
"""

import unittest
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.feature_flags import is_feature_enabled


class TestFeatureFlagsSystem(unittest.TestCase):
    """Test cases for the feature flag system"""
    
    def test_enhanced_trimp_calculation_admin_access(self):
        """Test that admin user (user_id=1) has access to enhanced TRIMP calculation"""
        # Admin should have access
        self.assertTrue(is_feature_enabled('enhanced_trimp_calculation', 1))
    
    def test_enhanced_trimp_calculation_beta_user_access(self):
        """Test that beta users (user_id=2, 3) have access to enhanced TRIMP calculation"""
        # Beta users should have access
        self.assertTrue(is_feature_enabled('enhanced_trimp_calculation', 2))
        self.assertTrue(is_feature_enabled('enhanced_trimp_calculation', 3))
    
    def test_enhanced_trimp_calculation_regular_user_access(self):
        """Test that regular users (user_id=4+) do not have access to enhanced TRIMP calculation"""
        # Regular users should not have access
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', 4))
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', 5))
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', 100))
    
    def test_enhanced_trimp_calculation_no_user_id(self):
        """Test that no user_id (None) does not have access to enhanced TRIMP calculation"""
        # No user should not have access
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', None))
    
    def test_enhanced_trimp_calculation_negative_user_id(self):
        """Test that negative user_id does not have access to enhanced TRIMP calculation"""
        # Negative user IDs should not have access
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', -1))
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', -100))
    
    def test_enhanced_trimp_calculation_zero_user_id(self):
        """Test that user_id=0 does not have access to enhanced TRIMP calculation"""
        # User ID 0 should not have access
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', 0))
    
    def test_settings_page_enabled_admin_access(self):
        """Test that admin user has access to settings page"""
        # Admin should have access to settings
        self.assertTrue(is_feature_enabled('settings_page_enabled', 1))
    
    def test_settings_page_enabled_beta_user_access(self):
        """Test that beta users have access to settings page"""
        # Beta users should have access to settings
        self.assertTrue(is_feature_enabled('settings_page_enabled', 2))
        self.assertTrue(is_feature_enabled('settings_page_enabled', 3))
    
    def test_settings_page_enabled_regular_user_access(self):
        """Test that regular users do not have access to settings page"""
        # Regular users should not have access to settings
        self.assertFalse(is_feature_enabled('settings_page_enabled', 4))
        self.assertFalse(is_feature_enabled('settings_page_enabled', 5))
    
    def test_unknown_feature_flag(self):
        """Test that unknown feature flags return False"""
        # Unknown feature flags should return False
        self.assertFalse(is_feature_enabled('unknown_feature', 1))
        self.assertFalse(is_feature_enabled('unknown_feature', 2))
        self.assertFalse(is_feature_enabled('unknown_feature', 4))
    
    def test_feature_flag_case_sensitivity(self):
        """Test that feature flag names are case sensitive"""
        # Feature flag names should be case sensitive
        self.assertFalse(is_feature_enabled('ENHANCED_TRIMP_CALCULATION', 1))
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation_', 1))
        self.assertFalse(is_feature_enabled('Enhanced_Trimp_Calculation', 1))
    
    def test_feature_flag_with_string_user_id(self):
        """Test feature flag behavior with string user IDs"""
        # String user IDs should be handled gracefully
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', '1'))
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', '2'))
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', 'admin'))
    
    def test_feature_flag_with_float_user_id(self):
        """Test feature flag behavior with float user IDs"""
        # Float user IDs should be handled gracefully
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', 1.0))
        self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', 2.5))
    
    def test_feature_flag_consistency(self):
        """Test that feature flag results are consistent across multiple calls"""
        # Results should be consistent
        result1 = is_feature_enabled('enhanced_trimp_calculation', 1)
        result2 = is_feature_enabled('enhanced_trimp_calculation', 1)
        self.assertEqual(result1, result2)
        
        result3 = is_feature_enabled('enhanced_trimp_calculation', 4)
        result4 = is_feature_enabled('enhanced_trimp_calculation', 4)
        self.assertEqual(result3, result4)
    
    def test_all_feature_flags_for_admin(self):
        """Test all feature flags for admin user"""
        # Admin should have access to all enabled features
        self.assertTrue(is_feature_enabled('enhanced_trimp_calculation', 1))
        self.assertTrue(is_feature_enabled('settings_page_enabled', 1))
    
    def test_all_feature_flags_for_beta_users(self):
        """Test all feature flags for beta users"""
        # Beta users should have access to all enabled features
        for user_id in [2, 3]:
            self.assertTrue(is_feature_enabled('enhanced_trimp_calculation', user_id))
            self.assertTrue(is_feature_enabled('settings_page_enabled', user_id))
    
    def test_all_feature_flags_for_regular_users(self):
        """Test all feature flags for regular users"""
        # Regular users should not have access to any enhanced features
        for user_id in [4, 5, 10, 100]:
            self.assertFalse(is_feature_enabled('enhanced_trimp_calculation', user_id))
            self.assertFalse(is_feature_enabled('settings_page_enabled', user_id))


class TestFeatureFlagsIntegration(unittest.TestCase):
    """Integration tests for feature flags with TRIMP calculation"""
    
    def test_trimp_calculation_with_feature_flag_enabled(self):
        """Test TRIMP calculation when feature flag is enabled"""
        from strava_training_load import calculate_training_load
        from unittest.mock import MagicMock
        
        # Mock activity and client
        activity = MagicMock()
        activity.id = 12345
        client = MagicMock()
        hr_config = {'resting_hr': 50, 'max_hr': 180, 'gender': 'male'}
        
        # Mock the calculate_training_load function to check feature flag usage
        with patch('strava_training_load.calculate_training_load') as mock_calc:
            mock_calc.return_value = {'trimp': 100.0, 'hr_stream_used': True}
            
            # Test with admin user (feature flag enabled)
            result = calculate_training_load(activity, client, hr_config, user_id=1)
            
            # Should call the function
            mock_calc.assert_called_once()
    
    def test_trimp_calculation_with_feature_flag_disabled(self):
        """Test TRIMP calculation when feature flag is disabled"""
        from strava_training_load import calculate_training_load
        from unittest.mock import MagicMock
        
        # Mock activity and client
        activity = MagicMock()
        activity.id = 12345
        client = MagicMock()
        hr_config = {'resting_hr': 50, 'max_hr': 180, 'gender': 'male'}
        
        # Mock the calculate_training_load function
        with patch('strava_training_load.calculate_training_load') as mock_calc:
            mock_calc.return_value = {'trimp': 100.0, 'hr_stream_used': False}
            
            # Test with regular user (feature flag disabled)
            result = calculate_training_load(activity, client, hr_config, user_id=4)
            
            # Should call the function
            mock_calc.assert_called_once()


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
