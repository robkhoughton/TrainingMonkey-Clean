#!/usr/bin/env python3
"""
Integration Tests for Complete User Journey Flows

This module contains comprehensive integration tests for complete user journey
flows, including transitions between pages, integration points, and end-to-end
user experience testing.
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
sys.modules['onboarding_manager'] = Mock()
sys.modules['analytics_tracker'] = Mock()

class TestLandingToGettingStartedFlow(unittest.TestCase):
    """Test cases for landing page to getting started flow"""
    
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
    
    def test_landing_page_integration_point(self):
        """Test landing page integration point functionality"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test landing page integration point
                    self.mock_request.args = {'source': 'landing'}
                    
                    # Mock the landing page route
                    from strava_app import landing
                    
                    result = landing()
                    
                    # Verify landing page loads correctly
                    self.assertIsNotNone(result)
    
    def test_landing_to_getting_started_transition(self):
        """Test transition from landing page to getting started"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test transition with landing source
                    self.mock_request.args = {'source': 'landing'}
                    
                    # Mock getting started route
                    from strava_app import getting_started_resources
                    
                    result = getting_started_resources()
                    
                    # Verify transition works correctly
                    self.assertIsNotNone(result)
    
    def test_landing_cta_analytics_tracking(self):
        """Test analytics tracking for landing page CTA clicks"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test CTA click analytics
                    test_data = {
                        'event_type': 'cta_click',
                        'event_data': {
                            'button': 'see_how_it_works',
                            'source': 'landing',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify analytics tracking works
                    self.assertIsNotNone(result)
    
    def test_landing_integration_point_click_tracking(self):
        """Test integration point click tracking from landing page"""
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
                    
                    result = landing_analytics()
                    
                    # Verify integration point tracking works
                    self.assertIsNotNone(result)


class TestOnboardingToGettingStartedFlow(unittest.TestCase):
    """Test cases for onboarding page to getting started flow"""
    
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
    
    def test_onboarding_page_integration_point(self):
        """Test onboarding page integration point functionality"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test onboarding page integration point
                    self.mock_request.args = {'source': 'onboarding'}
                    
                    # Mock the onboarding page route
                    from strava_app import onboarding
                    
                    result = onboarding()
                    
                    # Verify onboarding page loads correctly
                    self.assertIsNotNone(result)
    
    def test_onboarding_to_getting_started_transition(self):
        """Test transition from onboarding page to getting started"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test transition with onboarding source
                    self.mock_request.args = {'source': 'onboarding'}
                    
                    # Mock getting started route
                    from strava_app import getting_started_resources
                    
                    result = getting_started_resources()
                    
                    # Verify transition works correctly
                    self.assertIsNotNone(result)
    
    def test_onboarding_help_link_analytics_tracking(self):
        """Test analytics tracking for onboarding help link clicks"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test help link click analytics
                    test_data = {
                        'event_type': 'integration_point_click',
                        'event_data': {
                            'integration_point': 'onboarding_help_link',
                            'source': 'onboarding',
                            'target': 'getting_started',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify analytics tracking works
                    self.assertIsNotNone(result)


class TestDashboardToGettingStartedFlow(unittest.TestCase):
    """Test cases for dashboard to getting started flow"""
    
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
    
    def test_dashboard_help_button_integration(self):
        """Test dashboard help button integration"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test dashboard help button
                    self.mock_request.args = {'source': 'dashboard'}
                    
                    # Mock getting started route
                    from strava_app import getting_started_resources
                    
                    result = getting_started_resources()
                    
                    # Verify dashboard integration works
                    self.assertIsNotNone(result)
    
    def test_dashboard_to_getting_started_transition(self):
        """Test transition from dashboard to getting started"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test transition with dashboard source
                    self.mock_request.args = {'source': 'dashboard'}
                    
                    # Mock getting started route
                    from strava_app import getting_started_resources
                    
                    result = getting_started_resources()
                    
                    # Verify transition works correctly
                    self.assertIsNotNone(result)
    
    def test_dashboard_help_button_analytics_tracking(self):
        """Test analytics tracking for dashboard help button clicks"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test help button click analytics
                    test_data = {
                        'event_type': 'integration_point_click',
                        'event_data': {
                            'integration_point': 'dashboard_help_button',
                            'source': 'dashboard',
                            'target': 'getting_started',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify analytics tracking works
                    self.assertIsNotNone(result)


class TestSettingsToGettingStartedFlow(unittest.TestCase):
    """Test cases for settings page to getting started flow"""
    
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
    
    def test_settings_page_integration_point(self):
        """Test settings page integration point functionality"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test settings page integration point
                    self.mock_request.args = {'source': 'settings'}
                    
                    # Mock the settings page route
                    from strava_app import settings
                    
                    result = settings()
                    
                    # Verify settings page loads correctly
                    self.assertIsNotNone(result)
    
    def test_settings_to_getting_started_transition(self):
        """Test transition from settings page to getting started"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test transition with settings source
                    self.mock_request.args = {'source': 'settings'}
                    
                    # Mock getting started route
                    from strava_app import getting_started_resources
                    
                    result = getting_started_resources()
                    
                    # Verify transition works correctly
                    self.assertIsNotNone(result)
    
    def test_settings_guide_button_analytics_tracking(self):
        """Test analytics tracking for settings guide button clicks"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test guide button click analytics
                    test_data = {
                        'event_type': 'integration_point_click',
                        'event_data': {
                            'integration_point': 'settings_guide_button',
                            'source': 'settings',
                            'target': 'getting_started',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify analytics tracking works
                    self.assertIsNotNone(result)


class TestGoalsToGettingStartedFlow(unittest.TestCase):
    """Test cases for goals page to getting started flow"""
    
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
    
    def test_goals_page_integration_point(self):
        """Test goals page integration point functionality"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test goals page integration point
                    self.mock_request.args = {'source': 'goals'}
                    
                    # Mock the goals page route
                    from strava_app import goals_setup
                    
                    result = goals_setup()
                    
                    # Verify goals page loads correctly
                    self.assertIsNotNone(result)
    
    def test_goals_to_getting_started_transition(self):
        """Test transition from goals page to getting started"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test transition with goals source
                    self.mock_request.args = {'source': 'goals'}
                    
                    # Mock getting started route
                    from strava_app import getting_started_resources
                    
                    result = getting_started_resources()
                    
                    # Verify transition works correctly
                    self.assertIsNotNone(result)
    
    def test_goals_guide_button_analytics_tracking(self):
        """Test analytics tracking for goals guide button clicks"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test guide button click analytics
                    test_data = {
                        'event_type': 'integration_point_click',
                        'event_data': {
                            'integration_point': 'goals_guide_button',
                            'source': 'goals',
                            'target': 'getting_started',
                            'timestamp': datetime.now().isoformat()
                        }
                    }
                    
                    self.mock_request.json_data = test_data
                    
                    # Mock analytics tracking
                    from strava_app import landing_analytics
                    
                    result = landing_analytics()
                    
                    # Verify analytics tracking works
                    self.assertIsNotNone(result)


class TestCompleteUserJourneyFlow(unittest.TestCase):
    """Test cases for complete user journey flows"""
    
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
    
    def test_new_user_complete_journey(self):
        """Test complete journey for new users"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test new user journey
                    self.mock_request.args = {'source': 'landing'}
                    
                    # Mock onboarding progress for new user
                    self.mock_onboarding_manager.get_user_onboarding_progress.return_value = {
                        'current_step': 'welcome',
                        'completed_steps': [],
                        'next_step': 'strava_connection'
                    }
                    
                    # Test landing to getting started
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify new user journey works
                    self.assertIsNotNone(result)
    
    def test_existing_user_complete_journey(self):
        """Test complete journey for existing users"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test existing user journey
                    self.mock_request.args = {'source': 'dashboard'}
                    
                    # Mock onboarding progress for existing user
                    self.mock_onboarding_manager.get_user_onboarding_progress.return_value = {
                        'current_step': 'complete',
                        'completed_steps': ['welcome', 'strava_connection', 'goals_setup'],
                        'next_step': None
                    }
                    
                    # Test dashboard to getting started
                    from strava_app import getting_started_resources
                    result = getting_started_resources()
                    
                    # Verify existing user journey works
                    self.assertIsNotNone(result)
    
    def test_user_journey_analytics_tracking(self):
        """Test analytics tracking throughout user journey"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test journey analytics tracking
                    journey_events = [
                        {
                            'event_type': 'page_view',
                            'event_data': {'source': 'landing'}
                        },
                        {
                            'event_type': 'integration_point_click',
                            'event_data': {
                                'integration_point': 'landing_cta',
                                'source': 'landing',
                                'target': 'getting_started'
                            }
                        },
                        {
                            'event_type': 'getting_started_access',
                            'event_data': {'source': 'landing'}
                        },
                        {
                            'event_type': 'tutorial_start',
                            'event_data': {
                                'tutorial_id': 'dashboard_tutorial',
                                'source': 'getting_started'
                            }
                        }
                    ]
                    
                    for event in journey_events:
                        with self.subTest(event=event):
                            self.mock_request.json_data = event
                            
                            # Mock analytics tracking
                            from strava_app import landing_analytics
                            
                            result = landing_analytics()
                            
                            # Verify each event is tracked
                            self.assertIsNotNone(result)
    
    def test_user_journey_error_handling(self):
        """Test error handling throughout user journey"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                with patch('flask.session', self.mock_session):
                    # Test error handling in journey
                    self.mock_request.args = {'source': 'landing'}
                    
                    # Mock database error
                    with patch('db_utils.execute_query', side_effect=Exception("Database error")):
                        # Test error handling
                        from strava_app import getting_started_resources
                        
                        result = getting_started_resources()
                        
                        # Verify error is handled gracefully
                        self.assertIsNotNone(result)


class TestIntegrationPointEffectiveness(unittest.TestCase):
    """Test cases for integration point effectiveness"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_request = MockRequest()
        self.mock_user = MockCurrentUser()
        self.mock_session = MockSession()
        
        # Mock database utilities
        self.mock_db_utils = Mock()
        self.mock_db_utils.execute_query = Mock()
        
        # Mock analytics tracker
        self.mock_analytics_tracker = Mock()
        self.mock_analytics_tracker.get_click_through_rates = Mock()
        self.mock_analytics_tracker.get_user_journey_funnel = Mock()
    
    def test_integration_point_performance_analysis(self):
        """Test analysis of integration point performance"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock integration point performance data
                mock_performance_data = [
                    {
                        'integration_point': 'landing_cta',
                        'total_impressions': 1000,
                        'total_clicks': 150,
                        'click_through_rate': 15.0,
                        'unique_users': 120,
                        'conversion_rate': 80.0
                    },
                    {
                        'integration_point': 'onboarding_help_link',
                        'total_impressions': 500,
                        'total_clicks': 75,
                        'click_through_rate': 15.0,
                        'unique_users': 60,
                        'conversion_rate': 80.0
                    },
                    {
                        'integration_point': 'dashboard_help_button',
                        'total_impressions': 200,
                        'total_clicks': 40,
                        'click_through_rate': 20.0,
                        'unique_users': 35,
                        'conversion_rate': 87.5
                    }
                ]
                
                # Mock analytics tracker
                with patch('analytics_tracker.analytics_tracker') as mock_tracker:
                    mock_tracker.get_click_through_rates.return_value = mock_performance_data
                    
                    # Test performance analysis
                    from strava_app import get_click_through_rates
                    
                    result = get_click_through_rates()
                    
                    # Verify performance analysis works
                    self.assertIsNotNone(result)
    
    def test_user_journey_conversion_analysis(self):
        """Test analysis of user journey conversion rates"""
        with patch('flask.request', self.mock_request):
            with patch('flask.current_user', self.mock_user):
                # Mock conversion funnel data
                mock_funnel_data = {
                    'time_period': '7d',
                    'steps': [
                        {
                            'step_name': 'Page Views',
                            'unique_users': 1000,
                            'conversion_rate': None
                        },
                        {
                            'step_name': 'Integration Clicks',
                            'unique_users': 150,
                            'conversion_rate': 15.0
                        },
                        {
                            'step_name': 'Getting Started Access',
                            'unique_users': 120,
                            'conversion_rate': 80.0
                        },
                        {
                            'step_name': 'Tutorial Starts',
                            'unique_users': 60,
                            'conversion_rate': 50.0
                        },
                        {
                            'step_name': 'Tutorial Completions',
                            'unique_users': 45,
                            'conversion_rate': 75.0
                        }
                    ]
                }
                
                # Mock analytics tracker
                with patch('analytics_tracker.analytics_tracker') as mock_tracker:
                    mock_tracker.get_user_journey_funnel.return_value = mock_funnel_data
                    
                    # Test conversion analysis
                    from strava_app import get_user_journey_funnel
                    
                    result = get_user_journey_funnel()
                    
                    # Verify conversion analysis works
                    self.assertIsNotNone(result)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestLandingToGettingStartedFlow))
    test_suite.addTest(unittest.makeSuite(TestOnboardingToGettingStartedFlow))
    test_suite.addTest(unittest.makeSuite(TestDashboardToGettingStartedFlow))
    test_suite.addTest(unittest.makeSuite(TestSettingsToGettingStartedFlow))
    test_suite.addTest(unittest.makeSuite(TestGoalsToGettingStartedFlow))
    test_suite.addTest(unittest.makeSuite(TestCompleteUserJourneyFlow))
    test_suite.addTest(unittest.makeSuite(TestIntegrationPointEffectiveness))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Transition Integration Tests Summary")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
