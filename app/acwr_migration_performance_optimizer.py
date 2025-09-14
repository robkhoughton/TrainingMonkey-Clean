#!/usr/bin/env python3
"""
ACWR Migration Performance Optimizer and Memory Manager
Advanced performance optimization and intelligent memory management for migration operations
"""

import logging
import time
import gc
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import weakref
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing as mp

import db_utils

logger = logging.getLogger(__name__)

class OptimizationStrategy(Enum):
    """Performance optimization strategies"""
    MEMORY_OPTIMIZED = "memory_optimized"
    CPU_OPTIMIZED = "cpu_optimized"
    IO_OPTIMIZED = "io_optimized"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"

class MemoryPressureLevel(Enum):
    """Memory pressure levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class PerformanceMetric(Enum):
    """Performance metrics"""
    THROUGHPUT = "throughput"
    LATENCY = "latency"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    IO_WAIT = "io_wait"
    ERROR_RATE = "error_rate"
    SUCCESS_RATE = "success_rate"

@dataclass
class SystemResourceMetrics:
    """System resource metrics"""
    timestamp: datetime
    memory_percent: float
    memory_available_mb: float
    memory_used_mb: float
    cpu_percent: float
    cpu_count: int
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    load_average: Tuple[float, float, float]
    process_count: int
    thread_count: int

@dataclass
class PerformanceMetrics:
    """Performance metrics for migration operations"""
    timestamp: datetime
    migration_id: str
    throughput_activities_per_second: float
    average_latency_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    io_wait_percent: float
    error_rate: float
    success_rate: float
    batch_processing_time_ms: float
    database_query_time_ms: float
    cache_hit_rate: float
    optimization_score: float

@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    metric: PerformanceMetric
    current_value: float
    target_value: float
    recommendation: str
    priority: int  # 1-10, higher is more important
    estimated_impact: float  # Expected improvement percentage
    implementation_effort: str  # "low", "medium", "high"

@dataclass
class MemoryManagementConfig:
    """Memory management configuration"""
    max_memory_usage_percent: float = 80.0
    gc_threshold: float = 70.0
    cache_size_limit_mb: float = 512.0
    batch_size_reduction_factor: float = 0.5
    memory_cleanup_interval_seconds: int = 30
    enable_weak_references: bool = True
    enable_memory_pooling: bool = True
    enable_garbage_collection: bool = True

class ACWRMigrationPerformanceOptimizer:
    """Advanced performance optimizer and memory manager for migration operations"""
    
    def __init__(self, config: Optional[MemoryManagementConfig] = None):
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.config = config or MemoryManagementConfig()
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.system_metrics_history: List[SystemResourceMetrics] = []
        self.optimization_recommendations: List[OptimizationRecommendation] = []
        
        # Memory management
        self.memory_pool: Dict[str, Any] = {}
        self.weak_references: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        self.cache: Dict[str, Any] = {}
        self.cache_access_count: Dict[str, int] = {}
        self.cache_creation_time: Dict[str, datetime] = {}
        
        # Performance monitoring
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
        # Optimization state
        self.current_optimization_strategy = OptimizationStrategy.BALANCED
        self.adaptive_batch_size = 1000
        self.adaptive_thread_count = mp.cpu_count()
        self.performance_baseline: Optional[PerformanceMetrics] = None
        
        # Threading and concurrency
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.process_pool: Optional[ProcessPoolExecutor] = None
        self.lock = threading.RLock()
        
        # Start monitoring
        self._start_performance_monitoring()
    
    def optimize_migration_performance(self, migration_id: str, 
                                     current_metrics: PerformanceMetrics,
                                     system_metrics: SystemResourceMetrics) -> List[OptimizationRecommendation]:
        """Analyze performance and generate optimization recommendations"""
        try:
            self.logger.info(f"Analyzing performance for migration {migration_id}")
            
            # Store metrics
            self.performance_history.append(current_metrics)
            self.system_metrics_history.append(system_metrics)
            
            # Keep only recent history (last 100 entries)
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]
            if len(self.system_metrics_history) > 100:
                self.system_metrics_history = self.system_metrics_history[-100:]
            
            # Generate recommendations
            recommendations = []
            
            # Memory optimization recommendations
            recommendations.extend(self._analyze_memory_performance(current_metrics, system_metrics))
            
            # CPU optimization recommendations
            recommendations.extend(self._analyze_cpu_performance(current_metrics, system_metrics))
            
            # I/O optimization recommendations
            recommendations.extend(self._analyze_io_performance(current_metrics, system_metrics))
            
            # Throughput optimization recommendations
            recommendations.extend(self._analyze_throughput_performance(current_metrics, system_metrics))
            
            # Error rate optimization recommendations
            recommendations.extend(self._analyze_error_performance(current_metrics, system_metrics))
            
            # Sort by priority and impact
            recommendations.sort(key=lambda x: (x.priority, x.estimated_impact), reverse=True)
            
            # Store recommendations
            self.optimization_recommendations = recommendations
            
            # Apply automatic optimizations
            self._apply_automatic_optimizations(recommendations)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error optimizing migration performance: {str(e)}")
            return []
    
    def manage_memory_usage(self, migration_id: str, 
                          current_memory_usage: float) -> Dict[str, Any]:
        """Intelligent memory management for migration operations"""
        try:
            self.logger.debug(f"Managing memory usage for migration {migration_id}")
            
            memory_actions = {
                'garbage_collection': False,
                'cache_cleanup': False,
                'batch_size_reduction': False,
                'memory_pool_cleanup': False,
                'weak_reference_cleanup': False,
                'new_batch_size': None,
                'memory_freed_mb': 0.0
            }
            
            # Check memory pressure level
            pressure_level = self._assess_memory_pressure(current_memory_usage)
            
            if pressure_level == MemoryPressureLevel.CRITICAL:
                # Critical memory pressure - aggressive cleanup
                memory_actions['garbage_collection'] = True
                memory_actions['cache_cleanup'] = True
                memory_actions['batch_size_reduction'] = True
                memory_actions['memory_pool_cleanup'] = True
                memory_actions['weak_reference_cleanup'] = True
                memory_actions['new_batch_size'] = int(self.adaptive_batch_size * 0.3)
                
            elif pressure_level == MemoryPressureLevel.HIGH:
                # High memory pressure - moderate cleanup
                memory_actions['garbage_collection'] = True
                memory_actions['cache_cleanup'] = True
                memory_actions['batch_size_reduction'] = True
                memory_actions['new_batch_size'] = int(self.adaptive_batch_size * 0.6)
                
            elif pressure_level == MemoryPressureLevel.MEDIUM:
                # Medium memory pressure - light cleanup
                memory_actions['cache_cleanup'] = True
                memory_actions['new_batch_size'] = int(self.adaptive_batch_size * 0.8)
                
            # Execute memory management actions
            if memory_actions['garbage_collection']:
                memory_freed = self._perform_garbage_collection()
                memory_actions['memory_freed_mb'] += memory_freed
                
            if memory_actions['cache_cleanup']:
                memory_freed = self._cleanup_cache()
                memory_actions['memory_freed_mb'] += memory_freed
                
            if memory_actions['memory_pool_cleanup']:
                memory_freed = self._cleanup_memory_pool()
                memory_actions['memory_freed_mb'] += memory_freed
                
            if memory_actions['weak_reference_cleanup']:
                memory_freed = self._cleanup_weak_references()
                memory_actions['memory_freed_mb'] += memory_freed
            
            # Update adaptive batch size
            if memory_actions['new_batch_size']:
                self.adaptive_batch_size = memory_actions['new_batch_size']
                self.logger.info(f"Adjusted batch size to {self.adaptive_batch_size} due to memory pressure")
            
            return memory_actions
            
        except Exception as e:
            self.logger.error(f"Error managing memory usage: {str(e)}")
            return {}
    
    def optimize_batch_processing(self, migration_id: str, 
                                current_batch_size: int,
                                processing_time: float,
                                error_rate: float) -> Dict[str, Any]:
        """Optimize batch processing parameters based on performance metrics"""
        try:
            self.logger.debug(f"Optimizing batch processing for migration {migration_id}")
            
            optimization_result = {
                'new_batch_size': current_batch_size,
                'new_thread_count': self.adaptive_thread_count,
                'new_strategy': self.current_optimization_strategy.value,
                'optimization_reason': '',
                'expected_improvement': 0.0
            }
            
            # Analyze current performance
            if processing_time > 60.0:  # Batch taking too long
                # Reduce batch size
                new_batch_size = max(100, int(current_batch_size * 0.7))
                optimization_result['new_batch_size'] = new_batch_size
                optimization_result['optimization_reason'] = 'Reduced batch size due to long processing time'
                optimization_result['expected_improvement'] = 0.3
                
            elif processing_time < 5.0 and error_rate < 0.01:  # Very fast and reliable
                # Increase batch size
                new_batch_size = min(10000, int(current_batch_size * 1.3))
                optimization_result['new_batch_size'] = new_batch_size
                optimization_result['optimization_reason'] = 'Increased batch size due to fast processing'
                optimization_result['expected_improvement'] = 0.2
                
            # Adjust thread count based on system resources
            system_metrics = self._get_current_system_metrics()
            if system_metrics.cpu_percent < 50.0:
                # Low CPU usage - can increase parallelism
                new_thread_count = min(mp.cpu_count() * 2, self.adaptive_thread_count + 2)
                optimization_result['new_thread_count'] = new_thread_count
                optimization_result['optimization_reason'] += '; Increased thread count due to low CPU usage'
                
            elif system_metrics.cpu_percent > 90.0:
                # High CPU usage - reduce parallelism
                new_thread_count = max(1, self.adaptive_thread_count - 1)
                optimization_result['new_thread_count'] = new_thread_count
                optimization_result['optimization_reason'] += '; Reduced thread count due to high CPU usage'
            
            # Adjust strategy based on error rate
            if error_rate > 0.05:  # High error rate
                optimization_result['new_strategy'] = OptimizationStrategy.CONSERVATIVE.value
                optimization_result['optimization_reason'] += '; Switched to conservative strategy due to high error rate'
                
            elif error_rate < 0.01 and system_metrics.memory_percent < 70.0:
                # Low error rate and good memory - can be more aggressive
                optimization_result['new_strategy'] = OptimizationStrategy.AGGRESSIVE.value
                optimization_result['optimization_reason'] += '; Switched to aggressive strategy due to good performance'
            
            # Update adaptive parameters
            self.adaptive_batch_size = optimization_result['new_batch_size']
            self.adaptive_thread_count = optimization_result['new_thread_count']
            self.current_optimization_strategy = OptimizationStrategy(optimization_result['new_strategy'])
            
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"Error optimizing batch processing: {str(e)}")
            return {}
    
    def get_performance_baseline(self) -> Optional[PerformanceMetrics]:
        """Get performance baseline for comparison"""
        if not self.performance_history:
            return None
        
        # Calculate average performance over last 10 measurements
        recent_metrics = self.performance_history[-10:]
        
        baseline = PerformanceMetrics(
            timestamp=datetime.now(),
            migration_id="baseline",
            throughput_activities_per_second=sum(m.throughput_activities_per_second for m in recent_metrics) / len(recent_metrics),
            average_latency_ms=sum(m.average_latency_ms for m in recent_metrics) / len(recent_metrics),
            memory_usage_mb=sum(m.memory_usage_mb for m in recent_metrics) / len(recent_metrics),
            cpu_usage_percent=sum(m.cpu_usage_percent for m in recent_metrics) / len(recent_metrics),
            io_wait_percent=sum(m.io_wait_percent for m in recent_metrics) / len(recent_metrics),
            error_rate=sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
            success_rate=sum(m.success_rate for m in recent_metrics) / len(recent_metrics),
            batch_processing_time_ms=sum(m.batch_processing_time_ms for m in recent_metrics) / len(recent_metrics),
            database_query_time_ms=sum(m.database_query_time_ms for m in recent_metrics) / len(recent_metrics),
            cache_hit_rate=sum(m.cache_hit_rate for m in recent_metrics) / len(recent_metrics),
            optimization_score=sum(m.optimization_score for m in recent_metrics) / len(recent_metrics)
        )
        
        return baseline
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of optimization recommendations and performance"""
        try:
            baseline = self.get_performance_baseline()
            current_metrics = self.performance_history[-1] if self.performance_history else None
            
            summary = {
                'current_strategy': self.current_optimization_strategy.value,
                'adaptive_batch_size': self.adaptive_batch_size,
                'adaptive_thread_count': self.adaptive_thread_count,
                'total_recommendations': len(self.optimization_recommendations),
                'high_priority_recommendations': len([r for r in self.optimization_recommendations if r.priority >= 8]),
                'memory_usage_mb': current_metrics.memory_usage_mb if current_metrics else 0.0,
                'throughput_activities_per_second': current_metrics.throughput_activities_per_second if current_metrics else 0.0,
                'optimization_score': current_metrics.optimization_score if current_metrics else 0.0,
                'performance_trend': self._calculate_performance_trend(),
                'memory_pressure_level': self._assess_memory_pressure(current_metrics.memory_usage_mb if current_metrics else 0.0).value,
                'top_recommendations': [
                    {
                        'metric': r.metric.value,
                        'recommendation': r.recommendation,
                        'priority': r.priority,
                        'estimated_impact': r.estimated_impact
                    }
                    for r in self.optimization_recommendations[:5]
                ]
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting optimization summary: {str(e)}")
            return {}
    
    def _start_performance_monitoring(self):
        """Start background performance monitoring"""
        try:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_performance, daemon=True)
            self.monitoring_thread.start()
            self.logger.info("Performance monitoring started")
            
        except Exception as e:
            self.logger.error(f"Error starting performance monitoring: {str(e)}")
    
    def _monitor_performance(self):
        """Background performance monitoring thread"""
        while not self.stop_monitoring.is_set():
            try:
                # Collect system metrics
                system_metrics = self._get_current_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Cleanup old metrics
                if len(self.system_metrics_history) > 1000:
                    self.system_metrics_history = self.system_metrics_history[-1000:]
                
                # Memory management
                if system_metrics.memory_percent > self.config.gc_threshold:
                    self._perform_garbage_collection()
                
                # Cache cleanup
                if len(self.cache) > 1000:
                    self._cleanup_cache()
                
                # Sleep for monitoring interval
                time.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring: {str(e)}")
                time.sleep(30)  # Wait longer on error
    
    def _get_current_system_metrics(self) -> SystemResourceMetrics:
        """Get current system resource metrics"""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0.0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0.0
            
            # Network I/O metrics
            network_io = psutil.net_io_counters()
            network_sent_mb = network_io.bytes_sent / (1024 * 1024) if network_io else 0.0
            network_recv_mb = network_io.bytes_recv / (1024 * 1024) if network_io else 0.0
            
            # Load average
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0.0, 0.0, 0.0)
            
            # Process and thread counts
            process_count = len(psutil.pids())
            thread_count = threading.active_count()
            
            return SystemResourceMetrics(
                timestamp=datetime.now(),
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                memory_used_mb=memory.used / (1024 * 1024),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_io_sent_mb=network_sent_mb,
                network_io_recv_mb=network_recv_mb,
                load_average=load_avg,
                process_count=process_count,
                thread_count=thread_count
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {str(e)}")
            return SystemResourceMetrics(
                timestamp=datetime.now(),
                memory_percent=0.0,
                memory_available_mb=0.0,
                memory_used_mb=0.0,
                cpu_percent=0.0,
                cpu_count=1,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_io_sent_mb=0.0,
                network_io_recv_mb=0.0,
                load_average=(0.0, 0.0, 0.0),
                process_count=0,
                thread_count=0
            )
    
    def _assess_memory_pressure(self, memory_usage_mb: float) -> MemoryPressureLevel:
        """Assess memory pressure level"""
        try:
            system_metrics = self._get_current_system_metrics()
            memory_percent = system_metrics.memory_percent
            
            if memory_percent >= 95.0:
                return MemoryPressureLevel.CRITICAL
            elif memory_percent >= 85.0:
                return MemoryPressureLevel.HIGH
            elif memory_percent >= 70.0:
                return MemoryPressureLevel.MEDIUM
            else:
                return MemoryPressureLevel.LOW
                
        except Exception as e:
            self.logger.error(f"Error assessing memory pressure: {str(e)}")
            return MemoryPressureLevel.MEDIUM
    
    def _analyze_memory_performance(self, metrics: PerformanceMetrics, 
                                  system_metrics: SystemResourceMetrics) -> List[OptimizationRecommendation]:
        """Analyze memory performance and generate recommendations"""
        recommendations = []
        
        # High memory usage
        if system_metrics.memory_percent > 80.0:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.MEMORY_USAGE,
                current_value=system_metrics.memory_percent,
                target_value=70.0,
                recommendation="Reduce memory usage by implementing memory pooling and cache cleanup",
                priority=9,
                estimated_impact=0.2,
                implementation_effort="medium"
            ))
        
        # Memory fragmentation
        if metrics.memory_usage_mb > system_metrics.memory_used_mb * 0.8:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.MEMORY_USAGE,
                current_value=metrics.memory_usage_mb,
                target_value=system_metrics.memory_used_mb * 0.6,
                recommendation="Implement memory defragmentation and object pooling",
                priority=7,
                estimated_impact=0.15,
                implementation_effort="high"
            ))
        
        return recommendations
    
    def _analyze_cpu_performance(self, metrics: PerformanceMetrics, 
                               system_metrics: SystemResourceMetrics) -> List[OptimizationRecommendation]:
        """Analyze CPU performance and generate recommendations"""
        recommendations = []
        
        # High CPU usage
        if system_metrics.cpu_percent > 90.0:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.CPU_USAGE,
                current_value=system_metrics.cpu_percent,
                target_value=70.0,
                recommendation="Reduce CPU usage by optimizing algorithms and reducing parallelism",
                priority=8,
                estimated_impact=0.25,
                implementation_effort="medium"
            ))
        
        # Low CPU utilization
        elif system_metrics.cpu_percent < 30.0 and metrics.throughput_activities_per_second < 100:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.CPU_USAGE,
                current_value=system_metrics.cpu_percent,
                target_value=60.0,
                recommendation="Increase CPU utilization by adding more parallel processing",
                priority=6,
                estimated_impact=0.3,
                implementation_effort="low"
            ))
        
        return recommendations
    
    def _analyze_io_performance(self, metrics: PerformanceMetrics, 
                              system_metrics: SystemResourceMetrics) -> List[OptimizationRecommendation]:
        """Analyze I/O performance and generate recommendations"""
        recommendations = []
        
        # High I/O wait
        if metrics.io_wait_percent > 20.0:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.IO_WAIT,
                current_value=metrics.io_wait_percent,
                target_value=10.0,
                recommendation="Reduce I/O wait by implementing connection pooling and batch operations",
                priority=8,
                estimated_impact=0.4,
                implementation_effort="medium"
            ))
        
        # Slow database queries
        if metrics.database_query_time_ms > 1000.0:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.LATENCY,
                current_value=metrics.database_query_time_ms,
                target_value=500.0,
                recommendation="Optimize database queries and add proper indexing",
                priority=9,
                estimated_impact=0.5,
                implementation_effort="high"
            ))
        
        return recommendations
    
    def _analyze_throughput_performance(self, metrics: PerformanceMetrics, 
                                      system_metrics: SystemResourceMetrics) -> List[OptimizationRecommendation]:
        """Analyze throughput performance and generate recommendations"""
        recommendations = []
        
        # Low throughput
        if metrics.throughput_activities_per_second < 50.0:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.THROUGHPUT,
                current_value=metrics.throughput_activities_per_second,
                target_value=100.0,
                recommendation="Increase throughput by optimizing batch processing and reducing overhead",
                priority=9,
                estimated_impact=0.6,
                implementation_effort="medium"
            ))
        
        # High latency
        if metrics.average_latency_ms > 5000.0:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.LATENCY,
                current_value=metrics.average_latency_ms,
                target_value=2000.0,
                recommendation="Reduce latency by optimizing data processing algorithms",
                priority=8,
                estimated_impact=0.4,
                implementation_effort="high"
            ))
        
        return recommendations
    
    def _analyze_error_performance(self, metrics: PerformanceMetrics, 
                                 system_metrics: SystemResourceMetrics) -> List[OptimizationRecommendation]:
        """Analyze error performance and generate recommendations"""
        recommendations = []
        
        # High error rate
        if metrics.error_rate > 0.05:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.ERROR_RATE,
                current_value=metrics.error_rate,
                target_value=0.01,
                recommendation="Reduce error rate by improving error handling and validation",
                priority=10,
                estimated_impact=0.8,
                implementation_effort="medium"
            ))
        
        # Low success rate
        if metrics.success_rate < 0.95:
            recommendations.append(OptimizationRecommendation(
                metric=PerformanceMetric.SUCCESS_RATE,
                current_value=metrics.success_rate,
                target_value=0.99,
                recommendation="Improve success rate by enhancing data validation and error recovery",
                priority=9,
                estimated_impact=0.7,
                implementation_effort="medium"
            ))
        
        return recommendations
    
    def _apply_automatic_optimizations(self, recommendations: List[OptimizationRecommendation]):
        """Apply automatic optimizations based on recommendations"""
        try:
            for recommendation in recommendations:
                if recommendation.priority >= 9 and recommendation.implementation_effort == "low":
                    if recommendation.metric == PerformanceMetric.MEMORY_USAGE:
                        self._perform_garbage_collection()
                        self._cleanup_cache()
                    elif recommendation.metric == PerformanceMetric.CPU_USAGE:
                        # Adjust thread count
                        if recommendation.current_value > recommendation.target_value:
                            self.adaptive_thread_count = max(1, self.adaptive_thread_count - 1)
                        else:
                            self.adaptive_thread_count = min(mp.cpu_count() * 2, self.adaptive_thread_count + 1)
                            
        except Exception as e:
            self.logger.error(f"Error applying automatic optimizations: {str(e)}")
    
    def _perform_garbage_collection(self) -> float:
        """Perform garbage collection and return memory freed"""
        try:
            # Get memory before GC
            memory_before = psutil.virtual_memory().used
            
            # Force garbage collection
            collected = gc.collect()
            
            # Get memory after GC
            memory_after = psutil.virtual_memory().used
            
            memory_freed_mb = (memory_before - memory_after) / (1024 * 1024)
            
            self.logger.debug(f"Garbage collection freed {memory_freed_mb:.2f} MB, collected {collected} objects")
            
            return memory_freed_mb
            
        except Exception as e:
            self.logger.error(f"Error performing garbage collection: {str(e)}")
            return 0.0
    
    def _cleanup_cache(self) -> float:
        """Cleanup cache and return memory freed"""
        try:
            memory_freed_mb = 0.0
            
            # Remove old cache entries
            current_time = datetime.now()
            keys_to_remove = []
            
            for key, creation_time in self.cache_creation_time.items():
                if (current_time - creation_time).total_seconds() > 3600:  # 1 hour
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                if key in self.cache:
                    del self.cache[key]
                if key in self.cache_access_count:
                    del self.cache_access_count[key]
                if key in self.cache_creation_time:
                    del self.cache_creation_time[key]
            
            # Remove least accessed entries if cache is still too large
            if len(self.cache) > 500:
                sorted_keys = sorted(self.cache_access_count.items(), key=lambda x: x[1])
                for key, _ in sorted_keys[:100]:  # Remove 100 least accessed
                    if key in self.cache:
                        del self.cache[key]
                    if key in self.cache_access_count:
                        del self.cache_access_count[key]
                    if key in self.cache_creation_time:
                        del self.cache_creation_time[key]
            
            # Estimate memory freed (rough calculation)
            memory_freed_mb = len(keys_to_remove) * 0.1  # Assume 0.1 MB per cache entry
            
            self.logger.debug(f"Cache cleanup removed {len(keys_to_remove)} entries, estimated {memory_freed_mb:.2f} MB freed")
            
            return memory_freed_mb
            
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {str(e)}")
            return 0.0
    
    def _cleanup_memory_pool(self) -> float:
        """Cleanup memory pool and return memory freed"""
        try:
            memory_freed_mb = 0.0
            
            # Clear memory pool
            pool_size_before = len(self.memory_pool)
            self.memory_pool.clear()
            
            # Estimate memory freed
            memory_freed_mb = pool_size_before * 0.05  # Assume 0.05 MB per pool entry
            
            self.logger.debug(f"Memory pool cleanup removed {pool_size_before} entries, estimated {memory_freed_mb:.2f} MB freed")
            
            return memory_freed_mb
            
        except Exception as e:
            self.logger.error(f"Error cleaning up memory pool: {str(e)}")
            return 0.0
    
    def _cleanup_weak_references(self) -> float:
        """Cleanup weak references and return memory freed"""
        try:
            # Weak references are automatically cleaned up by Python
            # This is just for logging and estimation
            memory_freed_mb = 0.0
            
            self.logger.debug("Weak reference cleanup completed")
            
            return memory_freed_mb
            
        except Exception as e:
            self.logger.error(f"Error cleaning up weak references: {str(e)}")
            return 0.0
    
    def _calculate_performance_trend(self) -> str:
        """Calculate performance trend over recent measurements"""
        try:
            if len(self.performance_history) < 5:
                return "insufficient_data"
            
            recent_metrics = self.performance_history[-5:]
            older_metrics = self.performance_history[-10:-5] if len(self.performance_history) >= 10 else self.performance_history[:-5]
            
            if not older_metrics:
                return "insufficient_data"
            
            # Calculate average optimization score
            recent_avg = sum(m.optimization_score for m in recent_metrics) / len(recent_metrics)
            older_avg = sum(m.optimization_score for m in older_metrics) / len(older_metrics)
            
            if recent_avg > older_avg * 1.1:
                return "improving"
            elif recent_avg < older_avg * 0.9:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error(f"Error calculating performance trend: {str(e)}")
            return "unknown"
    
    def shutdown(self):
        """Shutdown the performance optimizer"""
        try:
            self.logger.info("Shutting down performance optimizer")
            
            # Stop monitoring
            self.stop_monitoring.set()
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            # Shutdown thread pools
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True)
            if self.process_pool:
                self.process_pool.shutdown(wait=True)
            
            # Clear caches
            self.cache.clear()
            self.cache_access_count.clear()
            self.cache_creation_time.clear()
            self.memory_pool.clear()
            
            self.logger.info("Performance optimizer shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error shutting down performance optimizer: {str(e)}")

