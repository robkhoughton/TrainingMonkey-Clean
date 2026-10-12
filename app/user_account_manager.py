"""
User Account Manager Module

Account status and onboarding progress tracking for existing users.
Accounts are created through Strava OAuth (see /oauth-callback in strava_app.py).
"""

import logging
from datetime import datetime
from typing import Dict

from legal_compliance import get_legal_compliance_tracker
from db_utils import execute_query

logger = logging.getLogger(__name__)

class UserAccountManager:
    """Manages account status and onboarding progress for existing users"""
    
    def __init__(self):
        self.compliance_tracker = get_legal_compliance_tracker()
    
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
                SET %s = %s
                WHERE id = %s
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
                SET %s = %s
                WHERE id = %s
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
                WHERE id = %s
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
            step: New onboarding step (must be valid OnboardingStep enum value)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate step is a valid OnboardingStep enum value
            from onboarding_manager import OnboardingStep
            try:
                valid_step = OnboardingStep(step)
            except ValueError:
                logger.error(f"Invalid onboarding step: {step}. Must be one of: {[s.value for s in OnboardingStep]}")
                return False
            
            # Use proper SQL syntax with fixed column names
            query = """
                UPDATE user_settings 
                SET onboarding_step = %s, 
                    last_onboarding_activity = %s
                WHERE id = %s
            """
            
            current_time = datetime.now()
            execute_query(query, (valid_step.value, current_time, user_id))
            
            logger.info(f"Updated onboarding progress for user {user_id}: {valid_step.value}")
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
            # Update onboarding step and activate account with proper SQL syntax
            query = """
                UPDATE user_settings 
                SET onboarding_step = %s, 
                    account_status = %s,
                    onboarding_completed_at = %s,
                    onboarding_completed = true
                WHERE id = %s
            """
            
            current_time = datetime.now()
            execute_query(query, ('completed', 'active', current_time, user_id))
            
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
