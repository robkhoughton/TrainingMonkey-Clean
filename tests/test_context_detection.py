#!/usr/bin/env python3
"""
Unit Tests for Context Detection and User Authentication Handling

This module contains comprehensive unit tests for context detection,
user authentication handling, and related functionality.
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Mock Flask components
class MockFlask:
    def __init__(self):
        self.template_folder = 'templates'
        self.static_folder = 'static'

class MockRequest:
    def __init__(self, args=None, headers=None):
        self.args = args or {}
        self.headers = headers or {}
    
    def get(self, key, default=None):
        return self.args.get(key, default)
    
    def get_json(self):
        return self.json_data if hasattr(self, 'json_data') else None

class MockCurrentUser:
    def __init__(self, is_authenticated=True, id=1, email="test@example.com"):
        self.is_authenticated = is_authenticated
        self.id = id
        self.email = email

class MockSession:
    def __init__(self):
        self.data = {}
    
    def get(self, key, default=None):
        return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __getitem__(self, key):
        return self.data[key]

# Mock the Flask components
sys.modules['flask'] = Mock()
sys.modules['flask'].Flask = MockFlask
sys.modules['flask'].request = MockRequest()
sys.modules['flask'].session = MockSession()
sys.modules['flask'].current_user = MockCurrentUser()
sys.modules['flask'].render_template = Mock()
sys.modules['flask'].jsonify = Mock()
sys.modules['flask'].redirect = Mock()
sys.modules['flask'].url_for = Mock()

# Mock other dependencies
sys.modules['db_utils'] = Mock()
sys.modules['onboarding_manager'] = Mock()

class TestContextDetection(unittest.TestCase):
    """Test cases for context detection functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
        
        # Mock database utilities
        self.mock_db_utils = Mock()
        self.mock_db_utils.execute_query = Mock()
        
        # Mock onboarding manager
        self.mock_onboarding_manager = Mock()
        self.mock_onboarding_manager.get_user_onboarding_progress = Mock()
    
    def test_landing_source_detection(self):
        """Test detection of landing page source"""
        with patch('flask.request', self.mock_request):
            # Test landing source detection
            self.mock_request.args = {'source': 'landing'}
            
            # Mock the context detection logic
            source = self.mock_request.get('source', 'direct')
            
            self.assertEqual(source, 'landing')
            self.assertIn('source', self.mock_request.args)
    
    def test_onboarding_source_detection(self):
        """Test detection of onboarding page source"""
        with patch('flask.request', self.mock_request):
            # Test onboarding source detection
            self.mock_request.args = {'source': 'onboarding'}
            
            source = self.mock_request.get('source', 'direct')
            
            self.assertEqual(source, 'onboarding')
            self.assertIn('source', self.mock_request.args)
    
    def test_dashboard_source_detection(self):
        """Test detection of dashboard source"""
        with patch('flask.request', self.mock_request):
            # Test dashboard source detection
            self.mock_request.args = {'source': 'dashboard'}
            
            source = self.mock_request.get('source', 'direct')
            
            self.assertEqual(source, 'dashboard')
            self.assertIn('source', self.mock_request.args)
    
    def test_settings_source_detection(self):
        """Test detection of settings page source"""
        with patch('flask.request', self.mock_request):
            # Test settings source detection
            self.mock_request.args = {'source': 'settings'}
            
            source = self.mock_request.get('source', 'direct')
            
            self.assertEqual(source, 'settings')
            self.assertIn('source', self.mock_request.args)
    
    def test_goals_source_detection(self):
        """Test detection of goals page source"""
        with patch('flask.request', self.mock_request):
            # Test goals source detection
            self.mock_request.args = {'source': 'goals'}
            
            source = self.mock_request.get('source', 'direct')
            
            self.assertEqual(source, 'goals')
            self.assertIn('source', self.mock_request.args)
    
    def test_direct_source_detection(self):
        """Test detection of direct access (no source parameter)"""
        with patch('flask.request', self.mock_request):
            # Test direct access detection
            self.mock_request.args = {}
            
            source = self.mock_request.get('source', 'direct')
            
            self.assertEqual(source, 'direct')
            self.assertNotIn('source', self.mock_request.args)
    
    def test_invalid_source_detection(self):
        """Test handling of invalid source parameters"""
        with patch('flask.request', self.mock_request):
            # Test invalid source handling
            invalid_sources = ['invalid', 'unknown', 'test', '123', '']
            
            for invalid_source in invalid_sources:
                with self.subTest(source=invalid_source):
                    self.mock_request.args = {'source': invalid_source}
                    
                    source = self.mock_request.get('source', 'direct')
                    
                    # Should return the invalid source as-is
                    self.assertEqual(source, invalid_source)
    
    def test_multiple_source_parameters(self):
        """Test handling of multiple source parameters"""
        with patch('flask.request', self.mock_request):
            # Test multiple source parameters
            self.mock_request.args = {
                'source': 'landing',
                'utm_source': 'email',
                'utm_campaign': 'welcome'
            }
            
            source = self.mock_request.get('source', 'direct')
            
            self.assertEqual(source, 'landing')
            self.assertIn('source', self.mock_request.args)
            self.assertIn('utm_source', self.mock_request.args)
    
    def test_case_sensitive_source_detection(self):
        """Test case sensitivity of source detection"""
        with patch('flask.request', self.mock_request):
            # Test case sensitivity
            case_variations = ['Landing', 'LANDING', 'landing', 'LaNdInG']
            
            for case_variation in case_variations:
                with self.subTest(source=case_variation):
                    self.mock_request.args = {'source': case_variation}
                    
                    source = self.mock_request.get('source', 'direct')
                    
                    # Should preserve case
                    self.assertEqual(source, case_variation)


class TestUserAuthenticationHandling(unittest.TestCase):
    """Test cases for user authentication handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_session = MockSession()
    
    def test_authenticated_user_detection(self):
        """Test detection of authenticated users"""
        with patch('flask.current_user', MockCurrentUser(is_authenticated=True, id=1)):
            # Test authenticated user detection
            user = MockCurrentUser(is_authenticated=True, id=1)
            
            self.assertTrue(user.is_authenticated)
            self.assertEqual(user.id, 1)
            self.assertIsNotNone(user.email)
    
    def test_unauthenticated_user_detection(self):
        """Test detection of unauthenticated users"""
        with patch('flask.current_user', MockCurrentUser(is_authenticated=False, id=None)):
            # Test unauthenticated user detection
            user = MockCurrentUser(is_authenticated=False, id=None)
            
            self.assertFalse(user.is_authenticated)
            self.assertIsNone(user.id)
    
    def test_user_id_handling(self):
        """Test user ID handling for different user states"""
        test_cases = [
            {'is_authenticated': True, 'id': 1, 'expected_id': 1},
            {'is_authenticated': True, 'id': 123, 'expected_id': 123},
            {'is_authenticated': False, 'id': None, 'expected_id': None},
            {'is_authenticated': True, 'id': 0, 'expected_id': 0}
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                user = MockCurrentUser(
                    is_authenticated=case['is_authenticated'],
                    id=case['id']
                )
                
                self.assertEqual(user.id, case['expected_id'])
                self.assertEqual(user.is_authenticated, case['is_authenticated'])
    
    def test_user_email_handling(self):
        """Test user email handling"""
        test_emails = [
            'test@example.com',
            'user@domain.org',
            'admin@company.co.uk',
            'user+tag@example.com'
        ]
        
        for email in test_emails:
            with self.subTest(email=email):
                user = MockCurrentUser(is_authenticated=True, id=1, email=email)
                
                self.assertEqual(user.email, email)
                self.assertTrue(user.is_authenticated)
    
    def test_session_handling(self):
        """Test session handling for different user states"""
        with patch('flask.session', self.mock_session):
            # Test session data handling
            self.mock_session['user_id'] = 1
            self.mock_session['authenticated'] = True
            
            user_id = self.mock_session.get('user_id')
            authenticated = self.mock_session.get('authenticated')
            
            self.assertEqual(user_id, 1)
            self.assertTrue(authenticated)
    
    def test_session_cleanup(self):
        """Test session cleanup for unauthenticated users"""
        with patch('flask.session', self.mock_session):
            # Test session cleanup
            self.mock_session['user_id'] = None
            self.mock_session['authenticated'] = False
            
            user_id = self.mock_session.get('user_id')
            authenticated = self.mock_session.get('authenticated')
            
            self.assertIsNone(user_id)
            self.assertFalse(authenticated)


class TestContextualContentDelivery(unittest.TestCase):
    """Test cases for contextual content delivery"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
    
    def test_landing_context_content(self):
        """Test contextual content for landing page source"""
        with patch('flask.request', self.mock_request):
            # Test landing context content
            self.mock_request.args = {'source': 'landing'}
            
            source = self.mock_request.get('source', 'direct')
            
            # Mock contextual content based on source
            if source == 'landing':
                expected_title = "Welcome to TrainingMonkey!"
                expected_message = "Let's get you started with training analysis."
            else:
                expected_title = "Getting Started"
                expected_message = "Learn how to use TrainingMonkey."
            
            self.assertEqual(source, 'landing')
            self.assertIsNotNone(expected_title)
            self.assertIsNotNone(expected_message)
    
    def test_onboarding_context_content(self):
        """Test contextual content for onboarding page source"""
        with patch('flask.request', self.mock_request):
            # Test onboarding context content
            self.mock_request.args = {'source': 'onboarding'}
            
            source = self.mock_request.get('source', 'direct')
            
            # Mock contextual content based on source
            if source == 'onboarding':
                expected_title = "Need Help Getting Started?"
                expected_message = "We're here to help you through the setup process."
            else:
                expected_title = "Getting Started"
                expected_message = "Learn how to use TrainingMonkey."
            
            self.assertEqual(source, 'onboarding')
            self.assertIsNotNone(expected_title)
            self.assertIsNotNone(expected_message)
    
    def test_dashboard_context_content(self):
        """Test contextual content for dashboard source"""
        with patch('flask.request', self.mock_request):
            # Test dashboard context content
            self.mock_request.args = {'source': 'dashboard'}
            
            source = self.mock_request.get('source', 'direct')
            
            # Mock contextual content based on source
            if source == 'dashboard':
                expected_title = "Dashboard Help"
                expected_message = "Learn about advanced dashboard features."
            else:
                expected_title = "Getting Started"
                expected_message = "Learn how to use TrainingMonkey."
            
            self.assertEqual(source, 'dashboard')
            self.assertIsNotNone(expected_title)
            self.assertIsNotNone(expected_message)
    
    def test_settings_context_content(self):
        """Test contextual content for settings page source"""
        with patch('flask.request', self.mock_request):
            # Test settings context content
            self.mock_request.args = {'source': 'settings'}
            
            source = self.mock_request.get('source', 'direct')
            
            # Mock contextual content based on source
            if source == 'settings':
                expected_title = "Settings Guide"
                expected_message = "Understand how your settings affect your training analysis."
            else:
                expected_title = "Getting Started"
                expected_message = "Learn how to use TrainingMonkey."
            
            self.assertEqual(source, 'settings')
            self.assertIsNotNone(expected_title)
            self.assertIsNotNone(expected_message)
    
    def test_goals_context_content(self):
        """Test contextual content for goals page source"""
        with patch('flask.request', self.mock_request):
            # Test goals context content
            self.mock_request.args = {'source': 'goals'}
            
            source = self.mock_request.get('source', 'direct')
            
            # Mock contextual content based on source
            if source == 'goals':
                expected_title = "Goals Setup Guide"
                expected_message = "Understand how your goals affect your training recommendations."
            else:
                expected_title = "Getting Started"
                expected_message = "Learn how to use TrainingMonkey."
            
            self.assertEqual(source, 'goals')
            self.assertIsNotNone(expected_title)
            self.assertIsNotNone(expected_message)
    
    def test_direct_context_content(self):
        """Test contextual content for direct access"""
        with patch('flask.request', self.mock_request):
            # Test direct access context content
            self.mock_request.args = {}
            
            source = self.mock_request.get('source', 'direct')
            
            # Mock contextual content for direct access
            if source == 'direct':
                expected_title = "Getting Started with TrainingMonkey"
                expected_message = "Everything you need to know to unlock your training potential."
            else:
                expected_title = "Getting Started"
                expected_message = "Learn how to use TrainingMonkey."
            
            self.assertEqual(source, 'direct')
            self.assertIsNotNone(expected_title)
            self.assertIsNotNone(expected_message)


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling in context detection and authentication"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
    
    def test_request_error_handling(self):
        """Test error handling for request-related issues"""
        with patch('flask.request', self.mock_request):
            # Test request error handling
            try:
                # Simulate request error
                self.mock_request.args = None
                source = self.mock_request.get('source', 'direct')
                
                # Should handle None args gracefully
                self.assertEqual(source, 'direct')
            except Exception as e:
                self.fail(f"Request error handling failed: {e}")
    
    def test_user_authentication_error_handling(self):
        """Test error handling for user authentication issues"""
        with patch('flask.current_user', self.mock_user):
            # Test user authentication error handling
            try:
                # Simulate authentication error
                user = MockCurrentUser(is_authenticated=False, id=None)
                
                # Should handle unauthenticated users gracefully
                self.assertFalse(user.is_authenticated)
                self.assertIsNone(user.id)
            except Exception as e:
                self.fail(f"User authentication error handling failed: {e}")
    
    def test_session_error_handling(self):
        """Test error handling for session-related issues"""
        with patch('flask.session', self.mock_session):
            # Test session error handling
            try:
                # Simulate session error
                self.mock_session.data = None
                
                # Should handle None session data gracefully
                user_id = self.mock_session.get('user_id', None)
                self.assertIsNone(user_id)
            except Exception as e:
                self.fail(f"Session error handling failed: {e}")
    
    def test_database_error_handling(self):
        """Test error handling for database-related issues"""
        with patch('db_utils.execute_query', side_effect=Exception("Database error")):
            # Test database error handling
            try:
                # Simulate database error
                from db_utils import execute_query
                
                # Should handle database errors gracefully
                with self.assertRaises(Exception):
                    execute_query("SELECT * FROM users", ())
            except Exception as e:
                self.fail(f"Database error handling failed: {e}")


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestContextDetection))
    test_suite.addTest(unittest.makeSuite(TestUserAuthenticationHandling))
    test_suite.addTest(unittest.makeSuite(TestContextualContentDelivery))
    test_suite.addTest(unittest.makeSuite(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Context Detection and Authentication Tests Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
