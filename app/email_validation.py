"""
Email Validation Module

This module provides comprehensive email validation functionality for user registration,
including format validation, uniqueness checking, and integration with the registration system.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from db_utils import get_db_connection, execute_query

logger = logging.getLogger(__name__)


@dataclass
class EmailValidationResult:
    """Result of email validation"""
    is_valid: bool
    errors: List[str]
    suggestions: List[str]
    validation_details: Dict


class EmailValidator:
    """
    Comprehensive email validation with format checking, uniqueness validation,
    and integration with registration system.
    """
    
    def __init__(self):
        """Initialize the email validator with validation patterns"""
        # RFC 5322 compliant email regex pattern
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        )
        
        # Common disposable email domains
        self.disposable_domains = {
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com', 'tempmail.org',
            'throwaway.email', 'yopmail.com', 'getnada.com', 'sharklasers.com',
            'mailnesia.com', 'maildrop.cc', 'mailinator.net', 'guerrillamailblock.com'
        }
        
        # Common typos and corrections
        self.common_typos = {
            'gamil.com': 'gmail.com',
            'gmial.com': 'gmail.com',
            'gmal.com': 'gmail.com',
            'gmai.com': 'gmail.com',
            'gmeil.com': 'gmail.com',
            'hotmai.com': 'hotmail.com',
            'hotmial.com': 'hotmail.com',
            'hotmal.com': 'hotmail.com',
            'hotmeil.com': 'hotmail.com',
            'yahooo.com': 'yahoo.com',
            'yaho.com': 'yahoo.com',
            'yhaoo.com': 'yahoo.com'
        }
    
    def validate_email_format(self, email: str) -> EmailValidationResult:
        """
        Validate email format using RFC 5322 compliant regex
        
        Args:
            email: Email address to validate
            
        Returns:
            EmailValidationResult with validation details
        """
        errors = []
        suggestions = []
        validation_details = {
            'format_valid': False,
            'length_valid': False,
            'domain_valid': False,
            'local_part_valid': False,
            'has_common_typo': False,
            'suggested_correction': None
        }
        
        if not email:
            errors.append("Email address is required")
            return EmailValidationResult(False, errors, suggestions, validation_details)
        
        email = email.strip().lower()
        
        # Check length
        if len(email) > 254:  # RFC 5321 limit
            errors.append("Email address is too long (maximum 254 characters)")
        elif len(email) < 5:
            errors.append("Email address is too short")
        else:
            validation_details['length_valid'] = True
        
        # Check format
        if not self.email_pattern.match(email):
            errors.append("Invalid email format")
        else:
            validation_details['format_valid'] = True
            
            # Parse email parts
            try:
                local_part, domain = email.split('@', 1)
                
                # Validate local part
                if len(local_part) > 64:  # RFC 5321 limit
                    errors.append("Local part of email is too long (maximum 64 characters)")
                elif len(local_part) == 0:
                    errors.append("Local part of email cannot be empty")
                else:
                    validation_details['local_part_valid'] = True
                
                # Validate domain
                if len(domain) > 253:  # RFC 5321 limit
                    errors.append("Domain part of email is too long (maximum 253 characters)")
                elif len(domain) == 0:
                    errors.append("Domain part of email cannot be empty")
                elif '.' not in domain:
                    errors.append("Domain must contain at least one dot")
                else:
                    validation_details['domain_valid'] = True
                
                # Check for common typos
                if domain in self.common_typos:
                    validation_details['has_common_typo'] = True
                    suggested_domain = self.common_typos[domain]
                    suggested_correction = f"{local_part}@{suggested_domain}"
                    validation_details['suggested_correction'] = suggested_correction
                    suggestions.append(f"Did you mean {suggested_correction}?")
                
            except ValueError:
                errors.append("Email must contain exactly one @ symbol")
        
        # Check for disposable email domains
        if validation_details.get('domain_valid') and domain in self.disposable_domains:
            errors.append("Disposable email addresses are not allowed")
        
        is_valid = len(errors) == 0
        
        return EmailValidationResult(is_valid, errors, suggestions, validation_details)
    
    def check_email_uniqueness(self, email: str, exclude_user_id: Optional[int] = None) -> EmailValidationResult:
        """
        Check if email is unique in the system
        
        Args:
            email: Email address to check
            exclude_user_id: User ID to exclude from uniqueness check (for updates)
            
        Returns:
            EmailValidationResult with uniqueness validation
        """
        errors = []
        suggestions = []
        validation_details = {
            'is_unique': False,
            'existing_user_id': None,
            'existing_user_status': None,
            'last_used': None
        }
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    if exclude_user_id:
                        query = """
                        SELECT id, account_status, created_at 
                        FROM users 
                        WHERE LOWER(email) = LOWER(%s) AND id != %s
                        """
                        cursor.execute(query, (email, exclude_user_id))
                    else:
                        query = """
                        SELECT id, account_status, created_at 
                        FROM users 
                        WHERE LOWER(email) = LOWER(%s)
                        """
                        cursor.execute(query, (email,))
                else:
                    if exclude_user_id:
                        query = """
                        SELECT id, account_status, created_at 
                        FROM users 
                        WHERE LOWER(email) = LOWER(?) AND id != ?
                        """
                        cursor.execute(query, (email, exclude_user_id))
                    else:
                        query = """
                        SELECT id, account_status, created_at 
                        FROM users 
                        WHERE LOWER(email) = LOWER(?)
                        """
                        cursor.execute(query, (email,))
                
                result = cursor.fetchone()
                
                if result:
                    user_id, account_status, created_at = result
                    validation_details.update({
                        'is_unique': False,
                        'existing_user_id': user_id,
                        'existing_user_status': account_status,
                        'last_used': created_at.isoformat() if created_at else None
                    })
                    
                    if account_status == 'active':
                        errors.append("An account with this email address already exists")
                        suggestions.append("Try logging in instead, or use a different email address")
                    elif account_status == 'pending_verification':
                        errors.append("An account with this email is pending verification")
                        suggestions.append("Check your email for verification instructions, or use a different email address")
                    elif account_status == 'suspended':
                        errors.append("An account with this email has been suspended")
                        suggestions.append("Contact support for assistance, or use a different email address")
                    else:
                        errors.append("An account with this email address already exists")
                        suggestions.append("Try logging in instead, or use a different email address")
                else:
                    validation_details['is_unique'] = True
                    
        except Exception as e:
            logger.error(f"Error checking email uniqueness: {str(e)}")
            errors.append("Unable to verify email uniqueness. Please try again.")
        
        is_valid = len(errors) == 0
        
        return EmailValidationResult(is_valid, errors, suggestions, validation_details)
    
    def validate_email_for_registration(self, email: str) -> EmailValidationResult:
        """
        Comprehensive email validation for user registration
        
        Args:
            email: Email address to validate
            
        Returns:
            EmailValidationResult with all validation details
        """
        # First validate format
        format_result = self.validate_email_format(email)
        
        if not format_result.is_valid:
            return format_result
        
        # Then check uniqueness
        uniqueness_result = self.check_email_uniqueness(email)
        
        # Combine results
        combined_errors = format_result.errors + uniqueness_result.errors
        combined_suggestions = format_result.suggestions + uniqueness_result.suggestions
        combined_details = {**format_result.validation_details, **uniqueness_result.validation_details}
        
        is_valid = len(combined_errors) == 0
        
        return EmailValidationResult(is_valid, combined_errors, combined_suggestions, combined_details)
    
    def validate_email_for_update(self, email: str, user_id: int) -> EmailValidationResult:
        """
        Validate email for user profile updates (excludes current user from uniqueness check)
        
        Args:
            email: Email address to validate
            user_id: Current user ID to exclude from uniqueness check
            
        Returns:
            EmailValidationResult with validation details
        """
        # First validate format
        format_result = self.validate_email_format(email)
        
        if not format_result.is_valid:
            return format_result
        
        # Then check uniqueness (excluding current user)
        uniqueness_result = self.check_email_uniqueness(email, exclude_user_id=user_id)
        
        # Combine results
        combined_errors = format_result.errors + uniqueness_result.errors
        combined_suggestions = format_result.suggestions + uniqueness_result.suggestions
        combined_details = {**format_result.validation_details, **uniqueness_result.validation_details}
        
        is_valid = len(combined_errors) == 0
        
        return EmailValidationResult(is_valid, combined_errors, combined_suggestions, combined_details)
    
    def get_email_suggestions(self, email: str) -> List[str]:
        """
        Get suggestions for email corrections
        
        Args:
            email: Email address to get suggestions for
            
        Returns:
            List of suggested corrections
        """
        suggestions = []
        
        if not email or '@' not in email:
            return suggestions
        
        try:
            local_part, domain = email.lower().split('@', 1)
            
            # Check for common typos
            if domain in self.common_typos:
                suggested_domain = self.common_typos[domain]
                suggestions.append(f"{local_part}@{suggested_domain}")
            
            # Check for common domain variations
            if domain.endswith('.com'):
                base_domain = domain[:-4]
                if base_domain in ['gmail', 'hotmail', 'yahoo', 'outlook']:
                    suggestions.append(f"{local_part}@{base_domain}.com")
            
        except ValueError:
            pass
        
        return suggestions


# Global instance for easy access
email_validator = EmailValidator()


def validate_email_format(email: str) -> EmailValidationResult:
    """
    Convenience function to validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        EmailValidationResult
    """
    return email_validator.validate_email_format(email)


def check_email_uniqueness(email: str, exclude_user_id: Optional[int] = None) -> EmailValidationResult:
    """
    Convenience function to check email uniqueness
    
    Args:
        email: Email address to check
        exclude_user_id: User ID to exclude from check
        
    Returns:
        EmailValidationResult
    """
    return email_validator.check_email_uniqueness(email, exclude_user_id)


def validate_email_for_registration(email: str) -> EmailValidationResult:
    """
    Convenience function for comprehensive email validation
    
    Args:
        email: Email address to validate
        
    Returns:
        EmailValidationResult
    """
    return email_validator.validate_email_for_registration(email)


def validate_email_for_update(email: str, user_id: int) -> EmailValidationResult:
    """
    Convenience function for email validation during updates
    
    Args:
        email: Email address to validate
        user_id: Current user ID
        
    Returns:
        EmailValidationResult
    """
    return email_validator.validate_email_for_update(email, user_id)


def get_email_suggestions(email: str) -> List[str]:
    """
    Convenience function to get email suggestions
    
    Args:
        email: Email address to get suggestions for
        
    Returns:
        List of suggestions
    """
    return email_validator.get_email_suggestions(email)


if __name__ == "__main__":
    # Test the email validation system
    print("Email Validation System Test")
    print("=" * 50)
    
    test_emails = [
        "user@example.com",
        "invalid-email",
        "user@",
        "@example.com",
        "user@disposable.com",
        "user@gamil.com",  # Common typo
        "very.long.email.address.that.exceeds.the.maximum.length.allowed.by.rfc.5321@example.com",
        "",
        "user@example.com",  # Duplicate for uniqueness test
    ]
    
    validator = EmailValidator()
    
    for email in test_emails:
        print(f"\nTesting: {email}")
        result = validator.validate_email_for_registration(email)
        print(f"  Valid: {result.is_valid}")
        if result.errors:
            print(f"  Errors: {result.errors}")
        if result.suggestions:
            print(f"  Suggestions: {result.suggestions}")
    
    print("\n" + "=" * 50)
    print("Email validation system ready!")


