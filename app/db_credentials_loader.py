#!/usr/bin/env python3
"""
Database credentials loader - loads DATABASE_URL from .env file
This allows AI tools to run migrations without exposing credentials in code
"""

import os
from pathlib import Path

def load_database_url():
    """
    Load DATABASE_URL from .env file in project root
    Returns the DATABASE_URL or None if not found
    """
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
    Load and set DATABASE_URL environment variable
    """
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




