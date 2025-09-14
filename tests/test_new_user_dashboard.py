"""
Test Suite for New User Dashboard Module

This module tests the new user dashboard functionality including:
- Dashboard data generation and layout determination
- Dashboard sections and widgets management
- Quick actions and next steps generation
- Recommendations and tutorial integration
- Progress-based dashboard adaptation
- Fallback data handling
- Widget priority and visibility management
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json

from new_user_dashboard import (
    NewUserDashboardManager,
    DashboardSection,
    DashboardLayout,
    DashboardWidget,
    DashboardSection as DashboardSectionClass,
    NewUserDashboard,
    get_dashboard_data,
    dashboard_manager
)
from onboarding_manager import OnboardingStep, FeatureTier


class TestNewUserDashboardManager(unittest.TestCase):
    """Test cases for NewUserDashboardManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dashboard_manager = NewUserDashboardManager()
        self.user_id = 1
    
    def test_initialization(self):
        """Test dashboard manager initialization"""
        self.assertIsNotNone(self.dashboard_manager.onboarding_manager)
        self.assertIsNotNone(self.dashboard_manager.progress_tracker)
        self.assertIsNotNone(self.dashboard_manager.tutorial_system)
        self.assertIsNotNone(self.dashboard_manager.tiered_feature_manager)
    
    @patch.object(NewUserDashboardManager, 'progress_tracker')
    @patch.object(NewUserDashboardManager, 'tutorial_system')
    def test_get_dashboard_data_success(self, mock_tutorial_system, mock_progress_tracker):
        """Test successful dashboard data retrieval"""
        # Mock progress data
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 25.0
        mock_progress.current_step = OnboardingStep.WELCOME
        mock_progress.completed_steps = []
        mock_progress.unlocked_features = []
        mock_progress.current_tier = FeatureTier.BASIC
        mock_progress.status = 'in_progress'
        
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock tutorial system
        mock_tutorial_system.get_available_tutorials.return_value = [
            {'tutorial_id': 'welcome_tour', 'name': 'Welcome Tour'}
        ]
        
        # Mock other methods
        with patch.object(self.dashboard_manager, '_get_recent_activities', return_value=[]):
            with patch.object(self.dashboard_manager, '_get_user_goals', return_value=[]):
                dashboard_data = self.dashboard_manager.get_dashboard_data(self.user_id)
                
                self.assertIsInstance(dashboard_data, dict)
                self.assertIn('user_id', dashboard_data)
                self.assertIn('layout', dashboard_data)
                self.assertIn('progress', dashboard_data)
                self.assertIn('sections', dashboard_data)
                self.assertIn('widgets', dashboard_data)
                self.assertIn('quick_actions', dashboard_data)
                self.assertIn('next_steps', dashboard_data)
                self.assertIn('recommendations', dashboard_data)
                self.assertIn('tutorials', dashboard_data)
                self.assertIn('recent_activities', dashboard_data)
                self.assertIn('goals', dashboard_data)
                self.assertIn('last_updated', dashboard_data)
    
    @patch.object(NewUserDashboardManager, 'progress_tracker')
    def test_get_dashboard_data_no_progress(self, mock_progress_tracker):
        """Test dashboard data retrieval when no progress exists"""
        # Mock no progress initially, then mock progress after starting
        mock_progress_tracker.get_progress.side_effect = [None, MagicMock()]
        
        # Mock start progress tracking
        mock_progress_tracker.start_progress_tracking.return_value = True
        
        # Mock tutorial system
        with patch.object(self.dashboard_manager, 'tutorial_system') as mock_tutorial_system:
            mock_tutorial_system.get_available_tutorials.return_value = []
            
            # Mock other methods
            with patch.object(self.dashboard_manager, '_get_recent_activities', return_value=[]):
                with patch.object(self.dashboard_manager, '_get_user_goals', return_value=[]):
                    dashboard_data = self.dashboard_manager.get_dashboard_data(self.user_id)
                    
                    self.assertIsInstance(dashboard_data, dict)
                    mock_progress_tracker.start_progress_tracking.assert_called_once_with(self.user_id)
    
    def test_determine_dashboard_layout_minimal(self):
        """Test dashboard layout determination for minimal progress"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 10.0
        
        layout = self.dashboard_manager._determine_dashboard_layout(mock_progress)
        
        self.assertEqual(layout, DashboardLayout.MINIMAL)
    
    def test_determine_dashboard_layout_basic(self):
        """Test dashboard layout determination for basic progress"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 30.0
        
        layout = self.dashboard_manager._determine_dashboard_layout(mock_progress)
        
        self.assertEqual(layout, DashboardLayout.BASIC)
    
    def test_determine_dashboard_layout_standard(self):
        """Test dashboard layout determination for standard progress"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 60.0
        
        layout = self.dashboard_manager._determine_dashboard_layout(mock_progress)
        
        self.assertEqual(layout, DashboardLayout.STANDARD)
    
    def test_determine_dashboard_layout_complete(self):
        """Test dashboard layout determination for complete progress"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 85.0
        
        layout = self.dashboard_manager._determine_dashboard_layout(mock_progress)
        
        self.assertEqual(layout, DashboardLayout.COMPLETE)
    
    def test_get_dashboard_sections_minimal(self):
        """Test dashboard sections for minimal layout"""
        mock_progress = MagicMock()
        mock_progress.unlocked_features = []
        
        sections = self.dashboard_manager._get_dashboard_sections(self.user_id, mock_progress, DashboardLayout.MINIMAL)
        
        self.assertIsInstance(sections, list)
        self.assertGreater(len(sections), 0)
        
        # Should have welcome and progress sections
        section_ids = [section['section_id'] for section in sections]
        self.assertIn(DashboardSection.WELCOME.value, section_ids)
        self.assertIn(DashboardSection.PROGRESS.value, section_ids)
    
    def test_get_dashboard_sections_basic(self):
        """Test dashboard sections for basic layout"""
        mock_progress = MagicMock()
        mock_progress.unlocked_features = []
        
        sections = self.dashboard_manager._get_dashboard_sections(self.user_id, mock_progress, DashboardLayout.BASIC)
        
        self.assertIsInstance(sections, list)
        self.assertGreater(len(sections), 0)
        
        # Should have quick actions section
        section_ids = [section['section_id'] for section in sections]
        self.assertIn(DashboardSection.QUICK_ACTIONS.value, section_ids)
    
    def test_get_dashboard_sections_with_activities(self):
        """Test dashboard sections when user has activities"""
        mock_progress = MagicMock()
        mock_progress.unlocked_features = ['activity_viewer']
        
        sections = self.dashboard_manager._get_dashboard_sections(self.user_id, mock_progress, DashboardLayout.STANDARD)
        
        self.assertIsInstance(sections, list)
        
        # Should have recent activities section
        section_ids = [section['section_id'] for section in sections]
        self.assertIn(DashboardSection.RECENT_ACTIVITIES.value, section_ids)
    
    def test_get_dashboard_sections_with_goals(self):
        """Test dashboard sections when user has goals"""
        mock_progress = MagicMock()
        mock_progress.unlocked_features = ['custom_goals']
        
        sections = self.dashboard_manager._get_dashboard_sections(self.user_id, mock_progress, DashboardLayout.STANDARD)
        
        self.assertIsInstance(sections, list)
        
        # Should have goals section
        section_ids = [section['section_id'] for section in sections]
        self.assertIn(DashboardSection.GOALS.value, section_ids)
    
    def test_get_dashboard_widgets_minimal(self):
        """Test dashboard widgets for minimal layout"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 10.0
        mock_progress.completed_steps = []
        mock_progress.unlocked_features = []
        
        widgets = self.dashboard_manager._get_dashboard_widgets(self.user_id, mock_progress, DashboardLayout.MINIMAL)
        
        self.assertIsInstance(widgets, list)
        self.assertGreater(len(widgets), 0)
        
        # Should have welcome and progress widgets
        widget_ids = [widget['widget_id'] for widget in widgets]
        self.assertIn('welcome_message', widget_ids)
        self.assertIn('onboarding_progress', widget_ids)
    
    def test_get_dashboard_widgets_basic(self):
        """Test dashboard widgets for basic layout"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 30.0
        mock_progress.completed_steps = []
        mock_progress.unlocked_features = []
        
        widgets = self.dashboard_manager._get_dashboard_widgets(self.user_id, mock_progress, DashboardLayout.BASIC)
        
        self.assertIsInstance(widgets, list)
        self.assertGreater(len(widgets), 0)
        
        # Should have quick action widgets
        widget_sections = [widget['section'] for widget in widgets]
        self.assertIn(DashboardSection.QUICK_ACTIONS.value, widget_sections)
    
    def test_get_quick_actions_no_strava(self):
        """Test quick actions when Strava not connected"""
        mock_progress = MagicMock()
        mock_progress.completed_steps = []
        mock_progress.unlocked_features = []
        
        actions = self.dashboard_manager._get_quick_actions(self.user_id, mock_progress)
        
        self.assertIsInstance(actions, list)
        
        # Should have connect Strava action
        action_ids = [action['id'] for action in actions]
        self.assertIn('connect_strava', action_ids)
    
    def test_get_quick_actions_with_strava(self):
        """Test quick actions when Strava is connected"""
        mock_progress = MagicMock()
        mock_progress.completed_steps = [OnboardingStep.STRAVA_CONNECTED]
        mock_progress.unlocked_features = ['activity_viewer']
        
        actions = self.dashboard_manager._get_quick_actions(self.user_id, mock_progress)
        
        self.assertIsInstance(actions, list)
        
        # Should not have connect Strava action
        action_ids = [action['id'] for action in actions]
        self.assertNotIn('connect_strava', action_ids)
        
        # Should have view activities action
        self.assertIn('view_activities', action_ids)
    
    def test_get_next_steps_welcome(self):
        """Test next steps for welcome step"""
        mock_progress = MagicMock()
        mock_progress.current_step = OnboardingStep.WELCOME
        mock_progress.progress_percentage = 10.0
        
        next_steps = self.dashboard_manager._get_next_steps(self.user_id, mock_progress)
        
        self.assertIsInstance(next_steps, list)
        self.assertGreater(len(next_steps), 0)
        
        # Should have connect Strava step
        step_ids = [step['id'] for step in next_steps]
        self.assertIn('connect_strava', step_ids)
    
    def test_get_next_steps_strava_connected(self):
        """Test next steps for Strava connected step"""
        mock_progress = MagicMock()
        mock_progress.current_step = OnboardingStep.STRAVA_CONNECTED
        mock_progress.progress_percentage = 20.0
        
        next_steps = self.dashboard_manager._get_next_steps(self.user_id, mock_progress)
        
        self.assertIsInstance(next_steps, list)
        self.assertGreater(len(next_steps), 0)
        
        # Should have sync activities step
        step_ids = [step['id'] for step in next_steps]
        self.assertIn('sync_activities', step_ids)
    
    def test_get_next_steps_goals_setup(self):
        """Test next steps for goals setup step"""
        mock_progress = MagicMock()
        mock_progress.current_step = OnboardingStep.GOALS_SETUP
        mock_progress.progress_percentage = 60.0
        
        next_steps = self.dashboard_manager._get_next_steps(self.user_id, mock_progress)
        
        self.assertIsInstance(next_steps, list)
        self.assertGreater(len(next_steps), 0)
        
        # Should have explore features step
        step_ids = [step['id'] for step in next_steps]
        self.assertIn('explore_features', step_ids)
    
    @patch.object(NewUserDashboardManager, 'tutorial_system')
    def test_get_recommendations(self, mock_tutorial_system):
        """Test getting recommendations"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 40.0
        
        # Mock tutorial system
        mock_tutorial_system.get_available_tutorials.return_value = [
            {'tutorial_id': 'welcome_tour', 'name': 'Welcome Tour'}
        ]
        mock_tutorial_system.get_recommended_tutorials.return_value = [
            {'tutorial_id': 'dashboard_tutorial', 'name': 'Dashboard Tutorial'}
        ]
        
        recommendations = self.dashboard_manager._get_recommendations(self.user_id, mock_progress)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Should have tutorial recommendations
        recommendation_types = [rec['type'] for rec in recommendations]
        self.assertIn('tutorial', recommendation_types)
    
    def test_get_recent_activities(self):
        """Test getting recent activities"""
        activities = self.dashboard_manager._get_recent_activities(self.user_id)
        
        self.assertIsInstance(activities, list)
        
        # Should return placeholder data for now
        if activities:
            self.assertIn('id', activities[0])
            self.assertIn('name', activities[0])
            self.assertIn('type', activities[0])
            self.assertIn('distance', activities[0])
            self.assertIn('duration', activities[0])
            self.assertIn('date', activities[0])
            self.assertIn('url', activities[0])
    
    def test_get_user_goals(self):
        """Test getting user goals"""
        goals = self.dashboard_manager._get_user_goals(self.user_id)
        
        self.assertIsInstance(goals, list)
        
        # Should return placeholder data for now
        if goals:
            self.assertIn('id', goals[0])
            self.assertIn('title', goals[0])
            self.assertIn('type', goals[0])
            self.assertIn('target', goals[0])
            self.assertIn('current', goals[0])
            self.assertIn('progress', goals[0])
            self.assertIn('deadline', goals[0])
    
    def test_get_welcome_message_low_progress(self):
        """Test welcome message for low progress"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 10.0
        
        message = self.dashboard_manager._get_welcome_message(mock_progress)
        
        self.assertIsInstance(message, str)
        self.assertIn('Welcome to TrainingMonkey', message)
        self.assertIn('get you started', message)
    
    def test_get_welcome_message_high_progress(self):
        """Test welcome message for high progress"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 85.0
        
        message = self.dashboard_manager._get_welcome_message(mock_progress)
        
        self.assertIsInstance(message, str)
        self.assertIn('Welcome back', message)
        self.assertIn('ready to train', message)
    
    def test_get_user_name(self):
        """Test getting user name"""
        name = self.dashboard_manager._get_user_name(self.user_id)
        
        self.assertIsInstance(name, str)
        self.assertEqual(name, 'Athlete')  # Placeholder value
    
    def test_get_days_since_join(self):
        """Test getting days since join"""
        days = self.dashboard_manager._get_days_since_join(self.user_id)
        
        self.assertIsInstance(days, int)
        self.assertEqual(days, 1)  # Placeholder value
    
    def test_get_quick_action_widgets(self):
        """Test getting quick action widgets"""
        mock_progress = MagicMock()
        mock_progress.completed_steps = []
        
        widgets = self.dashboard_manager._get_quick_action_widgets(self.user_id, mock_progress)
        
        self.assertIsInstance(widgets, list)
        
        # Should have connect Strava widget
        widget_ids = [widget['widget_id'] for widget in widgets]
        self.assertIn('connect_strava_action', widget_ids)
        
        # Should have dashboard tutorial widget
        self.assertIn('dashboard_tutorial_action', widget_ids)
    
    def test_get_recent_activities_widget_no_activities(self):
        """Test recent activities widget with no activities"""
        with patch.object(self.dashboard_manager, '_get_recent_activities', return_value=[]):
            widget = self.dashboard_manager._get_recent_activities_widget(self.user_id)
            
            self.assertIsNone(widget)
    
    def test_get_recent_activities_widget_with_activities(self):
        """Test recent activities widget with activities"""
        activities = [
            {
                'id': 'activity_1',
                'name': 'Morning Run',
                'type': 'Run',
                'distance': '5.2 km',
                'duration': '28:15',
                'date': datetime.now().isoformat(),
                'url': '/activities/1'
            }
        ]
        
        with patch.object(self.dashboard_manager, '_get_recent_activities', return_value=activities):
            widget = self.dashboard_manager._get_recent_activities_widget(self.user_id)
            
            self.assertIsNotNone(widget)
            self.assertEqual(widget['widget_id'], 'recent_activities')
            self.assertEqual(widget['section'], DashboardSection.RECENT_ACTIVITIES.value)
            self.assertEqual(widget['widget_type'], 'activity_list')
    
    def test_get_goals_widget_no_goals(self):
        """Test goals widget with no goals"""
        with patch.object(self.dashboard_manager, '_get_user_goals', return_value=[]):
            widget = self.dashboard_manager._get_goals_widget(self.user_id)
            
            self.assertIsNone(widget)
    
    def test_get_goals_widget_with_goals(self):
        """Test goals widget with goals"""
        goals = [
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
        
        with patch.object(self.dashboard_manager, '_get_user_goals', return_value=goals):
            widget = self.dashboard_manager._get_goals_widget(self.user_id)
            
            self.assertIsNotNone(widget)
            self.assertEqual(widget['widget_id'], 'user_goals')
            self.assertEqual(widget['section'], DashboardSection.GOALS.value)
            self.assertEqual(widget['widget_type'], 'goal_cards')
    
    @patch.object(NewUserDashboardManager, 'tutorial_system')
    def test_get_recommendations_widget_no_recommendations(self, mock_tutorial_system):
        """Test recommendations widget with no recommendations"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 10.0
        
        # Mock empty recommendations
        with patch.object(self.dashboard_manager, '_get_recommendations', return_value=[]):
            widget = self.dashboard_manager._get_recommendations_widget(self.user_id, mock_progress)
            
            self.assertIsNone(widget)
    
    @patch.object(NewUserDashboardManager, 'tutorial_system')
    def test_get_recommendations_widget_with_recommendations(self, mock_tutorial_system):
        """Test recommendations widget with recommendations"""
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 40.0
        
        recommendations = [
            {
                'id': 'tutorial_welcome_tour',
                'type': 'tutorial',
                'title': 'Welcome Tour',
                'description': 'Get started with TrainingMonkey',
                'url': '/tutorials/welcome_tour',
                'estimated_time': '60 seconds',
                'priority': 90
            }
        ]
        
        with patch.object(self.dashboard_manager, '_get_recommendations', return_value=recommendations):
            widget = self.dashboard_manager._get_recommendations_widget(self.user_id, mock_progress)
            
            self.assertIsNotNone(widget)
            self.assertEqual(widget['widget_id'], 'recommendations')
            self.assertEqual(widget['section'], DashboardSection.RECOMMENDATIONS.value)
            self.assertEqual(widget['widget_type'], 'recommendation_list')
    
    @patch.object(NewUserDashboardManager, 'tutorial_system')
    def test_get_tutorials_widget_no_tutorials(self, mock_tutorial_system):
        """Test tutorials widget with no tutorials"""
        mock_tutorial_system.get_available_tutorials.return_value = []
        
        widget = self.dashboard_manager._get_tutorials_widget(self.user_id)
        
        self.assertIsNone(widget)
    
    @patch.object(NewUserDashboardManager, 'tutorial_system')
    def test_get_tutorials_widget_with_tutorials(self, mock_tutorial_system):
        """Test tutorials widget with tutorials"""
        tutorials = [
            {
                'tutorial_id': 'welcome_tour',
                'name': 'Welcome Tour',
                'description': 'Get started with TrainingMonkey',
                'tutorial_type': 'walkthrough',
                'trigger': 'automatic',
                'estimated_duration': 120,
                'difficulty_level': 'beginner',
                'category': 'onboarding',
                'completed': False,
                'prerequisites_met': True
            }
        ]
        
        mock_tutorial_system.get_available_tutorials.return_value = tutorials
        
        widget = self.dashboard_manager._get_tutorials_widget(self.user_id)
        
        self.assertIsNotNone(widget)
        self.assertEqual(widget['widget_id'], 'available_tutorials')
        self.assertEqual(widget['section'], DashboardSection.TUTORIALS.value)
        self.assertEqual(widget['widget_type'], 'tutorial_grid')
    
    def test_get_next_steps_widget_no_steps(self):
        """Test next steps widget with no steps"""
        mock_progress = MagicMock()
        mock_progress.current_step = OnboardingStep.COMPLETED
        mock_progress.progress_percentage = 100.0
        
        with patch.object(self.dashboard_manager, '_get_next_steps', return_value=[]):
            widget = self.dashboard_manager._get_next_steps_widget(self.user_id, mock_progress)
            
            self.assertIsNone(widget)
    
    def test_get_next_steps_widget_with_steps(self):
        """Test next steps widget with steps"""
        mock_progress = MagicMock()
        mock_progress.current_step = OnboardingStep.WELCOME
        mock_progress.progress_percentage = 10.0
        
        next_steps = [
            {
                'id': 'connect_strava',
                'title': 'Connect Your Strava Account',
                'description': 'Link your Strava account to start syncing activities',
                'url': '/connect-strava',
                'estimated_time': '2 minutes',
                'priority': 100
            }
        ]
        
        with patch.object(self.dashboard_manager, '_get_next_steps', return_value=next_steps):
            widget = self.dashboard_manager._get_next_steps_widget(self.user_id, mock_progress)
            
            self.assertIsNotNone(widget)
            self.assertEqual(widget['widget_id'], 'next_steps')
            self.assertEqual(widget['section'], DashboardSection.NEXT_STEPS.value)
            self.assertEqual(widget['widget_type'], 'step_list')
    
    def test_get_help_widget(self):
        """Test help widget"""
        widget = self.dashboard_manager._get_help_widget(self.user_id)
        
        self.assertIsNotNone(widget)
        self.assertEqual(widget['widget_id'], 'help_support')
        self.assertEqual(widget['section'], DashboardSection.HELP.value)
        self.assertEqual(widget['widget_type'], 'help_cards')
        
        # Should have help options
        self.assertIn('help_options', widget['data'])
        help_options = widget['data']['help_options']
        self.assertGreater(len(help_options), 0)
        
        # Should have tutorials, FAQ, and contact options
        option_ids = [option['id'] for option in help_options]
        self.assertIn('tutorials', option_ids)
        self.assertIn('faq', option_ids)
        self.assertIn('contact', option_ids)
    
    def test_get_fallback_dashboard_data(self):
        """Test fallback dashboard data"""
        dashboard_data = self.dashboard_manager._get_fallback_dashboard_data(self.user_id)
        
        self.assertIsInstance(dashboard_data, dict)
        self.assertIn('user_id', dashboard_data)
        self.assertIn('layout', dashboard_data)
        self.assertIn('progress', dashboard_data)
        self.assertIn('sections', dashboard_data)
        self.assertIn('widgets', dashboard_data)
        self.assertIn('quick_actions', dashboard_data)
        self.assertIn('next_steps', dashboard_data)
        self.assertIn('recommendations', dashboard_data)
        self.assertIn('tutorials', dashboard_data)
        self.assertIn('recent_activities', dashboard_data)
        self.assertIn('goals', dashboard_data)
        self.assertIn('last_updated', dashboard_data)
        
        # Should have minimal layout
        self.assertEqual(dashboard_data['layout'], DashboardLayout.MINIMAL.value)
        
        # Should have welcome section
        section_ids = [section['section_id'] for section in dashboard_data['sections']]
        self.assertIn(DashboardSection.WELCOME.value, section_ids)
        
        # Should have welcome widget
        widget_ids = [widget['widget_id'] for widget in dashboard_data['widgets']]
        self.assertIn('welcome_message', widget_ids)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch.object(dashboard_manager, 'get_dashboard_data')
    def test_get_dashboard_data_function(self, mock_get_data):
        """Test convenience function for getting dashboard data"""
        mock_data = {'user_id': self.user_id, 'layout': 'minimal'}
        mock_get_data.return_value = mock_data
        
        dashboard_data = get_dashboard_data(self.user_id)
        
        self.assertEqual(dashboard_data, mock_data)
        mock_get_data.assert_called_once_with(self.user_id)


class TestEnumsAndDataClasses(unittest.TestCase):
    """Test cases for enums and data classes"""
    
    def test_dashboard_section_enum(self):
        """Test DashboardSection enum values"""
        self.assertEqual(DashboardSection.WELCOME.value, 'welcome')
        self.assertEqual(DashboardSection.PROGRESS.value, 'progress')
        self.assertEqual(DashboardSection.QUICK_ACTIONS.value, 'quick_actions')
        self.assertEqual(DashboardSection.RECENT_ACTIVITIES.value, 'recent_activities')
        self.assertEqual(DashboardSection.GOALS.value, 'goals')
        self.assertEqual(DashboardSection.RECOMMENDATIONS.value, 'recommendations')
        self.assertEqual(DashboardSection.TUTORIALS.value, 'tutorials')
        self.assertEqual(DashboardSection.FEATURES.value, 'features')
        self.assertEqual(DashboardSection.NEXT_STEPS.value, 'next_steps')
        self.assertEqual(DashboardSection.HELP.value, 'help')
    
    def test_dashboard_layout_enum(self):
        """Test DashboardLayout enum values"""
        self.assertEqual(DashboardLayout.MINIMAL.value, 'minimal')
        self.assertEqual(DashboardLayout.BASIC.value, 'basic')
        self.assertEqual(DashboardLayout.STANDARD.value, 'standard')
        self.assertEqual(DashboardLayout.COMPLETE.value, 'complete')
    
    def test_dashboard_widget_dataclass(self):
        """Test DashboardWidget dataclass"""
        widget = DashboardWidget(
            widget_id='test_widget',
            section=DashboardSection.WELCOME,
            title='Test Widget',
            content='Test widget content',
            widget_type='card',
            data={'key': 'value'},
            actions=[{'text': 'Click', 'url': '/test'}],
            visible=True,
            priority=100,
            requires_feature='dashboard_basic',
            requires_step=OnboardingStep.WELCOME
        )
        
        self.assertEqual(widget.widget_id, 'test_widget')
        self.assertEqual(widget.section, DashboardSection.WELCOME)
        self.assertEqual(widget.title, 'Test Widget')
        self.assertEqual(widget.content, 'Test widget content')
        self.assertEqual(widget.widget_type, 'card')
        self.assertEqual(widget.data, {'key': 'value'})
        self.assertEqual(widget.actions, [{'text': 'Click', 'url': '/test'}])
        self.assertTrue(widget.visible)
        self.assertEqual(widget.priority, 100)
        self.assertEqual(widget.requires_feature, 'dashboard_basic')
        self.assertEqual(widget.requires_step, OnboardingStep.WELCOME)
    
    def test_dashboard_section_dataclass(self):
        """Test DashboardSection dataclass"""
        section = DashboardSectionClass(
            section_id=DashboardSection.WELCOME,
            title='Welcome Section',
            description='Welcome section description',
            widgets=[],
            visible=True,
            order=1,
            requires_feature='dashboard_basic',
            requires_step=OnboardingStep.WELCOME,
            layout='grid'
        )
        
        self.assertEqual(section.section_id, DashboardSection.WELCOME)
        self.assertEqual(section.title, 'Welcome Section')
        self.assertEqual(section.description, 'Welcome section description')
        self.assertEqual(section.widgets, [])
        self.assertTrue(section.visible)
        self.assertEqual(section.order, 1)
        self.assertEqual(section.requires_feature, 'dashboard_basic')
        self.assertEqual(section.requires_step, OnboardingStep.WELCOME)
        self.assertEqual(section.layout, 'grid')
    
    def test_new_user_dashboard_dataclass(self):
        """Test NewUserDashboard dataclass"""
        dashboard = NewUserDashboard(
            user_id=1,
            layout=DashboardLayout.MINIMAL,
            sections=[],
            widgets=[],
            customization={'theme': 'light'}
        )
        
        self.assertEqual(dashboard.user_id, 1)
        self.assertEqual(dashboard.layout, DashboardLayout.MINIMAL)
        self.assertEqual(dashboard.sections, [])
        self.assertEqual(dashboard.widgets, [])
        self.assertEqual(dashboard.customization, {'theme': 'light'})
        self.assertIsInstance(dashboard.last_updated, datetime)


class TestDashboardIntegration(unittest.TestCase):
    """Integration tests for dashboard functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.dashboard_manager = NewUserDashboardManager()
        self.user_id = 1
    
    @patch.object(NewUserDashboardManager, 'progress_tracker')
    @patch.object(NewUserDashboardManager, 'tutorial_system')
    def test_complete_dashboard_integration(self, mock_tutorial_system, mock_progress_tracker):
        """Test complete dashboard integration"""
        # Mock comprehensive progress data
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 75.0
        mock_progress.current_step = OnboardingStep.GOALS_SETUP
        mock_progress.completed_steps = [
            OnboardingStep.WELCOME,
            OnboardingStep.STRAVA_CONNECTED,
            OnboardingStep.FIRST_ACTIVITY,
            OnboardingStep.DASHBOARD_INTRO
        ]
        mock_progress.unlocked_features = [
            'dashboard_basic',
            'activity_viewer',
            'custom_goals'
        ]
        mock_progress.current_tier = FeatureTier.INTERMEDIATE
        mock_progress.status = 'in_progress'
        
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock tutorial system
        mock_tutorial_system.get_available_tutorials.return_value = [
            {'tutorial_id': 'goals_setup_tutorial', 'name': 'Goals Setup Tutorial'}
        ]
        mock_tutorial_system.get_recommended_tutorials.return_value = [
            {'tutorial_id': 'goals_setup_tutorial', 'name': 'Goals Setup Tutorial'}
        ]
        
        # Mock other methods
        with patch.object(self.dashboard_manager, '_get_recent_activities', return_value=[
            {'id': 'activity_1', 'name': 'Morning Run', 'type': 'Run', 'distance': '5.2 km', 'duration': '28:15', 'date': datetime.now().isoformat(), 'url': '/activities/1'}
        ]):
            with patch.object(self.dashboard_manager, '_get_user_goals', return_value=[
                {'id': 'goal_1', 'title': 'Run 100km this month', 'type': 'distance', 'target': '100 km', 'current': '25 km', 'progress': 25.0, 'deadline': (datetime.now() + timedelta(days=20)).isoformat()}
            ]):
                dashboard_data = self.dashboard_manager.get_dashboard_data(self.user_id)
                
                # Verify layout
                self.assertEqual(dashboard_data['layout'], DashboardLayout.STANDARD.value)
                
                # Verify progress data
                self.assertEqual(dashboard_data['progress']['overall_percentage'], 75.0)
                self.assertEqual(dashboard_data['progress']['current_step'], OnboardingStep.GOALS_SETUP.value)
                self.assertEqual(len(dashboard_data['progress']['completed_steps']), 4)
                self.assertEqual(len(dashboard_data['progress']['unlocked_features']), 3)
                self.assertEqual(dashboard_data['progress']['current_tier'], FeatureTier.INTERMEDIATE.value)
                
                # Verify sections
                self.assertGreater(len(dashboard_data['sections']), 0)
                section_ids = [section['section_id'] for section in dashboard_data['sections']]
                self.assertIn(DashboardSection.WELCOME.value, section_ids)
                self.assertIn(DashboardSection.PROGRESS.value, section_ids)
                self.assertIn(DashboardSection.QUICK_ACTIONS.value, section_ids)
                self.assertIn(DashboardSection.RECENT_ACTIVITIES.value, section_ids)
                self.assertIn(DashboardSection.GOALS.value, section_ids)
                self.assertIn(DashboardSection.RECOMMENDATIONS.value, section_ids)
                
                # Verify widgets
                self.assertGreater(len(dashboard_data['widgets']), 0)
                
                # Verify quick actions
                self.assertGreater(len(dashboard_data['quick_actions']), 0)
                
                # Verify next steps
                self.assertGreater(len(dashboard_data['next_steps']), 0)
                
                # Verify recommendations
                self.assertGreater(len(dashboard_data['recommendations']), 0)
                
                # Verify tutorials
                self.assertGreater(len(dashboard_data['tutorials']), 0)
                
                # Verify recent activities
                self.assertGreater(len(dashboard_data['recent_activities']), 0)
                
                # Verify goals
                self.assertGreater(len(dashboard_data['goals']), 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)


