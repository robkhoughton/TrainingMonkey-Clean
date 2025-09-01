"""
Test Suite for Onboarding Manager Module

This module tests the comprehensive onboarding management functionality including
progressive feature unlocking, onboarding progress tracking, and tiered user experience.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import json
from datetime import datetime, timedelta

# Add the app directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from onboarding_manager import (
    OnboardingManager, 
    OnboardingStep,
    FeatureTier,
    OnboardingProgress,
    FeatureUnlock,
    start_user_onboarding,
    get_user_onboarding_progress,
    complete_onboarding_step,
    is_feature_unlocked,
    get_available_features,
    onboarding_manager
)


class TestOnboardingManager(unittest.TestCase):
    """Test cases for onboarding manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = OnboardingManager()
        self.test_user_id = 999
    
    def test_feature_definitions_initialization(self):
        """Test that feature definitions are properly initialized"""
        self.assertIsNotNone(self.manager.feature_definitions)
        self.assertGreater(len(self.manager.feature_definitions), 0)
        
        # Check that all features have required attributes
        for feature_name, feature_def in self.manager.feature_definitions.items():
            self.assertIsInstance(feature_def, FeatureUnlock)
            self.assertIsInstance(feature_def.feature_name, str)
            self.assertIsInstance(feature_def.tier, FeatureTier)
            self.assertIsInstance(feature_def.required_steps, list)
            self.assertIsInstance(feature_def.required_activities, int)
            self.assertIsInstance(feature_def.required_days, int)
            self.assertIsInstance(feature_def.description, str)
            self.assertIsInstance(feature_def.tutorial_available, bool)
    
    def test_step_requirements_initialization(self):
        """Test that step requirements are properly initialized"""
        self.assertIsNotNone(self.manager.step_requirements)
        self.assertGreater(len(self.manager.step_requirements), 0)
        
        # Check that all steps have required attributes
        for step, req in self.manager.step_requirements.items():
            self.assertIsInstance(step, OnboardingStep)
            self.assertIsInstance(req, dict)
            self.assertIn('description', req)
            self.assertIn('auto_complete', req)
            self.assertIn('required_actions', req)
    
    def test_feature_tiers(self):
        """Test feature tier enumeration"""
        tiers = [FeatureTier.BASIC, FeatureTier.INTERMEDIATE, FeatureTier.ADVANCED, FeatureTier.EXPERT]
        for tier in tiers:
            self.assertIsInstance(tier, FeatureTier)
            self.assertIsInstance(tier.value, str)
    
    def test_onboarding_steps(self):
        """Test onboarding step enumeration"""
        steps = [
            OnboardingStep.WELCOME,
            OnboardingStep.STRAVA_CONNECTED,
            OnboardingStep.FIRST_ACTIVITY,
            OnboardingStep.DATA_SYNC,
            OnboardingStep.DASHBOARD_INTRO,
            OnboardingStep.FEATURES_TOUR,
            OnboardingStep.GOALS_SETUP,
            OnboardingStep.FIRST_RECOMMENDATION,
            OnboardingStep.JOURNAL_INTRO,
            OnboardingStep.COMPLETED
        ]
        for step in steps:
            self.assertIsInstance(step, OnboardingStep)
            self.assertIsInstance(step.value, str)
    
    @patch('onboarding_manager.get_db_connection')
    def test_start_onboarding(self, mock_connection):
        """Test starting onboarding for a user"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.manager.start_onboarding(self.test_user_id)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
        
        # Verify the correct SQL was executed
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('onboarding_step', call_args[0])
        self.assertIn('onboarding_completed_at', call_args[0])
    
    @patch('onboarding_manager.get_db_connection')
    def test_get_onboarding_progress(self, mock_connection):
        """Test getting onboarding progress for a user"""
        # Mock database connection with test data
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (
            OnboardingStep.WELCOME.value,  # onboarding_step
            None,  # onboarding_completed_at
            datetime.now(),  # last_onboarding_activity
            datetime.now() - timedelta(days=1)  # created_at
        )
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock _get_completed_steps and _get_unlocked_features
        with patch.object(self.manager, '_get_completed_steps', return_value=[]):
            with patch.object(self.manager, '_get_unlocked_features', return_value=[]):
                progress = self.manager.get_onboarding_progress(self.test_user_id)
        
        self.assertIsNotNone(progress)
        self.assertIsInstance(progress, OnboardingProgress)
        self.assertEqual(progress.user_id, self.test_user_id)
        self.assertEqual(progress.current_step, OnboardingStep.WELCOME)
        self.assertEqual(progress.progress_percentage, 0.0)
    
    @patch('onboarding_manager.get_db_connection')
    def test_complete_onboarding_step(self, mock_connection):
        """Test completing an onboarding step"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.manager.complete_onboarding_step(self.test_user_id, OnboardingStep.WELCOME)
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
        
        # Verify the correct SQL was executed
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('onboarding_step', call_args[0])
        self.assertIn('last_onboarding_activity', call_args[0])
    
    @patch('onboarding_manager.get_db_connection')
    def test_check_feature_unlock_basic_dashboard(self, mock_connection):
        """Test checking if basic dashboard feature is unlocked"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock get_onboarding_progress to return a user with WELCOME step completed
        mock_progress = OnboardingProgress(
            user_id=self.test_user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=[],
            progress_percentage=10.0,
            last_activity=datetime.now(),
            started_at=datetime.now() - timedelta(days=1)
        )
        
        with patch.object(self.manager, 'get_onboarding_progress', return_value=mock_progress):
            with patch.object(self.manager, '_get_user_activity_count', return_value=0):
                result = self.manager.check_feature_unlock(self.test_user_id, 'dashboard_basic')
        
        self.assertTrue(result)
    
    @patch('onboarding_manager.get_db_connection')
    def test_check_feature_unlock_advanced_dashboard_not_unlocked(self, mock_connection):
        """Test checking if advanced dashboard feature is not unlocked for new user"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock get_onboarding_progress to return a user with only WELCOME step completed
        mock_progress = OnboardingProgress(
            user_id=self.test_user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=[],
            progress_percentage=10.0,
            last_activity=datetime.now(),
            started_at=datetime.now() - timedelta(days=1)
        )
        
        with patch.object(self.manager, 'get_onboarding_progress', return_value=mock_progress):
            with patch.object(self.manager, '_get_user_activity_count', return_value=0):
                result = self.manager.check_feature_unlock(self.test_user_id, 'dashboard_advanced')
        
        self.assertFalse(result)
    
    @patch('onboarding_manager.get_db_connection')
    def test_unlock_feature(self, mock_connection):
        """Test unlocking a feature for a user"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock check_feature_unlock to return True
        with patch.object(self.manager, 'check_feature_unlock', return_value=True):
            with patch.object(self.manager, '_get_unlocked_features', return_value=[]):
                result = self.manager.unlock_feature(self.test_user_id, 'dashboard_basic')
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called()
    
    @patch('onboarding_manager.get_db_connection')
    def test_get_available_features(self, mock_connection):
        """Test getting available features for a user"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock check_feature_unlock to return True for dashboard_basic
        with patch.object(self.manager, 'check_feature_unlock', side_effect=lambda user_id, feature: feature == 'dashboard_basic'):
            features = self.manager.get_available_features(self.test_user_id)
        
        self.assertIsInstance(features, list)
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0].feature_name, 'Basic Dashboard')
    
    @patch('onboarding_manager.get_db_connection')
    def test_get_next_onboarding_step(self, mock_connection):
        """Test getting the next onboarding step for a user"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        # Mock get_onboarding_progress to return a user with WELCOME step completed
        mock_progress = OnboardingProgress(
            user_id=self.test_user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=[],
            progress_percentage=10.0,
            last_activity=datetime.now(),
            started_at=datetime.now() - timedelta(days=1)
        )
        
        with patch.object(self.manager, 'get_onboarding_progress', return_value=mock_progress):
            with patch.object(self.manager, '_can_complete_step', return_value=True):
                next_step = self.manager.get_next_onboarding_step(self.test_user_id)
        
        self.assertIsNotNone(next_step)
        self.assertIsInstance(next_step, OnboardingStep)
    
    @patch('onboarding_manager.get_db_connection')
    def test_get_user_activity_count(self, mock_connection):
        """Test getting user activity count"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)  # 5 activities
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        count = self.manager._get_user_activity_count(self.test_user_id)
        
        self.assertEqual(count, 5)
        mock_cursor.execute.assert_called()
    
    @patch('onboarding_manager.get_db_connection')
    def test_can_complete_step_auto_complete(self, mock_connection):
        """Test that auto-complete steps can be completed"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.manager._can_complete_step(self.test_user_id, OnboardingStep.WELCOME)
        
        self.assertTrue(result)
    
    @patch('onboarding_manager.get_db_connection')
    def test_can_complete_step_strava_connected(self, mock_connection):
        """Test checking if Strava connected step can be completed"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (12345,)  # Has Strava athlete ID
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.manager._can_complete_step(self.test_user_id, OnboardingStep.STRAVA_CONNECTED)
        
        self.assertTrue(result)
    
    @patch('onboarding_manager.get_db_connection')
    def test_can_complete_step_strava_not_connected(self, mock_connection):
        """Test checking if Strava connected step cannot be completed when not connected"""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (None,)  # No Strava athlete ID
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        result = self.manager._can_complete_step(self.test_user_id, OnboardingStep.STRAVA_CONNECTED)
        
        self.assertFalse(result)
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly"""
        # Test start_user_onboarding
        with patch.object(onboarding_manager, 'start_onboarding', return_value=True):
            result = start_user_onboarding(self.test_user_id)
            self.assertTrue(result)
        
        # Test get_user_onboarding_progress
        mock_progress = OnboardingProgress(
            user_id=self.test_user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[],
            unlocked_features=[],
            progress_percentage=0.0,
            last_activity=datetime.now(),
            started_at=datetime.now()
        )
        with patch.object(onboarding_manager, 'get_onboarding_progress', return_value=mock_progress):
            progress = get_user_onboarding_progress(self.test_user_id)
            self.assertEqual(progress.user_id, self.test_user_id)
        
        # Test complete_onboarding_step
        with patch.object(onboarding_manager, 'complete_onboarding_step', return_value=True):
            result = complete_onboarding_step(self.test_user_id, OnboardingStep.WELCOME)
            self.assertTrue(result)
        
        # Test is_feature_unlocked
        with patch.object(onboarding_manager, 'check_feature_unlock', return_value=True):
            result = is_feature_unlocked(self.test_user_id, 'dashboard_basic')
            self.assertTrue(result)
        
        # Test get_available_features
        mock_features = [onboarding_manager.feature_definitions['dashboard_basic']]
        with patch.object(onboarding_manager, 'get_available_features', return_value=mock_features):
            features = get_available_features(self.test_user_id)
            self.assertEqual(len(features), 1)
    
    def test_onboarding_progress_dataclass(self):
        """Test OnboardingProgress dataclass"""
        progress = OnboardingProgress(
            user_id=self.test_user_id,
            current_step=OnboardingStep.WELCOME,
            completed_steps=[OnboardingStep.WELCOME],
            unlocked_features=['dashboard_basic'],
            progress_percentage=10.0,
            last_activity=datetime.now(),
            started_at=datetime.now() - timedelta(days=1)
        )
        
        self.assertEqual(progress.user_id, self.test_user_id)
        self.assertEqual(progress.current_step, OnboardingStep.WELCOME)
        self.assertEqual(len(progress.completed_steps), 1)
        self.assertEqual(len(progress.unlocked_features), 1)
        self.assertEqual(progress.progress_percentage, 10.0)
    
    def test_feature_unlock_dataclass(self):
        """Test FeatureUnlock dataclass"""
        feature = FeatureUnlock(
            feature_name='Test Feature',
            tier=FeatureTier.BASIC,
            required_steps=[OnboardingStep.WELCOME],
            required_activities=0,
            required_days=0,
            description='Test feature description',
            tutorial_available=True
        )
        
        self.assertEqual(feature.feature_name, 'Test Feature')
        self.assertEqual(feature.tier, FeatureTier.BASIC)
        self.assertEqual(len(feature.required_steps), 1)
        self.assertEqual(feature.required_activities, 0)
        self.assertEqual(feature.required_days, 0)
        self.assertEqual(feature.description, 'Test feature description')
        self.assertTrue(feature.tutorial_available)


class TestOnboardingManagerIntegration(unittest.TestCase):
    """Integration tests for onboarding manager with database"""
    
    @patch('onboarding_manager.USE_POSTGRES', True)
    @patch('onboarding_manager.get_db_connection')
    def test_postgres_queries(self, mock_connection):
        """Test PostgreSQL query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        manager = OnboardingManager()
        manager.start_onboarding(1)
        
        # Verify PostgreSQL query was used
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('%s', call_args[0])  # PostgreSQL parameter style
    
    @patch('onboarding_manager.USE_POSTGRES', False)
    @patch('onboarding_manager.get_db_connection')
    def test_sqlite_queries(self, mock_connection):
        """Test SQLite query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connection.return_value.__enter__.return_value = mock_conn
        
        manager = OnboardingManager()
        manager.start_onboarding(1)
        
        # Verify SQLite query was used
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args[0]
        self.assertIn('?', call_args[0])  # SQLite parameter style


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
