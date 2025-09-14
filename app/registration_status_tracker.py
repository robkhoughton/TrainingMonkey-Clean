"""
Registration Status Tracker Module

This module handles comprehensive tracking of user registration status throughout
the registration lifecycle, including pending registrations, activation workflows,
and status transitions with detailed logging and monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
from flask import request, session
from dataclasses import dataclass

from db_utils import execute_query
from user_account_manager import user_account_manager

logger = logging.getLogger(__name__)


class RegistrationStatus(Enum):
    """Enumeration of registration statuses"""
    PENDING = 'pending'
    EMAIL_VERIFIED = 'email_verified'
    STRAVA_CONNECTED = 'strava_connected'
    ONBOARDING_COMPLETE = 'onboarding_complete'
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    EXPIRED = 'expired'


class RegistrationStep(Enum):
    """Enumeration of registration steps"""
    REGISTRATION_STARTED = 'registration_started'
    ACCOUNT_CREATED = 'account_created'
    EMAIL_VERIFICATION_SENT = 'email_verification_sent'
    EMAIL_VERIFIED = 'email_verified'
    STRAVA_CONNECTED = 'strava_connected'
    ONBOARDING_STARTED = 'onboarding_started'
    ONBOARDING_COMPLETE = 'onboarding_complete'
    ACCOUNT_ACTIVATED = 'account_activated'


@dataclass
class RegistrationEvent:
    """Data class for registration events"""
    user_id: int
    step: RegistrationStep
    status: RegistrationStatus
    timestamp: datetime
    ip_address: str
    user_agent: str
    metadata: Dict = None


class RegistrationStatusTracker:
    """Tracks and manages registration status throughout the registration process"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def start_registration_tracking(self, user_id: int) -> bool:
        """
        Start tracking registration process for a new user
        
        Args:
            user_id: User ID to track
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log registration start event
            self._log_registration_event(
                user_id, 
                RegistrationStep.REGISTRATION_STARTED,
                RegistrationStatus.PENDING
            )
            
            # Update user status to pending
            success = user_account_manager.update_onboarding_progress(
                user_id, 'registration_started'
            )
            
            if success:
                self.logger.info(f"Started registration tracking for user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to update onboarding progress for user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting registration tracking: {str(e)}")
            return False
    
    def track_account_creation(self, user_id: int) -> bool:
        """
        Track successful account creation
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log account creation event
            self._log_registration_event(
                user_id,
                RegistrationStep.ACCOUNT_CREATED,
                RegistrationStatus.PENDING
            )
            
            # Update onboarding progress
            success = user_account_manager.update_onboarding_progress(
                user_id, 'account_created'
            )
            
            if success:
                self.logger.info(f"Tracked account creation for user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to update onboarding progress for user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error tracking account creation: {str(e)}")
            return False
    
    def track_email_verification_sent(self, user_id: int, email: str) -> bool:
        """
        Track when email verification is sent
        
        Args:
            user_id: User ID
            email: Email address verification was sent to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log email verification sent event
            self._log_registration_event(
                user_id,
                RegistrationStep.EMAIL_VERIFICATION_SENT,
                RegistrationStatus.PENDING,
                metadata={'email': email}
            )
            
            # Update onboarding progress
            success = user_account_manager.update_onboarding_progress(
                user_id, 'email_verification_sent'
            )
            
            if success:
                self.logger.info(f"Tracked email verification sent for user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to update onboarding progress for user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error tracking email verification sent: {str(e)}")
            return False
    
    def track_email_verification_complete(self, user_id: int) -> bool:
        """
        Track successful email verification
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log email verification complete event
            self._log_registration_event(
                user_id,
                RegistrationStep.EMAIL_VERIFIED,
                RegistrationStatus.EMAIL_VERIFIED
            )
            
            # Update onboarding progress
            success = user_account_manager.update_onboarding_progress(
                user_id, 'email_verified'
            )
            
            if success:
                self.logger.info(f"Tracked email verification complete for user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to update onboarding progress for user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error tracking email verification complete: {str(e)}")
            return False
    
    def track_strava_connection(self, user_id: int, strava_user_id: str = None) -> bool:
        """
        Track successful Strava connection
        
        Args:
            user_id: User ID
            strava_user_id: Strava user ID (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log Strava connection event
            metadata = {}
            if strava_user_id:
                metadata['strava_user_id'] = strava_user_id
                
            self._log_registration_event(
                user_id,
                RegistrationStep.STRAVA_CONNECTED,
                RegistrationStatus.STRAVA_CONNECTED,
                metadata=metadata
            )
            
            # Update onboarding progress
            success = user_account_manager.update_onboarding_progress(
                user_id, 'strava_connected'
            )
            
            if success:
                self.logger.info(f"Tracked Strava connection for user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to update onboarding progress for user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error tracking Strava connection: {str(e)}")
            return False
    
    def track_onboarding_start(self, user_id: int) -> bool:
        """
        Track onboarding process start
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log onboarding start event
            self._log_registration_event(
                user_id,
                RegistrationStep.ONBOARDING_STARTED,
                RegistrationStatus.STRAVA_CONNECTED
            )
            
            # Update onboarding progress
            success = user_account_manager.update_onboarding_progress(
                user_id, 'onboarding_started'
            )
            
            if success:
                self.logger.info(f"Tracked onboarding start for user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to update onboarding progress for user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error tracking onboarding start: {str(e)}")
            return False
    
    def track_onboarding_complete(self, user_id: int) -> bool:
        """
        Track onboarding completion
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Log onboarding complete event
            self._log_registration_event(
                user_id,
                RegistrationStep.ONBOARDING_COMPLETE,
                RegistrationStatus.ONBOARDING_COMPLETE
            )
            
            # Complete onboarding and activate account
            success = user_account_manager.complete_onboarding(user_id)
            
            if success:
                # Log account activation event
                self._log_registration_event(
                    user_id,
                    RegistrationStep.ACCOUNT_ACTIVATED,
                    RegistrationStatus.ACTIVE
                )
                
                self.logger.info(f"Tracked onboarding completion and account activation for user {user_id}")
                return True
            else:
                self.logger.error(f"Failed to complete onboarding for user {user_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error tracking onboarding completion: {str(e)}")
            return False
    
    def get_registration_status(self, user_id: int) -> Dict:
        """
        Get comprehensive registration status for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with registration status information
        """
        try:
            # Get account status from user account manager
            account_status = user_account_manager.get_user_account_status(user_id)
            
            if not account_status:
                return {}
            
            # Get registration events
            events = self._get_registration_events(user_id)
            
            # Calculate registration progress
            progress = self._calculate_registration_progress(events)
            
            # Determine current status
            current_status = self._determine_current_status(account_status, events)
            
            return {
                'user_id': user_id,
                'account_status': account_status,
                'registration_events': events,
                'registration_progress': progress,
                'current_status': current_status,
                'is_complete': current_status == RegistrationStatus.ACTIVE.value,
                'next_steps': self._get_next_steps(current_status, events)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting registration status: {str(e)}")
            return {}
    
    def get_pending_registrations_summary(self) -> Dict:
        """
        Get summary of all pending registrations
        
        Returns:
            Dictionary with pending registration statistics
        """
        try:
            # Get all pending registrations
            pending = user_account_manager.get_pending_registrations()
            
            # Group by onboarding step
            step_counts = {}
            total_pending = len(pending)
            
            for registration in pending:
                step = registration.get('onboarding_step', 'unknown')
                step_counts[step] = step_counts.get(step, 0) + 1
            
            # Calculate time-based statistics
            now = datetime.now()
            recent_registrations = 0
            old_registrations = 0
            
            for registration in pending:
                created_at = registration.get('created_at')
                if created_at:
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    
                    days_old = (now - created_at).days
                    if days_old <= 1:
                        recent_registrations += 1
                    elif days_old >= 7:
                        old_registrations += 1
            
            return {
                'total_pending': total_pending,
                'step_breakdown': step_counts,
                'recent_registrations': recent_registrations,
                'old_registrations': old_registrations,
                'completion_rate': self._calculate_completion_rate()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pending registrations summary: {str(e)}")
            return {}
    
    def cleanup_expired_registrations(self, days_old: int = 7) -> int:
        """
        Clean up expired registrations and log cleanup events
        
        Args:
            days_old: Number of days after which to consider registrations expired
            
        Returns:
            Number of registrations cleaned up
        """
        try:
            # Get registrations to be cleaned up
            expired_registrations = self._get_expired_registrations(days_old)
            
            # Log cleanup events for each expired registration
            for registration in expired_registrations:
                self._log_registration_event(
                    registration['id'],
                    RegistrationStep.REGISTRATION_STARTED,  # Placeholder step
                    RegistrationStatus.EXPIRED,
                    metadata={'cleanup_reason': f'Expired after {days_old} days'}
                )
            
            # Perform cleanup
            cleaned_count = user_account_manager.cleanup_expired_registrations(days_old)
            
            self.logger.info(f"Cleaned up {cleaned_count} expired registrations")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up expired registrations: {str(e)}")
            return 0
    
    def _log_registration_event(self, user_id: int, step: RegistrationStep, 
                               status: RegistrationStatus, metadata: Dict = None):
        """
        Log a registration event to the database
        
        Args:
            user_id: User ID
            step: Registration step
            status: Registration status
            metadata: Additional metadata
        """
        try:
            ip_address = request.remote_addr if request else 'unknown'
            user_agent = request.headers.get('User-Agent', 'unknown') if request else 'unknown'
            
            query = """
                INSERT INTO registration_events (
                    user_id, step, status, timestamp, ip_address, user_agent, metadata
                ) VALUES (%s)
            """
            
            params = (
                user_id,
                step.value,
                status.value,
                datetime.now(),
                ip_address,
                user_agent,
                str(metadata) if metadata else None
            )
            
            execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Error logging registration event: {str(e)}")
    
    def _get_registration_events(self, user_id: int) -> List[Dict]:
        """
        Get registration events for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of registration events
        """
        try:
            query = """
                SELECT step, status, timestamp, ip_address, user_agent, metadata
                FROM registration_events
                WHERE user_id = %s
                ORDER BY timestamp ASC
            """
            
            result = execute_query(query, (user_id,), fetch=True)
            
            if result:
                return [dict(row) for row in result]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting registration events: {str(e)}")
            return []
    
    def _calculate_registration_progress(self, events: List[Dict]) -> Dict:
        """
        Calculate registration progress based on events
        
        Args:
            events: List of registration events
            
        Returns:
            Dictionary with progress information
        """
        if not events:
            return {'percentage': 0, 'current_step': 'not_started', 'total_steps': 8}
        
        # Define step order and weights
        step_order = [
            RegistrationStep.REGISTRATION_STARTED.value,
            RegistrationStep.ACCOUNT_CREATED.value,
            RegistrationStep.EMAIL_VERIFICATION_SENT.value,
            RegistrationStep.EMAIL_VERIFIED.value,
            RegistrationStep.STRAVA_CONNECTED.value,
            RegistrationStep.ONBOARDING_STARTED.value,
            RegistrationStep.ONBOARDING_COMPLETE.value,
            RegistrationStep.ACCOUNT_ACTIVATED.value
        ]
        
        completed_steps = [event['step'] for event in events]
        current_step = completed_steps[-1] if completed_steps else 'not_started'
        
        # Calculate percentage
        total_steps = len(step_order)
        completed_count = len(set(completed_steps))
        percentage = min(100, int((completed_count / total_steps) * 100))
        
        return {
            'percentage': percentage,
            'current_step': current_step,
            'total_steps': total_steps,
            'completed_steps': completed_count,
            'step_order': step_order
        }
    
    def _determine_current_status(self, account_status: Dict, events: List[Dict]) -> str:
        """
        Determine current registration status based on account status and events
        
        Args:
            account_status: Account status from user account manager
            events: List of registration events
            
        Returns:
            Current status string
        """
        if not account_status:
            return RegistrationStatus.PENDING.value
        
        # Check if account is active
        if account_status.get('account_status') == 'active':
            return RegistrationStatus.ACTIVE.value
        
        # Check if onboarding is complete
        if account_status.get('onboarding_step') == 'onboarding_complete':
            return RegistrationStatus.ONBOARDING_COMPLETE.value
        
        # Check if Strava is connected
        strava_connected = any(
            event['step'] == RegistrationStep.STRAVA_CONNECTED.value 
            for event in events
        )
        if strava_connected:
            return RegistrationStatus.STRAVA_CONNECTED.value
        
        # Check if email is verified
        email_verified = any(
            event['step'] == RegistrationStep.EMAIL_VERIFIED.value 
            for event in events
        )
        if email_verified:
            return RegistrationStatus.EMAIL_VERIFIED.value
        
        # Default to pending
        return RegistrationStatus.PENDING.value
    
    def _get_next_steps(self, current_status: str, events: List[Dict]) -> List[str]:
        """
        Get next steps for the user based on current status
        
        Args:
            current_status: Current registration status
            events: List of registration events
            
        Returns:
            List of next steps
        """
        next_steps = []
        
        if current_status == RegistrationStatus.PENDING.value:
            next_steps.append("Complete account creation")
            next_steps.append("Verify email address")
        
        elif current_status == RegistrationStatus.EMAIL_VERIFIED.value:
            next_steps.append("Connect Strava account")
        
        elif current_status == RegistrationStatus.STRAVA_CONNECTED.value:
            next_steps.append("Complete onboarding process")
            next_steps.append("Set up training preferences")
        
        elif current_status == RegistrationStatus.ONBOARDING_COMPLETE.value:
            next_steps.append("Account activation pending")
        
        elif current_status == RegistrationStatus.ACTIVE.value:
            next_steps.append("Registration complete!")
        
        return next_steps
    
    def _get_expired_registrations(self, days_old: int) -> List[Dict]:
        """
        Get list of expired registrations
        
        Args:
            days_old: Number of days after which to consider registrations expired
            
        Returns:
            List of expired registrations
        """
        try:
            query = """
                SELECT id, email, created_at
                FROM user_settings
                WHERE account_status = 'pending'
                AND created_at < NOW() - INTERVAL '{} days'
            """.format(days_old)
            
            result = execute_query(query, fetch=True)
            
            if result:
                return [dict(row) for row in result]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting expired registrations: {str(e)}")
            return []
    
    def _calculate_completion_rate(self) -> float:
        """
        Calculate registration completion rate
        
        Returns:
            Completion rate as percentage
        """
        try:
            # Get total registrations in the last 30 days
            query_total = """
                SELECT COUNT(*) as total
                FROM user_settings
                WHERE created_at >= NOW() - INTERVAL '30 days'
            """
            
            # Get completed registrations in the last 30 days
            query_completed = """
                SELECT COUNT(*) as completed
                FROM user_settings
                WHERE created_at >= NOW() - INTERVAL '30 days'
                AND account_status = 'active'
            """
            
            total_result = execute_query(query_total, fetch=True)
            completed_result = execute_query(query_completed, fetch=True)
            
            if total_result and completed_result:
                total = total_result[0]['total']
                completed = completed_result[0]['completed']
                
                if total > 0:
                    return round((completed / total) * 100, 2)
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating completion rate: {str(e)}")
            return 0.0


# Global instance
registration_status_tracker = RegistrationStatusTracker()
