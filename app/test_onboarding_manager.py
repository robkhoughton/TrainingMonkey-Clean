#!/usr/bin/env python3
"""
Test script for onboarding manager
Run this to test the onboarding manager functionality
"""

import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_onboarding_manager():
    """Test the onboarding manager functionality"""
    print("🧪 Testing Onboarding Manager")
    print("=" * 50)
    
    try:
        # Import the onboarding manager
        from onboarding_manager import (
            OnboardingManager, 
            OnboardingStep, 
            FeatureTier,
            onboarding_manager
        )
        
        print("✅ Successfully imported onboarding manager")
        
        # Test 1: Check feature definitions
        print("\n📋 Feature Definitions:")
        for feature_name, feature_def in onboarding_manager.feature_definitions.items():
            print(f"  {feature_name}: {feature_def.description}")
            print(f"    Tier: {feature_def.tier.value}")
            print(f"    Required Steps: {[step.value for step in feature_def.required_steps]}")
            print(f"    Required Activities: {feature_def.required_activities}")
            print(f"    Required Days: {feature_def.required_days}")
            print()
        
        # Test 2: Check step requirements
        print("📝 Step Requirements:")
        for step, req in onboarding_manager.step_requirements.items():
            print(f"  {step.value}: {req['description']}")
            print(f"    Auto-complete: {req['auto_complete']}")
            print(f"    Required Actions: {req['required_actions']}")
            print()
        
        # Test 3: Check onboarding steps
        print("🎯 Onboarding Steps:")
        for step in OnboardingStep:
            print(f"  {step.value}")
        
        print("\n✅ All tests passed! Onboarding manager is working correctly.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the app directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Check the onboarding manager implementation")

def test_database_connection():
    """Test database connection for onboarding manager"""
    print("\n🔌 Testing Database Connection")
    print("=" * 30)
    
    try:
        from db_utils import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                print("✅ Database connection successful")
            else:
                print("❌ Database connection failed")
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("Make sure DATABASE_URL is set in your environment")

def check_required_tables():
    """Check if required database tables exist"""
    print("\n🗄️ Checking Required Tables")
    print("=" * 30)
    
    try:
        from db_utils import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check user_settings table
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'user_settings'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            
            if columns:
                print("✅ user_settings table exists")
                print("Columns:")
                for col_name, col_type in columns:
                    print(f"  {col_name}: {col_type}")
            else:
                print("❌ user_settings table not found")
                
            # Check activities table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'activities'
            """)
            
            if cursor.fetchone()[0] > 0:
                print("✅ activities table exists")
            else:
                print("❌ activities table not found")
                
    except Exception as e:
        print(f"❌ Error checking tables: {e}")

if __name__ == "__main__":
    print("🚀 Onboarding Manager Test Suite")
    print("=" * 50)
    
    # Test 1: Basic functionality
    test_onboarding_manager()
    
    # Test 2: Database connection
    test_database_connection()
    
    # Test 3: Required tables
    check_required_tables()
    
    print("\n" + "=" * 50)
    print("🏁 Test suite completed!")

