"""
Test Suite for Onboarding Tutorial System Module

This module tests the comprehensive onboarding tutorial system functionality including:
- Tutorial initialization and management
- Tutorial session handling and progress tracking
- Tutorial content generation and rendering
- Tutorial recommendations and analytics
- Tutorial prerequisites and completion tracking
- Tutorial skip and resume functionality
- Tutorial personalization and scoring
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json

from onboarding_tutorial_system import (
    OnboardingTutorialSystem,
    TutorialType,
    TutorialTrigger,
    TutorialStatus,
    TutorialStep,
    Tutorial,
    TutorialSession,
    TutorialAnalytics,
    start_tutorial,
    get_tutorial_session,
    update_tutorial_progress,
    complete_tutorial,
    skip_tutorial,
    get_available_tutorials,
    get_recommended_tutorials,
    get_tutorial_analytics,
    get_tutorial_content,
    tutorial_system
)
from onboarding_manager import OnboardingStep, FeatureTier


class TestOnboardingTutorialSystem(unittest.TestCase):
    """Test cases for OnboardingTutorialSystem class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tutorial_system = OnboardingTutorialSystem()
        self.user_id = 1
    
    def test_initialization(self):
        """Test tutorial system initialization"""
        self.assertIsNotNone(self.tutorial_system.onboarding_manager)
        self.assertIsNotNone(self.tutorial_system.progress_tracker)
        self.assertIsNotNone(self.tutorial_system.tiered_feature_manager)
        self.assertIsNotNone(self.tutorial_system.tutorials)
        self.assertIsNotNone(self.tutorial_system.active_sessions)
        
        # Check that tutorials are defined
        self.assertGreater(len(self.tutorial_system.tutorials), 0)
        
        # Check tutorial structure
        for tutorial_id, tutorial in self.tutorial_system.tutorials.items():
            self.assertIsInstance(tutorial, Tutorial)
            self.assertEqual(tutorial.tutorial_id, tutorial_id)
            self.assertIsInstance(tutorial.name, str)
            self.assertIsInstance(tutorial.description, str)
            self.assertIsInstance(tutorial.tutorial_type, TutorialType)
            self.assertIsInstance(tutorial.trigger, TutorialTrigger)
            self.assertIsInstance(tutorial.steps, list)
            self.assertIsInstance(tutorial.estimated_duration, int)
            self.assertIsInstance(tutorial.difficulty_level, str)
            self.assertIsInstance(tutorial.category, str)
    
    def test_tutorials_structure(self):
        """Test that tutorials have correct structure"""
        expected_tutorials = [
            'welcome_tour', 'strava_connection_guide', 'first_activity_tutorial',
            'dashboard_tutorial', 'features_tour', 'goals_setup_tutorial', 'journal_tutorial'
        ]
        
        for tutorial_id in expected_tutorials:
            self.assertIn(tutorial_id, self.tutorial_system.tutorials)
    
    def test_tutorial_steps_structure(self):
        """Test that tutorial steps have correct structure"""
        for tutorial_id, tutorial in self.tutorial_system.tutorials.items():
            for step in tutorial.steps:
                self.assertIsInstance(step, TutorialStep)
                self.assertIsInstance(step.step_id, str)
                self.assertIsInstance(step.title, str)
                self.assertIsInstance(step.content, str)
                self.assertIsInstance(step.position, str)
                self.assertIsInstance(step.action_required, bool)
                self.assertIsInstance(step.estimated_duration, int)
                self.assertIsInstance(step.interactive, bool)
                self.assertIsInstance(step.skip_allowed, bool)
    
    @patch.object(OnboardingTutorialSystem, 'onboarding_manager')
    @patch.object(OnboardingTutorialSystem, 'progress_tracker')
    def test_start_tutorial_success(self, mock_progress_tracker, mock_onboarding_manager):
        """Test successful tutorial start"""
        # Mock tutorial prerequisites check
        with patch.object(self.tutorial_system, '_check_tutorial_prerequisites', return_value=True):
            # Mock database save
            with patch.object(self.tutorial_system, '_save_tutorial_session'):
                session = self.tutorial_system.start_tutorial(self.user_id, 'welcome_tour')
                
                self.assertIsNotNone(session)
                self.assertEqual(session.user_id, self.user_id)
                self.assertEqual(session.tutorial_id, 'welcome_tour')
                self.assertEqual(session.status, TutorialStatus.IN_PROGRESS)
                self.assertIsInstance(session.start_time, datetime)
                self.assertIsInstance(session.last_activity, datetime)
    
    def test_start_tutorial_not_found(self):
        """Test tutorial start with non-existent tutorial"""
        session = self.tutorial_system.start_tutorial(self.user_id, 'non_existent_tutorial')
        
        self.assertIsNone(session)
    
    @patch.object(OnboardingTutorialSystem, '_check_tutorial_prerequisites')
    def test_start_tutorial_prerequisites_not_met(self, mock_prerequisites):
        """Test tutorial start when prerequisites not met"""
        mock_prerequisites.return_value = False
        
        session = self.tutorial_system.start_tutorial(self.user_id, 'welcome_tour')
        
        self.assertIsNone(session)
        mock_prerequisites.assert_called_once()
    
    @patch.object(OnboardingTutorialSystem, '_load_tutorial_session')
    def test_get_tutorial_session_success(self, mock_load):
        """Test successful tutorial session retrieval"""
        # Mock session data
        mock_session = TutorialSession(
            session_id='test_session',
            user_id=self.user_id,
            tutorial_id='welcome_tour',
            status=TutorialStatus.IN_PROGRESS
        )
        
        mock_load.return_value = mock_session
        
        session = self.tutorial_system.get_tutorial_session('test_session')
        
        self.assertIsNotNone(session)
        self.assertEqual(session.session_id, 'test_session')
        self.assertEqual(session.user_id, self.user_id)
        self.assertEqual(session.tutorial_id, 'welcome_tour')
    
    @patch.object(OnboardingTutorialSystem, '_load_tutorial_session')
    def test_get_tutorial_session_not_found(self, mock_load):
        """Test tutorial session retrieval when not found"""
        mock_load.return_value = None
        
        session = self.tutorial_system.get_tutorial_session('non_existent_session')
        
        self.assertIsNone(session)
    
    @patch.object(OnboardingTutorialSystem, 'get_tutorial_session')
    @patch.object(OnboardingTutorialSystem, '_save_tutorial_session')
    def test_update_tutorial_progress_success(self, mock_save, mock_get_session):
        """Test successful tutorial progress update"""
        # Mock session data
        mock_session = TutorialSession(
            session_id='test_session',
            user_id=self.user_id,
            tutorial_id='welcome_tour',
            status=TutorialStatus.IN_PROGRESS,
            completed_steps=[],
            interactions=[]
        )
        
        mock_get_session.return_value = mock_session
        
        # Mock tutorial data
        with patch.dict(self.tutorial_system.tutorials, {
            'welcome_tour': Tutorial(
                tutorial_id='welcome_tour',
                name='Welcome Tour',
                description='Test tutorial',
                tutorial_type=TutorialType.WALKTHROUGH,
                trigger=TutorialTrigger.AUTOMATIC,
                steps=[TutorialStep(step_id='step1', title='Step 1', content='Content 1')]
            )
        }):
            success = self.tutorial_system.update_tutorial_progress(
                'test_session', 'step1', 'completed'
            )
            
            self.assertTrue(success)
            self.assertIn('step1', mock_session.completed_steps)
            self.assertEqual(len(mock_session.interactions), 1)
            mock_save.assert_called_once()
    
    @patch.object(OnboardingTutorialSystem, 'get_tutorial_session')
    def test_update_tutorial_progress_session_not_found(self, mock_get_session):
        """Test tutorial progress update when session not found"""
        mock_get_session.return_value = None
        
        success = self.tutorial_system.update_tutorial_progress(
            'non_existent_session', 'step1', 'completed'
        )
        
        self.assertFalse(success)
    
    @patch.object(OnboardingTutorialSystem, 'get_tutorial_session')
    @patch.object(OnboardingTutorialSystem, '_save_tutorial_session')
    def test_complete_tutorial_success(self, mock_save, mock_get_session):
        """Test successful tutorial completion"""
        # Mock session data
        mock_session = TutorialSession(
            session_id='test_session',
            user_id=self.user_id,
            tutorial_id='welcome_tour',
            status=TutorialStatus.IN_PROGRESS,
            completed_steps=['step1'],
            start_time=datetime.now() - timedelta(minutes=5)
        )
        
        mock_get_session.return_value = mock_session
        
        # Mock tutorial data
        with patch.dict(self.tutorial_system.tutorials, {
            'welcome_tour': Tutorial(
                tutorial_id='welcome_tour',
                name='Welcome Tour',
                description='Test tutorial',
                tutorial_type=TutorialType.WALKTHROUGH,
                trigger=TutorialTrigger.AUTOMATIC,
                steps=[
                    TutorialStep(step_id='step1', title='Step 1', content='Content 1'),
                    TutorialStep(step_id='step2', title='Step 2', content='Content 2')
                ]
            )
        }):
            success = self.tutorial_system.complete_tutorial('test_session')
            
            self.assertTrue(success)
            self.assertEqual(mock_session.status, TutorialStatus.COMPLETED)
            self.assertEqual(mock_session.progress_percentage, 100.0)
            self.assertIsNotNone(mock_session.end_time)
            self.assertGreater(mock_session.time_spent, 0)
            mock_save.assert_called_once()
    
    @patch.object(OnboardingTutorialSystem, 'get_tutorial_session')
    def test_complete_tutorial_session_not_found(self, mock_get_session):
        """Test tutorial completion when session not found"""
        mock_get_session.return_value = None
        
        success = self.tutorial_system.complete_tutorial('non_existent_session')
        
        self.assertFalse(success)
    
    @patch.object(OnboardingTutorialSystem, 'get_tutorial_session')
    @patch.object(OnboardingTutorialSystem, '_save_tutorial_session')
    def test_skip_tutorial_success(self, mock_save, mock_get_session):
        """Test successful tutorial skip"""
        # Mock session data
        mock_session = TutorialSession(
            session_id='test_session',
            user_id=self.user_id,
            tutorial_id='welcome_tour',
            status=TutorialStatus.IN_PROGRESS,
            start_time=datetime.now() - timedelta(minutes=2)
        )
        
        mock_get_session.return_value = mock_session
        
        success = self.tutorial_system.skip_tutorial('test_session', 'Too busy')
        
        self.assertTrue(success)
        self.assertEqual(mock_session.status, TutorialStatus.SKIPPED)
        self.assertIsNotNone(mock_session.end_time)
        self.assertIsNotNone(mock_session.user_feedback)
        self.assertEqual(mock_session.user_feedback['reason'], 'Too busy')
        mock_save.assert_called_once()
    
    @patch.object(OnboardingTutorialSystem, 'get_tutorial_session')
    def test_skip_tutorial_session_not_found(self, mock_get_session):
        """Test tutorial skip when session not found"""
        mock_get_session.return_value = None
        
        success = self.tutorial_system.skip_tutorial('non_existent_session')
        
        self.assertFalse(success)
    
    @patch.object(OnboardingTutorialSystem, '_check_tutorial_prerequisites')
    @patch.object(OnboardingTutorialSystem, '_has_user_completed_tutorial')
    def test_get_available_tutorials(self, mock_completed, mock_prerequisites):
        """Test getting available tutorials"""
        mock_prerequisites.return_value = True
        mock_completed.return_value = False
        
        tutorials = self.tutorial_system.get_available_tutorials(self.user_id)
        
        self.assertIsInstance(tutorials, list)
        self.assertGreater(len(tutorials), 0)
        
        for tutorial in tutorials:
            self.assertIn('tutorial_id', tutorial)
            self.assertIn('name', tutorial)
            self.assertIn('description', tutorial)
            self.assertIn('tutorial_type', tutorial)
            self.assertIn('trigger', tutorial)
            self.assertIn('estimated_duration', tutorial)
            self.assertIn('difficulty_level', tutorial)
            self.assertIn('category', tutorial)
            self.assertIn('completed', tutorial)
            self.assertIn('prerequisites_met', tutorial)
    
    @patch.object(OnboardingTutorialSystem, 'get_available_tutorials')
    @patch.object(OnboardingTutorialSystem, 'progress_tracker')
    def test_get_recommended_tutorials(self, mock_progress_tracker, mock_available):
        """Test getting recommended tutorials"""
        # Mock available tutorials
        mock_available.return_value = [
            {
                'tutorial_id': 'welcome_tour',
                'name': 'Welcome Tour',
                'description': 'Test tutorial',
                'tutorial_type': 'walkthrough',
                'trigger': 'automatic',
                'difficulty_level': 'beginner',
                'completed': False
            }
        ]
        
        # Mock progress data
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 10.0
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        recommendations = self.tutorial_system.get_recommended_tutorials(self.user_id, limit=3)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        for recommendation in recommendations:
            self.assertIn('tutorial_id', recommendation)
            self.assertIn('relevance_score', recommendation)
    
    def test_get_tutorial_analytics(self):
        """Test getting tutorial analytics"""
        analytics = self.tutorial_system.get_tutorial_analytics('welcome_tour')
        
        self.assertIsNotNone(analytics)
        self.assertIsInstance(analytics, TutorialAnalytics)
        self.assertEqual(analytics.tutorial_id, 'welcome_tour')
        self.assertIsInstance(analytics.total_sessions, int)
        self.assertIsInstance(analytics.completed_sessions, int)
        self.assertIsInstance(analytics.skipped_sessions, int)
        self.assertIsInstance(analytics.average_completion_time, float)
        self.assertIsInstance(analytics.average_progress_percentage, float)
        self.assertIsInstance(analytics.user_satisfaction_score, float)
        self.assertIsInstance(analytics.common_dropout_points, list)
        self.assertIsInstance(analytics.effectiveness_score, float)
    
    def test_get_tutorial_content_full(self):
        """Test getting full tutorial content"""
        content = self.tutorial_system.get_tutorial_content('welcome_tour')
        
        self.assertIsNotNone(content)
        self.assertIn('tutorial_id', content)
        self.assertIn('name', content)
        self.assertIn('description', content)
        self.assertIn('tutorial_type', content)
        self.assertIn('trigger', content)
        self.assertIn('estimated_duration', content)
        self.assertIn('difficulty_level', content)
        self.assertIn('category', content)
        self.assertIn('steps', content)
        self.assertIsInstance(content['steps'], list)
    
    def test_get_tutorial_content_step(self):
        """Test getting specific tutorial step content"""
        content = self.tutorial_system.get_tutorial_content('welcome_tour', 'welcome_intro')
        
        self.assertIsNotNone(content)
        self.assertIn('tutorial_id', content)
        self.assertIn('step', content)
        self.assertIn('step_id', content['step'])
        self.assertIn('title', content['step'])
        self.assertIn('content', content['step'])
        self.assertIn('position', content['step'])
        self.assertIn('action_required', content['step'])
        self.assertIn('estimated_duration', content['step'])
        self.assertIn('interactive', content['step'])
        self.assertIn('skip_allowed', content['step'])
    
    def test_get_tutorial_content_not_found(self):
        """Test getting tutorial content for non-existent tutorial"""
        content = self.tutorial_system.get_tutorial_content('non_existent_tutorial')
        
        self.assertIsNone(content)
    
    def test_get_tutorial_content_step_not_found(self):
        """Test getting tutorial step content for non-existent step"""
        content = self.tutorial_system.get_tutorial_content('welcome_tour', 'non_existent_step')
        
        self.assertIsNone(content)
    
    @patch.object(OnboardingTutorialSystem, 'onboarding_manager')
    def test_check_tutorial_prerequisites_step_completion(self, mock_onboarding_manager):
        """Test tutorial prerequisites check for step completion"""
        # Mock tutorial with step prerequisite
        tutorial = Tutorial(
            tutorial_id='test_tutorial',
            name='Test Tutorial',
            description='Test tutorial',
            tutorial_type=TutorialType.WALKTHROUGH,
            trigger=TutorialTrigger.AUTOMATIC,
            prerequisites=['step:welcome']
        )
        
        # Mock onboarding manager
        mock_onboarding_manager.has_completed_step.return_value = True
        
        result = self.tutorial_system._check_tutorial_prerequisites(self.user_id, tutorial)
        
        self.assertTrue(result)
        mock_onboarding_manager.has_completed_step.assert_called_once()
    
    @patch.object(OnboardingTutorialSystem, 'onboarding_manager')
    def test_check_tutorial_prerequisites_feature_unlock(self, mock_onboarding_manager):
        """Test tutorial prerequisites check for feature unlock"""
        # Mock tutorial with feature prerequisite
        tutorial = Tutorial(
            tutorial_id='test_tutorial',
            name='Test Tutorial',
            description='Test tutorial',
            tutorial_type=TutorialType.WALKTHROUGH,
            trigger=TutorialTrigger.AUTOMATIC,
            prerequisites=['feature:dashboard_basic']
        )
        
        # Mock onboarding manager
        mock_onboarding_manager.check_feature_unlock.return_value = True
        
        result = self.tutorial_system._check_tutorial_prerequisites(self.user_id, tutorial)
        
        self.assertTrue(result)
        mock_onboarding_manager.check_feature_unlock.assert_called_once()
    
    @patch.object(OnboardingTutorialSystem, 'tiered_feature_manager')
    def test_check_tutorial_prerequisites_activity_count(self, mock_tiered_manager):
        """Test tutorial prerequisites check for activity count"""
        # Mock tutorial with activity count prerequisite
        tutorial = Tutorial(
            tutorial_id='test_tutorial',
            name='Test Tutorial',
            description='Test tutorial',
            tutorial_type=TutorialType.WALKTHROUGH,
            trigger=TutorialTrigger.AUTOMATIC,
            prerequisites=['activities:5']
        )
        
        # Mock tiered feature manager
        mock_tiered_manager._get_user_activity_count.return_value = 10
        
        result = self.tutorial_system._check_tutorial_prerequisites(self.user_id, tutorial)
        
        self.assertTrue(result)
        mock_tiered_manager._get_user_activity_count.assert_called_once()
    
    def test_has_user_completed_tutorial(self):
        """Test checking if user has completed tutorial"""
        result = self.tutorial_system._has_user_completed_tutorial(self.user_id, 'welcome_tour')
        
        # Should return False as placeholder implementation
        self.assertFalse(result)
    
    @patch.object(OnboardingTutorialSystem, 'progress_tracker')
    def test_calculate_tutorial_relevance_score(self, mock_progress_tracker):
        """Test tutorial relevance score calculation"""
        # Mock progress data
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 25.0
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock tutorial info
        tutorial_info = {
            'completed': False,
            'trigger': 'on_step_enter',
            'difficulty_level': 'beginner'
        }
        
        score = self.tutorial_system._calculate_tutorial_relevance_score(
            self.user_id, tutorial_info, mock_progress
        )
        
        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
    
    @patch('onboarding_tutorial_system.USE_POSTGRES', True)
    @patch('onboarding_tutorial_system.get_db_connection')
    def test_postgresql_save_tutorial_session(self, mock_db):
        """Test PostgreSQL save tutorial session query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        session = TutorialSession(
            session_id='test_session',
            user_id=self.user_id,
            tutorial_id='welcome_tour',
            status=TutorialStatus.IN_PROGRESS
        )
        
        self.tutorial_system._save_tutorial_session(session)
        
        # Verify PostgreSQL query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("INSERT INTO user_settings", call_args[0][0])
        self.assertIn("tutorial_sessions", call_args[0][0])
    
    @patch('onboarding_tutorial_system.USE_POSTGRES', False)
    @patch('onboarding_tutorial_system.get_db_connection')
    def test_sqlite_save_tutorial_session(self, mock_db):
        """Test SQLite save tutorial session query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        session = TutorialSession(
            session_id='test_session',
            user_id=self.user_id,
            tutorial_id='welcome_tour',
            status=TutorialStatus.IN_PROGRESS
        )
        
        self.tutorial_system._save_tutorial_session(session)
        
        # Verify SQLite query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("INSERT OR REPLACE INTO user_settings", call_args[0][0])
        self.assertIn("tutorial_sessions", call_args[0][0])


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch.object(tutorial_system, 'start_tutorial')
    def test_start_tutorial_function(self, mock_start):
        """Test convenience function for starting tutorial"""
        mock_session = MagicMock()
        mock_start.return_value = mock_session
        
        session = start_tutorial(self.user_id, 'welcome_tour')
        
        self.assertEqual(session, mock_session)
        mock_start.assert_called_once_with(self.user_id, 'welcome_tour')
    
    @patch.object(tutorial_system, 'get_tutorial_session')
    def test_get_tutorial_session_function(self, mock_get):
        """Test convenience function for getting tutorial session"""
        mock_session = MagicMock()
        mock_get.return_value = mock_session
        
        session = get_tutorial_session('test_session')
        
        self.assertEqual(session, mock_session)
        mock_get.assert_called_once_with('test_session')
    
    @patch.object(tutorial_system, 'update_tutorial_progress')
    def test_update_tutorial_progress_function(self, mock_update):
        """Test convenience function for updating tutorial progress"""
        mock_update.return_value = True
        
        success = update_tutorial_progress('test_session', 'step1', 'completed')
        
        self.assertTrue(success)
        mock_update.assert_called_once_with('test_session', 'step1', 'completed', None)
    
    @patch.object(tutorial_system, 'complete_tutorial')
    def test_complete_tutorial_function(self, mock_complete):
        """Test convenience function for completing tutorial"""
        mock_complete.return_value = True
        
        success = complete_tutorial('test_session')
        
        self.assertTrue(success)
        mock_complete.assert_called_once_with('test_session')
    
    @patch.object(tutorial_system, 'skip_tutorial')
    def test_skip_tutorial_function(self, mock_skip):
        """Test convenience function for skipping tutorial"""
        mock_skip.return_value = True
        
        success = skip_tutorial('test_session', 'Too busy')
        
        self.assertTrue(success)
        mock_skip.assert_called_once_with('test_session', 'Too busy')
    
    @patch.object(tutorial_system, 'get_available_tutorials')
    def test_get_available_tutorials_function(self, mock_available):
        """Test convenience function for getting available tutorials"""
        mock_tutorials = [{'tutorial_id': 'welcome_tour', 'name': 'Welcome Tour'}]
        mock_available.return_value = mock_tutorials
        
        tutorials = get_available_tutorials(self.user_id)
        
        self.assertEqual(tutorials, mock_tutorials)
        mock_available.assert_called_once_with(self.user_id)
    
    @patch.object(tutorial_system, 'get_recommended_tutorials')
    def test_get_recommended_tutorials_function(self, mock_recommended):
        """Test convenience function for getting recommended tutorials"""
        mock_recommendations = [{'tutorial_id': 'welcome_tour', 'relevance_score': 85.0}]
        mock_recommended.return_value = mock_recommendations
        
        recommendations = get_recommended_tutorials(self.user_id, limit=3)
        
        self.assertEqual(recommendations, mock_recommendations)
        mock_recommended.assert_called_once_with(self.user_id, 3)
    
    @patch.object(tutorial_system, 'get_tutorial_analytics')
    def test_get_tutorial_analytics_function(self, mock_analytics):
        """Test convenience function for getting tutorial analytics"""
        mock_analytics_obj = MagicMock()
        mock_analytics.return_value = mock_analytics_obj
        
        analytics = get_tutorial_analytics('welcome_tour')
        
        self.assertEqual(analytics, mock_analytics_obj)
        mock_analytics.assert_called_once_with('welcome_tour')
    
    @patch.object(tutorial_system, 'get_tutorial_content')
    def test_get_tutorial_content_function(self, mock_content):
        """Test convenience function for getting tutorial content"""
        mock_content_data = {'tutorial_id': 'welcome_tour', 'name': 'Welcome Tour'}
        mock_content.return_value = mock_content_data
        
        content = get_tutorial_content('welcome_tour')
        
        self.assertEqual(content, mock_content_data)
        mock_content.assert_called_once_with('welcome_tour', None)
    
    @patch.object(tutorial_system, 'get_tutorial_content')
    def test_get_tutorial_content_function_with_step(self, mock_content):
        """Test convenience function for getting tutorial content with step"""
        mock_content_data = {'tutorial_id': 'welcome_tour', 'step': {'step_id': 'step1'}}
        mock_content.return_value = mock_content_data
        
        content = get_tutorial_content('welcome_tour', 'step1')
        
        self.assertEqual(content, mock_content_data)
        mock_content.assert_called_once_with('welcome_tour', 'step1')


class TestEnumsAndDataClasses(unittest.TestCase):
    """Test cases for enums and data classes"""
    
    def test_tutorial_type_enum(self):
        """Test TutorialType enum values"""
        self.assertEqual(TutorialType.OVERLAY.value, 'overlay')
        self.assertEqual(TutorialType.TOOLTIP.value, 'tooltip')
        self.assertEqual(TutorialType.MODAL.value, 'modal')
        self.assertEqual(TutorialType.SIDEBAR.value, 'sidebar')
        self.assertEqual(TutorialType.INLINE.value, 'inline')
        self.assertEqual(TutorialType.WALKTHROUGH.value, 'walkthrough')
        self.assertEqual(TutorialType.INTERACTIVE.value, 'interactive')
    
    def test_tutorial_trigger_enum(self):
        """Test TutorialTrigger enum values"""
        self.assertEqual(TutorialTrigger.AUTOMATIC.value, 'automatic')
        self.assertEqual(TutorialTrigger.MANUAL.value, 'manual')
        self.assertEqual(TutorialTrigger.ON_STEP_ENTER.value, 'on_step_enter')
        self.assertEqual(TutorialTrigger.ON_FEATURE_ACCESS.value, 'on_feature_access')
        self.assertEqual(TutorialTrigger.ON_ERROR.value, 'on_error')
        self.assertEqual(TutorialTrigger.ON_INACTIVITY.value, 'on_inactivity')
        self.assertEqual(TutorialTrigger.SCHEDULED.value, 'scheduled')
    
    def test_tutorial_status_enum(self):
        """Test TutorialStatus enum values"""
        self.assertEqual(TutorialStatus.NOT_STARTED.value, 'not_started')
        self.assertEqual(TutorialStatus.IN_PROGRESS.value, 'in_progress')
        self.assertEqual(TutorialStatus.COMPLETED.value, 'completed')
        self.assertEqual(TutorialStatus.SKIPPED.value, 'skipped')
        self.assertEqual(TutorialStatus.PAUSED.value, 'paused')
        self.assertEqual(TutorialStatus.FAILED.value, 'failed')
    
    def test_tutorial_step_dataclass(self):
        """Test TutorialStep dataclass"""
        step = TutorialStep(
            step_id='test_step',
            title='Test Step',
            content='Test step content',
            target_element='#test-element',
            position='top',
            action_required=True,
            action_text='Click Here',
            action_url='/test-url',
            hints=['Hint 1', 'Hint 2'],
            estimated_duration=45,
            interactive=True,
            skip_allowed=False
        )
        
        self.assertEqual(step.step_id, 'test_step')
        self.assertEqual(step.title, 'Test Step')
        self.assertEqual(step.content, 'Test step content')
        self.assertEqual(step.target_element, '#test-element')
        self.assertEqual(step.position, 'top')
        self.assertTrue(step.action_required)
        self.assertEqual(step.action_text, 'Click Here')
        self.assertEqual(step.action_url, '/test-url')
        self.assertEqual(step.hints, ['Hint 1', 'Hint 2'])
        self.assertEqual(step.estimated_duration, 45)
        self.assertTrue(step.interactive)
        self.assertFalse(step.skip_allowed)
    
    def test_tutorial_dataclass(self):
        """Test Tutorial dataclass"""
        tutorial = Tutorial(
            tutorial_id='test_tutorial',
            name='Test Tutorial',
            description='Test tutorial description',
            tutorial_type=TutorialType.WALKTHROUGH,
            trigger=TutorialTrigger.AUTOMATIC,
            target_step=OnboardingStep.WELCOME,
            target_feature='dashboard_basic',
            steps=[TutorialStep(step_id='step1', title='Step 1', content='Content 1')],
            prerequisites=['step:welcome'],
            estimated_duration=120,
            difficulty_level='intermediate',
            category='onboarding',
            tags=['beginner', 'essential'],
            version='1.0',
            active=True
        )
        
        self.assertEqual(tutorial.tutorial_id, 'test_tutorial')
        self.assertEqual(tutorial.name, 'Test Tutorial')
        self.assertEqual(tutorial.description, 'Test tutorial description')
        self.assertEqual(tutorial.tutorial_type, TutorialType.WALKTHROUGH)
        self.assertEqual(tutorial.trigger, TutorialTrigger.AUTOMATIC)
        self.assertEqual(tutorial.target_step, OnboardingStep.WELCOME)
        self.assertEqual(tutorial.target_feature, 'dashboard_basic')
        self.assertEqual(len(tutorial.steps), 1)
        self.assertEqual(tutorial.prerequisites, ['step:welcome'])
        self.assertEqual(tutorial.estimated_duration, 120)
        self.assertEqual(tutorial.difficulty_level, 'intermediate')
        self.assertEqual(tutorial.category, 'onboarding')
        self.assertEqual(tutorial.tags, ['beginner', 'essential'])
        self.assertEqual(tutorial.version, '1.0')
        self.assertTrue(tutorial.active)
    
    def test_tutorial_session_dataclass(self):
        """Test TutorialSession dataclass"""
        session = TutorialSession(
            session_id='test_session',
            user_id=1,
            tutorial_id='welcome_tour',
            current_step_index=2,
            completed_steps=['step1', 'step2'],
            skipped_steps=[],
            start_time=datetime.now(),
            last_activity=datetime.now(),
            status=TutorialStatus.IN_PROGRESS,
            progress_percentage=50.0,
            time_spent=60,
            interactions=[{'step_id': 'step1', 'action': 'completed'}],
            user_feedback={'rating': 5}
        )
        
        self.assertEqual(session.session_id, 'test_session')
        self.assertEqual(session.user_id, 1)
        self.assertEqual(session.tutorial_id, 'welcome_tour')
        self.assertEqual(session.current_step_index, 2)
        self.assertEqual(session.completed_steps, ['step1', 'step2'])
        self.assertEqual(session.skipped_steps, [])
        self.assertIsInstance(session.start_time, datetime)
        self.assertIsInstance(session.last_activity, datetime)
        self.assertEqual(session.status, TutorialStatus.IN_PROGRESS)
        self.assertEqual(session.progress_percentage, 50.0)
        self.assertEqual(session.time_spent, 60)
        self.assertEqual(len(session.interactions), 1)
        self.assertEqual(session.user_feedback, {'rating': 5})
    
    def test_tutorial_analytics_dataclass(self):
        """Test TutorialAnalytics dataclass"""
        analytics = TutorialAnalytics(
            tutorial_id='welcome_tour',
            total_sessions=100,
            completed_sessions=75,
            skipped_sessions=15,
            average_completion_time=120.0,
            average_progress_percentage=85.0,
            user_satisfaction_score=4.2,
            common_dropout_points=['step_2', 'step_4'],
            effectiveness_score=0.82
        )
        
        self.assertEqual(analytics.tutorial_id, 'welcome_tour')
        self.assertEqual(analytics.total_sessions, 100)
        self.assertEqual(analytics.completed_sessions, 75)
        self.assertEqual(analytics.skipped_sessions, 15)
        self.assertEqual(analytics.average_completion_time, 120.0)
        self.assertEqual(analytics.average_progress_percentage, 85.0)
        self.assertEqual(analytics.user_satisfaction_score, 4.2)
        self.assertEqual(analytics.common_dropout_points, ['step_2', 'step_4'])
        self.assertEqual(analytics.effectiveness_score, 0.82)
        self.assertIsInstance(analytics.last_updated, datetime)


class TestTutorialContent(unittest.TestCase):
    """Test cases for tutorial content and structure"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tutorial_system = OnboardingTutorialSystem()
    
    def test_welcome_tour_content(self):
        """Test welcome tour tutorial content"""
        tutorial = self.tutorial_system.tutorials['welcome_tour']
        
        self.assertEqual(tutorial.name, 'Welcome Tour')
        self.assertEqual(tutorial.description, 'Get started with your training journey')
        self.assertEqual(tutorial.tutorial_type, TutorialType.WALKTHROUGH)
        self.assertEqual(tutorial.trigger, TutorialTrigger.AUTOMATIC)
        self.assertEqual(tutorial.target_step, OnboardingStep.WELCOME)
        self.assertEqual(tutorial.difficulty_level, 'beginner')
        self.assertEqual(tutorial.category, 'onboarding')
        self.assertEqual(len(tutorial.steps), 3)
    
    def test_strava_connection_guide_content(self):
        """Test Strava connection guide tutorial content"""
        tutorial = self.tutorial_system.tutorials['strava_connection_guide']
        
        self.assertEqual(tutorial.name, 'Strava Connection Guide')
        self.assertEqual(tutorial.description, 'Step-by-step guide to connecting your Strava account')
        self.assertEqual(tutorial.tutorial_type, TutorialType.INTERACTIVE)
        self.assertEqual(tutorial.trigger, TutorialTrigger.ON_STEP_ENTER)
        self.assertEqual(tutorial.target_step, OnboardingStep.STRAVA_CONNECTED)
        self.assertEqual(tutorial.difficulty_level, 'beginner')
        self.assertEqual(tutorial.category, 'strava')
        self.assertEqual(len(tutorial.steps), 3)
    
    def test_dashboard_tutorial_content(self):
        """Test dashboard tutorial content"""
        tutorial = self.tutorial_system.tutorials['dashboard_tutorial']
        
        self.assertEqual(tutorial.name, 'Dashboard Tutorial')
        self.assertEqual(tutorial.description, 'Learn how to navigate and use your dashboard effectively')
        self.assertEqual(tutorial.tutorial_type, TutorialType.WALKTHROUGH)
        self.assertEqual(tutorial.trigger, TutorialTrigger.MANUAL)
        self.assertEqual(tutorial.target_step, OnboardingStep.DASHBOARD_INTRO)
        self.assertEqual(tutorial.difficulty_level, 'intermediate')
        self.assertEqual(tutorial.category, 'dashboard')
        self.assertEqual(len(tutorial.steps), 5)
    
    def test_tutorial_step_positions(self):
        """Test that tutorial steps have valid positions"""
        valid_positions = ['top', 'bottom', 'left', 'right', 'center']
        
        for tutorial_id, tutorial in self.tutorial_system.tutorials.items():
            for step in tutorial.steps:
                self.assertIn(step.position, valid_positions)
    
    def test_tutorial_step_durations(self):
        """Test that tutorial steps have reasonable durations"""
        for tutorial_id, tutorial in self.tutorial_system.tutorials.items():
            for step in tutorial.steps:
                self.assertGreater(step.estimated_duration, 0)
                self.assertLessEqual(step.estimated_duration, 300)  # Max 5 minutes per step
    
    def test_tutorial_total_durations(self):
        """Test that tutorial total durations are reasonable"""
        for tutorial_id, tutorial in self.tutorial_system.tutorials.items():
            self.assertGreater(tutorial.estimated_duration, 0)
            self.assertLessEqual(tutorial.estimated_duration, 600)  # Max 10 minutes per tutorial


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)


