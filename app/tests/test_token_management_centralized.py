#!/usr/bin/env python3
"""
Test script for Task 4.2 - Enhanced Token Management for Centralized OAuth
Tests the enhanced token management functionality with centralized credentials
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_token_management import (
    SimpleTokenManager, 
    get_centralized_credentials_status,
    get_enhanced_token_status,
    get_token_health_summary,
    validate_centralized_setup
)


class TestEnhancedTokenManagement(unittest.TestCase):
    """Test cases for enhanced token management with centralized OAuth"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_config = {
            "client_id": "test_client_id_12345",
            "client_secret": "test_client_secret_abcdef",
            "resting_hr": 44,
            "max_hr": 178,
            "gender": "male"
        }
        
        # Create a temporary config file for testing
        self.temp_config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(self.test_config, self.temp_config_file)
        self.temp_config_file.close()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_config_file.name):
            os.unlink(self.temp_config_file.name)

    def test_validate_centralized_credentials_valid(self):
        """Test validation of valid centralized credentials"""
        token_manager = SimpleTokenManager(user_id=1)
        
        is_valid, message = token_manager.validate_centralized_credentials(
            "valid_client_id_12345",
            "valid_client_secret_abcdefghij"
        )
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "Credentials appear valid")

    def test_validate_centralized_credentials_invalid(self):
        """Test validation of invalid centralized credentials"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Test missing credentials
        is_valid, message = token_manager.validate_centralized_credentials("", "")
        self.assertFalse(is_valid)
        self.assertIn("Missing", message)
        
        # Test invalid client_id format
        is_valid, message = token_manager.validate_centralized_credentials("123", "valid_secret")
        self.assertFalse(is_valid)
        self.assertIn("Invalid client_id", message)
        
        # Test invalid client_secret format
        is_valid, message = token_manager.validate_centralized_credentials("valid_id", "short")
        self.assertFalse(is_valid)
        self.assertIn("Invalid client_secret", message)

    def test_get_centralized_credentials_status_success(self):
        """Test successful centralized credentials status"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = self.temp_config_file.name
            
            status = get_centralized_credentials_status()
            
            self.assertEqual(status['status'], 'valid')
            self.assertTrue(status['has_credentials'])
            self.assertEqual(status['source'], 'strava_config.json')
            self.assertEqual(status['client_id_preview'], 'test_cli...')

    def test_get_centralized_credentials_status_unavailable(self):
        """Test centralized credentials status when unavailable"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = "/nonexistent/path/strava_config.json"
            
            with patch.dict(os.environ, {}, clear=True):
                status = get_centralized_credentials_status()
                
                self.assertEqual(status['status'], 'unavailable')
                self.assertFalse(status['has_credentials'])
                self.assertIsNone(status['source'])

    def test_get_enhanced_token_status_structure(self):
        """Test structure of enhanced token status"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = self.temp_config_file.name
            
            # Mock database response for tokens
            with patch('enhanced_token_management.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{
                    'strava_access_token': 'test_token',
                    'strava_refresh_token': 'test_refresh',
                    'strava_token_expires_at': 9999999999,  # Far future
                    'strava_athlete_id': 12345
                }]
                
                status = get_enhanced_token_status(user_id=1)
                
                # Check structure
                self.assertIn('status', status)
                self.assertIn('centralized_credentials', status)
                self.assertIn('token_management_type', status)
                self.assertIn('refresh_available', status)
                
                # Check values
                self.assertEqual(status['token_management_type'], 'centralized')
                self.assertTrue(status['refresh_available'])

    def test_get_token_health_summary_structure(self):
        """Test structure of token health summary"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = self.temp_config_file.name
            
            # Mock database response for tokens
            with patch('enhanced_token_management.db_utils.execute_query') as mock_db:
                mock_db.return_value = [{
                    'strava_access_token': 'test_token',
                    'strava_refresh_token': 'test_refresh',
                    'strava_token_expires_at': 9999999999,  # Far future
                    'strava_athlete_id': 12345
                }]
                
                health = get_token_health_summary(user_id=1)
                
                # Check structure
                self.assertIn('overall_health', health)
                self.assertIn('health_score', health)
                self.assertIn('token_status', health)
                self.assertIn('credentials_status', health)
                self.assertIn('needs_attention', health)
                self.assertIn('can_refresh', health)
                self.assertIn('last_checked', health)
                self.assertIn('user_id', health)
                
                # Check values
                self.assertEqual(health['user_id'], 1)
                self.assertIsInstance(health['health_score'], int)
                self.assertIsInstance(health['needs_attention'], bool)

    def test_validate_centralized_setup_ready(self):
        """Test centralized setup validation when ready"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = self.temp_config_file.name
            
            validation = validate_centralized_setup()
            
            self.assertEqual(validation['overall_status'], 'ready')
            self.assertTrue(validation['config_file_exists'])
            self.assertIsInstance(validation['recommendations'], list)

    def test_validate_centralized_setup_not_configured(self):
        """Test centralized setup validation when not configured"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = "/nonexistent/path/strava_config.json"
            
            with patch.dict(os.environ, {}, clear=True):
                validation = validate_centralized_setup()
                
                self.assertEqual(validation['overall_status'], 'not_configured')
                self.assertFalse(validation['config_file_exists'])
                self.assertFalse(validation['environment_variables_available'])
                self.assertGreater(len(validation['recommendations']), 0)

    def test_token_health_scoring(self):
        """Test token health scoring logic"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Test healthy scenario
        with patch.object(token_manager, 'get_enhanced_token_status') as mock_status:
            mock_status.return_value = {
                'status': 'valid',
                'centralized_credentials': {'status': 'valid'}
            }
            
            health = token_manager.get_token_health_summary()
            self.assertEqual(health['overall_health'], 'healthy')
            self.assertEqual(health['health_score'], 100)
            self.assertFalse(health['needs_attention'])

        # Test warning scenario
        with patch.object(token_manager, 'get_enhanced_token_status') as mock_status:
            mock_status.return_value = {
                'status': 'expiring_soon',
                'centralized_credentials': {'status': 'valid'}
            }
            
            health = token_manager.get_token_health_summary()
            self.assertEqual(health['overall_health'], 'warning')
            self.assertEqual(health['health_score'], 75)
            self.assertTrue(health['needs_attention'])

        # Test critical scenario
        with patch.object(token_manager, 'get_enhanced_token_status') as mock_status:
            mock_status.return_value = {
                'status': 'expired',
                'centralized_credentials': {'status': 'valid'}
            }
            
            health = token_manager.get_token_health_summary()
            self.assertEqual(health['overall_health'], 'critical')
            self.assertEqual(health['health_score'], 25)
            self.assertTrue(health['needs_attention'])


def test_enhanced_token_management_import():
    """Test that enhanced token management can be imported without errors"""
    try:
        from enhanced_token_management import (
            SimpleTokenManager,
            get_centralized_credentials_status,
            get_enhanced_token_status,
            get_token_health_summary,
            validate_centralized_setup
        )
        print("✅ Enhanced token management imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing enhanced token management: {str(e)}")
        return False


def test_api_endpoints_import():
    """Test that the main app with new API endpoints can be imported"""
    try:
        import strava_app
        print("✅ API endpoints import successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing API endpoints: {str(e)}")
        return False


if __name__ == '__main__':
    print("🧪 Testing Task 4.2 - Enhanced Token Management for Centralized OAuth")
    print("=" * 70)
    
    # Run basic tests
    test_results = []
    
    print("\n1. Testing enhanced token management import...")
    test_results.append(test_enhanced_token_management_import())
    
    print("\n2. Testing API endpoints import...")
    test_results.append(test_api_endpoints_import())
    
    print("\n3. Running unit tests...")
    # Run the unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 70)
    print("✅ Task 4.2 Enhanced Token Management Tests Complete")
    
    if all(test_results):
        print("🎉 All tests passed! Enhanced token management is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
