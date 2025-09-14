#!/usr/bin/env python3
"""
ACWR Migration Progress Tracker
Handles real-time progress tracking and updates for migration operations
"""

import logging
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import queue

logger = logging.getLogger(__name__)

class ProgressEventType(Enum):
    """Types of progress events"""
    MIGRATION_STARTED = "migration_started"
    MIGRATION_PAUSED = "migration_paused"
    MIGRATION_RESUMED = "migration_resumed"
    MIGRATION_CANCELLED = "migration_cancelled"
    MIGRATION_COMPLETED = "migration_completed"
    MIGRATION_FAILED = "migration_failed"
    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"
    BATCH_FAILED = "batch_failed"
    PROGRESS_UPDATE = "progress_update"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class ProgressEvent:
    """Progress event data"""
    event_type: ProgressEventType
    migration_id: str
    user_id: int
    timestamp: datetime
    data: Dict[str, Any]
    message: Optional[str] = None

@dataclass
class ProgressSnapshot:
    """Snapshot of current progress"""
    migration_id: str
    user_id: int
    status: str
    current_batch: int
    total_batches: int
    processed_activities: int
    total_activities: int
    successful_calculations: int
    failed_calculations: int
    progress_percentage: float
    estimated_completion: Optional[datetime]
    processing_rate: float  # activities per second
    elapsed_time: float  # seconds
    last_update: datetime

class ProgressSubscriber:
    """Subscriber for progress events"""
    
    def __init__(self, subscriber_id: str, callback: Callable[[ProgressEvent], None]):
        self.subscriber_id = subscriber_id
        self.callback = callback
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.is_active = True
    
    def notify(self, event: ProgressEvent):
        """Notify subscriber of progress event"""
        try:
            if self.is_active:
                self.callback(event)
                self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"Error notifying subscriber {self.subscriber_id}: {str(e)}")
            self.is_active = False

class ACWRMigrationProgressTracker:
    """Real-time progress tracker for migration operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Progress tracking
        self.active_migrations: Dict[str, ProgressSnapshot] = {}
        self.migration_history: List[ProgressEvent] = []
        
        # Subscribers
        self.subscribers: Dict[str, ProgressSubscriber] = {}
        self.subscriber_lock = threading.Lock()
        
        # Event queue for async processing
        self.event_queue = queue.Queue()
        self.event_processor_thread = None
        self.is_running = False
        
        # Performance tracking
        self.performance_metrics = {
            'total_events_processed': 0,
            'active_subscribers': 0,
            'average_event_processing_time': 0.0,
            'events_per_second': 0.0
        }
        
        # Start event processor
        self.start_event_processor()
    
    def start_event_processor(self):
        """Start the event processing thread"""
        if not self.is_running:
            self.is_running = True
            self.event_processor_thread = threading.Thread(
                target=self._process_events, daemon=True
            )
            self.event_processor_thread.start()
            self.logger.info("Progress tracker event processor started")
    
    def stop_event_processor(self):
        """Stop the event processing thread"""
        self.is_running = False
        if self.event_processor_thread:
            self.event_processor_thread.join(timeout=5)
        self.logger.info("Progress tracker event processor stopped")
    
    def subscribe(self, subscriber_id: str, callback: Callable[[ProgressEvent], None]) -> bool:
        """Subscribe to progress events"""
        try:
            with self.subscriber_lock:
                subscriber = ProgressSubscriber(subscriber_id, callback)
                self.subscribers[subscriber_id] = subscriber
                self.performance_metrics['active_subscribers'] = len(self.subscribers)
                
                self.logger.info(f"Subscriber {subscriber_id} added. Total subscribers: {len(self.subscribers)}")
                return True
                
        except Exception as e:
            self.logger.error(f"Error adding subscriber {subscriber_id}: {str(e)}")
            return False
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from progress events"""
        try:
            with self.subscriber_lock:
                if subscriber_id in self.subscribers:
                    del self.subscribers[subscriber_id]
                    self.performance_metrics['active_subscribers'] = len(self.subscribers)
                    
                    self.logger.info(f"Subscriber {subscriber_id} removed. Total subscribers: {len(self.subscribers)}")
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"Error removing subscriber {subscriber_id}: {str(e)}")
            return False
    
    def publish_event(self, event: ProgressEvent):
        """Publish a progress event"""
        try:
            # Add to event queue for async processing
            self.event_queue.put(event)
            
            # Update migration snapshot if it's a progress update
            if event.event_type == ProgressEventType.PROGRESS_UPDATE:
                self._update_migration_snapshot(event)
            
            # Add to history
            self.migration_history.append(event)
            
            # Keep history size manageable
            if len(self.migration_history) > 10000:
                self.migration_history = self.migration_history[-5000:]
                
        except Exception as e:
            self.logger.error(f"Error publishing event: {str(e)}")
    
    def _process_events(self):
        """Process events from the queue"""
        while self.is_running:
            try:
                # Get event with timeout
                event = self.event_queue.get(timeout=1.0)
                
                start_time = time.time()
                
                # Notify all subscribers
                with self.subscriber_lock:
                    active_subscribers = list(self.subscribers.values())
                
                for subscriber in active_subscribers:
                    if subscriber.is_active:
                        subscriber.notify(event)
                
                # Update performance metrics
                processing_time = time.time() - start_time
                self.performance_metrics['total_events_processed'] += 1
                self._update_processing_metrics(processing_time)
                
                self.event_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")
    
    def _update_migration_snapshot(self, event: ProgressEvent):
        """Update migration snapshot from progress event"""
        try:
            data = event.data
            migration_id = event.migration_id
            
            # Calculate progress percentage
            total_activities = data.get('total_activities', 0)
            processed_activities = data.get('processed_activities', 0)
            progress_percentage = (processed_activities / total_activities * 100) if total_activities > 0 else 0
            
            # Calculate processing rate
            elapsed_time = data.get('elapsed_time', 0)
            processing_rate = (processed_activities / elapsed_time) if elapsed_time > 0 else 0
            
            # Estimate completion time
            estimated_completion = None
            if processing_rate > 0 and processed_activities < total_activities:
                remaining_activities = total_activities - processed_activities
                estimated_seconds = remaining_activities / processing_rate
                estimated_completion = datetime.now() + timedelta(seconds=estimated_seconds)
            
            # Create or update snapshot
            snapshot = ProgressSnapshot(
                migration_id=migration_id,
                user_id=event.user_id,
                status=data.get('status', 'unknown'),
                current_batch=data.get('current_batch', 0),
                total_batches=data.get('total_batches', 0),
                processed_activities=processed_activities,
                total_activities=total_activities,
                successful_calculations=data.get('successful_calculations', 0),
                failed_calculations=data.get('failed_calculations', 0),
                progress_percentage=progress_percentage,
                estimated_completion=estimated_completion,
                processing_rate=processing_rate,
                elapsed_time=elapsed_time,
                last_update=event.timestamp
            )
            
            self.active_migrations[migration_id] = snapshot
            
        except Exception as e:
            self.logger.error(f"Error updating migration snapshot: {str(e)}")
    
    def _update_processing_metrics(self, processing_time: float):
        """Update event processing metrics"""
        try:
            total_events = self.performance_metrics['total_events_processed']
            current_avg = self.performance_metrics['average_event_processing_time']
            
            # Update average processing time
            new_avg = ((current_avg * (total_events - 1)) + processing_time) / total_events
            self.performance_metrics['average_event_processing_time'] = new_avg
            
            # Calculate events per second (simple moving average)
            if total_events > 0:
                self.performance_metrics['events_per_second'] = 1.0 / new_avg if new_avg > 0 else 0
                
        except Exception as e:
            self.logger.error(f"Error updating processing metrics: {str(e)}")
    
    def get_migration_progress(self, migration_id: str) -> Optional[ProgressSnapshot]:
        """Get current progress for a migration"""
        return self.active_migrations.get(migration_id)
    
    def get_all_migration_progress(self) -> List[ProgressSnapshot]:
        """Get progress for all active migrations"""
        return list(self.active_migrations.values())
    
    def get_migration_events(self, migration_id: str, limit: int = 100) -> List[ProgressEvent]:
        """Get events for a specific migration"""
        events = [event for event in self.migration_history if event.migration_id == migration_id]
        return events[-limit:] if limit > 0 else events
    
    def get_recent_events(self, limit: int = 100) -> List[ProgressEvent]:
        """Get recent events across all migrations"""
        return self.migration_history[-limit:] if limit > 0 else self.migration_history
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()
    
    def cleanup_inactive_subscribers(self, max_age_hours: int = 24):
        """Clean up inactive subscribers"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            with self.subscriber_lock:
                inactive_subscribers = [
                    sid for sid, sub in self.subscribers.items()
                    if sub.last_activity < cutoff_time or not sub.is_active
                ]
                
                for sid in inactive_subscribers:
                    del self.subscribers[sid]
                
                self.performance_metrics['active_subscribers'] = len(self.subscribers)
                
                if inactive_subscribers:
                    self.logger.info(f"Cleaned up {len(inactive_subscribers)} inactive subscribers")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up subscribers: {str(e)}")
    
    def cleanup_old_events(self, max_age_hours: int = 24):
        """Clean up old events from history"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            original_count = len(self.migration_history)
            self.migration_history = [
                event for event in self.migration_history
                if event.timestamp > cutoff_time
            ]
            
            removed_count = original_count - len(self.migration_history)
            if removed_count > 0:
                self.logger.info(f"Cleaned up {removed_count} old events")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up events: {str(e)}")
    
    def get_subscriber_stats(self) -> Dict[str, Any]:
        """Get subscriber statistics"""
        try:
            with self.subscriber_lock:
                active_count = sum(1 for sub in self.subscribers.values() if sub.is_active)
                inactive_count = len(self.subscribers) - active_count
                
                return {
                    'total_subscribers': len(self.subscribers),
                    'active_subscribers': active_count,
                    'inactive_subscribers': inactive_count,
                    'oldest_subscriber': min(
                        (sub.created_at for sub in self.subscribers.values()),
                        default=None
                    ),
                    'newest_subscriber': max(
                        (sub.created_at for sub in self.subscribers.values()),
                        default=None
                    )
                }
                
        except Exception as e:
            self.logger.error(f"Error getting subscriber stats: {str(e)}")
            return {}
    
    def export_progress_data(self, migration_id: str) -> Dict[str, Any]:
        """Export progress data for a migration"""
        try:
            snapshot = self.get_migration_progress(migration_id)
            events = self.get_migration_events(migration_id)
            
            return {
                'migration_id': migration_id,
                'current_snapshot': asdict(snapshot) if snapshot else None,
                'events': [asdict(event) for event in events],
                'export_timestamp': datetime.now().isoformat(),
                'total_events': len(events)
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting progress data: {str(e)}")
            return {}
    
    def __del__(self):
        """Cleanup when tracker is destroyed"""
        self.stop_event_processor()

