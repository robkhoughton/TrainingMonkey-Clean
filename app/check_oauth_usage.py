#!/usr/bin/env python3
"""
Check OAuth Usage and Manage Strava API Limits
"""

import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db_utils import execute_query

def check_oauth_usage():
    """Check current OAuth usage statistics"""
    try:
        print("=== OAuth Usage Statistics ===\n")
        
        # Count total users
        total_users = execute_query("SELECT COUNT(*) FROM user_settings", fetch=True)
        print(f"Total users: {total_users[0][0] if total_users else 0}")
        
        # Count centralized OAuth users
        centralized_users = execute_query(
            "SELECT COUNT(*) FROM user_settings WHERE oauth_type = 'centralized'", 
            fetch=True
        )
        print(f"Centralized OAuth users: {centralized_users[0][0] if centralized_users else 0}")
        
        # Count individual OAuth users
        individual_users = execute_query(
            "SELECT COUNT(*) FROM user_settings WHERE oauth_type = 'individual'", 
            fetch=True
        )
        print(f"Individual OAuth users: {individual_users[0][0] if individual_users else 0}")
        
        # Count users with valid tokens
        users_with_tokens = execute_query(
            "SELECT COUNT(*) FROM user_settings WHERE strava_access_token IS NOT NULL AND strava_access_token != ''", 
            fetch=True
        )
        print(f"Users with Strava tokens: {users_with_tokens[0][0] if users_with_tokens else 0}")
        
        # Count centralized users with valid tokens
        centralized_with_tokens = execute_query(
            "SELECT COUNT(*) FROM user_settings WHERE oauth_type = 'centralized' AND strava_access_token IS NOT NULL AND strava_access_token != ''", 
            fetch=True
        )
        print(f"Centralized users with valid tokens: {centralized_with_tokens[0][0] if centralized_with_tokens else 0}")
        
        # List all users and their OAuth status
        print("\n=== User Details ===")
        users = execute_query(
            "SELECT id, email, oauth_type, migration_status, strava_access_token IS NOT NULL as has_tokens FROM user_settings ORDER BY id", 
            fetch=True
        )
        
        for user in users:
            user_id, email, oauth_type, migration_status, has_tokens = user
            token_status = "✅ Has tokens" if has_tokens else "❌ No tokens"
            print(f"User {user_id}: {email} | OAuth: {oauth_type} | Migration: {migration_status} | {token_status}")
        
        # Check for users with placeholder tokens
        placeholder_tokens = execute_query(
            "SELECT COUNT(*) FROM user_settings WHERE strava_access_token LIKE 'centralized_%'", 
            fetch=True
        )
        print(f"\nUsers with placeholder tokens: {placeholder_tokens[0][0] if placeholder_tokens else 0}")
        
        return True
        
    except Exception as e:
        print(f"Error checking OAuth usage: {str(e)}")
        return False

def suggest_actions():
    """Suggest actions based on current usage"""
    print("\n=== Recommended Actions ===")
    
    try:
        # Check if we're near the limit
        centralized_users = execute_query(
            "SELECT COUNT(*) FROM user_settings WHERE oauth_type = 'centralized'", 
            fetch=True
        )
        count = centralized_users[0][0] if centralized_users else 0
        
        if count >= 50:  # Assuming 50 is a typical Strava limit
            print("⚠️  WARNING: Near or at Strava OAuth application limit!")
            print("Recommended actions:")
            print("1. Create additional Strava OAuth applications")
            print("2. Implement user rotation between applications")
            print("3. Use individual OAuth for new users")
        elif count >= 40:
            print("⚠️  WARNING: Approaching Strava OAuth application limit")
            print("Consider creating additional OAuth applications soon")
        else:
            print("✅ OAuth usage is within normal limits")
            
        # Check for users needing re-authentication
        placeholder_users = execute_query(
            "SELECT id, email FROM user_settings WHERE strava_access_token LIKE 'centralized_%'", 
            fetch=True
        )
        
        if placeholder_users:
            print(f"\n📋 Users needing re-authentication ({len(placeholder_users)}):")
            for user in placeholder_users:
                print(f"   - User {user[0]}: {user[1]}")
            print("\nThese users need to re-authenticate with Strava to get valid tokens.")
        
    except Exception as e:
        print(f"Error generating suggestions: {str(e)}")

if __name__ == "__main__":
    print("OAuth Usage Checker")
    print("=" * 50)
    
    if check_oauth_usage():
        suggest_actions()
    else:
        print("Failed to check OAuth usage")
