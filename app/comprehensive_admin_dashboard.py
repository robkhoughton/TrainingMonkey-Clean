#!/usr/bin/env python3
"""
Comprehensive Admin Dashboard
Single dashboard for monitoring all system components with real-time updates
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from db_utils import execute_query
from db_connection_manager import db_manager
from enhanced_trimp_metrics import get_enhanced_trimp_metrics

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class SystemComponent(Enum):
    """System components being monitored"""
    TRIMP_CALCULATIONS = "trimp_calculations"
    ACWR_CALCULATIONS = "acwr_calculations"
    DATABASE = "database"
    API_ENDPOINTS = "api_endpoints"
    FEATURE_FLAGS = "feature_flags"
    MIGRATION_SYSTEM = "migration_system"
    CLOUD_RUN = "cloud_run"
    CLOUD_SQL = "cloud_sql"

@dataclass
class Alert:
    """Alert structure"""
    id: str
    component: SystemComponent
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    details: Dict[str, Any] = None

@dataclass
class ComponentStatus:
    """Component status information"""
    component: SystemComponent
    status: str  # "healthy", "warning", "critical"
    health_score: int  # 0-100
    last_updated: datetime
    metrics: Dict[str, Any]
    alerts: List[Alert]

@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    overall_health_score: int
    total_alerts: int
    critical_alerts: int
    components: List[ComponentStatus]
    recent_errors: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    last_updated: datetime

class ComprehensiveAdminDashboard:
    """Comprehensive admin dashboard with real-time monitoring"""
    
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        self.cache_duration = 30  # seconds
        self.alerts: List[Alert] = []
        self.monitoring_active = False
        
        # Performance thresholds
        self.thresholds = {
            'trimp_calculation_time': 5.0,  # seconds
            'acwr_calculation_time': 3.0,   # seconds
            'api_response_time': 2.0,       # seconds
            'error_rate': 0.05,             # 5%
            'database_utilization': 0.80,   # 80%
            'memory_usage': 0.85,           # 85%
            'cpu_usage': 0.90               # 90%
        }
    
    def get_dashboard_data(self, force_refresh: bool = False) -> DashboardData:
        """Get complete dashboard data with caching"""
        cache_key = "dashboard_data"
        
        # Check cache
        if not force_refresh and self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        # Collect data from all monitoring sources
        components = self._collect_component_status()
        recent_errors = self._collect_recent_errors()
        performance_trends = self._collect_performance_trends()
        
        # Calculate overall health score
        overall_health = self._calculate_overall_health(components)
        
        # Count alerts
        total_alerts = len(self.alerts)
        critical_alerts = len([a for a in self.alerts if a.severity == AlertSeverity.CRITICAL])
        
        # Create dashboard data
        dashboard_data = DashboardData(
            overall_health_score=overall_health,
            total_alerts=total_alerts,
            critical_alerts=critical_alerts,
            components=components,
            recent_errors=recent_errors,
            performance_trends=performance_trends,
            last_updated=datetime.now()
        )
        
        # Cache the result
        self.cache[cache_key] = dashboard_data
        self.cache_timestamps[cache_key] = datetime.now()
        
        return dashboard_data
    
    def _collect_component_status(self) -> List[ComponentStatus]:
        """Collect status for all system components"""
        components = []
        
        # TRIMP Calculations
        components.append(self._get_trimp_status())
        
        # ACWR Calculations
        components.append(self._get_acwr_status())
        
        # Database
        components.append(self._get_database_status())
        
        # API Endpoints
        components.append(self._get_api_status())
        
        # Feature Flags
        components.append(self._get_feature_flags_status())
        
        # Migration System
        components.append(self._get_migration_status())
        
        # Cloud Run
        components.append(self._get_cloud_run_status())
        
        # Cloud SQL
        components.append(self._get_cloud_sql_status())
        
        return components
    
    def _get_trimp_status(self) -> ComponentStatus:
        """Get TRIMP calculation component status"""
        try:
            # Get TRIMP metrics for last hour
            trimp_metrics = get_enhanced_trimp_metrics(1)
            
            if not trimp_metrics.get('success'):
                return ComponentStatus(
                    component=SystemComponent.TRIMP_CALCULATIONS,
                    status="critical",
                    health_score=0,
                    last_updated=datetime.now(),
                    metrics={'error': trimp_metrics.get('error', 'Unknown error')},
                    alerts=[Alert(
                        id=f"trimp_error_{int(time.time())}",
                        component=SystemComponent.TRIMP_CALCULATIONS,
                        severity=AlertSeverity.CRITICAL,
                        title="TRIMP Metrics Unavailable",
                        message=trimp_metrics.get('error', 'Unknown error'),
                        timestamp=datetime.now()
                    )]
                )
            
            # Analyze metrics
            detailed_metrics = trimp_metrics.get('detailed_metrics', {})
            error_analysis = trimp_metrics.get('error_analysis', {})
            
            success_rate = detailed_metrics.get('overall_success_rate', 0)
            error_rate = error_analysis.get('overall_error_rate', 0)
            total_activities = detailed_metrics.get('total_activities_processed', 0)
            
            # Calculate health score
            health_score = self._calculate_component_health_score(
                success_rate, error_rate, total_activities
            )
            
            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "warning"
            else:
                status = "critical"
            
            # Check for alerts
            alerts = []
            if error_rate > self.thresholds['error_rate']:
                alerts.append(Alert(
                    id=f"trimp_error_rate_{int(time.time())}",
                    component=SystemComponent.TRIMP_CALCULATIONS,
                    severity=AlertSeverity.HIGH if error_rate > 0.10 else AlertSeverity.MEDIUM,
                    title="High TRIMP Error Rate",
                    message=f"TRIMP error rate is {error_rate:.1%}, exceeding threshold of {self.thresholds['error_rate']:.1%}",
                    timestamp=datetime.now(),
                    details={'error_rate': error_rate, 'threshold': self.thresholds['error_rate']}
                ))
            
            if success_rate < 95:
                alerts.append(Alert(
                    id=f"trimp_success_rate_{int(time.time())}",
                    component=SystemComponent.TRIMP_CALCULATIONS,
                    severity=AlertSeverity.MEDIUM,
                    title="Low TRIMP Success Rate",
                    message=f"TRIMP success rate is {success_rate:.1%}%",
                    timestamp=datetime.now(),
                    details={'success_rate': success_rate}
                ))
            
            return ComponentStatus(
                component=SystemComponent.TRIMP_CALCULATIONS,
                status=status,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics={
                    'success_rate': success_rate,
                    'error_rate': error_rate,
                    'total_activities': total_activities,
                    'calculation_methods': detailed_metrics.get('calculation_methods', {}),
                    'performance_score': detailed_metrics.get('performance_score', 'Unknown')
                },
                alerts=alerts
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.TRIMP_CALCULATIONS,
                status="critical",
                health_score=0,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"trimp_exception_{int(time.time())}",
                    component=SystemComponent.TRIMP_CALCULATIONS,
                    severity=AlertSeverity.CRITICAL,
                    title="TRIMP Status Check Failed",
                    message=f"Exception during TRIMP status check: {str(e)}",
                    timestamp=datetime.now()
                )]
            )
    
    def _get_acwr_status(self) -> ComponentStatus:
        """Get ACWR calculation component status"""
        try:
            # Check ACWR-related tables and recent activity
            acwr_metrics = execute_query("""
                SELECT 
                    COUNT(*) as total_calculations,
                    COUNT(CASE WHEN calculation_timestamp >= NOW() - INTERVAL '1 hour' THEN 1 END) as recent_calculations,
                    AVG(CASE WHEN calculation_timestamp >= NOW() - INTERVAL '1 hour' THEN 1 END) as avg_calculation_time
                FROM acwr_enhanced_calculations 
                WHERE calculation_timestamp >= NOW() - INTERVAL '7 days'
            """, fetch=True)
            
            if not acwr_metrics:
                return ComponentStatus(
                    component=SystemComponent.ACWR_CALCULATIONS,
                    status="warning",
                    health_score=50,
                    last_updated=datetime.now(),
                    metrics={'message': 'No ACWR data available'},
                    alerts=[]
                )
            
            metrics_data = acwr_metrics[0]
            total_calculations = metrics_data.get('total_calculations', 0)
            recent_calculations = metrics_data.get('recent_calculations', 0)
            avg_calculation_time = metrics_data.get('avg_calculation_time', 0) or 0
            
            # Calculate health score based on activity and performance
            health_score = 100
            alerts = []
            
            # Check calculation time
            if avg_calculation_time > self.thresholds['acwr_calculation_time'] * 1000:  # Convert to ms
                health_score -= 30
                alerts.append(Alert(
                    id=f"acwr_slow_calculation_{int(time.time())}",
                    component=SystemComponent.ACWR_CALCULATIONS,
                    severity=AlertSeverity.MEDIUM,
                    title="Slow ACWR Calculations",
                    message=f"Average ACWR calculation time is {avg_calculation_time:.0f}ms, exceeding threshold of {self.thresholds['acwr_calculation_time'] * 1000:.0f}ms",
                    timestamp=datetime.now(),
                    details={'avg_time': avg_calculation_time, 'threshold': self.thresholds['acwr_calculation_time'] * 1000}
                ))
            
            # Check recent activity
            if recent_calculations == 0 and total_calculations > 0:
                health_score -= 20
                alerts.append(Alert(
                    id=f"acwr_no_recent_activity_{int(time.time())}",
                    component=SystemComponent.ACWR_CALCULATIONS,
                    severity=AlertSeverity.MEDIUM,
                    title="No Recent ACWR Activity",
                    message="No ACWR calculations in the last hour",
                    timestamp=datetime.now()
                ))
            
            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "warning"
            else:
                status = "critical"
            
            return ComponentStatus(
                component=SystemComponent.ACWR_CALCULATIONS,
                status=status,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics={
                    'total_calculations': total_calculations,
                    'recent_calculations': recent_calculations,
                    'avg_calculation_time_ms': avg_calculation_time,
                    'activity_status': 'active' if recent_calculations > 0 else 'inactive'
                },
                alerts=alerts
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.ACWR_CALCULATIONS,
                status="critical",
                health_score=0,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"acwr_exception_{int(time.time())}",
                    component=SystemComponent.ACWR_CALCULATIONS,
                    severity=AlertSeverity.CRITICAL,
                    title="ACWR Status Check Failed",
                    message=f"Exception during ACWR status check: {str(e)}",
                    timestamp=datetime.now()
                )]
            )
    
    def _get_database_status(self) -> ComponentStatus:
        """Get database component status"""
        try:
            # Get database pool status
            pool_status = db_manager.get_pool_status()
            
            # Get database performance metrics
            db_metrics = execute_query("""
                SELECT 
                    COUNT(*) as active_connections,
                    (SELECT COUNT(*) FROM activities WHERE trimp_processed_at >= NOW() - INTERVAL '1 hour') as recent_activity
            """, fetch=True)
            
            if not db_metrics:
                raise Exception("Unable to query database metrics")
            
            metrics_data = db_metrics[0]
            active_connections = metrics_data.get('active_connections', 0)
            recent_activity = metrics_data.get('recent_activity', 0)
            
            # Calculate health score
            health_score = 100
            alerts = []
            
            # Check pool utilization
            pool_utilization = pool_status.get('pool_utilization', 0)
            if pool_utilization > self.thresholds['database_utilization']:
                health_score -= 40
                alerts.append(Alert(
                    id=f"db_high_utilization_{int(time.time())}",
                    component=SystemComponent.DATABASE,
                    severity=AlertSeverity.HIGH,
                    title="High Database Pool Utilization",
                    message=f"Database pool utilization is {pool_utilization:.1%}, exceeding threshold of {self.thresholds['database_utilization']:.1%}",
                    timestamp=datetime.now(),
                    details={'utilization': pool_utilization, 'threshold': self.thresholds['database_utilization']}
                ))
            
            # Check connection errors
            connection_errors = pool_status.get('stats', {}).get('connection_errors', 0)
            if connection_errors > 0:
                health_score -= min(30, connection_errors * 10)
                alerts.append(Alert(
                    id=f"db_connection_errors_{int(time.time())}",
                    component=SystemComponent.DATABASE,
                    severity=AlertSeverity.MEDIUM,
                    title="Database Connection Errors",
                    message=f"{connection_errors} database connection errors detected",
                    timestamp=datetime.now(),
                    details={'error_count': connection_errors}
                ))
            
            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "warning"
            else:
                status = "critical"
            
            return ComponentStatus(
                component=SystemComponent.DATABASE,
                status=status,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics={
                    'pool_status': pool_status.get('status', 'unknown'),
                    'pool_utilization': pool_utilization,
                    'active_connections': active_connections,
                    'connection_errors': connection_errors,
                    'recent_activity': recent_activity
                },
                alerts=alerts
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.DATABASE,
                status="critical",
                health_score=0,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"db_exception_{int(time.time())}",
                    component=SystemComponent.DATABASE,
                    severity=AlertSeverity.CRITICAL,
                    title="Database Status Check Failed",
                    message=f"Exception during database status check: {str(e)}",
                    timestamp=datetime.now()
                )]
            )
    
    def _get_api_status(self) -> ComponentStatus:
        """Get API endpoints component status"""
        try:
            # Check if api_logs table exists
            table_check = execute_query("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'api_logs'
                ) as table_exists
            """, fetch=True)
            
            if not table_check or not table_check[0]['table_exists']:
                return ComponentStatus(
                    component=SystemComponent.API_ENDPOINTS,
                    status="warning",
                    health_score=85,
                    last_updated=datetime.now(),
                    metrics={
                        'message': 'API monitoring not available - no logs table',
                        'endpoints_monitored': 0,
                        'avg_response_time_ms': 0,
                        'error_rate': 0
                    },
                    alerts=[]
                )
            
            # Get API performance metrics from api_logs table
            api_metrics = execute_query("""
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '1 hour' THEN 1 END) as recent_requests,
                    AVG(CASE WHEN timestamp >= NOW() - INTERVAL '1 hour' THEN response_time_ms END) as avg_response_time,
                    COUNT(CASE WHEN timestamp >= NOW() - INTERVAL '1 hour' AND status_code >= 400 THEN 1 END) as error_count,
                    COUNT(DISTINCT endpoint) as unique_endpoints
                FROM api_logs 
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
            """, fetch=True)
            
            if not api_metrics:
                return ComponentStatus(
                    component=SystemComponent.API_ENDPOINTS,
                    status="warning",
                    health_score=70,
                    last_updated=datetime.now(),
                    metrics={
                        'message': 'No API requests logged in last 24 hours',
                        'endpoints_monitored': 0,
                        'avg_response_time_ms': 0,
                        'error_rate': 0
                    },
                    alerts=[]
                )
            
            metrics = api_metrics[0]
            total_requests = metrics['total_requests'] or 0
            recent_requests = metrics['recent_requests'] or 0
            avg_response_time = metrics['avg_response_time'] or 0
            error_count = metrics['error_count'] or 0
            unique_endpoints = metrics['unique_endpoints'] or 0
            
            # Calculate error rate
            error_rate = (error_count / recent_requests * 100) if recent_requests > 0 else 0
            
            # Determine status based on metrics
            if error_rate > 10:
                status = "critical"
                health_score = 30
            elif error_rate > 5 or avg_response_time > 2000:
                status = "warning"
                health_score = 60
            else:
                status = "healthy"
                health_score = 90
            
            # Generate alerts
            alerts = []
            if error_rate > 10:
                alerts.append(Alert(
                    id=f"api_high_error_rate_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    severity=AlertSeverity.CRITICAL,
                    title="High API Error Rate",
                    message=f"API error rate is {error_rate:.1f}% (threshold: 10%)",
                    timestamp=datetime.now(),
                    acknowledged=False,
                    resolved=False,
                    details={'error_rate': error_rate, 'error_count': error_count, 'total_requests': recent_requests}
                ))
            elif error_rate > 5:
                alerts.append(Alert(
                    id=f"api_elevated_error_rate_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    severity=AlertSeverity.HIGH,
                    title="Elevated API Error Rate",
                    message=f"API error rate is {error_rate:.1f}% (threshold: 5%)",
                    timestamp=datetime.now(),
                    acknowledged=False,
                    resolved=False,
                    details={'error_rate': error_rate, 'error_count': error_count, 'total_requests': recent_requests}
                ))
            
            if avg_response_time > 2000:
                alerts.append(Alert(
                    id=f"api_slow_response_{datetime.now().strftime('%Y%m%d_%H%M')}",
                    severity=AlertSeverity.MEDIUM,
                    title="Slow API Response Times",
                    message=f"Average response time is {avg_response_time:.0f}ms (threshold: 2000ms)",
                    timestamp=datetime.now(),
                    acknowledged=False,
                    resolved=False,
                    details={'avg_response_time': avg_response_time}
                ))
            
            return ComponentStatus(
                component=SystemComponent.API_ENDPOINTS,
                status=status,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics={
                    'total_requests_24h': total_requests,
                    'recent_requests_1h': recent_requests,
                    'avg_response_time_ms': round(avg_response_time, 1),
                    'error_rate_percent': round(error_rate, 1),
                    'unique_endpoints': unique_endpoints,
                    'error_count_1h': error_count
                },
                alerts=alerts
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.API_ENDPOINTS,
                status="warning",
                health_score=70,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"api_exception_{int(time.time())}",
                    component=SystemComponent.API_ENDPOINTS,
                    severity=AlertSeverity.MEDIUM,
                    title="API Status Check Failed",
                    message=f"Exception during API status check: {str(e)}",
                    timestamp=datetime.now()
                )]
            )
    
    def _get_feature_flags_status(self) -> ComponentStatus:
        """Get feature flags component status"""
        try:
            from utils.feature_flags import is_feature_enabled
            
            # Check key feature flags
            feature_flags = {
                'enhanced_trimp_calculation': {
                    'admin': is_feature_enabled('enhanced_trimp_calculation', 1),
                    'beta_2': is_feature_enabled('enhanced_trimp_calculation', 2),
                    'beta_3': is_feature_enabled('enhanced_trimp_calculation', 3),
                    'regular': is_feature_enabled('enhanced_trimp_calculation', 4)
                },
                'enhanced_acwr_calculation': {
                    'admin': is_feature_enabled('enhanced_acwr_calculation', 1),
                    'beta_2': is_feature_enabled('enhanced_acwr_calculation', 2),
                    'beta_3': is_feature_enabled('enhanced_acwr_calculation', 3),
                    'regular': is_feature_enabled('enhanced_acwr_calculation', 4)
                }
            }
            
            # Calculate health score
            health_score = 100
            alerts = []
            
            # Check TRIMP feature flag rollout
            trimp_flags = feature_flags['enhanced_trimp_calculation']
            if not trimp_flags['admin']:
                health_score -= 50
                alerts.append(Alert(
                    id=f"trimp_flag_admin_disabled_{int(time.time())}",
                    component=SystemComponent.FEATURE_FLAGS,
                    severity=AlertSeverity.CRITICAL,
                    title="TRIMP Feature Flag Disabled for Admin",
                    message="Enhanced TRIMP calculation is disabled for admin user",
                    timestamp=datetime.now()
                ))
            
            # Check ACWR feature flag rollout
            acwr_flags = feature_flags['enhanced_acwr_calculation']
            if not acwr_flags['admin']:
                health_score -= 30
                alerts.append(Alert(
                    id=f"acwr_flag_admin_disabled_{int(time.time())}",
                    component=SystemComponent.FEATURE_FLAGS,
                    severity=AlertSeverity.HIGH,
                    title="ACWR Feature Flag Disabled for Admin",
                    message="Enhanced ACWR calculation is disabled for admin user",
                    timestamp=datetime.now()
                ))
            
            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "warning"
            else:
                status = "critical"
            
            return ComponentStatus(
                component=SystemComponent.FEATURE_FLAGS,
                status=status,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics=feature_flags,
                alerts=alerts
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.FEATURE_FLAGS,
                status="critical",
                health_score=0,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"feature_flags_exception_{int(time.time())}",
                    component=SystemComponent.FEATURE_FLAGS,
                    severity=AlertSeverity.CRITICAL,
                    title="Feature Flags Status Check Failed",
                    message=f"Exception during feature flags status check: {str(e)}",
                    timestamp=datetime.now()
                )]
            )
    
    def _get_migration_status(self) -> ComponentStatus:
        """Get migration system component status"""
        try:
            # Check for active migrations
            migration_metrics = execute_query("""
                SELECT 
                    COUNT(*) as total_migrations,
                    COUNT(CASE WHEN status = 'running' THEN 1 END) as active_migrations,
                    COUNT(CASE WHEN status = 'failed' AND created_at >= NOW() - INTERVAL '24 hours' THEN 1 END) as recent_failures
                FROM acwr_migration_history 
                WHERE created_at >= NOW() - INTERVAL '7 days'
            """, fetch=True)
            
            if not migration_metrics:
                return ComponentStatus(
                    component=SystemComponent.MIGRATION_SYSTEM,
                    status="healthy",
                    health_score=90,
                    last_updated=datetime.now(),
                    metrics={'message': 'No migration data available'},
                    alerts=[]
                )
            
            metrics_data = migration_metrics[0]
            total_migrations = metrics_data.get('total_migrations', 0)
            active_migrations = metrics_data.get('active_migrations', 0)
            recent_failures = metrics_data.get('recent_failures', 0)
            
            # Calculate health score
            health_score = 100
            alerts = []
            
            # Check for recent failures
            if recent_failures > 0:
                health_score -= min(40, recent_failures * 20)
                alerts.append(Alert(
                    id=f"migration_recent_failures_{int(time.time())}",
                    component=SystemComponent.MIGRATION_SYSTEM,
                    severity=AlertSeverity.HIGH if recent_failures > 2 else AlertSeverity.MEDIUM,
                    title="Recent Migration Failures",
                    message=f"{recent_failures} migration failures in the last 24 hours",
                    timestamp=datetime.now(),
                    details={'failure_count': recent_failures}
                ))
            
            # Check for stuck migrations
            if active_migrations > 0:
                # Check if any active migrations are stuck (running for more than 1 hour)
                stuck_migrations = execute_query("""
                    SELECT COUNT(*) as stuck_count
                    FROM acwr_migration_history 
                    WHERE status = 'running' 
                    AND created_at < NOW() - INTERVAL '1 hour'
                """, fetch=True)
                
                if stuck_migrations and stuck_migrations[0].get('stuck_count', 0) > 0:
                    health_score -= 30
                    alerts.append(Alert(
                        id=f"migration_stuck_{int(time.time())}",
                        component=SystemComponent.MIGRATION_SYSTEM,
                        severity=AlertSeverity.HIGH,
                        title="Stuck Migrations Detected",
                        message=f"{stuck_migrations[0]['stuck_count']} migrations have been running for over 1 hour",
                        timestamp=datetime.now(),
                        details={'stuck_count': stuck_migrations[0]['stuck_count']}
                    ))
            
            # Determine status
            if health_score >= 90:
                status = "healthy"
            elif health_score >= 70:
                status = "warning"
            else:
                status = "critical"
            
            return ComponentStatus(
                component=SystemComponent.MIGRATION_SYSTEM,
                status=status,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics={
                    'total_migrations': total_migrations,
                    'active_migrations': active_migrations,
                    'recent_failures': recent_failures,
                    'system_status': 'active' if active_migrations > 0 else 'idle'
                },
                alerts=alerts
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.MIGRATION_SYSTEM,
                status="warning",
                health_score=70,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"migration_exception_{int(time.time())}",
                    component=SystemComponent.MIGRATION_SYSTEM,
                    severity=AlertSeverity.MEDIUM,
                    title="Migration Status Check Failed",
                    message=f"Exception during migration status check: {str(e)}",
                    timestamp=datetime.now()
                )]
            )
    
    def _collect_recent_errors(self) -> List[Dict[str, Any]]:
        """Collect recent errors from all components"""
        recent_errors = []
        
        try:
            # Get recent TRIMP calculation errors
            trimp_errors = execute_query("""
                SELECT 
                    activity_id,
                    user_id,
                    trimp_calculation_method,
                    trimp_processed_at,
                    'TRIMP Calculation Error' as error_type
                FROM activities 
                WHERE trimp_processed_at >= NOW() - INTERVAL '1 hour'
                AND (trimp IS NULL OR trimp <= 0)
                AND activity_id > 0
                ORDER BY trimp_processed_at DESC
                LIMIT 10
            """, fetch=True)
            
            for error in trimp_errors:
                recent_errors.append({
                    'timestamp': error['trimp_processed_at'],
                    'component': 'TRIMP Calculations',
                    'error_type': error['error_type'],
                    'details': f"Activity {error['activity_id']} - Method: {error['trimp_calculation_method']}",
                    'user_id': error['user_id']
                })
            
            # Get recent ACWR calculation errors
            acwr_errors = execute_query("""
                SELECT 
                    id,
                    user_id,
                    calculation_timestamp,
                    'ACWR Calculation Error' as error_type
                FROM acwr_enhanced_calculations 
                WHERE calculation_timestamp >= NOW() - INTERVAL '1 hour'
                AND (enhanced_chronic_load IS NULL OR enhanced_chronic_load <= 0)
                ORDER BY calculation_timestamp DESC
                LIMIT 10
            """, fetch=True)
            
            for error in acwr_errors:
                recent_errors.append({
                    'timestamp': error['calculation_timestamp'],
                    'component': 'ACWR Calculations',
                    'error_type': error['error_type'],
                    'details': f"Calculation {error['id']} - Invalid result detected",
                    'user_id': error['user_id']
                })
            
        except Exception as e:
            recent_errors.append({
                'timestamp': datetime.now(),
                'component': 'Dashboard',
                'error_type': 'Error Collection Failed',
                'details': f"Failed to collect recent errors: {str(e)}",
                'user_id': None
            })
        
        # Sort by timestamp and return most recent
        recent_errors.sort(key=lambda x: x['timestamp'], reverse=True)
        return recent_errors[:20]
    
    def _collect_performance_trends(self) -> Dict[str, Any]:
        """Collect performance trends over the last 7 days"""
        try:
            # Get TRIMP performance trends
            trimp_trends = execute_query("""
                SELECT 
                    DATE(trimp_processed_at) as date,
                    COUNT(*) as total_calculations,
                    AVG(CASE WHEN trimp IS NOT NULL AND trimp > 0 THEN 1 ELSE 0 END) as success_rate,
                    COUNT(CASE WHEN trimp IS NULL OR trimp <= 0 THEN 1 END) as error_count
                FROM activities 
                WHERE trimp_processed_at >= NOW() - INTERVAL '7 days'
                AND activity_id > 0
                GROUP BY DATE(trimp_processed_at)
                ORDER BY date DESC
            """, fetch=True)
            
            # Get ACWR performance trends
            acwr_trends = execute_query("""
                SELECT 
                    DATE(calculation_timestamp) as date,
                    COUNT(*) as total_calculations,
                    AVG(enhanced_chronic_load) as avg_calculation_time,
                    COUNT(CASE WHEN enhanced_chronic_load IS NULL OR enhanced_chronic_load <= 0 THEN 1 END) as slow_calculations
                FROM acwr_enhanced_calculations 
                WHERE calculation_timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(calculation_timestamp)
                ORDER BY date DESC
            """, fetch=True)
            
            return {
                'trimp_trends': [dict(trend) for trend in trimp_trends] if trimp_trends else [],
                'acwr_trends': [dict(trend) for trend in acwr_trends] if acwr_trends else [],
                'trend_period': '7 days',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'trend_period': '7 days',
                'last_updated': datetime.now().isoformat()
            }
    
    def _calculate_overall_health(self, components: List[ComponentStatus]) -> int:
        """Calculate overall system health score"""
        if not components:
            return 0
        
        # Weight components by importance
        weights = {
            SystemComponent.TRIMP_CALCULATIONS: 0.20,
            SystemComponent.ACWR_CALCULATIONS: 0.20,
            SystemComponent.DATABASE: 0.15,
            SystemComponent.API_ENDPOINTS: 0.10,
            SystemComponent.FEATURE_FLAGS: 0.05,
            SystemComponent.MIGRATION_SYSTEM: 0.05,
            SystemComponent.CLOUD_RUN: 0.15,
            SystemComponent.CLOUD_SQL: 0.10
        }
        
        weighted_score = 0
        total_weight = 0
        
        for component in components:
            weight = weights.get(component.component, 0.1)
            weighted_score += component.health_score * weight
            total_weight += weight
        
        return int(weighted_score / total_weight) if total_weight > 0 else 0
    
    def _calculate_component_health_score(self, success_rate: float, error_rate: float, total_activities: int) -> int:
        """Calculate health score for a component"""
        score = 100
        
        # Deduct for low success rate
        if success_rate < 95:
            score -= (95 - success_rate) * 2
        
        # Deduct for high error rate
        if error_rate > 0:
            score -= min(50, error_rate * 1000)  # Scale error rate
        
        # Bonus for high activity
        if total_activities > 100:
            score = min(100, score + 5)
        
        return max(0, int(score))
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache_timestamps:
            return False
        
        cache_age = (datetime.now() - self.cache_timestamps[cache_key]).total_seconds()
        return cache_age < self.cache_duration
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def _get_cloud_run_status(self) -> ComponentStatus:
        """Get Cloud Run service status"""
        try:
            import os
            
            # Check if we're running in Cloud Run environment
            if not os.environ.get('K_SERVICE'):
                return ComponentStatus(
                    component=SystemComponent.CLOUD_RUN,
                    status="healthy",
                    health_score=95,
                    last_updated=datetime.now(),
                    metrics={
                        'environment': 'local_development',
                        'message': 'Not running in Cloud Run environment'
                    },
                    alerts=[]
                )
            
            # Get Cloud Run service info from environment variables
            service_name = os.environ.get('K_SERVICE', 'strava-training-personal')
            service_revision = os.environ.get('K_REVISION', 'unknown')
            service_configuration = os.environ.get('K_CONFIGURATION', 'unknown')
            
            # Get service URL from environment or construct it
            service_url = os.environ.get('K_SERVICE_URL', f'https://{service_name}-xxx.run.app')
            
            # Get resource limits from environment
            memory_limit = os.environ.get('MEMORY_LIMIT', '512Mi')
            cpu_limit = os.environ.get('CPU_LIMIT', '1000m')
            
            # Since we're running in Cloud Run, assume it's healthy
            # The fact that we're executing means the service is running
            health_score = 95
            status_text = "healthy"
            
            return ComponentStatus(
                component=SystemComponent.CLOUD_RUN,
                status=status_text,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics={
                    'service_name': service_name,
                    'service_revision': service_revision,
                    'service_configuration': service_configuration,
                    'service_url': service_url,
                    'cpu_limit': cpu_limit,
                    'memory_limit': memory_limit,
                    'environment': 'cloud_run_production'
                },
                alerts=[]
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.CLOUD_RUN,
                status="warning",
                health_score=70,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"cloud_run_exception_{int(time.time())}",
                    component=SystemComponent.CLOUD_RUN,
                    severity=AlertSeverity.MEDIUM,
                    title="Cloud Run Status Check Failed",
                    message=f"Exception during Cloud Run status check: {str(e)}",
                    timestamp=datetime.now(),
                    acknowledged=False,
                    resolved=False,
                    details={'exception': str(e)}
                )]
            )
    
    def _get_cloud_sql_status(self) -> ComponentStatus:
        """Get Cloud SQL instance status"""
        try:
            import os
            
            # Check if we're running in Cloud Run environment
            if not os.environ.get('K_SERVICE'):
                return ComponentStatus(
                    component=SystemComponent.CLOUD_SQL,
                    status="healthy",
                    health_score=95,
                    last_updated=datetime.now(),
                    metrics={
                        'environment': 'local_development',
                        'message': 'Not running in Cloud Run environment'
                    },
                    alerts=[]
                )
            
            # Test database connectivity as a proxy for Cloud SQL health
            from db_utils import execute_query
            
            # Simple connectivity test
            test_result = execute_query("SELECT 1 as test", fetch=True)
            
            if test_result:
                # Database is accessible, assume Cloud SQL is healthy
                health_score = 95
                status_text = "healthy"
                alerts = []
            else:
                health_score = 50
                status_text = "critical"
                alerts = [Alert(
                    id=f"cloud_sql_connectivity_failed_{int(time.time())}",
                    component=SystemComponent.CLOUD_SQL,
                    severity=AlertSeverity.CRITICAL,
                    title="Cloud SQL Connectivity Failed",
                    message="Cannot connect to Cloud SQL instance",
                    timestamp=datetime.now(),
                    acknowledged=False,
                    resolved=False,
                    details={'test_query': 'SELECT 1'}
                )]
            
            # Get database info from connection
            db_info = execute_query("SELECT version() as version", fetch=True)
            version = db_info[0]['version'] if db_info else 'Unknown'
            
            return ComponentStatus(
                component=SystemComponent.CLOUD_SQL,
                status=status_text,
                health_score=health_score,
                last_updated=datetime.now(),
                metrics={
                    'database_version': version,
                    'instance_name': 'train-monk-db-v3',
                    'connectivity_test': 'passed' if test_result else 'failed',
                    'environment': 'cloud_run_production'
                },
                alerts=alerts
            )
            
        except Exception as e:
            return ComponentStatus(
                component=SystemComponent.CLOUD_SQL,
                status="warning",
                health_score=70,
                last_updated=datetime.now(),
                metrics={'error': str(e)},
                alerts=[Alert(
                    id=f"cloud_sql_exception_{int(time.time())}",
                    component=SystemComponent.CLOUD_SQL,
                    severity=AlertSeverity.MEDIUM,
                    title="Cloud SQL Status Check Failed",
                    message=f"Exception during Cloud SQL status check: {str(e)}",
                    timestamp=datetime.now(),
                    acknowledged=False,
                    resolved=False,
                    details={'exception': str(e)}
                )]
            )
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                return True
        return False

# Global instance
dashboard = ComprehensiveAdminDashboard()
