"""
User Registration Validation Module

This module handles all validation logic for user registration, including:
- Email format and uniqueness validation
- Password strength validation
- Legal document acceptance validation
- CSRF protection
- Rate limiting for registration attempts
"""

import re
import logging
import hashlib
import time
import secrets
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from flask import request, session
from werkzeug.security import generate_password_hash

# Import existing modules
from legal_validation import LegalDocumentValidator
from legal_compliance import get_legal_compliance_tracker
from legal_document_versioning import get_current_legal_versions
from db_utils import execute_query
from email_validation import validate_email_for_registration

logger = logging.getLogger(__name__)

class RegistrationValidator:
    """Handles all validation for user registration"""
    
    def __init__(self):
        self.legal_validator = LegalDocumentValidator()
        self.compliance_tracker = get_legal_compliance_tracker()
        self.registration_attempts = {}  # Simple in-memory rate limiting
        
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """
        Validate email format and uniqueness using comprehensive email validation
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email address is required"
        
        # Use comprehensive email validation
        validation_result = validate_email_for_registration(email)
        
        if not validation_result.is_valid:
            # Return the first error message
            return False, validation_result.errors[0] if validation_result.errors else "Invalid email address"
        
        return True, ""
    
    def validate_password(self, password: str) -> Tuple[bool, List[str]]:
        """
        Validate password strength
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not password:
            errors.append("Password is required")
            return False, errors
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        # Character type checks
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for common weak passwords (only if password meets other requirements)
        if len(password) >= 8:
            weak_passwords = {
                'password', '123456', 'password123', 'qwerty', 'abc123',
                'password1', 'admin', 'letmein', 'welcome', 'monkey'
            }
            if password.lower() in weak_passwords:
                errors.append("Password is too common. Please choose a stronger password")
        
        # Check for sequential characters
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password contains too many repeated characters")
        
        return len(errors) == 0, errors
    
    def validate_password_confirmation(self, password: str, confirm_password: str) -> Tuple[bool, str]:
        """
        Validate password confirmation
        
        Args:
            password: Original password
            confirm_password: Confirmation password
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not confirm_password:
            return False, "Please confirm your password"
        
        if password != confirm_password:
            return False, "Passwords do not match"
        
        return True, ""
    
    def validate_legal_acceptance(self, terms_accepted: bool, privacy_accepted: bool, 
                                disclaimer_accepted: bool) -> Tuple[bool, List[str]]:
        """
        Validate legal document acceptance
        
        Args:
            terms_accepted: Whether terms were accepted
            privacy_accepted: Whether privacy policy was accepted
            disclaimer_accepted: Whether disclaimer was accepted
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        current_versions = get_current_legal_versions()
        
        # Check if all required documents are accepted
        if not terms_accepted:
            errors.append("You must accept the Terms and Conditions")
        
        if not privacy_accepted:
            errors.append("You must accept the Privacy Policy")
        
        if not disclaimer_accepted:
            errors.append("You must accept the Medical Disclaimer")
        
        # Validate against current versions
        required_documents = {
            'terms': terms_accepted,
            'privacy': privacy_accepted,
            'disclaimer': disclaimer_accepted
        }
        
        for doc_type, accepted in required_documents.items():
            if accepted:
                current_version = current_versions.get(doc_type)
                if not current_version:
                    errors.append(f"Unable to verify {doc_type} version")
        
        return len(errors) == 0, errors
    
    def validate_csrf_token(self, csrf_token: str) -> Tuple[bool, str]:
        """
        Validate CSRF token using enhanced CSRF protection
        
        Args:
            csrf_token: CSRF token from form
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            from csrf_protection import csrf_protection, CSRFTokenType
            return csrf_protection.validate_csrf_token(csrf_token, CSRFTokenType.FORM)
        except ImportError:
            # Fallback to basic validation if enhanced module not available
            if not csrf_token:
                return False, "Security token is missing"
            
            # Check if token exists in session
            session_token = session.get('csrf_token')
            if not session_token:
                return False, "Security token expired. Please refresh the page"
            
            if csrf_token != session_token:
                return False, "Invalid security token"
            
            return True, ""
    
    def check_rate_limit(self, ip_address: str) -> Tuple[bool, str]:
        """
        Check rate limiting for registration attempts
        
        Args:
            ip_address: IP address of the request
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        current_time = time.time()
        window_size = 3600  # 1 hour window
        max_attempts = 5  # Maximum attempts per hour
        
        # Clean old attempts
        self.registration_attempts = {
            ip: attempts for ip, attempts in self.registration_attempts.items()
            if current_time - attempts['first_attempt'] < window_size
        }
        
        if ip_address not in self.registration_attempts:
            self.registration_attempts[ip_address] = {
                'count': 1,
                'first_attempt': current_time,
                'last_attempt': current_time
            }
            return True, ""
        
        attempts = self.registration_attempts[ip_address]
        
        # Check if within time window
        if current_time - attempts['first_attempt'] > window_size:
            # Reset for new window
            attempts['count'] = 1
            attempts['first_attempt'] = current_time
            attempts['last_attempt'] = current_time
            return True, ""
        
        # Check attempt count
        if attempts['count'] >= max_attempts:
            remaining_time = int(window_size - (current_time - attempts['first_attempt']))
            return False, f"Too many registration attempts. Please try again in {remaining_time // 60} minutes"
        
        # Increment attempt count
        attempts['count'] += 1
        attempts['last_attempt'] = current_time
        
        return True, ""
    
    def generate_csrf_token(self) -> str:
        """
        Generate a new CSRF token using enhanced CSRF protection
        
        Returns:
            CSRF token string
        """
        try:
            from csrf_protection import csrf_protection, CSRFTokenType
            return csrf_protection.generate_csrf_token(CSRFTokenType.FORM)
        except ImportError:
            # Fallback to basic token generation if enhanced module not available
            token = hashlib.sha256(f"{time.time()}{secrets.token_hex(16)}".encode()).hexdigest()
            session['csrf_token'] = token
            return token
    
    def validate_registration_data(self, form_data: Dict) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Comprehensive validation of registration form data
        
        Args:
            form_data: Dictionary containing form data
            
        Returns:
            Tuple of (is_valid, dict_of_field_errors)
        """
        errors = {}
        
        # Get form data
        email = form_data.get('email', '').strip()
        password = form_data.get('password', '')
        confirm_password = form_data.get('confirm_password', '')
        terms_accepted = form_data.get('terms_accepted') == 'on'
        privacy_accepted = form_data.get('privacy_accepted') == 'on'
        disclaimer_accepted = form_data.get('disclaimer_accepted') == 'on'
        csrf_token = form_data.get('csrf_token', '')
        
        # Rate limiting check
        ip_address = request.remote_addr
        rate_ok, rate_error = self.check_rate_limit(ip_address)
        if not rate_ok:
            errors['general'] = [rate_error]
            return False, errors
        
        # Email validation
        email_ok, email_error = self.validate_email(email)
        if not email_ok:
            errors['email'] = [email_error]
        
        # Password validation
        password_ok, password_errors = self.validate_password(password)
        if not password_ok:
            errors['password'] = password_errors
        
        # Password confirmation validation
        confirm_ok, confirm_error = self.validate_password_confirmation(password, confirm_password)
        if not confirm_ok:
            errors['confirm_password'] = [confirm_error]
        
        # Legal acceptance validation
        legal_ok, legal_errors = self.validate_legal_acceptance(
            terms_accepted, privacy_accepted, disclaimer_accepted
        )
        if not legal_ok:
            errors['legal'] = legal_errors
        
        # CSRF validation
        csrf_ok, csrf_error = self.validate_csrf_token(csrf_token)
        if not csrf_ok:
            errors['csrf'] = [csrf_error]
        
        return len(errors) == 0, errors
    
    def create_user_account(self, email: str, password: str) -> Tuple[bool, Optional[int], str]:
        """
        Create a new user account using the user account manager
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Tuple of (success, user_id, error_message)
        """
        try:
            from user_account_manager import user_account_manager
            
            # Prepare legal acceptances (assuming all were accepted during validation)
            legal_acceptances = {
                'terms': True,
                'privacy': True,
                'disclaimer': True
            }
            
            # Use the user account manager to create the account
            success, user_id, error_message = user_account_manager.create_new_user_account(
                email, password, legal_acceptances
            )
            
            return success, user_id, error_message
                
        except Exception as e:
            logger.error(f"Error creating user account: {str(e)}")
            return False, None, "Unable to create account. Please try again."


# Global instance
registration_validator = RegistrationValidator()
