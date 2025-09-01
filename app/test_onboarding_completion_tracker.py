"""
Test Suite for Onboarding Completion Tracker Module

This module tests the onboarding completion tracking functionality including:
- Completion tracking initialization and management
- Milestone achievement checking and awarding
- Completion status updates and analytics
- Completion prediction and risk assessment
- Completion report generation and export
- Database integration and data persistence
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json

from onboarding_completion_tracker import (
    OnboardingCompletionTracker,
    CompletionStatus,
    MilestoneType,
    AchievementLevel,
    CompletionMilestone,
    UserCompletion,
    CompletionAnalytics,
    CompletionPrediction,
    start_completion_tracking,
    get_user_completion,
    update_completion_status,
    check_milestone_achievement,
    get_completion_analytics,
    predict_completion,
    export_completion_report,
    completion_tracker
)
from onboarding_manager import OnboardingStep, FeatureTier


class TestOnboardingCompletionTracker(unittest.TestCase):
    """Test cases for OnboardingCompletionTracker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.completion_tracker = OnboardingCompletionTracker()
        self.user_id = 1
    
    def test_initialization(self):
        """Test completion tracker initialization"""
        self.assertIsNotNone(self.completion_tracker.onboarding_manager)
        self.assertIsNotNone(self.completion_tracker.progress_tracker)
        self.assertIsNotNone(self.completion_tracker.tutorial_system)
        self.assertIsNotNone(self.completion_tracker.tiered_feature_manager)
        self.assertIsNotNone(self.completion_tracker.feature_triggers)
        self.assertIsNotNone(self.completion_tracker.dashboard_manager)
        self.assertIsNotNone(self.completion_tracker.milestones)
        
        # Check that milestones are defined
        self.assertGreater(len(self.completion_tracker.milestones), 0)
        
        # Check milestone structure
        for milestone_id, milestone in self.completion_tracker.milestones.items():
            self.assertIsInstance(milestone, CompletionMilestone)
            self.assertEqual(milestone.milestone_id, milestone_id)
            self.assertIsInstance(milestone.name, str)
            self.assertIsInstance(milestone.description, str)
            self.assertIsInstance(milestone.milestone_type, MilestoneType)
            self.assertIsInstance(milestone.achievement_level, AchievementLevel)
            self.assertIsInstance(milestone.points, int)
    
    def test_milestones_structure(self):
        """Test that milestones have correct structure"""
        expected_milestone_types = [
            MilestoneType.STEP_COMPLETION,
            MilestoneType.FEATURE_UNLOCK,
            MilestoneType.TUTORIAL_COMPLETION,
            MilestoneType.ACTIVITY_SYNC,
            MilestoneType.GOAL_SETUP,
            MilestoneType.TIME_BASED,
            MilestoneType.ENGAGEMENT_BASED
        ]
        
        # Check that we have milestones for each type
        milestone_types = set()
        for milestone in self.completion_tracker.milestones.values():
            milestone_types.add(milestone.milestone_type)
        
        for expected_type in expected_milestone_types:
            self.assertIn(expected_type, milestone_types)
    
    def test_start_completion_tracking_new_user(self):
        """Test starting completion tracking for a new user"""
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=None):
            with patch.object(self.completion_tracker, '_save_user_completion'):
                result = self.completion_tracker.start_completion_tracking(self.user_id)
                
                self.assertTrue(result)
    
    def test_start_completion_tracking_existing_user(self):
        """Test starting completion tracking for existing user"""
        existing_completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=existing_completion):
            result = self.completion_tracker.start_completion_tracking(self.user_id)
            
            self.assertTrue(result)
    
    def test_get_user_completion(self):
        """Test getting user completion data"""
        with patch.object(self.completion_tracker, '_load_user_completion') as mock_load:
            mock_completion = UserCompletion(
                user_id=self.user_id,
                completion_status=CompletionStatus.IN_PROGRESS,
                started_at=datetime.now()
            )
            mock_load.return_value = mock_completion
            
            completion = self.completion_tracker.get_user_completion(self.user_id)
            
            self.assertEqual(completion, mock_completion)
            mock_load.assert_called_once_with(self.user_id)
    
    def test_update_completion_status(self):
        """Test updating completion status"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=completion):
            with patch.object(self.completion_tracker, '_update_completion_metrics'):
                with patch.object(self.completion_tracker, '_save_user_completion'):
                    result = self.completion_tracker.update_completion_status(
                        self.user_id, 
                        CompletionStatus.COMPLETED,
                        "User completed onboarding"
                    )
                    
                    self.assertTrue(result)
                    self.assertEqual(completion.completion_status, CompletionStatus.COMPLETED)
                    self.assertIsNotNone(completion.completed_at)
                    self.assertEqual(completion.completion_notes, "User completed onboarding")
    
    def test_check_milestone_achievement_no_completion(self):
        """Test milestone achievement checking when no completion tracking exists"""
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=None):
            newly_achieved = self.completion_tracker.check_milestone_achievement(self.user_id)
            
            self.assertEqual(newly_achieved, [])
    
    def test_check_milestone_achievement_no_progress(self):
        """Test milestone achievement checking when no progress exists"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=completion):
            with patch.object(self.completion_tracker, 'progress_tracker') as mock_progress_tracker:
                mock_progress_tracker.get_progress.return_value = None
                
                newly_achieved = self.completion_tracker.check_milestone_achievement(self.user_id)
                
                self.assertEqual(newly_achieved, [])
    
    @patch.object(OnboardingCompletionTracker, 'progress_tracker')
    def test_check_milestone_achievement_success(self, mock_progress_tracker):
        """Test successful milestone achievement checking"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        mock_progress = MagicMock()
        mock_progress.completed_steps = [OnboardingStep.WELCOME]
        mock_progress.unlocked_features = ['activity_viewer']
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=completion):
            with patch.object(self.completion_tracker, '_check_milestone_conditions', return_value=True):
                with patch.object(self.completion_tracker, '_update_completion_metrics'):
                    with patch.object(self.completion_tracker, '_save_user_completion'):
                        with patch.object(self.completion_tracker, 'progress_tracker') as mock_progress_tracker2:
                            newly_achieved = self.completion_tracker.check_milestone_achievement(self.user_id)
                            
                            self.assertIsInstance(newly_achieved, list)
                            self.assertGreater(len(newly_achieved), 0)
    
    def test_check_milestone_conditions_step_completion(self):
        """Test milestone condition checking for step completion"""
        milestone = CompletionMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone',
            milestone_type=MilestoneType.STEP_COMPLETION,
            step_requirement=OnboardingStep.WELCOME
        )
        
        mock_progress = MagicMock()
        mock_progress.completed_steps = [OnboardingStep.WELCOME]
        
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        result = self.completion_tracker._check_milestone_conditions(
            self.user_id, milestone, mock_progress, completion
        )
        
        self.assertTrue(result)
    
    def test_check_milestone_conditions_feature_unlock(self):
        """Test milestone condition checking for feature unlock"""
        milestone = CompletionMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone',
            milestone_type=MilestoneType.FEATURE_UNLOCK,
            feature_requirement='activity_viewer'
        )
        
        mock_progress = MagicMock()
        mock_progress.unlocked_features = ['activity_viewer']
        
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        result = self.completion_tracker._check_milestone_conditions(
            self.user_id, milestone, mock_progress, completion
        )
        
        self.assertTrue(result)
    
    def test_check_milestone_conditions_activity_sync(self):
        """Test milestone condition checking for activity sync"""
        milestone = CompletionMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone',
            milestone_type=MilestoneType.ACTIVITY_SYNC,
            activity_count_requirement=5
        )
        
        mock_progress = MagicMock()
        
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        with patch.object(self.completion_tracker, 'tiered_feature_manager') as mock_tiered_manager:
            mock_tiered_manager._get_user_activity_count.return_value = 10
            
            result = self.completion_tracker._check_milestone_conditions(
                self.user_id, milestone, mock_progress, completion
            )
            
            self.assertTrue(result)
    
    def test_check_milestone_conditions_time_based(self):
        """Test milestone condition checking for time-based milestones"""
        milestone = CompletionMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone',
            milestone_type=MilestoneType.TIME_BASED,
            time_requirement=7
        )
        
        mock_progress = MagicMock()
        
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now() - timedelta(days=10)
        )
        
        result = self.completion_tracker._check_milestone_conditions(
            self.user_id, milestone, mock_progress, completion
        )
        
        self.assertTrue(result)
    
    def test_update_completion_metrics(self):
        """Test updating completion metrics"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 75.0
        mock_progress.current_tier = FeatureTier.INTERMEDIATE
        
        with patch.object(self.completion_tracker, 'progress_tracker') as mock_progress_tracker:
            mock_progress_tracker.get_progress.return_value = mock_progress
            
            self.completion_tracker._update_completion_metrics(completion)
            
            self.assertEqual(completion.completion_percentage, 75.0)
            self.assertEqual(completion.current_tier, FeatureTier.INTERMEDIATE)
            self.assertIsNotNone(completion.last_activity)
    
    def test_get_completion_analytics(self):
        """Test getting completion analytics"""
        analytics = self.completion_tracker.get_completion_analytics()
        
        self.assertIsInstance(analytics, CompletionAnalytics)
        self.assertGreater(analytics.total_users, 0)
        self.assertGreater(analytics.completion_rate, 0)
        self.assertGreater(len(analytics.milestone_completion_rates), 0)
        self.assertGreater(len(analytics.achievement_distribution), 0)
        self.assertGreater(len(analytics.tier_distribution), 0)
        self.assertGreater(len(analytics.completion_trends), 0)
        self.assertGreater(len(analytics.dropout_points), 0)
        self.assertGreater(len(analytics.optimization_recommendations), 0)
    
    def test_predict_completion_no_completion(self):
        """Test completion prediction when no completion tracking exists"""
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=None):
            prediction = self.completion_tracker.predict_completion(self.user_id)
            
            self.assertIsNone(prediction)
    
    def test_predict_completion_no_progress(self):
        """Test completion prediction when no progress exists"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=completion):
            with patch.object(self.completion_tracker, 'progress_tracker') as mock_progress_tracker:
                mock_progress_tracker.get_progress.return_value = None
                
                prediction = self.completion_tracker.predict_completion(self.user_id)
                
                self.assertIsNone(prediction)
    
    @patch.object(OnboardingCompletionTracker, 'progress_tracker')
    def test_predict_completion_success(self, mock_progress_tracker):
        """Test successful completion prediction"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now() - timedelta(hours=1)
        )
        
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 50.0
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=completion):
            with patch.object(self.completion_tracker, '_calculate_completion_probability', return_value=0.8):
                with patch.object(self.completion_tracker, '_identify_risk_factors', return_value=[]):
                    with patch.object(self.completion_tracker, '_generate_completion_recommendations', return_value=[]):
                        prediction = self.completion_tracker.predict_completion(self.user_id)
                        
                        self.assertIsNotNone(prediction)
                        self.assertEqual(prediction.user_id, self.user_id)
                        self.assertGreater(prediction.predicted_completion_percentage, 0)
                        self.assertGreater(prediction.predicted_completion_time_minutes, 0)
                        self.assertGreater(prediction.confidence_score, 0)
                        self.assertEqual(prediction.completion_probability, 0.8)
    
    def test_calculate_completion_probability(self):
        """Test completion probability calculation"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now() - timedelta(hours=2)
        )
        
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 75.0
        mock_progress.current_tier = FeatureTier.INTERMEDIATE
        
        probability = self.completion_tracker._calculate_completion_probability(
            self.user_id, mock_progress, completion
        )
        
        self.assertGreater(probability, 0)
        self.assertLessEqual(probability, 1.0)
    
    def test_identify_risk_factors(self):
        """Test risk factor identification"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now() - timedelta(days=10),
            last_activity=datetime.now() - timedelta(days=3)
        )
        
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 10.0
        mock_progress.completed_steps = []
        
        risk_factors = self.completion_tracker._identify_risk_factors(
            self.user_id, mock_progress, completion
        )
        
        self.assertIsInstance(risk_factors, list)
    
    def test_generate_completion_recommendations(self):
        """Test completion recommendation generation"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        mock_progress = MagicMock()
        mock_progress.completed_steps = []
        
        recommendations = self.completion_tracker._generate_completion_recommendations(
            self.user_id, mock_progress, completion
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_export_completion_report_no_completion(self):
        """Test completion report export when no completion tracking exists"""
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=None):
            report = self.completion_tracker.export_completion_report(self.user_id)
            
            self.assertEqual(report, {})
    
    @patch.object(OnboardingCompletionTracker, 'progress_tracker')
    def test_export_completion_report_success(self, mock_progress_tracker):
        """Test successful completion report export"""
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.COMPLETED,
            started_at=datetime.now() - timedelta(hours=2),
            completed_at=datetime.now(),
            total_time_minutes=120,
            completion_percentage=100.0,
            completion_score=95.0,
            current_tier=FeatureTier.ADVANCED,
            points_earned=500,
            milestones_achieved=['welcome_completed', 'strava_connected'],
            achievements_earned=['welcome_completed_achievement']
        )
        
        mock_progress = MagicMock()
        mock_progress.current_step = OnboardingStep.COMPLETED
        mock_progress.completed_steps = [OnboardingStep.WELCOME, OnboardingStep.STRAVA_CONNECTED]
        mock_progress.unlocked_features = ['activity_viewer']
        mock_progress.progress_percentage = 100.0
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        with patch.object(self.completion_tracker, 'get_user_completion', return_value=completion):
            with patch.object(self.completion_tracker, 'predict_completion', return_value=None):
                report = self.completion_tracker.export_completion_report(self.user_id)
                
                self.assertIsInstance(report, dict)
                self.assertIn('user_id', report)
                self.assertIn('completion_status', report)
                self.assertIn('started_at', report)
                self.assertIn('completed_at', report)
                self.assertIn('total_time_minutes', report)
                self.assertIn('completion_percentage', report)
                self.assertIn('completion_score', report)
                self.assertIn('current_tier', report)
                self.assertIn('points_earned', report)
                self.assertIn('milestones_achieved', report)
                self.assertIn('achievements_earned', report)
                self.assertIn('progress_data', report)
                self.assertIn('prediction', report)
                self.assertIn('exported_at', report)
    
    @patch('onboarding_completion_tracker.USE_POSTGRES', True)
    @patch('onboarding_completion_tracker.get_db_connection')
    def test_postgresql_save_user_completion(self, mock_db):
        """Test PostgreSQL save user completion query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        self.completion_tracker._save_user_completion(completion)
        
        # Verify PostgreSQL query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("INSERT INTO user_settings", call_args[0][0])
        self.assertIn("completion_data", call_args[0][0])
    
    @patch('onboarding_completion_tracker.USE_POSTGRES', False)
    @patch('onboarding_completion_tracker.get_db_connection')
    def test_sqlite_save_user_completion(self, mock_db):
        """Test SQLite save user completion query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        self.completion_tracker._save_user_completion(completion)
        
        # Verify SQLite query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("INSERT OR REPLACE INTO user_settings", call_args[0][0])
        self.assertIn("completion_data", call_args[0][0])


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch.object(completion_tracker, 'start_completion_tracking')
    def test_start_completion_tracking_function(self, mock_start):
        """Test convenience function for starting completion tracking"""
        mock_start.return_value = True
        
        result = start_completion_tracking(self.user_id)
        
        self.assertTrue(result)
        mock_start.assert_called_once_with(self.user_id)
    
    @patch.object(completion_tracker, 'get_user_completion')
    def test_get_user_completion_function(self, mock_get):
        """Test convenience function for getting user completion"""
        mock_completion = UserCompletion(
            user_id=self.user_id,
            completion_status=CompletionStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        mock_get.return_value = mock_completion
        
        completion = get_user_completion(self.user_id)
        
        self.assertEqual(completion, mock_completion)
        mock_get.assert_called_once_with(self.user_id)
    
    @patch.object(completion_tracker, 'update_completion_status')
    def test_update_completion_status_function(self, mock_update):
        """Test convenience function for updating completion status"""
        mock_update.return_value = True
        
        result = update_completion_status(self.user_id, CompletionStatus.COMPLETED, "Completed")
        
        self.assertTrue(result)
        mock_update.assert_called_once_with(self.user_id, CompletionStatus.COMPLETED, "Completed")
    
    @patch.object(completion_tracker, 'check_milestone_achievement')
    def test_check_milestone_achievement_function(self, mock_check):
        """Test convenience function for checking milestone achievement"""
        mock_check.return_value = ['welcome_completed', 'strava_connected']
        
        newly_achieved = check_milestone_achievement(self.user_id)
        
        self.assertEqual(newly_achieved, ['welcome_completed', 'strava_connected'])
        mock_check.assert_called_once_with(self.user_id)
    
    @patch.object(completion_tracker, 'get_completion_analytics')
    def test_get_completion_analytics_function(self, mock_analytics):
        """Test convenience function for getting completion analytics"""
        mock_analytics_obj = CompletionAnalytics()
        mock_analytics.return_value = mock_analytics_obj
        
        analytics = get_completion_analytics()
        
        self.assertEqual(analytics, mock_analytics_obj)
        mock_analytics.assert_called_once_with(None)
    
    @patch.object(completion_tracker, 'predict_completion')
    def test_predict_completion_function(self, mock_predict):
        """Test convenience function for predicting completion"""
        mock_prediction = CompletionPrediction(
            user_id=self.user_id,
            predicted_completion_percentage=85.0,
            predicted_completion_time_minutes=30,
            confidence_score=0.9,
            completion_probability=0.85
        )
        mock_predict.return_value = mock_prediction
        
        prediction = predict_completion(self.user_id)
        
        self.assertEqual(prediction, mock_prediction)
        mock_predict.assert_called_once_with(self.user_id)
    
    @patch.object(completion_tracker, 'export_completion_report')
    def test_export_completion_report_function(self, mock_export):
        """Test convenience function for exporting completion report"""
        mock_report = {'user_id': self.user_id, 'completion_status': 'completed'}
        mock_export.return_value = mock_report
        
        report = export_completion_report(self.user_id)
        
        self.assertEqual(report, mock_report)
        mock_export.assert_called_once_with(self.user_id)


class TestEnumsAndDataClasses(unittest.TestCase):
    """Test cases for enums and data classes"""
    
    def test_completion_status_enum(self):
        """Test CompletionStatus enum values"""
        self.assertEqual(CompletionStatus.NOT_STARTED.value, 'not_started')
        self.assertEqual(CompletionStatus.IN_PROGRESS.value, 'in_progress')
        self.assertEqual(CompletionStatus.COMPLETED.value, 'completed')
        self.assertEqual(CompletionStatus.ABANDONED.value, 'abandoned')
        self.assertEqual(CompletionStatus.EXPIRED.value, 'expired')
        self.assertEqual(CompletionStatus.FAILED.value, 'failed')
    
    def test_milestone_type_enum(self):
        """Test MilestoneType enum values"""
        self.assertEqual(MilestoneType.STEP_COMPLETION.value, 'step_completion')
        self.assertEqual(MilestoneType.FEATURE_UNLOCK.value, 'feature_unlock')
        self.assertEqual(MilestoneType.TUTORIAL_COMPLETION.value, 'tutorial_completion')
        self.assertEqual(MilestoneType.ACTIVITY_SYNC.value, 'activity_sync')
        self.assertEqual(MilestoneType.GOAL_SETUP.value, 'goal_setup')
        self.assertEqual(MilestoneType.TIME_BASED.value, 'time_based')
        self.assertEqual(MilestoneType.ENGAGEMENT_BASED.value, 'engagement_based')
        self.assertEqual(MilestoneType.PERFORMANCE_BASED.value, 'performance_based')
    
    def test_achievement_level_enum(self):
        """Test AchievementLevel enum values"""
        self.assertEqual(AchievementLevel.BRONZE.value, 'bronze')
        self.assertEqual(AchievementLevel.SILVER.value, 'silver')
        self.assertEqual(AchievementLevel.GOLD.value, 'gold')
        self.assertEqual(AchievementLevel.PLATINUM.value, 'platinum')
        self.assertEqual(AchievementLevel.DIAMOND.value, 'diamond')
    
    def test_completion_milestone_dataclass(self):
        """Test CompletionMilestone dataclass"""
        milestone = CompletionMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone description',
            milestone_type=MilestoneType.STEP_COMPLETION,
            step_requirement=OnboardingStep.WELCOME,
            achievement_level=AchievementLevel.BRONZE,
            points=25,
            badge_icon='test_badge',
            certificate_template='test_certificate'
        )
        
        self.assertEqual(milestone.milestone_id, 'test_milestone')
        self.assertEqual(milestone.name, 'Test Milestone')
        self.assertEqual(milestone.description, 'Test milestone description')
        self.assertEqual(milestone.milestone_type, MilestoneType.STEP_COMPLETION)
        self.assertEqual(milestone.step_requirement, OnboardingStep.WELCOME)
        self.assertEqual(milestone.achievement_level, AchievementLevel.BRONZE)
        self.assertEqual(milestone.points, 25)
        self.assertEqual(milestone.badge_icon, 'test_badge')
        self.assertEqual(milestone.certificate_template, 'test_certificate')
        self.assertIsInstance(milestone.created_at, datetime)
    
    def test_user_completion_dataclass(self):
        """Test UserCompletion dataclass"""
        completion = UserCompletion(
            user_id=1,
            completion_status=CompletionStatus.COMPLETED,
            started_at=datetime.now() - timedelta(hours=2),
            completed_at=datetime.now(),
            total_time_minutes=120,
            completion_percentage=100.0,
            milestones_achieved=['welcome_completed'],
            achievements_earned=['welcome_completed_achievement'],
            points_earned=100,
            current_tier=FeatureTier.ADVANCED,
            completion_score=95.0,
            last_activity=datetime.now(),
            completion_notes='User completed successfully'
        )
        
        self.assertEqual(completion.user_id, 1)
        self.assertEqual(completion.completion_status, CompletionStatus.COMPLETED)
        self.assertIsInstance(completion.started_at, datetime)
        self.assertIsInstance(completion.completed_at, datetime)
        self.assertEqual(completion.total_time_minutes, 120)
        self.assertEqual(completion.completion_percentage, 100.0)
        self.assertEqual(completion.milestones_achieved, ['welcome_completed'])
        self.assertEqual(completion.achievements_earned, ['welcome_completed_achievement'])
        self.assertEqual(completion.points_earned, 100)
        self.assertEqual(completion.current_tier, FeatureTier.ADVANCED)
        self.assertEqual(completion.completion_score, 95.0)
        self.assertIsInstance(completion.last_activity, datetime)
        self.assertEqual(completion.completion_notes, 'User completed successfully')
        self.assertIsInstance(completion.created_at, datetime)
        self.assertIsInstance(completion.updated_at, datetime)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)


