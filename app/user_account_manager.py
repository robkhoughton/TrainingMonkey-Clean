"""
User Account Manager Module

Onboarding completion for existing users.
Accounts are created through Strava OAuth (see /oauth-callback in strava_app.py).
"""

import logging
from datetime import datetime

from db_utils import execute_query

logger = logging.getLogger(__name__)

class UserAccountManager:
    """Marks onboarding complete for users created via Strava OAuth"""
    
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


# Global instance
user_account_manager = UserAccountManager()
