#!/usr/bin/env python3
"""
Test script for ACWR Migration Service
Tests the migration service functionality for batch processing historical data
"""

import sys
import os
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import json

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock database dependencies before importing
with patch.dict('sys.modules', {
    'db_utils': Mock(),
    'psycopg2': Mock(),
    'psycopg2.extras': Mock()
}):
    from acwr_migration_service import (
        ACWRMigrationService, MigrationProgress, MigrationResult, BatchResult
    )

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestACWRMigrationService(unittest.TestCase):
    """Test cases for ACWR Migration Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.migration_service = ACWRMigrationService()
        
        # Mock dependencies
        self.migration_service.config_service = Mock()
        self.migration_service.calc_service = Mock()
        self.migration_service.decay_engine = Mock()
        
        # Mock database connections
        self.mock_conn = Mock()
        self.mock_cursor = Mock()
        
        # Create a proper context manager mock
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        self.mock_conn.cursor.return_value = cursor_context
        
    def test_service_initialization(self):
        """Test service initialization"""
        logger.info("Testing service initialization...")
        
        # Test default configuration
        self.assertEqual(self.migration_service.batch_size, 1000)
        self.assertEqual(self.migration_service.max_workers, 4)
        self.assertEqual(self.migration_service.timeout_seconds, 300)
        
        # Test performance metrics initialization
        self.assertIn('total_migrations', self.migration_service.performance_metrics)
        self.assertIn('successful_migrations', self.migration_service.performance_metrics)
        self.assertIn('failed_migrations', self.migration_service.performance_metrics)
        self.assertIn('average_processing_time', self.migration_service.performance_metrics)
        self.assertIn('total_activities_processed', self.migration_service.performance_metrics)
        
        # Test active migrations initialization
        self.assertIsInstance(self.migration_service.active_migrations, dict)
        self.assertEqual(len(self.migration_service.active_migrations), 0)
        
        logger.info("✅ Service initialization test passed")
    
    def test_create_migration(self):
        """Test migration creation"""
        logger.info("Testing migration creation...")
        
        # Mock validation methods
        self.migration_service._validate_user_exists = Mock(return_value=True)
        self.migration_service._validate_configuration_exists = Mock(return_value=True)
        self.migration_service._get_user_activity_count = Mock(return_value=5000)
        
        # Test successful migration creation
        migration_id = self.migration_service.create_migration(
            user_id=1, configuration_id=1
        )
        
        # Verify migration ID format
        self.assertTrue(migration_id.startswith('migration_1_'))
        
        # Verify migration is stored
        self.assertIn(migration_id, self.migration_service.active_migrations)
        
        # Verify migration progress
        progress = self.migration_service.active_migrations[migration_id]
        self.assertEqual(progress.user_id, 1)
        self.assertEqual(progress.total_activities, 5000)
        self.assertEqual(progress.status, 'pending')
        self.assertEqual(progress.total_batches, 5)  # 5000 / 1000 = 5 batches
        
        logger.info("✅ Migration creation test passed")
    
    def test_create_migration_validation_errors(self):
        """Test migration creation with validation errors"""
        logger.info("Testing migration creation validation errors...")
        
        # Test user validation error
        self.migration_service._validate_user_exists = Mock(return_value=False)
        
        with self.assertRaises(ValueError) as context:
            self.migration_service.create_migration(user_id=999, configuration_id=1)
        
        self.assertIn("User 999 does not exist", str(context.exception))
        
        # Test configuration validation error
        self.migration_service._validate_user_exists = Mock(return_value=True)
        self.migration_service._validate_configuration_exists = Mock(return_value=False)
        
        with self.assertRaises(ValueError) as context:
            self.migration_service.create_migration(user_id=1, configuration_id=999)
        
        self.assertIn("Configuration 999 does not exist", str(context.exception))
        
        # Test no activities error
        self.migration_service._validate_configuration_exists = Mock(return_value=True)
        self.migration_service._get_user_activity_count = Mock(return_value=0)
        
        with self.assertRaises(ValueError) as context:
            self.migration_service.create_migration(user_id=1, configuration_id=1)
        
        self.assertIn("User 1 has no activities to migrate", str(context.exception))
        
        logger.info("✅ Migration creation validation errors test passed")
    
    def test_migration_progress_tracking(self):
        """Test migration progress tracking"""
        logger.info("Testing migration progress tracking...")
        
        # Create a migration
        self.migration_service._validate_user_exists = Mock(return_value=True)
        self.migration_service._validate_configuration_exists = Mock(return_value=True)
        self.migration_service._get_user_activity_count = Mock(return_value=1000)
        
        migration_id = self.migration_service.create_migration(user_id=1, configuration_id=1)
        
        # Test getting migration progress
        progress = self.migration_service.get_migration_progress(migration_id)
        self.assertIsNotNone(progress)
        self.assertEqual(progress.user_id, 1)
        self.assertEqual(progress.status, 'pending')
        
        # Test getting all migration progress
        all_progress = self.migration_service.get_all_migration_progress()
        self.assertEqual(len(all_progress), 1)
        # Note: MigrationProgress doesn't have migration_id, it's stored as key in active_migrations
        
        logger.info("✅ Migration progress tracking test passed")
    
    def test_migration_control_operations(self):
        """Test migration control operations (pause, resume, cancel)"""
        logger.info("Testing migration control operations...")
        
        # Create a migration
        self.migration_service._validate_user_exists = Mock(return_value=True)
        self.migration_service._validate_configuration_exists = Mock(return_value=True)
        self.migration_service._get_user_activity_count = Mock(return_value=1000)
        
        migration_id = self.migration_service.create_migration(user_id=1, configuration_id=1)
        
        # Test pause migration (should fail for pending status)
        result = self.migration_service.pause_migration(migration_id)
        self.assertFalse(result)
        
        # Set status to running and test pause
        progress = self.migration_service.active_migrations[migration_id]
        progress.status = 'running'
        result = self.migration_service.pause_migration(migration_id)
        self.assertTrue(result)
        self.assertEqual(progress.status, 'paused')
        
        # Test resume migration
        result = self.migration_service.resume_migration(migration_id)
        self.assertTrue(result)
        self.assertEqual(progress.status, 'running')
        
        # Test cancel migration
        result = self.migration_service.cancel_migration(migration_id)
        self.assertTrue(result)
        self.assertEqual(progress.status, 'cancelled')
        
        logger.info("✅ Migration control operations test passed")
    
    def test_batch_processing(self):
        """Test batch processing functionality"""
        logger.info("Testing batch processing...")
        
        # Mock configuration
        mock_config = {
            'id': 1,
            'chronic_period_days': 42,
            'decay_rate': 0.05
        }
        self.migration_service.config_service.get_configuration_by_id = Mock(return_value=mock_config)
        
        # Mock calculation service
        mock_result = {
            'acwr_ratio': 1.2,
            'acute_load': 80.5,
            'chronic_load': 67.1
        }
        self.migration_service.calc_service.calculate_acwr_for_user = Mock(return_value=mock_result)
        
        # Mock database operations
        self.migration_service._store_enhanced_calculation = Mock()
        
        # Test batch processing
        activities = [
            {'activity_id': 1, 'activity_date': datetime.now(), 'trimp_score': 50},
            {'activity_id': 2, 'activity_date': datetime.now(), 'trimp_score': 60},
            {'activity_id': 3, 'activity_date': datetime.now(), 'trimp_score': 70}
        ]
        
        batch_result = self.migration_service._process_activity_batch(
            batch_id=1, user_id=1, activities=activities, configuration_id=1
        )
        
        # Verify batch result
        self.assertEqual(batch_result.batch_id, 1)
        self.assertEqual(batch_result.user_id, 1)
        self.assertEqual(batch_result.activities_processed, 3)
        self.assertEqual(batch_result.successful_calculations, 3)
        self.assertEqual(batch_result.failed_calculations, 0)
        self.assertGreaterEqual(batch_result.processing_time, 0)  # Allow 0 for very fast processing
        
        # Verify calculation service was called for each activity
        self.assertEqual(
            self.migration_service.calc_service.calculate_acwr_for_user.call_count, 3
        )
        
        # Verify enhanced calculations were stored
        self.assertEqual(
            self.migration_service._store_enhanced_calculation.call_count, 3
        )
        
        logger.info("✅ Batch processing test passed")
    
    def test_batch_processing_with_errors(self):
        """Test batch processing with calculation errors"""
        logger.info("Testing batch processing with errors...")
        
        # Mock configuration
        mock_config = {
            'id': 1,
            'chronic_period_days': 42,
            'decay_rate': 0.05
        }
        self.migration_service.config_service.get_configuration_by_id = Mock(return_value=mock_config)
        
        # Mock calculation service to return None for some activities
        def mock_calculate(user_id, activity_date, chronic_period_days, decay_rate):
            if activity_date.day % 2 == 0:  # Even days fail
                return None
            return {'acwr_ratio': 1.2, 'acute_load': 80.5, 'chronic_load': 67.1}
        
        self.migration_service.calc_service.calculate_acwr_for_user = Mock(side_effect=mock_calculate)
        self.migration_service._store_enhanced_calculation = Mock()
        
        # Test batch processing with mixed results
        activities = [
            {'activity_id': 1, 'activity_date': datetime(2024, 1, 1), 'trimp_score': 50},
            {'activity_id': 2, 'activity_date': datetime(2024, 1, 2), 'trimp_score': 60},
            {'activity_id': 3, 'activity_date': datetime(2024, 1, 3), 'trimp_score': 70},
            {'activity_id': 4, 'activity_date': datetime(2024, 1, 4), 'trimp_score': 80}
        ]
        
        batch_result = self.migration_service._process_activity_batch(
            batch_id=1, user_id=1, activities=activities, configuration_id=1
        )
        
        # Verify batch result with errors
        self.assertEqual(batch_result.activities_processed, 4)
        self.assertEqual(batch_result.successful_calculations, 2)  # Odd days succeed
        self.assertEqual(batch_result.failed_calculations, 2)  # Even days fail
        self.assertEqual(len(batch_result.errors), 2)
        
        logger.info("✅ Batch processing with errors test passed")
    
    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        logger.info("Testing performance metrics...")
        
        # Get initial metrics
        initial_metrics = self.migration_service.get_performance_metrics()
        self.assertEqual(initial_metrics['total_migrations'], 0)
        self.assertEqual(initial_metrics['successful_migrations'], 0)
        self.assertEqual(initial_metrics['failed_migrations'], 0)
        
        # Simulate migration completion
        self.migration_service.performance_metrics['total_migrations'] = 1
        self.migration_service.performance_metrics['successful_migrations'] = 1
        self.migration_service.performance_metrics['total_activities_processed'] = 1000
        self.migration_service.performance_metrics['average_processing_time'] = 120.5
        
        # Get updated metrics
        updated_metrics = self.migration_service.get_performance_metrics()
        self.assertEqual(updated_metrics['total_migrations'], 1)
        self.assertEqual(updated_metrics['successful_migrations'], 1)
        self.assertEqual(updated_metrics['total_activities_processed'], 1000)
        self.assertEqual(updated_metrics['average_processing_time'], 120.5)
        
        logger.info("✅ Performance metrics test passed")
    
    def test_migration_result_creation(self):
        """Test migration result creation"""
        logger.info("Testing migration result creation...")
        
        # Create a migration result
        result = MigrationResult(
            user_id=1,
            migration_id="test_migration_123",
            start_time=datetime.now() - timedelta(minutes=5),
            end_time=datetime.now(),
            total_activities=1000,
            successful_calculations=950,
            failed_calculations=50,
            configuration_id=1,
            performance_metrics={
                'processing_time_seconds': 300.0,
                'activities_per_second': 3.33,
                'success_rate': 0.95
            },
            error_log=['Error 1', 'Error 2']
        )
        
        # Verify result structure
        self.assertEqual(result.user_id, 1)
        self.assertEqual(result.migration_id, "test_migration_123")
        self.assertEqual(result.total_activities, 1000)
        self.assertEqual(result.successful_calculations, 950)
        self.assertEqual(result.failed_calculations, 50)
        self.assertEqual(result.configuration_id, 1)
        self.assertIn('processing_time_seconds', result.performance_metrics)
        self.assertEqual(len(result.error_log), 2)
        
        logger.info("✅ Migration result creation test passed")
    
    def test_batch_result_creation(self):
        """Test batch result creation"""
        logger.info("Testing batch result creation...")
        
        # Create a batch result
        batch_result = BatchResult(
            batch_id=1,
            user_id=1,
            activities_processed=100,
            successful_calculations=95,
            failed_calculations=5,
            processing_time=30.5,
            errors=['Error 1', 'Error 2']
        )
        
        # Verify batch result structure
        self.assertEqual(batch_result.batch_id, 1)
        self.assertEqual(batch_result.user_id, 1)
        self.assertEqual(batch_result.activities_processed, 100)
        self.assertEqual(batch_result.successful_calculations, 95)
        self.assertEqual(batch_result.failed_calculations, 5)
        self.assertEqual(batch_result.processing_time, 30.5)
        self.assertEqual(len(batch_result.errors), 2)
        
        logger.info("✅ Batch result creation test passed")

def run_migration_service_tests():
    """Run all migration service tests"""
    logger.info("=" * 60)
    logger.info("ACWR Migration Service Test Suite")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestACWRMigrationService)
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Log results
    logger.info("=" * 60)
    logger.info(f"Test Results: {result.testsRun} tests run")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info("=" * 60)
    
    if result.wasSuccessful():
        logger.info("🎉 All migration service tests passed!")
        return True
    else:
        logger.error("⚠️  Some migration service tests failed.")
        for failure in result.failures:
            logger.error(f"FAILURE: {failure[0]}")
            logger.error(f"Details: {failure[1]}")
        for error in result.errors:
            logger.error(f"ERROR: {error[0]}")
            logger.error(f"Details: {error[1]}")
        return False

def main():
    """Run the test suite"""
    success = run_migration_service_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
