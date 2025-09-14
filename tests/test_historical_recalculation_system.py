#!/usr/bin/env python3
"""
Test suite for the historical TRIMP recalculation system
Tests the batch processing, progress tracking, and data validation functionality
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from historical_trimp_recalculation import (
    HistoricalTrimpRecalculator, 
    RecalculationStatus, 
    RecalculationOperation,
    RecalculationResult,
    BatchRecalculationResult
)


class TestHistoricalTrimpRecalculator(unittest.TestCase):
    """Test cases for the HistoricalTrimpRecalculator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.recalculator = HistoricalTrimpRecalculator()
        
        # Mock activity data
        self.sample_activity = {
            'activity_id': 12345,
            'user_id': 1,
            'trimp': 100.0,
            'duration_minutes': 60.0,
            'avg_heart_rate': 140,
            'trimp_calculation_method': 'average',
            'trimp_processed_at': None
        }
        
        # Mock HR config
        self.hr_config = {
            'resting_hr': 50,
            'max_hr': 180,
            'gender': 'male'
        }
    
    def test_recalculator_initialization(self):
        """Test that the recalculator initializes correctly"""
        self.assertEqual(self.recalculator.batch_size, 10)
        self.assertEqual(self.recalculator.max_processing_time_ms, 30000)
        self.assertIsInstance(self.recalculator._active_operations, dict)
    
    @patch('historical_trimp_recalculation.get_activities_needing_trimp_recalculation')
    def test_recalculate_activities_batch_no_activities(self, mock_get_activities):
        """Test batch recalculation when no activities need recalculation"""
        mock_get_activities.return_value = []
        
        result = self.recalculator.recalculate_activities_batch()
        
        self.assertEqual(result.total_activities, 0)
        self.assertEqual(result.processed_count, 0)
        self.assertEqual(result.success_count, 0)
        self.assertEqual(result.error_count, 0)
        self.assertEqual(result.skipped_count, 0)
        self.assertEqual(len(result.results), 0)
        self.assertEqual(len(result.errors), 0)
    
    @patch('historical_trimp_recalculation.get_activities_needing_trimp_recalculation')
    def test_recalculate_activities_batch_with_activities(self, mock_get_activities):
        """Test batch recalculation with activities"""
        mock_get_activities.return_value = [self.sample_activity]
        
        with patch.object(self.recalculator, '_recalculate_single_activity') as mock_recalc:
            mock_recalc.return_value = RecalculationResult(
                activity_id=12345,
                user_id=1,
                success=True,
                old_trimp=100.0,
                new_trimp=120.0,
                calculation_method='stream',
                hr_samples_used=600,
                processing_time_ms=100
            )
            
            result = self.recalculator.recalculate_activities_batch()
            
            self.assertEqual(result.total_activities, 1)
            self.assertEqual(result.processed_count, 1)
            self.assertEqual(result.success_count, 1)
            self.assertEqual(result.error_count, 0)
            self.assertEqual(len(result.results), 1)
    
    def test_should_recalculate_already_enhanced(self):
        """Test that activities already using enhanced method are skipped"""
        activity = self.sample_activity.copy()
        activity['trimp_calculation_method'] = 'stream'
        
        should_recalc = self.recalculator._should_recalculate(activity)
        self.assertFalse(should_recalc)
    
    def test_should_recalculate_recently_processed(self):
        """Test that recently processed activities are skipped"""
        activity = self.sample_activity.copy()
        activity['trimp_processed_at'] = datetime.now().isoformat()
        
        should_recalc = self.recalculator._should_recalculate(activity)
        self.assertFalse(should_recalc)
    
    def test_should_recalculate_old_processed(self):
        """Test that old processed activities are recalculated"""
        activity = self.sample_activity.copy()
        activity['trimp_processed_at'] = (datetime.now() - timedelta(days=2)).isoformat()
        
        should_recalc = self.recalculator._should_recalculate(activity)
        self.assertTrue(should_recalc)
    
    def test_should_recalculate_never_processed(self):
        """Test that never processed activities are recalculated"""
        activity = self.sample_activity.copy()
        activity['trimp_processed_at'] = None
        
        should_recalc = self.recalculator._should_recalculate(activity)
        self.assertTrue(should_recalc)
    
    def test_validate_activity_data_valid(self):
        """Test activity data validation with valid data"""
        result = self.recalculator._validate_activity_data(self.sample_activity)
        
        self.assertTrue(result['valid'])
        self.assertIsNone(result.get('error'))
    
    def test_validate_activity_data_missing_fields(self):
        """Test activity data validation with missing required fields"""
        invalid_activity = {'activity_id': 12345}  # Missing user_id
        
        result = self.recalculator._validate_activity_data(invalid_activity)
        
        self.assertFalse(result['valid'])
        self.assertIn('Missing required field', result['error'])
    
    def test_validate_activity_data_invalid_activity_id(self):
        """Test activity data validation with invalid activity ID"""
        invalid_activity = self.sample_activity.copy()
        invalid_activity['activity_id'] = -1
        
        result = self.recalculator._validate_activity_data(invalid_activity)
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid activity_id', result['error'])
    
    def test_validate_activity_data_invalid_duration(self):
        """Test activity data validation with invalid duration"""
        invalid_activity = self.sample_activity.copy()
        invalid_activity['duration_minutes'] = -10
        
        result = self.recalculator._validate_activity_data(invalid_activity)
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid duration_minutes', result['error'])
    
    def test_validate_activity_data_invalid_heart_rate(self):
        """Test activity data validation with invalid heart rate"""
        invalid_activity = self.sample_activity.copy()
        invalid_activity['avg_heart_rate'] = 300  # Too high
        
        result = self.recalculator._validate_activity_data(invalid_activity)
        
        self.assertFalse(result['valid'])
        self.assertIn('avg_heart_rate outside physiological range', result['error'])
    
    def test_validate_hr_config_valid(self):
        """Test HR configuration validation with valid data"""
        result = self.recalculator._validate_hr_config(self.hr_config)
        
        self.assertTrue(result['valid'])
        self.assertIsNone(result.get('error'))
    
    def test_validate_hr_config_missing_fields(self):
        """Test HR configuration validation with missing fields"""
        invalid_config = {'resting_hr': 50}  # Missing max_hr and gender
        
        result = self.recalculator._validate_hr_config(invalid_config)
        
        self.assertFalse(result['valid'])
        self.assertIn('Missing HR config field', result['error'])
    
    def test_validate_hr_config_invalid_resting_hr(self):
        """Test HR configuration validation with invalid resting HR"""
        invalid_config = self.hr_config.copy()
        invalid_config['resting_hr'] = 150  # Too high
        
        result = self.recalculator._validate_hr_config(invalid_config)
        
        self.assertFalse(result['valid'])
        self.assertIn('resting_hr outside physiological range', result['error'])
    
    def test_validate_hr_config_invalid_max_hr(self):
        """Test HR configuration validation with invalid max HR"""
        invalid_config = self.hr_config.copy()
        invalid_config['max_hr'] = 50  # Too low
        
        result = self.recalculator._validate_hr_config(invalid_config)
        
        self.assertFalse(result['valid'])
        self.assertIn('max_hr outside physiological range', result['error'])
    
    def test_validate_hr_config_max_hr_less_than_resting(self):
        """Test HR configuration validation when max HR is less than resting HR"""
        invalid_config = self.hr_config.copy()
        invalid_config['resting_hr'] = 100
        invalid_config['max_hr'] = 80
        
        result = self.recalculator._validate_hr_config(invalid_config)
        
        self.assertFalse(result['valid'])
        self.assertIn('max_hr must be greater than resting_hr', result['error'])
    
    def test_validate_hr_config_invalid_gender(self):
        """Test HR configuration validation with invalid gender"""
        invalid_config = self.hr_config.copy()
        invalid_config['gender'] = 'other'
        
        result = self.recalculator._validate_hr_config(invalid_config)
        
        self.assertFalse(result['valid'])
        self.assertIn('Invalid gender', result['error'])
    
    def test_validate_trimp_result_valid(self):
        """Test TRIMP result validation with valid result"""
        result = self.recalculator._validate_trimp_result(
            old_trimp=100.0,
            new_trimp=120.0,
            activity=self.sample_activity,
            load_data={'hr_stream_used': True}
        )
        
        self.assertTrue(result['valid'])
    
    def test_validate_trimp_result_negative(self):
        """Test TRIMP result validation with negative result"""
        result = self.recalculator._validate_trimp_result(
            old_trimp=100.0,
            new_trimp=-10.0,
            activity=self.sample_activity,
            load_data={'hr_stream_used': True}
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('negative', result['warning'])
    
    def test_validate_trimp_result_too_high(self):
        """Test TRIMP result validation with unreasonably high result"""
        result = self.recalculator._validate_trimp_result(
            old_trimp=100.0,
            new_trimp=15000.0,
            activity=self.sample_activity,
            load_data={'hr_stream_used': True}
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('unreasonably high', result['warning'])
    
    def test_validate_trimp_result_large_increase(self):
        """Test TRIMP result validation with large increase"""
        result = self.recalculator._validate_trimp_result(
            old_trimp=100.0,
            new_trimp=600.0,  # 6x increase
            activity=self.sample_activity,
            load_data={'hr_stream_used': True}
        )
        
        self.assertTrue(result['valid'])  # Should be valid but with warning
        self.assertIn('Large TRIMP increase', result['warning'])
    
    def test_validate_trimp_result_large_decrease(self):
        """Test TRIMP result validation with large decrease"""
        result = self.recalculator._validate_trimp_result(
            old_trimp=100.0,
            new_trimp=15.0,  # 85% decrease
            activity=self.sample_activity,
            load_data={'hr_stream_used': True}
        )
        
        self.assertTrue(result['valid'])  # Should be valid but with warning
        self.assertIn('Large TRIMP decrease', result['warning'])
    
    def test_validate_trimp_result_high_per_minute(self):
        """Test TRIMP result validation with high TRIMP per minute"""
        result = self.recalculator._validate_trimp_result(
            old_trimp=100.0,
            new_trimp=3000.0,  # 50 TRIMP per minute for 60-minute activity
            activity=self.sample_activity,
            load_data={'hr_stream_used': True}
        )
        
        self.assertTrue(result['valid'])  # Should be valid but with warning
        self.assertIn('High TRIMP per minute', result['warning'])
    
    def test_validate_trimp_result_low_per_minute(self):
        """Test TRIMP result validation with low TRIMP per minute"""
        result = self.recalculator._validate_trimp_result(
            old_trimp=100.0,
            new_trimp=3.0,  # 0.05 TRIMP per minute for 60-minute activity
            activity=self.sample_activity,
            load_data={'hr_stream_used': True}
        )
        
        self.assertTrue(result['valid'])  # Should be valid but with warning
        self.assertIn('Low TRIMP per minute', result['warning'])
    
    @patch('historical_trimp_recalculation.execute_query')
    def test_verify_database_update_success(self, mock_execute):
        """Test database update verification with successful update"""
        mock_execute.return_value = [{
            'trimp': 120.0,
            'trimp_calculation_method': 'stream',
            'hr_stream_sample_count': 600,
            'trimp_processed_at': datetime.now().isoformat()
        }]
        
        result = self.recalculator._verify_database_update(
            activity_id=12345,
            user_id=1,
            expected_trimp=120.0,
            expected_method='stream'
        )
        
        self.assertTrue(result['valid'])
    
    @patch('historical_trimp_recalculation.execute_query')
    def test_verify_database_update_trimp_mismatch(self, mock_execute):
        """Test database update verification with TRIMP mismatch"""
        mock_execute.return_value = [{
            'trimp': 100.0,  # Different from expected 120.0
            'trimp_calculation_method': 'stream',
            'hr_stream_sample_count': 600,
            'trimp_processed_at': datetime.now().isoformat()
        }]
        
        result = self.recalculator._verify_database_update(
            activity_id=12345,
            user_id=1,
            expected_trimp=120.0,
            expected_method='stream'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('TRIMP mismatch', result['error'])
    
    @patch('historical_trimp_recalculation.execute_query')
    def test_verify_database_update_method_mismatch(self, mock_execute):
        """Test database update verification with method mismatch"""
        mock_execute.return_value = [{
            'trimp': 120.0,
            'trimp_calculation_method': 'average',  # Different from expected 'stream'
            'hr_stream_sample_count': 600,
            'trimp_processed_at': datetime.now().isoformat()
        }]
        
        result = self.recalculator._verify_database_update(
            activity_id=12345,
            user_id=1,
            expected_trimp=120.0,
            expected_method='stream'
        )
        
        self.assertFalse(result['valid'])
        self.assertIn('Method mismatch', result['error'])
    
    def test_get_operation_status_existing(self):
        """Test getting status of existing operation"""
        operation = RecalculationOperation(
            operation_id='test-op-123',
            user_id=1,
            days_back=30,
            force_recalculation=False,
            status=RecalculationStatus.IN_PROGRESS,
            total_activities=10,
            processed_count=5,
            success_count=4,
            error_count=1,
            skipped_count=0,
            started_at=datetime.now(),
            completed_at=None,
            total_processing_time_ms=1000
        )
        
        self.recalculator._active_operations['test-op-123'] = operation
        
        retrieved_operation = self.recalculator.get_operation_status('test-op-123')
        self.assertEqual(retrieved_operation, operation)
    
    def test_get_operation_status_nonexistent(self):
        """Test getting status of non-existent operation"""
        retrieved_operation = self.recalculator.get_operation_status('nonexistent-op')
        self.assertIsNone(retrieved_operation)
    
    def test_get_active_operations(self):
        """Test getting all active operations"""
        operation1 = RecalculationOperation(
            operation_id='op-1',
            user_id=1,
            days_back=30,
            force_recalculation=False,
            status=RecalculationStatus.IN_PROGRESS,
            total_activities=10,
            processed_count=5,
            success_count=4,
            error_count=1,
            skipped_count=0,
            started_at=datetime.now(),
            completed_at=None,
            total_processing_time_ms=1000
        )
        
        operation2 = RecalculationOperation(
            operation_id='op-2',
            user_id=2,
            days_back=7,
            force_recalculation=True,
            status=RecalculationStatus.COMPLETED,
            total_activities=5,
            processed_count=5,
            success_count=5,
            error_count=0,
            skipped_count=0,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            total_processing_time_ms=2000
        )
        
        self.recalculator._active_operations['op-1'] = operation1
        self.recalculator._active_operations['op-2'] = operation2
        
        active_operations = self.recalculator.get_active_operations()
        self.assertEqual(len(active_operations), 2)
        self.assertIn(operation1, active_operations)
        self.assertIn(operation2, active_operations)
    
    def test_cancel_operation_success(self):
        """Test successful operation cancellation"""
        operation = RecalculationOperation(
            operation_id='cancel-test',
            user_id=1,
            days_back=30,
            force_recalculation=False,
            status=RecalculationStatus.IN_PROGRESS,
            total_activities=10,
            processed_count=5,
            success_count=4,
            error_count=1,
            skipped_count=0,
            started_at=datetime.now(),
            completed_at=None,
            total_processing_time_ms=1000
        )
        
        self.recalculator._active_operations['cancel-test'] = operation
        
        success = self.recalculator.cancel_operation('cancel-test')
        self.assertTrue(success)
        self.assertEqual(operation.status, RecalculationStatus.CANCELLED)
        self.assertIsNotNone(operation.completed_at)
    
    def test_cancel_operation_nonexistent(self):
        """Test cancelling non-existent operation"""
        success = self.recalculator.cancel_operation('nonexistent-op')
        self.assertFalse(success)
    
    def test_cancel_operation_already_completed(self):
        """Test cancelling already completed operation"""
        operation = RecalculationOperation(
            operation_id='completed-op',
            user_id=1,
            days_back=30,
            force_recalculation=False,
            status=RecalculationStatus.COMPLETED,
            total_activities=10,
            processed_count=10,
            success_count=10,
            error_count=0,
            skipped_count=0,
            started_at=datetime.now(),
            completed_at=datetime.now(),
            total_processing_time_ms=1000
        )
        
        self.recalculator._active_operations['completed-op'] = operation
        
        success = self.recalculator.cancel_operation('completed-op')
        self.assertFalse(success)
        self.assertEqual(operation.status, RecalculationStatus.COMPLETED)  # Should remain unchanged


class TestRecalculationDataStructures(unittest.TestCase):
    """Test cases for recalculation data structures"""
    
    def test_recalculation_operation_creation(self):
        """Test RecalculationOperation creation"""
        operation = RecalculationOperation(
            operation_id='test-op',
            user_id=1,
            days_back=30,
            force_recalculation=False,
            status=RecalculationStatus.IN_PROGRESS,
            total_activities=10,
            processed_count=5,
            success_count=4,
            error_count=1,
            skipped_count=0,
            started_at=datetime.now(),
            completed_at=None,
            total_processing_time_ms=1000
        )
        
        self.assertEqual(operation.operation_id, 'test-op')
        self.assertEqual(operation.user_id, 1)
        self.assertEqual(operation.status, RecalculationStatus.IN_PROGRESS)
        self.assertEqual(operation.total_activities, 10)
        self.assertEqual(operation.processed_count, 5)
        self.assertEqual(operation.success_count, 4)
        self.assertEqual(operation.error_count, 1)
        self.assertEqual(operation.skipped_count, 0)
    
    def test_recalculation_result_creation(self):
        """Test RecalculationResult creation"""
        result = RecalculationResult(
            activity_id=12345,
            user_id=1,
            success=True,
            old_trimp=100.0,
            new_trimp=120.0,
            calculation_method='stream',
            hr_samples_used=600,
            processing_time_ms=100
        )
        
        self.assertEqual(result.activity_id, 12345)
        self.assertEqual(result.user_id, 1)
        self.assertTrue(result.success)
        self.assertEqual(result.old_trimp, 100.0)
        self.assertEqual(result.new_trimp, 120.0)
        self.assertEqual(result.calculation_method, 'stream')
        self.assertEqual(result.hr_samples_used, 600)
        self.assertEqual(result.processing_time_ms, 100)
    
    def test_batch_recalculation_result_creation(self):
        """Test BatchRecalculationResult creation"""
        results = [
            RecalculationResult(
                activity_id=12345,
                user_id=1,
                success=True,
                old_trimp=100.0,
                new_trimp=120.0,
                calculation_method='stream',
                hr_samples_used=600,
                processing_time_ms=100
            )
        ]
        
        batch_result = BatchRecalculationResult(
            total_activities=1,
            processed_count=1,
            success_count=1,
            error_count=0,
            skipped_count=0,
            results=results,
            total_processing_time_ms=1000,
            errors=[]
        )
        
        self.assertEqual(batch_result.total_activities, 1)
        self.assertEqual(batch_result.processed_count, 1)
        self.assertEqual(batch_result.success_count, 1)
        self.assertEqual(batch_result.error_count, 0)
        self.assertEqual(batch_result.skipped_count, 0)
        self.assertEqual(len(batch_result.results), 1)
        self.assertEqual(len(batch_result.errors), 0)
        self.assertEqual(batch_result.total_processing_time_ms, 1000)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
