#!/usr/bin/env python3
"""
Enhanced TRIMP Performance Metrics
User-friendly monitoring and diagnosis tools
"""

import json
from datetime import datetime, timedelta
from db_utils import execute_query
from db_connection_manager import db_manager

def get_enhanced_trimp_metrics(hours_back=24):
    """
    Get enhanced TRIMP performance metrics with better formatting and diagnosis
    """
    try:
        # Initialize database connection pool if needed
        from db_connection_manager import initialize_database_pool
        import os
        database_url = os.environ.get('DATABASE_URL')
        if database_url and not initialize_database_pool(database_url):
            return {
                'success': False,
                'error': 'Failed to initialize database connection pool',
                'timestamp': datetime.now().isoformat()
            }
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Get comprehensive performance data
        metrics = _get_performance_summary(start_time, end_time)
        trends = _get_hourly_trends(start_time, end_time)
        errors = _get_error_analysis(start_time, end_time)
        system_health = _get_system_health()
        recommendations = _get_recommendations(metrics, errors, system_health)
        
        return {
            'success': True,
            'summary': _format_summary(metrics, errors, system_health),
            'detailed_metrics': metrics,
            'hourly_trends': trends,
            'error_analysis': errors,
            'system_health': system_health,
            'recommendations': recommendations,
            'time_range': {
                'start': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end': end_time.strftime('%Y-%m-%d %H:%M:%S'),
                'hours_analyzed': hours_back
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to get metrics: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }

def _get_performance_summary(start_time, end_time):
    """Get overall performance summary"""
    query = """
    SELECT 
        trimp_calculation_method,
        COUNT(*) as total_calculations,
        AVG(CASE WHEN trimp_processed_at IS NOT NULL THEN 1 ELSE 0 END) as success_rate,
        AVG(hr_stream_sample_count) as avg_hr_samples,
        AVG(trimp) as avg_trimp_value,
        MIN(trimp_processed_at) as first_calculation,
        MAX(trimp_processed_at) as last_calculation
    FROM activities 
    WHERE trimp_processed_at >= %s
    AND trimp_processed_at <= %s
    AND activity_id > 0
    GROUP BY trimp_calculation_method
    ORDER BY total_calculations DESC
    """
    
    results = execute_query(query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
    
    summary = {
        'total_activities_processed': sum(r['total_calculations'] for r in results),
        'calculation_methods': {},
        'overall_success_rate': 0,
        'performance_score': 'Unknown'
    }
    
    total_successful = 0
    total_attempts = 0
    
    for result in results:
        method = result['trimp_calculation_method']
        total_calc = result['total_calculations']
        success_rate = result['success_rate'] * 100 if result['success_rate'] else 0
        
        summary['calculation_methods'][method] = {
            'total_calculations': total_calc,
            'success_rate_percent': round(success_rate, 1),
            'avg_hr_samples': round(result['avg_hr_samples'] or 0, 0),
            'avg_trimp_value': round(result['avg_trimp_value'] or 0, 2),
            'first_calculation': result['first_calculation'].strftime('%H:%M:%S') if result['first_calculation'] else 'N/A',
            'last_calculation': result['last_calculation'].strftime('%H:%M:%S') if result['last_calculation'] else 'N/A'
        }
        
        total_successful += total_calc * (success_rate / 100)
        total_attempts += total_calc
    
    if total_attempts > 0:
        summary['overall_success_rate'] = round((total_successful / total_attempts) * 100, 1)
        summary['performance_score'] = _calculate_performance_score(summary['overall_success_rate'])
    
    return summary

def _get_hourly_trends(start_time, end_time):
    """Get hourly processing trends"""
    query = """
    SELECT 
        EXTRACT(HOUR FROM trimp_processed_at) as hour,
        trimp_calculation_method,
        COUNT(*) as calculations_count,
        AVG(hr_stream_sample_count) as avg_hr_samples,
        AVG(trimp) as avg_trimp_value
    FROM activities 
    WHERE trimp_processed_at >= %s
    AND trimp_processed_at <= %s
    AND activity_id > 0
    GROUP BY EXTRACT(HOUR FROM trimp_processed_at), trimp_calculation_method
    ORDER BY hour, trimp_calculation_method
    """
    
    results = execute_query(query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
    
    # Organize by hour
    hourly_data = {}
    for result in results:
        hour = int(result['hour'])
        method = result['trimp_calculation_method']
        
        if hour not in hourly_data:
            hourly_data[hour] = {
                'hour': hour,
                'total_calculations': 0,
                'methods': {}
            }
        
        hourly_data[hour]['methods'][method] = {
            'calculations': result['calculations_count'],
            'avg_hr_samples': round(result['avg_hr_samples'] or 0, 0),
            'avg_trimp': round(result['avg_trimp_value'] or 0, 2)
        }
        hourly_data[hour]['total_calculations'] += result['calculations_count']
    
    return list(hourly_data.values())

def _get_error_analysis(start_time, end_time):
    """Get detailed error analysis"""
    query = """
    SELECT 
        trimp_calculation_method,
        COUNT(*) as total_attempts,
        SUM(CASE WHEN trimp IS NULL OR trimp <= 0 THEN 1 ELSE 0 END) as error_count,
        SUM(CASE WHEN trimp IS NULL THEN 1 ELSE 0 END) as null_trimp_count,
        SUM(CASE WHEN trimp <= 0 AND trimp IS NOT NULL THEN 1 ELSE 0 END) as zero_trimp_count
    FROM activities 
    WHERE trimp_processed_at >= %s
    AND trimp_processed_at <= %s
    AND activity_id > 0
    GROUP BY trimp_calculation_method
    """
    
    results = execute_query(query, (start_time.isoformat(), end_time.isoformat()), fetch=True)
    
    error_analysis = {
        'total_errors': 0,
        'total_attempts': 0,
        'overall_error_rate': 0,
        'method_breakdown': {},
        'error_severity': 'Unknown'
    }
    
    for result in results:
        method = result['trimp_calculation_method']
        total = result['total_attempts']
        errors = result['error_count']
        null_count = result['null_trimp_count']
        zero_count = result['zero_trimp_count']
        
        error_rate = (errors / total * 100) if total > 0 else 0
        
        error_analysis['method_breakdown'][method] = {
            'total_attempts': total,
            'error_count': errors,
            'error_rate_percent': round(error_rate, 1),
            'null_trimp_count': null_count,
            'zero_trimp_count': zero_count,
            'severity': _get_error_severity(error_rate)
        }
        
        error_analysis['total_errors'] += errors
        error_analysis['total_attempts'] += total
    
    if error_analysis['total_attempts'] > 0:
        error_analysis['overall_error_rate'] = round((error_analysis['total_errors'] / error_analysis['total_attempts']) * 100, 1)
        error_analysis['error_severity'] = _get_error_severity(error_analysis['overall_error_rate'])
    
    return error_analysis

def _get_system_health():
    """Get system health metrics"""
    try:
        # Get database connection pool status
        pool_status = db_manager.get_pool_status()
        
        # Get recent activity processing rate
        recent_activities = execute_query("""
            SELECT COUNT(*) as count
            FROM activities 
            WHERE trimp_processed_at >= NOW() - INTERVAL '1 hour'
            AND activity_id > 0
        """, fetch=True)
        
        activities_last_hour = recent_activities[0]['count'] if recent_activities else 0
        
        return {
            'database_pool': {
                'status': pool_status.get('status', 'unknown'),
                'active_connections': pool_status.get('active_connections', 0),
                'pool_utilization': round(pool_status.get('pool_utilization', 0), 1),
                'connection_errors': pool_status.get('stats', {}).get('connection_errors', 0)
            },
            'processing_rate': {
                'activities_last_hour': activities_last_hour,
                'rate_status': 'Good' if activities_last_hour > 0 else 'No Activity'
            },
            'health_score': _calculate_health_score(pool_status, activities_last_hour)
        }
        
    except Exception as e:
        return {
            'database_pool': {'status': 'error', 'error': str(e)},
            'processing_rate': {'activities_last_hour': 0, 'rate_status': 'Unknown'},
            'health_score': 'Unknown'
        }

def _get_recommendations(metrics, errors, system_health):
    """Generate actionable recommendations"""
    recommendations = []
    
    # Performance recommendations
    if metrics['overall_success_rate'] < 95:
        recommendations.append({
            'category': 'Performance',
            'priority': 'High',
            'issue': f"Low success rate: {metrics['overall_success_rate']}%",
            'recommendation': 'Investigate TRIMP calculation failures and check heart rate data quality',
            'action': 'Review error logs and validate HR data sources'
        })
    
    # Error rate recommendations
    if errors['overall_error_rate'] > 5:
        recommendations.append({
            'category': 'Error Rate',
            'priority': 'High',
            'issue': f"High error rate: {errors['overall_error_rate']}%",
            'recommendation': 'Focus on improving data validation and error handling',
            'action': 'Check for missing HR data or invalid activity types'
        })
    
    # System health recommendations
    if system_health['health_score'] == 'Poor':
        recommendations.append({
            'category': 'System Health',
            'priority': 'Medium',
            'issue': 'System health issues detected',
            'recommendation': 'Monitor database connections and processing rates',
            'action': 'Check database performance and connection pool status'
        })
    
    # Processing rate recommendations
    if system_health['processing_rate']['activities_last_hour'] == 0:
        recommendations.append({
            'category': 'Processing',
            'priority': 'Medium',
            'issue': 'No activities processed in the last hour',
            'recommendation': 'Check if Strava sync is working properly',
            'action': 'Verify Strava API connectivity and sync processes'
        })
    
    if not recommendations:
        recommendations.append({
            'category': 'Status',
            'priority': 'Info',
            'issue': 'System operating normally',
            'recommendation': 'Continue monitoring for any issues',
            'action': 'No immediate action required'
        })
    
    return recommendations

def _format_summary(metrics, errors, system_health):
    """Format a human-readable summary"""
    return {
        'status': '✅ Healthy' if metrics['performance_score'] == 'Excellent' else 
                 '⚠️ Issues Detected' if metrics['performance_score'] in ['Good', 'Fair'] else 
                 '❌ Problems Found',
        'key_metrics': {
            'activities_processed': metrics['total_activities_processed'],
            'success_rate': f"{metrics['overall_success_rate']}%",
            'error_rate': f"{errors['overall_error_rate']}%",
            'system_health': system_health['health_score']
        },
        'top_issues': [
            f"Error rate: {errors['overall_error_rate']}%" if errors['overall_error_rate'] > 0 else "No errors detected",
            f"Success rate: {metrics['overall_success_rate']}%" if metrics['overall_success_rate'] < 100 else "Perfect success rate"
        ]
    }

def _calculate_performance_score(success_rate):
    """Calculate performance score based on success rate"""
    if success_rate >= 99:
        return 'Excellent'
    elif success_rate >= 95:
        return 'Good'
    elif success_rate >= 90:
        return 'Fair'
    else:
        return 'Poor'

def _get_error_severity(error_rate):
    """Get error severity level"""
    if error_rate == 0:
        return 'None'
    elif error_rate <= 2:
        return 'Low'
    elif error_rate <= 5:
        return 'Medium'
    elif error_rate <= 10:
        return 'High'
    else:
        return 'Critical'

def _calculate_health_score(pool_status, activities_last_hour):
    """Calculate overall system health score"""
    score = 100
    
    # Deduct for connection issues
    if pool_status.get('status') != 'active':
        score -= 30
    
    # Deduct for high pool utilization
    if pool_status.get('pool_utilization', 0) > 80:
        score -= 20
    
    # Deduct for connection errors
    connection_errors = pool_status.get('stats', {}).get('connection_errors', 0)
    if connection_errors > 0:
        score -= min(connection_errors * 5, 30)
    
    # Deduct for no recent activity
    if activities_last_hour == 0:
        score -= 25
    
    if score >= 90:
        return 'Excellent'
    elif score >= 75:
        return 'Good'
    elif score >= 60:
        return 'Fair'
    else:
        return 'Poor'
