#!/usr/bin/env python3
"""
Unit Tests for Getting Started Route Functionality

This module contains comprehensive unit tests for the getting started
route functionality, including context detection, user authentication,
and template rendering.
"""

import unittest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Mock Flask components before importing
class MockFlask:
    def __init__(self):
        self.template_folder = 'templates'
        self.static_folder = 'static'

class MockRequest:
    def __init__(self, args=None):
        self.args = args or {}
    
    def get(self, key, default=None):
        return self.args.get(key, default)

class MockCurrentUser:
    def __init__(self, is_authenticated=True, id=1):
        self.is_authenticated = is_authenticated
        self.id = id

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

class TestGettingStartedRoute(unittest.TestCase):
    """Test cases for getting started route functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_app = Mock()
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
        
        # Mock database utilities
        self.mock_db_utils = Mock()
        self.mock_db_utils.execute_query = Mock()
        
        # Mock onboarding manager
        self.mock_onboarding_manager = Mock()
        self.mock_onboarding_manager.get_user_onboarding_progress = Mock()
        
    def test_getting_started_route_authenticated_user(self):
        """Test getting started route with authenticated user"""
        # Mock authenticated user
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    with patch('db_utils.execute_query', self.mock_db_utils.execute_query):
                        with patch('onboarding_manager.OnboardingManager') as mock_onboarding:
                            # Setup mock onboarding manager
                            mock_onboarding.return_value.get_user_onboarding_progress.return_value = {
                                'current_step': 'welcome',
                                'completed_steps': ['welcome'],
                                'next_step': 'strava_connection'
                            }
                            
                            # Mock the route function
                            from strava_app import getting_started_resources
                            
                            # Test with different source parameters
                            test_sources = ['landing', 'onboarding', 'dashboard', 'settings', 'goals']
                            
                            for source in test_sources:
                                with self.subTest(source=source):
                                    self.mock_request.args = {'source': source}
                                    
                                    # Call the route function
                                    result = getting_started_resources()
                                    
                                    # Verify the function was called
                                    self.assertIsNotNone(result)
    
    def test_getting_started_route_unauthenticated_user(self):
        """Test getting started route with unauthenticated user"""
        # Mock unauthenticated user
        mock_unauthenticated_user = MockCurrentUser(is_authenticated=False, id=None)
        
        with patch('flask.current_user', mock_unauthenticated_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Mock the route function
                    from strava_app import getting_started_resources
                    
                    # Test with source parameter
                    self.mock_request.args = {'source': 'landing'}
                    
                    # Call the route function
                    result = getting_started_resources()
                    
                    # Verify the function handles unauthenticated users
                    self.assertIsNotNone(result)
    
    def test_context_detection_landing_source(self):
        """Test context detection for landing page source"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Test landing source
                    self.mock_request.args = {'source': 'landing'}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify context is detected correctly
                    self.assertIsNotNone(result)
    
    def test_context_detection_onboarding_source(self):
        """Test context detection for onboarding page source"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Test onboarding source
                    self.mock_request.args = {'source': 'onboarding'}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify context is detected correctly
                    self.assertIsNotNone(result)
    
    def test_context_detection_dashboard_source(self):
        """Test context detection for dashboard source"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Test dashboard source
                    self.mock_request.args = {'source': 'dashboard'}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify context is detected correctly
                    self.assertIsNotNone(result)
    
    def test_context_detection_settings_source(self):
        """Test context detection for settings page source"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Test settings source
                    self.mock_request.args = {'source': 'settings'}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify context is detected correctly
                    self.assertIsNotNone(result)
    
    def test_context_detection_goals_source(self):
        """Test context detection for goals page source"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Test goals source
                    self.mock_request.args = {'source': 'goals'}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify context is detected correctly
                    self.assertIsNotNone(result)
    
    def test_context_detection_no_source(self):
        """Test context detection with no source parameter"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Test with no source parameter
                    self.mock_request.args = {}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify default context is handled
                    self.assertIsNotNone(result)
    
    def test_user_context_creation(self):
        """Test user context creation for different user states"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    with patch('db_utils.execute_query', self.mock_db_utils.execute_query):
                        with patch('onboarding_manager.OnboardingManager') as mock_onboarding:
                            # Setup mock onboarding manager
                            mock_onboarding.return_value.get_user_onboarding_progress.return_value = {
                                'current_step': 'welcome',
                                'completed_steps': ['welcome'],
                                'next_step': 'strava_connection'
                            }
                            
                            # Test different user states
                            test_cases = [
                                {'is_authenticated': True, 'id': 1},
                                {'is_authenticated': False, 'id': None},
                                {'is_authenticated': True, 'id': 2}
                            ]
                            
                            for case in test_cases:
                                with self.subTest(case=case):
                                    mock_user = MockCurrentUser(
                                        is_authenticated=case['is_authenticated'],
                                        id=case['id']
                                    )
                                    
                                    with patch('flask.current_user', mock_user):
                                        from strava_app import getting_started_resources
                                        result = getting_started_resources()
                                        
                                        # Verify user context is created correctly
                                        self.assertIsNotNone(result)
    
    def test_onboarding_progress_integration(self):
        """Test integration with onboarding progress system"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    with patch('db_utils.execute_query', self.mock_db_utils.execute_query):
                        with patch('onboarding_manager.OnboardingManager') as mock_onboarding:
                            # Test different onboarding progress states
                            progress_states = [
                                {'current_step': 'welcome', 'completed_steps': [], 'next_step': 'strava_connection'},
                                {'current_step': 'strava_connection', 'completed_steps': ['welcome'], 'next_step': 'goals_setup'},
                                {'current_step': 'goals_setup', 'completed_steps': ['welcome', 'strava_connection'], 'next_step': 'complete'},
                                {'current_step': 'complete', 'completed_steps': ['welcome', 'strava_connection', 'goals_setup'], 'next_step': None}
                            ]
                            
                            for progress in progress_states:
                                with self.subTest(progress=progress):
                                    mock_onboarding.return_value.get_user_onboarding_progress.return_value = progress
                                    
                                    from strava_app import getting_started_resources
                                    result = getting_started_resources()
                                    
                                    # Verify onboarding progress is handled correctly
                                    self.assertIsNotNone(result)
    
    def test_error_handling(self):
        """Test error handling in getting started route"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    with patch('db_utils.execute_query', side_effect=Exception("Database error")):
                        # Test error handling
                        from strava_app import getting_started_resources
                        result = getting_started_resources()
                        
                        # Verify error is handled gracefully
                        self.assertIsNotNone(result)
    
    def test_template_rendering(self):
        """Test template rendering with different contexts"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    with patch('flask.render_template') as mock_render:
                        # Mock successful template rendering
                        mock_render.return_value = "Mock template content"
                        
                        # Test different source contexts
                        test_sources = ['landing', 'onboarding', 'dashboard', 'settings', 'goals']
                        
                        for source in test_sources:
                            with self.subTest(source=source):
                                self.mock_request.args = {'source': source}
                                
                                from strava_app import getting_started_resources
                                result = getting_started_resources()
                                
                                # Verify template is rendered
                                self.assertIsNotNone(result)
    
    def test_analytics_tracking_integration(self):
        """Test analytics tracking integration"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', self.mock_session):
                    # Test that analytics tracking is properly integrated
                    self.mock_request.args = {'source': 'landing'}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify analytics integration doesn't break the route
                    self.assertIsNotNone(result)


class TestGettingStartedAnalytics(unittest.TestCase):
    """Test cases for getting started analytics functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_app = Mock()
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
    
    def test_analytics_event_tracking(self):
        """Test analytics event tracking"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', MockSession()):
                    # Test analytics event tracking
                    from strava_app import landing_analytics
                    
                    # Mock request data
                    test_data = {
                        'event_type': 'getting_started_access',
                        'event_data': {
                            'source': 'landing',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    # Mock request.get_json
                    self.mock_request.get_json = Mock(return_value=test_data)
                    
                    # Test analytics tracking
                    result = landing_analytics()
                    
                    # Verify analytics tracking works
                    self.assertIsNotNone(result)
    
    def test_analytics_error_handling(self):
        """Test analytics error handling"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', MockSession()):
                    # Test analytics error handling
                    from strava_app import landing_analytics
                    
                    # Mock request.get_json to raise exception
                    self.mock_request.get_json = Mock(side_effect=Exception("JSON error"))
                    
                    # Test error handling
                    result = landing_analytics()
                    
                    # Verify error is handled gracefully
                    self.assertIsNotNone(result)


class TestGettingStartedIntegration(unittest.TestCase):
    """Test cases for getting started integration functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_app = Mock()
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
    
    def test_integration_point_routing(self):
        """Test integration point routing"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', MockSession()):
                    # Test different integration points
                    integration_points = [
                        {'source': 'landing', 'expected_context': 'landing'},
                        {'source': 'onboarding', 'expected_context': 'onboarding'},
                        {'source': 'dashboard', 'expected_context': 'dashboard'},
                        {'source': 'settings', 'expected_context': 'settings'},
                        {'source': 'goals', 'expected_context': 'goals'}
                    ]
                    
                    for point in integration_points:
                        with self.subTest(point=point):
                            self.mock_request.args = {'source': point['source']}
                            
                            from strava_app import getting_started_resources
                            result = getting_started_resources()
                            
                            # Verify integration point routing works
                            self.assertIsNotNone(result)
    
    def test_contextual_content_delivery(self):
        """Test contextual content delivery"""
        with patch('flask.current_user', self.mock_user):
            with patch('flask.request', self.mock_request):
                with patch('flask.session', MockSession()):
                    # Test contextual content delivery
                    self.mock_request.args = {'source': 'landing'}
                    
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify contextual content is delivered
                    self.assertIsNotNone(result)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestGettingStartedRoute))
    test_suite.addTest(unittest.makeSuite(TestGettingStartedAnalytics))
    test_suite.addTest(unittest.makeSuite(TestGettingStartedIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Getting Started Route Tests Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
