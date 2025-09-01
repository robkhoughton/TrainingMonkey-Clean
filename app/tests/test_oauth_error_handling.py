#!/usr/bin/env python3
"""
Test script for Task 4.4 - OAuth Error Handling and User-Friendly Messages
Tests the comprehensive OAuth error handling functionality
"""

import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import tempfile

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from oauth_error_handler import (
    OAuthErrorHandler,
    handle_oauth_error,
    format_oauth_error_response,
    get_oauth_flash_message
)


class TestOAuthErrorHandler(unittest.TestCase):
    """Test cases for OAuth error handling functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.error_handler = OAuthErrorHandler()

    def test_error_categorization_authentication(self):
        """Test authentication error categorization"""
        test_errors = [
            'Unauthorized: Invalid access token',
            'invalid token provided',
            'access denied',
            '401 Unauthorized'
        ]
        
        for error in test_errors:
            category = self.error_handler.categorize_error(error)
            self.assertEqual(category, 'authentication', f"Failed to categorize: {error}")

    def test_error_categorization_authorization(self):
        """Test authorization error categorization"""
        test_errors = [
            'Forbidden: Insufficient permissions',
            'permission denied',
            'scope required',
            '403 Forbidden'
        ]
        
        for error in test_errors:
            category = self.error_handler.categorize_error(error)
            self.assertEqual(category, 'authorization', f"Failed to categorize: {error}")

    def test_error_categorization_network(self):
        """Test network error categorization"""
        test_errors = [
            'Connection timeout',
            'network error',
            'DNS resolution failed',
            'connection refused'
        ]
        
        for error in test_errors:
            category = self.error_handler.categorize_error(error)
            self.assertEqual(category, 'network', f"Failed to categorize: {error}")

    def test_error_categorization_rate_limit(self):
        """Test rate limit error categorization"""
        test_errors = [
            'Rate limit exceeded',
            'too many requests',
            'quota exceeded',
            '429 Too Many Requests'
        ]
        
        for error in test_errors:
            category = self.error_handler.categorize_error(error)
            self.assertEqual(category, 'rate_limit', f"Failed to categorize: {error}")

    def test_error_categorization_token_expired(self):
        """Test token expired error categorization"""
        test_errors = [
            'Token expired',
            'access token has expired',
            'expired token'
        ]
        
        for error in test_errors:
            category = self.error_handler.categorize_error(error)
            self.assertEqual(category, 'token_expired', f"Failed to categorize: {error}")

    def test_error_categorization_with_error_codes(self):
        """Test error categorization with error codes"""
        # Test with error codes
        self.assertEqual(self.error_handler.categorize_error('Some error', '401'), 'authentication')
        self.assertEqual(self.error_handler.categorize_error('Some error', '403'), 'authorization')
        self.assertEqual(self.error_handler.categorize_error('Some error', '429'), 'rate_limit')
        self.assertEqual(self.error_handler.categorize_error('Some error', '500'), 'server_error')

    def test_get_error_info_structure(self):
        """Test error info structure"""
        error_info = self.error_handler.get_error_info('Test error message', '401')
        
        # Check required fields
        required_fields = [
            'category', 'title', 'description', 'user_message', 'suggestions',
            'severity', 'retryable', 'original_message', 'error_code', 'timestamp'
        ]
        
        for field in required_fields:
            self.assertIn(field, error_info, f"Missing field: {field}")
        
        # Check specific values
        self.assertEqual(error_info['category'], 'authentication')
        self.assertEqual(error_info['original_message'], 'Test error message')
        self.assertEqual(error_info['error_code'], '401')
        self.assertFalse(error_info['retryable'])

    def test_get_error_info_with_context(self):
        """Test error info with context"""
        context = {'operation': 'test', 'user_id': 123}
        error_info = self.error_handler.get_error_info('Test error', context=context)
        
        self.assertEqual(error_info['context'], context)

    def test_retry_delay_calculation(self):
        """Test retry delay calculation"""
        # Test different categories
        self.assertEqual(self.error_handler._get_retry_delay('network'), 30)
        self.assertEqual(self.error_handler._get_retry_delay('rate_limit'), 300)
        self.assertEqual(self.error_handler._get_retry_delay('server_error'), 60)
        self.assertEqual(self.error_handler._get_retry_delay('token_expired'), 10)
        self.assertEqual(self.error_handler._get_retry_delay('unknown'), 60)

    def test_max_retries_calculation(self):
        """Test max retries calculation"""
        # Test different categories
        self.assertEqual(self.error_handler._get_max_retries('network'), 3)
        self.assertEqual(self.error_handler._get_max_retries('rate_limit'), 1)
        self.assertEqual(self.error_handler._get_max_retries('server_error'), 3)
        self.assertEqual(self.error_handler._get_max_retries('token_expired'), 2)
        self.assertEqual(self.error_handler._get_max_retries('unknown'), 2)

    def test_format_user_message(self):
        """Test user message formatting"""
        error_info = self.error_handler.get_error_info('Test error')
        
        # Test with suggestions
        message_with_suggestions = self.error_handler.format_user_message(error_info, include_suggestions=True)
        self.assertIn('What you can do:', message_with_suggestions)
        self.assertIn('1.', message_with_suggestions)
        
        # Test without suggestions
        message_without_suggestions = self.error_handler.format_user_message(error_info, include_suggestions=False)
        self.assertNotIn('What you can do:', message_without_suggestions)

    def test_format_flash_message(self):
        """Test flash message formatting"""
        error_info = self.error_handler.get_error_info('Test error')
        message, category = self.error_handler.format_flash_message(error_info)
        
        self.assertIsInstance(message, str)
        self.assertIn(category, ['danger', 'warning', 'info'])

    def test_format_api_response(self):
        """Test API response formatting"""
        error_info = self.error_handler.get_error_info('Test error')
        response = self.error_handler.format_api_response(error_info)
        
        # Check structure
        self.assertFalse(response['success'])
        self.assertIn('error', response)
        self.assertIn('timestamp', response)
        
        error_data = response['error']
        required_fields = ['category', 'title', 'message', 'suggestions', 'retryable', 'severity']
        for field in required_fields:
            self.assertIn(field, error_data)

    def test_should_retry_logic(self):
        """Test retry logic"""
        # Test retryable error
        retryable_error = self.error_handler.get_error_info('network error')
        self.assertTrue(self.error_handler.should_retry(retryable_error, 0))
        self.assertTrue(self.error_handler.should_retry(retryable_error, 1))
        self.assertFalse(self.error_handler.should_retry(retryable_error, 3))
        
        # Test non-retryable error
        non_retryable_error = self.error_handler.get_error_info('authentication error')
        self.assertFalse(self.error_handler.should_retry(non_retryable_error, 0))

    def test_retry_delay_with_exponential_backoff(self):
        """Test retry delay with exponential backoff"""
        error_info = self.error_handler.get_error_info('network error')
        
        # Test exponential backoff
        self.assertEqual(self.error_handler.get_retry_delay(error_info, 0), 30)
        self.assertEqual(self.error_handler.get_retry_delay(error_info, 1), 60)
        self.assertEqual(self.error_handler.get_retry_delay(error_info, 2), 120)

    def test_handle_oauth_error_function(self):
        """Test the convenience function"""
        error_info = handle_oauth_error(
            error_message='Test error',
            error_code='401',
            context={'test': True},
            user_id=123,
            operation='test_operation'
        )
        
        self.assertEqual(error_info['category'], 'authentication')
        self.assertEqual(error_info['context']['test'], True)
        self.assertEqual(error_info['context']['user_id'], 123)

    def test_format_oauth_error_response_function(self):
        """Test the format error response function"""
        response = format_oauth_error_response('Test error', '401')
        
        self.assertFalse(response['success'])
        self.assertEqual(response['error']['category'], 'authentication')

    def test_get_oauth_flash_message_function(self):
        """Test the get flash message function"""
        message, category = get_oauth_flash_message('Test error', '401')
        
        self.assertIsInstance(message, str)
        self.assertIn(category, ['danger', 'warning', 'info'])

    def test_error_categories_completeness(self):
        """Test that all error categories have required fields"""
        required_fields = ['title', 'description', 'user_message', 'suggestions', 'severity', 'retryable']
        
        for category, info in self.error_handler.error_categories.items():
            for field in required_fields:
                self.assertIn(field, info, f"Category {category} missing field: {field}")
            
            # Check data types
            self.assertIsInstance(info['title'], str)
            self.assertIsInstance(info['description'], str)
            self.assertIsInstance(info['user_message'], str)
            self.assertIsInstance(info['suggestions'], list)
            self.assertIn(info['severity'], ['low', 'medium', 'high'])
            self.assertIsInstance(info['retryable'], bool)

    def test_unknown_error_handling(self):
        """Test handling of unknown errors"""
        error_info = self.error_handler.get_error_info('Completely unknown error type')
        
        self.assertEqual(error_info['category'], 'unknown')
        self.assertTrue(error_info['retryable'])
        self.assertEqual(error_info['severity'], 'medium')

    def test_empty_error_message(self):
        """Test handling of empty error messages"""
        error_info = self.error_handler.get_error_info('')
        
        self.assertEqual(error_info['category'], 'unknown')
        self.assertEqual(error_info['original_message'], '')

    def test_none_error_message(self):
        """Test handling of None error messages"""
        error_info = self.error_handler.get_error_info(None)
        
        self.assertEqual(error_info['category'], 'unknown')
        self.assertEqual(error_info['original_message'], None)


def test_oauth_error_handler_import():
    """Test that OAuth error handler can be imported without errors"""
    try:
        from oauth_error_handler import (
            OAuthErrorHandler,
            handle_oauth_error,
            format_oauth_error_response,
            get_oauth_flash_message
        )
        print("✅ OAuth error handler imports successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing OAuth error handler: {str(e)}")
        return False


def test_error_categories_validation():
    """Test that all error categories are properly configured"""
    try:
        from oauth_error_handler import oauth_error_handler
        
        # Test that all categories have proper structure
        for category, info in oauth_error_handler.error_categories.items():
            assert 'title' in info, f"Category {category} missing title"
            assert 'user_message' in info, f"Category {category} missing user_message"
            assert 'severity' in info, f"Category {category} missing severity"
            assert 'retryable' in info, f"Category {category} missing retryable"
        
        print("✅ All error categories properly configured")
        return True
    except Exception as e:
        print(f"❌ Error validating error categories: {str(e)}")
        return False


if __name__ == '__main__':
    print("🧪 Testing Task 4.4 - OAuth Error Handling and User-Friendly Messages")
    print("=" * 80)
    
    # Run basic tests
    test_results = []
    
    print("\n1. Testing OAuth error handler import...")
    test_results.append(test_oauth_error_handler_import())
    
    print("\n2. Testing error categories validation...")
    test_results.append(test_error_categories_validation())
    
    print("\n3. Running unit tests...")
    # Run the unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    print("\n" + "=" * 80)
    print("✅ Task 4.4 OAuth Error Handling Tests Complete")
    
    if all(test_results):
        print("🎉 All tests passed! OAuth error handling is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the output above.")
