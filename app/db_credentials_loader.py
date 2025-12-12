#!/usr/bin/env python3
"""
Database credentials loader - loads DATABASE_URL from .env file
This allows AI tools to run migrations without exposing credentials in code

MOCK MODE:
    Set USE_MOCK_DB=true in .env or environment to use mock data instead of real database.
    This is useful for local UI development with Playwright or design agents.
"""

import os
from pathlib import Path


def is_mock_mode():
    """
    Check if mock database mode is enabled.
    Returns True if USE_MOCK_DB=true in environment or .env file.
    """
    # Check environment variable first
    if os.environ.get('USE_MOCK_DB', '').lower() == 'true':
        return True

    # Check .env file
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('USE_MOCK_DB='):
                    value = line.split('=', 1)[1].strip('"').strip("'").lower()
                    return value == 'true'

    return False


def load_database_url():
    """
    Load DATABASE_URL from .env file in project root
    Returns the DATABASE_URL or None if not found
    Returns 'mock://localhost/trainingmonkey' if mock mode is enabled
    """
    # If mock mode, return mock URL
    if is_mock_mode():
        return 'mock://localhost/trainingmonkey'

    # Try to load from .env file
    env_file = Path(__file__).parent.parent / '.env'

    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('DATABASE_URL='):
                    # Extract value after =
                    value = line.split('=', 1)[1]
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    return value

    # Fallback to environment variable if already set
    return os.environ.get('DATABASE_URL')


def set_database_url():
    """
    Load and set DATABASE_URL environment variable.
    If mock mode is enabled, sets USE_MOCK_DB=true and returns True.
    """
    if is_mock_mode():
        os.environ['USE_MOCK_DB'] = 'true'
        os.environ['DATABASE_URL'] = 'mock://localhost/trainingmonkey'
        print("[MOCK MODE] Mock database enabled - using fake data for UI development")
        return True

    db_url = load_database_url()
    if db_url:
        os.environ['DATABASE_URL'] = db_url
        return True
    return False

if __name__ == "__main__":
    # Test the loader
    db_url = load_database_url()
    if db_url:
        # Print first 50 chars for verification
        print(f"DATABASE_URL found: {db_url[:50]}...")
        print("Successfully loaded database credentials")
    else:
        print("ERROR: Could not find DATABASE_URL in .env file")




