#!/usr/bin/env python3
"""
Delete Test Account Script
Safely deletes the test account and related data
"""

import psycopg2
import sys

# Database connection
DATABASE_URL = "postgresql://appuser:trainmonk25@35.223.144.85:5432/train-d"

def delete_test_account():
    """Delete the test account and all related data"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Test account email
        test_email = 'strava_187250886@training-monkey.com'
        
        print(f"🔍 Looking for test account: {test_email}")
        
        # First, check if the account exists
        cursor.execute("""
            SELECT id, email, strava_athlete_id, onboarding_step, account_status
            FROM user_settings 
            WHERE email = %s
        """, (test_email,))
        
        result = cursor.fetchone()
        if not result:
            print("❌ Test account not found")
            return False
        
        user_id, email, strava_id, onboarding_step, account_status = result
        print(f"✅ Found test account:")
        print(f"   ID: {user_id}")
        print(f"   Email: {email}")
        print(f"   Strava ID: {strava_id}")
        print(f"   Onboarding Step: {onboarding_step}")
        print(f"   Account Status: {account_status}")
        
        # Delete related data first (to avoid foreign key constraints)
        print("\n🗑️ Deleting related data...")
        
        # Delete activities
        cursor.execute("DELETE FROM activities WHERE user_id = %s", (user_id,))
        activities_deleted = cursor.rowcount
        print(f"   Deleted {activities_deleted} activities")
        
        # Delete onboarding analytics
        cursor.execute("DELETE FROM onboarding_analytics WHERE user_id = %s", (user_id,))
        analytics_deleted = cursor.rowcount
        print(f"   Deleted {analytics_deleted} onboarding analytics records")
        
        # Delete user dashboard configs
        cursor.execute("DELETE FROM user_dashboard_configs WHERE user_id = %s", (user_id,))
        configs_deleted = cursor.rowcount
        print(f"   Deleted {configs_deleted} dashboard configs")
        
        # Delete tutorial completions
        cursor.execute("DELETE FROM tutorial_completions WHERE user_id = %s", (user_id,))
        tutorials_deleted = cursor.rowcount
        print(f"   Deleted {tutorials_deleted} tutorial completions")
        
        # Delete tutorial sessions
        cursor.execute("DELETE FROM tutorial_sessions WHERE user_id = %s", (user_id,))
        sessions_deleted = cursor.rowcount
        print(f"   Deleted {sessions_deleted} tutorial sessions")
        
        # Delete legal compliance records
        cursor.execute("DELETE FROM legal_compliance WHERE user_id = %s", (user_id,))
        legal_deleted = cursor.rowcount
        print(f"   Deleted {legal_deleted} legal compliance records")
        
        # Finally, delete the user account
        print(f"\n🗑️ Deleting user account...")
        cursor.execute("DELETE FROM user_settings WHERE id = %s", (user_id,))
        user_deleted = cursor.rowcount
        
        if user_deleted > 0:
            print(f"✅ Successfully deleted user account")
        else:
            print(f"❌ Failed to delete user account")
            return False
        
        # Commit the transaction
        conn.commit()
        print(f"\n✅ Test account deletion completed successfully!")
        
        # Verify deletion
        cursor.execute("SELECT id FROM user_settings WHERE email = %s", (test_email,))
        verify_result = cursor.fetchone()
        
        if not verify_result:
            print("✅ Verification: Test account successfully removed")
        else:
            print("❌ Verification: Test account still exists")
            return False
        
        # Show remaining users
        print(f"\n📋 Remaining users:")
        cursor.execute("""
            SELECT id, email, strava_athlete_id, onboarding_step, account_status
            FROM user_settings 
            ORDER BY id
        """)
        
        remaining_users = cursor.fetchall()
        for user in remaining_users:
            print(f"   ID {user[0]}: {user[1]} (Strava: {user[2]}, Step: {user[3]}, Status: {user[4]})")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error deleting test account: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🧹 TrainingMonkey Test Account Deletion")
    print("=" * 50)
    
    success = delete_test_account()
    
    if success:
        print(f"\n🎉 Test account deletion completed successfully!")
        print(f"Ready to test new user signup flow.")
    else:
        print(f"\n💥 Test account deletion failed!")
        sys.exit(1)
