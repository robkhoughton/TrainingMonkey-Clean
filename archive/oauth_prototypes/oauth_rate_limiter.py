#!/usr/bin/env python3
"""
OAuth Rate Limiting and Security Measures for Training Monkey™ Dashboard
Implements rate limiting, security monitoring, and protection measures for OAuth flows
"""

import time
import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from collections import defaultdict, deque
import db_utils

logger = logging.getLogger(__name__)


class OAuthRateLimiter:
    """OAuth rate limiting and security monitoring system"""

    def __init__(self):
        """Initialize rate limiter with default limits"""
        self.rate_limits = {
            'oauth_initiation': {
                'max_requests': 5,
                'window_seconds': 300,  # 5 minutes
                'description': 'OAuth initiation requests'
            },
            'oauth_callback': {
                'max_requests': 10,
                'window_seconds': 600,  # 10 minutes
                'description': 'OAuth callback requests'
            },
            'token_refresh': {
                'max_requests': 20,
                'window_seconds': 3600,  # 1 hour
                'description': 'Token refresh requests'
            },
            'api_requests': {
                'max_requests': 100,
                'window_seconds': 3600,  # 1 hour
                'description': 'General API requests'
            }
        }
        
        # In-memory storage for rate limiting (can be replaced with Redis in production)
        self.request_history = defaultdict(lambda: defaultdict(deque))
        self.blocked_ips = {}
        self.suspicious_activities = defaultdict(list)
        
    def _get_client_identifier(self, request_data: Dict[str, Any]) -> str:
        """Generate a unique identifier for the client"""
        try:
            # Use IP address as primary identifier
            ip_address = request_data.get('ip_address', 'unknown')
            
            # Add user agent hash for additional uniqueness
            user_agent = request_data.get('user_agent', 'unknown')
            user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
            
            # Add user ID if available
            user_id = request_data.get('user_id', 'anonymous')
            
            return f"{ip_address}:{user_agent_hash}:{user_id}"
            
        except Exception as e:
            logger.error(f"Error generating client identifier: {str(e)}")
            return "unknown_client"
    
    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        try:
            if ip_address in self.blocked_ips:
                block_info = self.blocked_ips[ip_address]
                if datetime.now() < block_info['expires_at']:
                    return True
                else:
                    # Remove expired block
                    del self.blocked_ips[ip_address]
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking IP block status: {str(e)}")
            return False
    
    def _block_ip(self, ip_address: str, reason: str, duration_minutes: int = 60):
        """Block an IP address for a specified duration"""
        try:
            self.blocked_ips[ip_address] = {
                'reason': reason,
                'blocked_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(minutes=duration_minutes)
            }
            
            logger.warning(f"IP {ip_address} blocked for {duration_minutes} minutes. Reason: {reason}")
            
            # Log to database
            self._log_security_event('ip_blocked', {
                'ip_address': ip_address,
                'reason': reason,
                'duration_minutes': duration_minutes
            })
            
        except Exception as e:
            logger.error(f"Error blocking IP {ip_address}: {str(e)}")
    
    def _log_security_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log security events to database"""
        try:
            db_utils.execute_query(
                """INSERT INTO oauth_security_log 
                   (event_type, event_data, timestamp, ip_address, user_agent)
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    event_type,
                    json.dumps(event_data),
                    datetime.now().isoformat(),
                    event_data.get('ip_address', 'unknown'),
                    event_data.get('user_agent', 'unknown')
                ),
                fetch=False
            )
            
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
    
    def _detect_suspicious_activity(self, client_id: str, request_data: Dict[str, Any]) -> List[str]:
        """Detect suspicious activity patterns"""
        suspicious_patterns = []
        
        try:
            ip_address = request_data.get('ip_address', 'unknown')
            user_agent = request_data.get('user_agent', 'unknown')
            user_id = request_data.get('user_id', 'anonymous')
            
            # Check for rapid successive requests
            recent_requests = self.request_history[client_id].get('all_requests', deque())
            if len(recent_requests) >= 3:
                time_diff = time.time() - recent_requests[-3]
                if time_diff < 5:  # 3 requests within 5 seconds
                    suspicious_patterns.append('rapid_requests')
            
            # Check for missing or suspicious user agent
            if not user_agent or user_agent == 'unknown' or len(user_agent) < 10:
                suspicious_patterns.append('suspicious_user_agent')
            
            # Check for multiple failed attempts
            failed_attempts = self.suspicious_activities[client_id]
            recent_failures = [f for f in failed_attempts if time.time() - f['timestamp'] < 3600]
            if len(recent_failures) >= 5:
                suspicious_patterns.append('multiple_failures')
            
            # Check for unusual request patterns
            if user_id == 'anonymous' and len(recent_requests) > 10:
                suspicious_patterns.append('anonymous_abuse')
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {str(e)}")
        
        return suspicious_patterns
    
    def check_rate_limit(self, limit_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if request is within rate limits"""
        try:
            client_id = self._get_client_identifier(request_data)
            ip_address = request_data.get('ip_address', 'unknown')
            
            # Check if IP is blocked
            if self._is_ip_blocked(ip_address):
                return {
                    'allowed': False,
                    'reason': 'ip_blocked',
                    'message': 'IP address is temporarily blocked',
                    'retry_after': None
                }
            
            # Get rate limit configuration
            if limit_type not in self.rate_limits:
                logger.warning(f"Unknown rate limit type: {limit_type}")
                return {'allowed': True}
            
            limit_config = self.rate_limits[limit_type]
            max_requests = limit_config['max_requests']
            window_seconds = limit_config['window_seconds']
            
            # Get request history for this client and limit type
            history_key = f"{limit_type}_{client_id}"
            request_times = self.request_history[client_id][history_key]
            
            # Remove old requests outside the window
            current_time = time.time()
            while request_times and current_time - request_times[0] > window_seconds:
                request_times.popleft()
            
            # Check if limit exceeded
            if len(request_times) >= max_requests:
                # Calculate retry time
                oldest_request = request_times[0] if request_times else current_time
                retry_after = int(oldest_request + window_seconds - current_time)
                
                # Log rate limit violation
                self._log_security_event('rate_limit_exceeded', {
                    'client_id': client_id,
                    'ip_address': ip_address,
                    'limit_type': limit_type,
                    'max_requests': max_requests,
                    'window_seconds': window_seconds,
                    'current_requests': len(request_times)
                })
                
                # Check for suspicious activity
                suspicious_patterns = self._detect_suspicious_activity(client_id, request_data)
                if suspicious_patterns:
                    # Block IP for suspicious activity
                    self._block_ip(ip_address, f"Suspicious activity: {', '.join(suspicious_patterns)}", 120)
                    
                    return {
                        'allowed': False,
                        'reason': 'suspicious_activity',
                        'message': 'Suspicious activity detected',
                        'retry_after': None
                    }
                
                return {
                    'allowed': False,
                    'reason': 'rate_limit_exceeded',
                    'message': f'Rate limit exceeded for {limit_config["description"]}',
                    'retry_after': retry_after,
                    'limit_info': {
                        'max_requests': max_requests,
                        'window_seconds': window_seconds,
                        'current_requests': len(request_times)
                    }
                }
            
            # Add current request to history
            request_times.append(current_time)
            
            # Also track all requests for suspicious activity detection
            self.request_history[client_id]['all_requests'].append(current_time)
            
            return {
                'allowed': True,
                'remaining_requests': max_requests - len(request_times),
                'reset_time': current_time + window_seconds
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return {'allowed': True}  # Allow on error
    
    def record_failed_attempt(self, request_data: Dict[str, Any], failure_reason: str):
        """Record a failed OAuth attempt"""
        try:
            client_id = self._get_client_identifier(request_data)
            ip_address = request_data.get('ip_address', 'unknown')
            
            # Record failure
            self.suspicious_activities[client_id].append({
                'timestamp': time.time(),
                'reason': failure_reason,
                'ip_address': ip_address
            })
            
            # Clean up old failures (older than 24 hours)
            current_time = time.time()
            self.suspicious_activities[client_id] = [
                f for f in self.suspicious_activities[client_id]
                if current_time - f['timestamp'] < 86400
            ]
            
            # Log failure
            self._log_security_event('oauth_failure', {
                'client_id': client_id,
                'ip_address': ip_address,
                'failure_reason': failure_reason,
                'user_agent': request_data.get('user_agent', 'unknown')
            })
            
        except Exception as e:
            logger.error(f"Error recording failed attempt: {str(e)}")
    
    def get_rate_limit_status(self, client_id: str = None) -> Dict[str, Any]:
        """Get current rate limit status"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'rate_limits': {},
                'blocked_ips': len(self.blocked_ips),
                'suspicious_clients': len(self.suspicious_activities)
            }
            
            if client_id:
                # Get status for specific client
                for limit_type, config in self.rate_limits.items():
                    history_key = f"{limit_type}_{client_id}"
                    request_times = self.request_history[client_id][history_key]
                    
                    # Remove old requests
                    current_time = time.time()
                    while request_times and current_time - request_times[0] > config['window_seconds']:
                        request_times.popleft()
                    
                    status['rate_limits'][limit_type] = {
                        'current_requests': len(request_times),
                        'max_requests': config['max_requests'],
                        'remaining_requests': config['max_requests'] - len(request_times),
                        'window_seconds': config['window_seconds']
                    }
            else:
                # Get overall status
                for limit_type, config in self.rate_limits.items():
                    status['rate_limits'][limit_type] = {
                        'max_requests': config['max_requests'],
                        'window_seconds': config['window_seconds'],
                        'description': config['description']
                    }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {str(e)}")
            return {'error': str(e)}
    
    def cleanup_expired_data(self):
        """Clean up expired rate limiting data"""
        try:
            current_time = time.time()
            
            # Clean up request history
            for client_id in list(self.request_history.keys()):
                for history_key in list(self.request_history[client_id].keys()):
                    request_times = self.request_history[client_id][history_key]
                    
                    # Remove old requests
                    while request_times and current_time - request_times[0] > 86400:  # 24 hours
                        request_times.popleft()
                    
                    # Remove empty history
                    if not request_times:
                        del self.request_history[client_id][history_key]
                
                # Remove empty client history
                if not self.request_history[client_id]:
                    del self.request_history[client_id]
            
            # Clean up blocked IPs
            for ip_address in list(self.blocked_ips.keys()):
                if datetime.now() >= self.blocked_ips[ip_address]['expires_at']:
                    del self.blocked_ips[ip_address]
            
            logger.info("Cleaned up expired rate limiting data")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired data: {str(e)}")


class OAuthSecurityMonitor:
    """OAuth security monitoring and alerting system"""

    def __init__(self):
        """Initialize security monitor"""
        self.alert_thresholds = {
            'failed_attempts_per_hour': 10,
            'rate_limit_violations_per_hour': 5,
            'suspicious_ips_per_hour': 3,
            'blocked_ips_per_hour': 2
        }
        
        self.alerts = []
    
    def analyze_security_logs(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze security logs for patterns and threats"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Get security logs from database
            query = """
                SELECT event_type, event_data, timestamp, ip_address, user_agent
                FROM oauth_security_log 
                WHERE timestamp > %s
                ORDER BY timestamp DESC
            """
            
            result = db_utils.execute_query(query, (cutoff_time.isoformat(),), fetch=True)
            
            analysis = {
                'period_hours': hours,
                'total_events': len(result),
                'event_types': defaultdict(int),
                'ip_addresses': defaultdict(int),
                'threats_detected': [],
                'recommendations': []
            }
            
            # Analyze events
            for row in result:
                event_type = row['event_type']
                ip_address = row['ip_address']
                
                analysis['event_types'][event_type] += 1
                analysis['ip_addresses'][ip_address] += 1
            
            # Detect threats
            threats = self._detect_threats(analysis)
            analysis['threats_detected'] = threats
            
            # Generate recommendations
            recommendations = self._generate_recommendations(analysis)
            analysis['recommendations'] = recommendations
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing security logs: {str(e)}")
            return {'error': str(e)}
    
    def _detect_threats(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect security threats from analysis data"""
        threats = []
        
        try:
            # Check for high failure rates
            failed_attempts = analysis['event_types'].get('oauth_failure', 0)
            if failed_attempts > self.alert_thresholds['failed_attempts_per_hour']:
                threats.append({
                    'type': 'high_failure_rate',
                    'severity': 'high',
                    'description': f'High number of OAuth failures: {failed_attempts}',
                    'recommendation': 'Investigate failed authentication attempts'
                })
            
            # Check for rate limit violations
            rate_limit_violations = analysis['event_types'].get('rate_limit_exceeded', 0)
            if rate_limit_violations > self.alert_thresholds['rate_limit_violations_per_hour']:
                threats.append({
                    'type': 'rate_limit_abuse',
                    'severity': 'medium',
                    'description': f'High number of rate limit violations: {rate_limit_violations}',
                    'recommendation': 'Consider adjusting rate limits or implementing additional protection'
                })
            
            # Check for suspicious IPs
            suspicious_ips = [ip for ip, count in analysis['ip_addresses'].items() if count > 20]
            if len(suspicious_ips) > self.alert_thresholds['suspicious_ips_per_hour']:
                threats.append({
                    'type': 'suspicious_ips',
                    'severity': 'medium',
                    'description': f'Multiple suspicious IP addresses detected: {len(suspicious_ips)}',
                    'recommendation': 'Investigate IP addresses with high request volumes'
                })
            
        except Exception as e:
            logger.error(f"Error detecting threats: {str(e)}")
        
        return threats
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        try:
            total_events = analysis['total_events']
            
            if total_events > 1000:
                recommendations.append("Consider implementing additional rate limiting measures")
            
            if analysis['event_types'].get('oauth_failure', 0) > 50:
                recommendations.append("Review OAuth error handling and user guidance")
            
            if len(analysis['threats_detected']) > 0:
                recommendations.append("Implement automated threat response mechanisms")
            
            if analysis['event_types'].get('suspicious_activity', 0) > 10:
                recommendations.append("Consider implementing CAPTCHA or additional verification")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
        
        return recommendations


# Global instances
rate_limiter = OAuthRateLimiter()
security_monitor = OAuthSecurityMonitor()


def create_oauth_security_tables():
    """Create OAuth security tables if they don't exist"""
    try:
        # Create security log table
        create_log_table_query = """
        CREATE TABLE IF NOT EXISTS oauth_security_log (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            event_data JSON,
            timestamp TIMESTAMP NOT NULL,
            ip_address VARCHAR(45),
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
        
        db_utils.execute_query(create_log_table_query, fetch=False)
        logger.info("OAuth security log table created/verified")
        
    except Exception as e:
        logger.error(f"Error creating OAuth security tables: {str(e)}")


def get_oauth_security_status() -> Dict[str, Any]:
    """Get overall OAuth security status"""
    try:
        # Get rate limiter status
        rate_limit_status = rate_limiter.get_rate_limit_status()
        
        # Get security analysis
        security_analysis = security_monitor.analyze_security_logs(hours=24)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'rate_limiting': rate_limit_status,
            'security_analysis': security_analysis,
            'active_protections': {
                'rate_limiting': True,
                'ip_blocking': True,
                'suspicious_activity_detection': True,
                'security_logging': True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting OAuth security status: {str(e)}")
        return {'error': str(e)}


def cleanup_oauth_security_data():
    """Clean up old OAuth security data"""
    try:
        # Clean up rate limiter data
        rate_limiter.cleanup_expired_data()
        
        # Clean up old security logs (older than 30 days)
        cutoff_date = datetime.now() - timedelta(days=30)
        
        db_utils.execute_query(
            "DELETE FROM oauth_security_log WHERE timestamp < %s",
            (cutoff_date.isoformat(),),
            fetch=False
        )
        
        logger.info("Cleaned up old OAuth security data")
        
    except Exception as e:
        logger.error(f"Error cleaning up OAuth security data: {str(e)}")



