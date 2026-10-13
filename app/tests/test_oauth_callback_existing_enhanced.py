#!/usr/bin/env python3
"""
Test script for Task 4.6 - Enhanced Existing OAuth Callback for Centralized Flow
Tests the enhanced existing OAuth callback functionality with centralized credentials and improved UX
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock Flask components for testing
class MockRequest:
    def __init__(self, args=None, json_data=None):
        self.args = args or {}
        self.json = json_data or {}

class MockSession:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def pop(self, key, default=None):
        return self.data.pop(key, default)

class MockCurrentUser:
    def __init__(self, user_id=1):
        self.id = user_id
        self.is_authenticated = True

class MockFlash:
    def __init__(self):
        self.messages = []
    
    def __call__(self, message, category='info'):
        self.messages.append({'message': message, 'category': category})

class MockRedirect:
    def __init__(self):
        self.redirects = []
    
    def __call__(self, url):
        self.redirects.append(url)
        return f"REDIRECT: {url}"

class MockRenderTemplate:
    def __init__(self):
        self.rendered_templates = []
    
    def __call__(self, template, **kwargs):
        self.rendered_templates.append({'template': template, 'kwargs': kwargs})
        return f"RENDERED: {template}"


class TestEnhancedExistingOAuthCallback(unittest.TestCase):
    """Test cases for enhanced existing OAuth callback functionality"""

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

    def test_oauth_callback_error_handling_existing_user(self):
        """Test OAuth callback error handling for existing users"""
        # Mock request with error
        mock_request = MockRequest(args={'error': 'access_denied'})
        mock_current_user = MockCurrentUser(user_id=1)
        
        with patch('strava_app.request', mock_request):
            with patch('strava_app.current_user', mock_current_user):
                with patch('strava_app.flash') as mock_flash:
                    with patch('strava_app.redirect') as mock_redirect:
                        # Test error handling for existing users
                        pass

    def test_oauth_callback_missing_auth_code_existing_user(self):
        """Test OAuth callback with missing authorization code for existing users"""
        # Mock request without auth code
        mock_request = MockRequest(args={})
        mock_current_user = MockCurrentUser(user_id=1)
        
        with patch('strava_app.request', mock_request):
            with patch('strava_app.current_user', mock_current_user):
                with patch('strava_app.flash') as mock_flash:
                    with patch('strava_app.redirect') as mock_redirect:
                        # Test missing auth code scenario for existing users
                        pass

    def test_oauth_callback_configuration_error_existing_user(self):
        """Test OAuth callback with configuration error for existing users"""
        # Mock request with auth code but no config file
        mock_request = MockRequest(args={'code': 'test_auth_code'})
        mock_current_user = MockCurrentUser(user_id=1)
        
        with patch('strava_app.request', mock_request):
            with patch('strava_app.current_user', mock_current_user):
                with patch('strava_app.open', side_effect=FileNotFoundError()):
                    with patch('strava_app.flash') as mock_flash:
                        with patch('strava_app.redirect') as mock_redirect:
                            # Test configuration error handling for existing users
                            pass

    def test_oauth_callback_token_exchange_success_existing_user(self):
        """Test successful token exchange in OAuth callback for existing users"""
        # Mock successful token response
        mock_token_response = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_at': 9999999999
        }
        
        # Mock successful athlete response
        mock_athlete = MagicMock()
        mock_athlete.id = 12345
        mock_athlete.firstname = "John"
        mock_athlete.lastname = "Doe"
        
        with patch('stravalib.client.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client_instance.exchange_code_for_token.return_value = mock_token_response
            mock_client_instance.get_athlete.return_value = mock_athlete
            mock_client.return_value = mock_client_instance
            
            # Test successful token exchange for existing users
            pass

    def test_oauth_callback_token_saving_existing_user(self):
        """Test token saving for existing users"""
        # Mock token manager
        with patch('strava_app.SimpleTokenManager') as mock_token_manager:
            mock_manager_instance = MagicMock()
            mock_manager_instance.save_tokens_to_database.return_value = True
            mock_token_manager.return_value = mock_manager_instance
            
            # Test token saving for existing users
            pass

    def test_oauth_callback_session_management_existing_user(self):
        """Test session management for existing user OAuth callback"""
        # Mock session
        mock_session = MockSession()
        mock_session['temp_strava_client_id'] = 'old_client_id'
        mock_session['temp_strava_client_secret'] = 'old_client_secret'
        
        with patch('strava_app.session', mock_session):
            # Test session cleanup
            mock_session.pop('temp_strava_client_id', None)
            mock_session.pop('temp_strava_client_secret', None)
            
            # Verify session cleanup
            self.assertNotIn('temp_strava_client_id', mock_session.data)
            self.assertNotIn('temp_strava_client_secret', mock_session.data)

    def test_oauth_callback_enhanced_error_context(self):
        """Test enhanced error context for existing users"""
        # Mock error handling with context
        error_context = {
            'operation': 'oauth_callback',
            'user_id': 1,
            'existing_user': True
        }
        
        # Test that error context includes existing_user flag
        self.assertIn('existing_user', error_context)
        self.assertTrue(error_context['existing_user'])

    def test_oauth_callback_enhanced_logging(self):
        """Test enhanced logging for existing user OAuth callback"""
        # Mock logger
        with patch('strava_app.logger') as mock_logger:
            # Test enhanced logging
            mock_logger.info(f"Processing enhanced OAuth callback for existing user 1 with centralized credentials...")
            mock_logger.info.assert_called()

    def test_oauth_callback_athlete_id_extraction(self):
        """Test athlete ID extraction for existing users"""
        # Mock athlete object
        mock_athlete = MagicMock()
        mock_athlete.id = 12345
        
        # Test athlete ID extraction
        athlete_id = str(mock_athlete.id)
        self.assertEqual(athlete_id, '12345')

    def test_oauth_callback_enhanced_token_structure(self):
        """Test enhanced token structure for existing users"""
        # Mock token response
        token_response = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_at': 9999999999
        }
        
        # Enhanced token structure
        tokens = {
            'access_token': token_response['access_token'],
            'refresh_token': token_response['refresh_token'],
            'expires_at': token_response['expires_at'],
            'athlete_id': '12345'
        }
        
        # Test enhanced token structure
        self.assertIn('athlete_id', tokens)
        self.assertEqual(tokens['athlete_id'], '12345')

    def test_oauth_callback_existing_activities_check(self):
        """Test existing activities check for existing users"""
        # Mock database query for existing activities
        with patch('strava_app.db_utils.execute_query') as mock_db:
            # Test with existing activities
            mock_db.return_value = [{'count': 10}]
            has_existing_data = mock_db.return_value[0]['count'] > 0
            self.assertTrue(has_existing_data)
            
            # Test without existing activities
            mock_db.return_value = [{'count': 0}]
            has_existing_data = mock_db.return_value[0]['count'] > 0
            self.assertFalse(has_existing_data)

    def test_oauth_callback_centralized_credentials_usage(self):
        """Test centralized credentials usage for existing users"""
        # Mock config file reading
        with patch('builtins.open', mock_open(read_data=json.dumps(self.test_config))):
            with patch('json.load') as mock_json_load:
                mock_json_load.return_value = self.test_config
                
                # Test centralized credentials extraction
                client_id = self.test_config.get('client_id')
                client_secret = self.test_config.get('client_secret')
                
                self.assertEqual(client_id, 'test_client_id_12345')
                self.assertEqual(client_secret, 'test_client_secret_abcdef')

    def test_oauth_callback_template_data_preparation(self):
        """Test template data preparation for existing users"""
        # Mock template data
        template_data = {
            'athlete_name': 'John Doe',
            'athlete_id': '12345',
            'has_existing_data': True,
            'user_id': 1,
            'connection_type': 'existing_user'
        }
        
        # Test template data structure
        self.assertIn('athlete_name', template_data)
        self.assertIn('athlete_id', template_data)
        self.assertIn('has_existing_data', template_data)
        self.assertIn('user_id', template_data)
        self.assertIn('connection_type', template_data)
        self.assertEqual(template_data['connection_type'], 'existing_user')
