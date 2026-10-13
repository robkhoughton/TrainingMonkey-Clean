"""Suite-wide guard: the test suite must never reach a database.

There is no test database. With the Cloud SQL proxy up and a real DATABASE_URL in
the environment, importing strava_app (pool initialisation) or making a request
through the Flask test client (the api_logs after-request hook) would write to
production.

The block is applied at module level, not in an autouse fixture, because pytest
imports this conftest before any test module - so it is in place before
strava_app's import-time pool initialisation runs.
"""

import os

import psycopg2
import psycopg2.pool

# Dummy URL: db_utils raises at import if DATABASE_URL is unset. Overwrite rather
# than setdefault so a real URL in the environment never reaches app code.
os.environ['DATABASE_URL'] = 'postgresql://blocked:blocked@test-db-blocked.invalid:1/blocked'


class DatabaseAccessBlockedInTests(RuntimeError):
    """Raised when code under test tries to open a database connection."""


def _blocked(name):
    def _raise(*args, **kwargs):
        raise DatabaseAccessBlockedInTests(
            f"{name}() called during tests. The suite has no test database; "
            "mock db_utils / db_connection_manager instead."
        )
    return _raise


psycopg2.connect = _blocked('psycopg2.connect')
psycopg2.pool.SimpleConnectionPool = _blocked('psycopg2.pool.SimpleConnectionPool')
psycopg2.pool.ThreadedConnectionPool = _blocked('psycopg2.pool.ThreadedConnectionPool')


def pytest_configure(config):
    # A test that returns True/False instead of asserting passes whatever happens.
    # Fail it rather than warn.
    config.addinivalue_line('filterwarnings', 'error::pytest.PytestReturnNotNoneWarning')
