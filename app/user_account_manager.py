"""
User Account Manager Module

This module handles the complete user account creation process, integrating with:
- Registration validation
- Legal compliance tracking
- Password generation
- Account status management
- Onboarding progress tracking
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from flask import request
from werkzeug.security import generate_password_hash

# Import existing modules
from auth import User
from registration_validation import registration_validator
from legal_compliance import get_legal_compliance_tracker
from legal_document_versioning import get_current_legal_versions
from db_utils import execute_query, get_db_connection

logger = logging.getLogger(__name__)

class UserAccountManager:
    """Manages user account creation and status tracking"""
    
    def __init__(self):
        self.compliance_tracker = get_legal_compliance_tracker()
    
    def create_new_user_account(self, email: str, password: str, 
                               legal_acceptances: Dict[str, bool] = None) -> Tuple[bool, Optional[int], str]:
        """
        Create a new user account with full registration process
        
        Args:
            email: User's email address
            password: User's password
            legal_acceptances: Dictionary of legal document acceptances
            
        Returns:
            Tuple of (success, user_id, error_message)
        """
        try:
            # Validate input
            if not email or not password:
                return False, None, "Email and password are required"
            
            # Check if user already exists
            existing_user = User.get_by_email(email)
            if existing_user:
                return False, None, "An account with this email address already exists"
            
            # Get current legal versions
            current_versions = get_current_legal_versions()
            
            # Create user account with initial status
            user_id = self._create_user_record(email, password, current_versions)
            
            if not user_id:
                return False, None, "Failed to create user account"
            
            # Log legal acceptances if provided
            if legal_acceptances:
                self._log_legal_acceptances(user_id, legal_acceptances, current_versions)
            
            # Initialize onboarding progress
            self._initialize_onboarding_progress(user_id)
            
            # Log successful account creation
            logger.info(f"Successfully created new user account: {email} (ID: {user_id})")
            
            return True, user_id, ""
            
        except Exception as e:
            logger.error(f"Error creating user account: {str(e)}")
            return False, None, "Unable to create account. Please try again."
    
    def _create_user_record(self, email: str, password: str, 
                           legal_versions: Dict[str, str]) -> Optional[int]:
        """
        Create the user record in the database
        
        Args:
            email: User's email address
            password: User's password
            legal_versions: Current legal document versions
            
        Returns:
            User ID if successful, None otherwise
        """
        try:
            password_hash = generate_password_hash(password)
            current_time = datetime.now()
            
            # Build the insert query with all new fields
            query = """
                INSERT INTO user_settings (
                    email, password_hash, account_status, onboarding_step,
                    terms_accepted_version, privacy_accepted_version, disclaimer_accepted_version,
                    terms_accepted_date, privacy_accepted_date, disclaimer_accepted_date,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """
            
            params = (
                email, password_hash, 'pending', 'registration_complete',
                legal_versions.get('terms'), legal_versions.get('privacy'), legal_versions.get('disclaimer'),
                current_time, current_time, current_time,
                current_time, current_time
            )
            
            result = execute_query(query, params, fetch=True)
            
            if result and len(result) > 0:
                return result[0]['id']
            else:
                logger.error("No user ID returned from database insert")
                return None
                
        except Exception as e:
            logger.error(f"Database error creating user record: {str(e)}")
            return None
    
    def _log_legal_acceptances(self, user_id: int, legal_acceptances: Dict[str, bool], 
                              current_versions: Dict[str, str]):
        """
        Log legal document acceptances for the user
        
        Args:
            user_id: User ID
            legal_acceptances: Dictionary of legal acceptances
            current_versions: Current legal document versions
        """
        try:
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            for doc_type, accepted in legal_acceptances.items():
                if accepted and doc_type in current_versions:
                    self.compliance_tracker.log_user_legal_acceptance(
                        user_id, doc_type, current_versions[doc_type],
                        ip_address, user_agent
                    )
                    
        except Exception as e:
            logger.error(f"Error logging legal acceptances: {str(e)}")
    
    def _initialize_onboarding_progress(self, user_id: int):
        """
        Initialize onboarding progress for new user
        
        Args:
            user_id: User ID
        """
        try:
            # Set initial onboarding step
            query = """
                UPDATE user_settings 
                SET onboarding_step = ?, updated_at = ?
                WHERE id = ?
            """
            
            current_time = datetime.now()
            execute_query(query, ('registration_complete', current_time, user_id))
            
            logger.info(f"Initialized onboarding progress for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error initializing onboarding progress: {str(e)}")
    
    def activate_user_account(self, user_id: int) -> bool:
        """
        Activate a user account (change status from 'pending' to 'active')
        
        Args:
            user_id: User ID to activate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE user_settings 
                SET account_status = ?, updated_at = ?
                WHERE id = ?
            """
            
            current_time = datetime.now()
            execute_query(query, ('active', current_time, user_id))
            
            logger.info(f"Activated user account: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating user account: {str(e)}")
            return False
    
    def deactivate_user_account(self, user_id: int, reason: str = 'manual_deactivation') -> bool:
        """
        Deactivate a user account
        
        Args:
            user_id: User ID to deactivate
            reason: Reason for deactivation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE user_settings 
                SET account_status = ?, deactivation_reason = ?, updated_at = ?
                WHERE id = ?
            """
            
            current_time = datetime.now()
            execute_query(query, ('inactive', reason, current_time, user_id))
            
            logger.info(f"Deactivated user account: {user_id} (reason: {reason})")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating user account: {str(e)}")
            return False
    
    def get_user_account_status(self, user_id: int) -> Dict:
        """
        Get comprehensive user account status
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with account status information
        """
        try:
            query = """
                SELECT 
                    id, email, account_status, onboarding_step,
                    terms_accepted_version, privacy_accepted_version, disclaimer_accepted_version,
                    terms_accepted_date, privacy_accepted_date, disclaimer_accepted_date,
                    created_at, updated_at
                FROM user_settings 
                WHERE id = ?
            """
            
            result = execute_query(query, (user_id,), fetch=True)
            
            if result and len(result) > 0:
                user_data = dict(result[0])
                
                # Get legal compliance status
                legal_status = self.compliance_tracker.get_user_legal_status(user_id)
                
                return {
                    'user_id': user_data['id'],
                    'email': user_data['email'],
                    'account_status': user_data['account_status'],
                    'onboarding_step': user_data['onboarding_step'],
                    'legal_compliance': legal_status,
                    'created_at': user_data['created_at'],
                    'updated_at': user_data['updated_at']
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting user account status: {str(e)}")
            return {}
    
    def update_onboarding_progress(self, user_id: int, step: str) -> bool:
        """
        Update user's onboarding progress
        
        Args:
            user_id: User ID
            step: New onboarding step
            
        Returns:
            True if successful, False otherwise
        """
        try:
            query = """
                UPDATE user_settings 
                SET onboarding_step = ?, updated_at = ?
                WHERE id = ?
            """
            
            current_time = datetime.now()
            execute_query(query, (step, current_time, user_id))
            
            logger.info(f"Updated onboarding progress for user {user_id}: {step}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating onboarding progress: {str(e)}")
            return False
    
    def complete_onboarding(self, user_id: int) -> bool:
        """
        Mark user's onboarding as complete
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update onboarding step and activate account
            query = """
                UPDATE user_settings 
                SET onboarding_step = ?, account_status = ?, updated_at = ?
                WHERE id = ?
            """
            
            current_time = datetime.now()
            execute_query(query, ('onboarding_complete', 'active', current_time, user_id))
            
            logger.info(f"Completed onboarding for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing onboarding: {str(e)}")
            return False
    
    def get_pending_registrations(self) -> list:
        """
        Get list of pending user registrations
        
        Returns:
            List of pending user registrations
        """
        try:
            query = """
                SELECT 
                    id, email, account_status, onboarding_step, created_at
                FROM user_settings 
                WHERE account_status = 'pending'
                ORDER BY created_at DESC
            """
            
            result = execute_query(query, fetch=True)
            
            if result:
                return [dict(row) for row in result]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error getting pending registrations: {str(e)}")
            return []
    
    def cleanup_expired_registrations(self, days_old: int = 7) -> int:
        """
        Clean up expired pending registrations
        
        Args:
            days_old: Number of days after which to consider registrations expired
            
        Returns:
            Number of registrations cleaned up
        """
        try:
            query = """
                DELETE FROM user_settings 
                WHERE account_status = 'pending' 
                AND created_at < NOW() - INTERVAL '{} days'
            """.format(days_old)
            
            result = execute_query(query)
            
            if result:
                logger.info(f"Cleaned up {result} expired registrations")
                return result
            else:
                return 0
                
        except Exception as e:
            logger.error(f"Error cleaning up expired registrations: {str(e)}")
            return 0


# Global instance
user_account_manager = UserAccountManager()
