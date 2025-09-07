"""
New User Dashboard Module

This module provides a basic dashboard specifically designed for new users during
the onboarding process. It includes:

- Progressive dashboard layout that adapts to user progress
- Simplified interface for new users
- Onboarding progress visualization
- Quick access to next steps and tutorials
- Basic activity display for new users
- Goal setting and tracking for beginners
- Tutorial integration and contextual help
- Feature discovery and unlock notifications
- Personalized recommendations for new users
- Mobile-responsive design considerations
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

logger = logging.getLogger(__name__)


class DashboardSection(Enum):
    """Dashboard sections for new users"""
    WELCOME = 'welcome'
    PROGRESS = 'progress'
    QUICK_ACTIONS = 'quick_actions'
    RECENT_ACTIVITIES = 'recent_activities'
    GOALS = 'goals'
    RECOMMENDATIONS = 'recommendations'
    TUTORIALS = 'tutorials'
    FEATURES = 'features'
    NEXT_STEPS = 'next_steps'
    HELP = 'help'


class DashboardLayout(Enum):
    """Dashboard layout types"""
    MINIMAL = 'minimal'  # Just welcome and progress
    BASIC = 'basic'      # Welcome, progress, quick actions
    STANDARD = 'standard'  # Most sections for progressing users
    COMPLETE = 'complete'  # All sections for advanced users


@dataclass
class DashboardWidget:
    """Individual dashboard widget"""
    widget_id: str
    section: DashboardSection
    title: str
    content: str
    widget_type: str  # progress_bar, card, list, chart, button, etc.
    data: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    visible: bool = True
    priority: int = 0  # Higher number = higher priority
    requires_feature: Optional[str] = None
    requires_step: Optional[OnboardingStep] = None


@dataclass
class DashboardSection:
    """Dashboard section configuration"""
    section_id: DashboardSection
    title: str
    description: str
    widgets: List[DashboardWidget] = field(default_factory=list)
    visible: bool = True
    order: int = 0
    requires_feature: Optional[str] = None
    requires_step: Optional[OnboardingStep] = None
    layout: str = 'grid'  # grid, list, carousel, etc.


@dataclass
class NewUserDashboard:
    """New user dashboard configuration and data"""
    user_id: int
    layout: DashboardLayout
    sections: List[DashboardSection] = field(default_factory=list)
    widgets: List[DashboardWidget] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    customization: Dict[str, Any] = field(default_factory=dict)


class NewUserDashboardManager:
    """
    Manager for new user dashboard functionality
    """
    
    def __init__(self):
        """Initialize the dashboard manager"""
        self.onboarding_manager = OnboardingManager()
        self.progress_tracker = OnboardingProgressTracker()
        self.tutorial_system = OnboardingTutorialSystem()
        self.tiered_feature_manager = TieredFeatureUnlockManager()
        
    def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """
        Get complete dashboard data for a new user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with dashboard data for frontend rendering
        """
        try:
            # Get user progress
            progress = self.progress_tracker.get_progress(user_id)
            if not progress:
                # Start progress tracking if not already started
                self.progress_tracker.start_progress_tracking(user_id)
                progress = self.progress_tracker.get_progress(user_id)
            
            # Determine dashboard layout based on progress
            layout = self._determine_dashboard_layout(progress)
            
            # Get dashboard sections
            sections = self._get_dashboard_sections(user_id, progress, layout)
            
            # Get dashboard widgets
            widgets = self._get_dashboard_widgets(user_id, progress, layout)
            
            # Get quick actions
            quick_actions = self._get_quick_actions(user_id, progress)
            
            # Get next steps
            next_steps = self._get_next_steps(user_id, progress)
            
            # Get recommendations
            recommendations = self._get_recommendations(user_id, progress)
            
            # Get available tutorials
            tutorials = self.tutorial_system.get_available_tutorials(user_id)
            
            # Get recent activities (if any)
            recent_activities = self._get_recent_activities(user_id)
            
            # Get goals (if any)
            goals = self._get_user_goals(user_id)
            
            dashboard_data = {
                'user_id': user_id,
                'layout': layout.value,
                'progress': {
                    'overall_percentage': progress.progress_percentage,
                    'current_step': progress.current_step.value,
                    'completed_steps': [step.value for step in progress.completed_steps],
                    'unlocked_features': progress.unlocked_features,
                    'current_tier': progress.current_tier.value,
                    'status': progress.status.value
                },
                'sections': sections,
                'widgets': widgets,
                'quick_actions': quick_actions,
                'next_steps': next_steps,
                'recommendations': recommendations,
                'tutorials': tutorials,
                'recent_activities': recent_activities,
                'goals': goals,
                'last_updated': datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for user {user_id}: {str(e)}")
            return self._get_fallback_dashboard_data(user_id)
    
    def _determine_dashboard_layout(self, progress: Any) -> DashboardLayout:
        """Determine appropriate dashboard layout based on user progress"""
        try:
            if progress.progress_percentage < 20:
                return DashboardLayout.MINIMAL
            elif progress.progress_percentage < 50:
                return DashboardLayout.BASIC
            elif progress.progress_percentage < 80:
                return DashboardLayout.STANDARD
            else:
                return DashboardLayout.COMPLETE
                
        except Exception as e:
            logger.error(f"Error determining dashboard layout: {str(e)}")
            return DashboardLayout.MINIMAL
    
    def _get_dashboard_sections(self, user_id: int, progress: Any, layout: DashboardLayout) -> List[Dict[str, Any]]:
        """Get dashboard sections based on layout and user progress"""
        try:
            sections = []
            
            # Welcome section (always visible)
            sections.append({
                'section_id': DashboardSection.WELCOME.value,
                'title': 'Welcome to TrainingMonkey!',
                'description': 'Your personalized training companion',
                'visible': True,
                'order': 1,
                'layout': 'hero'
            })
            
            # Progress section (always visible)
            sections.append({
                'section_id': DashboardSection.PROGRESS.value,
                'title': 'Your Progress',
                'description': 'Track your onboarding journey',
                'visible': True,
                'order': 2,
                'layout': 'progress'
            })
            
            # Quick actions section (basic and above)
            if layout in [DashboardLayout.BASIC, DashboardLayout.STANDARD, DashboardLayout.COMPLETE]:
                sections.append({
                    'section_id': DashboardSection.QUICK_ACTIONS.value,
                    'title': 'Quick Actions',
                    'description': 'Get started with common tasks',
                    'visible': True,
                    'order': 3,
                    'layout': 'grid'
                })
            
            # Recent activities section (if user has activities)
            if progress.unlocked_features and 'activity_viewer' in progress.unlocked_features:
                sections.append({
                    'section_id': DashboardSection.RECENT_ACTIVITIES.value,
                    'title': 'Recent Activities',
                    'description': 'Your latest training sessions',
                    'visible': True,
                    'order': 4,
                    'layout': 'list'
                })
            
            # Goals section (if user has set goals)
            if progress.unlocked_features and 'custom_goals' in progress.unlocked_features:
                sections.append({
                    'section_id': DashboardSection.GOALS.value,
                    'title': 'Your Goals',
                    'description': 'Track your training objectives',
                    'visible': True,
                    'order': 5,
                    'layout': 'cards'
                })
            
            # Recommendations section (standard and above)
            if layout in [DashboardLayout.STANDARD, DashboardLayout.COMPLETE]:
                sections.append({
                    'section_id': DashboardSection.RECOMMENDATIONS.value,
                    'title': 'Recommendations',
                    'description': 'Personalized suggestions for you',
                    'visible': True,
                    'order': 6,
                    'layout': 'list'
                })
            
            # Tutorials section (always visible)
            sections.append({
                'section_id': DashboardSection.TUTORIALS.value,
                'title': 'Learn & Explore',
                'description': 'Interactive tutorials and guides',
                'visible': True,
                'order': 7,
                'layout': 'grid'
            })
            
            # Next steps section (always visible)
            sections.append({
                'section_id': DashboardSection.NEXT_STEPS.value,
                'title': 'Next Steps',
                'description': 'What to do next',
                'visible': True,
                'order': 8,
                'layout': 'list'
            })
            
            # Help section (always visible)
            sections.append({
                'section_id': DashboardSection.HELP.value,
                'title': 'Need Help?',
                'description': 'Get support and assistance',
                'visible': True,
                'order': 9,
                'layout': 'cards'
            })
            
            return sections
            
        except Exception as e:
            logger.error(f"Error getting dashboard sections: {str(e)}")
            return []
    
    def _get_dashboard_widgets(self, user_id: int, progress: Any, layout: DashboardLayout) -> List[Dict[str, Any]]:
        """Get dashboard widgets based on layout and user progress"""
        try:
            widgets = []
            
            # Welcome widget
            widgets.append({
                'widget_id': 'welcome_message',
                'section': DashboardSection.WELCOME.value,
                'title': 'Welcome!',
                'content': self._get_welcome_message(progress),
                'widget_type': 'hero_card',
                'data': {
                    'user_name': self._get_user_name(user_id),
                    'days_since_join': self._get_days_since_join(user_id)
                },
                'actions': [
                    {
                        'text': 'Start Tutorial',
                        'url': '/tutorials/welcome_tour',
                        'type': 'primary'
                    }
                ],
                'visible': True,
                'priority': 100
            })
            
            # Progress widget
            widgets.append({
                'widget_id': 'onboarding_progress',
                'section': DashboardSection.PROGRESS.value,
                'title': 'Onboarding Progress',
                'content': f'You\'re {progress.progress_percentage:.0f}% through your setup',
                'widget_type': 'progress_bar',
                'data': {
                    'percentage': progress.progress_percentage,
                    'current_step': progress.current_step.value,
                    'total_steps': len(OnboardingStep),
                    'completed_steps': len(progress.completed_steps)
                },
                'actions': [
                    {
                        'text': 'View Details',
                        'url': '/onboarding/progress',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 90
            })
            
            # Quick actions widgets
            if layout in [DashboardLayout.BASIC, DashboardLayout.STANDARD, DashboardLayout.COMPLETE]:
                quick_action_widgets = self._get_quick_action_widgets(user_id, progress)
                widgets.extend(quick_action_widgets)
            
            # Recent activities widget
            if progress.unlocked_features and 'activity_viewer' in progress.unlocked_features:
                recent_activities_widget = self._get_recent_activities_widget(user_id)
                if recent_activities_widget:
                    widgets.append(recent_activities_widget)
            
            # Goals widget
            if progress.unlocked_features and 'custom_goals' in progress.unlocked_features:
                goals_widget = self._get_goals_widget(user_id)
                if goals_widget:
                    widgets.append(goals_widget)
            
            # Recommendations widget
            if layout in [DashboardLayout.STANDARD, DashboardLayout.COMPLETE]:
                recommendations_widget = self._get_recommendations_widget(user_id, progress)
                if recommendations_widget:
                    widgets.append(recommendations_widget)
            
            # Tutorials widget
            tutorials_widget = self._get_tutorials_widget(user_id)
            if tutorials_widget:
                widgets.append(tutorials_widget)
            
            # Next steps widget
            next_steps_widget = self._get_next_steps_widget(user_id, progress)
            if next_steps_widget:
                widgets.append(next_steps_widget)
            
            # Help widget
            help_widget = self._get_help_widget(user_id)
            if help_widget:
                widgets.append(help_widget)
            
            return widgets
            
        except Exception as e:
            logger.error(f"Error getting dashboard widgets: {str(e)}")
            return []
    
    def _get_quick_actions(self, user_id: int, progress: Any) -> List[Dict[str, Any]]:
        """Get quick actions for the user"""
        try:
            actions = []
            
            # Connect Strava action
            if OnboardingStep.STRAVA_CONNECTED not in progress.completed_steps:
                actions.append({
                    'id': 'connect_strava',
                    'title': 'Connect Strava',
                    'description': 'Sync your activities automatically',
                    'icon': 'strava',
                    'url': '/connect-strava',
                    'type': 'primary',
                    'priority': 100
                })
            
            # Complete welcome action
            if OnboardingStep.WELCOME not in progress.completed_steps:
                actions.append({
                    'id': 'complete_welcome',
                    'title': 'Complete Welcome',
                    'description': 'Finish the welcome process',
                    'icon': 'welcome',
                    'url': '/onboarding/welcome',
                    'type': 'secondary',
                    'priority': 90
                })
            
            # View dashboard tutorial
            actions.append({
                'id': 'dashboard_tutorial',
                'title': 'Dashboard Tour',
                'description': 'Learn how to use your dashboard',
                'icon': 'tutorial',
                'url': '/tutorials/dashboard_tutorial',
                'type': 'secondary',
                'priority': 80
            })
            
            # Set goals action
            if progress.unlocked_features and 'custom_goals' in progress.unlocked_features:
                actions.append({
                    'id': 'set_goals',
                    'title': 'Set Goals',
                    'description': 'Define your training objectives',
                    'icon': 'goals',
                    'url': '/goals/setup',
                    'type': 'secondary',
                    'priority': 70
                })
            
            # View activities action
            if progress.unlocked_features and 'activity_viewer' in progress.unlocked_features:
                actions.append({
                    'id': 'view_activities',
                    'title': 'View Activities',
                    'description': 'See your training sessions',
                    'icon': 'activities',
                    'url': '/activities',
                    'type': 'secondary',
                    'priority': 60
                })
            
            return actions
            
        except Exception as e:
            logger.error(f"Error getting quick actions: {str(e)}")
            return []
    
    def _get_next_steps(self, user_id: int, progress: Any) -> List[Dict[str, Any]]:
        """Get next steps for the user"""
        try:
            next_steps = []
            
            # Determine next onboarding step
            current_step = progress.current_step
            if current_step == OnboardingStep.WELCOME:
                next_steps.append({
                    'id': 'connect_strava',
                    'title': 'Connect Your Strava Account',
                    'description': 'Link your Strava account to start syncing activities',
                    'url': '/connect-strava',
                    'estimated_time': '2 minutes',
                    'priority': 100
                })
            elif current_step == OnboardingStep.STRAVA_CONNECTED:
                next_steps.append({
                    'id': 'sync_activities',
                    'title': 'Sync Your Activities',
                    'description': 'Import your recent training sessions',
                    'url': '/sync-activities',
                    'estimated_time': '1 minute',
                    'priority': 100
                })
            elif current_step == OnboardingStep.FIRST_ACTIVITY:
                next_steps.append({
                    'id': 'explore_dashboard',
                    'title': 'Explore Your Dashboard',
                    'description': 'Learn about your training insights and features',
                    'url': '/tutorials/dashboard_tutorial',
                    'estimated_time': '5 minutes',
                    'priority': 90
                })
            elif current_step == OnboardingStep.DASHBOARD_INTRO:
                next_steps.append({
                    'id': 'set_goals',
                    'title': 'Set Your Training Goals',
                    'description': 'Define what you want to achieve',
                    'url': '/goals/setup',
                    'estimated_time': '3 minutes',
                    'priority': 90
                })
            elif current_step == OnboardingStep.GOALS_SETUP:
                next_steps.append({
                    'id': 'explore_features',
                    'title': 'Explore Advanced Features',
                    'description': 'Discover analytics, recommendations, and more',
                    'url': '/tutorials/features_tour',
                    'estimated_time': '8 minutes',
                    'priority': 80
                })
            
            # Add general next steps
            if progress.progress_percentage < 50:
                next_steps.append({
                    'id': 'complete_onboarding',
                    'title': 'Complete Onboarding',
                    'description': 'Finish setting up your account',
                    'url': '/onboarding',
                    'estimated_time': '10 minutes',
                    'priority': 70
                })
            
            return next_steps
            
        except Exception as e:
            logger.error(f"Error getting next steps: {str(e)}")
            return []
    
    def _get_recommendations(self, user_id: int, progress: Any) -> List[Dict[str, Any]]:
        """Get personalized recommendations for the user"""
        try:
            recommendations = []
            
            # Tutorial recommendations
            available_tutorials = self.tutorial_system.get_available_tutorials(user_id)
            recommended_tutorials = self.tutorial_system.get_recommended_tutorials(user_id, limit=3)
            
            for tutorial in recommended_tutorials:
                recommendations.append({
                    'id': f'tutorial_{tutorial["tutorial_id"]}',
                    'type': 'tutorial',
                    'title': tutorial['name'],
                    'description': tutorial['description'],
                    'url': f'/tutorials/{tutorial["tutorial_id"]}',
                    'estimated_time': f'{tutorial["estimated_duration"]} seconds',
                    'priority': 90
                })
            
            # Feature recommendations
            if progress.progress_percentage > 30:
                recommendations.append({
                    'id': 'set_goals',
                    'type': 'feature',
                    'title': 'Set Training Goals',
                    'description': 'Define clear objectives to stay motivated',
                    'url': '/goals/setup',
                    'estimated_time': '3 minutes',
                    'priority': 85
                })
            
            if progress.progress_percentage > 50:
                recommendations.append({
                    'id': 'journal_entry',
                    'type': 'feature',
                    'title': 'Start Training Journal',
                    'description': 'Track your thoughts and progress',
                    'url': '/journal/new',
                    'estimated_time': '5 minutes',
                    'priority': 80
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return []
    
    def _get_recent_activities(self, user_id: int) -> List[Dict[str, Any]]:
        """Get recent activities for the user"""
        try:
            # In practice, this would query the activities table
            # For now, return placeholder data
            return [
                {
                    'id': 'activity_1',
                    'name': 'Morning Run',
                    'type': 'Run',
                    'distance': '5.2 km',
                    'duration': '28:15',
                    'date': (datetime.now() - timedelta(days=1)).isoformat(),
                    'url': '/activities/1'
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting recent activities: {str(e)}")
            return []
    
    def _get_user_goals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user goals"""
        try:
            # In practice, this would query the goals table
            # For now, return placeholder data
            return [
                {
                    'id': 'goal_1',
                    'title': 'Run 100km this month',
                    'type': 'distance',
                    'target': '100 km',
                    'current': '25 km',
                    'progress': 25.0,
                    'deadline': (datetime.now() + timedelta(days=20)).isoformat()
                }
            ]
            
        except Exception as e:
            logger.error(f"Error getting user goals: {str(e)}")
            return []
    
    def _get_welcome_message(self, progress: Any) -> str:
        """Get personalized welcome message"""
        try:
            if progress.progress_percentage < 20:
                return "Welcome to TrainingMonkey! Let's get you started with your training journey."
            elif progress.progress_percentage < 50:
                return "Great progress! You're well on your way to unlocking all features."
            elif progress.progress_percentage < 80:
                return "Excellent! You're almost done with setup. Keep exploring!"
            else:
                return "Welcome back! You're all set up and ready to train."
                
        except Exception as e:
            logger.error(f"Error getting welcome message: {str(e)}")
            return "Welcome to TrainingMonkey!"
    
    def _get_user_name(self, user_id: int) -> str:
        """Get user's display name"""
        try:
            # In practice, this would query the users table
            # For now, return a placeholder
            return "Athlete"
            
        except Exception as e:
            logger.error(f"Error getting user name: {str(e)}")
            return "User"
    
    def _get_days_since_join(self, user_id: int) -> int:
        """Get days since user joined"""
        try:
            # In practice, this would query the users table
            # For now, return a placeholder
            return 1
            
        except Exception as e:
            logger.error(f"Error getting days since join: {str(e)}")
            return 1
    
    def _get_quick_action_widgets(self, user_id: int, progress: Any) -> List[Dict[str, Any]]:
        """Get quick action widgets"""
        try:
            widgets = []
            
            # Connect Strava widget
            if OnboardingStep.STRAVA_CONNECTED not in progress.completed_steps:
                widgets.append({
                    'widget_id': 'connect_strava_action',
                    'section': DashboardSection.QUICK_ACTIONS.value,
                    'title': 'Connect Strava',
                    'content': 'Sync your activities automatically',
                    'widget_type': 'action_card',
                    'data': {
                        'icon': 'strava',
                        'status': 'pending'
                    },
                    'actions': [
                        {
                            'text': 'Connect Now',
                            'url': '/connect-strava',
                            'type': 'primary'
                        }
                    ],
                    'visible': True,
                    'priority': 100
                })
            
            # Dashboard tutorial widget
            widgets.append({
                'widget_id': 'dashboard_tutorial_action',
                'section': DashboardSection.QUICK_ACTIONS.value,
                'title': 'Dashboard Tour',
                'content': 'Learn how to use your dashboard',
                'widget_type': 'action_card',
                'data': {
                    'icon': 'tutorial',
                    'status': 'available'
                },
                'actions': [
                    {
                        'text': 'Start Tour',
                        'url': '/tutorials/dashboard_tutorial',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 90
            })
            
            return widgets
            
        except Exception as e:
            logger.error(f"Error getting quick action widgets: {str(e)}")
            return []
    
    def _get_recent_activities_widget(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get recent activities widget"""
        try:
            activities = self._get_recent_activities(user_id)
            if not activities:
                return None
            
            return {
                'widget_id': 'recent_activities',
                'section': DashboardSection.RECENT_ACTIVITIES.value,
                'title': 'Recent Activities',
                'content': f'You have {len(activities)} recent activity',
                'widget_type': 'activity_list',
                'data': {
                    'activities': activities,
                    'total_count': len(activities)
                },
                'actions': [
                    {
                        'text': 'View All',
                        'url': '/activities',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 80
            }
            
        except Exception as e:
            logger.error(f"Error getting recent activities widget: {str(e)}")
            return None
    
    def _get_goals_widget(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get goals widget"""
        try:
            goals = self._get_user_goals(user_id)
            if not goals:
                return None
            
            return {
                'widget_id': 'user_goals',
                'section': DashboardSection.GOALS.value,
                'title': 'Your Goals',
                'content': f'You have {len(goals)} active goal',
                'widget_type': 'goal_cards',
                'data': {
                    'goals': goals,
                    'total_count': len(goals)
                },
                'actions': [
                    {
                        'text': 'Manage Goals',
                        'url': '/goals',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 75
            }
            
        except Exception as e:
            logger.error(f"Error getting goals widget: {str(e)}")
            return None
    
    def _get_recommendations_widget(self, user_id: int, progress: Any) -> Optional[Dict[str, Any]]:
        """Get recommendations widget"""
        try:
            recommendations = self._get_recommendations(user_id, progress)
            if not recommendations:
                return None
            
            return {
                'widget_id': 'recommendations',
                'section': DashboardSection.RECOMMENDATIONS.value,
                'title': 'Recommended for You',
                'content': f'{len(recommendations)} personalized recommendations',
                'widget_type': 'recommendation_list',
                'data': {
                    'recommendations': recommendations,
                    'total_count': len(recommendations)
                },
                'actions': [
                    {
                        'text': 'View All',
                        'url': '/recommendations',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 70
            }
            
        except Exception as e:
            logger.error(f"Error getting recommendations widget: {str(e)}")
            return None
    
    def _get_tutorials_widget(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get tutorials widget"""
        try:
            tutorials = self.tutorial_system.get_available_tutorials(user_id)
            if not tutorials:
                return None
            
            return {
                'widget_id': 'available_tutorials',
                'section': DashboardSection.TUTORIALS.value,
                'title': 'Learn & Explore',
                'content': f'{len(tutorials)} tutorials available',
                'widget_type': 'tutorial_grid',
                'data': {
                    'tutorials': tutorials,
                    'total_count': len(tutorials)
                },
                'actions': [
                    {
                        'text': 'Browse All',
                        'url': '/tutorials',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 65
            }
            
        except Exception as e:
            logger.error(f"Error getting tutorials widget: {str(e)}")
            return None
    
    def _get_next_steps_widget(self, user_id: int, progress: Any) -> Optional[Dict[str, Any]]:
        """Get next steps widget"""
        try:
            next_steps = self._get_next_steps(user_id, progress)
            if not next_steps:
                return None
            
            return {
                'widget_id': 'next_steps',
                'section': DashboardSection.NEXT_STEPS.value,
                'title': 'What\'s Next?',
                'content': f'{len(next_steps)} next steps to complete',
                'widget_type': 'step_list',
                'data': {
                    'steps': next_steps,
                    'total_count': len(next_steps)
                },
                'actions': [
                    {
                        'text': 'View All Steps',
                        'url': '/onboarding',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 60
            }
            
        except Exception as e:
            logger.error(f"Error getting next steps widget: {str(e)}")
            return None
    
    def _get_help_widget(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get help widget"""
        try:
            return {
                'widget_id': 'help_support',
                'section': DashboardSection.HELP.value,
                'title': 'Need Help?',
                'content': 'Get support and assistance',
                'widget_type': 'help_cards',
                'data': {
                    'help_options': [
                        {
                            'id': 'tutorials',
                            'title': 'Tutorials',
                            'description': 'Interactive guides',
                            'url': '/tutorials'
                        },
                        {
                            'id': 'faq',
                            'title': 'FAQ',
                            'description': 'Common questions',
                            'url': '/help/faq'
                        },
                        {
                            'id': 'contact',
                            'title': 'Contact Support',
                            'description': 'Get in touch',
                            'url': '/help/contact'
                        }
                    ]
                },
                'actions': [
                    {
                        'text': 'Get Help',
                        'url': '/help',
                        'type': 'secondary'
                    }
                ],
                'visible': True,
                'priority': 50
            }
            
        except Exception as e:
            logger.error(f"Error getting help widget: {str(e)}")
            return None
    
    def _get_fallback_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get fallback dashboard data if main data retrieval fails"""
        try:
            return {
                'user_id': user_id,
                'layout': DashboardLayout.MINIMAL.value,
                'progress': {
                    'overall_percentage': 0.0,
                    'current_step': OnboardingStep.WELCOME.value,
                    'completed_steps': [],
                    'unlocked_features': [],
                    'current_tier': FeatureTier.BASIC.value,
                    'status': 'not_started'
                },
                'sections': [
                    {
                        'section_id': DashboardSection.WELCOME.value,
                        'title': 'Welcome to TrainingMonkey!',
                        'description': 'Your personalized training companion',
                        'visible': True,
                        'order': 1,
                        'layout': 'hero'
                    }
                ],
                'widgets': [
                    {
                        'widget_id': 'welcome_message',
                        'section': DashboardSection.WELCOME.value,
                        'title': 'Welcome!',
                        'content': 'Welcome to TrainingMonkey! Let\'s get you started.',
                        'widget_type': 'hero_card',
                        'data': {
                            'user_name': 'User',
                            'days_since_join': 0
                        },
                        'actions': [
                            {
                                'text': 'Get Started',
                                'url': '/onboarding/welcome',
                                'type': 'primary'
                            }
                        ],
                        'visible': True,
                        'priority': 100
                    }
                ],
                'quick_actions': [],
                'next_steps': [],
                'recommendations': [],
                'tutorials': [],
                'recent_activities': [],
                'goals': [],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting fallback dashboard data: {str(e)}")
            return {}


# Convenience functions for easy integration
dashboard_manager = NewUserDashboardManager()


def get_dashboard_data(user_id: int) -> Dict[str, Any]:
    """Get complete dashboard data for a new user"""
    return dashboard_manager.get_dashboard_data(user_id)


if __name__ == "__main__":
    print("=" * 50)
    print("New User Dashboard Manager")
    print("=" * 50)
    print("Module loaded successfully!")
    print(f"Dashboard sections: {[section.value for section in DashboardSection]}")
    print(f"Dashboard layouts: {[layout.value for layout in DashboardLayout]}")
    print("=" * 50)


