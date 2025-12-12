#!/usr/bin/env python3
"""
Run Flask server with mock database for UI development.

This script starts the TrainingMonkey Flask app using fake/mock data
instead of connecting to Cloud SQL. Perfect for:
- UI development with Playwright
- Design iteration loops
- Frontend testing without database dependencies

Usage:
    python run_mock_server.py

The server will run on http://localhost:5001 with mock data.
"""

import os
import sys

# Set mock mode BEFORE any other imports
os.environ['USE_MOCK_DB'] = 'true'
os.environ['DATABASE_URL'] = 'mock://localhost/trainingmonkey'

# Patch db_utils to use mock version
# This must happen before strava_app imports db_utils
import importlib.util

def patch_db_utils():
    """Replace db_utils module with mock_db_utils."""
    # Load mock_db_utils
    mock_spec = importlib.util.spec_from_file_location(
        "mock_db_utils",
        os.path.join(os.path.dirname(__file__), "mock_db_utils.py")
    )
    mock_module = importlib.util.module_from_spec(mock_spec)
    mock_spec.loader.exec_module(mock_module)

    # Inject it as db_utils in sys.modules
    sys.modules['db_utils'] = mock_module

    print("=" * 60)
    print("MOCK DATABASE MODE ACTIVE")
    print("=" * 60)
    print("Using fake data for UI development")
    print("No Cloud SQL connection required")
    print("=" * 60)

    return mock_module

# Apply the patch and keep reference
mock_db = patch_db_utils()

# Also mock the connection manager since db_utils and strava_app import it
class MockDBManager:
    def __init__(self):
        self.initialized = True
        self.pool = None
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'pool_hits': 0,
            'pool_misses': 0,
            'connection_errors': 0
        }

    def initialize_pool(self, dsn=None, minconn=2, maxconn=10):
        pass

    def get_pool_connection(self):
        return None

    def release_pool_connection(self, conn):
        pass

    def execute_with_pool(self, query, params=(), fetch=False):
        from db_utils import execute_query
        return execute_query(query, params, fetch)

    def get_connection_stats(self):
        return self.connection_stats

    def get_pool_status(self):
        return {'available': 10, 'used': 0, 'status': 'mock'}

# Create mock module for db_connection_manager
import types
mock_conn_manager = types.ModuleType('db_connection_manager')
mock_conn_manager.db_manager = MockDBManager()
mock_conn_manager.DatabaseConnectionManager = MockDBManager
mock_conn_manager.initialize_database_pool = lambda database_url=None: None
mock_conn_manager.get_database_manager = lambda: mock_conn_manager.db_manager
mock_conn_manager.close_database_pool = lambda: None
mock_conn_manager.monitor_performance = lambda func: func  # No-op decorator

sys.modules['db_connection_manager'] = mock_conn_manager

# ============================================================================
# BYPASS AUTHENTICATION FOR MOCK MODE
# ============================================================================
# Monkey-patch flask_login BEFORE importing strava_app

from flask_login import UserMixin
import flask_login
from functools import wraps

class MockUser(UserMixin):
    """Fake user that's always authenticated."""
    def __init__(self):
        self.id = 1
        self.email = "demo@trainingmonkey.com"
        self.password_hash = "mock"
        self.resting_hr = 52
        self.max_hr = 185
        self.gender = "M"
        self.is_admin = False
        self.registration_date = None
        self.email_modal_dismissals = 0
        self.strava_athlete_id = 12345678
        self.account_status = 'active'
        self.timezone = 'America/Denver'

    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

# Create a singleton mock user
_mock_user = MockUser()

# Monkey-patch login_required to be a no-op that still calls the function
_original_login_required = flask_login.login_required

def mock_login_required(func):
    """No-op decorator that replaces login_required."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        return func(*args, **kwargs)
    return decorated_view

flask_login.login_required = mock_login_required

# Monkey-patch current_user to always be our mock user
class MockCurrentUserProxy:
    """Proxy that always returns mock user attributes."""
    def __getattr__(self, name):
        return getattr(_mock_user, name)

    def __bool__(self):
        return True

    def __repr__(self):
        return f"<MockUser id={_mock_user.id} email={_mock_user.email}>"

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

flask_login.current_user = MockCurrentUserProxy()

print("[MOCK MODE] login_required disabled, current_user mocked")

# Now import strava_app (with auth bypassed)
from strava_app import app
from flask import g

# Set LOGIN_DISABLED to skip the login_required decorator's redirect
app.config['LOGIN_DISABLED'] = True

# Override Flask-Login's internal _get_user function to always return mock user
import flask_login.utils as flu

def _mock_get_user():
    """Always return mock user."""
    return _mock_user

flu._get_user = _mock_get_user

# Also override the user loader
@app.login_manager.user_loader
def always_load_mock_user(user_id):
    """Always return mock user regardless of user_id."""
    return _mock_user

# Add before_request handler to ensure mock user is always set
@app.before_request
def ensure_mock_user_logged_in():
    """Ensure mock user is always available in request context."""
    g._login_user = _mock_user
    # Also patch current_user in the request context
    flask_login.utils._get_user = _mock_get_user

print("[MOCK MODE] Authentication fully bypassed via LOGIN_DISABLED + auto-login")

if __name__ == '__main__':
    print("\nStarting TrainingMonkey in MOCK mode...")
    print("   URL: http://localhost:5001")
    print("   Auth: BYPASSED (auto-logged in as mock user)")
    print("   Go directly to: http://localhost:5001/dashboard")
    print("\n   Press Ctrl+C to stop\n")

    # Run with debug for development
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        use_reloader=False  # Disable reloader to prevent double-patching issues
    )
