#!/usr/bin/env python3
"""
Test database connection with explicit environment variable
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load DATABASE_URL from .env file (never hardcode credentials)
from db_credentials_loader import set_database_url
set_database_url()

if not os.environ.get('DATABASE_URL'):
    print("ERROR: DATABASE_URL not found. Please ensure .env file exists with DATABASE_URL set.")
    sys.exit(1)

print("Testing database connection...")
print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'NOT SET')[:50]}...")

try:
    from db_utils import get_db_connection
    
    with get_db_connection() as conn:
        print("✅ Database connection successful!")
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"PostgreSQL version: {version[0]}")
            
            cursor.execute("SELECT current_database(), current_user;")
            db_info = cursor.fetchone()
            print(f"Database: {db_info[0]}, User: {db_info[1]}")
            
except Exception as e:
    print(f"❌ Database connection failed: {e}")

print("\nStarting Flask app...")
from strava_app import app

if __name__ == '__main__':
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    
    print("\nStarting server on http://localhost:5001")
    print("Press Ctrl+C to stop")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
