"""
Progressive Feature Unlock Triggers Module

This module provides automatic feature unlock triggers that activate based on user
actions and progress during the onboarding process. It includes:

- Automatic feature unlock triggers based on user actions
- Progress milestone-based feature unlocks
- Engagement pattern recognition and rewards
- Time-based feature unlocks for retention
- Achievement-based feature unlocks
- Social feature unlocks based on connections
- Activity-based feature unlocks
- Goal completion triggers
- Tutorial completion rewards
- Streak-based feature unlocks
- Performance-based feature unlocks
- Custom trigger conditions and rules
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any, Set, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from db_utils import get_db_connection, execute_query, USE_POSTGRES
from onboarding_manager import OnboardingManager, OnboardingStep, FeatureTier
from onboarding_progress_tracker import OnboardingProgressTracker, ProgressEventType
from onboarding_tutorial_system import OnboardingTutorialSystem
from tiered_feature_unlock import TieredFeatureUnlockManager, UnlockCondition
from new_user_dashboard import NewUserDashboardManager

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of feature unlock triggers"""
    ACTION_BASED = 'action_based'
    MILESTONE_BASED = 'milestone_based'
    TIME_BASED = 'time_based'
    ENGAGEMENT_BASED = 'engagement_based'
    ACHIEVEMENT_BASED = 'achievement_based'
    SOCIAL_BASED = 'social_based'
    ACTIVITY_BASED = 'activity_based'
    GOAL_BASED = 'goal_based'
    TUTORIAL_BASED = 'tutorial_based'
    STREAK_BASED = 'streak_based'
    PERFORMANCE_BASED = 'performance_based'
    CUSTOM = 'custom'


class TriggerStatus(Enum):
    """Trigger status enumeration"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    TRIGGERED = 'triggered'
    EXPIRED = 'expired'
    DISABLED = 'disabled'


@dataclass
class TriggerCondition:
    """Condition for a feature unlock trigger"""
    condition_id: str
    condition_type: str  # step_completed, activity_count, time_elapsed, etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    operator: str = 'equals'  # equals, greater_than, less_than, contains, etc.
    value: Any = None
    required: bool = True


@dataclass
class FeatureUnlockTrigger:
    """Feature unlock trigger definition"""
    trigger_id: str
    name: str
    description: str
    trigger_type: TriggerType
    target_feature: str
    conditions: List[TriggerCondition] = field(default_factory=list)
    priority: int = 0  # Higher number = higher priority
    cooldown_period: int = 0  # Seconds between triggers
    max_triggers: int = 1  # Maximum number of times this trigger can fire
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TriggerEvent:
    """Trigger event data"""
    event_id: str
    user_id: int
    trigger_id: str
    trigger_type: TriggerType
    target_feature: str
    event_data: Dict[str, Any] = field(default_factory=dict)
    triggered_at: datetime = field(default_factory=datetime.now)
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class TriggerAnalytics:
    """Trigger analytics data"""
    trigger_id: str
    total_events: int = 0
    successful_triggers: int = 0
    failed_triggers: int = 0
    average_trigger_time: float = 0.0
    success_rate: float = 0.0
    last_triggered: Optional[datetime] = None
    most_common_conditions: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0


class ProgressiveFeatureTriggers:
    """
    Manager for progressive feature unlock triggers
    """
    
    def __init__(self):
        """Initialize the trigger manager"""
        self.onboarding_manager = OnboardingManager()
        self.progress_tracker = OnboardingProgressTracker()
        self.tutorial_system = OnboardingTutorialSystem()
        self.tiered_feature_manager = TieredFeatureUnlockManager()
        self.dashboard_manager = NewUserDashboardManager()
        self.triggers = self._initialize_triggers()
        self.trigger_events = {}
        
    def _initialize_triggers(self) -> Dict[str, FeatureUnlockTrigger]:
        """Initialize feature unlock triggers"""
        return {
            # Action-based triggers
            'strava_connected': FeatureUnlockTrigger(
                trigger_id='strava_connected',
                name='Strava Connection Reward',
                description='Unlock activity viewer when Strava is connected',
                trigger_type=TriggerType.ACTION_BASED,
                target_feature='activity_viewer',
                conditions=[
                    TriggerCondition(
                        condition_id='strava_step_completed',
                        condition_type='step_completed',
                        parameters={'step': OnboardingStep.STRAVA_CONNECTED.value},
                        operator='equals',
                        value=True
                    )
                ],
                priority=100
            ),
            
            'first_activity_synced': FeatureUnlockTrigger(
                trigger_id='first_activity_synced',
                name='First Activity Reward',
                description='Unlock activity analysis when first activity is synced',
                trigger_type=TriggerType.ACTION_BASED,
                target_feature='activity_analysis',
                conditions=[
                    TriggerCondition(
                        condition_id='first_activity_step_completed',
                        condition_type='step_completed',
                        parameters={'step': OnboardingStep.FIRST_ACTIVITY.value},
                        operator='equals',
                        value=True
                    )
                ],
                priority=95
            ),
            
            'dashboard_intro_completed': FeatureUnlockTrigger(
                trigger_id='dashboard_intro_completed',
                name='Dashboard Introduction Reward',
                description='Unlock dashboard customization after dashboard intro',
                trigger_type=TriggerType.ACTION_BASED,
                target_feature='dashboard_customization',
                conditions=[
                    TriggerCondition(
                        condition_id='dashboard_intro_step_completed',
                        condition_type='step_completed',
                        parameters={'step': OnboardingStep.DASHBOARD_INTRO.value},
                        operator='equals',
                        value=True
                    )
                ],
                priority=90
            ),
            
            'goals_setup_completed': FeatureUnlockTrigger(
                trigger_id='goals_setup_completed',
                name='Goals Setup Reward',
                description='Unlock advanced goal tracking after goals setup',
                trigger_type=TriggerType.ACTION_BASED,
                target_feature='advanced_goal_tracking',
                conditions=[
                    TriggerCondition(
                        condition_id='goals_setup_step_completed',
                        condition_type='step_completed',
                        parameters={'step': OnboardingStep.GOALS_SETUP.value},
                        operator='equals',
                        value=True
                    )
                ],
                priority=85
            ),
            
            # Milestone-based triggers
            'onboarding_50_percent': FeatureUnlockTrigger(
                trigger_id='onboarding_50_percent',
                name='Halfway There Reward',
                description='Unlock progress insights at 50% onboarding completion',
                trigger_type=TriggerType.MILESTONE_BASED,
                target_feature='progress_insights',
                conditions=[
                    TriggerCondition(
                        condition_id='progress_percentage',
                        condition_type='progress_percentage',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=50.0
                    )
                ],
                priority=80
            ),
            
            'onboarding_75_percent': FeatureUnlockTrigger(
                trigger_id='onboarding_75_percent',
                name='Almost There Reward',
                description='Unlock advanced analytics at 75% onboarding completion',
                trigger_type=TriggerType.MILESTONE_BASED,
                target_feature='advanced_analytics',
                conditions=[
                    TriggerCondition(
                        condition_id='progress_percentage',
                        condition_type='progress_percentage',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=75.0
                    )
                ],
                priority=75
            ),
            
            'onboarding_completed': FeatureUnlockTrigger(
                trigger_id='onboarding_completed',
                name='Onboarding Complete Reward',
                description='Unlock all features when onboarding is completed',
                trigger_type=TriggerType.MILESTONE_BASED,
                target_feature='all_features',
                conditions=[
                    TriggerCondition(
                        condition_id='progress_percentage',
                        condition_type='progress_percentage',
                        parameters={},
                        operator='equals',
                        value=100.0
                    )
                ],
                priority=70
            ),
            
            # Activity-based triggers
            'five_activities': FeatureUnlockTrigger(
                trigger_id='five_activities',
                name='Activity Enthusiast',
                description='Unlock activity trends after 5 activities',
                trigger_type=TriggerType.ACTIVITY_BASED,
                target_feature='activity_trends',
                conditions=[
                    TriggerCondition(
                        condition_id='activity_count',
                        condition_type='activity_count',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=5
                    )
                ],
                priority=85
            ),
            
            'ten_activities': FeatureUnlockTrigger(
                trigger_id='ten_activities',
                name='Dedicated Athlete',
                description='Unlock performance insights after 10 activities',
                trigger_type=TriggerType.ACTIVITY_BASED,
                target_feature='performance_insights',
                conditions=[
                    TriggerCondition(
                        condition_id='activity_count',
                        condition_type='activity_count',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=10
                    )
                ],
                priority=80
            ),
            
            'twenty_activities': FeatureUnlockTrigger(
                trigger_id='twenty_activities',
                name='Training Veteran',
                description='Unlock advanced training analytics after 20 activities',
                trigger_type=TriggerType.ACTIVITY_BASED,
                target_feature='advanced_training_analytics',
                conditions=[
                    TriggerCondition(
                        condition_id='activity_count',
                        condition_type='activity_count',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=20
                    )
                ],
                priority=75
            ),
            
            # Time-based triggers
            'one_week_active': FeatureUnlockTrigger(
                trigger_id='one_week_active',
                name='Week One Reward',
                description='Unlock weekly insights after one week of activity',
                trigger_type=TriggerType.TIME_BASED,
                target_feature='weekly_insights',
                conditions=[
                    TriggerCondition(
                        condition_id='days_since_join',
                        condition_type='days_since_join',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=7
                    )
                ],
                priority=70
            ),
            
            'one_month_active': FeatureUnlockTrigger(
                trigger_id='one_month_active',
                name='Month One Reward',
                description='Unlock monthly reports after one month of activity',
                trigger_type=TriggerType.TIME_BASED,
                target_feature='monthly_reports',
                conditions=[
                    TriggerCondition(
                        condition_id='days_since_join',
                        condition_type='days_since_join',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=30
                    )
                ],
                priority=65
            ),
            
            # Engagement-based triggers
            'three_tutorials_completed': FeatureUnlockTrigger(
                trigger_id='three_tutorials_completed',
                name='Learning Enthusiast',
                description='Unlock advanced tutorials after completing 3 tutorials',
                trigger_type=TriggerType.ENGAGEMENT_BASED,
                target_feature='advanced_tutorials',
                conditions=[
                    TriggerCondition(
                        condition_id='tutorials_completed',
                        condition_type='tutorials_completed',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=3
                    )
                ],
                priority=75
            ),
            
            'five_tutorials_completed': FeatureUnlockTrigger(
                trigger_id='five_tutorials_completed',
                name='Knowledge Seeker',
                description='Unlock expert tutorials after completing 5 tutorials',
                trigger_type=TriggerType.ENGAGEMENT_BASED,
                target_feature='expert_tutorials',
                conditions=[
                    TriggerCondition(
                        condition_id='tutorials_completed',
                        condition_type='tutorials_completed',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=5
                    )
                ],
                priority=70
            ),
            
            # Goal-based triggers
            'first_goal_achieved': FeatureUnlockTrigger(
                trigger_id='first_goal_achieved',
                name='Goal Achiever',
                description='Unlock goal insights after achieving first goal',
                trigger_type=TriggerType.GOAL_BASED,
                target_feature='goal_insights',
                conditions=[
                    TriggerCondition(
                        condition_id='goals_achieved',
                        condition_type='goals_achieved',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=1
                    )
                ],
                priority=80
            ),
            
            'three_goals_achieved': FeatureUnlockTrigger(
                trigger_id='three_goals_achieved',
                name='Goal Master',
                description='Unlock advanced goal analytics after achieving 3 goals',
                trigger_type=TriggerType.GOAL_BASED,
                target_feature='advanced_goal_analytics',
                conditions=[
                    TriggerCondition(
                        condition_id='goals_achieved',
                        condition_type='goals_achieved',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=3
                    )
                ],
                priority=75
            ),
            
            # Streak-based triggers
            'three_day_streak': FeatureUnlockTrigger(
                trigger_id='three_day_streak',
                name='Consistency Starter',
                description='Unlock streak tracking after 3-day activity streak',
                trigger_type=TriggerType.STREAK_BASED,
                target_feature='streak_tracking',
                conditions=[
                    TriggerCondition(
                        condition_id='activity_streak',
                        condition_type='activity_streak',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=3
                    )
                ],
                priority=80
            ),
            
            'seven_day_streak': FeatureUnlockTrigger(
                trigger_id='seven_day_streak',
                name='Week Warrior',
                description='Unlock streak insights after 7-day activity streak',
                trigger_type=TriggerType.STREAK_BASED,
                target_feature='streak_insights',
                conditions=[
                    TriggerCondition(
                        condition_id='activity_streak',
                        condition_type='activity_streak',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=7
                    )
                ],
                priority=75
            ),
            
            # Performance-based triggers
            'personal_best': FeatureUnlockTrigger(
                trigger_id='personal_best',
                name='Personal Best',
                description='Unlock performance tracking after achieving a personal best',
                trigger_type=TriggerType.PERFORMANCE_BASED,
                target_feature='performance_tracking',
                conditions=[
                    TriggerCondition(
                        condition_id='personal_best_achieved',
                        condition_type='personal_best_achieved',
                        parameters={},
                        operator='equals',
                        value=True
                    )
                ],
                priority=85
            ),
            
            'improvement_streak': FeatureUnlockTrigger(
                trigger_id='improvement_streak',
                name='Improvement Tracker',
                description='Unlock improvement analytics after 3 consecutive improvements',
                trigger_type=TriggerType.PERFORMANCE_BASED,
                target_feature='improvement_analytics',
                conditions=[
                    TriggerCondition(
                        condition_id='improvement_streak',
                        condition_type='improvement_streak',
                        parameters={},
                        operator='greater_than_or_equal',
                        value=3
                    )
                ],
                priority=80
            )
        }
    
    def check_triggers(self, user_id: int, event_type: str = None, event_data: Optional[Dict[str, Any]] = None) -> List[TriggerEvent]:
        """
        Check and execute all applicable triggers for a user
        
        Args:
            user_id: User ID
            event_type: Type of event that triggered the check
            event_data: Additional event data
            
        Returns:
            List of trigger events that were executed
        """
        try:
            triggered_events = []
            
            # Get user progress
            progress = self.progress_tracker.get_progress(user_id)
            if not progress:
                logger.warning(f"No progress data found for user {user_id}")
                return triggered_events
            
            # Check each trigger
            for trigger_id, trigger in self.triggers.items():
                if not trigger.active:
                    continue
                
                # Check if trigger should be evaluated based on event type
                if event_type and not self._should_evaluate_trigger(trigger, event_type):
                    continue
                
                # Check if trigger conditions are met
                if self._check_trigger_conditions(user_id, trigger, progress, event_data):
                    # Check cooldown and max triggers
                    if self._can_trigger(user_id, trigger):
                        # Execute trigger
                        trigger_event = self._execute_trigger(user_id, trigger, event_data)
                        if trigger_event:
                            triggered_events.append(trigger_event)
                            
                            # Log trigger event
                            self.progress_tracker.update_progress(
                                user_id,
                                event_type=ProgressEventType.FEATURE_UNLOCKED,
                                event_data={
                                    'trigger_id': trigger_id,
                                    'target_feature': trigger.target_feature,
                                    'trigger_type': trigger.trigger_type.value,
                                    'timestamp': datetime.now().isoformat()
                                }
                            )
            
            # Sort by priority (higher priority first)
            triggered_events.sort(key=lambda x: self.triggers[x.trigger_id].priority, reverse=True)
            
            logger.info(f"Executed {len(triggered_events)} triggers for user {user_id}")
            return triggered_events
            
        except Exception as e:
            logger.error(f"Error checking triggers for user {user_id}: {str(e)}")
            return []
    
    def _should_evaluate_trigger(self, trigger: FeatureUnlockTrigger, event_type: str) -> bool:
        """Check if trigger should be evaluated based on event type"""
        try:
            # Map event types to trigger types
            event_trigger_mapping = {
                'step_completed': [TriggerType.ACTION_BASED, TriggerType.MILESTONE_BASED],
                'activity_synced': [TriggerType.ACTIVITY_BASED],
                'tutorial_completed': [TriggerType.ENGAGEMENT_BASED],
                'goal_achieved': [TriggerType.GOAL_BASED],
                'time_elapsed': [TriggerType.TIME_BASED],
                'streak_updated': [TriggerType.STREAK_BASED],
                'performance_improved': [TriggerType.PERFORMANCE_BASED]
            }
            
            if event_type in event_trigger_mapping:
                return trigger.trigger_type in event_trigger_mapping[event_type]
            
            # Default to evaluating all triggers
            return True
            
        except Exception as e:
            logger.error(f"Error checking trigger evaluation: {str(e)}")
            return True
    
    def _check_trigger_conditions(self, user_id: int, trigger: FeatureUnlockTrigger, 
                                progress: Any, event_data: Optional[Dict[str, Any]] = None) -> bool:
        """Check if all trigger conditions are met"""
        try:
            for condition in trigger.conditions:
                if not self._evaluate_condition(user_id, condition, progress, event_data):
                    if condition.required:
                        return False
                    # Non-required conditions can be skipped
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking trigger conditions: {str(e)}")
            return False
    
    def _evaluate_condition(self, user_id: int, condition: TriggerCondition, 
                          progress: Any, event_data: Optional[Dict[str, Any]] = None) -> bool:
        """Evaluate a single trigger condition"""
        try:
            condition_type = condition.condition_type
            
            if condition_type == 'step_completed':
                return self._evaluate_step_completed_condition(condition, progress)
            elif condition_type == 'progress_percentage':
                return self._evaluate_progress_percentage_condition(condition, progress)
            elif condition_type == 'activity_count':
                return self._evaluate_activity_count_condition(condition, user_id)
            elif condition_type == 'days_since_join':
                return self._evaluate_days_since_join_condition(condition, user_id)
            elif condition_type == 'tutorials_completed':
                return self._evaluate_tutorials_completed_condition(condition, user_id)
            elif condition_type == 'goals_achieved':
                return self._evaluate_goals_achieved_condition(condition, user_id)
            elif condition_type == 'activity_streak':
                return self._evaluate_activity_streak_condition(condition, user_id)
            elif condition_type == 'personal_best_achieved':
                return self._evaluate_personal_best_condition(condition, user_id)
            elif condition_type == 'improvement_streak':
                return self._evaluate_improvement_streak_condition(condition, user_id)
            else:
                logger.warning(f"Unknown condition type: {condition_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating condition {condition.condition_id}: {str(e)}")
            return False
    
    def _evaluate_step_completed_condition(self, condition: TriggerCondition, progress: Any) -> bool:
        """Evaluate step completed condition"""
        try:
            step_name = condition.parameters.get('step')
            if not step_name:
                return False
            
            try:
                step = OnboardingStep(step_name)
                is_completed = step in progress.completed_steps
                
                if condition.operator == 'equals':
                    return is_completed == condition.value
                elif condition.operator == 'not_equals':
                    return is_completed != condition.value
                else:
                    return is_completed
                    
            except ValueError:
                logger.warning(f"Invalid step name: {step_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating step completed condition: {str(e)}")
            return False
    
    def _evaluate_progress_percentage_condition(self, condition: TriggerCondition, progress: Any) -> bool:
        """Evaluate progress percentage condition"""
        try:
            current_percentage = progress.progress_percentage
            
            if condition.operator == 'equals':
                return current_percentage == condition.value
            elif condition.operator == 'greater_than':
                return current_percentage > condition.value
            elif condition.operator == 'greater_than_or_equal':
                return current_percentage >= condition.value
            elif condition.operator == 'less_than':
                return current_percentage < condition.value
            elif condition.operator == 'less_than_or_equal':
                return current_percentage <= condition.value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating progress percentage condition: {str(e)}")
            return False
    
    def _evaluate_activity_count_condition(self, condition: TriggerCondition, user_id: int) -> bool:
        """Evaluate activity count condition"""
        try:
            activity_count = self.tiered_feature_manager._get_user_activity_count(user_id)
            
            if condition.operator == 'equals':
                return activity_count == condition.value
            elif condition.operator == 'greater_than':
                return activity_count > condition.value
            elif condition.operator == 'greater_than_or_equal':
                return activity_count >= condition.value
            elif condition.operator == 'less_than':
                return activity_count < condition.value
            elif condition.operator == 'less_than_or_equal':
                return activity_count <= condition.value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating activity count condition: {str(e)}")
            return False
    
    def _evaluate_days_since_join_condition(self, condition: TriggerCondition, user_id: int) -> bool:
        """Evaluate days since join condition"""
        try:
            # In practice, this would query the users table
            # For now, use a placeholder value
            days_since_join = 1  # Placeholder
            
            if condition.operator == 'equals':
                return days_since_join == condition.value
            elif condition.operator == 'greater_than':
                return days_since_join > condition.value
            elif condition.operator == 'greater_than_or_equal':
                return days_since_join >= condition.value
            elif condition.operator == 'less_than':
                return days_since_join < condition.value
            elif condition.operator == 'less_than_or_equal':
                return days_since_join <= condition.value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating days since join condition: {str(e)}")
            return False
    
    def _evaluate_tutorials_completed_condition(self, condition: TriggerCondition, user_id: int) -> bool:
        """Evaluate tutorials completed condition"""
        try:
            # In practice, this would query tutorial completion data
            # For now, use a placeholder value
            tutorials_completed = 0  # Placeholder
            
            if condition.operator == 'equals':
                return tutorials_completed == condition.value
            elif condition.operator == 'greater_than':
                return tutorials_completed > condition.value
            elif condition.operator == 'greater_than_or_equal':
                return tutorials_completed >= condition.value
            elif condition.operator == 'less_than':
                return tutorials_completed < condition.value
            elif condition.operator == 'less_than_or_equal':
                return tutorials_completed <= condition.value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating tutorials completed condition: {str(e)}")
            return False
    
    def _evaluate_goals_achieved_condition(self, condition: TriggerCondition, user_id: int) -> bool:
        """Evaluate goals achieved condition"""
        try:
            # In practice, this would query goals achievement data
            # For now, use a placeholder value
            goals_achieved = 0  # Placeholder
            
            if condition.operator == 'equals':
                return goals_achieved == condition.value
            elif condition.operator == 'greater_than':
                return goals_achieved > condition.value
            elif condition.operator == 'greater_than_or_equal':
                return goals_achieved >= condition.value
            elif condition.operator == 'less_than':
                return goals_achieved < condition.value
            elif condition.operator == 'less_than_or_equal':
                return goals_achieved <= condition.value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating goals achieved condition: {str(e)}")
            return False
    
    def _evaluate_activity_streak_condition(self, condition: TriggerCondition, user_id: int) -> bool:
        """Evaluate activity streak condition"""
        try:
            # In practice, this would calculate activity streak
            # For now, use a placeholder value
            activity_streak = 0  # Placeholder
            
            if condition.operator == 'equals':
                return activity_streak == condition.value
            elif condition.operator == 'greater_than':
                return activity_streak > condition.value
            elif condition.operator == 'greater_than_or_equal':
                return activity_streak >= condition.value
            elif condition.operator == 'less_than':
                return activity_streak < condition.value
            elif condition.operator == 'less_than_or_equal':
                return activity_streak <= condition.value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating activity streak condition: {str(e)}")
            return False
    
    def _evaluate_personal_best_condition(self, condition: TriggerCondition, user_id: int) -> bool:
        """Evaluate personal best condition"""
        try:
            # In practice, this would check if user achieved a personal best
            # For now, use a placeholder value
            personal_best_achieved = False  # Placeholder
            
            if condition.operator == 'equals':
                return personal_best_achieved == condition.value
            else:
                return personal_best_achieved
                
        except Exception as e:
            logger.error(f"Error evaluating personal best condition: {str(e)}")
            return False
    
    def _evaluate_improvement_streak_condition(self, condition: TriggerCondition, user_id: int) -> bool:
        """Evaluate improvement streak condition"""
        try:
            # In practice, this would calculate improvement streak
            # For now, use a placeholder value
            improvement_streak = 0  # Placeholder
            
            if condition.operator == 'equals':
                return improvement_streak == condition.value
            elif condition.operator == 'greater_than':
                return improvement_streak > condition.value
            elif condition.operator == 'greater_than_or_equal':
                return improvement_streak >= condition.value
            elif condition.operator == 'less_than':
                return improvement_streak < condition.value
            elif condition.operator == 'less_than_or_equal':
                return improvement_streak <= condition.value
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error evaluating improvement streak condition: {str(e)}")
            return False
    
    def _can_trigger(self, user_id: int, trigger: FeatureUnlockTrigger) -> bool:
        """Check if trigger can be executed (cooldown and max triggers)"""
        try:
            # Check cooldown period
            if trigger.cooldown_period > 0:
                last_trigger = self._get_last_trigger_time(user_id, trigger.trigger_id)
                if last_trigger:
                    time_since_last = (datetime.now() - last_trigger).total_seconds()
                    if time_since_last < trigger.cooldown_period:
                        return False
            
            # Check max triggers
            if trigger.max_triggers > 0:
                trigger_count = self._get_trigger_count(user_id, trigger.trigger_id)
                if trigger_count >= trigger.max_triggers:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking trigger availability: {str(e)}")
            return False
    
    def _execute_trigger(self, user_id: int, trigger: FeatureUnlockTrigger, 
                        event_data: Optional[Dict[str, Any]] = None) -> Optional[TriggerEvent]:
        """Execute a feature unlock trigger"""
        try:
            # Create trigger event
            event_id = f"{user_id}_{trigger.trigger_id}_{datetime.now().timestamp()}"
            trigger_event = TriggerEvent(
                event_id=event_id,
                user_id=user_id,
                trigger_id=trigger.trigger_id,
                trigger_type=trigger.trigger_type,
                target_feature=trigger.target_feature,
                event_data=event_data or {},
                triggered_at=datetime.now()
            )
            
            # Attempt to unlock the feature
            try:
                success = self.tiered_feature_manager.unlock_feature(user_id, trigger.target_feature)
                trigger_event.success = success
                
                if not success:
                    trigger_event.error_message = "Feature unlock failed"
                    
            except Exception as e:
                trigger_event.success = False
                trigger_event.error_message = str(e)
                logger.error(f"Error unlocking feature {trigger.target_feature}: {str(e)}")
            
            # Save trigger event
            self._save_trigger_event(trigger_event)
            
            # Log successful trigger
            if trigger_event.success:
                logger.info(f"Successfully triggered {trigger.trigger_id} for user {user_id}, unlocked {trigger.target_feature}")
            
            return trigger_event
            
        except Exception as e:
            logger.error(f"Error executing trigger {trigger.trigger_id}: {str(e)}")
            return None
    
    def get_user_triggers(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all triggers for a user with their status"""
        try:
            user_triggers = []
            
            # Get user progress
            progress = self.progress_tracker.get_progress(user_id)
            if not progress:
                return user_triggers
            
            for trigger_id, trigger in self.triggers.items():
                if not trigger.active:
                    continue
                
                # Check trigger status
                status = self._get_trigger_status(user_id, trigger, progress)
                
                trigger_info = {
                    'trigger_id': trigger_id,
                    'name': trigger.name,
                    'description': trigger.description,
                    'trigger_type': trigger.trigger_type.value,
                    'target_feature': trigger.target_feature,
                    'priority': trigger.priority,
                    'status': status.value,
                    'conditions': [
                        {
                            'condition_id': condition.condition_id,
                            'condition_type': condition.condition_type,
                            'parameters': condition.parameters,
                            'operator': condition.operator,
                            'value': condition.value,
                            'required': condition.required
                        }
                        for condition in trigger.conditions
                    ]
                }
                
                user_triggers.append(trigger_info)
            
            # Sort by priority (higher priority first)
            user_triggers.sort(key=lambda x: x['priority'], reverse=True)
            
            return user_triggers
            
        except Exception as e:
            logger.error(f"Error getting user triggers: {str(e)}")
            return []
    
    def _get_trigger_status(self, user_id: int, trigger: FeatureUnlockTrigger, progress: Any) -> TriggerStatus:
        """Get the status of a trigger for a user"""
        try:
            # Check if trigger has already been triggered
            trigger_count = self._get_trigger_count(user_id, trigger.trigger_id)
            if trigger_count >= trigger.max_triggers:
                return TriggerStatus.TRIGGERED
            
            # Check if conditions are met
            if self._check_trigger_conditions(user_id, trigger, progress):
                return TriggerStatus.ACTIVE
            else:
                return TriggerStatus.INACTIVE
                
        except Exception as e:
            logger.error(f"Error getting trigger status: {str(e)}")
            return TriggerStatus.INACTIVE
    
    def get_trigger_analytics(self, trigger_id: str) -> Optional[TriggerAnalytics]:
        """Get analytics for a trigger"""
        try:
            # In practice, this would query aggregated data from the database
            # For now, return a placeholder analytics object
            analytics = TriggerAnalytics(
                trigger_id=trigger_id,
                total_events=50,
                successful_triggers=45,
                failed_triggers=5,
                average_trigger_time=2.5,
                success_rate=0.9,
                last_triggered=datetime.now() - timedelta(hours=2),
                most_common_conditions=['step_completed', 'progress_percentage'],
                effectiveness_score=0.85
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting trigger analytics: {str(e)}")
            return None
    
    # Database methods
    def _save_trigger_event(self, trigger_event: TriggerEvent):
        """Save trigger event to database"""
        try:
            event_data = {
                'event_id': trigger_event.event_id,
                'user_id': trigger_event.user_id,
                'trigger_id': trigger_event.trigger_id,
                'trigger_type': trigger_event.trigger_type.value,
                'target_feature': trigger_event.target_feature,
                'event_data': trigger_event.event_data,
                'triggered_at': trigger_event.triggered_at.isoformat(),
                'success': trigger_event.success,
                'error_message': trigger_event.error_message
            }
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if USE_POSTGRES:
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, trigger_events)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET trigger_events = user_settings.trigger_events || %s
                    """, (trigger_event.user_id, json.dumps([event_data]), json.dumps([event_data])))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO user_settings (user_id, trigger_events)
                        VALUES (?, ?)
                    """, (trigger_event.user_id, json.dumps([event_data])))
            
        except Exception as e:
            logger.error(f"Error saving trigger event: {str(e)}")
    
    def _get_last_trigger_time(self, user_id: int, trigger_id: str) -> Optional[datetime]:
        """Get the last time a trigger was executed for a user"""
        try:
            # In practice, this would query the database for the last trigger time
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            logger.error(f"Error getting last trigger time: {str(e)}")
            return None
    
    def _get_trigger_count(self, user_id: int, trigger_id: str) -> int:
        """Get the number of times a trigger has been executed for a user"""
        try:
            # In practice, this would query the database for trigger count
            # For now, return 0 as placeholder
            return 0
            
        except Exception as e:
            logger.error(f"Error getting trigger count: {str(e)}")
            return 0


# Convenience functions for easy integration
feature_triggers = ProgressiveFeatureTriggers()


def check_triggers(user_id: int, event_type: str = None, event_data: Optional[Dict[str, Any]] = None) -> List[TriggerEvent]:
    """Check and execute all applicable triggers for a user"""
    return feature_triggers.check_triggers(user_id, event_type, event_data)


def get_user_triggers(user_id: int) -> List[Dict[str, Any]]:
    """Get all triggers for a user with their status"""
    return feature_triggers.get_user_triggers(user_id)


def get_trigger_analytics(trigger_id: str) -> Optional[TriggerAnalytics]:
    """Get analytics for a trigger"""
    return feature_triggers.get_trigger_analytics(trigger_id)


if __name__ == "__main__":
    print("=" * 50)
    print("Progressive Feature Triggers")
    print("=" * 50)
    print("Module loaded successfully!")
    print(f"Triggers defined: {len(feature_triggers.triggers)}")
    print(f"Trigger types: {[trigger_type.value for trigger_type in TriggerType]}")
    print(f"Trigger statuses: {[status.value for status in TriggerStatus]}")
    print("=" * 50)


