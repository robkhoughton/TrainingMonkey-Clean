"""
Test Suite for Email Validation Module

This module tests the comprehensive email validation functionality including
format validation, uniqueness checking, and integration features.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from datetime import datetime

# Add the app directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_validation import (
    EmailValidator, 
    EmailValidationResult,
    validate_email_format,
    check_email_uniqueness,
    validate_email_for_registration,
    validate_email_for_update,
    get_email_suggestions
)


class TestEmailValidation(unittest.TestCase):
    """Test cases for email validation functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = EmailValidator()
    
    def test_valid_email_format(self):
        """Test valid email formats"""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@subdomain.example.com",
            "user@example.co.uk",
            "user123@example.com",
            "user-name@example.com",
            "user_name@example.com"
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                result = self.validator.validate_email_format(email)
                self.assertTrue(result.is_valid, f"Email {email} should be valid")
                self.assertEqual(len(result.errors), 0, f"No errors expected for {email}")
    
    def test_invalid_email_format(self):
        """Test invalid email formats"""
        invalid_emails = [
            "",  # Empty
            "invalid-email",  # No @
            "user@",  # No domain
            "@example.com",  # No local part
            "user@@example.com",  # Multiple @
            "user@.com",  # Empty domain
            "user@example",  # No TLD
            "user@example..com",  # Double dots
            "user@example.com.",  # Trailing dot
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                result = self.validator.validate_email_format(email)
                self.assertFalse(result.is_valid, f"Email {email} should be invalid")
                self.assertGreater(len(result.errors), 0, f"Errors expected for {email}")
    
    def test_email_length_validation(self):
        """Test email length validation"""
        # Test too short
        result = self.validator.validate_email_format("a@b")
        self.assertFalse(result.is_valid)
        self.assertIn("too short", result.errors[0])
        
        # Test too long (over 254 characters)
        long_email = "a" * 250 + "@example.com"
        result = self.validator.validate_email_format(long_email)
        self.assertFalse(result.is_valid)
        self.assertIn("too long", result.errors[0])
    
    def test_common_typos_detection(self):
        """Test detection of common email typos"""
        typo_emails = [
            "user@gamil.com",  # gmail typo
            "user@hotmai.com",  # hotmail typo
            "user@yahooo.com",  # yahoo typo
        ]
        
        for email in typo_emails:
            with self.subTest(email=email):
                result = self.validator.validate_email_format(email)
                self.assertTrue(result.validation_details['has_common_typo'])
                self.assertIsNotNone(result.validation_details['suggested_correction'])
                self.assertGreater(len(result.suggestions), 0)
    
    def test_disposable_email_detection(self):
        """Test detection of disposable email domains"""
        disposable_emails = [
            "user@10minutemail.com",
            "user@guerrillamail.com",
            "user@mailinator.com",
        ]
        
        for email in disposable_emails:
            with self.subTest(email=email):
                result = self.validator.validate_email_format(email)
                self.assertFalse(result.is_valid)
                self.assertIn("Disposable email addresses are not allowed", result.errors)
    
    @patch('email_validation.get_db_connection')
    def test_email_uniqueness_check_new_email(self, mock_connection):
        """Test email uniqueness check for new email"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No existing user
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.validator.check_email_uniqueness("newuser@example.com")
        
        self.assertTrue(result.is_valid)
        self.assertTrue(result.validation_details['is_unique'])
        self.assertEqual(len(result.errors), 0)
    
    @patch('email_validation.get_db_connection')
    def test_email_uniqueness_check_existing_email(self, mock_connection):
        """Test email uniqueness check for existing email"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 'active', datetime(2024, 1, 1))  # Existing user
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.validator.check_email_uniqueness("existing@example.com")
        
        self.assertFalse(result.is_valid)
        self.assertFalse(result.validation_details['is_unique'])
        self.assertIn("already exists", result.errors[0])
    
    @patch('email_validation.get_db_connection')
    def test_email_uniqueness_check_pending_verification(self, mock_connection):
        """Test email uniqueness check for pending verification account"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 'pending_verification', datetime(2024, 1, 1))
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.validator.check_email_uniqueness("pending@example.com")
        
        self.assertFalse(result.is_valid)
        self.assertIn("pending verification", result.errors[0])
    
    @patch('email_validation.get_db_connection')
    def test_email_uniqueness_check_suspended_account(self, mock_connection):
        """Test email uniqueness check for suspended account"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 'suspended', datetime(2024, 1, 1))
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.validator.check_email_uniqueness("suspended@example.com")
        
        self.assertFalse(result.is_valid)
        self.assertIn("suspended", result.errors[0])
    
    @patch('email_validation.get_db_connection')
    def test_email_uniqueness_check_with_exclusion(self, mock_connection):
        """Test email uniqueness check excluding current user"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # No other user with this email
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.validator.check_email_uniqueness("user@example.com", exclude_user_id=1)
        
        self.assertTrue(result.is_valid)
        self.assertTrue(result.validation_details['is_unique'])
    
    def test_comprehensive_registration_validation(self):
        """Test comprehensive email validation for registration"""
        # Test with valid email (format only, uniqueness mocked)
        with patch.object(self.validator, 'check_email_uniqueness') as mock_uniqueness:
            mock_uniqueness.return_value = EmailValidationResult(
                is_valid=True,
                errors=[],
                suggestions=[],
                validation_details={'is_unique': True}
            )
            
            result = self.validator.validate_email_for_registration("user@example.com")
            self.assertTrue(result.is_valid)
    
    def test_comprehensive_registration_validation_with_errors(self):
        """Test comprehensive email validation with format errors"""
        result = self.validator.validate_email_for_registration("invalid-email")
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.errors), 0)
    
    def test_email_suggestions(self):
        """Test email correction suggestions"""
        suggestions = self.validator.get_email_suggestions("user@gamil.com")
        self.assertIn("user@gmail.com", suggestions)
        
        suggestions = self.validator.get_email_suggestions("user@hotmai.com")
        self.assertIn("user@hotmail.com", suggestions)
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly"""
        # Test validate_email_format convenience function
        result = validate_email_format("user@example.com")
        self.assertTrue(result.is_valid)
        
        # Test get_email_suggestions convenience function
        suggestions = get_email_suggestions("user@gamil.com")
        self.assertIn("user@gmail.com", suggestions)
    
    def test_email_validation_result_dataclass(self):
        """Test EmailValidationResult dataclass"""
        result = EmailValidationResult(
            is_valid=True,
            errors=[],
            suggestions=["Try this instead"],
            validation_details={'test': 'value'}
        )
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(len(result.suggestions), 1)
        self.assertEqual(result.validation_details['test'], 'value')


class TestEmailValidationIntegration(unittest.TestCase):
    """Integration tests for email validation with database"""
    
    @patch('email_validation.USE_POSTGRES', True)
    @patch('email_validation.get_db_connection')
    def test_postgres_uniqueness_query(self, mock_connection):
        """Test PostgreSQL uniqueness query format"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        validator = EmailValidator()
        result = validator.check_email_uniqueness("test@example.com")
        
        # Verify PostgreSQL query was used
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn("LOWER(email) = LOWER(%s)", call_args[0])
    
    @patch('email_validation.USE_POSTGRES', False)
    @patch('email_validation.get_db_connection')
    def test_sqlite_uniqueness_query(self, mock_connection):
        """Test SQLite uniqueness query format"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        validator = EmailValidator()
        result = validator.check_email_uniqueness("test@example.com")
        
        # Verify SQLite query was used
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn("LOWER(email) = LOWER(?)", call_args[0])


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
