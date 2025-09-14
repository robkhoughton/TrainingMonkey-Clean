#!/usr/bin/env python3
"""
ACWR Feature Flag Monitoring and Logging
Handles comprehensive monitoring and logging for ACWR feature flags
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class FeatureFlagEvent:
    """Data class for feature flag events"""
    timestamp: datetime
    event_type: str  # 'access_granted', 'access_denied', 'flag_toggled', 'error'
    feature_name: str
    user_id: Optional[int]
    admin_user_id: Optional[int]
    details: Dict
    success: bool

class ACWRFeatureFlagMonitor:
    """Monitor and log ACWR feature flag activities"""
    
    def __init__(self):
        self.logger = logger
        self.events: List[FeatureFlagEvent] = []
        self.max_events = 1000  # Keep last 1000 events in memory
    
    def log_feature_access(self, feature_name: str, user_id: int, granted: bool, details: Dict = None):
        """Log feature flag access attempts"""
        try:
            event = FeatureFlagEvent(
                timestamp=datetime.now(),
                event_type='access_granted' if granted else 'access_denied',
                feature_name=feature_name,
                user_id=user_id,
                admin_user_id=None,
                details=details or {},
                success=granted
            )
            
            self._add_event(event)
            
            # Log to application logger
            if granted:
                self.logger.info(f"🎉 ACWR feature access granted to user {user_id} for {feature_name}")
            else:
                self.logger.info(f"⏳ ACWR feature access denied to user {user_id} for {feature_name}")
                
        except Exception as e:
            self.logger.error(f"Error logging feature access: {str(e)}")
    
    def log_feature_toggle(self, feature_name: str, admin_user_id: int, enabled: bool, details: Dict = None):
        """Log feature flag toggle events"""
        try:
            event = FeatureFlagEvent(
                timestamp=datetime.now(),
                event_type='flag_toggled',
                feature_name=feature_name,
                user_id=None,
                admin_user_id=admin_user_id,
                details=details or {},
                success=True
            )
            
            self._add_event(event)
            
            # Log to application logger
            self.logger.info(f"🔧 Admin {admin_user_id} toggled {feature_name} to {'enabled' if enabled else 'disabled'}")
            
        except Exception as e:
            self.logger.error(f"Error logging feature toggle: {str(e)}")
    
    def log_error(self, feature_name: str, user_id: Optional[int], error_message: str, details: Dict = None):
        """Log feature flag errors"""
        try:
            event = FeatureFlagEvent(
                timestamp=datetime.now(),
                event_type='error',
                feature_name=feature_name,
                user_id=user_id,
                admin_user_id=None,
                details=details or {'error': error_message},
                success=False
            )
            
            self._add_event(event)
            
            # Log to application logger
            self.logger.error(f"❌ ACWR feature flag error for {feature_name}: {error_message}")
            
        except Exception as e:
            self.logger.error(f"Error logging feature flag error: {str(e)}")
    
    def _add_event(self, event: FeatureFlagEvent):
        """Add event to memory store"""
        self.events.append(event)
        
        # Keep only the most recent events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
    
    def get_recent_events(self, hours_back: int = 24) -> List[Dict]:
        """Get recent events within specified time window"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            recent_events = [
                asdict(event) for event in self.events 
                if event.timestamp >= cutoff_time
            ]
            
            # Convert datetime objects to strings for JSON serialization
            for event in recent_events:
                event['timestamp'] = event['timestamp'].isoformat()
            
            return recent_events
            
        except Exception as e:
            self.logger.error(f"Error getting recent events: {str(e)}")
            return []
    
    def get_event_statistics(self, hours_back: int = 24) -> Dict:
        """Get statistics for recent events"""
        try:
            recent_events = self.get_recent_events(hours_back)
            
            if not recent_events:
                return {
                    'total_events': 0,
                    'access_granted': 0,
                    'access_denied': 0,
                    'flags_toggled': 0,
                    'errors': 0,
                    'unique_users': 0,
                    'success_rate': 0.0
                }
            
            # Calculate statistics
            total_events = len(recent_events)
            access_granted = sum(1 for e in recent_events if e['event_type'] == 'access_granted')
            access_denied = sum(1 for e in recent_events if e['event_type'] == 'access_denied')
            flags_toggled = sum(1 for e in recent_events if e['event_type'] == 'flag_toggled')
            errors = sum(1 for e in recent_events if e['event_type'] == 'error')
            
            # Get unique users
            user_ids = set()
            for event in recent_events:
                if event['user_id']:
                    user_ids.add(event['user_id'])
                if event['admin_user_id']:
                    user_ids.add(event['admin_user_id'])
            
            unique_users = len(user_ids)
            
            # Calculate success rate
            successful_events = sum(1 for e in recent_events if e['success'])
            success_rate = (successful_events / total_events) * 100 if total_events > 0 else 0.0
            
            return {
                'total_events': total_events,
                'access_granted': access_granted,
                'access_denied': access_denied,
                'flags_toggled': flags_toggled,
                'errors': errors,
                'unique_users': unique_users,
                'success_rate': round(success_rate, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting event statistics: {str(e)}")
            return {}
    
    def get_user_access_summary(self, hours_back: int = 24) -> Dict:
        """Get summary of user access patterns"""
        try:
            recent_events = self.get_recent_events(hours_back)
            
            user_summary = {}
            
            for event in recent_events:
                user_id = event.get('user_id')
                if not user_id:
                    continue
                
                if user_id not in user_summary:
                    user_summary[user_id] = {
                        'user_id': user_id,
                        'access_granted': 0,
                        'access_denied': 0,
                        'last_access': None,
                        'success_rate': 0.0
                    }
                
                if event['event_type'] == 'access_granted':
                    user_summary[user_id]['access_granted'] += 1
                elif event['event_type'] == 'access_denied':
                    user_summary[user_id]['access_denied'] += 1
                
                # Update last access time
                if not user_summary[user_id]['last_access'] or event['timestamp'] > user_summary[user_id]['last_access']:
                    user_summary[user_id]['last_access'] = event['timestamp']
            
            # Calculate success rates
            for user_id, summary in user_summary.items():
                total_attempts = summary['access_granted'] + summary['access_denied']
                if total_attempts > 0:
                    summary['success_rate'] = round((summary['access_granted'] / total_attempts) * 100, 2)
            
            return user_summary
            
        except Exception as e:
            self.logger.error(f"Error getting user access summary: {str(e)}")
            return {}
    
    def export_events(self, hours_back: int = 24) -> str:
        """Export events as JSON string"""
        try:
            recent_events = self.get_recent_events(hours_back)
            return json.dumps(recent_events, indent=2)
            
        except Exception as e:
            self.logger.error(f"Error exporting events: {str(e)}")
            return "[]"
    
    def clear_old_events(self, days_back: int = 7):
        """Clear events older than specified days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_back)
            self.events = [event for event in self.events if event.timestamp >= cutoff_time]
            
            self.logger.info(f"Cleared events older than {days_back} days. {len(self.events)} events remaining.")
            
        except Exception as e:
            self.logger.error(f"Error clearing old events: {str(e)}")

# Global monitor instance
acwr_feature_flag_monitor = ACWRFeatureFlagMonitor()

def log_acwr_feature_access(feature_name: str, user_id: int, granted: bool, details: Dict = None):
    """Convenience function to log ACWR feature access"""
    acwr_feature_flag_monitor.log_feature_access(feature_name, user_id, granted, details)

def log_acwr_feature_toggle(feature_name: str, admin_user_id: int, enabled: bool, details: Dict = None):
    """Convenience function to log ACWR feature toggle"""
    acwr_feature_flag_monitor.log_feature_toggle(feature_name, admin_user_id, enabled, details)

def log_acwr_feature_error(feature_name: str, user_id: Optional[int], error_message: str, details: Dict = None):
    """Convenience function to log ACWR feature errors"""
    acwr_feature_flag_monitor.log_error(feature_name, user_id, error_message, details)

