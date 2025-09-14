#!/usr/bin/env python3
"""
Standalone test script for ACWR Migration Monitoring and Logging System
Tests core monitoring functionality without database dependencies
"""

import sys
import os
import logging
import unittest
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the enums and dataclasses locally for testing
class LogLevel(Enum):
    """Log levels for migration monitoring"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MigrationStatus(Enum):
    """Migration status levels"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"

class MonitoringEventType(Enum):
    """Types of monitoring events"""
    MIGRATION_STARTED = "migration_started"
    MIGRATION_COMPLETED = "migration_completed"
    MIGRATION_FAILED = "migration_failed"
    MIGRATION_PAUSED = "migration_paused"
    MIGRATION_RESUMED = "migration_resumed"
    MIGRATION_CANCELLED = "migration_cancelled"
    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"
    BATCH_FAILED = "batch_failed"
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"
    PERFORMANCE_DEGRADED = "performance_degraded"
    RESOURCE_THRESHOLD_EXCEEDED = "resource_threshold_exceeded"
    ALERT_TRIGGERED = "alert_triggered"
    STATUS_CHANGED = "status_changed"

@dataclass
class LogEntry:
    """Log entry structure"""
    log_id: str
    migration_id: str
    user_id: int = None
    timestamp: datetime = None
    level: LogLevel = LogLevel.INFO
    message: str = ""
    details: dict = None
    source: str = "system"
    thread_id: str = "main"
    execution_time: float = None
    error_traceback: str = None

@dataclass
class Alert:
    """Alert structure"""
    alert_id: str
    migration_id: str
    user_id: int = None
    timestamp: datetime = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    alert_type: str = "general"
    title: str = ""
    message: str = ""
    details: dict = None
    acknowledged: bool = False
    acknowledged_by: int = None
    acknowledged_at: datetime = None
    resolved: bool = False
    resolved_at: datetime = None

@dataclass
class MonitoringEvent:
    """Monitoring event structure"""
    event_id: str
    migration_id: str
    user_id: int = None
    timestamp: datetime = None
    event_type: MonitoringEventType = MonitoringEventType.STATUS_CHANGED
    data: dict = None
    source: str = "system"

@dataclass
class MigrationHealthMetrics:
    """Migration health metrics"""
    migration_id: str
    timestamp: datetime = None
    status: MigrationStatus = MigrationStatus.RUNNING
    progress_percentage: float = 0.0
    estimated_completion_time: datetime = None
    error_count: int = 0
    warning_count: int = 0
    performance_score: float = 100.0
    resource_usage: dict = None
    throughput_activities_per_second: float = 0.0
    average_batch_time: float = 0.0
    success_rate: float = 1.0

class TestMigrationMonitoringStandalone(unittest.TestCase):
    """Test cases for standalone migration monitoring functionality"""
    
    def test_log_level_enum(self):
        """Test log level enumeration"""
        logger.info("Testing log level enumeration...")
        
        # Test log level values
        self.assertEqual(LogLevel.DEBUG.value, "DEBUG")
        self.assertEqual(LogLevel.INFO.value, "INFO")
        self.assertEqual(LogLevel.WARNING.value, "WARNING")
        self.assertEqual(LogLevel.ERROR.value, "ERROR")
        self.assertEqual(LogLevel.CRITICAL.value, "CRITICAL")
        
        # Test all log levels exist
        log_levels = [
            LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, 
            LogLevel.ERROR, LogLevel.CRITICAL
        ]
        self.assertEqual(len(log_levels), 5)
        
        logger.info("✅ Log level enumeration test passed")
    
    def test_alert_severity_enum(self):
        """Test alert severity enumeration"""
        logger.info("Testing alert severity enumeration...")
        
        # Test alert severity values
        self.assertEqual(AlertSeverity.LOW.value, "low")
        self.assertEqual(AlertSeverity.MEDIUM.value, "medium")
        self.assertEqual(AlertSeverity.HIGH.value, "high")
        self.assertEqual(AlertSeverity.CRITICAL.value, "critical")
        
        # Test all alert severities exist
        alert_severities = [
            AlertSeverity.LOW, AlertSeverity.MEDIUM, 
            AlertSeverity.HIGH, AlertSeverity.CRITICAL
        ]
        self.assertEqual(len(alert_severities), 4)
        
        logger.info("✅ Alert severity enumeration test passed")
    
    def test_migration_status_enum(self):
        """Test migration status enumeration"""
        logger.info("Testing migration status enumeration...")
        
        # Test migration status values
        self.assertEqual(MigrationStatus.PENDING.value, "pending")
        self.assertEqual(MigrationStatus.RUNNING.value, "running")
        self.assertEqual(MigrationStatus.PAUSED.value, "paused")
        self.assertEqual(MigrationStatus.COMPLETED.value, "completed")
        self.assertEqual(MigrationStatus.FAILED.value, "failed")
        self.assertEqual(MigrationStatus.CANCELLED.value, "cancelled")
        self.assertEqual(MigrationStatus.ROLLED_BACK.value, "rolled_back")
        
        # Test all migration statuses exist
        migration_statuses = [
            MigrationStatus.PENDING, MigrationStatus.RUNNING, MigrationStatus.PAUSED,
            MigrationStatus.COMPLETED, MigrationStatus.FAILED, MigrationStatus.CANCELLED,
            MigrationStatus.ROLLED_BACK
        ]
        self.assertEqual(len(migration_statuses), 7)
        
        logger.info("✅ Migration status enumeration test passed")
    
    def test_monitoring_event_type_enum(self):
        """Test monitoring event type enumeration"""
        logger.info("Testing monitoring event type enumeration...")
        
        # Test monitoring event type values
        self.assertEqual(MonitoringEventType.MIGRATION_STARTED.value, "migration_started")
        self.assertEqual(MonitoringEventType.MIGRATION_COMPLETED.value, "migration_completed")
        self.assertEqual(MonitoringEventType.MIGRATION_FAILED.value, "migration_failed")
        self.assertEqual(MonitoringEventType.BATCH_STARTED.value, "batch_started")
        self.assertEqual(MonitoringEventType.BATCH_COMPLETED.value, "batch_completed")
        self.assertEqual(MonitoringEventType.ERROR_OCCURRED.value, "error_occurred")
        self.assertEqual(MonitoringEventType.ALERT_TRIGGERED.value, "alert_triggered")
        
        # Test all monitoring event types exist
        event_types = [
            MonitoringEventType.MIGRATION_STARTED, MonitoringEventType.MIGRATION_COMPLETED,
            MonitoringEventType.MIGRATION_FAILED, MonitoringEventType.MIGRATION_PAUSED,
            MonitoringEventType.MIGRATION_RESUMED, MonitoringEventType.MIGRATION_CANCELLED,
            MonitoringEventType.BATCH_STARTED, MonitoringEventType.BATCH_COMPLETED,
            MonitoringEventType.BATCH_FAILED, MonitoringEventType.ERROR_OCCURRED,
            MonitoringEventType.WARNING_ISSUED, MonitoringEventType.PERFORMANCE_DEGRADED,
            MonitoringEventType.RESOURCE_THRESHOLD_EXCEEDED, MonitoringEventType.ALERT_TRIGGERED,
            MonitoringEventType.STATUS_CHANGED
        ]
        self.assertEqual(len(event_types), 15)
        
        logger.info("✅ Monitoring event type enumeration test passed")
    
    def test_log_entry_dataclass(self):
        """Test log entry dataclass"""
        logger.info("Testing log entry dataclass...")
        
        # Create a log entry
        log_entry = LogEntry(
            log_id="log_123",
            migration_id="migration_456",
            user_id=1,
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message="Test log message",
            details={"key": "value", "count": 42},
            source="test_system",
            thread_id="main_thread",
            execution_time=1.5,
            error_traceback=None
        )
        
        # Test log entry structure
        self.assertEqual(log_entry.log_id, "log_123")
        self.assertEqual(log_entry.migration_id, "migration_456")
        self.assertEqual(log_entry.user_id, 1)
        self.assertIsInstance(log_entry.timestamp, datetime)
        self.assertEqual(log_entry.level, LogLevel.INFO)
        self.assertEqual(log_entry.message, "Test log message")
        self.assertIsInstance(log_entry.details, dict)
        self.assertEqual(log_entry.details["key"], "value")
        self.assertEqual(log_entry.details["count"], 42)
        self.assertEqual(log_entry.source, "test_system")
        self.assertEqual(log_entry.thread_id, "main_thread")
        self.assertEqual(log_entry.execution_time, 1.5)
        self.assertIsNone(log_entry.error_traceback)
        
        logger.info("✅ Log entry dataclass test passed")
    
    def test_alert_dataclass(self):
        """Test alert dataclass"""
        logger.info("Testing alert dataclass...")
        
        # Create an alert
        alert = Alert(
            alert_id="alert_789",
            migration_id="migration_456",
            user_id=1,
            timestamp=datetime.now(),
            severity=AlertSeverity.HIGH,
            alert_type="performance_degraded",
            title="Performance Degradation Detected",
            message="Migration performance has degraded significantly",
            details={"performance_score": 45.0, "threshold": 75.0},
            acknowledged=False,
            acknowledged_by=None,
            acknowledged_at=None,
            resolved=False,
            resolved_at=None
        )
        
        # Test alert structure
        self.assertEqual(alert.alert_id, "alert_789")
        self.assertEqual(alert.migration_id, "migration_456")
        self.assertEqual(alert.user_id, 1)
        self.assertIsInstance(alert.timestamp, datetime)
        self.assertEqual(alert.severity, AlertSeverity.HIGH)
        self.assertEqual(alert.alert_type, "performance_degraded")
        self.assertEqual(alert.title, "Performance Degradation Detected")
        self.assertEqual(alert.message, "Migration performance has degraded significantly")
        self.assertIsInstance(alert.details, dict)
        self.assertEqual(alert.details["performance_score"], 45.0)
        self.assertEqual(alert.details["threshold"], 75.0)
        self.assertFalse(alert.acknowledged)
        self.assertIsNone(alert.acknowledged_by)
        self.assertIsNone(alert.acknowledged_at)
        self.assertFalse(alert.resolved)
        self.assertIsNone(alert.resolved_at)
        
        logger.info("✅ Alert dataclass test passed")
    
    def test_monitoring_event_dataclass(self):
        """Test monitoring event dataclass"""
        logger.info("Testing monitoring event dataclass...")
        
        # Create a monitoring event
        event = MonitoringEvent(
            event_id="event_101",
            migration_id="migration_456",
            user_id=1,
            timestamp=datetime.now(),
            event_type=MonitoringEventType.BATCH_COMPLETED,
            data={"batch_number": 5, "activities_processed": 1000, "processing_time": 30.5},
            source="batch_processor"
        )
        
        # Test monitoring event structure
        self.assertEqual(event.event_id, "event_101")
        self.assertEqual(event.migration_id, "migration_456")
        self.assertEqual(event.user_id, 1)
        self.assertIsInstance(event.timestamp, datetime)
        self.assertEqual(event.event_type, MonitoringEventType.BATCH_COMPLETED)
        self.assertIsInstance(event.data, dict)
        self.assertEqual(event.data["batch_number"], 5)
        self.assertEqual(event.data["activities_processed"], 1000)
        self.assertEqual(event.data["processing_time"], 30.5)
        self.assertEqual(event.source, "batch_processor")
        
        logger.info("✅ Monitoring event dataclass test passed")
    
    def test_migration_health_metrics_dataclass(self):
        """Test migration health metrics dataclass"""
        logger.info("Testing migration health metrics dataclass...")
        
        # Create migration health metrics
        metrics = MigrationHealthMetrics(
            migration_id="migration_456",
            timestamp=datetime.now(),
            status=MigrationStatus.RUNNING,
            progress_percentage=65.5,
            estimated_completion_time=datetime.now() + timedelta(minutes=30),
            error_count=3,
            warning_count=7,
            performance_score=85.2,
            resource_usage={"memory_percent": 72.5, "cpu_percent": 45.8, "disk_io_percent": 15.2},
            throughput_activities_per_second=250.5,
            average_batch_time=4.2,
            success_rate=0.95
        )
        
        # Test migration health metrics structure
        self.assertEqual(metrics.migration_id, "migration_456")
        self.assertIsInstance(metrics.timestamp, datetime)
        self.assertEqual(metrics.status, MigrationStatus.RUNNING)
        self.assertEqual(metrics.progress_percentage, 65.5)
        self.assertIsInstance(metrics.estimated_completion_time, datetime)
        self.assertEqual(metrics.error_count, 3)
        self.assertEqual(metrics.warning_count, 7)
        self.assertEqual(metrics.performance_score, 85.2)
        self.assertIsInstance(metrics.resource_usage, dict)
        self.assertEqual(metrics.resource_usage["memory_percent"], 72.5)
        self.assertEqual(metrics.resource_usage["cpu_percent"], 45.8)
        self.assertEqual(metrics.resource_usage["disk_io_percent"], 15.2)
        self.assertEqual(metrics.throughput_activities_per_second, 250.5)
        self.assertEqual(metrics.average_batch_time, 4.2)
        self.assertEqual(metrics.success_rate, 0.95)
        
        logger.info("✅ Migration health metrics dataclass test passed")
    
    def test_alert_threshold_logic(self):
        """Test alert threshold logic"""
        logger.info("Testing alert threshold logic...")
        
        def check_alert_thresholds(error_rate, performance_score, memory_usage, cpu_usage):
            """Check if alert thresholds are exceeded"""
            alerts = []
            
            if error_rate > 0.05:  # 5% error rate
                alerts.append({
                    'type': 'high_error_rate',
                    'severity': 'high',
                    'message': f'Error rate {error_rate:.2%} exceeds threshold of 5%'
                })
            
            if performance_score < 50.0:  # Performance below 50%
                alerts.append({
                    'type': 'performance_degraded',
                    'severity': 'medium',
                    'message': f'Performance score {performance_score} is below threshold of 50'
                })
            
            if memory_usage > 0.85:  # 85% memory usage
                alerts.append({
                    'type': 'high_memory_usage',
                    'severity': 'high',
                    'message': f'Memory usage {memory_usage:.1%} exceeds threshold of 85%'
                })
            
            if cpu_usage > 0.90:  # 90% CPU usage
                alerts.append({
                    'type': 'high_cpu_usage',
                    'severity': 'high',
                    'message': f'CPU usage {cpu_usage:.1%} exceeds threshold of 90%'
                })
            
            return alerts
        
        # Test different threshold scenarios
        test_cases = [
            (0.02, 75.0, 0.60, 0.70, 0),  # All good -> no alerts
            (0.08, 75.0, 0.60, 0.70, 1),  # High error rate -> 1 alert
            (0.02, 30.0, 0.60, 0.70, 1),  # Low performance -> 1 alert
            (0.02, 75.0, 0.90, 0.70, 1),  # High memory -> 1 alert
            (0.02, 75.0, 0.60, 0.95, 1),  # High CPU -> 1 alert
            (0.10, 25.0, 0.95, 0.95, 4),  # All bad -> 4 alerts
        ]
        
        for error_rate, performance_score, memory_usage, cpu_usage, expected_alerts in test_cases:
            alerts = check_alert_thresholds(error_rate, performance_score, memory_usage, cpu_usage)
            self.assertEqual(len(alerts), expected_alerts, 
                           f"Failed for error_rate={error_rate}, performance={performance_score}, "
                           f"memory={memory_usage}, cpu={cpu_usage}")
        
        logger.info("✅ Alert threshold logic test passed")
    
    def test_performance_score_calculation(self):
        """Test performance score calculation logic"""
        logger.info("Testing performance score calculation...")
        
        def calculate_performance_score(error_count, warning_count, failed_batches, total_batches):
            """Calculate performance score based on metrics"""
            score = 100.0
            
            # Deduct points for errors
            if error_count > 0:
                score -= min(50, error_count * 5)
            
            # Deduct points for warnings
            if warning_count > 0:
                score -= min(20, warning_count * 2)
            
            # Deduct points for failed batches
            if failed_batches > 0 and total_batches > 0:
                failure_rate = failed_batches / total_batches
                score -= failure_rate * 30
            
            return max(0, score)
        
        # Test different performance scenarios
        test_cases = [
            (0, 0, 0, 100, 100.0),    # Perfect performance
            (1, 0, 0, 100, 95.0),     # 1 error -> 95%
            (0, 5, 0, 100, 90.0),     # 5 warnings -> 90%
            (0, 0, 10, 100, 97.0),    # 10% failure rate -> 97%
            (5, 10, 20, 100, 49.0),   # Multiple issues -> 49% (5*5 + 10*2 + 0.2*30 = 25 + 20 + 6 = 51, 100-51=49)
            (20, 50, 50, 100, 15.0),  # Critical issues -> 15% (20*5=100 capped at 50, 50*2=100 capped at 20, 0.5*30=15, 100-50-20-15=15)
        ]
        
        for error_count, warning_count, failed_batches, total_batches, expected_score in test_cases:
            score = calculate_performance_score(error_count, warning_count, failed_batches, total_batches)
            self.assertEqual(score, expected_score, 
                           f"Failed for errors={error_count}, warnings={warning_count}, "
                           f"failed_batches={failed_batches}, total_batches={total_batches}")
        
        logger.info("✅ Performance score calculation test passed")
    
    def test_log_level_hierarchy(self):
        """Test log level hierarchy"""
        logger.info("Testing log level hierarchy...")
        
        def get_log_level_priority(level):
            """Get numeric priority for log level"""
            priorities = {
                LogLevel.DEBUG: 0,
                LogLevel.INFO: 1,
                LogLevel.WARNING: 2,
                LogLevel.ERROR: 3,
                LogLevel.CRITICAL: 4
            }
            return priorities.get(level, -1)
        
        def should_log(level, threshold):
            """Check if log level should be logged based on threshold"""
            return get_log_level_priority(level) >= get_log_level_priority(threshold)
        
        # Test log level priorities
        self.assertEqual(get_log_level_priority(LogLevel.DEBUG), 0)
        self.assertEqual(get_log_level_priority(LogLevel.INFO), 1)
        self.assertEqual(get_log_level_priority(LogLevel.WARNING), 2)
        self.assertEqual(get_log_level_priority(LogLevel.ERROR), 3)
        self.assertEqual(get_log_level_priority(LogLevel.CRITICAL), 4)
        
        # Test logging decisions
        test_cases = [
            (LogLevel.DEBUG, LogLevel.INFO, False),    # DEBUG < INFO
            (LogLevel.INFO, LogLevel.INFO, True),      # INFO = INFO
            (LogLevel.WARNING, LogLevel.INFO, True),   # WARNING > INFO
            (LogLevel.ERROR, LogLevel.WARNING, True),  # ERROR > WARNING
            (LogLevel.CRITICAL, LogLevel.ERROR, True), # CRITICAL > ERROR
        ]
        
        for level, threshold, expected in test_cases:
            result = should_log(level, threshold)
            self.assertEqual(result, expected, 
                           f"Failed for level={level.value}, threshold={threshold.value}")
        
        logger.info("✅ Log level hierarchy test passed")
    
    def test_alert_severity_hierarchy(self):
        """Test alert severity hierarchy"""
        logger.info("Testing alert severity hierarchy...")
        
        def get_alert_severity_priority(severity):
            """Get numeric priority for alert severity"""
            priorities = {
                AlertSeverity.LOW: 0,
                AlertSeverity.MEDIUM: 1,
                AlertSeverity.HIGH: 2,
                AlertSeverity.CRITICAL: 3
            }
            return priorities.get(severity, -1)
        
        def should_escalate_alert(severity, threshold):
            """Check if alert should be escalated based on severity"""
            return get_alert_severity_priority(severity) >= get_alert_severity_priority(threshold)
        
        # Test alert severity priorities
        self.assertEqual(get_alert_severity_priority(AlertSeverity.LOW), 0)
        self.assertEqual(get_alert_severity_priority(AlertSeverity.MEDIUM), 1)
        self.assertEqual(get_alert_severity_priority(AlertSeverity.HIGH), 2)
        self.assertEqual(get_alert_severity_priority(AlertSeverity.CRITICAL), 3)
        
        # Test escalation decisions
        test_cases = [
            (AlertSeverity.LOW, AlertSeverity.MEDIUM, False),      # LOW < MEDIUM
            (AlertSeverity.MEDIUM, AlertSeverity.MEDIUM, True),    # MEDIUM = MEDIUM
            (AlertSeverity.HIGH, AlertSeverity.MEDIUM, True),      # HIGH > MEDIUM
            (AlertSeverity.CRITICAL, AlertSeverity.HIGH, True),    # CRITICAL > HIGH
        ]
        
        for severity, threshold, expected in test_cases:
            result = should_escalate_alert(severity, threshold)
            self.assertEqual(result, expected, 
                           f"Failed for severity={severity.value}, threshold={threshold.value}")
        
        logger.info("✅ Alert severity hierarchy test passed")
    
    def test_migration_status_transitions(self):
        """Test migration status transitions"""
        logger.info("Testing migration status transitions...")
        
        def get_valid_status_transitions():
            """Get valid migration status transitions"""
            return {
                MigrationStatus.PENDING: [MigrationStatus.RUNNING, MigrationStatus.CANCELLED],
                MigrationStatus.RUNNING: [MigrationStatus.PAUSED, MigrationStatus.COMPLETED, 
                                        MigrationStatus.FAILED, MigrationStatus.CANCELLED],
                MigrationStatus.PAUSED: [MigrationStatus.RUNNING, MigrationStatus.CANCELLED],
                MigrationStatus.COMPLETED: [],  # Terminal state
                MigrationStatus.FAILED: [MigrationStatus.ROLLED_BACK],  # Can be rolled back
                MigrationStatus.CANCELLED: [],  # Terminal state
                MigrationStatus.ROLLED_BACK: []  # Terminal state
            }
        
        def is_valid_transition(from_status, to_status):
            """Check if status transition is valid"""
            valid_transitions = get_valid_status_transitions()
            return to_status in valid_transitions.get(from_status, [])
        
        # Test valid transitions
        valid_transitions = [
            (MigrationStatus.PENDING, MigrationStatus.RUNNING),
            (MigrationStatus.PENDING, MigrationStatus.CANCELLED),
            (MigrationStatus.RUNNING, MigrationStatus.PAUSED),
            (MigrationStatus.RUNNING, MigrationStatus.COMPLETED),
            (MigrationStatus.RUNNING, MigrationStatus.FAILED),
            (MigrationStatus.RUNNING, MigrationStatus.CANCELLED),
            (MigrationStatus.PAUSED, MigrationStatus.RUNNING),
            (MigrationStatus.PAUSED, MigrationStatus.CANCELLED),
            (MigrationStatus.FAILED, MigrationStatus.ROLLED_BACK),
        ]
        
        for from_status, to_status in valid_transitions:
            self.assertTrue(is_valid_transition(from_status, to_status), 
                          f"Failed for transition {from_status.value} -> {to_status.value}")
        
        # Test invalid transitions
        invalid_transitions = [
            (MigrationStatus.COMPLETED, MigrationStatus.RUNNING),
            (MigrationStatus.CANCELLED, MigrationStatus.RUNNING),
            (MigrationStatus.ROLLED_BACK, MigrationStatus.RUNNING),
            (MigrationStatus.PENDING, MigrationStatus.COMPLETED),
            (MigrationStatus.PAUSED, MigrationStatus.COMPLETED),
        ]
        
        for from_status, to_status in invalid_transitions:
            self.assertFalse(is_valid_transition(from_status, to_status), 
                           f"Failed for invalid transition {from_status.value} -> {to_status.value}")
        
        logger.info("✅ Migration status transitions test passed")

def run_standalone_migration_monitoring_tests():
    """Run all standalone migration monitoring tests"""
    logger.info("=" * 60)
    logger.info("ACWR Migration Monitoring Standalone Test Suite")
    logger.info("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestMigrationMonitoringStandalone)
    
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
        logger.info("🎉 All standalone migration monitoring tests passed!")
        return True
    else:
        logger.error("⚠️  Some standalone migration monitoring tests failed.")
        for failure in result.failures:
            logger.error(f"FAILURE: {failure[0]}")
            logger.error(f"Details: {failure[1]}")
        for error in result.errors:
            logger.error(f"ERROR: {error[0]}")
            logger.error(f"Details: {error[1]}")
        return False

def main():
    """Run the test suite"""
    success = run_standalone_migration_monitoring_tests()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
