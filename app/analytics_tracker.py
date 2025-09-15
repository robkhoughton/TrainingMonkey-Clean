"""
Analytics Tracker Module

This module provides comprehensive analytics tracking for integration points,
user interactions, and conversion funnel analysis.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from db_utils import get_db_connection, execute_query

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Analytics event types"""
    INTEGRATION_POINT_CLICK = 'integration_point_click'
    GETTING_STARTED_ACCESS = 'getting_started_access'
    TUTORIAL_START = 'tutorial_start'
    TUTORIAL_COMPLETE = 'tutorial_complete'
    TUTORIAL_SKIP = 'tutorial_skip'
    DEMO_INTERACTION = 'demo_interaction'
    CTA_CLICK = 'cta_click'
    PAGE_VIEW = 'page_view'
    SCROLL_DEPTH = 'scroll_depth'
    SESSION_START = 'session_start'
    SESSION_END = 'session_end'
    USER_JOURNEY_STEP = 'user_journey_step'
    TUTORIAL_TRIGGER_SHOWN = 'tutorial_trigger_shown'
    TUTORIAL_TRIGGER_CLICKED = 'tutorial_trigger_clicked'


class IntegrationPoint(Enum):
    """Integration point identifiers"""
    LANDING_CTA = 'landing_cta'
    LANDING_SEE_HOW_IT_WORKS = 'landing_see_how_it_works'
    ONBOARDING_HELP_LINK = 'onboarding_help_link'
    DASHBOARD_HELP_BUTTON = 'dashboard_help_button'
    SETTINGS_GUIDE_BUTTON = 'settings_guide_button'
    GOALS_GUIDE_BUTTON = 'goals_guide_button'
    REPLAY_TUTORIAL_BUTTON = 'replay_tutorial_button'
    CONTEXTUAL_TUTORIAL_TRIGGER = 'contextual_tutorial_trigger'


@dataclass
class AnalyticsEvent:
    """Analytics event data structure"""
    event_id: str
    user_id: Optional[int]
    session_id: str
    event_type: EventType
    integration_point: Optional[IntegrationPoint]
    source_page: str
    target_page: Optional[str]
    event_data: Dict[str, Any]
    timestamp: datetime
    user_agent: Optional[str]
    ip_address: Optional[str]
    referrer: Optional[str]


@dataclass
class ClickThroughRate:
    """Click-through rate metrics"""
    integration_point: str
    total_impressions: int
    total_clicks: int
    click_through_rate: float
    unique_users: int
    conversion_rate: float
    time_period: str
    date_range: Dict[str, str]


class AnalyticsTracker:
    """Comprehensive analytics tracking system"""
    
    def __init__(self):
        self.session_events = {}
        self.user_sessions = {}
    
    def track_event(self, event: AnalyticsEvent) -> bool:
        """
        Track an analytics event
        
        Args:
            event: AnalyticsEvent object
            
        Returns:
            True if successfully tracked, False otherwise
        """
        try:
            # Store in database
            self._store_event(event)
            
            # Update session tracking
            self._update_session_tracking(event)
            
            # Log for monitoring
            logger.info(f"Analytics event tracked: {event.event_type.value} - {event.integration_point.value if event.integration_point else 'N/A'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking analytics event: {str(e)}")
            return False
    
    def get_click_through_rates(self, time_period: str = '7d', 
                               integration_points: Optional[List[str]] = None) -> List[ClickThroughRate]:
        """
        Get click-through rate metrics for integration points
        
        Args:
            time_period: Time period for analysis ('1d', '7d', '30d', '90d')
            integration_points: Specific integration points to analyze (None for all)
            
        Returns:
            List of ClickThroughRate objects
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            if time_period == '1d':
                start_date = end_date - timedelta(days=1)
            elif time_period == '7d':
                start_date = end_date - timedelta(days=7)
            elif time_period == '30d':
                start_date = end_date - timedelta(days=30)
            elif time_period == '90d':
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Build query
            query = """
                SELECT 
                    integration_point,
                    COUNT(*) as total_events,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(CASE WHEN event_type = 'integration_point_click' THEN 1 END) as total_clicks,
                    COUNT(CASE WHEN event_type = 'page_view' THEN 1 END) as total_impressions
                FROM analytics_events 
                WHERE timestamp >= %s AND timestamp <= %s
                AND event_type IN ('integration_point_click', 'page_view', 'getting_started_access')
            """
            
            params = [start_date, end_date]
            
            if integration_points:
                placeholders = ','.join(['%s'] * len(integration_points))
                query += f" AND integration_point IN ({placeholders})"
                params.extend(integration_points)
            
            query += " GROUP BY integration_point ORDER BY total_clicks DESC"
            
            # Execute query
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                results = cursor.fetchall()
            
            # Process results
            ctr_metrics = []
            for row in results:
                integration_point, total_events, unique_users, total_clicks, total_impressions = row
                
                # Calculate CTR
                ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                
                # Calculate conversion rate (clicks that led to getting started access)
                conversion_query = """
                    SELECT COUNT(DISTINCT user_id) as conversions
                    FROM analytics_events 
                    WHERE integration_point = %s 
                    AND event_type = 'getting_started_access'
                    AND timestamp >= %s AND timestamp <= %s
                """
                
                cursor.execute(conversion_query, [integration_point, start_date, end_date])
                conversion_result = cursor.fetchone()
                conversions = conversion_result[0] if conversion_result else 0
                conversion_rate = (conversions / unique_users * 100) if unique_users > 0 else 0
                
                ctr_metrics.append(ClickThroughRate(
                    integration_point=integration_point,
                    total_impressions=total_impressions,
                    total_clicks=total_clicks,
                    click_through_rate=round(ctr, 2),
                    unique_users=unique_users,
                    conversion_rate=round(conversion_rate, 2),
                    time_period=time_period,
                    date_range={
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d')
                    }
                ))
            
            return ctr_metrics
            
        except Exception as e:
            logger.error(f"Error getting click-through rates: {str(e)}")
            return []
    
    def get_user_journey_funnel(self, time_period: str = '7d', funnel_type: str = 'onboarding') -> Dict[str, Any]:
        """
        Get user journey conversion funnel analysis
        
        Args:
            time_period: Time period for analysis
            funnel_type: Type of funnel ('onboarding', 'tutorial', 'engagement')
            
        Returns:
            Dictionary with funnel metrics
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            if time_period == '1d':
                start_date = end_date - timedelta(days=1)
            elif time_period == '7d':
                start_date = end_date - timedelta(days=7)
            elif time_period == '30d':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Define funnel steps based on type
            if funnel_type == 'onboarding':
                funnel_steps = [
                    ('page_view', 'Page Views'),
                    ('integration_point_click', 'Integration Clicks'),
                    ('getting_started_access', 'Getting Started Access'),
                    ('tutorial_start', 'Tutorial Starts'),
                    ('tutorial_complete', 'Tutorial Completions')
                ]
            elif funnel_type == 'tutorial':
                funnel_steps = [
                    ('tutorial_start', 'Tutorial Starts'),
                    ('tutorial_complete', 'Tutorial Completions'),
                    ('getting_started_engagement', 'Page Engagement'),
                    ('demo_interaction', 'Demo Interactions')
                ]
            elif funnel_type == 'engagement':
                funnel_steps = [
                    ('page_view', 'Page Views'),
                    ('getting_started_engagement', 'Page Engagement'),
                    ('demo_interaction', 'Demo Interactions'),
                    ('tutorial_click', 'Tutorial Clicks'),
                    ('faq_expansion', 'FAQ Interactions')
                ]
            else:
                funnel_steps = [
                    ('page_view', 'Page Views'),
                    ('integration_point_click', 'Integration Clicks'),
                    ('getting_started_access', 'Getting Started Access'),
                    ('tutorial_start', 'Tutorial Starts'),
                    ('tutorial_complete', 'Tutorial Completions')
                ]
            
            # Get funnel data with more detailed analysis
            funnel_query = """
                SELECT 
                    event_type,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(*) as total_events,
                    COUNT(DISTINCT session_id) as unique_sessions,
                    AVG(EXTRACT(EPOCH FROM (timestamp - LAG(timestamp) OVER (PARTITION BY user_id ORDER BY timestamp)))) as avg_time_between_events
                FROM analytics_events 
                WHERE timestamp >= %s AND timestamp <= %s
                AND event_type IN ({})
                GROUP BY event_type
                ORDER BY 
                    CASE event_type
                        {}
                    END
            """.format(
                ','.join(['%s'] * len(funnel_steps)),
                ' '.join([f"WHEN '{step[0]}' THEN {i+1}" for i, step in enumerate(funnel_steps)])
            )
            
            event_types = [step[0] for step in funnel_steps]
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(funnel_query, [start_date, end_date] + event_types)
                results = cursor.fetchall()
            
            # Process funnel data
            funnel_data = {
                'funnel_type': funnel_type,
                'time_period': time_period,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'steps': [],
                'overall_metrics': {
                    'total_users': 0,
                    'total_events': 0,
                    'total_sessions': 0,
                    'overall_conversion_rate': 0
                }
            }
            
            previous_count = None
            total_users = 0
            total_events = 0
            total_sessions = 0
            
            for event_type, unique_users, total_events_count, unique_sessions, avg_time_between in results:
                step_name = next((step[1] for step in funnel_steps if step[0] == event_type), event_type.replace('_', ' ').title())
                
                step = {
                    'step_name': step_name,
                    'event_type': event_type,
                    'unique_users': unique_users,
                    'total_events': total_events_count,
                    'unique_sessions': unique_sessions,
                    'conversion_rate': None,
                    'drop_off_rate': None,
                    'avg_time_between_events': round(avg_time_between, 2) if avg_time_between else None
                }
                
                if previous_count is not None:
                    step['conversion_rate'] = round((unique_users / previous_count * 100), 2)
                    step['drop_off_rate'] = round(((previous_count - unique_users) / previous_count * 100), 2)
                
                funnel_data['steps'].append(step)
                previous_count = unique_users
                total_users = max(total_users, unique_users)
                total_events += total_events_count
                total_sessions = max(total_sessions, unique_sessions)
            
            # Calculate overall metrics
            if funnel_data['steps']:
                first_step = funnel_data['steps'][0]
                last_step = funnel_data['steps'][-1]
                funnel_data['overall_metrics'] = {
                    'total_users': total_users,
                    'total_events': total_events,
                    'total_sessions': total_sessions,
                    'overall_conversion_rate': round((last_step['unique_users'] / first_step['unique_users'] * 100), 2) if first_step['unique_users'] > 0 else 0
                }
            
            return funnel_data
            
        except Exception as e:
            logger.error(f"Error getting user journey funnel: {str(e)}")
            return {}
    
    def get_detailed_funnel_analysis(self, time_period: str = '7d') -> Dict[str, Any]:
        """
        Get detailed funnel analysis with cohort tracking and drop-off analysis
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dictionary with detailed funnel metrics
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            if time_period == '7d':
                start_date = end_date - timedelta(days=7)
            elif time_period == '30d':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Get detailed funnel analysis
            detailed_query = """
                WITH user_journeys AS (
                    SELECT 
                        user_id,
                        session_id,
                        event_type,
                        timestamp,
                        source_page,
                        integration_point,
                        ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY timestamp) as step_number
                    FROM analytics_events 
                    WHERE timestamp >= %s AND timestamp <= %s
                    AND event_type IN ('page_view', 'integration_point_click', 'getting_started_access', 'tutorial_start', 'tutorial_complete')
                ),
                funnel_analysis AS (
                    SELECT 
                        event_type,
                        COUNT(DISTINCT user_id) as unique_users,
                        COUNT(DISTINCT session_id) as unique_sessions,
                        COUNT(*) as total_events,
                        AVG(step_number) as avg_step_position,
                        MIN(timestamp) as first_occurrence,
                        MAX(timestamp) as last_occurrence
                    FROM user_journeys
                    GROUP BY event_type
                )
                SELECT * FROM funnel_analysis
                ORDER BY 
                    CASE event_type
                        WHEN 'page_view' THEN 1
                        WHEN 'integration_point_click' THEN 2
                        WHEN 'getting_started_access' THEN 3
                        WHEN 'tutorial_start' THEN 4
                        WHEN 'tutorial_complete' THEN 5
                    END
            """
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(detailed_query, [start_date, end_date])
                results = cursor.fetchall()
            
            # Process detailed funnel data
            detailed_funnel = {
                'time_period': time_period,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'funnel_steps': [],
                'cohort_analysis': {},
                'drop_off_analysis': {}
            }
            
            previous_users = None
            for result in results:
                event_type, unique_users, unique_sessions, total_events, avg_step_position, first_occurrence, last_occurrence = result
                
                step = {
                    'event_type': event_type,
                    'step_name': event_type.replace('_', ' ').title(),
                    'unique_users': unique_users,
                    'unique_sessions': unique_sessions,
                    'total_events': total_events,
                    'avg_step_position': round(avg_step_position, 2),
                    'first_occurrence': first_occurrence.isoformat() if first_occurrence else None,
                    'last_occurrence': last_occurrence.isoformat() if last_occurrence else None,
                    'conversion_rate': None,
                    'drop_off_count': None,
                    'drop_off_rate': None
                }
                
                if previous_users is not None:
                    step['conversion_rate'] = round((unique_users / previous_users * 100), 2)
                    step['drop_off_count'] = previous_users - unique_users
                    step['drop_off_rate'] = round(((previous_users - unique_users) / previous_users * 100), 2)
                
                detailed_funnel['funnel_steps'].append(step)
                previous_users = unique_users
            
            return detailed_funnel
            
        except Exception as e:
            logger.error(f"Error getting detailed funnel analysis: {str(e)}")
            return {}
    
    def get_tutorial_analytics(self, time_period: str = '7d') -> Dict[str, Any]:
        """
        Get tutorial analytics and completion rates
        
        Args:
            time_period: Time period for analysis
            
        Returns:
            Dictionary with tutorial metrics
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            if time_period == '7d':
                start_date = end_date - timedelta(days=7)
            elif time_period == '30d':
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=7)
            
            # Get tutorial metrics
            tutorial_query = """
                SELECT 
                    JSON_EXTRACT(event_data, '$.tutorial_id') as tutorial_id,
                    COUNT(CASE WHEN event_type = 'tutorial_start' THEN 1 END) as starts,
                    COUNT(CASE WHEN event_type = 'tutorial_complete' THEN 1 END) as completions,
                    COUNT(CASE WHEN event_type = 'tutorial_skip' THEN 1 END) as skips,
                    COUNT(DISTINCT user_id) as unique_users
                FROM analytics_events 
                WHERE timestamp >= %s AND timestamp <= %s
                AND event_type IN ('tutorial_start', 'tutorial_complete', 'tutorial_skip')
                GROUP BY tutorial_id
                ORDER BY starts DESC
            """
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(tutorial_query, [start_date, end_date])
                results = cursor.fetchall()
            
            # Process tutorial data
            tutorial_analytics = {
                'time_period': time_period,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'tutorials': []
            }
            
            for tutorial_id, starts, completions, skips, unique_users in results:
                if tutorial_id:  # Skip null tutorial_ids
                    completion_rate = (completions / starts * 100) if starts > 0 else 0
                    skip_rate = (skips / starts * 100) if starts > 0 else 0
                    
                    tutorial_analytics['tutorials'].append({
                        'tutorial_id': tutorial_id.strip('"'),  # Remove quotes from JSON
                        'starts': starts,
                        'completions': completions,
                        'skips': skips,
                        'unique_users': unique_users,
                        'completion_rate': round(completion_rate, 2),
                        'skip_rate': round(skip_rate, 2)
                    })
            
            return tutorial_analytics
            
        except Exception as e:
            logger.error(f"Error getting tutorial analytics: {str(e)}")
            return {}
    
    def _store_event(self, event: AnalyticsEvent) -> None:
        """Store analytics event in database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert event
                cursor.execute("""
                    INSERT INTO analytics_events (
                        event_id, user_id, session_id, event_type, integration_point,
                        source_page, target_page, event_data, timestamp, user_agent, ip_address, referrer
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    event.event_id,
                    event.user_id,
                    event.session_id,
                    event.event_type.value,
                    event.integration_point.value if event.integration_point else None,
                    event.source_page,
                    event.target_page,
                    json.dumps(event.event_data),
                    event.timestamp,
                    event.user_agent,
                    event.ip_address,
                    event.referrer
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing analytics event: {str(e)}")
            raise
    
    def _update_session_tracking(self, event: AnalyticsEvent) -> None:
        """Update session tracking for user journey analysis"""
        try:
            session_key = f"{event.user_id}_{event.session_id}"
            
            if session_key not in self.user_sessions:
                self.user_sessions[session_key] = {
                    'user_id': event.user_id,
                    'session_id': event.session_id,
                    'start_time': event.timestamp,
                    'events': [],
                    'integration_points_clicked': set(),
                    'pages_visited': set()
                }
            
            session = self.user_sessions[session_key]
            session['events'].append(event)
            session['last_activity'] = event.timestamp
            
            if event.integration_point:
                session['integration_points_clicked'].add(event.integration_point.value)
            
            session['pages_visited'].add(event.source_page)
            
        except Exception as e:
            logger.error(f"Error updating session tracking: {str(e)}")
    
    def create_analytics_tables(self) -> None:
        """Create analytics tables if they don't exist"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Create analytics_events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS analytics_events (
                        id SERIAL PRIMARY KEY,
                        event_id VARCHAR(255) UNIQUE NOT NULL,
                        user_id INTEGER,
                        session_id VARCHAR(255) NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        integration_point VARCHAR(100),
                        source_page VARCHAR(255) NOT NULL,
                        target_page VARCHAR(255),
                        event_data JSONB,
                        timestamp TIMESTAMP DEFAULT NOW(),
                        user_agent TEXT,
                        ip_address INET,
                        referrer TEXT,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Create tutorial_sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tutorial_sessions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        tutorial_id VARCHAR(100) NOT NULL,
                        started_at TIMESTAMP DEFAULT NOW(),
                        start_data JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Create tutorial_completions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tutorial_completions (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        tutorial_id VARCHAR(100) NOT NULL,
                        completed_at TIMESTAMP DEFAULT NOW(),
                        completion_data JSONB,
                        created_at TIMESTAMP DEFAULT NOW(),
                        UNIQUE(user_id, tutorial_id)
                    )
                """)
                
                # Create tutorial_skips table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tutorial_skips (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        tutorial_id VARCHAR(100) NOT NULL,
                        skipped_at TIMESTAMP DEFAULT NOW(),
                        skip_data JSONB,
                        created_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp 
                    ON analytics_events (timestamp)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id 
                    ON analytics_events (user_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type 
                    ON analytics_events (event_type)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_analytics_events_integration_point 
                    ON analytics_events (integration_point)
                """)
                
                # Create indexes for tutorial tables
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_sessions_user_id 
                    ON tutorial_sessions (user_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_sessions_tutorial_id 
                    ON tutorial_sessions (tutorial_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_sessions_started_at 
                    ON tutorial_sessions (started_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_completions_user_id 
                    ON tutorial_completions (user_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_completions_tutorial_id 
                    ON tutorial_completions (tutorial_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_completions_completed_at 
                    ON tutorial_completions (completed_at)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_skips_user_id 
                    ON tutorial_skips (user_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_skips_tutorial_id 
                    ON tutorial_skips (tutorial_id)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_tutorial_skips_skipped_at 
                    ON tutorial_skips (skipped_at)
                """)
                
                conn.commit()
                logger.info("Analytics tables created successfully")
                
        except Exception as e:
            logger.error(f"Error creating analytics tables: {str(e)}")
            raise


# Global analytics tracker instance
analytics_tracker = AnalyticsTracker()


def track_analytics_event(event_type: EventType, event_data: Dict[str, Any], 
                         user_id: Optional[int] = None, session_id: Optional[str] = None,
                         integration_point: Optional[IntegrationPoint] = None,
                         source_page: str = 'unknown', target_page: Optional[str] = None,
                         request=None) -> bool:
    """
    Convenience function to track analytics events
    
    Args:
        event_type: Type of event to track
        event_data: Additional event data
        user_id: User ID (if authenticated)
        session_id: Session ID
        integration_point: Integration point identifier
        source_page: Source page name
        target_page: Target page name
        request: Flask request object (for extracting metadata)
        
    Returns:
        True if successfully tracked, False otherwise
    """
    try:
        # Generate event ID
        event_id = f"{event_type.value}_{datetime.now().timestamp()}_{user_id or 'anonymous'}"
        
        # Extract metadata from request if provided
        user_agent = request.headers.get('User-Agent') if request else None
        ip_address = request.remote_addr if request else None
        referrer = request.headers.get('Referer') if request else None
        
        # Create analytics event
        event = AnalyticsEvent(
            event_id=event_id,
            user_id=user_id,
            session_id=session_id or 'unknown',
            event_type=event_type,
            integration_point=integration_point,
            source_page=source_page,
            target_page=target_page,
            event_data=event_data,
            timestamp=datetime.now(),
            user_agent=user_agent,
            ip_address=ip_address,
            referrer=referrer
        )
        
        # Track the event
        return analytics_tracker.track_event(event)
        
    except Exception as e:
        logger.error(f"Error tracking analytics event: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Analytics Tracker Module")
    print("=" * 50)
    print("Module loaded successfully!")
    print(f"Event types: {[event_type.value for event_type in EventType]}")
    print(f"Integration points: {[point.value for point in IntegrationPoint]}")
    print("=" * 50)
