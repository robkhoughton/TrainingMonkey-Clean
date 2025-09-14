#!/usr/bin/env python3
"""
Test script for database connection to Google Cloud PostgreSQL
This script tests the connection and provides diagnostic information.
"""

import os
import sys
from pathlib import Path

def test_database_connection():
    """Test the database connection and provide diagnostics"""
    
    print("🔍 Testing Database Connection to Google Cloud PostgreSQL")
    print("=" * 60)
    print()
    
    # Add the app directory to the Python path
    app_dir = Path(__file__).parent.parent / "app"
    sys.path.insert(0, str(app_dir))
    
    # Check environment variables
    print("📋 Environment Variables:")
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Mask the password in the URL for display
        masked_url = database_url
        if '@' in database_url and ':' in database_url:
            parts = database_url.split('@')
            if len(parts) == 2:
                user_pass = parts[0].split('//')[-1]
                if ':' in user_pass:
                    user, _ = user_pass.split(':', 1)
                    masked_url = database_url.replace(user_pass, f"{user}:***")
        print(f"  DATABASE_URL: {masked_url}")
    else:
        print("  ❌ DATABASE_URL not found!")
        print("  💡 Make sure you have a .env file in the app directory")
        return False
    
    google_project = os.environ.get('GOOGLE_CLOUD_PROJECT')
    if google_project:
        print(f"  GOOGLE_CLOUD_PROJECT: {google_project}")
    else:
        print("  ⚠️  GOOGLE_CLOUD_PROJECT not set")
    
    print()
    
    # Test database connection
    print("🔌 Testing Database Connection:")
    try:
        from db_utils import get_db_connection
        
        with get_db_connection() as conn:
            print("  ✅ Connection established successfully!")
            
            with conn.cursor() as cursor:
                # Test basic query
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"  📊 PostgreSQL version: {version[0]}")
                
                # Test database info
                cursor.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
                db_info = cursor.fetchone()
                print(f"  🗄️  Database: {db_info[0]}")
                print(f"  👤 User: {db_info[1]}")
                print(f"  🌐 Server: {db_info[2]}:{db_info[3]}")
                
                # Test table count
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()
                print(f"  📋 Tables in database: {table_count[0]}")
                
                # List some tables
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                    LIMIT 10
                """)
                tables = cursor.fetchall()
                if tables:
                    print("  📋 Sample tables:")
                    for table in tables:
                        print(f"    - {table[0]}")
                    if table_count[0] > 10:
                        print(f"    ... and {table_count[0] - 10} more")
                
                # Test a simple data query if users table exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users'
                    )
                """)
                users_table_exists = cursor.fetchone()[0]
                
                if users_table_exists:
                    cursor.execute("SELECT COUNT(*) FROM users;")
                    user_count = cursor.fetchone()
                    print(f"  👥 Users in database: {user_count[0]}")
                else:
                    print("  ⚠️  Users table not found")
                
                print()
                print("✅ Database connection test completed successfully!")
                return True
                
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        print("  💡 Make sure you're running this from the project root and dependencies are installed")
        return False
        
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("  1. Check your .env file has the correct DATABASE_URL")
        print("  2. Verify your Google Cloud SQL instance is running")
        print("  3. Ensure your IP is whitelisted in Cloud SQL")
        print("  4. Check that the database credentials are correct")
        print("  5. Make sure you have the required Python packages installed")
        return False

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking Dependencies:")
    
    required_packages = [
        'psycopg2',
        'python-dotenv',
        'flask'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print()
        print("💡 Install missing packages with:")
        print(f"  pip install {' '.join(missing_packages)}")
        return False
    
    print("  ✅ All required packages are installed")
    return True

def main():
    """Main test function"""
    print("🚀 Training Monkey - Database Connection Test")
    print("=" * 60)
    print()
    
    # Check dependencies first
    if not check_dependencies():
        print()
        print("❌ Please install missing dependencies and try again")
        return
    
    print()
    
    # Test database connection
    success = test_database_connection()
    
    if success:
        print()
        print("🎉 Setup complete! You can now:")
        print("  1. Start the development server: python start_dev_server.ps1")
        print("  2. Access the application at: http://localhost:5000")
        print("  3. Use Cursor to develop with live database connection")
    else:
        print()
        print("❌ Setup incomplete. Please fix the issues above and try again.")

if __name__ == "__main__":
    main()
