#!/usr/bin/env python3
"""
Check tables in database
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
            # List all tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print("Tables in database:")
            for table in tables:
                print(f"  - {table[0]}")
                
except Exception as e:
    print(f"Error: {e}")
