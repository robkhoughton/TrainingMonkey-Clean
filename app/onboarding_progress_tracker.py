"""
Onboarding Progress Tracker Module

This module provides comprehensive onboarding progress tracking for the progressive
onboarding system. It includes:

- Detailed progress tracking with milestones and achievements
- Progress analytics and insights
- Progress visualization and reporting
- Milestone completion tracking
- Progress comparison and benchmarking
- Progress persistence and recovery
- Progress notifications and alerts
- Progress optimization recommendations
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from db_utils import get_db_connection, execute_query
from onboarding_manager import OnboardingManager, OnboardingStep, FeatureTier
from tiered_feature_unlock import TieredFeatureUnlockManager, UnlockCondition

logger = logging.getLogger(__name__)


class ProgressEventType(Enum):
    """Types of progress events"""
    STEP_COMPLETED = 'step_completed'
    FEATURE_UNLOCKED = 'feature_unlocked'
    MILESTONE_REACHED = 'milestone_reached'
    ACTIVITY_ADDED = 'activity_added'
    GOAL_SET = 'goal_set'
    ENGAGEMENT_INCREASED = 'engagement_increased'
    TIER_UPGRADED = 'tier_upgraded'
    ONBOARDING_STARTED = 'onboarding_started'
    ONBOARDING_COMPLETED = 'onboarding_completed'
    PROGRESS_STALLED = 'progress_stalled'


class ProgressStatus(Enum):
    """Progress status enumeration"""
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    STALLED = 'stalled'
    COMPLETED = 'completed'
    ABANDONED = 'abandoned'


@dataclass
class ProgressMilestone:
    """Individual progress milestone"""
    milestone_id: str
    name: str
    description: str
    required_steps: List[OnboardingStep]
    required_features: List[str]
    required_activities: int
    required_days: int
    reward_description: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0


@dataclass
class ProgressEvent:
    """Progress event record"""
    event_id: str
    user_id: int
    event_type: ProgressEventType
    event_data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OnboardingProgress:
    """Comprehensive onboarding progress data"""
    user_id: int
    current_step: OnboardingStep
    completed_steps: List[OnboardingStep]
    unlocked_features: List[str]
    current_tier: FeatureTier
    progress_percentage: float
    started_at: datetime
    last_activity: datetime
    completed_at: Optional[datetime] = None
    status: ProgressStatus = ProgressStatus.IN_PROGRESS
    milestones: List[ProgressMilestone] = field(default_factory=list)
    recent_events: List[ProgressEvent] = field(default_factory=list)
    analytics: Dict[str, Any] = field(default_factory=dict)


class OnboardingProgressTracker:
    """
    Comprehensive onboarding progress tracking system
    """
    
    def __init__(self):
        """Initialize the progress tracker"""
        self.onboarding_manager = OnboardingManager()
        self.tiered_feature_manager = TieredFeatureUnlockManager()
        self.milestones = self._initialize_milestones()
        self.progress_cache = {}
        
    def _initialize_milestones(self) -> Dict[str, ProgressMilestone]:
        """Initialize progress milestones"""
        return {
            'welcome_complete': ProgressMilestone(
                milestone_id='welcome_complete',
                name='Welcome Complete',
                description='Successfully completed the welcome process',
                required_steps=[OnboardingStep.WELCOME],
                required_features=[],
                required_activities=0,
                required_days=0,
                reward_description='Access to basic dashboard features'
            ),
            'strava_connected': ProgressMilestone(
                milestone_id='strava_connected',
                name='Strava Connected',
                description='Successfully connected your Strava account',
                required_steps=[OnboardingStep.STRAVA_CONNECTED],
                required_features=[],
                required_activities=0,
                required_days=0,
                reward_description='Start syncing your activities'
            ),
            'first_activity': ProgressMilestone(
                milestone_id='first_activity',
                name='First Activity',
                description='Synced your first activity from Strava',
                required_steps=[OnboardingStep.FIRST_ACTIVITY],
                required_features=[],
                required_activities=1,
                required_days=1,
                reward_description='Unlock activity analysis features'
            ),
            'data_sync_complete': ProgressMilestone(
                milestone_id='data_sync_complete',
                name='Data Sync Complete',
                description='Successfully synced multiple activities',
                required_steps=[OnboardingStep.DATA_SYNC],
                required_features=[],
                required_activities=3,
                required_days=3,
                reward_description='Access to advanced analytics'
            ),
            'dashboard_mastered': ProgressMilestone(
                milestone_id='dashboard_mastered',
                name='Dashboard Mastered',
                description='Completed dashboard introduction and tour',
                required_steps=[OnboardingStep.DASHBOARD_INTRO],
                required_features=['dashboard_basic'],
                required_activities=1,
                required_days=1,
                reward_description='Full dashboard access'
            ),
            'features_explored': ProgressMilestone(
                milestone_id='features_explored',
                name='Features Explored',
                description='Completed features overview tour',
                required_steps=[OnboardingStep.FEATURES_TOUR],
                required_features=['dashboard_advanced'],
                required_activities=3,
                required_days=3,
                reward_description='Access to intermediate features'
            ),
            'goals_configured': ProgressMilestone(
                milestone_id='goals_configured',
                name='Goals Configured',
                description='Set up your training goals',
                required_steps=[OnboardingStep.GOALS_SETUP],
                required_features=['custom_goals'],
                required_activities=3,
                required_days=3,
                reward_description='Goal tracking and recommendations'
            ),
            'first_recommendation': ProgressMilestone(
                milestone_id='first_recommendation',
                name='First Recommendation',
                description='Received your first AI training recommendation',
                required_steps=[OnboardingStep.FIRST_RECOMMENDATION],
                required_features=['recommendations'],
                required_activities=3,
                required_days=3,
                reward_description='Personalized training insights'
            ),
            'journal_setup': ProgressMilestone(
                milestone_id='journal_setup',
                name='Journal Setup',
                description='Completed journal introduction and setup',
                required_steps=[OnboardingStep.JOURNAL_INTRO],
                required_features=['journal'],
                required_activities=5,
                required_days=5,
                reward_description='Daily training journal access'
            ),
            'onboarding_complete': ProgressMilestone(
                milestone_id='onboarding_complete',
                name='Onboarding Complete',
                description='Successfully completed the full onboarding process',
                required_steps=[OnboardingStep.COMPLETED],
                required_features=['advanced_analytics'],
                required_activities=10,
                required_days=7,
                reward_description='Access to all advanced features'
            )
        }
    
    def start_progress_tracking(self, user_id: int) -> bool:
        """
        Start progress tracking for a new user
        
        Args:
            user_id: User ID to start tracking
            
        Returns:
            True if successfully started, False otherwise
        """
        try:
            # Initialize onboarding if not already started
            if not self.onboarding_manager.start_onboarding(user_id):
                logger.warning(f"Failed to start onboarding for user {user_id}")
                return False
            
            # Create initial progress record
            progress = OnboardingProgress(
                user_id=user_id,
                current_step=OnboardingStep.WELCOME,
                completed_steps=[],
                unlocked_features=[],
                current_tier=FeatureTier.BASIC,
                progress_percentage=0.0,
                started_at=datetime.now(),
                last_activity=datetime.now(),
                status=ProgressStatus.IN_PROGRESS,
                milestones=[],
                recent_events=[],
                analytics={}
            )
            
            # Save progress to database
            self._save_progress(progress)
            
            # Log start event
            self._log_progress_event(user_id, ProgressEventType.ONBOARDING_STARTED, {
                'step': OnboardingStep.WELCOME.value,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Started progress tracking for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting progress tracking for user {user_id}: {str(e)}")
            return False
    
    def get_progress(self, user_id: int) -> Optional[OnboardingProgress]:
        """
        Get comprehensive progress information for a user
        
        Args:
            user_id: User ID
            
        Returns:
            OnboardingProgress object or None if not found
        """
        try:
            # Check cache first
            if user_id in self.progress_cache:
                return self.progress_cache[user_id]
            
            # Load from database
            progress = self._load_progress(user_id)
            if not progress:
                return None
            
            # Update progress with current data
            progress = self._update_progress_data(progress)
            
            # Cache the result
            self.progress_cache[user_id] = progress
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting progress for user {user_id}: {str(e)}")
            return None
    
    def update_progress(self, user_id: int, step: Optional[OnboardingStep] = None, 
                       feature: Optional[str] = None, event_type: Optional[ProgressEventType] = None,
                       event_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update user progress
        
        Args:
            user_id: User ID
            step: Onboarding step to complete (optional)
            feature: Feature to unlock (optional)
            event_type: Progress event type (optional)
            event_data: Additional event data (optional)
            
        Returns:
            True if successfully updated, False otherwise
        """
        try:
            # Get current progress
            progress = self.get_progress(user_id)
            if not progress:
                logger.warning(f"No progress found for user {user_id}")
                return False
            
            # Update step if provided
            if step:
                if step not in progress.completed_steps:
                    progress.completed_steps.append(step)
                    self.onboarding_manager.complete_onboarding_step(user_id, step)
                    
                    # Log step completion event
                    self._log_progress_event(user_id, ProgressEventType.STEP_COMPLETED, {
                        'step': step.value,
                        'timestamp': datetime.now().isoformat()
                    })
            
            # Update feature if provided
            if feature:
                if feature not in progress.unlocked_features:
                    success, result = self.tiered_feature_manager.unlock_tiered_feature(user_id, feature)
                    if success:
                        progress.unlocked_features.append(feature)
                        
                        # Log feature unlock event
                        self._log_progress_event(user_id, ProgressEventType.FEATURE_UNLOCKED, {
                            'feature': feature,
                            'timestamp': datetime.now().isoformat()
                        })
            
            # Log custom event if provided
            if event_type and event_data:
                self._log_progress_event(user_id, event_type, event_data)
            
            # Update progress data
            progress.last_activity = datetime.now()
            progress = self._update_progress_data(progress)
            
            # Check for milestone completions
            self._check_milestones(progress)
            
            # Save updated progress
            self._save_progress(progress)
            
            # Update cache
            self.progress_cache[user_id] = progress
            
            logger.info(f"Updated progress for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating progress for user {user_id}: {str(e)}")
            return False
    
    def get_progress_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed progress analytics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with analytics data
        """
        try:
            progress = self.get_progress(user_id)
            if not progress:
                return {}
            
            analytics = {
                'user_id': user_id,
                'overall_progress': progress.progress_percentage,
                'current_tier': progress.current_tier.value,
                'steps_completed': len(progress.completed_steps),
                'total_steps': len(OnboardingStep),
                'features_unlocked': len(progress.unlocked_features),
                'milestones_completed': len([m for m in progress.milestones if m.completed]),
                'total_milestones': len(progress.milestones),
                'time_in_onboarding': (datetime.now() - progress.started_at).days,
                'last_activity_days_ago': (datetime.now() - progress.last_activity).days,
                'status': progress.status.value,
                'recent_events': len(progress.recent_events),
                'progress_trend': self._calculate_progress_trend(progress),
                'engagement_score': self._calculate_engagement_score(progress),
                'completion_estimate': self._estimate_completion_time(progress),
                'recommendations': self._generate_progress_recommendations(progress)
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting progress analytics for user {user_id}: {str(e)}")
            return {}
    
    def get_progress_comparison(self, user_id: int) -> Dict[str, Any]:
        """
        Get progress comparison with other users
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with comparison data
        """
        try:
            user_analytics = self.get_progress_analytics(user_id)
            if not user_analytics:
                return {}
            
            # Get benchmark data (simplified - in practice, this would query aggregated data)
            benchmarks = {
                'avg_completion_time_days': 14,
                'avg_progress_percentage': 65.0,
                'top_percentile_progress': 85.0,
                'avg_steps_completed': 6,
                'avg_features_unlocked': 4
            }
            
            comparison = {
                'user_id': user_id,
                'user_progress': user_analytics,
                'benchmarks': benchmarks,
                'percentile_rank': self._calculate_percentile_rank(user_analytics, benchmarks),
                'performance_rating': self._calculate_performance_rating(user_analytics, benchmarks),
                'improvement_areas': self._identify_improvement_areas(user_analytics, benchmarks)
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error getting progress comparison for user {user_id}: {str(e)}")
            return {}
    
    def get_progress_visualization_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get data for progress visualization
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with visualization data
        """
        try:
            progress = self.get_progress(user_id)
            if not progress:
                return {}
            
            # Create timeline data
            timeline = []
            for event in progress.recent_events:
                timeline.append({
                    'timestamp': event.timestamp.isoformat(),
                    'event_type': event.event_type.value,
                    'description': self._get_event_description(event),
                    'data': event.event_data
                })
            
            # Create milestone progress data
            milestone_progress = []
            for milestone in progress.milestones:
                milestone_progress.append({
                    'id': milestone.milestone_id,
                    'name': milestone.name,
                    'description': milestone.description,
                    'completed': milestone.completed,
                    'progress_percentage': milestone.progress_percentage,
                    'reward': milestone.reward_description
                })
            
            # Create step progress data
            step_progress = []
            for step in OnboardingStep:
                step_progress.append({
                    'step': step.value,
                    'completed': step in progress.completed_steps,
                    'required': self._is_step_required(step, progress)
                })
            
            # Create feature progress data
            feature_progress = []
            for feature_name, feature_def in self.tiered_feature_manager.feature_definitions.items():
                can_unlock, analysis = self.tiered_feature_manager.check_tiered_feature_unlock(user_id, feature_name)
                feature_progress.append({
                    'name': feature_name,
                    'tier': feature_def.tier.value,
                    'unlocked': feature_name in progress.unlocked_features,
                    'can_unlock': can_unlock,
                    'unlock_score': analysis.get('unlock_score', 0.0),
                    'requirements_met': len(analysis.get('requirements_met', [])),
                    'total_requirements': len(feature_def.requirements)
                })
            
            visualization_data = {
                'user_id': user_id,
                'timeline': timeline,
                'milestone_progress': milestone_progress,
                'step_progress': step_progress,
                'feature_progress': feature_progress,
                'overall_progress': progress.progress_percentage,
                'current_tier': progress.current_tier.value,
                'status': progress.status.value
            }
            
            return visualization_data
            
        except Exception as e:
            logger.error(f"Error getting progress visualization data for user {user_id}: {str(e)}")
            return {}
    
    def _update_progress_data(self, progress: OnboardingProgress) -> OnboardingProgress:
        """Update progress with current data"""
        try:
            # Get current onboarding progress
            onboarding_progress = self.onboarding_manager.get_onboarding_progress(progress.user_id)
            if onboarding_progress:
                progress.current_step = onboarding_progress.current_step
                progress.completed_steps = onboarding_progress.completed_steps
                progress.unlocked_features = onboarding_progress.unlocked_features
                progress.progress_percentage = onboarding_progress.progress_percentage
            
            # Update current tier
            progress.current_tier = FeatureTier(self.tiered_feature_manager._get_current_tier(progress.user_id))
            
            # Update milestones
            progress.milestones = self._get_user_milestones(progress.user_id)
            
            # Update status
            progress.status = self._determine_progress_status(progress)
            
            # Update analytics
            progress.analytics = self.get_progress_analytics(progress.user_id)
            
            return progress
            
        except Exception as e:
            logger.error(f"Error updating progress data: {str(e)}")
            return progress
    
    def _get_user_milestones(self, user_id: int) -> List[ProgressMilestone]:
        """Get milestones for a user with completion status"""
        try:
            user_milestones = []
            
            for milestone_id, milestone in self.milestones.items():
                # Create a copy of the milestone
                user_milestone = ProgressMilestone(
                    milestone_id=milestone.milestone_id,
                    name=milestone.name,
                    description=milestone.description,
                    required_steps=milestone.required_steps,
                    required_features=milestone.required_features,
                    required_activities=milestone.required_activities,
                    required_days=milestone.required_days,
                    reward_description=milestone.reward_description
                )
                
                # Check completion status
                user_milestone.completed = self._check_milestone_completion(user_id, user_milestone)
                user_milestone.progress_percentage = self._calculate_milestone_progress(user_id, user_milestone)
                
                if user_milestone.completed:
                    user_milestone.completed_at = self._get_milestone_completion_time(user_id, milestone_id)
                
                user_milestones.append(user_milestone)
            
            return user_milestones
            
        except Exception as e:
            logger.error(f"Error getting user milestones for user {user_id}: {str(e)}")
            return []
    
    def _check_milestone_completion(self, user_id: int, milestone: ProgressMilestone) -> bool:
        """Check if a milestone is completed"""
        try:
            # Check step requirements
            progress = self.onboarding_manager.get_onboarding_progress(user_id)
            if not progress:
                return False
            
            for required_step in milestone.required_steps:
                if required_step not in progress.completed_steps:
                    return False
            
            # Check feature requirements
            for required_feature in milestone.required_features:
                if not self.onboarding_manager.check_feature_unlock(user_id, required_feature):
                    return False
            
            # Check activity requirements
            activity_count = self.tiered_feature_manager._get_user_activity_count(user_id)
            if activity_count < milestone.required_activities:
                return False
            
            # Check days requirements
            days_active = self.tiered_feature_manager._get_user_days_active(user_id)
            if days_active < milestone.required_days:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking milestone completion: {str(e)}")
            return False
    
    def _calculate_milestone_progress(self, user_id: int, milestone: ProgressMilestone) -> float:
        """Calculate progress percentage for a milestone"""
        try:
            total_requirements = 0
            met_requirements = 0
            
            # Step requirements
            progress = self.onboarding_manager.get_onboarding_progress(user_id)
            if progress:
                for required_step in milestone.required_steps:
                    total_requirements += 1
                    if required_step in progress.completed_steps:
                        met_requirements += 1
            
            # Feature requirements
            for required_feature in milestone.required_features:
                total_requirements += 1
                if self.onboarding_manager.check_feature_unlock(user_id, required_feature):
                    met_requirements += 1
            
            # Activity requirements
            total_requirements += 1
            activity_count = self.tiered_feature_manager._get_user_activity_count(user_id)
            if activity_count >= milestone.required_activities:
                met_requirements += 1
            
            # Days requirements
            total_requirements += 1
            days_active = self.tiered_feature_manager._get_user_days_active(user_id)
            if days_active >= milestone.required_days:
                met_requirements += 1
            
            if total_requirements == 0:
                return 0.0
            
            return (met_requirements / total_requirements) * 100.0
            
        except Exception as e:
            logger.error(f"Error calculating milestone progress: {str(e)}")
            return 0.0
    
    def _check_milestones(self, progress: OnboardingProgress):
        """Check for milestone completions and log events"""
        try:
            for milestone in progress.milestones:
                if not milestone.completed and self._check_milestone_completion(progress.user_id, milestone):
                    milestone.completed = True
                    milestone.completed_at = datetime.now()
                    
                    # Log milestone completion event
                    self._log_progress_event(progress.user_id, ProgressEventType.MILESTONE_REACHED, {
                        'milestone_id': milestone.milestone_id,
                        'milestone_name': milestone.name,
                        'reward': milestone.reward_description,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    logger.info(f"Milestone '{milestone.name}' completed for user {progress.user_id}")
            
        except Exception as e:
            logger.error(f"Error checking milestones: {str(e)}")
    
    def _log_progress_event(self, user_id: int, event_type: ProgressEventType, event_data: Dict[str, Any]):
        """Log a progress event"""
        try:
            event = ProgressEvent(
                event_id=f"{user_id}_{event_type.value}_{datetime.now().timestamp()}",
                user_id=user_id,
                event_type=event_type,
                event_data=event_data,
                timestamp=datetime.now()
            )
            
            # Save event to database
            self._save_progress_event(event)
            
            # Add to recent events (keep only last 10)
            progress = self.get_progress(user_id)
            if progress:
                progress.recent_events.append(event)
                if len(progress.recent_events) > 10:
                    progress.recent_events = progress.recent_events[-10:]
            
        except Exception as e:
            logger.error(f"Error logging progress event: {str(e)}")
    
    def _determine_progress_status(self, progress: OnboardingProgress) -> ProgressStatus:
        """Determine the current progress status"""
        try:
            if progress.completed_at:
                return ProgressStatus.COMPLETED
            
            if progress.progress_percentage >= 100.0:
                return ProgressStatus.COMPLETED
            
            # Check if stalled (no activity for 7 days)
            days_since_activity = (datetime.now() - progress.last_activity).days
            if days_since_activity > 7:
                return ProgressStatus.STALLED
            
            if progress.progress_percentage > 0:
                return ProgressStatus.IN_PROGRESS
            
            return ProgressStatus.NOT_STARTED
            
        except Exception as e:
            logger.error(f"Error determining progress status: {str(e)}")
            return ProgressStatus.IN_PROGRESS
    
    def _calculate_progress_trend(self, progress: OnboardingProgress) -> str:
        """Calculate progress trend"""
        try:
            # Simplified trend calculation
            if progress.progress_percentage >= 80:
                return 'excellent'
            elif progress.progress_percentage >= 60:
                return 'good'
            elif progress.progress_percentage >= 40:
                return 'fair'
            else:
                return 'needs_improvement'
        except Exception as e:
            logger.error(f"Error calculating progress trend: {str(e)}")
            return 'unknown'
    
    def _calculate_engagement_score(self, progress: OnboardingProgress) -> float:
        """Calculate engagement score"""
        try:
            # Simplified engagement calculation
            days_in_onboarding = (datetime.now() - progress.started_at).days
            if days_in_onboarding == 0:
                return 100.0
            
            activity_frequency = len(progress.recent_events) / days_in_onboarding
            return min(activity_frequency * 20, 100.0)  # Scale to 0-100
            
        except Exception as e:
            logger.error(f"Error calculating engagement score: {str(e)}")
            return 0.0
    
    def _estimate_completion_time(self, progress: OnboardingProgress) -> int:
        """Estimate completion time in days"""
        try:
            if progress.progress_percentage >= 100:
                return 0
            
            if progress.progress_percentage == 0:
                return 14  # Default estimate
            
            # Simple linear projection
            days_elapsed = (datetime.now() - progress.started_at).days
            if days_elapsed == 0:
                return 14
            
            rate = progress.progress_percentage / days_elapsed
            remaining_percentage = 100 - progress.progress_percentage
            
            if rate == 0:
                return 14
            
            estimated_days = remaining_percentage / rate
            return max(1, min(30, int(estimated_days)))  # Clamp between 1 and 30 days
            
        except Exception as e:
            logger.error(f"Error estimating completion time: {str(e)}")
            return 14
    
    def _generate_progress_recommendations(self, progress: OnboardingProgress) -> List[str]:
        """Generate progress recommendations"""
        try:
            recommendations = []
            
            if progress.progress_percentage < 20:
                recommendations.append("Complete the welcome step to get started")
            
            if len(progress.completed_steps) < 3:
                recommendations.append("Connect your Strava account to sync activities")
            
            if len(progress.unlocked_features) < 2:
                recommendations.append("Complete more onboarding steps to unlock features")
            
            if progress.status == ProgressStatus.STALLED:
                recommendations.append("Resume your onboarding to continue progress")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating progress recommendations: {str(e)}")
            return []
    
    def _calculate_percentile_rank(self, user_analytics: Dict[str, Any], benchmarks: Dict[str, Any]) -> float:
        """Calculate percentile rank"""
        try:
            # Simplified percentile calculation
            user_progress = user_analytics.get('overall_progress', 0)
            avg_progress = benchmarks.get('avg_progress_percentage', 50)
            
            if user_progress >= avg_progress:
                return 75.0
            else:
                return 25.0
                
        except Exception as e:
            logger.error(f"Error calculating percentile rank: {str(e)}")
            return 50.0
    
    def _calculate_performance_rating(self, user_analytics: Dict[str, Any], benchmarks: Dict[str, Any]) -> str:
        """Calculate performance rating"""
        try:
            user_progress = user_analytics.get('overall_progress', 0)
            avg_progress = benchmarks.get('avg_progress_percentage', 50)
            
            if user_progress >= avg_progress * 1.2:
                return 'excellent'
            elif user_progress >= avg_progress:
                return 'good'
            elif user_progress >= avg_progress * 0.8:
                return 'fair'
            else:
                return 'needs_improvement'
                
        except Exception as e:
            logger.error(f"Error calculating performance rating: {str(e)}")
            return 'unknown'
    
    def _identify_improvement_areas(self, user_analytics: Dict[str, Any], benchmarks: Dict[str, Any]) -> List[str]:
        """Identify areas for improvement"""
        try:
            areas = []
            
            user_progress = user_analytics.get('overall_progress', 0)
            avg_progress = benchmarks.get('avg_progress_percentage', 50)
            
            if user_progress < avg_progress:
                areas.append("Overall progress is below average")
            
            user_steps = user_analytics.get('steps_completed', 0)
            avg_steps = benchmarks.get('avg_steps_completed', 5)
            
            if user_steps < avg_steps:
                areas.append("Complete more onboarding steps")
            
            user_features = user_analytics.get('features_unlocked', 0)
            avg_features = benchmarks.get('avg_features_unlocked', 3)
            
            if user_features < avg_features:
                areas.append("Unlock more features")
            
            return areas
            
        except Exception as e:
            logger.error(f"Error identifying improvement areas: {str(e)}")
            return []
    
    def _get_event_description(self, event: ProgressEvent) -> str:
        """Get human-readable event description"""
        try:
            if event.event_type == ProgressEventType.STEP_COMPLETED:
                step_name = event.event_data.get('step', 'Unknown step')
                return f"Completed {step_name} step"
            elif event.event_type == ProgressEventType.FEATURE_UNLOCKED:
                feature_name = event.event_data.get('feature', 'Unknown feature')
                return f"Unlocked {feature_name} feature"
            elif event.event_type == ProgressEventType.MILESTONE_REACHED:
                milestone_name = event.event_data.get('milestone_name', 'Unknown milestone')
                return f"Reached {milestone_name} milestone"
            elif event.event_type == ProgressEventType.ONBOARDING_STARTED:
                return "Started onboarding process"
            elif event.event_type == ProgressEventType.ONBOARDING_COMPLETED:
                return "Completed onboarding process"
            else:
                return f"{event.event_type.value.replace('_', ' ').title()}"
                
        except Exception as e:
            logger.error(f"Error getting event description: {str(e)}")
            return "Unknown event"
    
    def _is_step_required(self, step: OnboardingStep, progress: OnboardingProgress) -> bool:
        """Check if a step is required for current progress"""
        try:
            # Simplified logic - in practice, this would be more sophisticated
            return step in [OnboardingStep.WELCOME, OnboardingStep.STRAVA_CONNECTED, OnboardingStep.FIRST_ACTIVITY]
        except Exception as e:
            logger.error(f"Error checking if step is required: {str(e)}")
            return False
    
    def _get_milestone_completion_time(self, user_id: int, milestone_id: str) -> Optional[datetime]:
        """Get milestone completion time"""
        try:
            # In practice, this would query the database for the actual completion time
            # For now, return current time as placeholder
            return datetime.now()
        except Exception as e:
            logger.error(f"Error getting milestone completion time: {str(e)}")
            return None
    
    # Database methods
    def _save_progress(self, progress: OnboardingProgress):
        """Save progress to database"""
        try:
            # Save progress data to the onboarding_analytics table instead of non-existent column
            progress_data = {
                'user_id': progress.user_id,
                'current_step': progress.current_step.value,
                'completed_steps': [step.value for step in progress.completed_steps],
                'unlocked_features': progress.unlocked_features,
                'current_tier': progress.current_tier.value,
                'progress_percentage': progress.progress_percentage,
                'started_at': progress.started_at.isoformat(),
                'last_activity': progress.last_activity.isoformat(),
                'status': progress.status.value
            }
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Use onboarding_analytics table for detailed progress tracking
                cursor.execute("""
                    INSERT INTO onboarding_analytics (user_id, event_type, event_data, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id, event_type, timestamp) 
                    DO UPDATE SET event_data = %s
                """, (
                    progress.user_id, 
                    'progress_update', 
                    json.dumps(progress_data), 
                    progress.last_activity,
                    json.dumps(progress_data)
                ))
                
                # Also update the main user_settings table with current step
                cursor.execute("""
                    UPDATE user_settings 
                    SET onboarding_step = %s, 
                        last_onboarding_activity = %s
                    WHERE id = %s
                """, (progress.current_step.value, progress.last_activity, progress.user_id))
            
        except Exception as e:
            logger.error(f"Error saving progress: {str(e)}")
    
    def _load_progress(self, user_id: int) -> Optional[OnboardingProgress]:
        """Load progress from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Load from onboarding_analytics table (most recent progress update)
                cursor.execute("""
                    SELECT event_data FROM onboarding_analytics 
                    WHERE user_id = %s AND event_type = 'progress_update'
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """, (user_id,))
                
                result = cursor.fetchone()
                if not result or not result[0]:
                    # Fallback: create basic progress from user_settings
                    cursor.execute("""
                        SELECT onboarding_step, last_onboarding_activity, created_at
                        FROM user_settings 
                        WHERE id = %s
                    """, (user_id,))
                    
                    user_result = cursor.fetchone()
                    if not user_result:
                        return None
                    
                    onboarding_step, last_activity, created_at = user_result
                    
                    # Create basic progress object
                    return OnboardingProgress(
                        user_id=user_id,
                        current_step=OnboardingStep(onboarding_step) if onboarding_step else OnboardingStep.WELCOME,
                        completed_steps=[],
                        unlocked_features=[],
                        current_tier=FeatureTier.BASIC,
                        progress_percentage=0,
                        started_at=created_at or datetime.now(),
                        last_activity=last_activity or datetime.now(),
                        status=OnboardingStatus.IN_PROGRESS
                    )
                
                progress_data = json.loads(result[0])
                
                progress = OnboardingProgress(
                    user_id=progress_data['user_id'],
                    current_step=OnboardingStep(progress_data['current_step']),
                    completed_steps=[OnboardingStep(step) for step in progress_data['completed_steps']],
                    unlocked_features=progress_data['unlocked_features'],
                    current_tier=FeatureTier(progress_data['current_tier']),
                    progress_percentage=progress_data['progress_percentage'],
                    started_at=datetime.fromisoformat(progress_data['started_at']),
                    last_activity=datetime.fromisoformat(progress_data['last_activity']),
                    status=ProgressStatus(progress_data['status'])
                )
                
                return progress
                
        except Exception as e:
            logger.error(f"Error loading progress: {str(e)}")
            return None
    
    def _save_progress_event(self, event: ProgressEvent):
        """Save progress event to database"""
        try:
            # In practice, this would save to a dedicated events table
            # For now, we'll log it
            logger.info(f"Progress event: {event.event_type.value} for user {event.user_id}")
            
        except Exception as e:
            logger.error(f"Error saving progress event: {str(e)}")


# Convenience functions for easy integration
progress_tracker = OnboardingProgressTracker()


def start_progress_tracking(user_id: int) -> bool:
    """Start progress tracking for a new user"""
    return progress_tracker.start_progress_tracking(user_id)


def get_progress(user_id: int) -> Optional[OnboardingProgress]:
    """Get comprehensive progress information for a user"""
    return progress_tracker.get_progress(user_id)


def update_progress(user_id: int, step: Optional[OnboardingStep] = None, 
                   feature: Optional[str] = None, event_type: Optional[ProgressEventType] = None,
                   event_data: Optional[Dict[str, Any]] = None) -> bool:
    """Update user progress"""
    return progress_tracker.update_progress(user_id, step, feature, event_type, event_data)


def get_progress_analytics(user_id: int) -> Dict[str, Any]:
    """Get detailed progress analytics for a user"""
    return progress_tracker.get_progress_analytics(user_id)


def get_progress_comparison(user_id: int) -> Dict[str, Any]:
    """Get progress comparison with other users"""
    return progress_tracker.get_progress_comparison(user_id)


def get_progress_visualization_data(user_id: int) -> Dict[str, Any]:
    """Get data for progress visualization"""
    return progress_tracker.get_progress_visualization_data(user_id)


if __name__ == "__main__":
    print("=" * 50)
    print("Onboarding Progress Tracker")
    print("=" * 50)
    print("Module loaded successfully!")
    print(f"Milestones defined: {len(progress_tracker.milestones)}")
    print(f"Event types: {[event.value for event in ProgressEventType]}")
    print(f"Progress statuses: {[status.value for status in ProgressStatus]}")
    print("=" * 50)


