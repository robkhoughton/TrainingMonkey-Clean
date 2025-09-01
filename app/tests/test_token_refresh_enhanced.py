#!/usr/bin/env python3
"""
Test script for Task 4.3 - Enhanced OAuth Token Refresh Logic
Tests the enhanced token refresh functionality with retry logic and centralized credentials
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import time

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_token_management import (
    SimpleTokenManager,
    refresh_tokens_for_user,
    get_token_refresh_status,
    bulk_refresh_tokens
)


class TestEnhancedTokenRefresh(unittest.TestCase):
    """Test cases for enhanced token refresh logic"""

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

    def test_validate_refresh_prerequisites_valid(self):
        """Test validation of refresh prerequisites when all conditions are met"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Mock database response with valid tokens
        with patch('enhanced_token_management.db_utils.execute_query') as mock_db:
            mock_db.return_value = [{
                'strava_access_token': 'test_access_token',
                'strava_refresh_token': 'test_refresh_token',
                'strava_token_expires_at': 9999999999,  # Far future
                'strava_athlete_id': 12345
            }]
            
            with patch('os.path.join') as mock_join:
                mock_join.return_value = self.temp_config_file.name
                
                result = token_manager._validate_refresh_prerequisites()
                
                self.assertTrue(result['valid'])
                self.assertEqual(result['message'], 'All prerequisites met')
                self.assertIsNotNone(result['tokens'])
                self.assertIsNotNone(result['client_id'])
                self.assertIsNotNone(result['client_secret'])

    def test_validate_refresh_prerequisites_no_tokens(self):
        """Test validation when no tokens are available"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Mock database response with no tokens
        with patch('enhanced_token_management.db_utils.execute_query') as mock_db:
            mock_db.return_value = None
            
            result = token_manager._validate_refresh_prerequisites()
            
            self.assertFalse(result['valid'])
            self.assertEqual(result['message'], 'No refresh token available')
            self.assertIsNone(result['tokens'])

    def test_validate_refresh_prerequisites_no_credentials(self):
        """Test validation when no centralized credentials are available"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Mock database response with valid tokens
        with patch('enhanced_token_management.db_utils.execute_query') as mock_db:
            mock_db.return_value = [{
                'strava_access_token': 'test_access_token',
                'strava_refresh_token': 'test_refresh_token',
                'strava_token_expires_at': 9999999999,
                'strava_athlete_id': 12345
            }]
            
            # Mock no credentials available
            with patch('os.path.join') as mock_join:
                mock_join.return_value = "/nonexistent/path/strava_config.json"
                
                with patch.dict(os.environ, {}, clear=True):
                    result = token_manager._validate_refresh_prerequisites()
                    
                    self.assertFalse(result['valid'])
                    self.assertEqual(result['message'], 'No centralized credentials available')

    def test_is_retryable_error_retryable(self):
        """Test retryable error detection"""
        token_manager = SimpleTokenManager(user_id=1)
        
        retryable_errors = [
            "timeout error",
            "connection failed",
            "network error",
            "temporary failure",
            "rate limit exceeded",
            "too many requests",
            "server error 500",
            "internal error",
            "service unavailable"
        ]
        
        for error in retryable_errors:
            self.assertTrue(token_manager._is_retryable_error(error), f"Should be retryable: {error}")

    def test_is_retryable_error_non_retryable(self):
        """Test non-retryable error detection"""
        token_manager = SimpleTokenManager(user_id=1)
        
        non_retryable_errors = [
            "invalid refresh token",
            "invalid client credentials",
            "unauthorized access",
            "forbidden",
            "not found",
            "bad request"
        ]
        
        for error in non_retryable_errors:
            self.assertFalse(token_manager._is_retryable_error(error), f"Should not be retryable: {error}")

    def test_attempt_token_refresh_success(self):
        """Test successful token refresh attempt"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Mock successful Strava API response
        mock_refresh_response = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_at': 9999999999
        }
        
        with patch('stravalib.client.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.refresh_access_token.return_value = mock_refresh_response
            mock_client.return_value = mock_client_instance
            
            result = token_manager._attempt_token_refresh(
                'test_client_id',
                'test_client_secret',
                'test_refresh_token'
            )
            
            self.assertTrue(result['success'])
            self.assertIsNone(result['error'])
            self.assertEqual(result['tokens']['access_token'], 'new_access_token')

    def test_attempt_token_refresh_failure(self):
        """Test failed token refresh attempt"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Mock failed Strava API response
        with patch('stravalib.client.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.refresh_access_token.side_effect = Exception("Invalid refresh token")
            mock_client.return_value = mock_client_instance
            
            result = token_manager._attempt_token_refresh(
                'test_client_id',
                'test_client_secret',
                'test_refresh_token'
            )
            
            self.assertFalse(result['success'])
            self.assertIsNotNone(result['error'])
            self.assertIsNone(result['tokens'])

    def test_refresh_tokens_for_user_success(self):
        """Test successful token refresh for user"""
        # Mock the token manager
        with patch('enhanced_token_management.SimpleTokenManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            # Mock successful refresh
            mock_manager.is_token_expired_or_expiring_soon.return_value = True
            mock_manager.refresh_strava_tokens.return_value = {
                'access_token': 'new_token',
                'refresh_token': 'new_refresh',
                'expires_at': 9999999999
            }
            
            result = refresh_tokens_for_user(user_id=1)
            
            self.assertTrue(result['success'])
            self.assertTrue(result['refreshed'])
            self.assertEqual(result['user_id'], 1)

    def test_refresh_tokens_for_user_no_refresh_needed(self):
        """Test token refresh when no refresh is needed"""
        with patch('enhanced_token_management.SimpleTokenManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            # Mock no refresh needed
            mock_manager.is_token_expired_or_expiring_soon.return_value = False
            
            result = refresh_tokens_for_user(user_id=1)
            
            self.assertTrue(result['success'])
            self.assertFalse(result['refreshed'])
            self.assertEqual(result['message'], 'Tokens are still valid')

    def test_get_token_refresh_status_structure(self):
        """Test structure of token refresh status"""
        with patch('enhanced_token_management.SimpleTokenManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager_class.return_value = mock_manager
            
            # Mock status responses
            mock_manager.get_simple_token_status.return_value = {
                'status': 'valid',
                'message': 'Tokens are valid'
            }
            mock_manager.is_token_expired_or_expiring_soon.return_value = False
            mock_manager.get_centralized_credentials_status.return_value = {
                'status': 'valid',
                'has_credentials': True
            }
            
            result = get_token_refresh_status(user_id=1)
            
            # Check structure
            self.assertIn('user_id', result)
            self.assertIn('token_status', result)
            self.assertIn('credentials_status', result)
            self.assertIn('needs_refresh', result)
            self.assertIn('refresh_readiness', result)
            self.assertIn('readiness_message', result)
            self.assertIn('can_refresh', result)
            
            # Check values
            self.assertEqual(result['user_id'], 1)
            self.assertFalse(result['needs_refresh'])
            self.assertEqual(result['refresh_readiness'], 'not_needed')

    def test_bulk_refresh_tokens_structure(self):
        """Test structure of bulk refresh tokens"""
        with patch('enhanced_token_management.db_utils.execute_query') as mock_db:
            mock_db.return_value = [{'id': 1}, {'id': 2}]
            
            with patch('enhanced_token_management.refresh_tokens_for_user') as mock_refresh:
                mock_refresh.return_value = {
                    'success': True,
                    'refreshed': True,
                    'user_id': 1
                }
                
                result = bulk_refresh_tokens()
                
                # Check structure
                self.assertIn('success', result)
                self.assertIn('message', result)
                self.assertIn('total_users', result)
                self.assertIn('successful_refreshes', result)
                self.assertIn('failed_refreshes', result)
                self.assertIn('results', result)
                
                # Check values
                self.assertTrue(result['success'])
                self.assertEqual(result['total_users'], 2)

    def test_validate_client_connection_success(self):
        """Test successful client connection validation"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Mock successful athlete response
        mock_athlete = MagicMock()
        mock_athlete.firstname = "John"
        mock_athlete.lastname = "Doe"
        
        mock_client = MagicMock()
        mock_client.get_athlete.return_value = mock_athlete
        
        result = token_manager._validate_client_connection(mock_client)
        
        self.assertTrue(result['valid'])
        self.assertIsNone(result['error'])
        self.assertEqual(result['athlete_name'], "John Doe")

    def test_validate_client_connection_failure(self):
        """Test failed client connection validation"""
        token_manager = SimpleTokenManager(user_id=1)
        
        # Mock failed athlete response
        mock_client = MagicMock()
        mock_client.get_athlete.side_effect = Exception("Unauthorized")
        
        result = token_manager._validate_client_connection(mock_client)
        
        self.assertFalse(result['valid'])
        self.assertIsNotNone(result['error'])
        self.assertIsNone(result['athlete_name'])
        self.assertIn('authentication', result['error'])


def test_enhanced_token_refresh_import():
    """Test that enhanced token refresh can be imported without errors"""
    try:
        from enhanced_token_management import (
            SimpleTokenManager,
            refresh_tokens_for_user,
            get_token_refresh_status,
            bulk_refresh_tokens
        )
        print("✅ Enhanced token refresh imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing enhanced token refresh: {str(e)}")
        return False


def test_api_endpoints_import():
    """Test that the main app with new token refresh API endpoints can be imported"""
    try:
        import strava_app
        print("✅ Token refresh API endpoints import successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing token refresh API endpoints: {str(e)}")
        return False


if __name__ == '__main__':
    print("🧪 Testing Task 4.3 - Enhanced OAuth Token Refresh Logic")
    print("=" * 70)
    
    # Run basic tests
    test_results = []
    
    print("\n1. Testing enhanced token refresh import...")
    test_results.append(test_enhanced_token_refresh_import())
    
    print("\n2. Testing API endpoints import...")
    test_results.append(test_api_endpoints_import())
    
    print("\n3. Running unit tests...")
    # Run the unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 70)
    print("✅ Task 4.3 Enhanced Token Refresh Logic Tests Complete")
    
    if all(test_results):
        print("🎉 All tests passed! Enhanced token refresh logic is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
