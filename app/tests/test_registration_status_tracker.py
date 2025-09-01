"""
Test suite for registration status tracker module
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from registration_status_tracker import (
    RegistrationStatusTracker, 
    RegistrationStatus, 
    RegistrationStep
)


class TestRegistrationStatusTracker(unittest.TestCase):
    """Test cases for RegistrationStatusTracker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tracker = RegistrationStatusTracker()
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_start_registration_tracking_success(self, mock_user_manager, mock_execute):
        """Test successful registration tracking start"""
        # Mock dependencies
        mock_user_manager.update_onboarding_progress.return_value = True
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success = self.tracker.start_registration_tracking(123)
            
            self.assertTrue(success)
            mock_user_manager.update_onboarding_progress.assert_called_once_with(
                123, 'registration_started'
            )
    
    @patch('registration_status_tracker.user_account_manager')
    def test_start_registration_tracking_failure(self, mock_user_manager):
        """Test registration tracking start failure"""
        mock_user_manager.update_onboarding_progress.return_value = False
        
        success = self.tracker.start_registration_tracking(123)
        self.assertFalse(success)
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_track_account_creation_success(self, mock_user_manager, mock_execute):
        """Test successful account creation tracking"""
        mock_user_manager.update_onboarding_progress.return_value = True
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success = self.tracker.track_account_creation(123)
            
            self.assertTrue(success)
            mock_user_manager.update_onboarding_progress.assert_called_once_with(
                123, 'account_created'
            )
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_track_email_verification_sent_success(self, mock_user_manager, mock_execute):
        """Test successful email verification sent tracking"""
        mock_user_manager.update_onboarding_progress.return_value = True
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success = self.tracker.track_email_verification_sent(123, 'test@example.com')
            
            self.assertTrue(success)
            mock_user_manager.update_onboarding_progress.assert_called_once_with(
                123, 'email_verification_sent'
            )
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_track_email_verification_complete_success(self, mock_user_manager, mock_execute):
        """Test successful email verification complete tracking"""
        mock_user_manager.update_onboarding_progress.return_value = True
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success = self.tracker.track_email_verification_complete(123)
            
            self.assertTrue(success)
            mock_user_manager.update_onboarding_progress.assert_called_once_with(
                123, 'email_verified'
            )
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_track_strava_connection_success(self, mock_user_manager, mock_execute):
        """Test successful Strava connection tracking"""
        mock_user_manager.update_onboarding_progress.return_value = True
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success = self.tracker.track_strava_connection(123, 'strava_user_456')
            
            self.assertTrue(success)
            mock_user_manager.update_onboarding_progress.assert_called_once_with(
                123, 'strava_connected'
            )
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_track_onboarding_start_success(self, mock_user_manager, mock_execute):
        """Test successful onboarding start tracking"""
        mock_user_manager.update_onboarding_progress.return_value = True
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success = self.tracker.track_onboarding_start(123)
            
            self.assertTrue(success)
            mock_user_manager.update_onboarding_progress.assert_called_once_with(
                123, 'onboarding_started'
            )
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_track_onboarding_complete_success(self, mock_user_manager, mock_execute):
        """Test successful onboarding completion tracking"""
        mock_user_manager.complete_onboarding.return_value = True
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            success = self.tracker.track_onboarding_complete(123)
            
            self.assertTrue(success)
            mock_user_manager.complete_onboarding.assert_called_once_with(123)
    
    @patch('registration_status_tracker.user_account_manager')
    def test_track_onboarding_complete_failure(self, mock_user_manager):
        """Test onboarding completion tracking failure"""
        mock_user_manager.complete_onboarding.return_value = False
        
        success = self.tracker.track_onboarding_complete(123)
        self.assertFalse(success)
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_get_registration_status_success(self, mock_user_manager, mock_execute):
        """Test successful registration status retrieval"""
        # Mock account status
        mock_account_status = {
            'user_id': 123,
            'email': 'test@example.com',
            'account_status': 'pending',
            'onboarding_step': 'account_created'
        }
        mock_user_manager.get_user_account_status.return_value = mock_account_status
        
        # Mock registration events
        mock_events = [
            {
                'step': 'registration_started',
                'status': 'pending',
                'timestamp': datetime.now(),
                'ip_address': '192.168.1.1',
                'user_agent': 'Test User Agent',
                'metadata': None
            },
            {
                'step': 'account_created',
                'status': 'pending',
                'timestamp': datetime.now(),
                'ip_address': '192.168.1.1',
                'user_agent': 'Test User Agent',
                'metadata': None
            }
        ]
        mock_execute.return_value = mock_events
        
        status = self.tracker.get_registration_status(123)
        
        self.assertIn('user_id', status)
        self.assertIn('account_status', status)
        self.assertIn('registration_events', status)
        self.assertIn('registration_progress', status)
        self.assertIn('current_status', status)
        self.assertIn('is_complete', status)
        self.assertIn('next_steps', status)
    
    @patch('registration_status_tracker.user_account_manager')
    def test_get_registration_status_no_account(self, mock_user_manager):
        """Test registration status retrieval for non-existent account"""
        mock_user_manager.get_user_account_status.return_value = {}
        
        status = self.tracker.get_registration_status(999)
        self.assertEqual(status, {})
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_get_pending_registrations_summary_success(self, mock_user_manager, mock_execute):
        """Test successful pending registrations summary"""
        # Mock pending registrations
        mock_pending = [
            {
                'id': 123,
                'email': 'pending1@example.com',
                'account_status': 'pending',
                'onboarding_step': 'account_created',
                'created_at': datetime.now()
            },
            {
                'id': 124,
                'email': 'pending2@example.com',
                'account_status': 'pending',
                'onboarding_step': 'email_verified',
                'created_at': datetime.now()
            }
        ]
        mock_user_manager.get_pending_registrations.return_value = mock_pending
        
        # Mock completion rate calculation
        mock_execute.side_effect = [
            [{'total': 10}],  # Total registrations
            [{'completed': 7}]  # Completed registrations
        ]
        
        summary = self.tracker.get_pending_registrations_summary()
        
        self.assertIn('total_pending', summary)
        self.assertIn('step_breakdown', summary)
        self.assertIn('recent_registrations', summary)
        self.assertIn('old_registrations', summary)
        self.assertIn('completion_rate', summary)
        self.assertEqual(summary['total_pending'], 2)
    
    @patch('registration_status_tracker.execute_query')
    @patch('registration_status_tracker.user_account_manager')
    def test_cleanup_expired_registrations_success(self, mock_user_manager, mock_execute):
        """Test successful cleanup of expired registrations"""
        # Mock expired registrations
        mock_expired = [
            {'id': 123, 'email': 'expired1@example.com', 'created_at': datetime.now()},
            {'id': 124, 'email': 'expired2@example.com', 'created_at': datetime.now()}
        ]
        mock_execute.side_effect = [
            mock_expired,  # Get expired registrations
            True,  # Log cleanup events
            True,  # Log cleanup events
            2  # Cleanup result
        ]
        mock_user_manager.cleanup_expired_registrations.return_value = 2
        
        cleaned_count = self.tracker.cleanup_expired_registrations(7)
        
        self.assertEqual(cleaned_count, 2)
        mock_user_manager.cleanup_expired_registrations.assert_called_once_with(7)
    
    def test_calculate_registration_progress_no_events(self):
        """Test registration progress calculation with no events"""
        progress = self.tracker._calculate_registration_progress([])
        
        self.assertEqual(progress['percentage'], 0)
        self.assertEqual(progress['current_step'], 'not_started')
        self.assertEqual(progress['total_steps'], 8)
    
    def test_calculate_registration_progress_with_events(self):
        """Test registration progress calculation with events"""
        events = [
            {'step': 'registration_started'},
            {'step': 'account_created'},
            {'step': 'email_verified'}
        ]
        
        progress = self.tracker._calculate_registration_progress(events)
        
        self.assertGreater(progress['percentage'], 0)
        self.assertEqual(progress['current_step'], 'email_verified')
        self.assertEqual(progress['total_steps'], 8)
        self.assertEqual(progress['completed_steps'], 3)
    
    def test_determine_current_status_active(self):
        """Test current status determination for active account"""
        account_status = {'account_status': 'active'}
        events = []
        
        current_status = self.tracker._determine_current_status(account_status, events)
        
        self.assertEqual(current_status, RegistrationStatus.ACTIVE.value)
    
    def test_determine_current_status_pending(self):
        """Test current status determination for pending account"""
        account_status = {'account_status': 'pending'}
        events = []
        
        current_status = self.tracker._determine_current_status(account_status, events)
        
        self.assertEqual(current_status, RegistrationStatus.PENDING.value)
    
    def test_determine_current_status_strava_connected(self):
        """Test current status determination for Strava connected account"""
        account_status = {'account_status': 'pending'}
        events = [
            {'step': 'strava_connected'}
        ]
        
        current_status = self.tracker._determine_current_status(account_status, events)
        
        self.assertEqual(current_status, RegistrationStatus.STRAVA_CONNECTED.value)
    
    def test_get_next_steps_pending(self):
        """Test next steps for pending status"""
        next_steps = self.tracker._get_next_steps(RegistrationStatus.PENDING.value, [])
        
        self.assertIn("Complete account creation", next_steps)
        self.assertIn("Verify email address", next_steps)
    
    def test_get_next_steps_email_verified(self):
        """Test next steps for email verified status"""
        next_steps = self.tracker._get_next_steps(RegistrationStatus.EMAIL_VERIFIED.value, [])
        
        self.assertIn("Connect Strava account", next_steps)
    
    def test_get_next_steps_strava_connected(self):
        """Test next steps for Strava connected status"""
        next_steps = self.tracker._get_next_steps(RegistrationStatus.STRAVA_CONNECTED.value, [])
        
        self.assertIn("Complete onboarding process", next_steps)
        self.assertIn("Set up training preferences", next_steps)
    
    def test_get_next_steps_active(self):
        """Test next steps for active status"""
        next_steps = self.tracker._get_next_steps(RegistrationStatus.ACTIVE.value, [])
        
        self.assertIn("Registration complete!", next_steps)
    
    @patch('registration_status_tracker.execute_query')
    def test_get_registration_events_success(self, mock_execute):
        """Test successful registration events retrieval"""
        mock_events = [
            {
                'step': 'registration_started',
                'status': 'pending',
                'timestamp': datetime.now(),
                'ip_address': '192.168.1.1',
                'user_agent': 'Test User Agent',
                'metadata': None
            }
        ]
        mock_execute.return_value = mock_events
        
        events = self.tracker._get_registration_events(123)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['step'], 'registration_started')
    
    @patch('registration_status_tracker.execute_query')
    def test_get_registration_events_empty(self, mock_execute):
        """Test registration events retrieval for user with no events"""
        mock_execute.return_value = []
        
        events = self.tracker._get_registration_events(123)
        
        self.assertEqual(events, [])
    
    @patch('registration_status_tracker.execute_query')
    def test_get_expired_registrations_success(self, mock_execute):
        """Test successful expired registrations retrieval"""
        mock_expired = [
            {'id': 123, 'email': 'expired1@example.com', 'created_at': datetime.now()}
        ]
        mock_execute.return_value = mock_expired
        
        expired = self.tracker._get_expired_registrations(7)
        
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]['id'], 123)
    
    @patch('registration_status_tracker.execute_query')
    def test_calculate_completion_rate_success(self, mock_execute):
        """Test successful completion rate calculation"""
        mock_execute.side_effect = [
            [{'total': 10}],  # Total registrations
            [{'completed': 7}]  # Completed registrations
        ]
        
        rate = self.tracker._calculate_completion_rate()
        
        self.assertEqual(rate, 70.0)
    
    @patch('registration_status_tracker.execute_query')
    def test_calculate_completion_rate_zero_total(self, mock_execute):
        """Test completion rate calculation with zero total registrations"""
        mock_execute.side_effect = [
            [{'total': 0}],  # Total registrations
            [{'completed': 0}]  # Completed registrations
        ]
        
        rate = self.tracker._calculate_completion_rate()
        
        self.assertEqual(rate, 0.0)
    
    @patch('registration_status_tracker.execute_query')
    def test_log_registration_event_success(self, mock_execute):
        """Test successful registration event logging"""
        mock_execute.return_value = True
        
        with patch('registration_status_tracker.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            # Should not raise any exceptions
            self.tracker._log_registration_event(
                123,
                RegistrationStep.ACCOUNT_CREATED,
                RegistrationStatus.PENDING,
                {'test': 'metadata'}
            )
            
            mock_execute.assert_called_once()


if __name__ == '__main__':
    unittest.main()
