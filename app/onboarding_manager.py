"""
Onboarding Manager Module

This module manages the progressive onboarding system for new users, including:
- Tiered feature unlocking logic
- Onboarding progress tracking
- Tutorial system management
- Progressive user experience
- Onboarding analytics and optimization
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from db_utils import get_db_connection, execute_query

logger = logging.getLogger(__name__)


class OnboardingStep(Enum):
    """Enumeration of onboarding steps"""
    WELCOME = 'welcome'
    STRAVA_CONNECTED = 'strava_connected'
    FIRST_ACTIVITY = 'first_activity'
    DATA_SYNC = 'data_sync'
    DASHBOARD_INTRO = 'dashboard_intro'
    FEATURES_TOUR = 'features_tour'
    GOALS_SETUP = 'goals_setup'
    FIRST_RECOMMENDATION = 'first_recommendation'
    JOURNAL_INTRO = 'journal_intro'
    COMPLETED = 'completed'


class FeatureTier(Enum):
    """Enumeration of feature tiers for progressive unlocking"""
    BASIC = 'basic'
    INTERMEDIATE = 'intermediate'
    ADVANCED = 'advanced'
    EXPERT = 'expert'


@dataclass
class OnboardingProgress:
    """Data class for onboarding progress tracking"""
    user_id: int
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep]
    unlocked_features: List[str]
    progress_percentage: float
    last_activity: datetime
    started_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class FeatureUnlock:
    """Data class for feature unlock requirements"""
    feature_name: str
    tier: FeatureTier
    required_steps: List[OnboardingStep]
    required_activities: int
    required_days: int
    description: str
    tutorial_available: bool


class OnboardingManager:
    """
    Manages progressive onboarding system with tiered feature unlocking
    and comprehensive progress tracking.
    """
    
    def __init__(self):
        """Initialize the onboarding manager with feature definitions"""
        self.feature_definitions = self._initialize_feature_definitions()
        self.step_requirements = self._initialize_step_requirements()
    
    def _initialize_feature_definitions(self) -> Dict[str, FeatureUnlock]:
        """Initialize feature unlock definitions"""
        return {
            'dashboard_basic': FeatureUnlock(
                feature_name='Basic Dashboard',
                tier=FeatureTier.BASIC,
                required_steps=[OnboardingStep.WELCOME],
                required_activities=0,
                required_days=0,
                description='View basic training metrics and activity summary',
                tutorial_available=True
            ),
            'dashboard_advanced': FeatureUnlock(
                feature_name='Advanced Dashboard',
                tier=FeatureTier.INTERMEDIATE,
                required_steps=[OnboardingStep.DASHBOARD_INTRO, OnboardingStep.FIRST_ACTIVITY],
                required_activities=1,
                required_days=1,
                description='Access to ACWR, divergence analysis, and trend charts',
                tutorial_available=True
            ),
            'recommendations': FeatureUnlock(
                feature_name='AI Recommendations',
                tier=FeatureTier.INTERMEDIATE,
                required_steps=[OnboardingStep.FIRST_RECOMMENDATION, OnboardingStep.DATA_SYNC],
                required_activities=3,
                required_days=3,
                description='Personalized training recommendations and insights',
                tutorial_available=True
            ),
            'journal': FeatureUnlock(
                feature_name='Training Journal',
                tier=FeatureTier.ADVANCED,
                required_steps=[OnboardingStep.JOURNAL_INTRO, OnboardingStep.FEATURES_TOUR],
                required_activities=5,
                required_days=5,
                description='Daily training journal with AI analysis and alignment scoring',
                tutorial_available=True
            ),
            'advanced_analytics': FeatureUnlock(
                feature_name='Advanced Analytics',
                tier=FeatureTier.EXPERT,
                required_steps=[OnboardingStep.COMPLETED],
                required_activities=10,
                required_days=7,
                description='Deep analytics, pattern recognition, and predictive insights',
                tutorial_available=False
            ),
            'custom_goals': FeatureUnlock(
                feature_name='Custom Goals',
                tier=FeatureTier.ADVANCED,
                required_steps=[OnboardingStep.GOALS_SETUP],
                required_activities=3,
                required_days=3,
                description='Set and track custom training goals and milestones',
                tutorial_available=True
            )
        }
    
    def _initialize_step_requirements(self) -> Dict[OnboardingStep, Dict[str, Any]]:
        """Initialize step completion requirements"""
        return {
            OnboardingStep.WELCOME: {
                'description': 'Welcome and account setup',
                'auto_complete': True,
                'required_actions': []
            },
            OnboardingStep.STRAVA_CONNECTED: {
                'description': 'Connect Strava account',
                'auto_complete': False,
                'required_actions': ['strava_oauth_completed']
            },
            OnboardingStep.FIRST_ACTIVITY: {
                'description': 'Complete first activity sync',
                'auto_complete': False,
                'required_actions': ['activity_count > 0']
            },
            OnboardingStep.DATA_SYNC: {
                'description': 'Sync training data',
                'auto_complete': False,
                'required_actions': ['activity_count >= 3']
            },
            OnboardingStep.DASHBOARD_INTRO: {
                'description': 'Dashboard introduction tour',
                'auto_complete': False,
                'required_actions': ['user_action: dashboard_tour_completed']
            },
            OnboardingStep.FEATURES_TOUR: {
                'description': 'Features overview tour',
                'auto_complete': False,
                'required_actions': ['user_action: features_tour_completed']
            },
            OnboardingStep.GOALS_SETUP: {
                'description': 'Set up training goals',
                'auto_complete': False,
                'required_actions': ['user_action: goals_configured']
            },
            OnboardingStep.FIRST_RECOMMENDATION: {
                'description': 'Receive first AI recommendation',
                'auto_complete': False,
                'required_actions': ['recommendation_generated']
            },
            OnboardingStep.JOURNAL_INTRO: {
                'description': 'Journal introduction and setup',
                'auto_complete': False,
                'required_actions': ['user_action: journal_tour_completed']
            },
            OnboardingStep.COMPLETED: {
                'description': 'Onboarding completed',
                'auto_complete': False,
                'required_actions': ['all_previous_steps_completed']
            }
        }
    
    def start_onboarding(self, user_id: int) -> bool:
        """
        Start onboarding process for a new user
        
        Args:
            user_id: User ID to start onboarding for
            
        Returns:
            True if successfully started, False otherwise
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Initialize onboarding progress - PostgreSQL syntax
                cursor.execute("""
                    UPDATE user_settings 
                    SET onboarding_step = %s, 
                        onboarding_completed_at = NULL,
                        last_onboarding_activity = %s
                    WHERE user_id = %s
                """, (OnboardingStep.WELCOME.value, datetime.now(), user_id))
                
                # Log onboarding start
                self._log_onboarding_event(user_id, 'onboarding_started', {
                    'step': OnboardingStep.WELCOME.value,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"Started onboarding for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error starting onboarding for user {user_id}: {str(e)}")
            return False
    
    def get_onboarding_progress(self, user_id: int) -> Optional[OnboardingProgress]:
        """
        Get current onboarding progress for a user
        
        Args:
            user_id: User ID to get progress for
            
        Returns:
            OnboardingProgress object or None if error
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        SELECT onboarding_step, onboarding_completed_at, 
                               last_onboarding_activity, created_at
                        FROM user_settings 
                        WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT onboarding_step, onboarding_completed_at, 
                               last_onboarding_activity, created_at
                        FROM user_settings 
                        WHERE user_id = %s
                    """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                onboarding_step, completed_at, last_activity, created_at = result
                
                # Get completed steps from features_unlocked
                completed_steps = self._get_completed_steps(user_id)
                
                # Calculate progress percentage
                total_steps = len(OnboardingStep)
                progress_percentage = (len(completed_steps) / total_steps) * 100
                
                # Get unlocked features
                unlocked_features = self._get_unlocked_features(user_id)
                
                return OnboardingProgress(
                    user_id=user_id,
                    current_step=OnboardingStep(onboarding_step) if onboarding_step else OnboardingStep.WELCOME,
                    completed_steps=completed_steps,
                    unlocked_features=unlocked_features,
                    progress_percentage=progress_percentage,
                    last_activity=last_activity or created_at,
                    started_at=created_at,
                    completed_at=completed_at
                )
                
        except Exception as e:
            logger.error(f"Error getting onboarding progress for user {user_id}: {str(e)}")
            return None
    
    def complete_onboarding_step(self, user_id: int, step: OnboardingStep) -> bool:
        """
        Mark an onboarding step as completed
        
        Args:
            user_id: User ID
            step: Step to mark as completed
            
        Returns:
            True if successfully completed, False otherwise
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Update onboarding step
                # PostgreSQL syntax
                    cursor.execute("""
                        UPDATE user_settings 
                        SET onboarding_step = %s, 
                            last_onboarding_activity = %s
                        WHERE user_id = %s
                    """, (step.value, datetime.now(), user_id))
                else:
                    cursor.execute("""
                        UPDATE user_settings 
                        SET %s = %s
                        WHERE user_id = %s
                    """, (step.value, datetime.now(), user_id))
                
                # Log step completion
                self._log_onboarding_event(user_id, 'step_completed', {
                    'step': step.value,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Check if onboarding is complete
                if step == OnboardingStep.COMPLETED:
                    self._complete_onboarding(user_id)
                
                logger.info(f"Completed onboarding step {step.value} for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error completing onboarding step {step.value} for user {user_id}: {str(e)}")
            return False
    
    def check_feature_unlock(self, user_id: int, feature_name: str) -> bool:
        """
        Check if a user has unlocked a specific feature
        
        Args:
            user_id: User ID to check
            feature_name: Name of feature to check
            
        Returns:
            True if feature is unlocked, False otherwise
        """
        try:
            # Get feature definition
            feature_def = self.feature_definitions.get(feature_name)
            if not feature_def:
                logger.warning(f"Unknown feature: {feature_name}")
                return False
            
            # Get user's onboarding progress
            progress = self.get_onboarding_progress(user_id)
            if not progress:
                return False
            
            # Check step requirements
            for required_step in feature_def.required_steps:
                if required_step not in progress.completed_steps:
                    return False
            
            # Check activity requirements
            activity_count = self._get_user_activity_count(user_id)
            if activity_count < feature_def.required_activities:
                return False
            
            # Check days requirements
            days_since_start = (datetime.now() - progress.started_at).days
            if days_since_start < feature_def.required_days:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking feature unlock for user {user_id}, feature {feature_name}: {str(e)}")
            return False
    
    def unlock_feature(self, user_id: int, feature_name: str) -> bool:
        """
        Unlock a feature for a user
        
        Args:
            user_id: User ID
            feature_name: Name of feature to unlock
            
        Returns:
            True if successfully unlocked, False otherwise
        """
        try:
            # Check if feature can be unlocked
            if not self.check_feature_unlock(user_id, feature_name):
                logger.warning(f"Cannot unlock feature {feature_name} for user {user_id} - requirements not met")
                return False
            
            # Add to unlocked features
            unlocked_features = self._get_unlocked_features(user_id)
            if feature_name not in unlocked_features:
                unlocked_features.append(feature_name)
                
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # PostgreSQL syntax
                        cursor.execute("""
                            UPDATE user_settings 
                            SET features_unlocked = %s
                            WHERE user_id = %s
                        """, (json.dumps(unlocked_features), user_id))
                    else:
                        cursor.execute("""
                            UPDATE user_settings 
                            SET %s = %s
                            WHERE user_id = %s
                        """, (json.dumps(unlocked_features), user_id))
                
                # Log feature unlock
                self._log_onboarding_event(user_id, 'feature_unlocked', {
                    'feature': feature_name,
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"Unlocked feature {feature_name} for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error unlocking feature {feature_name} for user {user_id}: {str(e)}")
            return False
    
    def get_available_features(self, user_id: int) -> List[FeatureUnlock]:
        """
        Get list of features available to a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of available FeatureUnlock objects
        """
        try:
            available_features = []
            
            for feature_name, feature_def in self.feature_definitions.items():
                if self.check_feature_unlock(user_id, feature_name):
                    available_features.append(feature_def)
            
            return available_features
            
        except Exception as e:
            logger.error(f"Error getting available features for user {user_id}: {str(e)}")
            return []
    
    def get_next_onboarding_step(self, user_id: int) -> Optional[OnboardingStep]:
        """
        Get the next recommended onboarding step for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Next OnboardingStep or None if completed
        """
        try:
            progress = self.get_onboarding_progress(user_id)
            if not progress:
                return None
            
            # Check each step in order
            for step in OnboardingStep:
                if step not in progress.completed_steps:
                    # Check if step requirements are met
                    if self._can_complete_step(user_id, step):
                        return step
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting next onboarding step for user {user_id}: {str(e)}")
            return None
    
    def _get_completed_steps(self, user_id: int) -> List[OnboardingStep]:
        """Get list of completed onboarding steps for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        SELECT features_unlocked FROM user_settings WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT features_unlocked FROM user_settings WHERE user_id = %s
                    """, (user_id,))
                
                result = cursor.fetchone()
                if not result or not result[0]:
                    return []
                
                # Parse completed steps from features_unlocked
                features_unlocked = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                completed_steps = []
                
                # Map features to steps (simplified mapping)
                step_mapping = {
                    'dashboard_basic': [OnboardingStep.WELCOME],
                    'dashboard_advanced': [OnboardingStep.DASHBOARD_INTRO, OnboardingStep.FIRST_ACTIVITY],
                    'recommendations': [OnboardingStep.FIRST_RECOMMENDATION],
                    'journal': [OnboardingStep.JOURNAL_INTRO],
                    'custom_goals': [OnboardingStep.GOALS_SETUP]
                }
                
                for feature in features_unlocked:
                    if feature in step_mapping:
                        completed_steps.extend(step_mapping[feature])
                
                return list(set(completed_steps))  # Remove duplicates
                
        except Exception as e:
            logger.error(f"Error getting completed steps for user {user_id}: {str(e)}")
            return []
    
    def _get_unlocked_features(self, user_id: int) -> List[str]:
        """Get list of unlocked features for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        SELECT features_unlocked FROM user_settings WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT features_unlocked FROM user_settings WHERE user_id = %s
                    """, (user_id,))
                
                result = cursor.fetchone()
                if not result or not result[0]:
                    return []
                
                return json.loads(result[0]) if isinstance(result[0], str) else result[0]
                
        except Exception as e:
            logger.error(f"Error getting unlocked features for user {user_id}: {str(e)}")
            return []
    
    def _get_user_activity_count(self, user_id: int) -> int:
        """Get total activity count for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        SELECT COUNT(*) FROM activities WHERE user_id = %s
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT COUNT(*) FROM activities WHERE user_id = %s
                    """, (user_id,))
                
                result = cursor.fetchone()
                return result[0] if result else 0
                
        except Exception as e:
            logger.error(f"Error getting activity count for user {user_id}: {str(e)}")
            return 0
    
    def _can_complete_step(self, user_id: int, step: OnboardingStep) -> bool:
        """Check if a user can complete a specific step"""
        try:
            step_req = self.step_requirements.get(step)
            if not step_req:
                return False
            
            # Check auto-complete steps
            if step_req['auto_complete']:
                return True
            
            # Check required actions
            for action in step_req['required_actions']:
                if action == 'strava_oauth_completed':
                    # Check if Strava is connected
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # PostgreSQL syntax
                            cursor.execute("""
                                SELECT strava_athlete_id FROM user_settings WHERE user_id = %s
                            """, (user_id,))
                        else:
                            cursor.execute("""
                                SELECT strava_athlete_id FROM user_settings WHERE user_id = %s
                            """, (user_id,))
                        
                        result = cursor.fetchone()
                        if not result or not result[0]:
                            return False
                
                elif action.startswith('activity_count'):
                    # Parse activity count requirement
                    if '>' in action:
                        required_count = int(action.split('>')[1].strip())
                        actual_count = self._get_user_activity_count(user_id)
                        if actual_count <= required_count:
                            return False
                    elif '>=' in action:
                        required_count = int(action.split('>=')[1].strip())
                        actual_count = self._get_user_activity_count(user_id)
                        if actual_count < required_count:
                            return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking step completion for user {user_id}, step {step.value}: {str(e)}")
            return False
    
    def _complete_onboarding(self, user_id: int) -> bool:
        """Mark onboarding as completed for a user"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        UPDATE user_settings 
                        SET onboarding_completed_at = %s,
                            account_status = 'active'
                        WHERE user_id = %s
                    """, (datetime.now(), user_id))
                else:
                    cursor.execute("""
                        UPDATE user_settings 
                        SET %s = %s,
                            account_status = 'active'
                        WHERE user_id = %s
                    """, (datetime.now(), user_id))
                
                # Log onboarding completion
                self._log_onboarding_event(user_id, 'onboarding_completed', {
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"Completed onboarding for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error completing onboarding for user {user_id}: {str(e)}")
            return False
    
    def _log_onboarding_event(self, user_id: int, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log onboarding events for analytics"""
        try:
            # This could be expanded to log to a dedicated onboarding_events table
            logger.info(f"Onboarding event for user {user_id}: {event_type} - {event_data}")
        except Exception as e:
            logger.error(f"Error logging onboarding event: {str(e)}")


# Global instance for easy access
onboarding_manager = OnboardingManager()


def start_user_onboarding(user_id: int) -> bool:
    """
    Convenience function to start onboarding for a user
    
    Args:
        user_id: User ID
        
    Returns:
        True if successful, False otherwise
    """
    return onboarding_manager.start_onboarding(user_id)


def get_user_onboarding_progress(user_id: int) -> Optional[OnboardingProgress]:
    """
    Convenience function to get onboarding progress
    
    Args:
        user_id: User ID
        
    Returns:
        OnboardingProgress object or None
    """
    return onboarding_manager.get_onboarding_progress(user_id)


def complete_onboarding_step(user_id: int, step: OnboardingStep) -> bool:
    """
    Convenience function to complete an onboarding step
    
    Args:
        user_id: User ID
        step: Step to complete
        
    Returns:
        True if successful, False otherwise
    """
    return onboarding_manager.complete_onboarding_step(user_id, step)


def is_feature_unlocked(user_id: int, feature_name: str) -> bool:
    """
    Convenience function to check if a feature is unlocked
    
    Args:
        user_id: User ID
        feature_name: Feature name
        
    Returns:
        True if unlocked, False otherwise
    """
    return onboarding_manager.check_feature_unlock(user_id, feature_name)


def get_available_features(user_id: int) -> List[FeatureUnlock]:
    """
    Convenience function to get available features
    
    Args:
        user_id: User ID
        
    Returns:
        List of available features
    """
    return onboarding_manager.get_available_features(user_id)


if __name__ == "__main__":
    # Test the onboarding manager
    print("Onboarding Manager Test")
    print("=" * 50)
    
    # Test feature definitions
    print(f"Total features defined: {len(onboarding_manager.feature_definitions)}")
    for feature_name, feature_def in onboarding_manager.feature_definitions.items():
        print(f"  {feature_name}: {feature_def.description}")
    
    # Test step requirements
    print(f"\nTotal steps defined: {len(onboarding_manager.step_requirements)}")
    for step, req in onboarding_manager.step_requirements.items():
        print(f"  {step.value}: {req['description']}")
    
    print("\n" + "=" * 50)
    print("Onboarding manager ready!")


