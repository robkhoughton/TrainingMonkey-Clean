"""
Test Suite for Onboarding Progress Tracker Module

This module tests the comprehensive onboarding progress tracking functionality including:
- Progress tracking initialization and management
- Milestone completion tracking
- Progress analytics and insights
- Progress comparison and benchmarking
- Progress visualization data generation
- Event logging and status tracking
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json

from onboarding_progress_tracker import (
    OnboardingProgressTracker,
    ProgressEventType,
    ProgressStatus,
    ProgressMilestone,
    ProgressEvent,
    OnboardingProgress,
    start_progress_tracking,
    get_progress,
    update_progress,
    get_progress_analytics,
    get_progress_comparison,
    get_progress_visualization_data,
    progress_tracker
)
from onboarding_manager import OnboardingStep, FeatureTier


class TestOnboardingProgressTracker(unittest.TestCase):
    """Test cases for OnboardingProgressTracker class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tracker = OnboardingProgressTracker()
        self.user_id = 1
    
    def test_initialization(self):
        """Test tracker initialization"""
        self.assertIsNotNone(self.tracker.onboarding_manager)
        self.assertIsNotNone(self.tracker.tiered_feature_manager)
        self.assertIsNotNone(self.tracker.milestones)
        self.assertIsNotNone(self.tracker.progress_cache)
        
        # Check that milestones are defined
        self.assertGreater(len(self.tracker.milestones), 0)
        
        # Check milestone structure
        for milestone_id, milestone in self.tracker.milestones.items():
            self.assertIsInstance(milestone, ProgressMilestone)
            self.assertEqual(milestone.milestone_id, milestone_id)
            self.assertIsInstance(milestone.name, str)
            self.assertIsInstance(milestone.description, str)
            self.assertIsInstance(milestone.required_steps, list)
            self.assertIsInstance(milestone.required_features, list)
            self.assertIsInstance(milestone.required_activities, int)
            self.assertIsInstance(milestone.required_days, int)
            self.assertIsInstance(milestone.reward_description, str)
    
    def test_milestones_structure(self):
        """Test that milestones have correct structure"""
        expected_milestones = [
            'welcome_complete', 'strava_connected', 'first_activity', 
            'data_sync_complete', 'dashboard_mastered', 'features_explored',
            'goals_configured', 'first_recommendation', 'journal_setup', 
            'onboarding_complete'
        ]
        
        for milestone_id in expected_milestones:
            self.assertIn(milestone_id, self.tracker.milestones)
    
    @patch.object(OnboardingProgressTracker, 'onboarding_manager')
    def test_start_progress_tracking_success(self, mock_onboarding_manager):
        """Test successful progress tracking start"""
        # Mock onboarding manager responses
        mock_onboarding_manager.start_onboarding.return_value = True
        
        # Mock database save
        with patch.object(self.tracker, '_save_progress'):
            with patch.object(self.tracker, '_log_progress_event'):
                success = self.tracker.start_progress_tracking(self.user_id)
                
                self.assertTrue(success)
                mock_onboarding_manager.start_onboarding.assert_called_once_with(self.user_id)
    
    @patch.object(OnboardingProgressTracker, 'onboarding_manager')
    def test_start_progress_tracking_failure(self, mock_onboarding_manager):
        """Test failed progress tracking start"""
        # Mock onboarding manager failure
        mock_onboarding_manager.start_onboarding.return_value = False
        
        success = self.tracker.start_progress_tracking(self.user_id)
        
        self.assertFalse(success)
        mock_onboarding_manager.start_onboarding.assert_called_once_with(self.user_id)
    
    @patch.object(OnboardingProgressTracker, '_load_progress')
    @patch.object(OnboardingProgressTracker, '_update_progress_data')
    def test_get_progress_success(self, mock_update_data, mock_load):
        """Test successful progress retrieval"""
        # Mock progress data
        mock_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=0.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        mock_load.return_value = mock_progress
        mock_update_data.return_value = mock_progress
        
        progress = self.tracker.get_progress(self.user_id)
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress.user_id, self.user_id)
        self.assertEqual(progress.current_step, OnboardingStep.WELCOME)
        mock_load.assert_called_once_with(self.user_id)
        mock_update_data.assert_called_once_with(mock_progress)
    
    @patch.object(OnboardingProgressTracker, '_load_progress')
    def test_get_progress_not_found(self, mock_load):
        """Test progress retrieval when not found"""
        mock_load.return_value = None
        
        progress = self.tracker.get_progress(self.user_id)
        
        self.assertIsNone(progress)
        mock_load.assert_called_once_with(self.user_id)
    
    @patch.object(OnboardingProgressTracker, 'get_progress')
    @patch.object(OnboardingProgressTracker, 'onboarding_manager')
    @patch.object(OnboardingProgressTracker, 'tiered_feature_manager')
    def test_update_progress_step_completion(self, mock_tiered_manager, mock_onboarding_manager, mock_get_progress):
        """Test updating progress with step completion"""
        # Mock progress data
        mock_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=0.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        mock_get_progress.return_value = mock_progress
        
        # Mock database operations
        with patch.object(self.tracker, '_save_progress'):
            with patch.object(self.tracker, '_log_progress_event'):
                with patch.object(self.tracker, '_update_progress_data', return_value=mock_progress):
                    with patch.object(self.tracker, '_check_milestones'):
                        success = self.tracker.update_progress(
                            self.user_id, 
                            step=OnboardingStep.WELCOME
                        )
                        
                        self.assertTrue(success)
                        mock_onboarding_manager.complete_onboarding_step.assert_called_once_with(
                            self.user_id, OnboardingStep.WELCOME
                        )
    
    @patch.object(OnboardingProgressTracker, 'get_progress')
    @patch.object(OnboardingProgressTracker, 'tiered_feature_manager')
    def test_update_progress_feature_unlock(self, mock_tiered_manager, mock_get_progress):
        """Test updating progress with feature unlock"""
        # Mock progress data
        mock_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        mock_get_progress.return_value = mock_progress
        
        # Mock tiered feature manager
        mock_tiered_manager.unlock_tiered_feature.return_value = (True, {'success': True})
        
        # Mock database operations
        with patch.object(self.tracker, '_save_progress'):
            with patch.object(self.tracker, '_log_progress_event'):
                with patch.object(self.tracker, '_update_progress_data', return_value=mock_progress):
                    with patch.object(self.tracker, '_check_milestones'):
                        success = self.tracker.update_progress(
                            self.user_id, 
                            feature='dashboard_basic'
                        )
                        
                        self.assertTrue(success)
                        mock_tiered_manager.unlock_tiered_feature.assert_called_once_with(
                            self.user_id, 'dashboard_basic'
                        )
    
    @patch.object(OnboardingProgressTracker, 'get_progress')
    def test_update_progress_custom_event(self, mock_get_progress):
        """Test updating progress with custom event"""
        # Mock progress data
        mock_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=0.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        mock_get_progress.return_value = mock_progress
        
        # Mock database operations
        with patch.object(self.tracker, '_save_progress'):
            with patch.object(self.tracker, '_log_progress_event'):
                with patch.object(self.tracker, '_update_progress_data', return_value=mock_progress):
                    with patch.object(self.tracker, '_check_milestones'):
                        success = self.tracker.update_progress(
                            self.user_id,
                            event_type=ProgressEventType.ACTIVITY_ADDED,
                            event_data={'activity_count': 1}
                        )
                        
                        self.assertTrue(success)
    
    @patch.object(OnboardingProgressTracker, 'get_progress')
    def test_get_progress_analytics(self, mock_get_progress):
        """Test getting progress analytics"""
        # Mock progress data
        mock_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=['dashboard_basic'],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now() - timedelta(days=5),
            last_activity=datetime.now() - timedelta(days=1)
        )
        
        mock_get_progress.return_value = mock_progress
        
        analytics = self.tracker.get_progress_analytics(self.user_id)
        
        self.assertIsInstance(analytics, dict)
        self.assertIn('user_id', analytics)
        self.assertIn('overall_progress', analytics)
        self.assertIn('current_tier', analytics)
        self.assertIn('steps_completed', analytics)
        self.assertIn('features_unlocked', analytics)
        self.assertIn('milestones_completed', analytics)
        self.assertIn('time_in_onboarding', analytics)
        self.assertIn('last_activity_days_ago', analytics)
        self.assertIn('status', analytics)
        self.assertIn('progress_trend', analytics)
        self.assertIn('engagement_score', analytics)
        self.assertIn('completion_estimate', analytics)
        self.assertIn('recommendations', analytics)
    
    @patch.object(OnboardingProgressTracker, 'get_progress_analytics')
    def test_get_progress_comparison(self, mock_analytics):
        """Test getting progress comparison"""
        # Mock analytics data
        mock_analytics.return_value = {
            'user_id': self.user_id,
            'overall_progress': 65.0,
            'steps_completed': 6,
            'features_unlocked': 4
        }
        
        comparison = self.tracker.get_progress_comparison(self.user_id)
        
        self.assertIsInstance(comparison, dict)
        self.assertIn('user_id', comparison)
        self.assertIn('user_progress', comparison)
        self.assertIn('benchmarks', comparison)
        self.assertIn('percentile_rank', comparison)
        self.assertIn('performance_rating', comparison)
        self.assertIn('improvement_areas', comparison)
    
    @patch.object(OnboardingProgressTracker, 'get_progress')
    @patch.object(OnboardingProgressTracker, 'tiered_feature_manager')
    def test_get_progress_visualization_data(self, mock_tiered_manager, mock_get_progress):
        """Test getting progress visualization data"""
        # Mock progress data
        mock_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=['dashboard_basic'],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            recent_events=[
                ProgressEvent(
                    event_id='test_event',
                    user_id=self.user_id,
                    event_type=ProgressEventType.STEP_COMPLETED,
                    event_data={'step': 'welcome'},
                    timestamp=datetime.now()
                )
            ]
        )
        
        mock_get_progress.return_value = mock_progress
        
        # Mock tiered feature manager
        mock_tiered_manager.feature_definitions = {
            'dashboard_basic': MagicMock(tier=FeatureTier.BASIC)
        }
        mock_tiered_manager.check_tiered_feature_unlock.return_value = (True, {'unlock_score': 1.0})
        
        visualization_data = self.tracker.get_progress_visualization_data(self.user_id)
        
        self.assertIsInstance(visualization_data, dict)
        self.assertIn('user_id', visualization_data)
        self.assertIn('timeline', visualization_data)
        self.assertIn('milestone_progress', visualization_data)
        self.assertIn('step_progress', visualization_data)
        self.assertIn('feature_progress', visualization_data)
        self.assertIn('overall_progress', visualization_data)
        self.assertIn('current_tier', visualization_data)
        self.assertIn('status', visualization_data)
    
    @patch.object(OnboardingProgressTracker, 'onboarding_manager')
    def test_check_milestone_completion_success(self, mock_onboarding_manager):
        """Test successful milestone completion check"""
        # Mock milestone
        milestone = ProgressMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone description',
            required_steps=[OnboardingStep.WELCOME],
            required_features=[],
            required_activities=1,
            required_days=1,
            reward_description='Test reward'
        )
        
        # Mock onboarding manager responses
        mock_progress = MagicMock()
        mock_progress.completed_steps = [OnboardingStep.WELCOME]
        mock_onboarding_manager.get_onboarding_progress.return_value = mock_progress
        mock_onboarding_manager.check_feature_unlock.return_value = True
        
        # Mock tiered feature manager methods
        with patch.object(self.tracker.tiered_feature_manager, '_get_user_activity_count', return_value=2):
            with patch.object(self.tracker.tiered_feature_manager, '_get_user_days_active', return_value=3):
                completed = self.tracker._check_milestone_completion(self.user_id, milestone)
                
                self.assertTrue(completed)
    
    @patch.object(OnboardingProgressTracker, 'onboarding_manager')
    def test_check_milestone_completion_failure(self, mock_onboarding_manager):
        """Test failed milestone completion check"""
        # Mock milestone
        milestone = ProgressMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone description',
            required_steps=[OnboardingStep.WELCOME],
            required_features=[],
            required_activities=5,
            required_days=5,
            reward_description='Test reward'
        )
        
        # Mock onboarding manager responses
        mock_progress = MagicMock()
        mock_progress.completed_steps = [OnboardingStep.WELCOME]
        mock_onboarding_manager.get_onboarding_progress.return_value = mock_progress
        
        # Mock tiered feature manager methods
        with patch.object(self.tracker.tiered_feature_manager, '_get_user_activity_count', return_value=1):
            with patch.object(self.tracker.tiered_feature_manager, '_get_user_days_active', return_value=1):
                completed = self.tracker._check_milestone_completion(self.user_id, milestone)
                
                self.assertFalse(completed)
    
    def test_calculate_milestone_progress(self):
        """Test milestone progress calculation"""
        # Mock milestone
        milestone = ProgressMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone description',
            required_steps=[OnboardingStep.WELCOME],
            required_features=['dashboard_basic'],
            required_activities=1,
            required_days=1,
            reward_description='Test reward'
        )
        
        # Mock onboarding manager
        with patch.object(self.tracker.onboarding_manager, 'get_onboarding_progress') as mock_progress:
            mock_progress_obj = MagicMock()
            mock_progress_obj.completed_steps = [OnboardingStep.WELCOME]
            mock_progress.return_value = mock_progress_obj
            
            # Mock feature unlock check
            with patch.object(self.tracker.onboarding_manager, 'check_feature_unlock', return_value=True):
                # Mock activity and days counts
                with patch.object(self.tracker.tiered_feature_manager, '_get_user_activity_count', return_value=2):
                    with patch.object(self.tracker.tiered_feature_manager, '_get_user_days_active', return_value=2):
                        progress_percentage = self.tracker._calculate_milestone_progress(self.user_id, milestone)
                        
                        # Should be 100% (all requirements met)
                        self.assertEqual(progress_percentage, 100.0)
    
    def test_determine_progress_status(self):
        """Test progress status determination"""
        # Test completed status
        completed_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.COMPLETED,
            completed_steps=[OnboardingStep.COMPLETED],
            unlocked_features=[],
            current_tier=FeatureTier.EXPERT,
            progress_percentage=100.0,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            completed_at=datetime.now()
        )
        
        status = self.tracker._determine_progress_status(completed_progress)
        self.assertEqual(status, ProgressStatus.COMPLETED)
        
        # Test stalled status
        stalled_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now(),
            last_activity=datetime.now() - timedelta(days=10)
        )
        
        status = self.tracker._determine_progress_status(stalled_progress)
        self.assertEqual(status, ProgressStatus.STALLED)
        
        # Test in progress status
        in_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        status = self.tracker._determine_progress_status(in_progress)
        self.assertEqual(status, ProgressStatus.IN_PROGRESS)
    
    def test_calculate_progress_trend(self):
        """Test progress trend calculation"""
        # Test excellent trend
        excellent_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=85.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        trend = self.tracker._calculate_progress_trend(excellent_progress)
        self.assertEqual(trend, 'excellent')
        
        # Test good trend
        good_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=70.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        trend = self.tracker._calculate_progress_trend(good_progress)
        self.assertEqual(trend, 'good')
    
    def test_calculate_engagement_score(self):
        """Test engagement score calculation"""
        # Test high engagement
        high_engagement = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now() - timedelta(days=1),
            last_activity=datetime.now(),
            recent_events=[MagicMock() for _ in range(5)]
        )
        
        score = self.tracker._calculate_engagement_score(high_engagement)
        self.assertGreater(score, 0)
        
        # Test zero engagement
        zero_engagement = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=0.0,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            recent_events=[]
        )
        
        score = self.tracker._calculate_engagement_score(zero_engagement)
        self.assertEqual(score, 100.0)  # Should be 100% for same-day start
    
    def test_estimate_completion_time(self):
        """Test completion time estimation"""
        # Test completed progress
        completed_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.COMPLETED,
            completed_steps=[OnboardingStep.COMPLETED],
            unlocked_features=[],
            current_tier=FeatureTier.EXPERT,
            progress_percentage=100.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        estimate = self.tracker._estimate_completion_time(completed_progress)
        self.assertEqual(estimate, 0)
        
        # Test zero progress
        zero_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=0.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        estimate = self.tracker._estimate_completion_time(zero_progress)
        self.assertEqual(estimate, 14)  # Default estimate
    
    def test_generate_progress_recommendations(self):
        """Test progress recommendations generation"""
        # Test low progress
        low_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        recommendations = self.tracker._generate_progress_recommendations(low_progress)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
        
        # Test stalled progress
        stalled_progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now(),
            last_activity=datetime.now() - timedelta(days=10),
            status=ProgressStatus.STALLED
        )
        
        recommendations = self.tracker._generate_progress_recommendations(stalled_progress)
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_get_event_description(self):
        """Test event description generation"""
        # Test step completed event
        step_event = ProgressEvent(
            event_id='test',
            user_id=self.user_id,
            event_type=ProgressEventType.STEP_COMPLETED,
            event_data={'step': 'welcome'},
            timestamp=datetime.now()
        )
        
        description = self.tracker._get_event_description(step_event)
        self.assertEqual(description, 'Completed welcome step')
        
        # Test feature unlocked event
        feature_event = ProgressEvent(
            event_id='test',
            user_id=self.user_id,
            event_type=ProgressEventType.FEATURE_UNLOCKED,
            event_data={'feature': 'dashboard_basic'},
            timestamp=datetime.now()
        )
        
        description = self.tracker._get_event_description(feature_event)
        self.assertEqual(description, 'Unlocked dashboard_basic feature')
        
        # Test milestone reached event
        milestone_event = ProgressEvent(
            event_id='test',
            user_id=self.user_id,
            event_type=ProgressEventType.MILESTONE_REACHED,
            event_data={'milestone_name': 'Welcome Complete'},
            timestamp=datetime.now()
        )
        
        description = self.tracker._get_event_description(milestone_event)
        self.assertEqual(description, 'Reached Welcome Complete milestone')


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch.object(progress_tracker, 'start_progress_tracking')
    def test_start_progress_tracking_function(self, mock_start):
        """Test convenience function for starting progress tracking"""
        mock_start.return_value = True
        
        success = start_progress_tracking(self.user_id)
        
        self.assertTrue(success)
        mock_start.assert_called_once_with(self.user_id)
    
    @patch.object(progress_tracker, 'get_progress')
    def test_get_progress_function(self, mock_get):
        """Test convenience function for getting progress"""
        mock_progress = MagicMock()
        mock_get.return_value = mock_progress
        
        progress = get_progress(self.user_id)
        
        self.assertEqual(progress, mock_progress)
        mock_get.assert_called_once_with(self.user_id)
    
    @patch.object(progress_tracker, 'update_progress')
    def test_update_progress_function(self, mock_update):
        """Test convenience function for updating progress"""
        mock_update.return_value = True
        
        success = update_progress(self.user_id, step=OnboardingStep.WELCOME)
        
        self.assertTrue(success)
        mock_update.assert_called_once_with(self.user_id, step=OnboardingStep.WELCOME, feature=None, event_type=None, event_data=None)
    
    @patch.object(progress_tracker, 'get_progress_analytics')
    def test_get_progress_analytics_function(self, mock_analytics):
        """Test convenience function for getting analytics"""
        mock_analytics.return_value = {'user_id': self.user_id, 'progress': 50.0}
        
        analytics = get_progress_analytics(self.user_id)
        
        self.assertEqual(analytics, {'user_id': self.user_id, 'progress': 50.0})
        mock_analytics.assert_called_once_with(self.user_id)
    
    @patch.object(progress_tracker, 'get_progress_comparison')
    def test_get_progress_comparison_function(self, mock_comparison):
        """Test convenience function for getting comparison"""
        mock_comparison.return_value = {'user_id': self.user_id, 'percentile': 75.0}
        
        comparison = get_progress_comparison(self.user_id)
        
        self.assertEqual(comparison, {'user_id': self.user_id, 'percentile': 75.0})
        mock_comparison.assert_called_once_with(self.user_id)
    
    @patch.object(progress_tracker, 'get_progress_visualization_data')
    def test_get_progress_visualization_data_function(self, mock_visualization):
        """Test convenience function for getting visualization data"""
        mock_visualization.return_value = {'user_id': self.user_id, 'timeline': []}
        
        visualization_data = get_progress_visualization_data(self.user_id)
        
        self.assertEqual(visualization_data, {'user_id': self.user_id, 'timeline': []})
        mock_visualization.assert_called_once_with(self.user_id)


class TestEnumsAndDataClasses(unittest.TestCase):
    """Test cases for enums and data classes"""
    
    def test_progress_event_type_enum(self):
        """Test ProgressEventType enum values"""
        self.assertEqual(ProgressEventType.STEP_COMPLETED.value, 'step_completed')
        self.assertEqual(ProgressEventType.FEATURE_UNLOCKED.value, 'feature_unlocked')
        self.assertEqual(ProgressEventType.MILESTONE_REACHED.value, 'milestone_reached')
        self.assertEqual(ProgressEventType.ACTIVITY_ADDED.value, 'activity_added')
        self.assertEqual(ProgressEventType.GOAL_SET.value, 'goal_set')
        self.assertEqual(ProgressEventType.ENGAGEMENT_INCREASED.value, 'engagement_increased')
        self.assertEqual(ProgressEventType.TIER_UPGRADED.value, 'tier_upgraded')
        self.assertEqual(ProgressEventType.ONBOARDING_STARTED.value, 'onboarding_started')
        self.assertEqual(ProgressEventType.ONBOARDING_COMPLETED.value, 'onboarding_completed')
        self.assertEqual(ProgressEventType.PROGRESS_STALLED.value, 'progress_stalled')
    
    def test_progress_status_enum(self):
        """Test ProgressStatus enum values"""
        self.assertEqual(ProgressStatus.NOT_STARTED.value, 'not_started')
        self.assertEqual(ProgressStatus.IN_PROGRESS.value, 'in_progress')
        self.assertEqual(ProgressStatus.STALLED.value, 'stalled')
        self.assertEqual(ProgressStatus.COMPLETED.value, 'completed')
        self.assertEqual(ProgressStatus.ABANDONED.value, 'abandoned')
    
    def test_progress_milestone_dataclass(self):
        """Test ProgressMilestone dataclass"""
        milestone = ProgressMilestone(
            milestone_id='test_milestone',
            name='Test Milestone',
            description='Test milestone description',
            required_steps=[OnboardingStep.WELCOME],
            required_features=['dashboard_basic'],
            required_activities=5,
            required_days=3,
            reward_description='Test reward'
        )
        
        self.assertEqual(milestone.milestone_id, 'test_milestone')
        self.assertEqual(milestone.name, 'Test Milestone')
        self.assertEqual(milestone.description, 'Test milestone description')
        self.assertEqual(milestone.required_steps, [OnboardingStep.WELCOME])
        self.assertEqual(milestone.required_features, ['dashboard_basic'])
        self.assertEqual(milestone.required_activities, 5)
        self.assertEqual(milestone.required_days, 3)
        self.assertEqual(milestone.reward_description, 'Test reward')
        self.assertFalse(milestone.completed)
        self.assertIsNone(milestone.completed_at)
        self.assertEqual(milestone.progress_percentage, 0.0)
    
    def test_progress_event_dataclass(self):
        """Test ProgressEvent dataclass"""
        event = ProgressEvent(
            event_id='test_event',
            user_id=1,
            event_type=ProgressEventType.STEP_COMPLETED,
            event_data={'step': 'welcome'},
            timestamp=datetime.now()
        )
        
        self.assertEqual(event.event_id, 'test_event')
        self.assertEqual(event.user_id, 1)
        self.assertEqual(event.event_type, ProgressEventType.STEP_COMPLETED)
        self.assertEqual(event.event_data, {'step': 'welcome'})
        self.assertIsInstance(event.timestamp, datetime)
        self.assertIsInstance(event.metadata, dict)
    
    def test_onboarding_progress_dataclass(self):
        """Test OnboardingProgress dataclass"""
        progress = OnboardingProgress(
            user_id=1,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=['dashboard_basic'],
            current_tier=FeatureTier.BASIC,
            progress_percentage=10.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        self.assertEqual(progress.user_id, 1)
        self.assertEqual(progress.current_step, OnboardingStep.WELCOME)
        self.assertEqual(progress.completed_steps, [OnboardingStep.WELCOME])
        self.assertEqual(progress.unlocked_features, ['dashboard_basic'])
        self.assertEqual(progress.current_tier, FeatureTier.BASIC)
        self.assertEqual(progress.progress_percentage, 10.0)
        self.assertIsInstance(progress.started_at, datetime)
        self.assertIsInstance(progress.last_activity, datetime)
        self.assertIsNone(progress.completed_at)
        self.assertEqual(progress.status, ProgressStatus.IN_PROGRESS)
        self.assertIsInstance(progress.milestones, list)
        self.assertIsInstance(progress.recent_events, list)
        self.assertIsInstance(progress.analytics, dict)


class TestIntegration(unittest.TestCase):
    """Integration tests for database interactions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch('onboarding_progress_tracker.USE_POSTGRES', True)
    @patch('onboarding_progress_tracker.get_db_connection')
    def test_postgresql_save_progress(self, mock_db):
        """Test PostgreSQL save progress query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        tracker = OnboardingProgressTracker()
        progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=0.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        tracker._save_progress(progress)
        
        # Verify PostgreSQL query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("UPDATE user_settings", call_args[0][0])
        self.assertIn("SET onboarding_progress = %s", call_args[0][0])
        self.assertIn("WHERE user_id = %s", call_args[0][0])
    
    @patch('onboarding_progress_tracker.USE_POSTGRES', False)
    @patch('onboarding_progress_tracker.get_db_connection')
    def test_sqlite_save_progress(self, mock_db):
        """Test SQLite save progress query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        tracker = OnboardingProgressTracker()
        progress = OnboardingProgress(
            user_id=self.user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            current_tier=FeatureTier.BASIC,
            progress_percentage=0.0,
            started_at=datetime.now(),
            last_activity=datetime.now()
        )
        
        tracker._save_progress(progress)
        
        # Verify SQLite query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("UPDATE user_settings", call_args[0][0])
        self.assertIn("SET onboarding_progress = ?", call_args[0][0])
        self.assertIn("WHERE user_id = ?", call_args[0][0])


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)


