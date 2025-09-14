"""
Test Suite for Progressive Feature Triggers Module

This module tests the progressive feature unlock triggers functionality including:
- Trigger initialization and management
- Trigger condition evaluation and checking
- Trigger execution and feature unlocking
- Trigger status and analytics
- Event-based trigger evaluation
- Cooldown and max trigger enforcement
- Trigger priority and sorting
- Database integration and event persistence
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json

from progressive_feature_triggers import (
    ProgressiveFeatureTriggers,
    TriggerType,
    TriggerStatus,
    TriggerCondition,
    FeatureUnlockTrigger,
    TriggerEvent,
    TriggerAnalytics,
    check_triggers,
    get_user_triggers,
    get_trigger_analytics,
    feature_triggers
)
from onboarding_manager import OnboardingStep, FeatureTier


class TestProgressiveFeatureTriggers(unittest.TestCase):
    """Test cases for ProgressiveFeatureTriggers class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.feature_triggers = ProgressiveFeatureTriggers()
        self.user_id = 1
    
    def test_initialization(self):
        """Test feature triggers initialization"""
        self.assertIsNotNone(self.feature_triggers.onboarding_manager)
        self.assertIsNotNone(self.feature_triggers.progress_tracker)
        self.assertIsNotNone(self.feature_triggers.tutorial_system)
        self.assertIsNotNone(self.feature_triggers.tiered_feature_manager)
        self.assertIsNotNone(self.feature_triggers.dashboard_manager)
        self.assertIsNotNone(self.feature_triggers.triggers)
        self.assertIsNotNone(self.feature_triggers.trigger_events)
        
        # Check that triggers are defined
        self.assertGreater(len(self.feature_triggers.triggers), 0)
        
        # Check trigger structure
        for trigger_id, trigger in self.feature_triggers.triggers.items():
            self.assertIsInstance(trigger, FeatureUnlockTrigger)
            self.assertEqual(trigger.trigger_id, trigger_id)
            self.assertIsInstance(trigger.name, str)
            self.assertIsInstance(trigger.description, str)
            self.assertIsInstance(trigger.trigger_type, TriggerType)
            self.assertIsInstance(trigger.target_feature, str)
            self.assertIsInstance(trigger.conditions, list)
            self.assertIsInstance(trigger.priority, int)
            self.assertIsInstance(trigger.active, bool)
    
    def test_triggers_structure(self):
        """Test that triggers have correct structure"""
        expected_trigger_types = [
            TriggerType.ACTION_BASED,
            TriggerType.MILESTONE_BASED,
            TriggerType.TIME_BASED,
            TriggerType.ENGAGEMENT_BASED,
            TriggerType.ACTIVITY_BASED,
            TriggerType.GOAL_BASED,
            TriggerType.STREAK_BASED,
            TriggerType.PERFORMANCE_BASED
        ]
        
        # Check that we have triggers for each type
        trigger_types = set()
        for trigger in self.feature_triggers.triggers.values():
            trigger_types.add(trigger.trigger_type)
        
        for expected_type in expected_trigger_types:
            self.assertIn(expected_type, trigger_types)
    
    def test_trigger_conditions_structure(self):
        """Test that trigger conditions have correct structure"""
        for trigger_id, trigger in self.feature_triggers.triggers.items():
            for condition in trigger.conditions:
                self.assertIsInstance(condition, TriggerCondition)
                self.assertIsInstance(condition.condition_id, str)
                self.assertIsInstance(condition.condition_type, str)
                self.assertIsInstance(condition.parameters, dict)
                self.assertIsInstance(condition.operator, str)
                self.assertIsInstance(condition.required, bool)
    
    @patch.object(ProgressiveFeatureTriggers, 'progress_tracker')
    def test_check_triggers_no_progress(self, mock_progress_tracker):
        """Test trigger checking when no progress exists"""
        mock_progress_tracker.get_progress.return_value = None
        
        triggered_events = self.feature_triggers.check_triggers(self.user_id)
        
        self.assertEqual(triggered_events, [])
    
    @patch.object(ProgressiveFeatureTriggers, 'progress_tracker')
    @patch.object(ProgressiveFeatureTriggers, '_check_trigger_conditions')
    @patch.object(ProgressiveFeatureTriggers, '_can_trigger')
    @patch.object(ProgressiveFeatureTriggers, '_execute_trigger')
    def test_check_triggers_success(self, mock_execute, mock_can_trigger, mock_check_conditions, mock_progress_tracker):
        """Test successful trigger checking"""
        # Mock progress data
        mock_progress = MagicMock()
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock trigger conditions met
        mock_check_conditions.return_value = True
        
        # Mock trigger can execute
        mock_can_trigger.return_value = True
        
        # Mock trigger execution
        mock_trigger_event = TriggerEvent(
            event_id='test_event',
            user_id=self.user_id,
            trigger_id='strava_connected',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='activity_viewer',
            success=True
        )
        mock_execute.return_value = mock_trigger_event
        
        triggered_events = self.feature_triggers.check_triggers(self.user_id)
        
        self.assertIsInstance(triggered_events, list)
        self.assertGreater(len(triggered_events), 0)
        mock_execute.assert_called()
    
    def test_should_evaluate_trigger_action_based(self):
        """Test trigger evaluation for action-based triggers"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature'
        )
        
        # Should evaluate for step_completed event
        should_evaluate = self.feature_triggers._should_evaluate_trigger(trigger, 'step_completed')
        self.assertTrue(should_evaluate)
        
        # Should evaluate for milestone-based event
        should_evaluate = self.feature_triggers._should_evaluate_trigger(trigger, 'milestone_reached')
        self.assertTrue(should_evaluate)
    
    def test_should_evaluate_trigger_activity_based(self):
        """Test trigger evaluation for activity-based triggers"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTIVITY_BASED,
            target_feature='test_feature'
        )
        
        # Should evaluate for activity_synced event
        should_evaluate = self.feature_triggers._should_evaluate_trigger(trigger, 'activity_synced')
        self.assertTrue(should_evaluate)
        
        # Should not evaluate for tutorial_completed event
        should_evaluate = self.feature_triggers._should_evaluate_trigger(trigger, 'tutorial_completed')
        self.assertFalse(should_evaluate)
    
    def test_should_evaluate_trigger_unknown_event(self):
        """Test trigger evaluation for unknown event types"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature'
        )
        
        # Should default to evaluating for unknown events
        should_evaluate = self.feature_triggers._should_evaluate_trigger(trigger, 'unknown_event')
        self.assertTrue(should_evaluate)
    
    @patch.object(ProgressiveFeatureTriggers, '_evaluate_condition')
    def test_check_trigger_conditions_all_met(self, mock_evaluate):
        """Test trigger conditions when all conditions are met"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            conditions=[
                TriggerCondition(condition_id='cond1', condition_type='step_completed'),
                TriggerCondition(condition_id='cond2', condition_type='progress_percentage')
            ]
        )
        
        mock_progress = MagicMock()
        mock_evaluate.return_value = True
        
        conditions_met = self.feature_triggers._check_trigger_conditions(self.user_id, trigger, mock_progress)
        
        self.assertTrue(conditions_met)
        self.assertEqual(mock_evaluate.call_count, 2)
    
    @patch.object(ProgressiveFeatureTriggers, '_evaluate_condition')
    def test_check_trigger_conditions_some_not_met(self, mock_evaluate):
        """Test trigger conditions when some conditions are not met"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            conditions=[
                TriggerCondition(condition_id='cond1', condition_type='step_completed', required=True),
                TriggerCondition(condition_id='cond2', condition_type='progress_percentage', required=False)
            ]
        )
        
        mock_progress = MagicMock()
        mock_evaluate.side_effect = [True, False]  # First condition met, second not met
        
        conditions_met = self.feature_triggers._check_trigger_conditions(self.user_id, trigger, mock_progress)
        
        self.assertTrue(conditions_met)  # Should still be True because second condition is not required
    
    @patch.object(ProgressiveFeatureTriggers, '_evaluate_condition')
    def test_check_trigger_conditions_required_not_met(self, mock_evaluate):
        """Test trigger conditions when required condition is not met"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            conditions=[
                TriggerCondition(condition_id='cond1', condition_type='step_completed', required=True),
                TriggerCondition(condition_id='cond2', condition_type='progress_percentage', required=True)
            ]
        )
        
        mock_progress = MagicMock()
        mock_evaluate.side_effect = [True, False]  # First condition met, second not met
        
        conditions_met = self.feature_triggers._check_trigger_conditions(self.user_id, trigger, mock_progress)
        
        self.assertFalse(conditions_met)  # Should be False because second condition is required and not met
    
    def test_evaluate_step_completed_condition_met(self):
        """Test step completed condition evaluation when condition is met"""
        condition = TriggerCondition(
            condition_id='strava_step_completed',
            condition_type='step_completed',
            parameters={'step': OnboardingStep.STRAVA_CONNECTED.value},
            operator='equals',
            value=True
        )
        
        mock_progress = MagicMock()
        mock_progress.completed_steps = [OnboardingStep.STRAVA_CONNECTED]
        
        result = self.feature_triggers._evaluate_step_completed_condition(condition, mock_progress)
        
        self.assertTrue(result)
    
    def test_evaluate_step_completed_condition_not_met(self):
        """Test step completed condition evaluation when condition is not met"""
        condition = TriggerCondition(
            condition_id='strava_step_completed',
            condition_type='step_completed',
            parameters={'step': OnboardingStep.STRAVA_CONNECTED.value},
            operator='equals',
            value=True
        )
        
        mock_progress = MagicMock()
        mock_progress.completed_steps = []  # No completed steps
        
        result = self.feature_triggers._evaluate_step_completed_condition(condition, mock_progress)
        
        self.assertFalse(result)
    
    def test_evaluate_progress_percentage_condition_greater_than_or_equal(self):
        """Test progress percentage condition evaluation with greater_than_or_equal operator"""
        condition = TriggerCondition(
            condition_id='progress_percentage',
            condition_type='progress_percentage',
            operator='greater_than_or_equal',
            value=50.0
        )
        
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 75.0
        
        result = self.feature_triggers._evaluate_progress_percentage_condition(condition, mock_progress)
        
        self.assertTrue(result)
    
    def test_evaluate_progress_percentage_condition_equals(self):
        """Test progress percentage condition evaluation with equals operator"""
        condition = TriggerCondition(
            condition_id='progress_percentage',
            condition_type='progress_percentage',
            operator='equals',
            value=100.0
        )
        
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 100.0
        
        result = self.feature_triggers._evaluate_progress_percentage_condition(condition, mock_progress)
        
        self.assertTrue(result)
    
    @patch.object(ProgressiveFeatureTriggers, 'tiered_feature_manager')
    def test_evaluate_activity_count_condition(self, mock_tiered_manager):
        """Test activity count condition evaluation"""
        condition = TriggerCondition(
            condition_id='activity_count',
            condition_type='activity_count',
            operator='greater_than_or_equal',
            value=5
        )
        
        mock_tiered_manager._get_user_activity_count.return_value = 10
        
        result = self.feature_triggers._evaluate_activity_count_condition(condition, self.user_id)
        
        self.assertTrue(result)
        mock_tiered_manager._get_user_activity_count.assert_called_once_with(self.user_id)
    
    def test_evaluate_days_since_join_condition(self):
        """Test days since join condition evaluation"""
        condition = TriggerCondition(
            condition_id='days_since_join',
            condition_type='days_since_join',
            operator='greater_than_or_equal',
            value=7
        )
        
        result = self.feature_triggers._evaluate_days_since_join_condition(condition, self.user_id)
        
        # Should return False because placeholder value is 1, which is less than 7
        self.assertFalse(result)
    
    def test_evaluate_tutorials_completed_condition(self):
        """Test tutorials completed condition evaluation"""
        condition = TriggerCondition(
            condition_id='tutorials_completed',
            condition_type='tutorials_completed',
            operator='greater_than_or_equal',
            value=3
        )
        
        result = self.feature_triggers._evaluate_tutorials_completed_condition(condition, self.user_id)
        
        # Should return False because placeholder value is 0, which is less than 3
        self.assertFalse(result)
    
    def test_evaluate_goals_achieved_condition(self):
        """Test goals achieved condition evaluation"""
        condition = TriggerCondition(
            condition_id='goals_achieved',
            condition_type='goals_achieved',
            operator='greater_than_or_equal',
            value=1
        )
        
        result = self.feature_triggers._evaluate_goals_achieved_condition(condition, self.user_id)
        
        # Should return False because placeholder value is 0, which is less than 1
        self.assertFalse(result)
    
    def test_evaluate_activity_streak_condition(self):
        """Test activity streak condition evaluation"""
        condition = TriggerCondition(
            condition_id='activity_streak',
            condition_type='activity_streak',
            operator='greater_than_or_equal',
            value=3
        )
        
        result = self.feature_triggers._evaluate_activity_streak_condition(condition, self.user_id)
        
        # Should return False because placeholder value is 0, which is less than 3
        self.assertFalse(result)
    
    def test_evaluate_personal_best_condition(self):
        """Test personal best condition evaluation"""
        condition = TriggerCondition(
            condition_id='personal_best_achieved',
            condition_type='personal_best_achieved',
            operator='equals',
            value=True
        )
        
        result = self.feature_triggers._evaluate_personal_best_condition(condition, self.user_id)
        
        # Should return False because placeholder value is False
        self.assertFalse(result)
    
    def test_evaluate_improvement_streak_condition(self):
        """Test improvement streak condition evaluation"""
        condition = TriggerCondition(
            condition_id='improvement_streak',
            condition_type='improvement_streak',
            operator='greater_than_or_equal',
            value=3
        )
        
        result = self.feature_triggers._evaluate_improvement_streak_condition(condition, self.user_id)
        
        # Should return False because placeholder value is 0, which is less than 3
        self.assertFalse(result)
    
    def test_can_trigger_no_cooldown_no_max(self):
        """Test trigger availability with no cooldown and no max triggers"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            cooldown_period=0,
            max_triggers=0
        )
        
        can_trigger = self.feature_triggers._can_trigger(self.user_id, trigger)
        
        self.assertTrue(can_trigger)
    
    def test_can_trigger_with_cooldown(self):
        """Test trigger availability with cooldown period"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            cooldown_period=3600,  # 1 hour
            max_triggers=1
        )
        
        # Mock last trigger time to be recent
        with patch.object(self.feature_triggers, '_get_last_trigger_time') as mock_last_time:
            mock_last_time.return_value = datetime.now() - timedelta(minutes=30)  # 30 minutes ago
            
            can_trigger = self.feature_triggers._can_trigger(self.user_id, trigger)
            
            self.assertFalse(can_trigger)  # Should be False because cooldown hasn't passed
    
    def test_can_trigger_with_max_triggers(self):
        """Test trigger availability with max triggers"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            cooldown_period=0,
            max_triggers=1
        )
        
        # Mock trigger count to be at max
        with patch.object(self.feature_triggers, '_get_trigger_count') as mock_count:
            mock_count.return_value = 1
            
            can_trigger = self.feature_triggers._can_trigger(self.user_id, trigger)
            
            self.assertFalse(can_trigger)  # Should be False because max triggers reached
    
    @patch.object(ProgressiveFeatureTriggers, 'tiered_feature_manager')
    @patch.object(ProgressiveFeatureTriggers, '_save_trigger_event')
    def test_execute_trigger_success(self, mock_save, mock_tiered_manager):
        """Test successful trigger execution"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature'
        )
        
        mock_tiered_manager.unlock_feature.return_value = True
        
        trigger_event = self.feature_triggers._execute_trigger(self.user_id, trigger)
        
        self.assertIsNotNone(trigger_event)
        self.assertEqual(trigger_event.user_id, self.user_id)
        self.assertEqual(trigger_event.trigger_id, trigger.trigger_id)
        self.assertEqual(trigger_event.target_feature, trigger.target_feature)
        self.assertTrue(trigger_event.success)
        self.assertIsNone(trigger_event.error_message)
        
        mock_tiered_manager.unlock_feature.assert_called_once_with(self.user_id, trigger.target_feature)
        mock_save.assert_called_once()
    
    @patch.object(ProgressiveFeatureTriggers, 'tiered_feature_manager')
    @patch.object(ProgressiveFeatureTriggers, '_save_trigger_event')
    def test_execute_trigger_failure(self, mock_save, mock_tiered_manager):
        """Test failed trigger execution"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature'
        )
        
        mock_tiered_manager.unlock_feature.return_value = False
        
        trigger_event = self.feature_triggers._execute_trigger(self.user_id, trigger)
        
        self.assertIsNotNone(trigger_event)
        self.assertFalse(trigger_event.success)
        self.assertEqual(trigger_event.error_message, "Feature unlock failed")
        
        mock_tiered_manager.unlock_feature.assert_called_once_with(self.user_id, trigger.target_feature)
        mock_save.assert_called_once()
    
    @patch.object(ProgressiveFeatureTriggers, 'progress_tracker')
    def test_get_user_triggers(self, mock_progress_tracker):
        """Test getting user triggers"""
        # Mock progress data
        mock_progress = MagicMock()
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock trigger status
        with patch.object(self.feature_triggers, '_get_trigger_status') as mock_status:
            mock_status.return_value = TriggerStatus.ACTIVE
            
            user_triggers = self.feature_triggers.get_user_triggers(self.user_id)
            
            self.assertIsInstance(user_triggers, list)
            self.assertGreater(len(user_triggers), 0)
            
            for trigger_info in user_triggers:
                self.assertIn('trigger_id', trigger_info)
                self.assertIn('name', trigger_info)
                self.assertIn('description', trigger_info)
                self.assertIn('trigger_type', trigger_info)
                self.assertIn('target_feature', trigger_info)
                self.assertIn('priority', trigger_info)
                self.assertIn('status', trigger_info)
                self.assertIn('conditions', trigger_info)
    
    def test_get_trigger_status_triggered(self):
        """Test trigger status when trigger has been triggered"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            max_triggers=1
        )
        
        mock_progress = MagicMock()
        
        # Mock trigger count to be at max
        with patch.object(self.feature_triggers, '_get_trigger_count') as mock_count:
            mock_count.return_value = 1
            
            status = self.feature_triggers._get_trigger_status(self.user_id, trigger, mock_progress)
            
            self.assertEqual(status, TriggerStatus.TRIGGERED)
    
    def test_get_trigger_status_active(self):
        """Test trigger status when trigger is active"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            max_triggers=1
        )
        
        mock_progress = MagicMock()
        
        # Mock trigger count to be below max
        with patch.object(self.feature_triggers, '_get_trigger_count') as mock_count:
            mock_count.return_value = 0
            
            # Mock conditions are met
            with patch.object(self.feature_triggers, '_check_trigger_conditions') as mock_conditions:
                mock_conditions.return_value = True
                
                status = self.feature_triggers._get_trigger_status(self.user_id, trigger, mock_progress)
                
                self.assertEqual(status, TriggerStatus.ACTIVE)
    
    def test_get_trigger_status_inactive(self):
        """Test trigger status when trigger is inactive"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            max_triggers=1
        )
        
        mock_progress = MagicMock()
        
        # Mock trigger count to be below max
        with patch.object(self.feature_triggers, '_get_trigger_count') as mock_count:
            mock_count.return_value = 0
            
            # Mock conditions are not met
            with patch.object(self.feature_triggers, '_check_trigger_conditions') as mock_conditions:
                mock_conditions.return_value = False
                
                status = self.feature_triggers._get_trigger_status(self.user_id, trigger, mock_progress)
                
                self.assertEqual(status, TriggerStatus.INACTIVE)
    
    def test_get_trigger_analytics(self):
        """Test getting trigger analytics"""
        analytics = self.feature_triggers.get_trigger_analytics('test_trigger')
        
        self.assertIsNotNone(analytics)
        self.assertIsInstance(analytics, TriggerAnalytics)
        self.assertEqual(analytics.trigger_id, 'test_trigger')
        self.assertIsInstance(analytics.total_events, int)
        self.assertIsInstance(analytics.successful_triggers, int)
        self.assertIsInstance(analytics.failed_triggers, int)
        self.assertIsInstance(analytics.average_trigger_time, float)
        self.assertIsInstance(analytics.success_rate, float)
        self.assertIsInstance(analytics.most_common_conditions, list)
        self.assertIsInstance(analytics.effectiveness_score, float)
    
    @patch('progressive_feature_triggers.USE_POSTGRES', True)
    @patch('progressive_feature_triggers.get_db_connection')
    def test_postgresql_save_trigger_event(self, mock_db):
        """Test PostgreSQL save trigger event query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        trigger_event = TriggerEvent(
            event_id='test_event',
            user_id=self.user_id,
            trigger_id='test_trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            success=True
        )
        
        self.feature_triggers._save_trigger_event(trigger_event)
        
        # Verify PostgreSQL query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("INSERT INTO user_settings", call_args[0][0])
        self.assertIn("trigger_events", call_args[0][0])
    
    @patch('progressive_feature_triggers.USE_POSTGRES', False)
    @patch('progressive_feature_triggers.get_db_connection')
    def test_sqlite_save_trigger_event(self, mock_db):
        """Test SQLite save trigger event query format"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.__enter__.return_value = mock_conn
        
        trigger_event = TriggerEvent(
            event_id='test_event',
            user_id=self.user_id,
            trigger_id='test_trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            success=True
        )
        
        self.feature_triggers._save_trigger_event(trigger_event)
        
        # Verify SQLite query format
        mock_cursor.execute.assert_called_once()
        call_args = mock_cursor.execute.call_args
        self.assertIn("INSERT OR REPLACE INTO user_settings", call_args[0][0])
        self.assertIn("trigger_events", call_args[0][0])
    
    def test_get_last_trigger_time(self):
        """Test getting last trigger time"""
        last_time = self.feature_triggers._get_last_trigger_time(self.user_id, 'test_trigger')
        
        # Should return None as placeholder implementation
        self.assertIsNone(last_time)
    
    def test_get_trigger_count(self):
        """Test getting trigger count"""
        count = self.feature_triggers._get_trigger_count(self.user_id, 'test_trigger')
        
        # Should return 0 as placeholder implementation
        self.assertEqual(count, 0)


class TestConvenienceFunctions(unittest.TestCase):
    """Test cases for convenience functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user_id = 1
    
    @patch.object(feature_triggers, 'check_triggers')
    def test_check_triggers_function(self, mock_check):
        """Test convenience function for checking triggers"""
        mock_events = [TriggerEvent(
            event_id='test_event',
            user_id=self.user_id,
            trigger_id='test_trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            success=True
        )]
        mock_check.return_value = mock_events
        
        events = check_triggers(self.user_id, 'step_completed', {'step': 'welcome'})
        
        self.assertEqual(events, mock_events)
        mock_check.assert_called_once_with(self.user_id, 'step_completed', {'step': 'welcome'})
    
    @patch.object(feature_triggers, 'get_user_triggers')
    def test_get_user_triggers_function(self, mock_get):
        """Test convenience function for getting user triggers"""
        mock_triggers = [{'trigger_id': 'test_trigger', 'name': 'Test Trigger'}]
        mock_get.return_value = mock_triggers
        
        triggers = get_user_triggers(self.user_id)
        
        self.assertEqual(triggers, mock_triggers)
        mock_get.assert_called_once_with(self.user_id)
    
    @patch.object(feature_triggers, 'get_trigger_analytics')
    def test_get_trigger_analytics_function(self, mock_analytics):
        """Test convenience function for getting trigger analytics"""
        mock_analytics_obj = TriggerAnalytics(trigger_id='test_trigger')
        mock_analytics.return_value = mock_analytics_obj
        
        analytics = get_trigger_analytics('test_trigger')
        
        self.assertEqual(analytics, mock_analytics_obj)
        mock_analytics.assert_called_once_with('test_trigger')


class TestEnumsAndDataClasses(unittest.TestCase):
    """Test cases for enums and data classes"""
    
    def test_trigger_type_enum(self):
        """Test TriggerType enum values"""
        self.assertEqual(TriggerType.ACTION_BASED.value, 'action_based')
        self.assertEqual(TriggerType.MILESTONE_BASED.value, 'milestone_based')
        self.assertEqual(TriggerType.TIME_BASED.value, 'time_based')
        self.assertEqual(TriggerType.ENGAGEMENT_BASED.value, 'engagement_based')
        self.assertEqual(TriggerType.ACHIEVEMENT_BASED.value, 'achievement_based')
        self.assertEqual(TriggerType.SOCIAL_BASED.value, 'social_based')
        self.assertEqual(TriggerType.ACTIVITY_BASED.value, 'activity_based')
        self.assertEqual(TriggerType.GOAL_BASED.value, 'goal_based')
        self.assertEqual(TriggerType.TUTORIAL_BASED.value, 'tutorial_based')
        self.assertEqual(TriggerType.STREAK_BASED.value, 'streak_based')
        self.assertEqual(TriggerType.PERFORMANCE_BASED.value, 'performance_based')
        self.assertEqual(TriggerType.CUSTOM.value, 'custom')
    
    def test_trigger_status_enum(self):
        """Test TriggerStatus enum values"""
        self.assertEqual(TriggerStatus.ACTIVE.value, 'active')
        self.assertEqual(TriggerStatus.INACTIVE.value, 'inactive')
        self.assertEqual(TriggerStatus.TRIGGERED.value, 'triggered')
        self.assertEqual(TriggerStatus.EXPIRED.value, 'expired')
        self.assertEqual(TriggerStatus.DISABLED.value, 'disabled')
    
    def test_trigger_condition_dataclass(self):
        """Test TriggerCondition dataclass"""
        condition = TriggerCondition(
            condition_id='test_condition',
            condition_type='step_completed',
            parameters={'step': 'welcome'},
            operator='equals',
            value=True,
            required=True
        )
        
        self.assertEqual(condition.condition_id, 'test_condition')
        self.assertEqual(condition.condition_type, 'step_completed')
        self.assertEqual(condition.parameters, {'step': 'welcome'})
        self.assertEqual(condition.operator, 'equals')
        self.assertEqual(condition.value, True)
        self.assertTrue(condition.required)
    
    def test_feature_unlock_trigger_dataclass(self):
        """Test FeatureUnlockTrigger dataclass"""
        trigger = FeatureUnlockTrigger(
            trigger_id='test_trigger',
            name='Test Trigger',
            description='Test trigger description',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            conditions=[TriggerCondition(condition_id='cond1', condition_type='step_completed')],
            priority=100,
            cooldown_period=3600,
            max_triggers=1,
            active=True
        )
        
        self.assertEqual(trigger.trigger_id, 'test_trigger')
        self.assertEqual(trigger.name, 'Test Trigger')
        self.assertEqual(trigger.description, 'Test trigger description')
        self.assertEqual(trigger.trigger_type, TriggerType.ACTION_BASED)
        self.assertEqual(trigger.target_feature, 'test_feature')
        self.assertEqual(len(trigger.conditions), 1)
        self.assertEqual(trigger.priority, 100)
        self.assertEqual(trigger.cooldown_period, 3600)
        self.assertEqual(trigger.max_triggers, 1)
        self.assertTrue(trigger.active)
        self.assertIsInstance(trigger.created_at, datetime)
        self.assertIsInstance(trigger.updated_at, datetime)
    
    def test_trigger_event_dataclass(self):
        """Test TriggerEvent dataclass"""
        event = TriggerEvent(
            event_id='test_event',
            user_id=1,
            trigger_id='test_trigger',
            trigger_type=TriggerType.ACTION_BASED,
            target_feature='test_feature',
            event_data={'step': 'welcome'},
            success=True,
            error_message=None
        )
        
        self.assertEqual(event.event_id, 'test_event')
        self.assertEqual(event.user_id, 1)
        self.assertEqual(event.trigger_id, 'test_trigger')
        self.assertEqual(event.trigger_type, TriggerType.ACTION_BASED)
        self.assertEqual(event.target_feature, 'test_feature')
        self.assertEqual(event.event_data, {'step': 'welcome'})
        self.assertTrue(event.success)
        self.assertIsNone(event.error_message)
        self.assertIsInstance(event.triggered_at, datetime)
    
    def test_trigger_analytics_dataclass(self):
        """Test TriggerAnalytics dataclass"""
        analytics = TriggerAnalytics(
            trigger_id='test_trigger',
            total_events=100,
            successful_triggers=90,
            failed_triggers=10,
            average_trigger_time=2.5,
            success_rate=0.9,
            last_triggered=datetime.now(),
            most_common_conditions=['step_completed', 'progress_percentage'],
            effectiveness_score=0.85
        )
        
        self.assertEqual(analytics.trigger_id, 'test_trigger')
        self.assertEqual(analytics.total_events, 100)
        self.assertEqual(analytics.successful_triggers, 90)
        self.assertEqual(analytics.failed_triggers, 10)
        self.assertEqual(analytics.average_trigger_time, 2.5)
        self.assertEqual(analytics.success_rate, 0.9)
        self.assertIsInstance(analytics.last_triggered, datetime)
        self.assertEqual(analytics.most_common_conditions, ['step_completed', 'progress_percentage'])
        self.assertEqual(analytics.effectiveness_score, 0.85)


class TestTriggerIntegration(unittest.TestCase):
    """Integration tests for trigger functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.feature_triggers = ProgressiveFeatureTriggers()
        self.user_id = 1
    
    @patch.object(ProgressiveFeatureTriggers, 'progress_tracker')
    @patch.object(ProgressiveFeatureTriggers, 'tiered_feature_manager')
    def test_complete_trigger_integration(self, mock_tiered_manager, mock_progress_tracker):
        """Test complete trigger integration"""
        # Mock progress data
        mock_progress = MagicMock()
        mock_progress.progress_percentage = 100.0
        mock_progress.completed_steps = [OnboardingStep.WELCOME, OnboardingStep.STRAVA_CONNECTED]
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock feature unlock
        mock_tiered_manager.unlock_feature.return_value = True
        mock_tiered_manager._get_user_activity_count.return_value = 15
        
        # Mock database operations
        with patch.object(self.feature_triggers, '_save_trigger_event'):
            with patch.object(self.feature_triggers, '_get_last_trigger_time', return_value=None):
                with patch.object(self.feature_triggers, '_get_trigger_count', return_value=0):
                    # Check triggers
                    triggered_events = self.feature_triggers.check_triggers(self.user_id, 'step_completed')
                    
                    # Should have triggered events
                    self.assertIsInstance(triggered_events, list)
                    
                    # Verify feature unlock was called
                    mock_tiered_manager.unlock_feature.assert_called()
                    
                    # Verify progress tracking was updated
                    mock_progress_tracker.update_progress.assert_called()
    
    def test_trigger_priority_sorting(self):
        """Test that triggers are sorted by priority"""
        # Get user triggers
        with patch.object(self.feature_triggers, 'progress_tracker') as mock_progress_tracker:
            mock_progress = MagicMock()
            mock_progress_tracker.get_progress.return_value = mock_progress
            
            with patch.object(self.feature_triggers, '_get_trigger_status') as mock_status:
                mock_status.return_value = TriggerStatus.ACTIVE
                
                user_triggers = self.feature_triggers.get_user_triggers(self.user_id)
                
                # Verify triggers are sorted by priority (higher first)
                priorities = [trigger['priority'] for trigger in user_triggers]
                self.assertEqual(priorities, sorted(priorities, reverse=True))


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)


