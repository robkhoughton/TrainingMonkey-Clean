#!/usr/bin/env python3
"""
System Monitoring Dashboard for TRIMP Enhancement
Comprehensive monitoring of system performance and user experience metrics
"""

import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from db_utils import execute_query
from trimp_deployment_monitor import deployment_monitor
from feedback_collection_system import feedback_system

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected"""
    PERFORMANCE = "performance"
    USER_EXPERIENCE = "user_experience"
    SYSTEM_HEALTH = "system_health"
    BUSINESS_METRICS = "business_metrics"


class AlertLevel(Enum):
    """Alert levels for monitoring"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricData:
    """Individual metric data point"""
    metric_name: str
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Alert:
    """System alert"""
    alert_id: str
    alert_level: AlertLevel
    metric_name: str
    message: str
    threshold: float
    current_value: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SystemMonitoringDashboard:
    """Comprehensive system monitoring dashboard"""
    
    def __init__(self):
        self.metrics: List[MetricData] = []
        self.alerts: List[Alert] = []
        self.monitoring_active = False
    
    def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous monitoring"""
        self.monitoring_active = True
        logger.info(f"Starting system monitoring with {interval_seconds}s interval")
        
        while self.monitoring_active:
            try:
                self.collect_all_metrics()
                self.check_alerts()
                time.sleep(interval_seconds)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(interval_seconds)
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logger.info("System monitoring stopped")
    
    def collect_all_metrics(self):
        """Collect all system metrics"""
        try:
            # Performance metrics
            self._collect_performance_metrics()
            
            # User experience metrics
            self._collect_user_experience_metrics()
            
            # System health metrics
            self._collect_system_health_metrics()
            
            # Business metrics
            self._collect_business_metrics()
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {str(e)}")
    
    def _collect_performance_metrics(self):
        """Collect performance-related metrics"""
        try:
            # TRIMP calculation performance
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            # Get calculation metrics for last hour
            query = """
            SELECT 
                COUNT(*) as total_calculations,
                AVG(CASE WHEN trimp_processed_at IS NOT NULL THEN 1 ELSE 0 END) as success_rate,
                AVG(hr_stream_sample_count) as avg_hr_samples,
                COUNT(CASE WHEN trimp_calculation_method = 'enhanced_stream' THEN 1 END) as enhanced_calculations,
                COUNT(CASE WHEN trimp_calculation_method = 'average_hr' THEN 1 END) as average_calculations
            FROM activities 
            WHERE trimp_processed_at >= %s AND trimp_processed_at <= %s
            """
            
            results = execute_query(query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
            
            if results:
                result = results[0]
                
                # Add performance metrics
                self.metrics.append(MetricData(
                    metric_name="trimp_calculations_per_hour",
                    metric_type=MetricType.PERFORMANCE,
                    value=result['total_calculations'],
                    unit="calculations/hour",
                    timestamp=end_time,
                    metadata={'time_range': '1_hour'}
                ))
                
                self.metrics.append(MetricData(
                    metric_name="trimp_success_rate",
                    metric_type=MetricType.PERFORMANCE,
                    value=result['success_rate'] * 100,
                    unit="percentage",
                    timestamp=end_time,
                    metadata={'time_range': '1_hour'}
                ))
                
                self.metrics.append(MetricData(
                    metric_name="enhanced_calculation_ratio",
                    metric_type=MetricType.PERFORMANCE,
                    value=(result['enhanced_calculations'] / result['total_calculations'] * 100) if result['total_calculations'] > 0 else 0,
                    unit="percentage",
                    timestamp=end_time,
                    metadata={'time_range': '1_hour'}
                ))
                
                self.metrics.append(MetricData(
                    metric_name="avg_hr_stream_samples",
                    metric_type=MetricType.PERFORMANCE,
                    value=result['avg_hr_samples'] or 0,
                    unit="samples",
                    timestamp=end_time,
                    metadata={'time_range': '1_hour'}
                ))
            
        except Exception as e:
            logger.error(f"Error collecting performance metrics: {str(e)}")
    
    def _collect_user_experience_metrics(self):
        """Collect user experience metrics"""
        try:
            # Get user activity metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=24)
            
            # Active users in last 24 hours
            active_users_query = """
            SELECT COUNT(DISTINCT user_id) as active_users
            FROM activities 
            WHERE trimp_processed_at >= %s AND trimp_processed_at <= %s
            """
            
            active_users_result = execute_query(active_users_query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
            active_users = active_users_result[0]['active_users'] if active_users_result else 0
            
            self.metrics.append(MetricData(
                metric_name="active_users_24h",
                metric_type=MetricType.USER_EXPERIENCE,
                value=active_users,
                unit="users",
                timestamp=end_time,
                metadata={'time_range': '24_hours'}
            ))
            
            # User satisfaction from feedback
            feedback_summary = feedback_system.get_feedback_summary(7)  # Last 7 days
            if feedback_summary['average_rating']:
                self.metrics.append(MetricData(
                    metric_name="user_satisfaction_rating",
                    metric_type=MetricType.USER_EXPERIENCE,
                    value=feedback_summary['average_rating'],
                    unit="rating_1_5",
                    timestamp=end_time,
                    metadata={'time_range': '7_days'}
                ))
            
            # Feature adoption rate
            total_activities_query = """
            SELECT COUNT(*) as total_activities
            FROM activities 
            WHERE trimp_processed_at >= %s AND trimp_processed_at <= %s
            """
            
            total_activities_result = execute_query(total_activities_query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
            total_activities = total_activities_result[0]['total_activities'] if total_activities_result else 0
            
            if total_activities > 0:
                self.metrics.append(MetricData(
                    metric_name="feature_adoption_rate",
                    metric_type=MetricType.USER_EXPERIENCE,
                    value=(active_users / total_activities * 100) if total_activities > 0 else 0,
                    unit="percentage",
                    timestamp=end_time,
                    metadata={'time_range': '24_hours'}
                ))
            
        except Exception as e:
            logger.error(f"Error collecting user experience metrics: {str(e)}")
    
    def _collect_system_health_metrics(self):
        """Collect system health metrics"""
        try:
            # Database health
            db_health_query = "SELECT COUNT(*) as table_count FROM sqlite_master WHERE type='table'"
            db_result = execute_query(db_health_query, fetch=True)
            table_count = db_result[0]['table_count'] if db_result else 0
            
            self.metrics.append(MetricData(
                metric_name="database_table_count",
                metric_type=MetricType.SYSTEM_HEALTH,
                value=table_count,
                unit="tables",
                timestamp=datetime.now(),
                metadata={'component': 'database'}
            ))
            
            # Error rate
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            error_query = """
            SELECT COUNT(*) as error_count
            FROM activities 
            WHERE trimp_processed_at >= %s AND trimp_processed_at <= %s
            AND (trimp IS NULL OR trimp <= 0)
            """
            
            error_result = execute_query(error_query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
            error_count = error_result[0]['error_count'] if error_result else 0
            
            # Total calculations for error rate
            total_query = """
            SELECT COUNT(*) as total_count
            FROM activities 
            WHERE trimp_processed_at >= %s AND trimp_processed_at <= %s
            """
            
            total_result = execute_query(total_query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
            total_count = total_result[0]['total_count'] if total_result else 0
            
            error_rate = (error_count / total_count * 100) if total_count > 0 else 0
            
            self.metrics.append(MetricData(
                metric_name="system_error_rate",
                metric_type=MetricType.SYSTEM_HEALTH,
                value=error_rate,
                unit="percentage",
                timestamp=end_time,
                metadata={'time_range': '1_hour'}
            ))
            
            # Deployment metrics
            deployment_metrics = deployment_monitor.metrics
            self.metrics.append(MetricData(
                metric_name="deployment_uptime",
                metric_type=MetricType.SYSTEM_HEALTH,
                value=(datetime.now() - deployment_monitor.start_time).total_seconds() / 3600,
                unit="hours",
                timestamp=datetime.now(),
                metadata={'component': 'deployment'}
            ))
            
        except Exception as e:
            logger.error(f"Error collecting system health metrics: {str(e)}")
    
    def _collect_business_metrics(self):
        """Collect business-related metrics"""
        try:
            # TRIMP accuracy metrics
            feedback_summary = feedback_system.get_feedback_summary(30)  # Last 30 days
            accuracy_stats = feedback_summary['accuracy_statistics']
            
            self.metrics.append(MetricData(
                metric_name="trimp_accuracy_5_percent",
                metric_type=MetricType.BUSINESS_METRICS,
                value=accuracy_stats['accuracy_rate_5_percent'],
                unit="percentage",
                timestamp=datetime.now(),
                metadata={'time_range': '30_days'}
            ))
            
            self.metrics.append(MetricData(
                metric_name="trimp_accuracy_10_percent",
                metric_type=MetricType.BUSINESS_METRICS,
                value=accuracy_stats['accuracy_rate_10_percent'],
                unit="percentage",
                timestamp=datetime.now(),
                metadata={'time_range': '30_days'}
            ))
            
            # Feature flag adoption
            from utils.feature_flags import is_feature_enabled
            
            # Test different user types
            admin_access = is_feature_enabled('enhanced_trimp_calculation', 1)
            beta_access = is_feature_enabled('enhanced_trimp_calculation', 2)
            regular_access = is_feature_enabled('enhanced_trimp_calculation', 4)
            
            access_score = sum([admin_access, beta_access, regular_access]) / 3 * 100
            
            self.metrics.append(MetricData(
                metric_name="feature_flag_adoption",
                metric_type=MetricType.BUSINESS_METRICS,
                value=access_score,
                unit="percentage",
                timestamp=datetime.now(),
                metadata={'feature': 'enhanced_trimp_calculation'}
            ))
            
        except Exception as e:
            logger.error(f"Error collecting business metrics: {str(e)}")
    
    def check_alerts(self):
        """Check for alert conditions"""
        try:
            # Get recent metrics (last 5 minutes)
            cutoff_time = datetime.now() - timedelta(minutes=5)
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            
            # Check for critical alerts
            self._check_error_rate_alerts(recent_metrics)
            self._check_performance_alerts(recent_metrics)
            self._check_accuracy_alerts(recent_metrics)
            self._check_system_health_alerts(recent_metrics)
            
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    def _check_error_rate_alerts(self, metrics: List[MetricData]):
        """Check for error rate alerts"""
        error_metrics = [m for m in metrics if m.metric_name == 'system_error_rate']
        
        for metric in error_metrics:
            if metric.value > 10:  # More than 10% error rate
                self._create_alert(
                    metric_name=metric.metric_name,
                    message=f"High error rate: {metric.value:.1f}%",
                    threshold=10.0,
                    current_value=metric.value,
                    alert_level=AlertLevel.CRITICAL
                )
            elif metric.value > 5:  # More than 5% error rate
                self._create_alert(
                    metric_name=metric.metric_name,
                    message=f"Elevated error rate: {metric.value:.1f}%",
                    threshold=5.0,
                    current_value=metric.value,
                    alert_level=AlertLevel.WARNING
                )
    
    def _check_performance_alerts(self, metrics: List[MetricData]):
        """Check for performance alerts"""
        success_rate_metrics = [m for m in metrics if m.metric_name == 'trimp_success_rate']
        
        for metric in success_rate_metrics:
            if metric.value < 90:  # Less than 90% success rate
                self._create_alert(
                    metric_name=metric.metric_name,
                    message=f"Low success rate: {metric.value:.1f}%",
                    threshold=90.0,
                    current_value=metric.value,
                    alert_level=AlertLevel.WARNING
                )
    
    def _check_accuracy_alerts(self, metrics: List[MetricData]):
        """Check for accuracy alerts"""
        accuracy_metrics = [m for m in metrics if m.metric_name == 'trimp_accuracy_5_percent']
        
        for metric in accuracy_metrics:
            if metric.value < 80:  # Less than 80% accuracy
                self._create_alert(
                    metric_name=metric.metric_name,
                    message=f"Low accuracy: {metric.value:.1f}% within 5% of external sources",
                    threshold=80.0,
                    current_value=metric.value,
                    alert_level=AlertLevel.WARNING
                )
    
    def _check_system_health_alerts(self, metrics: List[MetricData]):
        """Check for system health alerts"""
        # Check for any system health issues
        health_metrics = [m for m in metrics if m.metric_type == MetricType.SYSTEM_HEALTH]
        
        for metric in health_metrics:
            if metric.metric_name == 'database_table_count' and metric.value < 5:
                self._create_alert(
                    metric_name=metric.metric_name,
                    message=f"Low database table count: {metric.value}",
                    threshold=5.0,
                    current_value=metric.value,
                    alert_level=AlertLevel.CRITICAL
                )
    
    def _create_alert(self, metric_name: str, message: str, threshold: float, 
                     current_value: float, alert_level: AlertLevel):
        """Create a new alert"""
        alert_id = f"alert_{int(time.time() * 1000)}"
        
        # Check if similar alert already exists
        existing_alerts = [a for a in self.alerts 
                          if a.metric_name == metric_name and not a.resolved]
        
        if existing_alerts:
            return  # Don't create duplicate alerts
        
        alert = Alert(
            alert_id=alert_id,
            alert_level=alert_level,
            metric_name=metric_name,
            message=message,
            threshold=threshold,
            current_value=current_value,
            timestamp=datetime.now()
        )
        
        self.alerts.append(alert)
        logger.warning(f"ALERT [{alert_level.value.upper()}] {message}")
    
    def get_dashboard_data(self, hours_back: int = 24) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            recent_alerts = [a for a in self.alerts if a.timestamp >= cutoff_time]
            
            # Group metrics by type
            metrics_by_type = {}
            for metric in recent_metrics:
                metric_type = metric.metric_type.value
                if metric_type not in metrics_by_type:
                    metrics_by_type[metric_type] = []
                metrics_by_type[metric_type].append({
                    'name': metric.metric_name,
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp.isoformat(),
                    'metadata': metric.metadata
                })
            
            # Group alerts by level
            alerts_by_level = {}
            for alert in recent_alerts:
                level = alert.alert_level.value
                if level not in alerts_by_level:
                    alerts_by_level[level] = []
                alerts_by_level[level].append({
                    'alert_id': alert.alert_id,
                    'metric_name': alert.metric_name,
                    'message': alert.message,
                    'threshold': alert.threshold,
                    'current_value': alert.current_value,
                    'timestamp': alert.timestamp.isoformat(),
                    'resolved': alert.resolved
                })
            
            # Get current system status
            system_status = self._get_system_status()
            
            return {
                'dashboard_data': {
                    'time_range_hours': hours_back,
                    'generated_at': datetime.now().isoformat(),
                    'metrics_by_type': metrics_by_type,
                    'alerts_by_level': alerts_by_level,
                    'system_status': system_status
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            return {}
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            # Get deployment status
            deployment_status = deployment_monitor.get_deployment_status()
            
            # Get feedback summary
            feedback_summary = feedback_system.get_feedback_summary(7)
            
            # Calculate overall health score
            health_score = 100  # Start with perfect score
            
            # Deduct points for issues
            if feedback_summary['accuracy_statistics']['accuracy_rate_5_percent'] < 90:
                health_score -= 20
            
            if feedback_summary['average_rating'] and feedback_summary['average_rating'] < 3.0:
                health_score -= 15
            
            # Check for critical alerts
            critical_alerts = [a for a in self.alerts if a.alert_level == AlertLevel.CRITICAL and not a.resolved]
            health_score -= len(critical_alerts) * 10
            
            # Check for warning alerts
            warning_alerts = [a for a in self.alerts if a.alert_level == AlertLevel.WARNING and not a.resolved]
            health_score -= len(warning_alerts) * 5
            
            health_score = max(0, health_score)  # Don't go below 0
            
            return {
                'overall_health_score': health_score,
                'deployment_phase': deployment_status['deployment_phase'],
                'deployment_uptime_hours': (datetime.now() - deployment_monitor.start_time).total_seconds() / 3600,
                'active_alerts': {
                    'critical': len(critical_alerts),
                    'warning': len(warning_alerts),
                    'info': len([a for a in self.alerts if a.alert_level == AlertLevel.INFO and not a.resolved])
                },
                'user_satisfaction': feedback_summary['average_rating'],
                'accuracy_rate': feedback_summary['accuracy_statistics']['accuracy_rate_5_percent']
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {'overall_health_score': 0, 'error': str(e)}


# Global instance for use in routes
monitoring_dashboard = SystemMonitoringDashboard()
