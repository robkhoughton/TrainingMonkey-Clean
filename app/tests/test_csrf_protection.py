"""
Test suite for CSRF protection module
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import time

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from csrf_protection import (
    CSRFProtectionManager, 
    CSRFProtectionLevel, 
    CSRFTokenType,
    CSRFToken,
    csrf_protected,
    require_csrf_token
)


class TestCSRFProtectionManager(unittest.TestCase):
    """Test cases for CSRFProtectionManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = CSRFProtectionManager()
    
    @patch('csrf_protection.session')
    def test_generate_csrf_token_success(self, mock_session):
        """Test successful CSRF token generation"""
        with patch('csrf_protection.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            token = self.manager.generate_csrf_token(CSRFTokenType.FORM)
            
            self.assertIsInstance(token, str)
            self.assertIn('.', token)  # Should contain timestamp
            self.assertGreater(len(token), 32)  # Should be reasonably long
            mock_session.__setitem__.assert_called_once()
    
    @patch('csrf_protection.session')
    def test_generate_csrf_token_with_metadata(self, mock_session):
        """Test CSRF token generation with metadata"""
        with patch('csrf_protection.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            metadata = {'form_name': 'test_form', 'user_id': 123}
            token = self.manager.generate_csrf_token(CSRFTokenType.FORM, user_id=123, metadata=metadata)
            
            self.assertIsInstance(token, str)
            mock_session.__setitem__.assert_called_once()
    
    @patch('csrf_protection.session')
    def test_validate_csrf_token_success(self, mock_session):
        """Test successful CSRF token validation"""
        # Mock session token
        mock_session.get.return_value = 'test_token.1234567890'
        
        with patch.object(self.manager, '_validate_token_format', return_value=True):
            with patch.object(self.manager, '_validate_token_timestamp', return_value=True):
                is_valid, error = self.manager.validate_csrf_token('test_token.1234567890')
                
                self.assertTrue(is_valid)
                self.assertEqual(error, "")
                mock_session.pop.assert_called_once()
    
    @patch('csrf_protection.session')
    def test_validate_csrf_token_missing(self, mock_session):
        """Test CSRF token validation with missing token"""
        is_valid, error = self.manager.validate_csrf_token('')
        
        self.assertFalse(is_valid)
        self.assertIn("required", error)
    
    @patch('csrf_protection.session')
    def test_validate_csrf_token_not_in_session(self, mock_session):
        """Test CSRF token validation with token not in session"""
        mock_session.get.return_value = None
        
        is_valid, error = self.manager.validate_csrf_token('test_token.1234567890')
        
        self.assertFalse(is_valid)
        self.assertIn("not found", error)
    
    @patch('csrf_protection.session')
    def test_validate_csrf_token_mismatch(self, mock_session):
        """Test CSRF token validation with token mismatch"""
        mock_session.get.return_value = 'different_token.1234567890'
        
        with patch.object(self.manager, '_validate_token_format', return_value=True):
            is_valid, error = self.manager.validate_csrf_token('test_token.1234567890')
            
            self.assertFalse(is_valid)
            self.assertIn("mismatch", error)
    
    @patch('csrf_protection.session')
    def test_validate_csrf_token_expired(self, mock_session):
        """Test CSRF token validation with expired token"""
        mock_session.get.return_value = 'test_token.1234567890'
        
        with patch.object(self.manager, '_validate_token_format', return_value=True):
            with patch.object(self.manager, '_validate_token_timestamp', return_value=False):
                with patch.object(self.manager, '_update_session_status', return_value=True):
                    is_valid, error = self.manager.validate_csrf_token('test_token.1234567890')
                    
                    self.assertFalse(is_valid)
                    self.assertIn("expired", error)
    
    @patch('csrf_protection.session')
    def test_validate_csrf_token_enhanced_protection(self, mock_session):
        """Test CSRF token validation with enhanced protection level"""
        self.manager.protection_level = CSRFProtectionLevel.ENHANCED
        mock_session.get.return_value = 'test_token.1234567890'
        
        with patch.object(self.manager, '_validate_token_format', return_value=True):
            with patch.object(self.manager, '_validate_token_timestamp', return_value=True):
                with patch.object(self.manager, '_validate_request_origin', return_value=True):
                    with patch.object(self.manager, '_validate_referer', return_value=True):
                        with patch.object(self.manager, '_validate_https', return_value=True):
                            is_valid, error = self.manager.validate_csrf_token('test_token.1234567890')
                            
                            self.assertTrue(is_valid)
                            self.assertEqual(error, "")
    
    @patch('csrf_protection.session')
    def test_validate_csrf_token_strict_protection(self, mock_session):
        """Test CSRF token validation with strict protection level"""
        self.manager.protection_level = CSRFProtectionLevel.STRICT
        mock_session.get.return_value = 'test_token.1234567890'
        
        with patch.object(self.manager, '_validate_token_format', return_value=True):
            with patch.object(self.manager, '_validate_token_timestamp', return_value=True):
                with patch.object(self.manager, '_validate_request_origin', return_value=True):
                    with patch.object(self.manager, '_validate_referer', return_value=True):
                        with patch.object(self.manager, '_validate_https', return_value=True):
                            with patch.object(self.manager, '_validate_user_context', return_value=True):
                                with patch.object(self.manager, '_validate_ip_address', return_value=True):
                                    is_valid, error = self.manager.validate_csrf_token('test_token.1234567890', user_id=123)
                                    
                                    self.assertTrue(is_valid)
                                    self.assertEqual(error, "")
    
    @patch('csrf_protection.session')
    def test_refresh_csrf_token_success(self, mock_session):
        """Test successful CSRF token refresh"""
        with patch.object(self.manager, 'generate_csrf_token', return_value='new_token.1234567890'):
            new_token = self.manager.refresh_csrf_token(CSRFTokenType.FORM)
            
            self.assertEqual(new_token, 'new_token.1234567890')
            mock_session.pop.assert_called_once()
    
    @patch('csrf_protection.session')
    def test_invalidate_csrf_token_success(self, mock_session):
        """Test successful CSRF token invalidation"""
        success = self.manager.invalidate_csrf_token(CSRFTokenType.FORM)
        
        self.assertTrue(success)
        mock_session.pop.assert_called_once()
    
    def test_get_csrf_token_for_form(self):
        """Test getting CSRF token for specific form"""
        with patch.object(self.manager, 'generate_csrf_token', return_value='form_token.1234567890'):
            token = self.manager.get_csrf_token_for_form('test_form', user_id=123)
            
            self.assertEqual(token, 'form_token.1234567890')
    
    def test_validate_form_submission_success(self):
        """Test successful form submission validation"""
        form_data = {'csrf_token': 'test_token.1234567890'}
        
        with patch.object(self.manager, 'validate_csrf_token', return_value=(True, "")):
            is_valid, error = self.manager.validate_form_submission(form_data, 'test_form', user_id=123)
            
            self.assertTrue(is_valid)
            self.assertEqual(error, "")
    
    def test_validate_form_submission_failure(self):
        """Test form submission validation failure"""
        form_data = {'csrf_token': 'invalid_token'}
        
        with patch.object(self.manager, 'validate_csrf_token', return_value=(False, "Invalid token")):
            is_valid, error = self.manager.validate_form_submission(form_data, 'test_form')
            
            self.assertFalse(is_valid)
            self.assertEqual(error, "Invalid token")
    
    @patch('csrf_protection.session')
    def test_cleanup_expired_tokens(self, mock_session):
        """Test cleanup of expired tokens"""
        # Mock session with expired and valid tokens
        mock_session.keys.return_value = ['csrf_token_form', 'csrf_token_api']
        mock_session.__getitem__.side_effect = lambda key: {
            'csrf_token_form': 'expired_token.1234567890',
            'csrf_token_api': 'valid_token.1234567890'
        }[key]
        
        with patch.object(self.manager, '_is_token_expired', side_effect=[True, False]):
            cleaned_count = self.manager.cleanup_expired_tokens()
            
            self.assertEqual(cleaned_count, 1)
            mock_session.pop.assert_called_once_with('csrf_token_form')
    
    @patch('csrf_protection.session')
    def test_get_csrf_statistics(self, mock_session):
        """Test getting CSRF statistics"""
        # Mock session with tokens
        mock_session.keys.return_value = ['csrf_token_form', 'csrf_token_api', 'csrf_token_session']
        
        stats = self.manager.get_csrf_statistics()
        
        self.assertIn('active_tokens', stats)
        self.assertIn('token_types', stats)
        self.assertIn('protection_level', stats)
        self.assertEqual(stats['active_tokens'], 3)
        self.assertEqual(stats['protection_level'], 'enhanced')
    
    def test_validate_token_format_valid(self):
        """Test token format validation with valid token"""
        token = 'valid_token_with_timestamp.1234567890'
        is_valid = self.manager._validate_token_format(token)
        self.assertTrue(is_valid)
    
    def test_validate_token_format_invalid(self):
        """Test token format validation with invalid token"""
        # Token without timestamp
        token = 'invalid_token_without_timestamp'
        is_valid = self.manager._validate_token_format(token)
        self.assertFalse(is_valid)
        
        # Token too short
        token = 'short.123'
        is_valid = self.manager._validate_token_format(token)
        self.assertFalse(is_valid)
    
    def test_validate_token_timestamp_valid(self):
        """Test token timestamp validation with valid timestamp"""
        current_time = int(time.time())
        token = f'test_token.{current_time}'
        is_valid = self.manager._validate_token_timestamp(token)
        self.assertTrue(is_valid)
    
    def test_validate_token_timestamp_expired(self):
        """Test token timestamp validation with expired timestamp"""
        # Token from 25 hours ago (expired)
        expired_time = int(time.time()) - (25 * 3600)
        token = f'test_token.{expired_time}'
        is_valid = self.manager._validate_token_timestamp(token)
        self.assertFalse(is_valid)
    
    def test_is_token_expired(self):
        """Test token expiration check"""
        # Expired token
        expired_time = int(time.time()) - (25 * 3600)
        expired_token = f'test_token.{expired_time}'
        is_expired = self.manager._is_token_expired(expired_token)
        self.assertTrue(is_expired)
        
        # Valid token
        current_time = int(time.time())
        valid_token = f'test_token.{current_time}'
        is_expired = self.manager._is_token_expired(valid_token)
        self.assertFalse(is_expired)
    
    @patch('csrf_protection.request')
    def test_validate_request_origin_success(self, mock_request):
        """Test request origin validation success"""
        mock_request.headers.get.return_value = 'https://example.com'
        
        with patch('csrf_protection.current_app') as mock_app:
            mock_app.config.get.return_value = []  # No restrictions
            is_valid = self.manager._validate_request_origin()
            self.assertTrue(is_valid)
    
    @patch('csrf_protection.request')
    def test_validate_request_origin_failure(self, mock_request):
        """Test request origin validation failure"""
        mock_request.headers.get.return_value = None
        
        is_valid = self.manager._validate_request_origin()
        self.assertFalse(is_valid)
    
    @patch('csrf_protection.request')
    def test_validate_referer_success(self, mock_request):
        """Test referer validation success"""
        mock_request.headers.get.return_value = 'https://example.com/page'
        mock_request.url = 'https://example.com/api'
        
        is_valid = self.manager._validate_referer()
        self.assertTrue(is_valid)
    
    @patch('csrf_protection.request')
    def test_validate_referer_failure(self, mock_request):
        """Test referer validation failure"""
        mock_request.headers.get.return_value = 'https://malicious.com/page'
        mock_request.url = 'https://example.com/api'
        
        is_valid = self.manager._validate_referer()
        self.assertFalse(is_valid)
    
    @patch('csrf_protection.request')
    def test_validate_https_success(self, mock_request):
        """Test HTTPS validation success"""
        mock_request.headers.get.return_value = 'https'
        mock_request.is_secure = True
        
        is_valid = self.manager._validate_https()
        self.assertTrue(is_valid)
    
    @patch('csrf_protection.request')
    def test_validate_https_localhost(self, mock_request):
        """Test HTTPS validation for localhost"""
        mock_request.headers.get.return_value = None
        mock_request.is_secure = False
        mock_request.host = 'localhost'
        
        is_valid = self.manager._validate_https()
        self.assertTrue(is_valid)
    
    @patch('csrf_protection.request')
    def test_validate_https_failure(self, mock_request):
        """Test HTTPS validation failure"""
        mock_request.headers.get.return_value = None
        mock_request.is_secure = False
        mock_request.host = 'example.com'
        
        is_valid = self.manager._validate_https()
        self.assertFalse(is_valid)
    
    def test_validate_user_context(self):
        """Test user context validation"""
        # This is a placeholder implementation
        is_valid = self.manager._validate_user_context('test_token', 123)
        self.assertTrue(is_valid)
    
    def test_validate_ip_address(self):
        """Test IP address validation"""
        # This is a placeholder implementation
        is_valid = self.manager._validate_ip_address('test_token')
        self.assertTrue(is_valid)


class TestCSRFDecorators(unittest.TestCase):
    """Test cases for CSRF decorators"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = CSRFProtectionManager()
    
    @patch('csrf_protection.request')
    @patch('csrf_protection.csrf_protection')
    def test_csrf_protected_decorator_success(self, mock_csrf_protection, mock_request):
        """Test CSRF protected decorator success"""
        mock_request.method = 'POST'
        mock_request.form.get.return_value = 'valid_token'
        mock_csrf_protection.validate_csrf_token.return_value = (True, "")
        
        @csrf_protected(CSRFTokenType.FORM)
        def test_function():
            return {'success': True}
        
        result = test_function()
        self.assertEqual(result, {'success': True})
    
    @patch('csrf_protection.request')
    @patch('csrf_protection.csrf_protection')
    def test_csrf_protected_decorator_failure(self, mock_csrf_protection, mock_request):
        """Test CSRF protected decorator failure"""
        mock_request.method = 'POST'
        mock_request.form.get.return_value = 'invalid_token'
        mock_csrf_protection.validate_csrf_token.return_value = (False, "Invalid token")
        
        @csrf_protected(CSRFTokenType.FORM)
        def test_function():
            return {'success': True}
        
        result, status_code = test_function()
        self.assertEqual(status_code, 400)
        self.assertIn('error', result)
    
    @patch('csrf_protection.csrf_protection')
    def test_require_csrf_token_decorator(self, mock_csrf_protection):
        """Test require CSRF token decorator"""
        mock_csrf_protection.generate_csrf_token.return_value = 'new_token.1234567890'
        
        @require_csrf_token(CSRFTokenType.FORM)
        def test_function():
            return 'test_template', {'key': 'value'}
        
        template, context = test_function()
        self.assertEqual(template, 'test_template')
        self.assertIn('csrf_token', context)
        self.assertEqual(context['csrf_token'], 'new_token.1234567890')


if __name__ == '__main__':
    unittest.main()
