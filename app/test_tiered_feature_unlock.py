"""
Test Suite for Tiered Feature Unlock Module

This module tests the sophisticated tiered feature unlocking logic including:
- Feature unlock requirement checking
- Tiered progression tracking
- Performance metrics calculation
- Unlock condition validation
- Progress analysis and recommendations
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json

from tiered_feature_unlock import (
    TieredFeatureUnlockManager,
    UnlockCondition,
    UnlockTrigger,
    UnlockRequirement,
    TieredFeatureDefinition,
    FeatureTier,
    check_tiered_feature_unlock,
    unlock_tiered_feature,
    get_tiered_feature_progress,
    get_available_tiered_features,
    tiered_feature_manager
)
from onboarding_manager import OnboardingStep


class TestTieredFeatureUnlockManager(unittest.TestCase):
    """Test cases for TieredFeatureUnlockManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = TieredFeatureUnlockManager()
        self.user_id = 1
    
    def test_initialization(self):
        """Test manager initialization"""
        self.assertIsNotNone(self.manager.onboarding_manager)
        self.assertIsNotNone(self.manager.feature_definitions)
        self.assertIsNotNone(self.manager.unlock_rules)
        self.assertIsNotNone(self.manager.performance_metrics)
        
        # Check that features are defined
        self.assertGreater(len(self.manager.feature_definitions), 0)
        
        # Check that all tiers are represented
        tiers = set()
        for feature_def in self.manager.feature_definitions.values():
            tiers.add(feature_def.tier)
        
        self.assertIn(FeatureTier.BASIC, tiers)
        self.assertIn(FeatureTier.INTERMEDIATE, tiers)
        self.assertIn(FeatureTier.ADVANCED, tiers)
        self.assertIn(FeatureTier.EXPERT, tiers)
    
    def test_feature_definitions_structure(self):
        """Test that feature definitions have correct structure"""
        for feature_name, feature_def in self.manager.feature_definitions.items():
            self.assertIsInstance(feature_def, TieredFeatureDefinition)
            # feature_name is the key, feature_def.feature_name is the display name
            self.assertIsInstance(feature_def.feature_name, str)
            self.assertIsInstance(feature_def.tier, FeatureTier)
            self.assertIsInstance(feature_def.requirements, list)
            self.assertIsInstance(feature_def.dependencies, list)
            self.assertIsInstance(feature_def.unlock_trigger, UnlockTrigger)
            self.assertIsInstance(feature_def.unlock_conditions, dict)
            self.assertIsInstance(feature_def.description, str)
            self.assertIsInstance(feature_def.tutorial_available, bool)
            self.assertIsInstance(feature_def.priority, int)
    
    @patch('tiered_feature_unlock.get_db_connection')
    def test_get_user_activity_count(self, mock_db):
        """Test getting user activity count"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        count = self.manager._get_user_activity_count(self.user_id)
        
        self.assertEqual(count, 5)
        mock_cursor.execute.assert_called_once()
    
    @patch('tiered_feature_unlock.get_db_connection')
    def test_get_user_days_active(self, mock_db):
        """Test getting user days active"""
        # Mock database response
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (3,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        days = self.manager._get_user_days_active(self.user_id)
        
        self.assertEqual(days, 3)
        mock_cursor.execute.assert_called_once()
    
    @patch.object(TieredFeatureUnlockManager, '_get_user_days_active')
    @patch('tiered_feature_unlock.get_db_connection')
    def test_get_usage_frequency(self, mock_db, mock_days_active):
        """Test calculating usage frequency"""
        # Mock responses
        mock_days_active.return_value = 5
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (datetime.now() - timedelta(days=10),)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        frequency = self.manager._get_usage_frequency(self.user_id)
        
        # Should be 5/10 = 0.5
        self.assertEqual(frequency, 0.5)
    
    def test_get_performance_score(self):
        """Test calculating performance score"""
        with patch.object(self.manager, '_get_user_activity_count', return_value=6):
            with patch.object(self.manager, '_get_user_days_active', return_value=3):
                score = self.manager._get_performance_score(self.user_id)
                
                # 6 activities / (3 days * 2) = 1.0 (capped at 1.0)
                self.assertEqual(score, 1.0)
    
    def test_get_engagement_level(self):
        """Test calculating engagement level"""
        with patch.object(self.manager, '_get_usage_frequency', return_value=0.7):
            with patch.object(self.manager, '_get_user_activity_count', return_value=8):
                engagement = self.manager._get_engagement_level(self.user_id)
                
                # (0.7 * 0.6) + (min(8/10, 1.0) * 0.4) = 0.42 + 0.32 = 0.74
                expected = (0.7 * 0.6) + (min(8/10, 1.0) * 0.4)
                self.assertAlmostEqual(engagement, expected, places=2)
    
    def test_get_social_score(self):
        """Test calculating social score"""
        with patch.object(self.manager, '_get_user_activity_count', return_value=6):
            score = self.manager._get_social_score(self.user_id)
            self.assertEqual(score, 1)  # 6 >= 5
    
    def test_compare_values(self):
        """Test value comparison with different operators"""
        # Test >= operator
        self.assertTrue(self.manager._compare_values(5, 3, '>='))
        self.assertTrue(self.manager._compare_values(3, 3, '>='))
        self.assertFalse(self.manager._compare_values(2, 3, '>='))
        
        # Test > operator
        self.assertTrue(self.manager._compare_values(5, 3, '>'))
        self.assertFalse(self.manager._compare_values(3, 3, '>'))
        
        # Test == operator
        self.assertTrue(self.manager._compare_values(3, 3, '=='))
        self.assertFalse(self.manager._compare_values(3, 4, '=='))
        
        # Test invalid operator
        self.assertFalse(self.manager._compare_values(3, 3, 'invalid'))
    
    @patch.object(TieredFeatureUnlockManager, 'onboarding_manager')
    def test_check_requirement_step_completion(self, mock_onboarding_manager):
        """Test checking step completion requirement"""
        # Mock onboarding manager responses
        mock_progress_obj = MagicMock()
        mock_progress_obj.completed_steps = [OnboardingStep.WELCOME, OnboardingStep.FIRST_ACTIVITY]
        mock_onboarding_manager.get_onboarding_progress.return_value = mock_progress_obj
        
        requirement = UnlockRequirement(
            UnlockCondition.STEP_COMPLETION,
            OnboardingStep.WELCOME,
            '==',
            'Complete welcome step'
        )
        
        result = self.manager._check_requirement(self.user_id, requirement)
        self.assertTrue(result)
    
    @patch.object(TieredFeatureUnlockManager, '_get_user_activity_count')
    def test_check_requirement_activity_count(self, mock_activity_count):
        """Test checking activity count requirement"""
        mock_activity_count.return_value = 5
        
        requirement = UnlockRequirement(
            UnlockCondition.ACTIVITY_COUNT,
            3,
            '>=',
            'Have at least 3 activities'
        )
        
        result = self.manager._check_requirement(self.user_id, requirement)
        self.assertTrue(result)
    
    @patch.object(TieredFeatureUnlockManager, '_get_usage_frequency')
    def test_check_requirement_usage_frequency(self, mock_usage_freq):
        """Test checking usage frequency requirement"""
        mock_usage_freq.return_value = 0.7
        
        requirement = UnlockRequirement(
            UnlockCondition.USAGE_FREQUENCY,
            0.6,
            '>=',
            'Use the app regularly'
        )
        
        result = self.manager._check_requirement(self.user_id, requirement)
        self.assertTrue(result)
    
    @patch.object(TieredFeatureUnlockManager, '_get_performance_score')
    def test_check_requirement_performance_threshold(self, mock_perf_score):
        """Test checking performance threshold requirement"""
        mock_perf_score.return_value = 0.8
        
        requirement = UnlockRequirement(
            UnlockCondition.PERFORMANCE_THRESHOLD,
            0.7,
            '>=',
            'Meet performance standards'
        )
        
        result = self.manager._check_requirement(self.user_id, requirement)
        self.assertTrue(result)
    
    @patch.object(TieredFeatureUnlockManager, '_get_engagement_level')
    def test_check_requirement_engagement_level(self, mock_engagement):
        """Test checking engagement level requirement"""
        mock_engagement.return_value = 0.8
        
        requirement = UnlockRequirement(
            UnlockCondition.ENGAGEMENT_LEVEL,
            0.7,
            '>=',
            'Show consistent engagement'
        )
        
        result = self.manager._check_requirement(self.user_id, requirement)
        self.assertTrue(result)
    
    @patch.object(TieredFeatureUnlockManager, '_get_social_score')
    def test_check_requirement_social_interaction(self, mock_social):
        """Test checking social interaction requirement"""
        mock_social.return_value = 1
        
        requirement = UnlockRequirement(
            UnlockCondition.SOCIAL_INTERACTION,
            1,
            '>=',
            'Show social engagement'
        )
        
        result = self.manager._check_requirement(self.user_id, requirement)
        self.assertTrue(result)
    
    @patch.object(TieredFeatureUnlockManager, 'onboarding_manager')
    def test_check_tiered_feature_unlock_success(self, mock_onboarding_manager):
        """Test successful feature unlock check"""
        # Mock onboarding manager responses
        mock_onboarding_manager.check_feature_unlock.return_value = True
        mock_onboarding_manager.get_onboarding_progress.return_value = MagicMock(
            completed_steps=[OnboardingStep.WELCOME]
        )
        
        # Mock requirement checking methods
        with patch.object(self.manager, '_get_user_activity_count', return_value=5):
            with patch.object(self.manager, '_get_user_days_active', return_value=3):
                with patch.object(self.manager, '_get_usage_frequency', return_value=0.7):
                    with patch.object(self.manager, '_get_engagement_level', return_value=0.8):
                        with patch.object(self.manager, '_check_unlock_conditions', return_value=True):
                            can_unlock, analysis = self.manager.check_tiered_feature_unlock(
                                self.user_id, 'dashboard_advanced'
                            )
                            
                            self.assertTrue(can_unlock)
                            self.assertIn('feature_name', analysis)
                            self.assertIn('tier', analysis)
                            self.assertIn('unlock_score', analysis)
                            self.assertIn('can_unlock', analysis)
    
    @patch.object(TieredFeatureUnlockManager, 'onboarding_manager')
    def test_check_tiered_feature_unlock_failure(self, mock_onboarding_manager):
        """Test failed feature unlock check"""
        # Mock onboarding manager responses
        mock_onboarding_manager.check_feature_unlock.return_value = False
        mock_onboarding_manager.get_onboarding_progress.return_value = MagicMock(
            completed_steps=[]
        )
        
        can_unlock, analysis = self.manager.check_tiered_feature_unlock(
            self.user_id, 'dashboard_advanced'
        )
        
        self.assertFalse(can_unlock)
        self.assertIn('requirements_failed', analysis)
        self.assertIn('recommendations', analysis)
    
    @patch.object(TieredFeatureUnlockManager, 'check_tiered_feature_unlock')
    @patch.object(TieredFeatureUnlockManager, 'onboarding_manager')
    def test_unlock_tiered_feature_success(self, mock_onboarding_manager, mock_check):
        """Test successful feature unlock"""
        # Mock successful unlock check
        mock_check.return_value = (True, {
            'feature_name': 'dashboard_advanced',
            'tier': 'intermediate',
            'unlock_score': 1.0
        })
        
        # Mock onboarding manager unlock
        mock_onboarding_manager.unlock_feature.return_value = True
        
        success, result = self.manager.unlock_tiered_feature(self.user_id, 'dashboard_advanced')
        
        self.assertTrue(success)
        self.assertIn('success', result)
        self.assertIn('feature_name', result)
        self.assertIn('tier', result)
    
    @patch.object(TieredFeatureUnlockManager, 'check_tiered_feature_unlock')
    def test_unlock_tiered_feature_failure(self, mock_check):
        """Test failed feature unlock"""
        # Mock failed unlock check
        mock_check.return_value = (False, {
            'requirements_failed': ['dependency not met'],
            'recommendations': ['Complete basic dashboard first']
        })
        
        success, result = self.manager.unlock_tiered_feature(self.user_id, 'dashboard_advanced')
        
        self.assertFalse(success)
        self.assertIn('reason', result)
        self.assertIn('analysis', result)
    
    @patch.object(TieredFeatureUnlockManager, 'check_tiered_feature_unlock')
    @patch.object(TieredFeatureUnlockManager, '_get_current_tier')
    @patch.object(TieredFeatureUnlockManager, '_get_user_activity_count')
    @patch.object(TieredFeatureUnlockManager, '_get_user_days_active')
    def test_get_tiered_feature_progress(self, mock_days_active, mock_activity_count, mock_current_tier, mock_check):
        """Test getting tiered feature progress"""
        # Mock responses
        mock_current_tier.return_value = 'basic'
        mock_activity_count.return_value = 1
        mock_days_active.return_value = 2
        mock_check.return_value = (False, {
            'unlock_score': 0.5,
            'requirements_met': [],
            'requirements_failed': []
        })
        
        progress = self.manager.get_tiered_feature_progress(self.user_id)
        
        self.assertIn('user_id', progress)
        self.assertIn('current_tier', progress)
        self.assertIn('features_by_tier', progress)
        self.assertIn('unlock_progress', progress)
        self.assertIn('recommendations', progress)
        self.assertIn('next_milestones', progress)
    
    def test_generate_unlock_recommendations(self):
        """Test generating unlock recommendations"""
        feature_def = self.manager.feature_definitions['dashboard_advanced']
        analysis = {
            'requirements_failed': [
                {'condition': 'activity_count', 'value': 3},
                {'condition': 'days_active', 'value': 5},
                {'condition': 'usage_frequency', 'value': 0.6},
                {'condition': 'engagement_level', 'value': 0.7}
            ]
        }
        
        recommendations = self.manager._generate_unlock_recommendations(
            self.user_id, feature_def, analysis
        )
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)
    
    def test_generate_user_recommendations(self):
        """Test generating user recommendations"""
        with patch.object(self.manager, '_get_user_activity_count', return_value=1):
            with patch.object(self.manager, '_get_user_days_active', return_value=1):
                with patch.object(self.manager, '_get_usage_frequency', return_value=0.3):
                    recommendations = self.manager._generate_user_recommendations(self.user_id)
                    
                    self.assertIsInstance(recommendations, list)
                    self.assertGreater(len(recommendations), 0)
    
    def test_get_next_milestones(self):
        """Test getting next milestones"""
        with patch.object(self.manager, '_get_user_activity_count', return_value=1):
            with patch.object(self.manager, '_get_user_days_active', return_value=2):
                milestones = self.manager._get_next_milestones(self.user_id)
                
                self.assertIsInstance(milestones, list)
                for milestone in milestones:
                    self.assertIn('type', milestone)
                    self.assertIn('current', milestone)
                    self.assertIn('target', milestone)
                    self.assertIn('description', milestone)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch.object(tiered_feature_manager, 'check_tiered_feature_unlock')
    def test_check_tiered_feature_unlock_function(self, mock_check):
        """Test convenience function for checking feature unlock"""
        mock_check.return_value = (True, {'unlock_score': 1.0})
        
        can_unlock, analysis = check_tiered_feature_unlock(self.user_id, 'dashboard_advanced')
        
        self.assertTrue(can_unlock)
        self.assertIn('unlock_score', analysis)
        mock_check.assert_called_once_with(self.user_id, 'dashboard_advanced')
    
    @patch.object(tiered_feature_manager, 'unlock_tiered_feature')
    def test_unlock_tiered_feature_function(self, mock_unlock):
        """Test convenience function for unlocking feature"""
        mock_unlock.return_value = (True, {'success': True})
        
        success, result = unlock_tiered_feature(self.user_id, 'dashboard_advanced')
        
        self.assertTrue(success)
        self.assertIn('success', result)
        mock_unlock.assert_called_once_with(self.user_id, 'dashboard_advanced')
    
    @patch.object(tiered_feature_manager, 'get_tiered_feature_progress')
    def test_get_tiered_feature_progress_function(self, mock_progress):
        """Test convenience function for getting progress"""
        mock_progress.return_value = {'user_id': self.user_id, 'current_tier': 'basic'}
        
        progress = get_tiered_feature_progress(self.user_id)
        
        self.assertIn('user_id', progress)
        self.assertIn('current_tier', progress)
        mock_progress.assert_called_once_with(self.user_id)
    
    @patch.object(tiered_feature_manager, 'check_tiered_feature_unlock')
    def test_get_available_tiered_features(self, mock_check):
        """Test getting available tiered features"""
        # Mock responses for different features
        mock_check.side_effect = [
            (True, {'unlock_score': 1.0}),   # dashboard_basic
            (False, {'unlock_score': 0.5}),  # dashboard_advanced
            (True, {'unlock_score': 0.8})    # recommendations
        ]
        
        features = get_available_tiered_features(self.user_id)
        
        self.assertIsInstance(features, list)
        self.assertGreater(len(features), 0)
        
        for feature in features:
            self.assertIn('name', feature)
            self.assertIn('tier', feature)
            self.assertIn('description', feature)
            self.assertIn('can_unlock', feature)
            self.assertIn('unlock_score', feature)
            self.assertIn('requirements_met', feature)
            self.assertIn('total_requirements', feature)
            self.assertIn('tutorial_available', feature)
            self.assertIn('priority', feature)


class TestEnumsAndDataClasses(unittest.TestCase):
    """Test cases for enums and data classes"""
    
    def test_unlock_condition_enum(self):
        """Test UnlockCondition enum values"""
        self.assertEqual(UnlockCondition.STEP_COMPLETION.value, 'step_completion')
        self.assertEqual(UnlockCondition.ACTIVITY_COUNT.value, 'activity_count')
        self.assertEqual(UnlockCondition.DAYS_ACTIVE.value, 'days_active')
        self.assertEqual(UnlockCondition.USAGE_FREQUENCY.value, 'usage_frequency')
        self.assertEqual(UnlockCondition.PERFORMANCE_THRESHOLD.value, 'performance_threshold')
        self.assertEqual(UnlockCondition.ENGAGEMENT_LEVEL.value, 'engagement_level')
        self.assertEqual(UnlockCondition.SOCIAL_INTERACTION.value, 'social_interaction')
        self.assertEqual(UnlockCondition.TIME_BASED.value, 'time_based')
        self.assertEqual(UnlockCondition.CUSTOM_RULE.value, 'custom_rule')
    
    def test_unlock_trigger_enum(self):
        """Test UnlockTrigger enum values"""
        self.assertEqual(UnlockTrigger.AUTOMATIC.value, 'automatic')
        self.assertEqual(UnlockTrigger.MANUAL.value, 'manual')
        self.assertEqual(UnlockTrigger.SCHEDULED.value, 'scheduled')
        self.assertEqual(UnlockTrigger.EVENT_BASED.value, 'event_based')
        self.assertEqual(UnlockTrigger.CONDITIONAL.value, 'conditional')
    
    def test_unlock_requirement_dataclass(self):
        """Test UnlockRequirement dataclass"""
        requirement = UnlockRequirement(
            condition=UnlockCondition.ACTIVITY_COUNT,
            value=5,
            operator='>=',
            description='Have at least 5 activities',
            weight=1.0
        )
        
        self.assertEqual(requirement.condition, UnlockCondition.ACTIVITY_COUNT)
        self.assertEqual(requirement.value, 5)
        self.assertEqual(requirement.operator, '>=')
        self.assertEqual(requirement.description, 'Have at least 5 activities')
        self.assertEqual(requirement.weight, 1.0)
    
    def test_tiered_feature_definition_dataclass(self):
        """Test TieredFeatureDefinition dataclass"""
        feature_def = TieredFeatureDefinition(
            feature_name='test_feature',
            tier=FeatureTier.INTERMEDIATE,
            requirements=[],
            dependencies=[],
            unlock_trigger=UnlockTrigger.CONDITIONAL,
            unlock_conditions={},
            description='Test feature',
            tutorial_available=True,
            priority=1
        )
        
        self.assertEqual(feature_def.feature_name, 'test_feature')
        self.assertEqual(feature_def.tier, FeatureTier.INTERMEDIATE)
        self.assertEqual(feature_def.unlock_trigger, UnlockTrigger.CONDITIONAL)
        self.assertEqual(feature_def.description, 'Test feature')
        self.assertTrue(feature_def.tutorial_available)
        self.assertEqual(feature_def.priority, 1)


class TestIntegration(unittest.TestCase):
    """Integration tests for database interactions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch('tiered_feature_unlock.USE_POSTGRES', True)
    @patch('tiered_feature_unlock.get_db_connection')
    def test_postgresql_activity_count_query(self, mock_db):
        """Test PostgreSQL activity count query format"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (3,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        manager = TieredFeatureUnlockManager()
        count = manager._get_user_activity_count(self.user_id)
        
        # Verify PostgreSQL query format
        mock_cursor.execute.assert_called_with(
            "SELECT COUNT(*) FROM activities WHERE user_id = %s",
            (self.user_id,)
        )
        self.assertEqual(count, 3)
    
    @patch('tiered_feature_unlock.USE_POSTGRES', False)
    @patch('tiered_feature_unlock.get_db_connection')
    def test_sqlite_activity_count_query(self, mock_db):
        """Test SQLite activity count query format"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (3,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        manager = TieredFeatureUnlockManager()
        count = manager._get_user_activity_count(self.user_id)
        
        # Verify SQLite query format
        mock_cursor.execute.assert_called_with(
            "SELECT COUNT(*) FROM activities WHERE user_id = ?",
            (self.user_id,)
        )
        self.assertEqual(count, 3)
    
    @patch('tiered_feature_unlock.USE_POSTGRES', True)
    @patch('tiered_feature_unlock.get_db_connection')
    def test_postgresql_days_active_query(self, mock_db):
        """Test PostgreSQL days active query format"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (5,)
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        manager = TieredFeatureUnlockManager()
        days = manager._get_user_days_active(self.user_id)
        
        # Verify PostgreSQL query format - check that the call was made with the right parameters
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("SELECT COUNT(DISTINCT date)", call_args[0][0])
        self.assertIn("FROM activities", call_args[0][0])
        self.assertIn("WHERE user_id = %s", call_args[0][0])
        self.assertEqual(call_args[0][1], (self.user_id,))
        self.assertEqual(days, 5)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
