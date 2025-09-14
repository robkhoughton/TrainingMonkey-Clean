#!/usr/bin/env python3
"""
Check users in database
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Explicitly set the correct DATABASE_URL
os.environ['DATABASE_URL'] = 'postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d'

try:
    from db_utils import get_db_connection
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Check if user_settings table exists
            cursor.execute("SELECT COUNT(*) FROM user_settings")
            count = cursor.fetchone()
            print(f"Users in database: {count[0]}")
            
            # List first few users
            cursor.execute("SELECT email FROM user_settings LIMIT 5")
            users = cursor.fetchall()
            print("Sample users:")
            for user in users:
                print(f"  - {user[0]}")
                
except Exception as e:
    print(f"Error: {e}")
