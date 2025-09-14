#!/usr/bin/env python3
"""
ACWR Migration Service
Handles batch processing of historical data to migrate from standard ACWR calculations
to the new configurable ACWR system with exponential decay
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Generator
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import psycopg2
from psycopg2.extras import RealDictCursor

from acwr_configuration_service import ACWRConfigurationService
from acwr_calculation_service import ACWRCalculationService
from exponential_decay_engine import ExponentialDecayEngine
from acwr_migration_progress_tracker import (
    ACWRMigrationProgressTracker, ProgressEvent, ProgressEventType
)
import db_utils

logger = logging.getLogger(__name__)

@dataclass
class MigrationProgress:
    """Migration progress tracking"""
    user_id: int
    total_activities: int
    processed_activities: int
    successful_calculations: int
    failed_calculations: int
    start_time: datetime
    last_update: datetime
    status: str  # 'pending', 'running', 'completed', 'failed', 'paused'
    configuration_id: int
    error_message: Optional[str] = None
    current_batch: int = 0
    total_batches: int = 0

@dataclass
class MigrationResult:
    """Result of migration operation"""
    user_id: int
    migration_id: str
    start_time: datetime
    end_time: datetime
    total_activities: int
    successful_calculations: int
    failed_calculations: int
    configuration_id: int
    performance_metrics: Dict[str, Any]
    error_log: List[str]

@dataclass
class BatchResult:
    """Result of batch processing"""
    batch_id: int
    user_id: int
    activities_processed: int
    successful_calculations: int
    failed_calculations: int
    processing_time: float
    errors: List[str]

class ACWRMigrationService:
    """Service for migrating historical ACWR calculations"""
    
    def __init__(self):
        self.config_service = ACWRConfigurationService()
        self.calc_service = ACWRCalculationService()
        self.decay_engine = ExponentialDecayEngine()
        self.logger = logging.getLogger(__name__)
        
        # Migration configuration
        self.batch_size = 1000
        self.max_workers = 4
        self.timeout_seconds = 300
        
        # Progress tracking
        self.active_migrations: Dict[str, MigrationProgress] = {}
        self.migration_lock = threading.Lock()
        
        # Real-time progress tracker
        self.progress_tracker = ACWRMigrationProgressTracker()
        
        # Performance tracking
        self.performance_metrics = {
            'total_migrations': 0,
            'successful_migrations': 0,
            'failed_migrations': 0,
            'average_processing_time': 0.0,
            'total_activities_processed': 0
        }
    
    def create_migration(self, user_id: int, configuration_id: int, 
                        batch_size: Optional[int] = None) -> str:
        """Create a new migration operation"""
        migration_id = f"migration_{user_id}_{int(time.time())}"
        
        try:
            # Validate user and configuration
            if not self._validate_user_exists(user_id):
                raise ValueError(f"User {user_id} does not exist")
            
            if not self._validate_configuration_exists(configuration_id):
                raise ValueError(f"Configuration {configuration_id} does not exist")
            
            # Get total activity count
            total_activities = self._get_user_activity_count(user_id)
            if total_activities == 0:
                raise ValueError(f"User {user_id} has no activities to migrate")
            
            # Calculate batches
            batch_size = batch_size or self.batch_size
            total_batches = (total_activities + batch_size - 1) // batch_size
            
            # Create migration progress
            progress = MigrationProgress(
                user_id=user_id,
                total_activities=total_activities,
                processed_activities=0,
                successful_calculations=0,
                failed_calculations=0,
                start_time=datetime.now(),
                last_update=datetime.now(),
                status='pending',
                configuration_id=configuration_id,
                current_batch=0,
                total_batches=total_batches
            )
            
            # Store migration
            with self.migration_lock:
                self.active_migrations[migration_id] = progress
            
            # Publish migration created event
            self._publish_progress_event(
                ProgressEventType.MIGRATION_STARTED,
                migration_id,
                user_id,
                {
                    'total_activities': total_activities,
                    'total_batches': total_batches,
                    'batch_size': batch_size,
                    'configuration_id': configuration_id
                },
                f"Migration created for user {user_id} with {total_activities} activities"
            )
            
            # Log migration creation
            self.logger.info(f"Created migration {migration_id} for user {user_id} "
                           f"with {total_activities} activities in {total_batches} batches")
            
            return migration_id
            
        except Exception as e:
            self.logger.error(f"Failed to create migration for user {user_id}: {str(e)}")
            raise
    
    def execute_migration(self, migration_id: str, 
                         configuration_id: int) -> MigrationResult:
        """Execute the migration operation"""
        if migration_id not in self.active_migrations:
            raise ValueError(f"Migration {migration_id} not found")
        
        progress = self.active_migrations[migration_id]
        start_time = datetime.now()
        
        try:
            # Update status to running
            progress.status = 'running'
            progress.last_update = datetime.now()
            
            # Publish migration started event
            self._publish_progress_event(
                ProgressEventType.MIGRATION_STARTED,
                migration_id,
                progress.user_id,
                {
                    'status': 'running',
                    'total_activities': progress.total_activities,
                    'total_batches': progress.total_batches
                },
                f"Migration started for user {progress.user_id}"
            )
            
            self.logger.info(f"Starting migration {migration_id} for user {progress.user_id}")
            
            # Get user activities in batches
            activity_batches = self._get_user_activities_batched(
                progress.user_id, self.batch_size
            )
            
            # Process batches
            batch_results = []
            for batch_id, activities in enumerate(activity_batches, 1):
                if progress.status == 'paused':
                    self.logger.info(f"Migration {migration_id} paused at batch {batch_id}")
                    break
                
                progress.current_batch = batch_id
                progress.last_update = datetime.now()
                
                # Publish batch started event
                self._publish_progress_event(
                    ProgressEventType.BATCH_STARTED,
                    migration_id,
                    progress.user_id,
                    {
                        'batch_id': batch_id,
                        'total_batches': progress.total_batches,
                        'activities_in_batch': len(activities)
                    },
                    f"Starting batch {batch_id}/{progress.total_batches}"
                )
                
                # Process batch
                batch_result = self._process_activity_batch(
                    batch_id, progress.user_id, activities, configuration_id
                )
                batch_results.append(batch_result)
                
                # Update progress
                progress.processed_activities += batch_result.activities_processed
                progress.successful_calculations += batch_result.successful_calculations
                progress.failed_calculations += batch_result.failed_calculations
                progress.last_update = datetime.now()
                
                # Publish batch completed event
                self._publish_progress_event(
                    ProgressEventType.BATCH_COMPLETED,
                    migration_id,
                    progress.user_id,
                    {
                        'batch_id': batch_id,
                        'total_batches': progress.total_batches,
                        'activities_processed': batch_result.activities_processed,
                        'successful_calculations': batch_result.successful_calculations,
                        'failed_calculations': batch_result.failed_calculations,
                        'processing_time': batch_result.processing_time
                    },
                    f"Batch {batch_id}/{progress.total_batches} completed"
                )
                
                # Publish progress update
                elapsed_time = (datetime.now() - start_time).total_seconds()
                self._publish_progress_event(
                    ProgressEventType.PROGRESS_UPDATE,
                    migration_id,
                    progress.user_id,
                    {
                        'status': progress.status,
                        'current_batch': progress.current_batch,
                        'total_batches': progress.total_batches,
                        'processed_activities': progress.processed_activities,
                        'total_activities': progress.total_activities,
                        'successful_calculations': progress.successful_calculations,
                        'failed_calculations': progress.failed_calculations,
                        'elapsed_time': elapsed_time
                    },
                    f"Progress: {progress.processed_activities}/{progress.total_activities} activities"
                )
                
                # Log progress
                self.logger.info(f"Migration {migration_id} batch {batch_id}/{progress.total_batches} "
                               f"completed: {batch_result.activities_processed} activities processed")
            
            # Complete migration
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Create migration result
            result = MigrationResult(
                user_id=progress.user_id,
                migration_id=migration_id,
                start_time=start_time,
                end_time=end_time,
                total_activities=progress.total_activities,
                successful_calculations=progress.successful_calculations,
                failed_calculations=progress.failed_calculations,
                configuration_id=configuration_id,
                performance_metrics={
                    'processing_time_seconds': processing_time,
                    'activities_per_second': progress.total_activities / processing_time if processing_time > 0 else 0,
                    'success_rate': progress.successful_calculations / progress.total_activities if progress.total_activities > 0 else 0,
                    'batch_results': [asdict(br) for br in batch_results]
                },
                error_log=[error for br in batch_results for error in br.errors]
            )
            
            # Update status
            if progress.failed_calculations == 0:
                progress.status = 'completed'
                self.performance_metrics['successful_migrations'] += 1
                
                # Publish migration completed event
                self._publish_progress_event(
                    ProgressEventType.MIGRATION_COMPLETED,
                    migration_id,
                    progress.user_id,
                    {
                        'status': 'completed',
                        'total_activities': progress.total_activities,
                        'successful_calculations': progress.successful_calculations,
                        'failed_calculations': progress.failed_calculations,
                        'processing_time': processing_time
                    },
                    f"Migration completed successfully: {progress.successful_calculations}/{progress.total_activities} calculations"
                )
            else:
                progress.status = 'completed'  # Completed with some failures
                self.performance_metrics['successful_migrations'] += 1
                
                # Publish migration completed with warnings event
                self._publish_progress_event(
                    ProgressEventType.MIGRATION_COMPLETED,
                    migration_id,
                    progress.user_id,
                    {
                        'status': 'completed_with_warnings',
                        'total_activities': progress.total_activities,
                        'successful_calculations': progress.successful_calculations,
                        'failed_calculations': progress.failed_calculations,
                        'processing_time': processing_time
                    },
                    f"Migration completed with {progress.failed_calculations} failures: {progress.successful_calculations}/{progress.total_activities} calculations"
                )
            
            # Update performance metrics
            self.performance_metrics['total_migrations'] += 1
            self.performance_metrics['total_activities_processed'] += progress.total_activities
            self._update_average_processing_time(processing_time)
            
            # Store migration result
            self._store_migration_result(result)
            
            self.logger.info(f"Migration {migration_id} completed successfully: "
                           f"{progress.successful_calculations}/{progress.total_activities} "
                           f"calculations successful")
            
            return result
            
        except Exception as e:
            # Handle migration failure
            progress.status = 'failed'
            progress.error_message = str(e)
            progress.last_update = datetime.now()
            
            self.performance_metrics['failed_migrations'] += 1
            
            # Publish migration failed event
            self._publish_progress_event(
                ProgressEventType.MIGRATION_FAILED,
                migration_id,
                progress.user_id,
                {
                    'status': 'failed',
                    'error': str(e),
                    'total_activities': progress.total_activities,
                    'successful_calculations': progress.successful_calculations,
                    'failed_calculations': progress.failed_calculations
                },
                f"Migration failed: {str(e)}"
            )
            
            self.logger.error(f"Migration {migration_id} failed: {str(e)}")
            
            # Create failed result
            return MigrationResult(
                user_id=progress.user_id,
                migration_id=migration_id,
                start_time=start_time,
                end_time=datetime.now(),
                total_activities=progress.total_activities,
                successful_calculations=progress.successful_calculations,
                failed_calculations=progress.failed_calculations,
                configuration_id=configuration_id,
                performance_metrics={'error': str(e)},
                error_log=[str(e)]
            )
    
    def _process_activity_batch(self, batch_id: int, user_id: int, 
                               activities: List[Dict], configuration_id: int) -> BatchResult:
        """Process a batch of activities"""
        start_time = time.time()
        successful = 0
        failed = 0
        errors = []
        
        try:
            # Get configuration
            configuration = self.config_service.get_configuration_by_id(configuration_id)
            if not configuration:
                raise ValueError(f"Configuration {configuration_id} not found")
            
            # Process each activity
            for activity in activities:
                try:
                    # Calculate enhanced ACWR for this activity
                    # Convert date to string format if it's a datetime object
                    activity_date = activity['date']
                    if hasattr(activity_date, 'strftime'):
                        activity_date = activity_date.strftime('%Y-%m-%d')
                    elif isinstance(activity_date, str):
                        # Already a string, use as-is
                        pass
                    else:
                        # Convert to string
                        activity_date = str(activity_date)
                    
                    result = self.calc_service.calculate_acwr_for_user(
                        user_id=user_id,
                        activity_date=activity_date
                    )
                    
                    if result and result.get('success') and result.get('enhanced_acute_chronic_ratio') is not None:
                        # Store enhanced calculation
                        self._store_enhanced_calculation(
                            user_id, activity['activity_id'], result, configuration_id
                        )
                        successful += 1
                    else:
                        failed += 1
                        errors.append(f"Activity {activity['activity_id']}: No result returned")
                        
                except Exception as e:
                    failed += 1
                    error_msg = f"Activity {activity['activity_id']}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.warning(error_msg)
            
            processing_time = time.time() - start_time
            
            return BatchResult(
                batch_id=batch_id,
                user_id=user_id,
                activities_processed=len(activities),
                successful_calculations=successful,
                failed_calculations=failed,
                processing_time=processing_time,
                errors=errors
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Batch {batch_id} failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            
            return BatchResult(
                batch_id=batch_id,
                user_id=user_id,
                activities_processed=len(activities),
                successful_calculations=successful,
                failed_calculations=failed,
                processing_time=processing_time,
                errors=errors
            )
    
    def start_migration(self, migration_id: str) -> bool:
        """Start a migration by executing it"""
        try:
            if migration_id not in self.active_migrations:
                self.logger.error(f"Migration {migration_id} not found in active migrations")
                return False
            
            progress = self.active_migrations[migration_id]
            if progress.status != 'pending':
                self.logger.warning(f"Migration {migration_id} is not in pending status (current: {progress.status})")
                return False
            
            # Get the configuration ID from the migration progress
            configuration_id = progress.configuration_id
            
            self.logger.info(f"Starting migration {migration_id} for user {progress.user_id}")
            
            # Execute the migration
            result = self.execute_migration(migration_id, configuration_id)
            
            if result:
                self.logger.info(f"Migration {migration_id} started successfully")
                return True
            else:
                self.logger.error(f"Failed to start migration {migration_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting migration {migration_id}: {str(e)}")
            return False
    
    def get_migration_progress(self, migration_id: str) -> Optional[MigrationProgress]:
        """Get current progress of a migration"""
        return self.active_migrations.get(migration_id)
    
    def get_all_migration_progress(self) -> List[MigrationProgress]:
        """Get progress of all active migrations"""
        with self.migration_lock:
            return list(self.active_migrations.values())
    
    def pause_migration(self, migration_id: str) -> bool:
        """Pause a running migration"""
        if migration_id not in self.active_migrations:
            return False
        
        progress = self.active_migrations[migration_id]
        if progress.status == 'running':
            progress.status = 'paused'
            progress.last_update = datetime.now()
            self.logger.info(f"Migration {migration_id} paused")
            return True
        
        return False
    
    def resume_migration(self, migration_id: str) -> bool:
        """Resume a paused migration"""
        if migration_id not in self.active_migrations:
            return False
        
        progress = self.active_migrations[migration_id]
        if progress.status == 'paused':
            progress.status = 'running'
            progress.last_update = datetime.now()
            self.logger.info(f"Migration {migration_id} resumed")
            return True
        
        return False
    
    def cancel_migration(self, migration_id: str) -> bool:
        """Cancel a migration"""
        if migration_id not in self.active_migrations:
            return False
        
        progress = self.active_migrations[migration_id]
        if progress.status in ['pending', 'running', 'paused']:
            progress.status = 'cancelled'
            progress.last_update = datetime.now()
            self.logger.info(f"Migration {migration_id} cancelled")
            return True
        
        return False
    
    def get_migration_history(self, user_id: Optional[int] = None) -> List[MigrationResult]:
        """Get migration history"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    query = """
                        SELECT * FROM acwr_migration_history 
                        WHERE ($1 IS NULL OR user_id = $1)
                        ORDER BY start_time DESC
                        LIMIT 100
                    """
                    cursor.execute(query, (user_id,))
                    results = cursor.fetchall()
                    
                    return [MigrationResult(**dict(row)) for row in results]
                    
        except Exception as e:
            self.logger.error(f"Failed to get migration history: {str(e)}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get migration performance metrics"""
        return self.performance_metrics.copy()
    
    def _validate_user_exists(self, user_id: int) -> bool:
        """Validate that user exists"""
        try:
            # Use the correct table and column names
            query = "SELECT 1 FROM user_settings WHERE id = %s"
            result = db_utils.execute_query(query, (user_id,), fetch=True)
            return result is not None and len(result) > 0
        except Exception as e:
            self.logger.error(f"Error validating user {user_id}: {str(e)}")
            return False
    
    def _validate_configuration_exists(self, configuration_id: int) -> bool:
        """Validate that configuration exists"""
        try:
            configuration = self.config_service.get_configuration_by_id(configuration_id)
            return configuration is not None
        except Exception as e:
            self.logger.error(f"Error validating configuration {configuration_id}: {str(e)}")
            return False
    
    def _get_user_activity_count(self, user_id: int) -> int:
        """Get total activity count for user"""
        try:
            query = "SELECT COUNT(*) as total FROM activities WHERE user_id = %s"
            result = db_utils.execute_query(query, (user_id,), fetch=True)
            if result and len(result) > 0:
                return result[0]['total']
            return 0
        except Exception as e:
            self.logger.error(f"Error getting activity count for user {user_id}: {str(e)}")
            return 0
    
    def _get_user_activities_batched(self, user_id: int, batch_size: int) -> Generator[List[Dict], None, None]:
        """Get user activities in batches"""
        try:
            offset = 0
            while True:
                query = """
                    SELECT activity_id, date, trimp
                    FROM activities 
                    WHERE user_id = %s 
                    ORDER BY date ASC
                    LIMIT %s OFFSET %s
                """
                batch = db_utils.execute_query(query, (user_id, batch_size, offset), fetch=True)
                
                if not batch:
                    break
                
                yield batch
                offset += batch_size
                        
        except Exception as e:
            self.logger.error(f"Error getting activities for user {user_id}: {str(e)}")
            yield []
    
    def _store_enhanced_calculation(self, user_id: int, activity_id: int, 
                                   result: Dict, configuration_id: int):
        """Store enhanced ACWR calculation"""
        try:
            # Use the configuration service to store the calculation
            # This ensures we use the correct table structure
            config_service = ACWRConfigurationService()
            success = config_service.store_enhanced_calculation(result)
            
            if not success:
                raise Exception("Failed to store enhanced calculation")
                    
        except Exception as e:
            self.logger.error(f"Error storing enhanced calculation: {str(e)}")
            raise
    
    def _store_migration_result(self, result: MigrationResult):
        """Store migration result in database"""
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO acwr_migration_history 
                        (migration_id, user_id, start_time, end_time, total_activities,
                         successful_calculations, failed_calculations, configuration_id,
                         performance_metrics, error_log)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        result.migration_id, result.user_id, result.start_time,
                        result.end_time, result.total_activities,
                        result.successful_calculations, result.failed_calculations,
                        result.configuration_id, json.dumps(result.performance_metrics),
                        json.dumps(result.error_log)
                    ))
                    conn.commit()
                    
        except Exception as e:
            self.logger.error(f"Error storing migration result: {str(e)}")
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        total_migrations = self.performance_metrics['total_migrations']
        if total_migrations > 0:
            current_avg = self.performance_metrics['average_processing_time']
            new_avg = ((current_avg * (total_migrations - 1)) + processing_time) / total_migrations
            self.performance_metrics['average_processing_time'] = new_avg
        else:
            self.performance_metrics['average_processing_time'] = processing_time
    
    def _publish_progress_event(self, event_type: ProgressEventType, migration_id: str, 
                               user_id: int, data: Dict[str, Any], message: Optional[str] = None):
        """Publish a progress event to the tracker"""
        try:
            event = ProgressEvent(
                event_type=event_type,
                migration_id=migration_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data=data,
                message=message
            )
            self.progress_tracker.publish_event(event)
        except Exception as e:
            self.logger.error(f"Error publishing progress event: {str(e)}")
    
    def get_progress_tracker(self) -> ACWRMigrationProgressTracker:
        """Get the progress tracker instance"""
        return self.progress_tracker
