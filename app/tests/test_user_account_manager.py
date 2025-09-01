"""
Test suite for user account manager module
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from user_account_manager import UserAccountManager


class TestUserAccountManager(unittest.TestCase):
    """Test cases for UserAccountManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = UserAccountManager()
    
    @patch('user_account_manager.execute_query')
    @patch('user_account_manager.User.get_by_email')
    @patch('user_account_manager.get_current_legal_versions')
    def test_create_new_user_account_success(self, mock_versions, mock_get_user, mock_execute):
        """Test successful user account creation"""
        # Mock dependencies
        mock_get_user.return_value = None  # No existing user
        mock_versions.return_value = {
            'terms': '2.0',
            'privacy': '2.0',
            'disclaimer': '2.0'
        }
        mock_execute.return_value = [{'id': 123}]
        
        with patch('user_account_manager.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success, user_id, error = self.manager.create_new_user_account(
                'test@example.com', 'password123'
            )
            
            self.assertTrue(success)
            self.assertEqual(user_id, 123)
            self.assertEqual(error, "")
    
    @patch('user_account_manager.User.get_by_email')
    def test_create_new_user_account_existing_user(self, mock_get_user):
        """Test user account creation with existing user"""
        # Mock existing user
        mock_user = MagicMock()
        mock_user.id = 456
        mock_get_user.return_value = mock_user
        
        success, user_id, error = self.manager.create_new_user_account(
            'existing@example.com', 'password123'
        )
        
        self.assertFalse(success)
        self.assertIsNone(user_id)
        self.assertIn("already exists", error)
    
    def test_create_new_user_account_missing_credentials(self):
        """Test user account creation with missing credentials"""
        # Missing email
        success, user_id, error = self.manager.create_new_user_account('', 'password123')
        self.assertFalse(success)
        self.assertIn("required", error)
        
        # Missing password
        success, user_id, error = self.manager.create_new_user_account('test@example.com', '')
        self.assertFalse(success)
        self.assertIn("required", error)
    
    @patch('user_account_manager.execute_query')
    def test_activate_user_account_success(self, mock_execute):
        """Test successful account activation"""
        mock_execute.return_value = True
        
        success = self.manager.activate_user_account(123)
        self.assertTrue(success)
    
    @patch('user_account_manager.execute_query')
    def test_activate_user_account_failure(self, mock_execute):
        """Test account activation failure"""
        mock_execute.side_effect = Exception("Database error")
        
        success = self.manager.activate_user_account(123)
        self.assertFalse(success)
    
    @patch('user_account_manager.execute_query')
    def test_deactivate_user_account_success(self, mock_execute):
        """Test successful account deactivation"""
        mock_execute.return_value = True
        
        success = self.manager.deactivate_user_account(123, 'test_reason')
        self.assertTrue(success)
    
    @patch('user_account_manager.execute_query')
    def test_deactivate_user_account_failure(self, mock_execute):
        """Test account deactivation failure"""
        mock_execute.side_effect = Exception("Database error")
        
        success = self.manager.deactivate_user_account(123)
        self.assertFalse(success)
    
    @patch('user_account_manager.execute_query')
    def test_get_user_account_status_success(self, mock_execute):
        """Test successful account status retrieval"""
        mock_user_data = {
            'id': 123,
            'email': 'test@example.com',
            'account_status': 'active',
            'onboarding_step': 'onboarding_complete',
            'terms_accepted_version': '2.0',
            'privacy_accepted_version': '2.0',
            'disclaimer_accepted_version': '2.0',
            'terms_accepted_date': datetime.now(),
            'privacy_accepted_date': datetime.now(),
            'disclaimer_accepted_date': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        mock_execute.return_value = [mock_user_data]
        
        with patch.object(self.manager.compliance_tracker, 'get_user_legal_status') as mock_legal:
            mock_legal.return_value = {'terms': True, 'privacy': True, 'disclaimer': True}
            
            status = self.manager.get_user_account_status(123)
            
            self.assertEqual(status['user_id'], 123)
            self.assertEqual(status['email'], 'test@example.com')
            self.assertEqual(status['account_status'], 'active')
            self.assertEqual(status['onboarding_step'], 'onboarding_complete')
            self.assertIn('legal_compliance', status)
    
    @patch('user_account_manager.execute_query')
    def test_get_user_account_status_not_found(self, mock_execute):
        """Test account status retrieval for non-existent user"""
        mock_execute.return_value = []
        
        status = self.manager.get_user_account_status(999)
        self.assertEqual(status, {})
    
    @patch('user_account_manager.execute_query')
    def test_update_onboarding_progress_success(self, mock_execute):
        """Test successful onboarding progress update"""
        mock_execute.return_value = True
        
        success = self.manager.update_onboarding_progress(123, 'strava_connected')
        self.assertTrue(success)
    
    @patch('user_account_manager.execute_query')
    def test_update_onboarding_progress_failure(self, mock_execute):
        """Test onboarding progress update failure"""
        mock_execute.side_effect = Exception("Database error")
        
        success = self.manager.update_onboarding_progress(123, 'strava_connected')
        self.assertFalse(success)
    
    @patch('user_account_manager.execute_query')
    def test_complete_onboarding_success(self, mock_execute):
        """Test successful onboarding completion"""
        mock_execute.return_value = True
        
        success = self.manager.complete_onboarding(123)
        self.assertTrue(success)
    
    @patch('user_account_manager.execute_query')
    def test_complete_onboarding_failure(self, mock_execute):
        """Test onboarding completion failure"""
        mock_execute.side_effect = Exception("Database error")
        
        success = self.manager.complete_onboarding(123)
        self.assertFalse(success)
    
    @patch('user_account_manager.execute_query')
    def test_get_pending_registrations_success(self, mock_execute):
        """Test successful pending registrations retrieval"""
        mock_pending_data = [
            {
                'id': 123,
                'email': 'pending1@example.com',
                'account_status': 'pending',
                'onboarding_step': 'registration_complete',
                'created_at': datetime.now()
            },
            {
                'id': 124,
                'email': 'pending2@example.com',
                'account_status': 'pending',
                'onboarding_step': 'registration_complete',
                'created_at': datetime.now()
            }
        ]
        mock_execute.return_value = mock_pending_data
        
        pending = self.manager.get_pending_registrations()
        
        self.assertEqual(len(pending), 2)
        self.assertEqual(pending[0]['id'], 123)
        self.assertEqual(pending[1]['id'], 124)
    
    @patch('user_account_manager.execute_query')
    def test_get_pending_registrations_empty(self, mock_execute):
        """Test pending registrations retrieval when none exist"""
        mock_execute.return_value = []
        
        pending = self.manager.get_pending_registrations()
        self.assertEqual(pending, [])
    
    @patch('user_account_manager.execute_query')
    def test_cleanup_expired_registrations_success(self, mock_execute):
        """Test successful cleanup of expired registrations"""
        mock_execute.return_value = 5  # 5 registrations cleaned up
        
        cleaned_count = self.manager.cleanup_expired_registrations(7)
        self.assertEqual(cleaned_count, 5)
    
    @patch('user_account_manager.execute_query')
    def test_cleanup_expired_registrations_failure(self, mock_execute):
        """Test cleanup failure"""
        mock_execute.side_effect = Exception("Database error")
        
        cleaned_count = self.manager.cleanup_expired_registrations(7)
        self.assertEqual(cleaned_count, 0)
    
    @patch('user_account_manager.execute_query')
    @patch('user_account_manager.get_current_legal_versions')
    def test_create_user_record_success(self, mock_versions, mock_execute):
        """Test successful user record creation"""
        mock_versions.return_value = {
            'terms': '2.0',
            'privacy': '2.0',
            'disclaimer': '2.0'
        }
        mock_execute.return_value = [{'id': 123}]
        
        user_id = self.manager._create_user_record('test@example.com', 'password123', {
            'terms': '2.0',
            'privacy': '2.0',
            'disclaimer': '2.0'
        })
        
        self.assertEqual(user_id, 123)
    
    @patch('user_account_manager.execute_query')
    def test_create_user_record_failure(self, mock_execute):
        """Test user record creation failure"""
        mock_execute.side_effect = Exception("Database error")
        
        user_id = self.manager._create_user_record('test@example.com', 'password123', {})
        self.assertIsNone(user_id)
    
    def test_log_legal_acceptances_success(self):
        """Test successful legal acceptance logging"""
        with patch('user_account_manager.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            with patch.object(self.manager.compliance_tracker, 'log_user_legal_acceptance') as mock_log:
                legal_acceptances = {
                    'terms': True,
                    'privacy': True,
                    'disclaimer': True
                }
                current_versions = {
                    'terms': '2.0',
                    'privacy': '2.0',
                    'disclaimer': '2.0'
                }
                
                self.manager._log_legal_acceptances(123, legal_acceptances, current_versions)
                
                # Verify that log_user_legal_acceptance was called for each accepted document
                self.assertEqual(mock_log.call_count, 3)
    
    @patch('user_account_manager.execute_query')
    def test_initialize_onboarding_progress_success(self, mock_execute):
        """Test successful onboarding progress initialization"""
        mock_execute.return_value = True
        
        self.manager._initialize_onboarding_progress(123)
        # Should not raise any exceptions
    
    @patch('user_account_manager.execute_query')
    def test_initialize_onboarding_progress_failure(self, mock_execute):
        """Test onboarding progress initialization failure"""
        mock_execute.side_effect = Exception("Database error")
        
        # Should handle the exception gracefully
        self.manager._initialize_onboarding_progress(123)
        # Should not raise any exceptions


if __name__ == '__main__':
    unittest.main()
