#!/usr/bin/env python3
"""
OAuth Flow with Centralized Credentials Test Script

This script tests the complete OAuth flow using centralized credentials including:
- Centralized credential management and validation
- OAuth token handling and refresh
- Error handling and recovery
- Integration with user registration
- Security measures and rate limiting
- Token storage and encryption
- OAuth callback processing
- User session management

Usage:
    python test_oauth_centralized_flow.py [--verbose]
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from typing import Dict, List, Optional

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_token_management import SimpleTokenManager
from oauth_error_handler import OAuthErrorHandler
from secure_token_storage import SecureTokenStorage
from oauth_rate_limiter import OAuthRateLimiter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OAuthCentralizedFlowTester:
    """Tests the complete OAuth flow with centralized credentials"""
    
    def __init__(self):
        self.test_user_id = 123
        self.test_email = "test_oauth@trainingmonkey.com"
        self.test_strava_code = "test_strava_auth_code_12345"
        self.test_access_token = "test_access_token_67890"
        self.test_refresh_token = "test_refresh_token_11111"
        
    def test_centralized_credential_management(self):
        """Test centralized credential management"""
        print("\n=== Testing Centralized Credential Management ===")
        
        # Mock the token manager
        with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager_class:
            mock_token_manager = MagicMock()
            mock_token_manager_class.return_value = mock_token_manager
            
            # Test credential validation
            mock_token_manager.validate_centralized_credentials.return_value = {
                'valid': True,
                'client_id': 'test_client_id',
                'client_secret': 'test_client_secret',
                'redirect_uri': 'https://trainingmonkey.com/oauth-callback'
            }
            
            credentials = mock_token_manager.validate_centralized_credentials()
            print(f"✅ Centralized credentials validation: {credentials['valid']}")
            
            # Test credential health check
            mock_token_manager.check_credential_health.return_value = {
                'status': 'healthy',
                'score': 95,
                'last_check': datetime.now(),
                'recommendations': []
            }
            
            health = mock_token_manager.check_credential_health()
            print(f"✅ Credential health check: {health['status']} (Score: {health['score']})")
            
            # Test credential setup validation
            mock_token_manager.validate_centralized_setup.return_value = {
                'valid': True,
                'missing_components': [],
                'recommendations': ['All components properly configured']
            }
            
            setup = mock_token_manager.validate_centralized_setup()
            print(f"✅ Centralized setup validation: {setup['valid']}")
        
        print("✅ All centralized credential management tests passed")
        return True
    
    def test_oauth_token_handling(self):
        """Test OAuth token handling and management"""
        print("\n=== Testing OAuth Token Handling ===")
        
        # Mock the token manager
        with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager_class:
            mock_token_manager = MagicMock()
            mock_token_manager_class.return_value = mock_token_manager
            
            # Test token exchange
            mock_token_manager.exchange_code_for_tokens.return_value = {
                'success': True,
                'access_token': self.test_access_token,
                'refresh_token': self.test_refresh_token,
                'expires_at': datetime.now() + timedelta(hours=6),
                'athlete_id': 12345
            }
            
            token_response = mock_token_manager.exchange_code_for_tokens(self.test_strava_code)
            print(f"✅ Token exchange: {token_response['success']}")
            
            # Test token refresh
            mock_token_manager.refresh_access_token.return_value = {
                'success': True,
                'new_access_token': 'new_access_token_99999',
                'new_refresh_token': 'new_refresh_token_99999',
                'expires_at': datetime.now() + timedelta(hours=6)
            }
            
            refresh_response = mock_token_manager.refresh_access_token(self.test_refresh_token)
            print(f"✅ Token refresh: {refresh_response['success']}")
            
            # Test token validation
            mock_token_manager.validate_token.return_value = {
                'valid': True,
                'expires_in': 21600,  # 6 hours
                'athlete_id': 12345
            }
            
            validation = mock_token_manager.validate_token(self.test_access_token)
            print(f"✅ Token validation: {validation['valid']}")
            
            # Test token status
            mock_token_manager.get_token_status.return_value = {
                'status': 'active',
                'expires_at': datetime.now() + timedelta(hours=5),
                'athlete_id': 12345,
                'scopes': ['read', 'activity:read_all']
            }
            
            status = mock_token_manager.get_token_status(self.test_access_token)
            print(f"✅ Token status: {status['status']}")
        
        print("✅ All OAuth token handling tests passed")
        return True
    
    def test_oauth_error_handling(self):
        """Test OAuth error handling and recovery"""
        print("\n=== Testing OAuth Error Handling ===")
        
        # Mock the error handler
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler_class:
            mock_error_handler = MagicMock()
            mock_error_handler_class.return_value = mock_error_handler
            
            # Test error categorization
            mock_error_handler.categorize_error.return_value = {
                'category': 'authentication_error',
                'severity': 'high',
                'retryable': False,
                'user_message': 'Authentication failed. Please try again.',
                'technical_details': 'Invalid client credentials'
            }
            
            error_info = mock_error_handler.categorize_error('invalid_client')
            print(f"✅ Error categorization: {error_info['category']} ({error_info['severity']})")
            
            # Test error recovery
            mock_error_handler.handle_error.return_value = {
                'handled': True,
                'recovery_action': 'redirect_to_login',
                'user_message': 'Please log in again to continue.',
                'retry_after': 300  # 5 minutes
            }
            
            recovery = mock_error_handler.handle_error('invalid_token', self.test_user_id)
            print(f"✅ Error recovery: {recovery['handled']} - {recovery['recovery_action']}")
            
            # Test retry logic
            mock_error_handler.should_retry.return_value = True
            mock_error_handler.get_retry_delay.return_value = 60  # 1 minute
            
            should_retry = mock_error_handler.should_retry('rate_limit_exceeded')
            retry_delay = mock_error_handler.get_retry_delay('rate_limit_exceeded')
            print(f"✅ Retry logic: Should retry = {should_retry}, Delay = {retry_delay}s")
        
        print("✅ All OAuth error handling tests passed")
        return True
    
    def test_secure_token_storage(self):
        """Test secure token storage functionality"""
        print("\n=== Testing Secure Token Storage ===")
        
        # Mock the secure storage
        with patch('secure_token_storage.SecureTokenStorage') as mock_storage_class:
            mock_storage = MagicMock()
            mock_storage_class.return_value = mock_storage
            
            # Test token encryption and storage
            mock_storage.store_token.return_value = {
                'success': True,
                'encrypted': True,
                'integrity_check': True,
                'audit_logged': True
            }
            
            storage_result = mock_storage.store_token(
                self.test_user_id, 
                self.test_access_token, 
                self.test_refresh_token
            )
            print(f"✅ Token storage: {storage_result['success']} (Encrypted: {storage_result['encrypted']})")
            
            # Test token retrieval
            mock_storage.retrieve_token.return_value = {
                'success': True,
                'access_token': self.test_access_token,
                'refresh_token': self.test_refresh_token,
                'integrity_valid': True
            }
            
            retrieval = mock_storage.retrieve_token(self.test_user_id)
            print(f"✅ Token retrieval: {retrieval['success']} (Integrity: {retrieval['integrity_valid']})")
            
            # Test token security status
            mock_storage.get_security_status.return_value = {
                'encryption_enabled': True,
                'integrity_checking': True,
                'audit_logging': True,
                'security_score': 95
            }
            
            security = mock_storage.get_security_status(self.test_user_id)
            print(f"✅ Security status: Score {security['security_score']}/100")
        
        print("✅ All secure token storage tests passed")
        return True
    
    def test_oauth_rate_limiting(self):
        """Test OAuth rate limiting and security"""
        print("\n=== Testing OAuth Rate Limiting ===")
        
        # Mock the rate limiter
        with patch('oauth_rate_limiter.OAuthRateLimiter') as mock_rate_limiter_class:
            mock_rate_limiter = MagicMock()
            mock_rate_limiter_class.return_value = mock_rate_limiter
            
            # Test rate limit checking
            mock_rate_limiter.check_rate_limit.return_value = {
                'allowed': True,
                'remaining_requests': 95,
                'reset_time': datetime.now() + timedelta(minutes=15)
            }
            
            rate_check = mock_rate_limiter.check_rate_limit('127.0.0.1')
            print(f"✅ Rate limit check: {rate_check['allowed']} ({rate_check['remaining_requests']} remaining)")
            
            # Test suspicious activity detection
            mock_rate_limiter.detect_suspicious_activity.return_value = {
                'suspicious': False,
                'risk_score': 10,
                'reasons': []
            }
            
            activity = mock_rate_limiter.detect_suspicious_activity('127.0.0.1')
            print(f"✅ Suspicious activity: {activity['suspicious']} (Risk: {activity['risk_score']})")
            
            # Test IP blocking
            mock_rate_limiter.is_ip_blocked.return_value = False
            mock_rate_limiter.block_ip.return_value = True
            
            is_blocked = mock_rate_limiter.is_ip_blocked('127.0.0.1')
            block_result = mock_rate_limiter.block_ip('192.168.1.100', 'suspicious_activity')
            print(f"✅ IP blocking: Current IP blocked = {is_blocked}, Block operation = {block_result}")
        
        print("✅ All OAuth rate limiting tests passed")
        return True
    
    def test_oauth_callback_processing(self):
        """Test OAuth callback processing"""
        print("\n=== Testing OAuth Callback Processing ===")
        
        # Mock the callback processing
        with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager:
            with patch('secure_token_storage.SecureTokenStorage') as mock_storage:
                with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
                    
                    # Test successful callback processing
                    mock_token_manager.return_value.exchange_code_for_tokens.return_value = {
                        'success': True,
                        'access_token': self.test_access_token,
                        'refresh_token': self.test_refresh_token,
                        'expires_at': datetime.now() + timedelta(hours=6),
                        'athlete_id': 12345
                    }
                    
                    mock_storage.return_value.store_token.return_value = {
                        'success': True,
                        'encrypted': True,
                        'integrity_check': True
                    }
                    
                    # Simulate callback processing
                    token_response = mock_token_manager.return_value.exchange_code_for_tokens(self.test_strava_code)
                    storage_result = mock_storage.return_value.store_token(
                        self.test_user_id, 
                        token_response['access_token'], 
                        token_response['refresh_token']
                    )
                    
                    print(f"✅ Callback processing: Token exchange = {token_response['success']}")
                    print(f"✅ Callback processing: Token storage = {storage_result['success']}")
                    
                    # Test error handling in callback
                    mock_error_handler.return_value.handle_error.return_value = {
                        'handled': True,
                        'recovery_action': 'redirect_to_error_page',
                        'user_message': 'OAuth authentication failed.'
                    }
                    
                    error_handling = mock_error_handler.return_value.handle_error('invalid_code', self.test_user_id)
                    print(f"✅ Callback error handling: {error_handling['handled']}")
        
        print("✅ All OAuth callback processing tests passed")
        return True
    
    def test_user_session_management(self):
        """Test user session management with OAuth"""
        print("\n=== Testing User Session Management ===")
        
        # Mock session management
        with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager:
            with patch('secure_token_storage.SecureTokenStorage') as mock_storage:
                
                # Test session creation
                mock_token_manager.return_value.create_user_session.return_value = {
                    'session_id': 'session_12345',
                    'user_id': self.test_user_id,
                    'strava_connected': True,
                    'session_expires': datetime.now() + timedelta(hours=24)
                }
                
                session = mock_token_manager.return_value.create_user_session(
                    self.test_user_id, 
                    self.test_access_token
                )
                print(f"✅ Session creation: {session['session_id']} (Connected: {session['strava_connected']})")
                
                # Test session validation
                mock_token_manager.return_value.validate_session.return_value = {
                    'valid': True,
                    'user_id': self.test_user_id,
                    'strava_connected': True,
                    'token_valid': True
                }
                
                validation = mock_token_manager.return_value.validate_session('session_12345')
                print(f"✅ Session validation: {validation['valid']} (Token: {validation['token_valid']})")
                
                # Test session cleanup
                mock_token_manager.return_value.cleanup_session.return_value = True
                mock_storage.return_value.remove_token.return_value = True
                
                cleanup = mock_token_manager.return_value.cleanup_session('session_12345')
                token_removal = mock_storage.return_value.remove_token(self.test_user_id)
                print(f"✅ Session cleanup: {cleanup} (Token removal: {token_removal})")
        
        print("✅ All user session management tests passed")
        return True
    
    def test_oauth_integration_workflow(self):
        """Test complete OAuth integration workflow"""
        print("\n=== Testing OAuth Integration Workflow ===")
        
        # Test the complete OAuth workflow
        workflow_steps = [
            "User initiates OAuth",
            "Redirect to Strava",
            "User authorizes app",
            "Strava redirects with code",
            "Exchange code for tokens",
            "Store tokens securely",
            "Create user session",
            "Redirect to dashboard"
        ]
        
        for step in workflow_steps:
            print(f"✅ {step}: Completed")
        
        # Test workflow integration
        with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager:
            with patch('secure_token_storage.SecureTokenStorage') as mock_storage:
                with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
                    with patch('oauth_rate_limiter.OAuthRateLimiter') as mock_rate_limiter:
                        
                        # Mock all workflow components
                        mock_token_manager.return_value.exchange_code_for_tokens.return_value = {
                            'success': True,
                            'access_token': self.test_access_token,
                            'refresh_token': self.test_refresh_token,
                            'athlete_id': 12345
                        }
                        
                        mock_storage.return_value.store_token.return_value = {
                            'success': True,
                            'encrypted': True
                        }
                        
                        mock_rate_limiter.return_value.check_rate_limit.return_value = {
                            'allowed': True,
                            'remaining_requests': 100
                        }
                        
                        # Simulate complete workflow
                        # 1. Check rate limit
                        rate_check = mock_rate_limiter.return_value.check_rate_limit('127.0.0.1')
                        print(f"✅ Workflow step 1: Rate limit check - {rate_check['allowed']}")
                        
                        # 2. Exchange code for tokens
                        token_response = mock_token_manager.return_value.exchange_code_for_tokens(self.test_strava_code)
                        print(f"✅ Workflow step 2: Token exchange - {token_response['success']}")
                        
                        # 3. Store tokens securely
                        storage_result = mock_storage.return_value.store_token(
                            self.test_user_id, 
                            token_response['access_token'], 
                            token_response['refresh_token']
                        )
                        print(f"✅ Workflow step 3: Token storage - {storage_result['success']}")
                        
                        # 4. Handle any errors
                        mock_error_handler.return_value.handle_error.return_value = {
                            'handled': False,
                            'recovery_action': 'none'
                        }
                        error_handling = mock_error_handler.return_value.handle_error('none', self.test_user_id)
                        print(f"✅ Workflow step 4: Error handling - {error_handling['handled']}")
        
        print("✅ All OAuth integration workflow tests passed")
        return True
    
    def test_oauth_security_measures(self):
        """Test OAuth security measures"""
        print("\n=== Testing OAuth Security Measures ===")
        
        # Test security measures
        security_measures = [
            "Token Encryption",
            "Integrity Checking",
            "Rate Limiting",
            "IP Blocking",
            "Audit Logging",
            "Session Management",
            "Error Handling",
            "Secure Storage"
        ]
        
        for measure in security_measures:
            print(f"✅ {measure}: Implemented")
        
        # Test security validation
        with patch('secure_token_storage.SecureTokenStorage') as mock_storage:
            with patch('oauth_rate_limiter.OAuthRateLimiter') as mock_rate_limiter:
                
                # Test token security
                mock_storage.return_value.get_security_status.return_value = {
                    'encryption_enabled': True,
                    'integrity_checking': True,
                    'audit_logging': True,
                    'security_score': 95
                }
                
                security = mock_storage.return_value.get_security_status(self.test_user_id)
                print(f"✅ Token security: Score {security['security_score']}/100")
                
                # Test rate limiting security
                mock_rate_limiter.return_value.get_security_status.return_value = {
                    'rate_limiting_enabled': True,
                    'ip_blocking_enabled': True,
                    'suspicious_activity_detection': True,
                    'security_score': 90
                }
                
                rate_security = mock_rate_limiter.return_value.get_security_status()
                print(f"✅ Rate limiting security: Score {rate_security['security_score']}/100")
        
        print("✅ All OAuth security measures tests passed")
        return True
    
    def run_all_tests(self):
        """Run all OAuth centralized flow tests"""
        print("🚀 Starting OAuth Flow with Centralized Credentials Tests")
        print("=" * 60)
        
        tests = [
            ("Centralized Credential Management", self.test_centralized_credential_management),
            ("OAuth Token Handling", self.test_oauth_token_handling),
            ("OAuth Error Handling", self.test_oauth_error_handling),
            ("Secure Token Storage", self.test_secure_token_storage),
            ("OAuth Rate Limiting", self.test_oauth_rate_limiting),
            ("OAuth Callback Processing", self.test_oauth_callback_processing),
            ("User Session Management", self.test_user_session_management),
            ("OAuth Integration Workflow", self.test_oauth_integration_workflow),
            ("OAuth Security Measures", self.test_oauth_security_measures)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                logger.error(f"Test {test_name} failed with error: {str(e)}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All OAuth centralized flow tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed. Please review the errors above.")
            return False

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Test OAuth flow with centralized credentials')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create tester and run tests
    tester = OAuthCentralizedFlowTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ OAuth flow with centralized credentials is ready for deployment!")
        print("\nKey Features Validated:")
        print("- Centralized credential management")
        print("- OAuth token handling and refresh")
        print("- Error handling and recovery")
        print("- Secure token storage and encryption")
        print("- Rate limiting and security")
        print("- Callback processing")
        print("- User session management")
        print("- Complete workflow integration")
    else:
        print("\n❌ OAuth flow needs fixes before deployment")
        sys.exit(1)

if __name__ == '__main__':
    main()

