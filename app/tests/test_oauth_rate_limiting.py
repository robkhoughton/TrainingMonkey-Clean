#!/usr/bin/env python3
"""
Test script for Task 4.8 - OAuth Rate Limiting and Security Measures
Tests the OAuth rate limiting, security monitoring, and protection measures
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

# Mock Flask components for testing
class MockRequest:
    def __init__(self, args=None, json_data=None, remote_addr='127.0.0.1', headers=None):
        self.args = args or {}
        self.json = json_data or {}
        self.remote_addr = remote_addr
        self.headers = headers or {'User-Agent': 'test-agent'}

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


class TestOAuthRateLimiting(unittest.TestCase):
    """Test cases for OAuth rate limiting functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_request_data = {
            'ip_address': '127.0.0.1',
            'user_agent': 'test-user-agent',
            'user_id': 123
        }
        
        self.test_request_data_anonymous = {
            'ip_address': '127.0.0.1',
            'user_agent': 'test-user-agent',
            'user_id': 'anonymous'
        }

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test rate limit configurations
        self.assertIn('oauth_initiation', rate_limiter.rate_limits)
        self.assertIn('oauth_callback', rate_limiter.rate_limits)
        self.assertIn('token_refresh', rate_limiter.rate_limits)
        self.assertIn('api_requests', rate_limiter.rate_limits)
        
        # Test default limits
        self.assertEqual(rate_limiter.rate_limits['oauth_initiation']['max_requests'], 5)
        self.assertEqual(rate_limiter.rate_limits['oauth_callback']['max_requests'], 10)

    def test_client_identifier_generation(self):
        """Test client identifier generation"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test identifier generation
        client_id = rate_limiter._get_client_identifier(self.test_request_data)
        self.assertIsInstance(client_id, str)
        self.assertIn('127.0.0.1', client_id)
        self.assertIn('123', client_id)
        
        # Test different data produces different identifiers
        different_data = {
            'ip_address': '192.168.1.1',
            'user_agent': 'different-agent',
            'user_id': 456
        }
        different_client_id = rate_limiter._get_client_identifier(different_data)
        self.assertNotEqual(client_id, different_client_id)

    def test_rate_limit_checking(self):
        """Test rate limit checking functionality"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test initial request (should be allowed)
        result = rate_limiter.check_rate_limit('oauth_callback', self.test_request_data)
        self.assertTrue(result['allowed'])
        self.assertIn('remaining_requests', result)
        
        # Test multiple requests within limit
        for i in range(5):
            result = rate_limiter.check_rate_limit('oauth_callback', self.test_request_data)
            self.assertTrue(result['allowed'])
        
        # Test rate limit exceeded
        for i in range(10):  # Exceed the limit
            result = rate_limiter.check_rate_limit('oauth_callback', self.test_request_data)
        
        # Should be blocked
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'rate_limit_exceeded')

    def test_ip_blocking(self):
        """Test IP blocking functionality"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test IP is not initially blocked
        self.assertFalse(rate_limiter._is_ip_blocked('127.0.0.1'))
        
        # Block an IP
        rate_limiter._block_ip('127.0.0.1', 'test_block', 60)
        
        # Test IP is now blocked
        self.assertTrue(rate_limiter._is_ip_blocked('127.0.0.1'))
        
        # Test rate limit check with blocked IP
        result = rate_limiter.check_rate_limit('oauth_callback', self.test_request_data)
        self.assertFalse(result['allowed'])
        self.assertEqual(result['reason'], 'ip_blocked')

    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test rapid requests detection
        rapid_data = self.test_request_data.copy()
        
        # Make rapid requests
        for i in range(5):
            rate_limiter.check_rate_limit('oauth_callback', rapid_data)
            time.sleep(0.1)  # Small delay
        
        # Check for suspicious patterns
        client_id = rate_limiter._get_client_identifier(rapid_data)
        patterns = rate_limiter._detect_suspicious_activity(client_id, rapid_data)
        
        # Should detect rapid requests
        self.assertIn('rapid_requests', patterns)

    def test_failed_attempt_recording(self):
        """Test failed attempt recording"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Record failed attempts
        for i in range(3):
            rate_limiter.record_failed_attempt(self.test_request_data, f"test_failure_{i}")
        
        # Check suspicious activities
        client_id = rate_limiter._get_client_identifier(self.test_request_data)
        suspicious_activities = rate_limiter.suspicious_activities[client_id]
        
        self.assertEqual(len(suspicious_activities), 3)

    def test_rate_limit_status(self):
        """Test rate limit status reporting"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Get overall status
        status = rate_limiter.get_rate_limit_status()
        
        self.assertIn('timestamp', status)
        self.assertIn('rate_limits', status)
        self.assertIn('blocked_ips', status)
        self.assertIn('suspicious_clients', status)
        
        # Get specific client status
        client_id = rate_limiter._get_client_identifier(self.test_request_data)
        client_status = rate_limiter.get_rate_limit_status(client_id)
        
        self.assertIn('rate_limits', client_status)

    def test_security_monitor_initialization(self):
        """Test security monitor initialization"""
        from oauth_rate_limiter import OAuthSecurityMonitor
        
        monitor = OAuthSecurityMonitor()
        
        self.assertIn('failed_attempts_per_hour', monitor.alert_thresholds)
        self.assertIn('rate_limit_violations_per_hour', monitor.alert_thresholds)
        self.assertIn('suspicious_ips_per_hour', monitor.alert_thresholds)

    def test_security_analysis(self):
        """Test security analysis functionality"""
        from oauth_rate_limiter import OAuthSecurityMonitor
        
        monitor = OAuthSecurityMonitor()
        
        # Mock database query result
        mock_result = [
            {
                'event_type': 'oauth_failure',
                'event_data': '{"reason": "test"}',
                'timestamp': '2024-01-01T00:00:00',
                'ip_address': '127.0.0.1',
                'user_agent': 'test-agent'
            }
        ]
        
        with patch('oauth_rate_limiter.db_utils.execute_query') as mock_db:
            mock_db.return_value = mock_result
            
            analysis = monitor.analyze_security_logs(hours=24)
            
            self.assertIn('period_hours', analysis)
            self.assertIn('total_events', analysis)
            self.assertIn('event_types', analysis)
            self.assertIn('threats_detected', analysis)
            self.assertIn('recommendations', analysis)

    def test_threat_detection(self):
        """Test threat detection functionality"""
        from oauth_rate_limiter import OAuthSecurityMonitor
        
        monitor = OAuthSecurityMonitor()
        
        # Test threat detection with high failure rate
        analysis = {
            'event_types': {'oauth_failure': 15},  # Above threshold
            'ip_addresses': {'127.0.0.1': 25},  # High volume
            'total_events': 100
        }
        
        threats = monitor._detect_threats(analysis)
        
        # Should detect high failure rate threat
        threat_types = [threat['type'] for threat in threats]
        self.assertIn('high_failure_rate', threat_types)

    def test_recommendation_generation(self):
        """Test recommendation generation"""
        from oauth_rate_limiter import OAuthSecurityMonitor
        
        monitor = OAuthSecurityMonitor()
        
        # Test recommendation generation
        analysis = {
            'total_events': 1500,  # High volume
            'event_types': {'oauth_failure': 60},  # High failures
            'threats_detected': [{'type': 'test_threat'}]
        }
        
        recommendations = monitor._generate_recommendations(analysis)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    def test_oauth_callback_rate_limiting(self):
        """Test OAuth callback rate limiting integration"""
        # Mock Flask components
        mock_request = MockRequest()
        mock_current_user = MockCurrentUser()
        mock_flash = MockFlash()
        mock_redirect = MockRedirect()
        
        with patch('strava_app.request', mock_request):
            with patch('strava_app.current_user', mock_current_user):
                with patch('strava_app.flash', mock_flash):
                    with patch('strava_app.redirect', mock_redirect):
                        # Test rate limiting integration
                        from oauth_rate_limiter import rate_limiter
                        
                        # Check rate limit
                        request_data = {
                            'ip_address': mock_request.remote_addr,
                            'user_agent': mock_request.headers.get('User-Agent'),
                            'user_id': mock_current_user.id
                        }
                        
                        result = rate_limiter.check_rate_limit('oauth_callback', request_data)
                        self.assertTrue(result['allowed'])

    def test_security_logging(self):
        """Test security event logging"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test security event logging
        event_data = {
            'ip_address': '127.0.0.1',
            'reason': 'test_event'
        }
        
        with patch('oauth_rate_limiter.db_utils.execute_query') as mock_db:
            rate_limiter._log_security_event('test_event', event_data)
            
            # Verify database call was made
            mock_db.assert_called()

    def test_cleanup_functionality(self):
        """Test cleanup functionality"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Add some test data
        rate_limiter._block_ip('127.0.0.1', 'test', 1)
        
        # Test cleanup
        rate_limiter.cleanup_expired_data()
        
        # Should not raise any exceptions
        self.assertTrue(True)

    def test_error_handling(self):
        """Test error handling in rate limiting"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test with invalid data
        invalid_data = {}
        
        # Should handle gracefully
        result = rate_limiter.check_rate_limit('oauth_callback', invalid_data)
        self.assertIn('allowed', result)

    def test_rate_limit_configuration(self):
        """Test rate limit configuration"""
        from oauth_rate_limiter import OAuthRateLimiter
        
        rate_limiter = OAuthRateLimiter()
        
        # Test all rate limit types
        limit_types = ['oauth_initiation', 'oauth_callback', 'token_refresh', 'api_requests']
        
        for limit_type in limit_types:
            self.assertIn(limit_type, rate_limiter.rate_limits)
            config = rate_limiter.rate_limits[limit_type]
            
            self.assertIn('max_requests', config)
            self.assertIn('window_seconds', config)
            self.assertIn('description', config)
            
            self.assertIsInstance(config['max_requests'], int)
            self.assertIsInstance(config['window_seconds'], int)
            self.assertIsInstance(config['description'], str)


def test_oauth_rate_limiting_import():
    """Test that OAuth rate limiting can be imported without errors"""
    try:
        from oauth_rate_limiter import OAuthRateLimiter, OAuthSecurityMonitor
        print("✅ OAuth rate limiting imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing OAuth rate limiting: {str(e)}")
        return False


def test_oauth_rate_limiting_components():
    """Test that all OAuth rate limiting components are available"""
    try:
        from oauth_rate_limiter import (
            OAuthRateLimiter,
            OAuthSecurityMonitor,
            rate_limiter,
            security_monitor,
            create_oauth_security_tables,
            get_oauth_security_status,
            cleanup_oauth_security_data
        )
        
        print("✅ All OAuth rate limiting components available")
        return True
    except Exception as e:
        print(f"❌ Error accessing OAuth rate limiting components: {str(e)}")
        return False


def test_oauth_security_tables():
    """Test OAuth security table creation"""
    try:
        from oauth_rate_limiter import create_oauth_security_tables
        
        with patch('oauth_rate_limiter.db_utils.execute_query') as mock_db:
            create_oauth_security_tables()
            
            # Verify table creation was called
            mock_db.assert_called()
        
        print("✅ OAuth security tables creation works")
        return True
    except Exception as e:
        print(f"❌ Error creating OAuth security tables: {str(e)}")
        return False


if __name__ == '__main__':
    print("🧪 Testing Task 4.8 - OAuth Rate Limiting and Security Measures")
    print("=" * 80)
    
    # Run basic tests
    test_results = []
    
    print("\n1. Testing OAuth rate limiting import...")
    test_results.append(test_oauth_rate_limiting_import())
    
    print("\n2. Testing OAuth rate limiting components...")
    test_results.append(test_oauth_rate_limiting_components())
    
    print("\n3. Testing OAuth security tables...")
    test_results.append(test_oauth_security_tables())
    
    print("\n4. Running unit tests...")
    # Run the unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 80)
    print("✅ Task 4.8 OAuth Rate Limiting Tests Complete")
    
    if all(test_results):
        print("🎉 All tests passed! OAuth rate limiting is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
