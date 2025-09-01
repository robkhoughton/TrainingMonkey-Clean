"""
Registration Session Manager Module

This module handles session management for pending registrations, allowing users
to resume their registration process where they left off. It includes session
creation, validation, resumption, and cleanup functionality.
"""

import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from enum import Enum
from flask import request, session, current_app
from dataclasses import dataclass

from db_utils import execute_query
from user_account_manager import user_account_manager
from registration_status_tracker import registration_status_tracker

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Enumeration of session statuses"""
    ACTIVE = 'active'
    EXPIRED = 'expired'
    COMPLETED = 'completed'
    INVALIDATED = 'invalidated'


class SessionType(Enum):
    """Enumeration of session types"""
    REGISTRATION = 'registration'
    EMAIL_VERIFICATION = 'email_verification'
    STRAVA_CONNECTION = 'strava_connection'
    ONBOARDING = 'onboarding'


@dataclass
class RegistrationSession:
    """Data class for registration session"""
    session_id: str
    user_id: int
    session_type: SessionType
    status: SessionStatus
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    metadata: Dict = None


class RegistrationSessionManager:
    """Manages registration sessions for pending registrations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_timeout_hours = 24  # Default 24-hour timeout
        self.max_sessions_per_user = 3   # Maximum active sessions per user
    
    def create_registration_session(self, user_id: int, session_type: SessionType, 
                                   metadata: Dict = None) -> Tuple[bool, Optional[str], str]:
        """
        Create a new registration session
        
        Args:
            user_id: User ID
            session_type: Type of session
            metadata: Additional session metadata
            
        Returns:
            Tuple of (success, session_id, error_message)
        """
        try:
            # Check if user exists and is in pending status
            account_status = user_account_manager.get_user_account_status(user_id)
            if not account_status:
                return False, None, "User not found"
            
            if account_status.get('account_status') != 'pending':
                return False, None, "User account is not in pending status"
            
            # Check for existing active sessions
            active_sessions = self._get_active_sessions_for_user(user_id)
            if len(active_sessions) >= self.max_sessions_per_user:
                # Invalidate oldest session
                oldest_session = min(active_sessions, key=lambda s: s.created_at)
                self._invalidate_session(oldest_session.session_id, "Max sessions exceeded")
            
            # Generate session ID
            session_id = self._generate_session_id()
            
            # Set expiration time
            expires_at = datetime.now() + timedelta(hours=self.session_timeout_hours)
            
            # Get request information
            ip_address = request.remote_addr if request else 'unknown'
            user_agent = request.headers.get('User-Agent', 'unknown') if request else 'unknown'
            
            # Create session record
            success = self._create_session_record(
                session_id, user_id, session_type, expires_at, ip_address, user_agent, metadata
            )
            
            if success:
                # Log session creation
                self.logger.info(f"Created registration session {session_id} for user {user_id}")
                
                # Store session ID in Flask session for easy access
                session['registration_session_id'] = session_id
                
                return True, session_id, ""
            else:
                return False, None, "Failed to create session record"
                
        except Exception as e:
            self.logger.error(f"Error creating registration session: {str(e)}")
            return False, None, "Unable to create session"
    
    def validate_session(self, session_id: str) -> Tuple[bool, Optional[RegistrationSession], str]:
        """
        Validate a registration session
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            Tuple of (is_valid, session_data, error_message)
        """
        try:
            # Get session data
            session_data = self._get_session_data(session_id)
            if not session_data:
                return False, None, "Session not found"
            
            # Check if session is active
            if session_data.status != SessionStatus.ACTIVE:
                return False, None, f"Session is {session_data.status.value}"
            
            # Check if session has expired
            if datetime.now() > session_data.expires_at:
                # Mark session as expired
                self._update_session_status(session_id, SessionStatus.EXPIRED)
                return False, None, "Session has expired"
            
            # Update last activity
            self._update_last_activity(session_id)
            
            return True, session_data, ""
            
        except Exception as e:
            self.logger.error(f"Error validating session: {str(e)}")
            return False, None, "Session validation failed"
    
    def resume_registration(self, session_id: str) -> Tuple[bool, Dict, str]:
        """
        Resume registration process for a valid session
        
        Args:
            session_id: Session ID
            
        Returns:
            Tuple of (success, registration_data, error_message)
        """
        try:
            # Validate session
            is_valid, session_data, error = self.validate_session(session_id)
            if not is_valid:
                return False, {}, error
            
            # Get user registration status
            registration_status = registration_status_tracker.get_registration_status(session_data.user_id)
            
            # Get account status
            account_status = user_account_manager.get_user_account_status(session_data.user_id)
            
            # Prepare resume data
            resume_data = {
                'session_id': session_id,
                'session_type': session_data.session_type.value,
                'user_id': session_data.user_id,
                'registration_status': registration_status,
                'account_status': account_status,
                'session_expires_at': session_data.expires_at.isoformat(),
                'resume_url': self._get_resume_url(session_data.session_type, session_data.user_id)
            }
            
            self.logger.info(f"Resumed registration for session {session_id}")
            return True, resume_data, ""
            
        except Exception as e:
            self.logger.error(f"Error resuming registration: {str(e)}")
            return False, {}, "Unable to resume registration"
    
    def complete_session(self, session_id: str, completion_data: Dict = None) -> bool:
        """
        Mark a session as completed
        
        Args:
            session_id: Session ID
            completion_data: Optional completion metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update session status
            success = self._update_session_status(session_id, SessionStatus.COMPLETED, completion_data)
            
            if success:
                # Remove from Flask session
                session.pop('registration_session_id', None)
                
                self.logger.info(f"Completed registration session {session_id}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error completing session: {str(e)}")
            return False
    
    def invalidate_session(self, session_id: str, reason: str = "manual_invalidation") -> bool:
        """
        Invalidate a session
        
        Args:
            session_id: Session ID
            reason: Reason for invalidation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success = self._invalidate_session(session_id, reason)
            
            if success:
                # Remove from Flask session if it matches
                if session.get('registration_session_id') == session_id:
                    session.pop('registration_session_id', None)
                
                self.logger.info(f"Invalidated registration session {session_id} (reason: {reason})")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"Error invalidating session: {str(e)}")
            return False
    
    def get_user_sessions(self, user_id: int) -> List[RegistrationSession]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of user sessions
        """
        try:
            return self._get_active_sessions_for_user(user_id)
        except Exception as e:
            self.logger.error(f"Error getting user sessions: {str(e)}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions
        
        Returns:
            Number of sessions cleaned up
        """
        try:
            query = """
                UPDATE registration_sessions 
                SET status = ?, updated_at = ?
                WHERE status = ? AND expires_at < ?
            """
            
            current_time = datetime.now()
            execute_query(query, (
                SessionStatus.EXPIRED.value,
                current_time,
                SessionStatus.ACTIVE.value,
                current_time
            ))
            
            # Get count of updated sessions
            count_query = """
                SELECT COUNT(*) as count
                FROM registration_sessions
                WHERE status = ? AND updated_at = ?
            """
            
            result = execute_query(count_query, (SessionStatus.EXPIRED.value, current_time), fetch=True)
            
            if result:
                cleaned_count = result[0]['count']
                self.logger.info(f"Cleaned up {cleaned_count} expired sessions")
                return cleaned_count
            else:
                return 0
                
        except Exception as e:
            self.logger.error(f"Error cleaning up expired sessions: {str(e)}")
            return 0
    
    def extend_session(self, session_id: str, hours: int = 24) -> bool:
        """
        Extend session expiration time
        
        Args:
            session_id: Session ID
            hours: Hours to extend by
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate session first
            is_valid, session_data, error = self.validate_session(session_id)
            if not is_valid:
                return False
            
            # Calculate new expiration time
            new_expires_at = datetime.now() + timedelta(hours=hours)
            
            # Update session
            query = """
                UPDATE registration_sessions 
                SET expires_at = ?, updated_at = ?
                WHERE session_id = ?
            """
            
            current_time = datetime.now()
            execute_query(query, (new_expires_at, current_time, session_id))
            
            self.logger.info(f"Extended session {session_id} by {hours} hours")
            return True
            
        except Exception as e:
            self.logger.error(f"Error extending session: {str(e)}")
            return False
    
    def get_session_analytics(self) -> Dict:
        """
        Get session analytics
        
        Returns:
            Dictionary with session statistics
        """
        try:
            # Get total sessions
            total_query = "SELECT COUNT(*) as count FROM registration_sessions"
            total_result = execute_query(total_query, fetch=True)
            total_sessions = total_result[0]['count'] if total_result else 0
            
            # Get active sessions
            active_query = "SELECT COUNT(*) as count FROM registration_sessions WHERE status = ?"
            active_result = execute_query(active_query, (SessionStatus.ACTIVE.value,), fetch=True)
            active_sessions = active_result[0]['count'] if active_result else 0
            
            # Get completed sessions
            completed_query = "SELECT COUNT(*) as count FROM registration_sessions WHERE status = ?"
            completed_result = execute_query(completed_query, (SessionStatus.COMPLETED.value,), fetch=True)
            completed_sessions = completed_result[0]['count'] if completed_result else 0
            
            # Get expired sessions
            expired_query = "SELECT COUNT(*) as count FROM registration_sessions WHERE status = ?"
            expired_result = execute_query(expired_query, (SessionStatus.EXPIRED.value,), fetch=True)
            expired_sessions = expired_result[0]['count'] if expired_result else 0
            
            # Get sessions by type
            type_query = """
                SELECT session_type, COUNT(*) as count
                FROM registration_sessions
                GROUP BY session_type
            """
            type_result = execute_query(type_query, fetch=True)
            sessions_by_type = {row['session_type']: row['count'] for row in type_result} if type_result else {}
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': active_sessions,
                'completed_sessions': completed_sessions,
                'expired_sessions': expired_sessions,
                'sessions_by_type': sessions_by_type,
                'completion_rate': (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting session analytics: {str(e)}")
            return {}
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return secrets.token_urlsafe(32)
    
    def _create_session_record(self, session_id: str, user_id: int, session_type: SessionType,
                              expires_at: datetime, ip_address: str, user_agent: str, 
                              metadata: Dict = None) -> bool:
        """Create session record in database"""
        try:
            query = """
                INSERT INTO registration_sessions (
                    session_id, user_id, session_type, status, created_at, expires_at,
                    last_activity, ip_address, user_agent, metadata, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            current_time = datetime.now()
            params = (
                session_id, user_id, session_type.value, SessionStatus.ACTIVE.value,
                current_time, expires_at, current_time, ip_address, user_agent,
                str(metadata) if metadata else None, current_time
            )
            
            execute_query(query, params)
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating session record: {str(e)}")
            return False
    
    def _get_session_data(self, session_id: str) -> Optional[RegistrationSession]:
        """Get session data from database"""
        try:
            query = """
                SELECT session_id, user_id, session_type, status, created_at, expires_at,
                       last_activity, ip_address, user_agent, metadata
                FROM registration_sessions
                WHERE session_id = ?
            """
            
            result = execute_query(query, (session_id,), fetch=True)
            
            if result and len(result) > 0:
                row = result[0]
                return RegistrationSession(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    session_type=SessionType(row['session_type']),
                    status=SessionStatus(row['status']),
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    last_activity=row['last_activity'],
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    metadata=eval(row['metadata']) if row['metadata'] else None
                )
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting session data: {str(e)}")
            return None
    
    def _get_active_sessions_for_user(self, user_id: int) -> List[RegistrationSession]:
        """Get active sessions for a user"""
        try:
            query = """
                SELECT session_id, user_id, session_type, status, created_at, expires_at,
                       last_activity, ip_address, user_agent, metadata
                FROM registration_sessions
                WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            """
            
            result = execute_query(query, (user_id, SessionStatus.ACTIVE.value), fetch=True)
            
            sessions = []
            for row in result:
                sessions.append(RegistrationSession(
                    session_id=row['session_id'],
                    user_id=row['user_id'],
                    session_type=SessionType(row['session_type']),
                    status=SessionStatus(row['status']),
                    created_at=row['created_at'],
                    expires_at=row['expires_at'],
                    last_activity=row['last_activity'],
                    ip_address=row['ip_address'],
                    user_agent=row['user_agent'],
                    metadata=eval(row['metadata']) if row['metadata'] else None
                ))
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error getting active sessions for user: {str(e)}")
            return []
    
    def _update_session_status(self, session_id: str, status: SessionStatus, 
                              metadata: Dict = None) -> bool:
        """Update session status"""
        try:
            query = """
                UPDATE registration_sessions 
                SET status = ?, updated_at = ?, metadata = ?
                WHERE session_id = ?
            """
            
            current_time = datetime.now()
            metadata_str = str(metadata) if metadata else None
            
            execute_query(query, (status.value, current_time, metadata_str, session_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating session status: {str(e)}")
            return False
    
    def _update_last_activity(self, session_id: str) -> bool:
        """Update session last activity time"""
        try:
            query = """
                UPDATE registration_sessions 
                SET last_activity = ?, updated_at = ?
                WHERE session_id = ?
            """
            
            current_time = datetime.now()
            execute_query(query, (current_time, current_time, session_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating last activity: {str(e)}")
            return False
    
    def _invalidate_session(self, session_id: str, reason: str) -> bool:
        """Invalidate a session"""
        try:
            query = """
                UPDATE registration_sessions 
                SET status = ?, updated_at = ?, metadata = ?
                WHERE session_id = ?
            """
            
            current_time = datetime.now()
            metadata = {'invalidation_reason': reason}
            
            execute_query(query, (SessionStatus.INVALIDATED.value, current_time, str(metadata), session_id))
            return True
            
        except Exception as e:
            self.logger.error(f"Error invalidating session: {str(e)}")
            return False
    
    def _get_resume_url(self, session_type: SessionType, user_id: int) -> str:
        """Get resume URL based on session type"""
        if session_type == SessionType.REGISTRATION:
            return f"/signup/resume/{user_id}"
        elif session_type == SessionType.EMAIL_VERIFICATION:
            return f"/email-verification/{user_id}"
        elif session_type == SessionType.STRAVA_CONNECTION:
            return f"/strava-connect/{user_id}"
        elif session_type == SessionType.ONBOARDING:
            return f"/onboarding/{user_id}"
        else:
            return f"/dashboard/{user_id}"


# Global instance
registration_session_manager = RegistrationSessionManager()
