"""
Test suite for registration validation module
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime
from flask import Flask

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create a test Flask app for context
app = Flask(__name__)
app.config['TESTING'] = True

from registration_validation import RegistrationValidator


class TestRegistrationValidator(unittest.TestCase):
    """Test cases for RegistrationValidator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.validator = RegistrationValidator()
        
    def test_validate_email_valid(self):
        """Test valid email addresses"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                is_valid, error = self.validator.validate_email(email)
                self.assertTrue(is_valid, f"Email {email} should be valid: {error}")
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses"""
        invalid_emails = [
            '',  # Empty
            'invalid-email',  # No @
            '@example.com',  # No local part
            'user@',  # No domain
            'user@.com',  # No domain name
            'user@example',  # No TLD
            'user space@example.com',  # Space in local part
            'user@example space.com',  # Space in domain
            'a' * 255 + '@example.com'  # Too long
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                is_valid, error = self.validator.validate_email(email)
                self.assertFalse(is_valid, f"Email {email} should be invalid")
                self.assertTrue(error, "Should return error message")
    
    def test_validate_email_disposable_domains(self):
        """Test disposable email domain rejection"""
        disposable_emails = [
            'test@10minutemail.com',
            'user@tempmail.org',
            'test@guerrillamail.com'
        ]
        
        for email in disposable_emails:
            with self.subTest(email=email):
                is_valid, error = self.validator.validate_email(email)
                self.assertFalse(is_valid, f"Disposable email {email} should be rejected")
                self.assertIn("disposable", error.lower())
    
    @patch('registration_validation.execute_query')
    def test_validate_email_already_exists(self, mock_execute):
        """Test email uniqueness validation"""
        # Mock existing user
        mock_execute.return_value = [{'id': 1}]
        
        is_valid, error = self.validator.validate_email('existing@example.com')
        self.assertFalse(is_valid)
        self.assertIn("already exists", error)
    
    @patch('registration_validation.execute_query')
    def test_validate_email_unique(self, mock_execute):
        """Test unique email validation"""
        # Mock no existing user
        mock_execute.return_value = []
        
        is_valid, error = self.validator.validate_email('new@example.com')
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    @patch('registration_validation.execute_query')
    def test_validate_email_database_error(self, mock_execute):
        """Test email validation with database error"""
        # Mock database error
        mock_execute.side_effect = Exception("Database error")
        
        is_valid, error = self.validator.validate_email('test@example.com')
        self.assertFalse(is_valid)
        self.assertIn("Unable to verify email address", error)
    
    def test_validate_password_valid(self):
        """Test valid passwords"""
        valid_passwords = [
            'StrongPass123!',
            'MySecureP@ssw0rd',
            'Complex#Password1',
            'ValidP@ss123'
        ]
        
        for password in valid_passwords:
            with self.subTest(password=password):
                is_valid, errors = self.validator.validate_password(password)
                self.assertTrue(is_valid, f"Password should be valid: {errors}")
    
    def test_validate_password_invalid(self):
        """Test invalid passwords"""
        test_cases = [
            ('', ['Password is required']),
            ('short', ['Password must be at least 8 characters long', 'Password must contain at least one uppercase letter', 'Password must contain at least one number', 'Password must contain at least one special character']),
            ('nouppercase123!', ['Password must contain at least one uppercase letter']),
            ('NOLOWERCASE123!', ['Password must contain at least one lowercase letter']),
            ('NoNumbers!', ['Password must contain at least one number']),
            ('NoSpecial123', ['Password must contain at least one special character']),
            ('password', ['Password must be at least 8 characters long', 'Password must contain at least one uppercase letter', 'Password must contain at least one number', 'Password must contain at least one special character']),
            ('password123', ['Password must contain at least one uppercase letter', 'Password must contain at least one special character']),
            ('aaa123!', ['Password must be at least 8 characters long', 'Password must contain at least one uppercase letter', 'Password contains too many repeated characters'])
        ]
        
        for password, expected_errors in test_cases:
            with self.subTest(password=password):
                is_valid, errors = self.validator.validate_password(password)
                self.assertFalse(is_valid)
                for expected_error in expected_errors:
                    self.assertIn(expected_error, errors)
    
    def test_validate_password_weak_passwords(self):
        """Test weak password rejection"""
        weak_passwords = [
            'password',
            '123456',
            'password123',
            'qwerty',
            'abc123'
        ]
        
        for password in weak_passwords:
            with self.subTest(password=password):
                is_valid, errors = self.validator.validate_password(password)
                self.assertFalse(is_valid)
                self.assertIn("too common", errors[0])
    
    def test_validate_password_confirmation(self):
        """Test password confirmation validation"""
        # Valid confirmation
        is_valid, error = self.validator.validate_password_confirmation('password123', 'password123')
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
        
        # Mismatch
        is_valid, error = self.validator.validate_password_confirmation('password123', 'different123')
        self.assertFalse(is_valid)
        self.assertIn("do not match", error)
        
        # Empty confirmation
        is_valid, error = self.validator.validate_password_confirmation('password123', '')
        self.assertFalse(is_valid)
        self.assertIn("confirm your password", error)
    
    def test_validate_legal_acceptance(self):
        """Test legal document acceptance validation"""
        # All accepted
        is_valid, errors = self.validator.validate_legal_acceptance(True, True, True)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
        
        # Terms not accepted
        is_valid, errors = self.validator.validate_legal_acceptance(False, True, True)
        self.assertFalse(is_valid)
        self.assertIn("Terms and Conditions", errors[0])
        
        # Privacy not accepted
        is_valid, errors = self.validator.validate_legal_acceptance(True, False, True)
        self.assertFalse(is_valid)
        self.assertIn("Privacy Policy", errors[0])
        
        # Disclaimer not accepted
        is_valid, errors = self.validator.validate_legal_acceptance(True, True, False)
        self.assertFalse(is_valid)
        self.assertIn("Medical Disclaimer", errors[0])
        
        # None accepted
        is_valid, errors = self.validator.validate_legal_acceptance(False, False, False)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 3)
    
    def test_validate_csrf_token(self):
        """Test CSRF token validation"""
        with app.test_request_context():
            # Mock session
            with patch('registration_validation.session') as mock_session:
                mock_session.get.return_value = 'valid_token'
                
                # Valid token
                is_valid, error = self.validator.validate_csrf_token('valid_token')
                self.assertTrue(is_valid)
                self.assertEqual(error, "")
                
                # Invalid token
                is_valid, error = self.validator.validate_csrf_token('invalid_token')
                self.assertFalse(is_valid)
                self.assertIn("Invalid security token", error)
                
                # Missing token
                is_valid, error = self.validator.validate_csrf_token('')
                self.assertFalse(is_valid)
                self.assertIn("Security token is missing", error)
                
                # No session token
                mock_session.get.return_value = None
                is_valid, error = self.validator.validate_csrf_token('any_token')
                self.assertFalse(is_valid)
                self.assertIn("Security token expired", error)
    
    def test_check_rate_limit(self):
        """Test rate limiting"""
        ip_address = '192.168.1.1'
        
        # First attempt should succeed
        is_allowed, error = self.validator.check_rate_limit(ip_address)
        self.assertTrue(is_allowed)
        self.assertEqual(error, "")
        
        # Multiple attempts within limit should succeed
        for i in range(4):  # 4 more attempts (total 5)
            is_allowed, error = self.validator.check_rate_limit(ip_address)
            self.assertTrue(is_allowed, f"Attempt {i+2} should be allowed")
        
        # 6th attempt should be blocked
        is_allowed, error = self.validator.check_rate_limit(ip_address)
        self.assertFalse(is_allowed)
        self.assertIn("Too many registration attempts", error)
    
    def test_generate_csrf_token(self):
        """Test CSRF token generation"""
        with app.test_request_context():
            with patch('registration_validation.session') as mock_session:
                token = self.validator.generate_csrf_token()
                
                self.assertIsInstance(token, str)
                self.assertEqual(len(token), 64)  # SHA256 hash length
                mock_session.__setitem__.assert_called_with('csrf_token', token)
    
    @patch('registration_validation.execute_query')
    def test_create_user_account_success(self, mock_execute):
        """Test successful user account creation"""
        # Mock successful database insertion
        mock_execute.return_value = [{'id': 123}]
        
        with app.test_request_context():
            with patch('registration_validation.get_current_legal_versions') as mock_versions:
                mock_versions.return_value = {
                    'terms': '2.0',
                    'privacy': '2.0',
                    'disclaimer': '2.0'
                }
                
                success, user_id, error = self.validator.create_user_account('test@example.com', 'password123')
                
                self.assertTrue(success)
                self.assertEqual(user_id, 123)
                self.assertEqual(error, "")
    
    @patch('registration_validation.execute_query')
    def test_create_user_account_failure(self, mock_execute):
        """Test user account creation failure"""
        # Mock database error
        mock_execute.side_effect = Exception("Database error")
        
        success, user_id, error = self.validator.create_user_account('test@example.com', 'password123')
        
        self.assertFalse(success)
        self.assertIsNone(user_id)
        self.assertIn("Unable to create account", error)
    
    def test_validate_registration_data_comprehensive(self):
        """Test comprehensive registration data validation"""
        with app.test_request_context():
            # Mock dependencies
            with patch.object(self.validator, 'check_rate_limit') as mock_rate:
                with patch.object(self.validator, 'validate_email') as mock_email:
                    with patch.object(self.validator, 'validate_password') as mock_password:
                        with patch.object(self.validator, 'validate_password_confirmation') as mock_confirm:
                            with patch.object(self.validator, 'validate_legal_acceptance') as mock_legal:
                                with patch.object(self.validator, 'validate_csrf_token') as mock_csrf:
                                    
                                    # All valid
                                    mock_rate.return_value = (True, "")
                                    mock_email.return_value = (True, "")
                                    mock_password.return_value = (True, [])
                                    mock_confirm.return_value = (True, "")
                                    mock_legal.return_value = (True, [])
                                    mock_csrf.return_value = (True, "")
                                    
                                    form_data = {
                                        'email': 'test@example.com',
                                        'password': 'Password123!',
                                        'confirm_password': 'Password123!',
                                        'terms_accepted': 'on',
                                        'privacy_accepted': 'on',
                                        'disclaimer_accepted': 'on',
                                        'csrf_token': 'valid_token'
                                    }
                                    
                                    is_valid, errors = self.validator.validate_registration_data(form_data)
                                    self.assertTrue(is_valid)
                                    self.assertEqual(errors, {})
                                    
                                    # Invalid email
                                    mock_email.return_value = (False, "Invalid email")
                                    is_valid, errors = self.validator.validate_registration_data(form_data)
                                    self.assertFalse(is_valid)
                                    self.assertIn('email', errors)
                                    self.assertIn("Invalid email", errors['email'])


if __name__ == '__main__':
    unittest.main()
