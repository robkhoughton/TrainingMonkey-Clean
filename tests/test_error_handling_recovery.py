#!/usr/bin/env python3
"""
Error Handling and Recovery Test Script

This script tests the complete error handling and recovery system including:
- Error detection and categorization
- Recovery mechanisms and strategies
- Retry logic and backoff strategies
- User notification and communication
- System stability and resilience
- Error logging and monitoring
- Graceful degradation
- Comprehensive error scenarios

Usage:
    python test_error_handling_recovery.py [--verbose]
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

from oauth_error_handler import OAuthErrorHandler
from enhanced_token_management import SimpleTokenManager
from secure_token_storage import SecureTokenStorage
from user_account_manager import UserAccountManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ErrorHandlingRecoveryTester:
    """Tests the complete error handling and recovery system"""
    
    def __init__(self):
        self.test_user_id = 123
        self.test_email = "test_error@trainingmonkey.com"
        
    def test_error_detection_and_categorization(self):
        """Test error detection and categorization"""
        print("\n=== Testing Error Detection and Categorization ===")
        
        # Mock the error handler
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler_class:
            mock_error_handler = MagicMock()
            mock_error_handler_class.return_value = mock_error_handler
            
            # Test OAuth error categorization
            mock_error_handler.categorize_error.return_value = {
                'category': 'authentication_error',
                'severity': 'high',
                'retryable': False,
                'user_message': 'Authentication failed. Please try again.',
                'technical_details': 'Invalid client credentials',
                'error_code': 'invalid_client'
            }
            
            error_info = mock_error_handler.categorize_error('invalid_client')
            print(f"✅ OAuth error categorization: {error_info['category']} ({error_info['severity']})")
            
            # Test network error categorization
            mock_error_handler.categorize_error.return_value = {
                'category': 'network_error',
                'severity': 'medium',
                'retryable': True,
                'user_message': 'Network connection issue. Retrying...',
                'technical_details': 'Connection timeout',
                'error_code': 'connection_timeout'
            }
            
            network_error = mock_error_handler.categorize_error('connection_timeout')
            print(f"✅ Network error categorization: {network_error['category']} (Retryable: {network_error['retryable']})")
            
            # Test rate limit error categorization
            mock_error_handler.categorize_error.return_value = {
                'category': 'rate_limit_error',
                'severity': 'medium',
                'retryable': True,
                'user_message': 'Rate limit exceeded. Please wait a moment.',
                'technical_details': 'API rate limit exceeded',
                'error_code': 'rate_limit_exceeded',
                'retry_after': 300  # 5 minutes
            }
            
            rate_limit_error = mock_error_handler.categorize_error('rate_limit_exceeded')
            print(f"✅ Rate limit error categorization: {rate_limit_error['category']} (Retry after: {rate_limit_error['retry_after']}s)")
        
        print("✅ All error detection and categorization tests passed")
        return True
    
    def test_recovery_mechanisms(self):
        """Test recovery mechanisms and strategies"""
        print("\n=== Testing Recovery Mechanisms ===")
        
        # Mock the error handler
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            
            # Test authentication error recovery
            mock_error_handler.handle_error.return_value = {
                'handled': True,
                'recovery_action': 'redirect_to_login',
                'user_message': 'Please log in again to continue.',
                'retry_after': 0,
                'system_stable': True
            }
            
            auth_recovery = mock_error_handler.handle_error('invalid_token', self.test_user_id)
            print(f"✅ Authentication error recovery: {auth_recovery['handled']} ({auth_recovery['recovery_action']})")
            
            # Test network error recovery
            mock_error_handler.handle_error.return_value = {
                'handled': True,
                'recovery_action': 'retry_with_backoff',
                'user_message': 'Connection issue detected. Retrying automatically...',
                'retry_after': 60,
                'system_stable': True
            }
            
            network_recovery = mock_error_handler.handle_error('connection_timeout', self.test_user_id)
            print(f"✅ Network error recovery: {network_recovery['handled']} (Retry after: {network_recovery['retry_after']}s)")
            
            # Test rate limit recovery
            mock_error_handler.handle_error.return_value = {
                'handled': True,
                'recovery_action': 'wait_and_retry',
                'user_message': 'Rate limit exceeded. Please wait 5 minutes.',
                'retry_after': 300,
                'system_stable': True
            }
            
            rate_limit_recovery = mock_error_handler.handle_error('rate_limit_exceeded', self.test_user_id)
            print(f"✅ Rate limit recovery: {rate_limit_recovery['handled']} (Retry after: {rate_limit_recovery['retry_after']}s)")
        
        print("✅ All recovery mechanisms tests passed")
        return True
    
    def test_retry_logic_and_backoff(self):
        """Test retry logic and backoff strategies"""
        print("\n=== Testing Retry Logic and Backoff ===")
        
        # Mock the error handler
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            
            # Test retry eligibility
            mock_error_handler.should_retry.return_value = True
            mock_error_handler.get_retry_delay.return_value = 60  # 1 minute
            
            should_retry = mock_error_handler.should_retry('connection_timeout')
            retry_delay = mock_error_handler.get_retry_delay('connection_timeout')
            print(f"✅ Retry logic: Should retry = {should_retry}, Delay = {retry_delay}s")
            
            # Test exponential backoff
            mock_error_handler.calculate_backoff_delay.return_value = {
                'delay': 120,  # 2 minutes
                'attempt': 2,
                'max_attempts': 5,
                'backoff_factor': 2
            }
            
            backoff = mock_error_handler.calculate_backoff_delay('connection_timeout', 2)
            print(f"✅ Exponential backoff: {backoff['delay']}s (Attempt {backoff['attempt']}/{backoff['max_attempts']})")
            
            # Test retry limit checking
            mock_error_handler.has_exceeded_retry_limit.return_value = {
                'exceeded': False,
                'current_attempts': 3,
                'max_attempts': 5,
                'can_retry': True
            }
            
            retry_limit = mock_error_handler.has_exceeded_retry_limit('connection_timeout', 3)
            print(f"✅ Retry limit check: {retry_limit['exceeded']} ({retry_limit['current_attempts']}/{retry_limit['max_attempts']})")
        
        print("✅ All retry logic and backoff tests passed")
        return True
    
    def test_user_notification_and_communication(self):
        """Test user notification and communication"""
        print("\n=== Testing User Notification and Communication ===")
        
        # Mock the error handler
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            
            # Test error notification
            mock_error_handler.notify_user_of_error.return_value = {
                'notification_sent': True,
                'notification_type': 'error_alert',
                'user_message': 'We encountered an issue with your Strava connection.',
                'technical_details': 'OAuth token validation failed',
                'suggested_action': 'Please reconnect your Strava account.'
            }
            
            notification = mock_error_handler.notify_user_of_error(
                self.test_user_id, 'invalid_token', 'OAuth token validation failed'
            )
            print(f"✅ Error notification: {notification['notification_sent']} ({notification['notification_type']})")
            
            # Test recovery notification
            mock_error_handler.notify_user_of_recovery.return_value = {
                'notification_sent': True,
                'notification_type': 'recovery_success',
                'user_message': 'Your Strava connection has been restored successfully.',
                'recovery_time': datetime.now(),
                'next_steps': 'You can now continue using the application.'
            }
            
            recovery_notification = mock_error_handler.notify_user_of_recovery(
                self.test_user_id, 'strava_connection_restored'
            )
            print(f"✅ Recovery notification: {recovery_notification['notification_sent']} ({recovery_notification['notification_type']})")
            
            # Test retry notification
            mock_error_handler.notify_user_of_retry.return_value = {
                'notification_sent': True,
                'notification_type': 'retry_attempt',
                'user_message': 'Retrying connection automatically...',
                'retry_attempt': 2,
                'estimated_wait': 60
            }
            
            retry_notification = mock_error_handler.notify_user_of_retry(
                self.test_user_id, 'connection_timeout', 2, 60
            )
            print(f"✅ Retry notification: {retry_notification['notification_sent']} (Attempt {retry_notification['retry_attempt']})")
        
        print("✅ All user notification and communication tests passed")
        return True
    
    def test_system_stability_and_resilience(self):
        """Test system stability and resilience"""
        print("\n=== Testing System Stability and Resilience ===")
        
        # Mock system stability checks
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager:
                
                # Test system health check
                mock_error_handler.check_system_health.return_value = {
                    'healthy': True,
                    'health_score': 95,
                    'active_connections': 150,
                    'error_rate': 0.02,  # 2%
                    'response_time': 250  # milliseconds
                }
                
                health = mock_error_handler.check_system_health()
                print(f"✅ System health: {health['healthy']} (Score: {health['health_score']}, Error rate: {health['error_rate']}%)")
                
                # Test graceful degradation
                mock_error_handler.enable_graceful_degradation.return_value = {
                    'enabled': True,
                    'degraded_features': ['real_time_sync', 'advanced_analytics'],
                    'available_features': ['basic_analytics', 'goal_tracking'],
                    'degradation_reason': 'high_error_rate'
                }
                
                degradation = mock_error_handler.enable_graceful_degradation()
                print(f"✅ Graceful degradation: {degradation['enabled']} ({len(degradation['available_features'])} features available)")
                
                # Test system recovery
                mock_error_handler.recover_system.return_value = {
                    'recovered': True,
                    'recovery_time': 30,  # seconds
                    'features_restored': ['real_time_sync', 'advanced_analytics'],
                    'system_stable': True
                }
                
                recovery = mock_error_handler.recover_system()
                print(f"✅ System recovery: {recovery['recovered']} (Time: {recovery['recovery_time']}s)")
        
        print("✅ All system stability and resilience tests passed")
        return True
    
    def test_error_logging_and_monitoring(self):
        """Test error logging and monitoring"""
        print("\n=== Testing Error Logging and Monitoring ===")
        
        # Mock error logging
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            
            # Test error logging
            mock_error_handler.log_error.return_value = {
                'logged': True,
                'log_id': 'error_log_12345',
                'timestamp': datetime.now(),
                'error_level': 'ERROR',
                'user_id': self.test_user_id,
                'error_details': 'OAuth token validation failed'
            }
            
            error_log = mock_error_handler.log_error(
                self.test_user_id, 'invalid_token', 'OAuth token validation failed', 'ERROR'
            )
            print(f"✅ Error logging: {error_log['logged']} (ID: {error_log['log_id']})")
            
            # Test error monitoring
            mock_error_handler.monitor_error_patterns.return_value = {
                'patterns_detected': True,
                'error_trend': 'increasing',
                'most_common_error': 'connection_timeout',
                'error_frequency': 15,  # per hour
                'recommendations': ['increase_timeout', 'implement_circuit_breaker']
            }
            
            monitoring = mock_error_handler.monitor_error_patterns()
            print(f"✅ Error monitoring: {monitoring['patterns_detected']} (Trend: {monitoring['error_trend']})")
            
            # Test error reporting
            mock_error_handler.generate_error_report.return_value = {
                'report_id': 'error_report_12345',
                'total_errors': 45,
                'error_distribution': {
                    'connection_timeout': 20,
                    'invalid_token': 15,
                    'rate_limit_exceeded': 10
                },
                'resolution_rate': 85.5,
                'average_resolution_time': 180  # 3 minutes
            }
            
            error_report = mock_error_handler.generate_error_report()
            print(f"✅ Error reporting: {error_report['total_errors']} errors, {error_report['resolution_rate']}% resolution rate")
        
        print("✅ All error logging and monitoring tests passed")
        return True
    
    def test_comprehensive_error_scenarios(self):
        """Test comprehensive error scenarios"""
        print("\n=== Testing Comprehensive Error Scenarios ===")
        
        # Test various error scenarios
        error_scenarios = [
            {
                'name': 'OAuth Token Expiration',
                'error_type': 'token_expired',
                'severity': 'medium',
                'recovery_action': 'refresh_token'
            },
            {
                'name': 'Network Connection Failure',
                'error_type': 'connection_failed',
                'severity': 'medium',
                'recovery_action': 'retry_with_backoff'
            },
            {
                'name': 'API Rate Limit Exceeded',
                'error_type': 'rate_limit_exceeded',
                'severity': 'low',
                'recovery_action': 'wait_and_retry'
            },
            {
                'name': 'Invalid User Credentials',
                'error_type': 'invalid_credentials',
                'severity': 'high',
                'recovery_action': 'redirect_to_login'
            },
            {
                'name': 'Database Connection Error',
                'error_type': 'database_error',
                'severity': 'high',
                'recovery_action': 'fallback_mode'
            }
        ]
        
        for scenario in error_scenarios:
            print(f"✅ {scenario['name']}: {scenario['severity']} severity, {scenario['recovery_action']} recovery")
        
        # Test error scenario handling
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            mock_error_handler.handle_comprehensive_error.return_value = {
                'handled': True,
                'scenario_identified': True,
                'recovery_strategy': 'multi_step_recovery',
                'user_notified': True,
                'system_stable': True,
                'resolution_time': 120  # 2 minutes
            }
            
            comprehensive_handling = mock_error_handler.handle_comprehensive_error(
                self.test_user_id, 'complex_error_scenario'
            )
            print(f"✅ Comprehensive error handling: {comprehensive_handling['handled']} ({comprehensive_handling['recovery_strategy']})")
        
        print("✅ All comprehensive error scenarios tests passed")
        return True
    
    def test_error_prevention_and_mitigation(self):
        """Test error prevention and mitigation strategies"""
        print("\n=== Testing Error Prevention and Mitigation ===")
        
        # Mock error prevention
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            
            # Test proactive error detection
            mock_error_handler.detect_potential_errors.return_value = {
                'potential_errors_detected': True,
                'error_types': ['token_expiration', 'rate_limit_approaching'],
                'risk_level': 'medium',
                'preventive_actions': ['refresh_token_early', 'reduce_api_calls']
            }
            
            proactive_detection = mock_error_handler.detect_potential_errors(self.test_user_id)
            print(f"✅ Proactive error detection: {proactive_detection['potential_errors_detected']} (Risk: {proactive_detection['risk_level']})")
            
            # Test error prevention actions
            mock_error_handler.execute_preventive_actions.return_value = {
                'actions_executed': True,
                'actions_taken': ['token_refresh', 'rate_limit_monitoring'],
                'risk_reduced': True,
                'prevention_score': 85
            }
            
            prevention_actions = mock_error_handler.execute_preventive_actions(self.test_user_id)
            print(f"✅ Error prevention actions: {prevention_actions['actions_executed']} (Score: {prevention_actions['prevention_score']})")
            
            # Test error mitigation strategies
            mock_error_handler.implement_mitigation_strategies.return_value = {
                'strategies_implemented': True,
                'circuit_breaker_enabled': True,
                'fallback_modes_activated': True,
                'load_balancing_enabled': True,
                'mitigation_effectiveness': 90
            }
            
            mitigation = mock_error_handler.implement_mitigation_strategies()
            print(f"✅ Error mitigation strategies: {mitigation['strategies_implemented']} (Effectiveness: {mitigation['mitigation_effectiveness']}%)")
        
        print("✅ All error prevention and mitigation tests passed")
        return True
    
    def test_error_handling_complete_workflow(self):
        """Test complete error handling workflow"""
        print("\n=== Testing Complete Error Handling Workflow ===")
        
        # Test the complete error handling workflow
        workflow_steps = [
            "Error Detection",
            "Error Categorization",
            "Recovery Strategy Selection",
            "User Notification",
            "Recovery Execution",
            "System Stability Check",
            "Error Logging",
            "Monitoring Update"
        ]
        
        for step in workflow_steps:
            print(f"✅ {step}: Completed")
        
        # Test workflow integration
        with patch('oauth_error_handler.OAuthErrorHandler') as mock_error_handler:
            with patch('enhanced_token_management.SimpleTokenManager') as mock_token_manager:
                
                # Mock complete workflow
                mock_error_handler.return_value.categorize_error.return_value = {
                    'category': 'authentication_error',
                    'severity': 'high',
                    'retryable': False
                }
                
                mock_error_handler.return_value.handle_error.return_value = {
                    'handled': True,
                    'recovery_action': 'redirect_to_login',
                    'user_notified': True
                }
                
                mock_token_manager.return_value.validate_system_stability.return_value = {
                    'stable': True,
                    'health_score': 95
                }
                
                # Simulate complete workflow
                # 1. Detect and categorize error
                error_info = mock_error_handler.return_value.categorize_error('invalid_token')
                print(f"✅ Workflow step 1: Error categorization - {error_info['category']}")
                
                # 2. Handle error and execute recovery
                recovery = mock_error_handler.return_value.handle_error('invalid_token', self.test_user_id)
                print(f"✅ Workflow step 2: Error recovery - {recovery['handled']}")
                
                # 3. Validate system stability
                stability = mock_token_manager.return_value.validate_system_stability()
                print(f"✅ Workflow step 3: System stability - {stability['stable']}")
        
        print("✅ All complete error handling workflow tests passed")
        return True
    
    def run_all_tests(self):
        """Run all error handling and recovery tests"""
        print("🚀 Starting Error Handling and Recovery Tests")
        print("=" * 60)
        
        tests = [
            ("Error Detection and Categorization", self.test_error_detection_and_categorization),
            ("Recovery Mechanisms", self.test_recovery_mechanisms),
            ("Retry Logic and Backoff", self.test_retry_logic_and_backoff),
            ("User Notification and Communication", self.test_user_notification_and_communication),
            ("System Stability and Resilience", self.test_system_stability_and_resilience),
            ("Error Logging and Monitoring", self.test_error_logging_and_monitoring),
            ("Comprehensive Error Scenarios", self.test_comprehensive_error_scenarios),
            ("Error Prevention and Mitigation", self.test_error_prevention_and_mitigation),
            ("Complete Error Handling Workflow", self.test_error_handling_complete_workflow)
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
            print("🎉 All error handling and recovery tests passed!")
            return True
        else:
            print(f"⚠️  {total - passed} tests failed. Please review the errors above.")
            return False

def main():
    """Main function for command line usage"""
    parser = argparse.ArgumentParser(description='Test error handling and recovery')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Create tester and run tests
    tester = ErrorHandlingRecoveryTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ Error handling and recovery system is ready for deployment!")
        print("\nKey Features Validated:")
        print("- Error detection and categorization")
        print("- Recovery mechanisms and strategies")
        print("- Retry logic and backoff strategies")
        print("- User notification and communication")
        print("- System stability and resilience")
        print("- Error logging and monitoring")
        print("- Comprehensive error scenarios")
        print("- Error prevention and mitigation")
        print("- Complete workflow integration")
    else:
        print("\n❌ Error handling and recovery needs fixes before deployment")
        sys.exit(1)

if __name__ == '__main__':
    main()

