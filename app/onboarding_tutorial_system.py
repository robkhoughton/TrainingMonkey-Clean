"""
Onboarding Tutorial System Module

This module provides comprehensive interactive tutorials and guided tours for the
progressive onboarding system. It includes:

- Interactive tutorial overlays and tooltips
- Guided tours for different onboarding steps
- Contextual help and hints
- Tutorial progress tracking and persistence
- Customizable tutorial content and flow
- Tutorial analytics and completion tracking
- Tutorial skip and resume functionality
- Tutorial personalization based on user progress
- Tutorial accessibility features
- Tutorial localization support
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
from tiered_feature_unlock import TieredFeatureUnlockManager

logger = logging.getLogger(__name__)


class TutorialType(Enum):
    """Types of tutorials"""
    OVERLAY = 'overlay'
    TOOLTIP = 'tooltip'
    MODAL = 'modal'
    SIDEBAR = 'sidebar'
    INLINE = 'inline'
    WALKTHROUGH = 'walkthrough'
    INTERACTIVE = 'interactive'


class TutorialTrigger(Enum):
    """Tutorial trigger conditions"""
    AUTOMATIC = 'automatic'
    MANUAL = 'manual'
    ON_STEP_ENTER = 'on_step_enter'
    ON_FEATURE_ACCESS = 'on_feature_access'
    ON_ERROR = 'on_error'
    ON_INACTIVITY = 'on_inactivity'
    SCHEDULED = 'scheduled'


class TutorialStatus(Enum):
    """Tutorial status enumeration"""
    NOT_STARTED = 'not_started'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    SKIPPED = 'skipped'
    PAUSED = 'paused'
    FAILED = 'failed'


@dataclass
class TutorialStep:
    """Individual tutorial step"""
    step_id: str
    title: str
    content: str
    target_element: Optional[str] = None
    position: str = 'bottom'  # top, bottom, left, right, center
    action_required: bool = False
    action_text: Optional[str] = None
    action_url: Optional[str] = None
    hints: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration: int = 30  # seconds
    interactive: bool = False
    skip_allowed: bool = True
    completion_criteria: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tutorial:
    """Complete tutorial definition"""
    tutorial_id: str
    name: str
    description: str
    tutorial_type: TutorialType
    trigger: TutorialTrigger
    target_step: Optional[OnboardingStep] = None
    target_feature: Optional[str] = None
    steps: List[TutorialStep] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_duration: int = 120  # seconds
    difficulty_level: str = 'beginner'  # beginner, intermediate, advanced
    category: str = 'general'
    tags: List[str] = field(default_factory=list)
    version: str = '1.0'
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class TutorialSession:
    """Tutorial session data"""
    session_id: str
    user_id: int
    tutorial_id: str
    current_step_index: int = 0
    completed_steps: List[str] = field(default_factory=list)
    skipped_steps: List[str] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: TutorialStatus = TutorialStatus.NOT_STARTED
    progress_percentage: float = 0.0
    time_spent: int = 0  # seconds
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    user_feedback: Optional[Dict[str, Any]] = None


@dataclass
class TutorialAnalytics:
    """Tutorial analytics data"""
    tutorial_id: str
    total_sessions: int = 0
    completed_sessions: int = 0
    skipped_sessions: int = 0
    average_completion_time: float = 0.0
    average_progress_percentage: float = 0.0
    user_satisfaction_score: float = 0.0
    common_dropout_points: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class OnboardingTutorialSystem:
    """
    Comprehensive onboarding tutorial system
    """
    
    def __init__(self):
        """Initialize the tutorial system"""
        self.onboarding_manager = OnboardingManager()
        self.progress_tracker = OnboardingProgressTracker()
        self.tiered_feature_manager = TieredFeatureUnlockManager()
        self.tutorials = self._initialize_tutorials()
        self.active_sessions = {}
        
    def _initialize_tutorials(self) -> Dict[str, Tutorial]:
        """Initialize tutorial definitions"""
        return {
            'welcome_tour': Tutorial(
                tutorial_id='welcome_tour',
                name='Welcome Tour',
                description='Get started with your training journey',
                tutorial_type=TutorialType.WALKTHROUGH,
                trigger=TutorialTrigger.AUTOMATIC,
                target_step=OnboardingStep.WELCOME,
                steps=[
                    TutorialStep(
                        step_id='welcome_intro',
                        title='Welcome to TrainingMonkey!',
                        content='Welcome to your personalized training companion. Let\'s take a quick tour to get you started.',
                        position='center',
                        action_required=False,
                        estimated_duration=15
                    ),
                    TutorialStep(
                        step_id='strava_connection',
                        title='Connect Your Strava Account',
                        content='Connect your Strava account to automatically sync your activities and get personalized insights.',
                        target_element='#strava-connect-btn',
                        position='bottom',
                        action_required=True,
                        action_text='Connect Strava',
                        action_url='/connect-strava',
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='dashboard_overview',
                        title='Your Dashboard',
                        content='This is your main dashboard where you\'ll see your training progress, recent activities, and personalized recommendations.',
                        target_element='#dashboard-container',
                        position='top',
                        action_required=False,
                        estimated_duration=20
                    )
                ],
                estimated_duration=65,
                difficulty_level='beginner',
                category='onboarding'
            ),
            
            'strava_connection_guide': Tutorial(
                tutorial_id='strava_connection_guide',
                name='Strava Connection Guide',
                description='Step-by-step guide to connecting your Strava account',
                tutorial_type=TutorialType.INTERACTIVE,
                trigger=TutorialTrigger.ON_STEP_ENTER,
                target_step=OnboardingStep.STRAVA_CONNECTED,
                steps=[
                    TutorialStep(
                        step_id='strava_explanation',
                        title='Why Connect Strava?',
                        content='Connecting your Strava account allows us to analyze your training patterns and provide personalized recommendations.',
                        position='center',
                        action_required=False,
                        estimated_duration=20
                    ),
                    TutorialStep(
                        step_id='connection_process',
                        title='Connection Process',
                        content='Click the "Connect Strava" button below. You\'ll be redirected to Strava to authorize the connection.',
                        target_element='#strava-connect-btn',
                        position='bottom',
                        action_required=True,
                        action_text='Connect Now',
                        action_url='/connect-strava',
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='permissions_explanation',
                        title='What We Access',
                        content='We only access your activity data to provide training insights. We never post to your Strava account.',
                        position='center',
                        action_required=False,
                        estimated_duration=15
                    )
                ],
                estimated_duration=65,
                difficulty_level='beginner',
                category='strava'
            ),
            
            'first_activity_tutorial': Tutorial(
                tutorial_id='first_activity_tutorial',
                name='First Activity Tutorial',
                description='Learn how to view and analyze your first synced activity',
                tutorial_type=TutorialType.OVERLAY,
                trigger=TutorialTrigger.ON_FEATURE_ACCESS,
                target_feature='activity_viewer',
                steps=[
                    TutorialStep(
                        step_id='activity_sync_notification',
                        title='Activity Synced!',
                        content='Great! Your first activity has been synced from Strava. Let\'s explore what you can learn from it.',
                        position='center',
                        action_required=False,
                        estimated_duration=15
                    ),
                    TutorialStep(
                        step_id='activity_details',
                        title='Activity Details',
                        content='Here you can see detailed information about your activity including distance, duration, pace, and more.',
                        target_element='#activity-details',
                        position='right',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='training_load',
                        title='Training Load',
                        content='This shows your training load for this activity. Training load helps track your fitness and fatigue levels.',
                        target_element='#training-load',
                        position='left',
                        action_required=False,
                        estimated_duration=20
                    ),
                    TutorialStep(
                        step_id='next_steps',
                        title='What\'s Next?',
                        content='Continue syncing activities to unlock more features and get personalized training recommendations.',
                        position='center',
                        action_required=False,
                        estimated_duration=15
                    )
                ],
                estimated_duration=75,
                difficulty_level='beginner',
                category='activities'
            ),
            
            'dashboard_tutorial': Tutorial(
                tutorial_id='dashboard_tutorial',
                name='Dashboard Tutorial',
                description='Learn how to navigate and use your dashboard effectively',
                tutorial_type=TutorialType.WALKTHROUGH,
                trigger=TutorialTrigger.MANUAL,
                target_step=OnboardingStep.DASHBOARD_INTRO,
                steps=[
                    TutorialStep(
                        step_id='dashboard_layout',
                        title='Dashboard Layout',
                        content='Your dashboard is organized into sections: Recent Activities, Training Load, Goals, and Recommendations.',
                        target_element='#dashboard-layout',
                        position='top',
                        action_required=False,
                        estimated_duration=20
                    ),
                    TutorialStep(
                        step_id='recent_activities',
                        title='Recent Activities',
                        content='This section shows your most recent activities. Click on any activity to view detailed analysis.',
                        target_element='#recent-activities',
                        position='bottom',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='training_load_chart',
                        title='Training Load Chart',
                        content='This chart shows your training load over time. Green zones indicate good training balance.',
                        target_element='#training-load-chart',
                        position='left',
                        action_required=False,
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='goals_section',
                        title='Goals Section',
                        content='Set and track your training goals here. Goals help keep you motivated and focused.',
                        target_element='#goals-section',
                        position='right',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='recommendations',
                        title='AI Recommendations',
                        content='Get personalized training recommendations based on your activities and goals.',
                        target_element='#recommendations',
                        position='bottom',
                        action_required=False,
                        estimated_duration=20
                    )
                ],
                estimated_duration=120,
                difficulty_level='intermediate',
                category='dashboard'
            ),
            
            'features_tour': Tutorial(
                tutorial_id='features_tour',
                name='Features Tour',
                description='Explore all available features and capabilities',
                tutorial_type=TutorialType.MODAL,
                trigger=TutorialTrigger.MANUAL,
                target_step=OnboardingStep.FEATURES_TOUR,
                steps=[
                    TutorialStep(
                        step_id='features_overview',
                        title='Available Features',
                        content='TrainingMonkey offers many features to enhance your training experience. Let\'s explore them!',
                        position='center',
                        action_required=False,
                        estimated_duration=15
                    ),
                    TutorialStep(
                        step_id='analytics_features',
                        title='Analytics & Insights',
                        content='Advanced analytics help you understand your training patterns and identify areas for improvement.',
                        target_element='#analytics-features',
                        position='top',
                        action_required=False,
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='goal_tracking',
                        title='Goal Tracking',
                        content='Set custom goals and track your progress towards achieving them.',
                        target_element='#goal-tracking',
                        position='bottom',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='recommendations_engine',
                        title='AI Recommendations',
                        content='Get personalized training recommendations based on your data and goals.',
                        target_element='#recommendations-engine',
                        position='left',
                        action_required=False,
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='journal_feature',
                        title='Training Journal',
                        content='Keep a digital training journal to track your thoughts and progress.',
                        target_element='#journal-feature',
                        position='right',
                        action_required=False,
                        estimated_duration=25
                    )
                ],
                estimated_duration=125,
                difficulty_level='intermediate',
                category='features'
            ),
            
            'goals_setup_tutorial': Tutorial(
                tutorial_id='goals_setup_tutorial',
                name='Goals Setup Tutorial',
                description='Learn how to set up and manage your training goals',
                tutorial_type=TutorialType.INTERACTIVE,
                trigger=TutorialTrigger.ON_STEP_ENTER,
                target_step=OnboardingStep.GOALS_SETUP,
                steps=[
                    TutorialStep(
                        step_id='goals_importance',
                        title='Why Set Goals?',
                        content='Setting clear, achievable goals helps you stay motivated and track your progress effectively.',
                        position='center',
                        action_required=False,
                        estimated_duration=20
                    ),
                    TutorialStep(
                        step_id='goal_types',
                        title='Types of Goals',
                        content='You can set different types of goals: distance goals, time goals, frequency goals, and performance goals.',
                        target_element='#goal-types',
                        position='top',
                        action_required=False,
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='create_first_goal',
                        title='Create Your First Goal',
                        content='Let\'s create your first training goal. Choose something achievable but challenging.',
                        target_element='#create-goal-form',
                        position='bottom',
                        action_required=True,
                        action_text='Create Goal',
                        action_url='/goals/create',
                        estimated_duration=45
                    ),
                    TutorialStep(
                        step_id='goal_tracking',
                        title='Track Your Progress',
                        content='Once created, you can track your progress towards your goals on your dashboard.',
                        target_element='#goal-progress',
                        position='right',
                        action_required=False,
                        estimated_duration=20
                    )
                ],
                estimated_duration=115,
                difficulty_level='intermediate',
                category='goals'
            ),
            
            'journal_tutorial': Tutorial(
                tutorial_id='journal_tutorial',
                name='Training Journal Tutorial',
                description='Learn how to use the training journal feature',
                tutorial_type=TutorialType.SIDEBAR,
                trigger=TutorialTrigger.ON_FEATURE_ACCESS,
                target_feature='journal',
                steps=[
                    TutorialStep(
                        step_id='journal_intro',
                        title='Training Journal',
                        content='Your training journal helps you track not just your activities, but also your thoughts, feelings, and progress.',
                        position='center',
                        action_required=False,
                        estimated_duration=20
                    ),
                    TutorialStep(
                        step_id='journal_entry',
                        title='Create Your First Entry',
                        content='Start by creating your first journal entry. Reflect on your training, how you felt, and any insights.',
                        target_element='#journal-entry-form',
                        position='right',
                        action_required=True,
                        action_text='Write Entry',
                        action_url='/journal/new',
                        estimated_duration=60
                    ),
                    TutorialStep(
                        step_id='journal_features',
                        title='Journal Features',
                        content='Use tags, mood tracking, and goal reflections to make your journal entries more meaningful.',
                        target_element='#journal-features',
                        position='left',
                        action_required=False,
                        estimated_duration=30
                    )
                ],
                estimated_duration=110,
                difficulty_level='intermediate',
                category='journal'
            ),
            
            # Additional tutorials for existing users
            'dashboard_advanced_tutorial': Tutorial(
                tutorial_id='dashboard_advanced_tutorial',
                name='Advanced Dashboard Features',
                description='Learn about advanced dashboard features and customization options',
                tutorial_type=TutorialType.WALKTHROUGH,
                trigger=TutorialTrigger.MANUAL,
                target_step=None,  # Available to all existing users
                steps=[
                    TutorialStep(
                        step_id='advanced_metrics',
                        title='Advanced Metrics',
                        content='Learn about ACWR, TRIMP, and divergence analysis - the key metrics that make TrainingMonkey unique.',
                        target_element='#metrics-section',
                        position='top',
                        action_required=False,
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='chart_interactions',
                        title='Chart Interactions',
                        content='Discover how to interact with charts: hover for details, click to freeze tooltips, and use legends for explanations.',
                        target_element='#training-charts',
                        position='bottom',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='progressive_disclosure',
                        title='Progressive Features',
                        content='As you use the dashboard more, advanced features will automatically appear. Use the toggle to show/hide them manually.',
                        target_element='#progressive-disclosure-toggle',
                        position='right',
                        action_required=False,
                        estimated_duration=20
                    ),
                    TutorialStep(
                        step_id='help_system',
                        title='Help System',
                        content='Use the help button (❓) and tooltips throughout the dashboard to get contextual assistance.',
                        target_element='#help-button',
                        position='left',
                        action_required=False,
                        estimated_duration=15
                    )
                ],
                estimated_duration=90,
                difficulty_level='intermediate',
                category='dashboard'
            ),
            
            'training_analysis_tutorial': Tutorial(
                tutorial_id='training_analysis_tutorial',
                name='Understanding Training Analysis',
                description='Deep dive into training load analysis and divergence insights',
                tutorial_type=TutorialType.MODAL,
                trigger=TutorialTrigger.MANUAL,
                target_step=None,  # Available to all existing users
                steps=[
                    TutorialStep(
                        step_id='external_vs_internal',
                        title='External vs Internal Load',
                        content='External load is what you do (distance, elevation), internal load is how your body responds (heart rate zones).',
                        position='center',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='divergence_explained',
                        title='Divergence Analysis',
                        content='Divergence shows when your internal and external loads don\'t match. This reveals fatigue, fitness changes, or environmental stress.',
                        target_element='#divergence-chart',
                        position='top',
                        action_required=False,
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='acwr_understanding',
                        title='ACWR (Acute:Chronic Workload Ratio)',
                        content='ACWR compares your recent training (7 days) to your training base (28 days). Values 0.8-1.3 are optimal.',
                        target_element='#acwr-metrics',
                        position='bottom',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='trimp_understanding',
                        title='TRIMP (Training Impulse)',
                        content='TRIMP measures internal training stress based on heart rate zones and duration. Higher values = more intense training.',
                        target_element='#trimp-chart',
                        position='left',
                        action_required=False,
                        estimated_duration=20
                    )
                ],
                estimated_duration=100,
                difficulty_level='advanced',
                category='analysis'
            ),
            
            'ai_recommendations_tutorial': Tutorial(
                tutorial_id='ai_recommendations_tutorial',
                name='AI Recommendations Guide',
                description='Learn how to interpret and use AI-powered training recommendations',
                tutorial_type=TutorialType.INTERACTIVE,
                trigger=TutorialTrigger.MANUAL,
                target_step=None,  # Available to all existing users
                steps=[
                    TutorialStep(
                        step_id='ai_overview',
                        title='AI Recommendations',
                        content='Our AI analyzes your training patterns, goals, and current fitness to provide personalized recommendations.',
                        target_element='#recommendations-section',
                        position='top',
                        action_required=False,
                        estimated_duration=20
                    ),
                    TutorialStep(
                        step_id='recommendation_types',
                        title='Types of Recommendations',
                        content='You\'ll get daily training decisions, weekly planning advice, and pattern insights based on your data.',
                        position='center',
                        action_required=False,
                        estimated_duration=25
                    ),
                    TutorialStep(
                        step_id='generate_recommendations',
                        title='Generate New Recommendations',
                        content='Click the "Generate AI Analysis" button to get fresh recommendations based on your latest training data.',
                        target_element='#generate-recommendations-btn',
                        position='bottom',
                        action_required=True,
                        action_text='Generate Analysis',
                        estimated_duration=30
                    ),
                    TutorialStep(
                        step_id='interpret_recommendations',
                        title='Interpreting Recommendations',
                        content='Look for specific guidance on training intensity, recovery needs, and goal progress in your recommendations.',
                        position='center',
                        action_required=False,
                        estimated_duration=20
                    )
                ],
                estimated_duration=95,
                difficulty_level='intermediate',
                category='recommendations'
            )
        }
    
    def start_tutorial(self, user_id: int, tutorial_id: str) -> Optional[TutorialSession]:
        """
        Start a tutorial for a user
        
        Args:
            user_id: User ID
            tutorial_id: Tutorial ID to start
            
        Returns:
            TutorialSession object or None if failed
        """
        try:
            # Check if tutorial exists
            if tutorial_id not in self.tutorials:
                logger.warning(f"Tutorial {tutorial_id} not found")
                return None
            
            tutorial = self.tutorials[tutorial_id]
            
            # Check if tutorial is active
            if not tutorial.active:
                logger.warning(f"Tutorial {tutorial_id} is not active")
                return None
            
            # Check prerequisites
            if not self._check_tutorial_prerequisites(user_id, tutorial):
                logger.warning(f"Prerequisites not met for tutorial {tutorial_id}")
                return None
            
            # Create session
            session_id = f"{user_id}_{tutorial_id}_{datetime.now().timestamp()}"
            session = TutorialSession(
                session_id=session_id,
                user_id=user_id,
                tutorial_id=tutorial_id,
                status=TutorialStatus.IN_PROGRESS,
                start_time=datetime.now(),
                last_activity=datetime.now()
            )
            
            # Save session
            self._save_tutorial_session(session)
            
            # Add to active sessions
            self.active_sessions[session_id] = session
            
            # Log tutorial start event
            self.progress_tracker.update_progress(
                user_id,
                event_type=ProgressEventType.ENGAGEMENT_INCREASED,
                event_data={
                    'tutorial_id': tutorial_id,
                    'action': 'started',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Started tutorial {tutorial_id} for user {user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Error starting tutorial {tutorial_id} for user {user_id}: {str(e)}")
            return None
    
    def get_tutorial_session(self, session_id: str) -> Optional[TutorialSession]:
        """
        Get tutorial session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            TutorialSession object or None if not found
        """
        try:
            # Check active sessions first
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            # Load from database
            return self._load_tutorial_session(session_id)
            
        except Exception as e:
            logger.error(f"Error getting tutorial session {session_id}: {str(e)}")
            return None
    
    def update_tutorial_progress(self, session_id: str, step_id: str, 
                               action: str = 'viewed', data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update tutorial progress
        
        Args:
            session_id: Session ID
            step_id: Step ID that was completed
            action: Action performed (viewed, completed, skipped, etc.)
            data: Additional data
            
        Returns:
            True if successfully updated, False otherwise
        """
        try:
            session = self.get_tutorial_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False
            
            # Update session
            session.last_activity = datetime.now()
            
            # Record interaction
            interaction = {
                'step_id': step_id,
                'action': action,
                'timestamp': datetime.now().isoformat(),
                'data': data or {}
            }
            session.interactions.append(interaction)
            
            # Update progress based on action
            if action == 'completed':
                if step_id not in session.completed_steps:
                    session.completed_steps.append(step_id)
            elif action == 'skipped':
                if step_id not in session.skipped_steps:
                    session.skipped_steps.append(step_id)
            
            # Calculate progress percentage
            tutorial = self.tutorials.get(session.tutorial_id)
            if tutorial:
                total_steps = len(tutorial.steps)
                completed_steps = len(session.completed_steps)
                session.progress_percentage = (completed_steps / total_steps) * 100.0
            
            # Check if tutorial is complete
            if session.progress_percentage >= 100.0:
                session.status = TutorialStatus.COMPLETED
                session.end_time = datetime.now()
                
                # Log tutorial completion event
                self.progress_tracker.update_progress(
                    session.user_id,
                    event_type=ProgressEventType.ENGAGEMENT_INCREASED,
                    event_data={
                        'tutorial_id': session.tutorial_id,
                        'action': 'completed',
                        'progress_percentage': session.progress_percentage,
                        'timestamp': datetime.now().isoformat()
                    }
                )
            
            # Save updated session
            self._save_tutorial_session(session)
            
            # Update active sessions
            if session_id in self.active_sessions:
                self.active_sessions[session_id] = session
            
            logger.info(f"Updated tutorial progress for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating tutorial progress for session {session_id}: {str(e)}")
            return False
    
    def complete_tutorial(self, session_id: str) -> bool:
        """
        Complete a tutorial session
        
        Args:
            session_id: Session ID
            
        Returns:
            True if successfully completed, False otherwise
        """
        try:
            session = self.get_tutorial_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False
            
            # Mark all remaining steps as completed
            tutorial = self.tutorials.get(session.tutorial_id)
            if tutorial:
                for step in tutorial.steps:
                    if step.step_id not in session.completed_steps and step.step_id not in session.skipped_steps:
                        session.completed_steps.append(step.step_id)
            
            # Update session
            session.status = TutorialStatus.COMPLETED
            session.end_time = datetime.now()
            session.progress_percentage = 100.0
            
            # Calculate time spent
            if session.start_time and session.end_time:
                session.time_spent = int((session.end_time - session.start_time).total_seconds())
            
            # Save session
            self._save_tutorial_session(session)
            
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Log tutorial completion event
            self.progress_tracker.update_progress(
                session.user_id,
                event_type=ProgressEventType.ENGAGEMENT_INCREASED,
                event_data={
                    'tutorial_id': session.tutorial_id,
                    'action': 'completed',
                    'time_spent': session.time_spent,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Completed tutorial session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error completing tutorial session {session_id}: {str(e)}")
            return False
    
    def skip_tutorial(self, session_id: str, reason: Optional[str] = None) -> bool:
        """
        Skip a tutorial session
        
        Args:
            session_id: Session ID
            reason: Reason for skipping (optional)
            
        Returns:
            True if successfully skipped, False otherwise
        """
        try:
            session = self.get_tutorial_session(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return False
            
            # Update session
            session.status = TutorialStatus.SKIPPED
            session.end_time = datetime.now()
            
            # Calculate time spent
            if session.start_time and session.end_time:
                session.time_spent = int((session.end_time - session.start_time).total_seconds())
            
            # Add user feedback
            session.user_feedback = {
                'skipped': True,
                'reason': reason,
                'timestamp': datetime.now().isoformat()
            }
            
            # Save session
            self._save_tutorial_session(session)
            
            # Remove from active sessions
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # Log tutorial skip event
            self.progress_tracker.update_progress(
                session.user_id,
                event_type=ProgressEventType.ENGAGEMENT_INCREASED,
                event_data={
                    'tutorial_id': session.tutorial_id,
                    'action': 'skipped',
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"Skipped tutorial session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error skipping tutorial session {session_id}: {str(e)}")
            return False
    
    def get_available_tutorials(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get available tutorials for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of available tutorials with metadata
        """
        try:
            available_tutorials = []
            
            for tutorial_id, tutorial in self.tutorials.items():
                if not tutorial.active:
                    continue
                
                # Check if user meets prerequisites
                if not self._check_tutorial_prerequisites(user_id, tutorial):
                    continue
                
                # Check if user has already completed this tutorial
                completed = self._has_user_completed_tutorial(user_id, tutorial_id)
                
                tutorial_info = {
                    'tutorial_id': tutorial_id,
                    'name': tutorial.name,
                    'description': tutorial.description,
                    'tutorial_type': tutorial.tutorial_type.value,
                    'trigger': tutorial.trigger.value,
                    'estimated_duration': tutorial.estimated_duration,
                    'difficulty_level': tutorial.difficulty_level,
                    'category': tutorial.category,
                    'tags': tutorial.tags,
                    'completed': completed,
                    'prerequisites_met': True
                }
                
                available_tutorials.append(tutorial_info)
            
            return available_tutorials
            
        except Exception as e:
            logger.error(f"Error getting available tutorials for user {user_id}: {str(e)}")
            return []
    
    def get_recommended_tutorials(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recommended tutorials for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended tutorials
        """
        try:
            # Get user progress
            progress = self.progress_tracker.get_progress(user_id)
            if not progress:
                return []
            
            # Get available tutorials
            available_tutorials = self.get_available_tutorials(user_id)
            
            # Score tutorials based on user progress and preferences
            scored_tutorials = []
            for tutorial_info in available_tutorials:
                score = self._calculate_tutorial_relevance_score(user_id, tutorial_info, progress)
                scored_tutorials.append((tutorial_info, score))
            
            # Sort by score and return top recommendations
            scored_tutorials.sort(key=lambda x: x[1], reverse=True)
            
            recommendations = []
            for tutorial_info, score in scored_tutorials[:limit]:
                tutorial_info['relevance_score'] = score
                recommendations.append(tutorial_info)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommended tutorials for user {user_id}: {str(e)}")
            return []
    
    def get_tutorial_analytics(self, tutorial_id: str) -> Optional[TutorialAnalytics]:
        """
        Get analytics for a tutorial
        
        Args:
            tutorial_id: Tutorial ID
            
        Returns:
            TutorialAnalytics object or None if not found
        """
        try:
            # In practice, this would query aggregated data from the database
            # For now, return a placeholder analytics object
            analytics = TutorialAnalytics(
                tutorial_id=tutorial_id,
                total_sessions=100,
                completed_sessions=75,
                skipped_sessions=15,
                average_completion_time=120.0,
                average_progress_percentage=85.0,
                user_satisfaction_score=4.2,
                common_dropout_points=['step_2', 'step_4'],
                effectiveness_score=0.82
            )
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting tutorial analytics for {tutorial_id}: {str(e)}")
            return None
    
    def get_tutorial_content(self, tutorial_id: str, step_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get tutorial content for frontend rendering
        
        Args:
            tutorial_id: Tutorial ID
            step_id: Specific step ID (optional)
            
        Returns:
            Tutorial content dictionary or None if not found
        """
        try:
            if tutorial_id not in self.tutorials:
                return None
            
            tutorial = self.tutorials[tutorial_id]
            
            if step_id:
                # Return specific step content
                for step in tutorial.steps:
                    if step.step_id == step_id:
                        return {
                            'tutorial_id': tutorial_id,
                            'step': {
                                'step_id': step.step_id,
                                'title': step.title,
                                'content': step.content,
                                'target_element': step.target_element,
                                'position': step.position,
                                'action_required': step.action_required,
                                'action_text': step.action_text,
                                'action_url': step.action_url,
                                'hints': step.hints,
                                'estimated_duration': step.estimated_duration,
                                'interactive': step.interactive,
                                'skip_allowed': step.skip_allowed
                            }
                        }
                return None
            else:
                # Return full tutorial content
                return {
                    'tutorial_id': tutorial_id,
                    'name': tutorial.name,
                    'description': tutorial.description,
                    'tutorial_type': tutorial.tutorial_type.value,
                    'trigger': tutorial.trigger.value,
                    'estimated_duration': tutorial.estimated_duration,
                    'difficulty_level': tutorial.difficulty_level,
                    'category': tutorial.category,
                    'steps': [
                        {
                            'step_id': step.step_id,
                            'title': step.title,
                            'content': step.content,
                            'target_element': step.target_element,
                            'position': step.position,
                            'action_required': step.action_required,
                            'action_text': step.action_text,
                            'action_url': step.action_url,
                            'hints': step.hints,
                            'estimated_duration': step.estimated_duration,
                            'interactive': step.interactive,
                            'skip_allowed': step.skip_allowed
                        }
                        for step in tutorial.steps
                    ]
                }
            
        except Exception as e:
            logger.error(f"Error getting tutorial content for {tutorial_id}: {str(e)}")
            return None
    
    def _check_tutorial_prerequisites(self, user_id: int, tutorial: Tutorial) -> bool:
        """Check if user meets tutorial prerequisites"""
        try:
            # For existing users, we'll be more lenient with prerequisites
            # Check if user is an existing user (has completed onboarding)
            is_existing_user = self._is_existing_user(user_id)
            
            for prerequisite in tutorial.prerequisites:
                # Check step completion
                if prerequisite.startswith('step:'):
                    step_name = prerequisite.split(':', 1)[1]
                    try:
                        step = OnboardingStep(step_name)
                        if not self.onboarding_manager.has_completed_step(user_id, step):
                            # For existing users, skip step prerequisites for most tutorials
                            if is_existing_user and tutorial.category in ['dashboard', 'features', 'general']:
                                continue
                            return False
                    except ValueError:
                        continue
                
                # Check feature unlock
                elif prerequisite.startswith('feature:'):
                    feature_name = prerequisite.split(':', 1)[1]
                    if not self.onboarding_manager.check_feature_unlock(user_id, feature_name):
                        # For existing users, allow access to most features
                        if is_existing_user and tutorial.category in ['dashboard', 'features', 'general']:
                            continue
                        return False
                
                # Check activity count
                elif prerequisite.startswith('activities:'):
                    required_count = int(prerequisite.split(':', 1)[1])
                    actual_count = self.tiered_feature_manager._get_user_activity_count(user_id)
                    if actual_count < required_count:
                        # For existing users, reduce activity requirements
                        if is_existing_user and actual_count > 0:
                            continue
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking tutorial prerequisites: {str(e)}")
            return False
    
    def _is_existing_user(self, user_id: int) -> bool:
        """Check if user is an existing user (has completed onboarding)"""
        try:
            # Check if user has completed the welcome step (indicating they're past initial onboarding)
            return self.onboarding_manager.has_completed_step(user_id, OnboardingStep.WELCOME)
        except Exception as e:
            logger.error(f"Error checking if user is existing user: {str(e)}")
            return False
    
    def _has_user_completed_tutorial(self, user_id: int, tutorial_id: str) -> bool:
        """Check if user has completed a tutorial"""
        try:
            # Check database for actual completion records
            completion_query = """
                SELECT COUNT(*) as count 
                FROM tutorial_completions 
                WHERE user_id = %s AND tutorial_id = %s
            """
            
            result = db_utils.execute_query(completion_query, (user_id, tutorial_id), fetch=True)
            if result and result.get('count', 0) > 0:
                return True
            
            # Fallback for existing users (simulate completion for demo purposes)
            if self._is_existing_user(user_id):
                completed_tutorials = [
                    'welcome_tour',
                    'dashboard_tutorial',
                    'features_tour'
                ]
                return tutorial_id in completed_tutorials
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking tutorial completion: {str(e)}")
            return False
    
    def mark_tutorial_completed(self, user_id: int, tutorial_id: str, completion_data: Dict[str, Any] = None) -> bool:
        """Mark a tutorial as completed for a user"""
        try:
            # Insert completion record
            completion_query = """
                INSERT INTO tutorial_completions (user_id, tutorial_id, completed_at, completion_data)
                VALUES (%s, %s, NOW(), %s)
                ON CONFLICT (user_id, tutorial_id) DO UPDATE SET
                    completed_at = NOW(),
                    completion_data = EXCLUDED.completion_data
            """
            
            completion_data_json = json.dumps(completion_data) if completion_data else None
            db_utils.execute_query(completion_query, (user_id, tutorial_id, completion_data_json))
            
            # Track analytics event
            from analytics_tracker import track_analytics_event, EventType
            track_analytics_event(
                event_type=EventType.TUTORIAL_COMPLETE,
                event_data={
                    'tutorial_id': tutorial_id,
                    'user_id': user_id,
                    'completion_data': completion_data
                },
                user_id=user_id,
                source_page='tutorial_system'
            )
            
            logger.info(f"Tutorial {tutorial_id} marked as completed for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking tutorial as completed: {str(e)}")
            return False
    
    def mark_tutorial_started(self, user_id: int, tutorial_id: str, start_data: Dict[str, Any] = None) -> bool:
        """Mark a tutorial as started for a user"""
        try:
            # Insert start record
            start_query = """
                INSERT INTO tutorial_sessions (user_id, tutorial_id, started_at, start_data)
                VALUES (%s, %s, NOW(), %s)
            """
            
            start_data_json = json.dumps(start_data) if start_data else None
            db_utils.execute_query(start_query, (user_id, tutorial_id, start_data_json))
            
            # Track analytics event
            from analytics_tracker import track_analytics_event, EventType
            track_analytics_event(
                event_type=EventType.TUTORIAL_START,
                event_data={
                    'tutorial_id': tutorial_id,
                    'user_id': user_id,
                    'start_data': start_data
                },
                user_id=user_id,
                source_page='tutorial_system'
            )
            
            logger.info(f"Tutorial {tutorial_id} marked as started for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking tutorial as started: {str(e)}")
            return False
    
    def mark_tutorial_skipped(self, user_id: int, tutorial_id: str, skip_data: Dict[str, Any] = None) -> bool:
        """Mark a tutorial as skipped for a user"""
        try:
            # Insert skip record
            skip_query = """
                INSERT INTO tutorial_skips (user_id, tutorial_id, skipped_at, skip_data)
                VALUES (%s, %s, NOW(), %s)
            """
            
            skip_data_json = json.dumps(skip_data) if skip_data else None
            db_utils.execute_query(skip_query, (user_id, tutorial_id, skip_data_json))
            
            # Track analytics event
            from analytics_tracker import track_analytics_event, EventType
            track_analytics_event(
                event_type=EventType.TUTORIAL_SKIP,
                event_data={
                    'tutorial_id': tutorial_id,
                    'user_id': user_id,
                    'skip_data': skip_data
                },
                user_id=user_id,
                source_page='tutorial_system'
            )
            
            logger.info(f"Tutorial {tutorial_id} marked as skipped for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking tutorial as skipped: {str(e)}")
            return False
    
    def get_tutorial_completion_stats(self, tutorial_id: str = None, time_period: str = '7d') -> Dict[str, Any]:
        """Get tutorial completion statistics"""
        try:
            # Calculate date range
            from datetime import datetime, timedelta
            end_date = datetime.now()
            if time_period == '1d':
                start_date = end_date - timedelta(days=1)
            elif time_period == '7d':
                start_date = end_date - timedelta(days=7)
            elif time_period == '30d':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Build query
            if tutorial_id:
                query = """
                    SELECT 
                        t.tutorial_id,
                        COUNT(DISTINCT ts.user_id) as total_starts,
                        COUNT(DISTINCT tc.user_id) as total_completions,
                        COUNT(DISTINCT tsk.user_id) as total_skips,
                        ROUND(
                            (COUNT(DISTINCT tc.user_id)::float / NULLIF(COUNT(DISTINCT ts.user_id), 0)) * 100, 2
                        ) as completion_rate,
                        ROUND(
                            (COUNT(DISTINCT tsk.user_id)::float / NULLIF(COUNT(DISTINCT ts.user_id), 0)) * 100, 2
                        ) as skip_rate
                    FROM (
                        SELECT %s as tutorial_id
                    ) t
                    LEFT JOIN tutorial_sessions ts ON t.tutorial_id = ts.tutorial_id 
                        AND ts.started_at >= %s AND ts.started_at <= %s
                    LEFT JOIN tutorial_completions tc ON t.tutorial_id = tc.tutorial_id 
                        AND tc.completed_at >= %s AND tc.completed_at <= %s
                    LEFT JOIN tutorial_skips tsk ON t.tutorial_id = tsk.tutorial_id 
                        AND tsk.skipped_at >= %s AND tsk.skipped_at <= %s
                    GROUP BY t.tutorial_id
                """
                params = [tutorial_id, start_date, end_date, start_date, end_date, start_date, end_date]
            else:
                query = """
                    SELECT 
                        COALESCE(ts.tutorial_id, tc.tutorial_id, tsk.tutorial_id) as tutorial_id,
                        COUNT(DISTINCT ts.user_id) as total_starts,
                        COUNT(DISTINCT tc.user_id) as total_completions,
                        COUNT(DISTINCT tsk.user_id) as total_skips,
                        ROUND(
                            (COUNT(DISTINCT tc.user_id)::float / NULLIF(COUNT(DISTINCT ts.user_id), 0)) * 100, 2
                        ) as completion_rate,
                        ROUND(
                            (COUNT(DISTINCT tsk.user_id)::float / NULLIF(COUNT(DISTINCT ts.user_id), 0)) * 100, 2
                        ) as skip_rate
                    FROM (
                        SELECT tutorial_id FROM tutorial_sessions WHERE started_at >= %s AND started_at <= %s
                        UNION
                        SELECT tutorial_id FROM tutorial_completions WHERE completed_at >= %s AND completed_at <= %s
                        UNION
                        SELECT tutorial_id FROM tutorial_skips WHERE skipped_at >= %s AND skipped_at <= %s
                    ) all_tutorials
                    LEFT JOIN tutorial_sessions ts ON all_tutorials.tutorial_id = ts.tutorial_id 
                        AND ts.started_at >= %s AND ts.started_at <= %s
                    LEFT JOIN tutorial_completions tc ON all_tutorials.tutorial_id = tc.tutorial_id 
                        AND tc.completed_at >= %s AND tc.completed_at <= %s
                    LEFT JOIN tutorial_skips tsk ON all_tutorials.tutorial_id = tsk.tutorial_id 
                        AND tsk.skipped_at >= %s AND tsk.skipped_at <= %s
                    GROUP BY all_tutorials.tutorial_id
                    ORDER BY total_starts DESC
                """
                params = [start_date, end_date, start_date, end_date, start_date, end_date, 
                         start_date, end_date, start_date, end_date, start_date, end_date]
            
            result = db_utils.execute_query(query, params, fetch=True)
            
            if tutorial_id and result:
                return {
                    'tutorial_id': result.get('tutorial_id'),
                    'total_starts': result.get('total_starts', 0),
                    'total_completions': result.get('total_completions', 0),
                    'total_skips': result.get('total_skips', 0),
                    'completion_rate': result.get('completion_rate', 0),
                    'skip_rate': result.get('skip_rate', 0),
                    'time_period': time_period
                }
            elif not tutorial_id:
                return {
                    'tutorials': result if isinstance(result, list) else [result] if result else [],
                    'time_period': time_period,
                    'total_tutorials': len(result) if isinstance(result, list) else (1 if result else 0)
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error getting tutorial completion stats: {str(e)}")
            return {}
    
    def _calculate_tutorial_relevance_score(self, user_id: int, tutorial_info: Dict[str, Any], 
                                          progress: Any) -> float:
        """Calculate tutorial relevance score for recommendations"""
        try:
            score = 0.0
            
            # Base score for incomplete tutorials
            if not tutorial_info.get('completed', False):
                score += 50.0
            
            # Bonus for tutorials matching current step
            if tutorial_info.get('trigger') == 'on_step_enter':
                score += 30.0
            
            # Bonus for beginner tutorials for new users
            if progress.progress_percentage < 30 and tutorial_info.get('difficulty_level') == 'beginner':
                score += 20.0
            
            # Bonus for intermediate tutorials for progressing users
            if 30 <= progress.progress_percentage < 70 and tutorial_info.get('difficulty_level') == 'intermediate':
                score += 20.0
            
            # Bonus for advanced tutorials for experienced users
            if progress.progress_percentage >= 70 and tutorial_info.get('difficulty_level') == 'advanced':
                score += 20.0
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating tutorial relevance score: {str(e)}")
            return 0.0
    
    # Database methods
    def _save_tutorial_session(self, session: TutorialSession):
        """Save tutorial session to database"""
        try:
            session_data = {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'tutorial_id': session.tutorial_id,
                'current_step_index': session.current_step_index,
                'completed_steps': session.completed_steps,
                'skipped_steps': session.skipped_steps,
                'start_time': session.start_time.isoformat(),
                'last_activity': session.last_activity.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'status': session.status.value,
                'progress_percentage': session.progress_percentage,
                'time_spent': session.time_spent,
                'interactions': session.interactions,
                'user_feedback': session.user_feedback
            }
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # PostgreSQL syntax
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, tutorial_sessions)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET tutorial_sessions = user_settings.tutorial_sessions || %s
                    """, (session.user_id, json.dumps([session_data]), json.dumps([session_data])))
                else:
                    cursor.execute("""
                        INSERT INTO user_settings (user_id, tutorial_sessions)
                        VALUES (%s, %s)
                    """, (session.user_id, json.dumps([session_data])))
            
        except Exception as e:
            logger.error(f"Error saving tutorial session: {str(e)}")
    
    def _load_tutorial_session(self, session_id: str) -> Optional[TutorialSession]:
        """Load tutorial session from database"""
        try:
            # In practice, this would query the database for the session
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            logger.error(f"Error loading tutorial session: {str(e)}")
            return None


# Convenience functions for easy integration
tutorial_system = OnboardingTutorialSystem()


def start_tutorial(user_id: int, tutorial_id: str) -> Optional[TutorialSession]:
    """Start a tutorial for a user"""
    return tutorial_system.start_tutorial(user_id, tutorial_id)


def get_tutorial_session(session_id: str) -> Optional[TutorialSession]:
    """Get tutorial session by ID"""
    return tutorial_system.get_tutorial_session(session_id)


def update_tutorial_progress(session_id: str, step_id: str, 
                           action: str = 'viewed', data: Optional[Dict[str, Any]] = None) -> bool:
    """Update tutorial progress"""
    return tutorial_system.update_tutorial_progress(session_id, step_id, action, data)


def complete_tutorial(session_id: str) -> bool:
    """Complete a tutorial session"""
    return tutorial_system.complete_tutorial(session_id)


def skip_tutorial(session_id: str, reason: Optional[str] = None) -> bool:
    """Skip a tutorial session"""
    return tutorial_system.skip_tutorial(session_id, reason)


def get_available_tutorials(user_id: int) -> List[Dict[str, Any]]:
    """Get available tutorials for a user"""
    return tutorial_system.get_available_tutorials(user_id)


def get_recommended_tutorials(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recommended tutorials for a user"""
    return tutorial_system.get_recommended_tutorials(user_id, limit)


def get_tutorial_analytics(tutorial_id: str) -> Optional[TutorialAnalytics]:
    """Get analytics for a tutorial"""
    return tutorial_system.get_tutorial_analytics(tutorial_id)


def get_tutorial_content(tutorial_id: str, step_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get tutorial content for frontend rendering"""
    return tutorial_system.get_tutorial_content(tutorial_id, step_id)


if __name__ == "__main__":
    print("=" * 50)
    print("Onboarding Tutorial System")
    print("=" * 50)
    print("Module loaded successfully!")
    print(f"Tutorials defined: {len(tutorial_system.tutorials)}")
    print(f"Tutorial types: {[tutorial_type.value for tutorial_type in TutorialType]}")
    print(f"Tutorial triggers: {[trigger.value for trigger in TutorialTrigger]}")
    print(f"Tutorial statuses: {[status.value for status in TutorialStatus]}")
    print("=" * 50)


