#!/usr/bin/env python3
"""
Database Connection Test Script
Tests direct connection to Google Cloud PostgreSQL database
"""

import os
import sys
import psycopg2
import psycopg2.extras
from datetime import datetime

def test_database_connection():
    """Test direct database connection to Google Cloud PostgreSQL"""
    
    print("🔗 Testing Database Connection")
    print("=" * 50)
    
    # Database connection details from project rules
    # Load database config from .env file (never hardcode credentials)
    from db_credentials_loader import load_database_url
    from urllib.parse import urlparse
    
    database_url = load_database_url()
    if not database_url:
        print("ERROR: Could not load DATABASE_URL from .env file")
        return
    
    # Parse connection string
    parsed = urlparse(database_url)
    db_config = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password
    }
    
    # Construct connection string
    connection_string = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    
    print(f"Host: {db_config['host']}")
    print(f"Port: {db_config['port']}")
    print(f"Database: {db_config['database']}")
    print(f"User: {db_config['user']}")
    print(f"Connection String: {connection_string[:50]}...")
    print()
    
    try:
        # Test connection
        print("🔄 Attempting connection...")
        conn = psycopg2.connect(connection_string)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        
        print("✅ Connection successful!")
        
        # Test basic query
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"📊 PostgreSQL Version: {version['version']}")
        
        # Test database info
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_user, now();")
            info = cursor.fetchone()
            print(f"📊 Current Database: {info['current_database']}")
            print(f"📊 Current User: {info['current_user']}")
            print(f"📊 Server Time: {info['now']}")
        
        # Test table existence
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print(f"📊 Tables Found: {len(tables)}")
            for table in tables:
                print(f"   - {table['table_name']}")
        
        # Test user_settings table structure
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'user_settings' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print(f"📊 user_settings columns: {len(columns)}")
            for col in columns[:5]:  # Show first 5 columns
                print(f"   - {col['column_name']:<30} {col['data_type']:<15}")
            if len(columns) > 5:
                print(f"   ... and {len(columns) - 5} more columns")
        
        # Test activities table count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM activities;")
            result = cursor.fetchone()
            print(f"📊 Activities Count: {result['count']}")
        
        # Test user_settings count
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM user_settings;")
            result = cursor.fetchone()
            print(f"📊 Users Count: {result['count']}")
        
        conn.close()
        print("\n✅ Database connection test completed successfully!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if Google Cloud SQL instance is running")
        print("2. Verify public IP is enabled")
        print("3. Check if your IP is authorized")
        print("4. Verify database credentials")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def test_environment_setup():
    """Test environment variable setup"""
    print("\n🔧 Testing Environment Setup")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"✅ DATABASE_URL is set: {database_url[:50]}...")
    else:
        print("❌ DATABASE_URL is not set")
        print("\n🔧 To set DATABASE_URL:")
        print("Windows: Create .env file with: DATABASE_URL=postgresql://user:password@host:port/database")
        print("Linux/Mac: Create .env file with: DATABASE_URL=postgresql://user:password@host:port/database")
    
    # Check required packages
    try:
        import psycopg2
        print("✅ psycopg2 is installed")
    except ImportError:
        print("❌ psycopg2 is not installed")
        print("Install with: pip install psycopg2-binary")
    
    try:
        import psycopg2.extras
        print("✅ psycopg2.extras is available")
    except ImportError:
        print("❌ psycopg2.extras is not available")
    
    return database_url is not None

def main():
    """Main test execution"""
    print("🚀 Database Connection Test Suite")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test environment setup
    env_ok = test_environment_setup()
    
    # Test database connection
    if env_ok:
        db_ok = test_database_connection()
    else:
        print("\n⚠️  Skipping database connection test due to environment issues")
        db_ok = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Environment Setup: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Database Connection: {'✅ PASS' if db_ok else '❌ FAIL'}")
    
    if env_ok and db_ok:
        print("\n🎉 All tests passed! Database connection is working correctly.")
        print("You can now run the database optimization tests.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
