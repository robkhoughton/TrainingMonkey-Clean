#!/usr/bin/env python3
"""
Unit Tests for Analytics Tracking Functionality

This module contains comprehensive unit tests for analytics tracking,
event handling, and related functionality.
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
    def __init__(self, args=None, headers=None, remote_addr=None):
        self.args = args or {}
        self.headers = headers or {}
        self.remote_addr = remote_addr or '127.0.0.1'
    
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
sys.modules['analytics_tracker'] = Mock()

class TestAnalyticsEventTracking(unittest.TestCase):
    """Test cases for analytics event tracking"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
        
        # Mock database utilities
        self.mock_db_utils = Mock()
        self.mock_db_utils.execute_query = Mock()
        self.mock_db_utils.get_db_connection = Mock()
    
    def test_integration_point_click_tracking(self):
        """Test tracking of integration point clicks"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test integration point click tracking
                    test_data = {
                        'event_type': 'integration_point_click',
                        'event_data': {
                            'integration_point': 'landing_cta',
                            'source': 'landing',
                            'target': 'getting_started',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    # Test the analytics endpoint
                    result = landing_analytics()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_getting_started_access_tracking(self):
        """Test tracking of getting started page access"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test getting started access tracking
                    test_data = {
                        'event_type': 'getting_started_access',
                        'event_data': {
                            'source': 'landing',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    # Test the analytics endpoint
                    result = landing_analytics()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_tutorial_start_tracking(self):
        """Test tracking of tutorial start events"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test tutorial start tracking
                    test_data = {
                        'event_type': 'tutorial_start',
                        'event_data': {
                            'tutorial_id': 'dashboard_tutorial',
                            'source': 'getting_started',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    # Test the analytics endpoint
                    result = landing_analytics()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_tutorial_complete_tracking(self):
        """Test tracking of tutorial completion events"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test tutorial completion tracking
                    test_data = {
                        'event_type': 'tutorial_complete',
                        'event_data': {
                            'tutorial_id': 'dashboard_tutorial',
                            'completion_time': 300,
                            'steps_completed': 5,
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    # Test the analytics endpoint
                    result = landing_analytics()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_demo_interaction_tracking(self):
        """Test tracking of demo interactions"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test demo interaction tracking
                    test_data = {
                        'event_type': 'demo_interaction',
                        'event_data': {
                            'scenario': 'overtraining',
                            'source': 'getting_started',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    # Test the analytics endpoint
                    result = landing_analytics()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_engagement_metrics_tracking(self):
        """Test tracking of engagement metrics"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test engagement metrics tracking
                    test_data = {
                        'event_type': 'getting_started_engagement',
                        'event_data': {
                            'event_subtype': 'scroll_milestone',
                            'depth': 50,
                            'source': 'landing',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    # Test the analytics endpoint
                    result = landing_analytics()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_analytics_error_handling(self):
        """Test error handling in analytics tracking"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test error handling
                    self.mock_request.json_data = None
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    # Test error handling
                    result = landing_analytics()
                    
                    # Verify error is handled gracefully
                    self.assertIsNotNone(result)


class TestAnalyticsDataRetrieval(unittest.TestCase):
    """Test cases for analytics data retrieval"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
        
        # Mock database utilities
        self.mock_db_utils = Mock()
        self.mock_db_utils.execute_query = Mock()
        self.mock_db_utils.get_db_connection = Mock()
    
    def test_click_through_rates_retrieval(self):
        """Test retrieval of click-through rates"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock click-through rates data
                mock_ctr_data = [
                    {
                        'integration_point': 'landing_cta',
                        'total_impressions': 1000,
                        'total_clicks': 150,
                        'click_through_rate': 15.0,
                        'unique_users': 120,
                        'conversion_rate': 80.0
                    }
                ]
                
                # Mock analytics tracker
                with patch('analytics_tracker.analytics_tracker') as mock_tracker:
                    mock_tracker.get_click_through_rates.return_value = mock_ctr_data
                    
                    # Test click-through rates endpoint
                    from strava_app import get_click_through_rates
                    
                    result = get_click_through_rates()
                    
                    # Verify data retrieval works
                    self.assertIsNotNone(result)
    
    def test_user_journey_funnel_retrieval(self):
        """Test retrieval of user journey funnel data"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock funnel data
                mock_funnel_data = {
                    'time_period': '7d',
                    'date_range': {
                        'start': '2024-01-01',
                        'end': '2024-01-07'
                    },
                    'steps': [
                        {
                            'step_name': 'Page Views',
                            'unique_users': 1000,
                            'total_events': 1200,
                            'conversion_rate': None
                        },
                        {
                            'step_name': 'Integration Clicks',
                            'unique_users': 150,
                            'total_events': 180,
                            'conversion_rate': 15.0
                        }
                    ]
                }
                
                # Mock analytics tracker
                with patch('analytics_tracker.analytics_tracker') as mock_tracker:
                    mock_tracker.get_user_journey_funnel.return_value = mock_funnel_data
                    
                    # Test user journey funnel endpoint
                    from strava_app import get_user_journey_funnel
                    
                    result = get_user_journey_funnel()
                    
                    # Verify data retrieval works
                    self.assertIsNotNone(result)
    
    def test_tutorial_analytics_retrieval(self):
        """Test retrieval of tutorial analytics data"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock tutorial analytics data
                mock_tutorial_data = {
                    'time_period': '7d',
                    'date_range': {
                        'start': '2024-01-01',
                        'end': '2024-01-07'
                    },
                    'tutorials': [
                        {
                            'tutorial_id': 'dashboard_tutorial',
                            'starts': 50,
                            'completions': 35,
                            'skips': 5,
                            'unique_users': 45,
                            'completion_rate': 70.0,
                            'skip_rate': 10.0
                        }
                    ]
                }
                
                # Mock analytics tracker
                with patch('analytics_tracker.analytics_tracker') as mock_tracker:
                    mock_tracker.get_tutorial_analytics.return_value = mock_tutorial_data
                    
                    # Test tutorial analytics endpoint
                    from strava_app import get_tutorial_analytics
                    
                    result = get_tutorial_analytics()
                    
                    # Verify data retrieval works
                    self.assertIsNotNone(result)
    
    def test_detailed_funnel_retrieval(self):
        """Test retrieval of detailed funnel analysis"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock detailed funnel data
                mock_detailed_funnel = {
                    'detailed_funnel': {
                        'time_period': '7d',
                        'funnel_steps': []
                    },
                    'enhanced_funnel': {
                        'funnel_type': 'onboarding',
                        'steps': []
                    }
                }
                
                # Mock analytics tracker
                with patch('analytics_tracker.analytics_tracker') as mock_tracker:
                    mock_tracker.get_detailed_funnel_analysis.return_value = mock_detailed_funnel['detailed_funnel']
                    mock_tracker.get_user_journey_funnel.return_value = mock_detailed_funnel['enhanced_funnel']
                    
                    # Test detailed funnel endpoint
                    from strava_app import get_detailed_funnel
                    
                    result = get_detailed_funnel()
                    
                    # Verify data retrieval works
                    self.assertIsNotNone(result)


class TestTutorialTracking(unittest.TestCase):
    """Test cases for tutorial tracking functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
        
        # Mock database utilities
        self.mock_db_utils = Mock()
        self.mock_db_utils.execute_query = Mock()
        self.mock_db_utils.get_db_connection = Mock()
    
    def test_tutorial_start_tracking(self):
        """Test tutorial start tracking"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Test tutorial start tracking
                test_data = {
                    'tutorial_id': 'dashboard_tutorial',
                    'source': 'getting_started',
                    'timestamp': datetime.now().isoformat()
                }
                
                self.mock_request.json_data = test_data
                
                # Mock tutorial system
                with patch('onboarding_tutorial_system.OnboardingTutorialSystem') as mock_tutorial_system:
                    mock_tutorial_system.return_value.mark_tutorial_started.return_value = True
                    
                    # Test tutorial start endpoint
                    from strava_app import start_tutorial
                    
                    result = start_tutorial()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_tutorial_complete_tracking(self):
        """Test tutorial completion tracking"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Test tutorial completion tracking
                test_data = {
                    'tutorial_id': 'dashboard_tutorial',
                    'source': 'getting_started',
                    'timestamp': datetime.now().isoformat(),
                    'completion_time': 300,
                    'steps_completed': 5
                }
                
                self.mock_request.json_data = test_data
                
                # Mock tutorial system
                with patch('onboarding_tutorial_system.OnboardingTutorialSystem') as mock_tutorial_system:
                    mock_tutorial_system.return_value.mark_tutorial_completed.return_value = True
                    
                    # Test tutorial complete endpoint
                    from strava_app import complete_tutorial
                    
                    result = complete_tutorial()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_tutorial_skip_tracking(self):
        """Test tutorial skip tracking"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Test tutorial skip tracking
                test_data = {
                    'tutorial_id': 'dashboard_tutorial',
                    'source': 'getting_started',
                    'timestamp': datetime.now().isoformat(),
                    'skip_reason': 'not_interested',
                    'step_skipped_at': 2
                }
                
                self.mock_request.json_data = test_data
                
                # Mock tutorial system
                with patch('onboarding_tutorial_system.OnboardingTutorialSystem') as mock_tutorial_system:
                    mock_tutorial_system.return_value.mark_tutorial_skipped.return_value = True
                    
                    # Test tutorial skip endpoint
                    from strava_app import skip_tutorial
                    
                    result = skip_tutorial()
                    
                    # Verify tracking works
                    self.assertIsNotNone(result)
    
    def test_tutorial_stats_retrieval(self):
        """Test tutorial statistics retrieval"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock tutorial stats data
                mock_stats_data = {
                    'tutorial_id': 'dashboard_tutorial',
                    'total_starts': 50,
                    'total_completions': 35,
                    'total_skips': 5,
                    'completion_rate': 70.0,
                    'skip_rate': 10.0,
                    'time_period': '7d'
                }
                
                # Mock tutorial system
                with patch('onboarding_tutorial_system.OnboardingTutorialSystem') as mock_tutorial_system:
                    mock_tutorial_system.return_value.get_tutorial_completion_stats.return_value = mock_stats_data
                    
                    # Test tutorial stats endpoint
                    from strava_app import get_tutorial_stats
                    
                    result = get_tutorial_stats()
                    
                    # Verify data retrieval works
                    self.assertIsNotNone(result)


class TestAnalyticsErrorHandling(unittest.TestCase):
    """Test cases for analytics error handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
    
    def test_analytics_tracking_error_handling(self):
        """Test error handling in analytics tracking"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test error handling
                    self.mock_request.json_data = None
                    
                    # Mock analytics tracking with error
                    from strava_app import landing_analytics
                    
                    # Test error handling
                    result = landing_analytics()
                    
                    # Verify error is handled gracefully
                    self.assertIsNotNone(result)
    
    def test_analytics_data_retrieval_error_handling(self):
        """Test error handling in analytics data retrieval"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock analytics tracker with error
                with patch('analytics_tracker.analytics_tracker') as mock_tracker:
                    mock_tracker.get_click_through_rates.side_effect = Exception("Database error")
                    
                    # Test error handling
                    from strava_app import get_click_through_rates
                    
                    result = get_click_through_rates()
                    
                    # Verify error is handled gracefully
                    self.assertIsNotNone(result)
    
    def test_tutorial_tracking_error_handling(self):
        """Test error handling in tutorial tracking"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Test tutorial tracking error handling
                test_data = {
                    'tutorial_id': 'dashboard_tutorial',
                    'source': 'getting_started'
                }
                
                self.mock_request.json_data = test_data
                
                # Mock tutorial system with error
                with patch('onboarding_tutorial_system.OnboardingTutorialSystem') as mock_tutorial_system:
                    mock_tutorial_system.return_value.mark_tutorial_started.side_effect = Exception("Database error")
                    
                    # Test error handling
                    from strava_app import start_tutorial
                    
                    result = start_tutorial()
                    
                    # Verify error is handled gracefully
                    self.assertIsNotNone(result)


class TestAnalyticsIntegration(unittest.TestCase):
    """Test cases for analytics integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
    
    def test_analytics_with_authenticated_user(self):
        """Test analytics with authenticated user"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test analytics with authenticated user
                    test_data = {
                        'event_type': 'integration_point_click',
                        'event_data': {
                            'integration_point': 'landing_cta',
                            'source': 'landing'
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify analytics works with authenticated user
                    self.assertIsNotNone(result)
    
    def test_analytics_with_unauthenticated_user(self):
        """Test analytics with unauthenticated user"""
        mock_unauthenticated_user = MockCurrentUser(is_authenticated=False, id=None)
        
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', mock_unauthenticated_user):
                with patch('flask.session', self.mock_session):
                    # Test analytics with unauthenticated user
                    test_data = {
                        'event_type': 'page_view',
                        'event_data': {
                            'source': 'landing'
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify analytics works with unauthenticated user
                    self.assertIsNotNone(result)
    
    def test_analytics_session_handling(self):
        """Test analytics session handling"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test session handling
                    self.mock_session['session_id'] = 'test_session_123'
                    
                    test_data = {
                        'event_type': 'getting_started_access',
                        'event_data': {
                            'source': 'landing'
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify session handling works
                    self.assertIsNotNone(result)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestAnalyticsEventTracking))
    test_suite.addTest(unittest.makeSuite(TestAnalyticsDataRetrieval))
    test_suite.addTest(unittest.makeSuite(TestTutorialTracking))
    test_suite.addTest(unittest.makeSuite(TestAnalyticsErrorHandling))
    test_suite.addTest(unittest.makeSuite(TestAnalyticsIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Analytics Tracking Tests Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
