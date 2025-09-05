#!/usr/bin/env python3
"""
Test script for proactive token refresh functionality
"""

import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_token_management import (
    get_all_users_needing_token_refresh,
    proactive_token_refresh_for_all_users,
    SimpleTokenManager
)

def test_proactive_token_refresh():
    """Test the proactive token refresh functionality"""
    try:
        print("=== Testing Proactive Token Refresh ===\n")
        
        # Test 1: Get users needing token refresh
        print("1. Checking which users need token refresh...")
        users_needing_refresh = get_all_users_needing_token_refresh()
        
        if users_needing_refresh:
            print(f"   Found {len(users_needing_refresh)} users needing token refresh:")
            for user in users_needing_refresh:
                print(f"   - User {user['user_id']} ({user['email']}): expires in {user['expires_in_minutes']} minutes")
        else:
            print("   No users need token refresh")
        
        # Test 2: Proactive refresh for all users
        print("\n2. Running proactive token refresh for all users...")
        refresh_result = proactive_token_refresh_for_all_users()
        
        if refresh_result['success']:
            print(f"   ✅ Proactive refresh completed successfully")
            print(f"   - Users checked: {refresh_result['users_checked']}")
            print(f"   - Users refreshed: {refresh_result['users_refreshed']}")
            print(f"   - Users failed: {refresh_result['users_failed']}")
            
            if refresh_result['results']:
                print("\n   Detailed results:")
                for result in refresh_result['results']:
                    status_icon = "✅" if result['status'] == 'success' else "❌"
                    print(f"   {status_icon} User {result['user_id']} ({result['email']}): {result['message']}")
        else:
            print(f"   ❌ Proactive refresh failed: {refresh_result['message']}")
        
        # Test 3: Check individual user token status
        print("\n3. Checking individual user token status...")
        if users_needing_refresh:
            test_user_id = users_needing_refresh[0]['user_id']
            print(f"   Testing with user {test_user_id}...")
            
            token_manager = SimpleTokenManager(test_user_id)
            token_status = token_manager.get_simple_token_status()
            
            print(f"   Token status: {token_status['status']}")
            print(f"   Message: {token_status['message']}")
            if 'expires_in_hours' in token_status:
                print(f"   Expires in: {token_status['expires_in_hours']} hours")
        
        print("\n=== Test Complete ===")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_proactive_token_refresh()
    sys.exit(0 if success else 1)

