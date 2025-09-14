#!/usr/bin/env python3
"""
ACWR Migration Batch Processor
Handles optimized batch processing of large datasets with memory management and performance optimization
"""

import logging
import time
import gc
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Generator
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
import numpy as np

from acwr_migration_service import ACWRMigrationService, MigrationProgress, BatchResult
from acwr_migration_progress_tracker import ACWRMigrationProgressTracker, ProgressEvent, ProgressEventType
import db_utils

logger = logging.getLogger(__name__)

class BatchProcessingStrategy(Enum):
    """Batch processing strategies"""
    SEQUENTIAL = "sequential"           # Process batches one by one
    PARALLEL = "parallel"              # Process multiple batches in parallel
    ADAPTIVE = "adaptive"              # Adapt strategy based on system resources
    MEMORY_OPTIMIZED = "memory_optimized"  # Optimize for memory usage
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # Optimize for speed

class MemoryThreshold(Enum):
    """Memory usage thresholds"""
    LOW = 0.5      # 50% memory usage
    MEDIUM = 0.7   # 70% memory usage
    HIGH = 0.85    # 85% memory usage
    CRITICAL = 0.95 # 95% memory usage

@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    batch_size: int = 1000
    max_parallel_batches: int = 4
    memory_threshold: float = 0.8
    processing_strategy: BatchProcessingStrategy = BatchProcessingStrategy.ADAPTIVE
    enable_memory_monitoring: bool = True
    enable_performance_monitoring: bool = True
    auto_gc_frequency: int = 10  # Run garbage collection every N batches
    max_retry_attempts: int = 3
    retry_delay_seconds: int = 5
    progress_reporting_interval: int = 100  # Report progress every N activities

@dataclass
class SystemResourceMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    memory_used_gb: float
    disk_io_percent: float
    timestamp: datetime

@dataclass
class BatchProcessingMetrics:
    """Batch processing performance metrics"""
    total_batches: int
    completed_batches: int
    failed_batches: int
    total_activities_processed: int
    total_processing_time: float
    average_batch_time: float
    memory_peak_usage: float
    memory_average_usage: float
    cpu_peak_usage: float
    cpu_average_usage: float
    throughput_activities_per_second: float
    error_rate: float

class ACWRMigrationBatchProcessor:
    """Advanced batch processor for ACWR migration operations"""
    
    def __init__(self, config: Optional[BatchProcessingConfig] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or BatchProcessingConfig()
        self.migration_service = ACWRMigrationService()
        self.progress_tracker = ACWRMigrationProgressTracker()
        
        # Processing state
        self.is_processing = False
        self.current_migration_id: Optional[str] = None
        self.processing_lock = threading.Lock()
        
        # Metrics tracking
        self.metrics = BatchProcessingMetrics(
            total_batches=0,
            completed_batches=0,
            failed_batches=0,
            total_activities_processed=0,
            total_processing_time=0.0,
            average_batch_time=0.0,
            memory_peak_usage=0.0,
            memory_average_usage=0.0,
            cpu_peak_usage=0.0,
            cpu_average_usage=0.0,
            throughput_activities_per_second=0.0,
            error_rate=0.0
        )
        
        # Resource monitoring
        self.resource_metrics: List[SystemResourceMetrics] = []
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
        # Performance optimization
        self.batch_cache: Dict[str, List[Dict]] = {}
        self.cache_lock = threading.Lock()
    
    def process_migration_batches(self, migration_id: str, user_ids: List[int], 
                                 configuration_id: int) -> BatchProcessingMetrics:
        """Process migration in optimized batches"""
        try:
            with self.processing_lock:
                if self.is_processing:
                    raise RuntimeError("Batch processing is already in progress")
                
                self.is_processing = True
                self.current_migration_id = migration_id
                
                self.logger.info(f"Starting batch processing for migration {migration_id}")
                
                # Initialize metrics
                self._initialize_metrics()
                
                # Start resource monitoring
                if self.config.enable_memory_monitoring:
                    self._start_resource_monitoring()
                
                # Process batches based on strategy
                if self.config.processing_strategy == BatchProcessingStrategy.SEQUENTIAL:
                    self._process_sequential_batches(migration_id, user_ids, configuration_id)
                elif self.config.processing_strategy == BatchProcessingStrategy.PARALLEL:
                    self._process_parallel_batches(migration_id, user_ids, configuration_id)
                elif self.config.processing_strategy == BatchProcessingStrategy.ADAPTIVE:
                    self._process_adaptive_batches(migration_id, user_ids, configuration_id)
                elif self.config.processing_strategy == BatchProcessingStrategy.MEMORY_OPTIMIZED:
                    self._process_memory_optimized_batches(migration_id, user_ids, configuration_id)
                elif self.config.processing_strategy == BatchProcessingStrategy.PERFORMANCE_OPTIMIZED:
                    self._process_performance_optimized_batches(migration_id, user_ids, configuration_id)
                else:
                    raise ValueError(f"Unknown processing strategy: {self.config.processing_strategy}")
                
                # Finalize metrics
                self._finalize_metrics()
                
                self.logger.info(f"Batch processing completed for migration {migration_id}")
                return self.metrics
                
        except Exception as e:
            self.logger.error(f"Error in batch processing: {str(e)}")
            raise
        finally:
            self.is_processing = False
            self.current_migration_id = None
            if self.config.enable_memory_monitoring:
                self._stop_resource_monitoring()
    
    def _process_sequential_batches(self, migration_id: str, user_ids: List[int], 
                                   configuration_id: int):
        """Process batches sequentially"""
        self.logger.info("Processing batches sequentially")
        
        for user_id in user_ids:
            if not self.is_processing:
                break
                
            # Get user activities in batches
            for batch_data in self._get_user_activities_batches(user_id, configuration_id):
                if not self.is_processing:
                    break
                
                self._process_single_batch(migration_id, user_id, batch_data, configuration_id)
    
    def _process_parallel_batches(self, migration_id: str, user_ids: List[int], 
                                 configuration_id: int):
        """Process batches in parallel"""
        self.logger.info(f"Processing batches in parallel (max {self.config.max_parallel_batches} batches)")
        
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_parallel_batches) as executor:
            futures = []
            
            for user_id in user_ids:
                if not self.is_processing:
                    break
                
                # Submit batch processing tasks
                for batch_data in self._get_user_activities_batches(user_id, configuration_id):
                    if not self.is_processing:
                        break
                    
                    future = executor.submit(
                        self._process_single_batch, 
                        migration_id, user_id, batch_data, configuration_id
                    )
                    futures.append(future)
                    
                    # Limit concurrent batches based on memory usage
                    if self._should_limit_concurrent_batches():
                        # Wait for some batches to complete
                        completed_futures = [f for f in futures if f.done()]
                        if len(completed_futures) >= self.config.max_parallel_batches // 2:
                            concurrent.futures.wait(completed_futures, return_when=concurrent.futures.FIRST_COMPLETED)
            
            # Wait for all batches to complete
            concurrent.futures.wait(futures)
    
    def _process_adaptive_batches(self, migration_id: str, user_ids: List[int], 
                                 configuration_id: int):
        """Process batches with adaptive strategy based on system resources"""
        self.logger.info("Processing batches with adaptive strategy")
        
        for user_id in user_ids:
            if not self.is_processing:
                break
            
            # Determine optimal batch size based on current resources
            optimal_batch_size = self._calculate_optimal_batch_size()
            
            # Get user activities with optimal batch size
            for batch_data in self._get_user_activities_batches(user_id, configuration_id, optimal_batch_size):
                if not self.is_processing:
                    break
                
                # Choose processing method based on current resources
                if self._should_use_parallel_processing():
                    self._process_single_batch_parallel(migration_id, user_id, batch_data, configuration_id)
                else:
                    self._process_single_batch(migration_id, user_id, batch_data, configuration_id)
                
                # Adaptive memory management
                self._adaptive_memory_management()
    
    def _process_memory_optimized_batches(self, migration_id: str, user_ids: List[int], 
                                         configuration_id: int):
        """Process batches optimized for memory usage"""
        self.logger.info("Processing batches with memory optimization")
        
        # Use smaller batch sizes and aggressive memory management
        original_batch_size = self.config.batch_size
        self.config.batch_size = min(500, self.config.batch_size)
        
        try:
            for user_id in user_ids:
                if not self.is_processing:
                    break
                
                for batch_data in self._get_user_activities_batches(user_id, configuration_id):
                    if not self.is_processing:
                        break
                    
                    # Check memory before processing
                    if self._is_memory_pressure_high():
                        self._aggressive_memory_cleanup()
                        time.sleep(1)  # Brief pause to allow memory cleanup
                    
                    self._process_single_batch(migration_id, user_id, batch_data, configuration_id)
                    
                    # Aggressive garbage collection
                    if self.metrics.completed_batches % 5 == 0:
                        gc.collect()
                        
        finally:
            # Restore original batch size
            self.config.batch_size = original_batch_size
    
    def _process_performance_optimized_batches(self, migration_id: str, user_ids: List[int], 
                                              configuration_id: int):
        """Process batches optimized for performance"""
        self.logger.info("Processing batches with performance optimization")
        
        # Use larger batch sizes and parallel processing
        original_batch_size = self.config.batch_size
        self.config.batch_size = max(2000, self.config.batch_size)
        
        try:
            # Pre-load all user data for better caching
            self._preload_user_data(user_ids, configuration_id)
            
            # Use parallel processing with optimized settings
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_parallel_batches * 2) as executor:
                futures = []
                
                for user_id in user_ids:
                    if not self.is_processing:
                        break
                    
                    for batch_data in self._get_user_activities_batches(user_id, configuration_id):
                        if not self.is_processing:
                            break
                        
                        future = executor.submit(
                            self._process_single_batch_optimized, 
                            migration_id, user_id, batch_data, configuration_id
                        )
                        futures.append(future)
                
                # Wait for all batches to complete
                concurrent.futures.wait(futures)
                
        finally:
            # Restore original batch size
            self.config.batch_size = original_batch_size
            # Clear preloaded data
            self._clear_preloaded_data()
    
    def _process_single_batch(self, migration_id: str, user_id: int, 
                             batch_data: List[Dict], configuration_id: int) -> BatchResult:
        """Process a single batch of activities"""
        start_time = time.time()
        
        try:
            # Update metrics
            self.metrics.total_batches += 1
            
            # Process batch using migration service
            batch_result = self.migration_service._process_activity_batch(
                migration_id, user_id, batch_data, configuration_id
            )
            
            # Update metrics
            self.metrics.completed_batches += 1
            self.metrics.total_activities_processed += len(batch_data)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            self.metrics.total_processing_time += processing_time
            self.metrics.average_batch_time = (
                self.metrics.total_processing_time / self.metrics.completed_batches
            )
            
            # Update throughput
            self.metrics.throughput_activities_per_second = (
                self.metrics.total_activities_processed / self.metrics.total_processing_time
            )
            
            # Publish progress event
            self._publish_batch_progress_event(migration_id, user_id, batch_result)
            
            # Memory management
            if self.metrics.completed_batches % self.config.auto_gc_frequency == 0:
                gc.collect()
            
            return batch_result
            
        except Exception as e:
            self.metrics.failed_batches += 1
            self.metrics.error_rate = self.metrics.failed_batches / self.metrics.total_batches
            
            self.logger.error(f"Error processing batch for user {user_id}: {str(e)}")
            
            # Publish error event
            self._publish_error_event(migration_id, user_id, str(e))
            
            raise
    
    def _process_single_batch_parallel(self, migration_id: str, user_id: int, 
                                      batch_data: List[Dict], configuration_id: int):
        """Process a single batch with parallel optimization"""
        # Split batch into smaller chunks for parallel processing
        chunk_size = max(100, len(batch_data) // 4)
        chunks = [batch_data[i:i + chunk_size] for i in range(0, len(batch_data), chunk_size)]
        
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(chunks))) as executor:
            futures = []
            
            for chunk in chunks:
                future = executor.submit(
                    self._process_single_batch, 
                    migration_id, user_id, chunk, configuration_id
                )
                futures.append(future)
            
            # Wait for all chunks to complete
            concurrent.futures.wait(futures)
    
    def _process_single_batch_optimized(self, migration_id: str, user_id: int, 
                                       batch_data: List[Dict], configuration_id: int):
        """Process a single batch with performance optimizations"""
        # Use optimized database operations
        start_time = time.time()
        
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Use bulk insert for better performance
                    self._bulk_insert_enhanced_calculations(cursor, batch_data, configuration_id)
                    conn.commit()
            
            # Update metrics
            self.metrics.completed_batches += 1
            self.metrics.total_activities_processed += len(batch_data)
            
            processing_time = time.time() - start_time
            self.metrics.total_processing_time += processing_time
            
            # Publish progress event
            self._publish_batch_progress_event(migration_id, user_id, 
                                             BatchResult(success=True, processed_count=len(batch_data)))
            
        except Exception as e:
            self.metrics.failed_batches += 1
            self.logger.error(f"Error in optimized batch processing: {str(e)}")
            raise
    
    def _get_user_activities_batches(self, user_id: int, configuration_id: int, 
                                    batch_size: Optional[int] = None) -> Generator[List[Dict], None, None]:
        """Get user activities in batches"""
        batch_size = batch_size or self.config.batch_size
        
        try:
            with db_utils.get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    # Get total count
                    cursor.execute("""
                        SELECT COUNT(*) as count
                        FROM activities 
                        WHERE user_id = %s
                    """, (user_id,))
                    total_count = cursor.fetchone()['count']
                    
                    # Process in batches
                    offset = 0
                    while offset < total_count:
                        cursor.execute("""
                            SELECT * FROM activities 
                            WHERE user_id = %s
                            ORDER BY activity_id
                            LIMIT %s OFFSET %s
                        """, (user_id, batch_size, offset))
                        
                        batch = cursor.fetchall()
                        if not batch:
                            break
                        
                        yield [dict(record) for record in batch]
                        offset += batch_size
                        
        except Exception as e:
            self.logger.error(f"Error getting user activities batches: {str(e)}")
            raise
    
    def _bulk_insert_enhanced_calculations(self, cursor, batch_data: List[Dict], configuration_id: int):
        """Bulk insert enhanced calculations for better performance"""
        try:
            # Prepare data for bulk insert
            insert_data = []
            for activity in batch_data:
                # Calculate ACWR (simplified - in practice, use the full calculation service)
                acwr_ratio = 1.0  # Placeholder
                acute_load = 100.0  # Placeholder
                chronic_load = 80.0  # Placeholder
                
                insert_data.append((
                    activity['activity_id'],
                    activity['user_id'],
                    configuration_id,
                    acwr_ratio,
                    acute_load,
                    chronic_load,
                    datetime.now(),
                    'enhanced'
                ))
            
            # Bulk insert
            execute_batch(cursor, """
                INSERT INTO acwr_enhanced_calculations 
                (activity_id, user_id, configuration_id, acwr_ratio, acute_load, chronic_load, 
                 calculation_date, calculation_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, insert_data)
            
        except Exception as e:
            self.logger.error(f"Error in bulk insert: {str(e)}")
            raise
    
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on current system resources"""
        try:
            # Get current memory usage
            memory_percent = psutil.virtual_memory().percent / 100.0
            
            # Adjust batch size based on memory usage
            if memory_percent < 0.5:
                return min(2000, self.config.batch_size * 2)
            elif memory_percent < 0.7:
                return self.config.batch_size
            elif memory_percent < 0.85:
                return max(500, self.config.batch_size // 2)
            else:
                return max(250, self.config.batch_size // 4)
                
        except Exception as e:
            self.logger.warning(f"Error calculating optimal batch size: {str(e)}")
            return self.config.batch_size
    
    def _should_use_parallel_processing(self) -> bool:
        """Determine if parallel processing should be used based on system resources"""
        try:
            memory_percent = psutil.virtual_memory().percent / 100.0
            cpu_percent = psutil.cpu_percent()
            
            # Use parallel processing if resources are available
            return (memory_percent < self.config.memory_threshold and 
                   cpu_percent < 80.0 and 
                   self.metrics.completed_batches > 10)  # Allow some warm-up
            
        except Exception as e:
            self.logger.warning(f"Error checking parallel processing conditions: {str(e)}")
            return False
    
    def _should_limit_concurrent_batches(self) -> bool:
        """Check if concurrent batches should be limited due to resource constraints"""
        try:
            memory_percent = psutil.virtual_memory().percent / 100.0
            return memory_percent > self.config.memory_threshold
            
        except Exception as e:
            self.logger.warning(f"Error checking concurrent batch limits: {str(e)}")
            return True
    
    def _is_memory_pressure_high(self) -> bool:
        """Check if memory pressure is high"""
        try:
            memory_percent = psutil.virtual_memory().percent / 100.0
            return memory_percent > 0.85
            
        except Exception as e:
            self.logger.warning(f"Error checking memory pressure: {str(e)}")
            return False
    
    def _adaptive_memory_management(self):
        """Perform adaptive memory management based on current usage"""
        try:
            memory_percent = psutil.virtual_memory().percent / 100.0
            
            if memory_percent > 0.8:
                # Aggressive cleanup
                self._aggressive_memory_cleanup()
            elif memory_percent > 0.6:
                # Moderate cleanup
                gc.collect()
                
        except Exception as e:
            self.logger.warning(f"Error in adaptive memory management: {str(e)}")
    
    def _aggressive_memory_cleanup(self):
        """Perform aggressive memory cleanup"""
        try:
            # Clear caches
            with self.cache_lock:
                self.batch_cache.clear()
            
            # Force garbage collection
            gc.collect()
            
            # Clear any temporary data
            self._clear_temporary_data()
            
        except Exception as e:
            self.logger.warning(f"Error in aggressive memory cleanup: {str(e)}")
    
    def _preload_user_data(self, user_ids: List[int], configuration_id: int):
        """Pre-load user data for better caching"""
        try:
            with self.cache_lock:
                for user_id in user_ids:
                    # Pre-load user activities
                    activities = list(self._get_user_activities_batches(user_id, configuration_id, 10000))
                    self.batch_cache[f"user_{user_id}"] = activities
                    
        except Exception as e:
            self.logger.warning(f"Error preloading user data: {str(e)}")
    
    def _clear_preloaded_data(self):
        """Clear preloaded data"""
        try:
            with self.cache_lock:
                self.batch_cache.clear()
                
        except Exception as e:
            self.logger.warning(f"Error clearing preloaded data: {str(e)}")
    
    def _clear_temporary_data(self):
        """Clear temporary data structures"""
        try:
            # Clear any temporary variables or data structures
            pass
            
        except Exception as e:
            self.logger.warning(f"Error clearing temporary data: {str(e)}")
    
    def _start_resource_monitoring(self):
        """Start resource monitoring thread"""
        try:
            self.stop_monitoring.clear()
            self.monitoring_thread = threading.Thread(target=self._monitor_resources)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            
        except Exception as e:
            self.logger.error(f"Error starting resource monitoring: {str(e)}")
    
    def _stop_resource_monitoring(self):
        """Stop resource monitoring thread"""
        try:
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.stop_monitoring.set()
                self.monitoring_thread.join(timeout=5)
                
        except Exception as e:
            self.logger.error(f"Error stopping resource monitoring: {str(e)}")
    
    def _monitor_resources(self):
        """Monitor system resources"""
        try:
            while not self.stop_monitoring.is_set():
                try:
                    # Get system metrics
                    cpu_percent = psutil.cpu_percent()
                    memory = psutil.virtual_memory()
                    disk_io = psutil.disk_io_counters()
                    
                    metrics = SystemResourceMetrics(
                        cpu_percent=cpu_percent,
                        memory_percent=memory.percent,
                        memory_available_gb=memory.available / (1024**3),
                        memory_used_gb=memory.used / (1024**3),
                        disk_io_percent=0.0,  # Simplified
                        timestamp=datetime.now()
                    )
                    
                    # Store metrics
                    self.resource_metrics.append(metrics)
                    
                    # Keep only recent metrics (last 1000)
                    if len(self.resource_metrics) > 1000:
                        self.resource_metrics = self.resource_metrics[-1000:]
                    
                    # Update peak usage
                    self.metrics.memory_peak_usage = max(self.metrics.memory_peak_usage, memory.percent)
                    self.metrics.cpu_peak_usage = max(self.metrics.cpu_peak_usage, cpu_percent)
                    
                    # Sleep for monitoring interval
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.warning(f"Error in resource monitoring: {str(e)}")
                    time.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Error in resource monitoring thread: {str(e)}")
    
    def _initialize_metrics(self):
        """Initialize processing metrics"""
        self.metrics = BatchProcessingMetrics(
            total_batches=0,
            completed_batches=0,
            failed_batches=0,
            total_activities_processed=0,
            total_processing_time=0.0,
            average_batch_time=0.0,
            memory_peak_usage=0.0,
            memory_average_usage=0.0,
            cpu_peak_usage=0.0,
            cpu_average_usage=0.0,
            throughput_activities_per_second=0.0,
            error_rate=0.0
        )
        self.resource_metrics.clear()
    
    def _finalize_metrics(self):
        """Finalize processing metrics"""
        try:
            # Calculate average resource usage
            if self.resource_metrics:
                memory_values = [m.memory_percent for m in self.resource_metrics]
                cpu_values = [m.cpu_percent for m in self.resource_metrics]
                
                self.metrics.memory_average_usage = np.mean(memory_values)
                self.metrics.cpu_average_usage = np.mean(cpu_values)
            
            # Calculate final error rate
            if self.metrics.total_batches > 0:
                self.metrics.error_rate = self.metrics.failed_batches / self.metrics.total_batches
            
            # Calculate final throughput
            if self.metrics.total_processing_time > 0:
                self.metrics.throughput_activities_per_second = (
                    self.metrics.total_activities_processed / self.metrics.total_processing_time
                )
            
        except Exception as e:
            self.logger.warning(f"Error finalizing metrics: {str(e)}")
    
    def _publish_batch_progress_event(self, migration_id: str, user_id: int, batch_result: BatchResult):
        """Publish batch progress event"""
        try:
            event = ProgressEvent(
                event_type=ProgressEventType.BATCH_COMPLETED,
                migration_id=migration_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data={
                    'batch_result': asdict(batch_result),
                    'metrics': asdict(self.metrics)
                }
            )
            self.progress_tracker.publish_event(event)
            
        except Exception as e:
            self.logger.warning(f"Error publishing batch progress event: {str(e)}")
    
    def _publish_error_event(self, migration_id: str, user_id: int, error_message: str):
        """Publish error event"""
        try:
            event = ProgressEvent(
                event_type=ProgressEventType.MIGRATION_FAILED,
                migration_id=migration_id,
                user_id=user_id,
                timestamp=datetime.now(),
                data={
                    'error_message': error_message,
                    'metrics': asdict(self.metrics)
                }
            )
            self.progress_tracker.publish_event(event)
            
        except Exception as e:
            self.logger.warning(f"Error publishing error event: {str(e)}")
    
    def get_processing_metrics(self) -> BatchProcessingMetrics:
        """Get current processing metrics"""
        return self.metrics
    
    def get_resource_metrics(self) -> List[SystemResourceMetrics]:
        """Get resource monitoring metrics"""
        return self.resource_metrics.copy()
    
    def stop_processing(self):
        """Stop current processing"""
        self.is_processing = False
        self.logger.info("Batch processing stop requested")
    
    def is_processing_active(self) -> bool:
        """Check if processing is currently active"""
        return self.is_processing

