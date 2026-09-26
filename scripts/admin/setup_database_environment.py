#!/usr/bin/env python3
"""
Database Environment Setup Script
Sets up the environment for direct database connection
"""

import os
import sys

def setup_environment():
    """Set up environment variables for database connection"""
    
    print("🔧 Setting up Database Environment")
    print("=" * 50)
    
    # Database connection - load from .env file (never hardcode credentials)
    from db_credentials_loader import load_database_url
    database_url = load_database_url()
    
    if not database_url:
        print("❌ ERROR: Could not load DATABASE_URL from .env file")
        print("Please ensure .env file exists in project root with DATABASE_URL set")
        return False
    
    # Set environment variable
    os.environ['DATABASE_URL'] = database_url
    
    print("✅ DATABASE_URL set (value not printed — it contains the password)")
    
    # Verify the setting
    if os.environ.get('DATABASE_URL'):
        print("✅ Environment variable verified")
        return True
    else:
        print("❌ Failed to set environment variable")
        return False

def test_imports():
    """Test if required packages are available"""
    
    print("\n📦 Testing Required Packages")
    print("=" * 50)
    
    packages = [
        'psycopg2',
        'psycopg2.extras',
        'db_utils',
        'db_connection_manager'
    ]
    
    all_ok = True
    
    for package in packages:
        try:
            if package == 'psycopg2':
                import psycopg2
                print(f"✅ {package} - version {psycopg2.__version__}")
            elif package == 'psycopg2.extras':
                import psycopg2.extras
                print(f"✅ {package} - available")
            elif package == 'db_utils':
                import db_utils
                print(f"✅ {package} - available")
            elif package == 'db_connection_manager':
                import db_connection_manager
                print(f"✅ {package} - available")
        except ImportError as e:
            print(f"❌ {package} - {str(e)}")
            all_ok = False
    
    return all_ok

def main():
    """Main setup execution"""
    
    print("🚀 Database Environment Setup")
    print("=" * 60)
    
    # Setup environment
    env_ok = setup_environment()
    
    # Test imports
    imports_ok = test_imports()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 SETUP SUMMARY")
    print("=" * 60)
    print(f"Environment Setup: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Package Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    
    if env_ok and imports_ok:
        print("\n🎉 Environment setup completed successfully!")
        print("You can now run database tests and optimization scripts.")
        return True
    else:
        print("\n⚠️  Setup incomplete. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
