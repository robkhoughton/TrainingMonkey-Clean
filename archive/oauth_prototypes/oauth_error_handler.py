#!/usr/bin/env python3
"""
OAuth Error Handler for Training Monkey™ Dashboard
Provides user-friendly error messages and proper error categorization for OAuth operations
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class OAuthErrorHandler:
    """Comprehensive OAuth error handling with user-friendly messages"""
    
    def __init__(self):
        """Initialize the OAuth error handler"""
        self.error_categories = {
            'authentication': {
                'title': 'Authentication Error',
                'description': 'There was a problem with your Strava authentication.',
                'user_message': 'We couldn\'t verify your Strava account. Please try connecting again.',
                'suggestions': [
                    'Make sure you\'re logged into the correct Strava account',
                    'Try disconnecting and reconnecting your Strava account',
                    'Check that your Strava account is active and accessible'
                ],
                'severity': 'high',
                'retryable': False
            },
            'authorization': {
                'title': 'Authorization Error',
                'description': 'Your Strava account doesn\'t have the required permissions.',
                'user_message': 'We need permission to access your Strava data. Please authorize the connection.',
                'suggestions': [
                    'Click "Connect with Strava" to grant the required permissions',
                    'Make sure to check all permission boxes during authorization',
                    'If you previously denied permissions, you may need to revoke and re-authorize'
                ],
                'severity': 'medium',
                'retryable': True
            },
            'network': {
                'title': 'Connection Error',
                'description': 'We couldn\'t connect to Strava due to a network issue.',
                'user_message': 'We\'re having trouble connecting to Strava. Please try again in a moment.',
                'suggestions': [
                    'Check your internet connection',
                    'Try again in a few minutes',
                    'If the problem persists, contact support'
                ],
                'severity': 'low',
                'retryable': True
            },
            'rate_limit': {
                'title': 'Rate Limit Exceeded',
                'description': 'We\'ve made too many requests to Strava. Please wait before trying again.',
                'user_message': 'We\'re temporarily limited in how often we can connect to Strava. Please wait a moment.',
                'suggestions': [
                    'Wait 5-10 minutes before trying again',
                    'Try again during off-peak hours',
                    'Contact support if this happens frequently'
                ],
                'severity': 'medium',
                'retryable': True
            },
            'token_expired': {
                'title': 'Session Expired',
                'description': 'Your Strava connection has expired and needs to be refreshed.',
                'user_message': 'Your Strava connection has expired. We\'ll automatically refresh it for you.',
                'suggestions': [
                    'The system will automatically try to refresh your connection',
                    'If automatic refresh fails, try reconnecting manually',
                    'This is normal and happens periodically for security'
                ],
                'severity': 'low',
                'retryable': True
            },
            'token_invalid': {
                'title': 'Invalid Connection',
                'description': 'Your Strava connection is no longer valid and needs to be re-established.',
                'user_message': 'Your Strava connection needs to be renewed. Please reconnect your account.',
                'suggestions': [
                    'Click "Connect with Strava" to establish a new connection',
                    'This may happen if you changed your Strava password',
                    'Or if you revoked access from your Strava settings'
                ],
                'severity': 'medium',
                'retryable': False
            },
            'server_error': {
                'title': 'Strava Service Error',
                'description': 'Strava is experiencing technical difficulties.',
                'user_message': 'Strava is currently having technical issues. Please try again later.',
                'suggestions': [
                    'Check Strava\'s status page for service updates',
                    'Try again in 15-30 minutes',
                    'Contact support if the problem persists for more than an hour'
                ],
                'severity': 'medium',
                'retryable': True
            },
            'configuration': {
                'title': 'System Configuration Error',
                'description': 'There\'s a problem with our Strava integration setup.',
                'user_message': 'We\'re experiencing a technical issue with our Strava connection. Our team has been notified.',
                'suggestions': [
                    'This is a system issue, not something you can fix',
                    'Our technical team has been automatically notified',
                    'Please try again in 30 minutes or contact support'
                ],
                'severity': 'high',
                'retryable': False
            },
            'user_cancelled': {
                'title': 'Connection Cancelled',
                'description': 'You cancelled the Strava authorization process.',
                'user_message': 'You cancelled the Strava connection. You can try again anytime.',
                'suggestions': [
                    'Click "Connect with Strava" when you\'re ready to try again',
                    'Make sure you have time to complete the authorization process',
                    'The connection is required to sync your training data'
                ],
                'severity': 'low',
                'retryable': True
            },
            'unknown': {
                'title': 'Unexpected Error',
                'description': 'An unexpected error occurred during the Strava connection process.',
                'user_message': 'Something unexpected happened while connecting to Strava. Please try again.',
                'suggestions': [
                    'Try refreshing the page and connecting again',
                    'Clear your browser cache and cookies',
                    'Contact support if the problem continues'
                ],
                'severity': 'medium',
                'retryable': True
            }
        }

    def categorize_error(self, error_message: str, error_code: Optional[str] = None) -> str:
        """Categorize an error based on the error message and code"""
        if not error_message:
            return 'unknown'
        
        error_lower = error_message.lower()
        
        # Check for specific error patterns
        if any(phrase in error_lower for phrase in ['unauthorized', 'invalid token', 'access denied']):
            return 'authentication'
        elif any(phrase in error_lower for phrase in ['forbidden', 'permission denied', 'scope required']):
            return 'authorization'
        elif any(phrase in error_lower for phrase in ['timeout', 'connection', 'network', 'dns']):
            return 'network'
        elif any(phrase in error_lower for phrase in ['rate limit', 'too many requests', 'quota exceeded']):
            return 'rate_limit'
        elif any(phrase in error_lower for phrase in ['token expired', 'expired']):
            return 'token_expired'
        elif any(phrase in error_lower for phrase in ['invalid refresh token', 'invalid client']):
            return 'token_invalid'
        elif any(phrase in error_lower for phrase in ['server error', 'internal error', 'service unavailable']):
            return 'server_error'
        elif any(phrase in error_lower for phrase in ['configuration', 'client_id', 'client_secret']):
            return 'configuration'
        elif any(phrase in error_lower for phrase in ['cancelled', 'denied', 'user cancelled']):
            return 'user_cancelled'
        
        # Check error codes
        if error_code:
            if error_code in ['401', 'unauthorized']:
                return 'authentication'
            elif error_code in ['403', 'forbidden']:
                return 'authorization'
            elif error_code in ['429', 'rate_limit']:
                return 'rate_limit'
            elif error_code in ['500', '502', '503', '504']:
                return 'server_error'
        
        return 'unknown'

    def get_error_info(self, error_message: str, error_code: Optional[str] = None, 
                      context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get comprehensive error information including user-friendly messages"""
        category = self.categorize_error(error_message, error_code)
        error_info = self.error_categories.get(category, self.error_categories['unknown']).copy()
        
        # Add context-specific information
        error_info.update({
            'category': category,
            'original_message': error_message,
            'error_code': error_code,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        })
        
        # Add retry information
        if error_info['retryable']:
            error_info['retry_after'] = self._get_retry_delay(category)
            error_info['max_retries'] = self._get_max_retries(category)
        
        return error_info

    def _get_retry_delay(self, category: str) -> int:
        """Get recommended retry delay in seconds for a given error category"""
        retry_delays = {
            'network': 30,      # 30 seconds
            'rate_limit': 300,  # 5 minutes
            'server_error': 60, # 1 minute
            'token_expired': 10, # 10 seconds
            'authorization': 5,  # 5 seconds
            'unknown': 60       # 1 minute
        }
        return retry_delays.get(category, 60)

    def _get_max_retries(self, category: str) -> int:
        """Get maximum number of retries for a given error category"""
        max_retries = {
            'network': 3,
            'rate_limit': 1,  # Don't retry rate limits immediately
            'server_error': 3,
            'token_expired': 2,
            'authorization': 1,  # Don't retry authorization errors
            'unknown': 2
        }
        return max_retries.get(category, 2)

    def format_user_message(self, error_info: Dict[str, Any], 
                          include_suggestions: bool = True) -> str:
        """Format a user-friendly error message"""
        message = error_info['user_message']
        
        if include_suggestions and error_info.get('suggestions'):
            message += '\n\nWhat you can do:\n'
            for i, suggestion in enumerate(error_info['suggestions'], 1):
                message += f'{i}. {suggestion}\n'
        
        if error_info.get('retry_after'):
            message += f'\n\nPlease wait {error_info["retry_after"]} seconds before trying again.'
        
        return message

    def format_flash_message(self, error_info: Dict[str, Any]) -> Tuple[str, str]:
        """Format error for Flask flash messages"""
        message = error_info['user_message']
        
        # Determine flash category based on severity
        severity = error_info.get('severity', 'medium')
        if severity == 'high':
            flash_category = 'danger'
        elif severity == 'medium':
            flash_category = 'warning'
        else:
            flash_category = 'info'
        
        return message, flash_category

    def format_api_response(self, error_info: Dict[str, Any]) -> Dict[str, Any]:
        """Format error for API responses"""
        return {
            'success': False,
            'error': {
                'category': error_info['category'],
                'title': error_info['title'],
                'message': error_info['user_message'],
                'suggestions': error_info.get('suggestions', []),
                'retryable': error_info['retryable'],
                'retry_after': error_info.get('retry_after'),
                'severity': error_info['severity']
            },
            'timestamp': error_info['timestamp']
        }

    def log_error(self, error_info: Dict[str, Any], user_id: Optional[int] = None,
                 operation: Optional[str] = None) -> None:
        """Log error information for monitoring and debugging"""
        log_data = {
            'user_id': user_id,
            'operation': operation,
            'category': error_info['category'],
            'severity': error_info['severity'],
            'retryable': error_info['retryable'],
            'original_message': error_info['original_message'],
            'error_code': error_info.get('error_code'),
            'context': error_info.get('context', {})
        }
        
        if error_info['severity'] == 'high':
            logger.error(f"OAuth Error: {log_data}")
        elif error_info['severity'] == 'medium':
            logger.warning(f"OAuth Error: {log_data}")
        else:
            logger.info(f"OAuth Error: {log_data}")

    def should_retry(self, error_info: Dict[str, Any], attempt_count: int = 0) -> bool:
        """Determine if an error should be retried"""
        if not error_info['retryable']:
            return False
        
        max_retries = error_info.get('max_retries', 2)
        return attempt_count < max_retries

    def get_retry_delay(self, error_info: Dict[str, Any], attempt_count: int = 0) -> int:
        """Get retry delay with exponential backoff"""
        base_delay = error_info.get('retry_after', 60)
        return base_delay * (2 ** attempt_count)


# Global error handler instance
oauth_error_handler = OAuthErrorHandler()


def handle_oauth_error(error_message: str, error_code: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None,
                      user_id: Optional[int] = None,
                      operation: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to handle OAuth errors"""
    error_info = oauth_error_handler.get_error_info(error_message, error_code, context)
    oauth_error_handler.log_error(error_info, user_id, operation)
    return error_info


def format_oauth_error_response(error_message: str, error_code: Optional[str] = None,
                               context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format OAuth error for API response"""
    error_info = oauth_error_handler.get_error_info(error_message, error_code, context)
    return oauth_error_handler.format_api_response(error_info)


def get_oauth_flash_message(error_message: str, error_code: Optional[str] = None) -> Tuple[str, str]:
    """Get OAuth error formatted for Flask flash messages"""
    error_info = oauth_error_handler.get_error_info(error_message, error_code)
    return oauth_error_handler.format_flash_message(error_info)



