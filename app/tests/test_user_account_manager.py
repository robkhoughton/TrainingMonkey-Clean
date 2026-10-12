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
    
if __name__ == '__main__':
    unittest.main()
