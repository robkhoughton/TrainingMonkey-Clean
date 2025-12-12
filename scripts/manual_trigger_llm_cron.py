#!/usr/bin/env python3
"""
Manually trigger LLM recommendations generation for testing purposes.
This bypasses the Cloud Scheduler and directly calls the generation function.
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from db_utils import execute_query
from llm_recommendations_module import generate_recommendations
from timezone_utils import get_user_current_date

def get_active_users(days=7):
    """Get list of active users with recent activity"""
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    results = execute_query("""
        SELECT DISTINCT user_id, 
               (SELECT email FROM user_settings WHERE id = user_id) as email,
               MAX(date) as last_activity
        FROM activities 
        WHERE date >= %s AND activity_id != 0
        GROUP BY user_id
        ORDER BY MAX(date) DESC
    """, (cutoff_date,), fetch=True)
    
    return [dict(row) for row in results] if results else []


def generate_for_user(user_id, email=None):
    """Generate recommendation for a specific user"""
    print(f"\n{'='*60}")
    print(f"  Generating recommendation for User {user_id}")
    if email:
        print(f"  Email: {email}")
    print('='*60)
    
    try:
        # Get user's current date
        current_date = get_user_current_date(user_id)
        print(f"  User's current date: {current_date.strftime('%Y-%m-%d')}")
        
        # Check if user has activity today
        from llm_recommendations_module import check_activity_for_date
        has_activity = check_activity_for_date(user_id, current_date.strftime('%Y-%m-%d'))
        
        target_date = (current_date + timedelta(days=1)) if has_activity else current_date
        print(f"  Has activity today: {has_activity}")
        print(f"  Target date: {target_date.strftime('%Y-%m-%d')}")
        
        # Generate recommendation
        print(f"\n  Calling generate_recommendations()...")
        result = generate_recommendations(force=True, user_id=user_id)
        
        if result:
            print(f"\n  ✅ SUCCESS")
            print(f"     Recommendation ID: {result.get('id', 'N/A')}")
            print(f"     Target date: {result.get('target_date', 'N/A')}")
            print(f"     Generated: {result.get('generation_date', 'N/A')}")
            print(f"     Autopsy-informed: {result.get('is_autopsy_informed', False)}")
            
            # Preview daily recommendation
            daily_rec = result.get('daily_recommendation', '')
            if daily_rec:
                preview = daily_rec[:150] + "..." if len(daily_rec) > 150 else daily_rec
                print(f"\n     Daily recommendation preview:")
                print(f"     {preview}")
            
            return True
        else:
            print(f"\n  ❌ FAILED - No recommendation generated")
            return False
            
    except Exception as e:
        print(f"\n  ❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║  MANUAL LLM RECOMMENDATIONS GENERATION                   ║")
    print("╚" + "="*58 + "╝")
    
    print("\nThis script manually triggers LLM recommendation generation")
    print("bypassing Cloud Scheduler (useful for testing and debugging).\n")
    
    # Get active users
    print("Fetching active users...")
    active_users = get_active_users(days=7)
    
    if not active_users:
        print("\n⚠️  No active users found (no activity in last 7 days)")
        return
    
    print(f"\nFound {len(active_users)} active user(s):\n")
    for i, user in enumerate(active_users, 1):
        email = user.get('email', 'No email')
        last_activity = user.get('last_activity', 'Unknown')
        print(f"  {i}. User {user['user_id']} - {email} (Last activity: {last_activity})")
    
    print(f"\n{'='*60}")
    print("  GENERATION OPTIONS")
    print('='*60)
    print("\n  1. Generate for ALL active users")
    print("  2. Generate for specific user ID")
    print("  3. Cancel")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        print(f"\nGenerating for ALL {len(active_users)} users...")
        successful = 0
        failed = 0
        
        for user in active_users:
            if generate_for_user(user['user_id'], user.get('email')):
                successful += 1
            else:
                failed += 1
        
        print(f"\n{'='*60}")
        print(f"  GENERATION COMPLETE")
        print('='*60)
        print(f"\n  Successful: {successful}")
        print(f"  Failed: {failed}")
        print(f"  Total: {len(active_users)}")
        
    elif choice == "2":
        user_id = input("\nEnter user ID: ").strip()
        try:
            user_id = int(user_id)
            generate_for_user(user_id)
        except ValueError:
            print("\n❌ Invalid user ID")
            
    else:
        print("\nCancelled")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)







