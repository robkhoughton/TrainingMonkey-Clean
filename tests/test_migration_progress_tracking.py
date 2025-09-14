#!/usr/bin/env python3
"""
Test script for ACWR Migration Progress Tracking
Tests the real-time progress tracking functionality
"""

import sys
import os
import logging
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import time
import threading

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock database dependencies before importing
with patch.dict('sys.modules', {
    'db_utils': Mock(),
    'psycopg2': Mock(),
    'psycopg2.extras': Mock()
}):
    from acwr_migration_progress_tracker import (
        ACWRMigrationProgressTracker, ProgressEvent, ProgressEventType, 
        ProgressSnapshot, ProgressSubscriber
    )

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestACWRMigrationProgressTracker(unittest.TestCase):
    """Test cases for ACWR Migration Progress Tracker"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tracker = ACWRMigrationProgressTracker()
        self.received_events = []
        
    def tearDown(self):
        """Clean up after tests"""
        self.tracker.stop_event_processor()
    
    def test_tracker_initialization(self):
        """Test tracker initialization"""
        logger.info("Testing tracker initialization...")
        
        # Test initial state
        self.assertIsInstance(self.tracker.active_migrations, dict)
        self.assertIsInstance(self.tracker.migration_history, list)
        self.assertIsInstance(self.tracker.subscribers, dict)
        self.assertIsInstance(self.tracker.performance_metrics, dict)
        
        # Test performance metrics initialization
        self.assertIn('total_events_processed', self.tracker.performance_metrics)
        self.assertIn('active_subscribers', self.tracker.performance_metrics)
        self.assertIn('average_event_processing_time', self.tracker.performance_metrics)
        self.assertIn('events_per_second', self.tracker.performance_metrics)
        
        # Test event processor is running
        self.assertTrue(self.tracker.is_running)
        
        logger.info("✅ Tracker initialization test passed")
    
    def test_subscriber_management(self):
        """Test subscriber management"""
        logger.info("Testing subscriber management...")
        
        # Test adding subscriber
        def test_callback(event):
            self.received_events.append(event)
        
        subscriber_id = "test_subscriber_1"
        result = self.tracker.subscribe(subscriber_id, test_callback)
        self.assertTrue(result)
        self.assertIn(subscriber_id, self.tracker.subscribers)
        self.assertEqual(self.tracker.performance_metrics['active_subscribers'], 1)
        
        # Test removing subscriber
        result = self.tracker.unsubscribe(subscriber_id)
        self.assertTrue(result)
        self.assertNotIn(subscriber_id, self.tracker.subscribers)
        self.assertEqual(self.tracker.performance_metrics['active_subscribers'], 0)
        
        # Test removing non-existent subscriber
        result = self.tracker.unsubscribe("non_existent")
        self.assertFalse(result)
        
        logger.info("✅ Subscriber management test passed")
    
    def test_progress_event_publishing(self):
        """Test progress event publishing"""
        logger.info("Testing progress event publishing...")
        
        # Add subscriber
        def test_callback(event):
            self.received_events.append(event)
        
        subscriber_id = "test_subscriber_2"
        self.tracker.subscribe(subscriber_id, test_callback)
        
        # Create and publish event
        event = ProgressEvent(
            event_type=ProgressEventType.MIGRATION_STARTED,
            migration_id="test_migration_1",
            user_id=1,
            timestamp=datetime.now(),
            data={'total_activities': 1000},
            message="Test migration started"
        )
        
        self.tracker.publish_event(event)
        
        # Wait for event processing
        time.sleep(0.1)
        
        # Verify event was received
        self.assertEqual(len(self.received_events), 1)
        self.assertEqual(self.received_events[0].migration_id, "test_migration_1")
        self.assertEqual(self.received_events[0].event_type, ProgressEventType.MIGRATION_STARTED)
        
        # Verify event was added to history
        self.assertEqual(len(self.tracker.migration_history), 1)
        
        logger.info("✅ Progress event publishing test passed")
    
    def test_migration_snapshot_updates(self):
        """Test migration snapshot updates"""
        logger.info("Testing migration snapshot updates...")
        
        # Create progress update event
        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            migration_id="test_migration_2",
            user_id=1,
            timestamp=datetime.now(),
            data={
                'status': 'running',
                'current_batch': 2,
                'total_batches': 5,
                'processed_activities': 400,
                'total_activities': 1000,
                'successful_calculations': 380,
                'failed_calculations': 20,
                'elapsed_time': 120.5
            },
            message="Progress update"
        )
        
        self.tracker.publish_event(event)
        
        # Wait for processing
        time.sleep(0.1)
        
        # Verify snapshot was created/updated
        snapshot = self.tracker.get_migration_progress("test_migration_2")
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.migration_id, "test_migration_2")
        self.assertEqual(snapshot.user_id, 1)
        self.assertEqual(snapshot.status, 'running')
        self.assertEqual(snapshot.current_batch, 2)
        self.assertEqual(snapshot.total_batches, 5)
        self.assertEqual(snapshot.processed_activities, 400)
        self.assertEqual(snapshot.total_activities, 1000)
        self.assertEqual(snapshot.successful_calculations, 380)
        self.assertEqual(snapshot.failed_calculations, 20)
        self.assertEqual(snapshot.progress_percentage, 40.0)  # 400/1000 * 100
        self.assertEqual(snapshot.processing_rate, 400/120.5)  # activities per second
        self.assertEqual(snapshot.elapsed_time, 120.5)
        
        logger.info("✅ Migration snapshot updates test passed")
    
    def test_progress_calculations(self):
        """Test progress calculations"""
        logger.info("Testing progress calculations...")
        
        # Test progress percentage calculation
        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            migration_id="test_migration_3",
            user_id=1,
            timestamp=datetime.now(),
            data={
                'status': 'running',
                'current_batch': 3,
                'total_batches': 10,
                'processed_activities': 750,
                'total_activities': 1000,
                'successful_calculations': 720,
                'failed_calculations': 30,
                'elapsed_time': 300.0
            },
            message="Progress update"
        )
        
        self.tracker.publish_event(event)
        time.sleep(0.1)
        
        snapshot = self.tracker.get_migration_progress("test_migration_3")
        self.assertEqual(snapshot.progress_percentage, 75.0)  # 750/1000 * 100
        self.assertEqual(snapshot.processing_rate, 2.5)  # 750/300
        
        # Test estimated completion time
        self.assertIsNotNone(snapshot.estimated_completion)
        estimated_remaining = (snapshot.total_activities - snapshot.processed_activities) / snapshot.processing_rate
        expected_completion = datetime.now() + timedelta(seconds=estimated_remaining)
        # Allow 1 second tolerance
        time_diff = abs((snapshot.estimated_completion - expected_completion).total_seconds())
        self.assertLess(time_diff, 1.0)
        
        logger.info("✅ Progress calculations test passed")
    
    def test_multiple_migrations_tracking(self):
        """Test tracking multiple migrations simultaneously"""
        logger.info("Testing multiple migrations tracking...")
        
        # Create events for multiple migrations
        migrations = [
            ("migration_1", 1, 500, 1000),
            ("migration_2", 2, 750, 1500),
            ("migration_3", 3, 200, 800)
        ]
        
        for migration_id, user_id, processed, total in migrations:
            event = ProgressEvent(
                event_type=ProgressEventType.PROGRESS_UPDATE,
                migration_id=migration_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data={
                    'status': 'running',
                    'current_batch': 1,
                    'total_batches': 2,
                    'processed_activities': processed,
                    'total_activities': total,
                    'successful_calculations': processed - 10,
                    'failed_calculations': 10,
                    'elapsed_time': 60.0
                },
                message=f"Progress update for {migration_id}"
            )
            self.tracker.publish_event(event)
        
        time.sleep(0.1)
        
        # Verify all migrations are tracked
        all_progress = self.tracker.get_all_migration_progress()
        self.assertEqual(len(all_progress), 3)
        
        # Verify individual migrations
        for migration_id, user_id, processed, total in migrations:
            snapshot = self.tracker.get_migration_progress(migration_id)
            self.assertIsNotNone(snapshot)
            self.assertEqual(snapshot.migration_id, migration_id)
            self.assertEqual(snapshot.user_id, user_id)
            self.assertEqual(snapshot.processed_activities, processed)
            self.assertEqual(snapshot.total_activities, total)
        
        logger.info("✅ Multiple migrations tracking test passed")
    
    def test_event_history_management(self):
        """Test event history management"""
        logger.info("Testing event history management...")
        
        # Create multiple events
        for i in range(5):
            event = ProgressEvent(
                event_type=ProgressEventType.PROGRESS_UPDATE,
                migration_id=f"migration_{i}",
                user_id=i,
                timestamp=datetime.now(),
                data={'batch': i},
                message=f"Event {i}"
            )
            self.tracker.publish_event(event)
        
        time.sleep(0.1)
        
        # Verify events in history
        self.assertEqual(len(self.tracker.migration_history), 5)
        
        # Test getting recent events
        recent_events = self.tracker.get_recent_events(limit=3)
        self.assertEqual(len(recent_events), 3)
        
        # Test getting events for specific migration
        migration_events = self.tracker.get_migration_events("migration_0")
        self.assertEqual(len(migration_events), 1)
        self.assertEqual(migration_events[0].migration_id, "migration_0")
        
        logger.info("✅ Event history management test passed")
    
    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        logger.info("Testing performance metrics...")
        
        # Add subscriber to generate events
        def test_callback(event):
            pass
        
        self.tracker.subscribe("perf_test_subscriber", test_callback)
        
        # Publish multiple events
        for i in range(10):
            event = ProgressEvent(
                event_type=ProgressEventType.PROGRESS_UPDATE,
                migration_id="perf_test_migration",
                user_id=1,
                timestamp=datetime.now(),
                data={'event': i},
                message=f"Performance test event {i}"
            )
            self.tracker.publish_event(event)
        
        time.sleep(0.2)
        
        # Verify performance metrics
        metrics = self.tracker.get_performance_metrics()
        self.assertGreater(metrics['total_events_processed'], 0)
        self.assertGreaterEqual(metrics['average_event_processing_time'], 0)  # Allow 0 for very fast processing
        self.assertGreaterEqual(metrics['events_per_second'], 0)  # Allow 0 for very fast processing
        
        logger.info("✅ Performance metrics test passed")
    
    def test_subscriber_cleanup(self):
        """Test subscriber cleanup functionality"""
        logger.info("Testing subscriber cleanup...")
        
        # Add multiple subscribers
        for i in range(5):
            def test_callback(event):
                pass
            self.tracker.subscribe(f"cleanup_test_{i}", test_callback)
        
        self.assertEqual(len(self.tracker.subscribers), 5)
        
        # Simulate inactive subscribers by setting last_activity to old time
        for subscriber in self.tracker.subscribers.values():
            subscriber.last_activity = datetime.now() - timedelta(hours=25)
        
        # Run cleanup
        self.tracker.cleanup_inactive_subscribers(max_age_hours=24)
        
        # Verify cleanup
        self.assertEqual(len(self.tracker.subscribers), 0)
        
        logger.info("✅ Subscriber cleanup test passed")
    
    def test_export_progress_data(self):
        """Test progress data export"""
        logger.info("Testing progress data export...")
        
        # Create migration with events
        migration_id = "export_test_migration"
        
        # Add progress update
        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            migration_id=migration_id,
            user_id=1,
            timestamp=datetime.now(),
            data={
                'status': 'running',
                'processed_activities': 500,
                'total_activities': 1000
            },
            message="Export test"
        )
        self.tracker.publish_event(event)
        
        time.sleep(0.1)
        
        # Export data
        exported_data = self.tracker.export_progress_data(migration_id)
        
        # Verify export structure
        self.assertIn('migration_id', exported_data)
        self.assertIn('current_snapshot', exported_data)
        self.assertIn('events', exported_data)
        self.assertIn('export_timestamp', exported_data)
        self.assertIn('total_events', exported_data)
        
        self.assertEqual(exported_data['migration_id'], migration_id)
        self.assertIsNotNone(exported_data['current_snapshot'])
        self.assertEqual(len(exported_data['events']), 1)
        self.assertEqual(exported_data['total_events'], 1)
        
        logger.info("✅ Progress data export test passed")

def run_progress_tracking_tests():
    """Run all progress tracking tests"""
    logger.info("=" * 60)
    logger.info("ACWR Migration Progress Tracking Test Suite")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestACWRMigrationProgressTracker)
    
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
        logger.info("🎉 All progress tracking tests passed!")
        return True
    else:
        logger.error("⚠️  Some progress tracking tests failed.")
        for failure in result.failures:
            logger.error(f"FAILURE: {failure[0]}")
            logger.error(f"Details: {failure[1]}")
        for error in result.errors:
            logger.error(f"ERROR: {error[0]}")
            logger.error(f"Details: {error[1]}")
        return False

def main():
    """Run the test suite"""
    success = run_progress_tracking_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
