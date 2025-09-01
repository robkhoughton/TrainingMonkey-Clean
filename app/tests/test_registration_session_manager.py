"""
Test suite for registration session manager module
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from registration_session_manager import (
    RegistrationSessionManager, 
    SessionStatus, 
    SessionType,
    RegistrationSession
)


class TestRegistrationSessionManager(unittest.TestCase):
    """Test cases for RegistrationSessionManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = RegistrationSessionManager()
    
    @patch('registration_session_manager.execute_query')
    @patch('registration_session_manager.user_account_manager')
    def test_create_registration_session_success(self, mock_user_manager, mock_execute):
        """Test successful registration session creation"""
        # Mock dependencies
        mock_user_manager.get_user_account_status.return_value = {
            'account_status': 'pending'
        }
        mock_execute.return_value = True
        
        with patch('registration_session_manager.request') as mock_request:
            mock_request.remote_addr = '192.168.1.1'
            mock_request.headers.get.return_value = 'Test User Agent'
            
            with patch('registration_session_manager.session') as mock_flask_session:
                success, session_id, error = self.manager.create_registration_session(
                    123, SessionType.REGISTRATION
                )
                
                self.assertTrue(success)
                self.assertIsNotNone(session_id)
                self.assertEqual(error, "")
                mock_flask_session.__setitem__.assert_called_once()
    
    @patch('registration_session_manager.user_account_manager')
    def test_create_registration_session_user_not_found(self, mock_user_manager):
        """Test session creation for non-existent user"""
        mock_user_manager.get_user_account_status.return_value = {}
        
        success, session_id, error = self.manager.create_registration_session(
            999, SessionType.REGISTRATION
        )
        
        self.assertFalse(success)
        self.assertIsNone(session_id)
        self.assertIn("not found", error)
    
    @patch('registration_session_manager.user_account_manager')
    def test_create_registration_session_not_pending(self, mock_user_manager):
        """Test session creation for non-pending user"""
        mock_user_manager.get_user_account_status.return_value = {
            'account_status': 'active'
        }
        
        success, session_id, error = self.manager.create_registration_session(
            123, SessionType.REGISTRATION
        )
        
        self.assertFalse(success)
        self.assertIsNone(session_id)
        self.assertIn("not in pending status", error)
    
    @patch('registration_session_manager.execute_query')
    @patch('registration_session_manager.user_account_manager')
    def test_validate_session_success(self, mock_user_manager, mock_execute):
        """Test successful session validation"""
        # Mock session data
        mock_session_data = RegistrationSession(
            session_id='test_session_123',
            user_id=123,
            session_type=SessionType.REGISTRATION,
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            last_activity=datetime.now(),
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        with patch.object(self.manager, '_get_session_data', return_value=mock_session_data):
            with patch.object(self.manager, '_update_last_activity', return_value=True):
                is_valid, session_data, error = self.manager.validate_session('test_session_123')
                
                self.assertTrue(is_valid)
                self.assertEqual(session_data, mock_session_data)
                self.assertEqual(error, "")
    
    @patch('registration_session_manager.execute_query')
    def test_validate_session_not_found(self, mock_execute):
        """Test session validation for non-existent session"""
        with patch.object(self.manager, '_get_session_data', return_value=None):
            is_valid, session_data, error = self.manager.validate_session('invalid_session')
            
            self.assertFalse(is_valid)
            self.assertIsNone(session_data)
            self.assertIn("not found", error)
    
    @patch('registration_session_manager.execute_query')
    def test_validate_session_expired(self, mock_execute):
        """Test session validation for expired session"""
        # Mock expired session data
        mock_session_data = RegistrationSession(
            session_id='expired_session',
            user_id=123,
            session_type=SessionType.REGISTRATION,
            status=SessionStatus.ACTIVE,
            created_at=datetime.now() - timedelta(hours=25),
            expires_at=datetime.now() - timedelta(hours=1),
            last_activity=datetime.now() - timedelta(hours=1),
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        with patch.object(self.manager, '_get_session_data', return_value=mock_session_data):
            with patch.object(self.manager, '_update_session_status', return_value=True):
                is_valid, session_data, error = self.manager.validate_session('expired_session')
                
                self.assertFalse(is_valid)
                self.assertIsNone(session_data)
                self.assertIn("expired", error)
    
    @patch('registration_session_manager.execute_query')
    @patch('registration_session_manager.registration_status_tracker')
    @patch('registration_session_manager.user_account_manager')
    def test_resume_registration_success(self, mock_user_manager, mock_status_tracker, mock_execute):
        """Test successful registration resumption"""
        # Mock session data
        mock_session_data = RegistrationSession(
            session_id='test_session_123',
            user_id=123,
            session_type=SessionType.REGISTRATION,
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            last_activity=datetime.now(),
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        # Mock dependencies
        mock_status_tracker.get_registration_status.return_value = {
            'current_status': 'pending',
            'registration_progress': {'percentage': 25}
        }
        mock_user_manager.get_user_account_status.return_value = {
            'account_status': 'pending',
            'onboarding_step': 'account_created'
        }
        
        with patch.object(self.manager, 'validate_session', return_value=(True, mock_session_data, "")):
            success, resume_data, error = self.manager.resume_registration('test_session_123')
            
            self.assertTrue(success)
            self.assertIn('session_id', resume_data)
            self.assertIn('user_id', resume_data)
            self.assertIn('registration_status', resume_data)
            self.assertEqual(error, "")
    
    @patch('registration_session_manager.execute_query')
    def test_resume_registration_invalid_session(self, mock_execute):
        """Test registration resumption with invalid session"""
        with patch.object(self.manager, 'validate_session', return_value=(False, None, "Session expired")):
            success, resume_data, error = self.manager.resume_registration('invalid_session')
            
            self.assertFalse(success)
            self.assertEqual(resume_data, {})
            self.assertIn("expired", error)
    
    @patch('registration_session_manager.execute_query')
    def test_complete_session_success(self, mock_execute):
        """Test successful session completion"""
        with patch.object(self.manager, '_update_session_status', return_value=True):
            with patch('registration_session_manager.session') as mock_flask_session:
                success = self.manager.complete_session('test_session_123', {'completion_reason': 'success'})
                
                self.assertTrue(success)
                mock_flask_session.pop.assert_called_once()
    
    @patch('registration_session_manager.execute_query')
    def test_complete_session_failure(self, mock_execute):
        """Test session completion failure"""
        with patch.object(self.manager, '_update_session_status', return_value=False):
            success = self.manager.complete_session('test_session_123')
            
            self.assertFalse(success)
    
    @patch('registration_session_manager.execute_query')
    def test_invalidate_session_success(self, mock_execute):
        """Test successful session invalidation"""
        with patch.object(self.manager, '_invalidate_session', return_value=True):
            with patch('registration_session_manager.session') as mock_flask_session:
                mock_flask_session.get.return_value = 'test_session_123'
                
                success = self.manager.invalidate_session('test_session_123', 'test_reason')
                
                self.assertTrue(success)
                mock_flask_session.pop.assert_called_once()
    
    @patch('registration_session_manager.execute_query')
    def test_invalidate_session_failure(self, mock_execute):
        """Test session invalidation failure"""
        with patch.object(self.manager, '_invalidate_session', return_value=False):
            success = self.manager.invalidate_session('test_session_123')
            
            self.assertFalse(success)
    
    @patch('registration_session_manager.execute_query')
    def test_get_user_sessions_success(self, mock_execute):
        """Test successful user sessions retrieval"""
        mock_sessions = [
            RegistrationSession(
                session_id='session1',
                user_id=123,
                session_type=SessionType.REGISTRATION,
                status=SessionStatus.ACTIVE,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24),
                last_activity=datetime.now(),
                ip_address='192.168.1.1',
                user_agent='Test User Agent'
            )
        ]
        
        with patch.object(self.manager, '_get_active_sessions_for_user', return_value=mock_sessions):
            sessions = self.manager.get_user_sessions(123)
            
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].session_id, 'session1')
    
    @patch('registration_session_manager.execute_query')
    def test_cleanup_expired_sessions_success(self, mock_execute):
        """Test successful cleanup of expired sessions"""
        mock_execute.side_effect = [True, [{'count': 5}]]  # Update, then count query
        
        cleaned_count = self.manager.cleanup_expired_sessions()
        
        self.assertEqual(cleaned_count, 5)
    
    @patch('registration_session_manager.execute_query')
    def test_extend_session_success(self, mock_execute):
        """Test successful session extension"""
        # Mock session data
        mock_session_data = RegistrationSession(
            session_id='test_session_123',
            user_id=123,
            session_type=SessionType.REGISTRATION,
            status=SessionStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            last_activity=datetime.now(),
            ip_address='192.168.1.1',
            user_agent='Test User Agent'
        )
        
        with patch.object(self.manager, 'validate_session', return_value=(True, mock_session_data, "")):
            with patch.object(self.manager, '_update_session_status', return_value=True):
                success = self.manager.extend_session('test_session_123', 48)
                
                self.assertTrue(success)
    
    @patch('registration_session_manager.execute_query')
    def test_extend_session_invalid(self, mock_execute):
        """Test session extension for invalid session"""
        with patch.object(self.manager, 'validate_session', return_value=(False, None, "Session expired")):
            success = self.manager.extend_session('invalid_session', 48)
            
            self.assertFalse(success)
    
    @patch('registration_session_manager.execute_query')
    def test_get_session_analytics_success(self, mock_execute):
        """Test successful session analytics retrieval"""
        mock_execute.side_effect = [
            [{'count': 100}],  # Total sessions
            [{'count': 25}],   # Active sessions
            [{'count': 60}],   # Completed sessions
            [{'count': 15}],   # Expired sessions
            [{'session_type': 'registration', 'count': 50}]  # Sessions by type
        ]
        
        analytics = self.manager.get_session_analytics()
        
        self.assertIn('total_sessions', analytics)
        self.assertIn('active_sessions', analytics)
        self.assertIn('completed_sessions', analytics)
        self.assertIn('expired_sessions', analytics)
        self.assertIn('sessions_by_type', analytics)
        self.assertIn('completion_rate', analytics)
        self.assertEqual(analytics['total_sessions'], 100)
        self.assertEqual(analytics['completion_rate'], 60.0)
    
    def test_generate_session_id(self):
        """Test session ID generation"""
        session_id1 = self.manager._generate_session_id()
        session_id2 = self.manager._generate_session_id()
        
        self.assertIsInstance(session_id1, str)
        self.assertIsInstance(session_id2, str)
        self.assertNotEqual(session_id1, session_id2)
        self.assertGreater(len(session_id1), 20)  # Should be reasonably long
    
    @patch('registration_session_manager.execute_query')
    def test_create_session_record_success(self, mock_execute):
        """Test successful session record creation"""
        mock_execute.return_value = True
        
        success = self.manager._create_session_record(
            'test_session_123',
            123,
            SessionType.REGISTRATION,
            datetime.now() + timedelta(hours=24),
            '192.168.1.1',
            'Test User Agent',
            {'test': 'metadata'}
        )
        
        self.assertTrue(success)
    
    @patch('registration_session_manager.execute_query')
    def test_create_session_record_failure(self, mock_execute):
        """Test session record creation failure"""
        mock_execute.side_effect = Exception("Database error")
        
        success = self.manager._create_session_record(
            'test_session_123',
            123,
            SessionType.REGISTRATION,
            datetime.now() + timedelta(hours=24),
            '192.168.1.1',
            'Test User Agent'
        )
        
        self.assertFalse(success)
    
    @patch('registration_session_manager.execute_query')
    def test_get_session_data_success(self, mock_execute):
        """Test successful session data retrieval"""
        mock_result = [{
            'session_id': 'test_session_123',
            'user_id': 123,
            'session_type': 'registration',
            'status': 'active',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24),
            'last_activity': datetime.now(),
            'ip_address': '192.168.1.1',
            'user_agent': 'Test User Agent',
            'metadata': None
        }]
        mock_execute.return_value = mock_result
        
        session_data = self.manager._get_session_data('test_session_123')
        
        self.assertIsNotNone(session_data)
        self.assertEqual(session_data.session_id, 'test_session_123')
        self.assertEqual(session_data.user_id, 123)
        self.assertEqual(session_data.session_type, SessionType.REGISTRATION)
        self.assertEqual(session_data.status, SessionStatus.ACTIVE)
    
    @patch('registration_session_manager.execute_query')
    def test_get_session_data_not_found(self, mock_execute):
        """Test session data retrieval for non-existent session"""
        mock_execute.return_value = []
        
        session_data = self.manager._get_session_data('invalid_session')
        
        self.assertIsNone(session_data)
    
    @patch('registration_session_manager.execute_query')
    def test_get_active_sessions_for_user_success(self, mock_execute):
        """Test successful active sessions retrieval for user"""
        mock_result = [{
            'session_id': 'session1',
            'user_id': 123,
            'session_type': 'registration',
            'status': 'active',
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24),
            'last_activity': datetime.now(),
            'ip_address': '192.168.1.1',
            'user_agent': 'Test User Agent',
            'metadata': None
        }]
        mock_execute.return_value = mock_result
        
        sessions = self.manager._get_active_sessions_for_user(123)
        
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].session_id, 'session1')
        self.assertEqual(sessions[0].user_id, 123)
    
    @patch('registration_session_manager.execute_query')
    def test_update_session_status_success(self, mock_execute):
        """Test successful session status update"""
        mock_execute.return_value = True
        
        success = self.manager._update_session_status(
            'test_session_123',
            SessionStatus.COMPLETED,
            {'completion_reason': 'success'}
        )
        
        self.assertTrue(success)
    
    @patch('registration_session_manager.execute_query')
    def test_update_last_activity_success(self, mock_execute):
        """Test successful last activity update"""
        mock_execute.return_value = True
        
        success = self.manager._update_last_activity('test_session_123')
        
        self.assertTrue(success)
    
    @patch('registration_session_manager.execute_query')
    def test_invalidate_session_internal_success(self, mock_execute):
        """Test successful internal session invalidation"""
        mock_execute.return_value = True
        
        success = self.manager._invalidate_session('test_session_123', 'test_reason')
        
        self.assertTrue(success)
    
    def test_get_resume_url_registration(self):
        """Test resume URL generation for registration session"""
        url = self.manager._get_resume_url(SessionType.REGISTRATION, 123)
        self.assertEqual(url, '/signup/resume/123')
    
    def test_get_resume_url_email_verification(self):
        """Test resume URL generation for email verification session"""
        url = self.manager._get_resume_url(SessionType.EMAIL_VERIFICATION, 123)
        self.assertEqual(url, '/email-verification/123')
    
    def test_get_resume_url_strava_connection(self):
        """Test resume URL generation for Strava connection session"""
        url = self.manager._get_resume_url(SessionType.STRAVA_CONNECTION, 123)
        self.assertEqual(url, '/strava-connect/123')
    
    def test_get_resume_url_onboarding(self):
        """Test resume URL generation for onboarding session"""
        url = self.manager._get_resume_url(SessionType.ONBOARDING, 123)
        self.assertEqual(url, '/onboarding/123')
    
    def test_get_resume_url_unknown(self):
        """Test resume URL generation for unknown session type"""
        url = self.manager._get_resume_url(SessionType.REGISTRATION, 123)  # Using registration as fallback
        self.assertEqual(url, '/signup/resume/123')


if __name__ == '__main__':
    unittest.main()
