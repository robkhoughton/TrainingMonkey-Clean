"""
Mock database utilities for local UI development.

This module provides fake data for UI testing without requiring a real database.
Enable by setting USE_MOCK_DB=true in environment or .env file.

Usage:
    # In .env or environment:
    USE_MOCK_DB=true

    # Then run the app normally - it will use mock data
"""

import os
import json
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
import random

logger = logging.getLogger(__name__)

# ============================================================================
# MOCK DATA STORE - In-memory storage for stateful operations
# ============================================================================

class MockDataStore:
    """In-memory data store that simulates database tables."""

    def __init__(self):
        self._initialized = False
        self.reset()

    def reset(self):
        """Reset all data to initial mock state."""
        self._initialized = True

        # Default mock user
        self.mock_user_id = 1
        self.mock_email = "demo@trainingmonkey.com"
        self.mock_password = "demo123"  # Password for mock user

        # Generate dates for the last 90 days
        today = datetime.now().date()

        # Generate a real werkzeug password hash for "demo123"
        from werkzeug.security import generate_password_hash
        mock_password_hash = generate_password_hash(self.mock_password)

        # User settings
        self.user_settings = {
            1: {
                'id': 1,
                'email': self.mock_email,
                'password_hash': mock_password_hash,
                'age': 35,
                'resting_hr': 52,
                'max_hr': 185,
                'gender': 'M',
                'last_sync_date': today.isoformat(),
                'is_admin': False,
                'strava_athlete_id': 12345678,
                'strava_access_token': 'mock_token',
                'strava_refresh_token': 'mock_refresh',
                'strava_token_expires_at': int((datetime.now() + timedelta(hours=6)).timestamp()),
                'terms_accepted_at': datetime.now().isoformat(),
                'privacy_policy_accepted_at': datetime.now().isoformat(),
                'onboarding_completed_at': datetime.now().isoformat(),
                'account_status': 'active',
                'training_schedule_json': json.dumps({
                    'monday': 'easy',
                    'tuesday': 'workout',
                    'wednesday': 'easy',
                    'thursday': 'workout',
                    'friday': 'rest',
                    'saturday': 'long',
                    'sunday': 'easy'
                }),
                'coaching_style_spectrum': 50,
                'coaching_tone': 'supportive',
                'timezone': 'America/Denver'
            }
        }

        # Generate realistic activities
        self.activities = self._generate_mock_activities(today, 90)

        # LLM Recommendations
        self.llm_recommendations = {
            1: {
                'id': 1,
                'user_id': 1,
                'generation_date': today.isoformat(),
                'target_date': today.isoformat(),
                'valid_until': (today + timedelta(days=1)).isoformat(),
                'daily_recommendation': self._get_mock_daily_recommendation(),
                'weekly_recommendation': self._get_mock_weekly_recommendation(),
                'pattern_insights': 'Your training consistency has been excellent. Consider adding a recovery week soon.',
                'created_at': datetime.now().isoformat(),
                'is_autopsy_informed': True,
                'metrics_snapshot': json.dumps({
                    'acute_load': 45.2,
                    'chronic_load': 38.7,
                    'acwr': 1.17,
                    'trimp_acwr': 1.12
                })
            }
        }

        # Journal entries
        self.journal_entries = self._generate_mock_journal_entries(today, 14)

        # AI Autopsies
        self.ai_autopsies = self._generate_mock_autopsies(today, 7)

        # Race goals
        self.race_goals = [
            {
                'id': 1,
                'user_id': 1,
                'race_name': 'Spring Half Marathon',
                'race_date': (today + timedelta(days=60)).isoformat(),
                'race_type': 'half_marathon',
                'priority': 'A',
                'target_time': '1:45:00',
                'notes': 'Goal race for the season',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 2,
                'user_id': 1,
                'race_name': 'Local 10K',
                'race_date': (today + timedelta(days=30)).isoformat(),
                'race_type': '10k',
                'priority': 'B',
                'target_time': '42:00',
                'notes': 'Tune-up race',
                'created_at': datetime.now().isoformat()
            }
        ]

        # Weekly programs
        self.weekly_programs = self._generate_mock_weekly_program(today)

        logger.info("MockDataStore initialized with sample data")

    def _generate_mock_activities(self, today, days: int) -> List[Dict]:
        """Generate realistic training activities."""
        activities = []
        activity_id = 1

        # Activity patterns by day of week (0=Monday)
        day_patterns = {
            0: ('easy', 5.0, 400),      # Monday: Easy
            1: ('workout', 6.0, 500),   # Tuesday: Workout
            2: ('easy', 5.5, 350),      # Wednesday: Easy
            3: ('workout', 7.0, 600),   # Thursday: Workout
            4: ('rest', 0, 0),          # Friday: Rest
            5: ('long', 12.0, 800),     # Saturday: Long
            6: ('easy', 4.0, 200),      # Sunday: Recovery
        }

        for i in range(days, 0, -1):
            date = today - timedelta(days=i)
            dow = date.weekday()
            pattern, base_dist, base_elev = day_patterns[dow]

            # Skip ~20% of days randomly for realism
            if pattern == 'rest' or random.random() < 0.15:
                continue

            # Add some variation
            distance = base_dist * random.uniform(0.85, 1.15)
            elevation = base_elev * random.uniform(0.8, 1.2)

            # Calculate metrics
            avg_hr = random.randint(135, 165)
            max_hr = avg_hr + random.randint(15, 35)
            duration = distance * random.uniform(8.5, 10.5)  # pace in min/mile
            trimp = duration * (avg_hr - 52) / (185 - 52) * random.uniform(0.8, 1.2)

            activity = {
                'activity_id': activity_id,
                'user_id': 1,
                'date': date.isoformat(),
                'name': self._get_activity_name(pattern),
                'type': 'Run',
                'sport_type': 'running',
                'distance_miles': round(distance, 2),
                'elevation_gain_feet': round(elevation, 0),
                'elevation_load_miles': round(elevation / 100 * 0.1, 2),
                'total_load_miles': round(distance + elevation / 100 * 0.1, 2),
                'avg_heart_rate': avg_hr,
                'max_heart_rate': max_hr,
                'duration_minutes': round(duration, 1),
                'trimp': round(trimp, 1),
                'time_in_zone1': round(duration * 0.1, 1),
                'time_in_zone2': round(duration * 0.4, 1),
                'time_in_zone3': round(duration * 0.3, 1),
                'time_in_zone4': round(duration * 0.15, 1),
                'time_in_zone5': round(duration * 0.05, 1),
                'seven_day_avg_load': round(random.uniform(5, 8), 2),
                'twentyeight_day_avg_load': round(random.uniform(5.5, 7), 2),
                'seven_day_avg_trimp': round(random.uniform(45, 75), 1),
                'twentyeight_day_avg_trimp': round(random.uniform(50, 65), 1),
                'acute_chronic_ratio': round(random.uniform(0.85, 1.3), 3),
                'trimp_acute_chronic_ratio': round(random.uniform(0.9, 1.25), 3),
                'normalized_divergence': round(random.uniform(-0.15, 0.15), 3),
                'perceived_effort': random.randint(5, 8),
                'feeling_score': random.randint(3, 5),
                'trimp_calculation_method': 'stream',
                'hr_stream_sample_count': random.randint(200, 500)
            }

            activities.append(activity)
            activity_id += 1

        return activities

    def _get_activity_name(self, pattern: str) -> str:
        """Get a realistic activity name based on pattern."""
        names = {
            'easy': ['Easy Run', 'Recovery Run', 'Shake-out Run', 'Morning Jog'],
            'workout': ['Tempo Run', 'Interval Session', 'Fartlek', 'Speed Work', 'Track Workout'],
            'long': ['Long Run', 'Weekend Long Run', 'Endurance Run'],
        }
        return random.choice(names.get(pattern, ['Run']))

    def _get_mock_daily_recommendation(self) -> str:
        return """**Today's Recommendation: Easy Recovery Run**

Based on your recent training load and yesterday's workout, today is ideal for active recovery.

**Suggested workout:**
- 4-5 miles at easy pace (Zone 2)
- Keep heart rate below 145 bpm
- Focus on relaxed form

**Why:** Your ACWR is at 1.17, slightly elevated. An easy day helps maintain fitness while allowing adaptation."""

    def _get_mock_weekly_recommendation(self) -> str:
        return """**Weekly Overview**

You're in good shape heading into this week. Your chronic training load is well-established, and you have capacity for quality work.

**Key Sessions:**
1. Tuesday: Tempo intervals (3x10 min at threshold)
2. Thursday: Hill repeats (6x90 sec)
3. Saturday: Long run with race pace finish

**Recovery Focus:**
- Prioritize sleep this week
- Consider foam rolling after hard sessions"""

    def _generate_mock_journal_entries(self, today, days: int) -> List[Dict]:
        """Generate mock journal entries."""
        entries = []
        for i in range(days):
            date = today - timedelta(days=i)
            entries.append({
                'date': date.isoformat(),
                'user_id': 1,
                'energy_level': random.randint(2, 5),
                'rpe_score': random.randint(4, 8),
                'pain_percentage': random.randint(0, 30),
                'notes': random.choice([
                    'Felt good today',
                    'Legs were heavy',
                    'Great energy in the morning',
                    'Tired but pushed through',
                    ''
                ]),
                'updated_at': datetime.now().isoformat()
            })
        return entries

    def _generate_mock_autopsies(self, today, days: int) -> List[Dict]:
        """Generate mock AI autopsies."""
        autopsies = []
        for i in range(1, days + 1):
            date = today - timedelta(days=i)
            autopsies.append({
                'user_id': 1,
                'date': date.isoformat(),
                'prescribed_action': random.choice(['Easy run', 'Tempo workout', 'Rest day', 'Long run']),
                'actual_activities': random.choice(['Completed as planned', 'Modified slightly', 'Skipped']),
                'autopsy_analysis': 'Good alignment between planned and executed training.',
                'alignment_score': round(random.uniform(0.7, 1.0), 2),
                'generated_at': datetime.now().isoformat()
            })
        return autopsies

    def _generate_mock_weekly_program(self, today) -> List[Dict]:
        """Generate mock weekly program."""
        week_start = today - timedelta(days=today.weekday())
        return [{
            'id': 1,
            'user_id': 1,
            'week_start_date': week_start.isoformat(),
            'program_json': json.dumps({
                'monday': {'type': 'easy', 'distance': 5, 'notes': 'Recovery pace'},
                'tuesday': {'type': 'workout', 'distance': 6, 'notes': '3x10min tempo'},
                'wednesday': {'type': 'easy', 'distance': 5, 'notes': 'Easy effort'},
                'thursday': {'type': 'workout', 'distance': 7, 'notes': 'Hill repeats'},
                'friday': {'type': 'rest', 'distance': 0, 'notes': 'Complete rest'},
                'saturday': {'type': 'long', 'distance': 14, 'notes': 'Long run with progression'},
                'sunday': {'type': 'easy', 'distance': 4, 'notes': 'Recovery'}
            }),
            'predicted_acwr': 1.15,
            'predicted_divergence': 0.05,
            'generated_at': datetime.now().isoformat(),
            'generation_type': 'scheduled'
        }]


# Global mock data store instance
_mock_store = MockDataStore()


# ============================================================================
# MOCK DATABASE CONNECTION
# ============================================================================

class MockCursor:
    """Mock cursor that simulates psycopg2 cursor behavior."""

    def __init__(self):
        self.description = None
        self._results = []
        self._index = 0

    def execute(self, query: str, params: tuple = ()):
        """Parse query and return mock results."""
        self._results = _parse_and_execute_mock_query(query, params)
        self._index = 0

    def fetchone(self):
        if self._index < len(self._results):
            result = self._results[self._index]
            self._index += 1
            return MockRow(result) if isinstance(result, dict) else result
        return None

    def fetchall(self):
        results = self._results[self._index:]
        self._index = len(self._results)
        return [MockRow(r) if isinstance(r, dict) else r for r in results]

    def close(self):
        pass


class MockRow(dict):
    """Mock row that behaves like psycopg2 RealDictRow."""

    def __init__(self, data: dict):
        super().__init__(data)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'MockRow' has no attribute '{name}'")


class MockConnection:
    """Mock connection that simulates psycopg2 connection."""

    def __init__(self):
        self.closed = False

    def cursor(self):
        return MockCursor()

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        self.closed = True


# ============================================================================
# QUERY PARSER - Interprets SQL and returns appropriate mock data
# ============================================================================

def _parse_and_execute_mock_query(query: str, params: tuple) -> List[Dict]:
    """Parse SQL query and return mock data."""
    query_lower = query.lower().strip()

    # Debug logging
    print(f"[MOCK DB] Query: {query_lower[:100]}...")
    print(f"[MOCK DB] Params: {params}")

    # Extract user_id from params if present (usually first param for user-scoped queries)
    user_id = params[0] if params and isinstance(params[0], int) else 1

    # SELECT queries
    if query_lower.startswith('select'):
        result = _handle_select(query_lower, params)
        print(f"[MOCK DB] Result count: {len(result)}")
        return result

    # INSERT queries - return empty but don't fail
    if query_lower.startswith('insert'):
        logger.debug(f"Mock INSERT: {query[:50]}...")
        return []

    # UPDATE queries
    if query_lower.startswith('update'):
        logger.debug(f"Mock UPDATE: {query[:50]}...")
        return []

    # DELETE queries
    if query_lower.startswith('delete'):
        logger.debug(f"Mock DELETE: {query[:50]}...")
        return []

    # Default empty result
    return []


def _handle_select(query: str, params: tuple) -> List[Dict]:
    """Handle SELECT queries and return appropriate mock data."""

    # Count queries
    if 'count(*)' in query or 'count(1)' in query:
        if 'activities' in query:
            return [{'count': len(_mock_store.activities)}]
        if 'user_settings' in query:
            return [{'count': 1}]
        return [{'count': 0}]

    # User settings queries
    if 'user_settings' in query:
        # Check WHERE clause to determine lookup type
        if 'where email' in query and params:
            # Looking up by email
            email = params[0] if isinstance(params[0], str) else _mock_store.mock_email
            logger.info(f"Mock DB: Looking up user by email: '{email}' (mock email: '{_mock_store.mock_email}')")
            # Case-insensitive email comparison
            if email.lower() == _mock_store.mock_email.lower():
                logger.info(f"Mock DB: Found mock user!")
                return [_mock_store.user_settings[1]]
            logger.warning(f"Mock DB: Email not found in mock data")
            return []
        if 'where id' in query and params:
            # Looking up by ID
            user_id = params[0]
            logger.info(f"Mock DB: Looking up user by ID: {user_id}")
            if user_id in _mock_store.user_settings:
                return [_mock_store.user_settings[user_id]]
            return []
        # No WHERE clause - return all users
        return list(_mock_store.user_settings.values())

    # Activities queries
    if 'activities' in query:
        activities = _mock_store.activities.copy()

        # Filter by date range if present
        if 'date >=' in query or 'date >' in query:
            # Simple date filtering - get recent activities
            if len(params) >= 2:
                try:
                    # Assume date params are strings
                    activities = [a for a in activities if a['date'] >= str(params[-1])]
                except:
                    pass

        # Order by date descending (most common)
        if 'order by' in query and 'desc' in query:
            activities.sort(key=lambda x: x['date'], reverse=True)

        # Limit
        if 'limit' in query:
            try:
                limit_idx = query.index('limit')
                limit_val = int(query[limit_idx:].split()[1])
                activities = activities[:limit_val]
            except:
                pass

        return activities

    # LLM Recommendations
    if 'llm_recommendations' in query:
        user_id = params[0] if params else 1
        if user_id in _mock_store.llm_recommendations:
            return [_mock_store.llm_recommendations[user_id]]
        return []

    # Journal entries
    if 'journal_entries' in query:
        entries = _mock_store.journal_entries.copy()
        if params and len(params) >= 2:
            # Filter by user_id and date if present
            entries = [e for e in entries if str(params[-1]) in e.get('date', '')]
        return entries

    # AI Autopsies
    if 'ai_autopsies' in query:
        return _mock_store.ai_autopsies

    # Race goals
    if 'race_goals' in query:
        return _mock_store.race_goals

    # Weekly programs
    if 'weekly_programs' in query:
        return _mock_store.weekly_programs

    # Race history
    if 'race_history' in query:
        return []  # Empty race history for mock

    # Default: empty result
    logger.debug(f"Mock SELECT unhandled: {query[:80]}...")
    return []


# ============================================================================
# PUBLIC API - Matches db_utils.py interface
# ============================================================================

# Legacy compatibility
DB_FILE = None
USE_POSTGRES = False  # We're mocking, not using real postgres
DATABASE_URL = "mock://localhost/trainingmonkey"


@contextmanager
def get_db_connection():
    """Context manager for mock database connections."""
    conn = MockConnection()
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = (), fetch: bool = False, use_pool: bool = False) -> Any:
    """Execute a mock database query."""
    results = _parse_and_execute_mock_query(query, params)

    if fetch:
        return [MockRow(r) if isinstance(r, dict) else r for r in results]
    return None


def execute_batch_queries(queries_with_params: List[Tuple[str, tuple]]) -> bool:
    """Execute multiple mock queries."""
    for query, params in queries_with_params:
        execute_query(query, params)
    return True


# LLM Recommendation functions
def save_llm_recommendation(recommendation: Dict) -> bool:
    """Mock save LLM recommendation."""
    user_id = recommendation.get('user_id', 1)
    _mock_store.llm_recommendations[user_id] = recommendation
    return True


def get_latest_recommendation(user_id: int) -> Optional[Dict]:
    """Get mock latest recommendation."""
    return _mock_store.llm_recommendations.get(user_id)


def recommendation_needs_update(user_id: int) -> bool:
    """Check if mock recommendation needs update."""
    return False  # Never needs update in mock mode


def cleanup_old_recommendations(user_id: int, keep_days: int = 14) -> int:
    """Mock cleanup old recommendations."""
    return 0


# Activity functions
def get_last_activity_date(user_id: int) -> Optional[str]:
    """Get mock last activity date."""
    activities = [a for a in _mock_store.activities if a['user_id'] == user_id]
    if activities:
        activities.sort(key=lambda x: x['date'], reverse=True)
        return activities[0]['date']
    return None


# Schema/validation functions (all return success in mock mode)
def initialize_db(force: bool = False) -> bool:
    """Mock initialize database."""
    logger.info("Mock DB: initialize_db called (no-op)")
    return True


def validate_database() -> Dict:
    """Mock validate database."""
    return {'valid': True, 'tables': ['activities', 'user_settings', 'llm_recommendations']}


def migrate_user_settings_schema() -> bool:
    """Mock migrate user settings schema."""
    return True


def migrate_legal_compliance_table() -> bool:
    """Mock migrate legal compliance table."""
    return True


# TRIMP/HR functions
def validate_trimp_schema() -> bool:
    """Mock validate TRIMP schema."""
    return True


def validate_hr_streams_table() -> bool:
    """Mock validate HR streams table."""
    return True


def get_trimp_schema_status() -> Dict:
    """Mock get TRIMP schema status."""
    return {
        'trimp_fields_exist': True,
        'hr_streams_table_exists': True,
        'activities_with_trimp': len(_mock_store.activities),
        'activities_with_hr_streams': len(_mock_store.activities)
    }


def save_hr_stream_data(activity_id: int, user_id: int, hr_data: List, sample_rate: int) -> bool:
    """Mock save HR stream data."""
    return True


def get_hr_stream_data(activity_id: int, user_id: int) -> Optional[Dict]:
    """Mock get HR stream data."""
    return {'hr_data': [140, 145, 150, 155, 160], 'sample_rate': 1}


def update_activity_trimp_metadata(activity_id: int, user_id: int,
                                    calculation_method: str, sample_count: int,
                                    trimp_value: float) -> bool:
    """Mock update activity TRIMP metadata."""
    return True


def get_activities_needing_trimp_recalculation(user_id: int, days_back: int = 90) -> List[Dict]:
    """Mock get activities needing TRIMP recalculation."""
    return []  # None need recalculation in mock mode


def delete_hr_stream_data(activity_id: int, user_id: int) -> bool:
    """Mock delete HR stream data."""
    return True


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def reset_mock_data():
    """Reset mock data to initial state. Useful for testing."""
    _mock_store.reset()


def get_mock_store() -> MockDataStore:
    """Get direct access to mock data store for testing/customization."""
    return _mock_store


# Export list matching db_utils.py
__all__ = [
    'get_db_connection',
    'execute_query',
    'execute_batch_queries',
    'save_llm_recommendation',
    'get_latest_recommendation',
    'recommendation_needs_update',
    'cleanup_old_recommendations',
    'get_last_activity_date',
    'initialize_db',
    'validate_database',
    'migrate_user_settings_schema',
    'migrate_legal_compliance_table',
    'validate_trimp_schema',
    'validate_hr_streams_table',
    'get_trimp_schema_status',
    'save_hr_stream_data',
    'get_hr_stream_data',
    'update_activity_trimp_metadata',
    'get_activities_needing_trimp_recalculation',
    'delete_hr_stream_data',
    'DB_FILE',
    'USE_POSTGRES',
    'DATABASE_URL',
    # Mock-specific
    'reset_mock_data',
    'get_mock_store',
]


logger.info("Mock database utilities loaded - USE_MOCK_DB mode active")
