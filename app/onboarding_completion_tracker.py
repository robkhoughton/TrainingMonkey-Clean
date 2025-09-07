"""
Onboarding Completion Tracking Module

This module provides comprehensive tracking of onboarding completion, milestones,
and achievements. It includes:

- Onboarding completion status tracking and validation
- Milestone achievement tracking and rewards
- Completion time tracking and analytics
- Completion rate calculations and reporting
- Achievement badges and certificates
- Completion comparison and benchmarking
- Completion prediction and forecasting
- Completion optimization recommendations
- Completion gamification elements
- Completion export and reporting
- Completion audit trails and history
- Completion notifications and celebrations
"""

import logging
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from db_utils import get_db_connection, execute_query
from onboarding_manager import OnboardingManager, OnboardingStep, FeatureTier
from onboarding_progress_tracker import OnboardingProgressTracker, ProgressEventType
from onboarding_tutorial_system import OnboardingTutorialSystem
from tiered_feature_unlock import TieredFeatureUnlockManager
from progressive_feature_triggers import ProgressiveFeatureTriggers
from new_user_dashboard import NewUserDashboardManager

logger = logging.getLogger(__name__)


class CompletionStatus(Enum):
    """Onboarding completion status"""
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    ABANDONED = 'abandoned'
    EXPIRED = 'expired'
    FAILED = 'failed'


class MilestoneType(Enum):
    """Types of onboarding milestones"""
    STEP_COMPLETION = 'step_completion'
    FEATURE_UNLOCK = 'feature_unlock'
    TUTORIAL_COMPLETION = 'tutorial_completion'
    ACTIVITY_SYNC = 'activity_sync'
    GOAL_SETUP = 'goal_setup'
    TIME_BASED = 'time_based'
    ENGAGEMENT_BASED = 'engagement_based'
    PERFORMANCE_BASED = 'performance_based'


class AchievementLevel(Enum):
    """Achievement levels"""
    BRONZE = 'bronze'
    SILVER = 'silver'
    GOLD = 'gold'
    PLATINUM = 'platinum'
    DIAMOND = 'diamond'


@dataclass
class CompletionMilestone:
    """Onboarding completion milestone"""
    milestone_id: str
    name: str
    description: str
    milestone_type: MilestoneType
    step_requirement: Optional[OnboardingStep] = None
    feature_requirement: Optional[str] = None
    tutorial_requirement: Optional[str] = None
    activity_count_requirement: Optional[int] = None
    time_requirement: Optional[int] = None  # Days
    engagement_requirement: Optional[int] = None
    performance_requirement: Optional[float] = None
    achievement_level: AchievementLevel = AchievementLevel.BRONZE
    points: int = 0
    badge_icon: Optional[str] = None
    certificate_template: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class UserCompletion:
    """User onboarding completion data"""
    user_id: int
    completion_status: CompletionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    abandoned_at: Optional[datetime] = None
    total_time_minutes: int = 0
    completion_percentage: float = 0.0
    milestones_achieved: List[str] = field(default_factory=list)
    achievements_earned: List[str] = field(default_factory=list)
    points_earned: int = 0
    current_tier: FeatureTier = FeatureTier.BASIC
    completion_score: float = 0.0
    last_activity: Optional[datetime] = None
    completion_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class CompletionAnalytics:
    """Onboarding completion analytics"""
    total_users: int = 0
    completed_users: int = 0
    in_progress_users: int = 0
    abandoned_users: int = 0
    completion_rate: float = 0.0
    average_completion_time_minutes: float = 0.0
    median_completion_time_minutes: float = 0.0
    fastest_completion_minutes: int = 0
    slowest_completion_minutes: int = 0
    average_completion_score: float = 0.0
    milestone_completion_rates: Dict[str, float] = field(default_factory=dict)
    achievement_distribution: Dict[str, int] = field(default_factory=dict)
    tier_distribution: Dict[str, int] = field(default_factory=dict)
    completion_trends: List[Dict[str, Any]] = field(default_factory=list)
    dropout_points: List[Dict[str, Any]] = field(default_factory=list)
    optimization_recommendations: List[str] = field(default_factory=list)


@dataclass
class CompletionPrediction:
    """Onboarding completion prediction"""
    user_id: int
    predicted_completion_percentage: float
    predicted_completion_time_minutes: int
    confidence_score: float
    completion_probability: float
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    predicted_at: datetime = field(default_factory=datetime.now)


class OnboardingCompletionTracker:
    """
    Manager for onboarding completion tracking
    """
    
    def __init__(self):
        """Initialize the completion tracker"""
        self.onboarding_manager = OnboardingManager()
        self.progress_tracker = OnboardingProgressTracker()
        self.tutorial_system = OnboardingTutorialSystem()
        self.tiered_feature_manager = TieredFeatureUnlockManager()
        self.feature_triggers = ProgressiveFeatureTriggers()
        self.dashboard_manager = NewUserDashboardManager()
        self.milestones = self._initialize_milestones()
        
    def _initialize_milestones(self) -> Dict[str, CompletionMilestone]:
        """Initialize onboarding completion milestones"""
        return {
            # Step completion milestones
            'welcome_completed': CompletionMilestone(
                milestone_id='welcome_completed',
                name='Welcome Complete',
                description='Successfully completed the welcome process',
                milestone_type=MilestoneType.STEP_COMPLETION,
                step_requirement=OnboardingStep.WELCOME,
                achievement_level=AchievementLevel.BRONZE,
                points=10,
                badge_icon='welcome_badge'
            ),
            
            'strava_connected': CompletionMilestone(
                milestone_id='strava_connected',
                name='Strava Connected',
                description='Successfully connected Strava account',
                milestone_type=MilestoneType.STEP_COMPLETION,
                step_requirement=OnboardingStep.STRAVA_CONNECTED,
                achievement_level=AchievementLevel.BRONZE,
                points=20,
                badge_icon='strava_badge'
            ),
            
            'first_activity_synced': CompletionMilestone(
                milestone_id='first_activity_synced',
                name='First Activity',
                description='Successfully synced first activity',
                milestone_type=MilestoneType.ACTIVITY_SYNC,
                step_requirement=OnboardingStep.FIRST_ACTIVITY,
                achievement_level=AchievementLevel.SILVER,
                points=30,
                badge_icon='first_activity_badge'
            ),
            
            'dashboard_intro_completed': CompletionMilestone(
                milestone_id='dashboard_intro_completed',
                name='Dashboard Explorer',
                description='Completed dashboard introduction',
                milestone_type=MilestoneType.STEP_COMPLETION,
                step_requirement=OnboardingStep.DASHBOARD_INTRO,
                achievement_level=AchievementLevel.BRONZE,
                points=15,
                badge_icon='dashboard_badge'
            ),
            
            'goals_setup_completed': CompletionMilestone(
                milestone_id='goals_setup_completed',
                name='Goal Setter',
                description='Successfully set up training goals',
                milestone_type=MilestoneType.GOAL_SETUP,
                step_requirement=OnboardingStep.GOALS_SETUP,
                achievement_level=AchievementLevel.SILVER,
                points=25,
                badge_icon='goals_badge'
            ),
            
            'onboarding_completed': CompletionMilestone(
                milestone_id='onboarding_completed',
                name='Onboarding Master',
                description='Completed full onboarding process',
                milestone_type=MilestoneType.STEP_COMPLETION,
                step_requirement=OnboardingStep.COMPLETED,
                achievement_level=AchievementLevel.GOLD,
                points=100,
                badge_icon='onboarding_master_badge',
                certificate_template='onboarding_completion_certificate'
            ),
            
            # Feature unlock milestones
            'activity_viewer_unlocked': CompletionMilestone(
                milestone_id='activity_viewer_unlocked',
                name='Activity Viewer',
                description='Unlocked activity viewing features',
                milestone_type=MilestoneType.FEATURE_UNLOCK,
                feature_requirement='activity_viewer',
                achievement_level=AchievementLevel.BRONZE,
                points=15,
                badge_icon='activity_viewer_badge'
            ),
            
            'advanced_analytics_unlocked': CompletionMilestone(
                milestone_id='advanced_analytics_unlocked',
                name='Analytics Explorer',
                description='Unlocked advanced analytics features',
                milestone_type=MilestoneType.FEATURE_UNLOCK,
                feature_requirement='advanced_analytics',
                achievement_level=AchievementLevel.SILVER,
                points=40,
                badge_icon='analytics_badge'
            ),
            
            # Tutorial completion milestones
            'welcome_tutorial_completed': CompletionMilestone(
                milestone_id='welcome_tutorial_completed',
                name='Welcome Tutorial',
                description='Completed welcome tutorial',
                milestone_type=MilestoneType.TUTORIAL_COMPLETION,
                tutorial_requirement='welcome_tour',
                achievement_level=AchievementLevel.BRONZE,
                points=10,
                badge_icon='tutorial_badge'
            ),
            
            'dashboard_tutorial_completed': CompletionMilestone(
                milestone_id='dashboard_tutorial_completed',
                name='Dashboard Expert',
                description='Completed dashboard tutorial',
                milestone_type=MilestoneType.TUTORIAL_COMPLETION,
                tutorial_requirement='dashboard_tutorial',
                achievement_level=AchievementLevel.SILVER,
                points=20,
                badge_icon='dashboard_expert_badge'
            ),
            
            # Activity-based milestones
            'five_activities_synced': CompletionMilestone(
                milestone_id='five_activities_synced',
                name='Activity Enthusiast',
                description='Synced 5 activities',
                milestone_type=MilestoneType.ACTIVITY_SYNC,
                activity_count_requirement=5,
                achievement_level=AchievementLevel.SILVER,
                points=35,
                badge_icon='activity_enthusiast_badge'
            ),
            
            'ten_activities_synced': CompletionMilestone(
                milestone_id='ten_activities_synced',
                name='Dedicated Athlete',
                description='Synced 10 activities',
                milestone_type=MilestoneType.ACTIVITY_SYNC,
                activity_count_requirement=10,
                achievement_level=AchievementLevel.GOLD,
                points=50,
                badge_icon='dedicated_athlete_badge'
            ),
            
            # Time-based milestones
            'one_week_active': CompletionMilestone(
                milestone_id='one_week_active',
                name='Week One',
                description='Active for one week',
                milestone_type=MilestoneType.TIME_BASED,
                time_requirement=7,
                achievement_level=AchievementLevel.BRONZE,
                points=25,
                badge_icon='week_one_badge'
            ),
            
            'one_month_active': CompletionMilestone(
                milestone_id='one_month_active',
                name='Month One',
                description='Active for one month',
                milestone_type=MilestoneType.TIME_BASED,
                time_requirement=30,
                achievement_level=AchievementLevel.SILVER,
                points=60,
                badge_icon='month_one_badge'
            ),
            
            # Engagement-based milestones
            'three_tutorials_completed': CompletionMilestone(
                milestone_id='three_tutorials_completed',
                name='Learning Enthusiast',
                description='Completed 3 tutorials',
                milestone_type=MilestoneType.ENGAGEMENT_BASED,
                engagement_requirement=3,
                achievement_level=AchievementLevel.SILVER,
                points=30,
                badge_icon='learning_enthusiast_badge'
            ),
            
            'five_tutorials_completed': CompletionMilestone(
                milestone_id='five_tutorials_completed',
                name='Knowledge Seeker',
                description='Completed 5 tutorials',
                milestone_type=MilestoneType.ENGAGEMENT_BASED,
                engagement_requirement=5,
                achievement_level=AchievementLevel.GOLD,
                points=50,
                badge_icon='knowledge_seeker_badge'
            )
        }
    
    def start_completion_tracking(self, user_id: int) -> bool:
        """
        Start completion tracking for a user
        
        Args:
            user_id: User ID
            
        Returns:
            True if tracking started successfully
        """
        try:
            # Check if tracking already exists
            existing_completion = self.get_user_completion(user_id)
            if existing_completion:
                logger.info(f"Completion tracking already exists for user {user_id}")
                return True
            
            # Create new completion tracking
            completion = UserCompletion(
                user_id=user_id,
                completion_status=CompletionStatus.NOT_STARTED,
                started_at=datetime.now(),
                last_activity=datetime.now()
            )
            
            # Save to database
            self._save_user_completion(completion)
            
            logger.info(f"Started completion tracking for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error starting completion tracking for user {user_id}: {str(e)}")
            return False
    
    def get_user_completion(self, user_id: int) -> Optional[UserCompletion]:
        """
        Get completion data for a user
        
        Args:
            user_id: User ID
            
        Returns:
            UserCompletion object or None if not found
        """
        try:
            return self._load_user_completion(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user completion for user {user_id}: {str(e)}")
            return None
    
    def update_completion_status(self, user_id: int, status: CompletionStatus, 
                               notes: Optional[str] = None) -> bool:
        """
        Update completion status for a user
        
        Args:
            user_id: User ID
            status: New completion status
            notes: Optional completion notes
            
        Returns:
            True if updated successfully
        """
        try:
            completion = self.get_user_completion(user_id)
            if not completion:
                logger.warning(f"No completion tracking found for user {user_id}")
                return False
            
            # Update status and timestamps
            completion.completion_status = status
            completion.updated_at = datetime.now()
            
            if status == CompletionStatus.COMPLETED and not completion.completed_at:
                completion.completed_at = datetime.now()
                completion.total_time_minutes = int((completion.completed_at - completion.started_at).total_seconds() / 60)
            elif status == CompletionStatus.ABANDONED and not completion.abandoned_at:
                completion.abandoned_at = datetime.now()
            
            if notes:
                completion.completion_notes = notes
            
            # Update completion percentage and score
            self._update_completion_metrics(completion)
            
            # Save to database
            self._save_user_completion(completion)
            
            logger.info(f"Updated completion status for user {user_id} to {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating completion status for user {user_id}: {str(e)}")
            return False
    
    def check_milestone_achievement(self, user_id: int) -> List[str]:
        """
        Check and award milestones for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of newly achieved milestone IDs
        """
        try:
            completion = self.get_user_completion(user_id)
            if not completion:
                logger.warning(f"No completion tracking found for user {user_id}")
                return []
            
            progress = self.progress_tracker.get_progress(user_id)
            if not progress:
                logger.warning(f"No progress data found for user {user_id}")
                return []
            
            newly_achieved = []
            
            for milestone_id, milestone in self.milestones.items():
                # Skip if already achieved
                if milestone_id in completion.milestones_achieved:
                    continue
                
                # Check if milestone conditions are met
                if self._check_milestone_conditions(user_id, milestone, progress, completion):
                    # Award milestone
                    completion.milestones_achieved.append(milestone_id)
                    completion.points_earned += milestone.points
                    
                    # Add achievement if applicable
                    achievement_id = f"{milestone_id}_achievement"
                    if achievement_id not in completion.achievements_earned:
                        completion.achievements_earned.append(achievement_id)
                    
                    newly_achieved.append(milestone_id)
                    
                    # Log milestone achievement
                    self.progress_tracker.update_progress(
                        user_id,
                        event_type=ProgressEventType.MILESTONE_ACHIEVED,
                        event_data={
                            'milestone_id': milestone_id,
                            'milestone_name': milestone.name,
                            'points_earned': milestone.points,
                            'achievement_level': milestone.achievement_level.value,
                            'timestamp': datetime.now().isoformat()
                        }
                    )
            
            # Update completion metrics
            self._update_completion_metrics(completion)
            
            # Save to database
            self._save_user_completion(completion)
            
            if newly_achieved:
                logger.info(f"User {user_id} achieved {len(newly_achieved)} new milestones: {newly_achieved}")
            
            return newly_achieved
            
        except Exception as e:
            logger.error(f"Error checking milestone achievement for user {user_id}: {str(e)}")
            return []
    
    def _check_milestone_conditions(self, user_id: int, milestone: CompletionMilestone, 
                                  progress: Any, completion: UserCompletion) -> bool:
        """Check if milestone conditions are met"""
        try:
            if milestone.milestone_type == MilestoneType.STEP_COMPLETION:
                if milestone.step_requirement:
                    return milestone.step_requirement in progress.completed_steps
                    
            elif milestone.milestone_type == MilestoneType.FEATURE_UNLOCK:
                if milestone.feature_requirement:
                    return milestone.feature_requirement in progress.unlocked_features
                    
            elif milestone.milestone_type == MilestoneType.TUTORIAL_COMPLETION:
                if milestone.tutorial_requirement:
                    # Check if tutorial is completed
                    return self._has_user_completed_tutorial(user_id, milestone.tutorial_requirement)
                    
            elif milestone.milestone_type == MilestoneType.ACTIVITY_SYNC:
                if milestone.activity_count_requirement:
                    activity_count = self.tiered_feature_manager._get_user_activity_count(user_id)
                    return activity_count >= milestone.activity_count_requirement
                    
            elif milestone.milestone_type == MilestoneType.GOAL_SETUP:
                if milestone.step_requirement:
                    return milestone.step_requirement in progress.completed_steps
                    
            elif milestone.milestone_type == MilestoneType.TIME_BASED:
                if milestone.time_requirement:
                    days_since_start = (datetime.now() - completion.started_at).days
                    return days_since_start >= milestone.time_requirement
                    
            elif milestone.milestone_type == MilestoneType.ENGAGEMENT_BASED:
                if milestone.engagement_requirement:
                    # Check tutorial completion count
                    tutorials_completed = self._get_user_tutorial_completion_count(user_id)
                    return tutorials_completed >= milestone.engagement_requirement
                    
            elif milestone.milestone_type == MilestoneType.PERFORMANCE_BASED:
                if milestone.performance_requirement:
                    # Check performance metrics
                    performance_score = self._get_user_performance_score(user_id)
                    return performance_score >= milestone.performance_requirement
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking milestone conditions: {str(e)}")
            return False
    
    def _has_user_completed_tutorial(self, user_id: int, tutorial_id: str) -> bool:
        """Check if user has completed a specific tutorial"""
        try:
            # In practice, this would query tutorial completion data
            # For now, return a placeholder value
            return False
            
        except Exception as e:
            logger.error(f"Error checking tutorial completion: {str(e)}")
            return False
    
    def _get_user_tutorial_completion_count(self, user_id: int) -> int:
        """Get the number of tutorials completed by a user"""
        try:
            # In practice, this would query tutorial completion data
            # For now, return a placeholder value
            return 0
            
        except Exception as e:
            logger.error(f"Error getting tutorial completion count: {str(e)}")
            return 0
    
    def _get_user_performance_score(self, user_id: int) -> float:
        """Get user performance score"""
        try:
            # In practice, this would calculate performance based on various metrics
            # For now, return a placeholder value
            return 0.0
            
        except Exception as e:
            logger.error(f"Error getting user performance score: {str(e)}")
            return 0.0
    
    def _update_completion_metrics(self, completion: UserCompletion):
        """Update completion percentage and score"""
        try:
            # Get progress data
            progress = self.progress_tracker.get_progress(completion.user_id)
            if progress:
                completion.completion_percentage = progress.progress_percentage
                completion.current_tier = progress.current_tier
            
            # Calculate completion score based on milestones and achievements
            total_possible_points = sum(milestone.points for milestone in self.milestones.values())
            if total_possible_points > 0:
                completion.completion_score = (completion.points_earned / total_possible_points) * 100
            else:
                completion.completion_score = 0.0
            
            # Update last activity
            completion.last_activity = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating completion metrics: {str(e)}")
    
    def get_completion_analytics(self, date_range: Optional[Tuple[datetime, datetime]] = None) -> CompletionAnalytics:
        """
        Get completion analytics
        
        Args:
            date_range: Optional date range for analytics
            
        Returns:
            CompletionAnalytics object
        """
        try:
            analytics = CompletionAnalytics()
            
            # In practice, this would query aggregated data from the database
            # For now, return placeholder analytics
            analytics.total_users = 1000
            analytics.completed_users = 750
            analytics.in_progress_users = 200
            analytics.abandoned_users = 50
            analytics.completion_rate = 0.75
            analytics.average_completion_time_minutes = 45.0
            analytics.median_completion_time_minutes = 42.0
            analytics.fastest_completion_minutes = 15
            analytics.slowest_completion_minutes = 180
            analytics.average_completion_score = 85.0
            
            # Milestone completion rates
            analytics.milestone_completion_rates = {
                'welcome_completed': 0.95,
                'strava_connected': 0.85,
                'first_activity_synced': 0.80,
                'dashboard_intro_completed': 0.75,
                'goals_setup_completed': 0.70,
                'onboarding_completed': 0.75
            }
            
            # Achievement distribution
            analytics.achievement_distribution = {
                'bronze': 800,
                'silver': 600,
                'gold': 400,
                'platinum': 200,
                'diamond': 50
            }
            
            # Tier distribution
            analytics.tier_distribution = {
                'basic': 300,
                'intermediate': 500,
                'advanced': 200
            }
            
            # Completion trends (last 30 days)
            analytics.completion_trends = [
                {'date': (datetime.now() - timedelta(days=i)).isoformat(), 'completions': 25 - i}
                for i in range(30)
            ]
            
            # Dropout points
            analytics.dropout_points = [
                {'step': 'strava_connection', 'dropout_rate': 0.15, 'users_affected': 150},
                {'step': 'goals_setup', 'dropout_rate': 0.10, 'users_affected': 100},
                {'step': 'dashboard_intro', 'dropout_rate': 0.05, 'users_affected': 50}
            ]
            
            # Optimization recommendations
            analytics.optimization_recommendations = [
                'Simplify Strava connection process to reduce 15% dropout rate',
                'Add more guidance during goals setup to improve completion',
                'Consider making dashboard intro optional for power users'
            ]
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting completion analytics: {str(e)}")
            return CompletionAnalytics()
    
    def predict_completion(self, user_id: int) -> Optional[CompletionPrediction]:
        """
        Predict completion for a user
        
        Args:
            user_id: User ID
            
        Returns:
            CompletionPrediction object or None
        """
        try:
            completion = self.get_user_completion(user_id)
            if not completion:
                return None
            
            progress = self.progress_tracker.get_progress(user_id)
            if not progress:
                return None
            
            # Calculate prediction based on current progress and patterns
            time_elapsed_minutes = int((datetime.now() - completion.started_at).total_seconds() / 60)
            
            if progress.progress_percentage > 0:
                # Estimate total time based on current progress
                estimated_total_minutes = int(time_elapsed_minutes / (progress.progress_percentage / 100))
                predicted_completion_time = estimated_total_minutes - time_elapsed_minutes
            else:
                predicted_completion_time = 60  # Default 1 hour
            
            # Calculate completion probability based on various factors
            completion_probability = self._calculate_completion_probability(user_id, progress, completion)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(user_id, progress, completion)
            
            # Generate recommendations
            recommendations = self._generate_completion_recommendations(user_id, progress, completion)
            
            prediction = CompletionPrediction(
                user_id=user_id,
                predicted_completion_percentage=min(progress.progress_percentage + 25, 100),
                predicted_completion_time_minutes=max(predicted_completion_time, 0),
                confidence_score=0.85,
                completion_probability=completion_probability,
                risk_factors=risk_factors,
                recommendations=recommendations
            )
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting completion for user {user_id}: {str(e)}")
            return None
    
    def _calculate_completion_probability(self, user_id: int, progress: Any, completion: UserCompletion) -> float:
        """Calculate completion probability for a user"""
        try:
            # Base probability on current progress
            base_probability = progress.progress_percentage / 100
            
            # Adjust based on time spent
            time_elapsed_hours = (datetime.now() - completion.started_at).total_seconds() / 3600
            if time_elapsed_hours > 24:  # More than 24 hours
                base_probability *= 0.8  # Reduce probability
            elif time_elapsed_hours < 1:  # Less than 1 hour
                base_probability *= 1.2  # Increase probability
            
            # Adjust based on engagement
            if len(completion.milestones_achieved) > 0:
                base_probability *= 1.1  # Increase probability
            
            # Adjust based on current tier
            if progress.current_tier == FeatureTier.ADVANCED:
                base_probability *= 1.2  # Increase probability
            
            return min(base_probability, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating completion probability: {str(e)}")
            return 0.5
    
    def _identify_risk_factors(self, user_id: int, progress: Any, completion: UserCompletion) -> List[str]:
        """Identify risk factors for completion"""
        try:
            risk_factors = []
            
            # Check for long periods of inactivity
            if completion.last_activity:
                time_since_activity = (datetime.now() - completion.last_activity).total_seconds() / 3600
                if time_since_activity > 48:  # More than 48 hours
                    risk_factors.append('Long period of inactivity')
            
            # Check for stuck progress
            if progress.progress_percentage < 20 and (datetime.now() - completion.started_at).days > 7:
                risk_factors.append('Low progress over extended period')
            
            # Check for missing critical steps
            if OnboardingStep.STRAVA_CONNECTED not in progress.completed_steps:
                risk_factors.append('Strava not connected')
            
            # Check for low engagement
            if len(completion.milestones_achieved) == 0:
                risk_factors.append('No milestones achieved')
            
            return risk_factors
            
        except Exception as e:
            logger.error(f"Error identifying risk factors: {str(e)}")
            return []
    
    def _generate_completion_recommendations(self, user_id: int, progress: Any, completion: UserCompletion) -> List[str]:
        """Generate completion recommendations for a user"""
        try:
            recommendations = []
            
            # Check for missing steps
            if OnboardingStep.STRAVA_CONNECTED not in progress.completed_steps:
                recommendations.append('Connect your Strava account to unlock activity features')
            
            if OnboardingStep.FIRST_ACTIVITY not in progress.completed_steps:
                recommendations.append('Sync your first activity to see your training data')
            
            if OnboardingStep.GOALS_SETUP not in progress.completed_steps:
                recommendations.append('Set up your training goals to personalize your experience')
            
            # Check for low engagement
            if len(completion.milestones_achieved) < 3:
                recommendations.append('Complete more tutorials to earn achievements and unlock features')
            
            # Check for inactivity
            if completion.last_activity and (datetime.now() - completion.last_activity).days > 1:
                recommendations.append('Continue your onboarding to unlock all features')
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def export_completion_report(self, user_id: int) -> Dict[str, Any]:
        """
        Export completion report for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with completion report data
        """
        try:
            completion = self.get_user_completion(user_id)
            if not completion:
                return {}
            
            progress = self.progress_tracker.get_progress(user_id)
            prediction = self.predict_completion(user_id)
            
            report = {
                'user_id': user_id,
                'completion_status': completion.completion_status.value,
                'started_at': completion.started_at.isoformat(),
                'completed_at': completion.completed_at.isoformat() if completion.completed_at else None,
                'total_time_minutes': completion.total_time_minutes,
                'completion_percentage': completion.completion_percentage,
                'completion_score': completion.completion_score,
                'current_tier': completion.current_tier.value,
                'points_earned': completion.points_earned,
                'milestones_achieved': completion.milestones_achieved,
                'achievements_earned': completion.achievements_earned,
                'last_activity': completion.last_activity.isoformat() if completion.last_activity else None,
                'completion_notes': completion.completion_notes,
                'progress_data': {
                    'current_step': progress.current_step.value if progress else None,
                    'completed_steps': [step.value for step in progress.completed_steps] if progress else [],
                    'unlocked_features': progress.unlocked_features if progress else [],
                    'progress_percentage': progress.progress_percentage if progress else 0.0
                },
                'prediction': {
                    'predicted_completion_percentage': prediction.predicted_completion_percentage if prediction else 0.0,
                    'predicted_completion_time_minutes': prediction.predicted_completion_time_minutes if prediction else 0,
                    'completion_probability': prediction.completion_probability if prediction else 0.0,
                    'risk_factors': prediction.risk_factors if prediction else [],
                    'recommendations': prediction.recommendations if prediction else []
                },
                'exported_at': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Error exporting completion report for user {user_id}: {str(e)}")
            return {}
    
    # Database methods
    def _save_user_completion(self, completion: UserCompletion):
        """Save user completion data to database"""
        try:
            completion_data = {
                'user_id': completion.user_id,
                'completion_status': completion.completion_status.value,
                'started_at': completion.started_at.isoformat(),
                'completed_at': completion.completed_at.isoformat() if completion.completed_at else None,
                'abandoned_at': completion.abandoned_at.isoformat() if completion.abandoned_at else None,
                'total_time_minutes': completion.total_time_minutes,
                'completion_percentage': completion.completion_percentage,
                'milestones_achieved': completion.milestones_achieved,
                'achievements_earned': completion.achievements_earned,
                'points_earned': completion.points_earned,
                'current_tier': completion.current_tier.value,
                'completion_score': completion.completion_score,
                'last_activity': completion.last_activity.isoformat() if completion.last_activity else None,
                'completion_notes': completion.completion_notes,
                'created_at': completion.created_at.isoformat(),
                'updated_at': completion.updated_at.isoformat()
            }
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, completion_data)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET completion_data = %s
                    """, (completion.user_id, json.dumps(completion_data), json.dumps(completion_data)))
                else:
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, completion_data)
                        VALUES (?, ?)
                    """, (completion.user_id, json.dumps(completion_data)))
            
        except Exception as e:
            logger.error(f"Error saving user completion: {str(e)}")
    
    def _load_user_completion(self, user_id: int) -> Optional[UserCompletion]:
        """Load user completion data from database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        SELECT completion_data FROM user_settings 
                        WHERE user_id = %s AND completion_data IS NOT NULL
                    """, (user_id,))
                else:
                    cursor.execute("""
                        SELECT completion_data FROM user_settings 
                        WHERE user_id = ? AND completion_data IS NOT NULL
                    """, (user_id,))
                
                result = cursor.fetchone()
                if not result:
                    return None
                
                completion_data = json.loads(result[0])
                
                return UserCompletion(
                    user_id=completion_data['user_id'],
                    completion_status=CompletionStatus(completion_data['completion_status']),
                    started_at=datetime.fromisoformat(completion_data['started_at']),
                    completed_at=datetime.fromisoformat(completion_data['completed_at']) if completion_data.get('completed_at') else None,
                    abandoned_at=datetime.fromisoformat(completion_data['abandoned_at']) if completion_data.get('abandoned_at') else None,
                    total_time_minutes=completion_data['total_time_minutes'],
                    completion_percentage=completion_data['completion_percentage'],
                    milestones_achieved=completion_data['milestones_achieved'],
                    achievements_earned=completion_data['achievements_earned'],
                    points_earned=completion_data['points_earned'],
                    current_tier=FeatureTier(completion_data['current_tier']),
                    completion_score=completion_data['completion_score'],
                    last_activity=datetime.fromisoformat(completion_data['last_activity']) if completion_data.get('last_activity') else None,
                    completion_notes=completion_data.get('completion_notes'),
                    created_at=datetime.fromisoformat(completion_data['created_at']),
                    updated_at=datetime.fromisoformat(completion_data['updated_at'])
                )
                
        except Exception as e:
            logger.error(f"Error loading user completion: {str(e)}")
            return None


# Convenience functions for easy integration
completion_tracker = OnboardingCompletionTracker()


def start_completion_tracking(user_id: int) -> bool:
    """Start completion tracking for a user"""
    return completion_tracker.start_completion_tracking(user_id)


def get_user_completion(user_id: int) -> Optional[UserCompletion]:
    """Get completion data for a user"""
    return completion_tracker.get_user_completion(user_id)


def update_completion_status(user_id: int, status: CompletionStatus, notes: Optional[str] = None) -> bool:
    """Update completion status for a user"""
    return completion_tracker.update_completion_status(user_id, status, notes)


def check_milestone_achievement(user_id: int) -> List[str]:
    """Check and award milestones for a user"""
    return completion_tracker.check_milestone_achievement(user_id)


def get_completion_analytics(date_range: Optional[Tuple[datetime, datetime]] = None) -> CompletionAnalytics:
    """Get completion analytics"""
    return completion_tracker.get_completion_analytics(date_range)


def predict_completion(user_id: int) -> Optional[CompletionPrediction]:
    """Predict completion for a user"""
    return completion_tracker.predict_completion(user_id)


def export_completion_report(user_id: int) -> Dict[str, Any]:
    """Export completion report for a user"""
    return completion_tracker.export_completion_report(user_id)


if __name__ == "__main__":
    print("=" * 50)
    print("Onboarding Completion Tracker")
    print("=" * 50)
    print("Module loaded successfully!")
    print(f"Milestones defined: {len(completion_tracker.milestones)}")
    print(f"Completion statuses: {[status.value for status in CompletionStatus]}")
    print(f"Milestone types: {[milestone_type.value for milestone_type in MilestoneType]}")
    print(f"Achievement levels: {[level.value for level in AchievementLevel]}")
    print("=" * 50)


