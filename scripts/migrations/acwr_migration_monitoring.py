#!/usr/bin/env python3
"""
ACWR Migration Monitoring and Logging System
Comprehensive monitoring, alerting, and logging for migration operations
"""

import logging
import time
import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import psycopg2
from psycopg2.extras import RealDictCursor

import db_utils

logger = logging.getLogger(__name__)

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
    user_id: Optional[int]
    timestamp: datetime
    level: LogLevel
    message: str
    details: Dict[str, Any]
    source: str
    thread_id: str
    execution_time: Optional[float] = None
    error_traceback: Optional[str] = None

@dataclass
class Alert:
    """Alert structure"""
    alert_id: str
    migration_id: str
    user_id: Optional[int]
    timestamp: datetime
    severity: AlertSeverity
    alert_type: str
    title: str
    message: str
    details: Dict[str, Any]
    acknowledged: bool = False
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class MonitoringEvent:
    """Monitoring event structure"""
    event_id: str
    migration_id: str
    user_id: Optional[int]
    timestamp: datetime
    event_type: MonitoringEventType
    data: Dict[str, Any]
    source: str

@dataclass
class MigrationHealthMetrics:
    """Migration health metrics"""
    migration_id: str
    timestamp: datetime
    status: MigrationStatus
    progress_percentage: float
    estimated_completion_time: Optional[datetime]
    error_count: int
    warning_count: int
    performance_score: float
    resource_usage: Dict[str, float]
    throughput_activities_per_second: float
    average_batch_time: float
    success_rate: float

class ACWRMigrationMonitor:
    """Comprehensive migration monitoring and logging system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Logging configuration
        self.log_queue = queue.Queue()
        self.alert_queue = queue.Queue()
        self.event_queue = queue.Queue()
        
        # Monitoring state
        self.active_migrations: Dict[str, Dict[str, Any]] = {}
        self.monitoring_threads: Dict[str, threading.Thread] = {}
        self.stop_monitoring = threading.Event()
        
        # Alert configuration
        self.alert_thresholds = {
            'error_rate': 0.05,  # 5% error rate
            'performance_degradation': 0.3,  # 30% performance drop
            'memory_usage': 0.85,  # 85% memory usage
            'cpu_usage': 0.90,  # 90% CPU usage
            'batch_timeout': 300,  # 5 minutes batch timeout
            'migration_timeout': 3600,  # 1 hour migration timeout
        }
        
        # Logging configuration
        self.log_retention_days = 30
        self.alert_retention_days = 90
        self.max_log_entries_per_migration = 10000
        
        # Start background processing
        self._start_background_processors()
    
    def start_migration_monitoring(self, migration_id: str, user_id: int, 
                                 configuration_id: int) -> bool:
        """Start monitoring a migration"""
        try:
            self.logger.info(f"Starting migration monitoring for {migration_id}")
            
            # Initialize migration monitoring data
            self.active_migrations[migration_id] = {
                'user_id': user_id,
                'configuration_id': configuration_id,
                'start_time': datetime.now(),
                'last_activity': datetime.now(),
                'status': MigrationStatus.RUNNING,
                'error_count': 0,
                'warning_count': 0,
                'batch_count': 0,
                'completed_batches': 0,
                'failed_batches': 0,
                'total_activities': 0,
                'processed_activities': 0
            }
            
            # Log migration start
            self.log_event(
                migration_id=migration_id,
                user_id=user_id,
                level=LogLevel.INFO,
                message=f"Migration monitoring started for migration {migration_id}",
                details={
                    'configuration_id': configuration_id,
                    'start_time': datetime.now().isoformat()
                },
                source="migration_monitor"
            )
            
            # Publish monitoring event
            self.publish_event(
                migration_id=migration_id,
                user_id=user_id,
                event_type=MonitoringEventType.MIGRATION_STARTED,
                data={
                    'configuration_id': configuration_id,
                    'start_time': datetime.now().isoformat()
                },
                source="migration_monitor"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting migration monitoring: {str(e)}")
            return False
    
    def stop_migration_monitoring(self, migration_id: str, final_status: MigrationStatus) -> bool:
        """Stop monitoring a migration"""
        try:
            if migration_id not in self.active_migrations:
                self.logger.warning(f"Migration {migration_id} not found in active migrations")
                return False
            
            migration_data = self.active_migrations[migration_id]
            
            # Update final status
            migration_data['status'] = final_status
            migration_data['end_time'] = datetime.now()
            migration_data['duration'] = (
                migration_data['end_time'] - migration_data['start_time']
            ).total_seconds()
            
            # Log migration completion
            self.log_event(
                migration_id=migration_id,
                user_id=migration_data['user_id'],
                level=LogLevel.INFO,
                message=f"Migration monitoring stopped for migration {migration_id}",
                details={
                    'final_status': final_status.value,
                    'end_time': migration_data['end_time'].isoformat(),
                    'duration_seconds': migration_data['duration'],
                    'total_batches': migration_data['batch_count'],
                    'completed_batches': migration_data['completed_batches'],
                    'failed_batches': migration_data['failed_batches'],
                    'total_activities': migration_data['total_activities'],
                    'processed_activities': migration_data['processed_activities']
                },
                source="migration_monitor"
            )
            
            # Publish monitoring event
            event_type = MonitoringEventType.MIGRATION_COMPLETED
            if final_status == MigrationStatus.FAILED:
                event_type = MonitoringEventType.MIGRATION_FAILED
            elif final_status == MigrationStatus.CANCELLED:
                event_type = MonitoringEventType.MIGRATION_CANCELLED
            
            self.publish_event(
                migration_id=migration_id,
                user_id=migration_data['user_id'],
                event_type=event_type,
                data={
                    'final_status': final_status.value,
                    'end_time': migration_data['end_time'].isoformat(),
                    'duration_seconds': migration_data['duration']
                },
                source="migration_monitor"
            )
            
            # Remove from active migrations
            del self.active_migrations[migration_id]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping migration monitoring: {str(e)}")
            return False
    
    def log_event(self, migration_id: str, user_id: Optional[int], level: LogLevel, 
                  message: str, details: Dict[str, Any], source: str, 
                  execution_time: Optional[float] = None, error_traceback: Optional[str] = None):
        """Log an event"""
        try:
            log_entry = LogEntry(
                log_id=f"log_{migration_id}_{int(time.time() * 1000)}",
                migration_id=migration_id,
                user_id=user_id,
                timestamp=datetime.now(),
                level=level,
                message=message,
                details=details,
                source=source,
                thread_id=threading.current_thread().name,
                execution_time=execution_time,
                error_traceback=error_traceback
            )
            
            # Add to queue for background processing
            self.log_queue.put(log_entry)
            
            # Update migration data if active
            if migration_id in self.active_migrations:
                migration_data = self.active_migrations[migration_id]
                migration_data['last_activity'] = datetime.now()
                
                if level == LogLevel.ERROR:
                    migration_data['error_count'] += 1
                elif level == LogLevel.WARNING:
                    migration_data['warning_count'] += 1
            
            # Check for alert conditions
            self._check_alert_conditions(migration_id, log_entry)
            
        except Exception as e:
            self.logger.error(f"Error logging event: {str(e)}")
    
    def log_batch_event(self, migration_id: str, user_id: int, batch_number: int, 
                       event_type: str, success: bool, activities_count: int, 
                       processing_time: float, error_message: Optional[str] = None):
        """Log a batch processing event"""
        try:
            level = LogLevel.INFO if success else LogLevel.ERROR
            message = f"Batch {batch_number} {'completed' if success else 'failed'}"
            
            details = {
                'batch_number': batch_number,
                'success': success,
                'activities_count': activities_count,
                'processing_time': processing_time,
                'throughput': activities_count / processing_time if processing_time > 0 else 0
            }
            
            if error_message:
                details['error_message'] = error_message
            
            self.log_event(
                migration_id=migration_id,
                user_id=user_id,
                level=level,
                message=message,
                details=details,
                source="batch_processor",
                execution_time=processing_time
            )
            
            # Update migration data
            if migration_id in self.active_migrations:
                migration_data = self.active_migrations[migration_id]
                migration_data['batch_count'] += 1
                migration_data['total_activities'] += activities_count
                
                if success:
                    migration_data['completed_batches'] += 1
                    migration_data['processed_activities'] += activities_count
                else:
                    migration_data['failed_batches'] += 1
            
            # Publish batch event
            event_type_enum = MonitoringEventType.BATCH_COMPLETED if success else MonitoringEventType.BATCH_FAILED
            self.publish_event(
                migration_id=migration_id,
                user_id=user_id,
                event_type=event_type_enum,
                data=details,
                source="batch_processor"
            )
            
        except Exception as e:
            self.logger.error(f"Error logging batch event: {str(e)}")
    
    def log_error(self, migration_id: str, user_id: Optional[int], error: Exception, 
                  context: str, details: Dict[str, Any] = None):
        """Log an error with full context"""
        try:
            error_details = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                'timestamp': datetime.now().isoformat()
            }
            
            if details:
                error_details.update(details)
            
            self.log_event(
                migration_id=migration_id,
                user_id=user_id,
                level=LogLevel.ERROR,
                message=f"Error in {context}: {str(error)}",
                details=error_details,
                source="error_handler",
                error_traceback=traceback.format_exc()
            )
            
            # Create alert for critical errors
            if isinstance(error, (MemoryError, SystemError, OSError)):
                self.create_alert(
                    migration_id=migration_id,
                    user_id=user_id,
                    severity=AlertSeverity.CRITICAL,
                    alert_type="system_error",
                    title=f"Critical System Error in {context}",
                    message=str(error),
                    details=error_details
                )
            
        except Exception as e:
            self.logger.error(f"Error logging error: {str(e)}")
    
    def create_alert(self, migration_id: str, user_id: Optional[int], 
                    severity: AlertSeverity, alert_type: str, title: str, 
                    message: str, details: Dict[str, Any] = None):
        """Create an alert"""
        try:
            alert = Alert(
                alert_id=f"alert_{migration_id}_{int(time.time() * 1000)}",
                migration_id=migration_id,
                user_id=user_id,
                timestamp=datetime.now(),
                severity=severity,
                alert_type=alert_type,
                title=title,
                message=message,
                details=details or {}
            )
            
            # Add to queue for background processing
            self.alert_queue.put(alert)
            
            # Log alert creation
            self.log_event(
                migration_id=migration_id,
                user_id=user_id,
                level=LogLevel.WARNING,
                message=f"Alert created: {title}",
                details={
                    'alert_id': alert.alert_id,
                    'severity': severity.value,
                    'alert_type': alert_type
                },
                source="alert_system"
            )
            
            # Publish alert event
            self.publish_event(
                migration_id=migration_id,
                user_id=user_id,
                event_type=MonitoringEventType.ALERT_TRIGGERED,
                data={
                    'alert_id': alert.alert_id,
                    'severity': severity.value,
                    'alert_type': alert_type,
                    'title': title,
                    'message': message
                },
                source="alert_system"
            )
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {str(e)}")
    
    def publish_event(self, migration_id: str, user_id: Optional[int], 
                     event_type: MonitoringEventType, data: Dict[str, Any], 
                     source: str):
        """Publish a monitoring event"""
        try:
            event = MonitoringEvent(
                event_id=f"event_{migration_id}_{int(time.time() * 1000)}",
                migration_id=migration_id,
                user_id=user_id,
                timestamp=datetime.now(),
                event_type=event_type,
                data=data,
                source=source
            )
            
            # Add to queue for background processing
            self.event_queue.put(event)
            
        except Exception as e:
            self.logger.error(f"Error publishing event: {str(e)}")
    
    def get_migration_health_metrics(self, migration_id: str) -> Optional[MigrationHealthMetrics]:
        """Get health metrics for a migration"""
        try:
            if migration_id not in self.active_migrations:
                return None
            
            migration_data = self.active_migrations[migration_id]
            
            # Calculate progress percentage
            progress_percentage = 0.0
            if migration_data['total_activities'] > 0:
                progress_percentage = (
                    migration_data['processed_activities'] / migration_data['total_activities']
                ) * 100
            
            # Calculate success rate
            success_rate = 0.0
            if migration_data['batch_count'] > 0:
                success_rate = migration_data['completed_batches'] / migration_data['batch_count']
            
            # Calculate performance score
            performance_score = self._calculate_performance_score(migration_data)
            
            # Get resource usage (simplified)
            resource_usage = {
                'memory_percent': 0.0,  # Would be populated by actual monitoring
                'cpu_percent': 0.0,
                'disk_io_percent': 0.0
            }
            
            # Calculate throughput
            duration = (datetime.now() - migration_data['start_time']).total_seconds()
            throughput = 0.0
            if duration > 0:
                throughput = migration_data['processed_activities'] / duration
            
            # Calculate average batch time
            average_batch_time = 0.0
            if migration_data['completed_batches'] > 0:
                # Simplified calculation
                average_batch_time = duration / migration_data['completed_batches']
            
            return MigrationHealthMetrics(
                migration_id=migration_id,
                timestamp=datetime.now(),
                status=migration_data['status'],
                progress_percentage=progress_percentage,
                estimated_completion_time=None,  # Would be calculated based on current rate
                error_count=migration_data['error_count'],
                warning_count=migration_data['warning_count'],
                performance_score=performance_score,
                resource_usage=resource_usage,
                throughput_activities_per_second=throughput,
                average_batch_time=average_batch_time,
                success_rate=success_rate
            )
            
        except Exception as e:
            self.logger.error(f"Error getting migration health metrics: {str(e)}")
            return None
    
    def get_migration_logs(self, migration_id: str, level: Optional[LogLevel] = None, 
                          limit: int = 1000) -> List[LogEntry]:
        """Get logs for a migration"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT * FROM acwr_migration_logs 
                        WHERE migration_id = %s
                    """
                    params = [migration_id]
                    
                    if level:
                        query += " AND level = %s"
                        params.append(level.value)
                    
                    query += " ORDER BY timestamp DESC LIMIT %s"
                    params.append(limit)
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    return [self._dict_to_log_entry(dict(row)) for row in results]
                    
        except Exception as e:
            self.logger.error(f"Error getting migration logs: {str(e)}")
            return []
    
    def get_migration_alerts(self, migration_id: str, severity: Optional[AlertSeverity] = None,
                           acknowledged: Optional[bool] = None) -> List[Alert]:
        """Get alerts for a migration"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT * FROM acwr_migration_alerts 
                        WHERE migration_id = %s
                    """
                    params = [migration_id]
                    
                    if severity:
                        query += " AND severity = %s"
                        params.append(severity.value)
                    
                    if acknowledged is not None:
                        query += " AND acknowledged = %s"
                        params.append(acknowledged)
                    
                    query += " ORDER BY timestamp DESC"
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    return [self._dict_to_alert(dict(row)) for row in results]
                    
        except Exception as e:
            self.logger.error(f"Error getting migration alerts: {str(e)}")
            return []
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: int) -> bool:
        """Acknowledge an alert"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE acwr_migration_alerts 
                        SET acknowledged = TRUE, acknowledged_by = %s, acknowledged_at = %s
                        WHERE alert_id = %s
                    """, (acknowledged_by, datetime.now(), alert_id))
                    
                    conn.commit()
                    return cursor.rowcount > 0
                    
        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {str(e)}")
            return False
    
    def _start_background_processors(self):
        """Start background processing threads"""
        try:
            # Start log processor
            log_thread = threading.Thread(target=self._process_log_queue, daemon=True)
            log_thread.start()
            
            # Start alert processor
            alert_thread = threading.Thread(target=self._process_alert_queue, daemon=True)
            alert_thread.start()
            
            # Start event processor
            event_thread = threading.Thread(target=self._process_event_queue, daemon=True)
            event_thread.start()
            
            # Start cleanup processor
            cleanup_thread = threading.Thread(target=self._process_cleanup, daemon=True)
            cleanup_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting background processors: {str(e)}")
    
    def _process_log_queue(self):
        """Process log queue in background"""
        while not self.stop_monitoring.is_set():
            try:
                # Get log entry from queue with timeout
                log_entry = self.log_queue.get(timeout=1)
                
                # Store in database
                self._store_log_entry(log_entry)
                
                # Mark task as done
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing log queue: {str(e)}")
    
    def _process_alert_queue(self):
        """Process alert queue in background"""
        while not self.stop_monitoring.is_set():
            try:
                # Get alert from queue with timeout
                alert = self.alert_queue.get(timeout=1)
                
                # Store in database
                self._store_alert(alert)
                
                # Mark task as done
                self.alert_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing alert queue: {str(e)}")
    
    def _process_event_queue(self):
        """Process event queue in background"""
        while not self.stop_monitoring.is_set():
            try:
                # Get event from queue with timeout
                event = self.event_queue.get(timeout=1)
                
                # Store in database
                self._store_event(event)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event queue: {str(e)}")
    
    def _process_cleanup(self):
        """Process cleanup tasks in background"""
        while not self.stop_monitoring.is_set():
            try:
                # Wait for cleanup interval
                time.sleep(3600)  # 1 hour
                
                # Cleanup old logs
                self._cleanup_old_logs()
                
                # Cleanup old alerts
                self._cleanup_old_alerts()
                
            except Exception as e:
                self.logger.error(f"Error in cleanup process: {str(e)}")
    
    def _store_log_entry(self, log_entry: LogEntry):
        """Store log entry in database"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO acwr_migration_logs 
                        (log_id, migration_id, user_id, timestamp, level, message, details, 
                         source, thread_id, execution_time, error_traceback)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        log_entry.log_id,
                        log_entry.migration_id,
                        log_entry.user_id,
                        log_entry.timestamp,
                        log_entry.level.value,
                        log_entry.message,
                        json.dumps(log_entry.details),
                        log_entry.source,
                        log_entry.thread_id,
                        log_entry.execution_time,
                        log_entry.error_traceback
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error storing log entry: {str(e)}")
    
    def _store_alert(self, alert: Alert):
        """Store alert in database"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO acwr_migration_alerts 
                        (alert_id, migration_id, user_id, timestamp, severity, alert_type, 
                         title, message, details, acknowledged, acknowledged_by, acknowledged_at, 
                         resolved, resolved_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        alert.alert_id,
                        alert.migration_id,
                        alert.user_id,
                        alert.timestamp,
                        alert.severity.value,
                        alert.alert_type,
                        alert.title,
                        alert.message,
                        json.dumps(alert.details),
                        alert.acknowledged,
                        alert.acknowledged_by,
                        alert.acknowledged_at,
                        alert.resolved,
                        alert.resolved_at
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error storing alert: {str(e)}")
    
    def _store_event(self, event: MonitoringEvent):
        """Store event in database"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO acwr_migration_events 
                        (event_id, migration_id, user_id, timestamp, event_type, data, source)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        event.event_id,
                        event.migration_id,
                        event.user_id,
                        event.timestamp,
                        event.event_type.value,
                        json.dumps(event.data),
                        event.source
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error storing event: {str(e)}")
    
    def _check_alert_conditions(self, migration_id: str, log_entry: LogEntry):
        """Check for alert conditions based on log entry"""
        try:
            if migration_id not in self.active_migrations:
                return
            
            migration_data = self.active_migrations[migration_id]
            
            # Check error rate
            if migration_data['batch_count'] > 10:
                error_rate = migration_data['failed_batches'] / migration_data['batch_count']
                if error_rate > self.alert_thresholds['error_rate']:
                    self.create_alert(
                        migration_id=migration_id,
                        user_id=migration_data['user_id'],
                        severity=AlertSeverity.HIGH,
                        alert_type="high_error_rate",
                        title="High Error Rate Detected",
                        message=f"Error rate is {error_rate:.2%}, exceeding threshold of {self.alert_thresholds['error_rate']:.2%}",
                        details={'error_rate': error_rate, 'threshold': self.alert_thresholds['error_rate']}
                    )
            
            # Check for timeout conditions
            if log_entry.level == LogLevel.ERROR and "timeout" in log_entry.message.lower():
                self.create_alert(
                    migration_id=migration_id,
                    user_id=migration_data['user_id'],
                    severity=AlertSeverity.MEDIUM,
                    alert_type="timeout_error",
                    title="Timeout Error Detected",
                    message=log_entry.message,
                    details=log_entry.details
                )
            
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {str(e)}")
    
    def _calculate_performance_score(self, migration_data: Dict[str, Any]) -> float:
        """Calculate performance score for migration"""
        try:
            score = 100.0
            
            # Deduct points for errors
            if migration_data['error_count'] > 0:
                score -= min(50, migration_data['error_count'] * 5)
            
            # Deduct points for warnings
            if migration_data['warning_count'] > 0:
                score -= min(20, migration_data['warning_count'] * 2)
            
            # Deduct points for failed batches
            if migration_data['failed_batches'] > 0:
                failure_rate = migration_data['failed_batches'] / max(1, migration_data['batch_count'])
                score -= failure_rate * 30
            
            return max(0, score)
            
        except Exception as e:
            self.logger.error(f"Error calculating performance score: {str(e)}")
            return 0.0
    
    def _cleanup_old_logs(self):
        """Cleanup old log entries"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.log_retention_days)
            
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM acwr_migration_logs 
                        WHERE timestamp < %s
                    """, (cutoff_date,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        self.logger.info(f"Cleaned up {deleted_count} old log entries")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {str(e)}")
    
    def _cleanup_old_alerts(self):
        """Cleanup old alerts"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.alert_retention_days)
            
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        DELETE FROM acwr_migration_alerts 
                        WHERE timestamp < %s AND resolved = TRUE
                    """, (cutoff_date,))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    
                    if deleted_count > 0:
                        self.logger.info(f"Cleaned up {deleted_count} old alerts")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up old alerts: {str(e)}")
    
    def _dict_to_log_entry(self, data: Dict[str, Any]) -> LogEntry:
        """Convert dictionary to LogEntry"""
        return LogEntry(
            log_id=data['log_id'],
            migration_id=data['migration_id'],
            user_id=data['user_id'],
            timestamp=data['timestamp'],
            level=LogLevel(data['level']),
            message=data['message'],
            details=json.loads(data['details']) if data['details'] else {},
            source=data['source'],
            thread_id=data['thread_id'],
            execution_time=data['execution_time'],
            error_traceback=data['error_traceback']
        )
    
    def _dict_to_alert(self, data: Dict[str, Any]) -> Alert:
        """Convert dictionary to Alert"""
        return Alert(
            alert_id=data['alert_id'],
            migration_id=data['migration_id'],
            user_id=data['user_id'],
            timestamp=data['timestamp'],
            severity=AlertSeverity(data['severity']),
            alert_type=data['alert_type'],
            title=data['title'],
            message=data['message'],
            details=json.loads(data['details']) if data['details'] else {},
            acknowledged=data['acknowledged'],
            acknowledged_by=data['acknowledged_by'],
            acknowledged_at=data['acknowledged_at'],
            resolved=data['resolved'],
            resolved_at=data['resolved_at']
        )
    
    def shutdown(self):
        """Shutdown the monitoring system"""
        try:
            self.logger.info("Shutting down migration monitoring system")
            
            # Signal stop
            self.stop_monitoring.set()
            
            # Wait for queues to empty
            self.log_queue.join()
            self.alert_queue.join()
            self.event_queue.join()
            
            self.logger.info("Migration monitoring system shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error shutting down monitoring system: {str(e)}")

