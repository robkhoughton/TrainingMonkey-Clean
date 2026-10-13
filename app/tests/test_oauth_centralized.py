#!/usr/bin/env python3
"""
Test script for Task 4.1 - Centralized OAuth Integration
Tests that OAuth routes are using centralized credentials from strava_config.json
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_token_management import SimpleTokenManager


class TestCentralizedOAuth(unittest.TestCase):
    """Test cases for centralized OAuth integration"""

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

    def test_get_centralized_credentials_file_not_found(self):
        """Test fallback to environment variables when config file not found"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = "/nonexistent/path/strava_config.json"
            
            with patch.dict(os.environ, {
                'STRAVA_CLIENT_ID': 'env_client_id',
                'STRAVA_CLIENT_SECRET': 'env_client_secret'
            }):
                client_id, client_secret = SimpleTokenManager(user_id=1).get_centralized_strava_credentials()
                
                self.assertEqual(client_id, "env_client_id")
                self.assertEqual(client_secret, "env_client_secret")

    def test_get_centralized_credentials_no_credentials(self):
        """Test behavior when no credentials are available"""
        with patch('os.path.join') as mock_join:
            mock_join.return_value = "/nonexistent/path/strava_config.json"
            
            with patch.dict(os.environ, {}, clear=True):
                client_id, client_secret = SimpleTokenManager(user_id=1).get_centralized_strava_credentials()
                
                self.assertIsNone(client_id)
                self.assertIsNone(client_secret)

    def test_simple_token_manager_centralized_credentials(self):
        """Test SimpleTokenManager uses centralized credentials"""
        token_manager = SimpleTokenManager(user_id=1)
        
        with patch('os.path.join') as mock_join:
            mock_join.return_value = self.temp_config_file.name
            
            client_id, client_secret = token_manager.get_centralized_strava_credentials()
            
            self.assertEqual(client_id, "test_client_id_12345")
            self.assertEqual(client_secret, "test_client_secret_abcdef")

    def test_config_file_malformed(self):
        """Test handling of malformed config file"""
        # Create a malformed config file
        malformed_config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        malformed_config_file.write('{"invalid": json}')
        malformed_config_file.close()
        
        try:
            with patch('os.path.join') as mock_join:
                mock_join.return_value = malformed_config_file.name
                
                with patch.dict(os.environ, {
                    'STRAVA_CLIENT_ID': 'env_client_id',
                    'STRAVA_CLIENT_SECRET': 'env_client_secret'
                }):
                    client_id, client_secret = SimpleTokenManager(user_id=1).get_centralized_strava_credentials()
                    
                    # Should fallback to environment variables
                    self.assertEqual(client_id, "env_client_id")
                    self.assertEqual(client_secret, "env_client_secret")
        finally:
            if os.path.exists(malformed_config_file.name):
                os.unlink(malformed_config_file.name)

    def test_config_file_missing_credentials(self):
        """Test handling of config file with missing credentials"""
        incomplete_config = {
            "resting_hr": 44,
            "max_hr": 178,
            "gender": "male"
            # Missing client_id and client_secret
        }
        
        incomplete_config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        json.dump(incomplete_config, incomplete_config_file)
        incomplete_config_file.close()
        
        try:
            with patch('os.path.join') as mock_join:
                mock_join.return_value = incomplete_config_file.name
                
                with patch.dict(os.environ, {
                    'STRAVA_CLIENT_ID': 'env_client_id',
                    'STRAVA_CLIENT_SECRET': 'env_client_secret'
                }):
                    client_id, client_secret = SimpleTokenManager(user_id=1).get_centralized_strava_credentials()
                    
                    # Should fallback to environment variables
                    self.assertEqual(client_id, "env_client_id")
                    self.assertEqual(client_secret, "env_client_secret")
        finally:
            if os.path.exists(incomplete_config_file.name):
                os.unlink(incomplete_config_file.name)
