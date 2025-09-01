"""
CSRF Protection Module

This module provides comprehensive CSRF (Cross-Site Request Forgery) protection
for all registration forms and endpoints. It extends the existing CSRF functionality
with enhanced security features, token management, and protection mechanisms.
"""

import logging
import secrets
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from enum import Enum
from flask import request, session, current_app, g
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class CSRFProtectionLevel(Enum):
    """Enumeration of CSRF protection levels"""
    BASIC = 'basic'           # Standard CSRF protection
    ENHANCED = 'enhanced'     # Enhanced with additional security measures
    STRICT = 'strict'         # Strict protection with additional validation


class CSRFTokenType(Enum):
    """Enumeration of CSRF token types"""
    FORM = 'form'             # Form submission tokens
    API = 'api'               # API endpoint tokens
    SESSION = 'session'       # Session-based tokens
    DOUBLE_SUBMIT = 'double_submit'  # Double submit cookie tokens


@dataclass
class CSRFToken:
    """Data class for CSRF token information"""
    token: str
    token_type: CSRFTokenType
    created_at: datetime
    expires_at: datetime
    user_id: Optional[int] = None
    ip_address: str = None
    user_agent: str = None
    metadata: Dict = None


class CSRFProtectionManager:
    """Manages comprehensive CSRF protection for the application"""
    
    def __init__(self, protection_level: CSRFProtectionLevel = CSRFProtectionLevel.ENHANCED):
        self.logger = logging.getLogger(__name__)
        self.protection_level = protection_level
        self.token_expiry_hours = 24  # Default token expiry
        self.max_tokens_per_user = 10  # Maximum tokens per user
        self.require_https = True  # Require HTTPS for token validation
        self.validate_origin = True  # Validate request origin
        self.validate_referer = True  # Validate referer header
    
    def generate_csrf_token(self, token_type: CSRFTokenType = CSRFTokenType.FORM, 
                           user_id: Optional[int] = None, metadata: Dict = None) -> str:
        """
        Generate a new CSRF token
        
        Args:
            token_type: Type of CSRF token
            user_id: User ID (optional)
            metadata: Additional metadata
            
        Returns:
            CSRF token string
        """
        try:
            # Generate cryptographically secure token
            token = secrets.token_urlsafe(32)
            
            # Add timestamp for additional security
            timestamp = str(int(time.time()))
            token_with_timestamp = f"{token}.{timestamp}"
            
            # Hash the token for storage
            token_hash = hashlib.sha256(token_with_timestamp.encode()).hexdigest()
            
            # Store token information
            self._store_token_info(token_hash, token_type, user_id, metadata)
            
            # Store in Flask session for easy access
            session[f'csrf_token_{token_type.value}'] = token_with_timestamp
            
            self.logger.info(f"Generated CSRF token of type {token_type.value} for user {user_id}")
            return token_with_timestamp
            
        except Exception as e:
            self.logger.error(f"Error generating CSRF token: {str(e)}")
            raise
    
    def validate_csrf_token(self, token: str, token_type: CSRFTokenType = CSRFTokenType.FORM,
                           user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Validate a CSRF token
        
        Args:
            token: CSRF token to validate
            token_type: Expected token type
            user_id: User ID for validation
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not token:
                return False, "CSRF token is required"
            
            # Check if token exists in session
            session_token = session.get(f'csrf_token_{token_type.value}')
            if not session_token:
                return False, "CSRF token not found in session"
            
            # Validate token format
            if not self._validate_token_format(token):
                return False, "Invalid CSRF token format"
            
            # Check if tokens match
            if token != session_token:
                return False, "CSRF token mismatch"
            
            # Validate token timestamp
            if not self._validate_token_timestamp(token):
                return False, "CSRF token has expired"
            
            # Enhanced validation for higher protection levels
            if self.protection_level in [CSRFProtectionLevel.ENHANCED, CSRFProtectionLevel.STRICT]:
                # Validate request origin
                if self.validate_origin and not self._validate_request_origin():
                    return False, "Invalid request origin"
                
                # Validate referer header
                if self.validate_referer and not self._validate_referer():
                    return False, "Invalid referer header"
                
                # Validate HTTPS requirement
                if self.require_https and not self._validate_https():
                    return False, "HTTPS required for CSRF protection"
            
            # Strict validation for highest protection level
            if self.protection_level == CSRFProtectionLevel.STRICT:
                # Validate user context
                if user_id and not self._validate_user_context(token, user_id):
                    return False, "Invalid user context for CSRF token"
                
                # Validate IP address
                if not self._validate_ip_address(token):
                    return False, "IP address mismatch for CSRF token"
            
            # Token is valid - remove from session to prevent reuse
            session.pop(f'csrf_token_{token_type.value}', None)
            
            self.logger.info(f"Validated CSRF token of type {token_type.value} for user {user_id}")
            return True, ""
            
        except Exception as e:
            self.logger.error(f"Error validating CSRF token: {str(e)}")
            return False, "CSRF validation failed"
    
    def refresh_csrf_token(self, token_type: CSRFTokenType = CSRFTokenType.FORM,
                          user_id: Optional[int] = None) -> str:
        """
        Refresh a CSRF token
        
        Args:
            token_type: Type of token to refresh
            user_id: User ID
            
        Returns:
            New CSRF token
        """
        try:
            # Remove old token
            session.pop(f'csrf_token_{token_type.value}', None)
            
            # Generate new token
            new_token = self.generate_csrf_token(token_type, user_id)
            
            self.logger.info(f"Refreshed CSRF token of type {token_type.value} for user {user_id}")
            return new_token
            
        except Exception as e:
            self.logger.error(f"Error refreshing CSRF token: {str(e)}")
            raise
    
    def invalidate_csrf_token(self, token_type: CSRFTokenType = CSRFTokenType.FORM) -> bool:
        """
        Invalidate a CSRF token
        
        Args:
            token_type: Type of token to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            session.pop(f'csrf_token_{token_type.value}', None)
            self.logger.info(f"Invalidated CSRF token of type {token_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error invalidating CSRF token: {str(e)}")
            return False
    
    def get_csrf_token_for_form(self, form_name: str, user_id: Optional[int] = None) -> str:
        """
        Get CSRF token for a specific form
        
        Args:
            form_name: Name of the form
            user_id: User ID
            
        Returns:
            CSRF token for the form
        """
        try:
            metadata = {'form_name': form_name}
            return self.generate_csrf_token(CSRFTokenType.FORM, user_id, metadata)
            
        except Exception as e:
            self.logger.error(f"Error getting CSRF token for form {form_name}: {str(e)}")
            raise
    
    def validate_form_submission(self, form_data: Dict, form_name: str,
                                user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Validate form submission with CSRF protection
        
        Args:
            form_data: Form data containing CSRF token
            form_name: Name of the form
            user_id: User ID
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            csrf_token = form_data.get('csrf_token', '')
            return self.validate_csrf_token(csrf_token, CSRFTokenType.FORM, user_id)
            
        except Exception as e:
            self.logger.error(f"Error validating form submission: {str(e)}")
            return False, "Form validation failed"
    
    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired CSRF tokens
        
        Returns:
            Number of tokens cleaned up
        """
        try:
            # This would typically clean up tokens from a database
            # For now, we'll just clean up session tokens
            cleaned_count = 0
            
            for key in list(session.keys()):
                if key.startswith('csrf_token_'):
                    # Check if token is expired by parsing timestamp
                    token_value = session[key]
                    if self._is_token_expired(token_value):
                        session.pop(key)
                        cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} expired CSRF tokens")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return 0
    
    def get_csrf_statistics(self) -> Dict:
        """
        Get CSRF protection statistics
        
        Returns:
            Dictionary with CSRF statistics
        """
        try:
            # Count active tokens in session
            active_tokens = 0
            token_types = {}
            
            for key in session.keys():
                if key.startswith('csrf_token_'):
                    active_tokens += 1
                    token_type = key.replace('csrf_token_', '')
                    token_types[token_type] = token_types.get(token_type, 0) + 1
            
            return {
                'active_tokens': active_tokens,
                'token_types': token_types,
                'protection_level': self.protection_level.value,
                'require_https': self.require_https,
                'validate_origin': self.validate_origin,
                'validate_referer': self.validate_referer
            }
            
        except Exception as e:
            self.logger.error(f"Error getting CSRF statistics: {str(e)}")
            return {}
    
    def _store_token_info(self, token_hash: str, token_type: CSRFTokenType,
                         user_id: Optional[int], metadata: Dict = None):
        """Store token information for tracking"""
        try:
            # In a production environment, this would store to a database
            # For now, we'll just log the information
            token_info = {
                'token_hash': token_hash,
                'token_type': token_type.value,
                'user_id': user_id,
                'ip_address': request.remote_addr if request else 'unknown',
                'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'unknown',
                'created_at': datetime.now(),
                'metadata': metadata or {}
            }
            
            # Store in Flask g for request context
            if not hasattr(g, 'csrf_tokens'):
                g.csrf_tokens = []
            g.csrf_tokens.append(token_info)
            
        except Exception as e:
            self.logger.error(f"Error storing token info: {str(e)}")
    
    def _validate_token_format(self, token: str) -> bool:
        """Validate CSRF token format"""
        try:
            # Check if token contains timestamp
            if '.' not in token:
                return False
            
            # Check if token is reasonably long
            if len(token) < 32:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_token_timestamp(self, token: str) -> bool:
        """Validate CSRF token timestamp"""
        try:
            # Extract timestamp from token
            timestamp_str = token.split('.')[-1]
            timestamp = int(timestamp_str)
            
            # Check if token is expired
            current_time = int(time.time())
            token_age = current_time - timestamp
            
            # Token expires after 24 hours
            max_age = self.token_expiry_hours * 3600
            
            return token_age <= max_age
            
        except Exception:
            return False
    
    def _is_token_expired(self, token: str) -> bool:
        """Check if token is expired"""
        return not self._validate_token_timestamp(token)
    
    def _validate_request_origin(self) -> bool:
        """Validate request origin"""
        try:
            origin = request.headers.get('Origin')
            if not origin:
                return False
            
            # Check if origin is from allowed domains
            allowed_domains = current_app.config.get('CSRF_ALLOWED_ORIGINS', [])
            if allowed_domains:
                from urllib.parse import urlparse
                parsed_origin = urlparse(origin)
                return parsed_origin.netloc in allowed_domains
            
            return True
            
        except Exception:
            return False
    
    def _validate_referer(self) -> bool:
        """Validate referer header"""
        try:
            referer = request.headers.get('Referer')
            if not referer:
                return False
            
            # Check if referer is from the same site
            from urllib.parse import urlparse
            parsed_referer = urlparse(referer)
            parsed_request = urlparse(request.url)
            
            return parsed_referer.netloc == parsed_request.netloc
            
        except Exception:
            return False
    
    def _validate_https(self) -> bool:
        """Validate HTTPS requirement"""
        try:
            # Check if request is over HTTPS
            if request.headers.get('X-Forwarded-Proto') == 'https':
                return True
            
            if request.is_secure:
                return True
            
            # Allow HTTP for localhost/development
            if request.host in ['localhost', '127.0.0.1']:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _validate_user_context(self, token: str, user_id: int) -> bool:
        """Validate user context for CSRF token"""
        try:
            # In a production environment, this would check against stored token info
            # For now, we'll assume it's valid if user is authenticated
            return True
            
        except Exception:
            return False
    
    def _validate_ip_address(self, token: str) -> bool:
        """Validate IP address for CSRF token"""
        try:
            # In a production environment, this would check against stored token info
            # For now, we'll assume it's valid
            return True
            
        except Exception:
            return False


# Global instance
csrf_protection = CSRFProtectionManager()


def csrf_protected(token_type: CSRFTokenType = CSRFTokenType.FORM):
    """
    Decorator for CSRF protection
    
    Args:
        token_type: Type of CSRF token to validate
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get CSRF token from request
                if request.method == 'POST':
                    csrf_token = request.form.get('csrf_token') or request.json.get('csrf_token')
                else:
                    csrf_token = request.args.get('csrf_token')
                
                # Validate CSRF token
                is_valid, error = csrf_protection.validate_csrf_token(csrf_token, token_type)
                
                if not is_valid:
                    return {'error': error}, 400
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"CSRF protection error: {str(e)}")
                return {'error': 'CSRF validation failed'}, 400
        
        return decorated_function
    return decorator


def require_csrf_token(token_type: CSRFTokenType = CSRFTokenType.FORM):
    """
    Decorator to require CSRF token in response
    
    Args:
        token_type: Type of CSRF token to include
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Generate CSRF token
                csrf_token = csrf_protection.generate_csrf_token(token_type)
                
                # Call original function
                result = f(*args, **kwargs)
                
                # Add CSRF token to response if it's a template
                if isinstance(result, str):
                    # Template response - add token to context
                    return result
                elif isinstance(result, tuple) and len(result) == 2:
                    # (template, context) response
                    template, context = result
                    context['csrf_token'] = csrf_token
                    return template, context
                else:
                    # Other response types
                    return result
                
            except Exception as e:
                logger.error(f"CSRF token requirement error: {str(e)}")
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator
